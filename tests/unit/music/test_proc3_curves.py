"""Unit tests for FabFilter Pro-C 3 calibration curves (pure)."""
from __future__ import annotations

import pytest

from fl_studio_mcp.music import proc3_curves as pc

pytestmark = pytest.mark.unit


class TestLinearParams:
    def test_threshold(self):
        assert pc.threshold_to_norm(-60.0) == pytest.approx(0.0)
        assert pc.threshold_to_norm(0.0) == pytest.approx(1.0)
        assert pc.norm_to_threshold(0.5) == pytest.approx(-30.0)

    def test_knee(self):
        assert pc.knee_to_norm(0.0) == pytest.approx(0.0)
        assert pc.knee_to_norm(72.0) == pytest.approx(1.0)
        assert pc.norm_to_knee(0.5) == pytest.approx(36.0)

    def test_range(self):
        assert pc.range_to_norm(0.0) == pytest.approx(0.0)
        assert pc.range_to_norm(60.0) == pytest.approx(1.0)

    def test_mix_100pct_at_half(self):
        assert pc.mix_to_norm(100.0) == pytest.approx(0.5)
        assert pc.norm_to_mix(0.5) == pytest.approx(100.0)

    def test_makeup(self):
        assert pc.makeup_db_to_norm(0.0) == pytest.approx(0.5)
        assert pc.norm_to_makeup_db(0.5) == pytest.approx(0.0)
        assert pc.norm_to_makeup_db(1.0) == pytest.approx(36.0)


class TestRatioNoTrap:
    def test_unity_at_zero(self):
        assert pc.ratio_to_norm(1.0) == pytest.approx(0.0)
        assert pc.norm_to_ratio(0.0) == pytest.approx(1.0)

    def test_max(self):
        assert pc.norm_to_ratio(1.0) == pytest.approx(100.0)

    @pytest.mark.parametrize("ratio", [1.10, 2.0, 4.0, 10.0])
    def test_roundtrip(self, ratio):
        assert pc.norm_to_ratio(pc.ratio_to_norm(ratio)) == pytest.approx(ratio, rel=0.05)

    def test_clamped_below_one(self):
        assert pc.ratio_to_norm(0.5) == pytest.approx(0.0)


class TestTimeParams:
    @pytest.mark.parametrize("ms", [0.036, 31.25, 128.0, 250.0])
    def test_attack_roundtrip(self, ms):
        assert pc.norm_to_attack_ms(pc.attack_ms_to_norm(ms)) == pytest.approx(ms, rel=0.05)

    @pytest.mark.parametrize("ms", [12.9, 309.5, 944.9, 2500.0])
    def test_release_roundtrip(self, ms):
        assert pc.norm_to_release_ms(pc.release_ms_to_norm(ms)) == pytest.approx(ms, rel=0.05)


class TestStyle:
    def test_known_styles(self):
        assert pc.style_to_norm("clean") == pytest.approx(0.0)
        assert pc.style_to_norm("pumping") == pytest.approx(1.0)
        assert pc.style_to_norm("Vari-Mu") == pytest.approx(0.50)  # case-insensitive

    def test_unknown_style_raises(self):
        with pytest.raises(KeyError):
            pc.style_to_norm("nonexistent")
