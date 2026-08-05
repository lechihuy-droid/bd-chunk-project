from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, model_validator
from sqlalchemy.orm import Session

from domain.difference import DiffSide
from persistence.session import get_session
from services.difference_service import DifferenceService

router = APIRouter(prefix="/api/vgov", tags=["difference"])


class DiffSideBody(BaseModel):
    run_id: str | None = None
    revision_id: str | None = None

    @model_validator(mode="after")
    def exactly_one_id(self):
        if (self.run_id is None) == (self.revision_id is None):
            raise ValueError("exactly one of run_id or revision_id is required")
        return self


class ExplainDifferenceBody(BaseModel):
    left: DiffSideBody
    right: DiffSideBody


@router.post("/explain-difference")
def explain_difference(body: ExplainDifferenceBody, session: Session = Depends(get_session)) -> dict:
    try:
        return DifferenceService(session).explain(
            DiffSide(**body.left.model_dump()), DiffSide(**body.right.model_dump())
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail={"code": "VALIDATION_ERROR"}) from error
