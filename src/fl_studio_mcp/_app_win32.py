"""Windows process control for the FL Studio application itself.

Distinct from ``_trigger_win32.py`` (which force-focuses an already-running FL
and sends the note-bridge hotkey): this launches, quits, and checks the FL
Studio *process*, independent of whether the daemon/MIDI bridge is connected.

This module is imported ONLY on Windows (by ``app_control``), so the
``ctypes.windll`` references never execute on other platforms.
"""

from __future__ import annotations

import ctypes
import glob
import os
import subprocess
import time
from ctypes import wintypes

_APP_ENV = "FLSTUDIO_MCP_APP"           # explicit path to FL64.exe (optional)
_FL_WINDOW_CLASS = "TFruityLoopsMainForm"

_u = ctypes.windll.user32
_u.FindWindowW.restype = wintypes.HWND
_u.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
_u.PostMessageW.argtypes = [wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM]
_u.PostMessageW.restype = wintypes.BOOL

_WM_CLOSE = 0x0010


def find_fl_exe() -> str | None:
    """Return the path to FL64.exe, or None. Env override wins."""
    env = os.environ.get(_APP_ENV)
    if env and os.path.isfile(env):
        return env
    candidates: list[str] = []
    for root in (os.environ.get("PROGRAMFILES", r"C:\Program Files"),
                 os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")):
        if root:
            candidates.extend(sorted(
                glob.glob(os.path.join(root, "Image-Line", "FL Studio*", "FL64.exe")),
                reverse=True))
    return candidates[0] if candidates else None


def _hwnd():
    return _u.FindWindowW(_FL_WINDOW_CLASS, None)


def is_running() -> bool:
    return bool(_hwnd())


def start(project_path: str | None = None, timeout: float = 15.0) -> dict:
    exe = find_fl_exe()
    if not exe:
        return {"ok": False, "platform": "win32", "app": None,
                "note": "FL64.exe not found under Program Files\\Image-Line. Set "
                        "FLSTUDIO_MCP_APP to its path if installed elsewhere."}

    already = is_running()
    try:
        args = [exe] + ([project_path] if project_path else [])
        subprocess.Popen(args, close_fds=True)
    except Exception as e:
        return {"ok": False, "platform": "win32", "app": exe,
                "already_running": already, "note": "launch failed: %s" % e}

    running = already
    if not running:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if is_running():
                running = True
                break
            time.sleep(0.5)

    return {"ok": running, "platform": "win32", "app": exe,
            "already_running": already, "project_path": project_path,
            "running": running,
            "note": None if running else
                    "launch requested but no FL window was detected within %.0fs" % timeout}


def stop(force: bool = False, timeout: float = 15.0) -> dict:
    exe = find_fl_exe()
    hwnd = _hwnd()
    if not hwnd:
        return {"ok": True, "platform": "win32", "app": exe,
                "already_stopped": True, "stopped": True, "forced": force, "note": None}

    if force:
        try:
            subprocess.run(["taskkill", "/IM", "FL64.exe", "/F"],
                           check=True, capture_output=True, timeout=5)
        except Exception as e:
            return {"ok": False, "platform": "win32", "app": exe,
                    "note": "force-kill failed: %s" % e}
        note = "force-killed -- any unsaved project changes were NOT saved."
    else:
        _u.PostMessageW(hwnd, _WM_CLOSE, 0, 0)
        note = ("close requested -- if FL has unsaved changes it will show its "
                "own save dialog and stay open until answered.")

    stopped = False
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _hwnd():
            stopped = True
            break
        time.sleep(0.5)

    return {"ok": stopped, "platform": "win32", "app": exe, "stopped": stopped,
            "forced": force, "note": note}


def status() -> dict:
    exe = find_fl_exe()
    return {"platform": "win32", "app": exe, "running": is_running()}
