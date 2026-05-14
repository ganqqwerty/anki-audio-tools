# WebView & Templates

## Settings Bundle

The settings UI keeps one committed webview bundle:

- source: `settings_ui/src/`
- output: `addon/anki_audio_quick_editor/templates/settings/settings_bundle.{js,css}`

Rebuild it with:

```bash
python3 scripts/dev.py build
```

## Bridge Rules

- All JavaScript -> Python commands go through `settings_ui/src/lib/bridge.ts`.
- All Python -> JavaScript async callbacks use `window.onAsyncProgress(...)`, `window.onAsyncDone(...)`, or `window.onSaveError(...)`.
- Always `json.dumps()` values before interpolating them into `webview.eval(...)`.
- Inline editor controls are injected from Python via `editor_ui.py`, not through the settings Svelte bundle.

## Important WebView Gotchas

- Scripts inserted via `innerHTML` do not execute.
- Functions used by inline handlers must be attached to `window`.
- JSON inserted into HTML must be escaped carefully; the settings shell embeds pre-serialized JSON into `window.__INITIAL_STATE__`.
