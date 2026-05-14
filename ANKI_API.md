# Anki API Notes

Read Anki's installed source before relying on hook names or class signatures.

Useful files:

- `aqt/gui_hooks.py`
- `aqt/main.py`
- `aqt/utils.py`
- `anki/collection.py`
- `anki/decks.py`
- `anki/notes.py`

## Patterns Used In This Add-on

- `gui_hooks.main_window_did_init` for startup registration
- `mw.addonManager.getConfig(...)` and `writeConfig(...)` for config persistence
- `mw.addonManager.setConfigAction(...)` for the Add-ons manager Config button
- `AnkiWebView.set_bridge_command(...)` for settings bridge commands
- editor hooks such as `editor_did_init` and `editor_will_load_note` for inline controls
- `mw.col.decks`, `mw.col.models`, and `mw.col.db` through `db_helpers.py`
