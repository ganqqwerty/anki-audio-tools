"""Application lifetime holder for the single recorder service."""

from .service import RecorderService

RECORDER_SERVICE = RecorderService()

__all__ = ["RECORDER_SERVICE"]
