# Standalone native DirectDraw 7 / Direct3D 7 probe

## Purpose

Final:EX continues to crash after changing graphics preferences and using 2EZ Native DirectX mode. That mode disables the fork's DirectDraw graphics hooks but still loads 2EZ IO, audio and startup patches. The previous Event 1000 fault occurred in the Intel graphics module igc32.dll. The exact cause remains unknown.

To distinguish a legacy system API issue from a game/2EZ issue, this tool runs **outside the game in its own x86 process**, without injecting, patching, changing display modes, installing drivers, or loading graphics wrappers from the program folder.

## How to run (Windows PowerShell)

~~~powershell
.\2EZDx7Probe.exe
.\2EZDx7Probe.exe --deep
~~~

Default mode loads Windows' 32-bit system ddraw.dll via its absolute system directory path, creates an IDirectDraw7 interface, tries DDSCL_NORMAL (supported with a NULL window), and reads the current display mode. It never calls SetDisplayMode or renders a scene.

Optional --deep additionally queries IDirect3D7 and enumerates legacy 3D devices. **Deep mode may enter driver code**: if the probe crashes, check Windows Event Viewer for a new 2EZDx7Probe.exe Application Error record. Neither mode starts Final:EX.

For saving results:

~~~powershell
.\2EZDx7Probe.exe | Out-File -Encoding utf8 dx7-basic.json
.\2EZDx7Probe.exe --deep | Out-File -Encoding utf8 dx7-deep.json
~~~

## Output interpretation

| Field | Meaning |
| --- | --- |
| system_directdraw_dll_loaded | Windows' own 32-bit ddraw.dll loaded |
| ddraw7_create_ok | DirectDrawCreateEx and IDirectDraw7 succeeded |
| ddscl_normal_ok | Windowed-style cooperative mode was accepted by OS test, **not the game** |
| display_mode_read_ok | Current display mode read without changing it |
| d3d7_interface_ok | The optional Direct3D7 interface was available |
| d3d7_enumeration_ok | The optional legacy 3D device enumeration finished |
| hresults | Hexadecimal status per call for comparing Windows/driver configurations |

Passing these checks does **not** prove Final:EX can create its own actual D3D7 device, use exclusive fullscreen, run its initialization patches or render successfully. Failing basic checks suggests a system-level legacy API issue without 2EZ. The probe never forces the Intel, NVIDIA or AMD adapter.

## Controlled next test

1. Keep the game at Display Original / Native DirectX ON / default refresh; do not add dgVoodoo or other graphics wrappers.
2. Run basic and deep probe separately and save the two JSON files.
3. Compare the Windows crash report for 2EZDx7Probe.exe and EZ2AC.exe if either crashes.
4. If probes pass but game fails, next isolate optional 2EZ startup/audio patches or the exact game's original Direct3D7 device creation. Directly launching an executable that requires 2EZ IO may be inconclusive.

## Safety and status

The program is XP-compatible x86, no network activity, no DLL injection, no registry writes, no changes to the game or display mode. CI self-test does not call the driver; real game/GPU compatibility remains unverified. A separate true Windowed mode for Final:EX is not implemented.

References: [Microsoft SetCooperativeLevel](https://learn.microsoft.com/en-us/windows/win32/api/ddraw/nf-ddraw-idirectdraw7-setcooperativelevel), [Native DirectX recovery](NATIVE_DIRECTX_RECOVERY.md), [GPU diagnostics](VENDOR_NEUTRAL_GPU.md).
