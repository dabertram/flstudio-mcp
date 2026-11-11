# Feasibility scan and design decisions (E3 / E7)

Offline assessment of what is reachable within FL Studio's MIDI-scripting API,
and the resulting accepted/rejected design decisions. Live benchmarks (E4-E6)
and the macOS automation risk matrix (E1) still need a running FL session.

## E3 — Missing-functionality feasibility

| Capability | Feasible? | Basis |
|---|---|---|
| Load new plugin/VST instances | No | No FL API; `fl_load_plugin` explains the limit and offers the manual step |
| Create patterns from scratch | No | API only clones; `fl_arrange_clone_pattern` / `fl_arrange_new_pattern` work around it |
| Load audio files / render audio | No | No scripting API; analysis works on files the user exports |
| Preset recall for walled-off VSTs (Serum) | No | See `SERUM_PROBE_FINDING.md` |
| Run a piano-roll pyscript programmatically | Partly | One manual arm per session, then hotkey re-trigger (note bridge) |
| Generic VST param read/write + calibration | Yes | Shipped (F3); opaque plugins degrade to normalized values |
| Playlist track / arrangement read / step grid / patterns | Yes | Shipped (F-T1/F-T2); live re-validation pending |
| Start/stop FL process | Yes (Win/macOS) | Shipped as OS-level control, independent of the bridge |
| Large list responses | Yes, paged | SysEx drops payloads above ~1.5 KB; pagination via `fetch_all_pages` |

## E7 — Decisions

Accepted:
- **Thin controller, smart server** — heavy `OnSysEx` work stalls FL; all judgement runs server-side.
- **SysEx transport with pagination** instead of a file queue — no polling, bounded payloads.
- **Daemon owns MIDI ports** — works regardless of how the MCP client starts the server.
- **Self-created virtual ports on macOS/Linux** — removes manual IAC setup.
- **Every write via the safety layer** (snapshot, write, readback, rollback, change log).
- **Runtime calibration with persistent, signature-keyed cache** instead of hard-coded curves only.
- **Platform adapters chosen at call time** — no foreign-platform imports (e.g. `ctypes.windll`).
- **Capability introspection** (`fl_capabilities`) so clients see automated vs. manual per OS.

Rejected:
- **Plugin loading / pattern creation via UI automation** — fragile, breaks across FL builds.
- **Linux process control under Wine** — setups vary too much; reported as unsupported.
- **Hand-authored per-synth maps without live dumps** — deferred until verified parameter dumps exist (F3-2b).
- **Judgement inside the controller** — rejected by the thin-controller rule.
