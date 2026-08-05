from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactIdentity:
    project_key: str
    artifact_type: str
    business_key: str


@dataclass(frozen=True)
class EditRevision:
    content: str
    mime_type: str = "text/markdown"
