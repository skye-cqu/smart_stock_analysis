from __future__ import annotations

from src.data.models import StockDailyData
from src.scoring.technical_scorer import TechnicalScorer


def _make_daily(closes: list[float]) -> list[StockDailyData]:
    return [
        StockDailyData(
            date=f"2026-01-{i + 1:02d}",
            open=c - 0.1,
            high=c + 0.2,
            low=c - 0.2,
            close=c,
            volume=1000,
            amount=c * 1000,
            turnover=1.0,
        )
        for i, c in enumerate(closes)
    ]


class TestTechnicalScorer:
    def test_rising_prices_positive_score(self):
        closes = [10.0 + i * 0.5 for i in range(30)]
        data = _make_daily(closes)
        scorer = TechnicalScorer()
        result = scorer.score(None, data)
        assert result > 0

    def test_falling_prices_applies_ma_penalty(self):
        closes = [30.0 - i * 0.5 for i in range(30)]
        data = _make_daily(closes)
        scorer = TechnicalScorer()
        result = scorer.score(None, data)
        # RSI ~10 (oversold) gives +40, MA5<MA20 gives -20, net >= -20
        assert -100 <= result <= 100

    def test_insufficient_data_returns_zero(self):
        closes = [10.0 + i * 0.1 for i in range(15)]
        data = _make_daily(closes)
        scorer = TechnicalScorer()
        result = scorer.score(None, data)
        assert result == 0.0

    def test_score_clamped(self):
        closes = [10.0 + i * 2.0 for i in range(30)]
        data = _make_daily(closes)
        scorer = TechnicalScorer()
        result = scorer.score(None, data)
        assert -100 <= result <= 100

    def test_flat_prices_moderate_score(self):
        closes = [10.0] * 25
        data = _make_daily(closes)
        scorer = TechnicalScorer()
        result = scorer.score(None, data)
        assert -50 <= result <= 50
