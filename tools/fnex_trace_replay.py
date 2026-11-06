#!/usr/bin/env python3
"""Offline Final:EX event state-machine rehearsal, NOT a running game hook.

Consumes synthetic / operator-authored JSONL observations. Emits a separate
JSONL file compatible with the opt-in 2EZConfig event bridge. Never opens,
patches or scans a game process, and never claims scores are verified.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

from companion_server import identifier, integer, CLEAR_TYPES

MAX_TRACE_SIZE = 512 * 1024
MAX_OBSERVATIONS = 5000
MAX_LINE = 4096
EVENT_TYPES = {"song.preview", "song.confirmed", "stage.started",
               "result.finalized", "stage.ended"}
END_REASONS = {"completed", "failed", "aborted", "interrupted"}


def validate_observation(item, line_number):
    if not isinstance(item, dict):
        raise ValueError(f"line {line_number}: observation must be a JSON object")
    kind = item.get("type")
    if kind not in EVENT_TYPES:
        raise ValueError(f"line {line_number}: unsupported observation type: {kind!r}")
    if kind in {"song.preview", "song.confirmed"}:
        identifier(item.get("song_id"), "song_id")
        identifier(item.get("chart_id"), "chart_id")
    if kind == "result.finalized":
        integer(item.get("score"), "score", 0, 1_000_000_000)
        integer(item.get("player_slot"), "player_slot", 1, 2)
        if item.get("clear_type") not in CLEAR_TYPES:
            raise ValueError(f"line {line_number}: invalid clear_type")
    if kind == "stage.ended" and item.get("reason") not in END_REASONS:
        raise ValueError(f"line {line_number}: unsupported stage end reason")
    return item


def load_observations(path: str | Path) -> tuple[list[dict], str]:
    path = Path(path)
    if not path.is_file():
        raise ValueError("Observation file not found")
    if path.stat().st_size > MAX_TRACE_SIZE:
        raise ValueError("Observation file exceeds 512 KiB")
    raw = path.read_bytes()
    if b"\0" in raw:
        raise ValueError("Observation file contains binary bytes")
    lines = raw.decode("utf-8-sig").splitlines()
    if len(lines) > MAX_OBSERVATIONS:
        raise ValueError("Too many observations")
    observations = []
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        if len(line.encode("utf-8")) > MAX_LINE:
            raise ValueError(f"line {line_number}: exceeds {MAX_LINE} bytes")
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {line_number}: invalid JSON") from exc
        observations.append(validate_observation(item, line_number))
    if not observations:
        raise ValueError("Observation file is empty")
    return observations, hashlib.sha256(raw).hexdigest()


def render_event(name, data):
    return {
        "schema_version": 1,
        "event": name,
        "game_id": "ez2ac_fn_ex",
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")
                         .replace("+00:00", "Z"),
        "data": {
            **data,
            "synthetic": True,
            "verified": False,
            "origin": "offline_fixture_replay"
        }
    }


def replay(observations: list[dict], trace_sha256: str) -> dict:
    """Deterministic fixture session IDs. Output timestamps are generated live."""
    if not isinstance(trace_sha256, str) or len(trace_sha256) != 64:
        raise ValueError("A valid fixture digest is required")
    state = "menu"
    selection = None
    emitted = []
    session_number = 0
    received_results = set()
    warnings = []

    for index, item in enumerate(observations, 1):
        validate_observation(item, index)
        kind = item["type"]
        if kind == "song.preview":
            # Preview scroll is NOT a confirmed game selection event.
            if state in {"playing", "results"}:
                raise ValueError(f"observation {index}: preview during an active stage")
            continue
        if kind == "song.confirmed":
            if state in {"playing", "results"}:
                raise ValueError(f"observation {index}: cannot change song during a stage")
            candidate = (item["song_id"], item["chart_id"])
            if state == "selected" and candidate == selection[:2]:
                continue  # duplicate confirmation in the synthetic trace
            session_number += 1
            session_id = f"fixture_{trace_sha256[:16]}_{session_number}"
            selection = (candidate[0], candidate[1], session_id)
            received_results = set()
            emitted.append(render_event("song.selected", {
                "song_id": selection[0], "chart_id": selection[1],
                "session_id": session_id
            }))
            state = "selected"
            continue
        if kind == "stage.started":
            if state != "selected":
                raise ValueError(f"observation {index}: stage requires confirmed song")
            state = "playing"
            continue
        if kind == "result.finalized":
            if state not in {"playing", "results"}:
                raise ValueError(f"observation {index}: result requires active stage")
            slot = item["player_slot"]
            if slot in received_results:
                raise ValueError(f"observation {index}: duplicate finalized player result")
            received_results.add(slot)
            emitted.append(render_event("score.observed", {
                "song_id": selection[0], "chart_id": selection[1],
                "session_id": selection[2], "player_slot": slot,
                "score": item["score"], "clear_type": item["clear_type"]
            }))
            state = "results"
            continue
        if kind == "stage.ended":
            if state not in {"playing", "results"}:
                raise ValueError(f"observation {index}: end requires started stage")
            emitted.append(render_event("session.ended", {
                "session_id": selection[2], "reason": item["reason"],
                "result_count": len(received_results)
            }))
            state = "menu"
            selection = None
            received_results = set()

    if state != "menu":
        warnings.append("Trace ended with a session still selected/active; no end event invented.")
    return {
        "schema_version": 1,
        "events": emitted,
        "event_count": len(emitted),
        "sessions_confirmed": session_number,
        "warnings": warnings,
        "origin": "offline_fixture_replay",
        "verified_gameplay": False
    }


def replay_file(input_path, output_path):
    """Create only a NEW output file, pre-validating the whole trace first."""
    observations, digest = load_observations(input_path)
    result = replay(observations, digest)
    output = Path(output_path)
    if not output.parent.is_dir():
        raise ValueError("Output directory does not exist")
    if output.resolve() == Path(input_path).resolve():
        raise ValueError("Refusing to replace the observation input")
    lines = "".join(json.dumps(event, separators=(",", ":")) + "\n"
                    for event in result["events"])
    # x mode: never overwrite a previous event spool or game settings.
    with output.open("x", encoding="utf-8") as stream:
        stream.write(lines)
    result["output"] = str(output)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Your synthetic observation JSONL")
    parser.add_argument("--output", required=True, help="NEW events JSONL file")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = replay_file(args.input, args.output)
        print(json.dumps(result, indent=2) if args.json else
              f"Emitted {result['event_count']} UNVERIFIED fixture events to {result['output']}")
        return 0
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}) if args.json else f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
