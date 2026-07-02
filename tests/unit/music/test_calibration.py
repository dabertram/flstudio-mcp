"""Unit tests for the runtime calibration engine (pure parts + fake-bridge sweep)."""
from __future__ import annotations

import pytest

from fl_studio_mcp import protocol
from fl_studio_mcp.music import calibration as cal

pytestmark = pytest.mark.unit


class TestCurve:
    def test_build_monotonic(self):
        table = [(0.0, 100.0), (0.5, 1000.0), (1.0, 20000.0)]
        curve = cal.build_curve(table)
        assert curve["monotonic"] is True
        assert curve["n"] == 3

    def test_drops_none(self):
        table = [(0.0, 100.0), (0.5, None), (1.0, 20000.0)]
        curve = cal.build_curve(table)
        assert curve["n"] == 2

    def test_norm_to_value_interp(self):
        curve = cal.build_curve([(0.0, 0.0), (1.0, 100.0)])
        assert cal.norm_to_value(curve, 0.25) == pytest.approx(25.0)

    def test_value_to_norm_inverse(self):
        curve = cal.build_curve([(0.0, 0.0), (1.0, 100.0)])
        assert cal.value_to_norm(curve, 75.0) == pytest.approx(0.75)

    def test_clamps_outside_range(self):
        curve = cal.build_curve([(0.0, 10.0), (1.0, 20.0)])
        assert cal.value_to_norm(curve, 5.0) == pytest.approx(0.0)
        assert cal.value_to_norm(curve, 99.0) == pytest.approx(1.0)


class TestSignatureAndCache:
    def test_signature_stable_and_sensitive(self):
        a = cal.signature("Serum", 541, ["A Level", "Filter Cutoff"])
        b = cal.signature("Serum", 541, ["A Level", "Filter Cutoff"])
        c = cal.signature("Serum", 540, ["A Level", "Filter Cutoff"])
        assert a == b
        assert a != c

    def test_cache_roundtrip(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cal, "CACHE_DIR", tmp_path)
        sig = cal.signature("P", 3, ["a"])
        assert cal.load_cache(sig) is None
        cal.save_cache(sig, {"k": {"unit": "Hz"}})
        assert cal.load_cache(sig) == {"k": {"unit": "Hz"}}
        assert not (tmp_path / f"{sig}.json.tmp").exists()


class _FakeSynthBridge:
    """Returns a value string that maps norm -> Hz (log-ish) so a sweep yields a
    real curve. Records the final restore call."""

    def __init__(self):
        self._v = 0.42
        self.restored_to = None

    def call(self, command, params=None, **kw):
        params = params or {}
        if command == protocol.CMD_PLUGIN_GET_PARAM:
            return {"i": params["param"], "name": "Cutoff", "v": self._v,
                    "s": self._hz(self._v)}
        if command == protocol.CMD_PLUGIN_SET_PARAM:
            self._v = float(params["value"])
            self.restored_to = self._v
            return {"i": params["param"], "name": "Cutoff", "v": self._v,
                    "s": self._hz(self._v)}
        raise ValueError(command)

    @staticmethod
    def _hz(norm):
        hz = 20.0 * (1000.0 ** norm)  # 20 Hz .. 20 kHz
        return f"{hz:.1f} Hz"


class TestSweep:
    def test_sweep_builds_hz_curve_and_restores(self):
        b = _FakeSynthBridge()
        out = cal.sweep_param(b, track=1, slot=-1, index=5, steps=6)
        assert out["unit"] == "Hz"
        assert len(out["table"]) == 6
        # final call restored the original value (0.42)
        assert b.restored_to == pytest.approx(0.42)

    def test_calibrate_param_no_cache(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cal, "CACHE_DIR", tmp_path)
        b = _FakeSynthBridge()
        res = cal.calibrate_param(b, 1, -1, 5, plugin_name="Test", param_count=10,
                                  sample_names=["Cutoff"], steps=6)
        assert res["unit"] == "Hz"
        assert res["cached"] is False
        assert res["curve"]["monotonic"] is True
        # second call hits cache
        res2 = cal.calibrate_param(b, 1, -1, 5, plugin_name="Test", param_count=10,
                                   sample_names=["Cutoff"], steps=6)
        assert res2["cached"] is True
