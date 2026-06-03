from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.data.models import ScoreResult, StockDailyData, StockInfo


def _make_daily_data(n: int = 40) -> list[StockDailyData]:
    data = []
    for i in range(n):
        p = 10.0 + i * 0.05
        data.append(
            StockDailyData(
                date=f"2026-01-{i + 1:02d}",
                open=p - 0.05,
                high=p + 0.2,
                low=p - 0.2,
                close=p,
                volume=1000000 + i * 50000,
                amount=p * (1000000 + i * 50000),
                turnover=2.0,
            )
        )
    return data


def _make_info() -> StockInfo:
    return StockInfo(
        code="000001",
        name="平安银行",
        industry="银行",
        pe_ratio=5.0,
        pb_ratio=0.6,
        roe=12.0,
    )


def _make_score() -> ScoreResult:
    return ScoreResult(
        total=65.0,
        technical=70.0,
        capital_flow=60.0,
        fundamental=55.0,
        sector=50.0,
        event=45.0,
    )


class TestQuickModeIntegration:
    """Integration test: mock DataProvider + LLM, but use real strategy + scoring."""

    @pytest.mark.asyncio
    async def test_quick_mode_end_to_end(self, sample_daily_data):
        provider = MagicMock()
        provider.get_daily_data.return_value = _make_daily_data(40)
        provider.get_stock_info.return_value = _make_info()

        llm_output = '{"technical_view": "看涨趋势，均线多头排列", "recommendation": "买入", "risk_notes": "注意回调风险"}'
        parsed_result = MagicMock(recommendation="买入")

        with (
            patch("src.pipeline.runner._get_provider", return_value=provider),
            patch("src.agents.reflection.verify_decisions", new_callable=AsyncMock),
            patch("src.llm.client.analyze", new_callable=AsyncMock) as mock_analyze,
            patch("src.llm.parsers.parse_analysis", return_value=parsed_result),
            patch("src.report.generator.generate_report", return_value="reports/000001.md"),
        ):
            mock_analyze.return_value = llm_output
            from src.pipeline.runner import run_pipeline

            result = await run_pipeline("000001", mode="quick")

        assert result.success is True
        assert result.result is not None
        assert result.result.stock_code == "000001"
        assert result.result.stock_name == "平安银行"
        assert result.result.current_price > 0
        assert len(result.result.strategy_signals) > 0
        assert result.result.recommendation == "买入"
        # Score should be computed by real scorer
        assert isinstance(result.result.score, ScoreResult)

    @pytest.mark.asyncio
    async def test_quick_mode_with_no_signals(self):
        """Pipeline works even when no strategy signals are generated."""
        provider = MagicMock()
        # Short data → strategies may not generate signals
        short_data = _make_daily_data(5)
        provider.get_daily_data.return_value = short_data
        provider.get_stock_info.return_value = _make_info()

        with (
            patch("src.pipeline.runner._get_provider", return_value=provider),
            patch("src.agents.reflection.verify_decisions", new_callable=AsyncMock),
            patch("src.llm.client.analyze", new_callable=AsyncMock) as mock_analyze,
            patch("src.llm.parsers.parse_analysis", return_value=MagicMock(recommendation="持有")),
            patch("src.report.generator.generate_report", return_value="reports/000001.md"),
        ):
            mock_analyze.return_value = (
                '{"technical_view": "数据不足", "recommendation": "持有", "risk_notes": "观望"}'
            )
            from src.pipeline.runner import run_pipeline

            result = await run_pipeline("000001")

        assert result.success is True
        # Should still have a result even with limited data
        assert result.result is not None


class TestPipelineResultStructure:
    @pytest.mark.asyncio
    async def test_result_has_all_required_fields(self):
        provider = MagicMock()
        provider.get_daily_data.return_value = _make_daily_data(30)
        provider.get_stock_info.return_value = _make_info()

        with (
            patch("src.pipeline.runner._get_provider", return_value=provider),
            patch("src.agents.reflection.verify_decisions", new_callable=AsyncMock),
            patch("src.llm.client.analyze", new_callable=AsyncMock) as mock_analyze,
            patch("src.llm.parsers.parse_analysis", return_value=MagicMock(recommendation="买入")),
            patch("src.report.generator.generate_report", return_value="reports/000001.md"),
        ):
            mock_analyze.return_value = (
                '{"technical_view": "test", "recommendation": "买入", "risk_notes": "test"}'
            )
            from src.pipeline.runner import run_pipeline

            result = await run_pipeline("000001")

        r = result.result
        assert r.stock_code == "000001"
        assert r.stock_name == "平安银行"
        assert r.current_price > 0
        assert r.score is not None
        assert r.score.total != 0 or r.score.technical != 0  # at least one dimension scored
        assert r.llm_analysis  # non-empty
        assert r.recommendation
