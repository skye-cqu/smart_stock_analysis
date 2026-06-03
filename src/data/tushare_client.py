from __future__ import annotations

import logging
import time

from src.config import settings
from src.data.models import StockDailyData, StockInfo

logger = logging.getLogger(__name__)


class TushareClient:
    def __init__(self) -> None:
        import tushare as ts

        self.pro = ts.pro_api(settings.data.tushare_token)

    def get_daily_data(
        self, stock_code: str, start_date: str, end_date: str
    ) -> list[StockDailyData]:
        time.sleep(0.3)
        ts_code = self._to_ts_code(stock_code)
        df = self.pro.daily(
            ts_code=ts_code,
            start_date=start_date.replace("-", ""),
            end_date=end_date.replace("-", ""),
        )
        if df is None or df.empty:
            return []
        result = []
        for _, row in df.iterrows():
            result.append(
                StockDailyData(
                    date=str(row["trade_date"]),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["vol"]),
                    amount=float(row["amount"]),
                    turnover=float(row.get("turnover_rate", 0) or 0),
                )
            )
        return result

    def get_stock_info(self, stock_code: str) -> StockInfo:
        time.sleep(0.3)
        ts_code = self._to_ts_code(stock_code)
        df = self.pro.stock_basic(ts_code=ts_code, fields="ts_code,name,industry,market")
        if df is None or df.empty:
            raise ValueError(f"No info for {stock_code}")
        row = df.iloc[0]
        return StockInfo(
            code=stock_code, name=str(row["name"]), industry=str(row.get("industry", ""))
        )

    @staticmethod
    def _to_ts_code(code: str) -> str:
        if code.startswith("6"):
            return f"{code}.SH"
        return f"{code}.SZ"
