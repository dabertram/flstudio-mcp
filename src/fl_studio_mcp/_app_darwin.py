"""macOS process control for the FL Studio application itself.

Distinct from ``_trigger_darwin.py`` (which focuses an already-running FL and
sends the note-bridge hotkey): this launches, quits, and checks the FL Studio
*process*, independent of whether the daemon/MIDI bridge is connected.
"""

from __future__ import annotations

import os
import subprocess
import time

from ._trigger_darwin import find_fl_app


def _app_name(app_path: str) -> str:
    return os.path.splitext(os.path.basename(app_path))[0]


def is_running(app_path: str) -> bool:
    # macOS app bundles don't always run under a process name matching the
    # bundle's display name (FL Studio's binary is "OsxFL", not "FL Studio
    # 2025") -- match on the bundle PATH instead, which is stable and always
    # present in the launched process's command line.
    try:
        r = subprocess.run(["pgrep", "-f", app_path], capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False


def start(project_path: str | None = None, timeout: float = 15.0) -> dict:
    app = find_fl_app()
    if not app:
        return {"ok": False, "platform": "darwin", "app": None,
                "note": "FL Studio.app not found under /Applications. Set "
                        "FLSTUDIO_MCP_APP to its path if installed elsewhere."}

    already = is_running(app)
    cmd = ["open", "-a", app]
    if project_path:
        cmd.append(project_path)
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=10)
    except Exception as e:
        return {"ok": False, "platform": "darwin", "app": app,
                "already_running": already, "note": "launch failed: %s" % e}

    running = already
    if not running:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if is_running(app):
                running = True
                break
            time.sleep(0.5)

    return {"ok": running, "platform": "darwin", "app": app,
            "already_running": already, "project_path": project_path,
            "running": running,
            "note": None if running else
                    "launch requested but the process wasn't detected within %.0fs" % timeout}


def stop(force: bool = False, timeout: float = 15.0) -> dict:
    app = find_fl_app()
    if not app:
        return {"ok": False, "platform": "darwin", "app": None,
                "note": "FL Studio.app not found under /Applications."}
    if not is_running(app):
        return {"ok": True, "platform": "darwin", "app": app,
                "already_stopped": True, "stopped": True, "forced": force, "note": None}

    name = _app_name(app)
    if force:
        try:
            # Match by bundle PATH, not process name (FL's binary is "OsxFL",
            # not the bundle's display name -- see is_running()).
            subprocess.run(["pkill", "-f", app], check=True, capture_output=True, timeout=5)
        except Exception as e:
            return {"ok": False, "platform": "darwin", "app": app,
                    "note": "force-kill failed: %s" % e}
        note = "force-killed -- any unsaved project changes were NOT saved."
    else:
        try:
            subprocess.run(["osascript", "-e", 'tell application "%s" to quit' % name],
                           check=True, capture_output=True, timeout=10)
        except Exception as e:
            return {"ok": False, "platform": "darwin", "app": app,
                    "note": "graceful quit failed: %s" % e}
        note = ("graceful quit sent -- if FL has unsaved changes it will show its "
                "own save dialog and stay open until answered.")

    stopped = False
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not is_running(app):
            stopped = True
            break
        time.sleep(0.5)

    return {"ok": stopped, "platform": "darwin", "app": app, "stopped": stopped,
            "forced": force, "note": note}


def status() -> dict:
    app = find_fl_app()
    running = bool(app and is_running(app))
    return {"platform": "darwin", "app": app, "running": running}
