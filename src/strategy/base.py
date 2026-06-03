from __future__ import annotations

from abc import ABC, abstractmethod

from src.data.models import StockDailyData, StrategySignal


class BaseStrategy(ABC):
    name: str = "base"
    description: str = ""

    def __init__(self, params: dict | None = None) -> None:
        self.params = params or {}

    @abstractmethod
    def calculate_indicators(self, data: list[StockDailyData]) -> dict:
        """Compute technical indicators from daily data."""

    @abstractmethod
    def generate_signal(self, data: list[StockDailyData], indicators: dict) -> StrategySignal:
        """Generate buy/sell/hold signal based on indicators."""

    def run(self, stock_code: str, data: list[StockDailyData]) -> StrategySignal:
        indicators = self.calculate_indicators(data)
        signal = self.generate_signal(data, indicators)
        signal.strategy_name = self.name
        signal.stock_code = stock_code
        signal.indicators = indicators
        return signal
