// Isolated DirectDraw7 / Direct3D7 capability probe.
// XP-compatible, no game process, injection, hooks, display-mode changes,
// wrappers, network or persistent writes. Optional device tests allocate and
// release a 128x128 render surface in the probe process only.
#define DIRECTDRAW_VERSION 0x0700
#define DIRECT3D_VERSION 0x0700
#include <windows.h>
#include <ddraw.h>
#include <d3d.h>
#include <cstdio>
#include <cstring>
#include <string>

enum class DeviceTest { None, HAL, RGB };

struct Probe {
    bool systemDllLoaded = false;
    bool entryPointFound = false;
    bool ddCreated = false;
    bool cooperativeNormal = false;
    bool displayModeRead = false;
    bool d3dInterface = false;
    bool devicesEnumerated = false;
    bool testWindowCreated = false;
    bool renderSurfaceCreated = false;
    bool deviceCreated = false;
    HRESULT surfaceResult = E_FAIL;
    HRESULT deviceResult = E_FAIL;
    DWORD windowError = 0;
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

static void printJson(const Probe& p, bool deep, bool selfTest, DeviceTest deviceTest) {
    std::printf("{\n"
                "  \"schema_version\":1,\n"
                "  \"tool\":\"2ez_native_ddraw7_probe\",\n"
                "  \"read_only\":%s,\n"
                "  \"no_persistent_changes\":true,\n"
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
                "  \"render_device_test_requested\":%s,\n"
                "  \"render_device_kind\":\"%s\",\n"
                "  \"test_window_created\":%s,\n"
                "  \"render_surface_created\":%s,\n"
                "  \"d3d7_render_device_created\":%s,\n"
                "  \"test_window_error\":%lu,\n"
                "  \"system_dll_error\":%lu,\n"
                "  \"hresults\":{\n"
                "    \"create\":\"0x%08lX\",\n"
                "    \"cooperative\":\"0x%08lX\",\n"
                "    \"display\":\"0x%08lX\",\n"
                "    \"d3d_interface\":\"0x%08lX\",\n"
                "    \"device_enumeration\":\"0x%08lX\",\n"
                "    \"render_surface\":\"0x%08lX\",\n"
                "    \"create_render_device\":\"0x%08lX\"\n"
                "  },\n"
                "  \"self_test\":%s,\n"
                "  \"note\":\"This probes OS legacy APIs in an isolated process. A passing result does not prove Final:EX, exclusive fullscreen, timing or hardware compatibility.\"\n"
                "}\n",
                deviceTest == DeviceTest::None ? "true" : "false",
                p.systemDllLoaded ? "true" : "false",
                p.entryPointFound ? "true" : "false",
                p.ddCreated ? "true" : "false",
                p.cooperativeNormal ? "true" : "false",
                p.displayModeRead ? "true" : "false",
                p.width, p.height, p.bpp, p.refreshHz,
                deep ? "true" : "false",
                p.d3dInterface ? "true" : "false",
                p.devicesEnumerated ? "true" : "false",
                p.devices,
                deviceTest == DeviceTest::None ? "false" : "true",
                deviceTest == DeviceTest::HAL ? "HAL" :
                    deviceTest == DeviceTest::RGB ? "RGB" : "none",
                p.testWindowCreated ? "true" : "false",
                p.renderSurfaceCreated ? "true" : "false",
                p.deviceCreated ? "true" : "false",
                static_cast<unsigned long>(p.windowError),
                static_cast<unsigned long>(p.systemDllError),
                static_cast<unsigned long>(p.createResult),
                static_cast<unsigned long>(p.cooperativeResult),
                static_cast<unsigned long>(p.displayResult),
                static_cast<unsigned long>(p.d3dResult),
                static_cast<unsigned long>(p.enumResult),
                static_cast<unsigned long>(p.surfaceResult),
                static_cast<unsigned long>(p.deviceResult),
                selfTest ? "true" : "false");
}

int main(int argc, char** argv) {
    bool deep = false, selfTest = false;
    DeviceTest deviceTest = DeviceTest::None;
    if (argc == 2 && !std::strcmp(argv[1], "--deep")) deep = true;
    else if (argc == 2 && !std::strcmp(argv[1], "--self-test")) selfTest = true;
    else if (argc == 2 && !std::strcmp(argv[1], "--device-hal")) {
        deviceTest = DeviceTest::HAL;
        deep = true;
    }
    else if (argc == 2 && !std::strcmp(argv[1], "--device-rgb")) {
        deviceTest = DeviceTest::RGB;
        deep = true;
    }
    else if (argc != 1) {
        std::fputs("Usage: 2EZDx7Probe.exe [--deep|--device-hal|--device-rgb|--self-test]\n", stderr);
        return 2;
    }

    Probe report;
    if (selfTest) {
        printJson(report, false, true, DeviceTest::None);
        return 0; // CI can exercise parsing without requiring a GPU/display.
    }

    wchar_t sysdir[MAX_PATH] = {};
    const UINT n = GetSystemDirectoryW(sysdir, MAX_PATH);
    if (!n || n >= MAX_PATH - 12) {
        report.systemDllError = GetLastError();
        printJson(report, deep, false, deviceTest);
        return 1;
    }
    const std::wstring path = std::wstring(sysdir) + L"\\ddraw.dll";
    // Absolute system path prevents accidentally loading local ddraw.dll
    // replacement/wrapper next to this diagnostic executable.
    HMODULE module = LoadLibraryExW(path.c_str(), nullptr, LOAD_WITH_ALTERED_SEARCH_PATH);
    if (!module) {
        report.systemDllError = GetLastError();
        printJson(report, deep, false, deviceTest);
        return 1;
    }
    report.systemDllLoaded = true;
    typedef HRESULT (WINAPI* DirectDrawCreateExFn)(GUID*, LPVOID*, REFIID, IUnknown*);
    const DirectDrawCreateExFn create = reinterpret_cast<DirectDrawCreateExFn>(
        GetProcAddress(module, "DirectDrawCreateEx"));
    if (!create) {
        report.systemDllError = GetLastError();
        printJson(report, deep, false, deviceTest);
        FreeLibrary(module);
        return 1;
    }
    report.entryPointFound = true;

    // Device-creation tests need their own genuine HWND. The window is never
    // shown, and it belongs to this probe, not to the game's process.
    HWND probeWindow = nullptr;
    if (deviceTest != DeviceTest::None) {
        probeWindow = CreateWindowExW(0, L"STATIC", L"2EZ Direct3D7 device test",
            WS_OVERLAPPED, 0, 0, 128, 128, nullptr, nullptr,
            GetModuleHandleW(nullptr), nullptr);
        if (!probeWindow) {
            report.windowError = GetLastError();
            printJson(report, deep, false, deviceTest);
            FreeLibrary(module);
            return 1;
        }
        report.testWindowCreated = true;
    }

    IDirectDraw7* ddraw = nullptr;
    report.createResult = create(nullptr, reinterpret_cast<LPVOID*>(&ddraw),
                                 IID_IDirectDraw7, nullptr);
    if (SUCCEEDED(report.createResult) && ddraw) {
        report.ddCreated = true;
        // DDSCL_NORMAL permits NULL HWND in basic/deep mode; device tests
        // use their own top-level probe HWND. No exclusive mode or hooking.
        report.cooperativeResult = ddraw->SetCooperativeLevel(probeWindow, DDSCL_NORMAL);
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
                if (deviceTest != DeviceTest::None && report.cooperativeNormal) {
                    DDSURFACEDESC2 target = {};
                    target.dwSize = sizeof(target);
                    target.dwFlags = DDSD_CAPS | DDSD_WIDTH | DDSD_HEIGHT;
                    target.dwWidth = 128;
                    target.dwHeight = 128;
                    target.ddsCaps.dwCaps = DDSCAPS_3DDEVICE | DDSCAPS_OFFSCREENPLAIN |
                        (deviceTest == DeviceTest::HAL ? DDSCAPS_VIDEOMEMORY : DDSCAPS_SYSTEMMEMORY);
                    IDirectDrawSurface7* surface = nullptr;
                    // This is an ephemeral GPU/system surface allocation in
                    // this process; no presentation, flipping or display changes.
                    report.surfaceResult = ddraw->CreateSurface(&target, &surface, nullptr);
                    if (SUCCEEDED(report.surfaceResult) && surface) {
                        report.renderSurfaceCreated = true;
                        IDirect3DDevice7* device = nullptr;
                        const GUID& guid = deviceTest == DeviceTest::HAL ?
                            IID_IDirect3DHALDevice : IID_IDirect3DRGBDevice;
                        report.deviceResult = d3d7->CreateDevice(guid, surface, &device);
                        report.deviceCreated = SUCCEEDED(report.deviceResult) && device;
                        if (device) device->Release();
                        surface->Release();
                    }
                }
                d3d7->Release();
            }
        }
        ddraw->Release();
    }
    if (probeWindow) DestroyWindow(probeWindow);
    FreeLibrary(module);
    printJson(report, deep, false, deviceTest);
    // Device mode explicitly fails when its ephemeral 3D render device
    // cannot be created; ordinary basic/deep behavior is backward-compatible.
    if (deviceTest != DeviceTest::None)
        return report.deviceCreated ? 0 : 1;
    return report.ddCreated && report.cooperativeNormal ? 0 : 1;
}
