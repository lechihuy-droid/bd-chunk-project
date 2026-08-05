import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from persistence.models import ApprovedBaseline, Artifact, ArtifactRevision
from services.baseline_service import BaselineService


def sqlstate(error: DBAPIError) -> str | None:
    return getattr(error.orig, "sqlstate", None) or getattr(error.orig, "pgcode", None)


def revision(session, no: int) -> ArtifactRevision:
    artifact = session.scalar(text("SELECT id FROM artifact LIMIT 1"))
    if artifact is None:
        item = Artifact(project_key="project", artifact_type="BD", business_key="F001", display_name="F001")
        session.add(item)
        session.flush()
        artifact = item.id
    row = ArtifactRevision(artifact_id=artifact, revision_no=no, origin="IMPORTED", content_hash="sha256:" + str(no) * 64,
        storage_uri=f"s3://vgov-artifacts/project/BD/F001/{no}.md", mime_type="text/markdown", size_bytes=1, created_by="test")
    session.add(row)
    session.commit()
    return row


def test_baseline_history_supersedes_old_pointer(session) -> None:
    first = revision(session, 1)
    second = revision(session, 2)
    service = BaselineService(session)
    old = service.approve(first.artifact_id, first.id, "default", "alice")
    new = service.approve(first.artifact_id, second.id, "default", "bob")
    assert not session.get(ApprovedBaseline, old.id).active
    assert new.superseded_baseline_id == old.id
    assert [row.id for row in service.history(first.artifact_id)] == [new.id, old.id]


def test_baseline_unique_active_and_pointer_trigger(session) -> None:
    first = revision(session, 1)
    second = revision(session, 2)
    baseline = BaselineService(session).approve(first.artifact_id, first.id, "default", "alice")
    session.add(ApprovedBaseline(artifact_id=first.artifact_id, artifact_revision_id=second.id, scope="default", approved_by="bob", active=True))
    with pytest.raises(DBAPIError) as duplicate:
        session.commit()
    assert sqlstate(duplicate.value) == "23505"
    session.rollback()
    with pytest.raises(DBAPIError) as immutable:
        session.execute(text("UPDATE approved_baseline SET artifact_revision_id = :revision WHERE id = :id"), {"revision": second.id, "id": baseline.id})
    assert sqlstate(immutable.value) == "VG409"
