from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.data.models import ScoreResult, StockDailyData, StockInfo, StrategySignal


def _make_daily_data(n: int = 30) -> list[StockDailyData]:
    data = []
    for i in range(n):
        p = 10.0 + i * 0.1
        data.append(
            StockDailyData(
                date=f"2026-01-{i + 1:02d}",
                open=p - 0.05,
                high=p + 0.2,
                low=p - 0.2,
                close=p,
                volume=1000000 + i * 10000,
                amount=p * (1000000 + i * 10000),
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


def _make_signals() -> list[StrategySignal]:
    return [
        StrategySignal(
            strategy_name="ma_cross",
            stock_code="000001",
            signal="buy",
            strength=0.8,
        )
    ]


def _patch_pipeline(provider, registry, scorer):
    """Return a nested context manager that patches all pipeline singletons + lazy imports."""
    import contextlib

    @contextlib.contextmanager
    def _ctx():
        with (
            patch("src.pipeline.runner._get_provider", return_value=provider),
            patch("src.pipeline.runner._get_registry", return_value=registry),
            patch("src.pipeline.runner._get_scorer", return_value=scorer),
            patch("src.agents.reflection.verify_decisions", new_callable=AsyncMock),
            patch("src.llm.client.analyze", new_callable=AsyncMock) as mock_analyze,
            patch("src.llm.parsers.parse_analysis") as mock_parse,
            patch("src.strategy.builtin.ma_cross.compute_ma") as mock_ma,
            patch("src.strategy.builtin.rsi_oversold.compute_rsi") as mock_rsi,
            patch("src.report.generator.generate_report") as mock_report,
        ):
            mock_analyze.return_value = (
                '{"technical_view": "看涨", "recommendation": "买入", "risk_notes": "注意"}'
            )
            mock_parse.return_value = MagicMock(recommendation="买入")
            mock_ma.return_value = [None, None, None, None, 12.0]  # last 5 values
            mock_rsi.return_value = 55.0
            mock_report.return_value = "reports/000001.md"
            yield mock_analyze

    return _ctx()


class TestRunPipelineQuick:
    @pytest.mark.asyncio
    async def test_success_returns_pipeline_result(self, sample_daily_data):
        provider = MagicMock()
        provider.get_daily_data.return_value = sample_daily_data
        provider.get_stock_info.return_value = _make_info()

        registry = MagicMock()
        registry.run_all.return_value = _make_signals()

        scorer = MagicMock()
        scorer.score.return_value = _make_score()

        with _patch_pipeline(provider, registry, scorer) as mock_analyze:
            from src.pipeline.runner import run_pipeline

            result = await run_pipeline("000001", mode="quick")

        assert result.success is True
        assert result.stock_code == "000001"
        assert result.result is not None
        assert result.result.stock_code == "000001"
        assert result.result.recommendation == "买入"
        mock_analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_daily_data_returns_failure(self):
        provider = MagicMock()
        provider.get_daily_data.return_value = []

        registry = MagicMock()
        scorer = MagicMock()

        with _patch_pipeline(provider, registry, scorer):
            from src.pipeline.runner import run_pipeline

            result = await run_pipeline("000001")

        assert result.success is False
        assert "No data" in result.error

    @pytest.mark.asyncio
    async def test_missing_stock_info_uses_unknown(self, sample_daily_data):
        provider = MagicMock()
        provider.get_daily_data.return_value = sample_daily_data
        provider.get_stock_info.return_value = None

        registry = MagicMock()
        registry.run_all.return_value = []

        scorer = MagicMock()
        scorer.score.return_value = _make_score()

        with _patch_pipeline(provider, registry, scorer):
            from src.pipeline.runner import run_pipeline

            result = await run_pipeline("000001")

        assert result.success is True
        assert result.result.stock_name == "Unknown"

    @pytest.mark.asyncio
    async def test_llm_failure_returns_failure(self, sample_daily_data):
        provider = MagicMock()
        provider.get_daily_data.return_value = sample_daily_data
        provider.get_stock_info.return_value = _make_info()

        registry = MagicMock()
        registry.run_all.return_value = _make_signals()

        scorer = MagicMock()
        scorer.score.return_value = _make_score()

        with (
            patch("src.pipeline.runner._get_provider", return_value=provider),
            patch("src.pipeline.runner._get_registry", return_value=registry),
            patch("src.pipeline.runner._get_scorer", return_value=scorer),
            patch("src.agents.reflection.verify_decisions", new_callable=AsyncMock),
            patch("src.llm.client.analyze", new_callable=AsyncMock) as mock_analyze,
            patch("src.strategy.builtin.ma_cross.compute_ma", return_value=[None] * 4 + [12.0]),
            patch("src.strategy.builtin.rsi_oversold.compute_rsi", return_value=55.0),
        ):
            mock_analyze.side_effect = RuntimeError("LLM API error")
            from src.pipeline.runner import run_pipeline

            result = await run_pipeline("000001")

        assert result.success is False
        assert result.error == "Pipeline execution failed"

    @pytest.mark.asyncio
    async def test_passes_correct_dates(self, sample_daily_data):
        provider = MagicMock()
        provider.get_daily_data.return_value = sample_daily_data
        provider.get_stock_info.return_value = _make_info()

        registry = MagicMock()
        registry.run_all.return_value = []

        scorer = MagicMock()
        scorer.score.return_value = _make_score()

        with _patch_pipeline(provider, registry, scorer):
            from src.pipeline.runner import run_pipeline

            await run_pipeline("000001")

        call_args = provider.get_daily_data.call_args
        stock_code_arg = call_args[0][0]
        start_date_arg = call_args[0][1]
        end_date_arg = call_args[0][2]

        assert stock_code_arg == "000001"
        assert len(start_date_arg) == 10  # YYYY-MM-DD
        assert len(end_date_arg) == 10


class TestPipelineResult:
    def test_dataclass_fields(self):
        from src.pipeline.runner import PipelineResult

        r = PipelineResult(stock_code="000001", success=True)
        assert r.stock_code == "000001"
        assert r.success is True
        assert r.result is None
        assert r.error == ""

    def test_with_error(self):
        from src.pipeline.runner import PipelineResult

        r = PipelineResult(stock_code="600519", success=False, error="No data available")
        assert r.success is False
        assert "No data" in r.error
