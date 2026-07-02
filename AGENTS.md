# AGENTS.md — working on flstudio-mcp

Guidance for AI agents (and humans) contributing to this repo. Keep changes
small, tested, and reversible.

## What this is
An MCP server that controls FL Studio through a MIDI-SysEx bridge. The split:

- **Controller** (`fl_controller/FLStudioMCP/device_FLStudioMCP.py`) runs INSIDE
  FL. Keep it THIN: return cheap raw data, do no judgement. It can't do file I/O.
  Changing it requires redeploying to FL's `Settings/Hardware/FLStudioMCP/` and
  **restarting FL** to reload.
- **Server** (`src/fl_studio_mcp/`) does all judgement (diagnosis, calibration,
  planning). This is where almost all logic and new tools live.
- **Daemon** (`daemon.py`) owns the MIDI ports and speaks TCP to the server, so
  the bridge works regardless of how the MCP client launches the server.

## Golden rules
1. **Thin controller, smart server.** Never push loops/judgement into the
   controller — a heavy `OnSysEx` tick stalls FL.
2. **Pagination.** SysEx payloads above ~1.5 KB are dropped. List commands
   return one bounded page (`total`/`next_start`); drive them with
   `connection.fetch_all_pages`.
3. **Every write is reversible.** Route project-modifying tools through
   `safety.safe_write` / `safe_write_group` (snapshot → write → readback →
   rollback, persisted change log). Read-only tools don't need it.
4. **Cross-platform.** No platform-specific code at import time. Window/keystroke
   automation lives behind `pyscript_trigger` → `_trigger_{win32,darwin,linux}`.
   Discover FL paths via `paths.py`. MIDI ports self-create on macOS/Linux
   (`connection._virtual_ports_enabled`).

## Dev setup
```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # add ,audio for analysis code
pytest -q                        # offline suite (no FL needed)
ruff check src/ tests/
mypy src/fl_studio_mcp            # gradual; informational in CI
```

## Testing
- **Offline** (`tests/`, `pytest -m "not live"`): pure curve/param/protocol logic
  and tool orchestration via the mock FL bridge (`tests/fixtures/mock_bridge.py`).
  Add coverage here for every new pure function or tool.
- **Live** (`scripts/test_bridge.py`, marker `live`): requires FL running +
  the bridge wired. Used for end-to-end validation, not CI.

## Adding a tool
1. If it needs new FL data, add a `CMD_*` in `protocol.py` AND a thin handler in
   the controller (register it in `_HANDLERS`). Redeploy + restart FL to test.
2. Add the server tool under `src/fl_studio_mcp/tools/`, register it in
   `server.py`. Writes go through the safety layer.
3. Add offline tests (mock bridge). Keep the controller side minimal.

## Generic VST control (the deep-control layer)
- `tools/plugin.py` — param read/set by name/index; `slot=-1` = channel generator.
- `music/vst_params.py` — role grouping + controllability tier.
- `music/value_parse.py` — display-string → (value, unit).
- `music/calibration.py` — sweep→curve + persistent cache under `~/.flstudio-mcp/`.
- `tools/vst.py` — overview / calibrate / unit-set / intent.
Curated per-synth maps should be authored against LIVE param dumps (verify names).

## Client setup
`fl-studio-mcp-install` detects MCP clients and registers the server safely
(backup + idempotent merge). macOS end-to-end setup: `scripts/install_macos.sh`.
