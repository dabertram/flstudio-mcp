"""Unit tests for the PURE Mix Doctor diagnosis rules."""
from __future__ import annotations

import pytest

from fl_studio_mcp.music import mix_doctor as md

pytestmark = pytest.mark.unit


def _track(index, name, **kw):
    t = {"index": index, "name": name, "vol_db": 0.0, "peak_db": None,
         "peak_max": None, "mute": False, "solo": False, "plugins": [], "routes_to": []}
    t.update(kw)
    return t


class TestHelpers:
    def test_lin_to_db(self):
        assert md.lin_to_db(1.0) == pytest.approx(0.0)
        assert md.lin_to_db(None) is None
        assert md.lin_to_db(0.0) is None

    def test_families_present(self):
        for fam in ("drums", "vocals", "bass", "synth", "guitar"):
            assert fam in md.FAMILIES


class TestDiagnoseGating:
    def test_stopped_skips_level_rules_and_notes(self):
        snap = {"playing": False, "tracks": [
            _track(0, "Master", peak_db=2.0),
            _track(1, "Kick", peak_db=1.5),
        ]}
        res = md.diagnose(snap)
        # No level-based clipping finding while stopped.
        assert not any(f["rule"] == "clipping" for f in res["findings"])
        # And a clear note explaining why.
        assert any("STOPPED" in n or "level rules" in n for n in res["notes"])

    def test_playing_runs_clipping(self):
        snap = {"playing": True, "tracks": [
            _track(0, "Master", peak_db=-6.0),
            _track(1, "Kick", peak_db=0.5),  # above CLIP_HARD_DB -> clipping
        ]}
        res = md.diagnose(snap)
        assert any(f["rule"] == "clipping" for f in res["findings"])

    def test_watch_capture_counts_as_valid(self):
        snap = {"playing": False, "levels_valid": True, "tracks": [
            _track(0, "Master", peak_db=-6.0),
            _track(1, "Kick", peak_db=0.5),
        ]}
        res = md.diagnose(snap)
        assert any(f["rule"] == "clipping" for f in res["findings"])

    def test_summary_shape(self):
        snap = {"playing": True, "tracks": [_track(0, "Master", peak_db=-6.0)]}
        res = md.diagnose(snap)
        assert set(res["summary"]) == {"high", "medium", "low"}
        assert res["track_count"] == 1
