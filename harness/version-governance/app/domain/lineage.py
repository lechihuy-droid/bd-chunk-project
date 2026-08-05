from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class LineageRequest:
    revision_id: UUID
