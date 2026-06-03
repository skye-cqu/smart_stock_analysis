from __future__ import annotations

from src.data.models import StockDailyData
from src.strategy.builtin.volume_breakout import VolumeBreakoutStrategy


def _make_daily(closes: list[float], volumes: list[float]) -> list[StockDailyData]:
    return [
        StockDailyData(
            date=f"2026-{i // 30 + 1:02d}-{i % 30 + 1:02d}",
            open=c,
            high=c + 0.1,
            low=c - 0.1,
            close=c,
            volume=v,
            amount=c * v,
            turnover=1.0,
        )
        for i, (c, v) in enumerate(zip(closes, volumes, strict=False))
    ]


class TestVolumeBreakoutStrategy:
    def test_breakout_with_volume_surge_buys(self):
        """Close above recent high AND volume >= 2x avg → buy."""
        closes = [10.0] * 20 + [12.0]
        volumes = [1000.0] * 20 + [3000.0]
        data = _make_daily(closes, volumes)
        strat = VolumeBreakoutStrategy()
        signal = strat.run("000001", data)
        assert signal.signal == "buy"
        assert signal.strength > 0

    def test_no_breakout_holds(self):
        """Close within recent range → hold."""
        closes = [
            10.0,
            10.5,
            10.2,
            10.8,
            10.3,
            10.1,
            10.4,
            10.6,
            10.2,
            10.5,
            10.3,
            10.1,
            10.4,
            10.7,
            10.2,
            10.5,
            10.3,
            10.6,
            10.4,
            10.2,
            10.3,
        ]
        volumes = [1000.0] * 21
        data = _make_daily(closes, volumes)
        strat = VolumeBreakoutStrategy()
        signal = strat.run("000001", data)
        assert signal.signal == "hold"

    def test_breakout_without_volume_surge_holds(self):
        """Close above high but volume < 2x → hold."""
        closes = [10.0] * 20 + [12.0]
        volumes = [1000.0] * 20 + [1500.0]  # only 1.5x, not 2x
        data = _make_daily(closes, volumes)
        strat = VolumeBreakoutStrategy()
        signal = strat.run("000001", data)
        assert signal.signal == "hold"

    def test_insufficient_data_returns_hold(self):
        closes = [10.0] * 5
        volumes = [1000.0] * 5
        data = _make_daily(closes, volumes)
        strat = VolumeBreakoutStrategy()
        signal = strat.run("000001", data)
        assert signal.signal == "hold"

    def test_custom_params(self):
        strat = VolumeBreakoutStrategy(params={"volume_ratio": 3.0, "lookback": 10})
        assert strat.volume_ratio == 3.0
        assert strat.lookback == 10
