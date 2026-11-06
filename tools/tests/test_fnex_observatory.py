"""Synthetic regression tests for offline FNEX mode and event observatory."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fnex_mode_inventory import inspect_mode_directory
from fnex_trace_replay import load_observations, replay, replay_file, main as trace_main

GDS = """[General]
NumberOfSlot=1
[Slot1]
NumberOfTrack=3
Track8={Key=15,16
SongTrack=10}
Track2={Key=10,-1
SongTrack=3}
Track1={Key=11,-1
SongTrack=4}
"""

GDS_COLLISION = GDS.replace("Key=10,-1", "Key=15,-1")
TRACE = [
    {"type": "song.preview", "song_id": "preview_only", "chart_id": "5k_n"},
    {"type": "song.confirmed", "song_id": "demo", "chart_id": "5k_n"},
    {"type": "song.confirmed", "song_id": "demo", "chart_id": "5k_n"},
    {"type": "stage.started"},
    {"type": "result.finalized", "player_slot": 1, "score": 123456, "clear_type": "clear"},
    {"type": "result.finalized", "player_slot": 2, "score": 234567, "clear_type": "full_combo"},
    {"type": "stage.ended", "reason": "completed"}
]


def sample_trace(path: Path, observations=TRACE):
    path.write_text("\n".join(json.dumps(row) for row in observations) + "\n",
                    encoding="utf-8")


class ModeInventoryTests(unittest.TestCase):
    def test_multimode_order_and_no_paths(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            a = root / "5keymix"
            b = root / "7StreetMix"
            a.mkdir()
            b.mkdir()
            (a / "keys.gds").write_text(GDS)
            (b / "keys.gds").write_text(GDS.replace("SongTrack=3", "SongTrack=12"))
            result = inspect_mode_directory(root)
            self.assertEqual(result["descriptor_count"], 2)
            self.assertTrue(result["read_only"])
            self.assertFalse(result["verified_with_game"])
            self.assertEqual([m["mode"] for m in result["descriptors"]],
                             ["5keymix", "7StreetMix"])
            keys = result["descriptors"][0]["slots"][0]["lanes"]
            self.assertEqual([x["song_track"] for x in keys], [10, 3, 4])
            self.assertEqual(keys[0]["key_pair"], [15, 16])
            # Avoid revealing entire directory paths in the generated report.
            self.assertNotIn(str(root), json.dumps(result))

    def test_collision_warning_and_empty_directory(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root)
            self.assertEqual(inspect_mode_directory(p)["status"], "no_descriptors_found")
            mode = p / "5keymix"
            mode.mkdir()
            (mode / "slot.gds").write_text(GDS_COLLISION)
            result = inspect_mode_directory(p)
            self.assertIn("input key 15 appears in multiple lanes",
                          " ".join(result["warnings"]))

    def test_reject_invalid_gds(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root) / "5keymix"
            p.mkdir()
            (p / "broken.gds").write_text("[Slot1]\nNumberOfTrack=99\n")
            with self.assertRaisesRegex(ValueError, "declared"):
                inspect_mode_directory(root)


class TraceReplayTests(unittest.TestCase):
    def test_final_scores_emitted_only_from_finalization(self):
        with tempfile.TemporaryDirectory() as root:
            src = Path(root) / "observations.jsonl"
            dst = Path(root) / "events.jsonl"
            sample_trace(src)
            observations, digest = load_observations(src)
            result = replay(observations, digest)
            self.assertEqual([r["event"] for r in result["events"]],
                             ["song.selected", "score.observed", "score.observed",
                              "session.ended"])
            self.assertEqual(result["sessions_confirmed"], 1)
            self.assertFalse(result["verified_gameplay"])
            selected = result["events"][0]
            self.assertEqual(selected["game_id"], "ez2ac_fn_ex")
            self.assertEqual(selected["data"]["song_id"], "demo")
            self.assertNotIn("preview_only", json.dumps(result))
            self.assertTrue(all(r["data"]["synthetic"] for r in result["events"]))
            self.assertTrue(all(r["data"]["verified"] is False for r in result["events"]))
            ids = {r["data"]["session_id"] for r in result["events"]}
            self.assertEqual(len(ids), 1)
            self.assertEqual(result["events"][-1]["data"]["result_count"], 2)
            persisted = replay_file(src, dst)
            self.assertEqual(persisted["event_count"], 4)
            self.assertEqual(len(dst.read_text().splitlines()), 4)
            with self.assertRaises(FileExistsError):
                replay_file(src, dst)
            self.assertEqual(trace_main(["--input", str(src), "--output", str(src)]), 1)

    def test_rejects_unconfirmed_or_duplicate_result(self):
        with tempfile.TemporaryDirectory() as root:
            src = Path(root) / "bad.jsonl"
            invalid = [
                {"type": "result.finalized", "player_slot": 1,
                 "score": 100, "clear_type": "clear"}]
            sample_trace(src, invalid)
            observations, digest = load_observations(src)
            with self.assertRaisesRegex(ValueError, "requires active stage"):
                replay(observations, digest)
            invalid = TRACE[:5] + [TRACE[4]] + TRACE[5:]
            sample_trace(src, invalid)
            observations, digest = load_observations(src)
            with self.assertRaisesRegex(ValueError, "duplicate finalized"):
                replay(observations, digest)
            self.assertFalse((Path(root) / "events.jsonl").exists())

    def test_abort_has_no_fabricated_score(self):
        obs = [
            {"type": "song.confirmed", "song_id": "demo", "chart_id": "5k_n"},
            {"type": "stage.started"},
            {"type": "stage.ended", "reason": "aborted"}
        ]
        result = replay(obs, "e" * 64)
        self.assertEqual([row["event"] for row in result["events"]],
                         ["song.selected", "session.ended"])
        self.assertEqual(result["events"][-1]["data"]["result_count"], 0)

    def test_invalid_data_rejected(self):
        obs = [
            {"type": "song.confirmed", "song_id": "x/escape", "chart_id": "5k_n"}]
        with self.assertRaises(ValueError):
            replay(obs, "a" * 64)
        obs = TRACE[:4] + [{"type": "result.finalized", "player_slot": 1,
                             "score": True, "clear_type": "clear"}]
        with self.assertRaises(ValueError):
            replay(obs, "b" * 64)
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "trace.jsonl"
            path.write_text("{ invalid json \n")
            with self.assertRaisesRegex(ValueError, "invalid JSON"):
                load_observations(path)


if __name__ == "__main__":
    unittest.main()
