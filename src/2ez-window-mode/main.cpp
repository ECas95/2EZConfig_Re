// Optional non-invasive window presentation helper for legacy arcade titles.
// It never loads a game DLL, changes display mode or manipulates game memory.
// Target Windows XP SP3+, 32-bit. No Windows hooks or network APIs.
#include <windows.h>
#include <shellapi.h>
#include <string>
#include <cwchar>
#include <cstdlib>

enum class Mode { Windowed, Borderless, BorderlessFullscreen, Draggable };

struct Options {
    DWORD pid = 0;
    Mode mode = Mode::Windowed;
    int width = 960, height = 720;
};

static bool parsePositive(const wchar_t* text, unsigned long* result) {
    if (!text || !*text || *text == L'-') return false;
    wchar_t* end = nullptr;
    const unsigned long value = wcstoul(text, &end, 10);
    if (!end || *end || !value) return false;
    *result = value;
    return true;
}

static bool parseOptions(int count, wchar_t** args, Options& config) {
    if (count != 9) return false; // executable, --pid VALUE, --mode VALUE, width/height
    bool pidSeen = false, modeSeen = false, widthSeen = false, heightSeen = false;
    for (int i = 1; i + 1 < count; i += 2) {
        const std::wstring key(args[i]), value(args[i + 1]);
        unsigned long number = 0;
        if (key == L"--pid" && !pidSeen && parsePositive(value.c_str(), &number)) {
            config.pid = static_cast<DWORD>(number);
            pidSeen = true;
        } else if (key == L"--width" && !widthSeen &&
                   parsePositive(value.c_str(), &number) && number >= 320 && number <= 3840) {
            config.width = static_cast<int>(number);
            widthSeen = true;
        } else if (key == L"--height" && !heightSeen &&
                   parsePositive(value.c_str(), &number) && number >= 240 && number <= 2160) {
            config.height = static_cast<int>(number);
            heightSeen = true;
        } else if (key == L"--mode" && !modeSeen) {
            if      (value == L"windowed") config.mode = Mode::Windowed;
            else if (value == L"borderless") config.mode = Mode::Borderless;
            else if (value == L"borderless_fullscreen") config.mode = Mode::BorderlessFullscreen;
            else if (value == L"draggable") config.mode = Mode::Draggable;
            else return false;
            modeSeen = true;
        } else {
            return false;
        }
    }
    return pidSeen && modeSeen && widthSeen && heightSeen;
}

struct WindowSearch {
    DWORD pid;
    HWND window = nullptr;
    LONG bestArea = 0;
};

static BOOL CALLBACK findWindow(HWND hwnd, LPARAM value) {
    auto* search = reinterpret_cast<WindowSearch*>(value);
    DWORD pid = 0;
    GetWindowThreadProcessId(hwnd, &pid);
    if (pid != search->pid || !IsWindowVisible(hwnd) || GetWindow(hwnd, GW_OWNER)) return TRUE;
    if (GetWindowLongW(hwnd, GWL_EXSTYLE) & WS_EX_TOOLWINDOW) return TRUE;
    RECT r = {};
    if (!GetWindowRect(hwnd, &r)) return TRUE;
    const LONG width = r.right - r.left, height = r.bottom - r.top;
    if (width < 160 || height < 120) return TRUE;
    const LONG area = width * height;
    if (area > search->bestArea) {
        search->bestArea = area;
        search->window = hwnd;
    }
    return TRUE;
}

static bool setWindowMode(HWND hwnd, const Options& config) {
    // Do not try to modify an exclusive DirectDraw surface's refresh or render state.
    // Some games may restore fullscreen themselves: this helper does not fight them.
    const bool framed = config.mode == Mode::Windowed;
    const LONG previous = GetWindowLongW(hwnd, GWL_STYLE);
    const LONG style = (previous & ~(WS_OVERLAPPEDWINDOW | WS_POPUP)) |
                       (framed ? WS_OVERLAPPEDWINDOW : WS_POPUP) | WS_VISIBLE;
    MONITORINFO info = {};
    info.cbSize = sizeof(info);
    HMONITOR monitor = MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST);
    if (!GetMonitorInfoW(monitor, &info)) return false;

    int width = config.width, height = config.height;
    int x = info.rcMonitor.left + (info.rcMonitor.right - info.rcMonitor.left - width) / 2;
    int y = info.rcMonitor.top + (info.rcMonitor.bottom - info.rcMonitor.top - height) / 2;
    if (config.mode == Mode::BorderlessFullscreen) {
        x = info.rcMonitor.left; y = info.rcMonitor.top;
        width = info.rcMonitor.right - x;
        height = info.rcMonitor.bottom - y;
    } else if (framed) {
        RECT rect = {0, 0, width, height};
        if (!AdjustWindowRectEx(&rect, style, FALSE,
                                static_cast<DWORD>(GetWindowLongW(hwnd, GWL_EXSTYLE)))) return false;
        width = rect.right - rect.left;
        height = rect.bottom - rect.top;
        x = info.rcMonitor.left + (info.rcMonitor.right - info.rcMonitor.left - width) / 2;
        y = info.rcMonitor.top + (info.rcMonitor.bottom - info.rcMonitor.top - height) / 2;
    }
    SetLastError(0);
    const LONG old = SetWindowLongW(hwnd, GWL_STYLE, style);
    if (!old && GetLastError() != 0) return false;
    if (SetWindowPos(hwnd, HWND_NOTOPMOST, x, y, width, height,
                     SWP_FRAMECHANGED | SWP_NOACTIVATE | SWP_SHOWWINDOW)) return true;
    // Best-effort rollback if WindowPos rejects the change.
    SetWindowLongW(hwnd, GWL_STYLE, previous);
    SetWindowPos(hwnd, nullptr, 0, 0, 0, 0,
                 SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED | SWP_NOACTIVATE);
    return false;
}

static void pollDrag(HWND hwnd, bool& dragging, POINT& offset) {
    const bool combo = (GetAsyncKeyState(VK_CONTROL) & 0x8000) &&
                       (GetAsyncKeyState(VK_MENU) & 0x8000) &&
                       (GetAsyncKeyState(VK_LBUTTON) & 0x8000);
    if (!combo || IsIconic(hwnd)) { dragging = false; return; }
    POINT pt = {};
    if (!GetCursorPos(&pt)) { dragging = false; return; }
    if (!dragging) {
        const HWND hit = WindowFromPoint(pt);
        if (!hit || GetAncestor(hit, GA_ROOT) != hwnd) return;
        RECT r = {};
        if (!GetWindowRect(hwnd, &r)) return;
        offset.x = pt.x - r.left;
        offset.y = pt.y - r.top;
        dragging = true;
    }
    SetWindowPos(hwnd, nullptr, pt.x - offset.x, pt.y - offset.y, 0, 0,
                 SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE);
}

int WINAPI WinMain(HINSTANCE, HINSTANCE, LPSTR, int) {
    // Dynamically select Vista DPI API to keep XP imports compatible.
    HMODULE user32 = GetModuleHandleW(L"user32.dll");
    if (user32) {
        typedef BOOL (WINAPI* SetDpiAware)();
        auto dpi = reinterpret_cast<SetDpiAware>(GetProcAddress(user32, "SetProcessDPIAware"));
        if (dpi) dpi();
    }
    int argc = 0;
    wchar_t** args = CommandLineToArgvW(GetCommandLineW(), &argc);
    if (!args) return 2;
    Options options;
    const bool parsed = parseOptions(argc, args, options);
    LocalFree(args);
    if (!parsed) return 2;

    HANDLE process = OpenProcess(SYNCHRONIZE, FALSE, options.pid);
    if (!process) return 3;
    const DWORD started = GetTickCount();
    HWND current = nullptr;
    bool dragging = false;
    POINT dragOffset = {};
    bool appliedAtLeastOnce = false;
    while (WaitForSingleObject(process, 0) == WAIT_TIMEOUT) {
        if (current && !IsWindow(current)) {
            current = nullptr;
            dragging = false;
        }
        if (!current) {
            WindowSearch search = {options.pid, nullptr, 0};
            EnumWindows(findWindow, reinterpret_cast<LPARAM>(&search));
            if (search.window) {
                current = search.window;
                if (!setWindowMode(current, options)) {
                    CloseHandle(process);
                    return 4;
                }
                appliedAtLeastOnce = true;
            } else if (static_cast<DWORD>(GetTickCount() - started) > 30000) {
                CloseHandle(process);
                return 5;
            }
        }
        if (current && options.mode == Mode::Draggable) {
            pollDrag(current, dragging, dragOffset);
        }
        Sleep(options.mode == Mode::Draggable ? 16 : 100);
    }
    CloseHandle(process);
    return appliedAtLeastOnce ? 0 : 5;
}
