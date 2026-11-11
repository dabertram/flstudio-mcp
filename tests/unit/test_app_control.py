"""Unit tests for the cross-platform FL Studio process-control dispatcher.

The critical regression these guard against: importing ``app_control`` (and,
on the host platform, its backend) must NOT crash on macOS/Linux -- mirrors
the same hazard ``pyscript_trigger`` guards against for ``ctypes.windll``.
"""
from __future__ import annotations

import sys

import pytest

from fl_studio_mcp import app_control as ac

pytestmark = pytest.mark.unit


def test_import_does_not_crash():
    assert hasattr(ac, "start_fl_studio")
    assert hasattr(ac, "stop_fl_studio")
    assert hasattr(ac, "get_status")


def test_platform_name_matches_host():
    expected = {"win32": "win32", "darwin": "darwin"}.get(sys.platform, "linux")
    assert ac.platform_name() == expected


def test_status_never_raises_on_host_platform():
    # No FL Studio installed on CI -- should degrade to a clean "not found"
    # report, never an exception.
    report = ac.get_status()
    assert report["platform"] == ac.platform_name()
    assert "running" in report


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only backend")
class TestDarwinBackend:
    def test_find_fl_app_env_override(self, monkeypatch, tmp_path):
        fake = tmp_path / "FL Studio 9999.app"
        fake.mkdir()
        monkeypatch.setenv("FLSTUDIO_MCP_APP", str(fake))

        from fl_studio_mcp import _app_darwin as ad

        assert ad.find_fl_app() == str(fake)

    def test_start_reports_not_found_when_app_missing(self, monkeypatch):
        # Patch find_fl_app itself (rather than the env-var override, which
        # falls back to a real /Applications search -- and would try to
        # actually launch FL Studio on a machine that has it installed).
        from fl_studio_mcp import _app_darwin as ad

        monkeypatch.setattr(ad, "find_fl_app", lambda: None)
        result = ac.start_fl_studio()
        assert result["ok"] is False
        assert "not found" in result["note"]

    def test_stop_reports_not_found_when_app_missing(self, monkeypatch):
        from fl_studio_mcp import _app_darwin as ad

        monkeypatch.setattr(ad, "find_fl_app", lambda: None)
        result = ac.stop_fl_studio()
        assert result["ok"] is False
        assert "not found" in result["note"]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only backend")
class TestWin32Backend:
    def test_find_fl_exe_env_override(self, monkeypatch, tmp_path):
        fake = tmp_path / "FL64.exe"
        fake.write_bytes(b"")
        monkeypatch.setenv("FLSTUDIO_MCP_APP", str(fake))

        from fl_studio_mcp import _app_win32 as aw

        assert aw.find_fl_exe() == str(fake)
