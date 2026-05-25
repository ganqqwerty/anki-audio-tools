# Editor Modification Button Behavior Rules

This document is the shared behavior contract for inline editor buttons that modify an audio field. It applies to any command that creates, restores, or selects a generated audio file and replaces the field's supported `[sound:...]` reference.

Ground truth for this document is the current toolbar registry in `settings_ui/src/lib/editor-toolbar-buttons.ts`, editor dispatch in `settings_ui/src/editor-inline/` and `addon/anki_audio_quick_editor/editor_*.py`, shared operation definitions in `audio_operations.py`, and the editor e2e tests under `e2e/`.

Available editor button commands are not the same as default-visible commands. The default config currently shows Play, Graph, Folder, Share, Shorten Pauses, Denoise, Slower, Faster, Undo, Redo, and Settings. Convert, Pitch Hum, Volume -, Volume +, Record, and Play yours are available toolbar commands but are hidden by the default `visible_editor_buttons` list unless the user enables them.

## Current Command Inventory

| Category | Commands | Contract status |
|----------|----------|-----------------|
| Generated-file modification commands | `aqe:convert`, `aqe:remove-pauses`, `aqe:denoise-standard`, `aqe:rnnoise`, `aqe:dpdfnet`, `aqe:voice-only`, `aqe:pitch-hum`, `aqe:slower`, `aqe:faster`, `aqe:volume-down`, `aqe:volume-up`, `aqe:delete-selection`, `aqe:delete-rest` | Covered by this document, except explicit no-op cases such as same-format Convert. |
| Generated-file history commands | `aqe:undo`, `aqe:redo` | Covered by this document where they restore/select generated media instead of rendering a new file. |
| Non-mutating split buttons | `aqe:play`, `aqe:analyze`, `aqe:record-voice`, `aqe:share` | Not covered by the modification contract; see "Buttons Outside Or Diverging From This Contract". |
| Non-mutating plain buttons | `aqe:play-recording`, `aqe:show-file`, `aqe:settings` | Not covered by the modification contract. |
| Recording lifecycle bridge commands | `aqe:stop-recording` | Not a standalone visible button. It is dispatched by the Record split button primary segment while a learner recording is active. |
| Internal bridge commands | `aqe:command-payload`, `aqe:save-split-defaults`, `aqe:analyze-field`, `aqe:set-cursor`, `aqe:play-ended`, `aqe:frontend-log`, `aqe:scan` | Not buttons. They are bridge plumbing and must not be documented as user-facing modification commands. |

`aqe:rnnoise`, `aqe:dpdfnet`, and `aqe:voice-only` are command payload variants selected from the Denoise split menu. They are not separate top-level toolbar buttons in the current UI.

## Button Shape

Every modification command with user-tunable per-action parameters must be a split button.

- The primary segment runs the command immediately with the current field-local quick setting.
- The secondary segment opens split-button quick settings for that command.
- Truly parameterless commands may remain plain buttons, but generated-file modification commands still follow the non-destructive, history, busy-state, playback, progress, and selection rules in this document.
- Split-button quick settings are field-local. Changing a value for field 0 must not change the value for field 1.
- Repeated primary clicks reuse the current field-local quick setting.
- Only one split quick-settings popover may be open at a time.
- A popover closes on outside click, Escape, opening another popover, or dispatching a command.
- Popover values must be clamped or validated at the frontend boundary and validated again at the Python command boundary.

Current split-button shapes:

| Shape | Commands |
|-------|----------|
| Individual split buttons | `aqe:play`, `aqe:analyze`, `aqe:record-voice`, `aqe:share`, `aqe:convert`, `aqe:remove-pauses`, `aqe:denoise-standard`, `aqe:pitch-hum` |
| Grouped split buttons | `aqe:slower` + `aqe:faster` share one Speed quick-settings menu; `aqe:volume-down` + `aqe:volume-up` share one Volume quick-settings menu. |
| Plain modification buttons | `aqe:delete-selection`, `aqe:delete-rest`, `aqe:undo`, `aqe:redo` |

`aqe:delete-selection` and `aqe:delete-rest` are selection-toolbar actions backed by a pending region-delete request. `aqe:delete-selection` can also be triggered from Backspace when the focused graph has a valid non-whole-clip selection.

## Settings Defaults

Every split quick setting must have a Settings default unless it is explicitly documented as a field-local-only choice.

- Settings values initialize split-button quick settings when editor controls are created or refreshed.
- Field-local quick setting changes never write back to persisted settings unless the user clicks the promote-default control.
- Changing Settings updates unedited field-local values when practical, but it must not overwrite a value the user already changed in that editor field.
- Most split defaults are injected through `window.__AQE_EDITOR_CONFIG__.splitButtonDefaults`; `repeatPlaybackByDefault` is injected as a top-level editor runtime flag.
- Python config schema, generated contracts, Settings UI, and editor runtime config must stay in sync for every persisted default.

Current split-button defaults include:

| Quick setting | Default source |
|---------------|----------------|
| Play repeat enabled | `repeat_playback_by_default` |
| Play repeat pause | `repeat_pause_seconds` |
| Share target | `share_target` |
| Graph voice range | `graph_voice_range` |
| Graph recording condition | `graph_recording_condition` |
| Graph smoothness | `graph_smoothness` |
| Graph short-dropout connection | `graph_connect_short_dropouts_ms` |
| Graph voice lock | `graph_voice_lock` |
| Volume step | `volume_step_db` |
| Speed step | `speed_step` |
| Shorten Pauses aggressiveness | `pause_aggressiveness` |
| Denoise algorithm | `denoise_algorithm` |
| DPDFNet aggressiveness | `dpdfnet_attn_limit_db` |
| Convert output format | `output_format` |
| Pitch Hum mode | `pitch_hum_mode` |
| Voice recording countdown | `voice_recording_countdown_seconds` |

Share target is persisted as a Settings default. The Share split menu initializes from `share_target`, lets the user pick Catbox or Litterbox locally per field, and exposes the same promote-default control as other split buttons.

## Editor And Batch Parity

Batch-capable behavior must be introduced as a shared import-safe operation before it is wired into either the editor bridge or Browser batch dialog.

Current shared batch/editor operations:

| Shared operation | Editor command surface | Batch operation |
|------------------|------------------------|-----------------|
| Convert | `aqe:convert` with `targetFormat` | `convert` with `target_format` |
| Denoise | Denoise split menu dispatching `aqe:denoise-standard`, `aqe:rnnoise`, `aqe:dpdfnet`, or `aqe:voice-only` | `denoise` with `denoise_algorithm` and optional `dpdfnet_attn_limit_db` |
| Shorten Pauses | `aqe:remove-pauses` with `pauseAggressiveness` | `remove_pauses` with `pause_aggressiveness` |
| Speed | `aqe:slower`, `aqe:faster` with `speedStep` | `slower`, `faster` with `speed_step` |
| Volume | `aqe:volume-down`, `aqe:volume-up` with `volumeStepDb` | `volume_down`, `volume_up` with `volume_step_db` |
| Graph | `aqe:analyze` with graph settings | `graph` appends an SVG to a target field |

Editor-only behavior:

- `aqe:pitch-hum`, `aqe:delete-selection`, `aqe:delete-rest`, `aqe:undo`, and `aqe:redo` are editor-only today.
- `aqe:play`, `aqe:record-voice`, `aqe:stop-recording`, `aqe:play-recording`, `aqe:share`, `aqe:show-file`, and `aqe:settings` are not batch operations.
- Selection-sensitive region deletion must not be added to Browser batch without a separate design, because it depends on editor graph selection state.

## Non-Destructive Media

Modification buttons must never overwrite or delete the source media file.

- A successful modification renders a new media file.
- The field's first supported `[sound:...]` reference is replaced with the generated filename.
- The original media file remains available in Anki media.
- Generated files used by undo and redo remain available; cleanup must not break history.
- Temporary working files may be deleted after success or failure when they are not user-facing artifacts.
- Failure must leave the note field and current audio reference unchanged.
- Convert to the same visible format is an accepted no-op: it does not render, write media, replace the field, push history, or trigger post-edit playback.

## Undo And Redo

Every successful modification must be reversible through the editor undo/redo buttons.

- A new successful modification pushes the previous edit state and current filename onto undo history.
- A new successful modification clears redo history.
- Undo restores the previous generated reference and pushes the current reference to redo history.
- Redo restores the next generated reference and pushes the current reference back to undo history.
- Undo and redo are disabled by behavior, not necessarily by visual state, while processing is busy: they must report the current processing state and avoid changing the field.
- Undo and redo should trigger the same post-replacement playback, progress, graph, and selection behavior as a newly rendered modification.

## Field Targeting

Modification buttons operate on one editor field at a time.

- The target field is the active field ordinal carried by the editor control or command payload.
- Multi-field notes must keep command state, split quick settings, playback, graph state, and generated media replacement isolated by field.
- A command must not update another field if focus changed, the requested field is stale, or the referenced source filename no longer matches the control state.
- Commands that depend on the graph selection must validate that the selected region belongs to the current field and current source filename.

## Busy State And Progress

Only one modification may process at a time.

- Dispatch is ignored or rejected while any editor operation is busy.
- Accepted processing stops existing editor playback before work starts.
- All editor controls are disabled while processing is busy.
- The active field shows a processing status; if the ffmpeg command is configured to be visible, it appears as status detail/title text rather than replacing the behavior contract.
- The visual progress indicator must not continue animating against an old file while processing runs.
- On success, playback state is set to stopped at the start of the generated file or effective playback region before post-edit playback starts.
- On failure, busy state is cleared, an error or warning status is shown, and stale playback/progress must not resume automatically.

## Post-Modification Playback

A successful modification should play the new audio reference automatically.

- Playback starts only after the field has been reloaded and the new controls can find the generated media reference.
- Playback uses the new file, not the previous source.
- Playback starts from the effective playback region start. After a normal generated-file replacement, this is usually `0 ms`.
- Repeat enabled state and repeat pause seconds are preserved from the field at dispatch time.
- If another edit finishes first, older scheduled post-edit playback attempts must not start.
- If playback cannot start because the frontend is not ready, retry briefly. If it still cannot start, leave the field in a stopped, usable state.
- Failed or rejected modifications must not trigger post-edit playback.

## Selection After Modification

Selections from the old audio must not survive as stale ranges on a generated file.

- Draft selections are always cleared when a modification starts or a graph is reset.
- After a successful generated-file replacement, cursor, progress, and selection state reset to the generated file, not the old duration.
- If the graph is redrawn for the new file, the default committed selection is the full new duration.
- If the graph is not active, there is no visible selection after the field reload.
- Region commands consume their selected range. After delete-selection or delete-rest succeeds, the previous selected interval is cleared and any new selection must come from the regenerated graph.
- Future commands that intentionally preserve or remap a selection must document that rule and cover duration changes, clipped ranges, and invalid remaps with tests.

## Graph Behavior

Modification buttons must keep graph state consistent with the generated audio.

- In-flight graph analysis for the affected field is canceled or ignored when modification processing starts.
- If a graph was active before a successful modification, it is redrawn for the generated file.
- If a graph was not active, the modification should not force a graph open unless the command specifically requires graph state.
- Graph redraw must clear stale track data before analysis and must not show old pitch/intensity data for a new file.

## Errors And Rejections

Rejected commands and failed renders must be predictable.

- Missing source media, missing supported sound references, stale field/source mismatches, invalid selections, missing binaries, and renderer failures must leave the note unchanged.
- User-correctable precondition failures should produce warning or error status text on the active field.
- Invalid quick-setting payload values should be clamped or ignored in favor of validated defaults where that is safer than failing the command.
- Commands that would delete or keep the whole clip by accident must be rejected with a warning.
- Failures must clear busy state and must not push undo history.

## Buttons Outside Or Diverging From This Contract

These buttons are current UI surfaces that do not fully follow this modification-button contract. The divergence is intentional unless noted otherwise.

| Button | Current behavior | Why it does not follow this contract |
|--------|------------------|--------------------------------------|
| `aqe:play` | Split button for playback and repeat settings. It may use the current selection region and repeat pause values. | It does not render, replace media, write history, or update note fields. |
| `aqe:analyze` | Split button for graph/prosody settings. It analyzes the current audio and renders an inline graph; Browser batch `graph` appends an SVG to a target field. | Editor Graph is analysis state, not a generated-audio modification. It does not replace the field's sound reference or push undo/redo history. |
| `aqe:record-voice` / `aqe:stop-recording` | Record is an opt-in icon-only split button for learner voice capture. It requires an existing target graph, stops target playback, clears any old learner overlay, shows the configured countdown, starts native recording, and toggles the primary action to Stop while recording. Stop finalizes the learner attempt, analyzes it, and overlays learner pitch only. | It creates sidecar learner media and analysis state for comparison, but intentionally does not replace the note field's sound reference, push undo/redo history, or trigger post-modification playback. |
| `aqe:play-recording` | Opt-in icon-only button grouped next to Record. It plays the latest ready learner recording through native playback and is disabled until a learner attempt is ready. | It plays sidecar learner media only. It does not render new target media, replace fields, write history, or update note data. |
| `aqe:share` | Split button for Catbox/Litterbox upload. It uploads the current audio, copies a URL, keeps the note unchanged, initializes from the `share_target` Settings default, and can promote the field-local target to the default. | It has field-local quick settings and busy state, but it intentionally does not create generated media or mutate the note. |
| `aqe:show-file` | Opens/reveals the current media file through the OS. | It has an external shell/file-manager side effect but no audio rendering, field replacement, or history behavior. |
| `aqe:settings` | Opens the add-on Settings dialog. | It configures defaults and toolbar visibility, but it is not an audio-field modification. |
| `aqe:convert` same-format request | Reports that the file is already in the target format and leaves the note unchanged. | This is an accepted no-op path for a modification button, so the normal render/replace/history/playback rules do not run. |

If a future non-mutating button uses split-button quick settings, document it here instead of forcing it into the generated-file modification rules.

## Architecture Rules

The implementation must keep existing layer boundaries.

- `settings_ui/src/editor-inline/` owns split-button rendering, field-local quick setting state, command payload creation, playback/progress UI state, and selection UI state.
- `editor_actions.py` owns import-safe command decoding and mapping from editor bridge commands to shared operation semantics.
- `audio_state.py`, `audio_operations.py`, and import-safe helpers own pure audio edit semantics.
- `audio_processor.py` owns rendering side effects and external tool execution.
- `editor_integration.py` and related editor adapter modules own Anki editor coordination, media writes, field replacement, task scheduling, status evaluation, and playback requests.
- Settings backend modules own persisted defaults and must not import editor runtime state.
- Browser batch operations must share operation semantics where relevant, but must not depend on editor split-button payloads or editor-only UI state.
- Share/upload, file reveal, settings, playback, and graph analysis each have their own adapter modules and must not be routed through generated-file render helpers just to reuse modification-button machinery.

## Test Requirements For New Modification Buttons

Every new or changed modification button needs tests proportional to its risk.

- Unit tests for command decoding, parameter validation, fallback behavior, and pure state changes.
- Frontend tests for split-button default initialization, field-local overrides, repeated clicks, popover close behavior, and busy-state blocking.
- Integration tests for command payload shape through Python command handling.
- E2E tests with real processing binaries for at least one successful render path when the command changes audio.
- E2E tests proving the original field reference is replaced only after success and unchanged on failure.
- E2E or integration tests for undo, redo, post-edit playback, progress reset, and multi-field isolation.
- Selection-sensitive commands need tests for stale source rejection, invalid ranges, whole-clip rejection, and post-success selection reset.
- Batch-capable commands need shared operation tests plus Browser batch tests proving the same defaults and operation-local overrides are used outside the editor.

Current e2e behavior references:

| Behavior area | Primary coverage |
|---------------|------------------|
| Standard generated-file edits, ffmpeg status, undo/redo | `e2e/test_editor_processing_workflow.py` |
| Split-button defaults, local overrides, save-default behavior | `e2e/test_editor_processing_split_buttons_workflow.py`, `e2e/test_editor_processing_split_buttons_parameter_workflow.py`, `settings_ui/tests/editor-inline.command-splits.integration.test.ts` |
| Busy locking and mid-render undo rejection | `e2e/test_editor_processing_busy_workflow.py` |
| Denoise and special transform success/failure | `e2e/test_editor_deep_filter_workflow.py`, `e2e/test_editor_deep_filter_failure_workflow.py`, `e2e/test_dpdfnet_attenuation_integration.py`, `e2e/test_editor_status_operation_variants_workflow.py` |
| Region delete and delete-rest | `e2e/test_editor_region_delete_workflow.py`, `e2e/test_editor_region_resize_workflow.py`, `settings_ui/tests/editor-inline.selection-delete.integration.test.ts` |
| Graph redraw after edits and graph parameter behavior | `e2e/test_editor_graph_visualizer_workflow.py`, `e2e/test_editor_graph_visualizer_edges_workflow.py`, `e2e/test_editor_graph_parameters_workflow.py` |
| Playback, repeat, and post-edit playback | `e2e/test_editor_playback_workflow.py`, `e2e/test_editor_region_loop_playback_workflow.py`, `settings_ui/tests/editor-inline.post-edit-playback.integration.test.ts` |
| Learner recording comparison | `e2e/test_editor_voice_recording_comparison_workflow.py`, `settings_ui/tests/editor-inline.recording.integration.test.ts`, `tests/test_audio_recording.py`, `tests/test_editor_recording.py`, `tests/test_editor_recording_state.py` |
| Share non-mutation and per-field target state | `e2e/test_editor_share_workflow.py`, `settings_ui/tests/editor-inline.command-splits.integration.test.ts` |

## New Button Checklist

Before a modification button is considered complete:

- It has the right button shape: split button when parameterized, plain button only when truly parameterless.
- Its quick settings are field-local and initialized from Settings defaults.
- Its Settings defaults are schema-backed and injected into editor runtime config.
- It creates a new media file and never mutates the original source file.
- It replaces only the intended field's first supported sound reference.
- It pushes undo history on success and clears redo history.
- It blocks duplicate processing while busy.
- It stops stale playback/progress on dispatch.
- It plays the generated file after success.
- It resets stale selection state after success.
- It redraws graph state only when graph state was active or required.
- It leaves the note unchanged on failure.
- It has shared batch semantics before Browser batch support is exposed, or it is explicitly documented as editor-only.
- Any intentional no-op or non-mutating behavior is documented in "Buttons Outside Or Diverging From This Contract".
- It has focused unit, frontend, integration, and E2E coverage for the behavior above.
