# Presentation modes, upscalers, shaders and refresh rates

**Status:** Phase 1 implemented in source; physical game and monitor testing remains pending. The original game is unchanged by default. The opt-in helper 2EZWindowMode.exe changes only the Win32 window rectangle/style after the game is launched. This is not a new Direct3D renderer or a general DirectDraw exclusive-mode converter.

## Controls in Display tab

| Option | Current function | Limitation |
| --- | --- | --- |
| Original | Leaves game window unmodified | Default and recommended for cabinets |
| Windowed | Adds normal resizable title bar, requested client size | Exclusive DirectDraw may override it |
| Borderless | Centered undecorated window at selected dimensions | No automatic output scaling |
| Borderless Fullscreen | Fills selected monitor with an undecorated window | 4:3 content can stretch without compatible renderer |
| Draggable | Centered borderless; Ctrl+Alt+left mouse drag moves window | Can conflict with game hotkeys; opt in only |
| Display refresh 60 / 120 Hz | DirectDraw4/7 SetDisplayMode refresh request | Not a game FPS unlock |
| Pixel-sharp POINT | Existing Direct3D texture sampling patch | Not a pixel shader, CRT filter or AI upscaler |

All settings are per game. The helper is an optional 32-bit Win32 application, built in the existing XP-targeted toolchain. It starts only after successful game launch, watches the real process PID, finds the largest suitable visible window and applies one style/geometry change. It does not inject any new DLL, read the game's memory, capture frames or make network calls. It exits after the game process exits; it stops if no game window appears within 30 seconds.

The 6th Trax / Remember 1st special launcher does not currently use the helper, to avoid inadvertently styling the intermediate process.

### Why a mode may not work

Windows styling is separate from DirectDraw cooperative mode. When a game invokes DDSCL_EXCLUSIVE / DDSCL_FULLSCREEN, the renderer may force fullscreen or recreate the primary surface, regardless of the helper. These options must be tested for each game and operating system. A failed windowed mode is **not** proof the underlying game supports a stable windowed DirectDraw renderer.

Microsoft: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowpos
Microsoft: https://learn.microsoft.com/en-us/windows/win32/api/ddraw/nf-ddraw-idirectdraw7-setcooperativelevel

## 60 Hz vs 120 Hz vs 120 FPS

- **Display Hz:** how frequently the monitor scans out a frame. The original patch already allowed forcing 60 Hz in some DirectDraw games.
- **Game-render FPS:** new graphics frames produced by the game; it may still render 60 unique frames while the monitor refreshes at 120 Hz.
- **Game simulation/judgement:** internally timed input, audio, long-note and scoring logic; it is not adjusted by the new refresh selector.
- **Upscaler/interpolator:** separate presentation filters can improve perceived image quality or insert synthetic frames but cannot magically change the original chart/gameplay tick rate.

A new 120 Hz mode request is issued only if the primary display enumerates an **exact matching width, height, color depth and 120 Hz mode**. Otherwise the original game request is used. If DirectDraw still rejects the requested 120 Hz mode, the hook retries the original refresh request before returning an error. The existing 60 Hz option remains compatible with legacy profiles. A matching driver mode still does not guarantee success, smooth pacing, or any number of original render FPS.

Microsoft: https://learn.microsoft.com/en-us/windows/win32/api/ddraw/nf-ddraw-idirectdraw7-setdisplaymode

### Original 15 kHz arcade CRT

Do not select 120 Hz without verifying the actual monitor and video timing. Mode enumeration is not a full CRT-safe electrical validation, especially with custom drivers. Leave native/60 Hz as appropriate and perform display tests on the intended hardware.

## Shaders and upscaler compatibility

A real postprocessing pipeline **has not been integrated**. The Display tab only offers the existing Direct3D POINT texture filter (sharper sampling). It is not accurate to label that as GPU upscaling or as a GLSL/FSR/CRT shader.

The independent options worth testing are:

| Backend | Technical fit | Status in this fork |
| --- | --- | --- |
| Magpie | Windows 10 1903+ / Windows 11, DX11 feature level GPU, windowed output, FSR/Anime4K/CRT shader options | External optional Windows upscaler; no built-in integration |
| DXGL | DirectDraw/older Direct3D via OpenGL; alpha quality with incomplete 3D support | Experimental research; not bundled |
| cnc-ddraw | Software 2D DirectDraw, OpenGL or D3D9 renderer with GLSL filters | **Not appropriate as a universal Final:EX D3D7 solution**; project excludes Direct3D games |

References:
- Magpie: https://github.com/Blinue/Magpie
- DXGL status: https://dxgl.org/progress/
- cnc-ddraw limitations: https://github.com/FunkyFr3sh/cnc-ddraw

Do not copy third-party wrapper DLLs into this repository or automatically override the game's ddraw.dll. Test rendering, input latency, screen focus, Alt+Tab, BGA and audio on the real game build.

### Proposed built-in upscaler milestone

1. Verify whether a supported title can expose a post-render surface without adding input, audio or judgement latency.
2. Add an **opt-in, switchable presentation backend**, not per-title undocumented offsets.
3. Implement aspect-aware 4:3 fit and integer scaling first; then bilinear and sharp-bilinear.
4. Only then evaluate CRT scanlines, GLSL/HLSL presets, adaptive scaling and FSR with independently reviewed licenses and measured overhead.
5. Always preserve direct native rendering fallback and allow one-click rollback.

Do not expose shader selections in the GUI as if they work before a renderer is implemented.

## How to test and roll back

- Use a self-owned, exact known EZ2 build.
- Select an optional Window mode and start the game; verify genuine window behavior, Alt+Tab and stable input/audio.
- Test 960×720 or 1280×960 for typical 4:3 artwork; borderless fullscreen may require an aspect-correct scaling backend.
- Test 60 Hz first. Try 120 Hz only on a supported modern LCD, measuring genuine render frames, actual display Hz, audio sync and note judgement.
- Return Window mode to Original and Display refresh to Game default to restore normal launcher behavior. No game files are modified.

Example optional fields in game settings:

~~~json
{
  "presentation_mode": "native",
  "presentation_width": 960,
  "presentation_height": 720,
  "display_refresh_hz": 0
}
~~~

The old force_60hz / ddraw4_force_60hz settings remain recognized. Changing the new refresh selector intentionally retires the corresponding old setting.

**Manual acceptance still pending:** Windows 10/11/XP game builds, monitor modes, original 15 kHz cabinets, external wrapper compatibility, real frame pacing and shader latency.

See [Compatibility Doctor](COMPATIBILITY_DOCTOR.md), [Modernization Strategy](MODERNIZATION_STRATEGY.md) and [Roadmap](ROADMAP.md).
