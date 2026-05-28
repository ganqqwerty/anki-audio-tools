"""Low-level editor webview bridge helpers."""

from __future__ import annotations

from typing import Any


def main(editor: Any, callback: Any) -> None:
    """Run a callback on Anki's main thread."""
    editor.mw.taskman.run_on_main(callback)


def eval_with_callback(editor: Any, expression: str, callback: Any) -> None:
    """Evaluate JavaScript and deliver the result to a Python callback."""
    if hasattr(editor.web, "evalWithCallback"):
        editor.web.evalWithCallback(expression, callback)
        return
    page = editor.web.page() if hasattr(editor.web, "page") else None
    if page is not None and hasattr(page, "runJavaScript"):
        page.runJavaScript(expression, callback)
