# Installation and first run

## Scope
The CMake configuration targets 32-bit Windows XP SP3 and later. This is an intended build target, **not** an independently verified compatibility matrix for this fork.

Supported game families represented in source: EZ2DJ/EZ2AC, EZ2Dancer and Sabin Sound Star: Renascence Burst. WASAPI audio options require Vista or newer. EZ2Dancer pad/hand-sensor lighting is incomplete.

## Install
1. Back up the original game files and existing settings.
2. Place `2EZConfig.exe` and `2EZ.dll` beside the game executable.
3. Launch the configurator **from the game folder as its working directory**. The code loads per-game settings from `.` and searches for `*.exe` there.
4. Auto-detection relies on an executable MD5 lookup. If no recognized executable is found, choose the correct family/version manually.
5. Optionally specify **Exe Name Override**. Set up **Buttons**, **Analogs** (EZ2DJ/AC), **Lights** and **Patches**, then click **Play EZ2**.

## Configurations

| Path | Meaning |
| --- | --- |
| `./game-settings.json` | Per-game selection, patches and launch options |
| `%APPDATA%\2ezconfig\global-settings.json` | Shared controller and global settings |
| `%APPDATA%\2ezconfig\patches.json` | Bundled patch definitions extracted from the executable |
| `./user-patches.json` (optional) | Game-specific custom patch definitions |
| `./2ez-logs.txt` (if enabled) | In-game diagnostic logging |

The bundled patch file is refreshed when its embedded `ver` is higher. Edit `user-patches.json` for custom definitions rather than relying on changes to the generated shared patch file. Back up **both** game-local and AppData configuration before upgrading.

## Optional video presentation (new)

**Safety change:** releases now distribute 2EZConfig.exe and 2EZ.dll only. The experimental 2EZWindowMode.exe helper remains in the source tree but is withheld from packages after an actual Final:EX Windowed crash report. The launcher refuses to run it for any unverified game build, even if an older version left a non-native presentation mode saved. The option Native DirectX in the Display tab can skip 2EZ's DirectDraw/Direct3D detours for debugging without installing dgVoodoo.

The Display tab also supports an optional **60 Hz or guarded 120 Hz display request** on titles with the supported DirectDraw4/7 hook, plus existing POINT sampling for sharp pixels. This is not a 120-FPS engine patch or built-in shader framework.

Use **Original** for current EZ2 game builds. Windowed, Borderless and Draggable are disabled pending a real native window capability. Do not test 120 Hz on an original CRT without verified timings. See [Native DirectX recovery](NATIVE_DIRECTX_RECOVERY.md) for crash isolation and [Presentation Modes](PRESENTATION_MODES.md) for future options.

## Launch options and limitations
- `-skip-config` bypasses the UI; the `skip_ui` field of the game JSON also bypasses it.
- Extra DLLs are supplied as a whitespace-separated string: paths with spaces are not reliably supported.
- Some legacy games are sensitive to periods (`.`) in folder names while reading INI files.
- Upstream notes that 1st SE on XP may require drive `C:`.
- Optional [DDrawCompat](https://github.com/narzoul/DDrawCompat) is external software and should be tested separately from built-in fixes.
- A 60 Hz patch requests a display mode; verify actual display refresh independently.

See [Troubleshooting](TROUBLESHOOTING.md) and [Patch reference](patches/README.md).