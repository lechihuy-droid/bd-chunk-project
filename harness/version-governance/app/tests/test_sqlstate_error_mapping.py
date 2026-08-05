"""SD §2.8 — Error code mapping ở tầng dữ liệu (chưa có test trực tiếp trước đây).

`errors.SQLSTATE_ERRORS` là bảng nguồn cho `install_error_handlers()` (dùng bởi FastAPI exception
handler) và cho `RunService._precondition_code()`. Test này gọi trực tiếp bảng đó — không dựng HTTP —
và chứng minh mỗi SQLSTATE trong `[SD §2.8]` thật sự phát sinh từ đúng loại vi phạm được mô tả:

| SQLSTATE | Nguồn                              | HTTP | code              |
|----------|-------------------------------------|------|-------------------|
| 23514    | CHECK constraint (`ck_no_alias`)    | 422  | VALIDATION_ERROR  |
| 23505    | unique violation (`uq_revision`)    | 409  | CONFLICT          |
| VG409    | trigger immutability (`trg_block_write`) | 409 | IMMUTABLE_OBJECT |
"""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

import errors
from persistence.models import Artifact, ArtifactRevision, ExecutionRun, RunManifest, WorkflowRelease


def sqlstate(error: DBAPIError) -> str | None:
    return getattr(error.orig, "sqlstate", None) or getattr(error.orig, "pgcode", None)


def _manifest(session) -> RunManifest:
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
        status="MANIFEST_FROZEN", correlation_id=uuid.uuid4(),
    )
    session.add(run)
    session.flush()
    manifest = RunManifest(
        run_id=run.id, workflow_release_id=release.id, git_repo="repo", git_commit="a" * 40,
        model_profile="model", runtime_adapter_id="langgraph", environment="PROD",
        input_source_ref="artifact_revision:x", input_hash="sha256:" + "a" * 64,
        manifest_hash="sha256:" + "b" * 64,
    )
    session.add(manifest)
    session.commit()
    return manifest


def test_ck_no_alias_check_violation_reports_sqlstate_23514(session) -> None:
    manifest = _manifest(session)
    with pytest.raises(DBAPIError) as error:
        session.execute(
            text(
                "INSERT INTO run_component (manifest_id, kind, ref, exact_version) "
                "VALUES (:manifest_id, 'TOOL', 'rd-reader', 'production')"
            ),
            {"manifest_id": manifest.id},
        )
    assert sqlstate(error.value) == "23514"
    session.rollback()
    assert errors.SQLSTATE_ERRORS["23514"] == (422, "VALIDATION_ERROR")


def test_uq_revision_unique_violation_reports_sqlstate_23505(session) -> None:
    artifact = Artifact(project_key="project", artifact_type="RD_SOURCE", business_key="RD", display_name="RD")
    session.add(artifact)
    session.flush()
    first = ArtifactRevision(
        artifact_id=artifact.id, revision_no=1, origin="IMPORTED", content_hash="sha256:" + "a" * 64,
        storage_uri="s3://vgov-artifacts/rd-1.md", mime_type="text/markdown", size_bytes=1, created_by="test",
    )
    session.add(first)
    session.commit()

    # Vi phạm uq_revision(artifact_id, revision_no) một cách chủ ý: hai row cùng revision_no=1 trên
    # cùng một artifact vừa tạo — không phải giả định về revision_no do service khác tính ra.
    duplicate = ArtifactRevision(
        artifact_id=artifact.id, revision_no=1, origin="IMPORTED", content_hash="sha256:" + "b" * 64,
        storage_uri="s3://vgov-artifacts/rd-1-dup.md", mime_type="text/markdown", size_bytes=1, created_by="test",
    )
    session.add(duplicate)
    with pytest.raises(DBAPIError) as error:
        session.commit()
    assert sqlstate(error.value) == "23505"
    session.rollback()
    assert errors.SQLSTATE_ERRORS["23505"] == (409, "CONFLICT")


def test_trigger_immutability_reports_sqlstate_vg409(session) -> None:
    manifest = _manifest(session)
    with pytest.raises(DBAPIError) as error:
        session.execute(text("UPDATE run_manifest SET model_profile = 'changed' WHERE id = :id"), {"id": manifest.id})
    assert sqlstate(error.value) == "VG409"
    session.rollback()
    assert errors.SQLSTATE_ERRORS["VG409"] == (409, "IMMUTABLE_OBJECT")


def test_sqlstate_mapping_table_matches_sd_section_2_8() -> None:
    assert errors.SQLSTATE_ERRORS == {
        "VG409": (409, "IMMUTABLE_OBJECT"),
        "23514": (422, "VALIDATION_ERROR"),
        "23505": (409, "CONFLICT"),
    }
