# Browser Audio “Convert to MP3” Recovery Implementation Plan

**Goal:** When Audio Quick Editor’s HTML audio element cannot decode an existing non-MP3 source, show a truthful playback error with an explicit **Convert to MP3** recovery action. The action must reuse the existing editor conversion operation, update the note only after the user clicks, and retain the current undo, redo, persistent-history, graph, post-edit autoplay, sharing, and Reviewer behavior.

**Decision:** Do not restore native `av_player` playback and do not create a transparent playback proxy. Keep HTML audio as the sole AQE playback engine. Conversion is an explicit media edit initiated by the user.

**Implementation style:** Test first. Keep the recovery action narrow and typed. Reuse `aqe:convert`; do not introduce a second conversion implementation or a new bridge command.

**Implementation status (2026-07-15):** Implemented. `scripts/dev.py check` and all feature-specific real-Anki E2Es pass, including missing media, M4A recovery with emitted PCM and undo/redo, and the AAC metadata/route-probe race. Two full parallel E2E attempts were not clean because unrelated shared-desktop/browser-selection and acoustic timing flakes occurred; exact reruns passed where rerun, and both feature-specific scenarios pass independently.

---

## 1. Context and Verified Root Cause

The reported file exists in Anki media and is valid AAC-LC audio in an M4A/MP4 container. FFmpeg can decode it and AQE can draw its graph. The hidden HTML audio element fails with `MediaError.code === 4` (`MEDIA_ERR_SRC_NOT_SUPPORTED`).

Anki Reviewer playback is not evidence that Qt WebEngine can decode the file. Reviewer turns `[sound:...]` into a bridge command and sends the audio to Anki’s native `av_player`, backed by bundled `mpv`. AQE deliberately removed that native playback path in the HTML-only playback migration.

A real Anki/Qt WebView diagnostic ruled out media delivery and MIME as the cause:

- The M4A request returned HTTP `200` with the complete file.
- Byte-range delivery returned HTTP `206` with a correct `Content-Range`.
- Anki served `.m4a` as `audio/mp4a-latm` on this macOS environment.
- Relabeling the same bytes as `audio/mp4`, `audio/mp4a-latm`, `audio/x-m4a`, `application/octet-stream`, or an unset MIME type still produced error code 4.
- `canPlayType('audio/mp4; codecs="mp4a.40.2"')` returned an empty string.
- An OGG control loaded from the same media server and through the same Blob mechanism reached `readyState === 4`.

The failure is therefore a codec-capability mismatch in the Qt WebEngine/Chromium media pipeline, not a missing file, broken URL, missing byte-range support, or fixable MIME label.

The current tests encode the wrong user-facing contract:

- real M4A E2E expects browser playback to fail;
- acoustic E2E expects that failure to remain silent;
- the frontend reducer test expects any source `audio_error` to become `AQE-MEDIA-002`.

Those tests correctly observe current behavior but must be replaced with tests for truthful classification and explicit recovery.

---

## 2. User Experience Contract

### 2.1 Initial unsupported/decode failure

For a note source that produces native media error code 3 or 4:

> **AQE-PLAYBACK-002:** This audio format cannot be played in Audio Quick Editor. **Help** **Convert to MP3**

The exact localized wording may be polished, but it must communicate that playback compatibility failed. It must not claim that the file is missing.

Use a semantic `<button type="button">` styled like an inline action for **Convert to MP3**. Keep the existing Help link separate. Do not embed HTML in locale strings, use a native `title`, or encode behavior in DOM `dataset` values.

### 2.2 Clicking the action

Clicking **Convert to MP3** must:

1. synchronously enter the existing editor busy state;
2. stop any AQE playback state for the field;
3. send the existing rich command payload:

   ```ts
   {
     command: "aqe:convert",
     fieldOrd,
     sourceFilename,
     overrides: { targetFormat: "mp3" },
   }
   ```

4. run the existing conversion renderer and guarded replacement path;
5. replace the field sound reference with the generated MP3 only after conversion succeeds;
6. redraw the graph for the MP3 and request the existing post-edit autoplay;
7. preserve the configured/default Convert split-button format and current split-button selection.

The recovery action is not “Compress Audio.” It uses standard MP3 conversion quality and semantics. Compress remains a separate user choice.

### 2.3 Successful result

After success:

- the note canonically references the MP3;
- the original source file remains unchanged in Anki media;
- the MP3 is the source for subsequent editing, playback, graphing, sharing, export, and sync;
- post-edit autoplay uses the MP3 through the existing HTML audio state machine;
- the status summary is the normal “Converted audio to MP3” result;
- no proxy cache, hidden playback derivative, native playback process, or new web export exists.

### 2.4 Failure and stale action behavior

- If the source is actually missing, conversion must terminate through the existing missing-media error path. Never manufacture `AQE-MEDIA-002` from a browser `MediaError` alone.
- If FFmpeg cannot decode the source, show the existing coded processing failure and remove the recovery action with the replaced status.
- If the field/source changed after the error was rendered, reject the stale recovery without writing media, changing the note, or adding history.
- If processing is already active, retain the existing busy behavior and do not enqueue a second conversion.
- Double-clicking the action must produce at most one command because busy state is entered synchronously.
- Do not offer “Convert to MP3” for an MP3 source. That would enter the existing same-visible-format no-op and could create a recovery loop. An MP3 playback failure gets the truthful error and Help link without the conversion action.

### 2.5 Other media error codes

| Native media error | Treatment |
| --- | --- |
| `1` aborted | Do not offer conversion; preserve normal cancellation/source-reconfiguration handling. |
| `2` network | Show the generic browser-audio failure; do not imply codec incompatibility or offer conversion. |
| `3` decode | Probe the media route; preserve `AQE-MEDIA-002` for `404`/`410`, otherwise offer MP3 recovery for a canonical non-MP3 source. |
| `4` source unsupported | Probe the media route because Chromium also uses code 4 for HTTP 404; preserve `AQE-MEDIA-002` for `404`/`410`, otherwise offer MP3 recovery for a canonical non-MP3 source. |
| unknown/null | Log it and show the generic browser-audio failure without conversion. |

The filename extension is used only to prevent a same-format MP3 recovery loop. It is not used to decide whether the browser supports a codec. The classification invariant is the native `MediaError.code` plus the failed source's route status; code 4 alone is ambiguous.

---

## 3. Invariants and Non-Goals

### Required invariants

1. Browser playback failure never implies media absence.
2. Conversion never starts without an explicit user click.
3. The recovery action always requests MP3, regardless of configured output format.
4. Normal toolbar Convert behavior remains configuration/split-state driven.
5. The backend revalidates field ordinal and source filename before recovery conversion.
6. Existing processing guards remain responsible for source replacement races after work starts.
7. The original media file is never overwritten or deleted by recovery.
8. Recovery uses normal in-memory and persistent undo history.
9. No native AQE playback path is restored.
10. No transparent proxy, playback cache, add-on web export, or release payload is introduced.
11. Learner recording playback does not receive this recovery action; it is not canonical note media.
12. Multi-field errors and actions remain scoped by field ordinal and source filename.

### Non-goals

- Adding AAC support to Qt WebEngine.
- Changing Anki’s media server MIME map.
- Automatically migrating collections to MP3.
- Automatically converting on note load or Play.
- Deleting orphaned/original media.
- Making every malformed MP3 repairable.
- Restoring the removed native temporary-segment playback architecture.
- Adding a configurable recovery output format.

---

## 4. Architecture

### 4.1 Keep playback and conversion ownership separate

The HTML audio session owns detection and classification:

```text
HTMLAudioElement error
  -> for code 3/4, HEAD the same source route
  -> AudioError(mediaErrorCode, mediaResponseStatus)
  -> failed HTML audio session
  -> typed playback error/recovery descriptor
```

The editor command path owns the user-initiated recovery:

```text
Convert to MP3 button
  -> command-actions.send("aqe:convert", explicit payload)
  -> editor_bridge.handle_payload_command()
  -> editor_conversion.convert_async()
  -> existing guarded special-transform replacement
  -> note/history/graph/post-edit autoplay
```

Do not make the playback reducer render media, call FFmpeg, or mutate the note.

### 4.2 Preserve the native error code and route status

Extend the typed event/state path so the native code and, for code 3/4, the same source route's response status reach the reducer and telemetry. The route probe is diagnostic-only, runs after failure, and must ignore its result if the audio source changes while it is pending.

Recommended shape:

```ts
type HtmlAudioSessionEvent =
  | {
      type: "AudioError";
      reason: "audio_error";
      cursorMs: number;
      mediaErrorCode: number | null;
      mediaResponseStatus: number | null;
    }
  | ...;
```

The failed state should retain both facts for diagnosis. Non-native failures such as play rejection, timeout, or seek failure use `null` for both.

`failedTransition()` should receive failure context, include both facts in `playback.html_failed` telemetry, and pass them to the failure-status decision. Update every real, learner, and test-driver `AudioError` dispatcher so the type remains exhaustive.

### 4.3 Add a new stable error code

Add:

```python
AQE_PLAYBACK_BROWSER_UNSUPPORTED = "AQE-PLAYBACK-002"
```

Do not repurpose `AQE-PLAYBACK-001`; its published meaning is playback-segment preparation failure.

Add the code to the public error catalog/index and create its help page. The page should explain:

- AQE playback uses Qt WebEngine while built-in Reviewer playback may use `mpv`;
- a file may therefore work during normal review but fail inside AQE;
- conversion creates a new MP3 and changes the field reference;
- the original remains in media;
- Undo restores the prior reference and may restore the playback incompatibility;
- processing/runtime troubleshooting steps if conversion fails.

### 4.4 Use an editor-only typed recovery descriptor

Do not extend the general Python/JSON `UserFacingError` contract with arbitrary executable commands. This error originates in the frontend, and serializing commands in general error payloads would unnecessarily enlarge the trust boundary.

Add an editor-only type alongside `EditorStatusMessage`:

```ts
interface ConvertToMp3RecoveryAction {
  kind: "convert_to_mp3";
  fieldOrd: number;
  sourceFilename: string;
}

interface ActionableEditorError extends UserFacingError {
  recovery?: ConvertToMp3RecoveryAction;
}
```

`EditorStatusMessage` remains `string | ActionableEditorError`. Existing Python-originated `UserFacingError` objects remain valid because `recovery` is optional.

The renderer maps the semantic action kind to localized text. It must not accept an arbitrary bridge command from an error object.

### 4.5 Store recovery behavior in typed frontend state

`editor-control-state.ts` remains the behavioral source of truth. The rendered button may have test/CSS attributes, but click handling must read the recovery descriptor from the typed status state rather than reconstructing field/source behavior from DOM data.

Recommended flow:

- `control-status-renderer.ts` renders the code, message, Help link, and semantic button.
- `EditorControls.svelte` handles the bubbled button click at the mounted field controls.
- the handler reads the current typed status/recovery for `target.ord`;
- `command-actions.send()` executes the existing `aqe:convert` command path with the explicit payload.

This avoids a circular import from the status renderer back into command dispatch and keeps all normal busy, playback-stop, processing-message, and post-edit-intent behavior in `send()`.

### 4.6 Support post-edit playback warnings without losing edit success

Format-preserving M4A edits and explicit MP3-to-M4A conversion can succeed and then fail during post-edit autoplay. Preserve the successful edit status and show the recovery action in the separate playback warning area.

Do not overwrite “Converted audio to M4A,” “Increased speed,” or another successful edit status with a claim that the edit failed.

Extend the typed per-field control state with a playback-warning value, or an equivalently typed field-scoped warning store. Render the warning with the same safe semantic recovery descriptor. Clear it when:

- a new source is configured;
- playback succeeds;
- the recovery command starts;
- the editor/note is disposed or replaced.

Do not keep warning behavior solely in `.aqe-playback-warning.textContent` or a module-level DOM flag.

### 4.7 Backend stale-source validation

`EditorCommandPayload` already supports `field_ord`, `source_filename`, and `overrides.target_format`; no new bridge command or communication schema is required.

For recovery payloads, `editor_conversion.convert_async()` must validate before starting work:

- `target_format` is explicitly `mp3`;
- `field_ord` identifies the current requested field after the existing focus bridge step;
- the field still references exactly `source_filename`;
- the resolved current media path belongs to that reference.

Apply this strict precondition only when `source_filename` is supplied. Normal toolbar Convert payloads that omit `source_filename` must retain current behavior.

If validation fails:

- do not render or write media;
- do not mutate the note/session/history;
- clear the frontend busy state;
- show a localized stale-recovery message such as “The audio changed before conversion started. Try playing the current audio again.”

Once rendering begins, reuse the existing `EditorProcessingGuard` and guarded replacement logic. Do not add a second generation/race mechanism.

---

## 5. Cross-Feature Consequences

| Function | Before recovery click | After successful recovery | Undo/redo consequence |
| --- | --- | --- | --- |
| Note sound tag | References original M4A/other source | References generated MP3 | Undo restores old reference; redo restores MP3 |
| Original file | Remains canonical | Remains unchanged in Anki media | Must remain available for history restore |
| Graph | May already render from original through FFmpeg | Redraws from generated MP3 | Redraw follows restored artifact |
| Playback | HTML decoder failure with action | Direct HTML MP3 playback | Undo may return to failure/action; redo returns to direct playback |
| Explicit Convert settings | Existing selected/default format | Unchanged; recovery uses a one-command MP3 override | No settings mutation |
| Format-preserving edits | Can create another unplayable M4A | User may add a later M4A-to-MP3 history step | Undo first returns edited M4A, then earlier source states |
| Convert MP3 to M4A | Edit succeeds; post-edit playback can fail | Warning offers conversion back to MP3 | History remains MP3 -> M4A -> MP3 |
| Compress Audio | Independently creates MP3 | Continues to operate on current MP3 | Existing compression history semantics |
| Share/show/export | Uses original before conversion | Uses canonical MP3 after conversion | Restored reference determines future operation source |
| Sync | No mutation from playback error | Syncs new MP3 plus changed note | Original remains a media item until normal cleanup policy |
| Persistent undo | No new entry for playback failure | Records normal conversion entry | Restarted sessions can restore either artifact |
| Reviewer AQE panel | HTML playback can fail | Conversion updates note and rerenders Reviewer side | Built-in Reviewer native audio remains outside AQE ownership |
| Built-in Reviewer sound button | Continues using Anki/mpv | Plays whichever file the note references | Not modified by AQE playback changes |
| Learner recording | Separate HTML session | No recovery action | No note-media conversion |
| Multi-field editor | Error/action scoped to one field | Only validated field changes | Other field state/history remains untouched |

The playback error itself must never create undo history, modify the note, write media, or affect sync.

---

## 6. File-Level Change Map

### Frontend playback classification

- Modify `settings_ui/src/editor-inline/audio-clock.ts`
  - pass `audio.error?.code ?? null` to the error callback;
  - retain existing structured log fields.
- Modify `settings_ui/src/editor-inline/actions-audio-clock.ts`
  - dispatch `AudioError` with the native code;
  - keep current stale-session checks.
- Modify `settings_ui/src/editor-inline/html-audio-session-types.ts`
  - type the native code on events/failed state/effects as needed;
  - add the narrow recovery descriptor on playback status effects.
- Modify `settings_ui/src/editor-inline/html-audio-session-machine.ts`
  - preserve the code through the failure transition.
- Modify `settings_ui/src/editor-inline/html-audio-session-machine-helpers.ts`
  - remove `audio_error -> AQE-MEDIA-002`;
  - classify code 3/4 non-MP3 canonical sources as `AQE-PLAYBACK-002` with recovery;
  - keep generic behavior for other failures.
- Modify other typed `AudioError` dispatchers, including learner/test-driver adapters, to supply `mediaErrorCode` while never offering canonical conversion for learner recordings.

### Typed status/recovery UI

- Modify `settings_ui/src/editor-inline/editor-control-state.ts`
  - define/store `ActionableEditorError` and `ConvertToMp3RecoveryAction`;
  - add typed field-scoped playback-warning state if required by the chosen projection.
- Modify `settings_ui/src/editor-inline/control-status-renderer.ts`
  - render the action as a semantic button;
  - retain the existing Help link;
  - do not dispatch commands directly.
- Modify `settings_ui/src/editor-inline/EditorControls.svelte`
  - handle status/warning recovery clicks and read the typed action for the mounted field.
- Modify `settings_ui/src/editor-inline/command-actions.ts`
  - expose a small typed recovery executor that calls existing `send()` with the explicit MP3 payload;
  - do not duplicate busy or post-edit setup.
- Modify `settings_ui/src/editor-inline/html-audio-session-controller.ts`
  - build actionable error/warning values from reducer effects;
  - clear stale warnings on successful/reconfigured sessions.
- Modify `settings_ui/src/editor-inline/styles/controls.css`
  - add inline-action and focus-visible styling;
  - keep wrapping usable in narrow editor fields.

### Backend conversion and errors

- Modify `addon/anki_audio_quick_editor/error_codes.py`
  - add `AQE_PLAYBACK_BROWSER_UNSUPPORTED`.
- Modify `addon/anki_audio_quick_editor/editor_conversion.py`
  - recognize a source-bound recovery payload;
  - validate field/source before work;
  - continue through the existing renderer/replacement pipeline.
- Modify `addon/anki_audio_quick_editor/editor_deps_protocols.py` and `editor_dependencies.py` only if the validator needs an existing resolver not already present in `ProcessingDeps`.
- Do not add a new handler to `editor_bridge.py`; `CMD_CONVERT` already accepts a rich payload.
- Do not change the general communication JSON schema unless implementation proves the action must cross from Python to the frontend. If that happens, stop and revisit the trust-boundary decision instead of silently widening it.

### Localization and public help

- Add localized strings for:
  - unsupported/decode playback error;
  - Convert to MP3 action;
  - stale recovery request;
  - post-edit success/playback warning if separate wording is needed.
- Update every locale catalog according to the repository’s locale-key parity rules.
- Add `AQE-PLAYBACK-002` to `docs/errors/error-page.js` and `docs/errors/index.html`.
- Create `docs/errors/AQE-PLAYBACK-002/index.html` using the existing error-page structure.
- Update `docs/architecture/html-audio-observability.md` with the native-code and recovery telemetry contract, without duplicating general logging guidance elsewhere.

---

## 7. Test-First Implementation Tasks

### Task 1: Preserve and classify the native media error code

**Tests first:**

- Modify `settings_ui/tests/html-audio-session-failures.test.ts`:
  - code 4 on non-MP3 canonical source produces `AQE-PLAYBACK-002` and `convert_to_mp3` recovery;
  - code 3 does the same;
  - route status 404/410 preserves `AQE-MEDIA-002` and does not offer conversion;
  - code 1, code 2, and null do not offer conversion;
  - code 4 on `.mp3` does not offer conversion;
  - learner recording never offers note conversion;
  - `AQE-MEDIA-002` is absent from present-route codec failures.
- Modify `settings_ui/tests/html-audio-session-transition-matrix.test.ts` so all typed `AudioError` events include a code/null value.
- Add an audio-clock handler test proving native error code 4 reaches the dispatched event unchanged.
- Add telemetry assertions for `mediaErrorCode`, `mediaResponseStatus`, source kind/filename, and `recoveryOffered`.

Run the focused frontend tests and confirm they fail before implementation.

**Implementation:** update the event, failed state, transition helper, dispatchers, and reducer effects. Keep the change surgical; do not redesign unrelated session states.

### Task 2: Render a safe, typed recovery action

**Tests first:**

- Extend `settings_ui/tests/editor-inline.actions.status.test.ts`:
  - actionable error renders `CODE: message Help Convert to MP3`;
  - Help remains an external URL action;
  - recovery is a `<button type="button">`, not an external link;
  - the button is keyboard-focusable and has visible text;
  - plain `UserFacingError` rendering is unchanged;
  - no native `title` or SVG tooltip is introduced.
- Add typed state tests:
  - stable error restoration retains its recovery descriptor;
  - source replacement/clear removes stale recovery;
  - post-edit playback warning stores recovery separately from successful edit status.
- Add a click-routing integration test proving the handler reads the action from `editor-control-state.ts`, not from behavioral `dataset` fields.

**Implementation:** add the narrow editor-only action type, renderer projection, field-mounted click handler, warning state/projection, and CSS.

### Task 3: Route recovery through the existing conversion command

**Tests first:**

- Add a frontend command integration test asserting exactly one payload:

  ```ts
  {
    command: "aqe:convert",
    fieldOrd: 0,
    sourceFilename: "clip.m4a",
    overrides: { targetFormat: "mp3" },
  }
  ```

- Configure the split-button/default format as FLAC or M4A and prove recovery still requests MP3 without mutating split state.
- Double-click the action and prove only one bridge command is emitted.
- Prove the action uses normal conversion busy text and post-edit intent.
- Prove an unrelated field’s action carries that field’s ordinal and source.

**Implementation:** call the existing `send()` path. Do not call `focusAndSendCommandPayload()` directly from the renderer, because that would bypass normal command lifecycle behavior.

### Task 4: Add authoritative stale-source validation

**Tests first in `tests/test_editor_convert_callbacks.py`:**

- matching `fieldOrd`/`sourceFilename` converts to MP3 even when config output is FLAC;
- settings/default output remains unchanged;
- mismatched source filename writes no file, changes no field, adds no history, and clears busy state;
- mismatched field ordinal has the same no-mutation behavior;
- a source replacement after the worker starts remains rejected by the existing processing guard;
- a missing matching source reports the existing missing-media error;
- FFmpeg failure reports the existing processing error and does not replace the note;
- normal toolbar Convert without `sourceFilename` retains current behavior;
- existing same-format toolbar no-op behavior remains unchanged.

Add/adjust pure command/status tests so a recovery conversion records the normal “Converted audio to MP3” summary.

**Implementation:** add the preflight validation to `convert_async()` and reuse `run_special_audio_transform_async()`. Do not fork the renderer, replacement callback, or history writer.

### Task 5: Verify history and operation interactions

Add integration tests for these state sequences:

1. **M4A -> recovery MP3 -> undo -> redo**
   - MP3 conversion adds one normal history entry;
   - undo restores M4A and its playback incompatibility/action;
   - redo restores MP3 and direct playback.
2. **Original M4A -> format-preserving M4A edit -> recovery MP3**
   - first undo restores the edited M4A;
   - second undo restores the original M4A;
   - neither original nor edited artifact is confused with the MP3.
3. **MP3 -> explicit M4A -> recovery MP3**
   - the M4A edit succeeds even though post-edit autoplay fails;
   - the warning offers recovery without overwriting the successful edit status;
   - history is MP3 -> M4A -> MP3.
4. **Recovery MP3 -> Compress Audio**
   - compression operates on the current MP3 and creates its own history entry;
   - recovery does not change compression defaults.
5. **Share/show/export before and after recovery**
   - before click, operations resolve the original source;
   - after success, they resolve the canonical MP3;
   - no hidden derivative path is exposed.
6. **Persistent undo across restart/reopen**
   - the stored conversion entry restores exact old/new filenames and field HTML.
7. **Reviewer adapter**
   - recovery updates the note and rerenders the current Reviewer side through the existing adapter;
   - AQE does not call native `av_player`;
   - built-in Reviewer playback remains outside this feature.

Prefer extending existing history, sharing, conversion, and Reviewer test files instead of creating parallel helpers.

### Task 6: Real Anki and acoustic E2E

Playback correctness depends on emitted audio, so follow Rule 36 and `docs/architecture/html-audio-observability.md`.

Replace the negative-only M4A acceptance test with real recovery coverage:

- open the real addressable AAC-LC M4A fixture in a real Anki editor WebView;
- verify graph rendering succeeds from the M4A;
- verify HTML audio fails with native code 4;
- verify the visible status is `AQE-PLAYBACK-002`, not `AQE-MEDIA-002`;
- verify **Convert to MP3** is visible;
- capture the initial failed playback interval and assert silence/no stale output;
- click the recovery action through a trusted pointer gesture;
- wait for a new `.mp3` note reference and on-disk media file;
- prove the original M4A bytes are unchanged;
- verify configured output format/split state was not changed;
- verify graph source identity moves to the generated MP3;
- verify post-edit playback emits the expected addressable PCM interval;
- verify there is no native playback attempt, overlap, old-source leak, or output after stop.

Add focused real-Anki cases for:

- undo to M4A restores the error/action and remains silent;
- redo to MP3 restores audible playback;
- format-preserving M4A edit followed by recovery;
- MP3-to-M4A conversion followed by recovery from the post-edit warning;
- source/note replacement before recovery click does not convert stale media;
- Reviewer AQE panel recovery smoke test;
- multi-field recovery changes only the targeted field;
- a normal MP3, WAV, and OGG never shows the recovery action;
- conversion failure replaces the recovery status with a truthful coded processing error and does not loop.

Name emitted-audio tests with `audible`, `acoustic`, or `emitted_pcm`, use real WebView PCM capture, and evaluate with the independent oracle.

### Task 7: Architecture guards and documentation

- Keep Rule 37’s no-native-playback guarantee passing.
- Extend frontend architecture coverage so:
  - recovery supports only the semantic `convert_to_mp3` action;
  - status actions cannot carry arbitrary bridge commands;
  - behavioral recovery identity is read from typed state, not DOM `dataset`;
  - no proxy/cache/web-export path is introduced.
- Update the playback observability document with:
  - native media error code logging;
  - recovery-offered and recovery-clicked events;
  - stale-source rejection context;
  - required acoustic assertion after conversion.
- Update the public error documentation and locale catalogs.
- Run `$doc-maintain` after implementation because this changes the documented HTML playback/error-recovery contract.
- Regenerate the architecture archive with:

  ```bash
  python3 scripts/dev.py graphs-archive
  ```

---

## 8. Logging and Diagnostics

Add low-frequency structured logs at these boundaries:

- `audio_clock.error`: retain `errorCode`, `mediaResponseStatus`, source, field, readiness state;
- `playback.html_failed`: add `mediaErrorCode`, `mediaResponseStatus`, `sourceKind`, `sourceFilename`, and `recoveryOffered`;
- recovery click: field ordinal, source filename, target format `mp3`;
- stale recovery rejection: requested and current field/source identities;
- conversion start/success/failure: reuse existing operation logs and operation IDs.

Do not log audio bytes, per-frame progress, or high-frequency cursor events. Do not log a missing-file claim unless the backend actually resolves the media as missing.

---

## 9. Verification Commands

Run focused tests after each task. Before declaring the feature complete, run:

```bash
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e-parallel
```

Use serial E2E only to diagnose a suspected parallel-harness issue or to confirm a failure that is timing-sensitive:

```bash
python3 scripts/dev.py test-e2e
```

Also run the Anki API compatibility gate if the final implementation changes any Anki-facing adapter or bridge dependency surface:

```bash
python3 scripts/dev.py test-anki-api
```

The feature is incomplete if only reducer/DOM tests pass. The real M4A recovery must finish with independently verified emitted PCM from the generated MP3.

---

## 10. Completion Criteria

- [ ] A real AAC-LC M4A that fails in Qt WebEngine shows `AQE-PLAYBACK-002` and **Convert to MP3**.
- [ ] A missing route (`404`/`410`) remains `AQE-MEDIA-002` and never offers conversion.
- [ ] Clicking the action invokes existing `aqe:convert` with an explicit MP3 override.
- [ ] Configured Convert defaults and split-button state are unchanged.
- [ ] The backend rejects stale field/source actions without mutation.
- [ ] Successful recovery creates a normal MP3 edit/history entry and post-edit autoplay.
- [ ] Undo/redo and persistent undo restore exact M4A/MP3 identities.
- [ ] Format-preserving edits, explicit conversion, compression, graphing, sharing, showing, export, sync, and Reviewer behavior match the impact table.
- [ ] The original media is unchanged and no proxy/native playback path exists.
- [ ] MP3 failures cannot loop through same-format recovery.
- [ ] Missing/corrupt/conversion failures surface truthful backend errors.
- [ ] Real acoustic E2E proves initial silence and correct MP3 output without overlap or stale audio.
- [ ] `python3 scripts/dev.py check` passes.
- [ ] `python3 scripts/dev.py test-e2e-parallel` passes.
- [ ] Documentation maintenance and architecture archive regeneration are complete.
