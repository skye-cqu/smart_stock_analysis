from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.orchestrator import AgentOrchestrator
from src.agents.schemas import PortfolioDecision, Recommendation
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


def _good_llm_response(prompt, system=""):
    if "最终投资决策" in prompt or "投资总监" in system:
        return '{"recommendation": "买入", "confidence": 0.8, "position_pct": 30, "reasoning": "看好", "risk_notes": "注意回调", "key_factors": ["均线多头"]}'
    return '{"analysis": "分析内容充足，趋势明显，技术指标支持上涨。" * 5, "signal": "看涨", "confidence": 0.7, "key_points": ["要点1"]}'


def _garbage_final_llm(prompt, system=""):
    if "最终投资决策" in prompt or "投资总监" in system:
        return "这不是有效的JSON"
    return '{"analysis": "good analysis" * 10, "signal": "看涨", "confidence": 0.7, "key_points": ["p1"]}'


class TestAgentOrchestrator:
    @pytest.mark.asyncio
    async def test_returns_portfolio_decision(self, tmp_path):
        with patch("src.agents.orchestrator.TradingMemoryLog") as MockMem:
            MockMem.return_value = MagicMock(
                get_past_context=MagicMock(return_value=""),
                store_decision=MagicMock(return_value=1),
            )
            llm = AsyncMock(side_effect=_good_llm_response)
            orch = AgentOrchestrator(llm)
            orch.memory = MockMem.return_value
            result, score = _make_result_and_score()
            decision = await orch.run_full_analysis(result, score)
            assert isinstance(decision, PortfolioDecision)
            assert decision.recommendation is Recommendation.BUY

    @pytest.mark.asyncio
    async def test_garbage_final_decision_fallback(self, tmp_path):
        with patch("src.agents.orchestrator.TradingMemoryLog") as MockMem:
            mem_mock = MagicMock(
                get_past_context=MagicMock(return_value=""),
                store_decision=MagicMock(return_value=1),
            )
            MockMem.return_value = mem_mock
            llm = AsyncMock(side_effect=_garbage_final_llm)
            orch = AgentOrchestrator(llm)
            orch.memory = mem_mock
            result, score = _make_result_and_score()
            decision = await orch.run_full_analysis(result, score)
            assert decision.recommendation is Recommendation.HOLD
            assert decision.confidence == 0.3

    @pytest.mark.asyncio
    async def test_stores_decision_in_memory(self):
        mem_mock = MagicMock(
            get_past_context=MagicMock(return_value=""),
            store_decision=MagicMock(return_value=1),
        )
        llm = AsyncMock(side_effect=_good_llm_response)
        orch = AgentOrchestrator(llm)
        orch.memory = mem_mock
        result, score = _make_result_and_score()
        await orch.run_full_analysis(result, score)
        mem_mock.store_decision.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyst_exceptions_graceful(self):
        mem_mock = MagicMock(
            get_past_context=MagicMock(return_value=""),
            store_decision=MagicMock(return_value=1),
        )

        call_count = 0

        async def mixed_llm(prompt, system=""):
            nonlocal call_count
            call_count += 1
            if "最终投资决策" in prompt or "投资总监" in system:
                return '{"recommendation": "持有", "confidence": 0.5, "position_pct": 10, "reasoning": "观望", "risk_notes": "不确定", "key_factors": ["数据不足"]}'
            if call_count <= 7:
                raise RuntimeError("LLM timeout")
            return '{"grade":"C","score":60,"issues":[],"summary":"ok"}'

        orch = AgentOrchestrator(mixed_llm)
        orch.memory = mem_mock
        result, score = _make_result_and_score()
        decision = await orch.run_full_analysis(result, score)
        assert isinstance(decision, PortfolioDecision)
