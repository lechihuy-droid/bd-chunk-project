from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from persistence.session import get_session
from services.lineage_service import LineageService

router = APIRouter(prefix="/api/vgov", tags=["lineage"])


@router.get("/revisions/{revision_id}/lineage")
def get_lineage(revision_id: UUID, session: Session = Depends(get_session)) -> dict:
    return LineageService(session).get(revision_id)
