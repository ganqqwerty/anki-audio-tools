# Compress Audio Lazy Metadata Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the user-facing size reduction action to Compress Audio and make source metadata probing lazy so editor injection and split menu opening never run ffprobe.

**Architecture:** Keep the existing internal command and operation ids (`aqe:reduce-size`, `reduce_size`) for compatibility with config, tests, and saved settings. Remove eager source metadata from the injected editor config, then add a narrow editor bridge request that is only sent by the Compress Audio split menu after its Advanced section is opened. Python starts a background worker for the requested field/source filename; the worker validates the current media path, runs `probe_audio_metadata()`, and returns a non-blocking success/error payload to the open advanced UI.

**Tech Stack:** Python 3.13 Anki add-on bridge, Svelte 5/TypeScript editor bundle, Vitest/jsdom, ffprobe via `probe_audio_metadata()`.

---

## File Structure

- Modify: `addon/anki_audio_quick_editor/locales/*.json`
  - Rename visible Reduce Size/Smaller text to Compress Audio.
  - Add loading/error strings for lazy source info.
  - Change the source-info label to `Current: {bitRate}, {sampleRate}, channels {channels}`.
- Modify: `addon/anki_audio_quick_editor/editor_webview_injection.py`
  - Remove `_audio_field_metadata()` and all metadata probing from editor injection.
- Create: `addon/anki_audio_quick_editor/editor_source_metadata.py`
  - Own the lazy source metadata bridge command.
  - Validate pending frontend request shape on the main thread, then resolve media and run ffprobe asynchronously before emitting a response payload.
- Modify: `addon/anki_audio_quick_editor/editor_actions.py`
  - Add a non-processing bridge command for lazy source metadata.
- Modify: `addon/anki_audio_quick_editor/editor_bridge.py`
  - Dispatch the lazy metadata command without entering the audio-processing path.
- Modify: `addon/anki_audio_quick_editor/editor_callbacks.py`, `addon/anki_audio_quick_editor/editor_dependencies.py`, `addon/anki_audio_quick_editor/editor_integration.py`
  - Wire the new helper through the existing callback/dependency facade.
- Modify: `settings_ui/src/editor-inline/bridge.ts`
  - Add a note-scoped pending request queue for source metadata.
- Modify: `settings_ui/src/editor-inline/window-contract.ts`
  - Expose pop/receive functions on `window`.
- Create: `settings_ui/src/editor-inline/source-metadata-requests.ts`
  - Promise-style request state for lazy metadata responses.
- Modify: `settings_ui/src/editor-inline/types.ts`
  - Add request/response types.
- Modify: `settings_ui/src/editor-inline/SplitExtraFields.svelte`
  - Remove injected metadata lookup.
  - Request metadata only when the Compress Audio advanced section opens.
- Modify: `settings_ui/src/lib/SizeReductionAdvancedParamsFields.svelte`
  - Report `<details>` open state and render loading/error/source-info states.
- Modify tests:
  - `tests/test_editor_integration.py`
  - Create `tests/test_editor_source_metadata.py`
  - `tests/test_editor_actions.py`
  - `settings_ui/tests/editor-inline.command-splits.integration.test.ts`
  - Update locale/text expectations touched by the rename.

## Behavioral Invariants

- Editor injection never calls `ffprobe`, `probe_audio_metadata()`, or `existing_media_file_path()` for source metadata.
- The injected runtime config keeps `audioFieldMetadata` empty or absent.
- If Compress Audio is hidden by `visible_editor_buttons`, no Compress split UI is rendered and no metadata request can be queued from the frontend.
- Opening the Compress Audio split menu does not call ffprobe.
- Opening Advanced Parameters inside that split menu starts the async metadata request.
- While the request is pending, the advanced section shows `Loading source info...`.
- On success, the advanced section shows `Current: 128 kbps, 44100 Hz, channels 2`.
- On failure, the advanced section shows `Could not inspect source info.` and leaves the compression controls usable.
- Directly clicking Compress Audio uses the existing `aqe:reduce-size` processing behavior and does not request source info first.

## Task 1: Rename Visible Size Reduction Text

**Files:**
- Modify: `addon/anki_audio_quick_editor/locales/en.json`
- Modify: `addon/anki_audio_quick_editor/locales/de.json`
- Modify: `addon/anki_audio_quick_editor/locales/ja.json`
- Modify: `addon/anki_audio_quick_editor/locales/ru.json`
- Modify: `addon/anki_audio_quick_editor/locales/vi.json`
- Modify: `addon/anki_audio_quick_editor/locales/zh_CN.json`
- Modify: `addon/anki_audio_quick_editor/locales/zh_TW.json`
- Test: `settings_ui/tests/editor-inline.command-splits.integration.test.ts`
- Test: any Python text tests found by `rg -n "Smaller|smaller MP3|Reduce size|size reduction" tests settings_ui/src addon/anki_audio_quick_editor/locales`

- [ ] **Step 1: Update English source strings**

In every locale JSON file, update these keys to the same English fallback text first. Translation quality can be handled separately, but the old Make Smaller/Reduce Size text must disappear.

```json
"editor.command.reduce_size.label": "Compress Audio",
"editor.command.reduce_size.title": "Compress audio with {level} compression",
"editor.help.reduce_size_desc": "Creates a compressed MP3 by lowering safe audio parameters.",
"editor.status.operation.reduce_size": "Compressed audio with {level} level.",
"operation.reduce_size": "Compress Audio",
"editor.split.description_reduce_size": "Compresses to MP3 by reducing bitrate, sample rate, or channels when that is safe.",
"settings.size_reduction_source_metadata": "Current: {bitRate}, {sampleRate}, channels {channels}",
"settings.size_reduction_source_metadata.loading": "Loading source info...",
"settings.size_reduction_source_metadata.error": "Could not inspect source info."
```

- [ ] **Step 2: Update tests that assert visible labels**

Replace expectations like:

```ts
expect(help).toHaveTextContent("Creates a smaller MP3 by lowering safe audio parameters.");
```

with:

```ts
expect(help).toHaveTextContent("Creates a compressed MP3 by lowering safe audio parameters.");
expect(help).toHaveTextContent("Compress Audio");
```

Keep internal selectors and payloads using `reduce-size`, for example:

```ts
document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-reduce-size-menu"]')!.click();
expect(window.__aqePendingCommandPayload?.command).toBe("aqe:reduce-size");
```

- [ ] **Step 3: Run text-focused frontend test**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.command-splits.integration.test.ts
```

Expected: failures only where later tasks have not yet implemented lazy metadata behavior. There should be no remaining expectations for `Smaller`, `smaller MP3`, or `Reduce Size`.

- [ ] **Step 4: Commit rename task**

```bash
git add addon/anki_audio_quick_editor/locales settings_ui/tests/editor-inline.command-splits.integration.test.ts
git commit -m "Rename size reduction to Compress Audio" -m "The action name should describe the user intent as compression instead of the implementation detail of making a file smaller. This updates visible labels while keeping the existing internal reduce_size identifiers for saved settings compatibility. Targeted text tests were run; full check and e2e were not run at this step."
```

## Task 2: Remove Eager Metadata From Editor Injection

**Files:**
- Modify: `tests/test_editor_integration.py`
- Modify: `addon/anki_audio_quick_editor/editor_webview_injection.py`
- Test: `tests/test_editor_ui.py`

- [ ] **Step 1: Replace the current eager metadata test with a no-probe regression test**

In `tests/test_editor_integration.py`, replace `test_editor_injection_script_embeds_source_audio_metadata` with:

```python
def test_editor_injection_script_never_probes_source_audio_metadata(
    tmp_path: Path,
    monkeypatch,
) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "clip.mp3").write_bytes(b"audio")

    class Editor:
        pass

    editor = Editor()
    editor.mw = SimpleNamespace(
        col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))),
        addonManager=SimpleNamespace(
            addonFromModule=lambda _module: "addon",
            getConfig=lambda _addon: {
                "visible_editor_buttons": ["aqe:reduce-size"],
            },
        ),
    )
    note = SimpleNamespace(fields=["[sound:clip.mp3]"])

    def fail_probe(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("editor injection must not probe source metadata")

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_webview_injection.probe_audio_metadata",
        fail_probe,
        raising=False,
    )

    script = editor_injection_script(editor, note)

    match = re.search(r"window\.__AQE_EDITOR_CONFIG__ = (?P<config>\{.*?\});", script)
    assert match is not None
    config = json.loads(match.group("config"))
    assert config["audioFieldMetadata"] == {}
    assert config["audioFieldSources"] == {"0": "clip.mp3"}
```

- [ ] **Step 2: Add hidden-button no-probe coverage**

Add a second test in the same file:

```python
def test_editor_injection_script_does_not_probe_when_compress_audio_hidden(
    tmp_path: Path,
    monkeypatch,
) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "clip.mp3").write_bytes(b"audio")

    class Editor:
        pass

    editor = Editor()
    editor.mw = SimpleNamespace(
        col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))),
        addonManager=SimpleNamespace(
            addonFromModule=lambda _module: "addon",
            getConfig=lambda _addon: {
                "visible_editor_buttons": ["aqe:slower"],
            },
        ),
    )
    note = SimpleNamespace(fields=["[sound:clip.mp3]"])

    def fail_probe(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("hidden Compress Audio must not probe source metadata")

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_webview_injection.probe_audio_metadata",
        fail_probe,
        raising=False,
    )

    script = editor_injection_script(editor, note)

    match = re.search(r"window\.__AQE_EDITOR_CONFIG__ = (?P<config>\{.*?\});", script)
    assert match is not None
    config = json.loads(match.group("config"))
    assert config["visibleEditorButtons"] == ["aqe:slower"]
    assert config["audioFieldMetadata"] == {}
```

- [ ] **Step 3: Run the new tests and verify they fail before implementation**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_integration.py
```

Expected before implementation: the first test fails with `editor injection must not probe source metadata`.

- [ ] **Step 4: Remove eager metadata implementation**

In `addon/anki_audio_quick_editor/editor_webview_injection.py`:

Remove these imports:

```python
from .audio_output_policy import probe_audio_metadata
from .audio_state import AudioProcessingConfig
from .errors import AudioProcessingError
from .media_paths import existing_media_file_path
```

Change the `injection_script(...)` call from:

```python
audio_field_metadata=_audio_field_metadata(editor, audio_field_sources, config),
```

to:

```python
audio_field_metadata={},
```

Delete the whole `_audio_field_metadata()` helper.

- [ ] **Step 5: Run injection tests**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_integration.py tests/test_editor_ui.py
```

Expected: pass.

- [ ] **Step 6: Commit injection task**

```bash
git add addon/anki_audio_quick_editor/editor_webview_injection.py tests/test_editor_integration.py tests/test_editor_ui.py
git commit -m "Stop probing source metadata during editor injection" -m "Opening the editor and Browser should not synchronously inspect audio files before the user asks for advanced compression details. This keeps injected config lightweight and leaves source info to a later explicit async request. Targeted injection tests were run; full check and e2e were not run at this step."
```

## Task 3: Add Async Python Metadata Bridge

**Files:**
- Create: `addon/anki_audio_quick_editor/editor_source_metadata.py`
- Modify: `addon/anki_audio_quick_editor/editor_actions.py`
- Modify: `addon/anki_audio_quick_editor/editor_bridge.py`
- Modify: `addon/anki_audio_quick_editor/editor_callbacks.py`
- Modify: `addon/anki_audio_quick_editor/editor_dependencies.py`
- Modify: `addon/anki_audio_quick_editor/editor_integration.py`
- Create: `tests/test_editor_source_metadata.py`
- Modify: `tests/test_editor_actions.py`
- Modify: `tests/test_architecture/test_rule21_broad_exception_allowlist.py`

- [ ] **Step 1: Add tests for the async metadata helper**

Create `tests/test_editor_source_metadata.py`:

```python
import json
from pathlib import Path
from types import SimpleNamespace

from anki_audio_quick_editor.editor_source_metadata import request_source_metadata


class ImmediateThread:
    def __init__(self, target, daemon=False):
        self._target = target
        self.daemon = daemon

    def start(self):
        self._target()


class EvalCollector:
    def __init__(self):
        self.calls = []

    def __call__(self, js):
        self.calls.append(js)


def _payload_from_eval(js: str) -> dict:
    prefix = "window.__aqeReceiveSourceMetadataResponse && window.__aqeReceiveSourceMetadataResponse("
    assert js.startswith(prefix)
    assert js.endswith(")")
    return json.loads(js[len(prefix):-1])


def test_request_source_metadata_probes_requested_source_on_worker(tmp_path: Path) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    evals = EvalCollector()
    request = {
        "requestId": "source-1",
        "fieldOrd": 0,
        "sourceFilename": "clip.mp3",
    }

    editor = SimpleNamespace(web=SimpleNamespace(eval=evals))

    def eval_with_callback(_editor, expression, callback):
        assert "__aqePopPendingSourceMetadataRequest" in expression
        callback(request)

    deps = SimpleNamespace(
        config=lambda _editor: {},
        eval_with_callback=eval_with_callback,
        main=lambda _editor, callback: callback(),
        probe_audio_metadata=lambda _path, _config: SimpleNamespace(
            bit_rate=128000,
            sample_rate=44100,
            channels=2,
        ),
        resolve_requested_field_media=lambda _editor, field_ord, expected: ("clip.mp3", source),
        threading=SimpleNamespace(Thread=ImmediateThread),
    )

    request_source_metadata(editor, deps)

    payload = _payload_from_eval(evals.calls[-1])
    assert payload == {
        "requestId": "source-1",
        "ok": True,
        "metadata": {"bitRate": 128000, "sampleRate": 44100, "channels": 2},
    }


def test_request_source_metadata_reports_non_blocking_error(tmp_path: Path) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    evals = EvalCollector()
    request = {
        "requestId": "source-1",
        "fieldOrd": 0,
        "sourceFilename": "clip.mp3",
    }
    editor = SimpleNamespace(web=SimpleNamespace(eval=evals))

    def eval_with_callback(_editor, _expression, callback):
        callback(request)

    def fail_probe(_path, _config):
        raise RuntimeError("ffprobe unavailable")

    deps = SimpleNamespace(
        config=lambda _editor: {},
        eval_with_callback=eval_with_callback,
        main=lambda _editor, callback: callback(),
        probe_audio_metadata=fail_probe,
        resolve_requested_field_media=lambda _editor, field_ord, expected: ("clip.mp3", source),
        threading=SimpleNamespace(Thread=ImmediateThread),
    )

    request_source_metadata(editor, deps)

    payload = _payload_from_eval(evals.calls[-1])
    assert payload["requestId"] == "source-1"
    assert payload["ok"] is False
    assert payload["error"] == "Could not inspect source info."


def test_request_source_metadata_ignores_missing_pending_request() -> None:
    evals = EvalCollector()
    editor = SimpleNamespace(web=SimpleNamespace(eval=evals))
    started = []

    def eval_with_callback(_editor, _expression, callback):
        callback(None)

    deps = SimpleNamespace(
        config=lambda _editor: {},
        eval_with_callback=eval_with_callback,
        main=lambda _editor, callback: callback(),
        probe_audio_metadata=lambda _path, _config: None,
        resolve_requested_field_media=lambda _editor, field_ord, expected: None,
        threading=SimpleNamespace(Thread=lambda *args, **kwargs: started.append((args, kwargs))),
    )

    request_source_metadata(editor, deps)

    assert evals.calls == []
    assert started == []


def test_request_source_metadata_rejects_stale_source_without_probe(tmp_path: Path) -> None:
    evals = EvalCollector()
    request = {
        "requestId": "source-1",
        "fieldOrd": 0,
        "sourceFilename": "old.mp3",
    }
    editor = SimpleNamespace(web=SimpleNamespace(eval=evals))
    probe_calls = []

    def eval_with_callback(_editor, _expression, callback):
        callback(request)

    deps = SimpleNamespace(
        config=lambda _editor: {},
        eval_with_callback=eval_with_callback,
        main=lambda _editor, callback: callback(),
        probe_audio_metadata=lambda _path, _config: probe_calls.append(_path),
        resolve_requested_field_media=lambda _editor, field_ord, expected: None,
        threading=SimpleNamespace(Thread=ImmediateThread),
    )

    request_source_metadata(editor, deps)

    payload = _payload_from_eval(evals.calls[-1])
    assert payload["ok"] is False
    assert payload["error"] == "Could not inspect source info."
    assert probe_calls == []
```

- [ ] **Step 2: Run helper tests and verify they fail**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_source_metadata.py
```

Expected before implementation: import failure for `anki_audio_quick_editor.editor_source_metadata`.

- [ ] **Step 3: Implement `editor_source_metadata.py`**

Create `addon/anki_audio_quick_editor/editor_source_metadata.py`:

```python
"""Lazy source metadata bridge for editor compression advanced settings."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .audio_state import AudioProcessingConfig
from .diagnostics_runtime import capture_exception, new_operation_id, record_breadcrumb
from .i18n import t

logger = logging.getLogger(__name__)
_SOURCE_INFO_ERROR = "settings.size_reduction_source_metadata.error"


def request_source_metadata(editor: Any, deps: Any) -> None:
    """Pop one frontend source metadata request and answer it asynchronously."""
    expression = """
    (() => window.__aqePopPendingSourceMetadataRequest
      ? window.__aqePopPendingSourceMetadataRequest()
      : null)()
    """

    def _continue(raw_request: Any) -> None:
        request = _parse_request(raw_request)
        if request is None:
            return
        _start_probe(editor, request, deps)

    deps.eval_with_callback(editor, expression, _continue)


def _parse_request(raw_request: Any) -> dict[str, Any] | None:
    if not isinstance(raw_request, dict):
        return None
    request_id = raw_request.get("requestId")
    field_ord = raw_request.get("fieldOrd")
    source_filename = raw_request.get("sourceFilename")
    if (
        not isinstance(request_id, str)
        or not request_id
        or isinstance(field_ord, bool)
        or not isinstance(field_ord, int)
        or not isinstance(source_filename, str)
        or not source_filename
    ):
        return None
    return {
        "requestId": request_id,
        "fieldOrd": field_ord,
        "sourceFilename": source_filename,
    }


def _start_probe(editor: Any, request: dict[str, Any], deps: Any) -> None:
    operation_id = new_operation_id("source-meta")
    record_breadcrumb(
        "editor.source_metadata.started",
        source="editor",
        operation="editor.source_metadata",
        operation_id=operation_id,
        boundary="editor.bridge",
        context={"field_ord": request["fieldOrd"], "source_filename": request["sourceFilename"]},
    )

    def _run() -> None:
        try:
            resolved = deps.resolve_requested_field_media(
                editor,
                int(request["fieldOrd"]),
                str(request["sourceFilename"]),
            )
            if resolved is None:
                payload = _error_payload(request)
                deps.main(editor, lambda: _emit_response(editor, payload, deps))
                return
            _filename, media_path = resolved
            metadata = deps.probe_audio_metadata(
                Path(media_path),
                AudioProcessingConfig.from_config(deps.config(editor)),
            )
            payload = {
                "requestId": request["requestId"],
                "ok": True,
                "metadata": {
                    "bitRate": metadata.bit_rate,
                    "sampleRate": metadata.sample_rate,
                    "channels": metadata.channels,
                },
            }
        except Exception as exc:
            capture_exception(
                "editor.source_metadata",
                exc,
                operation="editor.source_metadata",
                operation_id=operation_id,
                user_message=t(_SOURCE_INFO_ERROR),
                context={"field_ord": request["fieldOrd"], "source_filename": request["sourceFilename"]},
                log=logger,
            )
            payload = _error_payload(request)
        deps.main(editor, lambda: _emit_response(editor, payload, deps))

    deps.threading.Thread(target=_run, daemon=True).start()


def _error_payload(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "requestId": request["requestId"],
        "ok": False,
        "error": t(_SOURCE_INFO_ERROR),
    }


def _emit_response(editor: Any, payload: dict[str, Any], deps: Any) -> None:
    rendered = json.dumps(payload)
    editor.web.eval(
        "window.__aqeReceiveSourceMetadataResponse && "
        f"window.__aqeReceiveSourceMetadataResponse({rendered})"
    )
```

- [ ] **Step 4: Wire the bridge command**

In `addon/anki_audio_quick_editor/editor_actions.py`:

```python
CMD_SOURCE_METADATA = "aqe:source-metadata"
```

Add `CMD_SOURCE_METADATA` to `BRIDGE_COMMANDS` near the other non-processing payload commands.

In `addon/anki_audio_quick_editor/editor_bridge.py`, import the command and add it to `handlers` in `handle_non_processing_command`:

```python
CMD_SOURCE_METADATA: deps.request_source_metadata,
```

In `addon/anki_audio_quick_editor/editor_callbacks.py`:

```python
from . import editor_source_metadata

_request_source_metadata = _with_deps(
    editor_source_metadata.request_source_metadata,
    _bridge_deps,
)
```

In `addon/anki_audio_quick_editor/editor_dependencies.py`, import `probe_audio_metadata`:

```python
from .audio_output_policy import probe_audio_metadata
```

Inside `bridge_deps(...)`, add the local import and merge the new entries into the existing `SimpleNamespace`:

```python
def bridge_deps(callbacks: Any, frontend_callbacks: Any) -> SimpleNamespace:
    from . import editor_runtime

    return SimpleNamespace(
        # keep the existing entries and add these:
        request_source_metadata=callbacks.request_source_metadata,
        config=editor_runtime.config,
        main=frontend_callbacks.main,
        probe_audio_metadata=probe_audio_metadata,
        resolve_requested_field_media=resolve_requested_field_media,
        threading=threading,
    )
```

In `addon/anki_audio_quick_editor/editor_integration.py`, expose the callback alias:

```python
_request_source_metadata = editor_callbacks._request_source_metadata
```

- [ ] **Step 5: Add architecture allowance for the worker boundary**

In `tests/test_architecture/test_rule21_broad_exception_allowlist.py`, add this allowance beside the other editor worker boundaries:

```python
BroadExceptionAllowance(
    "editor_source_metadata",
    "_start_probe._run",
    1,
    "Lazy editor source metadata worker sends non-blocking UI error callbacks instead of leaking thread exceptions.",
),
```

- [ ] **Step 6: Add command mapping test**

In `tests/test_editor_actions.py`, extend the bridge command expectations:

```python
assert "aqe:source-metadata" in BRIDGE_COMMANDS
```

If the file imports individual constants, import and assert `CMD_SOURCE_METADATA == "aqe:source-metadata"`.

- [ ] **Step 7: Run backend bridge tests**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_source_metadata.py tests/test_editor_actions.py tests/test_editor_bridge_facade_commands.py tests/test_architecture/test_rule21_broad_exception_allowlist.py
```

Expected: pass.

- [ ] **Step 8: Commit backend async bridge**

```bash
git add addon/anki_audio_quick_editor/editor_source_metadata.py addon/anki_audio_quick_editor/editor_actions.py addon/anki_audio_quick_editor/editor_bridge.py addon/anki_audio_quick_editor/editor_callbacks.py addon/anki_audio_quick_editor/editor_dependencies.py addon/anki_audio_quick_editor/editor_integration.py tests/test_editor_source_metadata.py tests/test_editor_actions.py tests/test_architecture/test_rule21_broad_exception_allowlist.py
git commit -m "Load compression source info through an async editor bridge" -m "Source metadata is only useful after the user expands advanced compression settings, so the bridge now probes it on demand and off the UI thread. The request validates the current field/source filename to avoid stale split menus inspecting the wrong file. Targeted backend tests were run; full check and e2e were not run at this step."
```

## Task 4: Add Lazy Frontend Request State

**Files:**
- Create: `settings_ui/src/editor-inline/source-metadata-requests.ts`
- Modify: `settings_ui/src/editor-inline/bridge.ts`
- Modify: `settings_ui/src/editor-inline/window-contract.ts`
- Modify: `settings_ui/src/editor-inline/types.ts`
- Modify: `settings_ui/tests/editor-inline.command-splits.integration.test.ts`

- [ ] **Step 1: Add source metadata request/response types**

In `settings_ui/src/editor-inline/types.ts`, add:

```ts
export interface SourceMetadataRequest {
  requestId: string;
  fieldOrd: number;
  sourceFilename: string;
}

export interface SourceMetadataResponse {
  requestId: string;
  ok: boolean;
  metadata?: AudioSourceMetadataSummary;
  error?: string;
}
```

- [ ] **Step 2: Add pending request queue to editor bridge**

In `settings_ui/src/editor-inline/bridge.ts`, import the type and add:

```ts
import type { SourceMetadataRequest } from "./types.js";

const pendingSourceMetadataRequests: SourceMetadataRequest[] = [];

export function sendSourceMetadataRequest(request: SourceMetadataRequest): void {
  pendingSourceMetadataRequests.push(request);
  sendBridgeCommand("aqe:source-metadata");
}

export function popPendingSourceMetadataRequest(): SourceMetadataRequest | null {
  return pendingSourceMetadataRequests.shift() ?? null;
}
```

Update `clearPendingNoteScopedBridgeRequests()`:

```ts
pendingSourceMetadataRequests.length = 0;
```

- [ ] **Step 3: Create Promise-style frontend request helper**

Create `settings_ui/src/editor-inline/source-metadata-requests.ts`:

```ts
import type { AudioSourceMetadataSummary } from "../lib/size-reduction-parameters.js";
import { sendSourceMetadataRequest } from "./bridge.js";
import type { SourceMetadataResponse } from "./types.js";

const pending = new Map<string, {
  reject: (error: Error) => void;
  resolve: (metadata: AudioSourceMetadataSummary) => void;
}>();

let counter = 0;

export function requestSourceMetadata(
  fieldOrd: number,
  sourceFilename: string,
): Promise<AudioSourceMetadataSummary> {
  counter += 1;
  const requestId = `source_${counter}_${Date.now()}`;
  const promise = new Promise<AudioSourceMetadataSummary>((resolve, reject) => {
    pending.set(requestId, { resolve, reject });
  });
  sendSourceMetadataRequest({ requestId, fieldOrd, sourceFilename });
  return promise;
}

export function receiveSourceMetadataResponse(response: SourceMetadataResponse): void {
  const callbacks = pending.get(response.requestId);
  if (!callbacks) return;
  pending.delete(response.requestId);
  if (response.ok && response.metadata) {
    callbacks.resolve(response.metadata);
    return;
  }
  callbacks.reject(new Error(response.error || "Could not inspect source info."));
}

export function clearSourceMetadataRequestsForTest(): void {
  pending.clear();
  counter = 0;
}
```

- [ ] **Step 4: Expose pop/receive functions on the editor window contract**

In `settings_ui/src/editor-inline/window-contract.ts`, import:

```ts
import {
  receiveSourceMetadataResponse,
} from "./source-metadata-requests.js";
import {
  popPendingSourceMetadataRequest,
  popPendingRegionDeleteRequest,
  popPendingSplitDefaultSaveRequest,
} from "./bridge.js";
```

Add names:

```ts
"__aqePopPendingSourceMetadataRequest",
"__aqeReceiveSourceMetadataResponse",
```

Install them:

```ts
window.__aqePopPendingSourceMetadataRequest = popPendingSourceMetadataRequest;
window.__aqeReceiveSourceMetadataResponse = receiveSourceMetadataResponse;
```

Update the test window declaration file if TypeScript requires it.

- [ ] **Step 5: Add failing frontend tests for request timing**

In `settings_ui/tests/editor-inline.command-splits.integration.test.ts`, update the size reduction test setup to use `audioFieldSources` instead of `audioFieldMetadata`:

```ts
window.__AQE_EDITOR_CONFIG__ = {
  audioFieldIndices: [0],
  audioFieldSources: {
    0: "clip.mp3",
  },
  splitButtonDefaults: {
    denoiseAlgorithm: "standard",
    pauseAggressiveness: "normal",
    repeatPauseSeconds: 0,
    sizeReductionMode: "normal",
    sizeReductionBitrateKbps: 64,
    sizeReductionSampleRateHz: 32000,
    sizeReductionChannels: 1,
    speedStep: 1.5,
    volumeStepDb: 15,
  },
};
```

Add expectations after opening the split menu:

```ts
document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-reduce-size-menu"]')!.click();
await Promise.resolve();

const popover = document.querySelector<HTMLElement>('[data-testid="aqe-split-0-reduce-size-popover"]')!;
expect(bridgeCommands()).not.toContain("aqe:source-metadata");
expect(popover).not.toHaveTextContent("Loading source info...");
expect(popover).not.toHaveTextContent("Current: 128 kbps, 44100 Hz, channels 2");
```

Add expectations for opening Advanced:

```ts
const advanced = popover.querySelector<HTMLDetailsElement>(
  '[data-testid="aqe-split-0-reduce-size-size-reduction-advanced-params"]',
)!;
advanced.open = true;
advanced.dispatchEvent(new Event("toggle", { bubbles: true }));
await Promise.resolve();

expect(bridgeCommands()).toContain("aqe:source-metadata");
expect(popover).toHaveTextContent("Loading source info...");

const request = window.__aqePopPendingSourceMetadataRequest?.();
expect(request).toMatchObject({
  fieldOrd: 0,
  sourceFilename: "clip.mp3",
});

window.__aqeReceiveSourceMetadataResponse?.({
  requestId: request!.requestId,
  ok: true,
  metadata: { bitRate: 128000, sampleRate: 44100, channels: 2 },
});
await Promise.resolve();

expect(popover).toHaveTextContent("Current: 128 kbps, 44100 Hz, channels 2");
```

Add a direct-click regression test:

```ts
it("does not request source metadata for direct Compress Audio clicks", async () => {
  window.__AQE_EDITOR_CONFIG__ = {
    audioFieldIndices: [0],
    audioFieldSources: { 0: "clip.mp3" },
    splitButtonDefaults: {
      denoiseAlgorithm: "standard",
      pauseAggressiveness: "normal",
      repeatPauseSeconds: 0,
      sizeReductionMode: "normal",
      speedStep: 1.5,
      volumeStepDb: 15,
    },
  };
  initializeEditorRuntime(window.__AQE_EDITOR_CONFIG__);
  scan(window.__AQE_EDITOR_CONFIG__);

  document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-reduce-size"]')!.click();

  expect(bridgeCommands()).toContain("aqe:command-payload");
  expect(bridgeCommands()).not.toContain("aqe:source-metadata");
  expect(window.__aqePendingCommandPayload).toMatchObject({
    command: "aqe:reduce-size",
    fieldOrd: 0,
  });
});
```

Add a hidden-button regression test:

```ts
it("has no source metadata request path when Compress Audio is hidden", async () => {
  window.__AQE_EDITOR_CONFIG__ = {
    audioFieldIndices: [0],
    audioFieldSources: { 0: "clip.mp3" },
    visibleEditorButtons: ["aqe:slower"],
    splitButtonDefaults: {
      denoiseAlgorithm: "standard",
      pauseAggressiveness: "normal",
      repeatPauseSeconds: 0,
      speedStep: 1.5,
      volumeStepDb: 15,
    },
  };
  initializeEditorRuntime(window.__AQE_EDITOR_CONFIG__);
  scan(window.__AQE_EDITOR_CONFIG__);

  expect(document.querySelector('[data-testid="aqe-button-0-reduce-size"]')).toBeNull();
  expect(document.querySelector('[data-testid="aqe-split-0-reduce-size-menu"]')).toBeNull();
  expect(bridgeCommands()).not.toContain("aqe:source-metadata");
});
```

Add an error-state test:

```ts
window.__aqeReceiveSourceMetadataResponse?.({
  requestId: request!.requestId,
  ok: false,
  error: "Could not inspect source info.",
});
await Promise.resolve();

expect(popover).toHaveTextContent("Could not inspect source info.");
expect(popover.querySelector('[data-testid="aqe-split-0-reduce-size-size-reduction-bitrate-kbps"]')).not.toBeNull();
```

- [ ] **Step 6: Run frontend tests and verify failures before component wiring**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.command-splits.integration.test.ts
```

Expected before component wiring: failures around no metadata request after opening Advanced.

- [ ] **Step 7: Commit frontend request plumbing**

```bash
git add settings_ui/src/editor-inline/bridge.ts settings_ui/src/editor-inline/window-contract.ts settings_ui/src/editor-inline/types.ts settings_ui/src/editor-inline/source-metadata-requests.ts settings_ui/tests/editor-inline.command-splits.integration.test.ts
git commit -m "Add lazy source metadata request plumbing" -m "The frontend needs a dormant request path that only activates from compression advanced settings. This adds a note-scoped request queue and response callback without changing the direct compression command path. Targeted frontend tests were run and still fail until component wiring is completed; full check and e2e were not run at this step."
```

## Task 5: Wire Advanced Section Loading/Error UI

**Files:**
- Modify: `settings_ui/src/lib/SizeReductionAdvancedParamsFields.svelte`
- Modify: `settings_ui/src/editor-inline/SplitExtraFields.svelte`
- Modify: `settings_ui/tests/editor-inline.command-splits.integration.test.ts`

- [ ] **Step 1: Add open-state and source-info props to advanced fields**

In `settings_ui/src/lib/SizeReductionAdvancedParamsFields.svelte`, extend props:

```ts
sourceMetadataErrorText?: string | null;
sourceMetadataLoading?: boolean;
onAdvancedOpen?: () => void;
```

Add defaults:

```ts
sourceMetadataErrorText = null,
sourceMetadataLoading = false,
onAdvancedOpen,
```

Add a toggle handler:

```ts
function handleToggle(event: Event): void {
  const details = event.currentTarget as HTMLDetailsElement;
  if (details.open) onAdvancedOpen?.();
}
```

Wire it:

```svelte
<details
  class:advanced-params-compact={compact}
  class="advanced-params"
  data-testid={`${testPrefix}-advanced-params`}
  ontoggle={handleToggle}
>
```

Replace the metadata paragraph block with:

```svelte
{#if sourceMetadataLoading}
  <p class="source-metadata" data-testid={`${testPrefix}-source-metadata-loading`}>
    {t("settings.size_reduction_source_metadata.loading")}
  </p>
{:else if sourceMetadataText}
  <p class="source-metadata" data-testid={`${testPrefix}-source-metadata`}>
    {sourceMetadataText}
  </p>
{:else if sourceMetadataErrorText}
  <p class="source-metadata source-metadata-error" data-testid={`${testPrefix}-source-metadata-error`}>
    {sourceMetadataErrorText}
  </p>
{/if}
```

- [ ] **Step 2: Request metadata from `SplitExtraFields.svelte` only after Advanced opens**

In `settings_ui/src/editor-inline/SplitExtraFields.svelte`, remove:

```ts
const sourceMetadata = $derived(window.__AQE_EDITOR_CONFIG__?.audioFieldMetadata?.[targetOrd]);
const sourceMetadataText = $derived(formatSourceMetadata(sourceMetadata));
```

Import the helper:

```ts
import { requestSourceMetadata } from "./source-metadata-requests.js";
```

Add local state:

```ts
let sourceMetadata = $state<AudioSourceMetadataSummary | null>(null);
let sourceMetadataLoading = $state(false);
let sourceMetadataErrorText = $state<string | null>(null);
let sourceMetadataRequested = false;

const sourceMetadataText = $derived(sourceMetadata ? formatSourceMetadata(sourceMetadata) : null);
const sourceFilename = $derived(window.__AQE_EDITOR_CONFIG__?.audioFieldSources?.[targetOrd] ?? null);
```

Add the handler:

```ts
function requestSourceMetadataAfterAdvancedOpen(): void {
  if (command !== "aqe:reduce-size") return;
  if (sourceMetadataRequested || !sourceFilename) return;
  sourceMetadataRequested = true;
  sourceMetadataLoading = true;
  sourceMetadataErrorText = null;
  requestSourceMetadata(targetOrd, sourceFilename)
    .then((metadata) => {
      sourceMetadata = metadata;
      sourceMetadataErrorText = null;
    })
    .catch(() => {
      sourceMetadata = null;
      sourceMetadataErrorText = t("settings.size_reduction_source_metadata.error");
    })
    .finally(() => {
      sourceMetadataLoading = false;
    });
}
```

Pass the new props:

```svelte
<SizeReductionAdvancedParamsFields
  compact={true}
  bitrateKbps={sizeReductionBitrateKbps}
  sampleRateHz={sizeReductionSampleRateHz}
  channels={sizeReductionChannels}
  onBitrateKbps={applySizeReductionBitrate}
  onSampleRateHz={applySizeReductionSampleRate}
  onChannels={applySizeReductionChannels}
  onAdvancedOpen={requestSourceMetadataAfterAdvancedOpen}
  {sourceMetadataText}
  {sourceMetadataLoading}
  {sourceMetadataErrorText}
  testPrefix={`aqe-split-${targetOrd}-${slug}-size-reduction`}
/>
```

- [ ] **Step 3: Run split menu tests**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.command-splits.integration.test.ts
```

Expected: pass.

- [ ] **Step 4: Run frontend type checks**

Run:

```bash
cd settings_ui
npm run typecheck
npm run check
```

Expected: pass.

- [ ] **Step 5: Commit advanced UI wiring**

```bash
git add settings_ui/src/lib/SizeReductionAdvancedParamsFields.svelte settings_ui/src/editor-inline/SplitExtraFields.svelte settings_ui/tests/editor-inline.command-splits.integration.test.ts
git commit -m "Load compression source info from the advanced section" -m "The source-info label is helpful only when the user expands advanced compression controls, so the split menu no longer starts the heavy metadata path. The UI now shows loading, success, and non-blocking failure states while preserving direct compression clicks. Targeted frontend tests and type checks were run; full check and e2e were not run at this step."
```

## Task 6: Build Bundles And Run Final Verification

**Files:**
- Generated by build if needed: `addon/anki_audio_quick_editor/templates/editor/editor_bundle.js`
- Generated by build if needed: `addon/anki_audio_quick_editor/templates/editor/editor_bundle.css`
- Generated by build if needed: other committed templates under `addon/anki_audio_quick_editor/templates/`

- [ ] **Step 1: Rebuild frontend bundles**

Run:

```bash
python3 scripts/dev.py build
```

Expected: build succeeds and generated template changes reflect the Svelte/TypeScript edits.

- [ ] **Step 2: Run targeted Python tests**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_integration.py tests/test_editor_ui.py tests/test_editor_source_metadata.py tests/test_editor_actions.py tests/test_editor_bridge_facade_commands.py
```

Expected: pass.

- [ ] **Step 3: Run targeted frontend tests**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.command-splits.integration.test.ts
npm run typecheck
npm run check
```

Expected: pass.

- [ ] **Step 4: Run full reusable QC**

Run:

```bash
python3 scripts/dev.py check
```

Expected: pass.

- [ ] **Step 5: Run e2e before calling the feature complete**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected: pass. If e2e is skipped for time or environment, the final commit message must say that full e2e was not run.

- [ ] **Step 6: Inspect for stale visible labels**

Run:

```bash
rg -n "Smaller|smaller MP3|Reduce Size|Reduce size|Make Smaller|Make audio Smaller" addon/anki_audio_quick_editor settings_ui/src tests
```

Expected: no stale user-facing labels. Internal identifiers such as `reduce_size`, `aqe:reduce-size`, `size_reduction`, and test ids containing `reduce-size` may remain.

- [ ] **Step 7: Commit final build/verification changes**

```bash
git add addon/anki_audio_quick_editor/templates
git commit -m "Build lazy compression metadata UI" -m "The shipped editor bundle now matches the lazy Compress Audio metadata behavior. This makes the runtime change visible in Anki while keeping generated assets in sync. Full check and e2e were run before this commit; if either was skipped, replace this sentence with the exact commands that were not run and why."
```

## Self-Review Checklist

- [ ] Requirement 0 covered: user-facing Make Smaller/Reduce Size text becomes Compress Audio while internal ids remain compatible.
- [ ] Requirement 1 covered: hidden Compress Audio has no rendered metadata request path and editor injection never probes.
- [ ] Requirement 2 covered: ffprobe runs asynchronously only after Advanced opens inside the Compress Audio split menu.
- [ ] Split menu opening alone covered by frontend test asserting no `aqe:source-metadata` command.
- [ ] Direct click covered by frontend test asserting `aqe:command-payload` and no metadata request.
- [ ] Loading state covered by frontend test asserting `Loading source info...`.
- [ ] Success state covered by frontend test asserting `Current: 128 kbps, 44100 Hz, channels 2`.
- [ ] Error state covered by frontend test asserting `Could not inspect source info.` and controls remain usable.
- [ ] Backend safety covered by stale-source test using `resolve_requested_field_media` inside the worker path.
- [ ] Performance regression covered by Python injection test that fails if `probe_audio_metadata()` is called during injection.
