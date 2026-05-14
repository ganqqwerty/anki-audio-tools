#!/usr/bin/env python3
"""Validate config.json against config.schema.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema package not installed. Run: python3 scripts/dev.py setup")
    sys.exit(1)

ADDON_DIR = Path(__file__).resolve().parent.parent / "addon" / "anki_audio_quick_editor"
CONFIG_PATH = ADDON_DIR / "config.json"
SCHEMA_PATH = ADDON_DIR / "config.schema.json"


def validate() -> int:
    """Validate config.json against config.schema.json."""
    if not SCHEMA_PATH.exists():
        print(f"ERROR: schema not found: {SCHEMA_PATH}")
        return 1
    if not CONFIG_PATH.exists():
        print(f"ERROR: config not found: {CONFIG_PATH}")
        return 1

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    try:
        jsonschema.validate(instance=config, schema=schema)
    except jsonschema.ValidationError as exc:
        print(f"FAIL: config.json validation error:\n  {exc.message}")
        if exc.absolute_path:
            print(f"  Path: {'.'.join(str(part) for part in exc.absolute_path)}")
        return 1
    except jsonschema.SchemaError as exc:
        print(f"FAIL: config.schema.json is invalid:\n  {exc.message}")
        return 1

    print("PASS: config.json is valid against config.schema.json")
    return 0


if __name__ == "__main__":
    sys.exit(validate())
