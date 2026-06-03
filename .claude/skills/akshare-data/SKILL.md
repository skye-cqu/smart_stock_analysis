---
name: akshare-data
description: "Load when writing or modifying any AkShare or Tushare data fetching, caching, or data transformation code in src/data/."
user-invocable: false
---

<!-- WHAT THIS IS: A skill that loads as context when Claude works in this domain.
     HOW IT WORKS: Claude reads this automatically before writing code that matches the description.
     HOW TO CUSTOMIZE: Update the patterns and examples below as your project evolves.
     THINGS TO ADD: New conventions, discovered gotchas, team-specific patterns. -->

# AkShare & Data Layer Skill

## Overview

This project uses **AkShare** as the primary data source for A-stock market data (free, no token) and **Tushare Pro** as a fallback for data AkShare lacks. All data fetching goes through dedicated client modules, and results are cached in SQLite.

**Key files:**
- `src/data/akshare_client.py` — all AkShare API calls
- `src/data/tushare_client.py` — all Tushare API calls (requires token)
- `src/data/cache.py` — SQLite caching layer
- `src/data/models.py` — dataclass definitions for all data structures

## Conventions

- **Never import `akshare` or `tushare` outside of their client files.** All data access goes through the client modules.
- **Always check the cache first** before making an API call. The cache layer handles TTL checking.
- **Rate limit all API calls** — add `time.sleep(0.5)` between AkShare calls. Tushare has stricter limits (check your tier).
- **Stock codes are always 6-digit zero-padded strings**: `"000001"`, `"600519"`. Never use integers.
- **Return dataclasses, not dicts** — define response types in `models.py` and return typed objects.
- **Handle market closure gracefully** — during non-trading hours, data may be stale or unavailable. The cache layer handles this.

## Key Patterns

### Fetching with Cache

```python
from src.data.cache import CacheManager
from src.data.models import StockDailyData

async def get_daily_data(stock_code: str, start_date: str, end_date: str) -> list[StockDailyData]:
    cache = CacheManager()
    cached = cache.get("daily", stock_code=stock_code, start=start_date, end=end_date)
    if cached is not None:
        return cached

    time.sleep(0.5)  # Rate limit
    raw = akshare.stock_zh_a_hist(symbol=stock_code, period="daily",
                                   start_date=start_date, end_date=end_date)
    result = [StockDailyData.from_akshare(row) for _, row in raw.iterrows()]
    cache.set("daily", result, stock_code=stock_code, start=start_date, end=end_date)
    return result
```

### Stock Code Normalization

```python
def normalize_stock_code(code: str | int) -> str:
    """Normalize stock code to 6-digit zero-padded string."""
    code_str = str(code).strip()
    if len(code_str) < 6:
        code_str = code_str.zfill(6)
    return code_str

def get_market_prefix(code: str) -> str:
    """Return 'SH' or 'SZ' based on stock code prefix."""
    if code.startswith("6"):
        return "SH"
    return "SZ"
```

## Common Mistakes

- **Calling AkShare without rate limiting** — will get rate-limited or blocked
- **Using integer stock codes** — `"001".zfill(6)` is correct, `1` is not
- **Ignoring cache invalidation** — market data changes daily, cache must respect TTL
- **Not handling empty DataFrames** — AkShare returns empty DFs for invalid codes or closed markets
- **Hardcoding date ranges** — use `datetime.now()` and relative offsets, not fixed dates

## AkShare Common Functions

| Function | Purpose | Notes |
|----------|---------|-------|
| `stock_zh_a_hist()` | Daily OHLCV data | Most used function |
| `stock_zh_a_spot_em()` | Real-time quotes | A-stock spot data from EastMoney |
| `stock_individual_info_em()` | Stock basic info | Company name, industry, etc. |
| `stock_financial_analysis_indicator()` | Financial ratios | PE, PB, ROE, etc. |
| `stock_zh_a_gdhs_detail_em()` | Shareholder data | Top 10 shareholders |

## Integration Points

- **Pipeline** (`src/pipeline/`) calls data clients to fetch stock data before analysis
- **Backtest** (`src/backtest/`) uses historical data fetched by data clients
- **LLM** (`src/llm/`) receives pre-computed data from data layer — never fetches data directly
