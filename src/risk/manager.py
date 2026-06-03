from __future__ import annotations

import math
from dataclasses import dataclass

from src.data.models import StockDailyData


@dataclass
class RiskAssessment:
    volatility: float
    max_position_pct: float
    stop_loss_price: float
    risk_level: str


def assess_risk(data: list[StockDailyData], entry_price: float) -> RiskAssessment:
    if len(data) < 2:
        return RiskAssessment(
            volatility=0.0,
            max_position_pct=0.25,
            stop_loss_price=entry_price * 0.92,
            risk_level="低",
        )

    # Daily returns (up to last 60 days)
    window = data[-60:] if len(data) >= 60 else data
    returns = []
    for i in range(1, len(window)):
        if window[i - 1].close > 0:
            returns.append(window[i].close / window[i - 1].close - 1)

    if len(returns) < 2:
        vol = 0.0
    else:
        mean_ret = sum(returns) / len(returns)
        var = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
        vol = math.sqrt(var) * math.sqrt(252)

    # Position sizing by volatility regime
    if vol < 0.15:
        max_pos = 0.25
        level = "低"
    elif vol < 0.30:
        max_pos = 0.25 - (vol - 0.15) / 0.15 * 0.125
        level = "中"
    elif vol < 0.50:
        max_pos = 0.15 - (vol - 0.30) / 0.20 * 0.10
        level = "高"
    else:
        max_pos = 0.10
        level = "极高"

    return RiskAssessment(
        volatility=vol,
        max_position_pct=round(max_pos, 4),
        stop_loss_price=round(entry_price * 0.92, 2),
        risk_level=level,
    )


def check_stop_loss(current_price: float, entry_price: float, highest_since_entry: float) -> bool:
    if current_price < entry_price * 0.92:
        return True
    return highest_since_entry > 0 and current_price < highest_since_entry * 0.95
