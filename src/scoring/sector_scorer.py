from __future__ import annotations

import logging

from src.data.models import StockDailyData, StockInfo

logger = logging.getLogger(__name__)


class SectorScorer:
    def score(self, info: StockInfo, data: list[StockDailyData]) -> float:
        if not info.industry:
            return 0.0
        if len(data) < 6:
            return 0.0

        try:
            import akshare as ak

            df = ak.stock_board_industry_cons_em(symbol=info.industry)
            if df.empty:
                return 0.0

            # Board median daily return
            pct_col = None
            for col in ("涨跌幅", "change_pct", "pct_chg"):
                if col in df.columns:
                    pct_col = col
                    break
            if pct_col is None:
                return 0.0
            median_return = float(df[pct_col].median())
        except Exception as e:
            logger.warning(f"SectorScorer: failed to fetch sector data for {info.industry}: {e}")
            return 0.0

        # Stock 5-day return
        stock_return = (data[-1].close / data[-6].close - 1) * 100
        diff = stock_return - median_return

        if diff > 5:
            return 50.0
        elif diff > 2:
            return 30.0
        elif diff > 0:
            return 10.0
        elif diff < -5:
            return -50.0
        elif diff < -2:
            return -30.0
        elif diff < 0:
            return -10.0
        return 0.0
