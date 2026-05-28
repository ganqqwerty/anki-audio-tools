# Error Code Help Links Design

Status: approved for planning
Date: 2026-05-28

## Context

Audio Quick Editor currently shows user-facing errors as localized strings, raw exception text, batch status text, or settings diagnostics messages. This is readable in the moment, but it makes support harder because screenshots and copied messages do not always identify the exact remediation path.

The new system adds stable error codes and directly visible GitHub Pages help links to user-visible failures. The code gives support and documentation a durable identifier. The help link gives users a richer page with explanation, fixes, screenshots, and optional videos.

## Goals

- Show a stable code beside known user-visible errors.
- Show a directly visible help link whenever a code exists.
- Keep localized user messages intact.
- Preserve raw dynamic details in logs and support reports.
- Give Svelte-owned errors the same treatment as Python/backend errors.
- Keep the first implementation narrow enough to land without rewriting all error handling.

## Non-Goals

- Do not create a unique public code for every ffmpeg stderr line or OS exception.
- Do not replace diagnostics logs or support reports.
- Do not require all localized catalogs to duplicate help URLs.
- Do not block existing error display if a code or help page is missing.

## Error Code Format

Codes use:

```text
AQE-<AREA>-<NUMBER>
```

Examples:

- `AQE-MEDIA-001`
- `AQE-RUNTIME-001`
- `AQE-FRONTEND-999`

Area prefixes should describe the remediation area, not the implementation module. The initial areas are:

- `MEDIA`
- `RUNTIME`
- `AUDIO`
- `PLAYBACK`
- `GRAPH`
- `RECORDING`
- `BATCH`
- `SETTINGS`
- `FRONTEND`

`999` is reserved for unexpected fallback failures inside an area. It should not be used for known failure modes that can get a specific code.

## Initial Code Set

| Code | Meaning |
| --- | --- |
| `AQE-MEDIA-001` | Current field has no supported `[sound:...]` reference. |
| `AQE-MEDIA-002` | Referenced media file is missing from Anki media. |
| `AQE-RUNTIME-001` | `ffmpeg` is missing. |
| `AQE-RUNTIME-002` | `ffprobe` is missing. |
| `AQE-RUNTIME-003` | Managed or bundled runtime asset is missing. |
| `AQE-AUDIO-001` | Audio processing command failed. |
| `AQE-PLAYBACK-001` | Playback segment preparation failed. |
| `AQE-GRAPH-001` | Graph/prosody analysis failed. |
| `AQE-RECORDING-001` | Voice recording failed. |
| `AQE-BATCH-001` | Batch start request is invalid. |
| `AQE-SETTINGS-001` | Settings payload is invalid. |
| `AQE-FRONTEND-001` | Frontend received an invalid async result payload. |
| `AQE-FRONTEND-002` | Frontend async operation failed without a specific backend code. |
| `AQE-FRONTEND-999` | Unexpected frontend runtime error. |

More specific runtime codes can be added later for RNNoise, DPDFNet, Voice Only, and Silero if support volume shows that one shared runtime-asset code is too coarse.

## Help URL Scheme

Help URLs are deterministic:

```text
https://ganqqwerty.github.io/anki-audio-tools/errors/<CODE>/
```

Examples:

```text
https://ganqqwerty.github.io/anki-audio-tools/errors/AQE-RUNTIME-001/
https://ganqqwerty.github.io/anki-audio-tools/errors/AQE-FRONTEND-999/
```

The application should generate the URL from the code and the existing GitHub Pages base URL. Error payloads should not carry hardcoded per-error URLs unless a future external documentation target requires it.

## User-Facing Shape

All structured user-facing errors should converge on this shape:

```ts
type UserFacingError = {
  code: string;
  message: string;
  details?: string;
};
```

The rendered help URL is derived from `code`.

Python should use the same shape as a dictionary when sending errors to WebViews. String-only paths remain valid during migration, but new known errors should use the structured shape.

## Display Rules

Every coded error displays:

```text
AQE-RUNTIME-001: Audio Quick Editor requires ffmpeg. Help
```

Rules:

- `Help` is a visible inline link, not only a tooltip.
- The link opens the deterministic GitHub Pages URL.
- Compact editor status rows should keep the message short and show the link inline.
- Settings and batch views can show the same inline link in their status area.
- Raw details may be hidden from the compact UI but must remain available in logs/support reports.
- Unknown string-only failures display as they do today until migrated.

## Python Architecture

Add a small backend catalog, likely `addon/anki_audio_quick_editor/error_codes.py`.

Responsibilities:

- Define stable code constants.
- Build `UserFacingError` dictionaries.
- Attach a code to known exceptions or known error branches.
- Provide a formatting helper for string-only sinks that cannot yet accept structured payloads.

This should avoid a broad exception hierarchy rewrite. The first implementation can map known display points to codes at the boundary where an error is shown or sent to Svelte.

## Svelte Architecture

Add shared frontend helpers, likely:

- `settings_ui/src/lib/user-facing-error.ts`
- `settings_ui/src/lib/error-links.ts`
- `settings_ui/src/lib/ErrorMessage.svelte`

Responsibilities:

- Accept either a string or `UserFacingError`.
- Render code, localized message, and visible `Help` link.
- Build help links from `PRODUCT_LINKS.githubPages`.
- Provide frontend-owned errors for Svelte validation and uncaught runtime failures.

The component should be used by:

- Settings save error display.
- Settings diagnostics async error display.
- Batch dialog status errors.
- Inline editor status rendering by extending the existing window contract to accept either a string or `UserFacingError`.

## Svelte Error Classes

Expected backend errors shown in Svelte:

- Python sends a structured coded payload.
- Svelte renders it directly with `ErrorMessage`.
- Existing string payloads remain supported while callers migrate.

Frontend validation and contract errors:

- Invalid async result payload becomes `AQE-FRONTEND-001`.
- Unknown async error becomes `AQE-FRONTEND-002`.
- These should be shown when they affect the visible settings or batch workflow.

Uncaught Svelte/runtime exceptions:

- Settings and batch already install WebView-level error reporters that log to Python.
- Add a visible fallback status/banner for settings and batch:
  `AQE-FRONTEND-999: The interface hit an unexpected error. Help`
- Inline editor should use the existing status row rather than a large banner.
- Stack traces stay in frontend logs and support report context, not in the visible message.

## Data Flow

Backend editor error:

1. Python catches or detects a known failure.
2. Python maps it to a code and localized message.
3. Python sends a status payload or formatted coded string to the editor frontend.
4. Editor displays `CODE: message Help`.

Settings async error:

1. Python async worker catches an exception.
2. Known failures become structured coded payloads in `AsyncDonePayload`.
3. Svelte rejects with a `UserFacingError` instead of a plain `Error` when possible.
4. Diagnostics panel renders the visible link.

Batch error:

1. Python validates the start request or catches a batch-level failure.
2. `BatchErrorPayload` carries structured error data.
3. Batch app renders the coded message and help link in the status area.

Frontend runtime error:

1. Window error or unhandled rejection fires.
2. Logger records stack/context through existing frontend logging.
3. UI sets a visible `AQE-FRONTEND-999` message with help link.

## Documentation Pages

Each page under `docs/errors/<CODE>/` should include:

- Short title with code.
- What the error means.
- Common causes.
- How to fix it.
- What to include in a bug report if it persists.
- Optional video embed or link when available.

The first implementation can create concise starter pages for the initial code set. Videos can be added later without changing app code.

## Testing

Backend tests:

- Error catalog builds expected code and message shape.
- Known editor/media/runtime errors are mapped to codes.
- Settings and batch error payloads preserve compatibility with string-only callers if migration is staged.

Svelte tests:

- `ErrorMessage` renders code, message, and visible help link.
- Help link uses `PRODUCT_LINKS.githubPages`.
- Settings async invalid payload maps to `AQE-FRONTEND-001`.
- Unknown async error maps to `AQE-FRONTEND-002`.
- Batch error payload renders a visible help link.

E2E tests:

- A known missing-media/editor error displays a code and visible `Help` link.
- A settings invalid-save path displays `AQE-SETTINGS-001` and a help link.
- A batch invalid-start path displays `AQE-BATCH-001` and a help link.

## Rollout

1. Add catalog and frontend rendering helpers.
2. Migrate the most common known errors first: media missing, ffmpeg/ffprobe missing, generic audio processing failed, graph failed, settings invalid payload, batch invalid request.
3. Add docs pages for the initial code set.
4. Expand codes only when support cases show that a generic code is too broad.

## Implementation Decisions

- Inline editor status should extend the existing `__aqeSetStatus` and `__aqeSetVisualizerStatus` contracts to accept either a string or `UserFacingError`. This keeps direct links possible without embedding HTML in translated strings.
- Runtime asset failures should start as one shared `AQE-RUNTIME-003`. Separate tool/model codes should be added only when support cases require more precision.
- Documentation pages should be committed as static content under `docs/errors/<CODE>/` for the first implementation. A generated catalog can be introduced later if the list grows enough to justify it.
