"""Linux process control -- FL Studio has no native Linux build.

Wine/Bottles/PlayOnLinux setups vary too much (prefix path, wrapper script,
process name) to target generically, so this is a stub: every call reports
unsupported rather than guessing. Kept so the dispatcher never crashes on
import here.
"""

from __future__ import annotations

_NOTE = ("FL Studio has no native Linux build; start/stop process control isn't "
         "supported here (Wine setups vary too much to target generically). "
         "Start it yourself and use fl_ping to confirm the bridge is up.")


def start(project_path: str | None = None, timeout: float = 15.0) -> dict:
    return {"ok": False, "platform": "linux", "app": None, "note": _NOTE}


def stop(force: bool = False, timeout: float = 15.0) -> dict:
    return {"ok": False, "platform": "linux", "app": None, "note": _NOTE}


def status() -> dict:
    return {"platform": "linux", "app": None, "running": None, "note": _NOTE}
