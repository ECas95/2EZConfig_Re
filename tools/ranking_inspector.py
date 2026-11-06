#!/usr/bin/env python3
"""Read-only inspection of EZ2AC legacy ranking file candidates.

Research-derived layouts are NOT validated against a real FNEX cabinet.
Files are never modified or transmitted. Player names are hidden by default.
"""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

FORMATS = {
    "song_top5": 5,
    "mode_top99": 99
}


def inspect_rank_bytes(data: bytes, kind: str, *, include_names=False) -> dict:
    if kind not in FORMATS:
        raise ValueError(f"unknown ranking layout: {kind}")
    count = FORMATS[kind]
    expected = count * 8 + count * 4
    if len(data) != expected:
        raise ValueError(f"{kind}: expected exactly {expected} bytes, got {len(data)}")
    names = [data[i * 8:(i + 1) * 8] for i in range(count)]
    scores = struct.unpack("<" + "i" * count, data[count * 8:])
    warnings = []
    if any(score < 0 for score in scores):
        warnings.append("Negative signed scores detected; data may not match this layout.")
    if any(scores[i] < scores[i + 1] for i in range(count - 1)):
        warnings.append("Scores are not descending. The file may be unsorted or use another layout.")
    rows = []
    for index, score in enumerate(scores):
        row = {"position": index + 1, "score": score}
        if include_names:
            # For this format names are 8-byte fields; may contain arbitrary
            # bytes and should not be interpreted as authenticated identities.
            row["name_legacy"] = names[index].split(b"\0", 1)[0].decode(
                "cp1252", errors="replace").rstrip(" ")
        rows.append(row)
    return {
        "schema_version": 1,
        "format": kind,
        "entries": rows,
        "verified": False,
        "provenance": "locally supplied game data; read-only unverified interpretation",
        "warnings": warnings
    }


def inspect_rank_file(path: str | Path, kind: str, *, include_names=False) -> dict:
    path = Path(path)
    if not path.is_file():
        raise ValueError("Ranking file not found")
    count = FORMATS.get(kind)
    if count is None:
        raise ValueError("Unknown format. Choose song_top5 or mode_top99")
    expected = count * 12
    if path.stat().st_size != expected:
        raise ValueError(f"Expected {expected} bytes, found {path.stat().st_size}")
    return inspect_rank_bytes(path.read_bytes(), kind, include_names=include_names)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rank_file", help="Ranking .bin file from a user-owned installation")
    parser.add_argument("--format", choices=sorted(FORMATS), required=True)
    parser.add_argument("--names", action="store_true",
                        help="Explicit opt-in to print legacy name fields (may contain personal data)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = inspect_rank_file(args.rank_file, args.format, include_names=args.names)
        if args.json:
            print(json.dumps({"valid": True, **result}, ensure_ascii=False, indent=2))
        else:
            print(f"Read-only, UNVERIFIED {args.format} ranking ({len(result['entries'])} entries)")
            for entry in result["entries"]:
                suffix = " | " + entry.get("name_legacy", "") if args.names else ""
                print("%3d %12d%s" % (entry["position"], entry["score"], suffix))
            for warning in result["warnings"]:
                print("WARNING:", warning)
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}) if args.json else f"INVALID: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
