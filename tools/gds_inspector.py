#!/usr/bin/env python3
"""Read-only inspector of the Slot sections in user-provided EZ2AC .gds files.

This is a compatibility research aid. It does not load charts, patch games,
redistribute game files, or assert support for any exact executable revision.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

MAX_FILE = 1024 * 1024
SECTION_RE = re.compile(r"(?m)^\s*\[([A-Za-z0-9_]+)\]\s*$")
ENTRY_RE = re.compile(r"\bTrack(\d+)\s*=\s*\{([^{}]*)\}", re.I | re.S)
COUNT_RE = re.compile(r"\bNumberOfTrack\s*=\s*(\d+)\b", re.I)
SLOT_COUNT_RE = re.compile(r"\bNumberOfSlot\s*=\s*(\d+)\b", re.I)
KEY_RE = re.compile(r"\bKey\s*=\s*(-?\d+)\s*,\s*(-?\d+)\b", re.I)
SONG_TRACK_RE = re.compile(r"\bSongTrack\s*=\s*(-?\d+)\b", re.I)
SLOT_RE = re.compile(r"Slot(\d+)", re.I)
MAX_TRACKS = 128


def strip_comments(text: str) -> str:
    # Comments are not interpreted inside strings; this inspector only looks
    # at the structural, numeric Slot sections.
    return re.sub(r"(?m)^\s*(?:;|#|//).*$", "", text)


def inspect_gds_text(text: str) -> dict:
    if not isinstance(text, str):
        raise ValueError("GDS content must be text")
    if "\0" in text:
        raise ValueError("GDS content contains binary NUL bytes")
    if len(text) > MAX_FILE:
        raise ValueError("GDS input exceeds 1 MiB")
    text = strip_comments(text)
    sections = list(SECTION_RE.finditer(text))
    if not sections:
        raise ValueError("No [Section] headers found")

    result = {"schema_version": 1, "format": "ez2ac.gds.slot-map",
              "slots": [], "warnings": []}
    expected_slots = None
    for i, section in enumerate(sections):
        start = section.end()
        end = sections[i + 1].start() if i + 1 < len(sections) else len(text)
        name = section.group(1)
        body = text[start:end]
        if name.lower() == "general":
            declared = SLOT_COUNT_RE.search(body)
            if declared:
                expected_slots = int(declared.group(1))
                if not 0 <= expected_slots <= 8:
                    raise ValueError("General.NumberOfSlot must be 0..8")
            continue
        slot_match = SLOT_RE.fullmatch(name)
        if not slot_match:
            continue
        slot_number = int(slot_match.group(1))
        if not 1 <= slot_number <= 8:
            raise ValueError("Slot number must be 1..8")
        if any(slot["slot"] == slot_number for slot in result["slots"]):
            raise ValueError(f"Duplicate [Slot{slot_number}] section")
        count_match = COUNT_RE.search(body)
        if not count_match:
            raise ValueError(f"[Slot{slot_number}] missing NumberOfTrack")
        declared_count = int(count_match.group(1))
        if declared_count > MAX_TRACKS:
            raise ValueError(f"[Slot{slot_number}] NumberOfTrack exceeds {MAX_TRACKS}")

        lanes = []
        for match in ENTRY_RE.finditer(body):
            body_entry = match.group(2)
            key = KEY_RE.search(body_entry)
            track = SONG_TRACK_RE.search(body_entry)
            if key is None or track is None:
                raise ValueError(f"[Slot{slot_number}] Track{match.group(1)} missing Key or SongTrack")
            keys = [int(key.group(1)), int(key.group(2))]
            song_track = int(track.group(1))
            if any(k < -1 or k > 65535 for k in keys):
                raise ValueError(f"[Slot{slot_number}] key out of supported range")
            if song_track < -1 or song_track > 65535:
                raise ValueError(f"[Slot{slot_number}] SongTrack out of supported range")
            lanes.append({
                "lane_index": len(lanes),
                "file_label": "Track" + match.group(1),
                "input_keys": keys,
                "song_track": song_track
            })

        if len(lanes) != declared_count:
            raise ValueError(
                f"[Slot{slot_number}] declared {declared_count} tracks but parsed {len(lanes)}. "
                "This file may use syntax not yet supported by the inspector.")
        if len({x["file_label"].lower() for x in lanes}) != len(lanes):
            result["warnings"].append(f"Slot{slot_number}: repeated TrackN label")
        result["slots"].append({"slot": slot_number, "declared_tracks": declared_count,
                                "lanes": lanes})

    if not result["slots"]:
        raise ValueError("No [SlotN] sections found")
    if expected_slots is not None and expected_slots != len(result["slots"]):
        result["warnings"].append(
            f"General declares {expected_slots} slots; found {len(result['slots'])} Slot sections.")
    return result


def inspect_gds_file(path: str | Path) -> dict:
    path = Path(path)
    if not path.is_file():
        raise ValueError("GDS file not found")
    if path.stat().st_size > MAX_FILE:
        raise ValueError("GDS file is larger than 1 MiB")
    raw = path.read_bytes()
    # Common legacy game configuration files can use non-UTF-8 single-byte
    # encodings. Numeric fields parsed by this tool are all ASCII-compatible.
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        content = raw.decode("cp1252")
    return inspect_gds_text(content)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gds_file", help="A .gds descriptor from your own game installation")
    parser.add_argument("--json", action="store_true", help="Machine-readable summary")
    args = parser.parse_args(argv)
    try:
        result = inspect_gds_file(args.gds_file)
    except (OSError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}) if args.json else f"INVALID: {exc}")
        return 1
    if args.json:
        print(json.dumps({"valid": True, **result}, indent=2))
    else:
        print("Read-only GDS slot mapping (index = file order, NOT TrackN label):")
        for slot in result["slots"]:
            print(f"Slot{slot['slot']}: {slot['declared_tracks']} tracks")
            for lane in slot["lanes"]:
                print("  lane %02d: %-8s keys=%-11s song_track=%s" %
                      (lane["lane_index"], lane["file_label"], str(lane["input_keys"]), lane["song_track"]))
        for warning in result["warnings"]:
            print("WARNING:", warning)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
