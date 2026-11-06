#!/usr/bin/env python3
"""Read-only preflight for the BMSData/mode/category/song layout used by EZ2CustomMod.

Checks only metadata and chart declarations for self-authored or authorized
assets. Does not decode audio/video, interpret notes, modify files or run FNEX.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

CHART_SUFFIXES = {".bms", ".bme", ".bml"}
MODE_ALIASES = {
    "5keymix": "5keyMix", "5k": "5keyMix", "5kstandard": "5keyMix",
    "5keyonly": "5keyOnly", "5konly": "5keyOnly", "5k_only": "5keyOnly",
    "streetmix": "streetMix",
    "7keymix": "7keyMix", "7streetmix": "7keyMix",
    "7k": "7keyMix", "7kstandard": "7keyMix",
    "clubmix": "clubMix", "spacemix": "spaceMix",
    "rubymix": "rubyMix", "ruby": "rubyMix",
    "ez2catch": "ez2Catch", "catch": "ez2Catch",
    "turntable": "turnTable", "scratchmix": "turnTable", "scratch": "turnTable",
    "cv2mix": "cv2Mix"
}
DECLARATION = re.compile(r"(?mi)^\s*#(WAV|BMP)[0-9A-Z]{2}\s+(.+?)\s*$")
MAX_CHART_SIZE = 4 * 1024 * 1024
MAX_CHARTS = 150_000
MAX_SONGS = 40_000
MAX_ISSUES = 150


def as_relative(root: Path, file: Path) -> str:
    return file.relative_to(root).as_posix()


def valid_asset_reference(value: str) -> tuple[str, ...] | None:
    value = value.strip().strip('"').replace("\\", "/")
    if not value or value.startswith("/") or ":" in value or "\0" in value:
        return None
    parts = tuple(value.split("/"))
    if any(part in ("", ".", "..") for part in parts):
        return None
    return parts


def matching_child(folder: Path, name: str) -> Path | None:
    if not folder.is_dir() or folder.is_symlink():
        return None
    for child in folder.iterdir():
        if child.name.casefold() == name.casefold():
            return child
    return None


def declared_asset_found(song: Path, value: str) -> bool | None:
    """Return None for unsafe paths, else whether an asset exists in this song."""
    parts = valid_asset_reference(value)
    if parts is None:
        return None
    roots = [song]
    # Typical BMS libraries keep keysounds under sound/ when only basename is named.
    if len(parts) == 1:
        sub = matching_child(song, "sound")
        if sub is not None and sub.is_dir() and not sub.is_symlink():
            roots.append(sub)
    for root in roots:
        node = root
        for part in parts:
            node = matching_child(node, part)
            if node is None or node.is_symlink():
                break
        else:
            if node.is_file():
                return True
    return False


def inspect_bms_library(directory: str | Path, *, check_assets=False) -> dict:
    root = Path(directory).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("BMSData root must be a directory")
    counts = {"modes": 0, "categories": 0, "songs": 0, "charts": 0,
              "declared_assets": 0, "missing_assets": 0}
    issues = []
    omitted = 0
    per_mode = {}
    def issue(code, path, message):
        nonlocal omitted
        if len(issues) < MAX_ISSUES:
            issues.append({"code": code, "path": as_relative(root, path), "message": message})
        else:
            omitted += 1

    for mode in sorted(root.iterdir(), key=lambda p: p.name.casefold()):
        if mode.is_symlink():
            issue("symlink_ignored", mode, "Linked mode directory was not scanned")
            continue
        if not mode.is_dir():
            continue
        canonical = MODE_ALIASES.get(mode.name.casefold())
        if canonical is None:
            issue("unknown_mode", mode, "Not recognized as an EZ2CustomMod mode folder")
            continue
        counts["modes"] += 1
        per_mode.setdefault(canonical, {"categories": 0, "songs": 0, "charts": 0})
        for category in sorted(mode.iterdir(), key=lambda p: p.name.casefold()):
            if category.is_symlink():
                issue("symlink_ignored", category, "Linked category was not scanned")
                continue
            if not category.is_dir():
                continue
            counts["categories"] += 1
            per_mode[canonical]["categories"] += 1
            songs_found = 0
            for song in sorted(category.iterdir(), key=lambda p: p.name.casefold()):
                if song.is_symlink():
                    issue("symlink_ignored", song, "Linked song was not scanned")
                    continue
                if not song.is_dir():
                    continue
                songs_found += 1
                counts["songs"] += 1
                per_mode[canonical]["songs"] += 1
                if counts["songs"] > MAX_SONGS:
                    raise ValueError(f"Library exceeds safety cap of {MAX_SONGS} song folders")
                chart_paths = [
                    f for f in song.iterdir() if f.is_file() and
                    not f.is_symlink() and f.suffix.casefold() in CHART_SUFFIXES
                ]
                if not chart_paths:
                    issue("no_charts", song, "Expected chart file directly in song folder")
                    continue
                for chart in sorted(chart_paths, key=lambda p: p.name.casefold()):
                    counts["charts"] += 1
                    per_mode[canonical]["charts"] += 1
                    if counts["charts"] > MAX_CHARTS:
                        raise ValueError(f"Library exceeds safety cap of {MAX_CHARTS} charts")
                    if chart.stat().st_size > MAX_CHART_SIZE:
                        issue("chart_too_large", chart, "Chart over 4 MiB; declaration scan skipped")
                        continue
                    if not check_assets:
                        continue
                    raw = chart.read_bytes()
                    try:
                        text = raw.decode("utf-8-sig")
                    except UnicodeDecodeError:
                        text = raw.decode("cp932", errors="replace")
                    for match in DECLARATION.finditer(text):
                        declared = match.group(2)
                        counts["declared_assets"] += 1
                        found = declared_asset_found(song, declared)
                        if found is None:
                            issue("unsafe_asset_path", chart,
                                  "A WAV/BMP declaration uses an unsafe path")
                        elif found is False:
                            counts["missing_assets"] += 1
                            issue("missing_asset", chart,
                                  f"Declared {match.group(1).upper()} asset not found: {declared[:120]}")
            if songs_found == 0:
                issue("empty_category", category, "No song subfolders at mode/category/song depth")
            if songs_found > 800:
                issue("large_category", category,
                      "Category exceeds 800 songs; the mod documentation describes automatic splits")
    return {
        "schema_version": 1, "subject": "ez2custommod_bms_library",
        "read_only": True, "game_verified": False, "asset_checks_enabled": bool(check_assets),
        "counts": counts, "per_mode": per_mode,
        "issues": issues, "omitted_issue_count": omitted,
        "warning_count": len(issues) + omitted
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", help="Local BMSData root containing mode/category/song")
    parser.add_argument("--check-assets", action="store_true",
                        help="Also scan bounded chart headers for declared WAV/BMP resources")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = inspect_bms_library(args.directory, check_assets=args.check_assets)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("EZ2CustomMod BMSData library preflight — READ ONLY")
            for key, value in result["counts"].items():
                print(f"{key}: {value}")
            print("Warning count:", result["warning_count"])
            for item in result["issues"][:30]:
                print(f" [{item['code']}] {item['path']}: {item['message']}")
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}) if args.json else f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
