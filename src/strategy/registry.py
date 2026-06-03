from __future__ import annotations

import importlib
import logging
from pathlib import Path

import yaml

from src.data.models import StockDailyData, StrategySignal
from src.strategy.base import BaseStrategy

logger = logging.getLogger(__name__)


class StrategyRegistry:
    def __init__(self) -> None:
        self._strategies: dict[str, BaseStrategy] = {}
        self._load_builtin()

    def _load_builtin(self) -> None:
        builtin_dir = Path(__file__).parent / "builtin"
        for py_file in builtin_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            module_name = f"src.strategy.builtin.{py_file.stem}"
            try:
                module = importlib.import_module(module_name)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BaseStrategy)
                        and attr is not BaseStrategy
                    ):
                        strategy = attr()
                        self._strategies[strategy.name] = strategy
            except Exception as e:
                logger.warning(f"Failed to load {module_name}: {e}")

    def load_from_yaml(self, path: str) -> None:
        config_path = Path(path)
        if not config_path.exists():
            return
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        for name, params in config.get("strategies", {}).items():
            if name in self._strategies:
                self._strategies[name].params = params

    def get_strategy(self, name: str) -> BaseStrategy | None:
        return self._strategies.get(name)

    def get_all(self) -> dict[str, BaseStrategy]:
        return dict(self._strategies)

    def run_all(self, stock_code: str, data: list[StockDailyData]) -> list[StrategySignal]:
        signals = []
        for name, strategy in self._strategies.items():
            try:
                signal = strategy.run(stock_code, data)
                signals.append(signal)
            except Exception as e:
                logger.warning(f"Strategy {name} failed for {stock_code}: {e}")
        return signals
