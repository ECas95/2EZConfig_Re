# Build, test and release guide

This guide describes the **current code in `master`**. The project is a legacy-oriented Windows C/C++ application with CMake 3.20+, a 32-bit GCC 12.2 toolchain and C++17.

## Prerequisites

- Windows build environment with CMake **3.20+**, Git and the MinGW Makefiles generator/build tools.
- Network access for the initial toolchain and FetchContent downloads (or a previously prepared compatible build cache).
- 7-Zip (`7z` on PATH) if the CMake archive extraction path does not support the toolchain 7z file.

## Build and tests (PowerShell)

```powershell
git clone https://github.com/ECas95/2EZConfig_Re.git
Set-Location 2EZConfig_Re
cmake --preset release
cmake --build --preset release
ctest --test-dir build/release --output-on-failure
```

Outputs:

```text
build/release/bin/2EZConfig.exe
build/release/bin/2EZ.dll
```

Debug: use `cmake --preset debug` and `cmake --build --preset debug`; outputs are under `build/debug/bin/`.

**The `toolchain/` directory is created automatically on a fresh checkout.** On first configure, the project's MinGW toolchain archive is downloaded from the upstream `toolchain` release, and CMake verifies the SHA-256 `d76daf7a176f6e65ff75adc26efbadba89787bb14265696b94dce302cf1f8115`. For an alternate local toolchain, CMake exposes `TOOLCHAIN_DIR`; the provided compiler directory must contain `bin/gcc.exe`, `bin/g++.exe` and the appropriate resource compiler.

## Build dependencies

| Library or tool | Reference |
| --- | --- |
| GLFW | `3.3.10` + `patches/glfw-xp-compat.patch` |
| Dear ImGui | `v1.91.1` |
| nlohmann/json | `v3.11.3` |
| usb-hid-usage | `1a9085449bacdcbf3581b2ca694c0c158c3a8085` |
| MinHook | `8af6b4acae5a9388fd742b56fa79ece89d96f823` |
| MinGW GCC 12.2 32-bit | Official upstream archive, verified by SHA-256 |

Dependencies are pinned to specific revisions, but the build still fetches source code during configure; fully offline builds are not yet a guaranteed workflow. Review dependency upgrades for Windows XP API compatibility.

## Win32 presentation helper

The Windows Release build now also produces **build/release/bin/2EZWindowMode.exe**, a separate 32-bit GUI process built with the same XP-targeted MinGW toolchain. It is required only for optional non-native window styles, and does not add runtime dependencies to the injected 2EZ.dll.

CI checks that all three binaries exist and executes a safe invalid-command-line smoke test of the helper. Release packaging includes the helper and its SHA-256 alongside 2EZConfig.exe and 2EZ.dll. Tests on real game windows, DirectDraw exclusive mode and 120 Hz monitors are still manual acceptance tasks.

## Continuous integration

The [Pull Request CI](../.github/workflows/ci.yml) workflow runs on PRs targeting `master`:

1. Validate `CMakePresets.json` and `src/resources/patches.json` syntax.
2. Configure and compile on a Windows runner.
3. Run `ctest` to exercise `settings_io_tests`.
4. Verify the EXE and DLL exist and are nonempty.
5. Upload unsigned, non-release build artifacts.

The settings tests cover first-run defaults, previous-valid-file backups, malformed JSON recovery, invalid backups, repeated corruption, and rejection of invalid JSON root types. Windows CI has passed for the implementation, but **does not validate Windows XP SP3, original arcade cabinets or every game revision**.

## Companion tools and Python tests

Optional developer tools require Python **3.10+** on a modern PC. They are not part of the XP game executable and use only Python's standard library.

~~~powershell
python -m unittest discover -s tools/tests -p 'test_*.py' -v
python tools/companion_server.py --help
python tools/songpack_validator.py --help
python tools/cabinet_profiles.py --help
~~~

Pull Request CI runs these Python tests before the Windows build, then uses CTest to check both **settings_io_tests** and **extension_events_tests**. Run the same commands after a change to the companion API or the hook event format. See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md).

## Controlled releases

The [Release workflow](../.github/workflows/release.yml) builds in Windows and publishes a GitHub Release **only for version tags** that match `vX.Y.Z` (or a suffix such as `vX.Y.Z-rc1`). Manual workflow dispatch builds artifacts without publishing unless invoked on an eligible tag.

Release ZIP contents:
- `2EZConfig.exe` and `2EZ.dll`
- `LICENSE` and `THIRD_PARTY_LICENSES`
- `SHA256SUMS.txt` for the two binaries

The ZIP has an accompanying `.zip.sha256` digest. Use the provided checksums to verify transfer integrity; they are **not a substitute for a code-signing signature**.

## Additional regression work needed

Add game-version test evidence, Windows XP SP3 physical/VM compatibility checks, HID hotplug tests, multi-instance config access tests, malformed custom patch tests and actual monitor refresh measurements. See the [roadmap](ROADMAP.md).