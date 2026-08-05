from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RunRequest:
    project_key: str
    workflow_id: str
    input_revision_id: UUID
    output_business_key: str
    output_artifact_type: str = "API_BASIC_DESIGN"
    environment: str | None = "PROD"
    release_id: UUID | None = None
