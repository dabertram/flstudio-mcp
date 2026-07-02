"""Unit tests for level measurement helpers (mostly pure; uses MockBridge)."""
from __future__ import annotations

import math

import pytest

from fl_studio_mcp.music import levels

pytestmark = pytest.mark.unit


class TestPeakToDb:
    def test_none_and_silence(self):
        assert levels.peak_to_db(None) is None
        assert levels.peak_to_db(0.0) is None
        assert levels.peak_to_db(1e-7) is None  # <= 1e-6 guard

    def test_full_scale(self):
        assert levels.peak_to_db(1.0) == pytest.approx(0.0)

    def test_half(self):
        assert levels.peak_to_db(0.5) == pytest.approx(20 * math.log10(0.5), abs=1e-6)


class _ConstBridge:
    """Minimal bridge returning a constant peak for measure_* tests."""

    def __init__(self, peak):
        self._peak = peak

    def call(self, command, params=None, **kw):
        return {"peak_max": self._peak}


class TestMeasureTrackLevel:
    def test_playing(self):
        b = _ConstBridge(0.5)
        out = levels.measure_track_level(b, track=1, samples=3, interval_ms=0)
        assert out["playing"] is True
        assert out["peak_db"] == pytest.approx(20 * math.log10(0.5), abs=0.1)
        assert out["n_reads"] == 3

    def test_silence_guard(self):
        b = _ConstBridge(0.0)
        out = levels.measure_track_level(b, track=1, samples=3, interval_ms=0)
        assert out["playing"] is False
        assert out["avg_db"] is None
        assert out["peak_db"] is None


class TestMeasureMany:
    def test_shared_window(self):
        b = _ConstBridge(0.25)
        out = levels.measure_many(b, tracks=[1, 2, 3], samples=2, interval_ms=0)
        assert set(out) == {1, 2, 3}
        for t in (1, 2, 3):
            assert out[t]["playing"] is True
            assert out[t]["peak_lin"] == pytest.approx(0.25)
