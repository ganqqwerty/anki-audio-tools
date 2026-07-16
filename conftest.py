"""Repository-wide pytest collection policies."""

from __future__ import annotations

import pytest
from pytest_classification_policy import classification_errors, inferred_primary_marker

_SKIPPED_REPORTS: list[str] = []


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    root = config.rootpath
    errors: list[str] = []
    for item in items:
        path = item.path.relative_to(root).as_posix()
        markers = {marker.name for marker in item.iter_markers()}
        primary = inferred_primary_marker(path, markers)
        if not markers.intersection({"unit", "component", "in_anki_component", "e2e"}):
            item.add_marker(getattr(pytest.mark, primary))
            markers.add(primary)
        if "allow_managed_runtime" in markers and "external_runtime" not in markers:
            item.add_marker(pytest.mark.external_runtime)
            markers.add("external_runtime")
        errors.extend(classification_errors(item.nodeid, markers))
        persistence_markers = list(item.iter_markers("preserve_e2e_config"))
        if any(
            len(marker.args) != 1
            or not isinstance(marker.args[0], str)
            or not marker.args[0].strip()
            for marker in persistence_markers
        ):
            errors.append(
                f"{item.nodeid}: preserve_e2e_config requires one non-empty review reason"
            )
    if errors:
        raise pytest.UsageError("Invalid test classifications:\n" + "\n".join(errors))


def pytest_sessionstart(session: pytest.Session) -> None:
    assert session.config is not None
    _SKIPPED_REPORTS.clear()


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    if report.skipped:
        _SKIPPED_REPORTS.append(f"{report.nodeid} ({report.when})")


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if not _SKIPPED_REPORTS:
        return
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    message = "Collected tests may not skip or xfail at runtime:\n" + "\n".join(_SKIPPED_REPORTS)
    if reporter is not None:
        reporter.write_sep("=", message, red=True)
    if exitstatus == pytest.ExitCode.OK:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
