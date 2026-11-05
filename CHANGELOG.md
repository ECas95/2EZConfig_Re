# Changelog

This community fork is based on [ben-rnd/2EZConfig-V2](https://github.com/ben-rnd/2EZConfig-V2). Preserve original authorship and attribution. Entries below document changes developed within this fork.

## Unreleased — extension platform milestone

### Added
- Live, read-only HID **Diagnostics** tab.
- Disabled-by-default local extension event spool with a documented exported C ABI and runtime.ready event.
- Python 3.10+ companion prototype for local scores, leaderboards, event viewer and match lobbies.
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