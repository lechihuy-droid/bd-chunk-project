import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from domain.release import ReleaseDraft
from services.release_service import ReleaseService


class FakeSourceControl:
    def resolve_commit(self, repo: str, ref: str) -> str:
        return "a" * 40

    def commit_exists(self, repo: str, sha: str) -> bool:
        return True


def draft() -> ReleaseDraft:
    return ReleaseDraft("workflow", "1.0.0", "repo", "main", "graph:build_graph", "v1", {}, "langgraph", "design-accurate@v1", "meta/llama-3.1-8b-instruct")


def sqlstate(error: DBAPIError) -> str | None:
    return getattr(error.orig, "sqlstate", None) or getattr(error.orig, "pgcode", None)


def test_published_release_cannot_update_or_delete(session):
    service = ReleaseService(session, FakeSourceControl())
    release = service.publish(service.create_draft(draft(), "tester").id, "tester")
    release_id = release.id

    with pytest.raises(DBAPIError) as update_error:
        session.execute(text("UPDATE workflow_release SET git_commit = :sha WHERE id = :id"), {"sha": "b" * 40, "id": release_id})
    assert sqlstate(update_error.value) == "VG409"
    session.rollback()

    with pytest.raises(DBAPIError) as model_name_error:
        session.execute(text("UPDATE workflow_release SET model_name = 'other-model' WHERE id = :id"), {"id": release_id})
    assert sqlstate(model_name_error.value) == "VG409"
    session.rollback()

    with pytest.raises(DBAPIError) as delete_error:
        session.execute(text("DELETE FROM workflow_release WHERE id = :id"), {"id": release_id})
    assert sqlstate(delete_error.value) == "VG409"
    session.rollback()


def test_draft_definition_is_immutable_but_publish_transition_is_allowed(session):
    service = ReleaseService(session, FakeSourceControl())
    release = service.create_draft(draft(), "tester")
    release_id = release.id

    with pytest.raises(DBAPIError) as error:
        session.execute(text("UPDATE workflow_release SET model_profile = 'x' WHERE id = :id"), {"id": release_id})
    assert sqlstate(error.value) == "VG409"
    session.rollback()

    session.execute(text("UPDATE workflow_release SET status = 'PUBLISHED', git_commit = :sha, published_at = now() WHERE id = :id"), {"sha": "c" * 40, "id": release_id})
    session.commit()
    status = session.scalar(text("SELECT status::text FROM workflow_release WHERE id = :id"), {"id": release_id})
    assert status == "PUBLISHED"
