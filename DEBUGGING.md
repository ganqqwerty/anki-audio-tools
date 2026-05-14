# Debugging

## Quick Methods

- Let Anki show its startup error popup for load-time crashes.
- Use `showInfo("...")` for fast visible checks.
- Launch Anki from a terminal and use `print(...)` for stdout logs.

## debugpy

Set `DEBUG_ANKI=1` before launching Anki to make the add-on wait for a debugger on port `5678`.

## Logs

The add-on creates a rotating log file inside the add-on directory after `main_window_did_init`.
