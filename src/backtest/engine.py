from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field

from src.data.models import StockDailyData
from src.strategy.base import BaseStrategy

logger = logging.getLogger(__name__)

COMMISSION = 0.00025  # 万2.5 both sides
STAMP_TAX = 0.001  # 千1 sell only
SLIPPAGE = 0.001  # 0.1%
INITIAL_CAPITAL = 100_000.0


@dataclass
class Trade:
    date: str
    direction: str  # "buy" / "sell"
    price: float
    shares: int
    cost: float


@dataclass
class BacktestResult:
    trades: list[Trade] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)
    dates: list[str] = field(default_factory=list)
    total_return: float = 0.0
    annual_return: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0


def _buy_price(price: float) -> float:
    return price * (1 + COMMISSION + SLIPPAGE)


def _sell_price(price: float) -> float:
    return price * (1 - COMMISSION - STAMP_TAX - SLIPPAGE)


def _calc_metrics(
    equity_curve: list[float],
    dates: list[str],
    trades: list[Trade],
) -> tuple[float, float, float, float, float]:
    if not equity_curve or len(equity_curve) < 2:
        return 0.0, 0.0, 0.0, 0.0, 0.0

    initial = equity_curve[0]
    final = equity_curve[-1]
    total_return = (final - initial) / initial

    n_days = len(dates)
    annual_return = (1 + total_return) ** (252 / max(n_days, 1)) - 1

    # Max drawdown
    peak = equity_curve[0]
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd

    # Sharpe ratio (daily returns → annualized)
    daily_returns = []
    for i in range(1, len(equity_curve)):
        if equity_curve[i - 1] > 0:
            daily_returns.append(equity_curve[i] / equity_curve[i - 1] - 1)
    if len(daily_returns) >= 2:
        mean_ret = sum(daily_returns) / len(daily_returns)
        var = sum((r - mean_ret) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
        std_ret = math.sqrt(var) if var > 0 else 0.0
        sharpe = (mean_ret / std_ret * math.sqrt(252)) if std_ret > 0 else 0.0
    else:
        sharpe = 0.0

    # Win rate (sell trades where entry cost < exit proceeds)
    # Track buy/sell pairs: each buy is followed by a sell
    buy_trades = [t for t in trades if t.direction == "buy"]
    sell_trades = [t for t in trades if t.direction == "sell"]
    pairs = min(len(buy_trades), len(sell_trades))
    if pairs > 0:
        wins = sum(
            1
            for i in range(pairs)
            if sell_trades[i].price * sell_trades[i].shares
            > buy_trades[i].price * buy_trades[i].shares
        )
        win_rate = wins / pairs
    else:
        win_rate = 0.0

    return total_return, annual_return, max_dd, sharpe, win_rate


def run_backtest(
    stock_code: str,
    start_date: str,
    end_date: str,
    strategy_name: str = "ma_cross",
    initial_capital: float = INITIAL_CAPITAL,
    strategy: BaseStrategy | None = None,
    data: list[StockDailyData] | None = None,
) -> BacktestResult:
    # Resolve data
    if data is None:
        from src.data.provider import DataProvider

        data = DataProvider().get_daily_data(stock_code, start_date, end_date)
    if not data or len(data) < 2:
        logger.warning(f"No data for {stock_code} ({start_date} ~ {end_date})")
        return BacktestResult()

    # Resolve strategy
    if strategy is None:
        from src.strategy.registry import StrategyRegistry

        strategy = StrategyRegistry().get_strategy(strategy_name)
    if strategy is None:
        logger.error(f"Strategy '{strategy_name}' not found")
        return BacktestResult()

    cash = initial_capital
    shares = 0
    trades: list[Trade] = []
    equity_curve: list[float] = []
    dates: list[str] = []

    for i in range(1, len(data)):
        today = data[i]
        slice_data = data[: i + 1]
        signal = strategy.run(stock_code, slice_data)

        if signal.signal == "buy" and shares == 0:
            price = _buy_price(today.open)
            can_buy = int(cash / price) if price > 0 else 0
            if can_buy > 0:
                cost = can_buy * price
                cash -= cost
                shares = can_buy
                trades.append(
                    Trade(date=today.date, direction="buy", price=price, shares=can_buy, cost=cost)
                )

        elif signal.signal == "sell" and shares > 0:
            price = _sell_price(today.open)
            proceeds = shares * price
            cash += proceeds
            trades.append(
                Trade(
                    date=today.date,
                    direction="sell",
                    price=price,
                    shares=shares,
                    cost=proceeds,
                )
            )
            shares = 0

        equity = cash + shares * today.close
        equity_curve.append(equity)
        dates.append(today.date)

    total_return, annual_return, max_dd, sharpe, win_rate = _calc_metrics(
        equity_curve, dates, trades
    )

    return BacktestResult(
        trades=trades,
        equity_curve=equity_curve,
        dates=dates,
        total_return=total_return,
        annual_return=annual_return,
        max_drawdown=max_dd,
        sharpe_ratio=sharpe,
        win_rate=win_rate,
    )
