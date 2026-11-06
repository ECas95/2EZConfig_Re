#include "display_refresh.h"
#include <cstdio>

int main() {
    // These are guaranteed-invalid requests: guard must fail without
    // changing the system display mode or requiring special GPU hardware.
    if (ez2DisplayModeSupportsRefresh(0, 480, 32, 120)) return 1;
    if (ez2DisplayModeSupportsRefresh(640, 0, 32, 120)) return 2;
    if (ez2DisplayModeSupportsRefresh(640, 480, 32, 0)) return 3;
    std::puts("display_refresh: invalid requests rejected; no video mode changed");
    return 0;
}
