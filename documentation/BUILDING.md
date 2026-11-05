# Building and release pipeline

## Requirements
Windows host; CMake **3.20+**; Git; MinGW Makefiles generator and supporting build tools; network access for dependencies. The project configures 32-bit MinGW GCC 12.2 with XP-targeted flags and C++17. If the downloaded 7z archive is not supported by CMake's archive extractor, install 7-Zip and make `7z` available on PATH.

## Build (PowerShell)

~~~powershell
git clone https://github.com/ECas95/2EZConfig_Re.git
Set-Location 2EZConfig_Re
# Work around current CMake omission: it downloads into a folder it has not created.
New-Item -ItemType Directory -Force toolchain | Out-Null
cmake --preset release
cmake --build --preset release
~~~

Debug: `cmake --preset debug` then `cmake --build --preset debug`. Expected binaries: `build/release/bin/2EZConfig.exe` and `build/release/bin/2EZ.dll` (debug equivalents under `build/debug/bin`).

**These commands were reviewed against source but not executed on a Windows build machine in this audit.** Host-specific MinGW generator configuration may also be required.

## Dependencies

| Dependency | Current reference |
| --- | --- |
| GLFW (+ local XP compatibility patch) | `3.3.10` |
| Dear ImGui | `v1.91.1` |
| nlohmann/json | `v3.11.3` |
| usb-hid-usage | floating `master` |
| MinHook | floating `master` |
| MinGW toolchain | Upstream release archive, currently without checksum verification |

The project fetches code at configure time and is not reproducible/offline by default. Pin floating dependencies to commits, verify the toolchain archive with SHA-256, provide optional local toolchain paths, and cache dependencies.

## Current GitHub Actions release behavior
The workflow `.github/workflows/release.yml` starts on every push to `master` or manual dispatch. It builds on Windows, uploads executable + DLL, and produces a date-tagged GitHub Release from Ubuntu. The release zip contains **only** these two binaries (no license files or checksum).

Recommended: introduce PR build/test jobs; release only on controlled tags; include LICENSE and third-party notices; add SHA-256 checksums and test evidence.

## Test plan
There is no dedicated automated test suite in the reviewed tree. At a minimum test: fresh/upgrade settings; malformed JSON; game detection with recognized/unknown executables; user patch override behavior; inputs/outputs; UI and skip-UI launches; 6th Trax switching; XP startup, modern Windows audio/rendering, and 60 Hz hardware behavior.

See [Roadmap](ROADMAP.md).