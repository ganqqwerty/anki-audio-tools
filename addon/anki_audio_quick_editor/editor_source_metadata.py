"""Lazy source metadata bridge for editor compression advanced settings."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .audio_state import AudioProcessingConfig
from .diagnostics_runtime import capture_exception, new_operation_id, record_breadcrumb
from .i18n import t

if TYPE_CHECKING:
    from .editor_deps_protocols import BridgeDeps

logger = logging.getLogger(__name__)
_SOURCE_INFO_ERROR = "settings.size_reduction_source_metadata.error"


def request_source_metadata(editor: Any, deps: BridgeDeps) -> None:
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
        resolved = deps.resolve_requested_field_media(
            editor,
            int(request["fieldOrd"]),
            str(request["sourceFilename"]),
        )
        if resolved is None:
            _emit_response(editor, _error_payload(request))
            return
        _filename, media_path = resolved
        processing_config = AudioProcessingConfig.from_config(deps.config(editor))
        _start_probe(editor, request, Path(media_path), processing_config, deps)

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


def _start_probe(
    editor: Any,
    request: dict[str, Any],
    media_path: Path,
    processing_config: AudioProcessingConfig,
    deps: BridgeDeps,
) -> None:
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
            metadata = deps.probe_audio_metadata(media_path, processing_config)
            payload = {
                "requestId": request["requestId"],
                "ok": True,
                "metadata": {
                    "bitRate": metadata.bit_rate,
                    "sampleRate": metadata.sample_rate,
                    "channels": metadata.channels,
                    "fileSizeBytes": _file_size_bytes(media_path),
                },
            }
        except Exception as exc:
            capture_exception(
                "editor.source_metadata",
                exc,
                operation="editor.source_metadata",
                operation_id=operation_id,
                user_message=t(_SOURCE_INFO_ERROR),
                context={
                    "field_ord": request["fieldOrd"],
                    "source_filename": request["sourceFilename"],
                },
                log=logger,
            )
            payload = _error_payload(request)
        deps.main(editor, lambda: _emit_response(editor, payload))

    deps.threading.Thread(target=_run, daemon=True).start()


def _error_payload(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "requestId": request["requestId"],
        "ok": False,
        "error": t(_SOURCE_INFO_ERROR),
    }


def _file_size_bytes(path: Path) -> int | None:
    try:
        return path.stat().st_size
    except OSError:
        return None


def _emit_response(editor: Any, payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload)
    editor.web.eval(
        "window.__aqeReceiveSourceMetadataResponse && "
        f"window.__aqeReceiveSourceMetadataResponse({rendered})"
    )
