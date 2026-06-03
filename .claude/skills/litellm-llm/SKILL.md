---
name: litellm-llm
description: "Load when writing or modifying any LLM integration code in src/llm/, or when adding/changing LLM calls anywhere in the project."
user-invocable: false
---

<!-- WHAT THIS IS: A skill that loads as context when Claude works in this domain.
     HOW IT WORKS: Claude reads this automatically before writing code that matches the description.
     HOW TO CUSTOMIZE: Update the patterns and examples below as your project evolves.
     THINGS TO ADD: New conventions, discovered gotchas, team-specific patterns. -->

# LLM Integration Skill (litellm)

## Overview

All LLM calls in this project go through **litellm** — a unified API for DeepSeek, Gemini, Ollama, and other providers. The LLM is used **only for interpretation and narrative**, never for numerical calculations.

**Key files:**
- `src/llm/client.py` — the single entry point for all LLM calls
- `src/llm/prompts.py` — prompt templates (Jinja2 or f-string)
- `src/llm/parsers.py` — parse LLM outputs into structured data

## Critical Rule

**LLM does NOT do math.** All numerical calculations (moving averages, RSI, PE ratios, returns, drawdowns) are computed by deterministic Python code in `src/pipeline/analyzer.py` or `src/backtest/metrics.py`. The LLM receives pre-computed numbers and provides narrative interpretation.

```
[WRONG] prompt: "Calculate the 20-day MA for stock 000001"
[RIGHT] prompt: "The 20-day MA is 15.23, current price is 15.50. Interpret this signal."
```

## Conventions

- **All LLM calls MUST go through `src/llm/client.py`** — never import `litellm` directly in other modules
- **Use async** — all LLM calls are `async` to support concurrent analysis
- **Parse defensively** — LLM outputs can be malformed. Always wrap parsing in try/except with fallback
- **Log all LLM calls** — log prompt length, model, token usage, and latency
- **Use structured output** — prefer JSON mode or function calling when available

## Key Patterns

### Making an LLM Call

```python
# src/llm/client.py
from litellm import acompletion
from src.config import settings

async def analyze(prompt: str, system: str = "", model: str | None = None) -> str:
    """Single entry point for all LLM analysis calls."""
    model = model or settings.default_model  # e.g., "deepseek/deepseek-chat"
    logger.info(f"LLM call: model={model}, prompt_len={len(prompt)}")

    response = await acompletion(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,  # Low temp for consistent financial analysis
    )
    result = response.choices[0].message.content
    logger.info(f"LLM response: tokens={response.usage.total_tokens}")
    return result
```

### Prompt Template Pattern

```python
# src/llm/prompts.py
STOCK_ANALYSIS_TEMPLATE = """
你是一位专业的A股投资分析师。请根据以下技术指标和基本面数据，给出投资建议。

## 股票信息
- 代码: {stock_code}
- 名称: {stock_name}
- 当前价格: {current_price}

## 技术指标（已计算）
- 5日均线: {ma5}
- 20日均线: {ma20}
- RSI(14): {rsi}
- MACD: {macd}

## 基本面数据
- 市盈率(PE): {pe_ratio}
- 市净率(PB): {pb_ratio}
- 净资产收益率(ROE): {roe}

请给出:
1. 技术面分析（看涨/看跌/中性，及理由）
2. 基本面分析（估值是否合理）
3. 综合建议（买入/持有/卖出）
4. 风险提示

用JSON格式返回，包含以下字段: technical_view, fundamental_view, recommendation, risk_notes
"""
```

### Defensive Parsing

```python
# src/llm/parsers.py
import json
from dataclasses import dataclass

@dataclass
class AnalysisResult:
    technical_view: str
    fundamental_view: str
    recommendation: str  # "买入" | "持有" | "卖出"
    risk_notes: str

def parse_analysis(raw: str) -> AnalysisResult:
    """Parse LLM analysis output. Handles malformed responses gracefully."""
    try:
        json_str = raw
        if "```json" in raw:
            json_str = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            json_str = raw.split("```")[1].split("```")[0]

        data = json.loads(json_str)
        return AnalysisResult(
            technical_view=data["technical_view"],
            fundamental_view=data["fundamental_view"],
            recommendation=data["recommendation"],
            risk_notes=data.get("risk_notes", ""),
        )
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to parse LLM output as JSON: {e}")
        return AnalysisResult(
            technical_view=raw[:200],
            fundamental_view="解析失败，请查看原始输出",
            recommendation="持有",
            risk_notes="LLM输出解析失败，建议保守操作",
        )
```

## litellm Model Name Format

| Provider | Model String | Example |
|----------|-------------|---------|
| DeepSeek | `deepseek/deepseek-chat` | `deepseek/deepseek-chat` |
| Gemini | `gemini/gemini-2.0-flash` | `gemini/gemini-2.0-flash` |
| Ollama | `ollama/<model-name>` | `ollama/qwen2.5:14b` |

## Common Mistakes

- **Letting LLM calculate** — never ask LLM to compute MA, RSI, or any numerical metric
- **Not parsing defensively** — LLM output can be anything, always have fallback
- **High temperature** — use 0.1-0.3 for financial analysis, not 0.7+
- **Missing error handling** — API calls fail, handle timeouts and rate limits
- **Hardcoding model names** — use `settings.default_model` from config
- **Synchronous calls** — use `acompletion` (async), not `completion`

## Integration Points

- **Pipeline** (`src/pipeline/analyzer.py`) calls LLM client with pre-computed data
- **Decision** (`src/pipeline/decision.py`) calls LLM to synthesize multiple analyses
- **Reporter** (`src/pipeline/reporter.py`) calls LLM to generate human-readable reports
- **Backtest** does NOT use LLM — it's purely deterministic
