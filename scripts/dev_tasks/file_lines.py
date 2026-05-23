"""File length policy checks for hand-maintained Python sources."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

WARN_LIMIT = 400
ERROR_LIMIT = 500

SCAN_DIRS = (
    "addon/anki_audio_quick_editor",
    "tests",
    "e2e",
    "scripts",
)

IGNORED_PATH_PARTS = {
    "__pycache__",
    ".pytest_cache",
    "vendor",
    "templates",
    "aqe_artifacts",
    ".mypy_cache",
}

GENERATED_PYTHON_FILES = {
    "addon/anki_audio_quick_editor/contracts_generated.py",
}


@dataclass(frozen=True)
class FileLineAllowance:
    """A file-specific line cap with an explicit temporary reason."""

    relative_path: str
    max_lines: int
    reason: str


PYTHON_FILE_LINE_ALLOWLIST: tuple[FileLineAllowance, ...] = (
    FileLineAllowance(
        relative_path="addon/anki_audio_quick_editor/audio_commands.py",
        max_lines=453,
        reason="Legacy command helpers still share one import-safe module.",
    ),
    FileLineAllowance(
        relative_path="addon/anki_audio_quick_editor/audio_noise_reduction.py",
        max_lines=479,
        reason="Noise-reduction renderers have not been split by backend yet.",
    ),
    FileLineAllowance(
        relative_path="addon/anki_audio_quick_editor/audio_pitch_hum.py",
        max_lines=485,
        reason="Pitch-hum rendering paths remain co-located pending extraction.",
    ),
    FileLineAllowance(
        relative_path="addon/anki_audio_quick_editor/audio_processor.py",
        max_lines=500,
        reason="Processor orchestration still centralizes multiple edit pipelines.",
    ),
    FileLineAllowance(
        relative_path="addon/anki_audio_quick_editor/batch_operations.py",
        max_lines=409,
        reason="Batch note-processing orchestration remains in one module for now.",
    ),
    FileLineAllowance(
        relative_path="addon/anki_audio_quick_editor/diagnostics_runtime.py",
        max_lines=481,
        reason="Runtime diagnostics lifecycle and reporting are still coupled here.",
    ),
    FileLineAllowance(
        relative_path="addon/anki_audio_quick_editor/editor_processing.py",
        max_lines=580,
        reason="Editor processing callbacks and parameterized status remount paths still need a dedicated refactor pass.",
    ),
    FileLineAllowance(
        relative_path="addon/anki_audio_quick_editor/editor_region_delete.py",
        max_lines=430,
        reason="Region-delete callbacks still share remount, playback, and status orchestration in one module.",
    ),
    FileLineAllowance(
        relative_path="addon/anki_audio_quick_editor/support.py",
        max_lines=483,
        reason="Support report rendering and incident formatting remain combined.",
    ),
    FileLineAllowance(
        relative_path="e2e/test_editor_playback_workflow.py",
        max_lines=431,
        reason="Playback workflow coverage is still concentrated in one end-to-end file.",
    ),
    FileLineAllowance(
        relative_path="scripts/release.py",
        max_lines=496,
        reason="Release packaging flow remains centralized in the legacy script.",
    ),
    FileLineAllowance(
        relative_path="scripts/release_assets.py",
        max_lines=491,
        reason="Release asset staging is still grouped by platform in one script.",
    ),
    FileLineAllowance(
        relative_path="tests/test_audio_commands.py",
        max_lines=473,
        reason="Audio command coverage has not yet been split by command family.",
    ),
    FileLineAllowance(
        relative_path="tests/test_audio_rendering.py",
        max_lines=465,
        reason="Rendering coverage remains in one integration-heavy test module.",
    ),
    FileLineAllowance(
        relative_path="tests/test_batch_visualization.py",
        max_lines=483,
        reason="Batch visualization permutations still live in one regression file.",
    ),
    FileLineAllowance(
        relative_path="tests/test_diagnostics.py",
        max_lines=474,
        reason="Diagnostics probe coverage is still concentrated in one module.",
    ),
    FileLineAllowance(
        relative_path="tests/test_editor_bridge_commands.py",
        max_lines=463,
        reason="Editor bridge command routing remains covered in one focused file.",
    ),
    FileLineAllowance(
        relative_path="tests/test_editor_integration.py",
        max_lines=510,
        reason="Editor integration smoke coverage, settings lifecycle, and remount regressions are still bundled together.",
    ),
    FileLineAllowance(
        relative_path="tests/test_editor_noise_reduction_callbacks.py",
        max_lines=520,
        reason="Noise-reduction callback matrix and remount regressions are still maintained in one test file.",
    ),
    FileLineAllowance(
        relative_path="tests/test_release_assets.py",
        max_lines=445,
        reason="Release asset staging checks still share a single regression module.",
    ),
    FileLineAllowance(
        relative_path="tests/test_support.py",
        max_lines=407,
        reason="Support-report regression coverage remains grouped in one file.",
    ),
)


@dataclass(frozen=True)
class FileLineViolation:
    """A file whose physical line count crosses a policy threshold."""

    relative_path: str
    lines: int


@dataclass(frozen=True)
class FileLineReport:
    """Warnings and errors from a file length scan."""

    warnings: list[FileLineViolation]
    errors: list[FileLineViolation]

    @property
    def exit_code(self) -> int:
        return 1 if self.errors else 0


def scan_python_file_lengths(root: Path) -> FileLineReport:
    """Scan hand-maintained Python files below ``root`` for line limit violations."""

    warnings: list[FileLineViolation] = []
    errors: list[FileLineViolation] = []
    allowances = {
        item.relative_path: item
        for item in PYTHON_FILE_LINE_ALLOWLIST
    }
    for path in _python_files(root):
        relative_path = _relative_posix(root, path)
        lines = _physical_line_count(path)
        violation = FileLineViolation(relative_path=relative_path, lines=lines)
        allowance = allowances.get(relative_path)
        if allowance is not None:
            if lines > allowance.max_lines:
                errors.append(violation)
            continue
        if lines > ERROR_LIMIT:
            errors.append(violation)
        elif lines > WARN_LIMIT:
            warnings.append(violation)
    return FileLineReport(
        warnings=sorted(warnings, key=lambda item: item.relative_path),
        errors=sorted(errors, key=lambda item: item.relative_path),
    )


def format_python_file_length_report(report: FileLineReport) -> str:
    """Return a stable, human-readable report for the Python file length scan."""

    lines: list[str] = []
    if report.warnings:
        lines.append(f"WARNING: {len(report.warnings)} Python file(s) exceed {WARN_LIMIT} lines:")
        lines.extend(f"  {item.relative_path}: {item.lines}" for item in report.warnings)
    if report.errors:
        lines.append(f"ERROR: {len(report.errors)} Python file(s) exceed {ERROR_LIMIT} lines:")
        lines.extend(f"  {item.relative_path}: {item.lines}" for item in report.errors)
    if not lines:
        lines.append(f"PASS: no hand-maintained Python files exceed {WARN_LIMIT} lines.")
    return "\n".join(lines)


def is_generated_python_file(root: Path, path: Path) -> bool:
    """Return whether ``path`` is a generated Python file exempt from line policy."""

    return _relative_posix(root, path) in GENERATED_PYTHON_FILES


def python_file_line_allowance(root: Path, path: Path) -> FileLineAllowance | None:
    """Return the explicit allowlist entry for ``path``, if any."""

    relative = _relative_posix(root, path)
    return next((item for item in PYTHON_FILE_LINE_ALLOWLIST if item.relative_path == relative), None)


def _python_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for scan_dir in SCAN_DIRS:
        base = root / scan_dir
        if not base.exists():
            continue
        paths.extend(
            path
            for path in base.rglob("*.py")
            if _is_hand_maintained_python_file(root, path)
        )
    return sorted(paths)


def _is_hand_maintained_python_file(root: Path, path: Path) -> bool:
    relative = path.relative_to(root)
    if any(part in IGNORED_PATH_PARTS for part in relative.parts):
        return False
    return not is_generated_python_file(root, path)


def _physical_line_count(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    if not text:
        return 0
    return len(text.splitlines())


def _relative_posix(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()
