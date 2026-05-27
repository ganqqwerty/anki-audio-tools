"""Typed audio edit state and configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .audio_formats import DEFAULT_OUTPUT_FORMAT, normalize_output_format
from .audio_pause_settings import (
    bool_or_default,
    clamp_pause_seconds,
    clamp_pause_threshold,
    pause_aggressiveness_or_default,
    pause_detection_algorithm_or_default,
    preset_for_pause_detection,
)
from .dpdfnet_settings import (
    DEFAULT_DPDFNET_ATTENUATION_LIMIT_DB,
    normalize_dpdfnet_attn_limit_db,
)
from .errors import InvalidEditStateError
from .ffmpeg_defaults import default_ffmpeg_path

ConfigValue = str | int | float | bool
GraphVoiceRange = str
GraphRecordingCondition = str
GraphSmoothness = str
GraphVoiceLock = str


@dataclass(frozen=True)
class AudioProcessingConfig:
    """Runtime audio processing settings loaded from add-on config."""

    speed_step: float = 1.5
    min_speed: float = 0.2
    max_speed: float = 5.0
    volume_step_db: float = 15.0
    min_volume_db: float = -40.0
    max_volume_db: float = 40.0
    pause_aggressiveness: str = "normal"
    pause_detection_algorithm: str = "silencedetect"
    pause_silencedetect_threshold_db: float = -45.0
    pause_silencedetect_min_silence_seconds: float = 0.30
    pause_silencedetect_min_speech_seconds: float = 0.10
    pause_silencedetect_preprocess_denoise: bool = True
    pause_silero_threshold: float = 0.50
    pause_silero_min_silence_seconds: float = 0.45
    pause_silero_min_speech_seconds: float = 0.10
    pause_silero_preprocess_denoise: bool = False
    output_format: str = DEFAULT_OUTPUT_FORMAT
    ffmpeg_path: str = field(default_factory=default_ffmpeg_path)
    deep_filter_post_filter: bool = True
    dpdfnet_attn_limit_db: float = DEFAULT_DPDFNET_ATTENUATION_LIMIT_DB
    denoise_algorithm: str = "standard"
    pitch_hum_mode: str = "direct"
    show_ffmpeg_commands: bool = False
    graph_voice_range: GraphVoiceRange = "general"
    graph_recording_condition: GraphRecordingCondition = "auto"
    graph_smoothness: GraphSmoothness = "very_smooth"
    graph_connect_short_dropouts_ms: int = 240
    graph_voice_lock: GraphVoiceLock = "balanced"

    @classmethod
    def from_config(cls, config: dict[str, ConfigValue]) -> "AudioProcessingConfig":
        """Build typed settings from persisted add-on config."""
        pause_aggressiveness = pause_aggressiveness_or_default(
            config.get("pause_aggressiveness", cls.pause_aggressiveness)
        )
        pause_detection_algorithm = pause_detection_algorithm_or_default(
            config.get("pause_detection_algorithm", cls.pause_detection_algorithm)
        )
        silencedetect_preset = preset_for_pause_detection("silencedetect", pause_aggressiveness)
        silero_preset = preset_for_pause_detection("silero_vad", pause_aggressiveness)
        return cls(
            speed_step=float(config.get("speed_step", cls.speed_step)),
            min_speed=float(config.get("min_speed", cls.min_speed)),
            max_speed=float(config.get("max_speed", cls.max_speed)),
            volume_step_db=float(config.get("volume_step_db", cls.volume_step_db)),
            min_volume_db=float(config.get("min_volume_db", cls.min_volume_db)),
            max_volume_db=float(config.get("max_volume_db", cls.max_volume_db)),
            pause_aggressiveness=pause_aggressiveness,
            pause_detection_algorithm=pause_detection_algorithm,
            pause_silencedetect_threshold_db=clamp_pause_threshold(
                "silencedetect",
                config.get(
                    "pause_silencedetect_threshold_db",
                    silencedetect_preset.threshold,
                ),
                silencedetect_preset.threshold,
            ),
            pause_silencedetect_min_silence_seconds=clamp_pause_seconds(
                config.get(
                    "pause_silencedetect_min_silence_seconds",
                    silencedetect_preset.min_silence_seconds,
                ),
                silencedetect_preset.min_silence_seconds,
            ),
            pause_silencedetect_min_speech_seconds=clamp_pause_seconds(
                config.get(
                    "pause_silencedetect_min_speech_seconds",
                    silencedetect_preset.min_speech_seconds,
                ),
                silencedetect_preset.min_speech_seconds,
            ),
            pause_silencedetect_preprocess_denoise=bool_or_default(
                config.get(
                    "pause_silencedetect_preprocess_denoise",
                    silencedetect_preset.preprocess_denoise,
                ),
                silencedetect_preset.preprocess_denoise,
            ),
            pause_silero_threshold=clamp_pause_threshold(
                "silero_vad",
                config.get("pause_silero_threshold", silero_preset.threshold),
                silero_preset.threshold,
            ),
            pause_silero_min_silence_seconds=clamp_pause_seconds(
                config.get(
                    "pause_silero_min_silence_seconds",
                    silero_preset.min_silence_seconds,
                ),
                silero_preset.min_silence_seconds,
            ),
            pause_silero_min_speech_seconds=clamp_pause_seconds(
                config.get(
                    "pause_silero_min_speech_seconds",
                    silero_preset.min_speech_seconds,
                ),
                silero_preset.min_speech_seconds,
            ),
            pause_silero_preprocess_denoise=bool_or_default(
                config.get(
                    "pause_silero_preprocess_denoise",
                    silero_preset.preprocess_denoise,
                ),
                silero_preset.preprocess_denoise,
            ),
            output_format=normalize_output_format(config.get("output_format", cls.output_format)),
            ffmpeg_path=str(config.get("ffmpeg_path", default_ffmpeg_path())),
            deep_filter_post_filter=bool(
                config.get("deep_filter_post_filter", cls.deep_filter_post_filter)
            ),
            dpdfnet_attn_limit_db=normalize_dpdfnet_attn_limit_db(
                config.get("dpdfnet_attn_limit_db", cls.dpdfnet_attn_limit_db)
            ),
            denoise_algorithm=str(config.get("denoise_algorithm", cls.denoise_algorithm)),
            pitch_hum_mode=str(config.get("pitch_hum_mode", cls.pitch_hum_mode)),
            show_ffmpeg_commands=bool(
                config.get("show_ffmpeg_commands", cls.show_ffmpeg_commands)
            ),
            graph_voice_range=str(config.get("graph_voice_range", cls.graph_voice_range)),
            graph_recording_condition=str(
                config.get("graph_recording_condition", cls.graph_recording_condition)
            ),
            graph_smoothness=str(config.get("graph_smoothness", cls.graph_smoothness)),
            graph_connect_short_dropouts_ms=int(
                config.get(
                    "graph_connect_short_dropouts_ms",
                    cls.graph_connect_short_dropouts_ms,
                )
            ),
            graph_voice_lock=str(config.get("graph_voice_lock", cls.graph_voice_lock)),
        )


@dataclass(frozen=True)
class AudioEditState:
    """Current non-destructive edit state for one source audio file."""

    source_file: str
    left_trim_ms: int = 0
    right_trim_ms: int = 0
    speed: float = 1.0
    volume_db: float = 0.0
    remove_internal_pauses_enabled: bool = False

    def trim_left(self, step_ms: int) -> "AudioEditState":
        """Return a state with additional left trim."""
        return replace(self, left_trim_ms=max(0, self.left_trim_ms + step_ms))

    def untrim_left(self, step_ms: int) -> "AudioEditState":
        """Return a state with less left trim."""
        return replace(self, left_trim_ms=max(0, self.left_trim_ms - step_ms))

    def trim_right(self, step_ms: int) -> "AudioEditState":
        """Return a state with additional right trim."""
        return replace(self, right_trim_ms=max(0, self.right_trim_ms + step_ms))

    def untrim_right(self, step_ms: int) -> "AudioEditState":
        """Return a state with less right trim."""
        return replace(self, right_trim_ms=max(0, self.right_trim_ms - step_ms))

    def faster(self, config: AudioProcessingConfig) -> "AudioEditState":
        """Return a state with speed multiplied by the configured factor."""
        return replace(self, speed=round(min(config.max_speed, self.speed * config.speed_step), 2))

    def slower(self, config: AudioProcessingConfig) -> "AudioEditState":
        """Return a state with speed divided by the configured factor."""
        return replace(self, speed=round(max(config.min_speed, self.speed / config.speed_step), 2))

    def volume_up(self, config: AudioProcessingConfig) -> "AudioEditState":
        """Return a state with volume increased by the configured dB step."""
        return replace(
            self,
            volume_db=round(min(config.max_volume_db, self.volume_db + config.volume_step_db), 2),
        )

    def volume_down(self, config: AudioProcessingConfig) -> "AudioEditState":
        """Return a state with volume decreased by the configured dB step."""
        return replace(
            self,
            volume_db=round(max(config.min_volume_db, self.volume_db - config.volume_step_db), 2),
        )

    def toggle_internal_pauses(self) -> "AudioEditState":
        """Return a state with internal pause removal enabled."""
        return replace(self, remove_internal_pauses_enabled=True)

    def validate(self, duration_ms: int, config: AudioProcessingConfig) -> None:
        """Raise if this edit state cannot render playable audio."""
        if self.speed < config.min_speed or self.speed > config.max_speed:
            raise InvalidEditStateError("Invalid speed value.")
        if self.volume_db < config.min_volume_db or self.volume_db > config.max_volume_db:
            raise InvalidEditStateError("Invalid volume value.")
        if self.left_trim_ms < 0 or self.right_trim_ms < 0:
            raise InvalidEditStateError("Trim values cannot be negative.")
        if self.left_trim_ms + self.right_trim_ms >= max(0, duration_ms - 50):
            raise InvalidEditStateError("Trim amount would leave no playable audio.")
