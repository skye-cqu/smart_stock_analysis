from __future__ import annotations

from datetime import date, timedelta

from src.agents.memory import TradingMemoryLog


class TestTradingMemoryLog:
    def test_store_and_retrieve(self, tmp_path):
        db = str(tmp_path / "test.db")
        mem = TradingMemoryLog(db_path=db)
        mid = mem.store_decision(
            stock_code="000001",
            stock_name="平安银行",
            recommendation="买入",
            price=12.5,
            reasoning="看好",
        )
        assert mid is not None
        ctx = mem.get_past_context("000001")
        assert "000001" in ctx or "平安银行" in ctx or "买入" in ctx

    def test_get_past_context_empty(self, tmp_path):
        db = str(tmp_path / "test.db")
        mem = TradingMemoryLog(db_path=db)
        assert mem.get_past_context("999999") == ""

    def test_update_with_outcome(self, tmp_path):
        db = str(tmp_path / "test.db")
        mem = TradingMemoryLog(db_path=db)
        mid = mem.store_decision(
            stock_code="000001",
            stock_name="平安银行",
            recommendation="买入",
            price=12.5,
            reasoning="看好",
        )
        mem.update_with_outcome(mid, actual_return=0.05, reflection="涨了5%")
        ctx = mem.get_past_context("000001")
        assert "+5" in ctx or "反思" in ctx

    def test_get_past_context_limit(self, tmp_path):
        db = str(tmp_path / "test.db")
        mem = TradingMemoryLog(db_path=db)
        for i in range(10):
            mem.store_decision(
                stock_code="000001",
                stock_name="平安银行",
                recommendation="买入",
                price=12.0 + i * 0.1,
                reasoning=f"理由{i}",
            )
        ctx = mem.get_past_context("000001", limit=3)
        lines = [l for l in ctx.strip().split("\n") if l.startswith("-")]
        assert len(lines) == 3

    def test_get_unverified_returns_old_decisions(self, tmp_path):
        db = str(tmp_path / "test.db")
        mem = TradingMemoryLog(db_path=db)
        # Insert with yesterday's date
        import sqlite3

        yesterday = (date.today() - timedelta(days=2)).isoformat()
        with sqlite3.connect(db) as conn:
            conn.execute(
                "INSERT INTO decisions (stock_code, stock_name, decision_date, recommendation, price_at_decision, reasoning) VALUES (?, ?, ?, ?, ?, ?)",
                ("000001", "平安银行", yesterday, "买入", 12.5, "test"),
            )
        unverified = mem.get_unverified(days_old=1)
        assert len(unverified) >= 1
        assert unverified[0]["stock_code"] == "000001"

    def test_get_unverified_excludes_verified(self, tmp_path):
        db = str(tmp_path / "test.db")
        mem = TradingMemoryLog(db_path=db)
        import sqlite3

        yesterday = (date.today() - timedelta(days=2)).isoformat()
        with sqlite3.connect(db) as conn:
            conn.execute(
                "INSERT INTO decisions (stock_code, stock_name, decision_date, recommendation, price_at_decision, reasoning, actual_return, reflection) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ("000001", "平安银行", yesterday, "买入", 12.5, "test", 0.05, "ok"),
            )
        unverified = mem.get_unverified(days_old=1)
        assert len(unverified) == 0

    def test_empty_unverified(self, tmp_path):
        db = str(tmp_path / "test.db")
        mem = TradingMemoryLog(db_path=db)
        assert mem.get_unverified() == []

    def test_multiple_stocks_isolated(self, tmp_path):
        db = str(tmp_path / "test.db")
        mem = TradingMemoryLog(db_path=db)
        mem.store_decision(
            stock_code="000001", stock_name="A", recommendation="买入", price=10, reasoning="x"
        )
        mem.store_decision(
            stock_code="600519", stock_name="B", recommendation="卖出", price=20, reasoning="y"
        )
        ctx_a = mem.get_past_context("000001")
        ctx_b = mem.get_past_context("600519")
        assert "买入" in ctx_a
        assert "卖出" in ctx_b
        assert "买入" not in ctx_b
