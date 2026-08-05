from domain.release import ReleaseDraft
from services.release_service import ReleaseService


class FakeSourceControl:
    def resolve_commit(self, repo: str, ref: str) -> str:
        return "d" * 40

    def commit_exists(self, repo: str, sha: str) -> bool:
        return True


def release(version: str) -> ReleaseDraft:
    return ReleaseDraft("workflow", version, "repo", "main", "graph:build_graph", "v1", {}, "langgraph", "design-accurate@v1", "meta/llama-3.1-8b-instruct")


def test_rollback_moves_pointer_and_preserves_releases(session):
    service = ReleaseService(session, FakeSourceControl())
    first = service.publish(service.create_draft(release("1.0.0"), "tester").id, "tester")
    second = service.publish(service.create_draft(release("1.1.0"), "tester").id, "tester")

    service.set_environment("PROD", "workflow", second.id, "tester", "promote")
    service.set_environment("PROD", "workflow", first.id, "tester", "rollback")

    pointer = service.environment_releases("workflow")
    assert pointer["PROD"].id == first.id
    preserved = service.get_release(second.id)
    assert preserved.status == "PUBLISHED"
    assert preserved.git_commit == "d" * 40
    audits = service.environment_audit("PROD", "workflow")
    assert len(audits) == 2
    assert audits[0].from_release_id == second.id
    assert audits[0].to_release_id == first.id
