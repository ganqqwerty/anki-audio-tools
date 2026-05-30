# Debugging

## Quick Methods

- Let Anki show its startup error popup for load-time crashes.
- Use `showInfo("...")` for fast visible checks.
- Launch Anki from a terminal and use `print(...)` for stdout logs.

## debugpy

Set `DEBUG_ANKI=1` before launching Anki to make the add-on wait for a debugger on port `5678`.

## Logs

The add-on creates a rotating log file inside the add-on directory after `main_window_did_init`.

See [`ERROR_HANDLING_AND_DIAGNOSTICS.md`](ERROR_HANDLING_AND_DIAGNOSTICS.md) for the debug-mode breadcrumb, error-boundary, crash-forensics, and support-report strategy.

## QtWebEngine WebViews

Use QtWebEngine remote debugging when review, editor, or settings WebView CSS/JavaScript needs direct DOM, console, or computed-style inspection.

On macOS, Anki is launched through LaunchServices, so exporting an environment variable in the current shell is not enough for `open -a Anki`. Set the variable through `launchctl`, then launch Anki:

```bash
launchctl setenv QTWEBENGINE_REMOTE_DEBUGGING 9223
open -a /Applications/Anki.app
```

Then inspect the available WebViews:

```bash
curl -s http://127.0.0.1:9223/json/list
```

Open the `devtoolsFrontendUrl` for the relevant target, or connect to its `webSocketDebuggerUrl` with Chrome DevTools Protocol. Useful targets include `main webview` for Reviewer/card content, plus settings or previewer pages when those dialogs are open.

When finished, clear the launch environment so future Anki launches do not keep remote debugging enabled:

```bash
launchctl unsetenv QTWEBENGINE_REMOTE_DEBUGGING
```

If Anki is already running, quit and relaunch it after setting the environment. Directly running `/Applications/Anki.app/Contents/MacOS/launcher` may exit immediately on some installs; prefer the `launchctl` plus `open -a` flow above.

## Playback Cursor Bugs

When playback starts from the wrong point, inspect the graph state first: `anchorMs` is the user's selected start point and `cursorMs` is the visible/progress position.

The e2e fake player records playback intervals as `start_ms` and `end_ms`; use those records to verify whether AQE requested the wrong interval before investigating physical audio output.

Cursor playback should create a temporary `aqe_playback_*__from_<ms>ms_*.mp3` file and play it from zero. Check the temp filename, ffprobe duration, and fake-player interval records; AQE should not depend on Anki's relative seek for non-zero cursor starts.
