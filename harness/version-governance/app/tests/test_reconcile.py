import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import text

from persistence.models import ExecutionRun, WorkflowRelease
from ports.runtime import RuntimeStatus
from services.run_service import RunService


class Runtime:
    async def get_status(self, runtime_run_id: str) -> RuntimeStatus:
        return RuntimeStatus("SUCCEEDED", "success")


def test_reconcile_closes_lost_callback_without_creating_revision(session) -> None:
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
    result = asyncio.run(RunService(session, Runtime(), None, None, "http://api").reconcile(run))
    assert result.status == "SUCCEEDED"
    assert result.error_code == "CALLBACK_LOST"
    assert session.scalar(text("SELECT count(*) FROM artifact_revision")) == 0
