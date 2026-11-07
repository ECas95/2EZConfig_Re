#include <windows.h>
#include <mmsystem.h>
#include <tlhelp32.h>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>
#include <nlohmann/json.hpp>

#include "ez2dj_io.h"
#include "ez2dancer_io.h"
#include "sabin_io.h"
#include "bindings.h"
#include "input_manager.h"
#include "patch_store.h"
#include "settings.h"
#include "game_defs.h"
#include "startup_diagnostic_policy.h"
#include "logger.h"
#include "utils.h"

extern "C" {
#include "io.hardlock.hooks.h"
#include "io.hardlock.emulator.h"
}
#include "utilities.h"
#include "ddraw4_fix.h"
#include "ddraw7_fix.h"
#include "audio_eq.h"
#include "hypersonik_hook.h"
#include "hooks.h"
#include "extension_events.h"

extern "C" __declspec(dllexport) void hook_init(void) {}

// Stable C-ABI event entry point for authorized, per-game add-on hooks.
// Returns 1 if queued to the local JSONL spool; 0 if disabled/invalid/error.
extern "C" __declspec(dllexport) int __cdecl EZ2_PublishEvent(
    const char* eventName, const char* jsonObjectPayload) {
    return ExtensionEvents::publish(eventName, jsonObjectPayload) ? 1 : 0;
}


static InputManager* s_input = nullptr;
static BindingStore s_bindings;
static SettingsManager* s_settings = nullptr;
static std::string s_currDirectory;
static std::string s_gameId;
static GameFamily s_gameFamily;

static std::string startupMode() {
    return s_settings ? s_settings->gameSettings().value("startup_diagnostics_mode", "normal")
                      : "normal";
}

static void suspendOtherThreads(std::vector<HANDLE>& out) {
    DWORD myTid = GetCurrentThreadId();
    DWORD processId   = GetCurrentProcessId();
    HANDLE threadSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    if (threadSnapshot == INVALID_HANDLE_VALUE) {
        return;
    }
    THREADENTRY32 threadEntry = { sizeof(threadEntry) };
    if (Thread32First(threadSnapshot, &threadEntry)) {
        do {
            if (threadEntry.th32OwnerProcessID == processId && threadEntry.th32ThreadID != myTid) {
                HANDLE threadHandle = OpenThread(THREAD_SUSPEND_RESUME, FALSE, threadEntry.th32ThreadID);
                if (threadHandle) {
                    SuspendThread(threadHandle);
                    out.push_back(threadHandle);
                }
            }
        } while (Thread32Next(threadSnapshot, &threadEntry));
    }
    CloseHandle(threadSnapshot);
    Logger::info("[+] Application suspended");
}

static void resumeThreads(std::vector<HANDLE>& handles) {
    for (HANDLE threadHandle : handles) {
        ResumeThread(threadHandle);
        CloseHandle(threadHandle);
    }
    handles.clear();
    Logger::info("[+] Application resumed");
}

static DWORD WINAPI InitThread(void*) {
    timeBeginPeriod(1);

    if (!s_settings) {
        Logger::error("[-] Settings not loaded, InitThread aborting");
        return 0;
    }

    const std::string mode = startupMode();
    Logger::info(std::string("[Startup] InitThread begin; mode=") +
                 (StartupDiagnosticPolicy::minimal(mode) ? "minimal" : "normal"));
    ExtensionEvents::configure(s_currDirectory, s_gameId,
        s_settings->gameSettings().value("extension_events_enabled", false));

    if (s_settings->globalSettings().value("high_priority", false)){
        SetPriorityClass(GetCurrentProcess(), HIGH_PRIORITY_CLASS);
        Logger::info("[+] High Priority process initialised");
    }

    s_input = new InputManager();
    try {
        s_bindings.load(*s_settings, *s_input);
        Logger::info("[+] Bindings loaded successfully");
    } catch (...) {
        Logger::error("[-] Bindings failed to load");
    }

    // Required IO is deliberately NOT bypassed in minimal diagnostic mode.
    Logger::info("[Startup] IO init begin");
    switch (s_gameFamily) {
        case GameFamily::EZ2DJ:
            EZ2DJIO::initialiseIO(&s_bindings, s_input, s_settings);
            break;
        case GameFamily::EZ2Dancer:
            EZ2DancerIO::initialiseIO(&s_bindings, s_input, s_settings);
            break;
        case GameFamily::SabinSS:
            SabinIO::initialiseIO(&s_bindings, s_input);
            break;
    }
    
    Logger::info("[Startup] IO init end");

    // Apply patches that need to be run after decryption is finished.
    // 10ms seems to work reliably.
    Sleep(s_settings->globalSettings().value("shim_delay", 10));
    if (StartupDiagnosticPolicy::earlyPatchesEnabled(mode)) {
        Logger::info("[Startup] Early patch pass begin");
        s_settings->patchStore().applyEarlyPatches(s_gameId);
        Logger::info("[Startup] Early patch pass end");
    } else {
        Logger::info("[Startup] Early patch pass SKIPPED (minimal diagnostic)");
    }
    


    //Apply non critical patches that rely on game state being established. Apply last.
    Sleep(s_settings->globalSettings().value("patch_delay_ms", 2000));
    if (s_gameFamily == GameFamily::EZ2DJ || s_gameFamily == GameFamily::EZ2Dancer) {
        if (StartupDiagnosticPolicy::versionPatchEnabled(mode)) {
            Logger::info("[Startup] Version string patch begin");
            s_settings->patchStore().applyVersionPatch("2EZConfig V2.0");
            Logger::info("[Startup] Version string patch end");
        } else {
            Logger::info("[Startup] Version string patch SKIPPED (minimal diagnostic)");
        }
    }

    if (StartupDiagnosticPolicy::normalPatchesEnabled(mode)) {
        Logger::info("[Startup] Normal patch pass begin");
        s_settings->patchStore().applyPatches(s_gameId);
        Logger::info("[Startup] Normal patch pass end");
    } else {
        Logger::info("[Startup] Normal patch pass SKIPPED (minimal diagnostic)");
    }

    Logger::info("[Startup] InitThread done");
    // Lifecycle signal only. Score and song hooks require per-title adapters.
    ExtensionEvents::publish("runtime.ready", "{\"stage\":\"post_patches\"}");
    return 0;
}

static void applySuperEarlyPatches() {
    if (!s_settings || s_gameId.empty()) {
        return;
    }
    s_settings->patchStore().applySuperEarlyPatches(s_gameId);
}

static void initHardlock() {
    if (!s_settings->gameSettings().value("hardlock_enabled", false)) {
        return;
    }
    auto hardlockConfig = s_settings->gameSettings().value("hardlock", nlohmann::json::object());
    auto modAd = static_cast<unsigned short>(std::stoul(hardlockConfig.value("ModAd", "0"), nullptr, 16));
    auto seed1 = static_cast<unsigned short>(std::stoul(hardlockConfig.value("Seed1", "0"), nullptr, 16));
    auto seed2 = static_cast<unsigned short>(std::stoul(hardlockConfig.value("Seed2", "0"), nullptr, 16));
    auto seed3 = static_cast<unsigned short>(std::stoul(hardlockConfig.value("Seed3", "0"), nullptr, 16));
    Logger::info("[Hardlock] ModAd=0x" + toHexString(modAd) + " Seeds=0x" + toHexString(seed1) + ",0x" + toHexString(seed2) + ",0x" + toHexString(seed3));
    if (LoadHardLockInfo(modAd, seed1, seed2, seed3) && InitHooks()) {
        Logger::info("[+] Hardlock initialised");
    } else {
        Logger::error("[-] Hardlock initialisation failed");
    }
}

static void resolveRemember1st() {
    if (s_gameId != "ez2dj_6th") return;
    char exePath[MAX_PATH] = {};
    GetModuleFileNameA(NULL, exePath, MAX_PATH);
    const char* exeName = strrchr(exePath, '\\');
    exeName = exeName ? exeName + 1 : exePath;
    if (_stricmp(exeName, "EZ2DJ.exe") == 0) {
        s_gameId = "rmbr_1st";
        Logger::info("[Init] Remember 1st detected, using rmbr_1st patches");
    }
}

static void earlyInit() {

    if (!s_settings) {
        return;
    }

    const std::string mode = startupMode();
    Logger::info("[Startup] earlyInit begin");
    Logger::info("[Startup] Super-early patch pass begin (required)");
    applySuperEarlyPatches();
    Logger::info("[Startup] Super-early patch pass end");

    if (StartupDiagnosticPolicy::optionalAudioEnabled(mode) &&
        s_settings->gameSettings().value("hypersonik", false)) {
        Hypersonik::install();
        Hypersonik::setMasterVolume(s_settings->gameSettings().value("hypersonik_volume", 75));
    }

    if (!StartupDiagnosticPolicy::optionalAudioEnabled(mode)) {
        Logger::info("[Startup] Hypersonik and AudioEQ skipped (minimal diagnostic)");
    }
    GameFamily family = familyFromGameId(s_gameId);
    Logger::info("[Startup] Required game IO/hardlock hooks begin");
    switch (family) {
        case GameFamily::EZ2DJ:
            resolveRemember1st();
            initHardlock();
            EZ2DJIO::installHooks(s_settings);
            if (StartupDiagnosticPolicy::optionalAudioEnabled(mode)) {
                AudioEQ::install(s_settings);
            }
            if (s_settings->gameSettings().value("native_graphics_mode", false)) {
                Logger::info("[Display] Native DirectX diagnostic: 2EZ DDraw4/7 graphics hooks disabled.");
            } else if (s_gameId == "ez2dj_1st_se" || s_gameId == "rmbr_1st") {
                DDraw4Fix::install(s_gameId, s_settings);
            } else {
                DDraw7Fix::install(s_settings);
            }
            break;
        case GameFamily::EZ2Dancer:
            initHardlock();
            EZ2DancerIO::installHooks(s_settings);
            if (StartupDiagnosticPolicy::optionalAudioEnabled(mode)) {
                AudioEQ::install(s_settings);
            }
            if (s_settings->gameSettings().value("native_graphics_mode", false)) {
                Logger::info("[Display] Native DirectX diagnostic: 2EZ DDraw7 hooks disabled.");
            } else {
                DDraw7Fix::install(s_settings);
            }
            break;
        case GameFamily::SabinSS:
            SabinIO::installHooks();
            break;
    }
    Logger::info("[Startup] earlyInit complete; IO/hardlock retained");
}

static void loadSettings(HMODULE hModule) {
    char dllPath[MAX_PATH] = {};
    GetModuleFileNameA(hModule, dllPath, MAX_PATH);
    char* lastSlash = strrchr(dllPath, '\\');
    if (!lastSlash) {
        return;
    }
    *lastSlash = '\0';
    s_currDirectory = dllPath;

    std::string appDataDir = getAppDataDir();
    if (appDataDir.empty()) {
        return;
    }

    Logger::info("[Init] AppData dir: " + appDataDir);

    // Exit early if shared config dir doesn't exist — 2EZConfig has never been run.
    if (GetFileAttributesA(appDataDir.c_str()) == INVALID_FILE_ATTRIBUTES) {
        Logger::warn("[Init] AppData dir not found, aborting settings load");
        return;
    }

    s_settings = new SettingsManager();
    try {
        s_settings->load(s_currDirectory, appDataDir);
    } catch (...) {
        Logger::error("[Init] Failed to load settings from " + s_currDirectory);
        delete s_settings;
        s_settings = nullptr;
        return;
    }

    s_gameId = s_settings->gameSettings().value("game_id", "");
    s_gameFamily = familyFromGameId(s_gameId);

    Logger::info("[Init] DLL dir: " + s_currDirectory);
    Logger::info("[Init] Game ID: " + (s_gameId.empty() ? "(none)" : s_gameId));
}

static void initLogger() {
    if (!s_settings) {
        return;
    }
    bool loggingEnabled = s_settings->gameSettings().value("logging_enabled", false);
    Logger::init(s_currDirectory, loggingEnabled, "2ez-logs.txt");
}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) {
        loadSettings(hModule);
        initLogger();
        Logger::info("[Startup] hooks_init begin");
        hooks_init();
        Logger::info("[Startup] hooks_init end");
        earlyInit();
        Logger::info("[Startup] creating InitThread");
        CreateThread(nullptr, 0, reinterpret_cast<LPTHREAD_START_ROUTINE>(InitThread), nullptr, 0, nullptr);
    } else if (reason == DLL_PROCESS_DETACH) {
        hooks_shutdown();
    }
    return TRUE;
}
