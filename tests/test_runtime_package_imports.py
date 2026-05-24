"""Runtime import smoke tests for numeric Anki add-on package names."""

from __future__ import annotations

import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
ADDON_DIR = PROJECT_ROOT / "addon" / "anki_audio_quick_editor"


def test_runtime_helpers_import_siblings_under_numeric_package(tmp_path: Path) -> None:
    """Anki imports AnkiWeb/dev add-ons by numeric folder id, not source package name."""
    package_dir = tmp_path / "addons21" / "123456789"
    package_dir.mkdir(parents=True)
    for filename in (
        "audio_processor_rendering_portal.py",
        "batch_operations_helpers.py",
    ):
        shutil.copy2(ADDON_DIR / filename, package_dir / filename)
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "audio_state.py").write_text(
        textwrap.dedent(
            """
            class AudioEditState:
                pass

            class AudioProcessingConfig:
                def __init__(self, denoise_algorithm="standard"):
                    self.denoise_algorithm = denoise_algorithm
            """
        ),
        encoding="utf-8",
    )
    (package_dir / "audio_types.py").write_text(
        "class AudioProcessingResult:\n    pass\n",
        encoding="utf-8",
    )
    (package_dir / "audio_processor.py").write_text(
        textwrap.dedent(
            """
            from pathlib import Path

            def _sync_rendering_dependencies():
                pass

            def render_dpdfnet_audio(*args, **kwargs):
                return "dpdfnet"

            def render_noise_reduced_audio(*args, **kwargs):
                return "standard"

            def render_rnnoise_audio(*args, **kwargs):
                return "rnnoise"

            def render_voice_only_audio(*args, **kwargs):
                return "voice_only"

            class _Rendering:
                @staticmethod
                def make_output_filename(source_filename, now=None, token=None, *, output_format="mp3"):
                    return f"{source_filename}.{output_format}"

            _audio_rendering = _Rendering()
            _audio_noise_reduction = object()
            _audio_pitch_hum = object()
            uuid = object()
            _ORIGINAL_MAKE_PLAYBACK_SEGMENT_FILENAME = lambda source_filename, start_ms, token=None: source_filename
            """
        ),
        encoding="utf-8",
    )
    (package_dir / "batch_operations.py").write_text(
        textwrap.dedent(
            """
            from dataclasses import dataclass

            @dataclass(frozen=True)
            class BatchNoteResult:
                note_id: int
                status: str
                message: str

            def render_noise_reduced_audio(*args, **kwargs):
                return "batch-standard"
            """
        ),
        encoding="utf-8",
    )

    script = textwrap.dedent(
        f"""
        import importlib
        import importlib.util
        import sys
        from pathlib import Path

        excluded_paths = {{
            "",
            {str(PROJECT_ROOT)!r},
            {str(PROJECT_ROOT / "addon")!r},
        }}
        sys.path = [{str(package_dir.parent)!r}] + [
            path for path in sys.path if path not in excluded_paths
        ]
        assert "anki_audio_quick_editor" not in sys.modules
        assert importlib.util.find_spec("anki_audio_quick_editor") is None

        portal = importlib.import_module("123456789.audio_processor_rendering_portal")
        assert portal._facade().__name__ == "123456789.audio_processor"
        assert portal.make_output_filename("clip", output_format="mp3") == "clip.mp3"

        helpers = importlib.import_module("123456789.batch_operations_helpers")
        assert helpers.skipped_batch_note(7, "missing").note_id == 7
        config = importlib.import_module("123456789.audio_state").AudioProcessingConfig()
        assert helpers.render_batch_denoise(
            Path("clip.mp3"),
            config,
            Path("out.mp3"),
        ) == "batch-standard"
        """
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
