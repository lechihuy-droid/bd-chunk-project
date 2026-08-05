import json
import uuid
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from domain.difference import DiffSide
from persistence.models import Artifact, ArtifactRevision, ExecutionRun, RunComponent, RunManifest, WorkflowRelease
from services.difference_service import DifferenceService


def build_run(
    session, *, prompt_version: str, input_hash: str, input_ref: str, release: WorkflowRelease,
    model_name: str = "meta/llama-3.1-8b-instruct",
) -> tuple[ExecutionRun, ArtifactRevision]:
    run = ExecutionRun(
        project_key="project", workflow_id="workflow", workflow_release_id=release.id,
        output_business_key="BD-DEMO", output_artifact_type="API_BASIC_DESIGN", environment="PROD",
        execution_mode="ENVIRONMENT", status="SUCCEEDED", correlation_id=uuid.uuid4(),
    )
    session.add(run)
    session.flush()
    manifest = RunManifest(
        run_id=run.id, workflow_release_id=release.id, git_repo="repo", git_commit="a" * 40,
        model_profile="design-accurate@v1", runtime_adapter_id="langgraph", environment="PROD",
        input_source_ref=input_ref, input_hash=input_hash,
        manifest_hash="sha256:" + (prompt_version + input_hash[-1]) * 32,
    )
    session.add(manifest)
    session.flush()
    session.add_all([
        RunComponent(manifest_id=manifest.id, kind="PROMPT", ref="mlflow://api-bd-generator", exact_version=prompt_version, extra={}),
        RunComponent(manifest_id=manifest.id, kind="MODEL", ref="model://design-accurate@v1", exact_version=model_name, extra={}),
        RunComponent(manifest_id=manifest.id, kind="TOOL", ref="rd-reader", exact_version="1.0.0", extra={}),
        RunComponent(manifest_id=manifest.id, kind="AGENT", ref="bd-agent", exact_version="1.0.0", extra={}),
    ])
    artifact = session.scalar(select(Artifact).where(
        Artifact.project_key == "project", Artifact.artifact_type == "API_BASIC_DESIGN", Artifact.business_key == "BD-DEMO"
    ))
    if artifact is None:
        artifact = Artifact(project_key="project", artifact_type="API_BASIC_DESIGN", business_key="BD-DEMO", display_name="BD-DEMO")
        session.add(artifact)
        session.flush()
    revision = ArtifactRevision(
        artifact_id=artifact.id, revision_no=session.query(ArtifactRevision).filter_by(artifact_id=artifact.id).count() + 1,
        origin="AI_GENERATED", source_run_id=run.id, content_hash="sha256:" + uuid.uuid4().hex * 2,
        storage_uri=f"s3://vgov-artifacts/{run.id}.md", mime_type="text/markdown", size_bytes=1, created_by="runtime",
    )
    session.add(revision)
    session.commit()
    return run, revision


@pytest.fixture
def demo(session):
    release = WorkflowRelease(
        workflow_id="workflow", release_version="1.0.0", status="PUBLISHED", git_repo="repo", git_ref="HEAD",
        git_commit="a" * 40, entrypoint="graph:build_graph", state_schema_version="v1", bindings={},
        runtime_adapter_id="langgraph", model_profile="design-accurate@v1", model_name="meta/llama-3.1-8b-instruct", created_by="test",
        published_at=datetime.now(timezone.utc),
    )
    session.add(release)
    session.commit()
    a = build_run(session, prompt_version="1", input_hash="sha256:" + "a" * 64, input_ref="artifact_revision:rd-1", release=release)
    b = build_run(session, prompt_version="2", input_hash="sha256:" + "a" * 64, input_ref="artifact_revision:rd-1", release=release)
    c = build_run(session, prompt_version="2", input_hash="sha256:" + "b" * 64, input_ref="artifact_revision:rd-2", release=release)
    identical = build_run(session, prompt_version="1", input_hash="sha256:" + "a" * 64, input_ref="artifact_revision:rd-1", release=release)
    return a, b, c, identical


def compare(session, left, right):
    return DifferenceService(session).explain(DiffSide(revision_id=str(left.id)), DiffSide(revision_id=str(right.id)))


def test_a_vs_b_only_prompt_changes_and_is_byte_deterministic(session, demo) -> None:
    (_, a), (_, b), _, _ = demo
    first = compare(session, a, b)
    second = compare(session, a, b)
    assert first["verdict"] == "DIFFERENT"
    assert first["changed"] == [{"category": "PROMPT", "facet": "mlflow://api-bd-generator", "from": "1", "to": "2"}]
    assert {row["category"] for row in first["unchanged"]} == {
        "INPUT", "WORKFLOW_RELEASE", "MODEL", "TOOL", "RUNTIME", "HUMAN_EDIT"
    }
    assert json.dumps(first, separators=(",", ":"), sort_keys=False) == json.dumps(second, separators=(",", ":"), sort_keys=False)


def test_a_vs_c_changes_input_and_prompt(session, demo) -> None:
    (_, a), _, (_, c), _ = demo
    result = compare(session, a, c)
    assert {row["category"] for row in result["changed"]} == {"INPUT", "PROMPT"}


def test_model_component_changes_only_when_pinned_model_changes(session, demo) -> None:
    first_run, first = demo[0]
    release = session.get(WorkflowRelease, first_run.workflow_release_id)
    assert release is not None
    _, same_model = build_run(
        session, prompt_version="1", input_hash="sha256:" + "a" * 64,
        input_ref="artifact_revision:rd-1", release=release,
    )
    _, changed_model = build_run(
        session, prompt_version="1", input_hash="sha256:" + "a" * 64,
        input_ref="artifact_revision:rd-1", release=release, model_name="meta/llama-3.3-70b-instruct",
    )

    same = compare(session, first, same_model)
    changed = compare(session, first, changed_model)
    assert not [row for row in same["changed"] if row["category"] == "MODEL"]
    assert [row for row in same["unchanged"] if row["category"] == "MODEL"] == [{
        "category": "MODEL", "facet": "model://design-accurate@v1", "value": "meta/llama-3.1-8b-instruct",
    }]
    assert [row for row in changed["changed"] if row["category"] == "MODEL"] == [{
        "category": "MODEL", "facet": "model://design-accurate@v1",
        "from": "meta/llama-3.1-8b-instruct", "to": "meta/llama-3.3-70b-instruct",
    }]


def test_imported_revision_fails_closed(session) -> None:
    artifact = Artifact(project_key="project", artifact_type="RD_SOURCE", business_key="RD", display_name="RD")
    session.add(artifact)
    session.flush()
    imported = ArtifactRevision(artifact_id=artifact.id, revision_no=1, origin="IMPORTED", content_hash="sha256:" + "a" * 64,
                                storage_uri="s3://vgov-artifacts/rd.md", mime_type="text/markdown", size_bytes=1, created_by="test")
    session.add(imported)
    session.commit()
    with pytest.raises(HTTPException) as error:
        compare(session, imported, imported)
    assert error.value.status_code == 422
    assert error.value.detail["code"] == "NO_MANIFEST_FOR_REVISION"


def test_human_edit_is_detected_and_identical_runs_are_identical(session, demo) -> None:
    (run_a, a), (run_b, b), _, (identical_run, identical_revision) = demo
    next_no = session.query(ArtifactRevision).filter_by(artifact_id=a.artifact_id).count() + 1
    edited = ArtifactRevision(artifact_id=a.artifact_id, revision_no=next_no, origin="HUMAN_EDITED", parent_revision_id=a.id,
                              content_hash="sha256:" + "c" * 64, storage_uri="s3://vgov-artifacts/edit.md",
                              mime_type="text/markdown", size_bytes=1, created_by="human")
    session.add(edited)
    session.commit()
    edit_result = compare(session, edited, a)
    assert {row["category"] for row in edit_result["changed"]} == {"HUMAN_EDIT"}
    same = DifferenceService(session).explain(DiffSide(run_id=str(run_a.id)), DiffSide(run_id=str(identical_run.id)))
    assert same["verdict"] == "IDENTICAL"
    assert same["left"]["manifest_hash"] == same["right"]["manifest_hash"]
    assert run_b.id != run_a.id and b.id != a.id and identical_revision.id != a.id
