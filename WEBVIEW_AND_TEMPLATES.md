# WebView & Templates

## Settings Bundle

The settings UI keeps one committed webview bundle:

- source: `settings_ui/src/`
- output: `addon/anki_audio_quick_editor/templates/settings/settings_bundle.{js,css}`

No Browser batch-visualization template is bundled. That workflow uses a native Qt dialog from `browser_integration.py`.

Rebuild it with:

```bash
python3 scripts/dev.py build
```

Owned JSON communication contracts are schema-first:

- source schema: `contracts/communication.schema.json`
- generated TypeScript: `settings_ui/src/lib/generated/contracts.ts`
- generated Python: `addon/anki_audio_quick_editor/contracts_generated.py`

Regenerate them with `python3 scripts/dev.py contracts-generate`; `python3 scripts/dev.py contracts-check` fails when the committed generated files are stale.

## Bridge Rules

- All JavaScript -> Python commands go through `settings_ui/src/lib/bridge.ts`.
- All Python -> JavaScript async callbacks use `window.onAsyncProgress(...)`, `window.onAsyncDone(...)`, or `window.onSaveError(...)`.
- Settings bridge payloads and callback payloads should use the generated contract types rather than ad hoc `Any`/`unknown` shapes.
- Always `json.dumps()` values before interpolating them into `webview.eval(...)`.
- Inline editor controls are injected from Python via `editor_ui.py`, not through the settings Svelte bundle.
- Browser batch visualization progress and logging are native Qt widgets, not Svelte/WebView content.

## Important WebView Gotchas

- Scripts inserted via `innerHTML` do not execute.
- Functions used by inline handlers must be attached to `window`.
- JSON inserted into HTML must be escaped carefully; the settings shell embeds pre-serialized JSON into `window.__INITIAL_STATE__`.
