# Troubleshooting and diagnostics

**Before modifying your installation:** back up the game folder, `game-settings.json`, `user-patches.json` (if present) and `%APPDATA%\2ezconfig\`.

| Symptom | Recommended checks |
| --- | --- |
| Wrong game selected | Start the configurator with the game folder as working directory; MD5 auto-detection only recognizes known executables. Select the game/version manually if needed. |
| Game does not start | Confirm exe override, companion `2EZ.dll`, working directory and extra DLL dependencies. Disable third-party DLLs and optional patches for isolation. |
| Configuration UI is skipped | Remove `-skip-config` from launch options. If `skip_ui` is set in `game-settings.json`, back it up and change the value to `false`. |
| Buttons not registering | Verify the HID/keyboard device, selected game family, correct bindings and USB port. |
| Turntable not tracking | Check analog axis, inversion, virtual-turntable (+/-) bindings or mouse axis/sensitivity for EZ2DJ/AC. |
| Lighting not responding | Confirm that your HID output device supports the selected output mapping. EZ2Dancer sensor/pad lighting is incomplete. |
| Black/incorrect video | Try the base game without optional DDraw fixes; evaluate external DDrawCompat independently on supported Windows versions. |
| No WASAPI audio feature on XP | WASAPI-based audio requires Windows Vista or later. |
| Game crashes with patches | Disable `user-patches.json` and optional patches. Addresses/patterns can differ among executable revisions. |
| Damaged JSON settings warning | The program archives the bad file as `.corrupt`/`.corrupt.N` and attempts `.bak` recovery. If no valid backup exists, it loads defaults. Confirm controls and game selection before playing. |
| Settings cannot be saved | Check folder permissions, read-only files, antivirus locks and that the archive/backup location is writable. The UI reports save failures. |
| Build errors | Check CMake 3.20+, MinGW Makefiles, 7-Zip fallback, Git network access, and toolchain hash validation. See [BUILDING.md](BUILDING.md). |

## Recovering settings

Current save logic writes a temporary file in the same directory and replaces the settings file after preparing a `.bak` copy of the previous valid content. **This is a last-good backup, not a multi-version history.** A malformed JSON file or a non-object root is moved aside rather than silently discarded. If preserving it fails, startup should report the error instead of proceeding.

This recovery currently covers **game settings and global settings**. It does not validate arbitrary game files, back up the bundled patch definitions or prevent conflicts when multiple instances modify shared settings concurrently.

## Collecting useful diagnostics

Enable **Settings > Debug Settings > Enable Logging** when available. The injected DLL can write `2ez-logs.txt` in the game folder.

Before filing an issue, include: Windows version/architecture; game family/version and executable revision; controller/device model; selected patches; steps to reproduce; expected versus actual behavior; and sanitized logs. Strip personally identifying paths and device IDs, and do not upload copyrighted game executables/data or keys.

See [CONTRIBUTING.md](../CONTRIBUTING.md) and [the safety roadmap](ROADMAP.md).