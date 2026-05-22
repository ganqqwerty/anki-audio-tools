from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import numpy as np

MODEL_NAME = "dpdfnet4"
MODEL_FILENAME = f"{MODEL_NAME}.tflite"
EXPECTED_MODEL_BYTES = 13_515_600
EXPECTED_MODEL_SHA256 = "d544a0f9e65180b0f67d1442cb9d33cec33347076dc427af97a461a75dd19c06"
EXPECTED_INPUT_SHAPE = (1, 1, 161, 2)
EXPECTED_OUTPUT_SHAPE = (1, 1, 161, 2)


def bundled_model_path() -> Path:
    override = os.environ.get("DPDFNET_LITE_MODEL")
    if override:
        return Path(override).expanduser().resolve()

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass) / "dpdfnet_lite" / "assets" / MODEL_FILENAME

    package_asset = Path(__file__).resolve().parent / "assets" / MODEL_FILENAME
    if package_asset.is_file():
        return package_asset

    return Path(__file__).resolve().parents[3] / "build" / "tflite" / MODEL_FILENAME


def _load_interpreter_class():
    try:
        from ai_edge_litert.interpreter import Interpreter
    except ImportError as exc:
        raise RuntimeError(
            "The TFLite standalone runtime requires ai-edge-litert. "
            "Install the version pinned in requirements-lite-build.txt, or use the packaged executable."
        ) from exc
    return Interpreter


def _shape_tuple(detail: dict[str, Any]) -> tuple[int, ...]:
    shape = detail.get("shape")
    if shape is None:
        return ()
    return tuple(int(item) for item in shape)


def validate_signature(interpreter: Any) -> None:
    inputs = interpreter.get_input_details()
    outputs = interpreter.get_output_details()
    if len(inputs) != 1 or len(outputs) != 1:
        raise RuntimeError(
            f"Expected stateful dpdfnet4 TFLite signature with 1 input and 1 output; "
            f"got {len(inputs)} inputs and {len(outputs)} outputs."
        )

    input_shape = _shape_tuple(inputs[0])
    output_shape = _shape_tuple(outputs[0])
    input_dtype = np.dtype(inputs[0].get("dtype"))
    output_dtype = np.dtype(outputs[0].get("dtype"))

    if input_shape != EXPECTED_INPUT_SHAPE or output_shape != EXPECTED_OUTPUT_SHAPE:
        raise RuntimeError(
            "Unexpected dpdfnet4 TFLite tensor shapes: "
            f"input {input_shape}, output {output_shape}."
        )
    if input_dtype != np.dtype(np.float32) or output_dtype != np.dtype(np.float32):
        raise RuntimeError(
            "Unexpected dpdfnet4 TFLite tensor dtypes: "
            f"input {input_dtype}, output {output_dtype}."
        )


def build_interpreter(model_path: Path | None = None):
    path = Path(model_path) if model_path is not None else bundled_model_path()
    path = path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Bundled TFLite model not found: {path}")

    interpreter_cls = _load_interpreter_class()
    interpreter = interpreter_cls(model_path=str(path))
    interpreter.allocate_tensors()
    validate_signature(interpreter)
    return interpreter


def reset_interpreter(interpreter: Any) -> None:
    reset = getattr(interpreter, "reset_all_variables", None)
    if reset is None:
        raise RuntimeError("LiteRT interpreter does not expose reset_all_variables().")
    reset()
