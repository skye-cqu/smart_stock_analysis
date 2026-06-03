from __future__ import annotations

import logging
import os
import time

# Disable proxy before importing akshare
for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(key, None)
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

import akshare as ak

from src.config import settings
from src.data.models import StockDailyData, StockInfo

logger = logging.getLogger(__name__)


class AkShareClient:
    def get_daily_data(self, stock_code, start_date, end_date):
        time.sleep(settings.data.akshare_rate_limit)
        # Primary: Sina source (bypasses EastMoney proxy issue)
        try:
            prefix = "sz" if stock_code.startswith(("0", "3")) else "sh"
            df = ak.stock_zh_a_daily(
                symbol=f"{prefix}{stock_code}",
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                adjust="qfq",
            )
            if df.empty:
                logger.warning(f"No daily data for {stock_code}")
                return []
            result = []
            for _, row in df.iterrows():
                result.append(
                    StockDailyData(
                        date=str(row["date"]),
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=float(row["volume"]),
                        amount=float(row.get("amount", 0)),
                        turnover=float(row.get("turnover", 0)),
                    )
                )
            return result
        except Exception as e:
            logger.warning(f"stock_zh_a_daily failed for {stock_code}, trying stock_zh_a_hist: {e}")
        # Fallback: EastMoney source
        try:
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                adjust="qfq",
            )
            if df.empty:
                return []
            return [StockDailyData.from_akshare(row.to_dict()) for _, row in df.iterrows()]
        except Exception as e:
            logger.error(f"All daily data sources failed for {stock_code}: {e}")
            raise

    def get_stock_info(self, stock_code):
        time.sleep(settings.data.akshare_rate_limit)
        name = self._get_stock_name(stock_code)
        pe_ratio = None
        pb_ratio = None
        try:
            df = ak.stock_individual_info_em(symbol=stock_code)
            info_dict = {}
            for _, row in df.iterrows():
                info_dict[row.iloc[0]] = row.iloc[1]
            pe_ratio = float(info_dict.get("市盈率(动态)", 0) or 0) or None
            pb_ratio = float(info_dict.get("市净率", 0) or 0) or None
            return StockInfo(
                code=stock_code,
                name=name,
                industry=str(info_dict.get("行业", "")),
                market_cap=float(info_dict.get("总市值", 0) or 0),
                pe_ratio=pe_ratio,
                pb_ratio=pb_ratio,
            )
        except Exception as e:
            logger.warning(f"Detailed info unavailable for {stock_code}: {e}")
            return StockInfo(code=stock_code, name=name)

    def _get_stock_name(self, stock_code):
        try:
            df = ak.stock_info_a_code_name()
            row = df[df["code"] == stock_code]
            if not row.empty:
                return str(row.iloc[0]["name"])
        except Exception as e:
            logger.warning(f"stock_info_a_code_name failed: {e}")
        return stock_code
