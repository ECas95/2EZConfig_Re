#!/usr/bin/env python3
"""Privacy-conscious, read-only performance summary of EZ2CustomMod.log.

Produces aggregates, not raw player/song names or log messages. This is an
offline diagnostic helper, not live monitoring or proof of a healthy cabinet.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

MAX_LOG_SIZE = 32 * 1024 * 1024
SLOW = re.compile(r"\[slowframe\]\s+(\d+(?:\.\d+)?)\s*ms", re.I)
FRAME = re.compile(
    r"\[frametime\].*?avg\s+(\d+(?:\.\d+)?)\s*ms,\s*worst\s+"
    r"(\d+(?:\.\d+)?)\s*ms,\s*>25ms:\s*(\d+)", re.I)
VERSION = re.compile(r"\[version\]\s+(EZ2CustomMod_v[\w.-]{1,80})", re.I)
TIER = re.compile(r"\[config\]\s+memory tier=([\w.-]{1,20})", re.I)
CATEGORIES = ("[scancache]", "[bms]", "[filter]", "[wheeltex]", "[assets]",
              "[preview]", "[bga-direct]", "[judge]", "[lanecover]")


def summarize_log_text(text: str) -> dict:
    frame_samples, slow_frames = [], []
    tags = {name: 0 for name in CATEGORIES}
    failures, truncated, version, memory_tier = 0, 0, None, None
    for line in text.splitlines():
        match = VERSION.search(line)
        if match and version is None:
            version = match.group(1)
        match = TIER.search(line)
        if match:
            memory_tier = match.group(1)
        match = FRAME.search(line)
        if match:
            frame_samples.append({
                "avg_ms": float(match.group(1)),
                "worst_ms": float(match.group(2)),
                "over_25ms": int(match.group(3))
            })
        match = SLOW.search(line)
        if match:
            slow_frames.append(float(match.group(1)))
        if "RENDER FAILED" in line or "texture upload FAILED" in line:
            failures += 1
        if "TRUNCATED" in line:
            truncated += 1
        for tag in tags:
            if tag in line:
                tags[tag] += 1

    recommendations = []
    if slow_frames or (frame_samples and max(s["worst_ms"] for s in frame_samples) > 40):
        recommendations.append(
            "Review slowframe/frametime breakdown on the actual cabinet; "
            "video previews and file work should not block the game thread.")
    if failures:
        recommendations.append(
            "Investigate GDI/texture and art allocation failures using a private, sanitized log.")
    if truncated:
        recommendations.append(
            "Check oversized categories and song/texture caps; some content may be truncated.")
    if not frame_samples:
        recommendations.append(
            "No frametime samples found; this may be a startup-only or incomplete log.")

    return {
        "schema_version": 1, "subject": "ez2custommod_offline_log_summary",
        "read_only": True, "game_verified": False, "no_raw_lines": True,
        "reported_mod_version": version,
        "memory_tier": memory_tier,
        "frame_samples": len(frame_samples),
        "last_avg_frame_ms": frame_samples[-1]["avg_ms"] if frame_samples else None,
        "maximum_reported_worst_frame_ms": (
            max(s["worst_ms"] for s in frame_samples) if frame_samples else None),
        "reported_over_25ms_total": sum(s["over_25ms"] for s in frame_samples),
        "slowframe_samples": len(slow_frames),
        "max_slowframe_ms": max(slow_frames) if slow_frames else None,
        "render_or_texture_failures": failures,
        "truncation_warnings": truncated,
        "tag_counts": tags,
        "recommendations": recommendations
    }


def summarize_log_file(path: str | Path) -> dict:
    path = Path(path)
    if not path.is_file():
        raise ValueError("Log file not found")
    if path.stat().st_size > MAX_LOG_SIZE:
        raise ValueError("Log file exceeds 32 MiB analysis limit")
    data = path.read_bytes().decode("utf-8-sig", errors="replace")
    return summarize_log_text(data)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_file", help="Local logs/EZ2CustomMod.log")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = summarize_log_file(args.log_file)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("EZ2CustomMod read-only diagnostic summary; no raw log lines")
            for key, value in result.items():
                if key not in ("tag_counts", "recommendations"):
                    print(f"{key}: {value}")
            for recommendation in result["recommendations"]:
                print("NOTE:", recommendation)
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}) if args.json else f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
