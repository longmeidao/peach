"""AI Provider 只定义能力边界；阶段一不发真实模型请求。"""
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


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
