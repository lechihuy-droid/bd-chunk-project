import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from domain.run import RunRequest
from persistence.models import Artifact, ArtifactRevision, ExecutionRun, RunManifest, WorkflowRelease
from ports.prompt_registry import ResolvedPrompt
from ports.runtime import RuntimeHandle, RuntimeStatus
from services.run_service import RunService
from ports.blob_store import BlobRef


class BlobFake:
    def __init__(self, content: bytes): self.content = content
    def get(self, uri): return self.content
    def put_immutable(self, **kwargs): raise AssertionError("not used")
    def exists(self, key): return False


class PromptFake:
    def resolve(self, name: str, **_: object) -> ResolvedPrompt:
        return ResolvedPrompt("mlflow", name, 2, "resolved template", f"prompts:/{name}/2")


class SourceFake:
    def commit_exists(self, repo: str, sha: str) -> bool:
        return True


class FreezeSpyRuntime:
    def __init__(self, session) -> None:
        self.session = session

    async def start(self, request):
        run = self.session.get(ExecutionRun, request.run_id)
        manifest = self.session.scalar(select(RunManifest).where(RunManifest.run_id == request.run_id))
        assert run is not None
        assert manifest is not None
        return RuntimeHandle("langgraph", "runtime-1", None, RuntimeStatus("PENDING", "pending"))


def test_manifest_and_run_exist_before_runtime_start(session, tmp_path) -> None:
    release = WorkflowRelease(
        workflow_id="workflow",
        release_version="1.0.0",
        status="PUBLISHED",
        git_repo="repo",
        git_ref="HEAD",
        git_commit="a" * 40,
        entrypoint="graph:build_graph",
        state_schema_version="v1",
        bindings={"generate_bd": {"prompt_ref": "mlflow://prompt", "prompt_alias": "production"}},
        runtime_adapter_id="langgraph",
        model_profile="model",
        model_name="model",
        created_by="test",
        published_at=datetime.now(timezone.utc),
    )
    artifact = Artifact(project_key="project", artifact_type="RD_SOURCE", business_key="RD", display_name="RD")
    session.add_all([release, artifact])
    session.flush()
    input_file = tmp_path / "rd.md"
    input_file.write_text("RD content", encoding="utf-8")
    revision = ArtifactRevision(
        artifact_id=artifact.id,
        revision_no=1,
        origin="IMPORTED",
        content_hash="sha256:" + "b" * 64,
        storage_uri="s3://vgov-artifacts/project/RD_SOURCE/RD/test.md",
        mime_type="text/markdown",
        size_bytes=10,
        created_by="test",
    )
    session.add(revision)
    session.commit()

    service = RunService(session, FreezeSpyRuntime(session), PromptFake(), SourceFake(), "http://api", BlobFake(b"RD content"))
    run = asyncio.run(
        service.start(RunRequest("project", "workflow", revision.id, "OUT", release_id=release.id))
    )
    assert run.status == "RUNNING"
