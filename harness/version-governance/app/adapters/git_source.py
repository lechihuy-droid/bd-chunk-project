import re
import subprocess
from pathlib import Path


class GitSourceAdapter:
    def __init__(self, repo_path: str) -> None:
        self._repo_path = Path(repo_path)

    def resolve_commit(self, repo: str, ref: str) -> str:
        result = self._git("rev-parse", ref)
        sha = result.stdout.strip()
        if result.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError(f"Cannot resolve git ref: {ref}")
        if not self.commit_exists(repo, sha):
            raise ValueError(f"Git ref is not a commit: {ref}")
        return sha

    def commit_exists(self, repo: str, sha: str) -> bool:
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            return False
        return self._git("cat-file", "-e", f"{sha}^{{commit}}").returncode == 0

    def _git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args], cwd=self._repo_path, text=True, capture_output=True, check=False
        )
