# Architecture and data flow

This guide describes the **existing code**, not proposed functionality.

## Module map

| Module | Primary responsibility |
| --- | --- |
| `src/2ezconfig-exe/main.cpp` | ImGui/GLFW configuration UI, detection, embedded patch extraction, launch orchestration |
| `src/2ez-dll/dll.cpp` | Game-side initialization, patch timing, IO/audio/DirectDraw hooks |
| `src/libs/input/` | HID, keyboard, mouse capture, device polling and outputs |
| `src/libs/bindings/` | Input and output binding models, serialization |
| `src/libs/settings/` | Per-game and global JSON persistence |
| `src/libs/patches/` | Bundled/user patch parsing, state and memory patch execution |
| `src/libs/injector/` | Game process launch and companion DLL loading |
| `src/2ez-dll/ez2dj-io/`, `ez2dancer-io/`, `sabin-io/` | Game-family IO handlers |
| `src/2ez-dll/ddraw/`, `audio-eq/` | Rendering and audio compatibility features |
| `src/common/include/` | Game IDs and executable MD5 identification |
| `src/resources/patches.json` | Patch library embedded in the executable |

## Startup sequence
1. Configurator locates `%APPDATA%\2ezconfig`, writes a newer embedded patch bundle if applicable, and loads JSON settings.
2. The configurator attempts MD5-based executable recognition from the working directory; the user can manually choose game/version.
3. A launch starts the game with the companion DLL. 6th Trax / Remember 1st also monitors child processes.
4. The injected DLL loads game/global settings, chooses a game-family handler and initializes the selected compatibility components.
5. Patches run in `super_early`, `early`, or default phases, according to their definitions and selected state.

## Settings and patch flow

~~~text
src/resources/patches.json
    -> bundled in configurator
    -> %APPDATA%/2ezconfig/patches.json
       + game-folder/user-patches.json (overrides by game ID and patch ID)
       + game-folder/game-settings.json (enabled/state)
    -> DLL patch store -> memory patch execution
~~~

Button/analog/light bindings and other global settings live in `%APPDATA%\2ezconfig\global-settings.json`.

## Constraints observed during review
- The frontend remains largely monolithic in `main.cpp`, making independent UI testing difficult.
- `DllMain` initiates heavyweight setup; loader-lock correctness and XP compatibility require careful refactoring.
- MD5 detects *known builds* but is not a secure verification primitive.
- JSON files are saved directly to their final paths without atomic replacement or backup recovery.
- Patch writes operate on raw process memory. A safe validation/preview layer should be separated from execution.

## Suggested future modularization (not implemented)
Extract platform-independent configuration/schema and patch-validation logic first. Define narrower device and game-family interfaces. Keep operating-system-specific process and graphics/audio hooks in tested adapters. Then split GUI areas into independently maintained modules and add unit/integration tests.

See [Roadmap](ROADMAP.md).