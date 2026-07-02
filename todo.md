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
- [ ] C5: Capability introspection endpoint/resource (what is automated vs manual per OS)
- [ ] C6: Complete macOS installer flow (seeding, IAC checks, remediation, daemon guidance)

## Phase D — Performance, Safety, Efficiency Hardening
- [ ] D1: Command-class timeouts (fast read / heavy analysis / write)
- [ ] D2: Bounded retries only for safe/idempotent calls
- [ ] D3: Structured timing telemetry for bridge/tool latency
- [ ] D4: Deterministic error codes/messages (port missing, stale heartbeat, focus fail, daemon unreachable)
- [ ] D5: Re-verify snapshot→write→readback→rollback invariants for all write tools

## Phase E — Deep Research + Benchmarks (parallel with B/C/D)
- [ ] E1: macOS automation options risk matrix (AppleScript / AX / event injection)
- [ ] E2: MIDI transport robustness + recovery across IAC/loopMIDI/python-rtmidi/mido
- [ ] E3: Missing-functionality feasibility scan within FL API limits
- [ ] E4: Benchmarks — p50/p95/p99 latency for read/write tools
- [ ] E5: Benchmarks — burst throughput
- [ ] E6: Benchmarks — FL restart + MIDI port disruption recovery timing
- [ ] E7: Convert findings into accepted/rejected design decisions with rationale

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
- [ ] F-T1a: Unblock generator (slot=-1) addressing in plugin tools
- [ ] F-T1b: Playlist track tools (mute/solo/rename/color/select) — thin handlers + MCP tools + rollback
- [ ] F-T1c: Arrangement read tools (current time, selection range, marker list) — read-only
### Tier 2 (proven-API, moderate)
- [ ] F-T2a: Channel step-sequencer grid tools (get grid / set step / clear grid) — new controller handlers + protocol cmds
- [ ] F-T2b: Pattern management completion (select / rename / get-length handlers + tools)
- [ ] F-T2c: Extend VST comp/EQ intent coverage (reuse calibrate→intent; DO NOT re-implement base comp intent — already exists)
### Cross-cutting
- [ ] F-X1: Keep controller thin; judgement server-side
- [ ] F-X2: Paginate responses >~500B (SysEx ~1.5KB ceiling)
- [ ] F-X3: All state-changing tools rollback-safe

## Phase F3 — Generic Deep VST/AU Control Layer (headline vision)
### Layer 0 — Enumeration & discovery
- [ ] F3-0a: Fix macOS FL plugin-DB discovery (verify path; add to find_plugin_db + env override)
- [ ] F3-0b: Enumerate actually-installed plugins on the machine; identify ambiguous names (love/hate/tekno/audija kickdrum)
- [ ] F3-0c: Ensure generator addressing (slot=-1) works end-to-end (ties to F-T1a)
### Layer 1 — Generic parameter interface
- [ ] F3-1a: Full param dump w/ name+value+display string — extend to generators + large sets
- [ ] F3-1b: Param search/filter by name substring
- [ ] F3-1c: Batch set (multiple params as one rollback unit)
- [ ] F3-1d: Value-string-aware set (return display string for LLM iteration toward unit target)
### Layer 2 — Curated semantic maps
- [ ] F3-2a: Auto-group params by role (osc/filter/env/LFO/macros/master) via prefix heuristics
- [ ] F3-2b: Hand-authored curated maps for popular installed synths (Vital, Zebralette, Serum, ...) as pure data modules
### Layer 3 — Runtime calibration
- [ ] F3-3a: Runtime sweep tool (sweep param 0..1, parse value strings, build norm↔unit table)
- [ ] F3-3b: Safety — snapshot param first, restore after sweep
- [ ] F3-3c: Cache maps w/ re-validation on connect (dedupe 30-char name truncation collisions)
- [ ] F3-3d: PERSIST calibration cache to disk (~/.flstudio-mcp/) keyed by signature (plugin name + param count + sample name/index pairs); re-validate on connect, re-sweep on mismatch; in-memory layer on top
### Layer 4 — Generic semantic intents
- [ ] F3-4a: High-level moves (brighter/warmer/more attack/wider/resonance/release) mapped to calibrated params via role detection
- [ ] F3-4b: Reuse calibrate→interp→intent; degrade to raw normalized when not calibratable
### Degradation
- [ ] F3-5: 3-tier degradation surfaced to LLM (full names+strings / normalized+range / opaque Param N + warning); flag macro/NKS-walled params

## Phase G — Docs, Packaging, Finalization (Windows-first until final)
- [ ] G1: Keep README Windows-first during hardening
- [ ] G2doc: In-progress macOS setup/validation doc; merge into README after parity checklist passes
- [ ] G3doc: Update contributing + installer docs with cross-platform troubleshooting trees
- [ ] G4: Adjust packaging metadata/deps (true platform support; optional platform extras; make pygetwindow optional)

## Phase G2 — One-Command Installer + MCP Client Auto-Registration (macOS-first)
- [ ] G2-1: Single entry-point installer (deps, controller deploy, piano-roll seed, port verify+remediation, daemon guidance, client registration)
- [ ] G2-2: MCP client detection (Claude Desktop, Claude Code, Cursor, VS Code, Windsurf, Cline, Zed, Continue, ...)
- [ ] G2-3: CLI selection UX (auto-all / interactive multi-select / --clients flag; --dry-run; --list-detected)
- [ ] G2-4: Safe idempotent config merge (create-if-missing, timestamped backup, insert-if-absent, JSON validate, --restore)
- [ ] G2-5: Per-client schema handling (mcpServers vs VS Code "servers" vs Zed "context_servers")
- [ ] G2-6: Registration payload (fl-studio-mcp stdio, FLSTUDIO_MCP_TRANSPORT=tcp default) consistent w/ server.json
- [ ] G2-7: VERIFY exact config paths/keys against official docs (research draft had inaccuracies) — one table module + self-test
- [ ] G2-8: For non-standard clients, print copy-paste JSON + path instead of blind write
- [ ] G2-9: Uninstall/deregister path using same idempotent+backup logic

## Phase G3 — ROADMAP Integration
- [ ] G3-1: Fold GitHub Actions (lint + mock-FL tests) into F2 CI (single source of truth)
- [ ] G3-2: Pin known-working FL version range in README (tested mac + Win builds)
- [ ] G3-3: AGENTS.md for future contributors (concise)
- [ ] G3-4: evals/evals.json covering full post-expansion tool surface (incl. new Tier 1/2 + F3 tools)
- [ ] G3-5: Marketplace/registry packaging (.claude-plugin/marketplace.json + MCP registry server.json alignment) coordinated w/ G2 installer
- [ ] G3-6: Reconcile ROADMAP checkboxes with current shipped state
- [ ] G3-7 (deferred): demo video/screenshots (non-blocking)

## Phase H — Final Verification & Contribution Packaging
- [ ] H1: Full Windows regression pass
- [ ] H2: Full macOS parity pass on real FL environment
- [ ] H3: F3 generic VST verification (enumerate; test Vital/Zebralette/Serum/a FabFilter/a native; search; batch rollback; calibration round-trip; semantic intent on 2 synths; opaque degradation)
- [ ] H4: Produce commit groups (bug-fixes / macOS / performance-safety / features / docs-research)
- [ ] H5: Contribution packet (validated checklist, benchmark summary, risk register, PR split strategy)
