from __future__ import annotations

from src.data.models import StockDailyData, StrategySignal
from src.strategy.base import BaseStrategy


class DummyStrategy(BaseStrategy):
    name = "dummy"
    description = "test strategy"

    def calculate_indicators(self, data: list[StockDailyData]) -> dict:
        return {"avg_close": sum(d.close for d in data) / len(data)}

    def generate_signal(self, data: list[StockDailyData], indicators: dict) -> StrategySignal:
        if indicators["avg_close"] > 10:
            return StrategySignal(
                strategy_name=self.name, stock_code="", signal="buy", strength=0.5
            )
        return StrategySignal(strategy_name=self.name, stock_code="", signal="hold", strength=0.0)


class TestBaseStrategy:
    def test_run_returns_strategy_signal(self, sample_daily_data):
        strat = DummyStrategy()
        signal = strat.run("000001", sample_daily_data)
        assert isinstance(signal, StrategySignal)
        assert signal.strategy_name == "dummy"
        assert signal.stock_code == "000001"

    def test_run_sets_indicators_on_signal(self, sample_daily_data):
        strat = DummyStrategy()
        signal = strat.run("000001", sample_daily_data)
        assert "avg_close" in signal.indicators

    def test_params_default_empty_dict(self):
        strat = DummyStrategy()
        assert strat.params == {}

    def test_params_passed_to_init(self):
        strat = DummyStrategy(params={"key": "value"})
        assert strat.params["key"] == "value"
