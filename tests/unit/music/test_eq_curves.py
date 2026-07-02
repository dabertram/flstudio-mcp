"""Unit tests for Fruity Parametric EQ 2 calibration curves (pure)."""
from __future__ import annotations

import pytest

from fl_studio_mcp.music import eq_curves as eq

pytestmark = pytest.mark.unit


class TestFrequency:
    def test_endpoints(self):
        assert eq.freq_to_norm(20.0) == pytest.approx(0.0)
        assert eq.freq_to_norm(20000.0) == pytest.approx(1.0)
        assert eq.norm_to_freq(0.0) == pytest.approx(20.0)
        assert eq.norm_to_freq(1.0) == pytest.approx(20000.0)

    def test_midpoint_is_geometric_center(self):
        # 20 * 10**(3*0.5) == 20 * 10**1.5 ~= 632.46 Hz
        assert eq.norm_to_freq(0.5) == pytest.approx(632.456, rel=1e-3)
        assert eq.freq_to_norm(632.456) == pytest.approx(0.5, abs=1e-4)

    def test_clamp_and_nonpositive(self):
        assert eq.freq_to_norm(0.0) == 0.0
        assert eq.freq_to_norm(-100.0) == 0.0
        assert eq.freq_to_norm(1e9) == 1.0

    @pytest.mark.parametrize("hz", [50, 250, 1000, 5000, 12000])
    def test_roundtrip(self, hz):
        assert eq.norm_to_freq(eq.freq_to_norm(hz)) == pytest.approx(hz, rel=1e-6)


class TestLevel:
    def test_endpoints(self):
        assert eq.db_to_norm(-18.0) == pytest.approx(0.0)
        assert eq.db_to_norm(0.0) == pytest.approx(0.5)
        assert eq.db_to_norm(18.0) == pytest.approx(1.0)
        assert eq.norm_to_db(0.5) == pytest.approx(0.0)

    def test_clamp(self):
        assert eq.db_to_norm(-100.0) == 0.0
        assert eq.db_to_norm(100.0) == 1.0

    @pytest.mark.parametrize("db", [-18, -6, 0, 6, 18])
    def test_roundtrip(self, db):
        assert eq.norm_to_db(eq.db_to_norm(db)) == pytest.approx(db)


class TestWidth:
    def test_mapping(self):
        assert eq.width_to_norm(100.0) == pytest.approx(1.0)
        assert eq.width_to_norm(0.0) == pytest.approx(0.0)
        assert eq.norm_to_width(0.5) == pytest.approx(50.0)

    def test_clamp(self):
        assert eq.width_to_norm(200.0) == 1.0
        assert eq.norm_to_width(2.0) == 100.0


class TestBandLayout:
    @pytest.mark.parametrize("band,which,expected", [
        (1, "level", 0), (1, "freq", 7), (1, "width", 14), (1, "type", 21),
        (7, "level", 6), (7, "freq", 13), (7, "width", 20), (7, "type", 27),
        (4, "level", 3), (4, "freq", 10),
    ])
    def test_index(self, band, which, expected):
        assert eq.eq2_band_param_index(band, which) == expected

    def test_band_out_of_range(self):
        with pytest.raises(ValueError):
            eq.eq2_band_param_index(0, "level")
        with pytest.raises(ValueError):
            eq.eq2_band_param_index(8, "level")

    def test_bad_which(self):
        with pytest.raises(ValueError):
            eq.eq2_band_param_index(1, "gain")

    def test_type_norms_span_0_to_1(self):
        assert eq.TYPE_NORMS["disabled"] == pytest.approx(0.0)
        assert eq.TYPE_NORMS["high_shelf"] == pytest.approx(1.0)
        assert len(eq.TYPE_NORMS) == 8
