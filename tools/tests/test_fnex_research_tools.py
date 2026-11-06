"""Synthetic tests for FNEX research helpers: no original assets or executables."""
import hashlib
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adapter_compatibility import inspect_compatibility, validate_manifest
from gds_inspector import inspect_gds_file, inspect_gds_text
from gds_visualizer import render_svg, main as visualizer_main
from ranking_inspector import inspect_rank_bytes, inspect_rank_file


GDS_SAMPLE = """
[General]
NumberOfSlot=2

[Slot1]
NumberOfTrack=3
Track8 =
{
  Key=15,16
  SongTrack=10
}
Track2={Key=10,-1
SongTrack=3}
Track1 = { Key=11,-1
  SongTrack=4 }

[Slot2]
NumberOfTrack=1
Track1={Key=23,24
 SongTrack=10}

[Background]
SomeUnrelatedData=1
"""


class GdsInspectorTests(unittest.TestCase):
    def test_uses_file_order_not_track_suffix(self):
        result = inspect_gds_text(GDS_SAMPLE)
        self.assertEqual(len(result["slots"]), 2)
        lanes = result["slots"][0]["lanes"]
        self.assertEqual([lane["file_label"] for lane in lanes],
                         ["Track8", "Track2", "Track1"])
        self.assertEqual([lane["song_track"] for lane in lanes], [10, 3, 4])
        self.assertEqual(lanes[0]["input_keys"], [15, 16])
        self.assertEqual([lane["lane_index"] for lane in lanes], [0, 1, 2])

    def test_count_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "declared"):
            inspect_gds_text(GDS_SAMPLE.replace("NumberOfTrack=3", "NumberOfTrack=4"))

    def test_bad_key_and_missing_section_rejected(self):
        with self.assertRaisesRegex(ValueError, "out of supported range"):
            inspect_gds_text(GDS_SAMPLE.replace("Key=15,16", "Key=-2,16"))
        with self.assertRaisesRegex(ValueError, "No \\[SlotN\\]"):
            inspect_gds_text("[General]\nNumberOfSlot=2\n")

    def test_static_svg_lane_map(self):
        import xml.etree.ElementTree as ET
        mapping = inspect_gds_text(GDS_SAMPLE)
        svg = render_svg(mapping)
        self.assertIn("lane 0: Track8", svg)
        self.assertIn("keys [15, 16]", svg)
        ET.fromstring(svg)
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "sample.gds"
            dst = Path(tmp) / "lanes.svg"
            src.write_text(GDS_SAMPLE)
            self.assertEqual(visualizer_main([str(src), "--output", str(dst)]), 0)
            self.assertTrue(dst.is_file())
            self.assertEqual(visualizer_main([str(src), "--output", str(dst)]), 1)

    def test_file_read_and_nonutf8(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mode.gds"
            path.write_bytes(GDS_SAMPLE.encode("ascii") + b"\n; cp1252 \xe9\n")
            self.assertEqual(len(inspect_gds_file(path)["slots"]), 2)


class RankingInspectorTests(unittest.TestCase):
    def test_song_top5_unverified_and_redacted(self):
        names = b"".join(f"P{i}".encode().ljust(8, b"\0") for i in range(5))
        scores = [500, 400, 300, 200, 100]
        raw = names + struct.pack("<5i", *scores)
        masked = inspect_rank_bytes(raw, "song_top5")
        self.assertEqual([x["score"] for x in masked["entries"]], scores)
        self.assertFalse(masked["verified"])
        self.assertNotIn("name_legacy", masked["entries"][0])
        unmasked = inspect_rank_bytes(raw, "song_top5", include_names=True)
        self.assertEqual(unmasked["entries"][0]["name_legacy"], "P0")

    def test_mode_top99_and_size_guard(self):
        raw = bytes(99 * 8) + struct.pack("<99i", *range(99, 0, -1))
        self.assertEqual(len(inspect_rank_bytes(raw, "mode_top99")["entries"]), 99)
        with self.assertRaisesRegex(ValueError, "exactly"):
            inspect_rank_bytes(raw[:60], "mode_top99")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rank.bin"
            path.write_bytes(raw)
            self.assertEqual(inspect_rank_file(path, "mode_top99")["entries"][0]["score"], 99)


class AdapterCompatibilityTests(unittest.TestCase):
    def test_matches_exact_on_disk_sha256(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            executable = base / "test_game.exe"
            executable.write_bytes(b"synthetic executable bytes")
            digest = hashlib.sha256(executable.read_bytes()).hexdigest()
            manifest = {"schema_version": 1, "adapters": [
                {"adapter_id": "test_adaptor", "game_id": "ez2ac_fn_ex",
                 "fingerprint_type": "on_disk_file", "exe_sha256": digest,
                 "capabilities": ["song.selected"], "validation_status": "research"}
            ]}
            path = base / "adapters.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            result = inspect_compatibility(executable, path)
            self.assertTrue(result["matched"])
            self.assertFalse(result["verified"])
            executable.write_bytes(b"updated executable")
            self.assertFalse(inspect_compatibility(executable, path)["matched"])

    def test_rejects_unpacked_fingerprint_and_invalid_caps(self):
        base = {"schema_version": 1, "adapters": [
            {"adapter_id": "test", "game_id": "ez2ac_fn_ex",
             "fingerprint_type": "runtime_unpacked",
             "exe_sha256": "a" * 64, "capabilities": []}
        ]}
        with self.assertRaisesRegex(ValueError, "only on_disk_file"):
            validate_manifest(base)
        base["adapters"][0]["fingerprint_type"] = "on_disk_file"
        base["adapters"][0]["capabilities"] = ["drm.bypass"]
        with self.assertRaisesRegex(ValueError, "unsupported"):
            validate_manifest(base)


if __name__ == "__main__":
    unittest.main()
