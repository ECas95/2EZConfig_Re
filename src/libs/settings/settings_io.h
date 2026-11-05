#pragma once

#include <nlohmann/json.hpp>
#include <string>

// A damaged main file is preserved under *.corrupt[.N], never deleted.
struct JsonFileLoadResult {
    nlohmann::json value;
    bool needsSave = false;
    std::string warning;
};

// JSON root must be an object. On corruption, archive the bad file, attempt
// to recover from <path>.bak, otherwise return defaults.
JsonFileLoadResult loadJsonFileSafely(
    const std::string& path, const nlohmann::json& defaults);

// Write a new JSON file through a unique same-directory temporary file.
// Preserve the previous valid file as <path>.bak before atomic replacement.
// Throws std::runtime_error on failed write, backup or rename.
void saveJsonFileSafely(
    const std::string& path, const nlohmann::json& value);
