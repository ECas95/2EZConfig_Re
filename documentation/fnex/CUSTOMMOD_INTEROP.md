# EZ2CustomMod and 2EZConfig_Re interoperability

> **Status:** optional third-party interoperability. This fork provides original, read-only installation checks, BMS library diagnostics, performance-log summaries and launcher warnings. It **does not** bundle or automatically install the external mod, retail game executable, reconstructed code, decryption materials or copyrighted assets.

## The source and research received

The four privately supplied archives contain source code, decompiler output, documentation and extensive tests for **EZ2CustomMod**, an independently developed DLL for EZ2AC Final:EX.

Unlike the generic custom-song pack *manifest validator* in our fork, the supplied mod contains source for an actual Final:EX BMS scanner, song-select integration, custom chart/audio/resource loading, AutoChart, user categories, local rankings, BGA previews and XP-aware performance management. Its documentation reports testing a library of **23,587 BMS songs** on an original XP cabinet. **That is the mod project's report, not an independently reproduced test by 2EZConfig_Re.**

The uploaded archives do **not** contain a compiled EZ2CustomMod.dll, a complete standalone release bundle or the retail game executable. Their private decompiler dumps and reconstructed game code **have not been copied into this public fork**. Direct source integration would require a separate permissions, licensing and provenance review.

## Dividing responsibilities

| Area | 2EZConfig_Re | EZ2CustomMod (according to uploaded source/docs) |
| --- | --- | --- |
| Launch | Game selection, executable name override and additional DLL injection | Must be loaded into its compatible Final:EX game |
| IO | Cabinet input/output and compatibility patches | Uses game controls for custom UI and lane cover |
| Custom music | Generic offline pack manifest validation | BMS scanning, virtual songs, direct chart/resource loaders and AutoChart |
| Score | Unverified companion API and local event SDK | Custom local Top-5 and playdata; not authenticated online scores |
| Performance | Diagnostics and regression tests | Own logs, frame-time tracing, resource budgeting and background work |
| Multiplayer | Local prototype lobbies, no game synchronization | No authenticated online game/match protocol demonstrated |

The mod code is a **separate project**, not a replacement for the existing launcher and IO stack.

## How startup works

~~~text
2EZConfig.exe
   -> selects Final:EX in game-settings.json
   -> checks optional Exe Name Override
   -> starts selected game suspended
   -> injects 2EZ.dll
   -> injects Extra DLLs (operator can enable EZ2CustomMod.dll)
   -> resumes game
       -> optional external mod reads BMSMod.ini, BMSData and CustomCache
~~~

The launcher injects 2EZ.dll first and then the configured extra DLLs, but initialization threads and memory hooks can still run concurrently. **Injection order is not proof of compatibility or freedom from hook conflicts.** Never load a third-party mod automatically.

### Executable-name mismatch

This fork currently defines the default Final:EX executable as **EZ2AC.exe**, while the uploaded EZ2CustomMod guide and source refer to **EZ2B.exe**. Do not assume either filename is universally correct across versions.

If you own the installation, verify the actual filename and set **Settings → Exe Name Override** manually if necessary. Our configurator now displays an optional, read-only compatibility warning when a local EZ2CustomMod file is detected and the filename deserves attention.

## Read-only installation preflight

Run on a modern system with Python 3.10+:

~~~powershell
python tools/fnex_custommod_preflight.py --game-dir "D:\Arcade\FNEX" --json
python tools/fnex_custommod_preflight.py --game-dir "D:\Arcade\FNEX" --target-os xp
~~~

The preflight checks the game ID, selected executable, 2EZ.dll, 2EZConfig.exe, presence of the optional mod DLL, the Extra DLLs setting, BMSMod.ini, directory names and dependencies mentioned in the external guide.

For media, the guide mentions ffmpeg.exe, pthreadGC2.dll and a CJK TrueType collection. It also notes a Windows XP GDI+ deployment difference. **No external DLLs, fonts or media programs are redistributed here**; obtain them from legitimate sources and respect their licenses.

When a persistent CustomCache/idmap.txt is found, the tool highlights it as a valuable backup target. The supplied mod documentation explains that renumbering this file can orphan custom song favorites and rankings.

The result is a **structure/configuration check**, not a cryptographic verification of the DLL's origin, exact executable memory signatures, or actual cabinet functionality.

## Validating a BMS library

EZ2CustomMod expects this structure under the configured BMSData root:

~~~text
BMSData/
  5KeyMix/
    Original Pack/
      Original Song/
        normal.bms
        hard.bme
        sound/snare.wav
        jacket.png
~~~

Folders are **mode / category / song**. Charts reside directly in the song directory. Sounds may reside in a local sound subfolder. Accepted modes include 5KeyMix, 5KeyOnly, StreetMix, 7KeyMix, ClubMix, SpaceMix, RubyMix, Ez2Catch, TurnTable and CV2Mix, plus selected aliases.

~~~powershell
python tools/fnex_bms_library_check.py "D:\Arcade\FNEX\BMSData"
python tools/fnex_bms_library_check.py "D:\Arcade\FNEX\BMSData" --check-assets --json
~~~

This independent utility checks path hierarchy, known mode names, missing charts, empty and large categories, symlinks, traversal, Windows-style case-insensitive filenames and optional WAV/BMP declarations.

It reports warnings rather than asserting chart playability. **This is not a complete BMS parser**: it does not resolve all conditional branches, validate note timing, decode video/audio or prove that the songs may legally be redistributed. Missing declared assets may be unused by the chosen random branch. Scanning is bounded to 40,000 songs, 150,000 charts, 4 MiB per chart and 150 displayed issue records.

## Diagnosing XP performance and resource issues

The external research documents the impact of very large libraries on XP: category-changing delays, blocking audio previews, GDI/texture exhaustion and the importance of bounded graphics resources and background workers.

~~~powershell
python tools/fnex_custommod_log_report.py "D:\Arcade\FNEX\logs\EZ2CustomMod.log" --json
~~~

The report summarizes frame-time samples, maximum slow frame, memory tier, mod version, render/texture failures, truncation and diagnostic tag counts. It deliberately **does not include raw log lines, song titles or player identifiers**. It analyzes files up to 32 MiB, offline.

For low-end cabinets the external guide suggests reducing PreviewFps in BMSMod.ini after reviewing cabinet logs. Avoid applying undocumented timing or performance patches directly to game memory.

## Future cooperation with our event SDK

2EZ.dll already exposes **EZ2_PublishEvent(eventName, jsonObjectPayload)**, an opt-in local JSONL interface. The uploaded external mod source does **not** currently show calls to this export.

With the external maintainer's consent, a separately maintained adapter could publish after **confirmed song selection** and **finalized score state**, with stable song/chart IDs, session IDs and explicit provenance. Publishing must remain optional and must not stall audio, input or game rendering.

Until such an integration is built and verified on the exact game revision, this fork **does not automatically obtain real Final:EX selections or scores**, and its local score database does not certify real arcade performance. Multiplayer remains a prototype coordinator.

See [Extension Events](../EXTENSION_EVENTS.md), [Scores API](../SCORES_API.md), [Multiplayer](../MULTIPLAYER.md) and [Passive Observatory](PASSIVE_OBSERVATORY.md).

## Safe deployment and regression checklist

1. Back up all game settings and persistent CustomCache/idmap.txt, playdata and rank data. Never clear caches indiscriminately.
2. Identify the exact, legally obtained game build, its real executable filename and file fingerprint.
3. Use a separately trusted, version-compatible mod DLL. Enable it explicitly through Extra DLLs.
4. Confirm a small library of self-authored/authorized BMS charts with the preflight tools.
5. Compare normal game startup with and without the external mod; inspect both projects' logs for memory and hook conflicts.
6. Test buttons, turntable, audio, BGA, result screens and category transitions on the actual XP machine.
7. Only then scale library size and consider an opt-in event adapter.

CI for this fork exercises synthetic fixtures and its own 32-bit Windows build. **The uploaded external DLL is not built or executed in this PR**, and real XP/cabinet compatibility remains unverified.

## Source/privacy policy

The uploaded material includes private reverse-engineering notes and decompiler output. It should not be mirrored publicly merely because it was shared for evaluation. This guide presents high-level facts and **independently authored** utilities. Direct code incorporation would need an explicit authorization and rights review.
