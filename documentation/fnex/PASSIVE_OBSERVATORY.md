# Final:EX Passive Observatory v1

**Project phase:** offline observation and deterministic state-machine testing. This component **does not attach to EZ2AC.exe, install hooks, read live memory, decrypt charts or prove any arcade score**. Its output is explicitly synthetic/unverified.

This milestone builds on the private Final:EX research reviewed in [SOURCE_MAP.md](SOURCE_MAP.md) and the existing [Extension Event SDK](../EXTENSION_EVENTS.md). We can test event semantics, mode mappings and ranking changes **without endangering a cabinet or relying on unverifiable offsets**.

## What is actually implemented

| Component | Input | Output | Behavior |
| --- | --- | --- | --- |
| Mode inventory | User-supplied directory containing GDS files | JSON or terminal summary | Enumerate modes, logical lanes, Key pairs and SongTrack order; warn about collisions |
| Trace replay | Synthetic/author-created JSONL sequence of observations | NEW event JSONL file | Enforce confirmed selection → stage → finalized results → end lifecycle |
| Ranking snapshot diff | Two copies of one supported ranking layout | Redacted numeric changes | Detect changed numeric entries; never infer authenticated plays |
| Existing event bridge | Extension event JSONL | Preview or manually forwarded event viewer | Dry-run default; never creates leaderboard entries |

All commands use **Python 3.10+ on a modern computer**. Original game files and Windows XP are not needed for synthetic tests.

## 1. Inspect a mode directory

A GDS defines a mode's key and chart-track layout. Even a Track8 label can correspond to logical lane 0 if it appears first in the file. The inspector preserves **file order**, not the numeric suffix.

~~~powershell
python tools/fnex_mode_inventory.py examples/fnex --json
python tools/fnex_mode_inventory.py "D:\OwnGame\system"
~~~

The report contains mode/descriptor basenames, slot numbers, Key pairs, track IDs and collision warnings. It does not read game executables, extract media, include entire local paths or alter any source files. Conflicting SongTrack/Key entries are **warnings only** until an original IO implementation confirms their meaning.

Safety bounds: maximum 128 GDS files, five nested path components and the GDS parser's one-megabyte-per-file limit; symlinked paths are rejected. Point the tool at the **mode descriptor directory**, not an entire hard drive. For a single descriptor, continue using the [GDS inspector and SVG mapper](FORMATS.md).

## 2. Rehearse song and score events without game memory

The trace replay tool models artificial observations created by a developer, not automatically observed gameplay.

~~~text
song.preview (zero or more)  -> no event
song.confirmed              -> song.selected (deduplicated)
stage.started               -> no emitted event
result.finalized (P1/P2)    -> score.observed (one per player)
stage.ended                 -> session.ended (result_count included)
~~~

### Input observation JSONL

Each line is one object:

| type | Required fields | Rule |
| --- | --- | --- |
| song.preview | song_id, chart_id | Never emitted as a confirmed selection |
| song.confirmed | song_id, chart_id | Duplicate confirmation before start is ignored |
| stage.started | none | Requires a confirmed selection |
| result.finalized | player_slot (1 or 2), score, clear_type | Requires active stage; at most one final result per player |
| stage.ended | reason | Requires active stage; completed, failed, aborted or interrupted |

Valid clear_type strings: unknown, failed, clear, full_combo and perfect. Scores are bounded integers between 0 and 1,000,000,000; IDs use the companion's restricted ASCII identifier rules.

The fixture [synthetic_observations.jsonl](../../examples/fnex/synthetic_observations.jsonl) simulates previewing a track, confirming another track and finishing a two-player stage.

### Produce a new local event spool

~~~powershell
python tools/fnex_trace_replay.py --input examples/fnex/synthetic_observations.jsonl --output synthetic_events.jsonl --json
~~~

Output is compatible with the existing extension SDK:
- game_id = ez2ac_fn_ex
- event = song.selected, score.observed or session.ended
- schema_version = 1 with a UTC timestamp and a small data object
- synthetic = true, verified = false, origin = offline_fixture_replay
- Deterministic session IDs based on the fixture digest and confirmation sequence

The command never overwrites an existing output. The entire trace is validated before writing; no game executable, protected files or memory are accessed. No score is fabricated from previews, interim observations or an unfinished stage.

To preview these events **without networking**:

~~~powershell
python tools/event_bridge.py --file synthetic_events.jsonl
~~~

The bridge only transmits when manually invoked with --send; even then the companion receives them as events in the **local viewer**, not as SQLite ranked scores. Never present fixture events as genuine achievements; the session IDs do not authenticate a cabinet or player.

## 3. Compare historical ranking snapshots

Two read-only candidates from the research are 60-byte song top-five and 1,188-byte mode top-99 layouts. The snapshot diff compares numeric scores across **two copies**:

~~~powershell
python tools/fnex_ranking_diff.py --before "D:\Backup\before.bin" --after "D:\Backup\after.bin" --format song_top5 --json
~~~

Output includes SHA-256 fingerprints and a multiset comparison of **positive numeric scores only**. It never prints the legacy player names, local file paths, or timestamps not actually present in the source format. A changed name or row order may change the file digest without adding a score.

**Important:** layout compatibility is not established against a real Final:EX cabinet. A new score may have been imported, edited, or shifted from another rank. The tool does **not** prove a play happened, identify a song/chart without independent context, or upload any score.

## How this helps F1 and F2

The actual game adapter still needs a verified semantic observation source:
- **F1:** exact executable hash, guarded runtime callback, confirmed song/chart identity and rejection of cursor previews.
- **F2:** final result state, distinct P1/P2 events, per-mode scoring and modifiers, duplicate protection and a genuine play identity.
- **Runtime safety:** an on-disk SHA-256 is only a prerequisite. Also check loaded module identity, expected bytes, calling conventions and state before any memory hook.
- **Network reliability:** authenticated player identity, durable delivery, server-side idempotency and acknowledgements are still required.

No reconstructed private game code or addresses were copied. This work is **contract rehearsal**, not real Final:EX hooking. Physical-cabinet verification is still required.

## Tests

The Python suite checks mode inventory, lane order, collision warnings, wrong-state rejection, preview suppression, two-player results, duplicate handling, no-overwrite behavior, ranking-diff anonymity and invalid inputs.

~~~powershell
python -m unittest discover -s tools/tests -p 'test_*.py' -v
~~~

A passing synthetic test proves only the offline tooling works on synthetic inputs. See [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md), [HOOK_DESIGN.md](HOOK_DESIGN.md) and [COMPATIBILITY.md](COMPATIBILITY.md).
