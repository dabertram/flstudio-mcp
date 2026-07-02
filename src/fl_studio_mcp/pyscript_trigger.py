"""Trigger FL's "Run last script again" hotkey -- cross-platform dispatcher.

FL re-reads the piano-roll .pyscript on this hotkey, so paired with pyscript_gen
this applies fresh notes with no manual click. The platform-specific mechanics
(window focus + key send) live in the ``_trigger_{win32,darwin,linux}`` modules;
this module picks the right one AT CALL TIME so merely importing it never touches
a foreign platform's APIs (notably ``ctypes.windll`` on macOS/Linux).

The hotkey defaults to Ctrl+Alt+Y and can be overridden with
``FLSTUDIO_MCP_TRIGGER_HOTKEY`` (e.g. "ctrl+alt+y" or "cmd+alt+y").
"""

from __future__ import annotations

import os
import sys

DEFAULT_HOTKEY = ("ctrl", "alt", "y")


def _hotkey() -> tuple[str, ...]:
    env = os.environ.get("FLSTUDIO_MCP_TRIGGER_HOTKEY")
    if env:
        keys = tuple(k.strip().lower() for k in env.replace(" ", "").split("+") if k.strip())
        if keys:
            return keys
    return DEFAULT_HOTKEY


def platform_name() -> str:
    if sys.platform == "win32":
        return "win32"
    if sys.platform == "darwin":
        return "darwin"
    return "linux"


def trigger_run_last_script(settle: float = 0.35) -> dict:
    """Focus FL and send the run-last-script hotkey. Returns a dict describing
    what happened: ``{platform, fl_found, focused, hotkey, note?}``. The trigger
    is best-effort -- it cannot confirm the script actually ran (see the
    ``setup`` hint the caller adds)."""
    hotkey = _hotkey()
    plat = platform_name()
    try:
        if plat == "win32":
            from ._trigger_win32 import trigger as _impl
        elif plat == "darwin":
            from ._trigger_darwin import trigger as _impl
        else:
            from ._trigger_linux import trigger as _impl
    except Exception as e:
        return {"platform": plat, "fl_found": None, "focused": False,
                "hotkey": "+".join(hotkey),
                "note": "trigger backend unavailable on this platform (%s)" % e}
    return _impl(hotkey=hotkey, settle=settle)

