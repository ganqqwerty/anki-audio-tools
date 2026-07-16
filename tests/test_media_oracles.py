from __future__ import annotations

import math
from array import array

import pytest

from tests.media_oracles import db_ratio, difference_rms, rms, window_rms


def test_rms_and_db_ratio_use_signal_math_not_production_commands() -> None:
    reference = array("f", [math.sin(index / 10) * 0.1 for index in range(1_000)])
    doubled = array("f", [sample * 2 for sample in reference])

    assert rms(doubled) == pytest.approx(rms(reference) * 2)
    assert db_ratio(rms(reference), rms(doubled)) == pytest.approx(6.0206, abs=0.001)


@pytest.mark.parametrize(("reference", "measured"), [(0.0, 1.0), (1.0, 0.0)])
def test_db_ratio_rejects_silent_inputs(reference: float, measured: float) -> None:
    with pytest.raises(AssertionError, match="positive RMS"):
        db_ratio(reference, measured)


def test_window_rms_measures_only_the_requested_time_region() -> None:
    samples = array("f", [0.0] * 10 + [0.5] * 10)

    assert window_rms(samples, start_s=0.0, end_s=1.0, sample_rate=10) == 0.0
    assert window_rms(samples, start_s=1.0, end_s=2.0, sample_rate=10) == 0.5


def test_difference_rms_detects_a_changed_signal_window() -> None:
    reference = array("f", [0.0] * 10 + [0.25] * 10)
    measured = array("f", [0.0] * 10 + [0.5] * 10)

    assert difference_rms(
        reference,
        measured,
        start_s=1.0,
        end_s=2.0,
        sample_rate=10,
    ) == pytest.approx(0.25)
