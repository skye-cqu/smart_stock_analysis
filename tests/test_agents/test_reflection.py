from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

from src.agents.memory import TradingMemoryLog
from src.agents.reflection import verify_decisions
from src.data.models import StockDailyData


def _make_provider(current_price: float = 12.0):
    """Create a mock DataProvider that returns data with the given close price."""
    provider = MagicMock()
    data = [
        StockDailyData(
            date=date.today().isoformat(),
            open=current_price,
            high=current_price + 0.1,
            low=current_price - 0.1,
            close=current_price,
            volume=1_000_000,
            amount=10_000_000,
        )
    ]
    provider.get_daily_data.return_value = data
    return provider


@pytest.fixture
def memory(tmp_path):
    """Create a TradingMemoryLog backed by a temporary database."""
    db_path = str(tmp_path / "test_reflection.db")
    return TradingMemoryLog(db_path=db_path)


@pytest.fixture
def old_decision(memory):
    """Store a decision dated yesterday so it qualifies for verification."""
    yesterday = (date.today() - timedelta(days=2)).isoformat()
    with sqlite3.connect(memory.db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO decisions (stock_code, stock_name, decision_date, recommendation, price_at_decision, reasoning) VALUES (?, ?, ?, ?, ?, ?)",
            ("000001", "平安银行", yesterday, "BUY", 10.0, "test"),
        )
        return cursor.lastrowid


@pytest.mark.asyncio
async def test_verify_updates_actual_return(memory, old_decision):
    provider = _make_provider(current_price=12.0)
    await verify_decisions(provider, memory=memory)

    with sqlite3.connect(memory.db_path) as conn:
        row = conn.execute(
            "SELECT actual_return FROM decisions WHERE id = ?", (old_decision,)
        ).fetchone()

    assert row is not None
    assert row[0] is not None
    assert row[0] == pytest.approx(0.2, abs=0.01)


@pytest.mark.asyncio
async def test_verify_no_unverified_decisions(memory):
    provider = _make_provider()
    # No decisions stored — should complete without error
    await verify_decisions(provider, memory=memory)
    provider.get_daily_data.assert_not_called()


@pytest.mark.asyncio
async def test_verify_skips_today_decision(memory):
    """Decision from today should not be verified (days_old=1)."""
    today = date.today().isoformat()
    with sqlite3.connect(memory.db_path) as conn:
        conn.execute(
            "INSERT INTO decisions (stock_code, stock_name, decision_date, recommendation, price_at_decision, reasoning) VALUES (?, ?, ?, ?, ?, ?)",
            ("000001", "平安银行", today, "BUY", 10.0, "test"),
        )

    provider = _make_provider(current_price=12.0)
    await verify_decisions(provider, memory=memory)
    provider.get_daily_data.assert_not_called()


@pytest.mark.asyncio
async def test_verify_handles_no_data_gracefully(memory, old_decision):
    """When DataProvider returns no data, the decision stays unverified."""
    provider = MagicMock()
    provider.get_daily_data.return_value = []

    await verify_decisions(provider, memory=memory)

    with sqlite3.connect(memory.db_path) as conn:
        row = conn.execute(
            "SELECT actual_return FROM decisions WHERE id = ?", (old_decision,)
        ).fetchone()

    assert row[0] is None
