"""E2E coverage for playback after editor audio edits."""

from __future__ import annotations

from pathlib import Path

import pytest

from e2e.editor_graph_helpers import _click_graph_and_wait, _graph_state_js
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
    _wait_for_generated_mp3,
)
from e2e.editor_playback_helpers import _record_fake_playback
from e2e.helpers import (
    click_selector,
    generate_tone,
    run_js,
    wait_for_condition,
    wait_for_js_condition,
    wait_for_selector,
)


def test_standard_edit_plays_new_generated_audio(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_post_edit_playback_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:faster"), timeout=10.0)
        _install_post_edit_html_audio_driver(editor)
        with _record_fake_playback(
            media_dir,
            {source.name: 1000},
            ffmpeg_config=ffmpeg_config,
            max_attempt_count=0,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:faster"), timeout=5.0)
            generated_name = _wait_for_generated_mp3(note, media_dir, source.name)
            playing = wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None
                and state["sourceFilename"] == generated_name
                and state["playbackState"] == "playing"
                and state["playbackEngine"] == "html",
                timeout=5.0,
            )

        assert playback.attempts == []
        assert playing["sourceFilename"] == generated_name
        assert generated_name != source.name
    finally:
        editor.set_note(None)
        parent.close()


@pytest.mark.parametrize(
    ("command", "source_stem"),
    [
        ("aqe:faster", "speed"),
        ("aqe:volume-up", "volume"),
    ],
)
def test_standard_edit_pulls_generated_audio_into_html_playback_before_metadata_event(
    anki_mw,
    ffmpeg_config,
    command: str,
    source_stem: str,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / f"editor_post_edit_playback_loading_{source_stem}_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector(command), timeout=10.0)
        _click_graph_and_wait(editor, lambda state: state["sourceFilename"] == source.name)
        _install_post_edit_loading_audio_driver(editor)
        with _record_fake_playback(
            media_dir,
            {source.name: 1000},
            ffmpeg_config=ffmpeg_config,
            max_attempt_count=0,
        ) as playback:
            click_selector(editor.web, _button_selector(command), timeout=5.0)
            generated_name = _wait_for_generated_mp3(note, media_dir, source.name)
            playing = wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None
                and state["sourceFilename"] == generated_name
                and state["playbackState"] == "playing"
                and state["playbackEngine"] == "html",
                timeout=7.0,
            )
            html_playback = wait_for_js_condition(
                editor.web,
                """
                (() => {
                  const warning = document.querySelector('[data-testid="aqe-playback-warning-0"]');
                  const audio = document.querySelector('[data-testid="aqe-audio-clock-0"]');
                  return {
                    playCount: window.__aqePostEditLoadingPlayCount || 0,
                    src: audio?.getAttribute("src") || "",
                    warningHidden: warning ? warning.hidden : false,
                    warningText: warning?.textContent || "",
                  };
                })()
                """,
                lambda value: value["playCount"] == 1
                and value["warningHidden"] is True
                and generated_name.replace(" ", "%20") in value["src"],
                timeout=5.0,
            )

        assert playback.attempts == []
        assert playing["sourceFilename"] == generated_name
        assert html_playback["warningText"] == ""
    finally:
        editor.set_note(None)
        parent.close()


def test_post_edit_playback_waits_for_frontend_ready_event(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_post_edit_playback_retry_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:faster"), timeout=10.0)
        _delay_post_edit_playback_ready_event(editor, delay_ms=1500)
        _install_post_edit_html_audio_driver(editor)

        with _record_fake_playback(
            media_dir,
            {source.name: 1000},
            ffmpeg_config=ffmpeg_config,
            max_attempt_count=0,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:faster"), timeout=5.0)
            generated_name = _wait_for_generated_mp3(note, media_dir, source.name)
            playing = wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None
                and state["sourceFilename"] == generated_name
                and state["playbackState"] == "playing"
                and state["playbackEngine"] == "html",
                timeout=6.0,
            )

        assert playback.attempts == []
        assert playing["sourceFilename"] == generated_name
    finally:
        editor.set_note(None)
        parent.close()


def test_post_edit_playback_ready_uses_the_rendered_graph_when_one_is_already_visible(
    anki_mw,
    ffmpeg_config,
    caplog,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_post_edit_playback_undo_stale_graph.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:faster"), timeout=10.0)
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        _install_post_edit_ready_probe_for_rendered_graph(editor, source.name)

        wait_for_condition(
            lambda: any("post-edit playback ready dispatched" in record.message for record in caplog.records),
            timeout=5.0,
            message="Post-edit ready notification was blocked even though the required graph was already rendered",
        )
    finally:
        editor.set_note(None)
        parent.close()


def _delay_post_edit_playback_ready_event(editor, delay_ms: int) -> None:
    run_js(
        editor.web,
        f"""
        (() => {{
          window.__aqeDispatchPostEditPlaybackReadyForTest = (payload, dispatch) => {{
            if (payload.command !== "aqe:post-edit-playback-ready") {{
              return false;
            }}
            window.__aqeDispatchPostEditPlaybackReadyForTest = undefined;
            setTimeout(dispatch, {delay_ms});
            return true;
          }};
          return true;
        }})()
        """,
    )


def _install_post_edit_html_audio_driver(editor, duration_ms: int = 1000) -> None:
    run_js(
        editor.web,
        f"""
        (() => {{
          const install = (audio) => {{
            if (!audio || audio.__aqePostEditHtmlDriverInstalled) return;
            const markReady = () => {{
              try {{
                Object.defineProperty(audio, "duration", {{
                  configurable: true,
                  get: () => {{
                    const state = window.__aqeGraphStateForTest?.(0);
                    return Math.max(1, Number(state?.durationMs || {duration_ms}) / 1000);
                  }},
                }});
                Object.defineProperty(audio, "readyState", {{ configurable: true, value: 4 }});
              }} catch (_error) {{
              }}
              audio.dispatchEvent(new Event("loadedmetadata"));
            }};
            audio.pause = () => undefined;
            audio.play = () => Promise.resolve();
            audio.__aqeTestDriverInstalled = true;
            const observer = new MutationObserver(markReady);
            observer.observe(audio, {{ attributes: true, attributeFilter: ["src"] }});
            audio.__aqePostEditHtmlDriverInstalled = true;
            audio.__aqePostEditHtmlDriverObserver = observer;
            markReady();
          }};
          const installAll = () => {{
            for (const audio of document.querySelectorAll('[data-testid^="aqe-audio-clock-"]')) {{
              install(audio);
            }}
          }};
          if (!window.__aqePostEditHtmlDriverRootObserver) {{
            window.__aqePostEditHtmlDriverRootObserver = new MutationObserver(installAll);
            window.__aqePostEditHtmlDriverRootObserver.observe(document.body, {{
              childList: true,
              subtree: true,
            }});
          }}
          installAll();
          return true;
        }})()
        """,
    )
    wait_for_js_condition(
        editor.web,
        """
        (() => {
          const audio = document.querySelector('[data-testid="aqe-audio-clock-0"]');
          return Boolean(audio?.__aqePostEditHtmlDriverInstalled);
        })()
        """,
        lambda value: value is True,
        timeout=5.0,
    )


def _install_post_edit_loading_audio_driver(editor) -> None:
    run_js(
        editor.web,
        """
        (() => {
          window.__aqePostEditLoadingPlayCount = 0;
          const install = (audio) => {
            if (!audio || audio.__aqePostEditLoadingDriverInstalled) return;
            try {
              Object.defineProperty(audio, "readyState", { configurable: true, get: () => 0 });
            } catch (_error) {
            }
            audio.addEventListener("loadedmetadata", (event) => {
              event.stopImmediatePropagation();
            }, true);
            audio.pause = () => undefined;
            audio.play = () => {
              window.__aqePostEditLoadingPlayCount += 1;
              return Promise.resolve();
            };
            audio.__aqePostEditLoadingDriverInstalled = true;
          };
          const installAll = () => {
            for (const audio of document.querySelectorAll('[data-testid^="aqe-audio-clock-"]')) {
              install(audio);
            }
          };
          if (!window.__aqePostEditLoadingDriverRootObserver) {
            window.__aqePostEditLoadingDriverRootObserver = new MutationObserver(installAll);
            window.__aqePostEditLoadingDriverRootObserver.observe(document.body, {
              childList: true,
              subtree: true,
            });
          }
          installAll();
          return true;
        })()
        """,
    )
    wait_for_js_condition(
        editor.web,
        """
        (() => {
          const audio = document.querySelector('[data-testid="aqe-audio-clock-0"]');
          return Boolean(audio?.__aqePostEditLoadingDriverInstalled);
        })()
        """,
        lambda value: value is True,
        timeout=5.0,
    )


def _install_post_edit_ready_probe_for_rendered_graph(editor, source_name: str) -> None:
    run_js(
        editor.web,
        f"""
        (() => {{
          window.__AQE_EDITOR_CONFIG__.pendingPostEditPlayback = {{
            fieldOrd: 0,
            generation: 99,
            requireGraphRedraw: true,
            sourceFilename: {source_name!r},
          }};
          window.__aqeSetBusy(0, false);
          return true;
        }})()
        """,
    )
