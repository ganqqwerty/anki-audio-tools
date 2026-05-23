# Settings Buttons And Diagnostics Redesign

Date: 2026-05-24
Status: Proposed

## Goal

Reshape the Settings UI so button configuration is easier to understand from the same mental model as the editor toolbar, while also cleaning up diagnostics-related settings and removing the obsolete DeepFilterNet path override.

## Scope

This design covers:

- moving `Enable debug logging` and `Show ffmpeg commands while processing` to the Diagnostics tab
- redesigning the button settings into a dedicated `Buttons` section
- grouping button-specific behavior defaults with the matching button visibility/display controls
- changing default button visibility and display modes
- removing `deep_filter_path` from the supported settings surface
- changing `ffmpeg_path` defaults to real per-platform values

This design does not cover:

- a config migration path for existing users
- embedding or reusing the live editor toolbar component directly inside Settings
- changing the runtime processing behavior other than default config values and path resolution defaults

## User-Facing Outcome

The Settings dialog should feel closer to the editor experience without pretending to be the editor itself.

The new structure should let a user answer these questions quickly:

- Is this button shown at all?
- If it is shown, is it icon-only or text-only?
- What behavior defaults apply when I use this button?

The answer for each button should live in one place.

## Information Architecture

The Settings dialog keeps two tabs:

- `General`
- `Diagnostics`

### General tab

The General tab keeps non-diagnostic editing defaults, but the toolbar configuration becomes a first-class `Buttons` section.

Recommended section order:

1. playback defaults and general editor defaults
2. `Buttons`
3. any remaining non-button processing defaults that do not belong to a single button card

### Diagnostics tab

The Diagnostics tab contains:

- `Enable debug logging`
- `Show ffmpeg commands while processing`
- existing health-check and support-report actions
- existing diagnostics metadata and log-file actions

## Buttons Section

The `Buttons` section is a normal settings form, not a live toolbar simulator.

Its visual language should echo the editor popover panels:

- rounded cards
- segmented choice controls styled like the editor option pills
- matching icons and labels for editor commands
- compact vertical grouping, where display settings appear before button-specific defaults

### Button card model

Each command gets one card.

Each card contains, in this order:

1. command name and icon
2. visibility control: `Shown` or `Hidden`
3. display mode control: `Icon only` or `Text only`
4. button-specific defaults, if that command has any

Commands with no extra behavior settings only show items 1-3.

### Button-specific grouping

The cards should group behavior defaults like this:

- `Play`
  - shown/hidden
  - icon-only/text-only
  - repeat playback by default
  - repeat pause seconds

- `Graph`
  - shown/hidden
  - icon-only/text-only
  - speaker voice
  - recording condition
  - voice lock
  - smoothness
  - connect short dropouts

- `Convert`
  - shown/hidden
  - icon-only/text-only
  - default output format

- `Shorten Pauses`
  - shown/hidden
  - icon-only/text-only
  - silence threshold
  - pause threshold
  - target gap
  - pause aggressiveness

- `Denoise`
  - shown/hidden
  - icon-only/text-only
  - default denoise algorithm
  - DPDFNet aggressiveness
  - DeepFilterNet post-filter

- `Pitch hum`
  - shown/hidden
  - icon-only/text-only
  - pitch hum mode

- `Slower`
  - shown/hidden
  - icon-only/text-only
  - speed step
  - min speed

- `Faster`
  - shown/hidden
  - icon-only/text-only
  - speed step
  - max speed

- `Volume -`
  - shown/hidden
  - icon-only/text-only
  - volume step
  - min volume

- `Volume +`
  - shown/hidden
  - icon-only/text-only
  - volume step
  - max volume

- `Folder`
  - shown/hidden
  - icon-only/text-only

- `Share`
  - shown/hidden
  - icon-only/text-only

- `Undo`
  - shown/hidden
  - icon-only/text-only

- `Redo`
  - shown/hidden
  - icon-only/text-only

- `Settings`
  - shown/hidden
  - icon-only/text-only

### Why this structure

This is intentionally not a separate “visibility matrix plus advanced defaults elsewhere.”

The point of the redesign is to keep a button’s presentation and a button’s behavior defaults together, because the user thinks about them together from the editor toolbar.

## Default Button Configuration

The new default visibility and display mode should be:

- `Play`: shown, icon-only
- `Graph`: shown, icon-only
- `Folder`: shown, icon-only
- `Share`: shown, icon-only
- `Convert`: hidden, text-only
- `Shorten Pauses`: shown, text-only
- `Denoise`: shown, text-only
- `Pitch hum`: hidden, text-only
- `Slower`: shown, icon-only
- `Faster`: shown, icon-only
- `Volume -`: hidden, icon-only
- `Volume +`: hidden, icon-only
- `Undo`: shown, icon-only
- `Redo`: shown, icon-only
- `Settings`: shown, icon-only

Only the visibility list determines whether a button is shown. Hidden buttons still keep a default display mode in config so the mode remains deterministic if later enabled.

## Config Model

Keep the existing flat config shape where practical.

Do not introduce a new nested per-button config object for this redesign.

Rationale:

- the current config shape is already wired through Python, schema validation, frontend state, contracts, and tests
- the grouping problem is a UI composition problem, not a storage-model problem
- a nested refactor would add broad churn without user benefit

### Config changes

Supported config keys after the redesign:

- keep `visible_editor_buttons`
- keep `editor_button_modes`
- keep all button-behavior defaults that already exist
- keep `ffmpeg_path`
- remove `deep_filter_path`

`deep_filter_path` is no longer user-configurable through Settings and no longer part of the supported config contract.

## Path Defaults

### ffmpeg path

`ffmpeg_path` should default to a real per-platform value, not an empty string.

Design requirement:

- macOS default should be a concrete path that makes sense on this machine class, expected to be `/opt/homebrew/bin/ffmpeg`
- Linux default should be a sensible command/path default for typical installs
- Windows default should be a sensible command/path default for typical installs

The exact non-macOS defaults can be finalized during implementation, but they must be persisted as real defaults and not presented only as placeholders.

Reset-to-default behavior should restore the real platform default.

### DeepFilterNet path

Remove the setting entirely.

Runtime resolution should rely on the existing non-user-configured discovery path:

- bundled binary when available
- otherwise `PATH`

## No Migration

There is no migration work in scope.

Assumption accepted by user:

- there are no existing users whose saved config must be preserved

Consequences:

- no config-version migration logic is required for this redesign
- no backward-compatibility handling for `deep_filter_path`
- no old-shape fixture preservation for tests beyond what is required by unrelated coverage

Implementation can update the canonical supported config and tests directly.

## Implementation Areas

Expected code areas:

- [settings_ui/src/settings/GeneralSettingsPanel.svelte](/Users/iuriikatkov/IdeaProjects/anki-audio-tools/settings_ui/src/settings/GeneralSettingsPanel.svelte)
- [settings_ui/src/settings/DiagnosticsPanel.svelte](/Users/iuriikatkov/IdeaProjects/anki-audio-tools/settings_ui/src/settings/DiagnosticsPanel.svelte)
- [settings_ui/src/settings/ToolbarVisibilitySettings.svelte](/Users/iuriikatkov/IdeaProjects/anki-audio-tools/settings_ui/src/settings/ToolbarVisibilitySettings.svelte)
- [settings_ui/src/settings/settings-state.ts](/Users/iuriikatkov/IdeaProjects/anki-audio-tools/settings_ui/src/settings/settings-state.ts)
- [settings_ui/src/lib/editor-toolbar-buttons.ts](/Users/iuriikatkov/IdeaProjects/anki-audio-tools/settings_ui/src/lib/editor-toolbar-buttons.ts)
- [settings_ui/src/lib/i18n.ts](/Users/iuriikatkov/IdeaProjects/anki-audio-tools/settings_ui/src/lib/i18n.ts)
- [addon/anki_audio_quick_editor/config.schema.json](/Users/iuriikatkov/IdeaProjects/anki-audio-tools/addon/anki_audio_quick_editor/config.schema.json)
- [addon/anki_audio_quick_editor/config.json](/Users/iuriikatkov/IdeaProjects/anki-audio-tools/addon/anki_audio_quick_editor/config.json)
- settings/initial-state and save/load code in the Python runtime
- tests for settings state, settings commands, config defaults, schema, and Svelte UI behavior

## Verification Strategy

Before calling the implementation done, verify:

1. Schema and contracts
   - `python3 scripts/dev.py config-schema`
   - `python3 scripts/dev.py contracts-generate`
   - `python3 scripts/dev.py contracts-check`

2. Automated tests
   - `python3 scripts/dev.py test`
   - `python3 scripts/dev.py test-svelte`

3. End-to-end behavior
   - `python3 scripts/dev.py test-e2e`

## Risks And Non-Goals

Risks:

- the new `Buttons` section can become visually crowded if every card expands fully at once
- regrouping existing fields can break tests that assume current DOM structure or old labels
- removing `deep_filter_path` may expose hidden assumptions in diagnostics or support-report code

Non-goals:

- redesigning the editor toolbar itself
- changing command semantics
- creating a fully interactive toolbar preview inside Settings

## Recommendation

Implement the redesign as an editor-styled per-button settings list.

That is the best tradeoff between clarity and implementation cost:

- clearer mental model than the current mixed form
- closer to the editor panel without coupling Settings to editor runtime UI
- less custom behavior than a toolbar-preview-driven configurator
