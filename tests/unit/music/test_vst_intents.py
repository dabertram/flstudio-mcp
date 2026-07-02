"""Unit tests for generic semantic VST intents (pure)."""
from __future__ import annotations

import pytest

from fl_studio_mcp.music import vst_intents as vin

pytestmark = pytest.mark.unit


def _p(i, name, v=0.5):
    return {"i": i, "name": name, "v": v, "s": ""}


class TestResolve:
    def test_known(self):
        assert vin.resolve_intent("brighter")["direction"] == +1
        assert vin.resolve_intent("darker")["direction"] == -1
        assert vin.resolve_intent("BRIGHTER") is not None  # case-insensitive

    def test_unknown(self):
        assert vin.resolve_intent("sparklier") is None

    def test_list(self):
        names = vin.list_intents()
        assert "brighter" in names and "wider" in names


class TestPickParam:
    def test_prefers_specific_and_short(self):
        params = [
            _p(0, "Filter Cutoff"),
            _p(1, "Cutoff Env Amount"),
            _p(2, "Master Vol"),
        ]
        chosen = vin.pick_param(params, ("cutoff",))
        # both 0 and 1 match; shorter name (0) wins
        assert chosen["i"] == 0

    def test_no_match(self):
        assert vin.pick_param([_p(0, "Master Vol")], ("cutoff",)) is None


class TestRelativeTarget:
    def test_mul_up(self):
        spec = {"direction": +1, "mode": "mul"}
        # amount 0.5 -> factor 2.0
        assert vin.relative_target(1000.0, spec, 0.5, (20.0, 20000.0)) == pytest.approx(2000.0)

    def test_mul_down(self):
        spec = {"direction": -1, "mode": "mul"}
        assert vin.relative_target(1000.0, spec, 0.5, (20.0, 20000.0)) == pytest.approx(500.0)

    def test_frac_up_and_clamped(self):
        spec = {"direction": +1, "mode": "frac"}
        # move 0.5 * (100-0)=50 up from 80 -> 130 clamped to 100
        assert vin.relative_target(80.0, spec, 0.5, (0.0, 100.0)) == pytest.approx(100.0)

    def test_frac_down_clamped(self):
        spec = {"direction": -1, "mode": "frac"}
        assert vin.relative_target(10.0, spec, 0.5, (0.0, 100.0)) == pytest.approx(0.0)
