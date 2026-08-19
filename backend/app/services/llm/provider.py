"""Small internal LLM provider abstraction for reviewer use."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

StructuredResultT = TypeVar("StructuredResultT", bound=BaseModel)


class LLMProviderError(RuntimeError):
    """Raised when structured generation fails in an LLM provider."""

    def __init__(
        self,
        message: str,
        *,
        diagnostics: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.diagnostics = diagnostics


class LLMProvider(ABC):
    """Minimal provider interface for reviewer structured generation."""

    @abstractmethod
    def generate_structured(
        self,
        *,
        system_instruction: str,
        user_input: str,
        response_model: type[StructuredResultT],
    ) -> StructuredResultT:
        """Generate a validated structured reviewer result."""
        raise NotImplementedError
