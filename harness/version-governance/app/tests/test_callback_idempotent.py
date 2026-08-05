import asyncio
import uuid
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import text

from persistence.models import ExecutionRun, WorkflowRelease
from services.run_service import RunService
from ports.blob_store import BlobRef


class BlobFake:
    def put_immutable(self, *, key, data, mime_type):
        import hashlib
        return BlobRef(f"s3://vgov-artifacts/{key}", "sha256:" + hashlib.sha256(data).hexdigest(), len(data), mime_type)

    def get(self, uri):
        return b""

    def exists(self, key):
        return False


def make_running_run(session) -> ExecutionRun:
    release = WorkflowRelease(
        workflow_id="workflow", release_version="1", status="PUBLISHED", git_repo="repo", git_ref="HEAD",
        git_commit="a" * 40, entrypoint="graph:build_graph", state_schema_version="v1", bindings={},
        runtime_adapter_id="langgraph", model_profile="model", model_name="model", created_by="test", published_at=datetime.now(timezone.utc),
    )
    session.add(release)
    session.flush()
    run = ExecutionRun(
        project_key="project", workflow_id="workflow", workflow_release_id=release.id, output_business_key="OUT",
        output_artifact_type="API_BASIC_DESIGN", environment="PROD", execution_mode="ENVIRONMENT",
        status="RUNNING", correlation_id=uuid.uuid4(), runtime_run_id="runtime",
    )
    session.add(run)
    session.commit()
    return run


def test_callback_is_idempotent(session) -> None:
    run = make_running_run(session)
    service = RunService(session, None, None, None, "http://api", BlobFake())
    first = asyncio.run(service.callback(run.id, {"status": "success", "output": {"content": "# BD", "mime": "text/markdown"}}))
    second = asyncio.run(service.callback(run.id, {"status": "FAILED"}))
    third = asyncio.run(service.callback(run.id, {"status": "mystery"}))
    assert first == second == third == {"run_id": str(run.id), "status": "SUCCEEDED"}
    assert session.scalar(text("SELECT count(*) FROM runtime_callback")) == 1


def test_callback_returns_conflict_when_claim_is_in_progress(session) -> None:
    run = make_running_run(session)
    session.execute(text("INSERT INTO runtime_callback (correlation_id) VALUES (:id)"), {"id": run.correlation_id})
    session.commit()
    service = RunService(session, None, None, None, "http://api", BlobFake())
    with pytest.raises(HTTPException) as error:
        asyncio.run(service.callback(run.id, {"status": "success"}))
    assert error.value.status_code == 409
    assert error.value.detail["code"] == "CALLBACK_IN_PROGRESS"
