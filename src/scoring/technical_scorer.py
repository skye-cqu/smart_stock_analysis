from __future__ import annotations

from src.data.models import StockDailyData, StockInfo


class TechnicalScorer:
    def score(self, info: StockInfo, data: list[StockDailyData]) -> float:
        if len(data) < 20:
            return 0.0
        prices = [d.close for d in data]
        score = 0.0
        ma5 = sum(prices[-5:]) / 5
        ma20 = sum(prices[-20:]) / 20
        if ma5 > ma20:
            score += 30
        else:
            score -= 20
        rsi = self._rsi(prices)
        if rsi is not None:
            if 40 <= rsi <= 60:
                score += 20
            elif rsi < 30:
                score += 40
            elif rsi > 70:
                score -= 30
        current = prices[-1]
        high_20 = max(prices[-20:])
        if current > high_20 * 0.98:
            score += 10
        return max(-100, min(100, score))

    @staticmethod
    def _rsi(prices: list[float], period: int = 14) -> float | None:
        if len(prices) < period + 1:
            return None
        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            return 100.0
        return 100 - (100 / (1 + avg_gain / avg_loss))
