from __future__ import annotations

from src.data.models import StockDailyData, StrategySignal
from src.strategy.base import BaseStrategy


def compute_rsi(prices: list[float], period: int = 14) -> float | None:
    if len(prices) < period + 1:
        return None
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    return 100 - (100 / (1 + avg_gain / avg_loss))


class RSIOversoldStrategy(BaseStrategy):
    name = "rsi_oversold"
    description = "RSI oversold"

    def __init__(self, params: dict | None = None) -> None:
        super().__init__(params)
        self.oversold = self.params.get("oversold", 30)
        self.overbought = self.params.get("overbought", 70)

    def calculate_indicators(self, data: list[StockDailyData]) -> dict:
        prices = [d.close for d in data]
        return {"rsi": compute_rsi(prices)}

    def generate_signal(self, data: list[StockDailyData], indicators: dict) -> StrategySignal:
        rsi = indicators.get("rsi")
        if rsi is None:
            return StrategySignal(
                strategy_name=self.name, stock_code="", signal="hold", strength=0.0
            )
        if rsi < self.oversold:
            return StrategySignal(
                strategy_name=self.name,
                stock_code="",
                signal="buy",
                strength=(self.oversold - rsi) / self.oversold,
            )
        if rsi > self.overbought:
            return StrategySignal(
                strategy_name=self.name,
                stock_code="",
                signal="sell",
                strength=(rsi - self.overbought) / (100 - self.overbought),
            )
        return StrategySignal(strategy_name=self.name, stock_code="", signal="hold", strength=0.0)
