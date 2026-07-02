"""Integration test: batch plugin param set as one rollback unit."""
from __future__ import annotations

import pytest

from fl_studio_mcp import protocol, safety
from fl_studio_mcp.tools.plugin import resolve_param_index

pytestmark = pytest.mark.integration


class ParamBridge:
    """Minimal generator bridge with two integer-addressed params."""

    def __init__(self):
        self.vals = {0: 0.1, 1: 0.2}

    def call(self, command, params=None, **kw):
        p = params or {}
        if command == protocol.CMD_PLUGIN_GET_PARAM:
            i = int(p["param"])
            return {"i": i, "name": f"P{i}", "v": self.vals.get(i, 0.0), "s": ""}
        if command == protocol.CMD_PLUGIN_SET_PARAM:
            i = int(p["param"])
            self.vals[i] = float(p["value"])
            return {"i": i, "name": f"P{i}", "v": self.vals[i], "s": ""}
        raise ValueError(command)


def test_batch_set_then_rollback(isolated_changelog):
    b = ParamBridge()
    writes = []
    for idx, val in ((0, 0.8), (1, 0.9)):
        _i, _n = resolve_param_index(b, 1, -1, idx)
        writes.append({
            "snap_scope": f"plugin_param:1:-1:{idx}",
            "command": protocol.CMD_PLUGIN_SET_PARAM,
            "params": {"track": 1, "slot": -1, "param": idx, "value": val},
            "restore": (lambda before, i=idx: {"command": protocol.CMD_PLUGIN_SET_PARAM,
                        "params": {"track": 1, "slot": -1, "param": i, "value": before["v"]}}),
        })
    res = safety.safe_write_group(b, tool="plugin_set_params", scope="plugin:1:-1", writes=writes)
    assert res["ok"]
    assert b.vals == {0: pytest.approx(0.8), 1: pytest.approx(0.9)}

    # one changelog entry for the whole group
    assert len(isolated_changelog.recent()) == 1

    safety.rollback_last_change(b)
    assert b.vals == {0: pytest.approx(0.1), 1: pytest.approx(0.2)}
