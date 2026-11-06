# Research source crosswalk (metadata only)

This guide identifies **where the user-supplied private research package recorded each behavioral finding** and which component in 2EZConfig_Re can use it. It does not redistribute its reconstructed C/C++ source or disassembly.

The original package's paths below are **research pointers**. They are *not* bundled in this repository. All claims should be retested against a user's exact, authorized Final:EX executable before shipping live game hooks.

| Private reference location | Question answered | Relevant 2EZConfig_Re target | Confidence and current limit |
| --- | --- | --- | --- |
| docs/PACKAGE-OVERVIEW.md, docs/DONE-CRITERIA.md | Coverage and goals of the private reconstruction | This research overview | Self-reported research metrics; not rerun without target/toolchain |
| docs/gds-slots.md | How mode descriptors map Key pairs and SongTrack handles to ordered lanes | tools/gds_inspector.py, tools/gds_visualizer.py | Structural design supported by research; tested only with synthetic GDS |
| src/songinfo.cpp | Song record lookup and difficulty metadata | Future song selected observer; pack manifest validation | Depends on correct game build and mode |
| src/songselectctor.cpp | Stage.ini, selection pools, hidden/unlock handling and preview assets | Future catalog adapter, custom-song work | No live adapter implemented |
| src/ezchart.cpp, include/ezchart.h | Chart object, timing rescaling, lane searches and sample associations | Future chart parser/validator | Does not define a generic commercial chart format |
| src/ksongplayerbase.cpp, include/ksongplayer.h | Music clock and keysound playback separation | Future timing observability | Thread timing and unit conversions need live verification |
| docs/judge-timing.md, src/judge*.cpp | Note judgement and timing compensation | Proposed read-only latency/timing trace | Historical unit labels require reconciliation |
| docs/PORT-DELTAS.md, src/holdtick.cpp | Mode-specific hold-note/scoring differences | Score normalization test matrix | Must distinguish keys and catch paths |
| include/scorekeeper.h, src/scorerank.cpp | Score aggregation and grade state | Future score.observed finalized hook | In-flight counters are not certified final scores |
| src/resultrank.cpp, src/rankingctor.cpp | Local rankings and record-size candidates | tools/ranking_inspector.py | Read-only 5/99 candidate layouts; not authenticated |
| src/ez2dj*.cpp, src/testinput.cpp | Input and operator-test paths | Existing HID/arcade I/O diagnostics | Do not replace original port IO handlers without board tests |
| docs/PORTING.md, docs/PORT-ROADMAP.md | Component seams, dependencies and future port work | Adapter priorities and implementation plan | Some historical statistics predate completion criteria |

## Internal documentation conflicts to investigate

- **Completion metrics:** the package's final audit describes complete annotated coverage and roughly 96% matching accuracy, while older porting notes describe a much smaller measured implementation fraction at that earlier date. These measure different things and are not proof a compiled, working port is included.
- **Tick naming:** some documents express timing in beats, while others use measure units; these can differ by a factor of four. Do not copy one conversion constant into new production code without chart-tempo and replay confirmation.
- **Unpacked vs retail executable:** the reccmp target is an unpacked reference image. Its checksum must not be treated as the SHA-256 of the originally distributed encrypted executable.
- **Source inventory vs package contents:** some top-level overview text refers to separate port/card-reader trees. Those directories are **not** present in the supplied ZIP. Do not claim the missing port or companion works here.
- **File-backed ranks vs game events:** stored top-five/top-99 entries do not necessarily represent single authenticated completed sessions, especially in two-player/battle modes.

## What would improve confidence

Collect self-authored tests for the data contract first, then operator-owned, read-only file observations. For runtime hooks, require an authorized exact file fingerprint, verified memory signature, safe failure path, and repeatable hardware evidence. No private executable, copyright assets or full memory dump should be posted to GitHub.

See [COMPATIBILITY.md](COMPATIBILITY.md), [HOOK_DESIGN.md](HOOK_DESIGN.md) and [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md).
