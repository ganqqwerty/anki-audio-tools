"""Typed audio edit state and configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .errors import InvalidEditStateError


@dataclass(frozen=True)
class AudioProcessingConfig:
    """Runtime audio processing settings loaded from add-on config."""

    manual_trim_small_ms: int = 100
    manual_trim_large_ms: int = 500
    speed_step: float = 0.05
    min_speed: float = 0.75
    max_speed: float = 1.5
    edge_silence_threshold_db: int = -35
    edge_silence_min_ms: int = 100
    internal_pause_threshold_ms: int = 300
    internal_pause_target_gap_ms: int = 100
    output_format: str = "mp3"
    ffmpeg_path: str = ""
    show_ffmpeg_commands: bool = False

    @classmethod
    def from_config(cls, config: dict) -> "AudioProcessingConfig":
        """Build typed settings from persisted add-on config."""
        return cls(
            manual_trim_small_ms=int(config.get("manual_trim_small_ms", cls.manual_trim_small_ms)),
            manual_trim_large_ms=int(config.get("manual_trim_large_ms", cls.manual_trim_large_ms)),
            speed_step=float(config.get("speed_step", cls.speed_step)),
            min_speed=float(config.get("min_speed", cls.min_speed)),
            max_speed=float(config.get("max_speed", cls.max_speed)),
            edge_silence_threshold_db=int(
                config.get("edge_silence_threshold_db", cls.edge_silence_threshold_db)
            ),
            edge_silence_min_ms=int(config.get("edge_silence_min_ms", cls.edge_silence_min_ms)),
            internal_pause_threshold_ms=int(
                config.get("internal_pause_threshold_ms", cls.internal_pause_threshold_ms)
            ),
            internal_pause_target_gap_ms=int(
                config.get("internal_pause_target_gap_ms", cls.internal_pause_target_gap_ms)
            ),
            output_format=str(config.get("output_format", cls.output_format)),
            ffmpeg_path=str(config.get("ffmpeg_path", cls.ffmpeg_path)),
            show_ffmpeg_commands=bool(
                config.get("show_ffmpeg_commands", cls.show_ffmpeg_commands)
            ),
        )


@dataclass(frozen=True)
class AudioEditState:
    """Current non-destructive edit state for one source audio file."""

    source_file: str
    left_trim_ms: int = 0
    right_trim_ms: int = 0
    speed: float = 1.0
    edge_trim_enabled: bool = False
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
        """Return a state with speed increased by the configured step."""
        return replace(self, speed=round(min(config.max_speed, self.speed + config.speed_step), 2))

    def slower(self, config: AudioProcessingConfig) -> "AudioEditState":
        """Return a state with speed decreased by the configured step."""
        return replace(self, speed=round(max(config.min_speed, self.speed - config.speed_step), 2))

    def toggle_edge_trim(self) -> "AudioEditState":
        """Return a state with edge silence trimming enabled."""
        return replace(self, edge_trim_enabled=True)

    def toggle_internal_pauses(self) -> "AudioEditState":
        """Return a state with internal pause compression enabled."""
        return replace(self, remove_internal_pauses_enabled=True)

    def validate(self, duration_ms: int, config: AudioProcessingConfig) -> None:
        """Raise if this edit state cannot render playable audio."""
        if self.speed < config.min_speed or self.speed > config.max_speed:
            raise InvalidEditStateError("Invalid speed value.")
        if self.left_trim_ms < 0 or self.right_trim_ms < 0:
            raise InvalidEditStateError("Trim values cannot be negative.")
        if self.left_trim_ms + self.right_trim_ms >= max(0, duration_ms - 50):
            raise InvalidEditStateError("Trim amount would leave no playable audio.")
