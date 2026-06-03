# smart_stock_analysis

> A股AI多Agent投资分析系统 — 选股→评分→多角色辩论→决策→回测全链路。
> Python + litellm，不做自动交易，LLM只做解读，数值计算用确定性代码防幻觉。
> 参考架构：TradingAgents (论文) + virattt/ai-hedge-fund，针对A股场景定制。

---

## Commands

| Command | Description |
|---------|-------------|
| `python -m venv .venv` | Create virtual environment |
| `source .venv/Scripts/activate` | Activate venv (Git Bash on Windows) |
| `pip install -r requirements.txt` | Install dependencies |
| `pytest` | Run test suite |
| `pytest --cov=src --cov-report=term-missing` | Run tests with coverage |
| `ruff check .` | Lint with ruff |
| `ruff format .` | Format with ruff |
| `python -m src.main --stock 000001` | Quick analysis (single LLM call) |
| `python -m src.main --stock 000001 --mode full` | Full multi-agent analysis (7 analysts + debate) |

---

## Architecture

```
smart_stock_analysis/
  src/
    main.py              # Entry point — quick (single LLM) or full (multi-agent) mode
    config.py            # Settings, env vars, model configs (dataclasses)
    data/
      provider.py        # Data source priority chain (AkShare→Tushare) + cache
      akshare_client.py  # AkShare data fetching (primary, Sina→EastMoney fallback)
      tushare_client.py  # Tushare data fetching (fallback, requires token)
      cache.py           # SQLite caching layer (WAL mode, MD5 key, TTL=5min expiry)
      models.py          # Data models (StockDailyData, StockInfo, ScoreResult, etc.)
    strategy/
      base.py            # BaseStrategy ABC (calculate_indicators → generate_signal)
      registry.py        # StrategyRegistry — auto-discovers builtin/ + YAML override
      builtin/
        ma_cross.py      # MA golden cross / death cross (5/20 default)
        macd_divergence.py # MACD bottom divergence (EMA12/26/9)
        volume_breakout.py # Volume breakout (2x vol ratio)
        rsi_oversold.py  # RSI oversold / overbought (30/70 default)
    scoring/
      engine.py          # Five-dimensional scoring engine (weighted + veto)
      technical_scorer.py # MA cross + RSI + 20-day high proximity
      capital_flow_scorer.py # Volume surge + price trend + turnover proxy
      fundamental_scorer.py # PE/PB/ROE thresholds
      sector_scorer.py   # Sector relative performance via AkShare board data
      event_scorer.py    # Volume spike + limit up/down + consecutive trend
    llm/
      client.py          # litellm Router with 3-provider fallback (DeepSeek→Gemini→Ollama)
      prompts.py         # Stock analysis prompt template (Chinese)
      parsers.py         # Defensive JSON parsing with markdown code block stripping
    agents/              # Multi-agent decision system (inspired by TradingAgents)
      schemas.py         # Pydantic models: AnalystReport, DebateState, PortfolioDecision
      roles.py           # 7 analyst factories (tech/fundamental/news/policy/hotmoney/lockup/risk)
      debate.py          # Bull/Bear debate (2 rounds) + Risk debate (3-way: risky/safe/neutral)
      memory.py          # TradingMemoryLog — SQLite decision storage + past context retrieval
      quality_gate.py    # Dual-layer quality check (code rules + LLM assessment)
      orchestrator.py    # 8-step pipeline: context→analysts→quality→debate→risk→decision→store
      reflection.py      # Verify past decisions against current prices, update outcomes
    pipeline/
      runner.py          # Pipeline executor — quick (single LLM) or full (multi-agent) mode
      stages.py          # Pipeline stage enum definitions
    notifications/
      feishu.py          # Feishu webhook card push
    backtest/            # Backtest engine with A-stock cost model (commission+stamp+slippage)
    risk/                # Volatility-based risk assessment + stop-loss (fixed + trailing)
    report/              # Markdown report generator (五维评分 + strategy signals + AI analysis)
  tests/
    conftest.py          # Fixtures: sample_stock_code, sample_stock_codes
    test_llm/            # LLM client tests (mock router, retry, fallback)
    test_scoring/        # SectorScorer + EventScorer tests
    test_backtest/       # Backtest engine tests (costs, metrics, empty data)
    test_risk/           # Risk manager tests (volatility, stop-loss)
    test_agents/         # Reflection engine tests
    test_report/         # Report generator tests
  configs/
    strategies.yaml      # Strategy parameter overrides (ma_cross, rsi_oversold, volume_breakout)
  data/
    sqlite/              # SQLite database files (stock.db)
  .env.example           # Environment variable template
  .env                   # Local env (gitignored)
  CLAUDE.md              # This file
  requirements.txt       # Python dependencies
  pyproject.toml         # Project metadata + ruff + pytest config
```

---

## Code Style

- **Python 3.11+**, all files use `from __future__ import annotations`
- **Formatter**: `ruff format` (line length 100, double quotes)
- **Linter**: `ruff check` with `E, F, W, I, N, UP, B, A, SIM` rule sets
- **Naming**: `snake_case` functions/variables, `PascalCase` classes, `UPPER_SNAKE` constants
- **Imports**: absolute imports from `src.` root, grouped stdlib → third-party → local
- **Type hints**: required on all public function signatures, use `X | None` not `Optional[X]`
- **Dataclasses** over dicts for structured data — define in `src/data/models.py`
- **Error handling**: explicit `try/except` with specific exceptions, never bare `except:`
- **Docstrings**: Google style on public functions only, no docstrings on private helpers
- **Tests**: `pytest` with fixtures in `conftest.py`, file naming `test_<module>.py`

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DEEPSEEK_API_KEY` | DeepSeek API key for LLM analysis | Yes |
| `DEEPSEEK_BASE_URL` | DeepSeek API base URL | No (default: `https://api.deepseek.com`) |
| `GEMINI_API_KEY` | Google Gemini API key (alternative model) | No |
| `OLLAMA_BASE_URL` | Ollama local model server URL | No (default: `http://localhost:11434`) |
| `OLLAMA_MODEL` | Ollama model name | No (default: `qwen2.5:14b`) |
| `TUSHARE_TOKEN` | Tushare Pro API token | No (AkShare is primary) |
| `FEISHU_WEBHOOK_URL` | Feishu bot webhook URL for notifications | No |
| `SQLITE_DB_PATH` | Path to SQLite database file | No (default: `data/sqlite/stock.db`) |
| `LOG_LEVEL` | Logging level | No (default: `INFO`) |
| `LLM_PROVIDER` | Default LLM provider: `deepseek`, `gemini`, `ollama` | No (default: `deepseek`) |
| `LLM_MODEL` | Default model name for the chosen provider | No |
| `ANALYSIS_MAX_CONCURRENCY` | Max concurrent stock analysis tasks | No (default: `5`) |
| `CACHE_TTL_MINUTES` | Cache TTL for market data in minutes | No (default: `5`) |

---

## Key Design Decisions

1. **No LangChain/LangGraph** — pure Python + litellm. All orchestration is explicit code (asyncio.gather).
2. **LLM for interpretation only** — numerical calculations (MA, RSI, PE ratios) are deterministic Python code. LLM receives pre-computed data and provides narrative analysis.
3. **AkShare as primary data source** — free, no token required, covers A-stock well. Tushare as fallback for data AkShare lacks.
4. **SQLite for storage** — lightweight, no server needed, good for single-user analysis. WAL mode for concurrent reads.
5. **Multi-agent debate architecture** — 7 analyst roles → bull/bear debate (2 rounds) → 3-way risk debate → investment director final decision. Inspired by TradingAgents paper.
6. **Dual-mode pipeline** — `--mode quick` for fast single-LLM analysis, `--mode full` for multi-agent debate (13+ LLM calls).
7. **Plugin-based strategies** — BaseStrategy ABC + YAML config + auto-discovery from builtin/.
8. **Quality gate** — code-level checks (length/confidence/key_points) + LLM quality assessment before debate.

### Delivery Status (as of 2026-06)

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: Analysis pipeline | **Done** | Data→Strategy→Scoring→LLM single-pass |
| Phase 2: Multi-agent decision | **Done** | 7 analysts + debate + quality gate + memory |
| Phase 3: Backtest engine | **Done** | A-stock cost model, equity curve, Sharpe/drawdown/win-rate |
| Phase 4: Risk & Portfolio mgmt | **Done** | Volatility-based position sizing, fixed + trailing stop-loss |
| Phase 5: Reporting & Reflection | **Done** | Markdown reports, decision verification, LLM fallback chain |

---

## Gotchas

- **AkShare rate limits**: AkShare has undocumented rate limits. Always add `time.sleep(0.5)` between API calls. Use the cache layer aggressively.
- **A-stock trading hours**: Data is only updated during/after trading hours (9:30-15:00 CST). Running analysis during market hours gives incomplete data.
- **Tushare requires registration**: Tushare Pro needs a token from `tushare.pro`. Free tier has daily call limits. Use AkShare first.
- **litellm model names**: DeepSeek model format is `deepseek/deepseek-chat` (provider/model). Gemini is `gemini/gemini-2.0-flash`. Ollama is `ollama/<model-name>`.
- **SQLite concurrent writes**: SQLite doesn't handle concurrent writes well. Use WAL mode and serialize write operations.
- **Stock codes**: A-stock codes are 6-digit strings (`"000001"`, `"600519"`). Always zero-pad. SH prefix = Shanghai (60xxxx), SZ prefix = Shenzhen (00xxxx, 30xxxx).
- **Multi-agent LLM cost**: `--mode full` triggers 13+ LLM calls per stock (7 analysts + 2 debate rounds + 3 risk + 1 decision). Use `--mode quick` for development.
- **LLM JSON parsing fragility**: All agents output JSON wrapped in markdown code blocks. `parsers.py` handles stripping, but each agent module (`roles.py`, `orchestrator.py`, `quality_gate.py`) has its own inline parser — fix bugs in all three if changing the pattern.
- **Analyst gather swallows exceptions**: `asyncio.gather(return_exceptions=True)` in `orchestrator.py:42` silently drops failed analysts. Check `valid_reports` count in logs.
- **Sector scorer AkShare dependency**: `sector_scorer.py` calls `stock_board_industry_cons_em()` which may fail if AkShare changes its API. Returns 0.0 on error (graceful degradation).

---

## Troubleshooting

| 问题 | 解决 |
|------|------|
| `ModuleNotFoundError: akshare` | 确认虚拟环境已激活，`pip install akshare` |
| `DEEPSEEK_API_KEY not set` | 检查 `.env` 文件是否填写正确 |
| `No daily data for 000001` | 非交易时间数据可能为空，属正常现象 |
| `LLM call failed` | 检查 API Key 是否有效，网络是否连通 |
| `SQLite database is locked` | 确认没有其他进程占用数据库文件 |
| `StrategyRegistry found 0 strategies` | 检查 `src/strategy/builtin/` 目录下是否有 `__init__.py` |
| `Feishu notification failed` | 检查 webhook URL 是否正确，网络是否可达 |
| `Got 0 analyst reports` (full mode) | LLM 全部超时或 API key 无效，检查网络和日志 |
| `Quality gate: D` (full mode) | 分析师报告质量过低（内容过短/缺少要点），检查 LLM 输出 |
| `Failed to parse final decision` | LLM 未返回有效 JSON，自动降级为 HOLD + 0.3 信心度 |

---

## Claude Workflow

### Slash Commands

| Command | When to use |
|---------|------------|
| `/commit` | After completing a feature — stages and commits with conventional message |
| `/review-pr` | Before opening a PR — reviews the diff and flags issues |
| `/test` | Run pytest and report results |
| `/analyze` | Run the analysis pipeline for a stock |

### Agents

| Agent | When to use |
|-------|------------|
| `code-reviewer` | After implementing a feature, before creating a PR |
| `security-auditor` | Any code touching API keys, external data, or input validation |
| `data-pipeline-reviewer` | Data fetching, caching, and transformation logic |

### Skills

| Skill | Loaded when |
|-------|------------|
| `project-conventions` | Always — applies to all code |
| `akshare-data` | Writing or modifying AkShare data fetching code |
| `litellm-llm` | Writing or modifying LLM integration code |
| `stock-analysis` | Writing pipeline analysis or backtest logic |

### Memory

Claude maintains persistent memory in `memory/`. Tell Claude to "remember" facts
and it will update the appropriate file. These persist across sessions.

---

## Resources

- [AkShare Documentation](https://akshare.akfamily.xyz/) — A-stock data API
- [Tushare Pro](https://tushare.pro/) — Financial data API (requires registration)
- [litellm Docs](https://docs.litellm.ai/) — LLM provider abstraction
- [DeepSeek Platform](https://platform.deepseek.com/) — API key management
- [Feishu Open Platform](https://open.feishu.cn/) — Bot webhook setup

### Reference Open-Source Projects

| Project | Stars | What we reference |
|---------|-------|-------------------|
| [TradingAgents (TauricResearch)](https://github.com/TauricResearch/TradingAgents) | — | Multi-agent bull/bear debate architecture, LangGraph pipeline design |
| [TradingAgents-CN (hsliuping)](https://github.com/hsliuping/TradingAgents-CN) | 27.7k | A-stock data source chain (AkShare+Tushare+BaoStock), Chinese prompt patterns |
| [virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund) | 40k+ | Analyst→Risk→PM three-layer agent design, 19 investor-style agents |
