import asyncio
import re
from datetime import datetime, timezone

from sqlalchemy import select

from domain.run import RunRequest
from persistence.models import Artifact, ArtifactRevision, RunComponent, RunManifest, WorkflowRelease
from ports.prompt_registry import ResolvedPrompt
from ports.runtime import RuntimeHandle, RuntimeStatus
from services.run_service import RunService
from ports.blob_store import BlobRef


class BlobFake:
    def get(self, uri): return b"RD"
    def put_immutable(self, **kwargs): raise AssertionError("not used")
    def exists(self, key): return False


class Prompts:
    def resolve(self, name: str, **_: object) -> ResolvedPrompt:
        return ResolvedPrompt("mlflow", name, 12, "template", f"prompts:/{name}/12")


class Source:
    def commit_exists(self, repo: str, sha: str) -> bool:
        return True


class Runtime:
    async def start(self, request):
        return RuntimeHandle("langgraph", "runtime", None, RuntimeStatus("PENDING", "pending"))


def test_frozen_prompt_components_only_store_numeric_versions(session, tmp_path) -> None:
    release = WorkflowRelease(
        workflow_id="workflow", release_version="1", status="PUBLISHED", git_repo="repo", git_ref="HEAD",
        git_commit="a" * 40, entrypoint="graph:build_graph", state_schema_version="v1",
        bindings={"parse_rd": {"prompt_ref": "mlflow://parse", "prompt_alias": "production"}, "generate_bd": {"prompt_ref": "mlflow://generate", "prompt_version": 12}},
        runtime_adapter_id="langgraph", model_profile="model", model_name="model", created_by="test", published_at=datetime.now(timezone.utc),
    )
    artifact = Artifact(project_key="project", artifact_type="RD_SOURCE", business_key="RD", display_name="RD")
    session.add_all([release, artifact])
    session.flush()
    source = tmp_path / "rd.md"
    source.write_text("RD", encoding="utf-8")
    revision = ArtifactRevision(
        artifact_id=artifact.id, revision_no=1, origin="IMPORTED", content_hash="sha256:" + "b" * 64,
        storage_uri="s3://vgov-artifacts/project/RD_SOURCE/RD/test.md", mime_type="text/markdown", size_bytes=2, created_by="test",
    )
    session.add(revision)
    session.commit()

    run = asyncio.run(RunService(session, Runtime(), Prompts(), Source(), "http://api", BlobFake()).start(
        RunRequest("project", "workflow", revision.id, "OUT", release_id=release.id)
    ))
    manifest = session.scalar(select(RunManifest).where(RunManifest.run_id == run.id))
    prompts = list(session.scalars(select(RunComponent).where(RunComponent.manifest_id == manifest.id, RunComponent.kind == "PROMPT")))
    aliases = {"production", "prod", "latest", "staging", "champion", "current"}
    assert prompts
    assert all(re.fullmatch(r"[0-9]+", component.exact_version) for component in prompts)
    assert not any(component.exact_version.lower() in aliases for component in prompts)
