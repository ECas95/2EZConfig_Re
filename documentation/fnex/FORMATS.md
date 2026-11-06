# FNEX file-format observations and read-only tools

These observations are drawn from a privately supplied reverse-engineering research archive and have **not** been validated on a real EZ2AC Final:EX installation. This repository includes **no game files**; examples are synthetic and deliberately not game-compatible content.

## 1. GDS descriptors: lane order is explicit data

Research describes game mode descriptors below the game-provided system/<mode>/ directory as text files with a .gds extension. Among other sections, a descriptor may include General and Slot1/Slot2 sections. Inside each slot, NumberOfTrack tells how many logical lanes are described; each ordered Track entry includes a Key pair and a SongTrack handle.

Key finding: **the order of Track entries in the file is the logical lane order**. The numeric suffix in TrackN is a label, not a lane index. Sorting TrackN labels destroys original ordering. A Key pair can represent two controls mapped to a single lane (such as turntable directions); do not infer that every pair is a turntable.

### Synthetic sample

~~~ini
[General]
NumberOfSlot=2

[Slot1]
NumberOfTrack=2
Track8 = {
  Key=10,11
  SongTrack=5
}
Track2 = {
  Key=20,-1
  SongTrack=7
}

[Slot2]
NumberOfTrack=1
Track1 = {
  Key=30,31
  SongTrack=9
}
~~~

In this **self-authored** example, player 1 has lane 0 → SongTrack 5 and lane 1 → SongTrack 7, regardless of Track8/Track2 labeling. This sample is not copied from a commercial game's GDS file and is not a guaranteed usable stage descriptor.

### Inspect an actual user-provided descriptor

On a modern PC with Python 3.10+:

~~~powershell
python tools/gds_inspector.py examples/fnex/synthetic_mode.gds
python tools/gds_inspector.py "D:\OwnGame\system\your_mode\mode.gds" --json
~~~

The inspector reads at most 1 MiB, checks Slot declarations and counts, rejects malformed/range-invalid mappings and emits machine-readable player/lane/key/chart-track data. It does not load any game binaries, change mappings or decode proprietary charts.

### Generate a visual lane map (SVG)

You can also generate a **standalone, offline diagram** of the exact input/key-to-chart-track ordering reported by the inspector:

~~~powershell
python tools/gds_visualizer.py examples/fnex/synthetic_mode.gds --output example-lanes.svg
~~~

Open example-lanes.svg in a browser. The utility is independent of the arcade game, embeds no copyrighted assets or remote fonts, and refuses to overwrite an existing output unless --force is supplied.

Only the **Slot subset** of the full GDS grammar is parsed. Unknown game-defined sections are ignored by design, and unusual syntax may be rejected rather than guessed. Report a sanitized minimal example if a valid game-owned file uses a different syntax.

### Practical next use

Feed inspected lane mappings into a future **visual IO mapper** and custom-chart adaptation tests. Until a full per-game chart decoder exists, the number called SongTrack is only a handle: do not assume it is the physical lane, note index, song identifier or generic MIDI channel.

## 2. Local ranking file candidates

The source research separates song-specific top-five rankings from mode-wide top-99 records. Candidate file layouts observed in its reconstruction have:

| Candidate | Slots | Names | Scores | Expected total |
| --- | ---: | --- | --- | ---: |
| song_top5 | 5 | Five 8-byte legacy name fields | Five signed 32-bit little-endian scores | **60 bytes** |
| mode_top99 | 99 | Ninety-nine 8-byte legacy name fields | Ninety-nine signed 32-bit little-endian scores | **1,188 bytes** |

The game has different modes and paths, including battle/channel variants; **file names alone are not a guaranteed layout signature**. The research also describes quirks in legacy ranking-name handling. Never write these files from a generic tool or treat names as authenticated player identities.

### Read a ranking without altering it

~~~powershell
python tools/ranking_inspector.py "D:\OwnGame\sound\sample_rank.bin" --format song_top5
python tools/ranking_inspector.py "D:\OwnGame\system\ranking\sample.bin" --format mode_top99 --json
~~~

The tool:
- Rejects any byte length other than the chosen layout's exact expected size.
- Interprets signed 32-bit little-endian scores without modifying the file.
- Warns on negative scores and non-descending order.
- **Hides legacy player-name bytes by default**. Only show them with the explicit --names switch.
- Returns verified=false; observed local file contents are not proof of a genuine completed play.

### Can these rankings feed our companion server?

Eventually, yes, as **consented, historical, unverified imports**. However, top-five/top-99 files do not provide a unique authenticated play event, result timing, a validated song/chart ID or sufficient provenance for competitive score verification. Do not auto-upload or auto-promote them into ranked leaderboards.

A real score pipeline should use an exact game-version **result-finalized** hook with session identity and duplicate protection; the ranking inspector is a research/troubleshooting tool, not such a hook.

## 3. Song metadata, stage selection and chart resources

The private research reports:
- Mode selection loading configuration from the game's system/<mode>/Stage.ini and associated pools; hidden/unlock rules can change which songs are visible.
- Song metadata and per-difficulty availability stored separately from chart playback; a song list entry cannot be safely inferred from an arbitrary audio file alone.
- Mode-specific chart track mapping separate from the order of player inputs.
- Resource loading for song previews, cover/title imagery, sound samples and graphics as separate operations.
- Proprietary audio/chart/config file formats not universally self-describing.

Implication: the existing [custom-song manifest validator](../CUSTOM_SONGS.md) is **content intake**, not a universal game loader. A version-specific adapter must separately resolve catalog insertion, asset redirection, chart parsing, difficulty labels, rank IDs and safe removal/fallback.

## 4. Timing and score units: preserve provenance

The supplied research discusses musical tick timing, press processing, compensation, judgement grade thresholds, holds and different mode-specific scoring paths. Terminology varies between its historical documents (ticks per beat versus ticks per measure). We should adopt **explicit unit names and source provenance** in any future parser or timing-analysis tool, not encode a single global milliseconds conversion.

Never interpret a raw GDS SongTrack, score integer or note timestamp as a duration in milliseconds without checking its mode/version-specific representation. Timing changes must be tested with traceable synthetic charts and a named executable revision.

## 5. Future validators and visual tools

Suggested next milestones:
1. GDS compatibility corpus using user-supplied **sanitized, rights-cleared** examples.
2. Visual lane mapping over the inspector's JSON without modifying a game.
3. Chart timing inspector for supported *documented* formats, with explicit ticks per beat and BPM changes.
4. Read-only score migration preview with pseudonymization and duplicate detection.
5. Custom-song asset registry with collision checks; actual in-game loader only after exact executable compatibility tests.

See [HOOK_DESIGN.md](HOOK_DESIGN.md), [COMPATIBILITY.md](COMPATIBILITY.md), [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md).
