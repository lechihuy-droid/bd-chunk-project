from dataclasses import dataclass
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.difference import DiffSide
from persistence.models import ArtifactRevision, ExecutionRun, RunComponent, RunManifest, WorkflowRelease


CATEGORY_ORDER = ("INPUT", "WORKFLOW_RELEASE", "PROMPT", "MODEL", "TOOL", "RUNTIME", "HUMAN_EDIT")


@dataclass(frozen=True)
class ResolvedSide:
    run: ExecutionRun
    manifest: RunManifest
    release: WorkflowRelease
    revision: ArtifactRevision | None
    artifact_id: str | None
    human_edit: bool
    components: tuple[RunComponent, ...]


class DifferenceService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def explain(self, left: DiffSide, right: DiffSide) -> dict[str, Any]:
        left.validate()
        right.validate()
        resolved_left = self._resolve(left)
        resolved_right = self._resolve(right)
        changed: list[dict[str, Any]] = []
        unchanged: list[dict[str, Any]] = []
        for category in CATEGORY_ORDER:
            left_facets = self._facets(resolved_left, category)
            right_facets = self._facets(resolved_right, category)
            for facet in sorted(set(left_facets) | set(right_facets)):
                before, after = left_facets.get(facet), right_facets.get(facet)
                if before == after:
                    unchanged.append({"category": category, "facet": facet, "value": before})
                else:
                    changed.append({"category": category, "facet": facet, "from": before, "to": after})
        return {
            "left": self._side_response(resolved_left),
            "right": self._side_response(resolved_right),
            "same_artifact": resolved_left.artifact_id is not None and resolved_left.artifact_id == resolved_right.artifact_id,
            "verdict": "IDENTICAL" if not changed else "DIFFERENT",
            "changed": changed,
            "unchanged": unchanged,
        }

    def _resolve(self, side: DiffSide) -> ResolvedSide:
        if side.run_id is not None:
            try:
                run_id = UUID(side.run_id)
            except ValueError as error:
                raise HTTPException(status_code=422, detail={"code": "VALIDATION_ERROR"}) from error
            revision = self.session.scalar(
                select(ArtifactRevision)
                .where(ArtifactRevision.source_run_id == run_id)
                # `id` là UUID ngẫu nhiên — sắp theo nó là thứ tự vô nghĩa. Một run hiện chỉ sinh
                # đúng một revision nên vô hại, nhưng nếu điều đó đổi thì phải lấy bản mới nhất,
                # không phải bản có UUID nhỏ nhất.
                .order_by(ArtifactRevision.revision_no.desc())
            )
            return self._from_run(run_id, revision, human_edit=False)

        assert side.revision_id is not None
        try:
            revision = self.session.get(ArtifactRevision, UUID(side.revision_id))
        except ValueError as error:
            raise HTTPException(status_code=422, detail={"code": "VALIDATION_ERROR"}) from error
        if revision is None:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
        if revision.origin == "IMPORTED":
            self._no_manifest()
        if revision.origin == "AI_GENERATED":
            assert revision.source_run_id is not None
            return self._from_run(revision.source_run_id, revision, human_edit=False)

        current = revision
        while current.origin == "HUMAN_EDITED":
            if current.parent_revision_id is None:
                self._no_manifest()
            parent = self.session.get(ArtifactRevision, current.parent_revision_id)
            if parent is None:
                self._no_manifest()
            current = parent
        if current.origin != "AI_GENERATED" or current.source_run_id is None:
            self._no_manifest()
        return self._from_run(current.source_run_id, revision, human_edit=True)

    def _from_run(self, run_id: UUID, revision: ArtifactRevision | None, *, human_edit: bool) -> ResolvedSide:
        row = self.session.execute(
            select(ExecutionRun, RunManifest, WorkflowRelease)
            .join(RunManifest, RunManifest.run_id == ExecutionRun.id)
            .join(WorkflowRelease, WorkflowRelease.id == RunManifest.workflow_release_id)
            .where(ExecutionRun.id == run_id)
        ).one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
        run, manifest, release = row
        components = tuple(self.session.scalars(
            select(RunComponent).where(RunComponent.manifest_id == manifest.id)
            .order_by(RunComponent.kind, RunComponent.ref)
        ))
        return ResolvedSide(run, manifest, release, revision,
                            str(revision.artifact_id) if revision else None, human_edit, components)

    @staticmethod
    def _no_manifest() -> None:
        raise HTTPException(status_code=422, detail={"code": "NO_MANIFEST_FOR_REVISION"})

    @staticmethod
    def _side_response(side: ResolvedSide) -> dict[str, Any]:
        return {
            "run_id": str(side.run.id),
            "revision_id": str(side.revision.id) if side.revision else None,
            "artifact_id": side.artifact_id,
            "manifest_hash": side.manifest.manifest_hash,
        }

    def _facets(self, side: ResolvedSide, category: str) -> dict[str, Any]:
        manifest, release = side.manifest, side.release
        if category == "INPUT":
            return {"input_hash": manifest.input_hash, "input_source_ref": manifest.input_source_ref}
        if category == "WORKFLOW_RELEASE":
            return {
                "workflow_release_id": str(manifest.workflow_release_id), "release_version": release.release_version,
                "git_commit": manifest.git_commit, "entrypoint": release.entrypoint,
                "state_schema_version": release.state_schema_version,
            }
        if category == "PROMPT":
            return self._component_facets(side.components, {"PROMPT"})
        if category == "MODEL":
            return self._component_facets(side.components, {"MODEL"})
        if category == "TOOL":
            return self._component_facets(side.components, {"TOOL", "AGENT"})
        if category == "RUNTIME":
            return {"runtime_adapter_id": manifest.runtime_adapter_id, "environment": manifest.environment}
        return {"human_edit_present": side.human_edit}

    @staticmethod
    def _component_facets(components: tuple[RunComponent, ...], kinds: set[str]) -> dict[str, str]:
        selected = [item for item in components if item.kind in kinds]
        duplicate_refs = {item.ref for item in selected if sum(other.ref == item.ref for other in selected) > 1}
        return {
            (f"{item.kind}:{item.ref}" if item.ref in duplicate_refs else item.ref): item.exact_version
            for item in selected
        }
