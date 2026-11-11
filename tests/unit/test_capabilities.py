"""Unit tests for the capability-introspection report (pure)."""
from __future__ import annotations

import sys

import pytest

from fl_studio_mcp import capabilities

pytestmark = pytest.mark.unit


def test_report_shape():
    rep = capabilities.describe_capabilities()
    for key in ("platform", "transport", "midi_ports", "note_bridge",
                "automated", "manual_steps", "fl_api_limits"):
        assert key in rep
    assert isinstance(rep["automated"], list) and rep["automated"]
    assert isinstance(rep["manual_steps"], list) and rep["manual_steps"]


def test_platform_matches_host():
    rep = capabilities.describe_capabilities()
    expected = {"win32": "win32", "darwin": "darwin"}.get(sys.platform, "linux")
    assert rep["platform"] == expected


def test_transport_reflects_env(monkeypatch):
    monkeypatch.setenv("FLSTUDIO_MCP_TRANSPORT", "tcp")
    assert capabilities.describe_capabilities()["transport"] == "tcp"


def test_virtual_ports_note_toggles(monkeypatch):
    monkeypatch.setenv("FLSTUDIO_MCP_VIRTUAL_PORTS", "1")
    rep = capabilities.describe_capabilities()
    assert rep["midi_ports"]["virtual_ports_enabled"] is True

    monkeypatch.setenv("FLSTUDIO_MCP_VIRTUAL_PORTS", "0")
    rep = capabilities.describe_capabilities()
    assert rep["midi_ports"]["virtual_ports_enabled"] is False


def test_app_control_block():
    rep = capabilities.describe_capabilities()
    ac = rep["app_control"]
    assert ac["supported"] is (rep["platform"] in ("win32", "darwin"))


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-specific note")
def test_darwin_mentions_accessibility():
    rep = capabilities.describe_capabilities()
    assert any("Accessibility" in s for s in rep["manual_steps"])
