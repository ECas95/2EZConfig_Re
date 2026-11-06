# GPU-independent graphics diagnostics (DirectX 7)

## Requirement
2EZConfig_Re must remain usable with Intel, NVIDIA and AMD graphics, including integrated and dedicated GPUs, without installing dgVoodoo or vendor-specific graphics hooks. Universal actual DirectDraw7/Direct3D7 rendering cannot be promised on every modern driver without original-game changes or an API translator, which would itself be a graphics wrapper.

## Evidence in Final:EX (Nov 6, 2026)
| Adapter reported by Windows | Driver version |
| --- | --- |
| Intel UHD Graphics | 32.0.101.7088 |
| NVIDIA GeForce RTX 3050 6GB Laptop GPU | 32.0.15.9191 |

Windows crash events from the Native DirectX trial show igc32.dll as fault module, exception 0xC0000005, offset 0x00E44C06, with 2EZ DirectDraw4/7 detours disabled. This is not a complete root-cause explanation. Enumerating both GPUs **does not establish which one rendered the game** or which GPU is wired to the laptop display.

## Implemented: vendor-neutral tools

### In-app Diagnostics
The Diagnostics tab offers an Open Windows Graphics Settings shortcut. It opens the native Windows 10/11 graphics-preference screen (ms-settings:display-advancedgraphics), without changing a preference itself. If unsupported by the OS, it gives an informational message.

Use the **actual game executable** EZ2AC.exe (or the verified Exe Name Override), not merely the 2EZConfig.exe launcher, to request High performance or Power saving. This is a Windows preference, NOT an enforceable GPU selection for old DDraw/D3D7 and not proof the NVIDIA GPU rendered anything.

### Optional local GPU inventory
Windows PowerShell:

    .\tools\gpu_compatibility_report.ps1

The tool uses Win32_VideoController and prints JSON with adapter name, driver version and status only. It excludes PNP device IDs, paths, serials and account details; it never touches drivers, GPU preference, game process or the network. Multiple listed adapters are not proof of an Optimus/MUX topology.

Test the parser without real hardware using synthetic fixture:

    .\tools\gpu_compatibility_report.ps1 -FixturePath .\tools\tests\fixtures\synthetic_gpu_adapters.json

### Existing tools
Use windows_crash_report.ps1 for offline EVTX Event ID 1000 module/version/exception comparison and compatibility_doctor.py for executable architecture, legacy settings and local graphics DLL candidates.

## Controlled hybrid GPU experiment
Back up game settings. Use Original window, Native DirectX ON, game-default refresh, no window helper and no external graphics wrappers.

| Trial | OS preference on exact game EXE | What to observe |
| --- | --- | --- |
| A | Let Windows decide | Starts or crashes? module/offset? |
| B | High performance (often discrete) | Changed outcome? Do not assume selected GPU truly rendered |
| C | Power saving (often integrated) | Changed outcome compared with A/B? |

Restart the game between attempts. If a hardware MUX or dedicated-GPU display output exists, that can be investigated separately without assuming the laptop supports it. For any driver A/B, use only compatible OEM/vendor releases with restore capability.

## What is NOT implemented
- No Direct3D7-to-OpenGL/D3D11 conversion; that requires engine changes or an API wrapper.
- No universal windowed/120 FPS/CRT shader compatibility.
- No forced GPU switch, registry edits, vendor-specific DLL injection, driver install, or automatic fallback.
- No claim that Windows 11 optimizations for windowed DirectX 10/11 also apply to DirectDraw7.

## Next technical milestones
1. Enumerate OS display/monitor capabilities safely and identify exact supported legacy display modes.
2. Measure real adapter use and DirectDraw7 device creation in controlled tests across Intel/NVIDIA/AMD, without changing the retail executable.
3. Verify drivers and OS versions with synthetic/real tests; only allow validated per-game, reversible settings.
4. Provide a clear unsupported status when an original game cannot create a native D3D7 device, rather than installing a wrapper silently.

Sources:
- https://support.microsoft.com/en-us/windows/hardware/display-graphics/optimizations-for-windowed-games-in-windows-11
- https://www.intel.com/content/www/us/en/support/articles/000090168/graphics.html
- https://nvidia.custhelp.com/app/answers/detail/a_id/5035
- https://learn.microsoft.com/en-us/windows/win32/api/ddraw/nf-ddraw-idirectdraw7-setcooperativelevel

See [Native DirectX recovery](NATIVE_DIRECTX_RECOVERY.md), [Intel crash analysis](INTEL_DRIVER_CRASH.md), [Compatibility Doctor](COMPATIBILITY_DOCTOR.md) and [Roadmap](ROADMAP.md).