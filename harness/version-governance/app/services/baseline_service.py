import uuid

from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from persistence.models import ApprovedBaseline, ArtifactRevision


class BaselineService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def approve(self, artifact_id: uuid.UUID, revision_id: uuid.UUID, scope: str, actor: str) -> ApprovedBaseline:
        revision = self.session.get(ArtifactRevision, revision_id)
        if revision is None or revision.artifact_id != artifact_id:
            raise HTTPException(status_code=422, detail={"code": "VALIDATION_ERROR", "message": "revision does not belong to artifact"})
        old = self.session.scalar(select(ApprovedBaseline).where(
            ApprovedBaseline.artifact_id == artifact_id, ApprovedBaseline.scope == scope, ApprovedBaseline.active.is_(True)
        ).with_for_update())
        if old is not None:
            old.active = False
            self.session.flush()
        baseline = ApprovedBaseline(
            artifact_id=artifact_id, artifact_revision_id=revision_id, scope=scope, approved_by=actor,
            superseded_baseline_id=old.id if old else None, active=True,
        )
        self.session.add(baseline)
        self.session.commit()
        self.session.refresh(baseline)
        return baseline

    def history(self, artifact_id: uuid.UUID) -> list[ApprovedBaseline]:
        return list(self.session.scalars(select(ApprovedBaseline).where(
            ApprovedBaseline.artifact_id == artifact_id
        ).order_by(ApprovedBaseline.approved_at.desc())))
