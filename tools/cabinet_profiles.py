#!/usr/bin/env python3
"""Offline cabinet profile export/diff/apply utility.

The UI integration is not yet complete; this tool safely manages existing JSON.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import tempfile
from pathlib import Path


def read_object(path):
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON root must be an object")
    return value


def checked_profile(path):
    profile = read_object(path)
    if profile.get("format_version") != 1:
        raise ValueError("Unsupported profile format_version")
    if not isinstance(profile.get("game_settings"), dict):
        raise ValueError("profile.game_settings must be an object")
    if not isinstance(profile.get("global_settings"), dict):
        raise ValueError("profile.global_settings must be an object")
    return profile


def atomic_write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=path.parent, prefix=".2ez-",
                                         suffix=".tmp", encoding="utf-8",
                                         delete=False) as handle:
            temp = Path(handle.name)
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())

        if path.exists():
            # Ensure an invalid existing JSON file is never treated as a good backup.
            read_object(path)
            backup_temp = None
            try:
                with tempfile.NamedTemporaryFile("wb", dir=path.parent, prefix=".2ez-bak-",
                                                 delete=False) as handle:
                    backup_temp = Path(handle.name)
                shutil.copy2(path, backup_temp)
                os.replace(backup_temp, Path(str(path) + ".bak"))
            finally:
                if backup_temp:
                    backup_temp.unlink(missing_ok=True)
        os.replace(temp, path)
    finally:
        if temp:
            temp.unlink(missing_ok=True)


def create_profile(game_file, global_file):
    return {
        "format_version": 1,
        "exported_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "game_settings": read_object(game_file),
        "global_settings": read_object(global_file)
    }


def differences(actual, desired, prefix=""):
    if isinstance(actual, dict) and isinstance(desired, dict):
        keys = sorted(actual.keys() | desired.keys())
        changed = []
        for key in keys:
            current = f"{prefix}.{key}" if prefix else str(key)
            if key not in actual:
                changed.append({"path": current, "change": "added"})
            elif key not in desired:
                changed.append({"path": current, "change": "removed"})
            else:
                changed.extend(differences(actual[key], desired[key], current))
        return changed
    return [] if actual == desired else [{"path": prefix, "change": "modified"}]


def get_paths(args):
    game = Path(args.game_dir).resolve() / "game-settings.json"
    if args.global_file:
        global_file = Path(args.global_file).expanduser().resolve()
    elif os.environ.get("APPDATA"):
        global_file = Path(os.environ["APPDATA"]) / "2ezconfig" / "global-settings.json"
    else:
        raise ValueError("--global-file is required outside Windows with APPDATA")
    return game, global_file


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["export", "diff", "apply"])
    parser.add_argument("--game-dir", default=".")
    parser.add_argument("--global-file", help="Default: %APPDATA%/2ezconfig/global-settings.json")
    parser.add_argument("--profile", required=True, help="Profile JSON input/output")
    parser.add_argument("--apply", action="store_true",
                        help="Required to write settings; without it apply is a dry run")
    args = parser.parse_args(argv)

    try:
        game_path, global_path = get_paths(args)
        profile_path = Path(args.profile).expanduser().resolve()

        if args.command == "export":
            if profile_path.exists():
                raise ValueError("Refusing to overwrite an existing exported profile")
            profile = create_profile(game_path, global_path)
            atomic_write(profile_path, profile)
            print(f"Exported profile to: {profile_path}")
            print("Warning: exported HID identifiers and other settings may reveal device metadata.")
            return 0

        profile = checked_profile(profile_path)
        changes = differences(read_object(game_path), profile["game_settings"], "game")
        changes += differences(read_object(global_path), profile["global_settings"], "global")
        print(json.dumps({"changed_paths": changes, "count": len(changes)}, indent=2))
        if args.command == "apply" and args.apply:
            if not changes:
                print("No settings changes to apply.")
            else:
                atomic_write(game_path, profile["game_settings"])
                atomic_write(global_path, profile["global_settings"])
                print("Profile applied. Previous valid files saved with .bak suffix.")
        elif args.command == "apply":
            print("Dry run only. Repeat with --apply to write both settings files.")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
