from __future__ import annotations

from pathlib import Path

import pytest

from scripts.dev_tasks import e2e_preflight


def test_ensure_e2e_runtime_artifacts_skips_build_when_artifacts_exist(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.js"
    artifact.write_text("ok", encoding="utf-8")
    called = False

    def fake_build() -> int:
        nonlocal called
        called = True
        return 0

    e2e_preflight.ensure_e2e_runtime_artifacts(
        build_ui=fake_build,
        required_paths=(artifact,),
    )

    assert called is False


def test_ensure_e2e_runtime_artifacts_builds_missing_files(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.js"
    calls: list[str] = []

    def fake_build() -> int:
        calls.append("build")
        artifact.write_text("built", encoding="utf-8")
        return 0

    e2e_preflight.ensure_e2e_runtime_artifacts(
        build_ui=fake_build,
        required_paths=(artifact,),
    )

    assert calls == ["build"]
    assert artifact.read_text(encoding="utf-8") == "built"


def test_ensure_e2e_runtime_artifacts_raises_when_build_fails(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.js"

    with pytest.raises(RuntimeError, match="Missing generated e2e runtime artifacts"):
        e2e_preflight.ensure_e2e_runtime_artifacts(
            build_ui=lambda: 23,
            required_paths=(artifact,),
        )


def test_ensure_e2e_runtime_artifacts_raises_when_artifacts_still_missing(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.js"

    with pytest.raises(RuntimeError, match="still missing after build-ui"):
        e2e_preflight.ensure_e2e_runtime_artifacts(
            build_ui=lambda: 0,
            required_paths=(artifact,),
        )
