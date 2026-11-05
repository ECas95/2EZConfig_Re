#include "extension_events.h"
#include <windows.h>
#include <nlohmann/json.hpp>
#include <cstdio>
#include <fstream>
#include <string>

namespace {
// This MinGW/GCC toolchain uses win32 threads without std::mutex support.
// Win32 interlocked operations are available on the XP target.
volatile LONG g_lock = 0;
class ScopedEventLock {
public:
    ScopedEventLock() {
        while (InterlockedCompareExchange(&g_lock, 1, 0) != 0) Sleep(1);
    }
    ~ScopedEventLock() { InterlockedExchange(&g_lock, 0); }
    ScopedEventLock(const ScopedEventLock&) = delete;
    ScopedEventLock& operator=(const ScopedEventLock&) = delete;
};
bool g_enabled = false;
std::string g_path;
std::string g_gameId;

bool validEventName(const char* s) {
    if (!s || !*s) return false;
    size_t n = 0;
    for (const unsigned char* p = reinterpret_cast<const unsigned char*>(s); *p; ++p) {
        ++n;
        if (n > 64) return false;
        const unsigned char ch = *p;
        if (!((ch >= 'a' && ch <= 'z') ||
              (ch >= 'A' && ch <= 'Z') ||
              (ch >= '0' && ch <= '9') || ch == '.' || ch == '_' || ch == '-')) {
            return false;
        }
    }
    return true;
}

std::string utcTimestamp() {
    SYSTEMTIME t{};
    GetSystemTime(&t);
    char buffer[40] = {};
    std::snprintf(buffer, sizeof(buffer), "%04u-%02u-%02uT%02u:%02u:%02u.%03uZ",
                  t.wYear, t.wMonth, t.wDay,
                  t.wHour, t.wMinute, t.wSecond, t.wMilliseconds);
    return buffer;
}
}

void ExtensionEvents::configure(const std::string& gameDirectory,
                                const std::string& gameId,
                                bool enabled) {
    ScopedEventLock guard;
    g_enabled = enabled && !gameDirectory.empty() && !gameId.empty();
    g_path = g_enabled ? gameDirectory + "\\2ez-events.jsonl" : "";
    g_gameId = g_enabled ? gameId : "";
}

bool ExtensionEvents::isEnabled() {
    ScopedEventLock guard;
    return g_enabled;
}

bool ExtensionEvents::publish(const char* eventName, const char* jsonObjectPayload) {
    if (!validEventName(eventName) || !jsonObjectPayload) return false;
    size_t length = 0;
    for (; length <= 4096 && jsonObjectPayload[length] != '\0'; ++length) {}
    if (length > 4096) return false;

    try {
        const auto data = nlohmann::json::parse(
            jsonObjectPayload, jsonObjectPayload + length);
        if (!data.is_object()) return false;
        ScopedEventLock guard;
        if (!g_enabled) return false;
        const nlohmann::json record = {
            {"schema_version", 1},
            {"event", eventName},
            {"game_id", g_gameId},
            {"timestamp_utc", utcTimestamp()},
            {"data", data}
        };
        std::ofstream file(g_path, std::ios::binary | std::ios::app);
        if (!file) return false;
        file << record.dump() << "\n";
        file.flush();
        return static_cast<bool>(file);
    } catch (...) {
        // Always fail open: no auxiliary event may break the game.
        return false;
    }
}
