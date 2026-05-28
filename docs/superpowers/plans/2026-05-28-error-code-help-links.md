# Error Code Help Links Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add stable `AQE-*` error codes and directly visible GitHub Pages help links to known user-facing Python and Svelte errors.

**Architecture:** Add a small backend error catalog and a shared frontend error renderer. Extend existing contracts with an optional structured `user_error` payload while preserving current string fields during migration. Update settings, batch, and editor display paths to render `CODE: message Help` without embedding HTML in localized messages.

**Tech Stack:** Python 3.13, generated JSON contracts, Svelte 5, TypeScript, Vitest, pytest, static GitHub Pages docs under `docs/`.

---

## File Structure

- Create `addon/anki_audio_quick_editor/error_codes.py`: backend code constants and `UserFacingError` payload helpers.
- Modify `contracts/communication.schema.json`: add `UserFacingError` and optional `user_error` fields for settings, async, and batch failure payloads.
- Regenerate ignored contract outputs with `python3 scripts/dev.py contracts-generate`.
- Modify `addon/anki_audio_quick_editor/settings/commands.py`: send coded save errors.
- Modify `addon/anki_audio_quick_editor/settings/async_commands.py`: send coded async failure payloads.
- Modify `addon/anki_audio_quick_editor/browser_dialog_state.py`: allow coded batch error payloads.
- Modify `addon/anki_audio_quick_editor/browser_dialog.py`: send `AQE-BATCH-001` for invalid batch request.
- Modify `addon/anki_audio_quick_editor/editor_frontend.py`: allow structured status payloads.
- Modify editor failure sources in `editor_processing.py`, `editor_playback.py`, `editor_analysis.py`, and `editor_recording.py`: map common errors to coded payloads.
- Create `settings_ui/src/lib/user-facing-error.ts`: frontend type guards and construction helpers.
- Create `settings_ui/src/lib/error-links.ts`: deterministic GitHub Pages help URL helper.
- Create `settings_ui/src/lib/ErrorMessage.svelte`: shared visible error renderer.
- Modify `settings_ui/src/lib/async-jobs.ts`: reject with coded frontend errors when payload validation fails.
- Modify `settings_ui/src/settings/SettingsApp.svelte`, `GeneralSettingsPanel.svelte`, and `DiagnosticsPanel.svelte`: store/render `UserFacingError | string`.
- Modify `settings_ui/src/batch/BatchApp.svelte`: render coded batch errors.
- Modify `settings_ui/src/editor-inline/control-actions.ts`, `graph-actions.ts`, and `globals.d.ts`: render structured editor status payloads with links.
- Create docs pages under `docs/errors/` for the initial code set.
- Add/modify tests:
  - `tests/test_error_codes.py`
  - `tests/test_settings_commands_save.py`
  - `tests/test_settings_commands_diagnostics.py`
  - `tests/test_browser_dialog_state.py`
  - `tests/test_editor_frontend.py`
  - `settings_ui/tests/user-facing-error.test.ts`
  - `settings_ui/tests/error-message.test.ts`
  - `settings_ui/tests/async-jobs.test.ts`
  - `settings_ui/tests/app.test.ts`
  - `settings_ui/tests/batch-app.test.ts`
  - `settings_ui/tests/editor-inline.actions.test.ts`
  - `settings_ui/tests/product-links.test.ts`

---

### Task 1: Contracts And Backend Error Catalog

**Files:**
- Modify: `contracts/communication.schema.json`
- Create: `addon/anki_audio_quick_editor/error_codes.py`
- Test: `tests/test_error_codes.py`
- Test: `tests/test_settings_commands_save.py`
- Test: `tests/test_browser_dialog_state.py`

- [ ] **Step 1: Write failing backend catalog tests**

Create `tests/test_error_codes.py`:

```python
from __future__ import annotations

from anki_audio_quick_editor.error_codes import (
    AQE_BATCH_INVALID_REQUEST,
    AQE_RUNTIME_FFMPEG_MISSING,
    UserFacingError,
    coded_error,
    public_help_url,
)


def test_coded_error_payload_contains_code_message_and_details() -> None:
    payload = coded_error(
        AQE_RUNTIME_FFMPEG_MISSING,
        "Audio Quick Editor requires ffmpeg.",
        details="configured path did not exist",
    )

    assert payload == {
        "code": "AQE-RUNTIME-001",
        "message": "Audio Quick Editor requires ffmpeg.",
        "details": "configured path did not exist",
    }


def test_public_help_url_is_deterministic() -> None:
    assert public_help_url(AQE_BATCH_INVALID_REQUEST) == (
        "https://ganqqwerty.github.io/anki-audio-tools/errors/AQE-BATCH-001/"
    )


def test_user_facing_error_omits_empty_details() -> None:
    payload = UserFacingError("AQE-MEDIA-001", "No audio.").to_dict()

    assert payload == {"code": "AQE-MEDIA-001", "message": "No audio."}
```

Update `tests/test_settings_commands_save.py::test_settings_save_reports_invalid_payload` expected payload:

```python
    assert payload == {
        "error": "Invalid settings payload",
        "user_error": {
            "code": "AQE-SETTINGS-001",
            "message": "Invalid settings payload",
        },
    }
```

Update `tests/test_browser_dialog_state.py::test_progress_and_finish_payloads_match_frontend_contract` expected error payload:

```python
    assert batch_error_payload(
        "Choose a source field.",
        recoverable=True,
        user_error={
            "code": "AQE-BATCH-001",
            "message": "Choose a source field.",
        },
    ) == {
        "message": "Choose a source field.",
        "recoverable": True,
        "user_error": {
            "code": "AQE-BATCH-001",
            "message": "Choose a source field.",
        },
    }
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 scripts/dev.py test tests/test_error_codes.py tests/test_settings_commands_save.py tests/test_browser_dialog_state.py
```

Expected: fail because `error_codes.py` does not exist and payloads do not include `user_error`.

- [ ] **Step 3: Extend the communication schema**

In `contracts/communication.schema.json`, add this definition before `BatchErrorPayload`:

```json
    "UserFacingError": {
      "type": "object",
      "additionalProperties": false,
      "required": ["code", "message"],
      "properties": {
        "code": { "type": "string" },
        "message": { "type": "string" },
        "details": { "type": "string" }
      }
    },
```

Add optional `user_error` to `BatchErrorPayload`:

```json
        "message": { "type": "string" },
        "recoverable": { "type": "boolean" },
        "user_error": { "$ref": "#/definitions/UserFacingError" }
```

Add optional `user_error` to `AsyncFailurePayload`:

```json
        "id": { "type": "string" },
        "ok": { "enum": [false] },
        "error": { "type": "string" },
        "user_error": { "$ref": "#/definitions/UserFacingError" }
```

Add optional `user_error` to `SaveErrorPayload`:

```json
        "error": { "type": "string" },
        "user_error": { "$ref": "#/definitions/UserFacingError" }
```

- [ ] **Step 4: Add the backend catalog**

Create `addon/anki_audio_quick_editor/error_codes.py`:

```python
"""Stable user-facing error codes and help-link payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

GITHUB_PAGES_BASE_URL = "https://ganqqwerty.github.io/anki-audio-tools/"

AQE_MEDIA_CURRENT_FIELD_AUDIO_MISSING = "AQE-MEDIA-001"
AQE_MEDIA_REFERENCED_AUDIO_MISSING = "AQE-MEDIA-002"
AQE_RUNTIME_FFMPEG_MISSING = "AQE-RUNTIME-001"
AQE_RUNTIME_FFPROBE_MISSING = "AQE-RUNTIME-002"
AQE_RUNTIME_ASSET_MISSING = "AQE-RUNTIME-003"
AQE_AUDIO_PROCESSING_FAILED = "AQE-AUDIO-001"
AQE_PLAYBACK_PREPARE_FAILED = "AQE-PLAYBACK-001"
AQE_GRAPH_ANALYSIS_FAILED = "AQE-GRAPH-001"
AQE_RECORDING_FAILED = "AQE-RECORDING-001"
AQE_BATCH_INVALID_REQUEST = "AQE-BATCH-001"
AQE_SETTINGS_INVALID_PAYLOAD = "AQE-SETTINGS-001"
AQE_FRONTEND_INVALID_ASYNC_RESULT = "AQE-FRONTEND-001"
AQE_FRONTEND_UNKNOWN_ASYNC_ERROR = "AQE-FRONTEND-002"
AQE_FRONTEND_UNEXPECTED = "AQE-FRONTEND-999"


@dataclass(frozen=True)
class UserFacingError:
    """Structured error data safe to display directly to users."""

    code: str
    message: str
    details: str = ""

    def to_dict(self) -> dict[str, str]:
        payload = {"code": self.code, "message": self.message}
        if self.details:
            payload["details"] = self.details
        return payload


def public_help_url(code: str) -> str:
    """Return the public GitHub Pages help URL for an error code."""
    return f"{GITHUB_PAGES_BASE_URL}errors/{code}/"


def coded_error(code: str, message: str, *, details: str = "") -> dict[str, str]:
    """Return a JSON-serializable user-facing error payload."""
    return UserFacingError(code, message, details=details).to_dict()


def coded_error_from_message(code: str, message: Any, *, details: str = "") -> dict[str, str]:
    """Return a coded error after normalizing a non-string message."""
    return coded_error(code, str(message), details=details)
```

- [ ] **Step 5: Regenerate contracts**

Run:

```bash
python3 scripts/dev.py contracts-generate
```

Expected: exits `0` and regenerates ignored Python/TypeScript contract files.

- [ ] **Step 6: Update Python payload producers**

In `addon/anki_audio_quick_editor/settings/commands.py`, import:

```python
from ..error_codes import AQE_SETTINGS_INVALID_PAYLOAD, coded_error
```

Replace invalid save payload creation with:

```python
        payload = json.dumps(
            {
                "error": "Invalid settings payload",
                "user_error": coded_error(AQE_SETTINGS_INVALID_PAYLOAD, "Invalid settings payload"),
            }
        )
```

In `addon/anki_audio_quick_editor/browser_dialog_state.py`, import a type only if needed and change `batch_error_payload` to:

```python
def batch_error_payload(
    message: str,
    *,
    recoverable: bool = False,
    user_error: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Return the typed error payload sent to Svelte."""
    payload: dict[str, Any] = {
        "message": message,
        "recoverable": recoverable,
    }
    if user_error is not None:
        payload["user_error"] = user_error
    return payload
```

- [ ] **Step 7: Run focused tests**

Run:

```bash
python3 scripts/dev.py test tests/test_error_codes.py tests/test_settings_commands_save.py tests/test_browser_dialog_state.py
python3 scripts/dev.py contracts-check
```

Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add contracts/communication.schema.json addon/anki_audio_quick_editor/error_codes.py tests/test_error_codes.py tests/test_settings_commands_save.py tests/test_browser_dialog_state.py
git commit -m "feat: add user-facing error catalog"
```

---

### Task 2: Frontend Error Helpers And Renderer

**Files:**
- Create: `settings_ui/src/lib/error-links.ts`
- Create: `settings_ui/src/lib/user-facing-error.ts`
- Create: `settings_ui/src/lib/ErrorMessage.svelte`
- Test: `settings_ui/tests/user-facing-error.test.ts`
- Test: `settings_ui/tests/error-message.test.ts`
- Modify: `settings_ui/tests/product-links.test.ts`

- [ ] **Step 1: Write failing frontend helper tests**

Create `settings_ui/tests/user-facing-error.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import {
  frontendUserError,
  isUserFacingError,
  messageFromUnknownError,
} from "../src/lib/user-facing-error.js";

describe("user-facing errors", () => {
  it("recognizes structured coded errors", () => {
    expect(isUserFacingError({ code: "AQE-RUNTIME-001", message: "Missing ffmpeg" })).toBe(true);
    expect(isUserFacingError({ code: "AQE-RUNTIME-001" })).toBe(false);
    expect(isUserFacingError("Missing ffmpeg")).toBe(false);
  });

  it("creates frontend-owned coded errors", () => {
    expect(frontendUserError("AQE-FRONTEND-002", "Unknown async error")).toEqual({
      code: "AQE-FRONTEND-002",
      message: "Unknown async error",
    });
  });

  it("keeps message text from structured and native errors", () => {
    expect(messageFromUnknownError({ code: "AQE-BATCH-001", message: "Invalid batch" })).toBe("Invalid batch");
    expect(messageFromUnknownError(new Error("Native failure"))).toBe("Native failure");
    expect(messageFromUnknownError("string failure")).toBe("string failure");
  });
});
```

Create `settings_ui/tests/error-message.test.ts`:

```ts
import { render, screen } from "@testing-library/svelte";
import { describe, expect, it } from "vitest";

import ErrorMessage from "../src/lib/ErrorMessage.svelte";
import { errorHelpUrl } from "../src/lib/error-links.js";

describe("ErrorMessage", () => {
  it("renders plain string errors without help links", () => {
    render(ErrorMessage, { props: { error: "Plain failure" } });

    expect(screen.getByText("Plain failure")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Help" })).not.toBeInTheDocument();
  });

  it("renders coded errors with visible help link", () => {
    render(ErrorMessage, {
      props: {
        error: {
          code: "AQE-RUNTIME-001",
          message: "Audio Quick Editor requires ffmpeg.",
        },
      },
    });

    expect(screen.getByText(/AQE-RUNTIME-001:/)).toBeInTheDocument();
    expect(screen.getByText(/Audio Quick Editor requires ffmpeg/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Help" })).toHaveAttribute(
      "href",
      errorHelpUrl("AQE-RUNTIME-001"),
    );
  });
});
```

Add to `settings_ui/tests/product-links.test.ts`:

```ts
  it("builds first-party error help links", async () => {
    const { errorHelpUrl } = await import("../src/lib/error-links.js");
    const url = new URL(errorHelpUrl("AQE-RUNTIME-001"));

    expect(url.origin).toBe(FIRST_PARTY_ORIGIN);
    expect(url.pathname).toBe("/anki-audio-tools/errors/AQE-RUNTIME-001/");
  });
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd settings_ui && npm test -- user-facing-error.test.ts error-message.test.ts product-links.test.ts
```

Expected: fail because the new helper files do not exist.

- [ ] **Step 3: Add frontend helpers**

Create `settings_ui/src/lib/error-links.ts`:

```ts
import { PRODUCT_LINKS } from "./product-links.js";

export function errorHelpUrl(code: string): string {
  return `${PRODUCT_LINKS.githubPages}errors/${encodeURIComponent(code)}/`;
}
```

Create `settings_ui/src/lib/user-facing-error.ts`:

```ts
export interface UserFacingError {
  code: string;
  message: string;
  details?: string;
}

export type ErrorDisplayValue = string | UserFacingError;

export const AQE_FRONTEND_INVALID_ASYNC_RESULT = "AQE-FRONTEND-001";
export const AQE_FRONTEND_UNKNOWN_ASYNC_ERROR = "AQE-FRONTEND-002";
export const AQE_FRONTEND_UNEXPECTED = "AQE-FRONTEND-999";

export function isUserFacingError(value: unknown): value is UserFacingError {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value) &&
    typeof (value as { code?: unknown }).code === "string" &&
    typeof (value as { message?: unknown }).message === "string"
  );
}

export function frontendUserError(code: string, message: string, details?: string): UserFacingError {
  return details ? { code, message, details } : { code, message };
}

export function messageFromUnknownError(error: unknown): string {
  if (isUserFacingError(error)) return error.message;
  if (error instanceof Error) return error.message;
  return String(error);
}
```

Create `settings_ui/src/lib/ErrorMessage.svelte`:

```svelte
<script lang="ts">
  import { errorHelpUrl } from "./error-links.js";
  import { isUserFacingError, type ErrorDisplayValue } from "./user-facing-error.js";

  let {
    error,
    className = "",
    testId = undefined,
  }: {
    error: ErrorDisplayValue;
    className?: string;
    testId?: string;
  } = $props();

  const coded = $derived(isUserFacingError(error) ? error : null);
</script>

<span class={className} data-testid={testId}>
  {#if coded}
    <span class="error-code">{coded.code}:</span>
    {" "}{coded.message}
    <a class="error-help-link" href={errorHelpUrl(coded.code)} target="_blank" rel="noopener noreferrer">Help</a>
  {:else}
    {error}
  {/if}
</span>
```

- [ ] **Step 4: Run tests**

Run:

```bash
cd settings_ui && npm test -- user-facing-error.test.ts error-message.test.ts product-links.test.ts
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add settings_ui/src/lib/error-links.ts settings_ui/src/lib/user-facing-error.ts settings_ui/src/lib/ErrorMessage.svelte settings_ui/tests/user-facing-error.test.ts settings_ui/tests/error-message.test.ts settings_ui/tests/product-links.test.ts
git commit -m "feat: add frontend error help rendering"
```

---

### Task 3: Settings And Batch Coded Error Payloads

**Files:**
- Modify: `addon/anki_audio_quick_editor/settings/async_commands.py`
- Modify: `addon/anki_audio_quick_editor/browser_dialog.py`
- Modify: `addon/anki_audio_quick_editor/browser_dialog_state.py`
- Modify: `settings_ui/src/lib/async-jobs.ts`
- Modify: `settings_ui/src/settings/SettingsApp.svelte`
- Modify: `settings_ui/src/settings/GeneralSettingsPanel.svelte`
- Modify: `settings_ui/src/settings/DiagnosticsPanel.svelte`
- Modify: `settings_ui/src/batch/BatchApp.svelte`
- Test: `tests/test_settings_commands_diagnostics.py`
- Test: `tests/test_browser_dialog_state.py`
- Test: `settings_ui/tests/async-jobs.test.ts`
- Test: `settings_ui/tests/app.test.ts`
- Test: `settings_ui/tests/batch-app.test.ts`

- [ ] **Step 1: Write failing Python payload tests**

In `tests/test_settings_commands_diagnostics.py::test_async_command_reports_unknown_operation`, update expected result:

```python
    assert result == {
        "id": "job-unknown",
        "ok": False,
        "error": "Unknown async operation: explode",
        "user_error": {
            "code": "AQE-FRONTEND-002",
            "message": "Unknown async operation: explode",
        },
    }
```

In `tests/test_settings_commands_diagnostics.py::test_async_health_check_rejects_non_dict_payload_config`, update expected result:

```python
    assert result == {
        "id": "job-1",
        "ok": False,
        "error": "Invalid async command payload",
        "user_error": {
            "code": "AQE-FRONTEND-002",
            "message": "Invalid async command payload",
        },
    }
```

Add this assertion to a batch dialog state test:

```python
from anki_audio_quick_editor.error_codes import AQE_BATCH_INVALID_REQUEST, coded_error


def test_invalid_start_message_has_batch_error_code() -> None:
    payload = batch_error_payload(
        "Batch operation failed: Invalid batch request",
        user_error=coded_error(AQE_BATCH_INVALID_REQUEST, "Batch operation failed: Invalid batch request"),
    )

    assert payload["user_error"]["code"] == "AQE-BATCH-001"
```

- [ ] **Step 2: Write failing Svelte tests**

In `settings_ui/tests/async-jobs.test.ts`, change the invalid result assertion:

```ts
    await expect(promise).rejects.toMatchObject({
      code: "AQE-FRONTEND-001",
      message: "Invalid async result payload for show_log_file",
    });
```

Add a new async failure test:

```ts
  it("rejects with structured backend user errors", async () => {
    const promise = startAsyncOp("health_check", { config });
    const id = asyncCommandAt(0).id;

    handleAsyncDone({
      id,
      ok: false,
      error: "Invalid settings payload",
      user_error: { code: "AQE-SETTINGS-001", message: "Invalid settings payload" },
    });

    await expect(promise).rejects.toMatchObject({
      code: "AQE-SETTINGS-001",
      message: "Invalid settings payload",
    });
  });
```

In `settings_ui/tests/app.test.ts`, add:

```ts
  it("renders coded settings save errors with visible help link", async () => {
    setInitialState();
    render(App);

    window.onSaveError?.({
      error: "Invalid settings payload",
      user_error: { code: "AQE-SETTINGS-001", message: "Invalid settings payload" },
    });

    const error = await screen.findByTestId("save-error");
    expect(error).toHaveTextContent("AQE-SETTINGS-001: Invalid settings payload");
    expect(within(error).getByRole("link", { name: "Help" })).toHaveAttribute(
      "href",
      `${PRODUCT_LINKS.githubPages}errors/AQE-SETTINGS-001/`,
    );
  });
```

In `settings_ui/tests/batch-app.test.ts`, add:

```ts
  it("renders coded batch errors with visible help link", async () => {
    setInitialState();
    render(BatchApp);

    window.onBatchError?.({
      message: "Batch operation failed: Invalid batch request",
      recoverable: false,
      user_error: {
        code: "AQE-BATCH-001",
        message: "Batch operation failed: Invalid batch request",
      },
    });

    expect(screen.getByText(/AQE-BATCH-001:/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Help" })).toHaveAttribute(
      "href",
      `${PRODUCT_LINKS.githubPages}errors/AQE-BATCH-001/`,
    );
  });
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
python3 scripts/dev.py test tests/test_settings_commands_diagnostics.py tests/test_browser_dialog_state.py
cd settings_ui && npm test -- async-jobs.test.ts app.test.ts batch-app.test.ts
```

Expected: fail because structured error propagation and rendering are not integrated.

- [ ] **Step 4: Implement Python structured settings and batch errors**

In `addon/anki_audio_quick_editor/settings/async_commands.py`, import:

```python
from ..error_codes import AQE_FRONTEND_UNKNOWN_ASYNC_ERROR, coded_error
```

For invalid async payloads, build:

```python
        message = "Invalid async command payload"
        invalid_done_payload_json = json.dumps(
            {
                "id": raw_job_id,
                "ok": False,
                "error": message,
                "user_error": coded_error(AQE_FRONTEND_UNKNOWN_ASYNC_ERROR, message),
            }
        )
```

For async worker exceptions, build:

```python
            message = str(async_error)
            failure_done_payload_json = json.dumps(
                {
                    "id": job_id,
                    "ok": False,
                    "error": message,
                    "user_error": coded_error(AQE_FRONTEND_UNKNOWN_ASYNC_ERROR, message),
                }
            )
```

In `addon/anki_audio_quick_editor/browser_dialog.py`, import:

```python
from .error_codes import AQE_BATCH_INVALID_REQUEST, coded_error
```

Change invalid payload handling:

```python
        except (AssertionError, TypeError) as exc:
            message = self.tr("batch.failed", {"error": "Invalid batch request"})
            self.finish_with_error(
                message,
                user_error=coded_error(AQE_BATCH_INVALID_REQUEST, message),
            )
            logger.warning("invalid batch start payload: %s", exc)
            return True
```

Change `finish_with_error` signature:

```python
    def finish_with_error(
        self,
        message: str,
        *,
        recoverable: bool = False,
        user_error: dict[str, str] | None = None,
    ) -> None:
        """Show an unexpected batch-level failure."""
        self._running = False
        self._finished = not recoverable
        self.append_log(message)
        self._emit(
            "onBatchError",
            batch_error_payload(message, recoverable=recoverable, user_error=user_error),
        )
```

- [ ] **Step 5: Implement Svelte structured settings and batch rendering**

In `settings_ui/src/lib/async-jobs.ts`, import:

```ts
import {
  AQE_FRONTEND_INVALID_ASYNC_RESULT,
  AQE_FRONTEND_UNKNOWN_ASYNC_ERROR,
  frontendUserError,
  isUserFacingError,
} from "./user-facing-error.js";
```

Update failure branches:

```ts
    } else {
      job.reject(frontendUserError(AQE_FRONTEND_INVALID_ASYNC_RESULT, narrowed.error));
    }
  } else if (isUserFacingError(payload.user_error)) {
    job.reject(payload.user_error);
  } else {
    job.reject(frontendUserError(AQE_FRONTEND_UNKNOWN_ASYNC_ERROR, payload.error ?? "Unknown async error"));
  }
```

In `settings_ui/src/settings/SettingsApp.svelte`, import:

```ts
  import type { ErrorDisplayValue } from "$lib/user-facing-error.js";
  import { isUserFacingError, messageFromUnknownError } from "$lib/user-facing-error.js";
```

Change state:

```ts
  let saveError = $state<ErrorDisplayValue | "">("");
  let healthMessage = $state<ErrorDisplayValue>(t("settings.health.not_run"));
  let diagnosticsMessage = $state<ErrorDisplayValue | "">("");
```

Update save callback:

```ts
      onSaveError: (payload: SaveErrorPayload) => {
        saveError = isUserFacingError(payload.user_error) ? payload.user_error : payload.error;
      },
```

Replace `messageFromError(error)` calls with:

```ts
      const message = messageFromUnknownError(error);
      diagnosticsMessage = isUserFacingError(error) ? error : message;
```

Use `healthMessage = isUserFacingError(error) ? error : message;` in `runHealthCheck`.

In `GeneralSettingsPanel.svelte`, import `ErrorMessage` and change prop type/render:

```svelte
  import ErrorMessage from "$lib/ErrorMessage.svelte";
  import type { ErrorDisplayValue } from "$lib/user-facing-error.js";

  let { config = $bindable(), saveError }: {
    config: Config;
    saveError: ErrorDisplayValue | "";
  } = $props();
```

```svelte
    <p class="settings-error" data-testid="save-error">
      <ErrorMessage error={saveError} />
    </p>
```

In `DiagnosticsPanel.svelte`, import `ErrorMessage`, update prop types to `ErrorDisplayValue | ""`, and render:

```svelte
      <p class="settings-muted" data-testid="health-message">
        <ErrorMessage error={healthMessage} />
      </p>
      <p class="settings-muted" data-testid="diagnostics-message">
        {#if diagnosticsMessage}
          <ErrorMessage error={diagnosticsMessage} />
        {/if}
      </p>
```

In `BatchApp.svelte`, import:

```ts
  import ErrorMessage from "$lib/ErrorMessage.svelte";
  import type { ErrorDisplayValue } from "$lib/user-facing-error.js";
  import { isUserFacingError } from "$lib/user-facing-error.js";
```

Change status state:

```ts
  let status = $state<ErrorDisplayValue>(t("batch.instructions"));
```

In `onError`:

```ts
        status = isUserFacingError(payload.user_error) ? payload.user_error : payload.message;
```

Render header status:

```svelte
      <p><ErrorMessage error={status} /></p>
```

- [ ] **Step 6: Run focused tests**

Run:

```bash
python3 scripts/dev.py test tests/test_settings_commands_diagnostics.py tests/test_browser_dialog_state.py
cd settings_ui && npm test -- async-jobs.test.ts app.test.ts batch-app.test.ts
```

Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add addon/anki_audio_quick_editor/settings/async_commands.py addon/anki_audio_quick_editor/browser_dialog.py addon/anki_audio_quick_editor/browser_dialog_state.py settings_ui/src/lib/async-jobs.ts settings_ui/src/settings/SettingsApp.svelte settings_ui/src/settings/GeneralSettingsPanel.svelte settings_ui/src/settings/DiagnosticsPanel.svelte settings_ui/src/batch/BatchApp.svelte tests/test_settings_commands_diagnostics.py tests/test_browser_dialog_state.py settings_ui/tests/async-jobs.test.ts settings_ui/tests/app.test.ts settings_ui/tests/batch-app.test.ts
git commit -m "feat: show coded settings and batch errors"
```

---

### Task 4: Settings And Batch Frontend Runtime Fallbacks

**Files:**
- Modify: `settings_ui/src/settings/SettingsApp.svelte`
- Modify: `settings_ui/src/batch/BatchApp.svelte`
- Test: `settings_ui/tests/app.test.ts`
- Test: `settings_ui/tests/batch-app.test.ts`

- [ ] **Step 1: Write failing runtime fallback tests**

In `settings_ui/tests/app.test.ts`, add:

```ts
  it("shows a visible coded error when the settings frontend throws", async () => {
    setInitialState();
    render(App);

    window.dispatchEvent(new ErrorEvent("error", { message: "boom" }));

    const error = await screen.findByTestId("frontend-runtime-error");
    expect(error).toHaveTextContent("AQE-FRONTEND-999: The interface hit an unexpected error. Help");
    expect(within(error).getByRole("link", { name: "Help" })).toHaveAttribute(
      "href",
      `${PRODUCT_LINKS.githubPages}errors/AQE-FRONTEND-999/`,
    );
  });
```

In `settings_ui/tests/batch-app.test.ts`, add:

```ts
  it("shows a visible coded error when the batch frontend throws", async () => {
    setInitialState();
    render(BatchApp);

    window.dispatchEvent(new ErrorEvent("error", { message: "boom" }));

    const error = await screen.findByTestId("frontend-runtime-error");
    expect(error).toHaveTextContent("AQE-FRONTEND-999: The interface hit an unexpected error. Help");
    expect(within(error).getByRole("link", { name: "Help" })).toHaveAttribute(
      "href",
      `${PRODUCT_LINKS.githubPages}errors/AQE-FRONTEND-999/`,
    );
  });
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd settings_ui && npm test -- app.test.ts batch-app.test.ts
```

Expected: fail because no visible runtime fallback is rendered.

- [ ] **Step 3: Add settings runtime fallback**

In `settings_ui/src/settings/SettingsApp.svelte`, import:

```ts
  import ErrorMessage from "$lib/ErrorMessage.svelte";
  import {
    AQE_FRONTEND_UNEXPECTED,
    frontendUserError,
    type ErrorDisplayValue,
  } from "$lib/user-facing-error.js";
```

Add state:

```ts
  let frontendRuntimeError = $state<ErrorDisplayValue | "">("");
```

Inside `onMount`, add listeners and return cleanup:

```ts
    const showFrontendRuntimeError = () => {
      frontendRuntimeError = frontendUserError(
        AQE_FRONTEND_UNEXPECTED,
        "The interface hit an unexpected error.",
      );
    };
    window.addEventListener("error", showFrontendRuntimeError);
    window.addEventListener("unhandledrejection", showFrontendRuntimeError);
    return () => {
      window.removeEventListener("error", showFrontendRuntimeError);
      window.removeEventListener("unhandledrejection", showFrontendRuntimeError);
    };
```

Render below the hero/header:

```svelte
    {#if frontendRuntimeError}
      <p class="settings-error" data-testid="frontend-runtime-error">
        <ErrorMessage error={frontendRuntimeError} />
      </p>
    {/if}
```

- [ ] **Step 4: Add batch runtime fallback**

In `settings_ui/src/batch/BatchApp.svelte`, import:

```ts
  import {
    AQE_FRONTEND_UNEXPECTED,
    frontendUserError,
  } from "$lib/user-facing-error.js";
```

Add state:

```ts
  let frontendRuntimeError = $state<ErrorDisplayValue | "">("");
```

Inside `onMount`, add listeners and return cleanup:

```ts
    const showFrontendRuntimeError = () => {
      frontendRuntimeError = frontendUserError(
        AQE_FRONTEND_UNEXPECTED,
        "The interface hit an unexpected error.",
      );
    };
    window.addEventListener("error", showFrontendRuntimeError);
    window.addEventListener("unhandledrejection", showFrontendRuntimeError);
    return () => {
      window.removeEventListener("error", showFrontendRuntimeError);
      window.removeEventListener("unhandledrejection", showFrontendRuntimeError);
    };
```

Render below the header:

```svelte
    {#if frontendRuntimeError}
      <p class="batch-error" data-testid="frontend-runtime-error">
        <ErrorMessage error={frontendRuntimeError} />
      </p>
    {/if}
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
cd settings_ui && npm test -- app.test.ts batch-app.test.ts
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add settings_ui/src/settings/SettingsApp.svelte settings_ui/src/batch/BatchApp.svelte settings_ui/tests/app.test.ts settings_ui/tests/batch-app.test.ts
git commit -m "feat: show frontend runtime error links"
```

---

### Task 5: Inline Editor Coded Error Rendering

**Files:**
- Modify: `addon/anki_audio_quick_editor/editor_frontend.py`
- Modify: `addon/anki_audio_quick_editor/editor_processing.py`
- Modify: `addon/anki_audio_quick_editor/editor_playback.py`
- Modify: `addon/anki_audio_quick_editor/editor_analysis.py`
- Modify: `addon/anki_audio_quick_editor/editor_recording.py`
- Modify: `settings_ui/src/editor-inline/control-actions.ts`
- Modify: `settings_ui/src/editor-inline/graph-actions.ts`
- Modify: `settings_ui/src/editor-inline/globals.d.ts`
- Test: `tests/test_editor_frontend.py`
- Test: `settings_ui/tests/editor-inline.actions.test.ts`

- [ ] **Step 1: Write failing Python editor frontend tests**

Create `tests/test_editor_frontend.py`:

```python
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.editor_frontend import eval_status, eval_visualizer_status_for_field
from anki_audio_quick_editor.error_codes import AQE_MEDIA_CURRENT_FIELD_AUDIO_MISSING, coded_error


def test_eval_status_accepts_user_facing_error_payload() -> None:
    editor = SimpleNamespace(web=SimpleNamespace(eval=MagicMock()))
    payload = coded_error(AQE_MEDIA_CURRENT_FIELD_AUDIO_MISSING, "No [sound:...] reference found.")

    eval_status(editor, payload, kind="error")

    script = editor.web.eval.call_args.args[0]
    assert '"code": "AQE-MEDIA-001"' in script
    assert '"message": "No [sound:...] reference found."' in script
    assert '"error"' in script


def test_eval_visualizer_status_accepts_user_facing_error_payload() -> None:
    editor = SimpleNamespace(web=SimpleNamespace(eval=MagicMock()))
    payload = coded_error("AQE-GRAPH-001", "Audio visualization failed.")

    eval_visualizer_status_for_field(editor, 3, payload, kind="error")

    script = editor.web.eval.call_args.args[0]
    assert "window.__aqeSetVisualizerStatus" in script
    assert '"code": "AQE-GRAPH-001"' in script
```

- [ ] **Step 2: Write failing Svelte inline editor tests**

In `settings_ui/tests/editor-inline.actions.test.ts`, add imports:

```ts
import { PRODUCT_LINKS } from "../src/lib/product-links.js";
```

Add this test:

```ts
  it("renders coded editor status errors with visible help links", async () => {
    const visualizer = await mountTrack(0);
    window.__aqeActiveField = 0;

    window.__aqeSetStatus?.(
      { code: "AQE-MEDIA-001", message: "No [sound:...] reference found." },
      "error",
    );

    const controls = visualizer.closest<HTMLElement>(".aqe-controls")!;
    const status = controls.querySelector<HTMLElement>(".aqe-status")!;
    const link = status.querySelector<HTMLAnchorElement>("a")!;

    expect(status).toHaveTextContent("AQE-MEDIA-001: No [sound:...] reference found. Help");
    expect(link.href).toBe(`${PRODUCT_LINKS.githubPages}errors/AQE-MEDIA-001/`);
  });
```

Add this visualizer status test near the existing visualizer status test:

```ts
    setVisualizerStatusFromPython(
      0,
      { code: "AQE-GRAPH-001", message: "Audio visualization failed." },
      "error",
    );
    const status = visualizer.querySelector<HTMLElement>(".aqe-status");
    expect(status).toHaveTextContent("AQE-GRAPH-001: Audio visualization failed. Help");
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_frontend.py
cd settings_ui && npm test -- editor-inline.actions.test.ts
```

Expected: fail because editor status functions and Svelte status rendering accept only strings.

- [ ] **Step 4: Update Python editor frontend eval helpers**

In `addon/anki_audio_quick_editor/editor_frontend.py`, add a type alias:

```python
UserStatusPayload = str | dict[str, str]
```

Change signatures:

```python
def eval_status(editor: Any, message: UserStatusPayload, kind: str = "info") -> None:
```

```python
def eval_visualizer_status(editor: Any, message: UserStatusPayload, kind: str = "info") -> None:
```

```python
def eval_visualizer_status_for_field(
    editor: Any,
    field_index: int,
    message: UserStatusPayload,
    kind: str = "info",
) -> None:
```

Keep JSON serialization:

```python
    payload = json.dumps(message)
```

- [ ] **Step 5: Update Svelte inline status rendering**

In `settings_ui/src/editor-inline/globals.d.ts`, import:

```ts
import type { UserFacingError } from "../lib/user-facing-error.js";
```

Add:

```ts
type EditorStatusMessage = string | UserFacingError;
```

Change declarations:

```ts
    __aqeSetStatus?: ((message: EditorStatusMessage, kind?: string) => void) | undefined;
    __aqeSetVisualizerStatus?: ((ord: number, message: EditorStatusMessage, kind?: string) => void) | undefined;
```

In `settings_ui/src/editor-inline/control-actions.ts`, import:

```ts
import { errorHelpUrl } from "../lib/error-links.js";
import { isUserFacingError, type UserFacingError } from "../lib/user-facing-error.js";
```

Add:

```ts
type EditorStatusMessage = string | UserFacingError;

function statusText(message: EditorStatusMessage): string {
  return isUserFacingError(message) ? message.message : message;
}

function renderStatusContent(status: HTMLElement, message: EditorStatusMessage): void {
  status.textContent = "";
  if (!isUserFacingError(message)) {
    status.textContent = message;
    return;
  }
  const code = document.createElement("span");
  code.className = "aqe-error-code";
  code.textContent = `${message.code}:`;
  const link = document.createElement("a");
  link.className = "aqe-error-help-link";
  link.href = errorHelpUrl(message.code);
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = "Help";
  status.append(code, ` ${message.message} `, link);
}
```

Change signatures and stable dataset writes:

```ts
export function setStatus(message: EditorStatusMessage, kind = "info"): void {
  const ord = Number(window.__aqeActiveField ?? 0);
  setStatusForOrd(ord, message, kind);
}

export function setStatusForOrd(ord: number, message: EditorStatusMessage, kind = "info", command = ""): void {
  const status = statusForOrd(ord);
  if (!status) return;
  if (kind !== "processing") {
    status.dataset.stableMessage = statusText(message || "");
    if (isUserFacingError(message)) {
      status.dataset.stableUserError = JSON.stringify(message);
    } else {
      delete status.dataset.stableUserError;
    }
    status.dataset.stableKind = kind || "info";
    status.dataset.stableCommand = command || "";
  }
  renderStatus(status, message || "", kind || "info", command || "");
}
```

Update `restoreStableStatus`:

```ts
function restoreStableStatus(status: HTMLElement): void {
  let message: EditorStatusMessage = status.dataset.stableMessage || "";
  const rawUserError = status.dataset.stableUserError;
  if (rawUserError) {
    try {
      const parsed = JSON.parse(rawUserError) as unknown;
      if (isUserFacingError(parsed)) message = parsed;
    } catch {
      delete status.dataset.stableUserError;
    }
  }
  renderStatus(
    status,
    message,
    status.dataset.stableKind || "info",
    status.dataset.stableCommand || "",
  );
}
```

Update `clearStatus` to remove any stored structured error:

```ts
export function clearStatus(ord: number): void {
  const status = statusForOrd(ord);
  if (!status) return;
  status.dataset.stableMessage = "";
  delete status.dataset.stableUserError;
  status.dataset.stableKind = "info";
  status.dataset.stableCommand = "";
  renderStatus(status, "", "info", "");
}
```

Update `renderStatus`:

```ts
function renderStatus(status: HTMLElement, message: EditorStatusMessage, kind: string, command: string): void {
  renderStatusContent(status, message);
  status.dataset.kind = kind;
  setTooltipContent(status, command || statusText(message));
  const spinner = status.closest<HTMLElement>(".aqe-status-row")?.querySelector<HTMLElement>(".aqe-spinner");
  if (spinner) spinner.hidden = kind !== "processing";
}
```

In `settings_ui/src/editor-inline/graph-actions.ts`, import `type UserFacingError` and change:

```ts
export function setVisualizerStatusFromPython(ord: number, message: string | UserFacingError, kind = "info"): void {
```

- [ ] **Step 6: Map common editor errors to codes**

In editor modules, import needed constants:

```python
from .error_codes import (
    AQE_AUDIO_PROCESSING_FAILED,
    AQE_GRAPH_ANALYSIS_FAILED,
    AQE_MEDIA_CURRENT_FIELD_AUDIO_MISSING,
    AQE_MEDIA_REFERENCED_AUDIO_MISSING,
    AQE_PLAYBACK_PREPARE_FAILED,
    AQE_RECORDING_FAILED,
    coded_error,
)
```

Use these mappings at display boundaries:

```python
deps.eval_status(editor, coded_error(AQE_AUDIO_PROCESSING_FAILED, message), kind="error")
```

```python
deps.eval_status(editor, coded_error(AQE_PLAYBACK_PREPARE_FAILED, message or t("editor.playback.prepare_failed")), kind="error")
```

```python
deps.eval_visualizer_status_for_field(
    editor,
    field_index,
    coded_error(AQE_GRAPH_ANALYSIS_FAILED, message or t("editor.graph.failed")),
    kind="error",
)
```

```python
deps.eval_status(editor, coded_error(AQE_RECORDING_FAILED, message), kind="error")
```

For known media messages, use:

```python
coded_error(AQE_MEDIA_CURRENT_FIELD_AUDIO_MISSING, deps.current_field_audio_missing)
```

and:

```python
coded_error(AQE_MEDIA_REFERENCED_AUDIO_MISSING, deps.referenced_audio_missing)
```

- [ ] **Step 7: Run focused tests**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_frontend.py
cd settings_ui && npm test -- editor-inline.actions.test.ts editor-inline.window-contract.test.ts
```

Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add addon/anki_audio_quick_editor/editor_frontend.py addon/anki_audio_quick_editor/editor_processing.py addon/anki_audio_quick_editor/editor_playback.py addon/anki_audio_quick_editor/editor_analysis.py addon/anki_audio_quick_editor/editor_recording.py settings_ui/src/editor-inline/control-actions.ts settings_ui/src/editor-inline/graph-actions.ts settings_ui/src/editor-inline/globals.d.ts tests/test_editor_frontend.py settings_ui/tests/editor-inline.actions.test.ts
git commit -m "feat: show coded editor errors"
```

---

### Task 6: Error Documentation Pages

**Files:**
- Create: `docs/errors/index.html`
- Create: `docs/errors/error-page.js`
- Create: `docs/errors/<CODE>/index.html` for every initial code
- Modify: `settings_ui/tests/product-links.test.ts`

- [ ] **Step 1: Write failing docs link test**

Add to `settings_ui/tests/product-links.test.ts`:

```ts
const ERROR_CODES = [
  "AQE-MEDIA-001",
  "AQE-MEDIA-002",
  "AQE-RUNTIME-001",
  "AQE-RUNTIME-002",
  "AQE-RUNTIME-003",
  "AQE-AUDIO-001",
  "AQE-PLAYBACK-001",
  "AQE-GRAPH-001",
  "AQE-RECORDING-001",
  "AQE-BATCH-001",
  "AQE-SETTINGS-001",
  "AQE-FRONTEND-001",
  "AQE-FRONTEND-002",
  "AQE-FRONTEND-999",
] as const;
```

Add test:

```ts
  it("backs every initial error help link with a docs page", async () => {
    const { errorHelpUrl } = await import("../src/lib/error-links.js");

    for (const code of ERROR_CODES) {
      const url = new URL(errorHelpUrl(code));
      const pagePath = join(DOCS_ROOT, "errors", code, "index.html");

      expect(url.pathname).toBe(`/anki-audio-tools/errors/${code}/`);
      expect(existsSync(pagePath), `${code} docs page exists`).toBe(true);
    }
  });
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd settings_ui && npm test -- product-links.test.ts
```

Expected: fail because `docs/errors/<CODE>/index.html` files do not exist.

- [ ] **Step 3: Create shared docs script**

Create `docs/errors/error-page.js`:

```js
const ERROR_COPY = {
  "AQE-MEDIA-001": {
    title: "No sound reference in the current field",
    meaning: "Audio Quick Editor could not find a supported [sound:...] reference in the field you are editing.",
    causes: ["The active field has no audio.", "The first audio reference uses an unsupported file extension.", "The cursor is in a different field than the audio field."],
    fixes: ["Move to a field that contains a supported Anki sound reference.", "Add audio to the field and try again.", "Use Anki's media check if the field content looks correct but playback is broken."]
  },
  "AQE-MEDIA-002": {
    title: "Referenced audio file is missing",
    meaning: "The note points to an audio file that is not present in Anki's media folder.",
    causes: ["The media file was deleted.", "The collection has not finished syncing media.", "The sound tag has a typo."],
    fixes: ["Run Anki media check.", "Restore or re-add the missing audio file.", "Wait for media sync to finish and try again."]
  },
  "AQE-RUNTIME-001": {
    title: "ffmpeg is missing",
    meaning: "Audio Quick Editor could not find ffmpeg.",
    causes: ["The managed runtime is still installing.", "The configured ffmpeg path is wrong.", "ffmpeg is not available in PATH."],
    fixes: ["Open Settings > Diagnostics and run Install/Repair Runtime.", "Check the configured ffmpeg path.", "Install ffmpeg or make it available in PATH."]
  },
  "AQE-RUNTIME-002": {
    title: "ffprobe is missing",
    meaning: "Audio Quick Editor found ffmpeg but could not find ffprobe for duration inspection.",
    causes: ["ffprobe is not next to ffmpeg.", "The runtime pack is incomplete.", "A custom ffmpeg install omitted ffprobe."],
    fixes: ["Open Settings > Diagnostics and run Install/Repair Runtime.", "Use an ffmpeg installation that includes ffprobe.", "Check that ffprobe is executable."]
  },
  "AQE-RUNTIME-003": {
    title: "Runtime asset is missing",
    meaning: "A managed or bundled tool or model needed by the selected operation is missing.",
    causes: ["The runtime download did not complete.", "A runtime file was removed.", "This platform is not supported for the selected runtime asset."],
    fixes: ["Open Settings > Diagnostics and run Install/Repair Runtime.", "Copy a support report if repair fails.", "Use a supported macOS or Windows release target."]
  },
  "AQE-AUDIO-001": {
    title: "Audio processing failed",
    meaning: "The audio operation could not complete.",
    causes: ["ffmpeg or another tool returned an error.", "The source file is corrupt or unsupported.", "The selected edit would produce invalid audio."],
    fixes: ["Try playing the original file in Anki.", "Run Settings > Diagnostics > Run Health Check.", "Copy a support report with the exact failing operation."]
  },
  "AQE-PLAYBACK-001": {
    title: "Playback preparation failed",
    meaning: "Audio Quick Editor could not prepare the temporary segment used for playback from a cursor or selection.",
    causes: ["The source media is missing.", "ffmpeg failed to render the temporary segment.", "The requested cursor or selection is outside the audio duration."],
    fixes: ["Try playing from the start.", "Redraw the graph and retry.", "Run diagnostics if playback keeps failing."]
  },
  "AQE-GRAPH-001": {
    title: "Graph analysis failed",
    meaning: "Audio Quick Editor could not analyze pitch and loudness for the selected audio.",
    causes: ["The audio file is missing or unreadable.", "The analyzer failed on this file.", "Runtime tools required for fallback decoding are missing."],
    fixes: ["Try converting the audio to MP3 or WAV.", "Run Settings > Diagnostics > Run Health Check.", "Copy a support report if the file plays but graphing fails."]
  },
  "AQE-RECORDING-001": {
    title: "Voice recording failed",
    meaning: "Recording, saving, or analyzing your comparison recording failed.",
    causes: ["Microphone permission is denied.", "The recording target graph no longer matches the current audio.", "The recorded file could not be saved or analyzed."],
    fixes: ["Check operating system microphone permission for Anki.", "Redraw the graph and record again.", "Copy a support report if recording still fails."]
  },
  "AQE-BATCH-001": {
    title: "Invalid batch request",
    meaning: "The batch dialog could not start because the requested operation or fields were invalid.",
    causes: ["A required source field was not selected.", "A graph operation target field was not selected.", "The frontend sent a malformed request."],
    fixes: ["Choose a source field.", "Choose a target field for graph generation.", "Close and reopen the Browser batch dialog if the controls look stale."]
  },
  "AQE-SETTINGS-001": {
    title: "Invalid settings payload",
    meaning: "The settings dialog sent configuration data that failed validation.",
    causes: ["The dialog bundle and Python contract are out of sync.", "A setting value has an invalid shape.", "The settings window was open across an add-on update."],
    fixes: ["Close and reopen Settings.", "Restart Anki after updating the add-on.", "Copy a support report if saving still fails."]
  },
  "AQE-FRONTEND-001": {
    title: "Invalid frontend async result",
    meaning: "The Svelte interface received a Python async result that did not match the expected contract.",
    causes: ["Frontend and backend contracts are out of sync.", "An async operation returned the wrong result shape."],
    fixes: ["Restart Anki after updating the add-on.", "Copy a support report if the same action still fails."]
  },
  "AQE-FRONTEND-002": {
    title: "Frontend async operation failed",
    meaning: "A settings or diagnostics async operation failed without a more specific user-facing code.",
    causes: ["The backend operation raised an unexpected exception.", "The WebView received a generic failure result."],
    fixes: ["Retry the action once.", "Copy a support report if it fails again."]
  },
  "AQE-FRONTEND-999": {
    title: "Unexpected interface error",
    meaning: "The Svelte interface hit an unexpected runtime error.",
    causes: ["A JavaScript runtime exception occurred.", "The WebView state became inconsistent."],
    fixes: ["Close and reopen the dialog or editor note.", "Restart Anki if the interface remains broken.", "Copy a support report with frontend logs."]
  }
};

function currentCode() {
  const parts = window.location.pathname.split("/").filter(Boolean);
  return parts[parts.length - 1] || "";
}

function renderList(items) {
  return `<ul>${items.map((item) => `<li>${item}</li>`).join("")}</ul>`;
}

function renderErrorPage() {
  const code = currentCode();
  const copy = ERROR_COPY[code];
  const root = document.getElementById("error-page");
  if (!root) return;
  if (!copy) {
    root.innerHTML = `<h1>Unknown error code</h1><p>This error code is not documented yet.</p><p><a href="../">All error codes</a></p>`;
    return;
  }
  document.title = `${code}: ${copy.title}`;
  root.innerHTML = `
    <p><a href="../">All error codes</a></p>
    <h1>${code}: ${copy.title}</h1>
    <h2>What It Means</h2>
    <p>${copy.meaning}</p>
    <h2>Common Causes</h2>
    ${renderList(copy.causes)}
    <h2>How To Fix It</h2>
    ${renderList(copy.fixes)}
    <h2>If It Persists</h2>
    <p>Open Settings &gt; Diagnostics and copy a support report before filing a bug.</p>
  `;
}

renderErrorPage();
```

- [ ] **Step 4: Create docs index**

Create `docs/errors/index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Audio Quick Editor Error Codes</title>
    <link rel="stylesheet" href="../assets/site.css">
  </head>
  <body>
    <main>
      <h1>Audio Quick Editor Error Codes</h1>
      <p>Use the code shown in Anki to find the matching help page.</p>
      <ul>
        <li><a href="AQE-MEDIA-001/">AQE-MEDIA-001</a></li>
        <li><a href="AQE-MEDIA-002/">AQE-MEDIA-002</a></li>
        <li><a href="AQE-RUNTIME-001/">AQE-RUNTIME-001</a></li>
        <li><a href="AQE-RUNTIME-002/">AQE-RUNTIME-002</a></li>
        <li><a href="AQE-RUNTIME-003/">AQE-RUNTIME-003</a></li>
        <li><a href="AQE-AUDIO-001/">AQE-AUDIO-001</a></li>
        <li><a href="AQE-PLAYBACK-001/">AQE-PLAYBACK-001</a></li>
        <li><a href="AQE-GRAPH-001/">AQE-GRAPH-001</a></li>
        <li><a href="AQE-RECORDING-001/">AQE-RECORDING-001</a></li>
        <li><a href="AQE-BATCH-001/">AQE-BATCH-001</a></li>
        <li><a href="AQE-SETTINGS-001/">AQE-SETTINGS-001</a></li>
        <li><a href="AQE-FRONTEND-001/">AQE-FRONTEND-001</a></li>
        <li><a href="AQE-FRONTEND-002/">AQE-FRONTEND-002</a></li>
        <li><a href="AQE-FRONTEND-999/">AQE-FRONTEND-999</a></li>
      </ul>
    </main>
  </body>
</html>
```

- [ ] **Step 5: Create per-code pages**

For each initial code directory, create `index.html` with exactly this content:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Audio Quick Editor Error Help</title>
    <link rel="stylesheet" href="../../assets/site.css">
  </head>
  <body>
    <main id="error-page">
      <h1>Audio Quick Editor Error Help</h1>
    </main>
    <script src="../error-page.js"></script>
  </body>
</html>
```

Create these paths:

```text
docs/errors/AQE-MEDIA-001/index.html
docs/errors/AQE-MEDIA-002/index.html
docs/errors/AQE-RUNTIME-001/index.html
docs/errors/AQE-RUNTIME-002/index.html
docs/errors/AQE-RUNTIME-003/index.html
docs/errors/AQE-AUDIO-001/index.html
docs/errors/AQE-PLAYBACK-001/index.html
docs/errors/AQE-GRAPH-001/index.html
docs/errors/AQE-RECORDING-001/index.html
docs/errors/AQE-BATCH-001/index.html
docs/errors/AQE-SETTINGS-001/index.html
docs/errors/AQE-FRONTEND-001/index.html
docs/errors/AQE-FRONTEND-002/index.html
docs/errors/AQE-FRONTEND-999/index.html
```

- [ ] **Step 6: Run docs tests**

Run:

```bash
cd settings_ui && npm test -- product-links.test.ts
```

Expected: passes.

- [ ] **Step 7: Commit**

```bash
git add docs/errors settings_ui/tests/product-links.test.ts
git commit -m "docs: add error code help pages"
```

---

### Task 7: Final Verification And Quality Gate

**Files:**
- Verify all touched files.

- [ ] **Step 1: Run contract validation**

Run:

```bash
python3 scripts/dev.py contracts-check
```

Expected: pass.

- [ ] **Step 2: Run focused Python tests**

Run:

```bash
python3 scripts/dev.py test tests/test_error_codes.py tests/test_settings_commands_save.py tests/test_settings_commands_diagnostics.py tests/test_browser_dialog_state.py tests/test_editor_frontend.py
```

Expected: pass.

- [ ] **Step 3: Run focused Svelte tests**

Run:

```bash
cd settings_ui && npm test -- user-facing-error.test.ts error-message.test.ts async-jobs.test.ts app.test.ts batch-app.test.ts editor-inline.actions.test.ts product-links.test.ts
```

Expected: pass.

- [ ] **Step 4: Run repository frontend validation**

Run:

```bash
python3 scripts/dev.py test-svelte
```

Expected: pass.

- [ ] **Step 5: Run Python unit test suite**

Run:

```bash
python3 scripts/dev.py test
```

Expected: pass.

- [ ] **Step 6: Run full reusable QC gate**

Run:

```bash
python3 scripts/dev.py check
```

Expected: pass.

- [ ] **Step 7: Run e2e suite**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected: pass. If it cannot be run because Anki or the display environment is unavailable, record the exact failure in the final implementation summary.

- [ ] **Step 8: Final commit if verification changed files**

If contract generation or formatting changed files after previous commits, commit them:

```bash
git status --short
git add contracts/communication.schema.json addon/anki_audio_quick_editor settings_ui/src settings_ui/tests tests docs/errors
git commit -m "test: verify error code help links"
```

If `git status --short` is empty, do not create an empty commit.

---

## Spec Coverage Review

- Stable codes: Task 1 defines backend constants and Task 2 defines frontend constants.
- Visible direct links: Task 2 adds `ErrorMessage`, Task 3 integrates settings/batch, Task 4 integrates editor status.
- Svelte errors: Task 3 handles async and displayed Svelte workflow failures; Task 4 handles visible settings and batch runtime fallbacks; Task 5 covers inline editor status rendering.
- GitHub Pages docs: Task 6 creates deterministic `/errors/<CODE>/` pages.
- Compatibility: Tasks 1 and 3 keep existing `error`/`message` string fields and add optional `user_error`.
- Verification: Task 7 runs contract, Python, Svelte, QC, and e2e commands.
