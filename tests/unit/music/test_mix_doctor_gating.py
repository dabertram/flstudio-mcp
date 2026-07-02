"""Unit tests for diagnose() partial-vs-complete gating signal (Phase B5)."""
from __future__ import annotations

import pytest

from fl_studio_mcp.music import mix_doctor as md

pytestmark = pytest.mark.unit


def _track(index, name, **kw):
    t = {"index": index, "name": name, "vol_db": 0.0, "peak_db": None,
         "mute": False, "solo": False, "plugins": [], "routes_to": []}
    t.update(kw)
    return t


class TestGatingSignal:
    def test_stopped_is_partial(self):
        snap = {"playing": False, "tracks": [
            _track(0, "Master", peak_db=-6.0),
            _track(1, "Kick", peak_db=0.5),
        ]}
        res = md.diagnose(snap)
        assert res["levels_valid"] is False
        assert res["diagnosis_complete"] is False
        assert any("PARTIAL DIAGNOSIS" in n for n in res["notes"])
        # level rules must not have run
        assert not any(f["rule"] == "clipping" for f in res["findings"])

    def test_playing_is_complete(self):
        snap = {"playing": True, "tracks": [
            _track(0, "Master", peak_db=-6.0),
            _track(1, "Kick", peak_db=0.5),  # above CLIP_HARD_DB
        ]}
        res = md.diagnose(snap)
        assert res["levels_valid"] is True
        assert res["diagnosis_complete"] is True
        assert any(f["rule"] == "clipping" for f in res["findings"])
        assert not any("PARTIAL DIAGNOSIS" in n for n in res["notes"])

    def test_watch_capture_is_complete(self):
        snap = {"playing": False, "levels_valid": True, "tracks": [
            _track(0, "Master", peak_db=-6.0),
            _track(1, "Kick", peak_db=0.5),
        ]}
        res = md.diagnose(snap)
        assert res["levels_valid"] is True
        assert res["diagnosis_complete"] is True
        assert not any("PARTIAL DIAGNOSIS" in n for n in res["notes"])

    def test_new_keys_are_bools(self):
        snap = {"playing": True, "tracks": [_track(0, "Master", peak_db=-6.0)]}
        res = md.diagnose(snap)
        assert isinstance(res["levels_valid"], bool)
        assert isinstance(res["diagnosis_complete"], bool)
