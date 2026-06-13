from __future__ import annotations

from pathlib import Path

import pytest

from anki_audio_quick_editor.audio_artifacts import _max_pause_pipeline_run_id_length
from anki_audio_quick_editor.audio_pipeline import make_pause_pipeline_run_id
from anki_audio_quick_editor.errors import AudioProcessingError


def test_windows_pause_pipeline_root_budget_shrinks_as_root_grows() -> None:
    short_root = Path(r"C:\aqe_artifacts")
    long_root = Path(
        r"C:\Users\mickd\AppData\Roaming\Anki2\addons21"
        r"\anki_audio_quick_editor\aqe_artifacts"
    )
    source_filename = (
        "folder/"
        "1twister23_aqe_20260606_005401_832401_6279882d_"
        "aqe_20260606_005406_832438_cbdd3__aqe_20260606_005726_592354_45c285a4.wav"
    )

    short_budget = _max_pause_pipeline_run_id_length(short_root, is_windows=True)
    long_budget = _max_pause_pipeline_run_id_length(long_root, is_windows=True)

    assert short_budget > long_budget
    assert len(
        make_pause_pipeline_run_id(source_filename, max_length=short_budget)
    ) > len(
        make_pause_pipeline_run_id(source_filename, max_length=long_budget)
    )


def test_non_windows_pause_pipeline_root_uses_component_ceiling() -> None:
    root = Path("/Users/iuriikatkov/Library/Application Support/Anki2/addons21/anki_audio_quick_editor/aqe_artifacts")

    assert _max_pause_pipeline_run_id_length(root, is_windows=False) == 255


def test_impossible_windows_pause_pipeline_root_raises_audio_processing_error() -> None:
    root = Path(r"C:\Users\mickd\AppData\Roaming\Anki2\addons21") / ("very_long_segment_" * 12)

    with pytest.raises(AudioProcessingError, match="too long for Windows"):
        _max_pause_pipeline_run_id_length(root, is_windows=True)
