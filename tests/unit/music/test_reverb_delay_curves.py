"""Unit tests for Fruity Reeverb 2 + Fruity Delay 3 curves (pure)."""
from __future__ import annotations

import pytest

from fl_studio_mcp.music import reverb_delay_curves as rd

pytestmark = pytest.mark.unit


class TestReverb:
    def test_decay(self):
        assert rd.decay_to_norm(0.1) == pytest.approx(0.0)
        assert rd.decay_to_norm(20.0) == pytest.approx(1.0)
        assert rd.norm_to_decay(0.0) == pytest.approx(0.1)
        assert rd.norm_to_decay(1.0) == pytest.approx(20.0)

    def test_wet(self):
        assert rd.wet_to_norm(125.0) == pytest.approx(1.0)
        assert rd.norm_to_wet(0.8) == pytest.approx(100.0)

    def test_roomsize(self):
        assert rd.roomsize_to_norm(1.0) == pytest.approx(0.0)
        assert rd.roomsize_to_norm(100.0) == pytest.approx(1.0)
        assert rd.norm_to_roomsize(0.0) == pytest.approx(1.0)

    def test_highcut_off_sentinel(self):
        assert rd.norm_to_highcut_hz(1.0) is None
        assert rd.highcut_to_norm(500.0) == pytest.approx(0.0)

    def test_lowcut_off_sentinel(self):
        assert rd.norm_to_lowcut_hz(0.0) is None
        assert rd.lowcut_to_norm(100.0) == pytest.approx(rd.LOWCUT_MIN_NORM)


class TestDelay:
    def test_pct_linear(self):
        assert rd.delay_pct_to_norm(100.0) == pytest.approx(1.0)
        assert rd.norm_to_delay_pct(0.5) == pytest.approx(50.0)

    def test_feedback_safe_clamp(self):
        # default clamps at 100% -> 100/125 = 0.8
        assert rd.feedback_to_norm(125.0) == pytest.approx(0.8)
        # allow oscillation -> up to 125% -> 1.0
        assert rd.feedback_to_norm(125.0, allow_oscillation=True) == pytest.approx(1.0)

    def test_cutoff_endpoints(self):
        assert rd.norm_to_cutoff_hz(0.0) == pytest.approx(270.0)
        assert rd.norm_to_cutoff_hz(1.0) == pytest.approx(21985.0)

    @pytest.mark.parametrize("hz", [312.0, 1299.6, 5856.0, 15986.5])
    def test_cutoff_roundtrip(self, hz):
        assert rd.norm_to_cutoff_hz(rd.cutoff_hz_to_norm(hz)) == pytest.approx(hz, rel=0.02)

    def test_divisions(self):
        assert rd.division_norm("1/16") == pytest.approx(1 / 16)
        assert rd.division_norm("1/1") == pytest.approx(1.0)
        assert rd.nearest_division_index(1 / 16) == 0
        assert rd.nearest_division_index(1.0) == len(rd.DIVISIONS) - 1

    def test_unknown_division_raises(self):
        with pytest.raises(ValueError):
            rd.division_norm("1/3")

    def test_step_division_clamps(self):
        # stepping far past the top clamps to the last division
        assert rd.step_division(1 / 16, 99) == rd.DIVISIONS[-1]
        assert rd.step_division(1.0, -99) == rd.DIVISIONS[0]
