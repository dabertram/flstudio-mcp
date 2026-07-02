"""Unit tests for color parsing + channel resolution (pure)."""
from __future__ import annotations

import pytest

from fl_studio_mcp.tools import color

pytestmark = pytest.mark.unit


class TestParseColor:
    def test_named(self):
        assert color.parse_color("red") == (229, 57, 53)
        assert color.parse_color("BLUE") == (33, 150, 243)
        assert color.parse_color("grey") == color.parse_color("gray")

    def test_hex_6(self):
        assert color.parse_color("#33A1FF") == (0x33, 0xA1, 0xFF)
        assert color.parse_color("33a1ff") == (51, 161, 255)

    def test_hex_3_expands(self):
        assert color.parse_color("#f0a") == (0xFF, 0x00, 0xAA)

    def test_invalid(self):
        assert color.parse_color("notacolor") is None
        assert color.parse_color("#12") is None
        assert color.parse_color("#GGGGGG") is None
        assert color.parse_color(None) is None


class TestResolveChannels:
    def test_by_index_and_name(self):
        chans = [
            {"index": 0, "name": "Kick"},
            {"index": 1, "name": "Serum Bass"},
            {"index": 2, "name": "Hat"},
        ]
        # explicit index kept, name substring matches (case-insensitive)
        got = color._resolve_channels(chans, [0, "bass"])
        assert got == {0, 1}

    def test_channel_zero_included(self):
        chans = [{"index": 0, "name": "Kick"}]
        assert color._resolve_channels(chans, ["kick"]) == {0}

    def test_no_match(self):
        chans = [{"index": 0, "name": "Kick"}]
        assert color._resolve_channels(chans, ["synth"]) == set()
