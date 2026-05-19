# Error Handling And Diagnostics Design

## Problem

The add-on is used inside a host application that users do not control like a
normal developer process. A realistic support flow is:

1. The user installs the add-on.
2. The user performs normal editor, settings, or Browser batch actions.
3. Something fails.
4. The user enables debug logging.
5. The user reproduces the failure.
6. The user sends logs to the developer.

The current logging is useful but incomplete for that workflow. The add-on has a
rotating file log, frontend log forwarding, settings diagnostics, broad
exception boundaries, and special RNNoise / pause-shortening incidents. The gaps
are structural:

- Some failures are converted into user-facing messages without preserving a
  stack trace in the log.
- The log often shows the final error but not the sequence of user actions and
  internal steps that led to it.
- Frontend JavaScript errors and unhandled rejections do not consistently carry
  stack traces into Python logs.
- Batch per-note failures can be summarized as row failures without a developer
  stack trace.
- Hard process crashes can terminate Anki before Python cleanup code runs.
- The support report has special incident sections but no general latest-error
  and recent-event view.

The target is not "never crash." The target is that every supportable failure
leaves enough evidence for a developer to reconstruct what happened.

## Supportability Goal

When debug logging is enabled and the user reproduces a problem, the support
report should include:

- Add-on version, Anki version, Python version, OS, and relevant tool health.
- The active operation, operation id, and boundary where the failure was caught.
- A full Python stack trace for any Python exception.
- A JavaScript stack trace for frontend errors where WebEngine provides one.
- A recent breadcrumb sequence showing user actions and internal phases before
  the failure.
- External tool invocations with argv, return code, stderr/stdout tail, launch
  error, and duration.
- The user-visible message that was shown in Anki.
- The log file paths and crash-forensics paths.

For true native crashes, OS kills, or immediate process aborts, Python cannot
guarantee a final log line. The design should still preserve the last flushed
breadcrumbs, faulthandler output when possible, Qt messages, and a dirty-session
marker detected on next startup.

## Principles

- Boundary functions catch and log. Internal pure helpers raise normally.
- No unexpected exception is converted into a silent failure.
- Every broad `except Exception` either calls the diagnostics boundary helper or
  has an explicit architecture allowlist reason.
- Breadcrumbs are structured events, not prose-only log messages.
- Debug mode expands breadcrumbs and persists them to disk. A small in-memory
  breadcrumb buffer can exist outside debug mode for same-session reports.
- Error logs flush immediately.
- Diagnostics must avoid raw note text and raw audio content. Note ids,
  filenames, field names, operation names, timing, command argv, and local paths
  are acceptable support data.

## Proposed Log Files

Keep the existing human-readable rotating log:

- `anki_audio_quick_editor.log`

Add crash and event files:

- `anki_audio_quick_editor_events.jsonl`
  - Debug-mode structured breadcrumb stream.
  - Rotated and size-capped.
  - Flushed after important events and every captured error.
- `anki_audio_quick_editor_crash.log`
  - Python `faulthandler` output.
  - Appended or rotated at startup.
  - Used for fatal signals and explicit traceback dumps.
- `anki_audio_quick_editor_session.json`
  - Stores session id, pid, start time, clean-exit flag, last event sequence,
    and last operation id.
  - Written dirty on startup, marked clean on normal shutdown when possible.
  - If the next startup sees an unclean previous session, log a warning and
    include it in the support report.

## Diagnostics Core

Introduce a small diagnostics layer with these responsibilities:

- Create one session id at startup.
- Create operation ids for user-facing operations.
- Store an in-memory breadcrumb ring.
- Persist debug-mode breadcrumbs to JSONL.
- Capture exceptions at boundaries with stack traces and breadcrumb snapshots.
- Record the latest general incident for the support report.
- Flush error logs and event logs immediately.

Recommended event shape:

```json
{
  "schema": 1,
  "session_id": "20260519T153000Z-abc123",
  "seq": 42,
  "timestamp": "2026-05-19T15:30:42.123456+00:00",
  "level": "info",
  "source": "editor",
  "operation": "editor.region_delete",
  "operation_id": "op-123",
  "boundary": "editor.worker.region_delete",
  "event": "region_delete.accepted",
  "context": {
    "field_index": 0,
    "source_filename": "clip.mp3",
    "selection_start_ms": 1220,
    "selection_end_ms": 1840
  }
}
```

Recommended captured incident shape:

```json
{
  "timestamp": "2026-05-19T15:30:43.010000+00:00",
  "session_id": "20260519T153000Z-abc123",
  "operation": "editor.region_delete",
  "operation_id": "op-123",
  "boundary": "editor.worker.region_delete",
  "exception_type": "AudioProcessingError",
  "message": "Could not render region-deleted audio.",
  "user_message": "Could not render region-deleted audio.",
  "context": {
    "field_index": 0,
    "source_filename": "clip.mp3"
  },
  "breadcrumbs": [
    {"seq": 39, "event": "editor.command.received"},
    {"seq": 40, "event": "region_delete.request.pop"},
    {"seq": 41, "event": "region_delete.accepted"}
  ]
}
```

The incident record should not replace the normal log. The normal log remains
the authoritative stack trace:

```text
2026-05-19 ... ERROR ... boundary failed: editor.worker.region_delete operation_id=op-123 context=...
Traceback (most recent call last):
  ...
```

## Debug-Mode Breadcrumbs

Debug mode should do more than raise the logger level.

When `debug_logging` is false:

- Keep a small in-memory ring, for example 100 recent events.
- Log important lifecycle events at `INFO`.
- Do not write every breadcrumb to disk.

When `debug_logging` is true:

- Increase the in-memory ring, for example 1000 or 2000 events.
- Write structured breadcrumbs to `anki_audio_quick_editor_events.jsonl`.
- Include command payload summaries, operation phases, worker starts/stops,
  frontend user actions, and external tool phases.
- Avoid raw note field contents and unbounded payloads.
- Flush the event file after high-value events: operation start, external
  command start/end, boundary failure, frontend error, support report creation.

Debug mode should be applied through one shared log-level function so both the
friendly package logger and numeric runtime package logger are updated.

## Error Boundaries

### Process Boundary

Install these during early startup:

- `sys.excepthook` for uncaught main-thread Python exceptions.
- `threading.excepthook` for uncaught background-thread exceptions.
- Python `faulthandler` writing to `anki_audio_quick_editor_crash.log`.
- Qt message handler for Qt and WebEngine warnings/errors, if safe with Anki's
  existing handlers.
- Dirty-session marker that is written before normal operation begins.

Expected behavior:

- Uncaught Python exceptions are logged with full stack traces.
- Background thread escapes are logged even if the thread did not use the normal
  worker boundary.
- Fatal native crashes get best-effort faulthandler output.
- The next startup reports if the previous session did not exit cleanly.

### Anki Hook Boundary

Every function registered with `gui_hooks` should be wrapped or implemented as a
boundary:

- `main_window_did_init`
- editor hook callbacks
- Browser menu/context callbacks
- any future Anki hook callback

Expected context:

- Hook name.
- Add-on version.
- Current profile / collection availability when safe.
- For editor hooks: note id, field index, and whether controls were injected.
- For Browser hooks: selection count and action name when available.

Startup hook failures should be loud. Non-critical UI hook failures can show a
controlled warning and continue only when the add-on can remain consistent.

### WebView Bridge Boundary

Every Python entrypoint reached through `pycmd` should be a boundary:

- Settings commands.
- Settings async commands.
- Editor bridge commands.
- Editor pending command payloads.
- Frontend log ingestion.

Expected context:

- Command name, not raw unbounded payload.
- Payload shape and safe summary.
- Field index and note id where available.
- Operation id.
- Recent frontend breadcrumbs.

### Background Worker Boundary

Every thread or Anki task body should use a worker boundary helper:

- Standard editor render worker.
- Special denoise worker.
- Region-delete worker.
- Prosody analysis worker.
- Playback-segment worker.
- Settings async worker.
- Browser batch worker.

Expected behavior:

- Log a full stack trace with operation id and worker name.
- Schedule the user-visible failure back onto the main thread.
- Reset busy/session state consistently.
- Preserve the note unchanged when the operation was supposed to be
  non-destructive.

### Operation Boundary

Each user-facing operation should create a scope:

- `editor.render`
- `editor.rnnoise`
- `editor.pause_shortening`
- `editor.region_delete`
- `editor.playback`
- `editor.graph_analysis`
- `browser.batch`
- `settings.health_check`
- `settings.support_report`
- `settings.show_log_file`

The scope owns the operation id and emits these breadcrumbs:

- `operation.started`
- important validation decisions
- external command phases
- worker scheduled
- worker finished
- main-thread update scheduled
- operation succeeded or failed

### Per-Item Batch Boundary

Browser batch work needs one boundary per note. One note failure should not kill
the batch, but it must log a stack trace.

Expected context:

- Batch operation id.
- Note id.
- Source field.
- Target field.
- Audio filename.
- Result status.
- Failure message.

Expected behavior:

- Continue to the next note after a per-note failure.
- Include a failure row in the dialog.
- Log the developer stack trace and per-note breadcrumbs.

### Frontend Boundary

The settings and editor WebViews should capture:

- `window.onerror`
- `window.onunhandledrejection`
- Svelte/event handler errors where practical
- frontend logger calls
- high-value user actions as breadcrumbs

Payloads sent to Python should include:

- level
- message
- stack, if available
- filename, line, column
- frontend scope, for example `settings` or `editor`
- operation id when the frontend knows it
- safe context

Svelte does not provide React-style component error boundaries. The practical
boundary is global error/rejection capture plus wrapping async/event handlers
that are known to be high-value.

### External Tool Boundary

Every `ffmpeg`, `ffprobe`, DeepFilterNet, and RNNoise invocation should record:

- argv
- executable path
- input and output paths
- duration
- return code
- stdout tail
- stderr tail
- launch error
- operation id
- pipeline stage

The pause-shortening pipeline already records much of this in artifacts. The
same structure should be visible through the general diagnostics layer so the
support report is consistent across operations.

## Support Report Changes

Add these sections to the support report:

```text
Latest captured error
  Timestamp:
  Session:
  Operation:
  Operation id:
  Boundary:
  Exception type:
  User-visible message:
  Context:

Recent event sequence
  Last N breadcrumbs, ordered by sequence number.

Crash forensics
  Previous session ended cleanly:
  Current session id:
  Crash log path:
  Event log path:
  Last dirty-session marker:
```

Keep the existing RNNoise and pause-shortening incident sections. They remain
useful specialized reports, but they should complement the general latest-error
section rather than being the only incident model.

## Test Strategy

The test goal is to prove that every meaningful failure level leaves a good log
and support report. Tests should use deterministic fault injection, not random
crashes.

### Diagnostics Unit Tests

Add focused tests for the diagnostics core:

- `test_breadcrumb_ring_keeps_recent_events_in_order`
  - Record more events than capacity.
  - Assert sequence numbers are monotonic and only the newest events remain.
- `test_debug_breadcrumbs_are_written_as_jsonl_and_flushed`
  - Enable debug diagnostics.
  - Record events.
  - Assert the JSONL file exists, parses, and contains operation ids.
- `test_exception_boundary_logs_stack_context_and_breadcrumbs`
  - Raise a controlled exception inside the boundary helper.
  - Assert the log contains the boundary name, operation id, exception type,
    traceback, and breadcrumb snapshot.
- `test_exception_boundary_records_latest_incident`
  - Raise a controlled exception.
  - Assert the latest incident contains safe context and user-visible message.
- `test_exception_boundary_survives_logging_context_errors`
  - Pass an unserializable context object.
  - Assert the boundary still logs a traceback and substitutes a safe fallback.
- `test_support_report_includes_latest_error_and_recent_events`
  - Build a report after a captured incident.
  - Assert the report contains latest-error fields and recent event sequence.
- `test_support_report_truncates_large_context_and_log_tail`
  - Record large stdout/stderr/context.
  - Assert the support report remains bounded and marks truncation.

### Bootstrap And Process Boundary Tests

Add tests for process-level safety:

- `test_setup_diagnostics_installs_sys_and_threading_excepthooks_idempotently`
  - Install diagnostics twice.
  - Assert hooks are installed once and existing handlers are preserved or
    chained according to the chosen policy.
- `test_sys_excepthook_logs_uncaught_exception`
  - Call the installed hook with a fake exception tuple.
  - Assert stack trace and boundary metadata are logged.
- `test_threading_excepthook_logs_uncaught_worker_exception`
  - Call the installed threading hook with a fake args object.
  - Assert thread name, exception type, and stack trace are logged.
- `test_dirty_previous_session_is_reported_on_startup`
  - Create a session marker with `clean_exit=false`.
  - Start diagnostics.
  - Assert a warning and support-report crash-forensics entry are produced.
- `test_clean_session_marker_is_not_reported_as_crash`
  - Create a marker with `clean_exit=true`.
  - Assert no dirty-session warning.
- `test_faulthandler_writes_crash_log_in_subprocess`
  - Start a short subprocess that enables diagnostics and calls `os.abort()`.
  - Assert the subprocess exits nonzero and the crash log contains fatal
    traceback evidence when the platform supports it.
  - Keep this test isolated from the main pytest process.

### Anki Hook Boundary Tests

Add tests around hook wrappers:

- `test_hook_boundary_logs_editor_hook_failure`
  - Wrap a fake editor hook that raises.
  - Assert hook name, note id/field context, stack trace, and breadcrumbs.
- `test_hook_boundary_logs_browser_hook_failure`
  - Wrap a fake Browser hook that raises.
  - Assert selection count/action context and stack trace.
- `test_startup_hook_failure_is_visible`
  - Simulate a startup hook failure.
  - Assert it logs at error level and follows the chosen loud-failure policy.

### Bridge Boundary Tests

Add tests for Python bridge entrypoints:

- `test_settings_bridge_failure_logs_command_and_stacktrace`
  - Fault-inject a settings command handler failure.
  - Assert the log includes command name, boundary, operation id, and traceback.
- `test_settings_async_failure_returns_ui_error_and_logs_stacktrace`
  - Raise from a settings async operation.
  - Assert `window.onAsyncDone(... success=false ...)` is sent and the log has a
    traceback.
- `test_editor_bridge_failure_logs_command_context_and_stacktrace`
  - Raise during editor command dispatch.
  - Assert busy state resets, UI error is shown, and the log has a traceback.
- `test_pending_editor_payload_failure_logs_payload_shape_not_raw_payload`
  - Fault-inject pending payload handling.
  - Assert safe payload summary appears and raw field text does not.
- `test_frontend_log_payload_with_stack_is_preserved`
  - Send a frontend error payload containing a JS stack.
  - Assert Python logs message, stack, scope, and context.

### Worker Boundary Tests

Add tests for every worker category:

- `test_render_worker_failure_logs_stacktrace_and_resets_busy`
- `test_special_transform_worker_failure_logs_stacktrace_and_support_hint`
- `test_region_delete_worker_failure_logs_request_context_and_stacktrace`
- `test_prosody_analysis_worker_failure_logs_stacktrace`
- `test_playback_segment_worker_failure_logs_stacktrace`
- `test_settings_async_worker_failure_logs_stacktrace`
- `test_browser_batch_worker_failure_logs_stacktrace`

Each test should assert:

- The user-visible failure still reaches the UI path.
- Busy/session state is reset.
- The log contains full traceback text.
- The log contains operation id and boundary name.
- Recent breadcrumbs include operation start and the failing phase.

### Batch Per-Item Tests

Batch tests should prove the developer gets stack traces without breaking batch
isolation:

- `test_batch_note_graph_failure_logs_stacktrace_and_continues`
  - Fault-inject one note's graph rendering.
  - Assert the batch processes the next note and logs the failed note stack.
- `test_batch_note_transform_failure_logs_stacktrace_and_continues`
  - Fault-inject one transform render.
  - Assert the failed row is present, the next note runs, and the log contains
    note id, operation, audio filename, and traceback.
- `test_batch_apply_result_failure_logs_stacktrace_with_target_field`
  - Fault-inject `col.update_note`.
  - Assert the row fails and the log includes target field and stack trace.

### Frontend Tests

Add Svelte / TypeScript tests for frontend capture:

- `logger includes Error.stack`
  - Call `logger.error("message", error)`.
  - Assert the `frontend_log` payload contains message and stack.
- `global error reporter sends filename line column and stack`
  - Dispatch an `ErrorEvent`.
  - Assert payload shape.
- `unhandled rejection reporter sends reason stack`
  - Dispatch an unhandled rejection with an `Error`.
  - Assert stack is sent.
- `editor action breadcrumbs precede command pycmd`
  - Trigger a representative editor action.
  - Assert breadcrumb payload is queued before command payload.
- `settings diagnostics breadcrumbs include async operation ids`
  - Start a health check/support report.
  - Assert frontend breadcrumbs include the async job id.

### External Tool Tests

Add focused tests for command diagnostics:

- `test_external_command_success_records_duration_and_returncode`
- `test_external_command_nonzero_records_stderr_tail`
- `test_external_command_launch_error_records_exception`
- `test_pause_pipeline_failure_records_general_incident_and_special_incident`
- `test_rnnoise_failure_records_general_incident_and_special_incident`

These should use fake executables or monkeypatched command runners for failure
paths, while keeping existing real-binary smoke coverage where available.

### E2E Fault-Injection Tests

Add deterministic e2e tests with a test-only fault injection switch. Fault
injection must be unavailable in normal release behavior unless an explicit test
environment flag is set.

Recommended flag:

```text
AQE_FAULT_INJECTION=1
```

Recommended e2e cases:

- `test_debug_log_captures_editor_bridge_crash`
  - Enable debug logging.
  - Trigger a test-only editor bridge failure.
  - Copy support report.
  - Assert report contains boundary, stack trace, and editor breadcrumbs.
- `test_debug_log_captures_editor_worker_crash`
  - Enable debug logging.
  - Trigger a test-only render worker failure.
  - Assert support report contains worker boundary, stack trace, and operation
    breadcrumb sequence.
- `test_debug_log_captures_frontend_crash`
  - Enable debug logging.
  - Trigger a test-only JS throw in the editor bundle.
  - Assert support report contains JS stack and frontend breadcrumbs.
- `test_debug_log_captures_settings_async_crash`
  - Enable debug logging.
  - Trigger a test-only health-check/support-report failure.
  - Assert settings UI receives a failure and the log has a stack trace.
- `test_debug_log_captures_browser_batch_note_crash`
  - Enable debug logging.
  - Trigger a test-only per-note batch failure.
  - Assert the batch completes with a failed row and support report contains the
    note-level stack trace.
- `test_previous_session_dirty_marker_survives_for_next_startup`
  - Start Anki with diagnostics.
  - Simulate an unclean stop through a controlled subprocess or marker fixture.
  - Start again.
  - Assert support report says the previous session ended uncleanly.

Hard native crashes should be tested outside the main Anki e2e process through
subprocess tests. Do not intentionally abort the primary pytest or Anki process.

## Architecture Enforcement

Extend architecture tests after implementation:

- Broad exception allowlist entries must state the boundary and must call the
  diagnostics capture helper unless explicitly classified as best-effort cleanup.
- New thread/task bodies must use the worker boundary helper.
- New `gui_hooks` registrations must use hook boundary wrappers.
- Frontend files must continue to use the shared logger/bridge rather than raw
  `console.error` or raw `pycmd`.
- Support report tests must fail if latest captured error or breadcrumbs are
  omitted.

## Implementation Phases

1. Build the diagnostics core, breadcrumb model, incident recording, and support
   report rendering.
2. Install process-level hooks, faulthandler, session marker, and crash log.
3. Migrate settings bridge, editor bridge, and existing worker boundaries.
4. Add per-item batch boundaries and external-command breadcrumb integration.
5. Expand frontend logger payloads and global frontend error/rejection capture.
6. Add e2e fault injection and the crash-support test matrix.
7. Tighten architecture rules so future code cannot bypass the boundary system.

## Acceptance Criteria

The design is complete when:

- `python3 scripts/dev.py check` passes.
- `python3 scripts/dev.py test-e2e` passes.
- Every allowed broad exception boundary either uses diagnostics capture or has
  a narrow documented best-effort reason.
- A debug-mode support report from each simulated failure level contains a
  boundary name, operation id, stack trace where technically possible, and a
  recent breadcrumb sequence.
- A controlled fatal-crash subprocess leaves crash-log or dirty-session evidence
  that appears in the next support report.
