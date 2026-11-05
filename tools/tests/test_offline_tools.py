"""Offline tool regression tests; no arcade assets or game executables needed."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cabinet_profiles import atomic_write, create_profile, differences, main as profiles_main
from songpack_validator import validate_pack


class SongPackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "music").mkdir()
        (self.root / "charts").mkdir()
        (self.root / "music" / "original.ogg").write_bytes(b"synthetic test bytes")
        (self.root / "charts" / "easy.json").write_text("{}")
        self.manifest = {
            "format_version": 1,
            "id": "my_original_pack",
            "name": "My Original Songs",
            "license": "CC-BY-4.0",
            "songs": [{
                "id": "song_01", "title": "Demo", "artist": "Test",
                "audio": "music/original.ogg",
                "charts": [{"id": "easy", "mode": "5k", "level": 3, "file": "charts/easy.json"}]
            }]
        }
        self.save_manifest()

    def tearDown(self):
        self.tmp.cleanup()

    def save_manifest(self):
        (self.root / "pack.json").write_text(json.dumps(self.manifest))

    def test_valid_pack(self):
        result = validate_pack(self.root)
        self.assertEqual(result["songs"], 1)
        self.assertEqual(result["charts"], 1)
        self.assertFalse(result["game_integration"])

    def test_reject_path_escape(self):
        self.manifest["songs"][0]["audio"] = "../outside.ogg"
        self.save_manifest()
        with self.assertRaises(ValueError):
            validate_pack(self.root)

    def test_reject_duplicate_chart_and_bad_level(self):
        chart = self.manifest["songs"][0]["charts"][0]
        self.manifest["songs"][0]["charts"].append(dict(chart))
        self.save_manifest()
        with self.assertRaises(ValueError):
            validate_pack(self.root)
        self.manifest["songs"][0]["charts"] = [dict(chart, level=True)]
        self.save_manifest()
        with self.assertRaises(ValueError):
            validate_pack(self.root)

    def test_reject_bad_hash(self):
        self.manifest["songs"][0]["audio_sha256"] = "0" * 64
        self.save_manifest()
        with self.assertRaises(ValueError):
            validate_pack(self.root)


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.game_dir = self.root / "game"
        self.game_dir.mkdir()
        self.appdata = self.root / "global-settings.json"
        self.game = self.game_dir / "game-settings.json"
        atomic_write(self.game, {"game_id": "ez2dj_7th", "feature": False})
        atomic_write(self.appdata, {"button_bindings": {}})
        self.profile = self.root / "profile.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_export_diff_dry_run_apply(self):
        self.assertEqual(profiles_main(["export", "--game-dir", str(self.game_dir),
                                       "--global-file", str(self.appdata),
                                       "--profile", str(self.profile)]), 0)
        data = json.loads(self.profile.read_text())
        self.assertEqual(data["game_settings"]["game_id"], "ez2dj_7th")
        atomic_write(self.game, {"game_id": "ez2dj_7th", "feature": True})
        self.assertEqual(len(differences({"a": 1}, {"a": 2})), 1)
        args = ["apply", "--game-dir", str(self.game_dir),
                "--global-file", str(self.appdata), "--profile", str(self.profile)]
        self.assertEqual(profiles_main(args), 0)
        self.assertTrue(json.loads(self.game.read_text())["feature"])
        self.assertEqual(profiles_main(args + ["--apply"]), 0)
        self.assertFalse(json.loads(self.game.read_text())["feature"])
        self.assertTrue(Path(str(self.game) + ".bak").exists())

    def test_refuses_profile_overwrite(self):
        args = ["export", "--game-dir", str(self.game_dir),
                "--global-file", str(self.appdata), "--profile", str(self.profile)]
        self.assertEqual(profiles_main(args), 0)
        self.assertEqual(profiles_main(args), 1)


if __name__ == "__main__":
    unittest.main()
