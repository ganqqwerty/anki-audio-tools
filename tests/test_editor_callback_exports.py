from __future__ import annotations

from pathlib import Path
from typing import Any

from anki_audio_quick_editor import editor_callbacks
from anki_audio_quick_editor import editor_transform_post_processing as post_processing


def test_editor_callback_exports_are_explicit() -> None:
    exports = editor_callbacks._exports()

    assert exports.replace_current_field_after_special_transform is (
        exports.replace_current_field_after_noise_removal
    )
    assert hasattr(exports, "handle_bridge_command")
    assert hasattr(exports, "request_playback_after_edit")
    assert not hasattr(exports, "deps")
    assert not hasattr(exports, "processing_deps")
    assert not hasattr(exports, "with_deps")


def test_noise_removal_post_processing_name_delegates_to_special_transform(monkeypatch) -> None:
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def fake_special_transform(*args: Any, **kwargs: Any) -> None:
        calls.append((args, kwargs))

    monkeypatch.setattr(
        post_processing,
        "replace_current_field_after_special_transform",
        fake_special_transform,
    )

    post_processing.replace_current_field_after_noise_removal(
        "editor",
        "cleaned.mp3",
        "deps",
        guard="guard",
        output_path=Path("cleaned.mp3"),
    )

    assert calls == [
        (
            ("editor", "cleaned.mp3", "deps"),
            {"guard": "guard", "output_path": Path("cleaned.mp3")},
        )
    ]
