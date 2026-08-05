"""FR-MAN-004 / SD §2.5: nhiều node cùng khai một component (kind, ref).

Trước khi có `RunService._dedupe()`, hai node khai cùng `tool_refs` (kể cả cùng version) làm
`self.session.add(RunComponent(...))` được gọi hai lần cho cùng `(manifest_id, kind, ref)` — vi phạm
`uq_component` ngay ở lần INSERT thứ hai. Vi phạm đó ném `IntegrityError`, bị `except Exception` ở
`RunService.start()` nuốt và (trước sửa) rò ra `error_code` là chuỗi lỗi SQL thô thay vì mã ổn định.

Các test dưới đây chốt hai case theo đúng `[SD §2.5]`:
- cùng ref + cùng version -> dedupe, chỉ một hàng `run_component`.
- cùng ref + khác version -> mâu thuẫn thật, fail closed trước khi chạm DB.
"""

import asyncio
import re
import uuid
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi import HTTPException
from sqlalchemy import select, text

from domain.run import RunRequest
from persistence.models import Artifact, ArtifactRevision, RunComponent, RunManifest, WorkflowRelease
from ports.runtime import RuntimeHandle, RuntimeStatus
from services.run_service import RunService


class BlobFake:
    def get(self, uri: str) -> bytes:
        return b"RD"

    def put_immutable(self, **kwargs: Any) -> None:
        raise AssertionError("not used")

    def exists(self, key: str) -> bool:
        return False


class SourceFake:
    def commit_exists(self, repo: str, sha: str) -> bool:
        return True


class RuntimeFake:
    def __init__(self) -> None:
        self.request = None

    async def start(self, request: Any) -> RuntimeHandle:
        self.request = request
        return RuntimeHandle("langgraph", "runtime-1", None, RuntimeStatus("PENDING", "pending"))


def _release(bindings: dict[str, Any]) -> WorkflowRelease:
    return WorkflowRelease(
        workflow_id="workflow", release_version="1.0.0", status="PUBLISHED", git_repo="repo", git_ref="HEAD",
        git_commit="a" * 40, entrypoint="graph:build_graph", state_schema_version="v1", bindings=bindings,
        runtime_adapter_id="langgraph", model_profile="model", model_name="model", created_by="test", published_at=datetime.now(timezone.utc),
    )


def _seed_input(session, tmp_path) -> ArtifactRevision:
    artifact = Artifact(project_key="project", artifact_type="RD_SOURCE", business_key="RD", display_name="RD")
    session.add(artifact)
    session.flush()
    (tmp_path / "rd.md").write_text("RD", encoding="utf-8")
    revision = ArtifactRevision(
        artifact_id=artifact.id, revision_no=1, origin="IMPORTED", content_hash="sha256:" + "b" * 64,
        storage_uri="s3://vgov-artifacts/project/RD_SOURCE/RD/test.md", mime_type="text/markdown", size_bytes=2,
        created_by="test",
    )
    session.add(revision)
    session.commit()
    return revision


def test_same_tool_declared_on_two_nodes_with_identical_version_is_deduped(session, tmp_path) -> None:
    release = _release({
        "node_a": {"tool_refs": {"rd-reader": "1.0.0"}},
        "node_b": {"tool_refs": {"rd-reader": "1.0.0"}},
    })
    session.add(release)
    session.commit()
    revision = _seed_input(session, tmp_path)

    service = RunService(session, RuntimeFake(), None, SourceFake(), "http://api", BlobFake())
    run = asyncio.run(service.start(RunRequest("project", "workflow", revision.id, "OUT", release_id=release.id)))

    assert run.status == "RUNNING"
    manifest = session.scalar(select(RunManifest).where(RunManifest.run_id == run.id))
    tool_rows = list(session.scalars(
        select(RunComponent).where(
            RunComponent.manifest_id == manifest.id, RunComponent.kind == "TOOL", RunComponent.ref == "rd-reader"
        )
    ))
    assert len(tool_rows) == 1
    assert tool_rows[0].exact_version == "1.0.0"


def test_model_profile_and_pinned_model_are_frozen_separately(session, tmp_path) -> None:
    release = _release({})
    release.model_profile = "design-accurate@v1"
    release.model_name = "meta/llama-3.1-8b-instruct"
    session.add(release)
    session.commit()
    revision = _seed_input(session, tmp_path)
    runtime = RuntimeFake()

    run = asyncio.run(
        RunService(session, runtime, None, SourceFake(), "http://api", BlobFake()).start(
            RunRequest("project", "workflow", revision.id, "OUT", release_id=release.id)
        )
    )

    manifest = session.scalar(select(RunManifest).where(RunManifest.run_id == run.id))
    model = session.scalar(
        select(RunComponent).where(
            RunComponent.manifest_id == manifest.id,
            RunComponent.kind == "MODEL",
        )
    )
    assert manifest.model_profile == "design-accurate@v1"
    assert model.ref == "model://design-accurate@v1"
    assert model.exact_version == "meta/llama-3.1-8b-instruct"
    assert runtime.request.model_profile == "design-accurate@v1"
    assert runtime.request.model_name == "meta/llama-3.1-8b-instruct"


def test_same_tool_declared_on_two_nodes_with_conflicting_version_fails_closed(session, tmp_path) -> None:
    release = _release({
        "node_a": {"tool_refs": {"rd-reader": "1.0.0"}},
        "node_b": {"tool_refs": {"rd-reader": "2.0.0"}},
    })
    session.add(release)
    session.commit()
    revision = _seed_input(session, tmp_path)

    service = RunService(session, RuntimeFake(), None, SourceFake(), "http://api", BlobFake())
    with pytest.raises(HTTPException) as error:
        asyncio.run(service.start(RunRequest("project", "workflow", revision.id, "OUT", release_id=release.id)))

    assert error.value.status_code == 422
    assert session.scalar(text("SELECT count(*) FROM run_manifest")) == 0
    assert session.scalar(text("SELECT status FROM execution_run")) == "FAILED_PRECONDITION"
    error_code = session.scalar(text("SELECT error_code FROM execution_run"))
    assert error_code.startswith("CONFLICTING_COMPONENT_VERSION")
    assert error.value.detail["code"] == error_code


def test_precondition_error_code_never_leaks_raw_sql(session, tmp_path) -> None:
    """error_code phải luôn là mã ổn định, không bao giờ là chuỗi lỗi SQL/driver thô.

    Đây là chính lỗi #2 đã tìm thấy: IntegrityError của uq_component bị nuốt và error_code trở
    thành text của exception gốc (chứa tên bảng, câu SQL, tên driver). `_dedupe()` chặn case dedupe
    được, còn case mâu thuẫn thật vẫn phải trả về mã sạch — không phải rò rỉ nội bộ DB.
    """
    release = _release({
        "node_a": {"tool_refs": {"rd-reader": "1.0.0"}},
        "node_b": {"tool_refs": {"rd-reader": "2.0.0"}},
    })
    session.add(release)
    session.commit()
    revision = _seed_input(session, tmp_path)

    service = RunService(session, RuntimeFake(), None, SourceFake(), "http://api", BlobFake())
    with pytest.raises(HTTPException):
        asyncio.run(service.start(RunRequest("project", "workflow", revision.id, "OUT", release_id=release.id)))

    error_code = session.scalar(text("SELECT error_code FROM execution_run"))
    assert re.fullmatch(r"[A-Z_:./@a-z0-9-]+", error_code), error_code
    assert "SELECT" not in error_code
    assert "INSERT" not in error_code
    assert "psycopg" not in error_code


def test_missing_pinned_release_and_environment_mapping_have_distinct_codes(session) -> None:
    service = RunService(session, RuntimeFake(), None, SourceFake(), "http://api", BlobFake())

    with pytest.raises(HTTPException) as missing_release:
        asyncio.run(service.start(RunRequest("project", "workflow", uuid.uuid4(), "OUT", release_id=uuid.uuid4())))
    with pytest.raises(HTTPException) as missing_environment:
        asyncio.run(service.start(RunRequest("project", "workflow", uuid.uuid4(), "OUT")))

    assert missing_release.value.detail["code"] == "RELEASE_NOT_FOUND"
    assert missing_environment.value.detail["code"] == "NO_RELEASE_FOR_ENVIRONMENT"
    failed = list(session.scalars(select(WorkflowRelease)))
    assert failed == []
    error_codes = list(session.scalars(text("SELECT error_code FROM execution_run")))
    statuses = list(session.scalars(text("SELECT status::text FROM execution_run")))
    assert set(error_codes) == {"RELEASE_NOT_FOUND", "NO_RELEASE_FOR_ENVIRONMENT"}
    assert statuses == ["FAILED_PRECONDITION", "FAILED_PRECONDITION"]
