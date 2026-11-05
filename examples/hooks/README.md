# Adapter publisher example

sample_adapter.cpp is a **synthetic integration stub**, not a game-specific reverse-engineering implementation. It shows a dynamic GetProcAddress lookup of the actual 2EZ.dll C export, EZ2_PublishEvent.

## What it demonstrates

- A trusted extra DLL can call an exported C function to publish a low-frequency event.
- Event payloads use JSON objects and are appended to a game-local JSONL spool **only if the operator enabled event capture**.
- Event emission failures return 0 and never need to interrupt game logic.

## What it does not demonstrate

- The exported AdapterOnSongSelected and AdapterOnResultFinalized functions are **not automatically called** by any EZ2 game.
- This sample has **no offsets, patch patterns, detours, score memory extraction or chart loader**.
- Published score data is explicitly synthetic and must never be treated as a verified real play.

## Implementation notes

1. Build a 32-bit DLL with a compatible Windows XP-targeted toolchain.
2. The existing launcher can load a separately trusted add-on DLL using Extra DLLs, subject to the launcher’s filename/path limitations.
3. Invoke callbacks only from an exact game build's verified semantic event, **not** from audio, rendering or per-frame IO paths.
4. Use a JSON serializer rather than constructing payloads from raw user-controlled strings. This stub intentionally sends hard-coded synthetic values.
5. Document target executable hash, tested game revision, Windows version, failure behavior, and whether the add-on can be disabled independently.

See [EXTENSION_EVENTS.md](../../documentation/EXTENSION_EVENTS.md) and [NEW_HOOKS.md](../../documentation/NEW_HOOKS.md).