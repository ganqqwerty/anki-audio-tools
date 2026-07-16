"""Schema-wide tests for default migration behavior."""

from __future__ import annotations

import json
from pathlib import Path

from anki_audio_quick_editor.config_migration import (
    CURRENT_CONFIG_VERSION,
    migrate_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "addon" / "anki_audio_quick_editor" / "config.json"
SCHEMA_PATH = ROOT / "addon" / "anki_audio_quick_editor" / "config.schema.json"


def _defaults() -> dict[str, object]:
    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    payload.pop("$schema", None)
    return payload


def test_stamps_current_version() -> None:
    migrated, changed = migrate_config({}, {"enabled": True})
    assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
    assert changed is True


def test_keeps_current_config_without_changes() -> None:
    config = {
        "_config_version": CURRENT_CONFIG_VERSION,
        "enabled": True,
        "debug_logging": True,
    }
    migrated, changed = migrate_config(config, config)
    assert migrated == config
    assert changed is False


def test_migration_picks_up_every_schema_default_without_overwriting_user_values() -> None:
    defaults = _defaults()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    required = set(schema["required"])

    migrated, changed = migrate_config(
        {"_config_version": CURRENT_CONFIG_VERSION, "enabled": False},
        defaults,
    )

    assert set(defaults) == required
    assert set(migrated) == required
    assert migrated["enabled"] is False
    assert {key: migrated[key] for key in required - {"enabled"}} == {
        key: defaults[key] for key in required - {"enabled"}
    }
    assert changed is True


def test_current_version_only_marks_change_when_defaults_add_values() -> None:
    user = {"_config_version": CURRENT_CONFIG_VERSION, "enabled": False}
    defaults = {
        "_config_version": CURRENT_CONFIG_VERSION,
        "enabled": True,
        "debug_logging": True,
    }

    migrated, changed = migrate_config(user, defaults)

    assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
    assert migrated["enabled"] is False
    assert migrated["debug_logging"] is True
    assert changed is True
