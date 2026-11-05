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

HTTP 201 responds with a new ID, stored=true and **verified=false**. Scores are constrained integers 0–1,000,000,000. Clear types are unknown, failed, clear, full_combo and perfect. IDs accept a restricted ASCII character set.

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

Returns matching entries sorted descending by score, then earlier creation/row ID. Default limit 20, maximum 100. The response includes verified=false. Multiple rows per player may appear; per-user personal-best collapsing is pending.

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

## Production-hardening roadmap

- Verified result extraction at an exact game build's final results state; one event per play.
- Signed/session-bound events and durable queue acknowledgments; idempotency keys, retry/backoff, duplicate detection.
- Player identity and consent, privacy controls, retention and data deletion; pseudonymization by default.
- Score range normalization and modifiers by title/chart, personal bests, rival lists and seasons.
- HTTPS/auth, rate limiting, moderation, migrations, audit logs, backups and monitoring.
- Optional web dashboard, offline sync, tournament administration and community API.

See [EXTENSION_EVENTS.md](EXTENSION_EVENTS.md), [NEW_HOOKS.md](NEW_HOOKS.md) and [MULTIPLAYER.md](MULTIPLAYER.md).
