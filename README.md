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
- [Cabinet diagnostics and extension tools](#cabinet-diagnostics-and-extension-tools)
- [New hooks: custom songs, score servers and multiplayer](#new-hooks-custom-songs-score-servers-and-multiplayer)
- [Final:EX research and read-only tools](#finalex-research-and-read-only-tools)
- [Final:EX passive observatory](#finalex-passive-observatory)
- [EZ2CustomMod interoperability (external Final:EX song loader)](#ez2custommod-interoperability-external-finalex-song-loader)
- [Display modernization: window modes and 60/120 Hz](#display-modernization-window-modes-and-60120-hz)
- [Configuration files and recovery](#configuration-files-and-recovery)
- [Building from source](#building-from-source)
- [Compatibility and troubleshooting](#compatibility-and-troubleshooting)
- [Development status and roadmap](#development-status-and-roadmap)
- [Project documentation and contributing](#project-documentation-and-contributing)

## Product direction — compatibility and scoring first

The main priority of **2EZConfig_Re** is to make existing EZ2 arcade games more reliable on modern Windows while preserving legacy cabinets, and to offer **opt-in player services** without modifying note judgement or the original song catalogue.

**New working foundations:** an in-app Diagnostics **Check launcher files** action, an offline [Compatibility Doctor](documentation/COMPATIBILITY_DOCTOR.md), [idempotent local score submissions and personal-best leaderboards](documentation/GLOBAL_RANKINGS.md), and a browser dashboard that shows unverified scores and player statistics.

**Planned, not yet delivered:** tested Windows 10/11 compatibility profiles, passive final-result capture, a secure global ranking service, account/player identities and verified score synchronization. External custom-song mods remain a separate optional interoperability track, not the core roadmap.

Read the [modernization strategy](documentation/MODERNIZATION_STRATEGY.md) for priorities, reliability boundaries and phased delivery.

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
| **Device diagnostics** | Read-only live HID device/button/axis monitor in the new Diagnostics tab |
| **Extensions SDK** | Disabled-by-default local JSONL events and an exported C ABI for trusted, version-specific hook adapters |
| **Companion tools** | Read-only Compatibility Doctor, offline cabinet profiles, local idempotent score API, personal-best leaderboards and unverified player stats (Python 3.10+); prototype lobbies remain separate from game execution |

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

## Cabinet diagnostics and extension tools

**No Python or networking is required to play with the original configurator.** These optional tools are separate from the legacy game process.

| Tool | What you can use now | What it does NOT do |
| --- | --- | --- |
| **Diagnostics tab** | Monitor detected HID controls, pressed buttons and analog axes live | Does not decode undocumented original arcade IO boards |
| [Cabinet profiles](documentation/CABINET_PROFILES.md) | Export, compare and explicitly restore game/global settings with backups | No GUI profile picker or automated HID path remapping yet |
| [Song pack validator](documentation/CUSTOM_SONGS.md) | Validate original/licensed song manifests, paths, chart IDs and optional checksums | Does not install songs or charts into any proprietary game binary |
| [Local score API](documentation/SCORES_API.md) | Post/query **unverified** scores stored in SQLite; built-in local browser dashboard | Cannot currently extract actual arcade scores or certify gameplay |
| [Lobby coordinator](documentation/MULTIPLAYER.md) | Local room, join, ready, start and result protocol for 2–4 players | Does not synchronize real games or provide online multiplayer in the arcade process |
| [Event SDK](documentation/EXTENSION_EVENTS.md) | Opt-in JSONL events with a C ABI export in 2EZ.dll | Does not automatically identify song selection or result screens |

On a **modern PC with Python 3.10+**, start the companion:

~~~powershell
python tools/companion_server.py --host 127.0.0.1 --port 8765
~~~

Open the **local companion dashboard** at http://127.0.0.1:8765/dashboard to submit synthetic scores, inspect leaderboards, manage prototype lobbies and view events. The health check is at http://127.0.0.1:8765/health. The server binds only to localhost by default. It is a development prototype, **not a public ranked score server**.

Preview a saved cabinet profile without applying it:

~~~powershell
python tools/cabinet_profiles.py diff --game-dir "C:\Arcade\EZ2" --profile "D:\Backups\my_cabinet.json"
~~~

## New hooks: custom songs, score servers and multiplayer

**What is real today:** existing game-family IO/display/audio hooks; an opt-in exported function named `EZ2_PublishEvent`; the `runtime.ready` event; validation and companion infrastructure.

**What still requires game-specific development:** custom song catalogs and loaders, `song.selected` and verified `score.observed` hooks, score deduplication/anti-cheat, and live synchronized multiplayer. The companion accepts **synthetic or manual data** for development; it is not connected to a proprietary game's result memory.

Read the [new hooks research guide](documentation/NEW_HOOKS.md) for per-title reverse-engineering requirements and safety guards, then the guides on [custom songs](documentation/CUSTOM_SONGS.md), [score APIs](documentation/SCORES_API.md), [multiplayer](documentation/MULTIPLAYER.md) and the [event hook C ABI](documentation/EXTENSION_EVENTS.md). All examples use your own or rights-cleared assets.

## Final:EX research and read-only tools

A privately supplied EZ2AC Final:EX decompilation research archive was reviewed for **behavioral and data-format insights**. We did **not** import reconstructed game source, protected binaries, songs, license data, disassembly dumps or proprietary chart assets. The archive's unpacked-image fingerprint is **not** an on-disk retail-executable fingerprint.

Useful findings now have independent, safe implementations:

| New tool | Use today | Limits |
| --- | --- | --- |
| [GDS lane inspector and SVG mapping](documentation/fnex/FORMATS.md) | Read a mode `.gds`, inspect ordered SongTrack mappings and render a standalone diagram | Read-only structural subset; no chart loader |
| [Ranking inspector](documentation/fnex/FORMATS.md) | Read possible local top-five or top-99 score files without modifying them; player names hidden by default | Formats are research-derived; scores are unverified |
| [Exact-build preflight](documentation/fnex/COMPATIBILITY.md) | SHA-256 user-owned executable and compare with a registered, explicitly on-disk fingerprint | Does not install a hook or prove runtime compatibility |

Try the self-authored sample:

~~~powershell
python tools/gds_inspector.py examples/fnex/synthetic_mode.gds --json
python tools/gds_visualizer.py examples/fnex/synthetic_mode.gds --output synthetic_lanes.svg
python tools/adapter_compatibility.py --exe "C:\OwnGame\EZ2AC.exe" --manifest examples/fnex/adapter-registry.example.json --json
~~~

The adapter registry above intentionally contains a **fake all-zero SHA-256**, so a genuine executable should report no matching adapters. No user content is uploaded.

Research guides: [Final:EX integration overview](documentation/fnex/README.md), [data formats](documentation/fnex/FORMATS.md), [hook design](documentation/fnex/HOOK_DESIGN.md), [compatibility](documentation/fnex/COMPATIBILITY.md) and [implementation plan](documentation/fnex/INTEGRATION_PLAN.md).

**What is not available yet:** real Final:EX custom-song injection, an authenticated score-observation hook, latency changes based on hardcoded offsets or synchronized online multiplayer. These remain per-game-version development tasks.

## Final:EX passive observatory

To support the next hook milestone without guessing undocumented memory addresses, the fork now offers an **offline, read-only observatory** for modes, scores and game-session state transitions:

| Utility | Practical use | Boundary |
| --- | --- | --- |
| Mode inventory | Inspect every user-owned `.gds` in a mode directory and report lanes, key pairs and collisions | Does not read song files or game memory |
| Offline event rehearsal | Turn a synthetic song-preview / confirmation / stage / final-result trace into standard extension events | **Synthetic only**; not a real song or score hook |
| Ranking snapshot comparison | Compare two candidate 5-/99-entry ranking files without disclosing names | Numerical changes are **not authenticated plays** |

~~~powershell
python tools/fnex_mode_inventory.py examples/fnex --json
python tools/fnex_trace_replay.py --input examples/fnex/synthetic_observations.jsonl --output synthetic_events.jsonl --json
python tools/event_bridge.py --file synthetic_events.jsonl
~~~

These commands do **not** connect to a game or transmit data; the event bridge defaults to preview/dry-run. The output is always marked `synthetic=true` and `verified=false`. See the [complete observatory and data contracts guide](documentation/fnex/PASSIVE_OBSERVATORY.md). Runtime memory hooks for a specific, validated Final:EX executable are **still pending**.

## EZ2CustomMod interoperability (external Final:EX song loader)

The latest private source/docs supplied for the project describe a **separate, previously developed EZ2CustomMod DLL** with BMS scanning, custom FNEX song integration and AutoChart. **The loader exists in that external project; it is not bundled or implemented by 2EZConfig_Re**, and no private reconstructed game code was imported.

This fork now adds a contextual **Settings → Extra DLLs** readiness warning, an installation preflight, optional BMSData chart/asset diagnostics and privacy-redacted XP performance-log summaries.

**Important:** our Final:EX default executable is `EZ2AC.exe`, while the supplied external mod guide uses `EZ2B.exe`. Verify the actual installed game revision and use **Exe Name Override** when appropriate; we do not automatically change it.

~~~powershell
python tools/fnex_custommod_preflight.py --game-dir "D:\Arcade\FNEX" --json
python tools/fnex_bms_library_check.py "D:\Arcade\FNEX\BMSData" --check-assets --json
python tools/fnex_custommod_log_report.py "D:\Arcade\FNEX\logs\EZ2CustomMod.log" --json
~~~

The scripts read local metadata and file paths only; they neither install the mod nor start a game. They do not authenticate scores or verify DLL signatures. Start with the [interoperability guide](documentation/fnex/CUSTOMMOD_INTEROP.md) and [private-source audit](documentation/fnex/CUSTOMMOD_SOURCE_AUDIT.md).

## Controlled startup crash isolation

After both standalone HAL and RGB Direct3D7 device creation tests passed, the next controlled test is the real game's 2EZ startup. Settings now includes an **opt-in Minimal startup diagnostic**, retaining IO/hardlock and required super-early patches but skipping optional audio enhancements and later patch passes. Startup logs include before/after markers. A skipped stage can be required by a specific title: Minimal is for diagnosis only, defaults OFF and includes one-click restore. [Test guide](documentation/STARTUP_DIAGNOSTICS.md).

## Isolated native DirectDraw7 and Direct3D7 probe

The new 32-bit 2EZDx7Probe.exe checks the actual Windows system DirectDraw7 runtime without starting the game, injecting hooks, applying graphics wrappers or changing display modes. Optional --deep enumerates D3D7 devices in the standalone process. Results help isolate OS versus game startup failures, **not certify the actual game**. [DX7 probe guide](documentation/NATIVE_DX7_PROBE.md).

## Vendor-neutral graphics diagnostics

2EZConfig_Re should not depend on Intel, NVIDIA or AMD graphics. The Diagnostics tab now links to Windows per-application graphics preferences and provides a separate read-only GPU inventory script. Neither forces GPU selection nor asserts that a legacy DDraw7 game used a particular adapter.

Run tools/gpu_compatibility_report.ps1 on a modern Windows host. See [vendor-neutral GPU guide](documentation/VENDOR_NEUTRAL_GPU.md) for hybrid GPU testing and no-wrapper limitations.

## Intel driver crash evidence (native DirectX baseline)

An actual Final:EX Native DirectX test still produced three Windows Application Error records for **igc32.dll** (Intel driver 32.0.101.7088), `0xC0000005`, at the same fault offset. This is evidence of a failure in the Intel graphics-driver module, **not proof of sole driver responsibility**. 2EZ graphics detours were disabled for the correlated session.

New read-only [Windows crash report](tools/windows_crash_report.ps1) scans local EVTX exports or Windows Application Error events, omits personal system paths and deduplicates identical exports. See [Intel driver crash triage](documentation/INTEL_DRIVER_CRASH.md) for precise evidence and safe GPU/driver A/B experiments without dgVoodoo.

## Display modernization: window modes and 60/120 Hz

**Safety correction:** a real Final:EX report indicates a crash after selecting Windowed. The previous Win32 window restyler did not change DirectDraw cooperative mode. **All unverified Windowed/Borderless/Draggable modes are now disabled and saved non-native values ignored at launch**, rather than risking crashes.

The Display tab now includes **Native DirectX**, an optional per-game diagnostic that skips 2EZ's DirectDraw4/7 graphics hooks while preserving the other IO/patch functionality. It does not install dgVoodoo, change game rendering APIs or guarantee windowed presentation. See [Native DirectX recovery](documentation/NATIVE_DIRECTX_RECOVERY.md).


The Display tab lists Windowed, Borderless, Borderless Fullscreen and Draggable as **disabled until renderer compatibility is certified**. Native is the only currently selectable window mode on unverified builds. The previous helper is deliberately not launched, rather than assuming that window restyling can convert an exclusive renderer.

The DirectDraw4/7 refresh selector now offers **Game default, 60 Hz and experimental 120 Hz**. A 120 Hz monitor request **does not unlock 120 real game FPS**; if the exact display mode is not enumerated, the DLL preserves the game's original refresh request. The original 60 Hz setting is backward compatible.

Built-in POINT texture filtering is available for pixel-sharp visuals. **No GLSL/FSR/CRT shader engine is included yet.** A separate, compatible window upscaler such as Magpie can be evaluated on Windows 10/11, but remains untested and optional. See the [Display & Upscaling guide](documentation/PRESENTATION_MODES.md).

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

**Implemented in the fork:** cleaner and verified toolchain provisioning, pinned build dependencies, PR CI, controlled release packaging, non-destructive JSON settings recovery, live read-only HID diagnostics, opt-in JSONL hook events, and offline companion/utility prototypes.

**Partially implemented or still proposed:** the **Diagnostics tab** provides live HID views, and **Cabinet Profile Manager** has an offline CLI MVP. Still proposed are stricter patch memory-write validation, process-injection lifecycle hardening, real per-game song/score adapters, verified multiplayer, GUI profile management, a **Visual IO Mapper**, and a **Patch Compatibility Inspector**. See the [prioritized roadmap](documentation/ROADMAP.md) for technical evidence and acceptance criteria.

## Project documentation and contributing

| Guide | Description |
| --- | --- |
| [Installation](documentation/INSTALLATION.md) | First run, working directory, limitations and compatibility |
| [Build and releases](documentation/BUILDING.md) | Compiler, dependencies, presets, tests and release workflow |
| [Architecture](documentation/ARCHITECTURE.md) | Frontend, DLL, IO layers, patch engine and data flow |
| [Hook architecture](documentation/NEW_HOOKS.md) | Custom song, score and multiplayer adapter research by game build |
| [Extension event SDK](documentation/EXTENSION_EVENTS.md) | Local events and exported C ABI with safety rules |
| [Custom songs](documentation/CUSTOM_SONGS.md) | Licensed pack format, validation and in-game adapter roadmap |
| [Final:EX research](documentation/fnex/README.md) | Behavioral findings, GDS and ranking inspectors, SHA-256 preflight and guarded adapter plan |
| [EZ2CustomMod interoperability](documentation/fnex/CUSTOMMOD_INTEROP.md) | External mod setup, BMS library checks, XP performance diagnostics and limitations |
| [Private-source audit](documentation/fnex/CUSTOMMOD_SOURCE_AUDIT.md) | Research findings, integration risks and test evidence boundaries |
| [Scores API](documentation/SCORES_API.md) | Local score API, trust limitations and example requests |
| [Global rankings roadmap](documentation/GLOBAL_RANKINGS.md) | Idempotent scoring foundation and secure global services architecture |
| [Modernization strategy](documentation/MODERNIZATION_STRATEGY.md) | Compatibility-first product priorities and phased delivery |
| [Compatibility Doctor](documentation/COMPATIBILITY_DOCTOR.md) | Read-only x86/PE checks, audio/display warnings and modern OS risks |
| [Multiplayer](documentation/MULTIPLAYER.md) | Prototype lobby endpoints and network-coordination roadmap |
| [Cabinet profiles](documentation/CABINET_PROFILES.md) | Offline snapshots, diff and safe restore |
| [Patch authoring](documentation/patches/README.md) | Game IDs, custom JSON format and patch safety |
| [Troubleshooting](documentation/TROUBLESHOOTING.md) | Input/lighting/audio/video problems and safe recovery |
| [Roadmap](documentation/ROADMAP.md) | Audited risks and proposed improvements |
| [Contributing](CONTRIBUTING.md) | Reproduction details, tests and pull requests |
| [Developer verification](documentation/DEVELOPER_GUIDE.md) | CI setup, test matrix and per-version adapter practices |
| [Security policy](SECURITY.md) | Safe reporting and trust boundaries |
| [Changelog](CHANGELOG.md) | Changes developed in this community fork |

**Upstream:** [ben-rnd/2EZConfig-V2](https://github.com/ben-rnd/2EZConfig-V2), based on [the original 2EZConfig](https://github.com/ben-rnd/2EZConfig). This fork does not claim authorship of upstream work. Licensing is governed by [GPL-3.0-or-later](LICENSE) and the bundled [third-party notices](THIRD_PARTY_LICENSES). Preserve these when redistributing modified builds.
