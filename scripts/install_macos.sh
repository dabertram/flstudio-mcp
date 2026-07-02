#!/usr/bin/env bash
# ============================================================================
# FLStudioMCP -- macOS installer (v0.3)
#   [1] controller script  -> FL Settings/Hardware/FLStudioMCP/
#   [2] MCP server          -> pip install -e .
#   [3] note-bridge script  -> seeds MCP_Apply.pyscript in Piano roll scripts/
#   [4] MIDI port check      (virtual ports are auto-created; IAC optional)
#
# macOS uses the SAME FL data layout as Windows:
#   ~/Documents/Image-Line/FL Studio/Settings
# ============================================================================
set -euo pipefail

FL_SETTINGS="$HOME/Documents/Image-Line/FL Studio/Settings"
TARGET="$FL_SETTINGS/Hardware/FLStudioMCP"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PY="${PYTHON:-python3}"

echo
echo "[1/4] Installing FL Studio controller script..."
if [[ ! -d "$FL_SETTINGS/Hardware" ]]; then
  echo "  FL Studio Hardware folder not found at:"
  echo "    $FL_SETTINGS/Hardware"
  echo "  Open FL Studio at least once, then re-run this script."
  exit 1
fi
mkdir -p "$TARGET"
cp "$REPO_ROOT/fl_controller/FLStudioMCP/device_FLStudioMCP.py" "$TARGET/"
echo "  Installed to $TARGET"

echo
echo "[2/4] Installing the MCP server (editable)..."
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "  $PY not found. Install Python 3.10+ (e.g. 'brew install python@3.12') and re-run."
  exit 1
fi
cd "$REPO_ROOT"
"$PY" -m pip install --upgrade pip >/dev/null
"$PY" -m pip install -e .

echo
echo "[3/4] Seeding the note-bridge pyscript (MCP_Apply)..."
"$PY" -c "import os, fl_studio_mcp.pyscript_gen as g; os.makedirs(g.PIANO_ROLL_SCRIPTS_DIR, exist_ok=True); print('   seeded ' + g.write_apply_script([], mode='append'))" \
  || echo "   Note: could not pre-seed MCP_Apply (Piano roll scripts folder missing?). Non-fatal -- the daemon writes it on the first note-write."

echo
echo "[4/4] Checking MIDI ports..."
"$PY" - <<'PYEOF'
import mido
names = set(mido.get_output_names()) | set(mido.get_input_names())
rx, tx = "FLStudioMCP RX", "FLStudioMCP TX"
have = [n for n in (rx, tx) if any(n.lower() in x.lower() for x in names)]
if len(have) == 2:
    print("   Both named ports already present (IAC or a running daemon).")
else:
    print("   Named ports not present yet -- that's OK on macOS:")
    print("   the daemon/server SELF-CREATES virtual CoreMIDI ports on start")
    print("   (no IAC Driver setup needed). To force this: FLSTUDIO_MCP_VIRTUAL_PORTS=1")
PYEOF

cat <<EOF

Done.

Next steps:
  1. Start the bridge daemon and keep it running (it creates the virtual
     MIDI ports 'FLStudioMCP RX' / 'FLStudioMCP TX'):
        fl-studio-mcp-daemon
  2. Open FL Studio, then Options > MIDI Settings:
       Input  > 'FLStudioMCP RX': Enable, Controller type = FLStudioMCP, Port = 42
       Output > 'FLStudioMCP TX': Enable, Port = 42  (the SAME number)
     View > Script output should show '[FLStudioMCP] Ready'.
  3. (Note writing) Open the Piano roll and run 'MCP_Apply' ONCE from its
     Scripting menu each session. On macOS, grant Accessibility permission so
     the trigger hotkey reaches FL (System Settings > Privacy & Security >
     Accessibility).
  4. Register the server with your MCP client, e.g. Claude Desktop
     (~/Library/Application Support/Claude/claude_desktop_config.json):
        "fl-studio": { "command": "fl-studio-mcp",
                       "env": { "FLSTUDIO_MCP_TRANSPORT": "tcp" } }
  5. Verify: run  python scripts/test_bridge.py   (or ask your client fl_ping).

Optional audio features:  pip install -e ".[audio]"   (tempo/key + melody)
                          pip install -e ".[audio,audio-accurate]"  (+ CREPE)
EOF

