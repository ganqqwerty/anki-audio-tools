"""Shared exception types for Anki Audio Quick Editor."""


class AudioQuickEditorError(Exception):
    """Base exception for add-on failures that can be shown to users."""


class MissingFfmpegError(AudioQuickEditorError):
    """Raised when ffmpeg or ffprobe cannot be found."""


class MissingDeepFilterError(AudioQuickEditorError):
    """Raised when DeepFilterNet's deep-filter executable cannot be found."""


class MissingMediaError(AudioQuickEditorError):
    """Raised when a referenced Anki media file does not exist."""


class UnsupportedAudioError(AudioQuickEditorError):
    """Raised when a field references an unsupported audio file."""


class InvalidEditStateError(AudioQuickEditorError):
    """Raised when requested edit settings cannot produce playable audio."""


class AudioProcessingError(AudioQuickEditorError):
    """Raised when ffmpeg fails to render a preview or final file."""
