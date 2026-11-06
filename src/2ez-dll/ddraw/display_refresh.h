#pragma once

// Read-only availability check for optional 120 Hz DirectDraw display requests.
// A display request never upgrades the game's actual simulation/render FPS.
// The existing 60 Hz legacy override remains unchanged for old configurations.
#include <windows.h>

static inline bool ez2DisplayModeSupportsRefresh(
    DWORD width, DWORD height, DWORD bpp, DWORD requestedHz) {
    if (!width || !height || !requestedHz) return false;
    DEVMODEW mode = {};
    mode.dmSize = sizeof(mode);
    // EnumDisplaySettings enumerates primary-device modes only. Fail closed
    // if the chosen game monitor is unknown or an exact mode is not published.
    for (DWORD index = 0; index < 4096; ++index) {
        ZeroMemory(&mode, sizeof(mode));
        mode.dmSize = sizeof(mode);
        if (!EnumDisplaySettingsW(nullptr, index, &mode)) break;
        if (mode.dmPelsWidth == width &&
            mode.dmPelsHeight == height &&
            mode.dmBitsPerPel == bpp &&
            mode.dmDisplayFrequency == requestedHz) {
            return true;
        }
    }
    return false;
}
