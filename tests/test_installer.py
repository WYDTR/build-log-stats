from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "integration"))
from install_adapter import install, NEW

STUB = """def execute(request, target, patchfile, out):
    try:
        if True:
            verdict=validate(target,patchfile,out/'validation')
    except ValueError:
        raise
    return verdict
"""


class AdapterInstallerTests(unittest.TestCase):
    def fixture(self, directory, source=STUB):
        root = Path(directory)
        self.assertEqual(root.resolve().parent, Path(tempfile.gettempdir()).resolve())
        (root / "run_e11e12.py").write_text("# host entry\n", encoding="utf-8")
        pipeline = root / "labs/e11e12/pipeline.py"
        pipeline.parent.mkdir(parents=True)
        pipeline.write_text(source, encoding="utf-8")
        return root, pipeline

    def test_install_is_idempotent_and_keeps_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            root, target = self.fixture(directory)
            first = install(root)
            installed = target.read_bytes()
            second = install(root)
            self.assertEqual(target.read_bytes(), installed)
            self.assertEqual(first["pipeline_after_sha256"], second["pipeline_after_sha256"])
            self.assertEqual(Path(first["backup"]).read_text(encoding="utf-8"), STUB)
            self.assertIn(NEW, installed.decode())
            self.assertIn("build-log-stats-v1", (root / "docs/e11e12-build-log-stats-contract.md").read_text(encoding="utf-8"))

    def test_unknown_layout_is_not_modified(self):
        with tempfile.TemporaryDirectory() as directory:
            root, target = self.fixture(directory, "# different implementation\n")
            before = target.read_bytes()
            with self.assertRaisesRegex(ValueError, "Unknown pipeline layout"):
                install(root)
            self.assertEqual(target.read_bytes(), before)
            self.assertFalse((target.parent / "build_log_stats_adapter.py").exists())

    def test_default_profile_still_uses_existing_validator(self):
        with tempfile.TemporaryDirectory() as directory:
            root, target = self.fixture(directory)
            install(root)
            expected = {"accepted": True, "original_validator": True}
            namespace = {"validate": lambda *args: expected, "Failure": ValueError}
            exec(compile(target.read_text(encoding="utf-8"), str(target), "exec"), namespace)
            self.assertIs(namespace["execute"]({}, None, None, root), expected)
            with self.assertRaisesRegex(ValueError, "Unknown validation_profile"):
                namespace["execute"]({"validation_profile": "unknown"}, None, None, root)


if __name__ == "__main__":
    unittest.main()
