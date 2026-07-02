"""Integration tests: safety snapshot/write/rollback against the MockBridge."""
from __future__ import annotations

import pytest

from fl_studio_mcp import protocol, safety

pytestmark = pytest.mark.integration


@pytest.fixture
def bridge():
    from tests.fixtures.mock_bridge import MockBridge

    return MockBridge()


class TestSafeWrite:
    def test_volume_write_records_before_after(self, bridge, isolated_changelog):
        res = safety.safe_write(
            bridge, tool="mixer_set_volume", scope="mixer_track:1",
            command=protocol.CMD_MIXER_SET_VOLUME,
            params={"track": 1, "value": -6.0, "unit": "db"},
            build_restore=lambda b: {"command": protocol.CMD_MIXER_SET_VOLUME,
                                     "params": {"track": 1, "value": b["vol_db"], "unit": "db"}},
        )
        assert res["ok"] is True
        assert res["before"]["vol_db"] == 0.0
        assert res["after"]["vol_db"] == -6.0
        assert len(isolated_changelog.recent()) == 1

    def test_rollback_restores_previous_value(self, bridge, isolated_changelog):
        safety.safe_write(
            bridge, tool="mixer_set_volume", scope="mixer_track:1",
            command=protocol.CMD_MIXER_SET_VOLUME,
            params={"track": 1, "value": -6.0, "unit": "db"},
            build_restore=lambda b: {"command": protocol.CMD_MIXER_SET_VOLUME,
                                     "params": {"track": 1, "value": b["vol_db"], "unit": "db"}},
        )
        assert bridge._track(1)["vol_db"] == -6.0
        out = safety.rollback_last_change(bridge)
        assert out["ok"] is True
        assert bridge._track(1)["vol_db"] == 0.0
        assert len(isolated_changelog.recent()) == 0

    def test_rollback_empty_changelog(self, bridge, isolated_changelog):
        out = safety.rollback_last_change(bridge)
        assert out["ok"] is False


class TestSafeWriteGroup:
    def test_group_applies_and_rolls_back_atomically(self, bridge, isolated_changelog):
        writes = [
            {"snap_scope": "mixer_track:1", "command": protocol.CMD_MIXER_SET_MUTE,
             "params": {"track": 1, "state": True},
             "restore": (lambda b: {"command": protocol.CMD_MIXER_SET_MUTE,
                                    "params": {"track": 1, "state": b["mute"]}})},
            {"snap_scope": "mixer_track:2", "command": protocol.CMD_MIXER_SET_MUTE,
             "params": {"track": 2, "state": True},
             "restore": (lambda b: {"command": protocol.CMD_MIXER_SET_MUTE,
                                    "params": {"track": 2, "state": b["mute"]}})},
        ]
        res = safety.safe_write_group(bridge, tool="solo_group", scope="bulk", writes=writes)
        assert res["ok"] is True
        assert bridge._track(1)["mute"] is True
        assert bridge._track(2)["mute"] is True

        # one changelog entry for the whole group
        assert len(isolated_changelog.recent()) == 1

        safety.rollback_last_change(bridge)
        assert bridge._track(1)["mute"] is False
        assert bridge._track(2)["mute"] is False


class TestDryRun:
    def test_dry_run_does_not_write(self, bridge, isolated_changelog):
        safety.set_dry_run(True)
        try:
            res = safety.safe_write(
                bridge, tool="mixer_set_volume", scope="mixer_track:1",
                command=protocol.CMD_MIXER_SET_VOLUME,
                params={"track": 1, "value": -6.0, "unit": "db"},
                build_restore=lambda b: {"command": protocol.CMD_MIXER_SET_VOLUME,
                                         "params": {"track": 1, "value": 0.0, "unit": "db"}},
            )
            assert res.get("dry_run") is True
            assert bridge._track(1)["vol_db"] == 0.0  # unchanged
            assert len(isolated_changelog.recent()) == 0
        finally:
            safety.set_dry_run(False)


class TestSnapshotScopes:
    def test_route_snapshot(self, bridge, isolated_changelog):
        snap = safety.take_snapshot(bridge, "route:1:0")
        assert snap == {"src": 1, "dst": 0, "enabled": True}
        snap2 = safety.take_snapshot(bridge, "route:1:5")
        assert snap2["enabled"] is False

    def test_unknown_scope_raises(self, bridge):
        with pytest.raises(ValueError):
            safety.take_snapshot(bridge, "bogus:1")
