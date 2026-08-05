from datetime import datetime, timezone
import uuid

from persistence.models import Artifact, ArtifactRevision, ExecutionRun, RunComponent, RunManifest, WorkflowRelease
from services.lineage_service import LineageService


def test_lineage_returns_manifest_release_prompt_git_and_parent_chain(session) -> None:
    release = WorkflowRelease(
        workflow_id="workflow", release_version="1.0.0", status="PUBLISHED", git_repo="repo", git_ref="HEAD",
        git_commit="a" * 40, entrypoint="graph:build_graph", state_schema_version="v1", bindings={},
        runtime_adapter_id="langgraph", model_profile="model", model_name="model", created_by="test", published_at=datetime.now(timezone.utc),
    )
    input_artifact = Artifact(project_key="project", artifact_type="RD_SOURCE", business_key="RD", display_name="RD")
    output_artifact = Artifact(project_key="project", artifact_type="API_BASIC_DESIGN", business_key="BD", display_name="BD")
    session.add_all([release, input_artifact, output_artifact])
    session.flush()
    rd = ArtifactRevision(artifact_id=input_artifact.id, revision_no=1, origin="IMPORTED", content_hash="sha256:" + "b" * 64,
                          storage_uri="s3://vgov-artifacts/rd.md", mime_type="text/markdown", size_bytes=1, created_by="test")
    run = ExecutionRun(project_key="project", workflow_id="workflow", workflow_release_id=release.id, output_business_key="BD",
                       output_artifact_type="API_BASIC_DESIGN", environment="PROD", execution_mode="ENVIRONMENT", status="SUCCEEDED",
                       correlation_id=uuid.uuid4())
    session.add_all([rd, run])
    session.flush()
    manifest = RunManifest(run_id=run.id, workflow_release_id=release.id, git_repo="repo", git_commit="a" * 40,
                           model_profile="model", runtime_adapter_id="langgraph", environment="PROD",
                           input_source_ref=f"artifact_revision:{rd.id}", input_hash=rd.content_hash,
                           manifest_hash="sha256:" + "c" * 64)
    session.add(manifest)
    session.flush()
    session.add(RunComponent(manifest_id=manifest.id, kind="PROMPT", ref="mlflow://api-bd-generator", exact_version="1", extra={}))
    ai = ArtifactRevision(artifact_id=output_artifact.id, revision_no=1, origin="AI_GENERATED", source_run_id=run.id,
                          content_hash="sha256:" + "d" * 64, storage_uri="s3://vgov-artifacts/ai.md", mime_type="text/markdown", size_bytes=1, created_by="runtime")
    session.add(ai)
    session.flush()
    edited = ArtifactRevision(artifact_id=output_artifact.id, revision_no=2, origin="HUMAN_EDITED", parent_revision_id=ai.id,
                              content_hash="sha256:" + "e" * 64, storage_uri="s3://vgov-artifacts/edit.md", mime_type="text/markdown", size_bytes=1, created_by="human")
    session.add(edited)
    session.commit()

    result = LineageService(session).get(edited.id)
    assert result["parent_chain"][0]["id"] == str(ai.id)
    assert result["run"]["id"] == str(run.id)
    assert result["manifest"]["input_hash"] == rd.content_hash
    assert result["input_revision"]["id"] == str(rd.id)
    assert result["manifest"]["git_commit"] == "a" * 40
    assert result["workflow_release"]["release_version"] == "1.0.0"
    assert result["components"] == [{"kind": "PROMPT", "ref": "mlflow://api-bd-generator", "exact_version": "1"}]
