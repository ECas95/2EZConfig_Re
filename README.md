# 2EZConfig_Re

Community fork of [2EZConfig V2](https://github.com/ben-rnd/2EZConfig-V2) by ben-rnd, based on the original 2EZConfig project. Original attribution and license notices are retained.

**Status:** This fork is being documented and reviewed. The features below are present in the inherited codebase; they are not newly implemented features of this fork. Windows XP SP3 compatibility is a build target and has not been independently verified in this fork.

## What it does

2EZConfig configures input and output for **EZ2DJ/EZ2AC**, **EZ2Dancer**, and **Sabin Sound Star: Renascence Burst** on Windows. The source provides:
- HID, keyboard, turntable/mouse-axis and lighting configuration (support varies by game).
- Executable-hash-based game detection, with manual version selection.
- Built-in and per-game custom JSON patches; optional DirectDraw/60 Hz fixes.
- Optional WASAPI-based audio features on Windows Vista or newer.
- Launch-time DLL loading and support for the 6th Trax / Remember 1st workflow.

EZ2Dancer pad/hand-sensor lighting remains incomplete. Individual patches and compatibility options are not guaranteed to work with every game build.

## Quick start

1. Obtain a trusted build or [build from source](documentation/BUILDING.md).
2. Back up the game directory and existing settings.
3. Place `2EZConfig.exe` and `2EZ.dll` alongside the game executable.
4. Start the configurator **with the game folder as the working directory**. If detection fails, manually select the game/version and executable override.
5. Configure controls in **Settings**, **Buttons**, **Analogs** (where available), **Lights**, and **Patches**; then select **Play EZ2**.

Settings are stored in `game-settings.json` (working/game directory), `%APPDATA%\2ezconfig\global-settings.json` and `%APPDATA%\2ezconfig\patches.json`. Optional `user-patches.json` belongs in the game directory. The `-skip-config` argument launches without showing the UI.

## Documentation

- [Installation and compatibility](documentation/INSTALLATION.md)
- [Building and releases](documentation/BUILDING.md)
- [Architecture and data flow](documentation/ARCHITECTURE.md)
- [Troubleshooting](documentation/TROUBLESHOOTING.md)
- [Patch format](documentation/patches/README.md)
- [Technical audit and roadmap](documentation/ROADMAP.md)
- [Contributing](CONTRIBUTING.md)

## Build (Windows)

Requires CMake 3.20+, Git, a working MinGW Makefiles environment, network access for FetchContent, and a suitable 7z extractor if needed. The current CMake file downloads an XP-targeted MinGW GCC 12.2 toolchain. **Legacy-build note:** upstream revisions require creating `toolchain/` before first configure. [PR #2](https://github.com/ECas95/2EZConfig_Re/pull/2) adds automatic directory creation, a verified toolchain hash and pinned dependencies.

~~~powershell
New-Item -ItemType Directory -Force toolchain | Out-Null
cmake --preset release
cmake --build --preset release
~~~

Expected outputs: `build/release/bin/2EZConfig.exe` and `build/release/bin/2EZ.dll`. The corrected build has passed Windows GitHub Actions on [PR #2](https://github.com/ECas95/2EZConfig_Re/pull/2); Windows XP hardware remains untested. See [BUILDING.md](documentation/BUILDING.md).

## Safety, upstream and licensing

Runtime patching changes game process memory. Back up configurations, enable patches individually, and only use game/software copies you are permitted to use. Do not expose legacy Windows XP systems directly to untrusted networks.

Original upstream: [ben-rnd/2EZConfig-V2](https://github.com/ben-rnd/2EZConfig-V2). Retain upstream notices and comply with [LICENSE](LICENSE) (GPL-3.0-or-later) and [THIRD_PARTY_LICENSES](THIRD_PARTY_LICENSES) on redistribution. Contributions and issue reports for this fork belong in this repository.