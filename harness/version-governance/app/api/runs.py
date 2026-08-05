from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from adapters.git_source import GitSourceAdapter
from adapters.langgraph_runtime import LangGraphRuntimeAdapter
from adapters.mlflow_prompt import MlflowPromptAdapter
from adapters.minio_blob import MinioBlobAdapter
from config import load_settings
from domain.run import RunRequest
from persistence.models import Artifact, ArtifactRevision, ExecutionRun, RunComponent, RunManifest
from persistence.session import get_session
from domain.artifact import ArtifactIdentity
from services.artifact_service import ArtifactService
from services.run_service import RunService

router = APIRouter(prefix="/api/vgov", tags=["runs"])


def service(session: Session = Depends(get_session)) -> RunService:
    settings = load_settings()
    return RunService(
        session=session,
        runtime=LangGraphRuntimeAdapter(settings.runtime_base_url),
        prompts=MlflowPromptAdapter(),
        source=GitSourceAdapter(settings.git_repo_path),
        callback_base_url=settings.callback_base_url,
        blobs=MinioBlobAdapter(settings.s3_endpoint, settings.s3_access_key, settings.s3_secret_key),
        callback_grace_seconds=settings.callback_grace_seconds,
    )


def run_response(run: ExecutionRun) -> dict[str, Any]:
    return {
        "id": str(run.id),
        "status": run.status,
        "correlation_id": str(run.correlation_id),
        "runtime_run_id": run.runtime_run_id,
        "trace_id": run.trace_id,
        "error_code": run.error_code,
        "completed_at": run.completed_at,
    }


class StartBody(BaseModel):
    project_key: str
    workflow_id: str
    input_revision_id: UUID
    output_business_key: str
    output_artifact_type: str = "API_BASIC_DESIGN"
    environment: str | None = "PROD"
    release_id: UUID | None = None


@router.post("/inputs", status_code=201)
async def upload_input(
    project_key: str = Form(...),
    business_key: str = Form(...),
    file: UploadFile = File(...),
    actor: str = Header("local-user", alias="X-Actor"),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    data = await file.read()
    settings = load_settings()
    revision = ArtifactService(
        session, MinioBlobAdapter(settings.s3_endpoint, settings.s3_access_key, settings.s3_secret_key)
    ).create_imported(
        ArtifactIdentity(project_key, "RD_SOURCE", business_key), data, file.content_type or "text/plain",
        actor, file.filename or business_key,
    )
    session.commit()
    session.refresh(revision)
    return {
        "id": str(revision.id),
        "revision_no": revision.revision_no,
        "content_hash": revision.content_hash,
    }


@router.post("/runs", status_code=201)
async def start_run(
    body: StartBody,
    run_service: RunService = Depends(service),
) -> dict[str, Any]:
    return run_response(await run_service.start(RunRequest(**body.model_dump())))


@router.get("/inputs")
def list_inputs(
    project_key: str,
    session: Session = Depends(get_session),
) -> list[dict[str, Any]]:
    rows = session.execute(
        select(ArtifactRevision, Artifact)
        .join(Artifact, Artifact.id == ArtifactRevision.artifact_id)
        .where(Artifact.project_key == project_key, Artifact.artifact_type == "RD_SOURCE")
        .order_by(ArtifactRevision.created_at)
    )
    return [
        {
            "id": str(revision.id),
            "business_key": artifact.business_key,
            "revision_no": revision.revision_no,
            "content_hash": revision.content_hash,
        }
        for revision, artifact in rows
    ]


@router.get("/runs")
def list_runs(
    project_key: str,
    workflow_id: str | None = None,
    session: Session = Depends(get_session),
) -> list[dict[str, Any]]:
    """SD §6. Không reconcile ở đây — reconcile chỉ chạy ở GET /runs/{id} để một lần liệt kê
    không kéo theo N lần gọi runtime."""
    statement = (
        select(ExecutionRun)
        .where(ExecutionRun.project_key == project_key)
        .order_by(ExecutionRun.created_at.desc())
    )
    if workflow_id:
        statement = statement.where(ExecutionRun.workflow_id == workflow_id)
    return [run_response(run) for run in session.scalars(statement)]


@router.get("/runs/{run_id}")
async def get_run(
    run_id: UUID,
    run_service: RunService = Depends(service),
) -> dict[str, Any]:
    run = run_service.session.get(ExecutionRun, run_id)
    if run is None:
        raise HTTPException(status_code=404)
    return run_response(await run_service.reconcile(run))


@router.post("/runs/{run_id}/callback")
async def callback(
    run_id: UUID,
    body: dict[str, Any],
    run_service: RunService = Depends(service),
) -> dict[str, Any]:
    return await run_service.callback(run_id, body)


@router.get("/runs/{run_id}/manifest")
def get_manifest(run_id: UUID, session: Session = Depends(get_session)) -> dict[str, Any]:
    manifest = session.scalar(select(RunManifest).where(RunManifest.run_id == run_id))
    if manifest is None:
        raise HTTPException(status_code=404)
    components = session.scalars(
        select(RunComponent).where(RunComponent.manifest_id == manifest.id)
    )
    return {
        "id": str(manifest.id),
        "manifest_hash": manifest.manifest_hash,
        "components": [
            {
                "kind": component.kind,
                "ref": component.ref,
                "exact_version": component.exact_version,
            }
            for component in components
        ],
    }
