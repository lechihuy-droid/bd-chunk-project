from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from adapters.git_source import GitSourceAdapter
from config import load_settings
from domain.release import ReleaseDraft
from persistence.session import get_session
from services.release_service import ReleaseService

router = APIRouter(prefix="/api/vgov/releases", tags=["releases"])


class CreateReleaseBody(BaseModel):
    workflow_id: str
    release_version: str
    git_repo: str
    git_ref: str
    entrypoint: str
    state_schema_version: str
    bindings: dict[str, Any]
    runtime_adapter_id: str
    model_profile: str
    model_name: str


def service(session: Session = Depends(get_session)) -> ReleaseService:
    return ReleaseService(session, GitSourceAdapter(load_settings().git_repo_path))


def release_response(release) -> dict[str, Any]:
    return {
        "id": str(release.id), "workflow_id": release.workflow_id,
        "release_version": release.release_version, "status": release.status,
        "git_repo": release.git_repo, "git_ref": release.git_ref,
        "git_commit": release.git_commit, "entrypoint": release.entrypoint,
        "state_schema_version": release.state_schema_version, "bindings": release.bindings,
        "runtime_adapter_id": release.runtime_adapter_id, "model_profile": release.model_profile,
        "model_name": release.model_name,
        "created_at": release.created_at, "created_by": release.created_by,
        "published_at": release.published_at, "published_by": release.published_by,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_release(body: CreateReleaseBody, actor: str = Header("local-user", alias="X-Actor"), svc: ReleaseService = Depends(service)):
    return release_response(svc.create_draft(ReleaseDraft(**body.model_dump()), actor))


@router.post("/{release_id}/publish")
def publish_release(release_id: UUID, actor: str = Header("local-user", alias="X-Actor"), svc: ReleaseService = Depends(service)):
    return release_response(svc.publish(release_id, actor))


@router.get("")
def list_releases(workflow_id: str | None = None, status: str | None = None, svc: ReleaseService = Depends(service)):
    return [release_response(release) for release in svc.list_releases(workflow_id, status)]


@router.get("/{release_id}")
def get_release(release_id: UUID, svc: ReleaseService = Depends(service)):
    return release_response(svc.get_release(release_id))
