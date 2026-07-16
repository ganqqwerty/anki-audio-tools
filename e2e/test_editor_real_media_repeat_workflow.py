"""E2E reproduction for real WebView media repeat playback."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from e2e.editor_audio_generation_helpers import _generate_high_bitrate_mp3
from e2e.editor_graph_helpers import (
    _click_graph_and_wait,
    _graph_state_js,
    _set_full_time_viewport,
)
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
)
from e2e.editor_region_loop_helpers import (
    _set_repeat,
)
from e2e.helpers import (
    run_js,
    trusted_pointer_to_selector,
    wait_for_js_condition,
)

pytestmark = pytest.mark.trusted_input

MEDIA_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "audio"
EXPECTED_FORVO_REPEAT_PLAY_CALLS = 3
MAX_FORVO_REPEAT_PLAY_CALLS = EXPECTED_FORVO_REPEAT_PLAY_CALLS + 1


def test_real_mp3_playback_advances_graph_cursor_without_test_driver(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_real_mp3_cursor_source.mp3"
    _generate_high_bitrate_mp3(ffmpeg_config, source, duration_s=0.9)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, repeat_playback_by_default=False)

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == source.name,
            timeout=30.0,
        )
        _set_full_time_viewport(editor)
        _wait_for_real_audio_ready(editor)
        _install_real_audio_probe(editor)

        _trusted_click_selector(editor, _button_selector("aqe:play"))
        _wait_for_real_html_playback(editor)
        advanced = wait_for_js_condition(
            editor.web,
            _real_audio_probe_js(),
            lambda value: value is not None
            and value["currentTimeMs"] >= 180
            and value["state"]["progressMs"] >= 180
            and value["state"]["cursorX"] > 80,
            timeout=5.0,
        )

        assert advanced["state"]["audioPlaybackTestDriver"] is False
        assert advanced["state"]["playbackEngine"] == "html"
        assert advanced["state"]["progressClockMode"] == "audio"
        assert advanced["backendPlaybackRequests"] == []
        assert advanced["nativePlaybackRequests"] == []
    finally:
        _stop_real_audio_playback(editor)
        editor.set_note(None)
        parent.close()


def test_real_media_repeat_keeps_audio_playing_after_repeated_full_file_loops(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, source, _note, editor, parent, track = _open_real_media_editor(
        anki_mw,
        ffmpeg_config,
        MEDIA_FIXTURE_DIR / "forvo_Vertrag.ogg",
    )
    try:
        _set_repeat(editor, True)
        _install_real_audio_probe(editor)
        _trusted_click_selector(editor, _button_selector("aqe:play"))
        _wait_for_real_html_playback(editor)

        repeated = _wait_for_bounded_real_repeat(editor, track["durationMs"])

        assert repeated["state"]["playbackState"] == "playing"
        assert repeated["state"]["playbackEngine"] == "html"
        assert repeated["state"]["repeatEnabled"] is True
        assert repeated["loop"] is False
        assert repeated["paused"] is False, repeated
        assert repeated["errorCode"] is None, repeated
        assert EXPECTED_FORVO_REPEAT_PLAY_CALLS <= repeated["playCalls"] <= MAX_FORVO_REPEAT_PLAY_CALLS
        assert repeated["backendPlaybackRequests"] == []
        assert repeated["nativePlaybackRequests"] == []
        assert source.name == "forvo_Vertrag.ogg"
    finally:
        _stop_real_audio_playback(editor)
        editor.set_note(None)
        parent.close()


def test_real_m4a_reports_browser_audio_error_in_local_webview(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, source, _note, editor, parent, _track = _open_real_media_editor(
        anki_mw,
        ffmpeg_config,
        MEDIA_FIXTURE_DIR / "59ee74246d5fa0664820df3d6f5fc8bfb4bf79dd.m4a",
        require_browser_audio_ready=False,
    )
    try:
        failed = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None
            and state["htmlAudioReadinessState"] == "failed"
            and state["htmlAudioReadinessReason"] == "audio_error",
            timeout=10.0,
        )
        assert failed["sourceFilename"] == source.name
        assert failed["audioClockReady"] is False
    finally:
        editor.set_note(None)
        parent.close()


def _open_real_media_editor(
    anki_mw,
    ffmpeg_config,
    fixture_path: Path,
    *,
    config_overrides: dict | None = None,
    require_browser_audio_ready: bool = True,
):
    if not fixture_path.is_file():
        raise FileNotFoundError(f"real media fixture is not available: {fixture_path}")
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / fixture_path.name
    shutil.copy2(fixture_path, source)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        repeat_playback_by_default=False,
        **(config_overrides or {}),
    )
    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == source.name,
            timeout=30.0,
        )
        _set_full_time_viewport(editor)
        if require_browser_audio_ready:
            _wait_for_real_audio_ready(editor)
    except Exception:
        editor.set_note(None)
        parent.close()
        raise
    return media_dir, source, note, editor, parent, track


def _wait_for_real_audio_ready(editor, ord_: int = 0) -> None:
    wait_for_js_condition(
        editor.web,
        _graph_state_js(ord_),
        lambda state: state is not None
        and state["audioPlaybackTestDriver"] is False
        and state["htmlAudioReadinessState"] == "ready"
        and state["audioClockReady"] is True,
        timeout=10.0,
    )


def _wait_for_bounded_real_repeat(editor, duration_ms: int, ord_: int = 0):
    return wait_for_js_condition(
        editor.web,
        _real_audio_probe_js(ord_),
        _real_repeat_reached_expected_passes,
        timeout=(duration_ms / 1000) * (EXPECTED_FORVO_REPEAT_PLAY_CALLS + 1) + 8.0,
    )


def _real_repeat_reached_expected_passes(value) -> bool:
    if value is None:
        return False
    if value["playCalls"] > MAX_FORVO_REPEAT_PLAY_CALLS:
        raise AssertionError(
            "Real-media repeat playback exceeded the bounded play-call budget: "
            f"{value['playCalls']} > {MAX_FORVO_REPEAT_PLAY_CALLS}. Probe: {value!r}"
        )
    if value["nativePlaybackRequests"]:
        raise AssertionError(
            "Real-media repeat playback fell back to native playback unexpectedly: "
            f"{value['nativePlaybackRequests']!r}"
        )
    if value["backendPlaybackRequests"]:
        raise AssertionError(
            "Real-media repeat playback re-entered backend playback unexpectedly: "
            f"{value['backendPlaybackRequests']!r}"
        )
    return (
        value["state"]["playbackState"] == "playing"
        and value["state"]["playbackEngine"] == "html"
        and value["state"]["repeatEnabled"] is True
        and value["paused"] is False
        and value["errorCode"] is None
        and value["playCalls"] >= EXPECTED_FORVO_REPEAT_PLAY_CALLS
    )


def _stop_real_audio_playback(editor, ord_: int = 0) -> None:
    run_js(
        editor.web,
        f"""
        (() => {{
          window.__aqeStopEditorPlayback?.({ord_});
          const audio = document.querySelector('[data-testid="aqe-audio-clock-{ord_}"]');
          if (audio) {{
            try {{ audio.pause(); }} catch (_error) {{}}
            audio.removeAttribute("src");
            try {{ audio.load(); }} catch (_error) {{}}
          }}
          return true;
        }})()
        """,
    )
    wait_for_js_condition(
        editor.web,
        f"""
        (() => {{
          const state = window.__aqeGraphStateForTest?.({ord_});
          const audio = document.querySelector('[data-testid="aqe-audio-clock-{ord_}"]');
          return state && audio ? {{
            playbackState: state.playbackState,
            sourceAttribute: audio.getAttribute('src'),
          }} : null;
        }})()
        """,
        lambda value: value == {"playbackState": "stopped", "sourceAttribute": None},
        timeout=5.0,
    )


def _trusted_click_selector(editor, selector: str) -> None:
    trusted_pointer_to_selector(editor.web, selector, click=True)


def _install_real_audio_probe(editor, ord_: int = 0) -> None:
    wait_for_js_condition(
        editor.web,
        f"""
        (() => {{
          const probe = window.__aqeRealAudioProbe ??= {{
            backendPlaybackRequests: [],
            events: [],
            nativePlaybackRequests: [],
            pauseCalls: 0,
            playCalls: 0,
          }};
          const install = (audio) => {{
            if (!audio || audio.__aqeRealAudioProbeInstalled) return;
            const originalPlay = audio.play.bind(audio);
            const originalPause = audio.pause.bind(audio);
            audio.play = function play() {{
            probe.playCalls += 1;
            probe.events.push({{
              currentTime: audio.currentTime,
              paused: audio.paused,
              time: performance.now(),
              type: "play-call",
            }});
            const result = originalPlay();
            Promise.resolve(result).then(
              () => probe.events.push({{
                currentTime: audio.currentTime,
                paused: audio.paused,
                time: performance.now(),
                type: "play-resolved",
              }}),
              (error) => probe.events.push({{
                message: String(error && error.message || error),
                time: performance.now(),
                type: "play-rejected",
              }}),
            );
            return result;
            }};
            audio.pause = function pause() {{
            probe.pauseCalls += 1;
            probe.events.push({{
              currentTime: audio.currentTime,
              paused: audio.paused,
              time: performance.now(),
              type: "pause-call",
            }});
            return originalPause();
            }};
            for (const type of ["ended", "pause", "play", "playing", "seeked", "seeking", "timeupdate"]) {{
            audio.addEventListener(type, () => probe.events.push({{
              currentTime: audio.currentTime,
              ended: audio.ended,
              paused: audio.paused,
              time: performance.now(),
              type,
            }}));
            }}
            audio.__aqeRealAudioProbeInstalled = true;
          }};
          window.__aqeInstallRealAudioProbeForTest = () => {{
            for (const audio of document.querySelectorAll('[data-testid^="aqe-audio-clock-"]')) {{
              install(audio);
            }}
          }};
          if (!window.__aqeRealAudioProbePycmdInstalled) {{
            const originalPycmd = window.pycmd;
            window.pycmd = function monitoredPycmd(command) {{
              if (typeof command === "string") {{
                if (command === "aqe:play") {{
                  probe.backendPlaybackRequests.push(command);
                }}
                if (command.startsWith("aqe:play:")) {{
                  probe.nativePlaybackRequests.push(command);
                }}
              }}
              return originalPycmd.apply(this, arguments);
            }};
            window.__aqeRealAudioProbePycmdInstalled = true;
          }}
          if (!window.__aqeRealAudioProbeObserver) {{
            window.__aqeRealAudioProbeObserver = new MutationObserver(() => {{
              window.__aqeInstallRealAudioProbeForTest();
            }});
            window.__aqeRealAudioProbeObserver.observe(document.body, {{
              childList: true,
              subtree: true,
            }});
          }}
          window.__aqeInstallRealAudioProbeForTest();
          const audio = document.querySelector('[data-testid="aqe-audio-clock-{ord_}"]');
          return !!audio?.__aqeRealAudioProbeInstalled;
        }})()
        """,
        lambda value: value is True,
        timeout=5.0,
    )


def _wait_for_real_html_playback(editor, ord_: int = 0):
    return wait_for_js_condition(
        editor.web,
        _real_audio_probe_js(ord_),
        lambda value: value is not None
        and value["state"]["playbackState"] == "playing"
        and value["state"]["playbackEngine"] == "html"
        and value["state"]["progressClockMode"] == "audio"
        and value["playCalls"] >= 1
        and value["paused"] is False,
        timeout=10.0,
    )


def _real_audio_probe_js(ord_: int = 0) -> str:
    return f"""
    (() => {{
      const audio = document.querySelector('[data-testid="aqe-audio-clock-{ord_}"]');
      const state = window.__aqeGraphStateForTest?.({ord_});
      const probe = window.__aqeRealAudioProbe;
      if (!audio || !state || !probe) return null;
        return {{
            currentTimeMs: Math.round((Number(audio.currentTime) || 0) * 1000),
            durationMs: Math.round((Number(audio.duration) || 0) * 1000),
            ended: audio.ended,
            errorCode: audio.error ? audio.error.code : null,
        errorMessage: audio.error ? audio.error.message : "",
        backendPlaybackRequests: probe.backendPlaybackRequests.slice(),
        events: probe.events.slice(-24),
        loop: audio.loop,
        nativePlaybackRequests: probe.nativePlaybackRequests.slice(),
            pauseCalls: probe.pauseCalls,
            paused: audio.paused,
            playCalls: probe.playCalls,
            readyState: audio.readyState,
            src: audio.getAttribute("src") || audio.currentSrc || "",
            state,
          }};
        }})()
    """
