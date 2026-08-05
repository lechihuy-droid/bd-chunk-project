from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from persistence.models import ArtifactRevision, ExecutionRun, RunComponent, RunManifest, WorkflowRelease


class LineageService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, revision_id: UUID) -> dict[str, Any]:
        revision = self.session.get(ArtifactRevision, revision_id)
        if revision is None:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})

        parents = self._parent_chain(revision)
        source = revision if revision.origin == "AI_GENERATED" else next(
            (parent for parent in parents if parent.origin == "AI_GENERATED"), None
        )
        if source is None or source.source_run_id is None:
            return self._response(revision, parents, None, None, None, [])

        row = self.session.execute(
            select(ExecutionRun, RunManifest, WorkflowRelease)
            .join(RunManifest, RunManifest.run_id == ExecutionRun.id)
            .join(WorkflowRelease, WorkflowRelease.id == RunManifest.workflow_release_id)
            .where(ExecutionRun.id == source.source_run_id)
        ).one_or_none()
        if row is None:
            return self._response(revision, parents, None, None, None, [])
        run, manifest, release = row
        components = list(self.session.scalars(
            select(RunComponent).where(RunComponent.manifest_id == manifest.id)
            .order_by(RunComponent.kind, RunComponent.ref)
        ))
        return self._response(revision, parents, run, manifest, release, components)

    def _parent_chain(self, revision: ArtifactRevision) -> list[ArtifactRevision]:
        chain: list[ArtifactRevision] = []
        current = revision
        while current.parent_revision_id is not None:
            parent = self.session.get(ArtifactRevision, current.parent_revision_id)
            if parent is None:
                break
            chain.append(parent)
            current = parent
        return chain

    @staticmethod
    def _revision(row: ArtifactRevision) -> dict[str, Any]:
        return {
            "id": str(row.id), "artifact_id": str(row.artifact_id), "revision_no": row.revision_no,
            "origin": row.origin, "source_run_id": str(row.source_run_id) if row.source_run_id else None,
            "parent_revision_id": str(row.parent_revision_id) if row.parent_revision_id else None,
            "content_hash": row.content_hash,
        }

    def _response(self, revision, parents, run, manifest, release, components) -> dict[str, Any]:
        input_revision = self._input_revision(manifest.input_source_ref) if manifest else None
        return {
            "revision": self._revision(revision),
            "parent_chain": [self._revision(parent) for parent in parents],
            "run": None if run is None else {"id": str(run.id), "workflow_release_id": str(run.workflow_release_id)},
            "manifest": None if manifest is None else {
                "id": str(manifest.id), "manifest_hash": manifest.manifest_hash,
                "git_commit": manifest.git_commit, "input_source_ref": manifest.input_source_ref,
                "input_hash": manifest.input_hash,
            },
            "input_revision": None if input_revision is None else self._revision(input_revision),
            "workflow_release": None if release is None else {
                "id": str(release.id), "workflow_id": release.workflow_id,
                "release_version": release.release_version, "entrypoint": release.entrypoint,
                "state_schema_version": release.state_schema_version,
            },
            "components": [
                {"kind": item.kind, "ref": item.ref, "exact_version": item.exact_version}
                for item in components
            ],
        }

    def _input_revision(self, source_ref: str) -> ArtifactRevision | None:
        prefix = "artifact_revision:"
        if not source_ref.startswith(prefix):
            return None
        try:
            return self.session.get(ArtifactRevision, UUID(source_ref.removeprefix(prefix)))
        except ValueError:
            return None
