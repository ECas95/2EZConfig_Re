# Changelog

This community fork is based on [ben-rnd/2EZConfig-V2](https://github.com/ben-rnd/2EZConfig-V2). Preserve original authorship and attribution. Entries below document changes developed within this fork.

## Unreleased — Final:EX Passive Observatory

- Added a read-only per-directory GDS mode inventory with warnings about conflicting keys or chart-track mappings.
- Added a deterministic synthetic observation-to-event state machine: song preview never generates a selected song; results are emitted only after a started stage and once per player.
- Added a local, privacy-first numeric ranking snapshot diff, with no player names, file writes or automatic network submission.
- Added a self-authored two-player JSONL fixture, CI smoke coverage and detailed operator instructions.
- Game-specific Final:EX hooks are still **not** implemented. All fixture-generated scores remain synthetic/unverified.

## Unreleased — Final:EX research interoperability

### Added
- Read-only GDS Slot inspector with explicit file-order lane mapping and standalone SVG visualizer.
- Privacy-conscious read-only inspectors for candidate local top-five and top-99 ranking files.
- Exact on-disk executable SHA-256 adapter registry checker; no hook installation and no assumption that an unpacked image hash matches retail files.
- Synthetic fixtures and regression tests for GDS parsing, SVG, ranking schemas and adapter fingerprinting.
- Detailed Final:EX research section with formats, source crosswalk, runtime hook plan, compatibility evidence levels and a phased implementation roadmap.
- English/Spanish README usage and cross-links to the existing custom-song, score, multiplayer and developer guides.

### Limitations
- No protected source, game assets, disassembly or private reference package was imported.
- No verified Final:EX selection/result hook, playable custom-song loader or synchronized multiplayer implementation.
- Real retail game binaries and physical cabinets were not available for this analysis.

## Unreleased — extension platform milestone

### Added
- Live, read-only HID **Diagnostics** tab.
- Disabled-by-default local extension event spool with a documented exported C ABI and runtime.ready event.
- Python 3.10+ companion prototype for local scores, leaderboards, event viewer and match lobbies, including a same-origin local browser dashboard.
- Dry-run-first event bridge; offline cabinet profile export/diff/explicit apply; custom-song manifest validator.
- Integration tests covering Python tools and C++ event JSONL.
- Documentation of proposed per-game song selection, custom chart loader, scores and multiplayer adapters, with explicit limits.
- Community contribution/security/issue templates and a testing plan.

### Limitations
- No game-specific real song injection, score extraction or synchronized multiplayer hook is included.
- Companion scores are unverified and lobby participants are not authenticated.
- XP/hardware, release tags and arcade cabinet operations require manual testing.

## 2026-11-05 — reliability and documentation baseline

- [PR #1](https://github.com/ECas95/2EZConfig_Re/pull/1): English/Spanish README, architecture, installation, build, patch and troubleshooting guides.
- [PR #2](https://github.com/ECas95/2EZConfig_Re/pull/2): clean build improvements, verified toolchain hash, dependency pins and PR CI.
- [PR #3](https://github.com/ECas95/2EZConfig_Re/pull/3): JSON settings recovery, last-good backups and CTest.
- [PR #4](https://github.com/ECas95/2EZConfig_Re/pull/4): version-tag-triggered releases with license notices and checksums.

No release version is asserted by this changelog until a corresponding version tag and tested release asset exist.