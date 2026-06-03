from __future__ import annotations

import pytest

from src.data.models import AnalysisResult, ScoreResult, StockDailyData, StockInfo, StrategySignal


@pytest.fixture
def sample_stock_code() -> str:
    return "000001"


@pytest.fixture
def sample_stock_codes() -> list[str]:
    return ["000001", "600519", "000858"]


@pytest.fixture
def sample_stock_info() -> StockInfo:
    return StockInfo(
        code="000001",
        name="平安银行",
        industry="银行",
        market_cap=2000.0,
        pe_ratio=5.0,
        pb_ratio=0.6,
        roe=12.0,
        total_share=194.0,
        float_share=194.0,
    )


@pytest.fixture
def sample_daily_data() -> list[StockDailyData]:
    """Generate 30 days of synthetic daily data with upward trend."""
    data = []
    base_price = 10.0
    for i in range(30):
        price = base_price + i * 0.1
        data.append(
            StockDailyData(
                date=f"2026-01-{i + 1:02d}",
                open=price - 0.05,
                high=price + 0.2,
                low=price - 0.2,
                close=price,
                volume=1000000 + i * 10000,
                amount=price * (1000000 + i * 10000),
                turnover=2.0,
            )
        )
    return data


@pytest.fixture
def sample_score_result() -> ScoreResult:
    return ScoreResult(
        total=65.0,
        technical=70.0,
        capital_flow=60.0,
        fundamental=55.0,
        sector=50.0,
        event=45.0,
        veto=False,
        veto_reason="",
    )


@pytest.fixture
def sample_analysis_result(sample_score_result) -> AnalysisResult:
    return AnalysisResult(
        stock_code="000001",
        stock_name="平安银行",
        current_price=12.5,
        score=sample_score_result,
        strategy_signals=[
            StrategySignal(
                strategy_name="ma_cross",
                stock_code="000001",
                signal="buy",
                strength=0.8,
                indicators={"ma_s": 12.5, "ma_l": 12.0},
            )
        ],
        llm_analysis="Test analysis",
        recommendation="买入",
    )
