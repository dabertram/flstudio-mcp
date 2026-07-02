"""Shared pytest fixtures for the flstudio-mcp test suite.

The package is installed editable in the dev venv, so ``import fl_studio_mcp``
works directly. We also add ``src/`` to sys.path as a fallback so the suite runs
from a bare checkout (e.g. in CI before an editable install).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def isolated_changelog(tmp_path, monkeypatch):
    """Point the safety ChangeLog at a temp file and give it a fresh instance,
    so tests never touch the real ~/.flstudio-mcp/changelog.jsonl."""
    from fl_studio_mcp import safety

    monkeypatch.setattr(safety, "_DIR", tmp_path)
    monkeypatch.setattr(safety, "_PATH", tmp_path / "changelog.jsonl")
    fresh = safety.ChangeLog()
    monkeypatch.setattr(safety, "_log", fresh)
    return fresh


@pytest.fixture
def mock_bridge():
    """A MockBridge with a small default mix. Import here to keep collection cheap."""
    from tests.fixtures.mock_bridge import MockBridge

    return MockBridge()
