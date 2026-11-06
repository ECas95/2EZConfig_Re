# Global rankings: local foundation and production roadmap

**Implemented in this fork:** a modern-PC Python 3.10+ SQLite score service with an opt-in local dashboard, submission retry safety, personal bests and player statistics. All numeric scores remain **UNVERIFIED**. No real result-screen hook, authenticated global server or public leaderboard is deployed.

## Try the local scoring service

~~~powershell
python tools/companion_server.py --host 127.0.0.1 --port 8765 --db companion-scores.sqlite3
~~~

Open http://127.0.0.1:8765/dashboard to submit local test scores, switch between all entries and personal bests, view player statistics and explore experimental lobbies/events.

### Idempotent score submission

~~~http
POST /api/v1/scores
Content-Type: application/json

{
  "game_id": "ez2ac_fn_ex",
  "song_id": "test_song_001",
  "chart_id": "5k_n",
  "player_id": "local_p1",
  "score": 850000,
  "clear_type": "clear",
  "submission_id": "test_play_0001"
}
~~~

An optional submission_id keeps retries of exactly the same score from inserting duplicates. The first HTTP 201 has duplicate=false and verified=false. A retry with the same ID and identical score fields returns the same row ID with duplicate=true. Reusing the ID with different score data receives HTTP 400. The idempotency ledger persists in SQLite across restarts, including concurrent requests.

Requests without a submission_id preserve the original append-only behavior. Never use a new ID for each retry; create a unique ID once per finalized play in a future game adapter.

The score endpoint rejects a payload marked synthetic=true or verified=true. This does **not** prevent arbitrary manual submissions; without a verified adapter and authentication, the entire database remains unverified.

### Personal best leaderboard

~~~http
GET /api/v1/leaderboard?game_id=ez2ac_fn_ex&song_id=test_song_001&chart_id=5k_n&best_only=1&limit=20
~~~

best_only=1 selects the highest submission per player ID for that exact game/song/chart, sorted descending. Omit best_only or pass 0 to see all local scores. The response includes verified=false. Raw numbers across different games, charts or score rulesets must **not** be compared.

### Player statistics

~~~http
GET /api/v1/player-stats?game_id=ez2ac_fn_ex&player_id=local_p1
~~~

Returns locally stored plays, unique song/chart pairs, highest raw numeric score and most recent saved timestamp. The player_id is a pseudonym, **not** a verified profile or authenticated online account.

### Database compatibility

Existing score rows are retained without migration. A separate score_submission_ids table stores the optional stable retry keys and hashes. Historical records without IDs cannot be retroactively deduplicated without independent evidence. Back up the SQLite file with the companion closed or via SQLite online backup.

## Global architecture: design, not launched service

~~~text
Authorized game (XP or modern Windows)
  -> exact-build final-result observer                [FUTURE]
  -> local opt-in 2EZ.dll JSONL journal               [SDK IMPLEMENTED]
  -> modern-PC durable queue / consent + offset       [FUTURE]
  -> authenticated HTTPS gateway + replay protection  [FUTURE]
  -> normalized game/chart/ruleset score validation   [FUTURE]
  -> global verified leaderboard and player profiles  [FUTURE]
~~~

The injected DLL must never require internet access to continue gameplay. The current event bridge forwards to the companion's **event viewer only**, not the score database.

A genuine global ranking needs: game/build fingerprint, exact chart checksum and mode/ruleset, pseudonymous player ID, separate authenticated cabinet identity, final score/clear/modifiers/player slot, stable play ID, event source integrity, server-side chart rules and privacy consent. The server must support rejection, moderation, audit, idempotent writes and revocation.

A bearer-protected HTTP developer server is **not** safe to expose to the public internet. TLS termination, per-user credentials, rate limiting, a production database/backup strategy, retention limits, request signing and abuse response are still needed.

## Delivery milestones

1. **Current:** local idempotent submissions, PB boards, pseudonymous stats and dashboard, always unverified.
2. **Next:** modern-host durable queue with explicit opt-in, replay cursors, retries and acknowledgments.
3. **Game integration:** passive result-finalized event from one verified executable revision, not intermediate judge counters or Top-5 files.
4. **Server hardening:** HTTPS, identities, version/chart registry, signed submissions, anti-replay and independent rule validation.
5. **Community:** verified global boards, rivals, personal progression, seasons, trophies and asynchronous tournaments.

The user-supplied Final:EX research helps identify per-mode score and result timing boundaries, but a private decompilation does **not** prove a hook is safe for every revision. Do not copy game offsets or upload protected assets.

See [Score API](SCORES_API.md), [Modernization Strategy](MODERNIZATION_STRATEGY.md), [Extension Events](EXTENSION_EVENTS.md) and [Security](../SECURITY.md).
