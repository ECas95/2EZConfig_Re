# Architecture and data flow

This document describes the code currently integrated into the fork, including settings recovery and the new CI/release workflows.

## Component map

| Module | Responsibility |
| --- | --- |
| `src/2ezconfig-exe/main.cpp` | ImGui/GLFW configuration UI, game selection, bindings views, patch resource extraction, launch control and user-facing settings warnings |
| `src/2ez-dll/dll.cpp` | In-game module initialization, game-family IO hooking, patch timing, DirectDraw/audio hooks |
| `src/libs/input/` | HID/keyboard/mouse enumeration, capture, input state and outputs |
| `src/libs/extension_events/` | Optional local JSONL event spool and schema validation (no network calls) |
| `tools/companion_server.py` | Modern-host prototype: local scores, unverified leaderboards, event viewer and in-memory lobby coordination |
| `tools/event_bridge.py` | Dry-run-first explicit JSONL-to-companion event relay |
| `tools/songpack_validator.py` | Offline structural validation of rights-cleared song pack manifests |
| `tools/cabinet_profiles.py` | Export/diff/apply for existing JSON configurations; no GUI selector |
| `src/libs/bindings/` | Binding models and JSON serialization |
| `src/libs/settings/settings.cpp` | `SettingsManager` facade, game/global state and recovery warnings |
| `src/libs/settings/settings_io.cpp` | JSON object parsing, atomic-style save, `.bak` snapshot, preservation of damaged files |
| `src/libs/patches/` | Built-in/custom patch parsing, selection state and process memory writes |
| `src/libs/injector/` | Launching the game and loading DLLs |
| `src/2ez-dll/ez2dj-io/`, `ez2dancer-io/`, `sabin-io/` | Game-specific IO handlers |
| `src/2ez-dll/ddraw/`, `audio-eq/` | Display and audio compatibility logic |
| `src/common/include/` | Game metadata and executable-hash identification |
| `src/resources/patches.json` | Embedded patch definition data |
| `tests/settings_io_test.cpp` | Settings persistence/recovery regression tests |
| `tests/extension_events_test.cpp` | JSONL event validation/disabled behavior regression checks |
| `tools/tests/` | HTTP, song-pack, lobby and profile Python unit tests |
| `.github/workflows/ci.yml` | PR validation, build and tests |
| `.github/workflows/release.yml` | Controlled version-tag releases |

## Startup and settings data flow

1. The configurator locates `%APPDATA%\2ezconfig` and copies a newer embedded `patches.json` if needed.
2. `SettingsManager` loads game-local and roaming/global JSON objects through `settings_io.cpp`. Invalid main files are preserved as `.corrupt`; recovery uses the last valid `.bak` or defaults.
3. Executables in the working directory are checked against known MD5 signatures, with manual game/version selection possible.
4. The UI displays settings recovery/save warnings, and the user configures controls, lights, audio/graphics settings and patches.
5. Launch creates a game process with the companion DLL. 6th Trax has additional launcher/child-process handling.
6. The DLL loads game/global settings, configures game-family hooks and applies enabled patch phases.

The patch pipeline remains distinct:
`src/resources/patches.json` (bundled in EXE) -> `%APPDATA%\2ezconfig\patches.json` + game-local `user-patches.json` + selected state from `game-settings.json` -> DLL patch execution.

## Extension event data flow

With **extension_events_enabled** explicitly selected, the injected DLL emits a low-frequency **runtime.ready** JSONL record after the initialization thread applies normal patches. A trusted game-specific DLL may call the exported **EZ2_PublishEvent** function when it has a verified song/result event. Those events are appended locally to **2ez-events.jsonl**, never transmitted by the injected DLL. An operator may explicitly run **tools/event_bridge.py --send** on a modern host to send selected records to the companion's event viewer.

The companion separately supports manual **/api/v1/scores** submissions and an in-memory lobby state machine; neither is connected automatically to actual in-game results. The full contract and per-game adapter roadmap are in [EXTENSION_EVENTS.md](EXTENSION_EVENTS.md) and [NEW_HOOKS.md](NEW_HOOKS.md).

## Design constraints and known debt

- Some substantial initialization occurs within `DllMain`, which requires loader-lock caution.
- The frontend has a large monolithic `main.cpp`, limiting isolated UI tests.
- MD5 identifies known executable variants; it does not securely authenticate software.
- Patch memory writes need stricter address/length and expected-byte checks.
- Settings recovery does not serialize concurrent global settings writers.
- This is an XP-targeted 32-bit build; Windows CI success does not prove XP/arcade compatibility.

See the [roadmap](ROADMAP.md), [build guide](BUILDING.md) and [patch format](patches/README.md).