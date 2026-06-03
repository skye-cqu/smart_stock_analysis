from __future__ import annotations

from src.data.models import StockDailyData, StrategySignal
from src.strategy.base import BaseStrategy


class VolumeBreakoutStrategy(BaseStrategy):
    name = "volume_breakout"
    description = "Volume breakout"

    def __init__(self, params: dict | None = None) -> None:
        super().__init__(params)
        self.volume_ratio = self.params.get("volume_ratio", 2.0)
        self.lookback = self.params.get("lookback", 20)

    def calculate_indicators(self, data: list[StockDailyData]) -> dict:
        if len(data) < self.lookback + 1:
            return {"volume_ratio": None, "breakout": False}
        current = data[-1]
        recent = data[-self.lookback - 1 : -1]
        avg_vol = sum(d.volume for d in recent) / len(recent)
        recent_high = max(d.high for d in recent)
        return {
            "volume_ratio": current.volume / avg_vol if avg_vol > 0 else 0,
            "breakout": current.close > recent_high,
        }

    def generate_signal(self, data: list[StockDailyData], indicators: dict) -> StrategySignal:
        vr = indicators.get("volume_ratio")
        bo = indicators.get("breakout", False)
        if vr is None:
            return StrategySignal(
                strategy_name=self.name, stock_code="", signal="hold", strength=0.0
            )
        if bo and vr >= self.volume_ratio:
            return StrategySignal(
                strategy_name=self.name,
                stock_code="",
                signal="buy",
                strength=min(1.0, vr / (self.volume_ratio * 2)),
            )
        return StrategySignal(strategy_name=self.name, stock_code="", signal="hold", strength=0.0)
