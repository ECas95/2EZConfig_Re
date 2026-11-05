#include "settings_io.h"

#include <windows.h>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>

namespace {
bool fileExists(const std::string& path) {
    const DWORD attributes = GetFileAttributesA(path.c_str());
    if (attributes != INVALID_FILE_ATTRIBUTES) {
        return true;
    }
    const DWORD error = GetLastError();
    if (error == ERROR_FILE_NOT_FOUND || error == ERROR_PATH_NOT_FOUND) {
        return false;
    }
    throw std::runtime_error("Cannot determine whether settings file exists: " + path +
                             " (Win32 error " + std::to_string(error) + ")");
}

std::string win32Error(const std::string& action, DWORD code) {
    return action + " (Win32 error " + std::to_string(code) + ")";
}

nlohmann::json readJsonObject(const std::string& path) {
    std::ifstream file(path, std::ios::binary);
    if (!file) {
        throw std::runtime_error("Cannot read JSON file: " + path);
    }
    nlohmann::json value = nlohmann::json::parse(file);
    if (!value.is_object()) {
        throw std::runtime_error("JSON root must be an object: " + path);
    }
    return value;
}

std::string temporaryFileInDirectory(const std::string& path) {
    std::filesystem::path parent = std::filesystem::path(path).parent_path();
    std::string dir = parent.empty() ? "." : parent.string();
    char temp[MAX_PATH] = {};
    if (!GetTempFileNameA(dir.c_str(), "2ez", 0, temp)) {
        throw std::runtime_error(win32Error("Cannot allocate temporary settings file", GetLastError()));
    }
    return temp;
}

std::string archiveDamagedFile(const std::string& path) {
    // Never overwrite an earlier damaged file: users may need it for recovery.
    for (int attempt = 0; attempt < 1000; ++attempt) {
        std::string archive = path + ".corrupt";
        if (attempt) {
            archive += "." + std::to_string(attempt);
        }
        if (fileExists(archive)) {
            continue;
        }
        if (MoveFileExA(path.c_str(), archive.c_str(), MOVEFILE_WRITE_THROUGH)) {
            return archive;
        }
        throw std::runtime_error(win32Error("Cannot preserve damaged settings file " + path, GetLastError()));
    }
    throw std::runtime_error("Too many archived damaged settings files for " + path);
}

void backupValidFile(const std::string& path) {
    std::string backupTemp = temporaryFileInDirectory(path);
    try {
        if (!CopyFileA(path.c_str(), backupTemp.c_str(), FALSE)) {
            throw std::runtime_error(win32Error("Cannot copy settings backup", GetLastError()));
        }
        if (!MoveFileExA(backupTemp.c_str(), (path + ".bak").c_str(),
                         MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)) {
            throw std::runtime_error(win32Error("Cannot replace settings backup", GetLastError()));
        }
    } catch (...) {
        DeleteFileA(backupTemp.c_str());
        throw;
    }
}
} // namespace

JsonFileLoadResult loadJsonFileSafely(
    const std::string& path, const nlohmann::json& defaults) {
    if (!fileExists(path)) {
        return {defaults, true, ""};
    }

    try {
        return {readJsonObject(path), false, ""};
    } catch (const std::exception& originalError) {
        // Preserve the unreadable original before allowing any future save.
        const std::string archive = archiveDamagedFile(path);
        const std::string backup = path + ".bak";
        if (fileExists(backup)) {
            try {
                return {readJsonObject(backup), true,
                        "Damaged settings archived at " + archive +
                        "; restored last good backup. Reason: " + originalError.what()};
            } catch (const std::exception&) {
                // Keep the invalid backup untouched for forensic inspection.
            }
        }
        return {defaults, true,
                "Damaged settings archived at " + archive +
                "; no valid backup was available, so defaults were loaded. Reason: " +
                originalError.what()};
    }
}

void saveJsonFileSafely(const std::string& path, const nlohmann::json& value) {
    if (!value.is_object()) {
        throw std::runtime_error("Refusing to save JSON settings with a non-object root: " + path);
    }

    const std::string temp = temporaryFileInDirectory(path);
    try {
        {
            std::ofstream output(temp, std::ios::binary | std::ios::trunc);
            if (!output) {
                throw std::runtime_error("Cannot open temporary settings file: " + temp);
            }
            output << value.dump(2);
            output.flush();
            if (!output) {
                throw std::runtime_error("Cannot write temporary settings file: " + temp);
            }
            output.close();
            if (!output) {
                throw std::runtime_error("Cannot close temporary settings file: " + temp);
            }
        }

        if (fileExists(path)) {
            try {
                // Only a valid current file should replace the last good backup.
                readJsonObject(path);
                backupValidFile(path);
            } catch (const nlohmann::json::exception&) {
                archiveDamagedFile(path);
            } catch (const std::runtime_error& error) {
                // If the current file is unreadable, preserve it. But do not
                // swallow backup/rename failures, which must abort the save.
                const std::string reason = error.what();
                if (reason.find("Cannot read JSON file:") == 0 ||
                    reason.find("JSON root must be an object:") == 0) {
                    archiveDamagedFile(path);
                } else {
                    throw;
                }
            }
        }

        if (!MoveFileExA(temp.c_str(), path.c_str(),
                         MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)) {
            throw std::runtime_error(win32Error("Cannot replace settings file " + path, GetLastError()));
        }
    } catch (...) {
        DeleteFileA(temp.c_str());
        throw;
    }
}
