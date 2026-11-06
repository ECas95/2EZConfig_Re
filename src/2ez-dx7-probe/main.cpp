// Isolated DirectDraw7 / Direct3D7 capability probe.
// XP-compatible, no game process, injection, hooks, display-mode changes,
// wrappers, network or writes. Results are diagnostic, not certification.
#define DIRECTDRAW_VERSION 0x0700
#define DIRECT3D_VERSION 0x0700
#include <windows.h>
#include <ddraw.h>
#include <d3d.h>
#include <cstdio>
#include <cstring>
#include <string>

struct Probe {
    bool systemDllLoaded = false;
    bool entryPointFound = false;
    bool ddCreated = false;
    bool cooperativeNormal = false;
    bool displayModeRead = false;
    bool d3dInterface = false;
    bool devicesEnumerated = false;
    unsigned devices = 0;
    unsigned long width = 0, height = 0, bpp = 0, refreshHz = 0;
    DWORD systemDllError = 0;
    HRESULT createResult = E_FAIL;
    HRESULT cooperativeResult = E_FAIL;
    HRESULT displayResult = E_FAIL;
    HRESULT d3dResult = E_FAIL;
    HRESULT enumResult = E_FAIL;
};

static HRESULT CALLBACK countDevices(LPSTR, LPSTR, LPD3DDEVICEDESC7, LPVOID context) {
    unsigned* count = reinterpret_cast<unsigned*>(context);
    if (count && *count < 1000) ++*count;
    return D3DENUMRET_OK;
}

static void printJson(const Probe& p, bool deep, bool selfTest) {
    std::printf("{\n"
                "  \"schema_version\":1,\n"
                "  \"tool\":\"2ez_native_ddraw7_probe\",\n"
                "  \"read_only\":true,\n"
                "  \"modifies_display_mode\":false,\n"
                "  \"injects_game\":false,\n"
                "  \"game_compatibility_verified\":false,\n"
                "  \"system_directdraw_dll_loaded\":%s,\n"
                "  \"directdraw_create_ex_export\":%s,\n"
                "  \"ddraw7_create_ok\":%s,\n"
                "  \"ddscl_normal_ok\":%s,\n"
                "  \"display_mode_read_ok\":%s,\n"
                "  \"display_width\":%lu,\n"
                "  \"display_height\":%lu,\n"
                "  \"display_bpp\":%lu,\n"
                "  \"display_refresh_hz\":%lu,\n"
                "  \"deep_d3d7_enum_requested\":%s,\n"
                "  \"d3d7_interface_ok\":%s,\n"
                "  \"d3d7_enumeration_ok\":%s,\n"
                "  \"d3d7_device_count\":%u,\n"
                "  \"system_dll_error\":%lu,\n"
                "  \"hresults\":{\n"
                "    \"create\":\"0x%08lX\",\n"
                "    \"cooperative\":\"0x%08lX\",\n"
                "    \"display\":\"0x%08lX\",\n"
                "    \"d3d_interface\":\"0x%08lX\",\n"
                "    \"device_enumeration\":\"0x%08lX\"\n"
                "  },\n"
                "  \"self_test\":%s,\n"
                "  \"note\":\"This probes OS legacy APIs in an isolated process. A passing result does not prove Final:EX, exclusive fullscreen, timing or hardware compatibility.\"\n"
                "}\n",
                p.systemDllLoaded ? "true" : "false",
                p.entryPointFound ? "true" : "false",
                p.ddCreated ? "true" : "false",
                p.cooperativeNormal ? "true" : "false",
                p.displayModeRead ? "true" : "false",
                p.width, p.height, p.bpp, p.refreshHz,
                deep ? "true" : "false",
                p.d3dInterface ? "true" : "false",
                p.devicesEnumerated ? "true" : "false",
                p.devices, static_cast<unsigned long>(p.systemDllError),
                static_cast<unsigned long>(p.createResult),
                static_cast<unsigned long>(p.cooperativeResult),
                static_cast<unsigned long>(p.displayResult),
                static_cast<unsigned long>(p.d3dResult),
                static_cast<unsigned long>(p.enumResult),
                selfTest ? "true" : "false");
}

int main(int argc, char** argv) {
    bool deep = false, selfTest = false;
    if (argc == 2 && !std::strcmp(argv[1], "--deep")) deep = true;
    else if (argc == 2 && !std::strcmp(argv[1], "--self-test")) selfTest = true;
    else if (argc != 1) {
        std::fputs("Usage: 2EZDx7Probe.exe [--deep|--self-test]\n", stderr);
        return 2;
    }

    Probe report;
    if (selfTest) {
        printJson(report, false, true);
        return 0; // CI can exercise parsing without requiring a GPU/display.
    }

    wchar_t sysdir[MAX_PATH] = {};
    const UINT n = GetSystemDirectoryW(sysdir, MAX_PATH);
    if (!n || n >= MAX_PATH - 12) {
        report.systemDllError = GetLastError();
        printJson(report, deep, false);
        return 1;
    }
    const std::wstring path = std::wstring(sysdir) + L"\\ddraw.dll";
    // Absolute system path prevents accidentally loading local ddraw.dll
    // replacement/wrapper next to this diagnostic executable.
    HMODULE module = LoadLibraryExW(path.c_str(), nullptr, LOAD_WITH_ALTERED_SEARCH_PATH);
    if (!module) {
        report.systemDllError = GetLastError();
        printJson(report, deep, false);
        return 1;
    }
    report.systemDllLoaded = true;
    typedef HRESULT (WINAPI* DirectDrawCreateExFn)(GUID*, LPVOID*, REFIID, IUnknown*);
    const DirectDrawCreateExFn create = reinterpret_cast<DirectDrawCreateExFn>(
        GetProcAddress(module, "DirectDrawCreateEx"));
    if (!create) {
        report.systemDllError = GetLastError();
        printJson(report, deep, false);
        FreeLibrary(module);
        return 1;
    }
    report.entryPointFound = true;
    IDirectDraw7* ddraw = nullptr;
    report.createResult = create(nullptr, reinterpret_cast<LPVOID*>(&ddraw),
                                 IID_IDirectDraw7, nullptr);
    if (SUCCEEDED(report.createResult) && ddraw) {
        report.ddCreated = true;
        // DDSCL_NORMAL with a NULL window is explicitly supported by MSDN.
        // No SetDisplayMode, exclusive fullscreen, Win32 window restyling or hook.
        report.cooperativeResult = ddraw->SetCooperativeLevel(nullptr, DDSCL_NORMAL);
        report.cooperativeNormal = SUCCEEDED(report.cooperativeResult);
        if (report.cooperativeNormal) {
            DDSURFACEDESC2 mode = {};
            mode.dwSize = sizeof(mode);
            report.displayResult = ddraw->GetDisplayMode(&mode);
            if (SUCCEEDED(report.displayResult)) {
                report.displayModeRead = true;
                report.width = mode.dwWidth;
                report.height = mode.dwHeight;
                report.bpp = mode.ddpfPixelFormat.dwRGBBitCount;
                report.refreshHz = mode.dwRefreshRate;
            }
        }

        if (deep) {
            IDirect3D7* d3d7 = nullptr;
            report.d3dResult = ddraw->QueryInterface(IID_IDirect3D7,
                                                    reinterpret_cast<void**>(&d3d7));
            if (SUCCEEDED(report.d3dResult) && d3d7) {
                report.d3dInterface = true;
                report.enumResult = d3d7->EnumDevices(countDevices, &report.devices);
                report.devicesEnumerated = SUCCEEDED(report.enumResult);
                d3d7->Release();
            }
        }
        ddraw->Release();
    }
    FreeLibrary(module);
    printJson(report, deep, false);
    // Nonzero exit on inability to create native DD7 or set NORMAL cooperative.
    // A deep enumeration may fail while 2D DD7 succeeds; JSON retains both.
    return report.ddCreated && report.cooperativeNormal ? 0 : 1;
}
