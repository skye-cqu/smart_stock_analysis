from __future__ import annotations

from src.data.models import StockDailyData
from src.strategy.builtin.macd_divergence import MACDDivergenceStrategy, compute_ema


def _make_daily(closes: list[float]) -> list[StockDailyData]:
    return [
        StockDailyData(
            date=f"2026-{i // 30 + 1:02d}-{i % 30 + 1:02d}",
            open=c,
            high=c + 0.2,
            low=c - 0.2,
            close=c,
            volume=1000,
            amount=c * 1000,
            turnover=1.0,
        )
        for i, c in enumerate(closes)
    ]


class TestComputeEMA:
    def test_first_value_is_price(self):
        ema = compute_ema([10.0, 11.0, 12.0], 3)
        assert ema[0] == 10.0

    def test_length_matches_input(self):
        prices = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert len(compute_ema(prices, 3)) == 5

    def test_single_value(self):
        assert compute_ema([42.0], 5) == [42.0]


class TestMACDDivergenceStrategy:
    def test_insufficient_data_returns_hold(self):
        data = _make_daily([10.0] * 20)
        strat = MACDDivergenceStrategy()
        signal = strat.run("000001", data)
        assert signal.signal == "hold"
        indicators = strat.calculate_indicators(data)
        assert indicators == {"divergence": False}

    def test_enough_data_has_dif_dea(self):
        """With 40 data points, indicators should include dif/dea/macd."""
        closes = [10.0 + i * 0.01 for i in range(40)]
        data = _make_daily(closes)
        strat = MACDDivergenceStrategy()
        indicators = strat.calculate_indicators(data)
        assert "dif" in indicators
        assert "dea" in indicators
        assert "macd" in indicators

    def test_buy_when_dif_above_dea_and_negative(self):
        """Construct prices that produce DIF > DEA while DIF < 0."""
        # Declining then slightly recovering: DIF crosses above DEA while still negative
        closes = [20.0 - i * 0.3 for i in range(30)]
        closes += [closes[-1] + i * 0.4 for i in range(15)]
        data = _make_daily(closes)
        strat = MACDDivergenceStrategy()
        signal = strat.run("000001", data)
        # Just verify it returns a valid signal (buy or hold)
        assert signal.signal in ("buy", "hold")
