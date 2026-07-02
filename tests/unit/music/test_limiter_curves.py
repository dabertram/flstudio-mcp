"""Unit tests for Fruity Limiter COMP calibration curves (pure).

Focus: the bidirectional ratio trap (never return norm < 0.5), table-interp
monotonicity, and roundtrips within the calibrated range.
"""
from __future__ import annotations

import pytest

from fl_studio_mcp.music import limiter_curves as lc

pytestmark = pytest.mark.unit


class TestThreshold:
    def test_endpoints(self):
        assert lc.norm_to_threshold(0.0) == pytest.approx(-60.0)
        assert lc.norm_to_threshold(1.0) == pytest.approx(0.0)
        assert lc.norm_to_threshold(0.5) == pytest.approx(-11.2)

    def test_inverse(self):
        assert lc.threshold_to_norm(-60.0) == pytest.approx(0.0)
        assert lc.threshold_to_norm(0.0) == pytest.approx(1.0)

    @pytest.mark.parametrize("db", [-35.4, -22.0, -11.2, -4.1, -1.0])
    def test_roundtrip(self, db):
        assert lc.norm_to_threshold(lc.threshold_to_norm(db)) == pytest.approx(db, abs=0.2)


class TestRatioTrap:
    def test_never_below_half(self):
        # any ratio maps to norm >= 0.5 (downward compression half only)
        for ratio in [0.1, 0.5, 1.0, 2.0, 20.0]:
            assert lc.ratio_to_norm(ratio) >= 0.5

    def test_unity(self):
        assert lc.ratio_to_norm(1.0) == pytest.approx(0.5)
        assert lc.norm_to_ratio(0.5) == pytest.approx(1.0)

    def test_below_half_is_no_compression(self):
        assert lc.norm_to_ratio(0.4) == 1.0
        assert lc.norm_to_ratio(0.0) == 1.0

    def test_max_ratio(self):
        assert lc.ratio_to_norm(20.0) == pytest.approx(1.0)
        assert lc.norm_to_ratio(1.0) == pytest.approx(20.0)

    def test_ratio_clamped_below_one(self):
        # ratio < 1 clamps to 1 -> unity norm, never expansion
        assert lc.ratio_to_norm(0.25) == pytest.approx(0.5)


class TestTimeParams:
    @pytest.mark.parametrize("ms", [0.73, 42.77, 209.79, 1000.0])
    def test_attack_roundtrip(self, ms):
        assert lc.norm_to_attack_ms(lc.attack_ms_to_norm(ms)) == pytest.approx(ms, rel=0.02)

    @pytest.mark.parametrize("ms", [1.46, 85.53, 574.0, 2000.0])
    def test_release_roundtrip(self, ms):
        assert lc.norm_to_release_ms(lc.release_ms_to_norm(ms)) == pytest.approx(ms, rel=0.02)

    def test_attack_monotonic(self):
        prev = -1.0
        for n in [i / 20 for i in range(21)]:
            v = lc.norm_to_attack_ms(n)
            assert v >= prev
            prev = v


class TestKneeAndMakeup:
    def test_knee_center(self):
        assert lc.knee_pct_to_norm(0.0) == pytest.approx(0.5)
        assert lc.norm_to_knee_pct(0.5) == pytest.approx(0.0)

    def test_knee_endpoints(self):
        assert lc.knee_pct_to_norm(-100.0) == pytest.approx(0.0)
        assert lc.knee_pct_to_norm(100.0) == pytest.approx(1.0)

    def test_makeup(self):
        assert lc.makeup_db_to_norm(0.0) == pytest.approx(0.5)
        assert lc.norm_to_makeup_db(0.5) == pytest.approx(0.0)
        # negative makeup clamps to 0 dB (norm 0.5)
        assert lc.makeup_db_to_norm(-5.0) == pytest.approx(0.5)
