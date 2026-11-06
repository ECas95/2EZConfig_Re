# Compatibility Doctor: modern Windows / legacy arcade preflight

**Implemented:** a read-only Python 3.10+ report for a user-owned game folder. The tool does not inject DLLs, launch games, change Windows settings, patch executables, read graphics/audio device serials or test arcade hardware.

## Start with diagnostics

~~~powershell
python tools/compatibility_doctor.py --game-dir "D:\Arcade\EZ2" --json
python tools/compatibility_doctor.py --game-dir "D:\Arcade\EZ2" --exe EZ2B.exe --json
~~~

The second command changes only the file analyzed by the doctor. It **does not** edit Exe Name Override in the launcher. To change an actual game setting, use the normal 2EZConfig_Re UI after verifying the exact game revision.

### What the doctor checks

| Check | Why it matters | Limit |
| --- | --- | --- |
| DOS/NT PE signatures, architecture | This fork injects an x86 2EZ.dll; wrong architecture cannot share a 32-bit process | Header validation alone cannot establish file authenticity or integrity |
| PE32 vs PE32+, DLL flag | Detect accidental use of an incompatible 64-bit binary or ordinary EXE as injected DLL | No executable import/load simulation |
| Game executable selection | Helps spot missing/incorrect override per installed game | Default fallback is heuristic when settings lack a known game ID |
| 2EZConfig.exe and 2EZ.dll presence | Detect common launch-preparation errors | Never checks DLL authenticity or code signature |
| game-settings.json | Display/record relevant options without rewriting them | Does not auto-recover damaged JSON |
| 60 Hz / legacy DirectDraw options | Warn before unsafe refresh modes on CRT or mismatched digital displays | No actual monitor or GPU mode probing |
| WASAPI/Hypersonik settings | WASAPI is not available on XP; exclusive audio needs hardware testing | No actual audio latency or device-format measurement |
| Modern Windows host | Suggest DPI, fullscreen, graphics and audio tests | Host is the PC running Python, potentially different from the cabinet |

Reports include only chosen executable basename, game ID if found, PE-header properties, OS family and actionable issue codes. **No full game paths, file hashes or proprietary binary data are included**. The doctor does not search arbitrary game files or connect to any network.

### PE header warning

A valid-looking PE header is a **very weak** check. It does not prove the executable is an authorized retail build, clean, compatible, or safe to run. For sensitive executable-version-specific patch adapters, use the separate exact-SHA-256 adapter registry and verify expected target memory bytes before any hook.

### Error severity

- **error:** missing target or injected DLL, invalid PE, mismatched machine architecture.
- **warning:** missing settings or helper launcher; unsupported audio option when proven from host OS.
- **info:** review a selected compatibility mode or measured performance concern.

Return code is nonzero when an error is found; warning/info reports normally exit successfully to support automated diagnostics.

## Modern Windows risk matrix

| Component | Legacy game technology | Modern-system validation |
| --- | --- | --- |
| Graphics | DirectDraw 7 / Direct3D 7 | Native/windowed/fullscreen surface creation, loss/restoration, 4:3 scaling, palette, transparency, multi-GPU |
| Presentation | Fixed 60 Hz expectations and exclusive modes | Available monitor modes, DPI scaling and focus/alt-tab, fullscreen optimizer scope |
| Audio | DirectSound, per-voice keysound playback | Real latency and device access on Vista+ audio endpoints, shared/exclusive format, underruns |
| Input | Original arcade IO and optional HID/keyboard paths | Polling stability, device reconnection, event order, turns/scratch mapping |
| Compatibility patches | Per-title/version memory patterns | SHA-256 exact version, expected original bytes, rollback/no-op when mismatch |
| Operating systems | XP SP3 through newer Windows | Test *each* game revision and OS build, not just compile success |

On Windows 10/11, diagnosing legacy DirectDraw/DirectSound issues should be prioritized over installing a broad graphics/audio wrapper blindly. Windows 11's documented windowed-game optimization covers DX10/11, not a guaranteed fix for DirectDraw7. A DirectDraw wrapper, when validated, should be **optional and reversible** with licensing/driver compatibility checks.

Microsoft references:
- https://learn.microsoft.com/en-us/windows/desktop/directdraw/directdraw
- https://learn.microsoft.com/en-us/windows/win32/coreaudio/interoperability-with-legacy-audio-apis
- https://learn.microsoft.com/en-us/windows/win32/hidpi/high-dpi-desktop-application-development-on-windows
- https://support.microsoft.com/en-us/windows/hardware/display-graphics/optimizations-for-windowed-games-in-windows-11

## Next improvements (not implemented)

1. Windows-specific display mode inventory and safe, read-only device capability probes.
2. Accurate DPI-awareness inspection and application DPI policy experiments.
3. Basic audio endpoint health and supported sample-rate checks without changing system defaults.
4. Opt-in compatibility profiles with preview/diff and backup/restore; version-gated presets only.
5. Automated support bundles that redact user-specific paths, device serials, song titles and account information.
6. Hardware-lab checklists for CRT 15 kHz cabinets, modern monitors and dual-GPU PCs.

See [Modernization Strategy](MODERNIZATION_STRATEGY.md), [Architecture](ARCHITECTURE.md), [Roadmap](ROADMAP.md) and [Safety policy](../SECURITY.md).
