# Native DirectX 7 and safe presentation recovery

**Purpose:** restore original EZ2AC/EZ2DJ video behavior without dgVoodoo or an external graphics wrapper. Native DirectX is a diagnostic, not a promised windowed mode.

## November 2026 Final:EX field report

The operator's 2ez-logs.txt (25 log lines) shows the game's DirectDraw7 and Direct3D7 interfaces were created, with the 2EZ graphics detours enabled (32bpp=1, refreshHz=60, pointFilter=1, texelAlignment=1). A Direct3D7 device and DrawPrimitive hook were initialized. The last message was Applying Patch Timer Freeze. The JSONL event feed has just runtime.ready.

**The report contains no exception code, faulting module, crash dump or Win32 window helper trace.** It does not prove which operation caused the crash. However, the previous window helper used only SetWindowLong/SetWindowPos, without updating DirectDraw cooperative mode and surfaces. A fullscreen-exclusive renderer may fail when its game window is externally restyled.

## Why old Windowed was unsafe

DirectDraw separates DDSCL_NORMAL (windowed cooperative mode) from DDSCL_EXCLUSIVE + DDSCL_FULLSCREEN. The application, not a separate window-style helper, selects its cooperative level. Changing the HWND border does not convert exclusive primary/back-buffer surfaces into a windowed renderer.

Microsoft: https://learn.microsoft.com/en-us/windows/win32/api/ddraw/nf-ddraw-idirectdraw7-setcooperativelevel

## Safety patch implemented in 2EZConfig_Re

1. A central PresentationPolicy refuses to launch the standalone window restyler on game builds that have not been certified for safe native windowed rendering. No EZ2 version has passed this test yet.
2. The Display tab disables unsupported Windowed, Borderless, Borderless Fullscreen and Draggable options. A previously saved non-native mode is ignored on launch and can be reset using Reset saved window mode to Original.
3. The independent 2EZWindowMode.exe is NOT launched for an unverified game. The launcher leaves the original game window and display surfaces alone.
4. A new per-game Native DirectX (no 2EZ DirectDraw/Direct3D hooks) checkbox instructs 2EZ.dll not to install its DirectDraw4/7 graphics hooks. Existing IO, audio and other 2EZ services remain active.
5. Native graphics mode defaults OFF to preserve existing 2EZ compatibility fixes. DirectDraw refresh override, point filtering and texel alignment settings become inactive while native graphics is enabled, without deleting user configuration.

**This fixes the unsafe attempt, not the underlying windowed rendering ability.** The feature is blocked instead of creating another unpredictable crash.

## DirectX versus OpenGL

- The unmodified game already speaks DirectDraw7/Direct3D7. DirectX 7 is the only renderer we can use without changing or translating its rendering API.
- OpenGL or Direct3D 11 cannot directly execute old Direct3D7 commands. Switching requires a modified game renderer or an intercepting translation layer. Even an in-house one would be a graphics wrapper and violate a strict no-wrapper requirement.
- A separate Windows 10/11 Graphics Capture plus Direct3D11 viewer could display some native fullscreen output in a second window without injecting a graphics hook into the game, but that is a capture display, not a real windowed game. Input focus, exclusivity, black frames and latency remain open risks; this is only a feasibility proposal.
- Monitor refresh 120 Hz and actual game-rendered 120 FPS are separate problems. A graphics presentation change must not affect audio, judgement or scoring.

## Reproducible test plan

| Trial | Presentation | Native graphics switch | Expected observation |
| --- | --- | --- | --- |
| A | Original | OFF | Existing compatibility patches active, compare baseline startup |
| B | Original | ON | No DDraw4Fix/DDraw7Fix hook logs; the game uses Windows' original DirectX7 implementation |
| C | Original | Restore whichever worked | No unsafe external restyling |
| Windowed | Disabled | N/A | The launcher never launches an unverified restyler |

If Trial B still fails, it may reflect native driver/runtime incompatibility or another game/IO/patch issue; this toggle cannot cure every DirectX7 problem. Leave 120 Hz off during crash diagnostics.

To locate the actual crash, obtain the Windows Application Error exception code, faulting module and offset, OS version, GPU/driver and a hash of the locally owned game executable. A final log message is not a reliable faulting instruction. Do not upload commercial game binaries, media, DRM secrets or private player data.

## Follow-up: real Intel driver fault captured

An additional Final:EX run with Native DirectX ON reproduced a crash in `igc32.dll`, version `32.0.101.7088`, exception `0xC0000005`, offset `0x00E44C06`. The Windows logs show three matching fault signatures. This shifts the next diagnostic priority to **Intel GPU/driver compatibility and isolation of other game patches**, rather than assuming Win32 window restyling is the only problem. The exact crash stack and GPU model were not supplied. See [Intel driver crash triage](INTEL_DRIVER_CRASH.md).

## Next native presentation research

**Preferred:** research an existing *original game option* that creates a real DirectDraw DDSCL_NORMAL window, if one is available for a confirmed build. No such option has been demonstrated in the supplied log.

**Possible independent prototype:** use Windows Graphics Capture and a separate native Direct3D11 presentation window, with no game-process graphics interception. It would remain a captured mirror, not true game windowed mode; do not advertise it as the latter until measured.

**Not in scope:** Direct3D7 to OpenGL/D3D11 replacement. That inherently requires a new renderer or graphics translation/wrapper layer.

Sources:
- DirectDraw cooperative level: https://learn.microsoft.com/en-us/windows/win32/api/ddraw/nf-ddraw-idirectdraw7-setcooperativelevel
- Windows capture: https://learn.microsoft.com/en-us/uwp/api/windows.graphics.capture
- Windows 11 DX10/DX11 windowed optimizations: https://support.microsoft.com/en-us/windows/hardware/display-graphics/optimizations-for-windowed-games-in-windows-11

Related: [Presentation Modes](PRESENTATION_MODES.md), [Compatibility Doctor](COMPATIBILITY_DOCTOR.md), [Modernization Strategy](MODERNIZATION_STRATEGY.md).
