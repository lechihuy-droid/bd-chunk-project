from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class ReleaseDraft:
    workflow_id: str
    release_version: str
    git_repo: str
    git_ref: str
    entrypoint: str
    state_schema_version: str
    bindings: dict[str, Any]
    runtime_adapter_id: str
    model_profile: str
    model_name: str


@dataclass(frozen=True)
class Release:
    id: UUID
    workflow_id: str
    release_version: str
    status: str
    git_repo: str
    git_ref: str
    git_commit: str | None
    entrypoint: str
    state_schema_version: str
    bindings: dict[str, Any]
    runtime_adapter_id: str
    model_profile: str
    model_name: str
    created_at: datetime
    created_by: str
    published_at: datetime | None
    published_by: str | None
