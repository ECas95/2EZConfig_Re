#include "startup_diagnostic_policy.h"
#include <cstdio>

int main() {
    using namespace StartupDiagnosticPolicy;
    for (const char* mode : {"normal", "", "unrecognized"}) {
        if (minimal(mode) || !optionalAudioEnabled(mode) || !earlyPatchesEnabled(mode) ||
            !versionPatchEnabled(mode) || !normalPatchesEnabled(mode)) return 1;
        if (!ioAndHardlockEnabled(mode) || !superEarlyPatchesEnabled(mode)) return 2;
    }
    if (!minimal("minimal") || optionalAudioEnabled("minimal") ||
        earlyPatchesEnabled("minimal") || versionPatchEnabled("minimal") ||
        normalPatchesEnabled("minimal")) return 3;
    if (!ioAndHardlockEnabled("minimal") || !superEarlyPatchesEnabled("minimal")) return 4;
    std::puts("Minimal startup disables only optional modules; required IO retained.");
    return 0;
}
