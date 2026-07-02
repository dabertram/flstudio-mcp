"""Unit tests for generic VST param grouping + exposure classification (pure)."""
from __future__ import annotations

import pytest

from fl_studio_mcp.music import vst_params as vp

pytestmark = pytest.mark.unit


def _p(i, name, s=""):
    return {"i": i, "name": name, "v": 0.5, "s": s}


class TestGroupByRole:
    def test_buckets(self):
        params = [
            _p(0, "Osc A Level"),
            _p(1, "Filter Cutoff"),
            _p(2, "Env 1 Attack"),
            _p(3, "LFO 1 Rate"),
            _p(4, "Master Volume"),
            _p(5, "Reverb Mix"),
            _p(6, "Something Weird"),
        ]
        g = vp.group_params_by_role(params)
        assert 0 in [p["i"] for p in g["oscillator"]]
        assert 1 in [p["i"] for p in g["filter"]]
        assert 2 in [p["i"] for p in g["envelope"]]
        assert 3 in [p["i"] for p in g["lfo"]]
        assert 5 in [p["i"] for p in g["fx"]]
        assert 6 in [p["i"] for p in g["other"]]

    def test_empty(self):
        assert vp.group_params_by_role([]) == {}

    def test_lfo_priority_over_amp(self):
        # "LFO 1 Level" should land in lfo (checked before amp)
        g = vp.group_params_by_role([_p(0, "LFO 1 Level")])
        assert "lfo" in g


class TestGenericName:
    @pytest.mark.parametrize("name", ["Param 12", "param12", "P3", "CC7", "", "   "])
    def test_generic(self, name):
        assert vp.is_generic_name(name) is True

    @pytest.mark.parametrize("name", ["Cutoff", "Osc A Level", "Threshold"])
    def test_real(self, name):
        assert vp.is_generic_name(name) is False


class TestExposureTier:
    def test_full(self):
        params = [_p(i, f"Knob {i}", s="1.2 kHz") for i in range(10)]
        rep = vp.classify_param_exposure(params)
        assert rep["tier"] == "full"
        assert rep["total"] == 10

    def test_partial_names_no_strings(self):
        params = [_p(i, f"Knob {i}", s="") for i in range(10)]
        rep = vp.classify_param_exposure(params)
        assert rep["tier"] == "partial"

    def test_opaque_generic_names(self):
        params = [_p(i, f"Param {i}", s="") for i in range(10)]
        rep = vp.classify_param_exposure(params)
        assert rep["tier"] == "opaque"

    def test_empty(self):
        rep = vp.classify_param_exposure([])
        assert rep["tier"] == "empty"
        assert rep["total"] == 0
