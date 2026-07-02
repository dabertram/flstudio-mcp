"""Unit tests for the plugin value-string parser (pure)."""
from __future__ import annotations

import pytest

from fl_studio_mcp.music import value_parse as vp

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("s,value,unit", [
    ("-16.00 dB", -16.0, "dB"),
    ("+7.35 dB", 7.35, "dB"),
    ("1.2 kHz", 1200.0, "Hz"),
    ("400 Hz", 400.0, "Hz"),
    ("0.725 ms", 0.725, "ms"),
    ("100.0 ms", 100.0, "ms"),
    ("3.50:1", 3.5, "ratio"),
    ("50%", 50.0, "%"),
    ("0 semitones", 0.0, "semitone"),
    ("2 oct", 2.0, "oct"),
    ("1.20 s", 1.2, "s"),
])
def test_parse(s, value, unit):
    r = vp.parse_value_string(s)
    assert r["value"] == pytest.approx(value)
    assert r["unit"] == unit


def test_compound_primary_unit_wins():
    r = vp.parse_value_string("50% [-9.0 dB]")
    assert r["value"] == pytest.approx(50.0)
    assert r["unit"] == "%"


def test_ratio_inverted():
    # "1:2.0" -> take the non-1 side
    r = vp.parse_value_string("1:2.0")
    assert r["value"] == pytest.approx(2.0)
    assert r["unit"] == "ratio"


def test_empty_and_none():
    assert vp.parse_value_string("")["value"] is None
    assert vp.parse_value_string(None)["value"] is None
    assert vp.parse_value_string("   ")["unit"] is None


def test_plain_number():
    r = vp.parse_value_string("0.42")
    assert r["value"] == pytest.approx(0.42)
    assert r["unit"] is None


def test_to_canonical_seconds_to_ms():
    assert vp.to_canonical(1.2, "s") == (1200.0, "ms")
    assert vp.to_canonical(5.0, "dB") == (5.0, "dB")
