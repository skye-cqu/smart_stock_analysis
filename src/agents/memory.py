from __future__ import annotations

import logging
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from src.config import settings

logger = logging.getLogger(__name__)


class TradingMemoryLog:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or settings.data.sqlite_db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT NOT NULL,
                    stock_name TEXT NOT NULL,
                    decision_date TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    price_at_decision REAL NOT NULL,
                    reasoning TEXT NOT NULL,
                    actual_return REAL,
                    reflection TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def store_decision(
        self,
        stock_code: str,
        stock_name: str,
        recommendation: str,
        price: float,
        reasoning: str,
    ) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO decisions (stock_code, stock_name, decision_date, recommendation, price_at_decision, reasoning) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    stock_code,
                    stock_name,
                    date.today().isoformat(),
                    recommendation,
                    price,
                    reasoning,
                ),
            )
            return cursor.lastrowid

    def update_with_outcome(self, decision_id: int, actual_return: float, reflection: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE decisions SET actual_return = ?, reflection = ? WHERE id = ?",
                (actual_return, reflection, decision_id),
            )

    def get_past_context(self, stock_code: str, limit: int = 5) -> str:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT decision_date, recommendation, price_at_decision, actual_return, reflection FROM decisions WHERE stock_code = ? ORDER BY decision_date DESC LIMIT ?",
                (stock_code, limit),
            ).fetchall()
        if not rows:
            return ""
        context = "## 历史决策记录\n"
        for row in rows:
            ctx_date, rec, price, ret, refl = row
            ret_str = f"{ret:+.2%}" if ret is not None else "待验证"
            context += f"- {ctx_date}: {rec} @ {price:.2f}, 收益: {ret_str}"
            if refl:
                context += f", 反思: {refl}"
            context += "\n"
        return context

    def get_unverified(self, days_old: int = 1) -> list[dict]:
        cutoff = (date.today() - timedelta(days=days_old)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, stock_code, price_at_decision, decision_date FROM decisions WHERE actual_return IS NULL AND decision_date < ?",
                (cutoff,),
            ).fetchall()
        return [{"id": r[0], "stock_code": r[1], "price": r[2], "date": r[3]} for r in rows]
