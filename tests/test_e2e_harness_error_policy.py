from __future__ import annotations

import re

import pytest
from e2e.harness_error_policy import unexpected_messages


def test_error_policy_fails_closed_without_an_allowance() -> None:
    assert unexpected_messages(["addon: core import exploded"], ()) == (
        "addon: core import exploded",
    )


def test_error_policy_allows_only_the_reviewed_regex() -> None:
    messages = (
        "addon: AQE-MEDIA-002: expected missing fixture",
        "addon: unrelated failure",
    )

    assert unexpected_messages(messages, (r"AQE-MEDIA-002: expected missing fixture$",)) == (
        "addon: unrelated failure",
    )


def test_error_policy_rejects_invalid_allowance_regex() -> None:
    with pytest.raises(re.error):
        unexpected_messages(("failure",), ("[",))


def test_known_chromium_resize_observer_noise_is_narrowly_allowlisted() -> None:
    expected = (
        "1000000002.editor_bridge: editor frontend: ResizeObserver loop completed with undelivered "
        "notifications. | {'filename': 'http://127.0.0.1'}"
    )
    assert unexpected_messages((expected,), ()) == ()
    assert unexpected_messages(("other: ResizeObserver loop completed with undelivered notifications.",), ())
