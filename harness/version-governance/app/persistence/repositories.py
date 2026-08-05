from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.release import ReleaseDraft
from persistence.models import EnvironmentMapping, EnvironmentMappingAudit, WorkflowRelease


class ReleaseRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_draft(self, draft: ReleaseDraft, actor: str) -> WorkflowRelease:
        row = WorkflowRelease(**draft.__dict__, created_by=actor)
        self.session.add(row)
        self.session.flush()
        return row

    def get(self, release_id: UUID) -> WorkflowRelease | None:
        return self.session.get(WorkflowRelease, release_id)

    def list(self, workflow_id: str | None, status: str | None) -> list[WorkflowRelease]:
        statement = select(WorkflowRelease).order_by(WorkflowRelease.created_at.desc())
        if workflow_id:
            statement = statement.where(WorkflowRelease.workflow_id == workflow_id)
        if status:
            statement = statement.where(WorkflowRelease.status == status)
        return list(self.session.scalars(statement))


class EnvironmentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_workflow(self, workflow_id: str) -> list[EnvironmentMapping]:
        return list(self.session.scalars(select(EnvironmentMapping).where(EnvironmentMapping.workflow_id == workflow_id)))

    def get(self, environment: str, workflow_id: str) -> EnvironmentMapping | None:
        return self.session.scalar(select(EnvironmentMapping).where(EnvironmentMapping.environment == environment, EnvironmentMapping.workflow_id == workflow_id))

    def set_mapping(self, environment: str, workflow_id: str, release_id: UUID, actor: str, reason: str | None) -> tuple[EnvironmentMapping, EnvironmentMappingAudit]:
        mapping = self.get(environment, workflow_id)
        previous = mapping.workflow_release_id if mapping else None
        if mapping is None:
            mapping = EnvironmentMapping(environment=environment, workflow_id=workflow_id, workflow_release_id=release_id, updated_by=actor)
            self.session.add(mapping)
        else:
            mapping.workflow_release_id = release_id
            mapping.updated_by = actor
        audit = EnvironmentMappingAudit(environment=environment, workflow_id=workflow_id, from_release_id=previous, to_release_id=release_id, actor=actor, reason=reason)
        self.session.add(audit)
        self.session.flush()
        return mapping, audit

    def audit(self, environment: str, workflow_id: str) -> list[EnvironmentMappingAudit]:
        return list(self.session.scalars(select(EnvironmentMappingAudit).where(EnvironmentMappingAudit.environment == environment, EnvironmentMappingAudit.workflow_id == workflow_id).order_by(EnvironmentMappingAudit.at.desc())))
