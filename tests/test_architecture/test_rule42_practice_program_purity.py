"""Rule 42: practice reducers remain pure and side-effect free."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRACTICE = ROOT / "settings_ui/src/editor-inline/practice"


def test_practice_programs_have_structural_purity_canaries() -> None:
    architecture = (ROOT / "settings_ui/tests/state-management-architecture.test.ts").read_text(
        encoding="utf-8"
    )
    assert "Rule 42 / SM-A04" in architecture
    assert "forbiddenImports" in architecture
    assert "referencedGlobals" in architecture
    assert {path.name for path in PRACTICE.glob("*.ts")} >= {
        "chorusing.ts",
        "once.ts",
        "record-once.ts",
        "repeat.ts",
        "reducer.ts",
        "runtime.ts",
    }
