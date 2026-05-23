# Dev Check Parallelism Design

## Goal

Reduce `python3 scripts/dev.py check` wall-clock time without making the runner nondeterministic.

## Approved Approach

Keep `check` in three phases:

- Sequential preflight for steps that prepare shared generated artifacts or autofix files.
- Parallel middle phase for independent read-only validation and test steps.
- Sequential tail for the existing frontend validation flow that still rebuilds bundles and runs lint autofix.

## Phase Split

Preflight:

- `config-schema`
- `contracts-generate`
- `contracts-check`
- `build-ui`
- `lint`

Parallel core:

- `architecture-report`
- `file-lines`
- `typecheck`
- `security`
- `deadcode`
- `deps`
- `complexity`
- `qodana`
- `arch`
- `test-anki-api`
- `test`
- `coverage`

Tail:

- `test-svelte`

## Safety Constraints

- `--verbose` stays on the current sequential path so subprocess output remains readable.
- Concurrent pytest-based steps must not share the same pytest cache directory.
- `check` should continue running all phases and summarize failures at the end, matching the current non-fail-fast behavior.

## Testing

- Add dev-runner unit coverage for the phase split.
- Add dev-runner unit coverage for the parallel executor.
- Add pytest helper coverage for per-run cache-dir isolation.
