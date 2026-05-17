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

- Settings dialogs should render through Anki `AnkiWebView.stdHtml()` so Anki owns theme classes such as `html.night-mode`, `body.nightMode`, `data-bs-theme`, bundled webview CSS variables, and live theme updates. Settings Svelte styles should prefer Anki variables such as `--canvas`, `--canvas-elevated`, `--canvas-inset`, `--fg`, `--fg-subtle`, `--border`, and button variables.
- Inline editor toolbar icons use Lucide Svelte with `currentColor`, so buttons inherit Anki/editor foreground color in light and dark modes. Keep button state changes scoped to `.aqe-button-label` and `data-aqe-button-state` so icon DOM stays intact.
- Generated prosody SVG media must be self-contained. They are usually loaded as standalone image files, so use embedded light defaults plus `@media (prefers-color-scheme: dark)` rather than relying on card body classes.
- Scripts inserted via `innerHTML` do not execute.
- Functions used by inline handlers must be attached to `window`.
- JSON inserted into HTML must be escaped carefully; the settings shell embeds pre-serialized JSON into `window.__INITIAL_STATE__`.
- Injected editor bundles can outlive one apparent editor render through scheduled scans and Anki field reloads. Dispose the old `window.__aqe*` runtime before replacing note field contents, and make dispose idempotent so repeated injections do not leave orphaned controls.
- The editable Anki field DOM is not a reliable source of truth during early note load. `editor_will_load_note` injection can run before `[sound:...]` markup is fully visible to WebEngine scans, so startup behavior that needs audio sources should pass note-derived data from Python and let later DOM scans refine it.
- Inline editor scans can also beat Svelte control mounting by a tick. Queue-based startup work should retry briefly when the target visualizer or controls are not mounted yet, instead of treating that field as absent.
- Prefer stable `data-testid` attributes for settings controls that e2e tests must click. Text labels and Svelte structure are easier to disturb during UI polish than explicit test ids.
