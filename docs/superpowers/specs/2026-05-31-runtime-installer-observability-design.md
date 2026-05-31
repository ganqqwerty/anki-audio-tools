# Runtime Installer Observability Design

Status: awaiting review
Date: 2026-05-31

## Context

Audio Quick Editor public releases are thin. They ship `bin/runtime_manifest.json` and download a platform runtime pack on first use or when the user runs Install/Repair Runtime from Diagnostics. The installer already performs important safety checks: archive SHA-256 verification, manifest-listed extraction, unsafe and unexpected zip member rejection, extracted file size checks, extracted file SHA-256 checks, executable bit application, atomic promotion, and runtime state persistence.

The current user experience is too opaque. Startup schedules a background install and Settings exposes a single Install/Repair Runtime action, but users mostly see coarse status text such as "downloading" or a final error. When installation fails, support reports do not clearly identify the failed step, operation instance, download source, runtime manifest, platform, or probe details. Users can dismiss transient messages and then hit confusing runtime-dependent failures elsewhere in the add-on.

## Goals

- Make runtime installation and repair observable through one dedicated detailed window.
- Use the same detailed installer for first-run startup install and Settings > Diagnostics > Install/Repair Runtime.
- Show a stable checklist of runtime installation steps with clear status, progress, and details.
- Let users dismiss the installer window without disabling the add-on.
- Warn users after dismissing an incomplete install that AQE may not work properly and that they should use Settings > Diagnostics > Install/Repair Runtime.
- Fail runtime-dependent AQE actions early with coded runtime repair guidance when the runtime is missing, invalid, or not ready.
- Log every runtime install failure with a stable error code, operation ID, failed step ID, manifest ID, platform, relevant paths, URL, and recent step history.
- Keep the existing runtime integrity guarantees and add observability around them.

## Non-Goals

- Do not disable the Anki add-on when the installer is dismissed.
- Do not globally hide AQE UI after dismissal.
- Do not block all Anki interaction with an undismissable modal.
- Do not replace Settings diagnostics or support reports; enrich them with runtime install context.
- Do not make file size checks the primary integrity mechanism. Checksums remain the authoritative integrity check.
- Do not add a dependency on a system package manager or runtime install outside the managed runtime directory.

## User-Facing Behavior

When runtime status is not ready during startup, AQE opens a dedicated Runtime Installation window automatically. The window starts or attaches to the active runtime install operation and shows the full checklist. If the runtime becomes ready, the window shows the completed checklist and a clear ready state.

When the user clicks Settings > Diagnostics > Install/Repair Runtime, AQE opens the same Runtime Installation window every time. If the runtime is already ready, the window runs a verification-only pass and shows the completed ready state. Forced reinstall is not part of the first implementation.

The installer window is dismissible. If the user closes it while installation is not complete, AQE shows a warning:

```text
Audio Quick Editor runtime installation was not completed. Audio Quick Editor may not work properly.
To fix this, open Settings > Diagnostics and click Install/Repair Runtime.
```

AQE remains loaded after dismissal. Runtime-dependent actions remain visible, but before they launch external tools or read managed runtime files they check runtime readiness. If runtime is not ready, they fail early with a coded runtime error that points to Settings > Diagnostics > Install/Repair Runtime. This avoids lower-level `ffmpeg`, `ffprobe`, file-not-found, permission, or subprocess errors when the real problem is an incomplete managed runtime.

## Installer Checklist

The window displays a fixed ordered checklist. Each step has a status: pending, running, passed, failed, or skipped. Steps may show details under the row, such as URL, path, size, hash, command, exit code, or stderr tail.

1. **Select runtime package**
   Detect platform, load the packaged manifest, show manifest ID, selected runtime pack name, and download URL.

2. **Check local state**
   Check whether the managed runtime is already ready and whether a previously downloaded archive can be reused.

3. **Preflight**
   Create/check runtime and download directories and confirm they are writable. Check available disk space with `shutil.disk_usage()` when a runtime pack size is known. Low disk space is a hard failure when available free space is lower than twice the pack size, because extraction needs room for the archive and temporary extracted files.

4. **Download**
   Download the runtime pack from the manifest URL into a `*.download` temp file. Show URL, downloaded bytes, total bytes when known, and percent progress.

5. **Verify downloaded archive**
   Check archive file size when the manifest provides a size, then verify archive SHA-256. The checksum is authoritative; size exists for faster diagnostics and progress.

6. **Check archive contents**
   Open the zip and validate member names before extraction: reject unsafe paths, unexpected files, and missing expected files.

7. **Unarchive**
   Extract only manifest-listed files into a temporary extracting directory.

8. **Verify extracted runtime files**
   For each manifest-listed file, verify existence, size when provided, and SHA-256. Include executables, shared libraries, and model files.

9. **Check executable permissions**
   Apply executable bits where the manifest marks files executable, then verify expected executable files have executable permission on platforms where that is applicable. On Windows, this step should be marked skipped or limited to existence/path checks.

10. **Promote runtime**
    Atomically move the verified temporary runtime into `user_files/runtime/<runtime_manifest_id>/` and write `user_files/runtime_state.json`.

11. **Dry-run tools**
    Run lightweight probes for expected executables where a safe diagnostic command exists. Record executable path, arguments, timeout, exit code, and stdout/stderr tail. This verifies that files are not only present but runnable on the current host.

12. **Cleanup**
    Remove temp download/extraction files and old runtime directories where safe. Cleanup failures should be logged and shown as warnings unless they make the runtime unusable.

13. **Ready**
    Confirm runtime lookup resolves required tools from the managed runtime and show the final runtime root.

## Progress And Data Model

The runtime installer should emit structured progress snapshots, not only percentage/message strings. The model should include:

- `operation_id`: stable identifier for one install/repair attempt.
- `phase`: high-level status compatible with current runtime status semantics.
- `manifest_id`.
- `platform`.
- `runtime_root`.
- `current_step_id`.
- `steps`: ordered step snapshots with ID, label, status, progress, message, and details.
- `source_url` and `archive_name` for the selected pack.
- `downloaded_bytes` and `expected_bytes` for download progress when available.
- `error_code`, `error_message`, and `error_details` when failed.
- `failed_step_id` when failed.

Step details should be JSON-safe and support report friendly. Sensitive data is not expected in runtime pack URLs or local runtime paths, but the same safe JSON filtering used by diagnostics should still be applied before logging.

The existing `RuntimeStatus` summary contract can remain for compact diagnostics state, but Install/Repair Runtime should open the detailed installer window and use the detailed progress/result model. `RuntimeStatus` should stay concise; the detailed installer contract carries operation and step details.

## Python Architecture

The current install orchestration lives in `runtime_install.py`, with archive helpers in `runtime_archive.py`, manifest helpers in `runtime_manifest.py`, lookup/readiness checks in `runtime_lookup.py`, and state payload helpers in `runtime_state.py`.

The implementation should introduce a small runtime install progress layer rather than pushing UI concerns into archive helpers:

- `runtime_install_progress.py`
  - Step IDs and labels.
  - Dataclasses/builders for operation snapshots.
  - Helpers to mark steps running/passed/failed/skipped and emit snapshots.

- `runtime_install.py`
  - Keeps orchestration.
  - Emits step snapshots before and after each install action.
  - Records operation breadcrumbs and coded failures.

- `runtime_archive.py`
  - Keeps archive-specific validation and extraction.
  - Returns validation detail summaries or accepts a narrow progress callback for archive contents/extracted file verification, without depending on UI modules.

- `runtime_probes.py` or equivalent
  - Owns safe dry-run commands and timeout handling for `ffmpeg`, `ffprobe`, `deep-filter`, `rnnoise-cli`, `dpdfnet`, `sherpa-spleeter`, and `silero-vad` where supported.
  - Returns structured probe results for logs and UI.

Startup and Settings should not run two independent installers. They should attach to the active install operation when one is already running, or start one when needed. This preserves a single operation ID and prevents concurrent writes to the same runtime directory.

## Installer Window

The detailed window should be an AnkiWebView-hosted Svelte dialog. The rest of Settings already uses Svelte and generated contracts, so this keeps the rich checklist testable with the existing frontend tooling and avoids hand-building complex Qt rows.

The UI should be utilitarian:

- Header with runtime state, manifest ID, platform, and operation ID.
- Checklist rows with fixed ordering and compact status indicators.
- Expandable details for URL, paths, hashes, byte counts, probe commands, and error details.
- Primary action when failed: "Open Settings" or "Install/Repair Runtime" depending on where the dialog is hosted.
- Secondary action: close.
- Copyable operation ID and failed step in the failure state.

The window should not rely on native HTML `title` tooltips. If Svelte tooltips are needed, use the existing `AqeTooltip`/`AqeTooltipProvider` pattern.

## Error Codes And Logging

Existing runtime install errors use `AQE-RUNTIME-003` for managed runtime asset failures. Keep `AQE-RUNTIME-003` for the early runtime-required guardrail, and add more precise install-time codes for the detailed installer:

- `AQE-RUNTIME-004`: runtime download failed.
- `AQE-RUNTIME-005`: runtime archive verification failed.
- `AQE-RUNTIME-006`: runtime extraction or extracted file verification failed.
- `AQE-RUNTIME-007`: runtime executable permission or dry-run probe failed.

Failure logs must include structured detail:

- `operation_id`.
- `step_id`.
- `manifest_id`.
- `platform`.
- `runtime_root`.
- `archive_name`.
- `source_url`.
- Relevant local path.
- Expected and actual size/hash where applicable.
- Exception type and message.
- Probe command, exit code, timeout, stdout tail, and stderr tail where applicable.

Every failure has both a user-visible code and a precise operation/step identifier.

Every step transition should record a breadcrumb. Failed steps should be warning/error breadcrumbs with `flush=True`. The latest failed runtime install operation should be included in support reports, not only the final `RuntimeStatus`.

## Runtime-Dependent Action Guardrail

Before any AQE action depends on managed runtime tools or files, it should check readiness through the existing runtime status/lookup layer. If runtime is missing or invalid, it should return a user-facing coded runtime error:

```text
AQE-RUNTIME-003: Audio Quick Editor runtime is not installed or not ready. Open Settings > Diagnostics and click Install/Repair Runtime.
```

This should apply to editor transformations, graph/prosody paths that need managed tools, Browser batch operations, reviewer editor actions that invoke processing, and Settings health checks that would otherwise run external tools. Actions that only open Settings, show logs, collect support reports, or display existing diagnostics should continue to work.

This guardrail does not hide UI and does not disable the add-on. It prevents misleading downstream failures.

## Testing

Unit tests should cover:

- Step order and state transitions for successful install.
- Reusing an already downloaded archive.
- Malformed or missing runtime manifest fails in the package-selection step with a coded error.
- Unsupported platform fails before download and shows platform details.
- Preflight rejects unwritable runtime/download directories.
- Preflight rejects low disk space when pack size is known and available free space is below the threshold.
- Download timeout, HTTP failure, and interrupted partial download failures include URL, bytes downloaded, operation ID, and failed step.
- Reused cached archives are revalidated and rejected when their checksum no longer matches the manifest.
- Archive checksum mismatch failure includes operation ID and failed step.
- Archive size mismatch details are logged when size is known.
- Corrupt/non-zip archive failures map to archive verification.
- Unsafe path, unexpected file, and missing file failures map to the archive contents step.
- Extracted file size/hash mismatch maps to extracted file verification.
- Extraction write failure leaves no promoted partial runtime and records temp paths.
- Permission check behavior on POSIX, chmod failure behavior, and skipped/limited behavior on Windows.
- Promotion failure, including an existing target directory that cannot be removed or replaced, leaves the prior ready runtime untouched when one existed.
- `runtime_state.json` write failure prevents the install from being reported as ready.
- Cleanup failure is surfaced as a warning when runtime is otherwise usable and as an error when it prevents readiness.
- Concurrent startup and Settings repair attempts attach to one active operation instead of racing writes.
- Dry-run probe success, timeout, non-zero exit, and executable-not-found handling.
- Dismissed incomplete installer returns/shows the warning message.
- Reopening the installer after dismissal attaches to the active operation or shows the latest failed operation.
- Runtime-dependent action guard returns a coded runtime repair error.
- Support report context includes latest failed runtime install operation details.

Svelte/frontend tests should cover:

- Installer window renders all fixed steps.
- Running, passed, failed, skipped, and warning/cleanup states render correctly.
- Download byte/progress details render without layout overflow.
- Failure state shows code, operation ID, failed step, and repair guidance.
- Settings Install/Repair Runtime opens the detailed installer flow.
- Closing the window during an active install shows the incomplete-install warning and does not mark the operation as successful.
- Reopening after a failure preserves the failed step details instead of showing only a generic runtime status.

E2E coverage should include:

- Startup with missing runtime opens the detailed installer window.
- Dismissing incomplete install shows the warning.
- Settings > Diagnostics > Install/Repair Runtime opens the same detailed installer.
- A forced failure, such as checksum mismatch in a test manifest, shows the failed step and coded message.
- A forced download or archive failure leaves no promoted partial runtime and the next repair attempt can retry.
- Invoking a runtime-dependent action after a dismissed or failed install shows the coded repair guidance instead of a subprocess/file error.
- After successful install, runtime-dependent editor or batch action no longer hits the guardrail.

Full completion for the feature requires `python3 scripts/dev.py check` and `python3 scripts/dev.py test-e2e` unless a commit explicitly documents that full check/e2e were not run.

## Documentation

Update:

- `ARCHITECTURE.md` managed runtime section to describe the detailed installer and structured step logging.
- `TESTING.md` runtime asset testing notes if new tests or e2e fixtures are added.
- Runtime error help page `docs/errors/AQE-RUNTIME-003/index.html` to mention the new installer window, operation ID, and what to include in bug reports.
- `WEBVIEW_AND_TEMPLATES.md` only if a new WebView bundle/dialog is added.

## Decisions

- Use an AnkiWebView-hosted Svelte dialog for the detailed installer.
- Settings > Diagnostics > Install/Repair Runtime opens the detailed installer every time. If runtime is already ready, it runs a verification-only pass and shows ready.
- Do not force reinstall in the first implementation.
- Add install-time runtime error codes `AQE-RUNTIME-004` through `AQE-RUNTIME-007`, while keeping `AQE-RUNTIME-003` for runtime-not-ready guardrails.
- Treat low disk space as a hard preflight failure when `shutil.disk_usage()` is available and free space is lower than twice the runtime pack size.
