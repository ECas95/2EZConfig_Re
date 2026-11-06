#!/usr/bin/env python3
"""Offline executable fingerprint and proposed adapter compatibility checker.

No memory hooks or patch writes. An adapter manifest is not evidence of
compatibility until separately tested on the exact installed game version.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

MAX_MANIFEST_BYTES = 1024 * 1024
MAX_EXECUTABLE_BYTES = 2 * 1024 * 1024 * 1024
ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,95}$")
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
CAPABILITIES = {
    "runtime.ready", "song.selected", "chart.loaded", "score.observed",
    "session.ended", "cabinet.input.diagnostic"
}


def validate_manifest(value: dict) -> list:
    if not isinstance(value, dict) or type(value.get("schema_version")) is not int \
            or value.get("schema_version") != 1:
        raise ValueError("Manifest root must have schema_version=1")
    entries = value.get("adapters")
    if not isinstance(entries, list) or len(entries) > 500:
        raise ValueError("adapters must be an array of at most 500 records")
    adapter_ids = set()
    normalized = []
    for i, item in enumerate(entries):
        if not isinstance(item, dict):
            raise ValueError(f"adapters[{i}] must be an object")
        name = item.get("adapter_id")
        game_id = item.get("game_id")
        if not isinstance(name, str) or not ID_RE.fullmatch(name):
            raise ValueError(f"adapters[{i}]: invalid adapter_id")
        if name in adapter_ids:
            raise ValueError(f"Duplicate adapter_id: {name}")
        adapter_ids.add(name)
        if not isinstance(game_id, str) or not ID_RE.fullmatch(game_id):
            raise ValueError(f"{name}: invalid game_id")
        fingerprint = item.get("exe_sha256")
        if not isinstance(fingerprint, str) or not SHA256_RE.fullmatch(fingerprint):
            raise ValueError(f"{name}: expected 64-character SHA-256")
        if item.get("fingerprint_type") != "on_disk_file":
            raise ValueError(
                f"{name}: only on_disk_file fingerprints are supported. "
                "Do not use a research dump's unpacked-image checksum here.")
        events = item.get("capabilities", [])
        if not isinstance(events, list) or any(
                not isinstance(x, str) or x not in CAPABILITIES for x in events):
            raise ValueError(f"{name}: unsupported capabilities list")
        if len(set(events)) != len(events):
            raise ValueError(f"{name}: duplicate capability")
        status = item.get("validation_status", "research")
        if status not in {"research", "prototype", "tested"}:
            raise ValueError(f"{name}: invalid validation_status")
        normalized.append({
            "adapter_id": name, "game_id": game_id,
            "exe_sha256": fingerprint.lower(),
            "capabilities": list(events),
            "validation_status": status,
            "fingerprint_type": "on_disk_file"
        })
    return normalized


def sha256_file(path: str | Path) -> str:
    path = Path(path)
    if not path.is_file():
        raise ValueError("Executable file not found")
    if path.stat().st_size > MAX_EXECUTABLE_BYTES:
        raise ValueError("Executable exceeds the 2 GiB safety limit")
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_compatibility(executable_path: str | Path, manifest_path: str | Path) -> dict:
    manifest_path = Path(manifest_path)
    if not manifest_path.is_file():
        raise ValueError("Adapter manifest not found")
    if manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
        raise ValueError("Adapter manifest exceeds 1 MiB")
    entries = validate_manifest(json.loads(manifest_path.read_text(encoding="utf-8")))
    digest = sha256_file(executable_path)
    matches = [
        {k: entry[k] for k in ("adapter_id", "game_id", "capabilities", "validation_status")}
        for entry in entries if entry["exe_sha256"] == digest
    ]
    return {
        "schema_version": 1, "sha256": digest, "matching_adapters": matches,
        "matched": bool(matches), "verified": False,
        "message": ("Matching manifest metadata found. It does not install or verify any hook."
                    if matches else "No exact on-disk fingerprint match; no hooks should be installed.")
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, help="User-supplied executable to hash (read-only)")
    parser.add_argument("--manifest", required=True, help="JSON adapter registry")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = inspect_compatibility(args.exe, args.manifest)
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}) if args.json else f"INVALID: {exc}")
        return 1
    if args.json:
        print(json.dumps({"valid": True, **result}, indent=2))
    else:
        print("Executable SHA-256:", result["sha256"])
        print(result["message"])
        for match in result["matching_adapters"]:
            print(" ", match["adapter_id"], match["game_id"], match["validation_status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
