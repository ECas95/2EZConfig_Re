#!/usr/bin/env python3
"""Read-only EZ2CustomMod / 2EZConfig_Re installation preflight.

Reports integration readiness for authorized EZ2AC Final:EX installations.
This never installs DLLs, launches games, modifies settings, or reads
proprietary executable contents.
"""
from __future__ import annotations

import argparse
import configparser
import json
import re
from pathlib import Path

EXPECTED_ID = "ez2ac_fn_ex"
MOD_DLL = "EZ2CustomMod.dll"
SAFE_FILE = re.compile(r"^[^/\\:\x00-\x1f]+$")


def inspect_installation(game_dir: str | Path, target_os="modern") -> dict:
    if target_os not in {"xp", "modern"}:
        raise ValueError("target_os must be xp or modern")
    root = Path(game_dir).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("game_dir is not a directory")
    checks = []
    def record(level, code, message, action=""):
        checks.append({"level": level, "code": code,
                       "message": message, "action": action})

    for name in ("2EZ.dll", "2EZConfig.exe"):
        if not (root / name).is_file():
            record("warning", "missing_launcher_component",
                   f"{name} was not found beside the game files",
                   "Verify the installed 2EZConfig_Re launcher files.")

    settings_path = root / "game-settings.json"
    settings = {}
    if not settings_path.is_file():
        record("warning", "game_settings_missing",
               "game-settings.json was not found", "Save settings once in 2EZConfig_Re.")
    elif settings_path.stat().st_size > 1024 * 1024:
        record("error", "game_settings_too_large", "game-settings.json exceeds 1 MiB")
    else:
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8-sig"))
            if not isinstance(settings, dict):
                raise ValueError("root is not an object")
        except (OSError, ValueError, UnicodeError) as exc:
            settings = {}
            record("error", "game_settings_invalid", "Cannot safely read game-settings.json",
                   "Use 2EZConfig_Re settings recovery; inspect the file before editing.")

    game_id = settings.get("game_id")
    if game_id != EXPECTED_ID:
        record("warning", "game_id_unconfirmed",
               "Launcher game ID is not explicitly confirmed as ez2ac_fn_ex",
               "Select Final:EX in 2EZConfig_Re before applying any mod.")

    exe = settings.get("exe_name", "EZ2AC.exe")
    if not isinstance(exe, str) or not SAFE_FILE.fullmatch(exe) or exe in (".", ".."):
        record("error", "exe_name_invalid",
               "Configured executable name is not a safe filename",
               "Use only a local executable filename in the launcher settings.")
        exe = ""
    elif not (root / exe).is_file():
        record("error", "game_executable_missing",
               f"Configured game executable '{exe}' does not exist",
               "Review Settings > Exe Name Override. The supplied mod guide uses EZ2B.exe.")
    if exe.lower() == "ez2ac.exe" and (root / "EZ2B.exe").is_file():
        record("warning", "fnex_executable_variant",
               "EZ2B.exe is present but the launcher is configured for EZ2AC.exe",
               "Verify your *exact* FNEX build before setting Exe Name Override to EZ2B.exe.")

    extras = settings.get("extra_dlls", "")
    if not isinstance(extras, str):
        extras = ""
        record("error", "extra_dlls_invalid", "extra_dlls is not a string")
    tokens = extras.split()
    matches = [token for token in tokens if token.casefold() == MOD_DLL.casefold()]
    if not (root / MOD_DLL).is_file():
        record("warning", "custommod_dll_missing", "EZ2CustomMod.dll not found",
               "Only install a separately obtained, trusted mod build for your verified game revision.")
    if not matches:
        record("warning", "custommod_not_enabled", "Mod is not listed in Extra DLLs",
               "To opt in, enter EZ2CustomMod.dll under Settings > Extra DLLs.")
    elif len(matches) > 1:
        record("error", "duplicate_mod_dll", "EZ2CustomMod.dll appears multiple times in Extra DLLs")
    for token in tokens:
        if not SAFE_FILE.fullmatch(token) or token in (".", ".."):
            record("warning", "extra_dll_path", "An Extra DLLs entry is not a plain filename",
                   "The launcher splits entries on whitespace; use filenames without spaces.")
            break

    ini_path = root / "BMSMod.ini"
    ini = configparser.ConfigParser(interpolation=None, strict=False)
    if ini_path.is_file():
        if ini_path.stat().st_size > 512 * 1024:
            record("error", "mod_config_too_large", "BMSMod.ini exceeds 512 KiB")
        else:
            try:
                ini.read_string(ini_path.read_text(encoding="utf-8-sig", errors="replace"))
            except (configparser.Error, OSError):
                record("warning", "mod_config_invalid", "BMSMod.ini could not be parsed")
    else:
        record("warning", "mod_config_missing", "BMSMod.ini was not found",
               "Use the mod author's own configuration from an authorized distribution.")
    try:
        if ini.has_option("Core", "Enable") and not ini.getboolean("Core", "Enable"):
            record("warning", "mod_disabled", "BMSMod.ini disables the mod",
                   "Set Core > Enable=1 only after reviewing the mod's documentation.")
    except ValueError:
        record("warning", "mod_config_value", "Core > Enable is not a valid boolean")

    for name in ("ffmpeg.exe", "pthreadGC2.dll", "wqy-microhei.ttc"):
        if not (root / name).is_file():
            record("warning", "optional_dependency_missing", f"{name} was not found",
                   "Some previews, CJK text or media decoding may not work.")
    if target_os == "xp" and not (root / "gdiplus.dll").is_file():
        record("warning", "xp_gdiplus_missing",
               "Windows XP target: no local gdiplus.dll found",
               "Use an appropriately licensed XP-compatible dependency from your own system.")
    data_root = ini.get("CustomSongs", "Root", fallback="BMSData").strip()
    if not data_root or not SAFE_FILE.fullmatch(data_root) or data_root in (".", ".."):
        record("warning", "bms_root_nonlocal", "CustomSongs.Root is not a simple local folder",
               "Review manually; this preflight does not traverse arbitrary configured paths.")
    elif not (root / data_root).is_dir():
        record("warning", "library_missing", f"Custom song directory '{data_root}' not found",
               "Use the expected mode/category/song folder layout for original or licensed BMS.")
    cache_root = ini.get("CustomSongs", "CacheRoot", fallback="CustomCache").strip()
    if SAFE_FILE.fullmatch(cache_root) and (root / cache_root / "idmap.txt").is_file():
        record("info", "persistent_idmap",
               "Persistent idmap.txt exists; keep it backed up",
               "Deleting or renaming idmap.txt may orphan favorites and ranking data.")
    elif not SAFE_FILE.fullmatch(cache_root):
        record("warning", "cache_root_nonlocal", "CustomSongs.CacheRoot needs manual review")

    return {
        "schema_version": 1, "subject": "fnex_ez2custommod_preflight",
        "read_only": True, "runtime_verified": False, "target_os": target_os,
        "game_id": game_id if isinstance(game_id, str) else None,
        "configured_exe": exe,
        "custommod_enabled": len(matches) == 1,
        "errors": sum(x["level"] == "error" for x in checks),
        "warnings": sum(x["level"] == "warning" for x in checks),
        "checks": checks
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", required=True, help="Directory of your own FNEX installation")
    parser.add_argument("--target-os", choices=("modern", "xp"), default="modern")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = inspect_installation(args.game_dir, args.target_os)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("EZ2CustomMod / 2EZConfig_Re preflight — READ ONLY, game compatibility UNVERIFIED")
            for issue in result["checks"]:
                print(f"[{issue['level']}] {issue['code']}: {issue['message']}")
                if issue["action"]:
                    print(f"  → {issue['action']}")
            print(f"Errors: {result['errors']} | Warnings: {result['warnings']}")
        return 1 if result["errors"] else 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}) if args.json else f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
