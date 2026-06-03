---
name: stock-analysis
description: "Load when writing or modifying pipeline analysis (src/pipeline/), backtest logic (src/backtest/), or stock data models (src/data/models.py)."
user-invocable: false
---

<!-- WHAT THIS IS: A skill that loads as context when Claude works in this domain.
     HOW IT WORKS: Claude reads this automatically before writing code that matches the description.
     HOW TO CUSTOMIZE: Update the patterns and examples below as your project evolves.
     THINGS TO ADD: New conventions, discovered gotchas, team-specific patterns. -->

# Stock Analysis Pipeline Skill

## Overview

The analysis pipeline is the core of this project: **selector -> analyzer -> decision -> reporter**. It takes a stock code, fetches data, computes technical/fundamental indicators (deterministic code), asks LLM to interpret the results, and pushes a report.

**Key files:**
- `src/pipeline/selector.py` — stock screening/selection
- `src/pipeline/analyzer.py` — technical + fundamental analysis (all deterministic math)
- `src/pipeline/decision.py` — LLM-assisted decision synthesis
- `src/pipeline/reporter.py` — report generation + Feishu push
- `src/backtest/engine.py` — backtesting engine
- `src/backtest/strategies.py` — strategy definitions
- `src/backtest/metrics.py` — performance metrics (Sharpe, max drawdown, etc.)

## Architecture Flow

```
Stock Code(s)
    |
[selector.py] — filter by criteria (market cap, industry, etc.)
    |
[analyzer.py] — compute ALL numerical indicators (MA, RSI, MACD, PE, PB, ROE)
    |
[decision.py] — send pre-computed data to LLM for interpretation
    |
[reporter.py] — format report, push to Feishu, save to SQLite
```

## Critical Design Rules

1. **Deterministic math in Python** — MA, RSI, MACD, PE ratios, returns, drawdowns are all computed with standard formulas in `analyzer.py` and `metrics.py`. NEVER ask the LLM to calculate these.

2. **LLM for interpretation only** — the LLM receives a structured prompt with pre-computed numbers and generates narrative analysis (bullish/bearish reasoning, risk assessment, recommendation).

3. **Backtest is 100% deterministic** — `src/backtest/` never calls the LLM. Strategies are pure Python functions that generate buy/sell signals from historical data.

## Conventions

- **Dataclasses for all data structures** — define in `src/data/models.py`
- **Each pipeline stage is a standalone function** — can be called independently for testing
- **No global state** — pass data explicitly between stages
- **Log every stage** — log input/output of each pipeline stage for debugging

## Key Patterns

### Technical Indicator Calculation

```python
# src/pipeline/analyzer.py
import numpy as np

def compute_ma(prices: list[float], period: int) -> list[float | None]:
    """Compute simple moving average. Returns None for insufficient data."""
    result: list[float | None] = []
    for i in range(len(prices)):
        if i < period - 1:
            result.append(None)
        else:
            window = prices[i - period + 1 : i + 1]
            result.append(sum(window) / period)
    return result

def compute_rsi(prices: list[float], period: int = 14) -> float:
    """Compute RSI using standard Wilder's smoothing method."""
    if len(prices) < period + 1:
        raise ValueError(f"Need at least {period + 1} prices for RSI({period})")

    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))
```

### Pipeline Stage Pattern

```python
# src/pipeline/analyzer.py
@dataclass
class AnalysisResult:
    stock_code: str
    stock_name: str
    current_price: float
    ma5: float | None
    ma20: float | None
    rsi: float
    macd: float
    pe_ratio: float | None
    pb_ratio: float | None
    roe: float | None
    analysis_date: str

async def analyze_stock(stock_code: str) -> AnalysisResult:
    """Full analysis of a single stock. All computation is deterministic."""
    # 1. Fetch data
    daily_data = await get_daily_data(stock_code, ...)
    info = await get_stock_info(stock_code)

    # 2. Compute technical indicators (deterministic)
    prices = [d.close for d in daily_data]
    ma5 = compute_ma(prices, 5)[-1]
    ma20 = compute_ma(prices, 20)[-1]
    rsi = compute_rsi(prices, 14)
    macd = compute_macd(prices)

    # 3. Fetch fundamental data
    pe = info.get("pe_ratio")
    pb = info.get("pb_ratio")
    roe = info.get("roe")

    return AnalysisResult(
        stock_code=stock_code,
        stock_name=info["name"],
        current_price=prices[-1],
        ma5=ma5, ma20=ma20, rsi=rsi, macd=macd,
        pe_ratio=pe, pb_ratio=pb, roe=roe,
        analysis_date=datetime.now().strftime("%Y-%m-%d"),
    )
```

### Backtest Strategy Pattern

```python
# src/backtest/strategies.py
def ma_crossover_strategy(data: list[StockDailyData], short: int = 5, long: int = 20) -> list[Signal]:
    """Generate buy/sell signals based on MA crossover."""
    prices = [d.close for d in data]
    ma_short = compute_ma(prices, short)
    ma_long = compute_ma(prices, long)

    signals = []
    for i in range(1, len(data)):
        if ma_short[i] and ma_long[i] and ma_short[i - 1] and ma_long[i - 1]:
            if ma_short[i] > ma_long[i] and ma_short[i - 1] <= ma_long[i - 1]:
                signals.append(Signal(date=data[i].date, action="buy", price=data[i].close))
            elif ma_short[i] < ma_long[i] and ma_short[i - 1] >= ma_long[i - 1]:
                signals.append(Signal(date=data[i].date, action="sell", price=data[i].close))
    return signals
```

## Common Mistakes

- **Computing indicators in the prompt** — "calculate RSI" in a prompt means the LLM will hallucinate a number
- **Using numpy for simple windowed stats** — pure Python lists are fine for the data sizes we handle
- **Not handling missing data** — stocks can have suspended trading days, resulting in gaps
- **Off-by-one in window calculations** — MA at index `i` should use data from `i-period+1` to `i` inclusive
- **Integer stock codes** — always use 6-digit zero-padded strings
- **Hardcoded date ranges** — use `datetime.now()` and relative offsets

## A-Stock Specific Knowledge

- **Trading calendar**: A-stocks trade Mon-Fri, excluding Chinese holidays. No weekend data.
- **Limit up/down**: Daily price limit is +/-10% (+/-20% for ChiNext/STAR Market stocks)
- **T+1 rule**: Shares bought today can only be sold tomorrow
- **Market segments**: Main board (60xxxx, 00xxxx), ChiNext (30xxxx), STAR Market (68xxxx), BSE (8xxxxx, 4xxxxx)
