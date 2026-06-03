from __future__ import annotations

from src.data.models import StockDailyData, StockInfo


class EventScorer:
    def score(self, info: StockInfo, data: list[StockDailyData]) -> float:
        if len(data) < 6:
            return 0.0

        score = 0.0

        # Volume spike: last volume > 3x average of prior 5 days
        prior_volumes = [d.volume for d in data[-6:-1]]
        avg_vol = sum(prior_volumes) / len(prior_volumes)
        if avg_vol > 0 and data[-1].volume / avg_vol > 3.0:
            score += 40

        # Limit-up: >9.5% daily gain
        if data[-2].close > 0:
            daily_change = data[-1].close / data[-2].close
            if daily_change > 1.095:
                score += 30
            elif daily_change < 0.905:
                score -= 30

        # Consecutive moves (3+ days in same direction)
        if len(data) >= 4:
            up_streak = 0
            down_streak = 0
            for i in range(-1, -4, -1):
                if data[i].close > data[i - 1].close:
                    up_streak += 1
                elif data[i].close < data[i - 1].close:
                    down_streak += 1
            if up_streak >= 3:
                score += 20
            if down_streak >= 3:
                score -= 20

        return max(-100.0, min(100.0, score))
