"""macOS implementation of the piano-roll script trigger.

Strategy (matches the Windows behaviour, adapted to macOS):
  1. Bring FL Studio to the foreground with ``open -a <FL app>`` (no hard-coded
     version -- the app is discovered, e.g. "FL Studio 2025.app").
  2. Send the "Run last script again" hotkey to the now-frontmost app via
     pyautogui.

Notes / caveats:
  * Sending synthetic keystrokes requires macOS **Accessibility** permission for
    the process running this code (System Settings > Privacy & Security >
    Accessibility). Without it the hotkey silently does nothing -- surfaced in
    the returned ``note``.
  * The Piano Roll must be FL's active panel for the shortcut to fire (same as
    on Windows).
  * The default hotkey is Ctrl+Alt+Y; override with FLSTUDIO_MCP_TRIGGER_HOTKEY
    if a given FL/macOS build maps "Run last script again" differently.
"""

from __future__ import annotations

import glob
import os
import subprocess
import time

_APP_ENV = "FLSTUDIO_MCP_APP"          # explicit path to FL Studio.app (optional)


def find_fl_app() -> str | None:
    """Return the path to the FL Studio .app bundle, or None. Env override wins."""
    env = os.environ.get(_APP_ENV)
    if env and os.path.isdir(env):
        return env
    candidates: list[str] = []
    for root in ("/Applications", os.path.expanduser("~/Applications")):
        candidates.extend(sorted(glob.glob(os.path.join(root, "FL Studio*.app")), reverse=True))
    return candidates[0] if candidates else None


def _activate(app_path: str) -> bool:
    """Bring FL to the front. ``open -a`` activates without needing the exact
    (versioned) app name or the process name."""
    try:
        subprocess.run(["open", "-a", app_path], check=True,
                       capture_output=True, timeout=5)
        return True
    except Exception:
        return False


def trigger(hotkey=("ctrl", "alt", "y"), settle=0.35):
    """Focus FL and send the run-last-script hotkey. Returns what it did."""
    app = find_fl_app()
    focused = _activate(app) if app else False
    time.sleep(settle)

    note = None
    try:
        import pyautogui

        pyautogui.FAILSAFE = False
        pyautogui.hotkey(*hotkey)
    except Exception as e:
        note = ("could not send hotkey (%s). On macOS this usually means the "
                "process lacks Accessibility permission (System Settings > "
                "Privacy & Security > Accessibility)." % e)

    if not app:
        note = ("FL Studio.app not found under /Applications. Set %s to its path "
                "if installed elsewhere." % _APP_ENV)

    return {"platform": "darwin", "fl_found": bool(app), "focused": bool(focused),
            "hotkey": "+".join(hotkey), "app": app, "note": note}
