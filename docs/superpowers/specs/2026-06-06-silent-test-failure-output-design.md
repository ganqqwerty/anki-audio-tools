# Silent Test Failure Output Design

## Goal

Make non-verbose test runs effectively silent when they pass, while still showing enough inline detail on failure that rerunning with `--verbose` is unnecessary.

## Scope

This design applies to test-oriented flows in `scripts/dev.py`:

- `test`
- `test-anki-api`
- `test-e2e`
- `test-e2e-parallel`
- `test-svelte`
- `coverage`
- test-backed steps reached through `check`: `test`, `test-anki-api`, `test-svelte`, and `coverage`

Non-test QC commands such as lint, complexity, and architecture checks keep their existing concise success output.

## Locked Behavior

### Success path

- In non-verbose mode, top-level test commands do not print a selected-command banner just to announce that they started.
- In non-verbose mode, passing test flows print nothing from the test subprocesses they run.
- This includes nested preparation commands that exist only to support a test flow, such as contract generation for `test`, bundle builds for `test-svelte`, and runtime/build preflights for `test-e2e`.
- `test-e2e-parallel` also stays quiet on success: no shard plan, no shard completion lines, no rerun hints.
- Verbose mode keeps the current live streamed behavior.

### Failure path

- When a test subprocess fails in non-verbose mode, the runner prints one clear label for the failing command or shard and then replays that subprocess's full captured output inline.
- Passing sibling subprocesses remain silent even if a later subprocess fails.
- The runner does not try to grep or synthesize a smaller error summary. It replays the real tool output.
- For pytest-based commands, the existing quiet pytest flags remain the primary filter so the replay naturally focuses on failed tests and their captured output instead of passing-test noise.

## Design

### 1. Add a shared quiet-success execution mode

The process helpers gain an explicit non-verbose mode for test flows:

- suppress start banners in quiet mode unless a failure occurs
- suppress success status lines in quiet mode
- keep buffering stdout/stderr so failure output can be replayed without rerunning

This mode must be scoped, not hardcoded per subprocess call, so nested helpers inherit the same behavior automatically.

### 2. Enter that mode at the command boundary

Top-level test commands should activate the quiet-success mode before calling their existing helpers. That lets the command stay silent even when it invokes shared setup commands that still behave normally elsewhere.

Examples:

- `cmd_test()` should keep contract generation silent on success
- `cmd_test_svelte()` should keep build and lint-fix silent on success
- `cmd_test_e2e()` should keep runtime preflight and UI build silent on success

### 3. Apply the same mode selectively inside `check`

`check` should preserve concise pass output for non-test steps while wrapping only test-backed steps in the quiet-success mode.

That means:

- lint, complexity, deps, and similar checks keep their current summaries
- `test`, `test-anki-api`, `test-svelte`, and `coverage` stay silent on success
- if one of those steps fails, its full captured failure output appears inline without affecting the logging style of unrelated passing steps

### 4. Keep pytest responsible for failed-test focus

The current pytest quiet arguments already do most of the filtering work:

- `-q`
- `--tb=short`
- `--show-capture=all`
- `-rfE`

That combination should stay in place. The runner's job is to replay the failing subprocess output, not to post-process individual tests out of it.

### 5. Extend parallel e2e failure reporting the same way

`test-e2e-parallel` should use the same quiet-success mode for:

- collection
- shard execution
- shard-level summary output

On success, the command stays quiet. On failure, only the failing shard output is replayed inline, along with a short label identifying the shard. Rerun commands can remain as extra context after the failure output, but they must not replace the inline details.

## Non-Goals

- No grep-based parsing of Svelte, pytest, or e2e output
- No change to verbose mode
- No broader logging redesign for non-test commands
- No attempt to collapse failure output to only a tail section or guessed error block

## Testing

- Add process-runner tests for quiet-success mode suppressing start and success lines while still replaying full failure output.
- Add command-level tests that confirm top-level test commands keep nested prep steps silent on success.
- Add `check` runner tests proving test-backed steps stay silent on pass while non-test steps still report concise success.
- Extend parallel e2e runner tests to verify success silence and inline failed-shard output behavior.
