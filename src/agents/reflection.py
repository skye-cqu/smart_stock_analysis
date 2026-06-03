from __future__ import annotations

import logging
from datetime import date

from src.agents.memory import TradingMemoryLog

logger = logging.getLogger(__name__)


async def verify_decisions(provider, memory: TradingMemoryLog | None = None) -> None:
    """Verify past trading decisions by fetching current prices and computing returns."""
    if memory is None:
        memory = TradingMemoryLog()

    unverified = memory.get_unverified(days_old=1)
    if not unverified:
        logger.info("No unverified decisions found")
        return

    today = date.today().isoformat()
    verified = 0

    for decision in unverified:
        try:
            data = provider.get_daily_data(decision["stock_code"], decision["date"], today)
            if not data:
                stock = decision["stock_code"]
                did = decision["id"]
                logger.warning(f"No data for {stock} to verify decision {did}")
                continue

            current_price = data[-1].close
            entry_price = decision["price"]
            if entry_price <= 0:
                continue

            actual_return = (current_price - entry_price) / entry_price
            memory.update_with_outcome(decision["id"], round(actual_return, 6), "")
            verified += 1
        except Exception as e:
            logger.warning(f"Failed to verify decision {decision['id']}: {e}")

    logger.info(f"Verified {verified}/{len(unverified)} decisions")
