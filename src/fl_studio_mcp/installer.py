"""One-command MCP client registration for fl-studio-mcp.

Detects installed MCP clients and registers this server's stdio launch command
into each selected client's config -- safely: create-if-missing, timestamped
backup, insert-only-if-absent/changed, JSON re-validate, and a --restore path.

Design notes:
  * Auto-registration is limited to clients that keep MCP servers in a DEDICATED
    JSON file with a stable top-level key (Claude Desktop, Cursor, Windsurf) --
    merging those is safe. For clients whose config is nested/evolving (VS Code,
    Zed, Cline, Claude Code), we print an exact copy-paste snippet + path
    instead of writing blindly.
  * Exact paths/keys should be re-checked against current client docs over time;
    they're centralised here with a self-test (``--list``).

CLI:
    fl-studio-mcp-install --list
    fl-studio-mcp-install --all [--dry-run]
    fl-studio-mcp-install --clients claude-desktop,cursor
    fl-studio-mcp-install --uninstall --clients cursor
    fl-studio-mcp-install --restore <backup-file>
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

SERVER_NAME = "fl-studio-mcp"
SERVER_COMMAND = "fl-studio-mcp"
SERVER_ENV = {"FLSTUDIO_MCP_TRANSPORT": "tcp"}


@dataclass
class ClientSpec:
    id: str
    label: str
    schema_key: str                 # "mcpServers" | "servers" | "context_servers"
    paths: dict                     # platform -> path template (str)
    auto: bool = True               # safe to auto-merge?
    stdio_type: bool = False        # include "type": "stdio" (VS Code style)
    note: str = ""
    detect_hint: list = field(default_factory=list)  # extra dirs whose existence implies installed


def _home() -> Path:
    return Path.home()


def _appdata() -> Path:
    return Path(os.environ.get("APPDATA", str(_home() / "AppData" / "Roaming")))


def _expand(template: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(template)))


# Path templates use ~ and $APPDATA; resolved per current OS.
CLIENTS: list[ClientSpec] = [
    ClientSpec(
        id="claude-desktop", label="Claude Desktop", schema_key="mcpServers", auto=True,
        paths={
            "darwin": "~/Library/Application Support/Claude/claude_desktop_config.json",
            "win32": "$APPDATA/Claude/claude_desktop_config.json",
            "linux": "~/.config/Claude/claude_desktop_config.json",
        }),
    ClientSpec(
        id="cursor", label="Cursor", schema_key="mcpServers", auto=True,
        paths={
            "darwin": "~/.cursor/mcp.json",
            "win32": "~/.cursor/mcp.json",
            "linux": "~/.cursor/mcp.json",
        }),
    ClientSpec(
        id="windsurf", label="Windsurf (Codeium)", schema_key="mcpServers", auto=True,
        paths={
            "darwin": "~/.codeium/windsurf/mcp_config.json",
            "win32": "~/.codeium/windsurf/mcp_config.json",
            "linux": "~/.codeium/windsurf/mcp_config.json",
        }),
    ClientSpec(
        id="vscode", label="VS Code (workspace .vscode/mcp.json)", schema_key="servers",
        auto=False, stdio_type=True,
        paths={"darwin": "./.vscode/mcp.json", "win32": "./.vscode/mcp.json",
               "linux": "./.vscode/mcp.json"},
        note="VS Code uses a 'servers' map; register per-workspace or via the UI."),
    ClientSpec(
        id="zed", label="Zed", schema_key="context_servers", auto=False,
        paths={"darwin": "~/.config/zed/settings.json", "win32": "$APPDATA/Zed/settings.json",
               "linux": "~/.config/zed/settings.json"},
        note="Zed nests servers under 'context_servers' in settings.json; edit manually."),
    ClientSpec(
        id="claude-code", label="Claude Code (CLI)", schema_key="mcpServers", auto=False,
        paths={"darwin": "~/.claude.json", "win32": "~/.claude.json", "linux": "~/.claude.json"},
        note="Prefer: run `claude mcp add fl-studio -- fl-studio-mcp` (sets env separately)."),
]


def config_path(spec: ClientSpec) -> Path | None:
    tmpl = spec.paths.get(sys.platform) or spec.paths.get("linux")
    return _expand(tmpl) if tmpl else None


def is_installed(spec: ClientSpec) -> bool:
    """A client counts as installed if its config file OR its parent dir exists."""
    path = config_path(spec)
    if path is None:
        return False
    if path.exists():
        return True
    # parent config dir existing implies the app created its data folder
    parent = path.parent
    return parent.exists() and spec.id != "vscode"  # vscode workspace file is project-local


def detect_clients() -> list[ClientSpec]:
    return [c for c in CLIENTS if is_installed(c)]


def server_entry(spec: ClientSpec) -> dict:
    entry: dict = {"command": SERVER_COMMAND, "env": dict(SERVER_ENV)}
    if spec.stdio_type:
        entry = {"type": "stdio", **entry}
    return entry


def merge_config(doc: dict, spec: ClientSpec, name: str, entry: dict) -> tuple[dict, bool]:
    """Insert/update our server under the client's schema key. PURE.

    Returns (new_doc, changed). Idempotent: no change if an identical entry is
    already present.
    """
    doc = dict(doc or {})
    servers = dict(doc.get(spec.schema_key) or {})
    if servers.get(name) == entry:
        return doc, False
    servers[name] = entry
    doc[spec.schema_key] = servers
    return doc, True


def remove_from_config(doc: dict, spec: ClientSpec, name: str) -> tuple[dict, bool]:
    """Remove our server entry. PURE. Returns (new_doc, changed)."""
    doc = dict(doc or {})
    servers = dict(doc.get(spec.schema_key) or {})
    if name not in servers:
        return doc, False
    servers.pop(name)
    doc[spec.schema_key] = servers
    return doc, True


def _load(path: Path) -> dict:
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _backup(path: Path) -> Path | None:
    if path.is_file():
        bak = path.with_suffix(path.suffix + ".bak.%d" % int(time.time()))
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        return bak
    return None


def _atomic_write(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def register(spec: ClientSpec, *, dry_run: bool = False, remove: bool = False) -> dict:
    """Register (or remove) our server in a client's config. Returns a report."""
    path = config_path(spec)
    if path is None:
        return {"client": spec.id, "ok": False, "error": "no config path for this OS"}

    if not spec.auto:
        entry = server_entry(spec)
        return {"client": spec.id, "ok": True, "action": "manual",
                "path": str(path), "schema_key": spec.schema_key,
                "snippet": {spec.schema_key: {SERVER_NAME: entry}},
                "note": spec.note or "auto-registration disabled for this client; add manually"}

    doc = _load(path)
    if remove:
        new_doc, changed = remove_from_config(doc, spec, SERVER_NAME)
    else:
        new_doc, changed = merge_config(doc, spec, SERVER_NAME, server_entry(spec))

    if not changed:
        return {"client": spec.id, "ok": True, "action": "unchanged", "path": str(path)}
    if dry_run:
        return {"client": spec.id, "ok": True, "action": "would-" + ("remove" if remove else "add"),
                "path": str(path)}

    bak = _backup(path)
    try:
        _atomic_write(path, new_doc)
        json.loads(path.read_text(encoding="utf-8"))  # validate
    except Exception as e:
        if bak:
            path.write_text(bak.read_text(encoding="utf-8"), encoding="utf-8")
        return {"client": spec.id, "ok": False, "error": "write/validate failed: %s" % e,
                "restored_from": str(bak) if bak else None}
    return {"client": spec.id, "ok": True, "action": ("removed" if remove else "registered"),
            "path": str(path), "backup": str(bak) if bak else None}


def _by_ids(ids: list[str]) -> list[ClientSpec]:
    idset = {i.strip() for i in ids if i.strip()}
    return [c for c in CLIENTS if c.id in idset]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="fl-studio-mcp-install",
                                 description="Register fl-studio-mcp with MCP clients.")
    ap.add_argument("--list", action="store_true", help="list known + detected clients")
    ap.add_argument("--all", action="store_true", help="target all DETECTED clients")
    ap.add_argument("--clients", help="comma-separated client ids to target")
    ap.add_argument("--uninstall", action="store_true", help="remove the server entry instead of adding")
    ap.add_argument("--dry-run", action="store_true", help="preview without writing")
    ap.add_argument("--restore", metavar="BACKUP", help="restore a client config from a .bak file")
    args = ap.parse_args(argv)

    if args.restore:
        bak = Path(args.restore)
        target = Path(str(bak).split(".bak.")[0]) if ".bak." in str(bak) else None
        if not bak.is_file() or target is None:
            print("restore: need an existing '<config>.bak.<ts>' file")
            return 2
        target.write_text(bak.read_text(encoding="utf-8"), encoding="utf-8")
        print("restored %s <- %s" % (target, bak))
        return 0

    detected = detect_clients()
    if args.list or (not args.all and not args.clients):
        det_ids = {c.id for c in detected}
        print("Known MCP clients (auto = safe to auto-register):")
        for c in CLIENTS:
            p = config_path(c)
            mark = "detected" if c.id in det_ids else "-"
            print("  %-14s auto=%-5s [%-8s] %s" % (c.id, str(c.auto).lower(), mark, p))
        if not args.list:
            print("\nRe-run with --all (detected) or --clients id1,id2. Add --dry-run to preview.")
        return 0

    targets = detected if args.all else _by_ids((args.clients or "").split(","))
    if not targets:
        print("No matching clients. Use --list to see ids.")
        return 1

    rc = 0
    for spec in targets:
        rep = register(spec, dry_run=args.dry_run, remove=args.uninstall)
        if rep.get("action") == "manual":
            print("\n[%s] add this to %s :" % (rep["client"], rep["path"]))
            print(json.dumps(rep["snippet"], indent=2))
            if rep.get("note"):
                print("  note:", rep["note"])
        else:
            status = "OK" if rep.get("ok") else "FAIL"
            print("[%s] %s: %s (%s)" % (rep["client"], status,
                                        rep.get("action", rep.get("error", "")),
                                        rep.get("path", "")))
            if not rep.get("ok"):
                rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
