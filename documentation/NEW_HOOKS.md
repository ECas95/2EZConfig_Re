# New hooks: investigation guide and proposed extension points

This document proposes **game-specific hook development** without inventing unsupported memory offsets, undocumented proprietary file layouts or claiming feature parity across EZ2DJ, EZ2AC, EZ2Dancer and Sabin Sound Star.

## Current hook inventory

Existing source already hooks/enhances:
- Legacy arcade IO using exception handlers for privileged input/output instructions and per-family binding translation.
- Select DirectDraw interfaces, display modes and texture settings.
- Audio mixer/EQ paths and optional WASAPI/Hypersonik integration.
- Memory patch phases (super early, early, normal) and selected license/hardlock compatibility paths.
- Process launch with injection of the companion DLL and optional explicitly configured extra DLLs.

**No universal song loader, result-screen score extractor or network multiplayer hook currently exists.** Existing IO hooks do not imply gameplay object layouts are known.

## Build-aware hook registry (proposed)

A future adapter registry should map exact executable SHA-256 to a verified adapter package, not just a game family:

| Field | Required? | Purpose |
| --- | --- | --- |
| game_id | yes | Existing game_defs.h ID |
| exe_sha256 | yes | Exact supported executable revision; MD5 legacy lookup is not a security fingerprint |
| adapter_id and version | yes | Identify maintainers and provide migration path |
| architecture | yes | x86 only, plus calling convention requirements |
| supported_events | yes | Song selection, result finalized, chart loaded or session ended |
| signatures/guards | yes | Verified code pattern and expected bytes; ambiguous targets rejected |
| offsets/revisions | per adapter | Carefully tested, never silently reused across builds |
| tested_os | yes | Real XP SP3/modern Windows results |
| validation_status | yes | experimental, observed, tested, incompatible |

Planned decision flow: hash executable → identify exact adapter → preflight patterns and original bytes → validate hook target → enable selected event callbacks → fail open if anything differs. Do not reuse a hook signature simply because another title shares a filename.

## Use case A: custom songs (research phase)

**Goal:** expose original, freely distributable or permission-cleared content in the song list.

1. Inventory **catalog enumeration**, song ID allocation, metadata reads, audio resource opening, jacket/BGA loading, chart decoding, score IDs and result-screen references for one game revision.
2. Validate a [song pack manifest](CUSTOM_SONGS.md), including safe relative paths, title/artist, chart modes and checksums.
3. Make a *read-only* discovery adapter that reports catalog entries. Confirm where song IDs are created and when lists are refreshed.
4. Add an isolated content registry that maps stable custom IDs into unused supported IDs without overwriting built-in entries or collisions.
5. Integrate assets through game-specific, well-scoped resource hooks with fallback to original loading if no custom resource exists.
6. Maintain chart timing, turntable/foot mappings, music/BGA references, encoding and memory limits for each supported game revision.
7. Report song.selected and chart.loaded through the event SDK, not by injecting network requests into the arcade process.
8. Enforce license and provenance rules; do not include original game assets or commercial music.

**Acceptance:** one fully original test song loads and plays correctly (audio, note timing, visuals and return to UI) on an explicitly supported game build. **This has not yet been implemented.**

## Use case B: online scores and leaderboards

**Goal:** share authorized community scores while retaining offline play.

1. Hook only a verified **result finalized** state, never a live changing score display.
2. Collect game_id, stable song ID, chart ID, score, clear status, optional session nonce and pseudonymous player ID.
3. Pass the event to the local spool. On a modern host, validate the envelope and explicitly forward to the companion.
4. The [local score API](SCORES_API.md) stores and queries unverified entries. Plan signed adapters, identity, replay prevention, quotas and score normalization before running a public competitive service.
5. Queue events durably with acknowledgments in a later phase, so an unavailable network never changes gameplay.

**Acceptance:** a real, version-verified result hook emits one deduplicated event per completed play; known song/chart IDs are enforced and remote outages do not affect the cabinet. **The collector hook and anti-cheat are pending.**

## Use case C: multiplayer

The safest first step is **asynchronous score battles**: two or more cabinets agree on song and chart, play locally, and compare completed results. A basic lobby/ready/start/result coordinator is implemented in the Python companion for **protocol prototyping only**.

Real simultaneous play requires more:
- explicit session ownership, player matching and per-game version compatibility;
- reliable stage start scheduling against monotonic clocks;
- measured clock drift, latency, disconnects and deterministic result settlement;
- clear handling of mismatched song/chart assets and version IDs;
- no raw input replay in the game process without careful security review;
- fair-play and authorization controls if scores are competitive.

**Acceptance:** two cabinets independently play matching, authorized content and report correct results; only after this should live synchronized starts be attempted. Current lobby API does **not** synchronize actual gameplay or inject network state.

## Use case D: cabinet diagnostics and live monitoring

A new **Diagnostics** tab now displays available HID buttons/axis snapshots read-only, while the existing Lights tab performs bounded output tests. Future adapters can identify original arcade IO signals where HID does not apply, with known board protocol evidence and non-destructive probes.

**Acceptance:** devices appear correctly on supported controllers; no exclusive access conflict with game execution; outputs return to zero after tests.

## Research and compatibility artifacts

Each proposed adapter should include:
- a sanitized compatibility report; exact executable hash but no game executable;
- a diagram of the relevant call flow and state transitions;
- sample synthetic events with normal, malformed and edge-case values;
- automated tests and hardware/OS validation table;
- source attribution and licensing; documentation of any game rights restrictions;
- a rollback plan when mismatches or regressions are detected.

Do not upload proprietary binaries or unofficial server credentials. Avoid bypassing external services' authentication or evading anti-cheat systems. The project should support preservation and authorized community play, not secret third-party access.

## Development priorities

1. Implement read-only hooks for **one exact game revision** and verify a song-selected event.
2. Implement a result-finalized hook and wire a real score event to the offline companion.
3. Add stable custom song registry with rights-cleared test assets and a per-game loader.
4. Graduate the lobby prototype to reliable asynchronous tournaments.
5. Investigate synchronized multiplayer only after reproducible, measured latency studies.
