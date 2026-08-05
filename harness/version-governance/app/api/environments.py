from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.releases import release_response
from adapters.git_source import GitSourceAdapter
from config import load_settings
from persistence.session import get_session
from services.release_service import ReleaseService

router = APIRouter(prefix="/api/vgov/environments", tags=["environments"])


class SetEnvironmentBody(BaseModel):
    workflow_id: str
    release_id: UUID
    reason: str | None = None


def service(session: Session = Depends(get_session)) -> ReleaseService:
    return ReleaseService(session, GitSourceAdapter(load_settings().git_repo_path))


def mapping_response(mapping) -> dict[str, Any]:
    return {"environment": mapping.environment, "workflow_id": mapping.workflow_id, "release_id": str(mapping.workflow_release_id), "updated_at": mapping.updated_at, "updated_by": mapping.updated_by}


def audit_response(audit) -> dict[str, Any]:
    return {"environment": audit.environment, "workflow_id": audit.workflow_id, "from_release_id": str(audit.from_release_id) if audit.from_release_id else None, "to_release_id": str(audit.to_release_id), "actor": audit.actor, "reason": audit.reason, "at": audit.at}


@router.get("")
def list_environments(workflow_id: str, svc: ReleaseService = Depends(service)):
    return {environment: release_response(release) for environment, release in svc.environment_releases(workflow_id).items()}


@router.put("/{environment}")
def set_environment(environment: str, body: SetEnvironmentBody, actor: str = Header("local-user", alias="X-Actor"), svc: ReleaseService = Depends(service)):
    if environment not in {"DEV", "PROD"}:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail={"code": "VALIDATION_ERROR", "message": "Unknown environment"})
    mapping, audit = svc.set_environment(environment, body.workflow_id, body.release_id, actor, body.reason)
    return {"mapping": mapping_response(mapping), "audit": audit_response(audit)}


@router.get("/{environment}/audit")
def environment_audit(environment: str, workflow_id: str, svc: ReleaseService = Depends(service)):
    return [audit_response(audit) for audit in svc.environment_audit(environment, workflow_id)]
