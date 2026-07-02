"""Integration test: end-to-end unit-targeted plugin control.

Mirrors the fl_plugin_set_param_value flow (calibrate -> invert curve ->
safe_write -> readback -> rollback) against a fake generator bridge whose
display string maps norm -> Hz, so we exercise the real calibration + safety
path without live FL.
"""
from __future__ import annotations

import pytest

from fl_studio_mcp import protocol, safety
from fl_studio_mcp.music import calibration as cal

pytestmark = pytest.mark.integration


class FakeSynthBridge:
    """One generator at (track=1, slot=-1) with a log Hz 'Filter Cutoff' param."""

    def __init__(self):
        self.vals = {0: 0.5, 1: 0.42}  # param index -> normalised value
        self.names = {0: "Master Vol", 1: "Filter Cutoff"}

    def _hz(self, v):
        return f"{20.0 * (1000.0 ** v):.1f} Hz"

    def _s(self, i, v):
        return self._hz(v) if i == 1 else f"{int(v * 100)}%"

    def call(self, command, params=None, **kw):
        p = params or {}
        if command == protocol.CMD_PLUGIN_GET_PARAM:
            i = int(p["param"])
            return {"i": i, "name": self.names[i], "v": self.vals[i], "s": self._s(i, self.vals[i])}
        if command == protocol.CMD_PLUGIN_SET_PARAM:
            i = int(p["param"])
            self.vals[i] = float(p["value"])
            return {"i": i, "name": self.names[i], "v": self.vals[i], "s": self._s(i, self.vals[i])}
        if command == protocol.CMD_PLUGIN_GET_PARAMS:
            start = int(p.get("start", 0))
            items = [{"i": i, "name": self.names[i], "v": self.vals[i], "s": self._s(i, self.vals[i])}
                     for i in sorted(self.names)]
            return {"plugin": "FakeSynth", "total": len(items), "start": start,
                    "next_start": None, "params": items[start:]}
        raise ValueError(command)


def test_unit_targeted_set_and_rollback(tmp_path, monkeypatch, isolated_changelog):
    monkeypatch.setattr(cal, "CACHE_DIR", tmp_path)
    b = FakeSynthBridge()
    idx = 1  # Filter Cutoff

    # calibrate the cutoff param
    res = cal.calibrate_param(b, 1, -1, idx, plugin_name="FakeSynth", param_count=2,
                              sample_names=["Master Vol", "Filter Cutoff"], steps=11)
    assert res["unit"] == "Hz"
    curve = res["curve"]
    assert curve["monotonic"]

    # target 2000 Hz -> normalised, then safe_write
    norm = max(0.0, min(1.0, cal.value_to_norm(curve, 2000.0)))
    out = safety.safe_write(
        b, tool="plugin_set_param_value", scope=f"plugin_param:1:-1:{idx}",
        command=protocol.CMD_PLUGIN_SET_PARAM,
        params={"track": 1, "slot": -1, "param": idx, "value": norm},
        build_restore=lambda before: {"command": protocol.CMD_PLUGIN_SET_PARAM,
                                       "params": {"track": 1, "slot": -1, "param": idx,
                                                  "value": before["v"]}})
    assert out["ok"]
    # achieved Hz should be near 2000 (within the sweep's interpolation error)
    achieved = 20.0 * (1000.0 ** b.vals[idx])
    assert achieved == pytest.approx(2000.0, rel=0.15)

    # rollback restores the original 0.42
    safety.rollback_last_change(b)
    assert b.vals[idx] == pytest.approx(0.42)
