#pragma once
#include <string>

// Opt-in startup isolation for diagnostic comparisons only.
// This never bypasses game IO, its hardlock emulator or the required
// super-early patch pass. It skips OPTIONAL audio enhancements and the
// early/late patch passes, which may also be required by a specific game.
namespace StartupDiagnosticPolicy {
inline bool minimal(const std::string& mode) { return mode == "minimal"; }
inline bool optionalAudioEnabled(const std::string& mode) { return !minimal(mode); }
inline bool earlyPatchesEnabled(const std::string& mode) { return !minimal(mode); }
inline bool versionPatchEnabled(const std::string& mode) { return !minimal(mode); }
inline bool normalPatchesEnabled(const std::string& mode) { return !minimal(mode); }
inline bool ioAndHardlockEnabled(const std::string&) { return true; }
inline bool superEarlyPatchesEnabled(const std::string&) { return true; }
}
