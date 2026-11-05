# Custom songs: manifest validation and loader roadmap

> **Implemented:** an offline validator for rights-cleared custom song packs. **Not implemented:** injecting/loading songs into any EZ2DJ/EZ2AC/EZ2Dancer/Sabin game. That requires independently validated per-game adapters.

## Authoring workflow

~~~text
Original or licensed music + charts + artwork
  -> pack.json
  -> tools/songpack_validator.py
  -> validated local song library
  -> future per-game catalog / chart / asset adapter
  -> in-game song selection, audio, BGA and score identity
~~~

**No proprietary game files, commercial songs, BGAs or charts are supplied.** Only distribute your own assets or assets you have redistribution rights for.

## Pack format v1

Create a folder containing a pack.json manifest plus your audio, charts and images. Example, replace paths with files that actually exist:

~~~json
{
  "format_version": 1,
  "id": "original_songs_vol1",
  "name": "Original Compositions Vol. 1",
  "license": "CC-BY-4.0",
  "songs": [
    {
      "id": "my_first_song",
      "title": "Original Track",
      "artist": "Your Studio",
      "audio": "audio/track.ogg",
      "jacket": "images/track.png",
      "charts": [
        {"id":"track_5k_normal","mode":"5k","level":5,"file":"charts/track_5k_n.json"},
        {"id":"track_7k_hard","mode":"7k","level":10,"file":"charts/track_7k_hd.json"}
      ]
    }
  ]
}
~~~

Paths refer to real files inside your pack directory. Add optional audio_sha256 per song or sha256 per chart if you have verified SHA-256 digests. Chart data is referenced as a file; **no universal EZ2 chart conversion is performed**.

Recognized declared modes: 5k, 7k, 5k_course, 7k_course, ez2catch, turntable, dancer and other. The mode strings are metadata, not evidence any specific game revision implements them.

## Validate on a modern Python 3.10+ host

~~~powershell
python tools/songpack_validator.py "D:\MySongPacks\original_songs_vol1"
python tools/songpack_validator.py "D:\MySongPacks\original_songs_vol1" --json
~~~

The validator enforces unique IDs, required metadata, at least one chart per song, valid difficulty (1–99), allowed extensions, relative paths that do not escape the pack root, presence of referenced assets, a file-size bound and optional checksum verification. Symlink escapes are rejected.

**Non-goals:** validating audio codecs, BGA decoding, BPM/timing accuracy, lane semantics, proprietary chart formats, malware, or legal ownership. A passing pack validates manifest structure only.

## Research steps for real game support

1. Select a single exact executable revision and record its SHA-256.
2. Map song catalog loading, song counts, chart index allocation and reserved song IDs.
3. Trace resource resolution for music, preview, jacket, video/BGA and chart data.
4. Map actual chart timing, turntable/lane layouts and per-game note formats.
5. Add a safe lookup mapping for original IDs; no collisions or overwrites of shipped game entries.
6. Implement a carefully scoped resource adapter which falls back to original behavior for all unknown paths.
7. Ensure memory ownership, unload/reload behavior and score key persistence are correct.
8. Expose song.selected and chart.loaded events only after verifying live semantic game state.

**First acceptance test:** one original test song loads, plays, scores, exits and relaunches correctly on one declared, tested game build and OS configuration. No such working in-game loader is shipped yet.

## Future integration

Pack manager in UI, safe install/uninstall, per-song checksum cache, chart preview, ID collision detection, per-cabinet catalog profiles, versioned content registry and licensing/provenance metadata.

See [NEW_HOOKS.md](NEW_HOOKS.md), [EXTENSION_EVENTS.md](EXTENSION_EVENTS.md), and [SCORES_API.md](SCORES_API.md).
