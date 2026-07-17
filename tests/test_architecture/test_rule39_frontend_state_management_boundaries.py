"""Rule 39: frontend state-management packages keep their public boundaries."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / ".dependency-cruiser.js"
DEPCRUISE = ROOT / "settings_ui" / "node_modules" / ".bin" / "depcruise"


def test_state_management_dependency_rules_are_active() -> None:
    source = CONFIG.read_text(encoding="utf-8")
    assert "rule39-sm-a01-transport-does-not-import-practice" in source
    assert "rule39-sm-a01-state-management-public-entry-only" in source
    assert "rule49-sm-a11-state-management-no-cycles" in source
    assert (ROOT / "settings_ui/src/editor-inline/transport/index.ts").is_file()
    assert (ROOT / "settings_ui/src/editor-inline/practice/index.ts").is_file()


def test_dependency_cruiser_rejects_external_deep_import_canary(tmp_path: Path) -> None:
    source_root = tmp_path / "settings_ui/src/editor-inline"
    transport = source_root / "transport"
    transport.mkdir(parents=True)
    (transport / "private.ts").write_text("export const value = 1;\n", encoding="utf-8")
    (transport / "index.ts").write_text(
        'export { value } from "./private.js";\n',
        encoding="utf-8",
    )
    consumer = source_root / "consumer.ts"
    consumer.write_text(
        'import { value } from "./transport/private.js"; void value;\n',
        encoding="utf-8",
    )
    config = tmp_path / "dependency-cruiser.cjs"
    config.write_text(
        f"const base = require({json.dumps(str(CONFIG))});\n"
        'module.exports = {...base, options: {...base.options, includeOnly: "^settings_ui/src"}};\n',
        encoding="utf-8",
    )

    rejected = _cruise(tmp_path, config)
    assert rejected.returncode != 0
    assert "rule39-sm-a01-state-management-public-entry-only" in rejected.stdout

    consumer.write_text(
        'import { value } from "./transport/index.js"; void value;\n',
        encoding="utf-8",
    )
    allowed = _cruise(tmp_path, config)
    assert allowed.returncode == 0, allowed.stdout + allowed.stderr


def _cruise(cwd: Path, config: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(DEPCRUISE), "-c", str(config), "settings_ui/src"],
        cwd=cwd,
        capture_output=True,
        check=False,
        text=True,
    )
