from __future__ import annotations

from src.data.models import StockDailyData, StockInfo


class CapitalFlowScorer:
    def score(self, info: StockInfo, data: list[StockDailyData]) -> float:
        if len(data) < 5:
            return 0.0
        score = 0.0
        recent = data[-5:]
        volumes = [d.volume for d in recent]
        avg_vol = sum(volumes) / len(volumes)
        if volumes[-1] > avg_vol * 1.5:
            score += 30
        prices_up = sum(1 for i in range(1, len(recent)) if recent[i].close > recent[i - 1].close)
        if prices_up >= 4:
            score += 40
        elif prices_up <= 1:
            score -= 30
        turnover = data[-1].turnover
        if turnover > 5:
            score += 20
        elif turnover < 1:
            score -= 10
        return max(-100, min(100, score))
