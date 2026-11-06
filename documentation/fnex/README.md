# EZ2AC Final:EX research integration

This section maps a **user-supplied, privately shared decompilation/reverse-engineering package** into practical, original development tasks for 2EZConfig_Re.

**Status:** source-level research and synthetic tests. This does **not** establish that the original game executable, encrypted files, every Final:EX revision, or cabinet hardware has been independently verified by this fork. No reconstructed game source, protected assets, binary dumps, license information, disassembly bytes, or private research scripts are imported into this public repository.

## What was examined

The supplied ZIP has 405 archive entries, including 247 game C++ implementation files and 44 C/C++ headers, plus a test harness, reccmp project metadata, decompilation notes and porting/design notes. Its documentation calls the matching target **EZ2AC_UNPACKED** and describes an executable image not shipped in the package.

**Important provenance caution:** the ZIP filename identifies Final:EX, and the internal research mentions Final:EX, but the supplied package does not include a retail executable or independent build-fingerprint evidence allowing us to equate its **unpacked-image** hash with a **retail on-disk** EZ2AC.exe hash. The current game selection ID in our code is **ez2ac_fn_ex**. Every runtime adapter must still check a separately acquired, exact on-disk file version and its verified in-memory target bytes before installing any hook.

The reference project's own completion criteria describe a reconstructed/annotated source inventory with approximately 96% matching accuracy by its tool's metric. Those **are research project claims**, not measurements rerun here; the target executable/toolchain are not included. A separate historical porting document contains older progress percentages and should not be interpreted as the project's final status.

## Findings usable by our fork

| Source area in private research | Relevant insight | Our reusable work |
| --- | --- | --- |
| Game mode descriptors | Mode-specific GDS Slot sections explicitly define lane order and input-to-song-track mappings; TrackN labels are not lane indices | Implemented read-only [GDS inspector](FORMATS.md) and synthetic tests |
| Song table and song selection | Song metadata, difficulty availability, category/stage rules and asset resolution are separate steps | [Song-selected adapter plan](HOOK_DESIGN.md), stronger custom-song manifest flow |
| Chart reader and judgement | Chart ticks, lane semantics, hold-note rules and judgement windows are mode-dependent, not generic fixed milliseconds | [Timing/score safety notes](HOOK_DESIGN.md) and phase-specific test requirements |
| Results and rankings | Local rankings use file-backed structures; result-score finalization is distinct from ongoing frame updates | Read-only [ranking inspector](FORMATS.md); future score event hook design |
| Cabinet IO | Original game has input translation and a cabinet IO branch, while the fork already exposes HID/keyboard/port emulation | Preserve existing I/O; collect diagnostics rather than replacing known-working hooks |
| Graphics and audio | Rendering, resource loads, sound playback and timing run through separable subsystems | Future guarded instrumentation, no new detours until per-build verification |
| Multiplayer | Existing game supports local two-player scoring modes, but source does not prove a network-multiplayer protocol | Use companion **asynchronous** score challenges first; actual synchronized gameplay remains research |

## Files added to 2EZConfig_Re

| File | Status | Purpose |
| --- | --- | --- |
| tools/gds_inspector.py | Implemented, read-only | Inspect GDS Slot order, Key pairs and SongTrack mappings |
| tools/gds_visualizer.py | Implemented, offline | Render parsed mode mappings as self-contained SVG lane diagrams |
| tools/ranking_inspector.py | Implemented, read-only | Inspect candidate 5- and 99-entry local ranking layouts without writing files |
| tools/adapter_compatibility.py | Implemented, offline | SHA-256 exact on-disk executable preflight against a separate adapter manifest |
| tools/tests/test_fnex_research_tools.py | Implemented | Synthetic fixtures, negative-path and privacy tests |
| examples/fnex/ | Self-authored examples | Safe practice files and an illustrative adapter registry |

These tools do **not** activate new game hooks. They only prepare the information needed to implement safe adapters.

## Detailed references

- [Formats and use cases](FORMATS.md) — GDS mapping, ranking metadata, commands and boundaries.
- [Game architecture and hook opportunities](HOOK_DESIGN.md) — song-selection, scoring, audio, charts, latency and multiplayer integration points.
- [Compatibility and research verification](COMPATIBILITY.md) — exact build checks, no-asset policy, CI and cabinet test matrix.
- [Actionable integration plan](INTEGRATION_PLAN.md) — what to implement next and measurable acceptance criteria.

General project resources: [custom songs](../CUSTOM_SONGS.md), [event SDK](../EXTENSION_EVENTS.md), [local scores](../SCORES_API.md), [multiplayer](../MULTIPLAYER.md), [technical roadmap](../ROADMAP.md).

## Distribution and trust

The supplied research package explicitly describes itself as private and warns that reconstructed game source can raise copyright and licensing questions despite its own GPL file. **Do not copy it wholesale into this public fork.** The work committed here consists of independently authored validation tools, synthetic data, and high-level compatibility findings. Redistribution of extracted/reconstructed code or specific private artifacts requires a separate rights/provenance review.

The project supports legitimate preservation research and modding of games the user is authorized to run. It does not distribute game binaries, media, protected decryption materials or third-party server credentials. Nothing in these guides requires bypassing license checks.
