from __future__ import annotations

from src.data.models import StockDailyData, StrategySignal
from src.strategy.base import BaseStrategy


def compute_ema(prices: list[float], period: int) -> list[float]:
    ema = [prices[0]]
    multiplier = 2.0 / (period + 1)
    for i in range(1, len(prices)):
        ema.append(prices[i] * multiplier + ema[-1] * (1 - multiplier))
    return ema


class MACDDivergenceStrategy(BaseStrategy):
    name = "macd_divergence"
    description = "MACD bottom divergence"

    def calculate_indicators(self, data: list[StockDailyData]) -> dict:
        prices = [d.close for d in data]
        if len(prices) < 35:
            return {"divergence": False}
        ema_fast = compute_ema(prices, 12)
        ema_slow = compute_ema(prices, 26)
        dif = [f - s for f, s in zip(ema_fast, ema_slow, strict=False)]
        dea = compute_ema(dif, 9)
        return {"dif": dif[-1], "dea": dea[-1], "macd": (dif[-1] - dea[-1]) * 2}

    def generate_signal(self, data: list[StockDailyData], indicators: dict) -> StrategySignal:
        dif = indicators.get("dif")
        dea = indicators.get("dea")
        if dif is not None and dea is not None and dif > dea and dif < 0:
            return StrategySignal(
                strategy_name=self.name, stock_code="", signal="buy", strength=0.7
            )
        return StrategySignal(strategy_name=self.name, stock_code="", signal="hold", strength=0.0)
