# Intel graphics driver crash triage — Final:EX native DirectX

This guide summarizes a private operator crash report using **only redacted technical evidence**. It does not contain their computer name, game directory, Windows username, saved music or executable.

## Observed facts (November 6, 2026)

The operator compared the PR #10 video preview with `v1.0.0-video-preview.2`, whose **Native DirectX** option bypasses all 2EZ DirectDraw4/7 graphics detours. Its supplied trace explicitly shows:

~~~text
[Display] Native DirectX diagnostic: 2EZ DDraw4/7 graphics hooks disabled.
~~~

The 2EZ log continues through IO initialization and selected patches. It ends with `Applying 2EZconfig Version patch`, **without a captured exception or call stack**. The JSONL spool contains only two `runtime.ready` events, at 14:34:24.189 UTC and 15:01:43.513 UTC. In this codebase, `runtime.ready` means **post-patches**, not that DirectDraw successfully presented a game frame.

The two uploaded EVTX files were **byte-for-byte identical** and contain three unique Application Error records:

| UTC time | Faulting EXE | Faulting module | Module version | Exception | Offset |
| --- | --- | --- | --- | --- | --- |
| 2026-11-06 15:01:43.728 | EZ2AC.exe | igc32.dll | 32.0.101.7088 | 0xC0000005 | 0x00E44C06 |
| 2026-11-06 15:02:17.868 | EZ2AC.exe | igc32.dll | 32.0.101.7088 | 0xC0000005 | 0x00E44C06 |
| 2026-11-06 15:02:48.790 | EZ2AC.exe | igc32.dll | 32.0.101.7088 | 0xC0000005 | 0x00E44C06 |

Event `runtime.ready` at **15:01:43.513 UTC** preceded the first crash by approximately **215 milliseconds**. The repeated exception code/offset provides a useful fingerprint, but there is not enough evidence to correlate the other two crashes with a specific 2EZ graphics-switch setting.

`0xC0000005` denotes an access violation. `igc32.dll` is part of the Intel graphics-driver stack. **The faulting module does not by itself prove that Intel, the game, or 2EZ is solely at fault**: an application may send bad state into a driver, and a driver may mishandle valid state. It does show the failing instruction address is **not in the 2EZ DDraw detour in this observed fault**, and the Native DirectX test still reaches a crash.

**Do not infer that the game uses OpenGL because the faulting DLL contains Intel Graphics Compiler code.** The original Final:EX renderer still uses DirectDraw7/Direct3D7. Converting to OpenGL or Direct3D11 would require a new renderer or a graphics translation layer—outside the no-wrapper goal.

## What is worth testing next (no dgVoodoo, no graphics wrappers)

1. **Establish a clean baseline:** game `Original`, Native DirectX ON, no 120Hz mode experiments, no locally installed graphics-wrapper DLLs. Keep IO settings that the authorized game requires. Use Compatibility Doctor to flag candidate ddraw.dll/d3d9.dll/dxgi.dll files; never delete unknown DLLs automatically.
2. **Identify exact GPU and driver:** Device Manager > Display adapters > Intel adapter > Properties > Driver. Record the GPU model, Windows version and driver version. The EVTX showed Intel driver `32.0.101.7088`, but did not identify the exact GPU model.
3. **If dual-GPU:** Windows Settings > System > Display > Graphics, choose the exact EZ2AC.exe path and test the alternative GPU. Windows' per-app preference may not be honored by all legacy DirectDraw7 applications; verify the faulting module after each test. Do not assume a second GPU exists.
4. **Driver A/B:** test a documented GPU-compatible Intel driver from the PC manufacturer's support page, or a safely restorable previous known-good driver. Back up/current restore point; do not force an unrelated Arc driver on an unsupported Intel GPU. Change one variable at a time.
5. **Optional patch isolation:** The Native DirectX setting disables 2EZ graphics detours, **not the other 2EZ game/IO patches**. The log still reports Fix Keyboard, Fix Spotlights and the version patch. Back up settings and test disabling only nonessential optional patches one at a time, without bypassing required authorized cabinet IO/security functionality. A patch can indirectly trigger an exception inside a graphics driver.
6. **If still failing:** capture the Windows Application Error Event ID 1000, Windows version, installed GPU driver/device ID and—only with explicit consent—a small, sanitized crash dump/stack to see which original game/driver operation precedes the exception.

Do not copy random igc32.dll files from DLL-download websites, disable Windows security or expose an XP arcade to the public internet.

An unrelated community report documents legacy game crashes in igc32.dll after Intel v32 driver updates. That is useful context, **not proof the user's v32.0.101.7088 failure is the same bug**.

References:
- Intel graphics driver/support hub: https://www.intel.com/content/www/us/en/support/products/80939/graphics.html
- Intel driver OEM/customization advisory: https://www.intel.com/content/www/us/en/download/785597/intel-arc-graphics-windows.html
- Intel 2026 graphics driver fix example: https://www.intel.com/content/www/us/en/support/articles/000101418/graphics.html
- Third-party legacy game / igc32.dll report: https://talontales.com/troubleshooting/client-crash-after-patch-with-igc32-dll-error/
- Windows DirectDraw cooperative mode: https://learn.microsoft.com/en-us/windows/win32/api/ddraw/nf-ddraw-idirectdraw7-setcooperativelevel

## Optional local crash report generator

From Windows PowerShell 5.1 or PowerShell 7, inside a local checkout of this repository:

~~~powershell
# Parse the recent Application Error events on this PC:
.\tools\windows_crash_report.ps1 -AppName EZ2AC.exe

# Or analyze two exported EVTX files; identical records are deduplicated:
.\tools\windows_crash_report.ps1 -EvtxPath 'C:\Logs\ez21.evtx','C:\Logs\ez22.evtx'
~~~

The report contains only event timestamps, EXE basename, module basename/version, exception and fault offsets, ephemeral process IDs, and counts grouped by failure signature. It excludes Windows account names, computer IDs, full paths, report IDs, raw event messages and event XML. **It never starts, hooks or modifies the game, and does not transmit data**.

Tested in CI using an entirely synthetic Event ID 1000 XML example. Parser availability depends on Windows Event Log support in the host PowerShell.

See [Native DirectX Recovery](NATIVE_DIRECTX_RECOVERY.md), [Compatibility Doctor](COMPATIBILITY_DOCTOR.md), and [Modernization Strategy](MODERNIZATION_STRATEGY.md).
