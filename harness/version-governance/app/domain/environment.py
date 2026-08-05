from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class EnvironmentMapping:
    environment: str
    workflow_id: str
    release_id: UUID
    updated_at: datetime
    updated_by: str


@dataclass(frozen=True)
class EnvironmentMappingAudit:
    environment: str
    workflow_id: str
    from_release_id: UUID | None
    to_release_id: UUID
    actor: str
    reason: str | None
    at: datetime
