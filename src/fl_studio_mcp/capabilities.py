"""Runtime capability introspection.

Reports, in one place, what this install can do automatically vs. what still
needs a manual step -- per OS, transport, and note-bridge automation. Pure and
env-based (no bridge needed) so it always answers, even when FL is closed.
"""

from __future__ import annotations

import os


def describe_capabilities() -> dict:
    """Return a structured capability report. Pure (env + platform only)."""
    from .connection import _virtual_ports_enabled
    from .paths import find_piano_roll_scripts_dir
    from .pyscript_trigger import _hotkey, platform_name

    plat = platform_name()
    transport = os.environ.get("FLSTUDIO_MCP_TRANSPORT", "direct").lower()
    virtual = _virtual_ports_enabled()
    hotkey = "+".join(_hotkey())

    # Note-bridge (piano-roll write) automation differs by OS.
    if plat == "win32":
        focus = "native window focus (Win32) + synthetic hotkey"
        focus_auto = True
        focus_note = None
    elif plat == "darwin":
        focus = "activate FL via `open -a` + synthetic hotkey"
        focus_auto = True
        focus_note = ("keystroke send needs macOS Accessibility permission for "
                      "the process running the daemon/server")
    else:
        focus = "hotkey only (no reliable cross-WM focus)"
        focus_auto = False
        focus_note = "click FL's Piano Roll first; focus is not automated on Linux"

    return {
        "platform": plat,
        "transport": transport,                       # 'direct' | 'tcp'
        "midi_ports": {
            "virtual_ports_enabled": virtual,
            "note": ("ports are self-created (no IAC/loopMIDI setup needed)"
                     if virtual else
                     "named ports must already exist (loopMIDI on Windows, or set env)"),
        },
        "note_bridge": {
            "hotkey": hotkey,
            "focus_method": focus,
            "focus_automated": focus_auto,
            "focus_note": focus_note,
            "one_time_setup": ("run 'MCP_Apply' ONCE from the Piano roll Scripting "
                               "menu per FL session to arm the hotkey (no FL API to "
                               "automate this)"),
            "piano_roll_scripts_dir": find_piano_roll_scripts_dir(),
        },
        "app_control": _app_control(plat),
        "automated": _automated(plat),
        "manual_steps": _manual_steps(plat, virtual),
        "fl_api_limits": [
            "cannot load new plugin/VST instances",
            "cannot create patterns from scratch (clone instead)",
            "cannot load audio files or render audio",
            "preset recall is walled off for some VSTs (e.g. Serum)",
        ],
    }


def _app_control(plat: str) -> dict:
    """OS-level FL process control (fl_studio_start/stop/status) per platform."""
    if plat == "win32":
        return {"supported": True,
                "method": "launch FL64.exe; WM_CLOSE (graceful) or taskkill (force)",
                "note": None}
    if plat == "darwin":
        return {"supported": True,
                "method": "`open -a` launch; AppleScript quit (graceful) or pkill (force)",
                "note": None}
    return {"supported": False, "method": None,
            "note": "FL Studio has no native Linux build; start it yourself"}


def _automated(plat: str) -> list[str]:
    base = [
        "transport (play/stop/tempo/position)",
        "mixer + channel read/write (volume/pan/mute/solo/name/color/routing)",
        "plugin parameter read/write (native + VST, by name or index)",
        "mixing/compression/reverb/delay intents (calibrated)",
        "mix diagnosis + gated, reversible fixes",
        "piano-roll note writing (after one-time arm)",
        "pattern clone/name + arrangement markers",
        "MIDI export to a .mid file",
    ]
    return base


def _manual_steps(plat: str, virtual: bool) -> list[str]:
    steps = []
    if not virtual:
        if plat == "win32":
            steps.append("create the two loopMIDI ports (FLStudioMCP RX / TX)")
        else:
            steps.append("create the two IAC Driver buses (FLStudioMCP RX / TX), "
                         "or set FLSTUDIO_MCP_VIRTUAL_PORTS=1")
    steps.append("in FL: enable FLStudioMCP RX (input, Controller type=FLStudioMCP) "
                 "and FLStudioMCP TX (output) with the SAME port number")
    steps.append("run 'MCP_Apply' once from the Piano roll Scripting menu each session")
    if plat == "darwin":
        steps.append("grant Accessibility permission so note-write hotkeys reach FL")
    steps.append("load plugins / audio files by hand (FL API can't); then Claude configures them")
    return steps
