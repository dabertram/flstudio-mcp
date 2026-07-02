# Dev Artifacts — cleanup tracker

This file tracks all throwaway/dev artifacts created during the macOS + cross-platform
hardening effort, so everything can be cleaned up afterwards.

## FL Studio projects saved during dev (max 10)

Rule: stay within the empty project by default. Only save when a test genuinely
needs a persisted project. Keep the count ≤ 10 and list each here.

| # | Project name / path | Purpose | Safe to delete |
|---|---------------------|---------|----------------|
| — | (none yet) | | |

## Temp files / scratch scripts created outside the normal tree

| Path | Purpose | Safe to delete |
|------|---------|----------------|
| — | (none yet) | |

## Environment changes made (deps installed, config written)

| Change | Where | Revert step |
|--------|-------|-------------|
| — | (none yet) | |

## Notes
- Calibration cache (when implemented) persists under `~/.flstudio-mcp/` — safe to delete/rebuild.
- Any MCP client config entries written by the installer are backed up with a timestamp; use the installer's `--restore` to revert.
