---
description: "Run the test suite with pytest and report results. Use after making code changes to verify nothing broke."
---

<!-- WHAT THIS IS: A slash command. Run it with /test in the Claude Code chat.
     HOW IT WORKS: Claude reads the ## Context section (! lines run as shell commands)
     then follows the ## Task instructions.
     HOW TO CUSTOMIZE: Edit the ## Task section. Add more ! context lines if needed. -->

## Context

!git diff --stat HEAD
!pytest --tb=short -q 2>&1 | head -50

## Task

1. Run the full pytest suite with `pytest --tb=short -q`
2. If tests fail, analyze the failure output and explain what went wrong
3. If all tests pass, report the count and confirm
4. If coverage is below 80%, flag which modules need more tests
5. Do NOT fix failing tests automatically — just report the findings
