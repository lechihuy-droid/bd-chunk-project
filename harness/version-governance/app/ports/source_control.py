from typing import Protocol


class SourceControlPort(Protocol):
    def resolve_commit(self, repo: str, ref: str) -> str:
        """Resolve a ref to an exact 40-hex commit SHA."""

    def commit_exists(self, repo: str, sha: str) -> bool:
        """Return whether SHA identifies a commit in repo."""
