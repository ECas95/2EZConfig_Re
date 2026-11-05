# Building and release pipeline

## Requirements
Windows host; CMake **3.20+**; Git; MinGW Makefiles generator and supporting build tools; network access for dependencies. The project configures 32-bit MinGW GCC 12.2 with XP-targeted flags and C++17. If the downloaded 7z archive is not supported by CMake's archive extractor, install 7-Zip and make `7z` available on PATH.

## Build (PowerShell)

~~~powershell
git clone https://github.com/ECas95/2EZConfig_Re.git
Set-Location 2EZConfig_Re
# Backward-compatible workaround for upstream revisions before PR #2.
New-Item -ItemType Directory -Force toolchain | Out-Null
cmake --preset release
cmake --build --preset release
~~~

Debug: `cmake --preset debug` then `cmake --build --preset debug`. Expected binaries: `build/release/bin/2EZConfig.exe` and `build/release/bin/2EZ.dll` (debug equivalents under `build/debug/bin`).

**Build validation:** [PR #2](https://github.com/ECas95/2EZConfig_Re/pull/2) passed a clean Windows GitHub Actions build. The manual folder-creation workaround is no longer needed once that PR is integrated. XP cabinets and additional Windows versions still require separate verification.

## Dependencies

| Dependency | Current reference |
| --- | --- |
| GLFW (+ local XP compatibility patch) | `3.3.10` |
| Dear ImGui | `v1.91.1` |
| nlohmann/json | `v3.11.3` |
| usb-hid-usage | floating `master` in original code; pinned commit in PR #2 |
| MinHook | floating `master` in original code; pinned commit in PR #2 |
| MinGW toolchain | Upstream release archive; PR #2 checks the release's SHA-256 digest |

The original build fetches code at configure time. [PR #2](https://github.com/ECas95/2EZConfig_Re/pull/2) pins floating dependencies and verifies the toolchain archive; full offline build support and hardware regression tests remain future work.

## Current GitHub Actions release behavior
In the original workflow, every push to `master` triggers a dated GitHub Release containing only the two binaries. [PR #4](https://github.com/ECas95/2EZConfig_Re/pull/4) proposes controlled version tags, bundled notices and SHA-256 checksums. Consult the merged workflow version before publishing.

[PR #2](https://github.com/ECas95/2EZConfig_Re/pull/2) adds PR build validation; [PR #3](https://github.com/ECas95/2EZConfig_Re/pull/3) adds settings recovery tests; [PR #4](https://github.com/ECas95/2EZConfig_Re/pull/4) changes release packaging. These must be merged and validated before they are treated as capabilities of `master`.

## Test plan
The original reviewed tree contained no dedicated test suite. PR #3 adds CTest coverage for JSON settings; other coverage remains pending. At a minimum test: fresh/upgrade settings; malformed JSON; game detection with recognized/unknown executables; user patch override behavior; inputs/outputs; UI and skip-UI launches; 6th Trax switching; XP startup, modern Windows audio/rendering, and 60 Hz hardware behavior.

See [Roadmap](ROADMAP.md).