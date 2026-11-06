"""Synthetic-only tests for FNEX CustomMod integration helpers.

No game binaries, songs, decoded assets or private mod source are used.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fnex_custommod_preflight import inspect_installation
from fnex_bms_library_check import inspect_bms_library, declared_asset_found


def codes(report):
    return [item["code"] for item in report["checks"]]


class CustomModInstallationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for name in ("2EZ.dll", "2EZConfig.exe", "EZ2B.exe",
                     "EZ2CustomMod.dll", "ffmpeg.exe", "pthreadGC2.dll",
                     "wqy-microhei.ttc"):
            (self.root / name).write_bytes(b"synthetic fixture")
        (self.root / "BMSData").mkdir()
        (self.root / "BMSMod.ini").write_text(
            "[Core]\nEnable=1\n[CustomSongs]\nRoot=BMSData\nCacheRoot=CustomCache\n")
        self.write_settings()

    def tearDown(self):
        self.tmp.cleanup()

    def write_settings(self, **extra):
        opts = {"game_id": "ez2ac_fn_ex", "exe_name": "EZ2B.exe",
                "extra_dlls": "EZ2CustomMod.dll"}
        opts.update(extra)
        (self.root / "game-settings.json").write_text(json.dumps(opts), encoding="utf-8")

    def test_ready_fixture_has_no_blockers(self):
        result = inspect_installation(self.root)
        self.assertTrue(result["read_only"])
        self.assertFalse(result["runtime_verified"])
        self.assertEqual(result["errors"], 0)
        self.assertEqual(result["warnings"], 0)
        self.assertTrue(result["custommod_enabled"])

    def test_default_fnex_exe_mismatch_detected(self):
        self.write_settings(exe_name="EZ2AC.exe")
        result = inspect_installation(self.root)
        self.assertIn("game_executable_missing", codes(result))
        self.assertIn("fnex_executable_variant", codes(result))
        self.assertEqual(result["configured_exe"], "EZ2AC.exe")

    def test_absent_extra_dll_and_dependency_warnings(self):
        self.write_settings(extra_dlls="some_other.dll")
        (self.root / "EZ2CustomMod.dll").unlink()
        (self.root / "ffmpeg.exe").unlink()
        result = inspect_installation(self.root)
        self.assertIn("custommod_not_enabled", codes(result))
        self.assertIn("custommod_dll_missing", codes(result))
        self.assertIn("optional_dependency_missing", codes(result))

    def test_no_settings_and_idmap_protection(self):
        (self.root / "game-settings.json").unlink()
        cache = self.root / "CustomCache"
        cache.mkdir()
        (cache / "idmap.txt").write_text("1|synthetic/song\n")
        result = inspect_installation(self.root, target_os="xp")
        self.assertIn("game_settings_missing", codes(result))
        self.assertIn("persistent_idmap", codes(result))
        self.assertIn("xp_gdiplus_missing", codes(result))

    def test_rejects_nonlocal_executable(self):
        self.write_settings(exe_name="../outside.exe")
        result = inspect_installation(self.root)
        self.assertIn("exe_name_invalid", codes(result))
        self.assertEqual(result["configured_exe"], "")


class CustomModLibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        song = self.root / "5KeyMix" / "My Pack" / "Demo Track"
        song.mkdir(parents=True)
        self.song = song
        (song / "sound").mkdir()
        (song / "sound" / "snare.wav").write_bytes(b"fixture")
        (song / "jacket.png").write_bytes(b"fixture")
        (song / "normal.bms").write_text(
            "#TITLE Original Test\n#WAV01 snare.wav\n#BMPAA jacket.png\n"
            "#00111:0101\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_valid_library_and_sound_subfolder(self):
        result = inspect_bms_library(self.root, check_assets=True)
        self.assertEqual(result["counts"]["modes"], 1)
        self.assertEqual(result["counts"]["songs"], 1)
        self.assertEqual(result["counts"]["charts"], 1)
        self.assertEqual(result["counts"]["declared_assets"], 2)
        self.assertEqual(result["counts"]["missing_assets"], 0)
        self.assertEqual(result["warning_count"], 0)

    def test_unsafe_and_missing_asset_paths(self):
        (self.song / "normal.bms").write_text(
            "#WAV01 ../escape.wav\n#WAV02 nonexistent.ogg\n")
        result = inspect_bms_library(self.root, check_assets=True)
        self.assertIn("unsafe_asset_path", [x["code"] for x in result["issues"]])
        self.assertIn("missing_asset", [x["code"] for x in result["issues"]])
        self.assertEqual(result["counts"]["missing_assets"], 1)

    def test_extra_depth_does_not_count_nested_charts(self):
        (self.song / "normal.bms").unlink()
        nested = self.song / "Extra"
        nested.mkdir()
        (nested / "normal.bme").write_text("#TITLE Deep")
        result = inspect_bms_library(self.root)
        self.assertIn("no_charts", [x["code"] for x in result["issues"]])

    def test_unknown_modes_and_symlink_guard(self):
        (self.root / "UnknownMode").mkdir()
        result = inspect_bms_library(self.root)
        self.assertIn("unknown_mode", [x["code"] for x in result["issues"]])
        self.assertIsNone(declared_asset_found(self.song, "../../escape.wav"))

    def test_asset_check_optional(self):
        (self.song / "normal.bms").write_text("#WAV01 missing.wav\n")
        result = inspect_bms_library(self.root)
        self.assertEqual(result["counts"]["declared_assets"], 0)
        self.assertEqual(result["counts"]["missing_assets"], 0)


if __name__ == "__main__":
    unittest.main()
