import re
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domain.release import ReleaseDraft
from ports.source_control import SourceControlPort
from persistence.models import WorkflowRelease
from persistence.repositories import EnvironmentRepository, ReleaseRepository


class ReleaseService:
    def __init__(self, session: Session, source_control: SourceControlPort) -> None:
        self.session = session
        self.releases = ReleaseRepository(session)
        self.environments = EnvironmentRepository(session)
        self.source_control = source_control

    def create_draft(self, draft: ReleaseDraft, actor: str) -> WorkflowRelease:
        release = self.releases.create_draft(draft, actor)
        self.session.commit()
        self.session.refresh(release)
        return release

    def publish(self, release_id: UUID, actor: str) -> WorkflowRelease:
        release = self._release_or_404(release_id)
        if release.status == "PUBLISHED":
            return release
        commit = self.source_control.resolve_commit(release.git_repo, release.git_ref)
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise ValueError("Source control returned a non-commit SHA")
        release.git_commit = commit
        release.status = "PUBLISHED"
        release.published_at = datetime.now(timezone.utc)
        release.published_by = actor
        self.session.commit()
        self.session.refresh(release)
        return release

    def list_releases(self, workflow_id: str | None, status: str | None) -> list[WorkflowRelease]:
        return self.releases.list(workflow_id, status)

    def get_release(self, release_id: UUID) -> WorkflowRelease:
        return self._release_or_404(release_id)

    def environment_releases(self, workflow_id: str) -> dict[str, WorkflowRelease]:
        rows = self.environments.list_for_workflow(workflow_id)
        return {row.environment: self._release_or_404(row.workflow_release_id) for row in rows}

    def set_environment(self, environment: str, workflow_id: str, release_id: UUID, actor: str, reason: str | None):
        release = self._release_or_404(release_id)
        if release.workflow_id != workflow_id:
            raise HTTPException(status_code=422, detail={"code": "VALIDATION_ERROR", "message": "Release belongs to another workflow"})
        if release.status != "PUBLISHED":
            raise HTTPException(status_code=422, detail={"code": "RELEASE_NOT_PUBLISHED", "message": "Environment requires a published release"})
        mapping, audit = self.environments.set_mapping(environment, workflow_id, release_id, actor, reason)
        self.session.commit()
        self.session.refresh(mapping)
        self.session.refresh(audit)
        return mapping, audit

    def environment_audit(self, environment: str, workflow_id: str):
        return self.environments.audit(environment, workflow_id)

    def _release_or_404(self, release_id: UUID) -> WorkflowRelease:
        release = self.releases.get(release_id)
        if release is None:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Release not found"})
        return release
