#!/usr/bin/env python3
"""Validate a proposed, rights-cleared custom song pack manifest.

This checks content and paths. It does NOT inject assets into a specific game.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,63}$")
MODES = {"5k", "7k", "5k_course", "7k_course", "ez2catch", "turntable", "dancer", "other"}
AUDIO_EXT = {".ogg", ".mp3", ".wav", ".flac"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}
CHART_EXT = {".json", ".txt", ".bin", ".dat"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked_name(value, kind):
    require(isinstance(value, str) and bool(ID.fullmatch(value)), f"{kind}: invalid ID")
    return value


def checked_text(value, field):
    require(isinstance(value, str) and 1 <= len(value.strip()) <= 160, f"{field}: invalid text")


def checked_file(root, reference, field, allowed_ext, sha256=None):
    require(isinstance(reference, str) and 1 <= len(reference) <= 240, f"{field}: invalid path")
    require("\\" not in reference and not reference.startswith("/") and ":" not in reference,
            f"{field}: paths must be relative POSIX paths")
    components = PurePosixPath(reference).parts
    require(bool(components) and all(part not in {"..", ".", ""} for part in components),
            f"{field}: unsafe path")
    require(Path(reference).suffix.lower() in allowed_ext, f"{field}: unsupported extension")
    candidate = (root / reference).resolve()
    require(candidate.is_relative_to(root), f"{field}: path escapes pack directory")
    require(candidate.is_file(), f"{field}: file not found: {reference}")
    require(candidate.stat().st_size <= 1024 * 1024 * 1024, f"{field}: file exceeds 1 GiB")
    if sha256 is not None:
        require(isinstance(sha256, str) and bool(re.fullmatch(r"[0-9a-fA-F]{64}", sha256)),
                f"{field}: invalid SHA-256")
        digest = hashlib.sha256()
        with candidate.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        require(digest.hexdigest().lower() == sha256.lower(), f"{field}: SHA-256 mismatch")
    return str(candidate.relative_to(root))


def validate_pack(directory):
    root = Path(directory).resolve(strict=True)
    require(root.is_dir(), "pack directory not found")
    manifest_path = root / "pack.json"
    require(manifest_path.is_file(), "pack.json missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(isinstance(manifest, dict), "root must be a JSON object")
    require(manifest.get("format_version") == 1, "format_version must be 1")
    checked_name(manifest.get("id"), "pack")
    checked_text(manifest.get("name"), "pack.name")
    checked_text(manifest.get("license"), "pack.license")
    songs = manifest.get("songs")
    require(isinstance(songs, list) and 1 <= len(songs) <= 1000, "songs must be an array (1..1000)")
    song_ids = set()
    total_charts = 0
    files = set()
    for song in songs:
        require(isinstance(song, dict), "song must be an object")
        song_id = checked_name(song.get("id"), "song")
        require(song_id not in song_ids, f"duplicate song ID: {song_id}")
        song_ids.add(song_id)
        checked_text(song.get("title"), f"{song_id}.title")
        checked_text(song.get("artist"), f"{song_id}.artist")
        audio = checked_file(root, song.get("audio"), f"{song_id}.audio", AUDIO_EXT, song.get("audio_sha256"))
        files.add(audio)
        jacket = song.get("jacket")
        if jacket:
            files.add(checked_file(root, jacket, f"{song_id}.jacket", IMAGE_EXT))
        charts = song.get("charts")
        require(isinstance(charts, list) and 1 <= len(charts) <= 32, f"{song_id}.charts: expected 1..32")
        chart_ids = set()
        for chart in charts:
            require(isinstance(chart, dict), f"{song_id}.chart must be an object")
            chart_id = checked_name(chart.get("id"), "chart")
            require(chart_id not in chart_ids, f"duplicate chart ID: {chart_id}")
            chart_ids.add(chart_id)
            require(chart.get("mode") in MODES, f"{chart_id}: unsupported mode")
            level = chart.get("level")
            require(type(level) is int and 1 <= level <= 99, f"{chart_id}: invalid level")
            files.add(checked_file(root, chart.get("file"), f"{chart_id}.file", CHART_EXT,
                                   chart.get("sha256")))
            total_charts += 1
    return {"valid": True, "pack_id": manifest["id"], "songs": len(song_ids),
            "charts": total_charts, "files_checked": len(files),
            "game_integration": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", help="Directory with pack.json")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    args = parser.parse_args()
    try:
        result = validate_pack(args.directory)
        print(json.dumps(result, indent=2) if args.json else
              f"OK: {result['pack_id']} — {result['songs']} songs, {result['charts']} charts")
        return 0
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}) if args.json else f"INVALID: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
