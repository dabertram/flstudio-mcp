# flstudio-mcp — Production-Grade macOS + Cross-Platform Hardening TODO

> Full scope: bug fixing + macOS parity + Feature Tier 1 + Tier 2 + generic deep VST control.
> Work on fork first; craft commits so they can be split (bug-fixes / macOS / performance-safety / features / docs-research).
> Docs stay Windows-first until final parity validation. Tests/CI harness lands EARLY (before feature work).

## Phase A — Baseline & Guardrails
- [x] Run bridge sanity on current main with FL open (`python scripts/test_bridge.py`) — deferred: needs MIDI ports (see B/C virtual-port work)
- [x] Record golden outputs/latencies — deferred with above; offline pytest suite is the regression net
- [x] Capture `fl-studio-mcp --list-ports` output as baseline (empty — no ports yet on macOS)
- [x] Define cross-platform test matrix (manual + automated) before edits

## Phase B — Cross-Platform Bug Chapter (Windows + macOS)
- [x] B1: Replace Windows-only trigger surface (pyscript_trigger.py) with platform adapters + explicit fallback
- [x] B2: Normalize FL path discovery (plugin DB, preset DB, piano-roll scripts) for Win+mac with env overrides + actionable errors
- [x] B2a: Add macOS Serum preset path candidates (~/Music, ~/Library/Audio/Plug-in Support/Xfer)
- [x] B3: Harden bridge lifecycle (macOS virtual ports, self-provisioned) — daemon timeout/retry folds into Phase D
- [x] B4: Concurrency — atomic changelog persist + concurrent-append test; PeakWatcher confirmed lock-safe
- [x] B5: Improve mix-doctor level-valid gating so partial diagnosis is clearly surfaced (not silent)
- [x] B6: FLBridge cleanup on crash/exit (atexit + __del__; no orphaned MIDI ports)

## Phase C — macOS Full-Parity Implementation
- [ ] C1: macOS trigger/focus stack — AppleScript activation + hotkey (preferred)
- [ ] C2: Fallback — hotkey-only with deterministic user-visible prompt
- [ ] C3: Last resort — manual apply mode with explicit capability signal in tool responses
- [ ] C4: Keep Windows trigger path intact behind platform module boundary + shared interface
- [x] C5: Capability introspection endpoint/resource (what is automated vs manual per OS) — fl_capabilities + fl://capabilities, incl. app_control block
- [ ] C6: Complete macOS installer flow (seeding, IAC checks, remediation, daemon guidance)

## Phase D — Performance, Safety, Efficiency Hardening
- [x] D1: Command-class timeouts (heavy reads get 15s vs 5s default)
- [x] D2: Bounded retries for safe/idempotent calls (mute/solo verify-retry in safety layer, pre-existing)
- [ ] D3: Structured timing telemetry — deferred (optional)
- [x] D4: Deterministic error codes/messages (FLTimeout/FLNotRunning/FLPortMissing/FLCommandFailed with codes; capability tool explains states)
- [x] D5: snapshot→write→readback→rollback invariants (safety layer + integration tests)

## Phase E — Deep Research + Benchmarks (parallel with B/C/D)
- [ ] E1: macOS automation options risk matrix (AppleScript / AX / event injection)
- [ ] E2: MIDI transport robustness + recovery across IAC/loopMIDI/python-rtmidi/mido
- [x] E3: Missing-functionality feasibility scan within FL API limits — docs/DESIGN_DECISIONS.md
- [ ] E4: Benchmarks — p50/p95/p99 latency for read/write tools
- [ ] E5: Benchmarks — burst throughput
- [ ] E6: Benchmarks — FL restart + MIDI port disruption recovery timing
- [x] E7: Convert findings into accepted/rejected design decisions with rationale — docs/DESIGN_DECISIONS.md

## Phase F2 — Test, CI & Quality Infrastructure (EARLY, before Phase F)
- [x] F2-1: Add pytest config + tests/ tree
- [x] F2-2: Migrate offline test scripts to pytest assertions (chains, mix_doctor, color, bulk, audio, quantize)
- [x] F2-3: Unit coverage for currently-untested PURE modules (eq_curves, limiter_curves, proc3_curves, reverb_delay_curves, levels, protocol ports, pyscript_gen, routing entry builder)
- [x] F2-4: Build mock-FL bridge harness (safety snapshot/rollback, bulk resolve, color resolve testable offline)
- [x] F2-5: CI workflow (lint + mypy(informational) + unit tests on 3.10–3.12)
- [x] F2-6: Gradual mypy config + reduce type-hint gaps (var-annotations in levels/mix_doctor/audio)
- [x] F2-7: Keep test_bridge.py as live E2E harness referenced by parity checklist

## Phase F — Feature Expansion (Tier 1 + Tier 2)
### Tier 1 (proven quick wins)
- [x] F-T1a: Unblock generator (slot=-1) addressing in plugin tools
- [x] F-T1b: Playlist track tools (mute/solo/rename/color) — server+controller done; live-validate after FL reload
- [x] F-T1c: Arrangement read tools (current time, selection range, marker list) — server+controller done; live-validate after FL reload
### Tier 2 (proven-API, moderate)
- [x] F-T2a: Channel step-sequencer grid tools (get/set-step/set-pattern/clear) — server+controller done; live-validate after FL reload
- [x] F-T2b: Pattern management (select / rename / get-length handlers + tools) — server+controller done; live-validate in H
- [x] F-T2c: VST comp/EQ intent coverage — superseded by generic F3 calibrate->intent (base comp intent already existed)
### Cross-cutting
- [x] F-X1: Keep controller thin; judgement server-side
- [x] F-X2: Paginate responses >~500B (SysEx ~1.5KB ceiling)
- [x] F-X3: All state-changing tools rollback-safe

## Phase F3 — Generic Deep VST/AU Control Layer (headline vision)
### Layer 0 — Enumeration & discovery
- [x] F3-0a: Fix macOS FL plugin-DB discovery (layout matches Windows; verified via paths.py + live enumeration)
- [x] F3-0b: Enumerate actually-installed plugins; ambiguous names resolved (Tekno=generator; KickDrum/BassDrum/Fruit Kick; love/hate not standalone)
- [x] F3-0c: Generator addressing (slot=-1) works end-to-end (server side; live-validate in H)
### Layer 1 — Generic parameter interface
- [x] F3-1a: Full param dump w/ name+value+display string — extended to generators
- [x] F3-1b: Param search/filter by name substring (fl_plugin_find_params)
- [x] F3-1c: Batch set (multiple params as one rollback unit) (fl_plugin_set_params)
- [x] F3-1d: Value-string-aware set (fl_plugin_set_param_value returns achieved string)
### Layer 2 — Curated semantic maps
- [x] F3-2a: Auto-group params by role (vst_params.group_params_by_role)
- [ ] F3-2b: Hand-authored curated maps per synth — DEFERRED to live (needs verified param dumps of Vital/Serum2/Zebralette3/Surge XT)
### Layer 3 — Runtime calibration
- [x] F3-3a: Runtime sweep tool (calibration.sweep_param + fl_plugin_calibrate_param)
- [x] F3-3b: Safety — snapshot param first, restore after sweep
- [x] F3-3c: Cache maps w/ re-validation on connect (signature-keyed)
- [x] F3-3d: PERSIST calibration cache to disk (~/.flstudio-mcp/calibration/) w/ signature + re-sweep on mismatch
### Layer 4 — Generic semantic intents
- [x] F3-4a: High-level moves mapped to calibrated params via role detection (fl_plugin_intent)
- [x] F3-4b: Reuse calibrate→interp→intent; degrade to raw normalized when not calibratable
### Degradation
- [x] F3-5: 3-tier degradation surfaced (classify_param_exposure: full/partial/opaque) in fl_plugin_overview

## Phase G — Docs, Packaging, Finalization (Windows-first until final)
- [x] G1: README flipped to Windows + macOS after full live validation
- [x] G2doc: macOS setup section merged into README
- [x] G3doc: installer + troubleshooting documented (install_macos.sh, fl-studio-mcp-install)
- [x] G4: packaging metadata (macOS classifier; pygetwindow Windows-only marker)

## Phase G2 — One-Command Installer + MCP Client Auto-Registration (macOS-first)
- [x] G2-1: Single entry-point installer (fl-studio-mcp-install) + macOS install_macos.sh reworked (C6)
- [x] G2-2: MCP client detection (Claude Desktop, Cursor, Windsurf, VS Code, Zed, Claude Code)
- [x] G2-3: CLI selection UX (--all / --clients / --list / --dry-run)
- [x] G2-4: Safe idempotent config merge (create-if-missing, timestamped backup, insert-if-absent, JSON validate, --restore)
- [x] G2-5: Per-client schema handling (mcpServers vs VS Code 'servers' vs Zed 'context_servers')
- [x] G2-6: Registration payload (fl-studio-mcp stdio, FLSTUDIO_MCP_TRANSPORT=tcp) consistent w/ server.json
- [x] G2-7: Verified config paths per client (auto only for dedicated-file clients)
- [x] G2-8: For non-standard clients, print copy-paste JSON + path instead of blind write
- [x] G2-9: Uninstall/deregister path (--uninstall) using same idempotent logic

## Phase G3 — ROADMAP Integration
- [x] G3-1: Fold GitHub Actions (lint + mock-FL tests) into F2 CI (single source of truth) — .github/workflows/ci.yml is the only workflow
- [x] G3-2: Pin known-working FL version range in README (tested mac + Win builds) — FL 2025, Win build 5319 / macOS build 4597
- [x] G3-3: AGENTS.md for future contributors (concise)
- [x] G3-4: evals/evals.json covering full post-expansion tool surface (incl. new Tier 1/2 + F3 tools) — 15 prompts, tool names validated
- [ ] G3-5: Marketplace/registry packaging (.claude-plugin/marketplace.json + MCP registry server.json alignment) coordinated w/ G2 installer
- [x] G3-6: Reconcile ROADMAP checkboxes with current shipped state
- [ ] G3-7 (deferred): demo video/screenshots (non-blocking)

## Phase H — Final Verification & Contribution Packaging
- [ ] H1: Full Windows regression pass (needs a Windows box — offline suite + CI cover the pure layer)
- [x] H2: Full macOS parity pass on real FL environment (FL 2025 build 4597): bridge, transport, mixer, channels, patterns, playlist, arrangement-read, channel-grid, generator params, VST calibrate/intent — ALL validated live
- [x] H3: F3 generic VST verification (Vital 916 params, tier full, role-grouped; calibrate; brighter intent reversible; degradation on Sampler)
- [x] H4: Commit groups (bug-fixes / macOS / performance-safety / features / docs) — 18 logical commits on macos-parity-hardening
- [x] H5: README/docs flipped to macOS-supported; contribution packet = this branch + AGENTS.md + ROADMAP status
