from __future__ import annotations

from src.data.models import StockDailyData, StockInfo


class FundamentalScorer:
    def score(self, info: StockInfo, data: list[StockDailyData]) -> float:
        if info is None:
            return 0.0
        score = 0.0
        if info.pe_ratio is not None:
            if 0 < info.pe_ratio < 15:
                score += 40
            elif 15 <= info.pe_ratio < 30:
                score += 20
            elif info.pe_ratio > 60:
                score -= 30
            elif info.pe_ratio < 0:
                score -= 50
        if info.pb_ratio is not None:
            if 0 < info.pb_ratio < 1.5:
                score += 30
            elif 1.5 <= info.pb_ratio < 3:
                score += 10
            elif info.pb_ratio > 5:
                score -= 20
        if info.roe is not None:
            if info.roe > 15:
                score += 30
            elif info.roe > 10:
                score += 15
            elif info.roe < 0:
                score -= 30
        return max(-100, min(100, score))
