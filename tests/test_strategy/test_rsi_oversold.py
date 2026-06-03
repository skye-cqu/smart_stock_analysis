from __future__ import annotations

from src.data.models import StockDailyData
from src.strategy.builtin.rsi_oversold import RSIOversoldStrategy, compute_rsi


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


class TestComputeRSI:
    def test_all_gains(self):
        """Monotonically rising prices → RSI = 100."""
        prices = [float(i) for i in range(1, 20)]
        rsi = compute_rsi(prices)
        assert rsi == 100.0

    def test_data_too_short(self):
        assert compute_rsi([1.0, 2.0, 3.0], period=14) is None

    def test_known_rsi_range(self):
        """Alternating up/down should give RSI near 50."""
        prices = [
            10.0,
            11.0,
            10.0,
            11.0,
            10.0,
            11.0,
            10.0,
            11.0,
            10.0,
            11.0,
            10.0,
            11.0,
            10.0,
            11.0,
            10.0,
            11.0,
        ]
        rsi = compute_rsi(prices)
        assert 40 < rsi < 60


class TestRSIOversoldStrategy:
    def test_oversold_buys(self):
        """Falling prices should push RSI below 30 → buy."""
        closes = [20.0 - i * 0.5 for i in range(20)]
        data = _make_daily(closes)
        strat = RSIOversoldStrategy()
        signal = strat.run("000001", data)
        assert signal.signal == "buy"

    def test_overbought_sells(self):
        """Rising prices should push RSI above 70 → sell."""
        closes = [10.0 + i * 1.0 for i in range(20)]
        data = _make_daily(closes)
        strat = RSIOversoldStrategy()
        signal = strat.run("000001", data)
        assert signal.signal == "sell"

    def test_neutral_zone_holds(self):
        """Alternating prices keep RSI in 30-70 → hold."""
        closes = [
            10.0,
            11.0,
            10.0,
            11.0,
            10.0,
            11.0,
            10.0,
            11.0,
            10.0,
            11.0,
            10.0,
            11.0,
            10.0,
            11.0,
            10.0,
            11.0,
        ]
        data = _make_daily(closes)
        strat = RSIOversoldStrategy()
        signal = strat.run("000001", data)
        assert signal.signal == "hold"

    def test_insufficient_data_returns_hold(self):
        data = _make_daily([10.0, 11.0])
        strat = RSIOversoldStrategy()
        signal = strat.run("000001", data)
        assert signal.signal == "hold"

    def test_custom_thresholds(self):
        strat = RSIOversoldStrategy(params={"oversold": 20, "overbought": 80})
        assert strat.oversold == 20
        assert strat.overbought == 80
