import hashlib
import re
import uuid

from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from domain.artifact import ArtifactIdentity
from persistence.models import Artifact, ArtifactRevision, ExecutionRun
from ports.blob_store import BlobStorePort


class ArtifactService:
    def __init__(self, session: Session, blobs: BlobStorePort) -> None:
        self.session = session
        self.blobs = blobs

    def create_imported(
        self, identity: ArtifactIdentity, content: bytes, mime_type: str, actor: str, display_name: str
    ) -> ArtifactRevision:
        return self._create_revision(
            identity, content, mime_type, actor, display_name, origin="IMPORTED", source_run_id=None,
            parent_revision_id=None,
        )

    def create_ai_generated(self, run: ExecutionRun, content: str, mime_type: str) -> ArtifactRevision:
        data = content.encode("utf-8")
        return self._create_revision(
            ArtifactIdentity(run.project_key, run.output_artifact_type, run.output_business_key),
            data, mime_type, "runtime", run.output_business_key, origin="AI_GENERATED", source_run_id=run.id,
            parent_revision_id=None,
        )

    def edit(self, revision_id: uuid.UUID, content: str, mime_type: str, actor: str) -> ArtifactRevision:
        parent = self.session.get(ArtifactRevision, revision_id)
        if parent is None:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
        artifact = self.session.get(Artifact, parent.artifact_id)
        assert artifact is not None
        return self._create_revision(
            ArtifactIdentity(artifact.project_key, artifact.artifact_type, artifact.business_key),
            content.encode("utf-8"), mime_type, actor, artifact.display_name, origin="HUMAN_EDITED",
            source_run_id=None, parent_revision_id=parent.id,
        )

    def content(self, revision: ArtifactRevision) -> bytes:
        return self.blobs.get(revision.storage_uri)

    #: project_key / artifact_type / business_key do người dùng nhập và trở thành segment của object
    #: key. Không giới hạn charset thì `../` đi thẳng vào key, và với MinIO backend filesystem có thể
    #: ghi ra ngoài thư mục bucket dự kiến.
    _SAFE_KEY_SEGMENT = re.compile(r"^[A-Za-z0-9._-]{1,128}$")

    @classmethod
    def _safe_segment(cls, name: str, value: str) -> str:
        if not cls._SAFE_KEY_SEGMENT.fullmatch(value) or value in {".", ".."}:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "VALIDATION_ERROR",
                    "message": f"{name} must match [A-Za-z0-9._-]{{1,128}} and cannot be '.' or '..'",
                },
            )
        return value

    def _create_revision(
        self, identity: ArtifactIdentity, data: bytes, mime_type: str, actor: str, display_name: str,
        *, origin: str, source_run_id: uuid.UUID | None, parent_revision_id: uuid.UUID | None,
    ) -> ArtifactRevision:
        digest = hashlib.sha256(data).hexdigest()
        key = "/".join((
            self._safe_segment("project_key", identity.project_key),
            self._safe_segment("artifact_type", identity.artifact_type),
            self._safe_segment("business_key", identity.business_key),
            f"{digest}.md",
        ))
        blob = self.blobs.put_immutable(key=key, data=data, mime_type=mime_type)
        artifact_id = self._ensure_artifact(identity, display_name)
        for attempt in range(3):
            try:
                with self.session.begin_nested():
                    self.session.execute(text("SELECT id FROM artifact WHERE id = :id FOR UPDATE"), {"id": artifact_id})
                    revision_no = self.session.scalar(text(
                        "SELECT coalesce(max(revision_no), 0) + 1 FROM artifact_revision WHERE artifact_id = :id"
                    ), {"id": artifact_id})
                    revision = ArtifactRevision(
                        artifact_id=artifact_id, revision_no=revision_no, origin=origin,
                        source_run_id=source_run_id, parent_revision_id=parent_revision_id,
                        content_hash=blob.content_hash, storage_uri=blob.uri, mime_type=blob.mime_type,
                        size_bytes=blob.size_bytes, created_by=actor,
                    )
                    self.session.add(revision)
                    self.session.flush()
                return revision
            except IntegrityError as exc:
                if self._sqlstate(exc) != "23505" or attempt == 2:
                    raise
        raise AssertionError("revision retry exhausted")

    def _ensure_artifact(self, identity: ArtifactIdentity, display_name: str) -> uuid.UUID:
        artifact = self.session.scalar(select(Artifact).where(
            Artifact.project_key == identity.project_key, Artifact.artifact_type == identity.artifact_type,
            Artifact.business_key == identity.business_key,
        ))
        if artifact is not None:
            return artifact.id
        inserted = self.session.execute(text(
            "INSERT INTO artifact (project_key, artifact_type, business_key, display_name) "
            "VALUES (:project_key, :artifact_type, :business_key, :display_name) "
            "ON CONFLICT (project_key, artifact_type, business_key) DO NOTHING RETURNING id"
        ), {**identity.__dict__, "display_name": display_name}).scalar()
        if inserted is not None:
            return inserted
        artifact_id = self.session.scalar(text(
            "SELECT id FROM artifact WHERE project_key = :project_key AND artifact_type = :artifact_type "
            "AND business_key = :business_key"
        ), identity.__dict__)
        assert artifact_id is not None
        return artifact_id

    @staticmethod
    def _sqlstate(exc: IntegrityError) -> str | None:
        return getattr(exc.orig, "sqlstate", None) or getattr(exc.orig, "pgcode", None)
