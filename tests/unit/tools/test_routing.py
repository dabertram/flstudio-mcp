"""Unit tests for routing write-entry builders + default-name heuristics (pure)."""
from __future__ import annotations

import pytest

from fl_studio_mcp import protocol
from fl_studio_mcp.tools import routing

pytestmark = pytest.mark.unit


class TestRouteWriteEntry:
    def test_shape(self):
        e = routing._route_write_entry(1, 2, True)
        assert e["snap_scope"] == "route:1:2"
        assert e["command"] == protocol.CMD_MIXER_SET_ROUTE
        assert e["params"] == {"src": 1, "dst": 2, "enabled": True}

    def test_restore_reverses(self):
        e = routing._route_write_entry(1, 2, True)
        before = {"src": 1, "dst": 2, "enabled": False}
        restore = e["restore"](before)
        assert restore["command"] == protocol.CMD_MIXER_SET_ROUTE
        assert restore["params"]["enabled"] is False


class TestBusRenameEntry:
    def test_restore_uses_old_name(self):
        e = routing._bus_rename_entry(5, "Drums Bus")
        assert e["params"] == {"track": 5, "name": "Drums Bus"}
        restore = e["restore"]({"name": "Insert 5"})
        assert restore["params"]["name"] == "Insert 5"


class TestDefaultNameHeuristics:
    @pytest.mark.parametrize("name,expected", [
        ("", True), (None, True), ("Channel 1", True), ("Sampler", True),
        ("Insert", True), ("Kick", False), ("My Bass", False),
    ])
    def test_default_channel(self, name, expected):
        assert routing._looks_default_channel_name(name) is expected

    @pytest.mark.parametrize("i,name,expected", [
        (0, "", True), (0, "Master", True), (0, "Bus", False),
        (3, "Insert 3", True), (3, "", True), (3, "Drums", False),
    ])
    def test_default_mixer(self, i, name, expected):
        assert routing._is_default_mixer_name(i, name) is expected
