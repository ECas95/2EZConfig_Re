#include "settings_io.h"

#include <windows.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {
void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

void overwriteRaw(const std::string& path, const std::string& content) {
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    out << content;
    require(static_cast<bool>(out), "Cannot write test fixture");
}

std::string testDirectory() {
    char path[MAX_PATH] = {};
    char name[MAX_PATH] = {};
    require(GetTempPathA(MAX_PATH, path) != 0, "GetTempPathA failed");
    require(GetTempFileNameA(path, "ezt", 0, name) != 0, "GetTempFileNameA failed");
    require(DeleteFileA(name) != 0, "Cannot remove temporary file");
    require(CreateDirectoryA(name, nullptr) != 0, "Cannot create test directory");
    return name;
}
}

int main() {
    const std::string directory = testDirectory();
    const std::string path = directory + "\\game-settings.json";
    const nlohmann::json defaults = {{"version", 0}};
    try {
        auto first = loadJsonFileSafely(path, defaults);
        require(first.needsSave && first.value == defaults, "Missing file must use defaults");

        saveJsonFileSafely(path, {{"version", 1}});
        auto loaded = loadJsonFileSafely(path, defaults);
        require(!loaded.needsSave && loaded.value["version"] == 1, "First save/load failed");

        saveJsonFileSafely(path, {{"version", 2}});
        auto old = loadJsonFileSafely(path + ".bak", defaults);
        require(old.value["version"] == 1, "Backup must contain previous valid settings");

        overwriteRaw(path, "{ malformed JSON");
        auto recovered = loadJsonFileSafely(path, defaults);
        require(recovered.needsSave, "Corrupted file must need a new save");
        require(recovered.value["version"] == 1, "Recovery must use last valid backup");
        require(!recovered.warning.empty(), "Recovery warning is required");
        require(std::filesystem::exists(path + ".corrupt"), "Damaged file must be preserved");
        require(!std::filesystem::exists(path), "Damaged file must be moved away");

        saveJsonFileSafely(path, recovered.value);
        auto afterRecovery = loadJsonFileSafely(path, defaults);
        require(afterRecovery.value["version"] == 1, "Recovered state not persisted");

        overwriteRaw(path, "[]");
        overwriteRaw(path + ".bak", "{ bad backup");
        auto fallback = loadJsonFileSafely(path, defaults);
        require(fallback.value == defaults, "Bad main and backup must use defaults");
        require(fallback.needsSave && !fallback.warning.empty(), "Fallback warning missing");
        require(std::filesystem::exists(path + ".corrupt.1"), "Second damaged file must be kept");
        require(std::filesystem::exists(path + ".bak"), "Invalid backup must never be destroyed");

        bool refused = false;
        try {
            saveJsonFileSafely(path, nlohmann::json::array());
        } catch (const std::exception&) {
            refused = true;
        }
        require(refused, "Writing a non-object settings root must fail");

        std::filesystem::remove_all(directory);
        std::cout << "settings_io_tests: passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "settings_io_tests: " << error.what()
                  << "\nFixtures retained in: " << directory << '\n';
        return 1;
    }
}
