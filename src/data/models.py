from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class StockDailyData:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    turnover: float = 0.0

    @classmethod
    def from_akshare(cls, row: dict) -> StockDailyData:
        return cls(
            date=str(row.get("日期", row.get("date", ""))),
            open=float(row.get("开盘", row.get("open", 0))),
            high=float(row.get("最高", row.get("high", 0))),
            low=float(row.get("最低", row.get("low", 0))),
            close=float(row.get("收盘", row.get("close", 0))),
            volume=float(row.get("成交量", row.get("volume", 0))),
            amount=float(row.get("成交额", row.get("amount", 0))),
            turnover=float(row.get("换手率", row.get("turnover", 0))),
        )


@dataclass
class StockInfo:
    code: str
    name: str
    industry: str = ""
    market_cap: float = 0.0
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    roe: float | None = None
    total_share: float = 0.0
    float_share: float = 0.0


@dataclass
class ScoreResult:
    total: float = 0.0
    technical: float = 0.0
    capital_flow: float = 0.0
    fundamental: float = 0.0
    sector: float = 0.0
    event: float = 0.0
    veto: bool = False
    veto_reason: str = ""


@dataclass
class StrategySignal:
    strategy_name: str
    stock_code: str
    signal: str  # "buy", "sell", "hold"
    strength: float = 0.0  # 0.0 - 1.0
    indicators: dict = field(default_factory=dict)


@dataclass
class AnalysisResult:
    stock_code: str
    stock_name: str
    current_price: float
    score: ScoreResult
    strategy_signals: list[StrategySignal] = field(default_factory=list)
    llm_analysis: str = ""
    recommendation: str = ""  # "买入", "持有", "卖出"
    analysis_date: str = field(default_factory=lambda: date.today().isoformat())
