import unittest
from unittest.mock import patch

from app.core.config import settings
from app.schemas.review import (
    EvidenceBasis,
    LLMReviewerFinding,
    SecurityReviewerLLMResult,
    Severity,
)
from app.services.llm.openai_provider import OpenAIProvider
from app.services.llm.provider import LLMProviderError


class _FailingResponses:
    def parse(self, **_: object) -> object:
        raise RuntimeError("transport failure")


class _LeakyFailingResponses:
    def __init__(self, leaked_text: str) -> None:
        self._leaked_text = leaked_text

    def parse(self, **_: object) -> object:
        raise RuntimeError(f"transport failure: {self._leaked_text}")


class _NoParsedResponses:
    def parse(self, **_: object) -> object:
        class _Response:
            output_parsed = None

        return _Response()


class _OkResponses:
    def parse(self, **_: object) -> object:
        class _Response:
            output_parsed = SecurityReviewerLLMResult(
                score=9,
                summary="Strong security posture.",
                engineering_reasoning="Auth and controls look sufficient.",
                findings=[
                    LLMReviewerFinding(
                        statement="JWT rotation policy is not specified; validate rotation controls.",
                        evidence_basis=EvidenceBasis.NOT_SPECIFIED,
                        severity_hint=Severity.LOW,
                    )
                ],
                recommendations=["Continue periodic security reviews"],
                estimated_impact="Low near-term exploitability risk.",
                score_rationale="Controls are strong with minor unspecified lifecycle detail.",
                severity_rationale="Unspecified lifecycle detail has low immediate blast radius.",
            )

        return _Response()


class _CaptureResponses:
    def __init__(self) -> None:
        self.last_kwargs: dict[str, object] | None = None

    def parse(self, **kwargs: object) -> object:
        self.last_kwargs = kwargs

        class _Response:
            output_parsed = SecurityReviewerLLMResult(
                score=9,
                summary="Strong security posture.",
                engineering_reasoning="Auth and controls look sufficient.",
                findings=[
                    LLMReviewerFinding(
                        statement="JWT rotation policy is not specified; validate rotation controls.",
                        evidence_basis=EvidenceBasis.NOT_SPECIFIED,
                        severity_hint=Severity.LOW,
                    )
                ],
                recommendations=["Continue periodic security reviews"],
                estimated_impact="Low near-term exploitability risk.",
                score_rationale="Controls are strong with minor unspecified lifecycle detail.",
                severity_rationale="Unspecified lifecycle detail has low immediate blast radius.",
            )

        return _Response()


class _Client:
    def __init__(self, responses: object) -> None:
        self.responses = responses


class _ValidationErrorResponses:
    def parse(self, **_: object) -> object:
        payload = {
            "score": 7,
            "summary": "Security posture needs validation.",
            "engineering_reasoning": "Claim construction should fail for NOT_SPECIFIED.",
            "findings": [
                {
                    "statement": "The architecture lacks authorization controls.",
                    "evidence_basis": "NOT_SPECIFIED",
                    "severity_hint": "MEDIUM",
                }
            ],
            "recommendations": ["Use uncertainty wording."],
            "estimated_impact": "Overstated confidence in absent control.",
            "score_rationale": "Invalid claim wording for NOT_SPECIFIED.",
            "severity_rationale": "Invalid claim wording for NOT_SPECIFIED.",
        }
        # Raises pydantic.ValidationError.
        SecurityReviewerLLMResult.model_validate(payload)
        raise AssertionError("Expected ValidationError")


class _FakeOpenAIAPIError(RuntimeError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.status_code = 429
        self.type = "rate_limit_error"
        self.code = "requests_per_minute_exceeded"
        self.request_id = "req_123abc"


class _APIErrorResponses:
    def parse(self, **_: object) -> object:
        raise _FakeOpenAIAPIError("rate limit hit")


class OpenAIProviderErrorTests(unittest.TestCase):
    def test_missing_api_key_raises(self) -> None:
        with self.assertRaises(LLMProviderError):
            OpenAIProvider(api_key="")

    def test_api_errors_are_wrapped(self) -> None:
        provider = OpenAIProvider(
            api_key="test-key",
            model="gpt-4.1-mini",
            client=_Client(_FailingResponses()),
        )

        with self.assertRaises(LLMProviderError) as ctx:
            provider.generate_structured(
                system_instruction="security rubric",
                user_input="{}",
                response_model=SecurityReviewerLLMResult,
            )

        self.assertIn("OpenAI structured generation failed", str(ctx.exception))
        self.assertIsInstance(ctx.exception.__cause__, RuntimeError)
        diagnostics = getattr(ctx.exception, "diagnostics", None)
        self.assertIsInstance(diagnostics, dict)
        assert isinstance(diagnostics, dict)
        self.assertEqual(diagnostics.get("exception_class"), "RuntimeError")
        self.assertEqual(diagnostics.get("message"), "transport failure")

    def test_api_key_is_redacted_from_diagnostics(self) -> None:
        leaked_key = "test-key"
        provider = OpenAIProvider(
            api_key=leaked_key,
            model="gpt-4.1-mini",
            client=_Client(_LeakyFailingResponses(leaked_key)),
        )

        with self.assertRaises(LLMProviderError) as ctx:
            provider.generate_structured(
                system_instruction="security rubric",
                user_input="{}",
                response_model=SecurityReviewerLLMResult,
            )

        diagnostics = getattr(ctx.exception, "diagnostics", None)
        self.assertIsInstance(diagnostics, dict)
        assert isinstance(diagnostics, dict)
        message = str(diagnostics.get("message"))
        self.assertNotIn(leaked_key, message)
        self.assertIn("[REDACTED_API_KEY]", message)

    def test_pydantic_validation_error_exposes_safe_error_details(self) -> None:
        provider = OpenAIProvider(
            api_key="test-key",
            model="gpt-4.1-mini",
            client=_Client(_ValidationErrorResponses()),
        )

        with self.assertRaises(LLMProviderError) as ctx:
            provider.generate_structured(
                system_instruction="security rubric",
                user_input="{}",
                response_model=SecurityReviewerLLMResult,
            )

        diagnostics = getattr(ctx.exception, "diagnostics", None)
        self.assertIsInstance(diagnostics, dict)
        assert isinstance(diagnostics, dict)
        self.assertEqual(diagnostics.get("exception_class"), "ValidationError")
        validation_errors = diagnostics.get("validation_errors")
        self.assertIsInstance(validation_errors, list)
        assert isinstance(validation_errors, list)
        self.assertGreaterEqual(len(validation_errors), 1)
        first_error = validation_errors[0]
        self.assertIn("loc", first_error)
        self.assertIn("msg", first_error)
        self.assertIn("type", first_error)

    def test_api_exception_exposes_http_and_request_metadata(self) -> None:
        provider = OpenAIProvider(
            api_key="test-key",
            model="gpt-4.1-mini",
            client=_Client(_APIErrorResponses()),
        )

        with self.assertRaises(LLMProviderError) as ctx:
            provider.generate_structured(
                system_instruction="security rubric",
                user_input="{}",
                response_model=SecurityReviewerLLMResult,
            )

        diagnostics = getattr(ctx.exception, "diagnostics", None)
        self.assertIsInstance(diagnostics, dict)
        assert isinstance(diagnostics, dict)
        self.assertEqual(diagnostics.get("http_status"), 429)
        self.assertEqual(diagnostics.get("api_error_type"), "rate_limit_error")
        self.assertEqual(
            diagnostics.get("api_error_code"),
            "requests_per_minute_exceeded",
        )
        self.assertEqual(diagnostics.get("request_id"), "req_123abc")

    def test_generic_exception_exposes_class_and_safe_message(self) -> None:
        provider = OpenAIProvider(
            api_key="test-key",
            model="gpt-4.1-mini",
            client=_Client(_FailingResponses()),
        )

        with self.assertRaises(LLMProviderError) as ctx:
            provider.generate_structured(
                system_instruction="security rubric",
                user_input="{}",
                response_model=SecurityReviewerLLMResult,
            )

        diagnostics = getattr(ctx.exception, "diagnostics", None)
        self.assertIsInstance(diagnostics, dict)
        assert isinstance(diagnostics, dict)
        self.assertEqual(diagnostics.get("exception_class"), "RuntimeError")
        self.assertEqual(diagnostics.get("message"), "transport failure")

    def test_missing_parsed_payload_is_error(self) -> None:
        provider = OpenAIProvider(
            api_key="test-key",
            model="gpt-4.1-mini",
            client=_Client(_NoParsedResponses()),
        )

        with self.assertRaises(LLMProviderError):
            provider.generate_structured(
                system_instruction="security rubric",
                user_input="{}",
                response_model=SecurityReviewerLLMResult,
            )

    def test_valid_parsed_payload_is_returned(self) -> None:
        provider = OpenAIProvider(
            api_key="test-key",
            model="gpt-4.1-mini",
            client=_Client(_OkResponses()),
        )

        result = provider.generate_structured(
            system_instruction="security rubric",
            user_input="{}",
            response_model=SecurityReviewerLLMResult,
        )

        self.assertEqual(result.score, 9)

    def test_uses_configured_openai_model_when_not_explicitly_provided(self) -> None:
        captured = _CaptureResponses()

        with patch.object(settings, "openai_model", "gpt-4.1-mini"):
            provider = OpenAIProvider(
                api_key="test-key",
                client=_Client(captured),
            )

            provider.generate_structured(
                system_instruction="security rubric",
                user_input="{}",
                response_model=SecurityReviewerLLMResult,
            )

        assert captured.last_kwargs is not None
        self.assertEqual(captured.last_kwargs["model"], "gpt-4.1-mini")


if __name__ == "__main__":
    unittest.main()
