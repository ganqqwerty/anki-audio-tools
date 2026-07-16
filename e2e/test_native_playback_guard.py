from __future__ import annotations

import pytest


@pytest.mark.allow_native_playback("start", "seek", "pause", "stop")
@pytest.mark.shared_desktop
def test_approved_native_playback_seam_records_every_operation(anki_mw) -> None:
    from aqt.sound import av_player

    assert anki_mw.col is not None
    av_player.play_tags([])
    av_player.seek_relative(3)
    av_player.toggle_pause()
    av_player.stop_and_clear_queue()
