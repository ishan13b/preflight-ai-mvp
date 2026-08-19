"""OpenAI-backed implementation of the internal LLM provider."""

from __future__ import annotations

import re
import time
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, ValidationError

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
        self._redaction_values = [resolved_api_key]
        self._last_parse_duration_ms: int | None = None

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

        started_at = time.perf_counter()
        try:
            response = self._client.responses.parse(
                model=self._model,
                instructions=system_instruction,
                input=user_input,
                text_format=response_model,
            )
        except Exception as exc:  # pragma: no cover - covered in tests via fake client
            self._last_parse_duration_ms = int((time.perf_counter() - started_at) * 1000)
            raise LLMProviderError(
                "OpenAI structured generation failed.",
                diagnostics=_build_error_diagnostics(
                    exc,
                    redaction_values=self._redaction_values,
                ),
            ) from exc
        self._last_parse_duration_ms = int((time.perf_counter() - started_at) * 1000)

        parsed = getattr(response, "output_parsed", None)
        if not isinstance(parsed, BaseModel):
            raise LLMProviderError("OpenAI response did not contain a parsed payload.")

        return parsed

    @property
    def last_parse_duration_ms(self) -> int | None:
        """Most recent wall-clock duration for a responses.parse(...) call."""
        return self._last_parse_duration_ms


def _redact_sensitive_text(value: str, *, redaction_values: list[str] | None = None) -> str:
    """Best-effort redaction for sensitive token-like values in exception text."""
    redacted = value

    all_redaction_values = list(redaction_values or [])
    configured_api_key = settings.openai_api_key
    if configured_api_key:
        all_redaction_values.append(configured_api_key)
    for secret in all_redaction_values:
        if secret:
            redacted = redacted.replace(secret, "[REDACTED_API_KEY]")

    redacted = re.sub(r"\bsk-[A-Za-z0-9_-]{8,}\b", "[REDACTED_API_KEY]", redacted)
    redacted = re.sub(
        r"(?i)\b(authorization)\s*:\s*bearer\s+[A-Za-z0-9._-]+",
        r"\1: Bearer [REDACTED_TOKEN]",
        redacted,
    )
    return redacted


def _safe_string(
    value: object,
    *,
    redaction_values: list[str] | None = None,
) -> str | None:
    if value is None:
        return None
    return _redact_sensitive_text(str(value), redaction_values=redaction_values)


def _safe_value(
    value: object,
    *,
    redaction_values: list[str] | None = None,
) -> object:
    """Recursively sanitize diagnostic values for safe local debugging."""
    if isinstance(value, str):
        return _safe_string(value, redaction_values=redaction_values)
    if isinstance(value, dict):
        return {
            str(key): _safe_value(val, redaction_values=redaction_values)
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [_safe_value(item, redaction_values=redaction_values) for item in value]
    return value


def _build_error_diagnostics(
    exc: Exception,
    *,
    redaction_values: list[str] | None = None,
) -> dict[str, object]:
    diagnostics: dict[str, object] = {
        "exception_class": type(exc).__name__,
        "exception_module": type(exc).__module__,
        "message": _safe_string(exc, redaction_values=redaction_values),
    }

    if isinstance(exc, ValidationError):
        validation_errors: list[dict[str, object]] = []
        for err in exc.errors():
            validation_errors.append(
                {
                    "loc": [str(part) for part in err.get("loc", ())],
                    "type": err.get("type"),
                    "msg": _safe_string(
                        err.get("msg"),
                        redaction_values=redaction_values,
                    ),
                    "input": _safe_value(
                        err.get("input"),
                        redaction_values=redaction_values,
                    ),
                }
            )
        diagnostics["validation_errors"] = validation_errors

    # OpenAI SDK exceptions commonly expose these attributes.
    status = getattr(exc, "status_code", None)
    if status is not None:
        diagnostics["http_status"] = status

    error_type = getattr(exc, "type", None)
    if error_type:
        diagnostics["api_error_type"] = _safe_string(
            error_type,
            redaction_values=redaction_values,
        )

    error_code = getattr(exc, "code", None)
    if error_code:
        diagnostics["api_error_code"] = _safe_string(
            error_code,
            redaction_values=redaction_values,
        )

    request_id = getattr(exc, "request_id", None)
    if request_id:
        diagnostics["request_id"] = _safe_string(
            request_id,
            redaction_values=redaction_values,
        )

    return diagnostics
