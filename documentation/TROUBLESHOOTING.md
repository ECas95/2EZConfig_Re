# Troubleshooting and diagnostics

**Before changing anything:** back up the game folder, `game-settings.json`, `user-patches.json` (if any) and `%APPDATA%\2ezconfig\`.

| Symptom | Suggested checks |
| --- | --- |
| Wrong game selected | Ensure game executable and working directory are correct. Auto-detection only recognizes known executable MD5 values; select the game/version manually. |
| Game not starting | Verify game EXE name, `2EZ.dll` location, working directory, permissions and extra DLL conflicts. Disable optional patches to isolate. |
| Configuration window does not appear | Remove `-skip-config` launch parameter. Back up `game-settings.json` and set `skip_ui` to `false` if needed. |
| Input not registering | Rebind device, verify Windows HID enumeration and connected controller/port; check the correct game family. |
| Turntable direction/sensitivity wrong | Check axis, inversion, virtual turntable (+/-) bindings, or mouse axis/sensitivity on EZ2DJ/AC. |
| Lights not responding | Ensure an HID device supports output; verify mapping/output index. EZ2Dancer pad and hand-sensor lighting is incomplete. |
| Video black or corrupted | Disable individual DirectDraw fixes; test external DDrawCompat separately on a supported modern Windows system. |
| WASAPI audio not available | WASAPI EQ/Hypersonik are Vista+ features, not XP features. |
| Patch fails or game crashes | Disable `user-patches.json`, restore backup, then enable one patch at a time; executable differences may invalidate addresses/patterns. |
| JSON settings corrupt | Rename the affected file **after backing it up**; let defaults regenerate. Current parser lacks a robust interactive recovery flow. |
| Fresh CMake configure fails | Create `toolchain/`, verify network access, 7z tools and MinGW generator support. See [BUILDING.md](BUILDING.md). |

## Collecting diagnostics
Enable **Settings > Debug Settings > Enable Logging** when available. The DLL uses `2ez-logs.txt` in the game folder when logging is enabled.

A useful issue report states: Windows version/architecture; game ID/version and whether executable is modified; controller/HID model; exact actions; expected vs actual behavior; selected patches and compatibility options; sanitized logs; and whether the problem reproduces without custom patches.

Remove personal names, local file paths, unique device paths and other sensitive data before uploading. Do not attach game binaries, proprietary game data, or secret keys.

## Non-destructive recovery
1. Exit the game/configurator and save a copy of the failing JSON and logs.
2. Disable extra DLLs and user-defined patches.
3. If the JSON cannot be loaded, rename (do not delete) the suspect configuration and allow the application to create defaults.
4. Test minimal launch; add bindings, video/audio options and patches back separately.
5. Report the first reproducible failure with the minimal configuration. This aids diagnosis and preserves the original files.