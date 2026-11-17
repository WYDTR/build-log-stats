import difflib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "integration"))
from build_log_stats_adapter import make_command, validate_build_log_stats


class RepairTests(unittest.TestCase):
    def fixture(self, directory):
        destination = Path(directory) / "project"
        shutil.copytree(ROOT, destination, ignore=shutil.ignore_patterns(
            ".git", "app", "app.exe", "*.o", "work", "__pycache__"))
        makefile = destination / "Makefile"
        healthy = makefile.read_text(encoding="utf-8")
        self.assertIn("helper.o: helper.c helper.h rules.h", healthy)
        broken = healthy.replace("helper.o: helper.c helper.h rules.h",
                                 "helper.o: helper.c helper.h", 1)
        makefile.write_text(broken, encoding="utf-8", newline="\n")
        return destination, broken, healthy

    def patchfile(self, directory, before, after):
        path = Path(directory) / "candidate.patch"
        path.write_text("".join(difflib.unified_diff(
            before.splitlines(True), after.splitlines(True),
            fromfile="a/Makefile", tofile="b/Makefile")), encoding="utf-8", newline="\n")
        return path

    def test_real_dependency_repair_and_header_rebuild(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(Path(directory).resolve().parent,
                             Path(tempfile.gettempdir()).resolve())
            project, broken, healthy = self.fixture(directory)
            original_header = (project / "rules.h").read_bytes()
            patch = self.patchfile(directory, broken, healthy)
            result = validate_build_log_stats(project, patch, Path(directory) / "validation")
            self.assertTrue(result["accepted"], result)
            self.assertTrue(all(result["checks"].values()), result)
            self.assertEqual((project / "Makefile").read_text(encoding="utf-8"), healthy)
            self.assertEqual((project / "rules.h").read_bytes(), original_header)

    def test_clean_build_only_patch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(Path(directory).resolve().parent,
                             Path(tempfile.gettempdir()).resolve())
            project, broken, _ = self.fixture(directory)
            patch = self.patchfile(directory, broken, broken + "\n# unrelated edit\n")
            result = validate_build_log_stats(project, patch, Path(directory) / "validation")
            self.assertFalse(result["accepted"])
            self.assertFalse(result["checks"]["header_change"])
            self.assertTrue(result["rollback"])
            self.assertEqual((project / "Makefile").read_text(encoding="utf-8"), broken)

    def test_malformed_patch_preserves_source(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(Path(directory).resolve().parent,
                             Path(tempfile.gettempdir()).resolve())
            project, broken, _ = self.fixture(directory)
            patch = Path(directory) / "bad.patch"
            patch.write_text("not a patch\n", encoding="utf-8")
            result = validate_build_log_stats(project, patch, Path(directory) / "validation")
            self.assertFalse(result["accepted"])
            self.assertTrue(result["rollback"])
            self.assertEqual((project / "Makefile").read_text(encoding="utf-8"), broken)

    def test_main_declares_all_local_dependencies(self):
        result = subprocess.run([sys.executable, "scripts/check_dependencies.py", "--json"],
                                cwd=ROOT, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["findings"], [])


if __name__ == "__main__":
    unittest.main()
