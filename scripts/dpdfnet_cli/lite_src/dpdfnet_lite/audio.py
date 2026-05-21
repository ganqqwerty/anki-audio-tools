from __future__ import annotations

import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np

MODEL_SAMPLE_RATE = 16000
WIN_LEN = 320
HOP_SIZE = WIN_LEN // 2
FREQ_BINS = WIN_LEN // 2 + 1
ATTN_LIMIT_NOISY_FRAME_OFFSET = 4


@dataclass(frozen=True)
class StftConfig:
    sample_rate: int
    win_len: int
    hop_size: int
    window: np.ndarray
    wnorm: float


def vorbis_window(window_len: int = WIN_LEN) -> np.ndarray:
    half = window_len / 2.0
    indices = np.arange(window_len, dtype=np.float32)
    sin = np.sin(0.5 * np.pi * (indices + 0.5) / half)
    return np.sin(0.5 * np.pi * sin * sin).astype(np.float32)


def get_wnorm(window_len: int, frame_size: int) -> float:
    return 1.0 / (window_len**2 / (2 * frame_size))


def make_stft_config() -> StftConfig:
    return StftConfig(
        sample_rate=MODEL_SAMPLE_RATE,
        win_len=WIN_LEN,
        hop_size=HOP_SIZE,
        window=vorbis_window(WIN_LEN),
        wnorm=get_wnorm(WIN_LEN, HOP_SIZE),
    )


def pcm16_safe(audio: np.ndarray) -> np.ndarray:
    x = np.clip(np.asarray(audio, dtype=np.float32), -1.0, 1.0)
    return (x * 32767.0).astype("<i2", copy=False)


def write_pcm16_wav(path: Path, audio: np.ndarray, sample_rate: int = MODEL_SAMPLE_RATE) -> Path:
    out_path = Path(path).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pcm = pcm16_safe(audio).reshape(-1)
    with wave.open(str(out_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(int(sample_rate))
        wav.writeframes(pcm.tobytes())
    return out_path


def validate_attn_limit_db(attn_limit_db: float | None) -> float | None:
    if attn_limit_db is None:
        return None
    value = float(attn_limit_db)
    if np.isnan(value) or value < 0.0:
        raise ValueError("attn_limit_db must be non-negative, infinity, or None.")
    return value


def apply_attn_limit(
    spec_noisy: np.ndarray,
    spec_enh: np.ndarray,
    attn_limit_db: float | None,
) -> np.ndarray:
    value = validate_attn_limit_db(attn_limit_db)
    enhanced = np.asarray(spec_enh, dtype=np.float32)
    if value is None:
        return enhanced

    noisy = np.asarray(spec_noisy, dtype=np.float32)
    if noisy.shape != enhanced.shape:
        raise ValueError(
            "spec_noisy and spec_enh must have matching shapes, "
            f"got {noisy.shape} and {enhanced.shape}."
        )

    aligned_noisy = np.zeros_like(noisy, dtype=np.float32)
    if noisy.shape[1] > ATTN_LIMIT_NOISY_FRAME_OFFSET:
        aligned_noisy[:, ATTN_LIMIT_NOISY_FRAME_OFFSET:, :, :] = noisy[
            :, :-ATTN_LIMIT_NOISY_FRAME_OFFSET, :, :
        ]

    alpha = float(10.0 ** (-value / 20.0))
    return np.ascontiguousarray(alpha * aligned_noisy + (1.0 - alpha) * enhanced, dtype=np.float32)


def _center_reflect_pad(waveform: np.ndarray, cfg: StftConfig) -> np.ndarray:
    x = np.asarray(waveform, dtype=np.float32).reshape(-1)
    if x.size == 0:
        return np.zeros(cfg.win_len, dtype=np.float32)
    if x.size == 1:
        return np.pad(x, (cfg.win_len // 2, cfg.win_len // 2), mode="edge")
    return np.pad(x, (cfg.win_len // 2, cfg.win_len // 2), mode="reflect")


def preprocess_waveform(waveform: np.ndarray, cfg: StftConfig | None = None) -> np.ndarray:
    cfg = cfg or make_stft_config()
    padded = _center_reflect_pad(waveform, cfg)
    n_frames = 1 + max(0, (padded.shape[0] - cfg.win_len) // cfg.hop_size)
    spec = np.empty((n_frames, FREQ_BINS), dtype=np.complex64)

    for frame_idx in range(n_frames):
        start = frame_idx * cfg.hop_size
        frame = padded[start : start + cfg.win_len]
        if frame.shape[0] < cfg.win_len:
            frame = np.pad(frame, (0, cfg.win_len - frame.shape[0]), mode="constant")
        spec[frame_idx] = np.fft.rfft(frame * cfg.window, n=cfg.win_len).astype(np.complex64)

    spec = (spec * cfg.wnorm).astype(np.complex64, copy=False)
    spec_ri = np.stack([spec.real, spec.imag], axis=-1).astype(np.float32, copy=False)
    return np.ascontiguousarray(spec_ri[None, ...], dtype=np.float32)


def postprocess_spec(spec_e: np.ndarray, cfg: StftConfig | None = None) -> np.ndarray:
    cfg = cfg or make_stft_config()
    spec_c = np.asarray(spec_e[0], dtype=np.float32)
    n_frames = int(spec_c.shape[0])
    out_len = cfg.win_len + cfg.hop_size * max(0, n_frames - 1)
    waveform = np.zeros(out_len, dtype=np.float32)
    window_sum = np.zeros(out_len, dtype=np.float32)

    for frame_idx in range(n_frames):
        complex_frame = spec_c[frame_idx, :, 0] + 1j * spec_c[frame_idx, :, 1]
        time_frame = np.fft.irfft(complex_frame, n=cfg.win_len).astype(np.float32)
        start = frame_idx * cfg.hop_size
        end = start + cfg.win_len
        windowed = time_frame * cfg.window
        waveform[start:end] += windowed
        window_sum[start:end] += cfg.window * cfg.window

    nonzero = window_sum > np.finfo(np.float32).eps
    waveform[nonzero] /= window_sum[nonzero]
    waveform = waveform[cfg.win_len // 2 :] / cfg.wnorm

    return np.concatenate(
        [waveform[cfg.win_len * 2 :], np.zeros(cfg.win_len * 2, dtype=np.float32)],
        axis=0,
    ).astype(np.float32, copy=False)


def fit_length(audio: np.ndarray, target_len: int) -> np.ndarray:
    x = np.asarray(audio, dtype=np.float32).reshape(-1)
    if x.shape[0] == target_len:
        return x
    if x.shape[0] > target_len:
        return x[:target_len]
    out = np.zeros(int(target_len), dtype=np.float32)
    out[: x.shape[0]] = x
    return out
