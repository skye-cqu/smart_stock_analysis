---
name: project-conventions
description: Apply the coding conventions and standards defined in CLAUDE.md for this project. Invoke this skill before writing new code, creating files, or refactoring — especially when the user hasn't specified a style preference. Claude-invocable only.
user-invocable: false
---

<!-- WHAT THIS IS: A skill that loads as context when Claude works in this domain.
     HOW IT WORKS: Claude reads this automatically before writing code that matches the description.
     HOW TO CUSTOMIZE: Update the patterns and examples below as your project evolves.
     THINGS TO ADD: New conventions, discovered gotchas, team-specific patterns. -->

# Project Conventions Skill

This skill reminds Claude to read and apply project-specific conventions before writing code.

## What to Read First

Before writing any code, always read:

1. **`CLAUDE.md`** — the authoritative source for this project's commands, architecture, and style
2. **Neighboring files** — files in the same directory as the file being created/edited reveal local patterns
3. **`memory/project_ai_workflow.md`** — AI-specific conventions for this project

## Core Principles

- **Match the surrounding style exactly** — if the codebase uses tabs, use tabs; if it uses `const`, use `const`
- **Read before you write** — read at least 2 existing files in the relevant module before creating anything new
- **No debug artifacts** — never commit `console.log`, `print()`, `debugger`, or commented-out blocks
- **No silent failures** — always propagate or log errors; never swallow exceptions

## Python Conventions for This Project

- **Python 3.11+** — use `from __future__ import annotations` in every file
- **Line length**: 100 characters max (ruff format)
- **Quotes**: double quotes everywhere
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_SNAKE` for constants
- **Imports**: absolute from `src.` root, grouped: stdlib -> third-party -> local, one blank line between groups
- **Type hints**: required on all public function signatures, use `X | None` not `Optional[X]`
- **Dataclasses**: use for structured data, define in `src/data/models.py`
- **Error handling**: specific exceptions, never bare `except:`, always log the error
- **Docstrings**: Google style on public functions only
- **No print()**: use `logging` module everywhere, get logger with `logger = logging.getLogger(__name__)`

## LLM Code Rules (Critical)

- **Never let LLM do math** — all numerical calculations (MA, RSI, PE, returns) must be deterministic Python
- **LLM receives pre-computed data** — format data as structured text, let LLM interpret and narrate
- **All LLM calls go through `src/llm/client.py`** — never import litellm directly elsewhere
- **Parse LLM outputs defensively** — use `src/llm/parsers.py`, handle malformed responses

## Data Code Rules

- **All API calls go through `src/data/akshare_client.py` or `tushare_client.py`** — never call APIs directly
- **Always cache** — check `src/data/cache.py` before making external API calls
- **Rate limit** — add `time.sleep(0.5)` between AkShare API calls
- **Stock codes** — always 6-digit zero-padded strings: `"000001"`, `"600519"`

## Before Finishing Any Task

Run through this checklist mentally:

- [ ] Does the new code match the surrounding style?
- [ ] Are all variables and functions named consistently with the rest of the file?
- [ ] Is there any debug code or dead code to remove?
- [ ] Are there hardcoded values that should be constants or environment variables?
- [ ] Does this need a test? If yes, was one written or is one planned?
- [ ] If this touches LLM: is numerical logic in deterministic code, not in the prompt?
- [ ] If this touches data APIs: is caching used and rate limiting applied?

## Customizing This Skill

Update the sections above to reflect your project's actual conventions.
The more specific you are, the less correction Claude will need.
