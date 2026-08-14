import unittest
from unittest.mock import patch

from app.core.config import settings
from app.schemas.review import SecurityReviewerLLMResult
from app.services.llm.openai_provider import OpenAIProvider
from app.services.llm.provider import LLMProviderError


class _FailingResponses:
    def parse(self, **_: object) -> object:
        raise RuntimeError("transport failure")


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
                risks=[],
                recommendations=["Continue periodic security reviews"],
                estimated_impact="Low near-term exploitability risk.",
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
                risks=[],
                recommendations=["Continue periodic security reviews"],
                estimated_impact="Low near-term exploitability risk.",
            )

        return _Response()


class _Client:
    def __init__(self, responses: object) -> None:
        self.responses = responses


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
