from __future__ import annotations

import sqlite3

import pytest

from src.data.cache import CacheManager


@pytest.fixture
def cache(tmp_path):
    db = tmp_path / "test_cache.db"
    return CacheManager(db_path=str(db), ttl_minutes=60)


class TestCacheManager:
    def test_get_miss_returns_none(self, cache):
        assert cache.get("daily", code="000001") is None

    def test_set_and_get(self, cache):
        data = [{"close": 10.5, "volume": 1000}]
        cache.set("daily", data, code="000001")
        result = cache.get("daily", code="000001")
        assert result == data

    def test_set_overwrites_existing(self, cache):
        cache.set("daily", [{"v": 1}], code="000001")
        cache.set("daily", [{"v": 2}], code="000001")
        result = cache.get("daily", code="000001")
        assert result == [{"v": 2}]

    def test_different_keys_independent(self, cache):
        cache.set("daily", [1], code="000001")
        cache.set("daily", [2], code="600519")
        assert cache.get("daily", code="000001") == [1]
        assert cache.get("daily", code="600519") == [2]

    def test_invalidate(self, cache):
        cache.set("daily", [1], code="000001")
        cache.invalidate("daily", code="000001")
        assert cache.get("daily", code="000001") is None

    def test_invalidate_nonexistent_is_noop(self, cache):
        cache.invalidate("daily", code="nonexistent")  # should not raise

    def test_ttl_expiry(self, tmp_path):
        db = tmp_path / "ttl_test.db"
        c = CacheManager(db_path=str(db), ttl_minutes=60)
        c.set("ns", {"a": 1}, key="k")
        # Manually set expires_at to the past
        with sqlite3.connect(str(db)) as conn:
            conn.execute("UPDATE cache SET expires_at = 0")
        assert c.get("ns", key="k") is None

    def test_clear_expired(self, tmp_path):
        db = tmp_path / "clear_test.db"
        c = CacheManager(db_path=str(db), ttl_minutes=60)
        c.set("ns", {"a": 1}, key="k1")
        c.set("ns", {"b": 2}, key="k2")
        # Manually set expires_at to the past
        with sqlite3.connect(str(db)) as conn:
            conn.execute("UPDATE cache SET expires_at = 0")
        count = c.clear_expired()
        assert count == 2

    def test_make_key_deterministic(self, cache):
        k1 = cache._make_key("daily", code="000001", start="2026-01-01")
        k2 = cache._make_key("daily", code="000001", start="2026-01-01")
        assert k1 == k2

    def test_make_key_different_kwargs(self, cache):
        k1 = cache._make_key("daily", code="000001")
        k2 = cache._make_key("daily", code="000002")
        assert k1 != k2

    def test_stores_list_data(self, cache):
        data = [{"close": 10.0}, {"close": 11.0}, {"close": 12.0}]
        cache.set("daily", data, code="000001")
        result = cache.get("daily", code="000001")
        assert len(result) == 3
        assert result[2]["close"] == 12.0

    def test_namespace_isolation(self, cache):
        cache.set("ns1", {"x": 1}, key="k")
        cache.set("ns2", {"y": 2}, key="k")
        assert cache.get("ns1", key="k") == {"x": 1}
        assert cache.get("ns2", key="k") == {"y": 2}

    def test_ttl_minutes_zero_means_zero_ttl(self, tmp_path):
        db = tmp_path / "zero_ttl.db"
        c = CacheManager(db_path=str(db), ttl_minutes=0)
        assert c.ttl_seconds == 0
        c.set("ns", {"a": 1}, key="k")
        # With ttl_minutes=0, expires_at == created_at, so already expired
        assert c.get("ns", key="k") is None

    def test_ttl_minutes_none_uses_default(self, tmp_path):
        db = tmp_path / "default_ttl.db"
        c = CacheManager(db_path=str(db), ttl_minutes=None)
        from src.config import settings

        expected = settings.data.cache_ttl_minutes * 60
        assert c.ttl_seconds == expected
