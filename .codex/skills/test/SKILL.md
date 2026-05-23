---
name: test
description: Run the repository quality checks through scripts/dev.py, summarize failures, and assess coverage gaps. Use when the user asks to test changes, reproduce local CI, or confirm feature completeness.
metadata:
  short-description: Run repo QC and e2e checks
---

# Test

Use the repo task runner instead of calling tools like `pytest`, `ruff`, or `mypy` directly.

`scripts/dev.py` is concise by default to keep agent transcripts small. If a check fails or you need live tool
output, rerun the specific command with `--verbose`, for example `python3 scripts/dev.py test --verbose`.

## Setup

- `python3 scripts/dev.py info` shows discovered paths and versions
- `python3 scripts/dev.py setup` performs one-time setup if needed

## Run Sequence

Run each step in order. If one step fails, note it and continue so the user gets the full picture.

1. `python3 scripts/dev.py config-schema`
2. `python3 scripts/dev.py test-anki-api`
3. `python3 scripts/dev.py test`
4. `python3 scripts/dev.py lint`
5. `python3 scripts/dev.py typecheck`
6. `python3 scripts/dev.py arch`
7. `python3 scripts/dev.py deadcode`
8. `python3 scripts/dev.py security`
9. `python3 scripts/dev.py deps`
10. `python3 scripts/dev.py complexity`
11. `python3 scripts/dev.py test-svelte`
12. `python3 scripts/dev.py coverage`
13. SonarQube if requested or already part of the workflow
14. `python3 scripts/dev.py test-e2e`

Run the default concise form first. Add `--verbose` only when the concise output is insufficient to diagnose a
failure.

`python3 scripts/dev.py complexity` fails on any hand-maintained add-on function or class at Radon rank C or worse; generated contract output is ignored by that fail decision.
`python3 scripts/dev.py coverage` uses branch coverage and fails below the configured threshold.
`python3 scripts/dev.py test-svelte` runs the full frontend validation chain, including Vitest coverage thresholds.

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
