#!/usr/bin/env python3
"""Read-only compatibility preflight for an authorized legacy EZ2 installation.

Inspects PE headers and 2EZConfig settings without executing, injecting,
patching, scanning memory, collecting serial numbers or using the network.
Run with Python 3.10+ on a modern helper PC. Does not prove game compatibility.
"""
from __future__ import annotations

import argparse
import json
import platform
import re
import struct
from pathlib import Path

MAX_PE_FILE = 2 * 1024 * 1024 * 1024
MAX_SETTINGS = 1024 * 1024
SAFE_FILENAME = re.compile(r"^[^/\\:\x00-\x1f]{1,200}$")
MACHINES = {0x14C: "x86", 0x8664: "x86_64", 0xAA64: "arm64"}
SUBSYSTEMS = {2: "windows_gui", 3: "windows_console"}


def inspect_pe(path: str | Path) -> dict:
    """Parse the PE identity only. Never load the executable or import-table DLLs."""
    file_path = Path(path)
    if not file_path.is_file():
        raise ValueError("PE file does not exist")
    size = file_path.stat().st_size
    if size < 0x40 or size > MAX_PE_FILE:
        raise ValueError("PE size outside safe header inspection bounds")
    with file_path.open("rb") as stream:
        dos = stream.read(64)
        if dos[:2] != b"MZ":
            raise ValueError("Missing DOS MZ header")
        offset = struct.unpack_from("<I", dos, 0x3C)[0]
        if offset < 64 or offset + 24 > size or offset > 16 * 1024 * 1024:
            raise ValueError("PE header offset is invalid")
        stream.seek(offset)
        header = stream.read(24)
        if header[:4] != b"PE\0\0" or len(header) != 24:
            raise ValueError("Missing NT PE signature")
        machine, sections, _, _, _, opt_size, characteristics = struct.unpack_from(
            "<HHIIIHH", header, 4)
        if opt_size < 70 or opt_size > 4096 or offset + 24 + opt_size > size:
            raise ValueError("Invalid optional header size")
        optional = stream.read(opt_size)
        opt_magic = struct.unpack_from("<H", optional, 0)[0]
        if opt_magic not in (0x10B, 0x20B):
            raise ValueError("Unsupported PE optional header magic")
        # Both PE32 and PE32+ define the subsystem field at byte offset 68.
        subsystem = struct.unpack_from("<H", optional, 68)[0]
        os_major, os_minor = struct.unpack_from("<HH", optional, 40)
        return {
            "valid_pe": True,
            "machine": MACHINES.get(machine, f"unknown_0x{machine:04x}"),
            "format": "PE32+" if opt_magic == 0x20B else "PE32",
            "sections": sections,
            "is_dll": bool(characteristics & 0x2000),
            "subsystem": SUBSYSTEMS.get(subsystem, f"other_{subsystem}"),
            "minimum_header_os_version": f"{os_major}.{os_minor}",
            "size_bytes": size
        }


def read_settings(path: Path) -> tuple[dict, str | None]:
    if not path.is_file():
        return {}, "Game settings file not found"
    if path.stat().st_size > MAX_SETTINGS:
        return {}, "Game settings larger than 1 MiB"
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, ValueError):
        return {}, "Game settings are not readable JSON"
    if not isinstance(value, dict):
        return {}, "Game settings root must be a JSON object"
    return value, None


def diagnose_installation(directory: str | Path, exe_name: str | None = None) -> dict:
    root = Path(directory).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Target must be a directory")
    settings, error = read_settings(root / "game-settings.json")
    diagnostics = []
    def add(severity, code, message, recommendation):
        diagnostics.append({
            "severity": severity, "code": code,
            "detail": message, "recommendation": recommendation
        })
    if error:
        add("warning", "settings_not_available", error,
            "Open the configurator to review or restore game-settings.json.")
    selected = exe_name if exe_name is not None else settings.get("exe_name", "")
    if not selected:
        game_id = settings.get("game_id", "")
        selected = ("EZ2AC.exe" if isinstance(game_id, str) and game_id.startswith("ez2ac_")
                    else "EZ2DJ.exe")
    if not isinstance(selected, str) or not SAFE_FILENAME.fullmatch(selected) or selected in (".", ".."):
        raise ValueError("Executable must be a simple filename within the selected directory")
    target = root / selected
    pe = None
    if not target.is_file():
        add("error", "game_executable_missing", f"Configured executable not present: {selected}",
            "Check the exact game build and Exe Name Override; do not rename game binaries.")
    else:
        try:
            pe = inspect_pe(target)
            if pe["machine"] != "x86" or pe["format"] != "PE32":
                add("error", "game_not_win32", f"{selected} is {pe['machine']} / {pe['format']}",
                    "2EZ.dll is an x86 module; select the correct supported 32-bit game.")
        except ValueError as exc:
            add("error", "game_pe_invalid", str(exc),
                "Do not launch unknown, malformed or unsupported executable files.")

    dll = None
    if not (root / "2EZ.dll").is_file():
        add("error", "injected_dll_missing", "2EZ.dll is absent",
            "Place a trusted 32-bit 2EZ.dll next to the launcher.")
    else:
        try:
            dll = inspect_pe(root / "2EZ.dll")
            if dll["machine"] != "x86" or not dll["is_dll"]:
                add("error", "injected_dll_arch", "2EZ.dll must be a 32-bit DLL",
                    "Use the verified x86 release artifact; never force-load a mismatched DLL.")
        except ValueError as exc:
            add("error", "injected_dll_invalid", str(exc),
                "Use a valid release or locally compiled 2EZ.dll.")

    if pe and dll and pe["machine"] != dll["machine"]:
        add("error", "architecture_mismatch", "Game and injected DLL architectures differ",
            "Do not inject across architectures.")
    if not (root / "2EZConfig.exe").is_file():
        add("warning", "launcher_missing", "2EZConfig.exe is absent",
            "Run the game through a matching 2EZConfig_Re release.")

    game_settings = settings if isinstance(settings, dict) else {}
    modern_host = platform.system() == "Windows" and platform.release() not in {"XP", "2000"}
    if game_settings.get("audio_eq") or game_settings.get("hypersonik"):
        add("info", "wasapi_backend_selected", "An optional WASAPI audio path is enabled",
            "Test device format, exclusive access and real latency; the feature requires Vista+.")
        if platform.system() == "Windows" and not modern_host:
            add("warning", "wasapi_not_available", "Legacy Windows host does not support WASAPI",
                "Disable WASAPI options on XP; preserve legacy DirectSound.")
    if game_settings.get("force_60hz") or game_settings.get("ddraw4_force_60hz"):
        add("info", "legacy_refresh_override", "A legacy 60 Hz display mode override is enabled",
            "Verify the monitor supports it; do not force unsafe modes on an original 15 kHz CRT.")
    if modern_host:
        add("info", "modern_windows_display_audio",
            "Modern Windows routes legacy graphics/audio through newer system components",
            "Verify DirectDraw7/Direct3D7 presentation, DPI, fullscreen focus and audio latency; "
            "do not assume Windows 11 DX10/11 windowed optimizations apply to DirectDraw7.")
    if game_settings.get("high_priority"):
        add("info", "priority_option", "High priority is configured",
            "Avoid using process priority as a substitute for profiling audio and rendering.")

    if not pe:
        add("info", "version_unverified", "Game version was not cryptographically verified",
            "Record a user-owned on-disk SHA-256 and use exact-build adapter preflight.")
    return {
        "schema_version": 1,
        "report": "2ezconfig_compatibility_doctor",
        "read_only": True, "gameplay_verified": False,
        "target": selected, "game_id": settings.get("game_id") if isinstance(settings.get("game_id"), str) else None,
        "host_system": platform.system(), "host_release": platform.release(),
        "game_pe": pe, "injected_dll_pe": dll,
        "issues": diagnostics,
        "error_count": sum(item["severity"] == "error" for item in diagnostics),
        "warning_count": sum(item["severity"] == "warning" for item in diagnostics),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", required=True, help="Authorized game installation folder")
    parser.add_argument("--exe", help="Override only for read-only analysis, not saved")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = diagnose_installation(args.game_dir, args.exe)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("2EZConfig Compatibility Doctor — no game/OS changes")
            for item in result["issues"]:
                print(f"[{item['severity']}] {item['code']}: {item['detail']}")
                print("   ", item["recommendation"])
            print("Game PE:", result["game_pe"])
            print("Errors:", result["error_count"], "Warnings:", result["warning_count"])
        return 1 if result["error_count"] else 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}) if args.json else f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
