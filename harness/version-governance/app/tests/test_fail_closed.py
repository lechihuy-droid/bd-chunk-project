import asyncio
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import text

from domain.run import RunRequest
from persistence.models import Artifact, ArtifactRevision, ExecutionRun, WorkflowRelease
from ports.prompt_registry import PromptResolutionError
from services.run_service import RunService
from ports.blob_store import BlobRef


class BlobFake:
    def get(self, uri): return b"RD"
    def put_immutable(self, **kwargs): raise AssertionError("not used")
    def exists(self, key): return False


class FailingPrompts:
    def resolve(self, name: str, **_: object):
        raise PromptResolutionError("missing alias")


class SourceFake:
    def commit_exists(self, repo: str, sha: str) -> bool:
        return True


class RuntimeSpy:
    def __init__(self) -> None:
        self.calls = 0

    async def start(self, request):
        self.calls += 1


def test_prompt_failure_creates_no_manifest_and_never_starts_runtime(session, tmp_path) -> None:
    release = WorkflowRelease(
        workflow_id="workflow", release_version="1.0.0", status="PUBLISHED", git_repo="repo", git_ref="HEAD",
        git_commit="a" * 40, entrypoint="graph:build_graph", state_schema_version="v1",
        bindings={"generate_bd": {"prompt_ref": "mlflow://prompt", "prompt_alias": "production"}},
        runtime_adapter_id="langgraph", model_profile="model", model_name="model", created_by="test", published_at=datetime.now(timezone.utc),
    )
    artifact = Artifact(project_key="project", artifact_type="RD_SOURCE", business_key="RD", display_name="RD")
    session.add_all([release, artifact])
    session.flush()
    input_file = tmp_path / "rd.md"
    input_file.write_text("RD", encoding="utf-8")
    revision = ArtifactRevision(
        artifact_id=artifact.id, revision_no=1, origin="IMPORTED", content_hash="sha256:" + "b" * 64,
        storage_uri="s3://vgov-artifacts/project/RD_SOURCE/RD/test.md", mime_type="text/markdown", size_bytes=2, created_by="test",
    )
    session.add(revision)
    session.commit()
    runtime = RuntimeSpy()
    service = RunService(session, runtime, FailingPrompts(), SourceFake(), "http://api", BlobFake())

    with pytest.raises(HTTPException) as error:
        asyncio.run(service.start(RunRequest("project", "workflow", revision.id, "OUT", release_id=release.id)))
    assert error.value.status_code == 422
    assert session.scalar(text("SELECT count(*) FROM run_manifest")) == 0
    assert session.scalar(text("SELECT status FROM execution_run")) == "FAILED_PRECONDITION"
    assert runtime.calls == 0
