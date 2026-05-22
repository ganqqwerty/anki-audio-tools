# Editor Audio Sharing Design

## Goal

Add an inline editor share action that uploads the current audio file to Catbox or Litterbox and copies the returned URL to the clipboard without changing note contents or local media references.

## Scope

In scope:

- An editor-only top-level `Share` toolbar action.
- A split-button choice between Catbox and Litterbox.
- Anonymous uploads of the current editor audio file.
- Clipboard copy plus a visible success status message.
- A hideable `aqe:share` toolbar command in the existing toolbar visibility setting.
- Unit, frontend, integration, architecture, and e2e coverage using a fake upload boundary.

Out of scope:

- Browser batch, settings-dialog, or menu-based sharing surfaces.
- Catbox account support, `userhash`, or any login/auth configuration.
- Persisted default host selection.
- Litterbox expiry customization or filename-length customization.
- Replacing note sound references with remote URLs.
- Upload history, retries, or background queue management.

## Service Model

The feature targets the current public Catbox and Litterbox services:

- Catbox is the persistent option.
- Litterbox is the temporary option.

The editor split button should expose only that one decision. To keep the UI one-dimensional, Litterbox uploads use a fixed three-day expiry in v1 instead of adding a second control for retention.

The implementation should centralize all service-specific request details in one Python module so future service drift is isolated to one place.

## UX

Add a new top-level editor command, `aqe:share`, placed immediately after `aqe:show-file`, because both actions operate on the current file rather than on audio transformations.

The control should follow the current split-button pattern:

- The primary segment uploads using the field's currently selected share target.
- The attached menu segment opens a small popover with two preset choices:
  - `Catbox`
  - `Litterbox (3 days)`
- The popover should not show the normal split-button "save default" affordance, because v1 does not persist a default host.
- The initial target for every newly mounted field is `Litterbox`.
- Choosing a target updates only that field's local state.
- Choosing a target does not write config and does not affect other fields.

Primary-click behavior:

- Resolve the same "current audio file" that `aqe:show-file` would reveal.
- Upload that file in the background.
- Copy the returned URL to the clipboard.
- Show a success status message that includes the host, for example `Copied Catbox link for clip.mp3`.

The action must not:

- alter the note field HTML,
- replace the current sound reference,
- create undo history entries,
- or launch a browser.

## Field State

Share target selection is local editor runtime state, not persisted config.

Add a field-local share target value alongside the other split-button field state. The state rules are:

- A newly mounted field starts with `catbox`.
- Changing field 0 to `litterbox` does not change field 1.
- Repeated primary clicks reuse the field's current target.
- Reloading the editor or note resets the target to `catbox`.

No new settings key is introduced for host selection.

## Command Flow

`aqe:share` should use the existing payload-capable editor command path instead of inventing a new bridge shape.

Expected payload shape:

```json
{
  "command": "aqe:share",
  "fieldOrd": 0,
  "shareTarget": "catbox"
}
```

`shareTarget` should be a top-level payload field, not part of `overrides`, because it is not an audio-processing parameter.

Flow:

1. The frontend split button builds a payload with `command`, `fieldOrd`, and `shareTarget`.
2. The frontend sends it through `aqe:command-payload`.
3. `editor_actions.py` decodes and validates `shareTarget`.
4. `editor_bridge.py` routes `aqe:share` as a non-processing command.
5. The editor adapter resolves the current media path using the same semantics as `aqe:show-file`.
6. A background worker uploads the file.
7. On the main thread, the returned URL is copied to the clipboard and a success status is shown.
8. The editor busy state is cleared.

Invalid `shareTarget` payloads should be rejected with a user-visible error instead of silently falling back to a different host.

## Upload Backend

Introduce a dedicated Python upload boundary instead of embedding HTTP logic in editor callbacks.

Module split:

- `file_sharing.py`
  - Owns host metadata, request construction, multipart form submission, timeout handling, response parsing, and normalized share errors.
  - Uses only Python stdlib runtime pieces such as `urllib.request`, `mimetypes`, and `pathlib`.
  - Returns a direct URL string on success.
- `editor_sharing.py`
  - Owns editor-side coordination: current-media resolution, busy-state transitions, worker thread startup, clipboard copy, and status messaging.

Behavior requirements:

- Uploads are anonymous only.
- Use a 60-second request timeout.
- Return host-specific error messages that preserve useful server text when available.
- Do not retry automatically.
- Do not upload if the editor is already busy processing another action.

The share worker should not mutate editor session audio state. Sharing is an external export action, not an audio edit.

## Clipboard And Recovery

The normal success path is:

- upload succeeds,
- clipboard write succeeds,
- success toast is shown.

If the upload succeeds but the clipboard is unavailable, the implementation must not discard the URL. It should:

- log a warning,
- show a status message containing the URL,
- and avoid re-uploading.

That keeps the result recoverable even if clipboard access fails unexpectedly.

## Errors

The feature should reuse existing editor media-resolution errors where possible:

- If the current field has no supported sound reference, reuse the current-field audio missing status.
- If the referenced media file is missing, reuse the missing-media status.
- If the editor is still processing another action, reuse the standard busy status.

Upload-specific failures should be normalized into concise user-visible messages:

- network timeout,
- network connection failure,
- HTTP rejection,
- unexpected non-URL response,
- or service-declared rejection.

The error must leave the note unchanged and must clear the busy state.

## Toolbar Visibility

`aqe:share` should become a normal top-level toolbar command:

- Add it to the editor command union and button metadata.
- Add it to the default visible toolbar list.
- Add it to the config schema enum for `visible_editor_buttons`.
- Allow users to hide it through the existing toolbar visibility setting.

No other settings changes are required.

## Architecture Boundaries

The implementation should follow the current editor split-button and command boundaries:

- `settings_ui/src/editor-inline/`
  - Owns the share split-button rendering, the two host choices, and field-local host selection.
  - Must not know endpoints, timeouts, clipboard APIs, or Python upload details.
- `settings_ui/src/lib/editor-toolbar-buttons.ts`
  - Owns `aqe:share` metadata, label/title wiring, default placement, and toolbar visibility participation.
- `editor_actions.py`
  - Owns `CMD_SHARE`, payload decoding, and payload validation.
  - Must not perform HTTP requests or clipboard writes.
- `editor_bridge.py`
  - Owns routing of `aqe:share` into the editor sharing adapter.
- `editor_sharing.py`
  - Owns the editor adapter behavior for sharing.
  - May coordinate background work, main-thread clipboard updates, and status messages.
- `file_sharing.py`
  - Owns external network side effects and service-specific request details.
- `editor_settings_actions.py`
  - Should remain focused on settings opening and file reveal. Share behavior should not be added there.
- `audio_operations.py`, `audio_state.py`, and `audio_processor.py`
  - Must remain unchanged in responsibility. Sharing is not a batchable audio operation and should not be modeled as one.

These new Python modules must be added to the architecture contract registry with the correct import and side-effect boundaries.

## Architecture Tests

The implementation should extend architecture coverage in these areas:

- `tests/test_architecture/test_rule3_editor_bridge_contract.py`
  - Keep `aqe:share` synchronized between Python bridge registration and editor frontend source.
- Import-safe boundary tests
  - Ensure `editor_actions.py` payload decoding stays free of Anki/Qt imports.
- Side-effect boundary tests
  - Ensure only `editor_sharing.py` and `file_sharing.py` own the new clipboard/network side effects.
- Module contract coverage
  - Ensure any new production module is registered in `MODULE_CONTRACTS`.
- Shared core independence
  - Ensure audio-operation shared core modules do not gain `aqe:share` or Catbox/Litterbox logic.

## Testing

No automated test should hit the live Catbox or Litterbox services.

Required coverage:

- Python unit tests for share payload decoding and invalid-target rejection.
- Python unit tests for Catbox request construction and response parsing.
- Python unit tests for Litterbox request construction and fixed-retention behavior.
- Python unit tests for upload failure mapping, including timeout, HTTP error, and malformed response cases.
- Frontend tests for the `aqe:share` split button rendering.
- Frontend tests proving the share popover offers Catbox and Litterbox choices and omits the save-default affordance.
- Frontend tests proving field-local host selection and repeated primary-click reuse.
- Integration tests for editor bridge routing of `aqe:share`.
- Integration tests for busy-state handling, missing-media handling, clipboard success, and clipboard-unavailable recovery.
- Tests for toolbar visibility settings and editor config injection including `aqe:share`.
- E2E tests using a fake uploader boundary that verify:
  - the button is visible by default,
  - Catbox selection copies a deterministic Catbox URL,
  - Litterbox selection copies a deterministic Litterbox URL,
  - repeated primary clicks reuse the current field's selected host,
  - different fields can hold different share targets,
  - and note contents remain unchanged after sharing.

## Non-Goals

This feature deliberately does not attempt to become a general export system. It is a narrow "share the current audio file" action for the inline editor.
