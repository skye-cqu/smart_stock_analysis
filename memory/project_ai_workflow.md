---
name: project-ai-workflow
description: How AI tools are integrated into this project's development workflow — agents, commands, hooks, and MCP servers in use
type: project
---

<!-- Update this file as your AI workflow evolves. Claude reads it every session.
     The more specific you are, the less you'll need to re-explain things to Claude. -->

# Project AI Workflow

## Slash Commands

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/commit` | Stage and create a conventional commit | After completing a feature or fix |
| `/review-pr` | Review the current branch before opening a PR | Before `gh pr create` |
| `/test` | Run pytest suite and report results | After any code change |
| `/analyze` | Run the stock analysis pipeline | Test pipeline or analyze a stock |

## Agents

| Agent | When Claude Uses It |
|-------|---------------------|
| `code-reviewer` | Reviewing changed code for bugs, security, and style issues |
| `security-auditor` | Any code touching API keys, external data, credentials, or input validation |
| `data-pipeline-reviewer` | Data fetching, caching, transformation, and pipeline logic |

## Skills (Auto-loaded Context)

| Skill | Loaded When |
|-------|------------|
| `project-conventions` | Always — applies to all code |
| `akshare-data` | Writing/modifying data fetching code in `src/data/` |
| `litellm-llm` | Writing/modifying LLM integration in `src/llm/` |
| `stock-analysis` | Writing/modifying pipeline or backtest code |

## MCP Servers

| Server | Purpose |
|--------|---------|
| `context7` | Live documentation lookup for any library (AkShare, litellm, etc.) |

## Project-Specific AI Context

### Core Design Principle
**LLM does NOT do math.** All numerical calculations are deterministic Python code. The LLM only interprets pre-computed data. This is the #1 rule of this project.

### Before Writing Data Code
- Always read `src/data/akshare_client.py` first to understand existing patterns
- Check `src/data/cache.py` for caching conventions
- Use `time.sleep(0.5)` between all AkShare API calls

### Before Writing LLM Code
- All LLM calls MUST go through `src/llm/client.py`
- Never import `litellm` directly in other modules
- Parse LLM outputs defensively with try/except fallback
- Use temperature 0.1-0.3 for financial analysis

### Before Writing Pipeline Code
- Read `src/pipeline/analyzer.py` for indicator calculation patterns
- Read `src/data/models.py` for dataclass definitions
- Each pipeline stage should be a pure function (no side effects)
- Stock codes are always 6-digit zero-padded strings

### Stock Code Format
- A-stock codes: `"000001"`, `"600519"` (6-digit, zero-padded)
- SH prefix = Shanghai (60xxxx), SZ prefix = Shenzhen (00xxxx, 30xxxx)
- Never use integers for stock codes

### litellm Model Names
- DeepSeek: `deepseek/deepseek-chat`
- Gemini: `gemini/gemini-2.0-flash`
- Ollama: `ollama/qwen2.5:14b`
