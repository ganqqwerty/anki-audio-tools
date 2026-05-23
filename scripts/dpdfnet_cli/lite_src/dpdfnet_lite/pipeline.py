from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np

from .audio import (
    MODEL_SAMPLE_RATE,
    apply_attn_limit,
    fit_length,
    make_stft_config,
    postprocess_spec,
    preprocess_waveform,
    validate_attn_limit_db,
    write_pcm16_wav,
)
from .ffmpeg import decode_audio
from .model import build_interpreter, reset_interpreter


@dataclass(frozen=True)
class EnhanceStats:
    input_path: Path
    output_path: Path
    frames: int
    inference_seconds: float
    avg_frame_ms: float
    rtf: float


ProgressCallback = Callable[[int, int], None]


def enhance_waveform(
    waveform: np.ndarray,
    interpreter,
    *,
    attn_limit_db: float | None = None,
    progress_callback: ProgressCallback | None = None,
) -> tuple[np.ndarray, int, float]:
    cfg = make_stft_config()
    waveform = np.asarray(waveform, dtype=np.float32).reshape(-1)
    waveform_padded = np.pad(waveform, (0, cfg.win_len), mode="constant")
    spec_r = preprocess_waveform(waveform_padded, cfg)

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    input_index = int(input_details[0]["index"])
    output_index = int(output_details[0]["index"])

    total_frames = int(spec_r.shape[1])
    if progress_callback is not None:
        progress_callback(0, total_frames)

    outputs: list[np.ndarray] = []
    total_infer_time_s = 0.0
    for frame_idx in range(total_frames):
        frame = np.ascontiguousarray(spec_r[:, frame_idx : frame_idx + 1, :, :], dtype=np.float32)
        interpreter.set_tensor(input_index, frame)
        t0 = time.perf_counter()
        interpreter.invoke()
        total_infer_time_s += time.perf_counter() - t0
        outputs.append(np.ascontiguousarray(interpreter.get_tensor(output_index), dtype=np.float32))
        if progress_callback is not None:
            progress_callback(frame_idx + 1, total_frames)

    if not outputs:
        return waveform.copy(), 0, 0.0

    spec_e = np.concatenate(outputs, axis=1).astype(np.float32, copy=False)
    spec_e = apply_attn_limit(spec_r, spec_e, attn_limit_db)
    enhanced = postprocess_spec(spec_e, cfg)
    return fit_length(enhanced, waveform.shape[0]), total_frames, total_infer_time_s


def enhance_file(
    input_path: Path,
    output_path: Path,
    *,
    interpreter=None,
    attn_limit_db: float | None = None,
    progress_callback: ProgressCallback | None = None,
) -> EnhanceStats:
    validate_attn_limit_db(attn_limit_db)
    runtime = interpreter if interpreter is not None else build_interpreter()
    reset_interpreter(runtime)

    in_path = Path(input_path).expanduser().resolve()
    out_path = Path(output_path).expanduser().resolve()
    waveform = decode_audio(in_path, sample_rate=MODEL_SAMPLE_RATE)
    enhanced, frames, inference_seconds = enhance_waveform(
        waveform,
        runtime,
        attn_limit_db=attn_limit_db,
        progress_callback=progress_callback,
    )
    write_pcm16_wav(out_path, enhanced, sample_rate=MODEL_SAMPLE_RATE)

    avg_frame_ms = (inference_seconds / frames) * 1000.0 if frames else float("nan")
    frame_duration_s = 0.010
    rtf = inference_seconds / (frames * frame_duration_s) if frames else float("nan")
    return EnhanceStats(
        input_path=in_path,
        output_path=out_path,
        frames=frames,
        inference_seconds=inference_seconds,
        avg_frame_ms=avg_frame_ms,
        rtf=rtf,
    )
