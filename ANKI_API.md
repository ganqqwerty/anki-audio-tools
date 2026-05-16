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

## Compatibility Gate

Run `python3 scripts/dev.py test-anki-api` after changing any Anki-facing layer or
after bumping Anki. This test suite imports the real installed Anki Python
runtime and checks the API surface discovered from production add-on code by
`anki_api_contract/discover.py`.

The gate is intentionally fast and does not launch a full Anki app or open a
collection. It verifies hook/filter signatures exactly, verifies callable
prefix signatures while allowing harmless optional tail parameters, and checks
the Qt exports used by the add-on.

The normal unit-test mocks in `tests/conftest.py` are checked against the same
generated surface by `tests/test_anki_api_contract_mocks.py`; when adding a new
Anki API dependency, update the add-on code and make the mocks explicit if the
new dependency is not already mocked.
