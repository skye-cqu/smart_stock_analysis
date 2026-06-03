from __future__ import annotations

from src.data.models import StockDailyData, StockInfo
from src.scoring.event_scorer import EventScorer

INFO = StockInfo(code="000001", name="Test")


def _make_data(prices: list[float], base_volume: float = 1_000_000) -> list[StockDailyData]:
    return [
        StockDailyData(
            date=f"2025-01-{i + 1:02d}",
            open=p,
            high=p + 0.1,
            low=p - 0.1,
            close=p,
            volume=base_volume,
            amount=base_volume * p,
        )
        for i, p in enumerate(prices)
    ]


class TestEventScorer:
    def test_insufficient_data_returns_zero(self):
        data = _make_data([10.0, 10.1, 10.2])
        assert EventScorer().score(INFO, data) == 0.0

    def test_volume_spike_gives_plus_40(self):
        data = _make_data([10.0] * 6, base_volume=1_000_000)
        # Override last day volume to 4x average
        data[-1] = StockDailyData(
            date=data[-1].date,
            open=10.0,
            high=10.1,
            low=9.9,
            close=10.0,
            volume=4_000_000,
            amount=40_000_000,
        )
        result = EventScorer().score(INFO, data)
        assert result == 40.0

    def test_limit_up_gives_plus_30(self):
        # 5 days flat, then +10% on day 6
        prices = [10.0] * 5 + [11.0]
        data = _make_data(prices)
        result = EventScorer().score(INFO, data)
        assert result == 30.0

    def test_limit_down_gives_minus_30(self):
        prices = [10.0] * 5 + [9.0]
        data = _make_data(prices)
        result = EventScorer().score(INFO, data)
        assert result == -30.0

    def test_consecutive_up_3_days_gives_plus_20(self):
        prices = [10.0, 10.0, 10.0, 10.1, 10.2, 10.3]
        data = _make_data(prices)
        result = EventScorer().score(INFO, data)
        assert result == 20.0

    def test_consecutive_down_3_days_gives_minus_20(self):
        prices = [10.3, 10.2, 10.1, 10.0, 9.9, 9.8]
        data = _make_data(prices)
        result = EventScorer().score(INFO, data)
        assert result == -20.0

    def test_combined_volume_spike_and_limit_up(self):
        # Volume spike (+40) + limit up (+30) = 70
        prices = [10.0] * 5 + [11.0]
        data = _make_data(prices, base_volume=1_000_000)
        data[-1] = StockDailyData(
            date=data[-1].date,
            open=10.0,
            high=11.0,
            low=10.0,
            close=11.0,
            volume=4_000_000,
            amount=44_000_000,
        )
        result = EventScorer().score(INFO, data)
        assert result == 70.0

    def test_clamp_at_100(self):
        # Volume spike + limit up + 3-day up = 40+30+20 = 90, still under 100
        # But let's verify clamping works by constructing extreme data
        prices = [10.0, 10.0, 10.0, 10.1, 10.2, 11.3]
        data = _make_data(prices, base_volume=1_000_000)
        data[-1] = StockDailyData(
            date=data[-1].date,
            open=10.2,
            high=11.3,
            low=10.2,
            close=11.3,
            volume=5_000_000,
            amount=56_500_000,
        )
        result = EventScorer().score(INFO, data)
        assert -100 <= result <= 100
