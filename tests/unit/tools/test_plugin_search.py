"""Unit tests for plugin param search filter (pure)."""
from __future__ import annotations

import pytest

from fl_studio_mcp.tools.plugin import filter_params_by_name

pytestmark = pytest.mark.unit


PARAMS = [
    {"i": 0, "name": "Master Vol", "v": 0.5, "s": "50%"},
    {"i": 1, "name": "A Filter Cutoff", "v": 0.7, "s": "1.2 kHz"},
    {"i": 2, "name": "B Filter Cutoff", "v": 0.3, "s": "400 Hz"},
    {"i": 3, "name": "A Filter Reso", "v": 0.2, "s": "20%"},
    {"i": 4, "name": "Env 1 Attack", "v": 0.1, "s": "5 ms"},
]


def test_single_token():
    hits = filter_params_by_name(PARAMS, "filter")
    assert {h["i"] for h in hits} == {1, 2, 3}


def test_all_tokens_must_match():
    hits = filter_params_by_name(PARAMS, "filter cutoff")
    assert {h["i"] for h in hits} == {1, 2}


def test_case_insensitive():
    assert filter_params_by_name(PARAMS, "MASTER")[0]["i"] == 0


def test_empty_query_returns_nothing():
    assert filter_params_by_name(PARAMS, "") == []
    assert filter_params_by_name(PARAMS, "   ") == []


def test_limit_and_sort():
    hits = filter_params_by_name(PARAMS, "filter", limit=2)
    assert len(hits) == 2
    # sorted by name -> "A Filter Cutoff", "A Filter Reso"
    assert [h["name"] for h in hits] == ["A Filter Cutoff", "A Filter Reso"]


def test_no_match():
    assert filter_params_by_name(PARAMS, "lfo") == []
