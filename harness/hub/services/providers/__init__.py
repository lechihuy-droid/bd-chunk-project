from __future__ import annotations

from types import ModuleType

from services.providers import base, claude_cli, codex_cli, nvidia_api

registry: dict[str, ModuleType] = {
    "nvidia": nvidia_api,
    "claude": claude_cli,
    "codex": codex_cli,
}


def get_provider(provider_id: str) -> ModuleType:
    provider = registry.get(provider_id)
    if provider is None:
        raise ValueError(f"Unknown provider: {provider_id}")
    return provider


def list_providers() -> list[base.ProviderStatus]:
    return [provider.status() for provider in registry.values()]
