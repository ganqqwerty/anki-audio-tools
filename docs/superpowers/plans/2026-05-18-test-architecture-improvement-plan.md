# Test Architecture Improvement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce repeated refactor-time test failures caused by scattered architecture metadata, file-name allowlists, and runner/config drift while preserving the useful behavior and boundary protection those tests provide.

**Architecture:** Make architecture metadata a first-class source of truth instead of a set of independent allowlists. Python module contracts should drive import-linter config, side-effect ownership, and broad-exception allowances; frontend architecture tests should read one explicit frontend contract manifest. Refactor tests should fail because behavior or documented boundaries changed, not because a responsibility moved to a new file and five registries were not updated yet.

**Tech Stack:** Python 3.13, pytest, import-linter, `scripts/dev.py`, TOML generation/checking, Vitest, TypeScript, ESLint, Git history analysis.

---

## Background

The max-file-lines refactor did two useful things:

1. Split genuinely oversized production modules and tests into smaller responsibility-focused modules.
2. Added stronger architecture and file-length guardrails so future oversized files are caught earlier.

The failure log at `docs/superpowers/plans/2026-05-18-max-file-lines-test-failure-log.md` and the branch history show a repeated problem: many failing tests were not behavior regressions. They were metadata synchronization failures. A typical module extraction required updates in several independent places:

- `tests/test_architecture/contracts.py` or the split `contract_*.py` files
- `pyproject.toml` import-linter `source_modules` and `forbidden_modules`
- `tests/test_architecture/test_rule21_broad_exception_allowlist.py`
- file-specific side-effect allowlists in architecture tests
- file-specific frontend architecture allowlists in `settings_ui/tests/frontend-architecture.test.ts`

That test shape is expensive during refactors. It also weakens signal quality: engineers learn to expect architecture failures as "metadata churn" even when some failures are real.

The same log also showed tests doing valuable work:

- Dropped `@dataclass` decorators were caught.
- Missing imports after extraction were caught.
- Monkeypatch compatibility routes were caught.
- Import-safety and side-effect boundaries caught real architecture mistakes.

The improvement should therefore keep the guardrails, but reduce duplicated metadata and make failures point at one authoritative contract.

## Evidence From Git History

Measured from `main` commit `390dcf8` to branch `codex/max-file-lines-refactor`:

- Test/e2e/frontend test files changed: 58 files, 8134 additions, 6709 deletions.
- Large test-file splits were expected and healthy:
  - `tests/test_audio_processor.py`: 1859 deletions
  - `tests/test_editor_integration.py`: 1138 deletions
  - `settings_ui/tests/editor-inline.integration.test.ts`: 944 deletions
  - `e2e/test_editor_processing_workflow.py`: 540 deletions
  - `e2e/test_editor_region_loop_workflow.py`: 661 deletions
- Architecture metadata files also changed repeatedly:
  - `pyproject.toml`
  - `tests/test_architecture/contracts.py`
  - `tests/test_architecture/contract_audio.py`
  - `tests/test_architecture/contract_core.py`
  - `tests/test_architecture/contract_editor.py`
  - `tests/test_architecture/contract_ui.py`
  - `tests/test_architecture/test_rule13_batch_operation_boundaries.py`
  - `tests/test_architecture/test_rule14_batch_adapter_and_persistence_boundaries.py`
  - `tests/test_architecture/test_rule19_shared_operation_contracts.py`
  - `tests/test_architecture/test_rule21_broad_exception_allowlist.py`
  - `settings_ui/tests/frontend-architecture.test.ts`

The useful split work and the avoidable metadata churn are different concerns. This plan addresses the metadata churn.

## Repeating Failure Patterns

### Pattern 1: Import-Linter Configuration Drift

Observed failures:

- `editor_session` added to `MODULE_CONTRACTS` but missing from `pyproject.toml`.
- `editor_processing` added to the import-safe source list even though its module contract classified it as a UI adapter.

Root cause:

`MODULE_CONTRACTS` and `pyproject.toml` both encode the same layer information. The check in `test_rule23_refactor_module_contracts.py` catches drift, but it still requires humans to manually update two sources.

Desired state:

`MODULE_CONTRACTS` is the source of truth. Import-linter config is generated from it or checked against a generated expected file with one repair command.

### Pattern 2: File-Name Side-Effect Allowlists

Observed failures:

- Persistence allowlists had to add `editor_processing.py` and `editor_region_delete.py`.
- Broad exception allowlists had to move entries from `editor_integration` to `editor_bridge`, `editor_processing`, `editor_region_delete`, `editor_playback`, and `editor_analysis`.
- Frontend DOM-query allowlists had to add `control-actions.ts` and `graph-actions.ts`.

Root cause:

The tests know about "which file may do X" through local constants in test files. Moving a responsibility requires updating the test file even if the module contract already says the new file owns that side effect.

Desired state:

Side-effect ownership is expressed next to the module contract. Rule tests derive their expected allowlists from contracts.

### Pattern 3: Responsibility Tests Bound To Old File Locations

Observed failures:

- Browser operation selector tests still inspected `browser_integration.py` after dialog ownership moved to `browser_dialog.py`.
- Shared operation tests needed explicit references to both `browser_dialog.py` and `browser_integration.py`.

Root cause:

Some tests assert "this string appears in this old file" instead of "the UI adapter responsible for operation selection is connected to the shared operation registry."

Desired state:

Tests should either:

- assert behavior through public functions/classes, or
- assert documented responsibility through a named module capability in the architecture contract.

### Pattern 4: Tooling Path Mismatch

Observed failures:

- `tests/test_dev_tasks_file_lines.py` imported a module successfully under pytest assumptions only after implementation existed.
- `python3 scripts/dev.py file-lines` initially failed because direct script execution did not put the repository root on `sys.path`.

Root cause:

The test covered import behavior but not the exact CLI entrypoint path.

Desired state:

Every dev-runner command with nontrivial path setup has a CLI-level test or smoke check that invokes `scripts/dev.py` the same way users and agents do.

### Pattern 5: Late Formatting Failure

Observed failure:

- `git diff --check` found trailing blank lines after test-file splits.

Root cause:

Whitespace validation was run late, outside the normal focused test cadence.

Desired state:

Add a lightweight diff hygiene command to the local pre-commit checklist and optionally to `scripts/dev.py` for dirty worktrees.

## Design Principles

- Keep behavior tests behavior-oriented. Do not replace unit/e2e tests with architecture metadata.
- Keep architecture tests strict, but make their metadata DRY.
- A new module should require one architectural declaration, not five scattered allowlist updates.
- The architecture declaration should explain the responsibility, not just silence a test.
- Generated or derived config should have a check command and a write command, following the existing contracts workflow.
- Refactor validation should run in layers: focused behavior tests, architecture fast lane, full check, e2e.

## Proposed Architecture

### Python Contracts Become The Source Of Truth

Extend `tests/test_architecture/contract_schema.py` so `ModuleContract` can express:

- layer
- allowed addon dependencies
- allowed side effects
- broad exception boundaries
- optional named capabilities for high-level responsibility checks

Keep the existing split files:

- `tests/test_architecture/contract_audio.py`
- `tests/test_architecture/contract_core.py`
- `tests/test_architecture/contract_editor.py`
- `tests/test_architecture/contract_ui.py`

Those files already have the right shape. The improvement is to move remaining local allowlists into this contract system.

### Import-Linter Config Is Derived

Create a generator/checker module under `scripts/dev_tasks/architecture_contracts.py`.

It should import `MODULE_CONTRACTS` and derive:

- `import-safe-no-upper-layers.source_modules`: all contracts where `layer == IMPORT_SAFE_CORE`
- `import-safe-no-upper-layers.forbidden_modules`: all non-import-safe modules except `__init__`
- `settings-backend-no-ui.source_modules`: all contracts where `layer == SETTINGS_BACKEND`
- `settings-backend-no-ui.forbidden_modules`: UI adapter and settings shell modules

Generate a committed config file at:

- `generated/importlinter.toml`

Then change `scripts/dev.py arch` to run:

```bash
lint-imports --config generated/importlinter.toml
```

The generated file is committed because import-linter needs a concrete config file. The source of truth is still `MODULE_CONTRACTS`; `python3 scripts/dev.py architecture-contracts-check` should fail if the committed generated file is stale, and `python3 scripts/dev.py architecture-contracts-generate` should rewrite it.

### Broad Exception Rules Are Contract-Driven

Move `BROAD_EXCEPTION_ALLOWLIST` entries into the relevant `ModuleContract`.

Current shape:

```python
BroadExceptionAllowance(
    "editor_playback",
    "start_playback_from_cursor._run",
    1,
    "Background playback-segment worker boundary reports failures on the main thread.",
)
```

Target shape:

```python
contract(
    "editor_playback",
    layer=Layer.UI_ADAPTER,
    allowed_side_effects=(SideEffect.THREAD_SPAWN, SideEffect.TEMP_FILESYSTEM_CLEANUP),
    allowed_broad_exceptions=(
        broad_exception(
            "start_playback_from_cursor._run",
            count=1,
            reason="Background playback-segment worker boundary reports failures on the main thread.",
        ),
    ),
)
```

`test_rule21_broad_exception_allowlist.py` should collect expected entries from `MODULE_CONTRACTS`, not from a separate file-local tuple.

### Persistence And Side-Effect Rules Use Module Contracts

`tests/test_architecture/inspection.py` already detects side effects and validates them against `allowed_side_effects`. Remove or reduce separate file-name allowlists such as `ALLOWED_PERSISTENCE_FILES`.

For rules that still need domain-specific checks, assert against contract fields:

- A module that writes media must have `SideEffect.MEDIA_WRITE`.
- A module that updates notes must have `SideEffect.NOTE_UPDATE`.
- A module that merges undo entries must have `SideEffect.UNDO_MERGE`.
- Import-safe core modules must not have any of those side effects.

### Frontend Architecture Gets A Contract Manifest

Create:

- `settings_ui/tests/frontend-architecture-contracts.ts`

It should define a typed manifest rather than several local allowlist constants:

```ts
export type FrontendCapability =
  | "pycmd"
  | "publicWindowContract"
  | "testWindowContract"
  | "domQuery"
  | "animationFrame"
  | "audioElement";

export interface FrontendModuleContract {
  relPath: string;
  lineLimit?: number;
  exportLimit?: number;
  capabilities?: FrontendCapability[];
  notes: string;
}

export const frontendModuleContracts: FrontendModuleContract[] = [
  {
    relPath: "src/editor-inline/control-actions.ts",
    capabilities: ["domQuery"],
    notes: "Owns editor control status, busy state, and button label DOM updates.",
  },
];
```

`settings_ui/tests/frontend-architecture.test.ts` should derive its allowlists from this manifest.

This does not remove manual judgment. It moves all frontend architecture exceptions to one typed manifest with notes.

### Add An Architecture Fast Lane

Create a command:

```bash
python3 scripts/dev.py architecture-fast
```

It should run:

- `python3 scripts/dev.py architecture-contracts-check`
- `python3 scripts/dev.py architecture-report`
- `python3 scripts/dev.py arch`
- `python3 scripts/dev.py test tests/test_architecture`
- `cd settings_ui && npm run test -- --run frontend-architecture`
- `python3 scripts/dev.py file-lines`
- `cd settings_ui && npm run lint:max-lines`

Use this after every module extraction before broad behavior tests. This directly addresses the repeated "focused behavior tests passed, full check later found metadata drift" pattern.

## Implementation Tasks

### Task 1: Add Contract Schema For Broad Exceptions And Capabilities

**Files:**

- Modify: `tests/test_architecture/contract_schema.py`
- Modify: `tests/test_architecture/contracts.py`
- Test: `tests/test_architecture/test_rule15_all_modules_have_contracts.py`
- Test: `tests/test_architecture/test_rule21_broad_exception_allowlist.py`

- [ ] Add broad exception contract primitives.

```python
@dataclass(frozen=True)
class BroadExceptionContract:
    """One approved broad exception boundary inside a module."""

    qualname: str
    count: int
    reason: str


def broad_exception(
    qualname: str,
    *,
    count: int,
    reason: str,
) -> BroadExceptionContract:
    if not reason.strip():
        raise ValueError("broad exception allowances require a reason")
    return BroadExceptionContract(qualname=qualname, count=count, reason=reason)
```

- [ ] Extend `ModuleContract`.

```python
@dataclass(frozen=True)
class ModuleContract:
    module: str
    layer: Layer
    allowed_addon_deps: frozenset[str]
    allowed_side_effects: frozenset[SideEffect]
    allowed_broad_exceptions: tuple[BroadExceptionContract, ...] = ()
    capabilities: frozenset[str] = frozenset()
    forbidden_import_prefixes: tuple[str, ...] = ()
    allow_module_level_anki_imports: bool = False
    allow_any_anki_imports: bool = False
    notes: str = ""
```

- [ ] Update `contract(...)` to accept `allowed_broad_exceptions` and `capabilities`.

- [ ] Add a focused schema test that a contract can carry a broad exception reason and capability.

Run:

```bash
python3 scripts/dev.py test tests/test_architecture/test_rule15_all_modules_have_contracts.py tests/test_architecture/test_rule21_broad_exception_allowlist.py
```

Expected:

- Initial failures until callers are updated.
- Final result passes after Task 2 moves allowlists into contracts.

### Task 2: Move Broad Exception Allowances Into Module Contracts

**Files:**

- Modify: `tests/test_architecture/contract_audio.py`
- Modify: `tests/test_architecture/contract_core.py`
- Modify: `tests/test_architecture/contract_editor.py`
- Modify: `tests/test_architecture/contract_ui.py`
- Modify: `tests/test_architecture/test_rule21_broad_exception_allowlist.py`

- [ ] Move each current `BroadExceptionAllowance` into the corresponding module's `contract(...)` call.

Example for `editor_playback`:

```python
"editor_playback": contract(
    "editor_playback",
    layer=Layer.UI_ADAPTER,
    allowed_addon_deps=("audio_state", "editor_session", "prosody_types"),
    allowed_side_effects=(
        SideEffect.TEMP_FILESYSTEM_CLEANUP,
        SideEffect.THREAD_SPAWN,
    ),
    allowed_broad_exceptions=(
        broad_exception(
            "stop_audio_playback",
            count=1,
            reason="Best-effort playback backend integration cannot assume a stable Anki audio API surface.",
        ),
        broad_exception(
            "toggle_native_pause_resume",
            count=1,
            reason="Best-effort playback backend integration reports pause/resume unavailability as a warning.",
        ),
        broad_exception(
            "start_playback_from_cursor._run",
            count=1,
            reason="Background playback-segment worker boundary reports failures on the main thread.",
        ),
    ),
)
```

- [ ] Replace the local tuple in `test_rule21_broad_exception_allowlist.py` with:

```python
def expected_broad_exception_allowances() -> Counter[tuple[str, str]]:
    return Counter(
        (module_name, allowance.qualname)
        for module_name, contract in MODULE_CONTRACTS.items()
        for allowance in contract.allowed_broad_exceptions
        for _ in range(allowance.count)
    )
```

- [ ] Keep a test that every broad exception reason is non-empty and at least 20 characters.

Run:

```bash
python3 scripts/dev.py test tests/test_architecture/test_rule21_broad_exception_allowlist.py
```

Expected:

- Broad exception detection still fails if a new `except Exception` appears without a documented contract entry.
- Moving a function between modules now requires updating the destination module contract, not a separate allowlist file.

### Task 3: Derive Import-Linter Config From Module Contracts

**Files:**

- Create: `scripts/dev_tasks/architecture_contracts.py`
- Create: `generated/importlinter.toml`
- Modify: `scripts/dev.py`
- Modify: `tests/test_architecture/test_rule23_refactor_module_contracts.py`
- Modify: `pyproject.toml`
- Test: `tests/test_architecture/test_rule23_refactor_module_contracts.py`

- [ ] Create `scripts/dev_tasks/architecture_contracts.py`.

Core functions:

```python
ADDON_PREFIX = "anki_audio_quick_editor"


def qualified(module_name: str) -> str:
    return f"{ADDON_PREFIX}.{module_name}"


def import_safe_source_modules(contracts: dict[str, ModuleContract]) -> list[str]:
    return sorted(
        qualified(name)
        for name, contract in contracts.items()
        if contract.layer == Layer.IMPORT_SAFE_CORE
    )


def upper_layer_forbidden_modules(contracts: dict[str, ModuleContract]) -> list[str]:
    return sorted(
        qualified(name)
        for name, contract in contracts.items()
        if contract.layer != Layer.IMPORT_SAFE_CORE and name != "__init__"
    )
```

- [ ] Render the import-linter TOML deterministically.

Required contracts:

```toml
[tool.importlinter]
root_packages = ["anki_audio_quick_editor"]
include_external_packages = true
exclude_type_checking_imports = true

[[tool.importlinter.contracts]]
name = "import-safe-no-upper-layers"
type = "forbidden"
source_modules = [...]
forbidden_modules = [...]

[[tool.importlinter.contracts]]
name = "settings-backend-no-ui"
type = "forbidden"
source_modules = [...]
forbidden_modules = [...]
```

- [ ] Add dev commands:

```bash
python3 scripts/dev.py architecture-contracts-generate
python3 scripts/dev.py architecture-contracts-check
```

- [ ] Change `python3 scripts/dev.py arch` to run:

```bash
lint-imports --config generated/importlinter.toml
```

- [ ] Remove the manually duplicated import-linter module lists from `pyproject.toml` after `dev.py arch` no longer depends on them.

- [ ] Keep `test_rule23_refactor_module_contracts.py` focused on generated config freshness:

```python
def test_generated_import_linter_config_matches_module_contracts() -> None:
    expected = render_import_linter_config(MODULE_CONTRACTS)
    actual = (PROJECT_ROOT / "generated" / "importlinter.toml").read_text()
    assert actual == expected
```

Run:

```bash
python3 scripts/dev.py architecture-contracts-check
python3 scripts/dev.py arch
python3 scripts/dev.py test tests/test_architecture/test_rule23_refactor_module_contracts.py
```

Expected:

- All pass.
- Adding a module contract and forgetting to regenerate gives a single precise stale-generated-config failure.

### Task 4: Replace File-Name Persistence Allowlists With Contract-Driven Side-Effect Tests

**Files:**

- Modify: `tests/test_architecture/test_rule14_batch_adapter_and_persistence_boundaries.py`
- Modify: `tests/test_architecture/inspection.py` only if a missing side-effect pattern is discovered
- Test: `tests/test_architecture/test_rule14_batch_adapter_and_persistence_boundaries.py`

- [ ] Remove `ALLOWED_PERSISTENCE_FILES`.

- [ ] Assert detected persistence side effects are allowed by module contracts.

Expected test shape:

```python
def test_direct_media_and_note_persistence_are_declared_by_module_contracts() -> None:
    observations = observe_all_modules()
    offenders = []
    for module_name, observation in observations.items():
        contract = MODULE_CONTRACTS[module_name]
        persistence_effects = {
            SideEffect.MEDIA_WRITE,
            SideEffect.NOTE_UPDATE,
            SideEffect.UNDO_MERGE,
        } & observation.side_effects
        undeclared = persistence_effects - contract.allowed_side_effects
        if undeclared:
            offenders.append(
                f"{module_name}: {', '.join(sorted(effect.value for effect in undeclared))}"
            )
    assert offenders == []
```

- [ ] Keep a separate assertion that import-safe modules do not declare persistence side effects.

Run:

```bash
python3 scripts/dev.py test tests/test_architecture/test_rule14_batch_adapter_and_persistence_boundaries.py
```

Expected:

- If a media write moves to a different UI adapter, only that module's contract needs updating.

### Task 5: Convert Browser Responsibility Checks To Capabilities

**Files:**

- Modify: `tests/test_architecture/contract_ui.py`
- Modify: `tests/test_architecture/test_rule13_batch_operation_boundaries.py`
- Modify: `tests/test_architecture/test_rule19_shared_operation_contracts.py`

- [ ] Add explicit capabilities to browser contracts.

Example:

```python
"browser_dialog": contract(
    "browser_dialog",
    layer=Layer.UI_ADAPTER,
    allowed_addon_deps=("audio_operations", "batch_operations", "browser_report"),
    capabilities=frozenset({"batch_operation_selector"}),
    notes="Owns Qt dialog operation selection and progress display.",
)
```

- [ ] Replace string-location assertions with capability assertions plus import checks.

Expected test shape:

```python
def test_one_browser_ui_adapter_owns_batch_operation_selection() -> None:
    owners = [
        name
        for name, contract in MODULE_CONTRACTS.items()
        if "batch_operation_selector" in contract.capabilities
    ]
    assert owners == ["browser_dialog"]
```

- [ ] Keep direct behavioral coverage in browser integration tests for operation labels, target-field requirements, and request creation.

Run:

```bash
python3 scripts/dev.py test tests/test_architecture/test_rule13_batch_operation_boundaries.py tests/test_architecture/test_rule19_shared_operation_contracts.py tests/test_browser_integration.py
```

Expected:

- Architecture tests describe ownership.
- Behavior tests prove the dialog still uses the shared registry.

### Task 6: Add Frontend Architecture Contract Manifest

**Files:**

- Create: `settings_ui/tests/frontend-architecture-contracts.ts`
- Modify: `settings_ui/tests/frontend-architecture.test.ts`
- Test: `settings_ui/tests/frontend-architecture.test.ts`

- [ ] Create the typed manifest.

```ts
export type FrontendCapability =
  | "pycmd"
  | "publicWindowContract"
  | "testWindowContract"
  | "domQuery"
  | "animationFrame"
  | "audioElement";

export interface FrontendModuleContract {
  relPath: string;
  lineLimit?: number;
  exportLimit?: number;
  capabilities?: FrontendCapability[];
  notes: string;
}
```

- [ ] Move current allowlists into manifest entries with notes.

Example:

```ts
export const frontendModuleContracts: FrontendModuleContract[] = [
  {
    relPath: "src/editor-inline/control-actions.ts",
    capabilities: ["domQuery"],
    notes: "Owns direct DOM updates for control busy state, statuses, and labels.",
  },
  {
    relPath: "src/editor-inline/playback-controller.ts",
    capabilities: ["animationFrame", "audioElement"],
    notes: "Owns HTMLAudioElement playback clock and animation-frame cursor updates.",
  },
];
```

- [ ] Derive `querySelectorAllowlist`, `requestAnimationFrameAllowlist`, `audioElementAllowlist`, and export/line limits from this manifest.

- [ ] Add a completeness check:

```ts
it("keeps frontend architecture contract entries unique and tied to existing files", () => {
  const paths = frontendModuleContracts.map((contract) => contract.relPath);
  expect(new Set(paths).size).toBe(paths.length);
  for (const relPath of paths) {
    expect(existsSync(join(projectRoot, relPath))).toBe(true);
  }
});
```

Run:

```bash
cd settings_ui && npm run test -- --run frontend-architecture
cd settings_ui && npm run lint
cd settings_ui && npm run typecheck
```

Expected:

- A new frontend module with DOM/audio/timer/window side effects fails with a contract-style message.
- Updating ownership requires one manifest entry, not scattered allowlist constants.

### Task 7: Add Architecture Fast Lane To The Dev Runner

**Files:**

- Modify: `scripts/dev.py`
- Modify: `scripts/dev_tasks/quality.py` or create `scripts/dev_tasks/architecture.py`
- Modify: `TESTING.md`
- Test: focused dev-runner tests if available

- [ ] Add command:

```bash
python3 scripts/dev.py architecture-fast
```

- [ ] The command should run:

```bash
python3 scripts/dev.py architecture-contracts-check
python3 scripts/dev.py architecture-report
python3 scripts/dev.py arch
python3 scripts/dev.py test tests/test_architecture
cd settings_ui && npm run test -- --run frontend-architecture
python3 scripts/dev.py file-lines
cd settings_ui && npm run lint:max-lines
```

- [ ] Make the output label clear:

```text
Step 1/7: architecture-contracts-check
Step 2/7: architecture-report
...
```

- [ ] Document the cadence in `TESTING.md`:

```markdown
After extracting or moving a module, run `python3 scripts/dev.py architecture-fast` before broad unit/e2e suites. This catches architecture metadata drift while the changed module boundary is still fresh.
```

Run:

```bash
python3 scripts/dev.py architecture-fast
```

Expected:

- Passes on the current branch.
- Runs much faster than full e2e.

### Task 8: Add CLI-Level Smoke Coverage For Dev Runner Commands

**Files:**

- Modify: `tests/test_dev_tasks_file_lines.py`
- Create: `tests/test_dev_runner_cli.py`
- Test: `tests/test_dev_runner_cli.py`

- [ ] Add a small helper for direct dev-runner invocations.

```python
def run_dev_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/dev.py", *args],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
```

- [ ] Add smoke tests for path-sensitive commands:

```python
def test_file_lines_command_runs_from_direct_script_entrypoint() -> None:
    result = run_dev_command("file-lines")
    assert result.returncode == 0
    assert "hand-maintained Python files" in result.stdout
```

- [ ] Add smoke coverage for the new architecture commands:

```python
def test_architecture_contracts_check_runs_from_direct_script_entrypoint() -> None:
    result = run_dev_command("architecture-contracts-check")
    assert result.returncode == 0
```

Run:

```bash
python3 scripts/dev.py test tests/test_dev_runner_cli.py tests/test_dev_tasks_file_lines.py
```

Expected:

- Direct CLI path behavior is covered, not just import behavior.

### Task 9: Add Dirty-Worktree Diff Hygiene Command

**Files:**

- Modify: `scripts/dev.py`
- Create or modify: `scripts/dev_tasks/git_checks.py`
- Modify: `TESTING.md`

- [ ] Add command:

```bash
python3 scripts/dev.py diff-check
```

- [ ] Implement it as:

```bash
git diff --check
git diff --cached --check
```

- [ ] Treat "no staged changes" and "no unstaged changes" as success.

- [ ] Add it to the documented local pre-commit checklist, but do not put it in CI-only clean-worktree flows unless the command gracefully handles no diff.

Run:

```bash
python3 scripts/dev.py diff-check
```

Expected:

- Passes on a clean or whitespace-clean worktree.
- Fails quickly on trailing whitespace or blank-line-at-EOF issues.

### Task 10: Update The Failure Log Process

**Files:**

- Modify: `docs/superpowers/plans/2026-05-18-max-file-lines-test-failure-log.md`
- Modify: `TESTING.md`

- [ ] Add a short "Failure Log Usage" section to `TESTING.md`.

Text:

```markdown
During large refactors, maintain a temporary failure log under `docs/superpowers/plans/`. Log failures that are not fixed as obvious typos in the same edit. Classify each as behavior regression, public contract break, architecture contract drift, brittle internal-detail dependency, fixture/tooling mismatch, generated artifact freshness, formatting fallout, or unclear.
```

- [ ] Add a rule to the current failure log:

```markdown
When a failure is classified as architecture contract drift, prefer moving the required metadata into the central contract source rather than adding another local allowlist.
```

Run:

```bash
python3 scripts/dev.py test tests/test_architecture
```

Expected:

- Documentation-only changes do not affect tests.

## Verification Strategy

Run verification in this order:

1. Contract schema and broad exception migration:

```bash
python3 scripts/dev.py test tests/test_architecture/test_rule21_broad_exception_allowlist.py tests/test_architecture/test_rule15_all_modules_have_contracts.py
```

2. Import-linter generation:

```bash
python3 scripts/dev.py architecture-contracts-generate
python3 scripts/dev.py architecture-contracts-check
python3 scripts/dev.py arch
```

3. Python architecture suite:

```bash
python3 scripts/dev.py test tests/test_architecture
```

4. Frontend architecture:

```bash
cd settings_ui && npm run test -- --run frontend-architecture
cd settings_ui && npm run lint
cd settings_ui && npm run typecheck
```

5. Fast lane:

```bash
python3 scripts/dev.py architecture-fast
```

6. Full non-e2e gate:

```bash
python3 scripts/dev.py check
```

7. E2E only if implementation touched runtime behavior or webview bundles:

```bash
python3 scripts/dev.py test-e2e
```

## Success Criteria

- Adding a new Python module requires one module contract entry and, if needed, one generated import-linter refresh.
- Moving a broad exception boundary requires updating the destination module contract, not a separate allowlist file.
- Moving media-write, note-update, undo, thread, subprocess, web-eval, or Anki-import ownership fails through `ModuleContract` validation, not file-name constants.
- Frontend DOM/audio/timer/window side-effect ownership is declared in one manifest.
- `python3 scripts/dev.py architecture-fast` catches architecture drift before the full check.
- The failure log for the next large refactor has fewer "architecture contract drift" entries and more failures that correspond to real behavior or public-contract risk.

## Non-Goals

- Do not weaken architecture constraints to make refactors easier.
- Do not remove e2e tests or replace behavior tests with contract tests.
- Do not make every test module register in a manifest; this plan targets architecture metadata, not all test organization.
- Do not make generated config invisible. Generated import-linter config should be committed and freshness-checked like generated communication contracts.
- Do not redesign the add-on runtime or frontend architecture as part of this cleanup.

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Generated import-linter config adds another generated artifact. | Treat it like communication contracts: deterministic write command, check command, committed output, clear docs. |
| Moving broad exception allowances into contracts makes contract files longer. | The allowances are architecture facts. Keeping them next to module side effects is clearer than hiding them in a separate rule file. |
| Frontend manifest becomes another allowlist. | Require `notes` for every capability and use typed capabilities, so entries explain responsibility rather than silence tests anonymously. |
| `architecture-fast` duplicates parts of `check`. | That is intentional; it is a fast refactor loop, not a replacement for `check`. |
| Developers bypass generated config commands and run `lint-imports` directly. | Update docs to prefer `python3 scripts/dev.py arch`; keep direct `lint-imports` use out of AGENTS/TESTING instructions. |

## Recommended Commit Breakdown

1. `Add architecture contract metadata primitives`
   - Broad exception and capability schema only.
2. `Move exception and persistence guardrails into contracts`
   - Rule 21 and Rule 14 updates.
3. `Generate import-linter config from module contracts`
   - Generator, generated config, dev commands, `arch` command change.
4. `Centralize frontend architecture ownership metadata`
   - Frontend manifest and test rewrite.
5. `Add architecture fast lane and CLI smoke tests`
   - Dev-runner commands and docs.

Each commit should pass:

```bash
python3 scripts/dev.py architecture-fast
```

The final commit should pass:

```bash
python3 scripts/dev.py check
```
