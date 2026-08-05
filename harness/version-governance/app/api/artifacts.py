from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from adapters.minio_blob import MinioBlobAdapter
from config import load_settings
from persistence.models import ApprovedBaseline, Artifact, ArtifactRevision
from persistence.session import get_session
from services.artifact_service import ArtifactService

router = APIRouter(prefix="/api/vgov", tags=["artifacts"])


def artifact_service(session: Session = Depends(get_session)) -> ArtifactService:
    settings = load_settings()
    return ArtifactService(session, MinioBlobAdapter(settings.s3_endpoint, settings.s3_access_key, settings.s3_secret_key))


def revision_response(revision: ArtifactRevision) -> dict[str, Any]:
    return {
        "id": str(revision.id), "artifact_id": str(revision.artifact_id), "revision_no": revision.revision_no,
        "origin": revision.origin, "source_run_id": str(revision.source_run_id) if revision.source_run_id else None,
        "parent_revision_id": str(revision.parent_revision_id) if revision.parent_revision_id else None,
        "content_hash": revision.content_hash, "storage_uri": revision.storage_uri, "mime_type": revision.mime_type,
        "size_bytes": revision.size_bytes, "created_at": revision.created_at, "created_by": revision.created_by,
    }


@router.get("/artifacts")
def list_artifacts(project_key: str, artifact_type: str, session: Session = Depends(get_session)) -> list[dict[str, Any]]:
    artifacts = session.scalars(select(Artifact).where(
        Artifact.project_key == project_key, Artifact.artifact_type == artifact_type
    ).order_by(Artifact.created_at)).all()
    result = []
    for artifact in artifacts:
        baseline = session.scalar(select(ApprovedBaseline).where(
            ApprovedBaseline.artifact_id == artifact.id, ApprovedBaseline.active.is_(True)
        ))
        result.append({
            "id": str(artifact.id), "project_key": artifact.project_key, "artifact_type": artifact.artifact_type,
            "business_key": artifact.business_key, "display_name": artifact.display_name,
            "baseline": {"id": str(baseline.id), "revision_id": str(baseline.artifact_revision_id), "scope": baseline.scope}
            if baseline else None,
        })
    return result


@router.get("/artifacts/{artifact_id}/revisions")
def list_revisions(artifact_id: UUID, session: Session = Depends(get_session)) -> list[dict[str, Any]]:
    return [revision_response(row) for row in session.scalars(select(ArtifactRevision).where(
        ArtifactRevision.artifact_id == artifact_id
    ).order_by(ArtifactRevision.revision_no))]


@router.get("/revisions/{revision_id}")
def get_revision(revision_id: UUID, session: Session = Depends(get_session)) -> dict[str, Any]:
    revision = session.get(ArtifactRevision, revision_id)
    if revision is None:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
    return revision_response(revision)


@router.get("/revisions/{revision_id}/content")
def get_content(revision_id: UUID, service: ArtifactService = Depends(artifact_service)) -> StreamingResponse:
    revision = service.session.get(ArtifactRevision, revision_id)
    if revision is None:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
    return StreamingResponse(iter((service.content(revision),)), media_type=revision.mime_type)


class EditBody(BaseModel):
    content: str
    mime_type: str = "text/markdown"


@router.post("/revisions/{revision_id}/edit", status_code=201)
def edit_revision(revision_id: UUID, body: EditBody, actor: str = Header("local-user", alias="X-Actor"), service: ArtifactService = Depends(artifact_service)) -> dict[str, Any]:
    revision = service.edit(revision_id, body.content, body.mime_type, actor)
    service.session.commit()
    service.session.refresh(revision)
    return revision_response(revision)
