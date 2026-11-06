# Technical audit and modernization roadmap

Last reviewed: **2026-11-05**. The findings below are from source inspection plus the automated Windows CI results. They are not a full arcade-hardware or Windows XP SP3 validation report.

## Current priority: modern compatibility and scoring

**Decision (November 2026):** 2EZConfig_Re is a compatibility and player-services platform. The user-provided Final:EX research informs feasibility, but adding songs or AutoChart is not the product's main goal.

| Priority | Deliverable | Status |
| --- | --- | --- |
| P0 | Read-only Compatibility Doctor for modern Windows and legacy 32-bit files | Implemented, hardware unverified |
| P0 | Reliable local scores, personal bests and pseudonymous stats | Implemented, all scores unverified |
| P1 | Verified Windows 10/11/XP compatibility profiles, display and audio diagnostics | Planned |
| P1 | Result-finalized observation for exact tested game build | Planned |
| P1 | Authenticated global rankings with chart rules, anti-replay and privacy controls | Planned |
| P2 | Player progression, rivals, achievements and score seasons | Planned |
| P2 | Offline-friendly cross-cabinet score challenges | Prototype rooms only |

The arcade must run without an internet connection. The modern PC companion can support network services in future, but the current local score server is not a public ranked service.

Read [Modernization Strategy](MODERNIZATION_STRATEGY.md), [Compatibility Doctor](COMPATIBILITY_DOCTOR.md) and [Global Rankings](GLOBAL_RANKINGS.md) before planning new features.

## Integrated foundation

| Item | Implementation | Status |
| --- | --- | --- |
| Windows build + PR CI | Toolchain directory creation, SHA-256 verification, pinned libraries, JSON validation and Windows artifacts ([PR #2](https://github.com/ECas95/2EZConfig_Re/pull/2)) | **Merged; CI passed** |
| JSON settings protection | Temporary file replacement, `.bak` backup, `.corrupt` recovery, warning display and CTest cases ([PR #3](https://github.com/ECas95/2EZConfig_Re/pull/3)) | **Merged; CI passed** |
| Controlled releases | Publish only on version tags; distribute license notices and SHA-256 checksums ([PR #4](https://github.com/ECas95/2EZConfig_Re/pull/4)) | **Merged; release packaging not yet proven by a tagged test release** |
| Documentation | English + Spanish README, architecture, installation, build, troubleshooting, patch reference and contribution guide ([PR #1](https://github.com/ECas95/2EZConfig_Re/pull/1)) | Documented |

## Extensions platform v1 (implemented prototype)

| Area | Implemented now | Still required for real game support |
| --- | --- | --- |
| Hardware diagnostics | Live, read-only HID button/axis tab | Original arcade board protocol adapters and reconnect tests |
| Event hooks | Opt-in 2EZ.dll C ABI, runtime.ready event and local JSONL file | Verified per-game song-selected/result-finalized adapters |
| Custom songs | Rights-cleared pack manifest validation with safe path and optional SHA-256 checks | Catalog, resource and chart loader by exact executable version |
| Scores | Local SQLite HTTP API, unverified submissions/leaderboards and last-100-event viewer | Authentic result capture, account auth, deduplication, anti-cheat, HTTPS hosting |
| Multiplayer | Prototype lobby join, ready, start and finish states | In-game session coordination, player identity and real synchronization |
| Profiles | Offline export/diff/explicit apply with backups | GUI manager, controller remapping, transactional multi-file restore |
| Community | Security policy, changelog, issue/PR templates, developer tests and case-study docs | Compatibility reports from real XP cabinets and tested game builds |

**Integrated in:** [PR #5](https://github.com/ECas95/2EZConfig_Re/pull/5). This is an opt-in extension platform milestone; gameplay hooks beyond runtime.ready remain proposed. The companion is for a modern Python 3.10+ host, not the Windows XP game process.

**Use-case guides:** [new hooks](NEW_HOOKS.md), [event SDK](EXTENSION_EVENTS.md), [custom songs](CUSTOM_SONGS.md), [score API](SCORES_API.md), [multiplayer](MULTIPLAYER.md), [cabinet profiles](CABINET_PROFILES.md) and [developer verification](DEVELOPER_GUIDE.md).

## Final:EX reverse-engineering research interoperability

**Research-level tools (this milestone):** a privately supplied FNEX decompilation archive has been analyzed without incorporating proprietary or reconstructed game source into this public fork. We added independent read-only tools for **GDS lane/order mapping**, a standalone **SVG lane visualizer**, privacy-conscious **5-/99-slot legacy ranking inspection**, and **exact on-disk executable SHA-256 adapter preflight**, plus synthetic tests and documentation.

These improve preservation research and enable data-driven hook design, but **no executable-specific runtime song/result hook has been validated on real Final:EX hardware**.

| Priority | Next deliverable | Acceptance criteria |
| --- | --- | --- |
| F0 | Test GDS/ranking readers against operator-owned Final:EX files | Observed lane order and scores match the game's UI; no writes made |
| F1 | Passive song-selected hook for one exact build | SHA-256 + memory guards verified; one event after confirmation; unsupported builds rejected |
| F2 | Passive result-finalized hook | Final score with correct player/mode/song/chart identity; duplicate-safe local event |
| F3 | Original-song pack loader for one build | One licensed track plays accurately and leaves original content unaffected; safe uninstall |
| F4 | Input-edge timing comparison | Read-only trace, explicit musical units and hardware evidence before any latency change |
| F5 | Two-cabinet asynchronous match | Authenticated session, matching chart hash, idempotent final scores and offline fallback |

Supporting guides: [FNEX research overview](fnex/README.md), [source crosswalk](fnex/SOURCE_MAP.md), [mode/ranking formats](fnex/FORMATS.md), [hook design](fnex/HOOK_DESIGN.md), [compatibility levels](fnex/COMPATIBILITY.md) and [integration plan](fnex/INTEGRATION_PLAN.md).

## Final:EX Passive Observatory (F0.5)

**Implemented:** multi-mode GDS inventory, isolated synthetic event lifecycle validation (song preview/confirmed, stage, finalized P1/P2 scores, end), a privacy-redacted historical ranking snapshot comparison and offline CI tests. [Operator guide](fnex/PASSIVE_OBSERVATORY.md).

**Not implemented:** live reading of a Final:EX executable, trusted song-selected or score-finalized detours, score authentication, direct custom-song loading, server-based ranked competition or synchronized multiplayer. F1/F2 still require exact executable and runtime memory validation on authorized hardware.

## External EZ2CustomMod interoperability (new foundation)

**Implemented in this fork:** Final:EX contextual Extra DLL warnings; read-only game executable/Extra DLL/dependency preflight; optional mode/category/song BMSData checker with bounded resource-reference checks; and aggregated, privacy-redacted EZ2CustomMod log diagnostics. [Guide](fnex/CUSTOMMOD_INTEROP.md) and [source audit](fnex/CUSTOMMOD_SOURCE_AUDIT.md).

**New evidence:** user-supplied private mod source documents a separate, already-existing Final:EX custom BMS loader with AutoChart and extensive regression tests. We should **interoperate with it**, not duplicate its unreleased/private game hook implementation in this fork.

**Still required:** independently verified, authorized EZ2CustomMod DLL build and exact retail FNEX executable compatibility; physical XP regression; two-DLL hook overlap analysis; and optional mod-maintained event publishing to our companion. No source/license rights are assumed.

## P0 — Remaining runtime safety work

| ID | Evidence | Proposed change | Acceptance criteria |
| --- | --- | --- | --- |
| P0-01 | `src/libs/patches/patch_store.cpp` writes raw process memory without checking memory bounds or the result of `VirtualProtect` | Add preflight target/length checking, expected-original-byte guards, explicit error codes and guarded writes | Invalid, ambiguous or unsafe patch targets are rejected without memory modification |
| P0-03 | `src/libs/injector/injector.cpp` has resource cleanup/error handling gaps | Audit process/remote allocation/thread handles, timeouts, exit codes and error propagation | Launch failures report concrete diagnostics and cleanup is verified |
| P0-04 | `src/2ez-dll/dll.cpp` initializes complex systems from DLL attach | Minimize loader-lock-sensitive initialization while preserving early game timing | Startup remains stable across selected game/OS matrix |
| P0-05 | Settings can be shared across multiple instances; no inter-process transaction coordination | Add multi-instance writer serialization and a recovery-friendly conflict policy | Concurrent saves do not silently overwrite newer settings |

**Notes on completed P0-02:** atomic-style saves, one last-good backup and corruption recovery are present. Full schema migrations, rolling history and a dedicated recovery manager UI are **not implemented**.

## P1 — Maintenance and test coverage

| ID | Proposed change | Acceptance criteria |
| --- | --- | --- |
| P1-01 | Support fully offline and externally supplied toolchains; add multi-target build reproducibility checks | Documented offline build succeeds without network access |
| P1-04 | Extract `src/2ezconfig-exe/main.cpp` into separate UI modules | Same behavior with isolated screen/config tests |
| P1-05 | Expand initial CTest/Python suite with patch-schema validation, game ID detection, HID integration and Windows XP SP3 smoke testing | Tests pass for malformed inputs and expected hardware behaviors |
| P1-06 | Make unknown executable hashes explicit instead of silently selecting the first entry | Unknown game displayed as unrecognized until manual choice |
| P1-07 | Verify the version-tag release workflow on a test tag; assess binary signing | Test release has complete ZIP, licenses and checksums |

## P2 — Proposed user-facing capabilities (not implemented)

| Feature | Proposal |
| --- | --- |
| **Cabinet Profile Manager** | Named setups per game/cabinet with import/export, comparison and one-click restore |
| **Device Diagnostics Lab** | Live HID buttons/axes, turntable direction graphs, output lighting tests, device reconnect alerts |
| **Visual IO Mapper** | Interactive button, turntable, pedal and lamp diagrams for EZ2DJ/AC, EZ2Dancer and Sabin |
| **Patch Compatibility Inspector** | Patch preview, executable fingerprint checks, expected-byte guards, overlapping write detection |
| **Guided Setup Wizard** | Distinct recommended paths for legacy CRT cabinets and supported modern Windows |
| **Settings Health Center** | Versioned history, migrations, health warnings and privacy-safe support bundles |
| **Display / Audio Inspector** | Actual refresh/driver reporting, sound backend and latency diagnostics |
| **Localization and accessibility** | Adjustable UI scale, English/Spanish application UI and tested keyboard navigation |

**Priority order:** patch-write preflight safety → injector lifecycle hardening → executable recognition and more tests → Device Diagnostics Lab → Cabinet Profile Manager → remaining UI modules.

## Compatibility verification matrix

Track **pass / fail / not tested** for Windows XP SP3 32-bit and current Windows; EZ2DJ/EZ2AC, EZ2Dancer and Sabin; known and modified game executables; keyboard, HID, mouse axes, original IO, CRT display modes, WASAPI on Vista+ only, first run and upgrades, and 6th Trax child-process behavior.

A successful CI build is **not** evidence of validated hardware compatibility. Each roadmap change should include focused tests, captured reproducible results and relevant licensing/attribution preservation.
