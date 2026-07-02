"""Unit tests for piano-roll pyscript generation + quantize (pure)."""
from __future__ import annotations

import pytest

from fl_studio_mcp import pyscript_gen as pg

pytestmark = pytest.mark.unit


class TestQuantizeNotes:
    def test_snaps_starts_to_grid(self):
        notes = [{"pitch": 60, "time_bars": 0.13, "length_bars": 0.5}]
        out = pg.quantize_notes(notes, grid_bars=0.0625)  # 1/16
        # 0.13 / 0.0625 = 2.08 -> round 2 -> 0.125
        assert out[0]["time_bars"] == pytest.approx(0.125)
        # length untouched when snap_ends is False
        assert out[0]["length_bars"] == pytest.approx(0.5)

    def test_snap_ends(self):
        notes = [{"pitch": 60, "time_bars": 0.0, "length_bars": 0.17}]
        out = pg.quantize_notes(notes, grid_bars=0.125, snap_ends=True)
        # 0.17 / 0.125 = 1.36 -> round 1 -> 0.125
        assert out[0]["length_bars"] == pytest.approx(0.125)

    def test_zero_grid_is_noop(self):
        notes = [{"pitch": 60, "time_bars": 0.13, "length_bars": 0.5}]
        out = pg.quantize_notes(notes, grid_bars=0.0)
        assert out[0]["time_bars"] == pytest.approx(0.13)

    def test_does_not_mutate_input(self):
        notes = [{"pitch": 60, "time_bars": 0.13, "length_bars": 0.5}]
        pg.quantize_notes(notes, grid_bars=0.0625)
        assert notes[0]["time_bars"] == 0.13


class TestRenderApplyScript:
    def test_contains_notes_and_mode(self):
        notes = [{"pitch": 64, "time_bars": 1.0, "length_bars": 0.5, "velocity": 0.8}]
        text = pg.render_apply_script(notes, mode="replace")
        assert "flpianoroll" in text
        assert "MODE = 'replace'" in text
        assert "64" in text  # pitch baked in
        assert "clearNotes" in text  # replace clears first

    def test_append_mode(self):
        text = pg.render_apply_script([], mode="append")
        assert "MODE = 'append'" in text

    def test_render_quantize_script(self):
        text = pg.render_quantize_script(0.0625, snap_ends=True)
        assert "GRID_BARS" in text
        assert "SNAP_ENDS = True" in text
