"""Unit tests for bulk target resolution (pure)."""
from __future__ import annotations

import pytest

from fl_studio_mcp.tools import bulk

pytestmark = pytest.mark.unit


TRACKS = [
    {"index": 0, "name": "Master", "mute": False, "solo": False},
    {"index": 1, "name": "Kick", "mute": False, "solo": False},
    {"index": 2, "name": "Snare", "mute": False, "solo": False},
    {"index": 3, "name": "Lead Vocal", "mute": False, "solo": False},
    {"index": 4, "name": "Bass 808", "mute": False, "solo": False},
]


class TestResolveTargets:
    def test_category_drums(self):
        got = bulk.resolve_targets(TRACKS, category="drums")
        assert got == {1, 2}  # Kick + Snare, not Master

    def test_category_bass(self):
        got = bulk.resolve_targets(TRACKS, category="bass")
        assert got == {4}

    def test_master_always_excluded(self):
        got = bulk.resolve_targets(TRACKS, names=[0, "master"])
        assert 0 not in got

    def test_explicit_index_and_name(self):
        got = bulk.resolve_targets(TRACKS, names=[3, "kick"])
        assert got == {1, 3}

    def test_unknown_category_is_literal_substring(self):
        got = bulk.resolve_targets(TRACKS, category="vocal")
        assert got == {3}

    def test_no_match(self):
        assert bulk.resolve_targets(TRACKS, category="strings") == set()
