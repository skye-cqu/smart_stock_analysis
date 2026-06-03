from __future__ import annotations

from unittest.mock import MagicMock

from src.data.models import StrategySignal
from src.strategy.base import BaseStrategy
from src.strategy.registry import StrategyRegistry


class TestStrategyRegistry:
    def test_discovers_builtin_strategies(self):
        reg = StrategyRegistry()
        all_strategies = reg.get_all()
        names = set(all_strategies.keys())
        assert "ma_cross" in names
        assert "rsi_oversold" in names
        assert "macd_divergence" in names
        assert "volume_breakout" in names

    def test_get_strategy_returns_instance(self):
        reg = StrategyRegistry()
        strat = reg.get_strategy("ma_cross")
        assert strat is not None
        assert isinstance(strat, BaseStrategy)
        assert strat.name == "ma_cross"

    def test_get_strategy_nonexistent_returns_none(self):
        reg = StrategyRegistry()
        assert reg.get_strategy("nonexistent") is None

    def test_run_all_returns_signals(self, sample_daily_data):
        reg = StrategyRegistry()
        signals = reg.run_all("000001", sample_daily_data)
        assert len(signals) >= 4
        assert all(isinstance(s, StrategySignal) for s in signals)

    def test_run_all_catches_strategy_exceptions(self, sample_daily_data):
        reg = StrategyRegistry()
        # Inject a broken strategy
        broken = MagicMock(spec=BaseStrategy)
        broken.name = "broken"
        broken.run.side_effect = ValueError("boom")
        reg._strategies["broken"] = broken
        signals = reg.run_all("000001", sample_daily_data)
        # broken strategy is silently skipped, others still return
        assert all(s.strategy_name != "broken" for s in signals)

    def test_load_from_yaml_nonexistent_path(self, tmp_path):
        reg = StrategyRegistry()
        reg.load_from_yaml(str(tmp_path / "nonexistent.yaml"))
        # no error, no-op

    def test_load_from_yaml_overrides_params(self, tmp_path):
        import yaml

        config = {"strategies": {"ma_cross": {"short_period": 3, "long_period": 10}}}
        path = tmp_path / "strategies.yaml"
        path.write_text(yaml.dump(config), encoding="utf-8")
        reg = StrategyRegistry()
        reg.load_from_yaml(str(path))
        strat = reg.get_strategy("ma_cross")
        assert strat.params["short_period"] == 3
        assert strat.params["long_period"] == 10
