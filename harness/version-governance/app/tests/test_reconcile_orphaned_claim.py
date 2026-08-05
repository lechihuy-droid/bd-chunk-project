"""[SD §4.1] / [ADR-010] — Reconciliation của claim mồ côi.

`test_reconcile.py` phủ case đơn giản: run `RUNNING`, KHÔNG có row `runtime_callback` nào, runtime báo
terminal -> `reconcile()` đóng run với `error_code=CALLBACK_LOST`.

File này phủ case khác: `runtime_callback` ĐÃ có row (bước 1 của `[SD §4.2]` — `INSERT ... ON CONFLICT
DO NOTHING` đã claim thành công) nhưng `response_body` vẫn NULL vì tiến trình xử lý callback chết giữa
transaction (container bị kill, exception không bắt được, v.v.) trước khi chạy tới bước 3-4.

`[ADR-010]` giải quyết bằng ngưỡng thời gian (`callback_grace_seconds`, mặc định 120s qua
`VGOV_CALLBACK_GRACE_SECONDS`) tính từ `runtime_callback.received_at`:
- Trong grace period, `response_body IS NULL` được coi là callback đang xử lý hợp lệ -> không đóng run.
- Quá grace period, row đó được coi là claim mồ côi -> đóng run với `CALLBACK_LOST`, y hệt case
  "không có row nào".

Test backdate `received_at` bằng INSERT trực tiếp thay vì `time.sleep`, để không phụ thuộc thời gian
thật trôi qua trong lúc test chạy.
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from persistence.models import ExecutionRun, WorkflowRelease
from ports.runtime import RuntimeStatus
from services.run_service import RunService

GRACE_SECONDS = 120


class Runtime:
    async def get_status(self, runtime_run_id: str) -> RuntimeStatus:
        return RuntimeStatus("SUCCEEDED", "success")


def _make_run(session) -> ExecutionRun:
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


def _claim(session, run: ExecutionRun, received_at: datetime) -> None:
    session.execute(
        text("INSERT INTO runtime_callback (correlation_id, received_at) VALUES (:id, :received_at)"),
        {"id": run.correlation_id, "received_at": received_at},
    )
    session.commit()


def test_reconcile_leaves_run_running_when_claim_is_within_grace_period(session) -> None:
    run = _make_run(session)
    # Bước 1 của [SD §4.2]: claim vừa xảy ra (received_at = now) -> đang trong grace period, có thể
    # là callback đang xử lý hợp lệ (đang ghi blob lên MinIO / insert artifact_revision).
    _claim(session, run, datetime.now(timezone.utc))

    result = asyncio.run(RunService(session, Runtime(), None, None, "http://api").reconcile(run))

    assert result.status == "RUNNING"
    assert result.error_code is None
    assert session.scalar(text("SELECT count(*) FROM artifact_revision")) == 0


def test_reconcile_closes_run_when_claim_is_older_than_grace_period(session) -> None:
    run = _make_run(session)
    # Claim đã xảy ra lâu hơn grace period -> tiến trình xử lý callback coi như đã chết giữa chừng,
    # đây là "claim mồ côi" mà [ADR-010] lấp gap.
    stale = datetime.now(timezone.utc) - timedelta(seconds=GRACE_SECONDS + 1)
    _claim(session, run, stale)

    result = asyncio.run(RunService(session, Runtime(), None, None, "http://api").reconcile(run))

    assert result.status == "SUCCEEDED"
    assert result.error_code == "CALLBACK_LOST"
    assert session.scalar(text("SELECT count(*) FROM artifact_revision")) == 0


def test_reconcile_closes_run_when_no_callback_row_exists(session) -> None:
    """Hành vi gốc của [SD §4.1] (case 1) — không có row `runtime_callback` nào, giữ nguyên."""
    run = _make_run(session)

    result = asyncio.run(RunService(session, Runtime(), None, None, "http://api").reconcile(run))

    assert result.status == "SUCCEEDED"
    assert result.error_code == "CALLBACK_LOST"
    assert session.scalar(text("SELECT count(*) FROM artifact_revision")) == 0
