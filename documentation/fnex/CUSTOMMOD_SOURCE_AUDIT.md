# Private FNEX EZ2CustomMod source audit — findings for 2EZConfig_Re

This is an engineering review of the **four user-supplied private archives**. It is **not** a mirror or a legal determination about redistribution. No code from private decompilation output has been added to this repository.

## Received inventory and limits

| Archive | Entries | Main contents | What can be verified here |
| --- | ---: | --- | --- |
| src.zip | 40 | Mod-specific C++ headers/implementations, plus old backup snapshots | Entry points, configuration model, broad hook boundaries |
| decomp.zip | 10 | Several different decompiler exports and analysis metadata | Cross-reference research hypotheses; **do not copy into public fork** |
| docs.zip | 23 | User/development guides, research chapters, technical paper assets | Architectural claims, installation instructions, performance scenarios |
| tests.zip | 57 | Mostly standalone C++ tests, plus Python and XP import checks | Test design and coverage areas; **not evidence of tests run locally** |

**Not supplied:** the game executable, a compiled EZ2CustomMod release DLL, full build scripts/tool directories, its dependency bundle, a test cabinet or permission to republish the private material. We therefore cannot compile and certify the mod DLL or reproduce the research's byte-matching claims from these archives alone.

The mod source and documents call the executable **EZ2B.exe**. The current 2EZConfig_Re Final:EX game definition still defaults to **EZ2AC.exe**. This is an important per-installation mismatch to check, not a reason to globally substitute one executable without version evidence.

## Observed mod architecture

The uploaded source divides responsibilities roughly as follows:

| Private module | Described responsibility | Safe improvement in 2EZConfig_Re |
| --- | --- | --- |
| mod_main.cpp | DLL entry, initialization, import-table hooks, memory/resource guards, previews and overlay UI | External DLL readiness warning and startup compatibility plan |
| trace_hooks.cpp | Enlarged song-select pools, category/wheel support and custom Top-5 | Per-version hook/patch conflict test matrix |
| bms_scanner.cpp | BMS library scanning, caching, generated charts, assets and previews | Independent BMSData structural/asset preflight |
| config.cpp and config.h | BMSMod.ini options and memory-tier behavior | Read-only config checks; no writes to mod settings |
| audio_decode.* | External-media decode integration | Check optional codec helper dependencies and runtime timing risk |
| chart_layout.h / lane_fold.h / ln_pairing.h | Lane conversion and long-note pairing | Document mode-specific chart mapping tests |
| play_data.h / rank_redirect.h | Custom IDs, favorites and local ranking files | Preserve idmap/playdata/rank during upgrades |
| texture_ring.h / image_bga.h | Bounded in-game graphics resources | Privacy-redacted frametime/texture diagnostics |
| patch.cpp / iat.* | Signature-dependent runtime hooks and file redirection | Reject unverified builds; no new invasive hook in our fork |

These descriptions are behavioral summaries, not a transfer of code or proprietary address tables.

## Meaningful functional evidence

The research document reports:
- A source implementation of a custom BMS catalog, not merely a proposal. Song metadata, original modes, generated layouts and asset redirects require game-specific hooks.
- A tested **23,587-song** library and library-driven screen/category allocation. This is a claim from its own measurements.
- Strong Windows XP constraints: 32-bit virtual memory, GDI object exhaustion, texture reuse, background preview decoding and expensive category rebuilds.
- Song/favorite/rank identity depending on **CustomCache/idmap.txt**, making a cache deletion or folder rename potentially destructive.
- A source-level XP import compatibility test for the mod release build and many narrow C++ tests for note/timing/graphics helpers.

These findings strongly favor **interoperability with an existing maintained mod** over copying/reimplementing the private loader and duplicating its large memory-patch surface.

## Compatibility risks and test priorities

1. **Launch target:** verify the exact on-disk executable and override, especially EZ2B.exe versus EZ2AC.exe.
2. **Initialization ordering:** 2EZConfig_Re injects 2EZ.dll first and then Extra DLLs; both DLLs have independent initialization. The order cannot by itself guarantee non-conflicting signatures, patched bytes or stage startup.
3. **Patch/graphics/audio interactions:** test both modules independently and together; don't assume a private mod version is compatible with every 2EZConfig_Re patch.
4. **Persistent user data:** back up BMSMod.ini, game-settings.json, CustomCache/idmap.txt, playdata and rank data before changing hooks or libraries.
5. **Old hardware:** collect the mod's startup and frame-time metrics on real XP; check memory tier, GDI/texture failures, video preview and turntable controls.
6. **BMS structure:** prefer a small original/licensed test song, then progressively expand modes and categories; parse WAV/BMP paths read-only before copying to a cabinet.
7. **Verification:** a passing CI test for our Python preflight cannot certify the external mod DLL or the retail game build.

## Out-of-scope / privacy considerations

- No direct import of reconstructed/decompiled game source or hard-coded private memory addresses.
- No original game files, commercial songs, audio/video, license keys or private DLL binary in this repository.
- No automatic scan of an entire disk, extraction or upload of user BMS libraries.
- No automated upload of custom local Top-5 scores as verified competitive results.
- No new synchronous logging inside audio/render/input callbacks.

## Concrete contributions in this fork

- [CustomMod interoperability guide](CUSTOMMOD_INTEROP.md).
- Read-only installed DLL/config/executable preflight.
- Optional BMSData folder/keysound/BGA reference analysis.
- Privacy-safe legacy XP performance-log aggregation.
- Contextual Final:EX warning in the existing GUI.
- Synthetic Python tests under tools/tests.

## Future integration contract

If a mod maintainer permits it, define a **separate, opt-in** bridge that publishes confirmed song selections and finalized results through 2EZ.dll's existing EZ2_PublishEvent API. It must preserve player slot, game mode and chart ID and must never equate a preview/cursor event with an actual selection. It should include stable event identities, high-confidence provenance and idempotent delivery **before** any ranked server integration.

See [Extension Events](../EXTENSION_EVENTS.md), [Passive Observatory](PASSIVE_OBSERVATORY.md), and [New Hooks](../NEW_HOOKS.md). Actual runtime hooks and release compatibility remain unverified without the authorized cabinet build.
