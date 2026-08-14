"""AI Provider capability registry; health discovery never sends model requests."""
from __future__ import annotations

import shutil
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Callable, Protocol


class ProviderKind(str, Enum):
    INFERENCE = "inference"
    AGENT = "agent"


@dataclass(frozen=True)
class ProviderCapabilities:
    streaming: bool = False
    structured_output: bool = False
    tool_use: bool = False
    sessions: bool = False
    cancellation: bool = False


@dataclass(frozen=True)
class ProviderStatus:
    id: str
    kind: ProviderKind
    provider: str
    auth_mode: str
    available: bool
    configured: bool | None
    experimental: bool
    capabilities: ProviderCapabilities
    note: str = ""

    def public_dict(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "provider": self.provider,
            "auth_mode": self.auth_mode,
            "available": self.available,
            "configured": self.configured,
            "experimental": self.experimental,
            "capabilities": asdict(self.capabilities),
            "note": self.note,
        }


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, ProviderStatus] = {}

    def register(self, status: ProviderStatus) -> None:
        if status.id in self._providers:
            raise ValueError(f"duplicate provider id: {status.id}")
        self._providers[status.id] = status

    def health(self) -> dict:
        providers = [self._providers[key].public_dict() for key in sorted(self._providers)]
        return {"ok": True, "providers": providers}


def default_registry(
    executable_finder: Callable[[str], str | None] = shutil.which,
) -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register(ProviderStatus(
        id="opencode-go",
        kind=ProviderKind.INFERENCE,
        provider="opencode-go",
        auth_mode="api-key",
        available=True,
        configured=False,
        experimental=False,
        capabilities=ProviderCapabilities(streaming=True, structured_output=True),
        note="Direct HTTP adapter supported; API key is not configured in phase one.",
    ))
    registry.register(ProviderStatus(
        id="codex-local",
        kind=ProviderKind.AGENT,
        provider="codex",
        auth_mode="vendor-managed-oauth",
        available=executable_finder("codex") is not None,
        configured=None,
        experimental=False,
        capabilities=ProviderCapabilities(
            streaming=True, structured_output=True, tool_use=True,
            sessions=True, cancellation=True,
        ),
        note="Authentication remains owned by the Codex runtime.",
    ))
    registry.register(ProviderStatus(
        id="claude-code-local-personal",
        kind=ProviderKind.AGENT,
        provider="claude-code",
        auth_mode="vendor-managed-oauth",
        available=executable_finder("claude") is not None,
        configured=None,
        experimental=True,
        capabilities=ProviderCapabilities(
            streaming=True, structured_output=True, tool_use=True,
            sessions=True, cancellation=True,
        ),
        note="Personal-local experimental adapter; Peach never reads Claude credentials.",
    ))
    return registry


class InferenceProvider(Protocol):
    name: str

    def health(self) -> dict: ...
    def list_models(self) -> list[dict]: ...
    def complete(self, request: dict) -> dict: ...


class AgentProvider(Protocol):
    name: str

    def health(self) -> dict: ...
    def start(self, request: dict) -> dict: ...
    def resume(self, thread_id: str, request: dict) -> dict: ...
    def cancel(self, thread_id: str) -> None: ...
