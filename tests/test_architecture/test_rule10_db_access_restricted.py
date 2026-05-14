"""Rule 10: direct collection/database access stays in db_helpers.py."""

from __future__ import annotations

import re

from .conftest import ADDON_DIR

ALLOWED_FILE = ADDON_DIR / "db_helpers.py"
PATTERNS = [
    r"\bcol\.db\.",
    r"\bcol\.models\.",
    r"\bcol\.decks\.",
    r"\bmw\.col\.db\.",
    r"\bmw\.col\.models\.",
    r"\bmw\.col\.decks\.",
]


def test_database_access_is_isolated() -> None:
    violations: list[str] = []
    for path in ADDON_DIR.rglob("*.py"):
        if path == ALLOWED_FILE or "__pycache__" in path.parts:
            continue
        for line_no, line in enumerate(path.read_text().splitlines(), start=1):
            if line.strip().startswith("#"):
                continue
            if any(re.search(pattern, line) for pattern in PATTERNS):
                violations.append(f"{path.relative_to(ADDON_DIR)}:{line_no}: {line.strip()}")
    assert violations == [], "\n".join(violations)
