---
name: test
description: Run the repository quality checks through scripts/dev.py, summarize failures, and assess coverage gaps. Use when the user asks to test changes, reproduce local CI, or confirm feature completeness.
metadata:
  short-description: Run repo QC and e2e checks
---

# Test

Use the repo task runner instead of calling tools like `pytest`, `ruff`, or `mypy` directly.

## Setup

- `python3 scripts/dev.py info` shows discovered paths and versions
- `python3 scripts/dev.py setup` performs one-time setup if needed

## Run Sequence

Run each step in order. If one step fails, note it and continue so the user gets the full picture.

1. `python3 scripts/dev.py config-schema`
2. `python3 scripts/dev.py test`
3. `python3 scripts/dev.py lint`
4. `python3 scripts/dev.py typecheck`
5. `python3 scripts/dev.py arch`
6. `python3 scripts/dev.py deadcode`
7. `python3 scripts/dev.py security`
8. `python3 scripts/dev.py deps`
9. `python3 scripts/dev.py complexity`
10. `python3 scripts/dev.py test-svelte`
11. `python3 scripts/dev.py coverage`
12. SonarQube if requested or already part of the workflow
13. `python3 scripts/dev.py test-e2e`

If `radon` prints nothing, complexity is effectively a pass.

## Coverage Review

After coverage runs, classify uncovered lines:

- **Needs tests**: pure logic, transformations, validators, parsers, error handling, and other unit-testable paths
- **Acceptable gaps**: thin Anki or Qt integration glue that inherently depends on the running app

## Feature Completion Rule

A feature is not complete until `python3 scripts/dev.py test-e2e` passes. If e2e is skipped, say that clearly and do not present the work as fully validated.

## Reporting

Report:

- pass/fail for each check
- specific failures with file and line references when available
- overall coverage and which gaps are actionable
- whether e2e passed, failed, or was skipped
