"""Linux implementation of the piano-roll script trigger.

There's no reliable, dependency-free way to force-focus an arbitrary window
across every Linux window manager, so this is best-effort: send the hotkey to
whatever is focused (assumed to be FL). The user should click FL's Piano Roll
first. Kept minimal on purpose.
"""

from __future__ import annotations

import time


def trigger(hotkey=("ctrl", "alt", "y"), settle=0.35):
    note = None
    try:
        import pyautogui

        pyautogui.FAILSAFE = False
        time.sleep(settle)
        pyautogui.hotkey(*hotkey)
    except Exception as e:
        note = ("could not send hotkey (%s). Install pyautogui and ensure an X/"
                "Wayland session with input access; then click FL's Piano Roll "
                "and press the hotkey manually if needed." % e)
    return {"platform": "linux", "fl_found": None, "focused": False,
            "hotkey": "+".join(hotkey), "note": note}
