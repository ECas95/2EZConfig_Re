# Developer guide and verification matrix

## Scope and project philosophy

This is a Windows XP-targeted x86/C++17 arcade configuration and hooking project. Compatibility must be based on **an exact game executable build, expected machine behavior and recorded tests**, not names alone. Never treat unknown memory offsets or a matching file name as proof of safe patching.

Architectural details: [ARCHITECTURE.md](ARCHITECTURE.md), [NEW_HOOKS.md](NEW_HOOKS.md), [EXTENSION_EVENTS.md](EXTENSION_EVENTS.md).

## Local build (Windows)

Requires CMake 3.20+, Git and an appropriate MinGW Makefiles build environment. The versioned compiler archive is checked against its upstream SHA-256 and dependencies are pinned.

~~~powershell
cmake --preset release
cmake --build --preset release
ctest --test-dir build/release --output-on-failure
~~~

Expected outputs: build/release/bin/2EZConfig.exe and build/release/bin/2EZ.dll.

## Optional Python tools (3.10+ modern host)

All companion tools currently use the standard library only:

~~~powershell
python -m unittest discover -s tools/tests -p 'test_*.py' -v
python tools/companion_server.py --help
python tools/songpack_validator.py --help
python tools/cabinet_profiles.py --help
python tools/event_bridge.py --help
~~~

The companion server's HTTP tests bind only to localhost. They use temporary SQLite files and do not need game assets or arcades.

## How the CI runs

A pull request to master starts:

1. JSON syntax validation of CMakePresets.json and bundled patches.json.
2. Python regression tests for the companion API, lobby states, song manifest paths and profiles.
3. Windows CMake configure + Release build using the verified toolchain.
4. CTest for settings recovery and local extension event JSONL.
5. Verification of EXE/DLL presence and upload of unsigned build artifacts.

**CI success is not a release** and is not verification of Windows XP or real games. Tagged releases are built through a separate workflow.

## Final:EX research utilities

~~~powershell
python tools/gds_inspector.py examples/fnex/synthetic_mode.gds --json
python tools/gds_visualizer.py examples/fnex/synthetic_mode.gds --output preview_lanes.svg
python tools/adapter_compatibility.py --exe "D:\OwnGame\EZ2AC.exe" --manifest examples/fnex/adapter-registry.example.json --json
~~~

The adapter registry's checksum is intentionally fake. These tools cannot install hooks or verify an actual retail executable, and no original game data is included. Unit tests in tools/tests/test_fnex_research_tools.py exercise only synthetic fixtures. See [Final:EX compatibility and evidence levels](fnex/COMPATIBILITY.md) and the [source crosswalk](fnex/SOURCE_MAP.md).

## Final:EX offline event observatory smoke tests

~~~powershell
python tools/fnex_mode_inventory.py examples/fnex --json
python tools/fnex_trace_replay.py --input examples/fnex/synthetic_observations.jsonl --output synthetic_events.jsonl --json
python tools/event_bridge.py --file synthetic_events.jsonl
~~~

The trace file is an original fixture; it does not originate from a cabinet. The replay rejects results without a started stage, ignores preview selections, prevents duplicate finalized results and flags every record synthetic/unverified. Do not merge this into ranked online score ingestion without a verified game adapter and independent player authentication.

Tests: tools/tests/test_fnex_observatory.py. Detailed guide: [PASSIVE_OBSERVATORY.md](fnex/PASSIVE_OBSERVATORY.md).

## Modern Windows and score service checks

Run the read-only compatibility tool against your own authorized game folder on a modern helper PC:

~~~powershell
python tools/compatibility_doctor.py --game-dir "D:\Arcade\EZ2" --json
python -m unittest discover -s tools/tests -p 'test_compatibility_doctor.py' -v
python -m unittest discover -s tools/tests -p 'test_companion_server.py' -v
~~~

The Python suite uses synthetic executable headers; it cannot certify a real game or graphics/audio performance. The Windows CI now exercises the compatibility and score tests as well as the existing CMake/CTest build. The score tests cover same-ID retries, concurrent submissions, per-player PBs and unverified stats.

New product context: [Modernization Strategy](MODERNIZATION_STRATEGY.md), [Compatibility Doctor](COMPATIBILITY_DOCTOR.md) and [Global Rankings](GLOBAL_RANKINGS.md).

## Display and FPS regression requirements

New **2EZWindowMode.exe** follows the game PID and restyles a top-level window only after injection and process resume; no new gameplay-memory hook is created. The default Native mode never launches the helper. Test Windowed, centered Borderless, Borderless Fullscreen and Ctrl+Alt+left-drag with a controlled synthetic Win32 app and real supported builds, especially when DirectDraw exclusive cooperative mode is active.

DirectDraw4/7 display_refresh_hz can request 0 (game default), 60 or 120. The 120 path compares Windows primary-adapter mode enumeration and otherwise preserves the original rate. This is only display refresh, **not actual game FPS**. A 120-FPS gameplay unlock requires separate timing/judgement/audio/frame evidence and is explicitly outside the implemented patch.

Native POINT texture sampling remains separate from shaders; there is no built-in postprocess backend. See [Presentation Modes](PRESENTATION_MODES.md).

## Minimum regression matrix

| Area | Positive case | Failure case | Evidence required |
| --- | --- | --- | --- |
| Settings | Save and reload valid game/global files | Corrupt main, corrupt backup, unwritable directory | CI CTest + manual Windows check |
| HID | Press/release inputs and move axes | Disconnect device or unknown caps | Synthetic tests + hardware |
| Display/audio | Expected modes and audio backends | Unsupported mode, no WASAPI on XP | Game/build/OS screenshots and logs |
| Existing game patch | Verified pattern and known target | Nonmatching pattern or mismatched revision | Mock tests and controlled hardware |
| Event spool | Enabled, valid JSON object and known game ID | Disabled, invalid JSON, file permission failure | CTest and log inspection |
| Score API | Known chart ID and score stored locally | Invalid score, unknown identifiers, malformed JSON | Python HTTP tests |
| Multiplayer | Two ready players, valid host, submitted scores | Full lobby, duplicate finish, wrong host | Python HTTP tests |
| Custom songs | Original test manifest passes | Traversal, symlink escape, hash mismatch | Python validator tests |
| Profiles | Export, diff, dry run and explicit apply | Corrupt JSON or unsafe override | Python tests and backup inspection |
| Actual custom-song hook | Original chart plays on a specified game build | Missing asset, wrong checksum, unsupported version | **Not yet implemented/tested** |
| Actual results hook | One event for a completed, verified song | Duplicate, crash, premature results, invalid score | **Not yet implemented/tested** |
| Actual networked gameplay | Matching chart sessions on two cabinets | Latency, reconnect, timing drift | **Not yet implemented/tested** |

## Writing a game adapter

- Keep one adapter per exact executable fingerprint and game family.
- Document inputs, expected original bytes, safe fallback and state machine.
- Prefer observing an authoritative semantic transition over polling untrusted memory.
- Do not block graphics, audio or input callbacks with network/file IO.
- Publish small events through the existing C ABI only after verifying a stable gameplay point.
- Feature toggles must fail open, and a missing DLL, missing config or offline companion must not block normal play.
- Build synthetic fixtures for new result/chart hooks; preserve release asset rights.

## Community contribution checklist

Before opening a PR:
- Explain which game/build/OS/hardware is covered and which remains untested.
- Add a focused unit test, fixture or safe reproduction path.
- Verify no paid/copyrighted song/asset is included without rights.
- Do not introduce plaintext secrets, hidden network connections, third-party telemetry or automatic uploads.
- Preserve upstream GPL-3.0-or-later and third-party notices.
- Update user docs, changelog and compatibility matrix if behavior changes.

See [CONTRIBUTING.md](../CONTRIBUTING.md), [SECURITY.md](../SECURITY.md) and [ROADMAP.md](ROADMAP.md).
