from __future__ import annotations

import math

from src.backtest.engine import (
    COMMISSION,
    SLIPPAGE,
    run_backtest,
)
from src.data.models import StockDailyData, StrategySignal
from src.strategy.base import BaseStrategy


class _MockStrategy(BaseStrategy):
    """Generates buy on `buy_day`, sell on `sell_day`, hold otherwise."""

    name = "mock"

    def __init__(self, buy_day: int = 4, sell_day: int = 8):
        super().__init__()
        self.buy_day = buy_day
        self.sell_day = sell_day
        self._call_count = 0

    def calculate_indicators(self, data: list[StockDailyData]) -> dict:
        return {}

    def generate_signal(self, data: list[StockDailyData], indicators: dict) -> StrategySignal:
        self._call_count += 1
        len(data) - 1  # 0-indexed relative to full dataset minus 1
        # We track via the total length seen so far (data[:i+1] for day i)
        # Day i corresponds to len(data) - 1 being the "current" day index in the original list
        # But we can't know the original list length. Use the fact that
        # each call adds one element: call_count = i (since we start from i=1)
        idx = self._call_count  # 1-indexed: first call is day 1 (data[0:2])
        if idx == self.buy_day:
            return StrategySignal(strategy_name="mock", stock_code="", signal="buy")
        elif idx == self.sell_day:
            return StrategySignal(strategy_name="mock", stock_code="", signal="sell")
        return StrategySignal(strategy_name="mock", stock_code="", signal="hold")


def _make_uptrend_data(n: int = 12, start: float = 10.0, step: float = 0.5) -> list[StockDailyData]:
    """Monotonically increasing prices."""
    return [
        StockDailyData(
            date=f"2024-01-{i + 1:02d}",
            open=start + i * step,
            high=start + i * step + 0.2,
            low=start + i * step - 0.2,
            close=start + i * step,
            volume=1_000_000,
            amount=10_000_000,
        )
        for i in range(n)
    ]


class TestRunBacktest:
    def test_buy_and_sell_generates_two_trades(self):
        data = _make_uptrend_data(12)
        strategy = _MockStrategy(buy_day=4, sell_day=8)
        result = run_backtest(
            stock_code="000001",
            start_date="2024-01-01",
            end_date="2024-01-12",
            strategy=strategy,
            data=data,
        )
        assert len(result.trades) == 2
        assert result.trades[0].direction == "buy"
        assert result.trades[1].direction == "sell"

    def test_total_return_accounts_for_costs(self):
        # Flat prices so only costs cause loss
        data = [
            StockDailyData(
                date=f"2024-01-{i + 1:02d}",
                open=10.0,
                high=10.1,
                low=9.9,
                close=10.0,
                volume=1_000_000,
                amount=10_000_000,
            )
            for i in range(12)
        ]
        strategy = _MockStrategy(buy_day=4, sell_day=8)
        result = run_backtest(
            stock_code="000001",
            start_date="2024-01-01",
            end_date="2024-01-12",
            strategy=strategy,
            data=data,
        )
        # With flat prices, total return should be negative (cost drag)
        assert result.total_return < 0

    def test_equity_curve_length_matches_data(self):
        data = _make_uptrend_data(12)
        strategy = _MockStrategy(buy_day=4, sell_day=8)
        result = run_backtest(
            stock_code="000001",
            start_date="2024-01-01",
            end_date="2024-01-12",
            strategy=strategy,
            data=data,
        )
        # Equity curve starts from day 1 (index 1), so length = len(data) - 1
        assert len(result.equity_curve) == len(data) - 1
        assert len(result.dates) == len(data) - 1

    def test_max_drawdown_non_negative(self):
        data = _make_uptrend_data(12)
        strategy = _MockStrategy(buy_day=4, sell_day=8)
        result = run_backtest(
            stock_code="000001",
            start_date="2024-01-01",
            end_date="2024-01-12",
            strategy=strategy,
            data=data,
        )
        assert result.max_drawdown >= 0

    def test_sharpe_ratio_is_finite(self):
        data = _make_uptrend_data(12)
        strategy = _MockStrategy(buy_day=4, sell_day=8)
        result = run_backtest(
            stock_code="000001",
            start_date="2024-01-01",
            end_date="2024-01-12",
            strategy=strategy,
            data=data,
        )
        assert math.isfinite(result.sharpe_ratio)

    def test_win_rate_with_profitable_trade(self):
        # Uptrend: buy at ~12.0, sell at ~14.0 → profitable
        data = _make_uptrend_data(12, start=10.0, step=1.0)
        strategy = _MockStrategy(buy_day=4, sell_day=8)
        result = run_backtest(
            stock_code="000001",
            start_date="2024-01-01",
            end_date="2024-01-12",
            strategy=strategy,
            data=data,
        )
        assert result.win_rate == 1.0

    def test_win_rate_with_losing_trade(self):
        # Downtrend: buy high, sell low → losing
        data = _make_uptrend_data(12, start=20.0, step=-1.0)
        strategy = _MockStrategy(buy_day=4, sell_day=8)
        result = run_backtest(
            stock_code="000001",
            start_date="2024-01-01",
            end_date="2024-01-12",
            strategy=strategy,
            data=data,
        )
        assert result.win_rate == 0.0

    def test_empty_data_returns_empty_result(self):
        result = run_backtest(
            stock_code="000001",
            start_date="2024-01-01",
            end_date="2024-01-01",
            strategy=_MockStrategy(),
            data=[],
        )
        assert result.trades == []
        assert result.equity_curve == []

    def test_insufficient_data_returns_empty_result(self):
        data = _make_uptrend_data(1)
        result = run_backtest(
            stock_code="000001",
            start_date="2024-01-01",
            end_date="2024-01-01",
            strategy=_MockStrategy(),
            data=data,
        )
        assert result.trades == []

    def test_no_signal_stays_in_cash(self):
        """Always-hold strategy: no trades, flat equity."""
        data = _make_uptrend_data(12)

        class HoldStrategy(BaseStrategy):
            name = "hold"

            def calculate_indicators(self, data):
                return {}

            def generate_signal(self, data, indicators):
                return StrategySignal(strategy_name="hold", stock_code="", signal="hold")

        result = run_backtest(
            stock_code="000001",
            start_date="2024-01-01",
            end_date="2024-01-12",
            strategy=HoldStrategy(),
            data=data,
        )
        assert len(result.trades) == 0
        # All equity values should equal initial capital
        assert all(eq == 100_000.0 for eq in result.equity_curve)

    def test_buy_sell_buy_again(self):
        """Two complete round-trips."""
        data = _make_uptrend_data(20, start=10.0, step=0.5)

        class DoubleTradeStrategy(BaseStrategy):
            name = "double"

            def __init__(self):
                super().__init__()
                self._count = 0

            def calculate_indicators(self, data):
                return {}

            def generate_signal(self, data, indicators):
                self._count += 1
                if self._count in (3, 12):
                    return StrategySignal(strategy_name="double", stock_code="", signal="buy")
                elif self._count in (7, 16):
                    return StrategySignal(strategy_name="double", stock_code="", signal="sell")
                return StrategySignal(strategy_name="double", stock_code="", signal="hold")

        result = run_backtest(
            stock_code="000001",
            start_date="2024-01-01",
            end_date="2024-01-20",
            strategy=DoubleTradeStrategy(),
            data=data,
        )
        assert len(result.trades) == 4
        assert result.trades[0].direction == "buy"
        assert result.trades[1].direction == "sell"
        assert result.trades[2].direction == "buy"
        assert result.trades[3].direction == "sell"

    def test_shares_are_integer(self):
        """Buy quantity must be integer (A-stock board lot = 100)."""
        data = _make_uptrend_data(12)
        strategy = _MockStrategy(buy_day=4, sell_day=8)
        result = run_backtest(
            stock_code="000001",
            start_date="2024-01-01",
            end_date="2024-01-12",
            strategy=strategy,
            data=data,
        )
        for trade in result.trades:
            assert isinstance(trade.shares, int)

    def test_buy_uses_open_price(self):
        """Trade price should be based on open, not close."""
        data = _make_uptrend_data(12)
        strategy = _MockStrategy(buy_day=4, sell_day=8)
        result = run_backtest(
            stock_code="000001",
            start_date="2024-01-01",
            end_date="2024-01-12",
            strategy=strategy,
            data=data,
        )
        # Day 4 (index 4) open = 10.0 + 4*0.5 = 12.0
        # buy_price = 12.0 * (1 + 0.00025 + 0.001) = 12.0 * 1.00125
        expected_price = 12.0 * (1 + COMMISSION + SLIPPAGE)
        assert abs(result.trades[0].price - expected_price) < 0.001

    def test_custom_initial_capital(self):
        data = _make_uptrend_data(12)
        strategy = _MockStrategy(buy_day=4, sell_day=8)
        result = run_backtest(
            stock_code="000001",
            start_date="2024-01-01",
            end_date="2024-01-12",
            strategy=strategy,
            initial_capital=50_000,
            data=data,
        )
        # First equity = initial capital (day 1, no trade yet)
        assert result.equity_curve[0] == 50_000.0
