"""Unit tests for the MCP-client installer (pure merge/remove + config IO)."""
from __future__ import annotations

import json

import pytest

from fl_studio_mcp import installer as ins

pytestmark = pytest.mark.unit


def _spec(schema="mcpServers", stdio=False):
    return ins.ClientSpec(id="t", label="T", schema_key=schema, paths={}, stdio_type=stdio)


class TestMerge:
    def test_insert_into_empty(self):
        spec = _spec()
        entry = ins.server_entry(spec)
        doc, changed = ins.merge_config({}, spec, ins.SERVER_NAME, entry)
        assert changed is True
        assert doc["mcpServers"][ins.SERVER_NAME] == entry

    def test_idempotent(self):
        spec = _spec()
        entry = ins.server_entry(spec)
        doc, _ = ins.merge_config({}, spec, ins.SERVER_NAME, entry)
        doc2, changed = ins.merge_config(doc, spec, ins.SERVER_NAME, entry)
        assert changed is False
        assert doc2 == doc

    def test_preserves_other_servers(self):
        spec = _spec()
        base = {"mcpServers": {"other": {"command": "x"}}}
        doc, changed = ins.merge_config(base, spec, ins.SERVER_NAME, ins.server_entry(spec))
        assert changed is True
        assert "other" in doc["mcpServers"]
        assert ins.SERVER_NAME in doc["mcpServers"]

    def test_vscode_servers_key_and_type(self):
        spec = _spec(schema="servers", stdio=True)
        entry = ins.server_entry(spec)
        assert entry["type"] == "stdio"
        doc, changed = ins.merge_config({}, spec, ins.SERVER_NAME, entry)
        assert "servers" in doc


class TestRemove:
    def test_remove_present(self):
        spec = _spec()
        doc, _ = ins.merge_config({}, spec, ins.SERVER_NAME, ins.server_entry(spec))
        doc2, changed = ins.remove_from_config(doc, spec, ins.SERVER_NAME)
        assert changed is True
        assert ins.SERVER_NAME not in doc2["mcpServers"]

    def test_remove_absent_noop(self):
        spec = _spec()
        doc, changed = ins.remove_from_config({"mcpServers": {}}, spec, ins.SERVER_NAME)
        assert changed is False


class TestRegisterIO:
    def test_register_creates_backup_and_writes(self, tmp_path, monkeypatch):
        cfg = tmp_path / "cursor" / "mcp.json"
        cfg.parent.mkdir(parents=True)
        cfg.write_text(json.dumps({"mcpServers": {"other": {"command": "x"}}}), encoding="utf-8")
        spec = ins.ClientSpec(id="cursor", label="Cursor", schema_key="mcpServers",
                              paths={"darwin": str(cfg), "win32": str(cfg), "linux": str(cfg)})
        rep = ins.register(spec)
        assert rep["ok"] and rep["action"] == "registered"
        doc = json.loads(cfg.read_text())
        assert ins.SERVER_NAME in doc["mcpServers"]
        assert "other" in doc["mcpServers"]           # preserved
        assert rep["backup"] and list(tmp_path.glob("cursor/*.bak.*"))

    def test_register_idempotent_second_run(self, tmp_path):
        cfg = tmp_path / "mcp.json"
        spec = ins.ClientSpec(id="cursor", label="Cursor", schema_key="mcpServers",
                              paths={"darwin": str(cfg), "win32": str(cfg), "linux": str(cfg)})
        ins.register(spec)
        rep2 = ins.register(spec)
        assert rep2["action"] == "unchanged"

    def test_dry_run_does_not_write(self, tmp_path):
        cfg = tmp_path / "mcp.json"
        spec = ins.ClientSpec(id="cursor", label="Cursor", schema_key="mcpServers",
                              paths={"darwin": str(cfg), "win32": str(cfg), "linux": str(cfg)})
        rep = ins.register(spec, dry_run=True)
        assert rep["action"].startswith("would-")
        assert not cfg.exists()

    def test_manual_client_returns_snippet(self):
        spec = next(c for c in ins.CLIENTS if not c.auto)
        rep = ins.register(spec)
        assert rep["action"] == "manual"
        assert "snippet" in rep
