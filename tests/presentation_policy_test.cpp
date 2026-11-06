#include "presentation_policy.h"
#include <cstdio>

int main() {
    // All legacy game renderers remain unverified until tested with a
    // genuine DirectDraw NORMAL cooperative level and matching surfaces.
    const char* games[] = {
        "ez2ac_fn_ex", "ez2ac_fn", "ez2ac_nt",
        "ez2dj_1st_se", "ez2dj_2nd", "ez2dancer_1st", "3s_rb"
    };
    const char* unsafeModes[] = {
        "windowed", "borderless", "borderless_fullscreen", "draggable"
    };
    for (const char* game : games) {
        if (PresentationPolicy::isWindowRestyleCertified(game)) return 1;
        for (const char* mode : unsafeModes) {
            if (PresentationPolicy::shouldLaunchWindowHelper(game, mode)) return 2;
        }
        if (PresentationPolicy::shouldLaunchWindowHelper(game, "native")) return 3;
        if (PresentationPolicy::shouldLaunchWindowHelper(game, "unexpected")) return 4;
    }
    std::puts("No unverified game can be restyled by the window helper.");
    return 0;
}
