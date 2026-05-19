from __future__ import annotations

import json
from unittest.mock import MagicMock


def _make_dialog() -> MagicMock:
    dialog = MagicMock()
    dialog.accepted = False
    dialog.rejected = False
    dialog.accept.side_effect = lambda: setattr(dialog, "accepted", True)
    dialog.reject.side_effect = lambda: setattr(dialog, "rejected", True)
    return dialog


def _capture_eval() -> tuple[list[str], callable]:
    calls: list[str] = []

    def eval_fn(js: str) -> None:
        calls.append(js)

    return calls, eval_fn


def _full_config() -> dict[str, object]:
        return {
            "_config_version": 11,
            "enabled": True,
            "debug_logging": False,
            "show_ffmpeg_commands": False,
            "repeat_playback_by_default": False,
            "repeat_pause_seconds": 0.0,
            "show_graph_by_default": False,
            "manual_trim_small_ms": 100,
            "manual_trim_large_ms": 500,
            "speed_step": 0.05,
            "min_speed": 0.75,
            "max_speed": 1.5,
            "volume_step_db": 3.0,
            "min_volume_db": -24.0,
            "max_volume_db": 24.0,
            "internal_pause_silence_threshold_db": -45,
            "internal_pause_threshold_ms": 300,
            "internal_pause_target_gap_ms": 100,
            "output_format": "mp3",
            "ffmpeg_path": "",
            "deep_filter_path": "",
            "deep_filter_post_filter": True,
            "denoise_algorithm": "standard",
            "pause_aggressiveness": "normal",
        }



def _parse_callback(js: str, name: str) -> dict:
    prefix = f"window.{name}("
    assert js.startswith(prefix)
    return json.loads(js[len(prefix):-1])
