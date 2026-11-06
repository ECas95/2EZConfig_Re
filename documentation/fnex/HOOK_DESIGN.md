# Game architecture → extension hook opportunities

This is a **design map**, not a list of deployable memory patches. The source archive supplied for research contains reconstructed implementations, but its addresses, structures and calling conventions are valid only for the particular image it describes. None of those private addresses are copied here as executable hook targets.

## Lifecycle and data flow

~~~text
Game initialization
  |
  +-- Cabinet input: original I/O or emulated input path
  |        +-- existing 2EZConfig IO handlers/HID diagnostics
  |
  +-- Mode selection and stage descriptor
  |        +-- system/<mode>/... .gds and Stage.ini
  |        +-- ordered per-player track/key mappings
  |
  +-- Song selection
  |        +-- song-table lookup, difficulty and unlock/channel rules
  |        +-- audio preview, banner/title art and resource discovery
  |        +-- proposed hook: song.selected (event after confirmation)
  |
  +-- Chart / music setup
  |        +-- chart decoder, tick/tempo transform and lane binding
  |        +-- sample loading, game-mode-specific stage setup
  |        +-- proposed hook: chart.loaded (after validation)
  |
  +-- Gameplay
  |        +-- music clock and sample scheduling
  |        +-- input edge read/port cache and frame update
  |        +-- judge → per-mode score/gauge sinks
  |
  +-- Results
           +-- round stats and rank calculation
           +-- per-song and mode-wide local rankings
           +-- proposed hook: score.observed (ONLY after finalization)
           +-- session.ended
~~~

## Evidence-to-design matrix

| Area | Source evidence family | What this changes in 2EZConfig_Re |
| --- | --- | --- |
| Input ports | Reconstructed I/O paths, DirectInput paths and game state sampling | Maintain current IO compatibility layer; map source event codes only after verifying exact build |
| Graphics | DirectDraw7/Direct3D7 wrappers and screen directors | Avoid generic renderer hooks; experimental previews should be separate, not inside render callbacks |
| Audio | DirectSound sample/voice handling and music clock | Avoid blocking audio threads; maintain separate audio and grading latency measurements |
| Mode/lanes | GDS reader and per-player track list | Use file-order lane mapping, not TrackN numeric order; add inspector tests |
| Song catalog | Song table lookup, Stage.ini configuration and selection director | Prototype read-only song.selected observer for one validated build |
| Charts | Chart objects, note record timing and sample indices | Document mode/version-specific semantics; do not inject unchecked arbitrary charts |
| Judge | Press/release, per-lane windows and separate music clock | Build trace-first timing lab; never hardcode legacy offsets across revisions |
| Scoring | Score accumulator and distinct per-mode/hold scoring paths | Wait for authoritative final score; distinguish keys, catch and other modes |
| Result/rank | Result director and local top-five/top-99 files | Read-only preview can work now; real score hook should occur before/after a documented finalization state |
| Two-player | Existing local two-player results/ranking branches | Start with asynchronous score matches; no evidence of native online synchronization |

## Hook A — observe song selection

**Purpose:** publish one low-frequency event after the selected song and chart become committed, not on every cursor movement.

Required proof for each game executable:
- Verified on-disk file hash and in-memory code signature with expected bytes.
- Call graph showing entry into a **stable confirmed selection**, not a preview cursor or hidden/unlocked pool change.
- Extraction of valid song ID and difficulty/chart key; no raw pointers in the published event.
- Stable fallback when a song is missing, the catalog changes or a game mode is unsupported.

Proposed event:

~~~json
{
  "event": "song.selected",
  "game_id": "ez2ac_fn_ex",
  "data": {
    "song_id": "own_test_song_01",
    "chart_id": "5k_n",
    "mode": "5keymix",
    "source": "verified_game_adapter",
    "adapter_id": "fnex_test_adapter"
  }
}
~~~

**This is a synthetic payload illustration, not output from an existing game hook.**

## Hook B — observe the completed result

**Purpose:** emit exactly one authenticated-for-session result *after* judgement and score calculation finish, and *before* state is cleared for the next stage.

Design notes:
- ScoreKeeper and per-mode PlayerSlot sinks are different concepts. Per-frame/hold counters are partial, not the final score.
- Some modes have different score accumulation and hold-note rules. A generic sum of judge events will be wrong.
- Top-five and top-99 files are a **presentation/storage layer**, not a reliable source of unique play event identity.
- Two-player results need explicit player slot identities and distinct chart/mode keys.

Proposed event metadata: game_id, chart_id, song_id, local session ID, player slot, final score, clear type, modifiers, stage, adapter ID, hash/provenance. A modern companion must still treat it as **unverified** until identity/integrity validation exists. Never collect personally identifying information by default.

## Hook C — custom-song catalog and assets

The research strongly supports a multi-step approach, **not** one file-open redirect:

1. Read existing mode-specific catalog and authorization/unlock state without modifications.
2. Stage rights-cleared custom-song metadata with validated IDs, levels, asset paths and chart references.
3. Determine a safe, noncolliding entry/ID allocation strategy for one exact executable.
4. Resolve the game's original preview/music/jacket/chart read sequence.
5. Integrate a minimal adapter only where its state and file rules are verified; fall back to original content paths otherwise.
6. Confirm chart timing, mode-specific lane order from GDS, sample IDs, sound playback and score identity.
7. Verify unload/reload and return-to-song-selection behavior on hardware.

**Not implemented:** registration, injection, packing/encryption or chart loaders. The [song-pack validator](../CUSTOM_SONGS.md) and [GDS inspector](FORMATS.md) only prepare data and test invariants.

## Hook D — precise timing / input latency research

The supplied notes describe two related but separate clocks:
- A music/chart clock advanced by an audio-side worker.
- Inputs sampled and dispatched to judgement during game-frame processing.

They also describe intentional input-latency compensation and per-chart judgement windows. This suggests a **potential** improvement: timestamp the actual input edge and compare it to the music clock, rather than changing the grade window itself. But:
- Converting between milliseconds, music ticks, beats and measures needs experimentally verified, explicit units.
- Press/release/hold lanes and simultaneous key events have different ordering semantics; a single global FIFO may misassociate them.
- The original implementation's compensation must not be accidentally applied twice.
- Hooking into a timing-critical code path can alter stability and scoring fairness.

**Recommendation:** build a read-only trace tool first: synthetic input edge timeline + observed final judgement records + chart tempo changes. Test hundreds of edge cases; implement a backdating patch only when exact-build behavior is demonstrated on a cabinet. No timing hook is enabled by this integration.

## Hook E — multiplayer

The reference describes original **local two-player** state and results. It does not establish a native networked multiplayer transport or cross-cabinet clock.

Use the already implemented 2EZConfig companion lobbies for **asynchronous** matches first: identical song/chart checksum, confirmed local start and eventual final result. Adding live synchronous starts requires real song/stage callbacks, monotonic clock sync, drift studies, authentication and robust disconnect handling. Never send frame-by-frame input through the existing JSONL synchronous event stream.

## Testing priorities

1. Strict executable build fingerprint and patch-byte preflight.
2. Read-only GDS, song table and ranking interpretation on **user-owned data**.
3. Passive song-selected event on one exact tested Final:EX executable.
4. Passive score-finalized event and end-to-end local delivery to unverified companion.
5. Optional original-content pack adapter with one **self-authored** chart and audio asset.
6. Asynchronous two-cabinet matches; only then real synchronized multiplayer.

See [COMPATIBILITY.md](COMPATIBILITY.md) and [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md).
