---
description: "Run the analysis pipeline for a stock. Use to test the pipeline end-to-end or analyze a specific stock."
---

<!-- WHAT THIS IS: A slash command. Run it with /analyze in the Claude Code chat.
     HOW IT WORKS: Claude reads the ## Context section (! lines run as shell commands)
     then follows the ## Task instructions.
     HOW TO CUSTOMIZE: Edit the ## Task section. Add more ! context lines if needed. -->

## Context

!ls src/pipeline/ 2>/dev/null
!ls src/main.py 2>/dev/null

## Task

1. Check if the pipeline code exists in `src/pipeline/`. If not, tell the user to run `/scaffold-structure` first.
2. If `$ARGUMENTS` is provided, use it as the stock code (e.g., `/analyze 000001`). Otherwise, ask which stock to analyze.
3. Validate the stock code is a 6-digit string (zero-pad if needed).
4. Run `python -m src.pipeline --stock <code>` or the appropriate entry point.
5. Report the results: technical indicators, LLM interpretation, and recommendation.
6. If the pipeline fails, diagnose the error and suggest fixes.
