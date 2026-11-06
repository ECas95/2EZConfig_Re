# 2EZConfig_Re modernization: compatibility and player services

**Product direction:** 2EZConfig_Re should make existing authorized EZ2 arcade installations run more consistently, diagnose cabinet configuration and support optional player services. **It is not intended to become another song-pack loader, game engine fork, AutoChart tool or copy of the private Final:EX reverse-engineering project.**

## Evidence from supplied reference material

The user-provided research archives describe several underlying game traits relevant to compatibility and scores:

| Research finding | Implication for 2EZConfig_Re | Evidence limit |
| --- | --- | --- |
| DirectDraw 7 / Direct3D 7 fixed-function renderer | Modern Windows focus, DPI, display refresh, palette/texture and wrapper compatibility must be profiled per build | Source describes one researched Final:EX image, not every series |
| DirectSound voices plus music clock | Distinguish audio output delay from scoring/judgement timing; do not blindly change judgement windows | Requires measured hardware/driver evidence |
| Game frame/input events and audio-worker clock | Input-latency lab must timestamp events and measure against the music clock | No verified general-purpose event hook exists |
| Mode-dependent score/gauge paths | Compare scores only inside a compatible game, chart, ruleset and difficulty | No normalized universal score formula is known |
| Result-finalization and local ranking storage | Publish a completed score only once final state is known; local rank files do not authenticate plays | Source and local ranking layouts require exact-build validation |
| Windows XP 32-bit memory/GDI constraints | Diagnostic profile must retain separate legacy cabinet behavior; don't replace XP DirectSound with Vista+ APIs | CPU/GPU/driver variation remains considerable |

Reference pointers (private, not mirrored): archive docs research/03-engine-architecture.md, 04-file-formats.md, 05-timing-judgement-scoring.md, 08-performance-on-xp.md and original Final:EX RE archive docs/judge-timing.md. Do not import reconstructed private source into this public fork.

## Modern Windows compatibility strategy

### P0 — Read-only, per-installation diagnosis

**Implemented:** tools/compatibility_doctor.py. Inspects PE headers and game configuration, checks x86/PE32 agreement with 2EZ.dll, detects absent or malformed files, and gives warnings for configured WASAPI/refresh options.

~~~powershell
python tools/compatibility_doctor.py --game-dir "D:\Arcade\EZ2" --json
python tools/compatibility_doctor.py --game-dir "D:\Arcade\EZ2" --exe EZ2B.exe
~~~

This runs with Python 3.10+ on a modern helper PC. It does **not** execute games, load DLLs, change settings, access the GPU/audio driver, inspect personal device identifiers, install a wrapper or assert an executable's legal provenance. Its results reflect **static compatibility checks, not verified playability**.

### P1 — Compatibility profiles (future)

Profiles must use the existing per-game and global settings model, with separate **tested combinations**, not blanket presets:

| Area | Existing options / concern | What should be tested |
| --- | --- | --- |
| Windows XP SP3 (32-bit) | Legacy DirectDraw and DirectSound; WASAPI unavailable | Real cabinet and CRT behavior; audio/IO without modern shims |
| Windows 7–11 | DirectDraw/Direct3D7 legacy presentation | Fullscreen/window focus, resolution switching, GDI, texture/resource loss |
| Display | force_60hz; DirectDraw4 options for early games | Correct output refresh and CRT/GPU capability, no unsafe 15 kHz modes |
| High DPI / mixed displays | Old fixed-size UI and game surfaces | 100/125/150/200% OS scaling; per-monitor handling without distorted inputs |
| Audio | DirectSound and existing Hypersonik/WASAPI options | Buffer access, actual offset/latency, device exclusive-mode failure and rollback |
| HID/IO | Existing binding and arcade I/O emulation | Plug/unplug, device enumeration and joystick/button repeat |
| Game revision | MD5 game lookup and additional exact SHA-256 preflight | Explicit game build confidence before applying version-specific patches |

The first implementation should generate a **dry-run diff** for each profile and preserve settings backups. Profiles cannot promise Windows 11, Windows XP or original cabinet compatibility without measurements.

### P2 — Non-invasive visual/audio measurements

Create test scenarios and evidence capture for frame pacing, display mode switches, device focus, controller sampling and audio output. Legacy DirectSound and DirectDraw cannot be made reliable by assuming that contemporary DX10/11 features apply. A new wrapper choice must be optional, versioned, independently licensed and reversible. Never inject unverified remote graphics libraries by default.

External documentation: Microsoft DirectDraw reference; Microsoft Interoperability with Legacy Audio APIs; Microsoft High DPI Desktop Application Development; Microsoft's Windows 11 windowed-game optimizations scope (DX10/DX11, *not* a blanket DirectDraw 7 fix).

## Global scoring strategy

**Already implemented baseline:** a localhost-only by default Python companion with SQLite, local unverified score submissions, leaderboard and optional in-memory events/lobbies.

**This milestone adds:** caller-stable, optional score submission IDs with durable idempotency across restarts; one-personal-best-per-chart leaderboard queries; pseudonymous per-player local stats; synthetic/claimed-verified score rejection at the submission endpoint; tests for concurrent retries. The local browser dashboard exposes these new functions.

**NOT implemented:** real game result capture, ranked public/global service, verified player identities, secure cross-cabinet upload, anti-cheat, automatic replay protection in the game process, GDPR/privacy controls or score normalization across game versions.

### Recommended architecture

~~~text
Authorized arcade game (XP or modern Windows)
       | confirmed final score, game-specific verified adapter (FUTURE)
       v
2EZ.dll local opt-in event journal (existing, low frequency)
       | no internet dependency in game process
       v
Modern companion PC (Python/SQLite)
       | durable queue / batch / idempotent uploads (FUTURE)
       v
HTTPS API + per-cabinet/player auth + anti-replay (FUTURE)
       |
       +-- authoritative chart/game/ruleset registry
       +-- verified score and provenance ledger
       +-- public leaderboard only for validated games/charts
       +-- profiles, personal bests, seasons and rival comparison
~~~

The current event bridge only forwards events to an in-memory viewer and **must not** automatically convert a synthetic or untrusted result observation into a ranked score. The game should be playable fully offline.

### Required data model before "global"

- Exact game ID, executable/version/adapter fingerprint, chart and mode/ruleset identity.
- Stable pseudonymous player ID and a *separate* authenticated cabinet/service identity.
- Unique play result ID; session ID, monotonic completion sequence, timestamp.
- Final score, clear/grade, modifiers, player slot, score scale and supported chart checksum.
- Cryptographically authenticated submission across a TLS server; opt-in, scoped retention.
- Validation status: manual/unverified, adapter-observed, server-validated or rejected. Never allow a client to mark itself verified.
- Explicit song/score interpretation per game version, not ranking unrelated titles on raw numeric scores.

### Progressive roadmap

1. **L0 now:** local score history + idempotent retries + personal-best leaderboard (unverified).
2. **L1:** account/privacy model, authorized cabinet registration, durable event queue with acknowledgments, per-play IDs and explicit source attribution.
3. **L2:** passive *result-finalized* hook for one exact verified executable, using the already documented C ABI and synthetic integration tests.
4. **L3:** authenticated modern companion upload over HTTPS, rate limits, dedupe, server-side score/chart registry and audit.
5. **L4:** public global leaderboard with validated result provenance, separate unverified sandbox, personal records and rivals.
6. **L5:** optional asynchronous tournaments and match challenges, then live features only where validated.

An API that accepts arbitrary numeric scores over the internet is **not a reliable global ranking service**. Do not publish the existing prototype to the open internet.

## Product success criteria

- Compatibility: no unauthorized setting changes, no game launch by diagnostic tools, complete evidence report with actionable risk categories; exact build and hardware validation before claims of broad Windows compatibility.
- Scores: retrying the same submission does not create extra records; every personal best is unique per player+game+song+chart; the leaderboard never labels manual numbers as verified.
- Gameplay: no new network operations in the injected game process and no dependency on internet to play.
- Quality: automated Linux/Python regression suite and unchanged Windows 32-bit build/CTest; XP and arcade hardware remain explicit manual certification tasks.
- Security: private game binaries, credentials, copyrighted assets and decompilation outputs are not uploaded or redistributed.

## Implementation boundaries

The external EZ2CustomMod BMS work stays a separate interoperability track. Its reverse-engineering documentation informs how results and timing are structured; **we will not prioritize copying its song loader or distributing game patches**. See [Global scoring architecture](GLOBAL_RANKINGS.md), [Compatibility Doctor](COMPATIBILITY_DOCTOR.md), [Score API](SCORES_API.md), [Extension Events](EXTENSION_EVENTS.md), and [Technical roadmap](ROADMAP.md).
