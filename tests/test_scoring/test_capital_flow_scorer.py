from __future__ import annotations

from src.data.models import StockDailyData
from src.scoring.capital_flow_scorer import CapitalFlowScorer


def _make_daily(
    closes: list[float],
    volumes: list[float] | None = None,
    turnovers: list[float] | None = None,
) -> list[StockDailyData]:
    if volumes is None:
        volumes = [1000.0] * len(closes)
    if turnovers is None:
        turnovers = [1.0] * len(closes)
    return [
        StockDailyData(
            date=f"2026-01-{i + 1:02d}",
            open=c - 0.1,
            high=c + 0.2,
            low=c - 0.2,
            close=c,
            volume=v,
            amount=c * v,
            turnover=t,
        )
        for i, (c, v, t) in enumerate(zip(closes, volumes, turnovers, strict=False))
    ]


class TestCapitalFlowScorer:
    def test_volume_surge_positive(self):
        closes = [10.0] * 10 + [10.5, 11.0, 11.5, 12.0, 12.5]
        volumes = [1000.0] * 10 + [3000.0, 3500.0, 4000.0, 3000.0, 3500.0]
        data = _make_daily(closes, volumes)
        scorer = CapitalFlowScorer()
        result = scorer.score(None, data)
        assert result > 0

    def test_declining_volume_and_price_negative(self):
        closes = [20.0 - i * 0.5 for i in range(15)]
        volumes = [100.0] * 15
        data = _make_daily(closes, volumes)
        scorer = CapitalFlowScorer()
        result = scorer.score(None, data)
        assert result < 0

    def test_insufficient_data_returns_zero(self):
        data = _make_daily([10.0, 11.0, 12.0])
        scorer = CapitalFlowScorer()
        result = scorer.score(None, data)
        assert result == 0.0

    def test_score_clamped(self):
        closes = [10.0] * 10 + [20.0] * 5
        volumes = [100.0] * 10 + [99999.0] * 5
        data = _make_daily(closes, volumes)
        scorer = CapitalFlowScorer()
        result = scorer.score(None, data)
        assert -100 <= result <= 100

    def test_high_turnover_contributes(self):
        closes = [10.0 + i * 0.1 for i in range(10)]
        volumes = [2000.0] * 10
        turnovers = [8.0] * 10
        data = _make_daily(closes, volumes, turnovers)
        scorer = CapitalFlowScorer()
        result = scorer.score(None, data)
        assert result > 0
