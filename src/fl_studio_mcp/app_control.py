"""Start/stop/status control of the FL Studio application -- cross-platform
dispatcher.

Distinct from ``pyscript_trigger`` (which triggers the note-bridge hotkey
inside an already-running FL): this controls the OS-level FL Studio process
itself, so it works even before the daemon/MIDI bridge is up. The
platform-specific mechanics live in the ``_app_{win32,darwin,linux}`` modules;
this module picks the right one AT CALL TIME so merely importing it never
touches a foreign platform's APIs (notably ``ctypes.windll`` on macOS/Linux).
"""

from __future__ import annotations

import sys


def platform_name() -> str:
    if sys.platform == "win32":
        return "win32"
    if sys.platform == "darwin":
        return "darwin"
    return "linux"


def _backend():
    plat = platform_name()
    if plat == "win32":
        from . import _app_win32 as impl
    elif plat == "darwin":
        from . import _app_darwin as impl
    else:
        from . import _app_linux as impl
    return impl


def start_fl_studio(project_path: str | None = None, timeout: float = 15.0) -> dict:
    """Launch FL Studio (or activate it if already running), optionally opening
    a specific project file. Returns a report dict; see the per-platform
    ``start`` for exact fields."""
    return _backend().start(project_path=project_path, timeout=timeout)


def stop_fl_studio(force: bool = False, timeout: float = 15.0) -> dict:
    """Quit FL Studio -- gracefully by default (FL may show its own
    save-changes dialog), or immediately with ``force=True`` (discards unsaved
    work). Returns a report dict."""
    return _backend().stop(force=force, timeout=timeout)


def get_status() -> dict:
    """Report whether the FL Studio process is running, at the OS level."""
    return _backend().status()
