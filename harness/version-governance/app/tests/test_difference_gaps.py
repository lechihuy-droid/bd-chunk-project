"""FR-DIF §5 — case chưa được `test_difference.py` phủ.

1. Hai revision thuộc hai artifact khác nhau vẫn so được (`[SD §5.1]`): "so hai output" là hợp lệ,
   response phải ghi rõ `artifact_id` mỗi bên để người đọc không nhầm là cùng artifact.
2. Facet có ở một bên, thiếu bên kia (`[SD §5.2]` bước 4): phải xuất hiện trong `changed` với giá trị
   thiếu là `None` — không được bỏ qua âm thầm vì `_component_facets` chỉ liệt kê những gì thực sự có.
3. Thứ tự category trong `changed` đúng thứ tự cố định `[SD §5.2]` bước 6:
   INPUT, WORKFLOW_RELEASE, PROMPT, MODEL, TOOL, RUNTIME, HUMAN_EDIT.
"""

import uuid
from datetime import datetime, timezone

from persistence.models import Artifact, ArtifactRevision, ExecutionRun, RunComponent, RunManifest, WorkflowRelease
from domain.difference import DiffSide
from services.difference_service import DifferenceService


def _release(session, **overrides) -> WorkflowRelease:
    defaults = dict(
        workflow_id="workflow", release_version="1.0.0", status="PUBLISHED", git_repo="repo", git_ref="HEAD",
        git_commit="a" * 40, entrypoint="graph:build_graph", state_schema_version="v1", bindings={},
        runtime_adapter_id="langgraph", model_profile="design-accurate@v1", model_name="meta/llama-3.1-8b-instruct", created_by="test",
        published_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    release = WorkflowRelease(**defaults)
    session.add(release)
    session.commit()
    return release


def _make_run(
    session, *, release: WorkflowRelease, business_key: str, input_hash: str, input_ref: str,
    model_profile: str = "design-accurate@v1", runtime_adapter_id: str = "langgraph", environment: str = "PROD",
    prompt_version: str = "1", tool_version: str = "1.0.0", include_tool: bool = True,
) -> tuple[ExecutionRun, ArtifactRevision]:
    run = ExecutionRun(
        project_key="project", workflow_id=release.workflow_id, workflow_release_id=release.id,
        output_business_key=business_key, output_artifact_type="API_BASIC_DESIGN", environment=environment,
        execution_mode="ENVIRONMENT", status="SUCCEEDED", correlation_id=uuid.uuid4(),
    )
    session.add(run)
    session.flush()
    manifest = RunManifest(
        run_id=run.id, workflow_release_id=release.id, git_repo=release.git_repo, git_commit=release.git_commit,
        model_profile=model_profile, runtime_adapter_id=runtime_adapter_id, environment=environment,
        input_source_ref=input_ref, input_hash=input_hash, manifest_hash="sha256:" + uuid.uuid4().hex * 2,
    )
    session.add(manifest)
    session.flush()
    components = [
        RunComponent(manifest_id=manifest.id, kind="PROMPT", ref="mlflow://shared-prompt", exact_version=prompt_version, extra={}),
        RunComponent(manifest_id=manifest.id, kind="MODEL", ref=f"model://{model_profile}", exact_version=f"{model_profile}-resolved", extra={}),
    ]
    if include_tool:
        components.append(RunComponent(manifest_id=manifest.id, kind="TOOL", ref="tool-x", exact_version=tool_version, extra={}))
    session.add_all(components)
    artifact = Artifact(project_key="project", artifact_type="API_BASIC_DESIGN", business_key=business_key, display_name=business_key)
    session.add(artifact)
    session.flush()
    revision = ArtifactRevision(
        artifact_id=artifact.id, revision_no=1, origin="AI_GENERATED", source_run_id=run.id,
        content_hash="sha256:" + uuid.uuid4().hex * 2, storage_uri=f"s3://vgov-artifacts/{run.id}.md",
        mime_type="text/markdown", size_bytes=1, created_by="runtime",
    )
    session.add(revision)
    session.commit()
    return run, revision


def test_two_different_artifacts_are_still_comparable_and_marked_not_same_artifact(session) -> None:
    release = _release(session)
    _, revision_a = _make_run(session, release=release, business_key="BD-A", input_hash="sha256:" + "a" * 64, input_ref="artifact_revision:rd-a")
    _, revision_b = _make_run(session, release=release, business_key="BD-B", input_hash="sha256:" + "a" * 64, input_ref="artifact_revision:rd-a")

    result = DifferenceService(session).explain(DiffSide(revision_id=str(revision_a.id)), DiffSide(revision_id=str(revision_b.id)))

    assert result["same_artifact"] is False
    assert result["left"]["artifact_id"] != result["right"]["artifact_id"]
    assert result["left"]["artifact_id"] == str(revision_a.artifact_id)
    assert result["right"]["artifact_id"] == str(revision_b.artifact_id)


def test_facet_missing_on_one_side_appears_in_changed_as_null_not_silently_dropped(session) -> None:
    release = _release(session)
    _, without_tool = _make_run(
        session, release=release, business_key="BD-NO-TOOL", input_hash="sha256:" + "a" * 64,
        input_ref="artifact_revision:rd-a", include_tool=False,
    )
    _, with_tool = _make_run(
        session, release=release, business_key="BD-WITH-TOOL", input_hash="sha256:" + "a" * 64,
        input_ref="artifact_revision:rd-a", include_tool=True,
    )

    result = DifferenceService(session).explain(DiffSide(revision_id=str(without_tool.id)), DiffSide(revision_id=str(with_tool.id)))

    tool_rows = [row for row in result["changed"] if row["category"] == "TOOL" and row["facet"] == "tool-x"]
    assert tool_rows == [{"category": "TOOL", "facet": "tool-x", "from": None, "to": "1.0.0"}]


def test_category_order_in_changed_output_follows_the_fixed_spec_order(session) -> None:
    release_left = _release(session, release_version="1.0.0", entrypoint="graph:left", state_schema_version="v1", git_commit="a" * 40)
    release_right = _release(session, release_version="2.0.0", entrypoint="graph:right", state_schema_version="v2", git_commit="b" * 40)

    _, revision_left = _make_run(
        session, release=release_left, business_key="BD-ORDER-LEFT", model_profile="left-model",
        runtime_adapter_id="langgraph", environment="DEV", input_hash="sha256:" + "a" * 64,
        input_ref="artifact_revision:left", prompt_version="1", tool_version="1.0.0",
    )
    _, revision_right = _make_run(
        session, release=release_right, business_key="BD-ORDER-RIGHT", model_profile="right-model",
        runtime_adapter_id="custom-adapter", environment="PROD", input_hash="sha256:" + "b" * 64,
        input_ref="artifact_revision:right", prompt_version="2", tool_version="2.0.0",
    )
    # HUMAN_EDIT chỉ khác biệt khi so bằng revision_id và một bên đi qua chuỗi HUMAN_EDITED
    # (DiffSide theo run_id luôn human_edit=False — [SD §5.1]).
    next_no = session.query(ArtifactRevision).filter_by(artifact_id=revision_left.artifact_id).count() + 1
    edited = ArtifactRevision(
        artifact_id=revision_left.artifact_id, revision_no=next_no, origin="HUMAN_EDITED",
        parent_revision_id=revision_left.id, content_hash="sha256:" + "c" * 64,
        storage_uri="s3://vgov-artifacts/edited.md", mime_type="text/markdown", size_bytes=1, created_by="human",
    )
    session.add(edited)
    session.commit()

    result = DifferenceService(session).explain(DiffSide(revision_id=str(edited.id)), DiffSide(revision_id=str(revision_right.id)))

    expected_order = ["INPUT", "WORKFLOW_RELEASE", "PROMPT", "MODEL", "TOOL", "RUNTIME", "HUMAN_EDIT"]
    # Mỗi category có thể góp nhiều facet (vd RUNTIME có 2), nên category có thể lặp liên tiếp trong
    # `changed` — dedupe giữ thứ tự xuất hiện đầu tiên để so với thứ tự category cố định.
    observed_order = list(dict.fromkeys(row["category"] for row in result["changed"]))
    assert observed_order == expected_order
