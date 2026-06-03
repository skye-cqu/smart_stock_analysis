from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.data.models import StockDailyData, StockInfo
from src.data.provider import DataProvider


def _make_provider(no_cache: bool = True):
    """Build a DataProvider with mocked internals (no real AkShare/SQLite)."""
    with (
        patch("src.data.cache.CacheManager") as MockCache,
        patch("src.data.akshare_client.AkShareClient") as MockAK,
    ):
        mock_cache = MagicMock()
        MockCache.return_value = mock_cache
        mock_ak = MagicMock()
        MockAK.return_value = mock_ak
        prov = DataProvider(no_cache=no_cache)
        prov.cache = mock_cache
        prov.clients = [(0, "akshare", mock_ak)]
        return prov, mock_cache, mock_ak


class TestGetDailyData:
    def test_cache_hit_returns_cached(self):
        prov, cache, ak = _make_provider(no_cache=False)
        cache.get.return_value = [
            {
                "date": "2026-01-01",
                "open": 10.0,
                "high": 11.0,
                "low": 9.5,
                "close": 10.5,
                "volume": 1000,
                "amount": 10500,
                "turnover": 1.0,
            }
        ]
        result = prov.get_daily_data("000001", "2026-01-01", "2026-06-01")
        assert len(result) == 1
        assert result[0].close == 10.5
        ak.get_daily_data.assert_not_called()

    def test_cache_miss_calls_client_and_caches(self):
        prov, cache, ak = _make_provider()
        cache.get.return_value = None
        ak.get_daily_data.return_value = [
            StockDailyData(
                date="2026-01-02",
                open=11.0,
                high=11.5,
                low=10.8,
                close=11.2,
                volume=2000,
                amount=22400,
                turnover=2.0,
            )
        ]
        result = prov.get_daily_data("000001", "2026-01-01", "2026-06-01")
        assert len(result) == 1
        assert result[0].close == 11.2
        cache.set.assert_called_once()

    def test_client_fails_returns_empty(self):
        prov, cache, ak = _make_provider()
        cache.get.return_value = None
        ak.get_daily_data.side_effect = Exception("network error")
        result = prov.get_daily_data("000001", "2026-01-01", "2026-06-01")
        assert result == []

    def test_client_returns_empty_list_falls_through(self):
        prov, cache, ak = _make_provider()
        cache.get.return_value = None
        ak.get_daily_data.return_value = []
        result = prov.get_daily_data("000001", "2026-01-01", "2026-06-01")
        assert result == []


class TestGetStockInfo:
    def test_cache_hit_returns_cached_info(self):
        prov, cache, ak = _make_provider(no_cache=False)
        cache.get.return_value = {"code": "600519", "name": "贵州茅台", "industry": "白酒"}
        result = prov.get_stock_info("600519")
        assert result.code == "600519"
        assert result.name == "贵州茅台"
        ak.get_stock_info.assert_not_called()

    def test_cache_miss_calls_client(self):
        prov, cache, ak = _make_provider()
        cache.get.return_value = None
        ak.get_stock_info.return_value = StockInfo(code="000001", name="平安银行")
        result = prov.get_stock_info("000001")
        assert result.name == "平安银行"
        cache.set.assert_called_once()

    def test_all_clients_fail_returns_none(self):
        prov, cache, ak = _make_provider()
        cache.get.return_value = None
        ak.get_stock_info.side_effect = Exception("down")
        result = prov.get_stock_info("000001")
        assert result is None
