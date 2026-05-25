"""Tests for generated JSON communication contract plumbing."""

from __future__ import annotations

from pathlib import Path

from scripts.generate_contracts import (
    _composed_schema,
    _postprocess_python,
    stale_targets,
)


def test_composed_contract_schema_uses_config_schema_source() -> None:
    schema = _composed_schema()
    definitions = schema["definitions"]
    assert isinstance(definitions, dict)
    config = definitions["Config"]
    assert isinstance(config, dict)
    assert config["additionalProperties"] is False
    assert "deep_filter_post_filter" in config["properties"]
    assert "repeat_playback_by_default" in config["properties"]
    assert "repeat_pause_seconds" in config["properties"]
    assert "voice_recording_countdown_seconds" in config["properties"]
    assert "show_graph_by_default" in config["properties"]
    assert "graph_voice_range" in config["properties"]
    assert "graph_recording_condition" in config["properties"]
    assert "graph_smoothness" in config["properties"]
    assert "graph_connect_short_dropouts_ms" in config["properties"]
    assert "graph_voice_lock" in config["properties"]


def test_stale_targets_reports_missing_and_changed_files(tmp_path: Path) -> None:
    missing = tmp_path / "missing.txt"
    changed = tmp_path / "changed.txt"
    current = tmp_path / "current.txt"
    changed.write_text("old", encoding="utf-8")
    current.write_text("same", encoding="utf-8")

    stale = stale_targets(
        {
            missing: "generated",
            changed: "new",
            current: "same",
        }
    )

    assert stale == [missing, changed]


def test_python_postprocess_replaces_bare_except() -> None:
    content = "    try:\n        return f(x)\n    except:\n        pass\n"

    processed = _postprocess_python(content)

    assert "except:" not in processed
    assert "except (AssertionError, TypeError, ValueError):" in processed
