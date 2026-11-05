#include "settings.h"
#include "settings_io.h"
#include "patch_store.h"
#include "logger.h"
#include <filesystem>

void SettingsManager::load(const std::string& gameDir, const std::string& userSettingsDir) {
    m_gameDir = gameDir;
    m_userSettingsDir = userSettingsDir;
    m_lastWarning.clear();
    m_lastError.clear();

    std::filesystem::create_directories(userSettingsDir);
    std::filesystem::create_directories(gameDir);

    const std::string gamePath = gameDir + "/game-settings.json";
    const std::string globalPath = userSettingsDir + "/global-settings.json";

    auto gameResult = loadJsonFileSafely(gamePath, {
        {"logging_enabled", false},
        {"skip_ui", false}
    });
    m_gameSettings = std::move(gameResult.value);

    auto globalResult = loadJsonFileSafely(globalPath, {
        {"button_bindings", json::object()},
        {"analog_bindings", json::object()},
        {"patch_delay_ms", 2000}
    });
    m_globalSettings = std::move(globalResult.value);

    if (!gameResult.warning.empty()) {
        m_lastWarning += gameResult.warning;
        Logger::warn("[Settings] " + gameResult.warning);
    }
    if (!globalResult.warning.empty()) {
        if (!m_lastWarning.empty()) m_lastWarning += "\n";
        m_lastWarning += globalResult.warning;
        Logger::warn("[Settings] " + globalResult.warning);
    }

    Logger::info("[Settings] Game settings: " + gamePath +
                 (gameResult.needsSave ? " (new/recovered)" : ""));
    Logger::info("[Settings] Global settings: " + globalPath +
                 (globalResult.needsSave ? " (new/recovered)" : ""));

    m_patchStore.load(userSettingsDir, m_gameDir);
    m_patchStore.loadState(m_gameSettings.value("patches", json::object()));

    if (gameResult.needsSave || globalResult.needsSave) {
        save();
    }
}

void SettingsManager::save() const {
    try {
        saveJsonFileSafely(m_gameDir + "/game-settings.json", m_gameSettings);
        saveJsonFileSafely(m_userSettingsDir + "/global-settings.json", m_globalSettings);
        m_lastError.clear();
    } catch (const std::exception& error) {
        m_lastError = std::string("Failed to save settings: ") + error.what();
        Logger::error("[Settings] " + m_lastError);
    }
}

const std::string& SettingsManager::lastError() const {
    return m_lastError;
}

const std::string& SettingsManager::lastWarning() const {
    return m_lastWarning;
}

json& SettingsManager::globalSettings() {
    return m_globalSettings;
}

json& SettingsManager::gameSettings() {
    return m_gameSettings;
}

PatchStore& SettingsManager::patchStore() {
    return m_patchStore;
}
