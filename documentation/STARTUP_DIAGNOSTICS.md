# Minimal startup: isolated Final:EX crash diagnosis

**Status:** opt-in diagnostic instrument in `2EZConfig_Re`, not a confirmed game fix. It does not change DirectDraw, install a wrapper, force a GPU, or claim that Final:EX works on modern Windows.

## Why this is the next test

The user's isolated native DirectDraw7 / Direct3D7 probes succeeded with **both HAL and RGB** paths. The independent test could load DirectDraw7, set `DDSCL_NORMAL`, enumerate three legacy D3D7 device types, create a temporary 128x128 offscreen surface and successfully call `IDirect3D7::CreateDevice` for both hardware and software devices (`HRESULT 0x00000000`).

These results rule out several **basic** missing-API/device-creation explanations, but not an exclusive-fullscreen driver path, a game-specific device format, textures, audio, input or any arcade game patch. The previous game's `Native DirectX` option disabled only the **2EZ DDraw4/7 graphics detours**. The game's own DirectX7 renderer, optional audio enhancements, IO and memory patch passes were still active.

## Two launcher settings to compare

In **2EZConfig.exe → Settings → Startup crash isolation (advanced)**, keep `Native DirectX` ON in Display, Window mode Original, Display refresh Game default, and `Enable Logging` ON.

| Run | Startup option | What remains enabled | What is omitted |
| --- | --- | --- | --- |
| A | Normal (default) | Normal IO/hardlock, graphics selection, audio enhancements and enabled patch stages | Nothing new |
| B | Minimal startup (explicit opt-in) | Game IO/hardlock hooks, global hook setup, super-early patch pass, normal game renderer (unless Native DirectX independently selected), timers and user settings | Hypersonik, AudioEQ, early post-decrypt patch pass, version string patch and normal late patch pass |

The setting is saved per game as `startup_diagnostics_mode: "normal"` or `"minimal"`. **Minimal is intentionally not a stable-play option**: one of the omitted patches might be necessary for this game build. It does not disable required cabinet IO/hardlock or undo code already patched before 2EZ loads; it does not prevent a separately configured Extra DLL from loading.

Selecting Minimal automatically enables per-game `logging_enabled` to ensure useful trace output. The UI provides **Restore normal startup**; click it after the test and verify Normal before ordinary gameplay. Logs remain enabled until explicitly disabled.

## Trace markers

The 2EZ log now marks these boundaries:

- `[Startup] hooks_init begin/end` — common hook setup
- `[Startup] earlyInit begin` — pre-game startup
- `[Startup] Super-early patch pass begin/end (required)` — not bypassed
- `[Startup] Required game IO/hardlock hooks begin` and `earlyInit complete` — not bypassed
- `[Startup] InitThread begin; mode=normal|minimal`
- `[Startup] IO init begin/end` — not bypassed
- `[Startup] Early patch pass begin/end` or `SKIPPED`
- `[Startup] Version string patch begin/end` or `SKIPPED`
- `[Startup] Normal patch pass begin/end` or `SKIPPED`
- `[Startup] InitThread done`

**The last log line is a checkpoint, not a crash stack trace.** Windows Event ID 1000 fault module/code/offset and/or an authorized crash dump remain necessary to localize the actual faulting instruction. A warning in a stage does not prove it caused the crash.

## Safe experiment

1. Back up 2EZConfig.exe, 2EZ.dll, and the settings JSON, including any Extra DLL configuration.
2. Keep the same Windows GPU preference, monitor and driver for both runs. Do not install dgVoodoo or other graphics wrappers.
3. Launch **Run A** with Normal startup + Native DirectX ON, wait for the result, save `2ez-logs.txt` and the Windows Application Error report.
4. Launch **Run B** with Minimal startup + Native DirectX ON, save the same evidence.
5. Restore Normal startup in Settings, regardless of the outcome.
6. Share the two **sanitized** logs and corresponding Event ID 1000 report (no game binaries, music, device serials or full paths).

### Interpret without overclaiming

| Outcome | Evidence it provides |
| --- | --- |
| Normal crashes; Minimal boots further | A skipped optional audio/patch stage or timing difference is worth isolating; not automatically the cause |
| Both crash at the same module/offset | The fault may occur in retained required startup hooks, game initialization or GPU driver path |
| Minimal fails earlier | One or more omitted patch stages may be required; restore Normal |
| Both boot | Capture actual presentation, audio sync and IO before declaring a fix |

## Next after this A/B

If only Normal fails, isolate optional stages **one at a time** by exact build: audio enhancement separately, then only the enabled late patches. Do not remove or bypass the original game's hardlock/license checks or alter proprietary game memory offsets speculatively.

If both crash, use Event Viewer and the checkpoint sequence to locate the next component; independent DirectDraw7 device creation has already been shown to work on the user's machine in these two specific modes.

Related: [Native DX7 Probe](NATIVE_DX7_PROBE.md), [Native DirectX Recovery](NATIVE_DIRECTX_RECOVERY.md), [Windows crash report](INTEL_DRIVER_CRASH.md).
