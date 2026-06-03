from __future__ import annotations

from src.data.models import StockDailyData, StrategySignal
from src.strategy.base import BaseStrategy


def compute_ma(prices: list[float], period: int) -> list[float | None]:
    result: list[float | None] = []
    for i in range(len(prices)):
        if i < period - 1:
            result.append(None)
        else:
            result.append(sum(prices[i - period + 1 : i + 1]) / period)
    return result


class MACrossStrategy(BaseStrategy):
    name = "ma_cross"
    description = "MA golden cross death cross"

    def __init__(self, params: dict | None = None) -> None:
        super().__init__(params)
        self.short_period = self.params.get("short_period", 5)
        self.long_period = self.params.get("long_period", 20)

    def calculate_indicators(self, data: list[StockDailyData]) -> dict:
        prices = [d.close for d in data]
        ma_short = compute_ma(prices, self.short_period)
        ma_long = compute_ma(prices, self.long_period)
        return {
            "ma_s": ma_short[-1],
            "ma_l": ma_long[-1],
            "ma_s_prev": ma_short[-2] if len(ma_short) > 1 else None,
            "ma_l_prev": ma_long[-2] if len(ma_long) > 1 else None,
        }

    def generate_signal(self, data: list[StockDailyData], indicators: dict) -> StrategySignal:
        ma_s = indicators.get("ma_s")
        ma_l = indicators.get("ma_l")
        ma_s_prev = indicators.get("ma_s_prev")
        ma_l_prev = indicators.get("ma_l_prev")
        if None in (ma_s, ma_l, ma_s_prev, ma_l_prev):
            return StrategySignal(
                strategy_name=self.name, stock_code="", signal="hold", strength=0.0
            )
        if ma_s > ma_l and ma_s_prev <= ma_l_prev:
            return StrategySignal(
                strategy_name=self.name, stock_code="", signal="buy", strength=0.8
            )
        if ma_s < ma_l and ma_s_prev >= ma_l_prev:
            return StrategySignal(
                strategy_name=self.name, stock_code="", signal="sell", strength=0.8
            )
        return StrategySignal(strategy_name=self.name, stock_code="", signal="hold", strength=0.0)
