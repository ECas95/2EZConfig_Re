# Score server and leaderboards (local prototype)

**Implemented:** a Python 3.10+ HTTP companion with SQLite score storage and unverified leaderboards. **Not implemented:** actual game result extraction, anti-cheat, real player identity, public internet hosting, replay protection or reliable delivery from cabinets.

## Start on a modern host

~~~powershell
python tools/companion_server.py --host 127.0.0.1 --port 8765 --db companion-scores.sqlite3
~~~

The default listens only on localhost without authentication. Binding to a nonlocal interface requires a bearer token, but HTTP alone does not encrypt that token. **Never expose the prototype to the public internet.** Put remote endpoints behind HTTPS/VPN plus authentication, limits and monitoring in a future production version.

~~~powershell
# Trusted LAN test only (plaintext HTTP is not suitable for untrusted networks)
python tools/companion_server.py --host 0.0.0.0 --port 8765 --token "REPLACE_WITH_LONG_RANDOM_SECRET"
~~~

## Optional browser dashboard

With the companion running, open **http://127.0.0.1:8765/dashboard**. The built-in HTML interface allows developers to submit sample scores, query the selected song/chart, explore hook events and exercise prototype lobby transitions. It uses only local static HTML/CSS/JavaScript, makes same-origin requests and saves no authorization token in browser storage. **All data is still unverified.** If the API uses a bearer token, enter it into the dashboard's connection field; the page is public static content but API requests remain authenticated.

## Score reliability and player records (implemented)

The local SQLite API now supports an **optional submission_id** on POST /api/v1/scores. Repeated submissions with the same ID and score fields return the same row (duplicate=true), while reusing an ID for different scores is rejected. This is *retry protection*, not proof of gameplay authenticity.

Get one personal best per player for an exact game/song/chart using **GET /api/v1/leaderboard?...&best_only=1** (the original all-submissions behavior remains when omitted). Get local participation totals using **GET /api/v1/player-stats?game_id=...&player_id=...**. Scores continue to return verified=false. Requests that claim verified=true or mark themselves synthetic=true are rejected by the score ingestion endpoint.

The local dashboard now exposes a personal-best switch, stats view and optional submission ID field. A remote/global leaderboard is **not** implemented: the companion is not meant to be deployed publicly. Read [Global rankings](GLOBAL_RANKINGS.md) for full examples, authentication requirements and a phased roadmap.

## REST endpoints

### GET /health

Returns service name, version and status.

### POST /api/v1/scores

~~~json
{
  "game_id": "ez2dj_7th",
  "song_id": "my_first_song",
  "chart_id": "track_5k_normal",
  "player_id": "cabinet_p1",
  "score": 912345,
  "clear_type": "full_combo"
}
~~~

HTTP 201 responds with an ID, stored=true, duplicate (true or false) and **verified=false**. Optional submission_id provides durable retry deduplication. Scores are constrained integers 0–1,000,000,000. Clear types are unknown, failed, clear, full_combo and perfect. IDs accept a restricted ASCII character set.

PowerShell:

~~~powershell
$score = @{
  game_id='ez2dj_7th'; song_id='my_first_song'; chart_id='track_5k_normal';
  player_id='cabinet_p1'; score=912345; clear_type='clear'
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8765/api/v1/scores' -ContentType 'application/json' -Body $score
~~~

### GET /api/v1/leaderboard

~~~text
/api/v1/leaderboard?game_id=ez2dj_7th&song_id=my_first_song&chart_id=track_5k_normal&limit=20
~~~

Returns matching entries sorted descending by score, then earlier creation/row ID. Default limit 20, maximum 100. Add best_only=1 to select each player ID's highest score on that chart. The response includes verified=false. Multiple rows per player may appear; per-user personal-best collapsing is pending.

### POST /api/v1/events

~~~json
{
  "event": "song.selected",
  "game_id": "ez2dj_7th",
  "data": {"song_id": "my_first_song", "chart_id": "track_5k_normal"}
}
~~~

Events supported in the viewer: runtime.ready, song.selected, score.observed and session.ended. The viewer accepts syntactically valid records; it cannot confirm that a real hook generated them.

### GET /api/v1/events

Returns the last 100 accepted events **held in memory**, cleared when the service restarts.

## How game results would reach the server

~~~text
Game-specific verified result-finalized hook (NOT IMPLEMENTED)
    -> opt-in 2EZ_PublishEvent (IMPLEMENTED)
    -> local 2ez-events.jsonl
    -> explicit tools/event_bridge.py --send (IMPLEMENTED)
    -> POST /api/v1/events (IMPLEMENTED)
    -> future validation/deduplication/score mapping
    -> POST /api/v1/scores (IMPLEMENTED but manual/unverified)
    -> GET /api/v1/leaderboard (IMPLEMENTED)
~~~

The bridge **does not automatically convert score.observed events into score submissions**. This is intentional: real score validation, unique event IDs and game-specific normalization are required before doing so.

## Data model

SQLite scores: ID, created_at timestamp, game_id, song_id, chart_id, player_id, score and clear_type. An index accelerates game/song/chart leaderboard lookups. Input fields are bounded and SQL statements use parameters.

The prototype has a shared optional bearer token, not per-player authentication. Results are **not evidence of a legitimate game play** and should never be used for ranked competitions without integrity controls.

## Final:EX passive result-contract rehearsal

A new [offline trace-replay tool](fnex/PASSIVE_OBSERVATORY.md) accepts explicitly synthetic observations and emits score.observed only after a stage begins and a result is marked finalized. Generated events are synthetic=true and verified=false, and enter the existing event viewer only via manual bridge operation. **They do not create SQLite scores or authenticate any gameplay.** A local ranking-snapshot diff also reports numerical changes without identifying players or inventing play events.

## Final:EX local ranking research

The new [ranking inspector](fnex/FORMATS.md) can read candidate Final:EX **top-five** (60-byte) and **top-99** (1,188-byte) ranking files from an operator-owned installation. It defaults to **redacting legacy player names**, makes no network requests and never changes the files.

~~~powershell
python tools/ranking_inspector.py "D:\OwnGame\system\ranking\some_ranking.bin" --format mode_top99 --json
~~~

File-backed rankings are **not** authoritative play events and may contain legacy formatting quirks. They do not identify exact song/chart or authenticated player without extra context. Do not upload or convert them automatically into verified competitive scores. Follow [the per-game result-finalized hook plan](fnex/HOOK_DESIGN.md) before designing ingestion from the running game.

## Production-hardening roadmap

- Verified result extraction at an exact game build's final results state; one event per play.
- Signed/session-bound events and durable queue acknowledgments; idempotency keys, retry/backoff, duplicate detection.
- Player identity and consent, privacy controls, retention and data deletion; pseudonymization by default.
- Score range normalization and modifiers by title/chart, personal bests, rival lists and seasons.
- HTTPS/auth, rate limiting, moderation, migrations, audit logs, backups and monitoring.
- Optional web dashboard, offline sync, tournament administration and community API.

See [EXTENSION_EVENTS.md](EXTENSION_EVENTS.md), [NEW_HOOKS.md](NEW_HOOKS.md) and [MULTIPLAYER.md](MULTIPLAYER.md).
