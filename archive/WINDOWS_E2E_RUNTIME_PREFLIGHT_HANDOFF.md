# Windows E2E Runtime Preflight Handoff

Date: 2026-06-05

## Goal

Catch as many platform-related bugs as possible while keeping macOS arm64 as a supported primary development target. The work focused on making dependency readiness explicit, sharing runtime installation logic between UI and developer workflows, and preventing tests from silently skipping, bypassing, or faking missing runtime dependencies.

## Difficulties Encountered

- Windows path rendering differs from POSIX path rendering. Many unit tests expected hard-coded `/bin/...` command strings even though production code returns `str(Path(...))`, which is `\bin\...` on Windows.
- Existing downloaded managed runtime state in the worktree could leak into ordinary unit tests. That made some tests accidentally pass or fail depending on local machine state instead of test setup.
- Some tests were using fake DeepFilter or DPDFNet executables in e2e paths. That hid platform packaging and executable-suffix issues that e2e should catch.
- Windows cannot create POSIX-only filenames, such as names containing literal newline, quote, or backslash characters. Tests for those semantics needed to isolate parser/header logic from the host filesystem.
- Windows does not expose POSIX executable bits in the same way as macOS/Linux. Release tests had to keep executable-bit assertions on POSIX while still verifying extraction and payloads everywhere.
- Captured subprocess output from ffmpeg could fail under the Windows locale when paths contained non-ASCII characters. Test helpers needed explicit UTF-8 replacement decoding, matching production subprocess handling.
- `scripts/dev.py arch` installed `lint-imports.exe` on Windows but looked only for `lint-imports`, so setup succeeded while the architecture check still failed.
- `scripts/release_smoke.py` could import already-loaded workspace modules instead of modules from the archive under test. That masked archive completeness issues.
- The umbrella `check` command includes Qodana, which is an external CLI. It correctly fails when `qodana` is not installed on PATH.

## Changes Made

- Added a shared headless runtime CLI bridge:
  - `scripts/dev_runtime.py`
  - `python scripts/dev.py runtime-install`
  - runtime readiness preflight through `require-ready`
- Kept `runtime_manager.ensure_runtime(...)` as the single install/verify/extract/promote core. The dialog remains a UI adapter and the developer command is a stdout/exit-code adapter.
- Added e2e preflight so `test-e2e` and `test-e2e-parallel` require:
  - managed runtime readiness
  - vendored wheel verification
  - no implicit e2e downloads
- Updated e2e dependency discovery:
  - `ffmpeg_config` resolves via runtime-aware add-on helpers
  - DPDFNet expectations use current platform runtime helpers
  - Windows executable suffixes and macOS arm64 paths are delegated to runtime platform helpers
- Removed fake e2e runtime executables and fake bundle replacement helpers from DeepFilter/DPDFNet workflows.
- Added tests that forbid `pytest.skip`, `pytest.importorskip`, and `pytest.mark.skipif` in `tests/` and `e2e/`.
- Added an `allow_managed_runtime` pytest marker for real-runtime smoke tests. Ordinary unit tests isolate managed runtime discovery; smoke tests intentionally use the downloaded managed runtime and fail clearly if it is missing.
- Fixed Windows platform assumptions in tests and helpers:
  - native `Path` string expectations
  - command assertions using structured `argv` where command display quoting differs
  - POSIX-only filename behavior separated from Windows filesystem limits
  - POSIX executable-bit assertions guarded to POSIX hosts
  - UTF-8 subprocess decoding for ffmpeg-generated fixtures
- Hardened release smoke testing so archive imports are isolated from already-loaded workspace modules.
- Fixed Windows import-linter lookup by resolving `lint-imports.exe`.
- Updated docs for first-time setup and runtime installation:
  - `python scripts/dev.py setup`
  - `python scripts/dev.py runtime-install`
  - `python scripts/dev.py test-e2e`

## Verification Performed

- `python scripts/dev.py setup` passed.
- `python scripts/dev.py runtime-install` passed.
- `python scripts/dev.py test` passed.
- `python scripts/dev.py lint` passed.
- `python scripts/dev.py typecheck` passed.
- `python scripts/dev.py test-svelte` passed.
- `python scripts/dev.py arch` passed.
- `python scripts/dev.py test-e2e` passed twice. The final run completed in 4m43s and included managed runtime and vendored wheel preflight.

## Remaining Work

- Install Qodana CLI on PATH before expecting `python scripts/dev.py check` to pass end to end. The command currently fails clearly with `qodana not found`.
- Consider adding a documented Windows add-on linking option if symlink creation remains unsupported for local Anki add-on setup.
- Keep platform e2e tests tied to real managed runtime artifacts. Avoid adding fake executables to e2e workflows unless the test is explicitly about error handling and cannot exercise a real dependency.
- Continue running full e2e on Windows and macOS arm64 after runtime metadata or platform helper changes.
