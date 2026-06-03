from __future__ import annotations

from src.data.models import StockDailyData
from src.strategy.builtin.ma_cross import MACrossStrategy, compute_ma


def _make_daily(closes: list[float]) -> list[StockDailyData]:
    data = []
    for i, c in enumerate(closes):
        data.append(
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
        )
    return data


class TestComputeMA:
    def test_known_values(self):
        prices = [10.0, 11.0, 12.0, 13.0, 14.0]
        ma3 = compute_ma(prices, 3)
        assert ma3[0] is None
        assert ma3[1] is None
        assert ma3[2] == 11.0
        assert ma3[3] == 12.0
        assert ma3[4] == 13.0

    def test_period_greater_than_data(self):
        ma = compute_ma([1.0, 2.0], 5)
        assert all(v is None for v in ma)

    def test_period_1_returns_prices(self):
        prices = [5.0, 6.0, 7.0]
        assert compute_ma(prices, 1) == [5.0, 6.0, 7.0]


class TestMACrossStrategy:
    def test_golden_cross_buys(self):
        """Build data where MA5 crosses above MA20 at the end."""
        # Flat at 10 for 24 days, then spike to 15 on day 25
        closes = [10.0] * 24 + [15.0]
        data = _make_daily(closes)
        strat = MACrossStrategy()
        signal = strat.run("000001", data)
        assert signal.signal == "buy"
        assert signal.strength > 0

    def test_death_cross_sells(self):
        """Build data where MA5 crosses below MA20."""
        closes = [15.0] * 24 + [10.0]
        data = _make_daily(closes)
        strat = MACrossStrategy()
        signal = strat.run("000001", data)
        assert signal.signal == "sell"

    def test_hold_when_no_crossover(self):
        """Steadily rising prices: MA5 always above MA20, no crossover."""
        closes = [10.0 + i * 0.05 for i in range(30)]
        data = _make_daily(closes)
        strat = MACrossStrategy()
        signal = strat.run("000001", data)
        assert signal.signal == "hold"

    def test_insufficient_data_returns_hold(self):
        data = _make_daily([10.0] * 5)
        strat = MACrossStrategy()
        signal = strat.run("000001", data)
        assert signal.signal == "hold"
        assert signal.strength == 0.0

    def test_custom_params(self):
        strat = MACrossStrategy(params={"short_period": 3, "long_period": 10})
        assert strat.short_period == 3
        assert strat.long_period == 10
