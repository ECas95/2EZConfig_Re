"""Synthetic tests for offline PE compatibility diagnostics (no real game files)."""
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compatibility_doctor import inspect_pe, diagnose_installation, main


def synthetic_pe(path, *, machine=0x14C, dll=False, optional_magic=0x10B):
    """Create a tiny structurally valid PE identity fixture with NO executable code."""
    data = bytearray(64 + 24 + 96)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 64)
    data[64:68] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", data, 68, machine, 1, 0, 0, 0,
                     96, 0x2000 if dll else 0x0002)
    struct.pack_into("<H", data, 88, optional_magic)
    struct.pack_into("<HH", data, 88 + 40, 5, 1)
    struct.pack_into("<H", data, 88 + 68, 2)
    path.write_bytes(data)


class PEDoctorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        synthetic_pe(self.root / "EZ2AC.exe")
        synthetic_pe(self.root / "2EZ.dll", dll=True)
        synthetic_pe(self.root / "2EZConfig.exe")
        (self.root / "game-settings.json").write_text(json.dumps({
            "game_id": "ez2ac_fn_ex", "exe_name": "EZ2AC.exe",
            "force_60hz": True, "hypersonik": True
        }))

    def tearDown(self):
        self.tmp.cleanup()

    def test_readonly_pe_and_settings_diagnostics(self):
        report = diagnose_installation(self.root)
        self.assertEqual(report["error_count"], 0)
        self.assertEqual(report["game_pe"]["machine"], "x86")
        self.assertEqual(report["injected_dll_pe"]["machine"], "x86")
        self.assertEqual(report["game_pe"]["minimum_header_os_version"], "5.1")
        self.assertTrue(report["read_only"])
        self.assertFalse(report["gameplay_verified"])
        codes = {issue["code"] for issue in report["issues"]}
        self.assertIn("legacy_refresh_override", codes)
        self.assertIn("wasapi_backend_selected", codes)
        self.assertNotIn(str(self.root), json.dumps(report))
        self.assertEqual(main(["--game-dir", str(self.root), "--json"]), 0)

    def test_reject_missing_or_wrong_architecture(self):
        synthetic_pe(self.root / "EZ2AC.exe", machine=0x8664, optional_magic=0x20B)
        report = diagnose_installation(self.root)
        self.assertGreater(report["error_count"], 0)
        self.assertIn("game_not_win32", {x["code"] for x in report["issues"]})
        self.assertIn("architecture_mismatch", {x["code"] for x in report["issues"]})
        (self.root / "2EZ.dll").unlink()
        report = diagnose_installation(self.root)
        self.assertIn("injected_dll_missing", {x["code"] for x in report["issues"]})

    def test_refuse_unknown_binary_and_traversal(self):
        (self.root / "EZ2AC.exe").write_text("not actually a PE")
        with self.assertRaisesRegex(ValueError, "Missing DOS"):
            inspect_pe(self.root / "EZ2AC.exe")
        report = diagnose_installation(self.root)
        self.assertIn("game_pe_invalid", {x["code"] for x in report["issues"]})
        with self.assertRaisesRegex(ValueError, "simple filename"):
            diagnose_installation(self.root, "../outside.exe")

    def test_invalid_settings_does_not_overwrite(self):
        settings = self.root / "game-settings.json"
        settings.write_text("{ not json")
        old = settings.read_bytes()
        report = diagnose_installation(self.root)
        self.assertIn("settings_not_available", {x["code"] for x in report["issues"]})
        self.assertEqual(settings.read_bytes(), old)

    def test_protect_optional_header_bounds(self):
        path = self.root / "small.exe"
        path.write_bytes(b"MZ" + bytes(100))
        with self.assertRaises(ValueError):
            inspect_pe(path)


if __name__ == "__main__":
    unittest.main()
