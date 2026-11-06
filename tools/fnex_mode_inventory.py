#!/usr/bin/env python3
"""Read-only inventory of FNEX mode GDS mappings.

Enumerates only user-provided descriptors, never game binaries or song assets.
No networking or game hooks. Requires Python 3.10+ on a modern host.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from gds_inspector import inspect_gds_file

MAX_DESCRIPTORS = 128
MAX_DEPTH = 5


def inspect_mode_directory(directory: str | Path) -> dict:
    root = Path(directory).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("GDS root must be a directory")
    candidates = []
    # pathlib.rglob does not normally traverse directory symlinks; explicitly
    # reject any linked file or linked parent before inspecting.
    for path in root.rglob("*"):
        if path.suffix.lower() != ".gds":
            continue
        if path.is_symlink():
            raise ValueError("Symlinked GDS files are not permitted")
        relative = path.relative_to(root)
        if len(relative.parts) > MAX_DEPTH:
            raise ValueError(f"GDS descriptor exceeds nesting limit: {path.name}")
        if any((root / Path(*relative.parts[:n])).is_symlink()
               for n in range(1, len(relative.parts))):
            raise ValueError("Symlinked GDS parent directory is not permitted")
        if not path.resolve().is_relative_to(root):
            raise ValueError("GDS descriptor escapes the selected root")
        if not path.is_file():
            continue
        candidates.append(path)
        if len(candidates) > MAX_DESCRIPTORS:
            raise ValueError(f"Too many GDS descriptors; maximum {MAX_DESCRIPTORS}")

    candidates.sort(key=lambda item: (str(item.relative_to(root)).casefold(),
                                      str(item.relative_to(root))))
    results = []
    warnings = []
    seen = set()
    for path in candidates:
        relative = path.relative_to(root)
        normalized = str(relative).casefold()
        if normalized in seen:
            raise ValueError("Duplicate case-insensitive GDS descriptor path")
        seen.add(normalized)
        mode = path.parent.name if path.parent != root else "(root)"
        parsed = inspect_gds_file(path)
        descriptor = {
            "mode": mode,
            "descriptor": path.name,
            "slots": [],
            "warnings": list(parsed["warnings"])
        }
        for slot in parsed["slots"]:
            key_to_lanes = {}
            track_to_lanes = {}
            for lane in slot["lanes"]:
                for key in lane["input_keys"]:
                    if key >= 0:
                        key_to_lanes.setdefault(key, []).append(lane["lane_index"])
                if lane["song_track"] >= 0:
                    track_to_lanes.setdefault(lane["song_track"], []).append(lane["lane_index"])
            for key, lanes in key_to_lanes.items():
                if len(set(lanes)) > 1:
                    descriptor["warnings"].append(
                        f"Slot{slot['slot']}: input key {key} appears in multiple lanes {lanes}")
            for track, lanes in track_to_lanes.items():
                if len(set(lanes)) > 1:
                    descriptor["warnings"].append(
                        f"Slot{slot['slot']}: SongTrack {track} appears in multiple lanes {lanes}")
            descriptor["slots"].append({
                "slot": slot["slot"],
                "lane_count": len(slot["lanes"]),
                "lanes": [
                    {"index": lane["lane_index"], "key_pair": lane["input_keys"],
                     "song_track": lane["song_track"]}
                    for lane in slot["lanes"]
                ]
            })
        results.append(descriptor)
        warnings += [f"{mode}/{path.name}: {msg}" for msg in descriptor["warnings"]]
    return {
        "schema_version": 1,
        "game_id": "ez2ac_fn_ex",
        "source": "operator_supplied_gds",
        "read_only": True,
        "descriptors": results,
        "descriptor_count": len(results),
        "warnings": warnings,
        "status": "no_descriptors_found" if not results else "inspected",
        "verified_with_game": False
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", help="Directory containing user-owned .gds descriptors")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = inspect_mode_directory(args.directory)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("Final:EX mode GDS inventory (READ-ONLY; game compatibility unverified)")
            print(f"Descriptors: {result['descriptor_count']}")
            for item in result["descriptors"]:
                slots = ", ".join(f"P{slot['slot']}: {slot['lane_count']} lanes"
                                  for slot in item["slots"])
                print(f"  {item['mode']}/{item['descriptor']}  |  {slots}")
            for warning in result["warnings"]:
                print("WARNING:", warning)
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}) if args.json else f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
