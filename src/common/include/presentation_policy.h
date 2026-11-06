#pragma once

#include <string>

// Window restyling is not a conversion from DirectDraw EXCLUSIVE to NORMAL.
// Do not attempt to restyle unverified game renderers: a failure can terminate
// the game during surface/device initialization. An explicit allowlist must be
// added here only after a tested game build proves it can render windowed
// without external graphics wrappers, patches or translation layers.
namespace PresentationPolicy {

inline bool isWindowRestyleCertified(const std::string& gameId) {
    (void)gameId;
    // No 2EZDJ/2EZAC/EZ2Dancer/SabinSS build has passed this validation yet.
    return false;
}

inline bool shouldLaunchWindowHelper(const std::string& gameId,
                                     const std::string& requestedMode) {
    if (requestedMode == "native" || requestedMode.empty()) return false;
    if (requestedMode != "windowed" && requestedMode != "borderless" &&
        requestedMode != "borderless_fullscreen" &&
        requestedMode != "draggable") return false;
    return isWindowRestyleCertified(gameId);
}

} // namespace PresentationPolicy
