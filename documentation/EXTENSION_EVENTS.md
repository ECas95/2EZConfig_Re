# Extension events and hook SDK (v1)

> **Implemented:** the DLL has an opt-in JSONL spool and a C ABI export. It does **not** automatically discover songs, scores, charts or sessions. Version-specific adapters must supply those events.

## Architecture

~~~text
Legacy Windows game (existing 2EZ.dll and optional trusted adapter)
         | EZ2_PublishEvent("song.selected", "{...}")
         v
2ez-events.jsonl (opt-in, appended in the game folder)
         | explicit operator file copy / shared folder
         v
Modern Python companion host
  tools/event_bridge.py --send
         | local HTTP or trusted HTTPS proxy
         v
  tools/companion_server.py
      /api/v1/events        preview last 100 events
      /api/v1/scores        local SQLite score ledger
      /api/v1/leaderboard   leaderboard queries
      /api/v1/lobbies       prototype lobby coordination
~~~

**No networking is performed by the injected DLL.** Python tools are for a modern PC with Python 3.10+, not Windows XP. No proprietary game files, song data or executable memory dumps are distributed.

## Enable event capture

Select **Settings → Debug Settings → Enable local extension events (opt-in)**, or explicitly set the per-game JSON option:

~~~json
{"extension_events_enabled": true}
~~~

The default is **false**. Changes apply when the game next loads the DLL. When enabled, a runtime.ready event is emitted after the background initialization and normal patch phase. The event file is placed beside the game's 2EZ.dll as **2ez-events.jsonl**.

The file is append-only and has no automatic log rotation in v1. Close the game before moving/rotating it; audit event content before sharing.

## C ABI (implemented)

~~~cpp
// Returns 1 if written to the local JSONL spool; otherwise 0.
extern "C" __declspec(dllexport) int __cdecl EZ2_PublishEvent(
    const char* eventName,
    const char* jsonObjectPayload);
~~~

An adapter can find this symbol via GetModuleHandleW(L"2EZ.dll") plus GetProcAddress. It is **not** a game memory hook by itself. The existing extra-DLLs setting can load a trusted, version-compatible adapter; the adapter must implement and validate its own event detection.

Input contracts:
- Event name: 1–64 ASCII letters, digits, period, underscore or hyphen.
- Payload: JSON object up to 4,096 bytes. Invalid or non-object payloads are rejected.
- Output: one JSON object per line, tagged with schema_version = 1, game_id and UTC timestamp.
- Errors return 0; event capture is disabled unless explicitly enabled.
- Append calls are synchronous and serialized. **Never call from a frame-rate, HID polling, audio or other latency-critical hook.**

Example JSONL record:

~~~json
{"schema_version":1,"event":"runtime.ready","game_id":"ez2dj_7th","timestamp_utc":"2026-11-05T17:02:19.122Z","data":{"stage":"post_patches"}}
~~~

The timestamp above is illustrative and generated at runtime.

## Event catalog and availability

| Event | Producer | Example data | Current status |
| --- | --- | --- | --- |
| runtime.ready | 2EZ.dll background initialization | stage: post_patches | **Implemented** |
| song.selected | Game-version song selection adapter | song_id, chart_id, mode | **Contract proposed; adapter missing** |
| score.observed | Game-version result screen adapter | song_id, chart_id, score, clear_type, player_id | **Contract proposed; adapter missing** |
| session.ended | Game-version stage/session adapter | stage, reason | **Contract proposed; adapter missing** |
| chart.loaded | Future chart-loader adapter | chart_id, source, content hash | **Proposed** |
| cabinet.input.diagnostic | Future diagnostics/export adapter | anonymized device capabilities | **Proposed** |

The companion event viewer accepts runtime.ready, song.selected, score.observed and session.ended in prototype form. Acceptance proves only JSON conformance, not that a genuine arcade hook generated the event.

## Test the event bridge

Start a modern host:

~~~powershell
python tools/companion_server.py --db companion-scores.sqlite3
~~~

Preview only, with **no network transfer**:

~~~powershell
python tools/event_bridge.py --file "C:\Arcade\EZ2\2ez-events.jsonl"
~~~

Forward events to an explicitly running localhost companion:

~~~powershell
python tools/event_bridge.py --file "C:\Arcade\EZ2\2ez-events.jsonl" --send
~~~

Every invocation starts reading at the beginning. **Re-running with --send will replay events.** Do not treat this prototype as an exactly-once score ingestion system. Remote delivery is refused over plaintext HTTP and needs a trusted HTTPS terminator.

## Adapter development requirements

1. Select an exact legally acquired game executable; record its SHA-256 and game/version.
2. Find a reproducible semantic event (selection confirmed, result finalized, session exited). Investigate read-only before detouring.
3. Verify target instructions, calling convention and state representation. Never substitute offsets from another game revision.
4. Reject unsupported signatures **before** applying any game-specific patch or hook.
5. Publish minimal metadata and pseudonymous player IDs. Do not capture copyrighted song assets, passwords, device serials or full memory pages.
6. Fail open: invalid data, failed logs or offline companion must **never** block gameplay.
7. Test repeated sessions, failures, delayed results, song IDs, game shutdown and actual XP compatibility.
8. Provide a compatibility table and synthetic, rights-cleared sample data.

See [NEW_HOOKS.md](NEW_HOOKS.md), [CUSTOM_SONGS.md](CUSTOM_SONGS.md), [SCORES_API.md](SCORES_API.md), [MULTIPLAYER.md](MULTIPLAYER.md) and the [adapter publisher shim](../examples/hooks/README.md).

## Known limitations

Not a plugin sandbox, API authentication mechanism, anti-cheat system or synchronized multiplayer protocol. It has no bounded log rotation, asynchronous writer, persistent offset tracking, event deduplication or cryptographic identity verification. Those items remain roadmap work.
