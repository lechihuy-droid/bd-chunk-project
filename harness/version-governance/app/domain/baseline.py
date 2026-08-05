from dataclasses import dataclass


@dataclass(frozen=True)
class BaselineRequest:
    artifact_id: str
    revision_id: str
    scope: str = "default"
