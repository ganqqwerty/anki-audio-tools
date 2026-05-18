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
    for path in _python_files(root):
        relative_path = _relative_posix(root, path)
        lines = _physical_line_count(path)
        violation = FileLineViolation(relative_path=relative_path, lines=lines)
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

