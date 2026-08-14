"""OpenAI-backed implementation of the internal LLM provider."""

from __future__ import annotations

from typing import Any

from openai import OpenAI
from pydantic import BaseModel

from app.core.config import settings
from app.services.llm.provider import LLMProvider, LLMProviderError, StructuredResultT


class OpenAIProvider(LLMProvider):
    """Generate structured reviewer outputs using the OpenAI Responses API."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
        client: Any | None = None,
    ) -> None:
        resolved_api_key = api_key if api_key is not None else settings.openai_api_key
        if not resolved_api_key:
            raise LLMProviderError("OPENAI_API_KEY is not configured.")

        self._model = model if model is not None else settings.openai_model

        if client is not None:
            self._client = client
            return

        timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.openai_timeout_seconds
        )
        self._client = OpenAI(api_key=resolved_api_key, timeout=timeout)

    def generate_structured(
        self,
        *,
        system_instruction: str,
        user_input: str,
        response_model: type[StructuredResultT],
    ) -> StructuredResultT:
        if not system_instruction.strip():
            raise LLMProviderError("System instruction cannot be empty.")
        if not user_input.strip():
            raise LLMProviderError("User input cannot be empty.")

        try:
            response = self._client.responses.parse(
                model=self._model,
                instructions=system_instruction,
                input=user_input,
                text_format=response_model,
            )
        except Exception as exc:  # pragma: no cover - covered in tests via fake client
            raise LLMProviderError("OpenAI structured generation failed.") from exc

        parsed = getattr(response, "output_parsed", None)
        if not isinstance(parsed, BaseModel):
            raise LLMProviderError("OpenAI response did not contain a parsed payload.")

        return parsed
