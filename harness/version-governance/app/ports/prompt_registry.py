from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ResolvedPrompt:
    registry: str
    name: str
    version: int
    template: str
    uri: str


class PromptResolutionError(Exception):
    pass


class PromptRegistryPort(Protocol):
    def resolve(
        self,
        name: str,
        *,
        alias: str | None = None,
        version: int | None = None,
    ) -> ResolvedPrompt: ...
