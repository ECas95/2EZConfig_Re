#!/usr/bin/env python3
"""Compare TWO locally supplied legacy ranking files without uploading or editing.

A changed ranking file is NOT evidence of a completed game. Player names are
never read into output. This is a read-only research / diagnostics aid.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from ranking_inspector import FORMATS, inspect_rank_bytes


def compare_rankings(before: bytes, after: bytes, kind: str) -> dict:
    old = inspect_rank_bytes(before, kind)
    new = inspect_rank_bytes(after, kind)
    before_scores = Counter(row["score"] for row in old["entries"] if row["score"] > 0)
    after_scores = Counter(row["score"] for row in new["entries"] if row["score"] > 0)
    added = after_scores - before_scores
    removed = before_scores - after_scores
    changed_file = before != after
    warnings = []
    warnings.extend(old["warnings"])
    warnings.extend(new["warnings"])
    if changed_file and not added and not removed:
        warnings.append(
            "Binary changed but positive score values did not; names/ordering/padding may have changed.")
    if added:
        warnings.append(
            "New score values are unverified file changes, not authenticated play events.")
    return {
        "schema_version": 1,
        "format": kind,
        "read_only": True,
        "verified": False,
        "source": "two_operator_supplied_ranking_snapshots",
        "file_changed": changed_file,
        "before_sha256": hashlib.sha256(before).hexdigest(),
        "after_sha256": hashlib.sha256(after).hexdigest(),
        "added_positive_scores": [
            {"score": score, "count": count}
            for score, count in sorted(added.items(), reverse=True)
        ],
        "removed_positive_scores": [
            {"score": score, "count": count}
            for score, count in sorted(removed.items(), reverse=True)
        ],
        "warnings": list(dict.fromkeys(warnings))
    }


def compare_ranking_files(before_path: str | Path, after_path: str | Path,
                          kind: str) -> dict:
    if kind not in FORMATS:
        raise ValueError("Unknown ranking layout")
    expected_size = FORMATS[kind] * 12
    paths = [Path(before_path), Path(after_path)]
    for path in paths:
        if not path.is_file():
            raise ValueError("Ranking snapshot missing")
        if path.stat().st_size != expected_size:
            raise ValueError(f"Expected exactly {expected_size} bytes for {kind}")
    return compare_rankings(paths[0].read_bytes(), paths[1].read_bytes(), kind)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True, help="Older, user-owned file copy")
    parser.add_argument("--after", required=True, help="Newer, user-owned file copy")
    parser.add_argument("--format", choices=sorted(FORMATS), required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = compare_ranking_files(args.before, args.after, args.format)
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print("UNVERIFIED legacy ranking comparison; files left untouched")
            print("Raw file changed:", report["file_changed"])
            print("New positive score values:", report["added_positive_scores"])
            print("Missing positive score values:", report["removed_positive_scores"])
            for warning in report["warnings"]:
                print("WARNING:", warning)
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}) if args.json else f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
