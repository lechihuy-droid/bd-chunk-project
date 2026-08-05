from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ResolvedPromptBinding:
    node: str
    name: str
    version: int
    template: str


@dataclass(frozen=True)
class StartRunRequest:
    correlation_id: str
    run_id: str
    entrypoint: str
    state_schema_version: str
    model_profile: str
    model_name: str
    prompts: tuple[ResolvedPromptBinding, ...]
    input_payload: str
    input_hash: str
    callback_url: str
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResumeRunRequest:
    correlation_id: str
    runtime_run_id: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class CancelRunRequest:
    correlation_id: str
    runtime_run_id: str
    reason: str | None = None


@dataclass(frozen=True)
class RuntimeStatus:
    canonical: str
    provider_status: str
    detail: str | None = None


@dataclass(frozen=True)
class RuntimeHandle:
    provider: str
    runtime_run_id: str
    runtime_thread_id: str | None
    status: RuntimeStatus


class RuntimeCapabilityNotSupported(Exception):
    pass


class WorkflowRuntimePort(Protocol):
    async def start(self, req: StartRunRequest) -> RuntimeHandle: ...

    async def resume(self, req: ResumeRunRequest) -> RuntimeHandle: ...

    async def cancel(self, req: CancelRunRequest) -> RuntimeHandle: ...

    async def get_status(self, runtime_run_id: str) -> RuntimeStatus: ...
