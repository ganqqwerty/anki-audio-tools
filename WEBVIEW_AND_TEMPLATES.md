# WebView & Templates

## Frontend Bundles

The frontend source keeps two committed webview bundles:

- settings source: `settings_ui/src/App.svelte`, `settings_ui/src/main.ts`, and shared `settings_ui/src/lib/`
- output: `addon/anki_audio_quick_editor/templates/settings/settings_bundle.{js,css}`
- inline editor source: `settings_ui/src/editor-inline/` and shared `settings_ui/src/lib/`
- output: `addon/anki_audio_quick_editor/templates/editor/editor_bundle.{js,css}`

No Browser batch-visualization template is bundled. That workflow uses a native Qt dialog from `browser_integration.py`.

Rebuild it with:

```bash
python3 scripts/dev.py build
```

Frontend-dependent test commands also build before they run. `python3 scripts/dev.py test-svelte` rebuilds before validation, and `python3 scripts/dev.py test-e2e` rebuilds before launching Anki e2e tests.

This build step is not optional for runtime verification. The Anki editor and settings dialogs load only the committed files in `addon/anki_audio_quick_editor/templates/`; they do not load Vite source files or a dev server. If e2e behavior does not match a TypeScript/Svelte edit, check whether the committed bundle changed and whether the test was run through `scripts/dev.py`.

After running `check`, `test-svelte`, or `test-e2e`, review bundle diffs before committing. A source-only frontend commit can be misleading because the packaged add-on uses the generated templates.

Owned JSON communication contracts are schema-first:

- source schema: `contracts/communication.schema.json`
- generated TypeScript: `settings_ui/src/lib/generated/contracts.ts`
- generated Python: `addon/anki_audio_quick_editor/contracts_generated.py`

Regenerate them with `python3 scripts/dev.py contracts-generate`; `python3 scripts/dev.py contracts-check` fails when the committed generated files are stale.

## Bridge Rules

- Settings JavaScript -> Python commands go through `settings_ui/src/lib/bridge.ts`.
- Inline editor JavaScript -> Python commands go through `settings_ui/src/editor-inline/bridge.ts`.
- All Python -> JavaScript async callbacks use `window.onAsyncProgress(...)`, `window.onAsyncDone(...)`, or `window.onSaveError(...)`.
- Settings bridge payloads and callback payloads should use the generated contract types rather than ad hoc `Any`/`unknown` shapes.
- Editor frontend logging reuses `FrontendLogPayload`; the editor bundle queues payloads on `window.__aqePopFrontendLog()` and notifies Python with `aqe:frontend-log`.
- Always `json.dumps()` values before interpolating them into `webview.eval(...)`.
- Inline editor controls are injected from Python via `editor_ui.py`, which embeds the committed editor bundle and field-index config.
- Browser batch visualization progress and logging are native Qt widgets, not Svelte/WebView content.

## Important WebView Gotchas

- Scripts inserted via `innerHTML` do not execute.
- Functions used by inline handlers must be attached to `window`.
- JSON inserted into HTML must be escaped carefully; the settings shell embeds pre-serialized JSON into `window.__INITIAL_STATE__`.
- Injected editor bundles can outlive one apparent editor render through scheduled scans and Anki field reloads. Dispose the old `window.__aqe*` runtime before replacing note field contents, and make dispose idempotent so repeated injections do not leave orphaned controls.
