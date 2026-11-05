#include "extension_events.h"
#include <windows.h>
#include <nlohmann/json.hpp>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {
void check(bool value, const char* message) {
    if (!value) throw std::runtime_error(message);
}
std::string tempDirectory() {
    char dir[MAX_PATH] = {};
    char name[MAX_PATH] = {};
    check(GetTempPathA(MAX_PATH, dir) != 0, "GetTempPathA failed");
    check(GetTempFileNameA(dir, "2ev", 0, name) != 0, "GetTempFileNameA failed");
    check(DeleteFileA(name) != 0, "Cannot delete temp file");
    check(CreateDirectoryA(name, nullptr) != 0, "Cannot create temp directory");
    return name;
}
}

int main() {
    const std::string folder = tempDirectory();
    const std::string logfile = folder + "\\2ez-events.jsonl";
    try {
        check(!ExtensionEvents::isEnabled(), "Event spool should default to off");
        check(!ExtensionEvents::publish("runtime.ready", "{}"), "Disabled event was accepted");
        check(!std::filesystem::exists(logfile), "Disabled event created file");

        ExtensionEvents::configure(folder, "ez2dj_7th", true);
        check(ExtensionEvents::isEnabled(), "Could not enable spool");
        check(!ExtensionEvents::publish("invalid/event", "{}"), "Invalid event name accepted");
        check(!ExtensionEvents::publish("song.selected", "[]"), "Array payload accepted");
        check(!ExtensionEvents::publish("song.selected", "{bad"), "Malformed payload accepted");
        check(ExtensionEvents::publish("runtime.ready", R"({"stage":"post_patches"})"),
              "Valid event not appended");

        std::ifstream in(logfile, std::ios::binary);
        check(static_cast<bool>(in), "Missing event JSONL");
        std::string line;
        check(static_cast<bool>(std::getline(in, line)), "Missing first line");
        const auto event = nlohmann::json::parse(line);
        check(event["schema_version"] == 1, "Schema version not preserved");
        check(event["event"] == "runtime.ready", "Wrong event type");
        check(event["game_id"] == "ez2dj_7th", "Wrong game ID");
        check(event["data"]["stage"] == "post_patches", "Event content not preserved");
        check(event.contains("timestamp_utc"), "Missing timestamp");
        in.close();

        ExtensionEvents::configure(folder, "ez2dj_7th", false);
        check(!ExtensionEvents::publish("runtime.ready", "{}"), "Disable was ignored");
        std::filesystem::remove_all(folder);
        std::cout << "extension_events_tests passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "extension_events_tests: " << error.what()
                  << "\nFixture retained at " << folder << '\n';
        return 1;
    }
}
