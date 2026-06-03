from __future__ import annotations

import pytest

from src.data.models import StockDailyData
from src.risk.manager import assess_risk, check_stop_loss


def _make_data(n: int, close: float = 10.0, amplitude: float = 0.0) -> list[StockDailyData]:
    """Generate n days of data. If amplitude > 0, prices oscillate."""
    import math

    return [
        StockDailyData(
            date=f"2024-01-{i + 1:02d}",
            open=close + amplitude * math.sin(i),
            high=close + amplitude * math.sin(i) + 0.1,
            low=close + amplitude * math.sin(i) - 0.1,
            close=close + amplitude * math.sin(i),
            volume=1_000_000,
            amount=10_000_000,
        )
        for i in range(n)
    ]


class TestAssessRisk:
    def test_single_data_point(self):
        data = _make_data(1)
        result = assess_risk(data, entry_price=10.0)
        assert result.volatility == 0.0
        assert result.max_position_pct == 0.25
        assert result.risk_level == "低"
        assert result.stop_loss_price == pytest.approx(9.2, abs=0.001)

    def test_flat_data_low_volatility(self):
        data = _make_data(30, close=10.0, amplitude=0.0)
        result = assess_risk(data, entry_price=10.0)
        assert result.volatility == 0.0
        assert result.max_position_pct == 0.25
        assert result.risk_level == "低"

    def test_moderate_volatility(self):
        # amplitude=0.15 creates moderate daily swings
        data = _make_data(60, close=10.0, amplitude=0.15)
        result = assess_risk(data, entry_price=10.0)
        assert result.volatility > 0.0
        assert result.max_position_pct <= 0.25
        assert result.risk_level in ("低", "中")

    def test_high_amplitude_high_volatility(self):
        # Large oscillations → high vol
        data = _make_data(60, close=10.0, amplitude=2.0)
        result = assess_risk(data, entry_price=10.0)
        assert result.volatility > 0.15
        assert result.max_position_pct < 0.25
        assert result.risk_level in ("中", "高", "极高")

    def test_stop_loss_price_is_8_pct_below_entry(self):
        data = _make_data(30)
        result = assess_risk(data, entry_price=100.0)
        assert result.stop_loss_price == pytest.approx(92.0, abs=0.01)

    def test_stop_loss_price_for_different_entry(self):
        data = _make_data(30)
        result = assess_risk(data, entry_price=50.0)
        assert result.stop_loss_price == pytest.approx(46.0, abs=0.01)

    def test_max_position_decreases_with_volatility(self):
        flat = assess_risk(_make_data(60, amplitude=0.0), 10.0)
        volatile = assess_risk(_make_data(60, amplitude=1.5), 10.0)
        assert flat.max_position_pct >= volatile.max_position_pct


class TestCheckStopLoss:
    def test_fixed_stop_loss_triggered(self):
        assert (
            check_stop_loss(current_price=91.0, entry_price=100.0, highest_since_entry=105.0)
            is True
        )

    def test_trailing_stop_loss_triggered(self):
        # highest=100, 95% = 95; current=94 → triggers
        assert (
            check_stop_loss(current_price=94.0, entry_price=100.0, highest_since_entry=100.0)
            is True
        )

    def test_no_stop_loss_triggered(self):
        assert (
            check_stop_loss(current_price=96.0, entry_price=100.0, highest_since_entry=100.0)
            is False
        )

    def test_price_at_exact_stop_boundary(self):
        # entry*0.92 = 92.0, current=92.0 → NOT triggered by fixed stop (strictly less than)
        # But trailing stop: 100*0.95=95.0, 92<95 → triggered
        # Use highest=92 so trailing is 92*0.95=87.4, 92>87.4 → not triggered
        assert (
            check_stop_loss(current_price=92.0, entry_price=100.0, highest_since_entry=92.0)
            is False
        )

    def test_price_just_below_stop(self):
        assert (
            check_stop_loss(current_price=91.99, entry_price=100.0, highest_since_entry=100.0)
            is True
        )

    def test_trailing_with_higher_peak(self):
        # Entry 100, ran up to 120, trailing stop = 120*0.95 = 114
        assert (
            check_stop_loss(current_price=113.0, entry_price=100.0, highest_since_entry=120.0)
            is True
        )

    def test_no_stop_when_price_above_both(self):
        assert (
            check_stop_loss(current_price=105.0, entry_price=100.0, highest_since_entry=110.0)
            is False
        )
