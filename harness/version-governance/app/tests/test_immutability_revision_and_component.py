"""NFR-001 / FR-ART-004 / FR-MAN-003 — immutability của `artifact_revision` và `run_component`.

`test_immutability.py` hiện chỉ phủ `workflow_release`. Hai bảng dưới đây cũng có
`trg_block_write()` gắn qua trigger `revision_immutable` / `component_immutable` (`[SD §2.5, §2.6]`)
nhưng chưa có test riêng khẳng định UPDATE/DELETE bị chặn ở tầng DB.
"""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from persistence.models import Artifact, ArtifactRevision, ExecutionRun, RunComponent, RunManifest, WorkflowRelease


def sqlstate(error: DBAPIError) -> str | None:
    return getattr(error.orig, "sqlstate", None) or getattr(error.orig, "pgcode", None)


def test_artifact_revision_content_hash_cannot_be_updated(session) -> None:
    artifact = Artifact(project_key="project", artifact_type="RD_SOURCE", business_key="RD", display_name="RD")
    session.add(artifact)
    session.flush()
    revision = ArtifactRevision(
        artifact_id=artifact.id, revision_no=1, origin="IMPORTED", content_hash="sha256:" + "a" * 64,
        storage_uri="s3://vgov-artifacts/rd.md", mime_type="text/markdown", size_bytes=1, created_by="test",
    )
    session.add(revision)
    session.commit()

    with pytest.raises(DBAPIError) as error:
        session.execute(
            text("UPDATE artifact_revision SET content_hash = :hash WHERE id = :id"),
            {"hash": "sha256:" + "b" * 64, "id": revision.id},
        )
    assert sqlstate(error.value) == "VG409"
    session.rollback()


def test_run_component_cannot_be_deleted(session) -> None:
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
    session.flush()
    component = RunComponent(manifest_id=manifest.id, kind="TOOL", ref="tool-x", exact_version="1.0.0", extra={})
    session.add(component)
    session.commit()

    with pytest.raises(DBAPIError) as error:
        session.execute(text("DELETE FROM run_component WHERE id = :id"), {"id": component.id})
    assert sqlstate(error.value) == "VG409"
    session.rollback()


def test_run_component_cannot_be_updated(session) -> None:
    """Trigger `component_immutable` bọc cả UPDATE lẫn DELETE (`trg_block_write` chặn cả hai)."""
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
    session.flush()
    component = RunComponent(manifest_id=manifest.id, kind="TOOL", ref="tool-x", exact_version="1.0.0", extra={})
    session.add(component)
    session.commit()

    with pytest.raises(DBAPIError) as error:
        session.execute(
            text("UPDATE run_component SET exact_version = '2.0.0' WHERE id = :id"), {"id": component.id}
        )
    assert sqlstate(error.value) == "VG409"
    session.rollback()
