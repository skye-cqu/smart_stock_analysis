from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.agents.debate import bull_bear_debate, risk_debate


class TestBullBearDebate:
    @pytest.mark.asyncio
    async def test_returns_string(self):
        llm = AsyncMock(return_value="综合判断：看涨")
        result = await bull_bear_debate("分析摘要", llm)
        assert isinstance(result, str)
        assert "看涨" in result

    @pytest.mark.asyncio
    async def test_llm_called_correct_times(self):
        llm = AsyncMock(return_value="观点")
        await bull_bear_debate("summary", llm, max_rounds=2)
        # 2 rounds * 2 (bull + bear) + 1 synthesis = 5
        assert llm.call_count == 5

    @pytest.mark.asyncio
    async def test_custom_max_rounds(self):
        llm = AsyncMock(return_value="观点")
        await bull_bear_debate("summary", llm, max_rounds=1)
        # 1 round * 2 + 1 synthesis = 3
        assert llm.call_count == 3

    @pytest.mark.asyncio
    async def test_bull_and_bear_interleave(self):
        calls = []

        async def track(prompt, system=""):
            calls.append(system)
            return "观点"

        await bull_bear_debate("summary", track, max_rounds=1)
        # First call should be bull, second bear
        assert "看涨" in calls[0]
        assert "看跌" in calls[1]


class TestRiskDebate:
    @pytest.mark.asyncio
    async def test_returns_string(self):
        llm = AsyncMock(return_value="风险等级：中")
        result = await risk_debate("决策摘要", llm)
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_llm_called_correct_times(self):
        llm = AsyncMock(return_value="观点")
        await risk_debate("summary", llm, max_rounds=1)
        # 1 round * 3 roles + 1 judge = 4
        assert llm.call_count == 4

    @pytest.mark.asyncio
    async def test_three_roles_in_each_round(self):
        systems = []

        async def track(prompt, system=""):
            systems.append(system)
            return "观点"

        await risk_debate("summary", track, max_rounds=1)
        # First 3 calls should be risky, safe, neutral
        role_systems = systems[:3]
        assert any("高风险" in s for s in role_systems)
        assert any("低风险" in s for s in role_systems)
        assert any("平衡" in s for s in role_systems)
