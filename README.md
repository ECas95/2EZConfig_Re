# 2EZConfig_Re

**A community-maintained fork of [2EZConfig V2](https://github.com/ben-rnd/2EZConfig-V2) for legacy EZ2 arcade games on Windows.**

[![Pull Request CI](https://github.com/ECas95/2EZConfig_Re/actions/workflows/ci.yml/badge.svg)](https://github.com/ECas95/2EZConfig_Re/actions/workflows/ci.yml)
[![License: GPL-3.0-or-later](https://img.shields.io/badge/license-GPL--3.0--or--later-blue.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](documentation/INSTALLATION.md)

**English** | [Español](README.es.md)

2EZConfig_Re helps configure input/output devices, launch supported EZ2 games, and apply optional game-specific compatibility patches. The project targets **32-bit Windows XP SP3 and later**, but compatibility depends on the game executable, drivers, controllers and optional patches. **Windows CI builds are passing; physical arcade hardware and XP SP3 have not been independently verified for this fork.**

> [!IMPORTANT]
> This repository contains a configuration/compatibility utility, **not game downloads or game assets**. Use only software and game installations you are authorized to use. This fork preserves the original authors' attribution and license.

## Contents

- [Features](#features)
- [Supported game families](#supported-game-families)
- [Quick start](#quick-start)
- [Configuration files and recovery](#configuration-files-and-recovery)
- [Building from source](#building-from-source)
- [Compatibility and troubleshooting](#compatibility-and-troubleshooting)
- [Development status and roadmap](#development-status-and-roadmap)
- [Project documentation and contributing](#project-documentation-and-contributing)

## Features

| Area | Current capabilities |
| --- | --- |
| **Arcade IO** | HID/keyboard buttons, EZ2DJ/AC turntable input from supported analog/mouse or button-based bindings, and HID output lighting |
| **Game detection** | Automatic identification for known executable MD5 signatures; manual game/version and executable override |
| **Patch engine** | Bundled and custom `user-patches.json` patches, RVA/pattern scans, toggle/value patches and staged application |
| **Compatibility** | Game-dependent DirectDraw settings, optional 60 Hz mode requests and audio fixes |
| **Launch tools** | Companion `2EZ.dll`, optional extra DLLs, a skip-UI option, and a special 6th Trax / Remember 1st launch flow |
| **Configuration safety** | Atomic-style JSON replacement using temporary files, `.bak` last-good backup and `.corrupt` preservation/recovery |
| **Build and quality** | CMake/MinGW 32-bit build, SHA-256-verified compiler archive, pinned dependencies and Windows CI + settings recovery tests |

**Limitations:** EZ2Dancer pad/hand-sensor lighting is not complete. Audio EQ/Hypersonik uses WASAPI and requires Vista or newer. Not every game build supports every patch. Automatic executable detection is a compatibility lookup, **not a cryptographic security guarantee**.

## Supported game families

The game selection table in `src/common/include/game_defs.h` currently includes:

| Family | Entries represented in the source |
| --- | --- |
| **EZ2DJ / EZ2AC** | 1st, Remember 1st, 1st Special Edition, 2nd, 3rd, 4th, Platinum, 6th, 7th (including 1.5/2.0), Codename: Violet, Bonus Edition/A, Azure ExpressioN/IC, Endless Circulation, Evolve, Night Traveller, Time Traveller, Final and Final:EX |
| **EZ2Dancer** | 1st Move, 2nd Move, UK Move, UK Move SE, Super China |
| **Sabin Sound Star** | Renascence Burst |

*Listed* means the source has a game entry; it **does not** mean each Windows version, executable revision or cabinet IO board has been tested. See [installation and compatibility](documentation/INSTALLATION.md).

## Quick start

1. **Back up** your game files and any old `game-settings.json` / shared settings.
2. Obtain `2EZConfig.exe` and `2EZ.dll` from a trusted build, or [compile them yourself](#building-from-source). GitHub Actions CI artifacts are test builds; release packages are created only from version tags.
3. Place **both** files in the game directory, beside the game's executable.
4. Start `2EZConfig.exe` **with that directory as the current working directory**. The configurator looks for `*.exe` and loads game-local settings from `.`.
5. If the game is not recognized, select the correct **Game** family/version and set **Exe Name Override** if necessary.
6. Configure **Settings**, **Buttons**, **Analogs** (EZ2DJ/AC), **Lights** and **Patches** as needed.
7. Press **Play EZ2**. Start with optional patches disabled and enable them individually after confirming that the baseline game works.

To bypass the configuration window after setup, launch `2EZConfig.exe -skip-config` (or configure `skip_ui` in the game JSON). Avoid enabling skip-UI until the game launches successfully.

## Configuration files and recovery

| Location | Contents |
| --- | --- |
| `<game folder>/game-settings.json` | Selected game/version, per-game options and patch state |
| `%APPDATA%\2ezconfig\global-settings.json` | Shared controls/bindings and global options |
| `%APPDATA%\2ezconfig\patches.json` | Embedded patch library, refreshed when its bundled version increases |
| `<game folder>/user-patches.json` *(optional)* | Your custom additions/overrides, organized by game ID |
| `<game folder>/2ez-logs.txt` *(when enabled)* | DLL log output |

Recent reliability changes protect **game and global settings**: when saving over a valid file the previous version is retained as `<file>.bak`; if a settings file cannot be parsed or is not a JSON object, it is preserved as `<file>.corrupt` (or `.corrupt.N`) while a valid backup is restored when available. Otherwise defaults are loaded and the configurator shows a warning.

**Backups are not a full version-history system.** If recovery is triggered, inspect your settings before launching the game. The bundled patch JSON and your custom patch definitions are separate from this settings recovery mechanism.

For examples and cautions, see [creating custom patches](documentation/patches/README.md) and [troubleshooting](documentation/TROUBLESHOOTING.md).

## Building from source

**Windows build host** with CMake **3.20+**, Git, MinGW Makefiles support, network access for dependencies, and optionally 7-Zip on PATH if CMake cannot extract the compiler archive:

```powershell
git clone https://github.com/ECas95/2EZConfig_Re.git
cd 2EZConfig_Re
cmake --preset release
cmake --build --preset release
ctest --test-dir build/release --output-on-failure
```

Expected binaries:

```text
build/release/bin/2EZConfig.exe
build/release/bin/2EZ.dll
```

The configured GCC 12.2 32-bit toolchain is downloaded automatically if absent and checked against its published **SHA-256**. MinHook and usb-hid-usage are pinned to specific commits; GLFW 3.3.10 has a repository-local XP compatibility patch. For debug builds, use the `debug` preset.

Every pull request can run **JSON validation**, a **Windows build**, **CTest settings recovery checks** and **artifact verification** through [GitHub Actions](.github/workflows/ci.yml). Releases are published **only from version tags**, with project/third-party license notices and checksums; see [BUILDING.md](documentation/BUILDING.md).

## Compatibility and troubleshooting

- **Windows XP SP3** is a compilation target, not a hardware-tested compatibility guarantee. Avoid connecting XP-based cabinets to untrusted networks.
- **Modern Windows:** external [DDrawCompat](https://github.com/narzoul/DDrawCompat) may help older DirectDraw games; test it separately from the tool's own DDraw options.
- **Display timing:** a 60 Hz patch requests a mode where available. Verify the actual refresh rate at the display/driver level.
- **Audio:** WASAPI-based options require Windows Vista or later.
- **Legacy paths:** some EZ2 games misread configuration when directory names include a period (`.`); upstream also notes 1st SE on XP may require the `C:` drive.
- **DLLs and patches:** avoid untrusted DLLs, and do not apply patches intended for a different executable revision.
- **Issues:** disable extra DLLs and optional patches first, enable debug logging, then consult [TROUBLESHOOTING.md](documentation/TROUBLESHOOTING.md).

## Development status and roadmap

**Implemented in the fork:** cleaner and verified toolchain provisioning, pinned build dependencies, PR CI, controlled release packaging and non-destructive JSON settings recovery.

**Proposed, not implemented:** stricter patch memory-write validation, process-injection lifecycle hardening, additional device/game compatibility tests, a **Device Diagnostics Lab**, **Cabinet Profile Manager**, **Visual IO Mapper**, and a **Patch Compatibility Inspector**. See the [prioritized roadmap](documentation/ROADMAP.md) for technical evidence and acceptance criteria.

## Project documentation and contributing

| Guide | Description |
| --- | --- |
| [Installation](documentation/INSTALLATION.md) | First run, working directory, limitations and compatibility |
| [Build and releases](documentation/BUILDING.md) | Compiler, dependencies, presets, tests and release workflow |
| [Architecture](documentation/ARCHITECTURE.md) | Frontend, DLL, IO layers, patch engine and data flow |
| [Patch authoring](documentation/patches/README.md) | Game IDs, custom JSON format and patch safety |
| [Troubleshooting](documentation/TROUBLESHOOTING.md) | Input/lighting/audio/video problems and safe recovery |
| [Roadmap](documentation/ROADMAP.md) | Audited risks and proposed improvements |
| [Contributing](CONTRIBUTING.md) | Reproduction details, tests and pull requests |

**Upstream:** [ben-rnd/2EZConfig-V2](https://github.com/ben-rnd/2EZConfig-V2), based on [the original 2EZConfig](https://github.com/ben-rnd/2EZConfig). This fork does not claim authorship of upstream work. Licensing is governed by [GPL-3.0-or-later](LICENSE) and the bundled [third-party notices](THIRD_PARTY_LICENSES). Preserve these when redistributing modified builds.
