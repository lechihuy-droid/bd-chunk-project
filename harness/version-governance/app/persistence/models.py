import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, BigInteger, String, Text, UniqueConstraint, desc, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


release_status = Enum("DRAFT", "PUBLISHED", name="release_status")
environment_name = Enum("DEV", "PROD", name="environment_name")
run_status = Enum("CREATED", "MANIFEST_FROZEN", "RUNNING", "SUCCEEDED", "FAILED", "FAILED_PRECONDITION", "CANCELLED", name="run_status")
component_kind = Enum("PROMPT", "AGENT", "TOOL", "MODEL", name="component_kind")
origin_type = Enum("AI_GENERATED", "HUMAN_EDITED", "IMPORTED", name="origin_type")


class WorkflowRelease(Base):
    __tablename__ = "workflow_release"
    __table_args__ = (UniqueConstraint("workflow_id", "release_version", name="uq_release"), CheckConstraint("status = 'DRAFT' OR (git_commit IS NOT NULL AND published_at IS NOT NULL)", name="ck_published_complete"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    workflow_id: Mapped[str] = mapped_column(Text)
    release_version: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(release_status, server_default="DRAFT")
    git_repo: Mapped[str] = mapped_column(Text)
    git_ref: Mapped[str] = mapped_column(Text)
    git_commit: Mapped[str | None] = mapped_column(String(40))
    entrypoint: Mapped[str] = mapped_column(Text)
    state_schema_version: Mapped[str] = mapped_column(Text)
    bindings: Mapped[dict] = mapped_column(JSONB)
    runtime_adapter_id: Mapped[str] = mapped_column(Text)
    model_profile: Mapped[str] = mapped_column(Text)
    model_name: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_by: Mapped[str | None] = mapped_column(Text)


class EnvironmentMapping(Base):
    __tablename__ = "environment_mapping"
    __table_args__ = (UniqueConstraint("environment", "workflow_id", name="uq_env"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    environment: Mapped[str] = mapped_column(environment_name)
    workflow_id: Mapped[str] = mapped_column(Text)
    workflow_release_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workflow_release.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_by: Mapped[str] = mapped_column(Text)


class EnvironmentMappingAudit(Base):
    __tablename__ = "environment_mapping_audit"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    environment: Mapped[str] = mapped_column(environment_name)
    workflow_id: Mapped[str] = mapped_column(Text)
    from_release_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("workflow_release.id"))
    to_release_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workflow_release.id"))
    actor: Mapped[str] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ExecutionRun(Base):
    __tablename__ = "execution_run"
    __table_args__ = (CheckConstraint("status IN ('CREATED','FAILED_PRECONDITION') OR workflow_release_id IS NOT NULL", name="ck_release_required"), Index("ix_run_project", "project_key", desc("created_at")))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    project_key: Mapped[str] = mapped_column(Text)
    workflow_id: Mapped[str] = mapped_column(Text)
    workflow_release_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("workflow_release.id"), nullable=True)
    output_business_key: Mapped[str] = mapped_column(Text)
    output_artifact_type: Mapped[str] = mapped_column(Text, server_default="API_BASIC_DESIGN")
    environment: Mapped[str | None] = mapped_column(environment_name)
    execution_mode: Mapped[str] = mapped_column(Text, server_default="ENVIRONMENT")
    status: Mapped[str] = mapped_column(run_status, server_default="CREATED")
    correlation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True)
    runtime_provider: Mapped[str | None] = mapped_column(Text)
    runtime_run_id: Mapped[str | None] = mapped_column(Text)
    runtime_thread_id: Mapped[str | None] = mapped_column(Text)
    trace_provider: Mapped[str | None] = mapped_column(Text)
    trace_id: Mapped[str | None] = mapped_column(Text)
    error_code: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RunManifest(Base):
    __tablename__ = "run_manifest"
    __table_args__ = (CheckConstraint("input_hash ~ '^sha256:[0-9a-f]{64}$'", name="ck_input_hash"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("execution_run.id"), unique=True)
    workflow_release_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workflow_release.id"))
    git_repo: Mapped[str] = mapped_column(Text)
    git_commit: Mapped[str] = mapped_column(String(40))
    model_profile: Mapped[str] = mapped_column(Text)
    runtime_adapter_id: Mapped[str] = mapped_column(Text)
    environment: Mapped[str | None] = mapped_column(environment_name)
    input_source_ref: Mapped[str] = mapped_column(Text)
    input_hash: Mapped[str] = mapped_column(String(71))
    manifest_hash: Mapped[str] = mapped_column(String(71))
    frozen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RunComponent(Base):
    __tablename__ = "run_component"
    __table_args__ = (UniqueConstraint("manifest_id", "kind", "ref", name="uq_component"), CheckConstraint("lower(exact_version) NOT IN ('production','prod','latest','staging','champion','current')", name="ck_no_alias"), CheckConstraint("kind <> 'PROMPT' OR exact_version ~ '^[0-9]+$'", name="ck_prompt_numeric"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    manifest_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("run_manifest.id"))
    kind: Mapped[str] = mapped_column(component_kind)
    ref: Mapped[str] = mapped_column(Text)
    exact_version: Mapped[str] = mapped_column(Text)
    extra: Mapped[dict] = mapped_column(JSONB, server_default="'{}'::jsonb")


class Artifact(Base):
    __tablename__ = "artifact"
    __table_args__ = (UniqueConstraint("project_key", "artifact_type", "business_key", name="uq_artifact"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    project_key: Mapped[str] = mapped_column(Text)
    artifact_type: Mapped[str] = mapped_column(Text)
    business_key: Mapped[str] = mapped_column(Text)
    display_name: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ArtifactRevision(Base):
    __tablename__ = "artifact_revision"
    __table_args__ = (UniqueConstraint("artifact_id", "revision_no", name="uq_revision"), CheckConstraint("content_hash ~ '^sha256:[0-9a-f]{64}$'", name="ck_content_hash"), CheckConstraint("(origin = 'AI_GENERATED' AND source_run_id IS NOT NULL) OR (origin = 'HUMAN_EDITED' AND parent_revision_id IS NOT NULL) OR (origin = 'IMPORTED' AND source_run_id IS NULL)", name="ck_provenance"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    artifact_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("artifact.id"))
    revision_no: Mapped[int] = mapped_column(Integer)
    origin: Mapped[str] = mapped_column(origin_type)
    source_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("execution_run.id"))
    parent_revision_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("artifact_revision.id"))
    content_hash: Mapped[str] = mapped_column(String(71))
    storage_uri: Mapped[str] = mapped_column(Text)
    mime_type: Mapped[str] = mapped_column(Text)
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[str] = mapped_column(Text)


class ApprovedBaseline(Base):
    __tablename__ = "approved_baseline"
    __table_args__ = (Index("uq_baseline_active", "artifact_id", "scope", unique=True, postgresql_where="active"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    artifact_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("artifact.id"))
    scope: Mapped[str] = mapped_column(Text, server_default="default")
    artifact_revision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("artifact_revision.id"))
    approved_by: Mapped[str] = mapped_column(Text)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    superseded_baseline_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("approved_baseline.id"))
    active: Mapped[bool] = mapped_column(Boolean, server_default="true")


class RuntimeCallback(Base):
    __tablename__ = "runtime_callback"
    correlation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("execution_run.correlation_id"), primary_key=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    response_body: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
