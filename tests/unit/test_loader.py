"""Unit tests for the capability-aware plugin loader (pure)."""
from __future__ import annotations

import pytest

from fl_studio_mcp.tools.loader import describe_load_limitation

pytestmark = pytest.mark.unit


def test_reports_unsupported():
    r = describe_load_limitation("Vital", True)
    assert r["ok"] is False
    assert r["supported"] is False
    assert r["requested"] == {"name": "Vital", "as_generator": True}


def test_informs_drawbacks_and_alternatives():
    r = describe_load_limitation("Pro-Q 3", False)
    assert r["drawbacks_of_ui_automation"]           # non-empty
    assert any("template" in x.lower() for x in r["recommended"])
    assert "after_loading" in r


def test_generator_vs_effect_wording():
    gen = describe_load_limitation("Serum", True)
    fx = describe_load_limitation("Fruity Reeverb 2", False)
    assert "generator" in gen["recommended"][0].lower() or "channel" in gen["recommended"][0].lower()
    assert "effect" in fx["recommended"][0].lower() or "mixer" in fx["recommended"][0].lower()
