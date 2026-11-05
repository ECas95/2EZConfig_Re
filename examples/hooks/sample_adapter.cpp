// Illustrative publisher shim for an explicitly loaded, trusted per-game adapter.
// No memory offsets, game-specific detours, song parser or network logic are installed.
// Adapter developers invoke these functions only from verified semantic callbacks.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
#include <string>

using PublishEvent = int (__cdecl *)(const char*, const char*);

static PublishEvent locatePublisher() {
    HMODULE module = GetModuleHandleW(L"2EZ.dll");
    if (!module) return nullptr;
    return reinterpret_cast<PublishEvent>(
        GetProcAddress(module, "EZ2_PublishEvent"));
}

extern "C" __declspec(dllexport)
int __cdecl AdapterOnSongSelected(const char* safeSongId, const char* safeChartId) {
    if (!safeSongId || !safeChartId) return 0;
    // A real adapter should validate these IDs against a version-specific
    // catalog. For safety this sample does not interpolate arbitrary strings
    // into JSON; it demonstrates only a fixed synthetic event payload.
    PublishEvent publish = locatePublisher();
    return publish ? publish("song.selected",
        "{\"song_id\":\"adapter_demo\",\"chart_id\":\"5k_n\"}") : 0;
}

extern "C" __declspec(dllexport)
int __cdecl AdapterOnResultFinalized() {
    // Synthetic data. DO NOT submit as an actual game score or rank it.
    PublishEvent publish = locatePublisher();
    return publish ? publish("score.observed",
        "{\"song_id\":\"adapter_demo\",\"chart_id\":\"5k_n\","
        "\"player_id\":\"local_demo\",\"score\":100000,"
        "\"clear_type\":\"clear\",\"synthetic\":true}") : 0;
}
