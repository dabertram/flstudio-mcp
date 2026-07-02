"""Unit tests for bridge virtual-port enablement + changelog atomicity."""
from __future__ import annotations

import sys

import pytest

from fl_studio_mcp import connection

pytestmark = pytest.mark.unit


class TestVirtualPortsEnabled:
    def test_forced_on(self, monkeypatch):
        monkeypatch.setenv("FLSTUDIO_MCP_VIRTUAL_PORTS", "1")
        assert connection._virtual_ports_enabled() is True

    def test_forced_off(self, monkeypatch):
        monkeypatch.setenv("FLSTUDIO_MCP_VIRTUAL_PORTS", "off")
        assert connection._virtual_ports_enabled() is False

    def test_auto_matches_platform(self, monkeypatch):
        monkeypatch.setenv("FLSTUDIO_MCP_VIRTUAL_PORTS", "auto")
        # auto = on everywhere except Windows
        assert connection._virtual_ports_enabled() is (sys.platform != "win32")

    def test_default_is_auto(self, monkeypatch):
        monkeypatch.delenv("FLSTUDIO_MCP_VIRTUAL_PORTS", raising=False)
        assert connection._virtual_ports_enabled() is (sys.platform != "win32")


class TestChangelogAtomicPersist:
    def test_append_and_reload(self, tmp_path, monkeypatch):
        from fl_studio_mcp import safety

        monkeypatch.setattr(safety, "_DIR", tmp_path)
        monkeypatch.setattr(safety, "_PATH", tmp_path / "changelog.jsonl")
        log = safety.ChangeLog()
        log.append({"tool": "t1", "n": 1})
        log.append({"tool": "t2", "n": 2})

        # A fresh instance reloads exactly what was persisted (valid JSON lines).
        reloaded = safety.ChangeLog()
        recent = reloaded.recent(10)
        assert [e["tool"] for e in recent] == ["t1", "t2"]
        # No leftover temp file.
        assert not (tmp_path / "changelog.jsonl.tmp").exists()

    def test_concurrent_appends_are_consistent(self, tmp_path, monkeypatch):
        import threading

        from fl_studio_mcp import safety

        monkeypatch.setattr(safety, "_DIR", tmp_path)
        monkeypatch.setattr(safety, "_PATH", tmp_path / "changelog.jsonl")
        log = safety.ChangeLog()

        def worker(base):
            for i in range(20):
                log.append({"tool": f"w{base}", "i": i})

        threads = [threading.Thread(target=worker, args=(b,)) for b in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # deque is bounded to _MAX; every retained entry must be a valid dict
        # (no torn writes), and the file must be parseable on reload.
        reloaded = safety.ChangeLog()
        entries = reloaded.recent(safety._MAX)
        assert all(isinstance(e, dict) and "tool" in e for e in entries)
        assert len(entries) <= safety._MAX
