"""Start/stop/status control of the FL Studio application process itself.

OS-level process control (launch/quit the app, optionally with a project
file) -- separate from the MIDI bridge/daemon: these tools work even before
the daemon is running, and ``fl_studio_status`` doesn't require FL's
controller script to be loaded. Use ``fl_ping`` to check the actual MIDI
connection once FL is up.
"""
from __future__ import annotations

from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from .. import app_control


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations={
        "title": "Start FL Studio",
        "readOnlyHint": False, "idempotentHint": True, "openWorldHint": True,
    })
    def fl_studio_start(
        project_path: Annotated[str | None, Field(
            description="Optional path to a .flp project to open. Omitted = "
                        "launch/activate FL with whatever it last had open.")] = None,
        timeout: Annotated[float, Field(
            description="Seconds to wait for the process to appear before "
                        "reporting the launch as unconfirmed.")] = 15.0,
    ) -> dict:
        """Launch FL Studio (or bring it to the front if already running),
        optionally opening a specific project file. OS-level process control --
        does not require the daemon or MIDI bridge to be up. Windows/macOS only
        (no native Linux build)."""
        return app_control.start_fl_studio(project_path=project_path, timeout=timeout)

    @mcp.tool(annotations={
        "title": "Stop FL Studio",
        "readOnlyHint": False, "idempotentHint": True, "openWorldHint": True,
    })
    def fl_studio_stop(
        force: Annotated[bool, Field(
            description="True = force-kill immediately -- UNSAVED CHANGES ARE "
                        "LOST. False (default) = graceful quit; FL shows its own "
                        "save-changes dialog if needed and stays open until "
                        "answered.")] = False,
        timeout: Annotated[float, Field(
            description="Seconds to wait for the process to exit before "
                        "reporting the stop as unconfirmed.")] = 15.0,
    ) -> dict:
        """Quit FL Studio. Defaults to a graceful quit (same as clicking the
        window's close button -- FL prompts to save if there are unsaved
        changes and will still be running until that dialog is answered).
        Pass force=True to kill it immediately; this WILL discard unsaved
        work, so only use it when you're sure."""
        return app_control.stop_fl_studio(force=force, timeout=timeout)

    @mcp.tool(annotations={
        "title": "FL Studio process status",
        "readOnlyHint": True, "idempotentHint": True, "openWorldHint": True,
    })
    def fl_studio_status() -> dict:
        """Report whether the FL Studio process is running and which app/exe
        was found, at the OS level -- independent of the MIDI bridge/daemon.
        Use fl_ping to check the actual MIDI connection once FL is up."""
        return app_control.get_status()
