"""Unit tests for the cross-platform trigger dispatcher.

The critical regression these guard against: importing ``pyscript_trigger`` (and,
on the host platform, its backend) must NOT crash on macOS/Linux -- the old
module executed ``ctypes.windll`` at import time.
"""
from __future__ import annotations

import sys

import pytest

from fl_studio_mcp import pyscript_trigger as pt

pytestmark = pytest.mark.unit


def test_import_does_not_crash():
    # Reaching here means the module imported cleanly on this platform.
    assert hasattr(pt, "trigger_run_last_script")


def test_platform_name_matches_host():
    expected = {"win32": "win32", "darwin": "darwin"}.get(sys.platform, "linux")
    assert pt.platform_name() == expected


class TestHotkey:
    def test_default(self, monkeypatch):
        monkeypatch.delenv("FLSTUDIO_MCP_TRIGGER_HOTKEY", raising=False)
        assert pt._hotkey() == ("ctrl", "alt", "y")

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("FLSTUDIO_MCP_TRIGGER_HOTKEY", "cmd+alt+y")
        assert pt._hotkey() == ("cmd", "alt", "y")

    def test_env_override_with_spaces(self, monkeypatch):
        monkeypatch.setenv("FLSTUDIO_MCP_TRIGGER_HOTKEY", " ctrl + shift + r ")
        assert pt._hotkey() == ("ctrl", "shift", "r")


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only backend")
def test_darwin_find_fl_app_env_override(monkeypatch, tmp_path):
    from fl_studio_mcp import _trigger_darwin as td

    fake = tmp_path / "FL Studio 9999.app"
    fake.mkdir()
    monkeypatch.setenv("FLSTUDIO_MCP_APP", str(fake))
    assert td.find_fl_app() == str(fake)
