# Debugging

## Quick Methods

- Let Anki show its startup error popup for load-time crashes.
- Use `showInfo("...")` for fast visible checks.
- Launch Anki from a terminal and use `print(...)` for stdout logs.

## debugpy

Set `DEBUG_ANKI=1` before launching Anki to make the add-on wait for a debugger on port `5678`.

## Logs

The add-on creates a rotating log file inside the add-on directory after `main_window_did_init`.

## Playback Cursor Bugs

When playback starts from the wrong point, inspect the graph state first: `anchorMs` is the user's selected start point and `cursorMs` is the visible/progress position.

The e2e fake player records playback intervals as `start_ms` and `end_ms`; use those records to verify whether AQE requested the wrong interval before investigating physical audio output.

Cursor playback should create a temporary `aqe_playback_*__from_<ms>ms_*.mp3` file and play it from zero. Check the temp filename, ffprobe duration, and fake-player interval records; AQE should not depend on Anki's relative seek for non-zero cursor starts.
