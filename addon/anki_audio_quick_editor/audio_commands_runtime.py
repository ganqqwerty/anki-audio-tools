"""Noise-reduction and playback command builders."""

from __future__ import annotations

from pathlib import Path

FFMPEG_AUDIO_CODEC_ARG = "-codec:a"


def build_deep_filter_prepare_command(
    ffmpeg_path: Path,
    source_path: Path,
    output_wav_path: Path,
) -> tuple[str, ...]:
    """Build the ffmpeg command that prepares a 48 kHz mono WAV for DeepFilterNet."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "48000",
        FFMPEG_AUDIO_CODEC_ARG,
        "pcm_s16le",
        str(output_wav_path),
    )


def build_silero_vad_prepare_command(
    ffmpeg_path: Path,
    source_path: Path,
    output_wav_path: Path,
) -> tuple[str, ...]:
    """Build the ffmpeg command that prepares 16 kHz mono WAV for Silero VAD."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        FFMPEG_AUDIO_CODEC_ARG,
        "pcm_s16le",
        str(output_wav_path),
    )


def build_silero_vad_command(
    silero_vad_path: Path,
    model_path: Path,
    input_wav_path: Path,
    output_wav_path: Path,
    *,
    threshold: float,
    min_silence_seconds: float,
    min_speech_seconds: float,
) -> tuple[str, ...]:
    """Build the Sherpa ONNX Silero VAD command for one prepared WAV file."""
    return (
        str(silero_vad_path),
        f"--silero-vad-model={model_path}",
        f"--silero-vad-threshold={threshold:g}",
        f"--silero-vad-min-silence-duration={min_silence_seconds:g}",
        f"--silero-vad-min-speech-duration={min_speech_seconds:g}",
        "--vad-num-threads=1",
        "--print-args=false",
        str(input_wav_path),
        str(output_wav_path),
    )


def build_deep_filter_command(
    deep_filter_path: Path,
    input_wav_path: Path,
    output_dir: Path,
    *,
    post_filter: bool,
) -> tuple[str, ...]:
    """Build the DeepFilterNet command for one prepared WAV file."""
    command = [str(deep_filter_path), "-D"]
    if post_filter:
        command.append("--pf")
    command.extend(("-o", str(output_dir), str(input_wav_path)))
    return tuple(command)


def build_rnnoise_prepare_command(
    ffmpeg_path: Path,
    source_path: Path,
    output_raw_path: Path,
) -> tuple[str, ...]:
    """Build the ffmpeg command that prepares 48 kHz mono raw PCM for RNNoise."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "48000",
        "-f",
        "s16le",
        FFMPEG_AUDIO_CODEC_ARG,
        "pcm_s16le",
        str(output_raw_path),
    )


def build_rnnoise_command(
    rnnoise_path: Path,
    input_raw_path: Path,
    output_raw_path: Path,
) -> tuple[str, ...]:
    """Build the RNNoise command for one prepared raw PCM file."""
    return (
        str(rnnoise_path),
        "denoise",
        "--input",
        str(input_raw_path),
        "--output",
        str(output_raw_path),
        "--overwrite",
        "--json",
    )


def build_dpdfnet_command(
    dpdfnet_path: Path,
    input_path: Path,
    output_wav_path: Path,
    *,
    attn_limit_db: float,
) -> tuple[str, ...]:
    """Build the DPDFNet command for one source audio file."""
    return (
        str(dpdfnet_path),
        "enhance",
        "--attn-limit-db",
        f"{attn_limit_db:g}",
        str(input_path),
        str(output_wav_path),
    )


def build_rnnoise_encode_command(
    ffmpeg_path: Path,
    source_raw_path: Path,
    output_path: Path,
) -> tuple[str, ...]:
    """Build the ffmpeg command that encodes RNNoise raw PCM output as MP3."""
    return (
        str(ffmpeg_path),
        "-y",
        "-f",
        "s16le",
        "-ar",
        "48000",
        "-ac",
        "1",
        "-i",
        str(source_raw_path),
        "-vn",
        FFMPEG_AUDIO_CODEC_ARG,
        "libmp3lame",
        "-q:a",
        "4",
        str(output_path),
    )


def build_spleeter_prepare_command(
    ffmpeg_path: Path,
    source_path: Path,
    output_wav_path: Path,
) -> tuple[str, ...]:
    """Build the ffmpeg command that prepares 44.1 kHz stereo WAV for Spleeter."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-ac",
        "2",
        "-ar",
        "44100",
        FFMPEG_AUDIO_CODEC_ARG,
        "pcm_s16le",
        str(output_wav_path),
    )


def build_spleeter_command(
    spleeter_path: Path,
    vocals_model_path: Path,
    accompaniment_model_path: Path,
    input_wav_path: Path,
    output_dir: Path,
) -> tuple[str, ...]:
    """Build the Sherpa Spleeter command used for voice-only extraction."""
    return (
        str(spleeter_path),
        f"--spleeter-vocals={vocals_model_path}",
        f"--spleeter-accompaniment={accompaniment_model_path}",
        f"--input-wav={input_wav_path}",
        f"--output-vocals-wav={output_dir / 'vocals.wav'}",
        f"--output-accompaniment-wav={output_dir / 'accompaniment.wav'}",
        "--num-threads=1",
    )


def build_mp3_encode_command(
    ffmpeg_path: Path,
    source_path: Path,
    output_path: Path,
) -> tuple[str, ...]:
    """Build the ffmpeg command used to encode processed WAV output as MP3."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        FFMPEG_AUDIO_CODEC_ARG,
        "libmp3lame",
        "-q:a",
        "4",
        str(output_path),
    )


def build_playback_segment_filters(start_ms: int, end_ms: int | None = None) -> str:
    """Build filters for a temporary native playback segment."""
    start_s = max(0, int(start_ms)) / 1000
    if end_ms is None:
        return f"atrim=start={start_s:.3f},asetpts=PTS-STARTPTS"
    end_s = max(start_s, int(end_ms) / 1000)
    return f"atrim=start={start_s:.3f}:end={end_s:.3f},asetpts=PTS-STARTPTS"
