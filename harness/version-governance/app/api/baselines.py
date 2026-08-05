from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from persistence.session import get_session
from services.baseline_service import BaselineService

router = APIRouter(prefix="/api/vgov", tags=["baselines"])


class CreateBaselineBody(BaseModel):
    artifact_id: UUID
    revision_id: UUID
    scope: str = "default"


def response(baseline) -> dict[str, Any]:
    return {
        "id": str(baseline.id), "artifact_id": str(baseline.artifact_id),
        "revision_id": str(baseline.artifact_revision_id), "scope": baseline.scope,
        "approved_by": baseline.approved_by, "approved_at": baseline.approved_at,
        "superseded_baseline_id": str(baseline.superseded_baseline_id) if baseline.superseded_baseline_id else None,
        "active": baseline.active,
    }


@router.post("/baselines", status_code=201)
def create_baseline(body: CreateBaselineBody, actor: str = Header("local-user", alias="X-Actor"), session: Session = Depends(get_session)) -> dict[str, Any]:
    return response(BaselineService(session).approve(body.artifact_id, body.revision_id, body.scope, actor))


@router.get("/baselines")
def list_baselines(artifact_id: UUID, session: Session = Depends(get_session)) -> list[dict[str, Any]]:
    return [response(row) for row in BaselineService(session).history(artifact_id)]
