from __future__ import annotations

import logging
from typing import Protocol

from src.config import settings
from src.data.models import StockDailyData, StockInfo

logger = logging.getLogger(__name__)


class DataClient(Protocol):
    def get_daily_data(
        self, stock_code: str, start_date: str, end_date: str
    ) -> list[StockDailyData]: ...
    def get_stock_info(self, stock_code: str) -> StockInfo: ...


class DataProvider:
    def __init__(self, no_cache: bool = True) -> None:
        from src.data.akshare_client import AkShareClient
        from src.data.cache import CacheManager

        self.no_cache = no_cache
        self.clients: list[tuple[int, str, DataClient]] = []
        self.cache = CacheManager()

        self.clients.append((0, "akshare", AkShareClient()))

        if settings.data.tushare_token:
            try:
                from src.data.tushare_client import TushareClient

                self.clients.append((1, "tushare", TushareClient()))
            except Exception as e:
                logger.warning(f"Failed to init Tushare: {e}")

        self.clients.sort(key=lambda x: x[0])

    def get_daily_data(
        self, stock_code: str, start_date: str, end_date: str
    ) -> list[StockDailyData]:
        if not self.no_cache:
            cached = self.cache.get("daily", code=stock_code, start=start_date, end=end_date)
            if cached is not None:
                return [StockDailyData(**item) for item in cached]

        for priority, name, client in self.clients:
            try:
                result = client.get_daily_data(stock_code, start_date, end_date)
                if result:
                    self.cache.set(
                        "daily",
                        [vars(d) for d in result],
                        code=stock_code,
                        start=start_date,
                        end=end_date,
                    )
                    return result
            except Exception as e:
                logger.warning(f"{name} failed for {stock_code}: {e}")

        logger.error(f"All data providers failed for {stock_code}")
        return []

    def get_stock_info(self, stock_code: str) -> StockInfo | None:
        if not self.no_cache:
            cached = self.cache.get("info", code=stock_code)
            if cached is not None:
                return StockInfo(**cached)

        for priority, name, client in self.clients:
            try:
                result = client.get_stock_info(stock_code)
                if result:
                    self.cache.set("info", vars(result), code=stock_code)
                    return result
            except Exception as e:
                logger.warning(f"{name} info failed for {stock_code}: {e}")

        logger.error(f"All data providers failed for info {stock_code}")
        return None
