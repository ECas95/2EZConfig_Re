# Multiplayer and score battles

> **Prototype implemented:** in-memory HTTP lobbies with join, ready, start and result states. **Not implemented:** game networking, real simultaneous play, synchronized game clocks, remote input replication, fair-play verification or persistent rooms.

## Intended multiplayer modes

| Mode | Concept | Current support |
| --- | --- | --- |
| Rival boards | Compare independent scores on the same chart | Unverified score database; no in-game UI |
| Asynchronous versus | Two cabinets play locally and submit results | Lobby protocol prototype only |
| Tournament | Rooms and standings across timed rounds | Planning only |
| Simultaneous versus | Start same chart with network-coordinated timing | Not implemented |
| Cooperative shared inputs | Live deterministic state/input exchange | Research only, not implemented |

**Recommended initial milestone:** asynchronous matching where the game never waits for the network. Real synchronized multiplayer is substantially more difficult and cannot be achieved by a lobby service alone.

For a simple local demonstration, start the companion and open **http://127.0.0.1:8765/dashboard**. The Multiplayer Lab panel can create a room, join a second synthetic player, mark ready, request start and submit scores without any cabinet connection.

## REST lobby workflow

Run tools/companion_server.py on a modern machine (see [SCORES_API.md](SCORES_API.md)).

### 1. Host creates a lobby

~~~http
POST /api/v1/lobbies
Content-Type: application/json

{
  "game_id": "ez2dj_7th",
  "song_id": "my_first_song",
  "chart_id": "track_5k_normal",
  "player_id": "cabinet_p1",
  "mode": "versus",
  "max_players": 2
}
~~~

Response includes a random room_id, host, status waiting and the initial players map. Valid mode labels are versus and coop; this does **not** implement cooperative score aggregation. Two to four players are supported in the prototype.

### 2. Another cabinet joins

~~~http
POST /api/v1/lobbies/{room_id}/join
Content-Type: application/json

{"player_id":"cabinet_p2"}
~~~

### 3. Both participants mark ready

~~~http
POST /api/v1/lobbies/{room_id}/ready
Content-Type: application/json

{"player_id":"cabinet_p1","ready":true}
~~~

Repeat for cabinet_p2. Ready may be toggled before start.

### 4. Host requests start

~~~http
POST /api/v1/lobbies/{room_id}/start
Content-Type: application/json

{"player_id":"cabinet_p1"}
~~~

The coordinator requires at least two joined players and all ready flags. It records started_at, but **this is not an in-game launch, synchronized countdown or verified host identity**. The player_id string can be spoofed in the current prototype.

### 5. Submit independent scores

~~~http
POST /api/v1/lobbies/{room_id}/finish
Content-Type: application/json

{"player_id":"cabinet_p1","score":912345}
~~~

Repeat for cabinet_p2. Once all joined members have submitted exactly once, status becomes finished. These room scores are **not written into the SQLite leaderboard** automatically.

### Inspect state

~~~http
GET /api/v1/lobbies/{room_id}
GET /api/v1/lobbies
~~~

Rooms are in memory and lost on restart. There is no automatic expiration, heartbeat, disconnect logic or production identity provider.

## Roadmap to genuine cabinet multiplayer

1. **Game-version compatibility**: verify executable build/adapter, chart format, song ID, exact media hash, scoring semantics and timing modifiers on both cabinets.
2. **Selection confirmation**: real game hook emits song.selected after actual choice; companion validates both cabinets agree.
3. **Asynchronous match**: each player launches the chart locally; verified result-finalized hook emits a durable, unique score event.
4. **Account security and results**: signed sessions, pseudonymous player identity, fair-play checks and idempotent settlement.
5. **Operational reliability**: match deadlines, cancellations, reconnect handling, offline delivery and rollback.
6. **Only then simultaneous starts**: use a monotonic clock model, measured drift and latency buffers; do not block the arcade game loop on the network.
7. **Synchronized cooperation**: research deterministic gameplay state, rollback feasibility, input timing and disconnection safety per game/version.

Avoid synchronizing live keyboard/HID events across an untrusted network or patching undocumented game memory without a proven per-title adapter.

## Test plan

- Full/joined room, duplicate players, invalid inputs and unsupported chart IDs.
- Ready/unready and start attempts by a non-host ID, before all players are ready.
- Duplicate/early scores, score overflow, network disconnect and server restart.
- Titles/revisions with differing scoring systems and modifiers.
- Two cabinets (XP/modern host split) on trusted LAN, with screenshots and timestamped diagnostics.
- Verify that server failure never freezes local audio, rendering or input handling.

See [EXTENSION_EVENTS.md](EXTENSION_EVENTS.md), [NEW_HOOKS.md](NEW_HOOKS.md) and [SCORES_API.md](SCORES_API.md).
