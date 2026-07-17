"""Bounded test-only PCM capture and independent acoustic-oracle adapter."""

from __future__ import annotations

import array
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from e2e.helpers import run_js, wait_for_js_condition

ROOT = Path(__file__).resolve().parents[1]
ANALYZER = ROOT / "settings_ui" / "tests" / "audible" / "analyze-capture.ts"
VITE_NODE = ROOT / "settings_ui" / "node_modules" / ".bin" / "vite-node"
AUDIBLE_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "audio"
AUDIBLE_SOURCE_NAME = "addressable-timecode.wav"
AUDIBLE_MANIFEST = AUDIBLE_FIXTURE_DIR / "addressable-timecode.manifest.json"


def enable_audible_worklet(anki_mw) -> None:
    """Expose only the test AudioWorklet through Anki's CSP-approved route."""
    anki_mw.addonManager.setWebExports("1000000002", r"test_support/.*\.js")


def install_audible_capture(editor, *, ord_: int = 0, max_duration_ms: int = 1500) -> None:
    """Attach a bounded AudioWorklet capture before a trusted playback gesture."""
    run_js(editor.web, _install_script(ord_, max_duration_ms))
    wait_for_js_condition(
        editor.web,
        "window.__aqeAudibleCapture?.status() || null",
        lambda value: value is not None and (value["ready"] or value["error"] is not None),
        timeout=5.0,
    )
    status = audible_capture_status(editor)
    if status["error"] is not None:
        raise AssertionError(f"audible capture installation failed: {status!r}")


def audible_capture_status(editor) -> dict[str, Any]:
    """Return capture health without transferring PCM."""
    return wait_for_js_condition(
        editor.web,
        "window.__aqeAudibleCapture?.status() || null",
        lambda value: value is not None,
        timeout=5.0,
    )


def finish_audible_capture(editor) -> dict[str, Any]:
    """Stop capture, transfer bounded PCM, and release Web Audio resources."""
    result = wait_for_js_condition(
        editor.web,
        "window.__aqeAudibleCapture?.finish() || null",
        lambda value: value is not None and value.get("finished") is True,
        timeout=8.0,
    )
    if not result["samples"]:
        raise AssertionError(f"audible capture returned no PCM: {result!r}")
    return result


def analyze_audible_capture(
    capture: dict[str, Any],
    *,
    contract: list[dict[str, Any]],
    manifest_path: Path,
    source_file_name: str,
    options: dict[str, int | float | bool] | None = None,
    oracle_options: dict[str, int | float | bool] | None = None,
) -> dict[str, Any]:
    """Evaluate captured PCM in the independent TypeScript acoustic oracle."""
    with tempfile.TemporaryDirectory(prefix="aqe-audible-") as directory_name:
        directory = Path(directory_name)
        pcm_path = directory / "capture.f32le"
        values = array.array("f", (float(value) for value in capture["samples"]))
        pcm_path.write_bytes(values.tobytes())
        request_path = directory / "request.json"
        request_path.write_text(
            json.dumps({
                "contract": contract,
                "manifestPath": str(manifest_path),
                "oracleOptions": oracle_options or {},
                "options": options or {},
                "pcmPath": str(pcm_path),
                "sampleRate": capture["sampleRate"],
                "sourceFileName": source_file_name,
            }),
            encoding="utf-8",
        )
        completed = subprocess.run(
            [str(VITE_NODE), str(ANALYZER), str(request_path)],
            cwd=ROOT / "settings_ui",
            check=True,
            capture_output=True,
            text=True,
        )
    return json.loads(completed.stdout)


def _install_script(ord_: int, max_duration_ms: int) -> str:
    return f"""
    (() => {{
      const audio = document.querySelector('[data-testid="aqe-audio-clock-{ord_}"]');
      if (!audio) throw new Error('audible capture target audio element is missing');
      const controller = {{
        chunks: [], context: null, error: null, finished: false, maxFrames: 0,
        audio: null, node: null, observer: null, ready: false, sampleRate: 0,
        source: null, totalFrames: 0,
        status() {{ return {{
          error: this.error, finished: this.finished, ready: this.ready,
          maxFrames: this.maxFrames, sampleRate: this.sampleRate, totalFrames: this.totalFrames,
          contextState: this.context?.state || 'unavailable',
        }}; }},
        finish() {{
          if (!this.finished) {{
            this.finished = true;
            try {{ this.node?.disconnect(); }} catch (_error) {{}}
            try {{ this.source?.disconnect(); }} catch (_error) {{}}
            try {{ this.observer?.disconnect(); }} catch (_error) {{}}
            try {{
              const closePromise = this.context?.close();
              if (closePromise) void closePromise.catch(() => {{}});
            }} catch (_error) {{}}
          }}
          const samples = new Array(this.totalFrames);
          let offset = 0;
          for (const chunk of this.chunks) {{ samples.splice(offset, chunk.length, ...chunk); offset += chunk.length; }}
          return {{ ...this.status(), finished: true, samples }};
        }},
      }};
      window.__aqeAudibleCapture = controller;
      void (async () => {{
        try {{
          const context = new AudioContext({{ latencyHint: 'interactive' }});
          controller.context = context;
          controller.sampleRate = context.sampleRate;
          controller.maxFrames = Math.floor(context.sampleRate * {max_duration_ms} / 1000);
          let workletReady = false;
          try {{
            await context.audioWorklet.addModule(
              '/_addons/1000000002/test_support/audio_probe_worklet.js'
            );
            workletReady = true;
          }} catch (_workletError) {{
            workletReady = false;
          }}
          const accept = (input) => {{
            if (controller.finished) return;
            const remaining = controller.maxFrames - controller.totalFrames;
            if (remaining <= 0) return;
            const values = Array.from(input.slice(0, remaining));
            controller.chunks.push(values); controller.totalFrames += values.length;
          }};
          const node = workletReady
            ? new AudioWorkletNode(context, 'aqe-audible-probe')
            : context.createScriptProcessor(1024, 1, 1);
          const sink = context.createGain(); sink.gain.value = 0;
          node.connect(sink).connect(context.destination);
          controller.node = node;
          const attach = () => {{
            const current = document.querySelector('[data-testid="aqe-audio-clock-{ord_}"]');
            if (!current || current === controller.audio || controller.finished) return;
            try {{ controller.source?.disconnect(); }} catch (_error) {{}}
            const source = context.createMediaElementSource(current);
            source.connect(node);
            source.connect(context.destination);
            controller.audio = current;
            controller.source = source;
          }};
          attach();
          controller.observer = new MutationObserver(attach);
          controller.observer.observe(document.body, {{ childList: true, subtree: true }});
          if (workletReady) {{
            node.port.onmessage = (event) => accept(new Float32Array(event.data));
          }} else {{
            node.onaudioprocess = (event) => {{
              const buffer = event.inputBuffer;
              const mono = new Float32Array(buffer.length);
              for (let channel = 0; channel < buffer.numberOfChannels; channel += 1) {{
                const values = buffer.getChannelData(channel);
                for (let i = 0; i < values.length; i += 1) mono[i] += values[i] / buffer.numberOfChannels;
              }}
              accept(mono);
            }};
          }}
          document.addEventListener('click', () => {{
            void context.resume();
          }}, {{ capture: true, once: true }});
          controller.ready = true;
        }} catch (error) {{ controller.error = String(error?.stack || error); }}
      }})();
      return true;
    }})()
    """
