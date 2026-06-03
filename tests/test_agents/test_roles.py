from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.agents.roles import ALL_ANALYSTS, create_analyst
from src.agents.schemas import AnalystReport
from src.data.models import AnalysisResult, ScoreResult, StrategySignal


def _make_result_and_score():
    score = ScoreResult(
        total=65, technical=70, capital_flow=60, fundamental=55, sector=50, event=45
    )
    result = AnalysisResult(
        stock_code="000001",
        stock_name="平安银行",
        current_price=12.5,
        score=score,
        strategy_signals=[
            StrategySignal(
                strategy_name="ma_cross", stock_code="000001", signal="buy", strength=0.8
            ),
        ],
        llm_analysis="test",
        recommendation="买入",
    )
    return result, score


class TestCreateAnalyst:
    @pytest.mark.asyncio
    async def test_valid_json_returns_report(self):
        mock_llm = AsyncMock(
            return_value='{"analysis": "看涨趋势明显", "signal": "看涨", "confidence": 0.8, "key_points": ["均线多头", "放量上涨"]}'
        )
        factory = create_analyst("测试分析师", "测试用", "技术面")
        analyze = factory(mock_llm)
        result, score = _make_result_and_score()
        report = await analyze(result, score)
        assert isinstance(report, AnalystReport)
        assert report.role == "测试分析师"
        assert report.signal == "看涨"
        assert report.confidence == 0.8

    @pytest.mark.asyncio
    async def test_garbage_json_fallback(self):
        mock_llm = AsyncMock(return_value="这不是JSON")
        factory = create_analyst("测试分析师", "测试用", "技术面")
        analyze = factory(mock_llm)
        result, score = _make_result_and_score()
        report = await analyze(result, score)
        assert report.signal == "中性"
        assert report.confidence == 0.3

    @pytest.mark.asyncio
    async def test_markdown_json_block(self):
        mock_llm = AsyncMock(
            return_value='```json\n{"analysis": "震荡", "signal": "中性", "confidence": 0.5, "key_points": ["test"]}\n```'
        )
        factory = create_analyst("测试", "test", "test")
        analyze = factory(mock_llm)
        result, score = _make_result_and_score()
        report = await analyze(result, score)
        assert report.analysis == "震荡"
        assert report.key_points == ["test"]


class TestAllAnalysts:
    def test_seven_analysts(self):
        assert len(ALL_ANALYSTS) == 7

    @pytest.mark.asyncio
    async def test_each_analyst_returns_report(self):
        mock_llm = AsyncMock(
            return_value='{"analysis": "A"*100, "signal": "中性", "confidence": 0.5, "key_points": ["p1"]}'
        )
        result, score = _make_result_and_score()
        for factory_fn in ALL_ANALYSTS:
            analyze = factory_fn(mock_llm)
            report = await analyze(result, score)
            assert isinstance(report, AnalystReport)
            assert report.role
            assert report.confidence >= 0

    @pytest.mark.asyncio
    async def test_analyst_prompt_contains_stock_info(self):
        captured = []

        async def capture(prompt, system=""):
            captured.append(prompt)
            return '{"analysis": "test", "signal": "中性", "confidence": 0.5, "key_points": ["p1"]}'

        factory_fn = ALL_ANALYSTS[0]
        analyze = factory_fn(capture)
        result, score = _make_result_and_score()
        await analyze(result, score)
        assert any("000001" in p for p in captured)
        assert any("平安银行" in p for p in captured)
