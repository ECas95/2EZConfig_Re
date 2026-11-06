# Final:EX integration plan — from read-only evidence to supported hooks

**Goal:** responsibly extend 2EZConfig_Re to support authorized Final:EX custom content, score observation, diagnostics and eventually cross-cabinet competitive play, without substituting unverified addresses from a private decompilation.

## Milestone F0 — foundation and operator tooling (this PR)

- [x] Inspect research package without redistributing reconstructed game code or assets.
- [x] Record the source limitations and separate on-disk executable fingerprints from unpacked images.
- [x] Add read-only GDS mapping inspector with synthetic tests.
- [x] Add read-only local ranking inspector with privacy redaction by default.
- [x] Add an exact-SHA-256 adapter registry preflight and fake demonstration registry.
- [x] Document likely game seams, event payloads, score safety and remaining blockers.
- [ ] Run the tools against authorized, real user-owned Final:EX files and compare with cabinet observations.

**Acceptance:** all synthetic tests pass; no game file changes, game downloads or network requests; unknown executable revisions remain unmatched.

## Milestone F1 — passive Final:EX song catalog observer

User-facing target: after a song is *confirmed* in a supported Final:EX build, a single song.selected event can be emitted through the existing opt-in local JSONL SDK.

Development checklist:
1. Obtain a private, authorized exact executable SHA-256 and memory verification evidence.
2. Name the exact song-selection state transition and valid song/chart ID source.
3. Build a **passive observer** with guarded signatures, no catalog mutation and no file writes.
4. Test disabled/mismatch behavior and one event per confirmed selection.
5. Confirm hidden songs, mode changes and restart do not generate bogus events.
6. Publish only an independently reviewed adapter implementation and non-proprietary fixtures.

**Not yet implemented.** The private RE includes candidate source areas but they are not verified hook targets for all versions.

## Milestone F2 — trustworthy result event

User-facing target: emit one score.observed event when a genuine Final:EX score has finalized; allow offline caching and explicit relay to a modern companion host.

Development checklist:
1. Locate the final scoring state in an exact supported game build.
2. Distinguish player slot, game mode, song ID, chart ID, modifiers, clear/grade and final score.
3. Match result-phase transitions and confirm no event is sent from intermediate frame counters.
4. Confirm holds, scratches, two-player sessions, catch and course modes behave as expected.
5. Add a unique local play/event ID and durable replay guard to the companion (not yet present).
6. Only then consider converting unverified score.observed events into leaderboard submissions.

**Not yet implemented.** The current ranking inspector is read-only and does not certify play legitimacy.

## Milestone F3 — custom-song loader (one game build first)

User-facing target: install and play **one self-authored test song** with a known chart, audio, art and safe rollback.

Prerequisites:
- Per-mode GDS lane order and chart format agreement.
- Song table/Stage.ini catalog rules documented for the exact game build.
- Noncolliding IDs, difficulty options, chart/song resource ownership and score-key mapping.
- Licensed assets, safe path resolving and a controlled interface that returns original behavior on unknown resources.

Implementation should be staged: catalog-only preview → chart parsing/validation → one-song loader → audio and graphics → score persistence → removal/rollback. Do not write a universal "copy audio into sound folder" feature that assumes every title interprets resources identically.

**Not yet implemented.** The existing generic pack validator validates metadata, not gameplay.

## Milestone F4 — diagnostics and measured timing

The current configurator has read-only HID diagnostics. A dedicated Final:EX IO/timing lab can add:
- Operator-approved read-only mode and track labels from GDS files.
- Measured raw HID edge timestamps versus final judgement outcomes.
- Clear unit tags for musical ticks, beats, measures and milliseconds.
- Offline trace export with no player personal data or copyrighted notes/audio.

Do not change judgement windows or hook the audio thread before hardware validation. The research mentions timing compensation but also has terminology differences between documents; a direct hardcoded compensation patch could worsen fairness.

**Partially available:** existing HID tab and GDS CLI; no Final:EX timing hook.

## Milestone F5 — score challenges and multiplayer

- Start with the local companion's existing lobby state and independent plays.
- Match title revision, song/chart fingerprints and scoring rules.
- Require legitimate final results and eventual identity/authentication.
- Add reliable offline queue, deduplication, timeout and reconnect behavior.
- Only explore live synchronized play after measuring clock drift and latency.

**No in-game multiplayer networking is currently implemented.**

## Milestone F6 — wider support and release readiness

- Expand per-executable compatibility matrix without claiming all Final:EX variants.
- Test Windows XP SP3, original IO and modern USB/HID mappings.
- Validate graphics, sound, 60 Hz mode, crash handling, invalid data and device reconnect.
- Document reproducible release test evidence; verify license attribution and privacy boundaries.
- Prefer an explicit opt-in experimental setting for each hook with rollback.

## Technical decision records

1. **Avoid direct decomp imports.** Independent tools and behavior-level notes are sufficient until code-rights review.
2. **Read-only before detour.** GDS/rank inspection first, memory hooks only after exact-build verification.
3. **No network in game DLL.** Keep existing event file → explicit bridge → modern companion design.
4. **One exact build before generalization.** No shared magic addresses across EZ2AC Final and Final:EX, or across updates.
5. **Keep local and online scoring separate.** A ranking file does not authenticate a completed game play.

## Where to contribute

Issues: use the feature/bug templates and link synthetic fixtures, test matrix results or sanitized observations. Never upload copyrighted game binaries or protected assets.

Relevant docs: [overview](README.md), [formats](FORMATS.md), [hooks](HOOK_DESIGN.md), [compatibility](COMPATIBILITY.md), [parent roadmap](../ROADMAP.md).
