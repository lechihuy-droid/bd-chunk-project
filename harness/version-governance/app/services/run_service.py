import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from domain.manifest import manifest_hash
from domain.run import RunRequest
from persistence.models import (
    ArtifactRevision,
    EnvironmentMapping,
    ExecutionRun,
    RunComponent,
    RunManifest,
    RuntimeCallback,
    WorkflowRelease,
)
from ports.prompt_registry import PromptRegistryPort, PromptResolutionError, ResolvedPrompt
from ports.runtime import ResolvedPromptBinding, StartRunRequest, WorkflowRuntimePort
from ports.source_control import SourceControlPort
from ports.blob_store import BlobStorePort
from services.artifact_service import ArtifactService


class RunService:
    def __init__(
        self,
        session: Session,
        runtime: WorkflowRuntimePort,
        prompts: PromptRegistryPort,
        source: SourceControlPort,
        callback_base_url: str,
        blobs: BlobStorePort | None = None,
        callback_grace_seconds: int = 120,
    ) -> None:
        self.session = session
        self.runtime = runtime
        self.prompts = prompts
        self.source = source
        self.callback_base_url = callback_base_url
        self.blobs = blobs
        self.callback_grace_seconds = callback_grace_seconds

    async def start(self, req: RunRequest) -> ExecutionRun:
        run = ExecutionRun(
            project_key=req.project_key,
            workflow_id=req.workflow_id,
            output_business_key=req.output_business_key,
            output_artifact_type=req.output_artifact_type,
            environment=req.environment,
            execution_mode="PINNED_RELEASE" if req.release_id else "ENVIRONMENT",
            correlation_id=uuid.uuid4(),
        )
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)

        try:
            release = self._resolve_release(req)
            revision = self._input_revision(req.input_revision_id)
            prompts, components = self._freeze_components(release)
            if not self.source.commit_exists(release.git_repo, release.git_commit):
                raise ValueError("GIT_COMMIT_NOT_FOUND")

            if self.blobs is None:
                raise ValueError("BLOB_STORE_REQUIRED")
            input_payload = self.blobs.get(revision.storage_uri).decode("utf-8")
            manifest = RunManifest(
                run_id=run.id,
                workflow_release_id=release.id,
                git_repo=release.git_repo,
                git_commit=release.git_commit,
                model_profile=release.model_profile,
                runtime_adapter_id=release.runtime_adapter_id,
                environment=req.environment,
                input_source_ref=f"artifact_revision:{revision.id}",
                input_hash=revision.content_hash,
                manifest_hash=manifest_hash(
                    release_id=release.id,
                    git_commit=release.git_commit,
                    model_profile=release.model_profile,
                    runtime_adapter_id=release.runtime_adapter_id,
                    input_hash=revision.content_hash,
                    components=components,
                ),
            )
            self.session.add(manifest)
            self.session.flush()
            for component in components:
                self.session.add(RunComponent(manifest_id=manifest.id, **component))

            run.workflow_release_id = release.id
            run.status = "MANIFEST_FROZEN"
            self.session.commit()
        except Exception as exc:
            self.session.rollback()
            failed_run = self.session.get(ExecutionRun, run.id)
            assert failed_run is not None
            failed_run.status = "FAILED_PRECONDITION"
            failed_run.error_code = self._precondition_code(exc)
            failed_run.error_message = str(exc)
            self.session.commit()
            raise HTTPException(
                status_code=422,
                detail={"code": failed_run.error_code, "message": str(exc)},
            ) from exc

        try:
            handle = await self.runtime.start(
                StartRunRequest(
                    correlation_id=str(run.correlation_id),
                    run_id=str(run.id),
                    entrypoint=release.entrypoint,
                    state_schema_version=release.state_schema_version,
                    model_profile=release.model_profile,
                    model_name=release.model_name,
                    prompts=tuple(prompts),
                    input_payload=input_payload,
                    input_hash=revision.content_hash,
                    callback_url=f"{self.callback_base_url}/api/vgov/runs/{run.id}/callback",
                )
            )
        except Exception as exc:
            run.status = "FAILED"
            run.error_code = "RUNTIME_UNAVAILABLE"
            run.error_message = str(exc)
            self.session.commit()
            raise HTTPException(
                status_code=502,
                detail={"code": "RUNTIME_UNAVAILABLE", "message": str(exc)},
            ) from exc

        run.status = "RUNNING"
        run.runtime_provider = handle.provider
        run.runtime_run_id = handle.runtime_run_id
        run.runtime_thread_id = handle.runtime_thread_id
        run.started_at = datetime.now(timezone.utc)
        self.session.commit()
        return run

    async def callback(self, run_id: uuid.UUID, body: dict[str, Any]) -> dict[str, Any]:
        run = self.session.get(ExecutionRun, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})

        claimed = self.session.execute(
            text(
                "INSERT INTO runtime_callback (correlation_id) VALUES (:correlation_id) "
                "ON CONFLICT DO NOTHING"
            ),
            {"correlation_id": run.correlation_id},
        ).rowcount
        if not claimed:
            callback = self.session.get(RuntimeCallback, run.correlation_id)
            if callback is None or callback.response_body is None:
                self.session.rollback()
                raise HTTPException(
                    status_code=409,
                    detail={"code": "CALLBACK_IN_PROGRESS"},
                )
            return callback.response_body

        status, error_code = self._canonical_callback_status(body.get("status"))
        if status == "SUCCEEDED":
            output = body.get("output")
            if not isinstance(output, dict) or not isinstance(output.get("content"), str):
                status, error_code = "FAILED", "RUNTIME_OUTPUT_MISSING"
                run.error_message = "successful callback missing output.content"
            else:
                ArtifactService(self.session, self.blobs).create_ai_generated(
                    run, output["content"], str(output.get("mime") or "text/markdown")
                )
        run.status = status
        run.error_code = error_code
        run.error_message = body.get("error") if status == "FAILED" else None
        run.trace_id = body.get("trace_id")
        run.trace_provider = "mlflow" if run.trace_id else None
        run.completed_at = datetime.now(timezone.utc)
        response = {"run_id": str(run.id), "status": run.status}
        callback = self.session.get(RuntimeCallback, run.correlation_id)
        assert callback is not None
        callback.response_body = response
        callback.completed_at = datetime.now(timezone.utc)
        self.session.commit()
        return response

    async def reconcile(self, run: ExecutionRun) -> ExecutionRun:
        """[SD §4.1] / [ADR-010]. Đóng run RUNNING khi runtime báo terminal và callback chưa hoàn tất:
        không có row `runtime_callback` nào (mất từ đầu), hoặc có row nhưng `response_body` vẫn NULL
        quá `callback_grace_seconds` (claim mồ côi — process xử lý nó đã chết giữa chừng). Trong grace
        period, một row `response_body IS NULL` được coi là callback đang xử lý hợp lệ và không bị
        đụng vào."""
        if run.status != "RUNNING" or not run.runtime_run_id:
            return run

        status = await self.runtime.get_status(run.runtime_run_id)
        if status.canonical not in {"SUCCEEDED", "FAILED", "CANCELLED"}:
            return run

        callback = self.session.get(RuntimeCallback, run.correlation_id)
        orphaned = callback is None or (
            callback.response_body is None
            and callback.received_at
            <= datetime.now(timezone.utc) - timedelta(seconds=self.callback_grace_seconds)
        )
        if orphaned:
            run.status = status.canonical
            run.error_code = "CALLBACK_LOST"
            run.completed_at = datetime.now(timezone.utc)
            self.session.commit()
        return run

    def _resolve_release(self, req: RunRequest) -> WorkflowRelease:
        if req.release_id:
            release = self.session.get(WorkflowRelease, req.release_id)
            if release is None:
                raise ValueError("RELEASE_NOT_FOUND")
        else:
            release = self.session.scalar(
                select(WorkflowRelease)
                .join(
                    EnvironmentMapping,
                    EnvironmentMapping.workflow_release_id == WorkflowRelease.id,
                )
                .where(
                    EnvironmentMapping.environment == req.environment,
                    EnvironmentMapping.workflow_id == req.workflow_id,
                )
            )
            if release is None:
                raise ValueError("NO_RELEASE_FOR_ENVIRONMENT")
        if release.status != "PUBLISHED":
            raise ValueError("RELEASE_NOT_PUBLISHED")
        return release

    def _input_revision(self, revision_id: uuid.UUID) -> ArtifactRevision:
        revision = self.session.get(ArtifactRevision, revision_id)
        if revision is None:
            raise ValueError("INPUT_NOT_FOUND")
        return revision

    def _freeze_components(
        self,
        release: WorkflowRelease,
    ) -> tuple[list[ResolvedPromptBinding], list[dict[str, Any]]]:
        prompts: list[ResolvedPromptBinding] = []
        components: list[dict[str, Any]] = [
            {
                "kind": "MODEL",
                "ref": f"model://{release.model_profile}",
                "exact_version": release.model_name,
                "extra": {},
            }
        ]
        for node, binding in release.bindings.items():
            if not isinstance(binding, dict):
                raise ValueError(f"INVALID_BINDING:{node}")
            prompt_ref = binding.get("prompt_ref")
            if prompt_ref:
                prompt = self._resolve_prompt(node, prompt_ref, binding)
                prompts.append(
                    ResolvedPromptBinding(node, prompt.name, prompt.version, prompt.template)
                )
                components.append(
                    {
                        "kind": "PROMPT",
                        "ref": prompt_ref,
                        "exact_version": str(prompt.version),
                        "extra": {},
                    }
                )
            self._append_declared_component(components, "AGENT", binding.get("agent_ref"), binding.get("agent_version"))
            self._append_tools(components, binding.get("tool_refs"))
        return prompts, self._dedupe(components)

    @staticmethod
    def _dedupe(components: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Gộp component trùng (kind, ref) khai ở nhiều node.

        Một tool hay prompt dùng chung cho nhiều node là bình thường, nhưng
        `uq_component(manifest_id, kind, ref)` chỉ cho phép một hàng. Không gộp ở đây thì INSERT ném
        IntegrityError giữa pha freeze và bị nuốt thành error_code là chuỗi SQL thô.

        Cùng (kind, ref) mà khác exact_version là mâu thuẫn thật trong release — fail closed.
        """
        merged: dict[tuple[str, str], dict[str, Any]] = {}
        for component in components:
            key = (component["kind"], component["ref"])
            existing = merged.get(key)
            if existing is None:
                merged[key] = component
            elif existing["exact_version"] != component["exact_version"]:
                raise ValueError(
                    f"CONFLICTING_COMPONENT_VERSION:{component['kind']}:{component['ref']}"
                )
        return list(merged.values())

    def _resolve_prompt(
        self,
        node: str,
        prompt_ref: str,
        binding: dict[str, Any],
    ) -> ResolvedPrompt:
        if not prompt_ref.startswith("mlflow://"):
            raise PromptResolutionError(f"Unsupported prompt ref for {node}: {prompt_ref}")
        name = prompt_ref.removeprefix("mlflow://")
        if binding.get("prompt_version") is not None:
            return self.prompts.resolve(name, version=int(binding["prompt_version"]))
        alias = binding.get("prompt_alias")
        if not alias:
            raise PromptResolutionError(f"Missing prompt_alias or prompt_version for {node}")
        return self.prompts.resolve(name, alias=str(alias))

    @staticmethod
    def _append_declared_component(
        components: list[dict[str, Any]],
        kind: str,
        ref: Any,
        version: Any,
    ) -> None:
        if ref is None:
            return
        if version is None:
            raise ValueError(f"MISSING_{kind}_VERSION")
        components.append({"kind": kind, "ref": str(ref), "exact_version": str(version), "extra": {}})

    def _append_tools(self, components: list[dict[str, Any]], tool_refs: Any) -> None:
        if tool_refs is None:
            return
        if isinstance(tool_refs, dict):
            entries = tool_refs.items()
        elif isinstance(tool_refs, list):
            entries = ((item.get("ref"), item.get("version")) for item in tool_refs if isinstance(item, dict))
        else:
            raise ValueError("INVALID_TOOL_REFS")
        for ref, value in entries:
            version = value.get("version") if isinstance(value, dict) else value
            self._append_declared_component(components, "TOOL", ref, version)

    @staticmethod
    def _precondition_code(exc: Exception) -> str:
        """Mã lỗi ổn định cho client — không bao giờ để chuỗi SQL thô lọt ra ngoài."""
        if isinstance(exc, PromptResolutionError):
            return "PROMPT_UNRESOLVED"
        if isinstance(exc, DBAPIError):
            sqlstate = getattr(exc.orig, "sqlstate", None) or getattr(exc.orig, "pgcode", None)
            return {"VG409": "IMMUTABLE_OBJECT", "23514": "VALIDATION_ERROR", "23505": "CONFLICT"}.get(
                sqlstate, "DATABASE_ERROR"
            )
        if isinstance(exc, ValueError):
            return str(exc)
        return "PRECONDITION_FAILED"

    @staticmethod
    def _canonical_callback_status(value: Any) -> tuple[str, str | None]:
        normalized = str(value or "").strip().lower()
        mapping = {
            "pending": "RUNNING",
            "queued": "RUNNING",
            "running": "RUNNING",
            "success": "SUCCEEDED",
            "succeeded": "SUCCEEDED",
            "error": "FAILED",
            "failed": "FAILED",
            "timeout": "FAILED",
            "cancelled": "CANCELLED",
        }
        status = mapping.get(normalized)
        if status is None:
            return "FAILED", "RUNTIME_STATUS_UNKNOWN"
        return status, None
