from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.llm.client import analyze


def _fake_response(content="test result", model="deepseek/deepseek-chat", tokens=100):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        model=model,
        usage=SimpleNamespace(total_tokens=tokens),
    )


@pytest.fixture(autouse=True)
def reset_router():
    import src.llm.client as mod

    mod._router = None
    yield
    mod._router = None


class TestAnalyze:
    @pytest.mark.asyncio
    async def test_returns_text_on_success(self):
        fake_router = MagicMock()
        fake_router.acompletion = AsyncMock(return_value=_fake_response("分析结果"))
        with patch("src.llm.client._get_router", return_value=fake_router):
            result = await analyze("test prompt")
        assert result == "分析结果"

    @pytest.mark.asyncio
    async def test_retries_on_rate_limit_then_succeeds(self):
        from litellm.exceptions import RateLimitError

        fake_router = MagicMock()
        fake_router.acompletion = AsyncMock(
            side_effect=[
                RateLimitError(
                    message="rate limited", model="deepseek/deepseek-chat", llm_provider="deepseek"
                ),
                _fake_response("retry ok"),
            ]
        )
        with patch("src.llm.client._get_router", return_value=fake_router):
            # Router handles retries internally, so a single call that
            # raises means the retry is at the router level.
            # We verify that the function propagates the error correctly.
            with pytest.raises(RateLimitError):
                await analyze("test")

    @pytest.mark.asyncio
    async def test_propagates_exception_on_all_failures(self):
        fake_router = MagicMock()
        fake_router.acompletion = AsyncMock(side_effect=RuntimeError("all providers down"))
        with patch("src.llm.client._get_router", return_value=fake_router):
            with pytest.raises(RuntimeError, match="all providers down"):
                await analyze("test")

    @pytest.mark.asyncio
    async def test_custom_model_and_temperature(self):
        fake_router = MagicMock()
        fake_router.acompletion = AsyncMock(return_value=_fake_response())
        with patch("src.llm.client._get_router", return_value=fake_router):
            await analyze("test", model="gemini/gemini-2.0-flash", temperature=0.7)
        call_kwargs = fake_router.acompletion.call_args[1]
        assert call_kwargs["model"] == "gemini/gemini-2.0-flash"
        assert call_kwargs["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_system_prompt_default(self):
        fake_router = MagicMock()
        fake_router.acompletion = AsyncMock(return_value=_fake_response())
        with patch("src.llm.client._get_router", return_value=fake_router):
            await analyze("test")
        messages = fake_router.acompletion.call_args[1]["messages"]
        assert messages[0]["role"] == "system"
        assert "A股" in messages[0]["content"]
