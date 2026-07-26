from pathlib import Path

QUALITY_WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "quality.yml"


def test_quality_workflow_runs_only_for_main_pushes() -> None:
    workflow = QUALITY_WORKFLOW.read_text(encoding="utf-8")
    trigger_block = workflow.split("on:\n", 1)[1].split("\nconcurrency:", 1)[0]

    assert trigger_block == "  push:\n    branches: [main]\n"
    assert "github.event_name" not in workflow
