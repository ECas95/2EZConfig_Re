# Self-authored Final:EX research fixtures

All example data in this directory is **synthetic**. It does not come from a commercial game, is not a chart/audio file, and is not intended to be installed into a cabinet.

## Validate the sample GDS lane order

~~~powershell
python tools/gds_inspector.py examples/fnex/synthetic_mode.gds
python tools/gds_inspector.py examples/fnex/synthetic_mode.gds --json
~~~

Expected in Slot1: Track8 is **lane 0**, mapped to SongTrack 5; Track2 is **lane 1**, mapped to SongTrack 7. The suffixes of the TrackN labels are not lane indices.

## Visual lane map

~~~powershell
python tools/gds_visualizer.py examples/fnex/synthetic_mode.gds --output synthetic_lanes.svg
~~~

The SVG is self-contained and uses original drawing code; it does not contain artwork from any commercial game.

## Exact executable compatibility checker

~~~powershell
python tools/adapter_compatibility.py --exe "D:\OwnGame\EZ2AC.exe" --manifest examples/fnex/adapter-registry.example.json --json
~~~

The registry contains a **deliberately fake all-zero hash** and should never match a real executable. It installs no hooks. Replace the fake hash only after verifying the *exact on-disk build* you are allowed to run, then test the adapter's in-memory target bytes separately. A hash of an unpacked/reconstructed research image **cannot replace** the original on-disk hash.

## Synthetic ranking file

For testing the ranking inspector, generate a small file yourself:

~~~powershell
python -c "import struct,pathlib; pathlib.Path('synthetic_rank.bin').write_bytes(bytes(5*8)+struct.pack('<5i', 500,400,300,200,100))"
python tools/ranking_inspector.py synthetic_rank.bin --format song_top5 --json
~~~

This writes only **synthetic test data to your working directory**. You can delete synthetic_rank.bin afterward. The inspector never writes or uploads ranking files.

See [research overview](../../documentation/fnex/README.md), [formats](../../documentation/fnex/FORMATS.md) and [compatibility](../../documentation/fnex/COMPATIBILITY.md).
