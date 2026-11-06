#!/usr/bin/env python3
"""Generate a standalone SVG lane/key map from a user-supplied .gds descriptor.

Original visualization code with no game assets or network access. The input
is parsed by gds_inspector and the output is an illustration, not a game patch.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape

from gds_inspector import inspect_gds_file

COL_WIDTH = 320
MARGIN = 28
ROW_HEIGHT = 38
FONT = "Arial, sans-serif"


def render_svg(mapping: dict) -> str:
    slots = mapping.get("slots", [])
    if not isinstance(slots, list) or not slots:
        raise ValueError("A valid lane mapping with at least one Slot is required")
    width = max(480, MARGIN * 2 + len(slots) * COL_WIDTH)
    longest = max(len(slot.get("lanes", [])) for slot in slots)
    height = 126 + (longest + 1) * ROW_HEIGHT + 40
    result = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="GDS lane mapping">',
        '<rect width="100%" height="100%" fill="#091725"/>',
        '<text x="28" y="45" fill="#dff4ff" font-family="Arial, sans-serif" font-size="23" '
        'font-weight="bold">GDS Lane / Track Mapping</text>',
        '<text x="28" y="74" fill="#9eb9ce" font-family="Arial, sans-serif" font-size="13">'
        'Read-only research preview — lane order follows file order, not TrackN suffix</text>'
    ]
    for index, slot in enumerate(slots):
        x = MARGIN + index * COL_WIDTH
        lanes = slot["lanes"]
        panel_height = 76 + max(1, len(lanes)) * ROW_HEIGHT
        result += [
            f'<rect x="{x}" y="96" width="{COL_WIDTH - 14}" height="{panel_height}" '
            'rx="12" fill="#142b3e" stroke="#38617a" stroke-width="1"/>',
            f'<text x="{x + 15}" y="125" fill="#78d8ed" font-family="{FONT}" '
            f'font-size="18" font-weight="bold">Player Slot {int(slot["slot"])}</text>',
            f'<text x="{x + 15}" y="146" fill="#a7becb" font-family="{FONT}" '
            f'font-size="12">{len(lanes)} chart lanes</text>'
        ]
        for lane in lanes:
            row_index = int(lane["lane_index"])
            y = 160 + row_index * ROW_HEIGHT
            label = escape(str(lane["file_label"]))
            keys = ", ".join(str(key) for key in lane["input_keys"])
            track = str(int(lane["song_track"]))
            result += [
                f'<rect x="{x + 12}" y="{y}" width="{COL_WIDTH - 38}" height="32" '
                'rx="6" fill="#203c51"/>',
                f'<text x="{x + 21}" y="{y + 21}" fill="#e9f7ff" '
                f'font-family="{FONT}" font-size="12">lane {row_index}: {label}</text>',
                f'<text x="{x + 144}" y="{y + 21}" fill="#a8e6c1" '
                f'font-family="{FONT}" font-size="11">keys [{escape(keys)}] → {track}</text>'
            ]
        if not lanes:
            result.append(
                f'<text x="{x + 16}" y="183" fill="#a7becb" '
                f'font-family="{FONT}" font-size="12">No tracks declared</text>')
    result += [
        f'<text x="28" y="{height - 18}" fill="#7994aa" font-family="{FONT}" '
        'font-size="12">Generated locally by 2EZConfig_Re • No game data is embedded</text>',
        '</svg>'
    ]
    return "\n".join(result) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gds_file", help="Mode descriptor from your own installation")
    parser.add_argument("--output", required=True, help="New SVG path to create")
    parser.add_argument("--force", action="store_true", help="Explicitly overwrite an existing SVG")
    args = parser.parse_args(argv)
    try:
        mapping = inspect_gds_file(args.gds_file)
        output = Path(args.output)
        if output.suffix.lower() != ".svg":
            raise ValueError("Output path must end in .svg")
        if output.exists() and not args.force:
            raise ValueError("Output already exists; use --force to replace your generated SVG")
        if not output.parent.is_dir():
            raise ValueError("Output directory does not exist")
        svg = render_svg(mapping)
        output.write_text(svg, encoding="utf-8")
        print(json.dumps({
            "created": True,
            "path": str(output),
            "slots": len(mapping["slots"]),
            "warnings": mapping["warnings"]
        }, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
