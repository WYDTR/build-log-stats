import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / ("app.exe" if os.name == "nt" else "app")


class CommandLineTests(unittest.TestCase):
    def run_app(self, *args, data=b""):
        return subprocess.run([str(APP), *args], cwd=ROOT, input=data,
                              capture_output=True, timeout=10)

    def stats(self, data):
        result = self.run_app("--json", data=data)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_fixture_file(self):
        result = self.run_app("--json", "tests/fixtures/compiler.log")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"lines": 9, "warnings": 1, "errors": 2})

    def test_empty_input(self):
        self.assertEqual(self.stats(b""), {"lines": 0, "warnings": 0, "errors": 0})

    def test_final_line_without_newline(self):
        self.assertEqual(self.stats(b"warning: last line")["warnings"], 1)
        self.assertEqual(self.stats(b"plain line")["lines"], 1)

    def test_crlf_and_blank_lines(self):
        result = self.stats(b"warning: first\r\n\r\nerror: third\r\n")
        self.assertEqual(result, {"lines": 3, "warnings": 1, "errors": 1})

    def test_ansi_colour_sequences(self):
        self.assertEqual(self.stats(b"file: \x1b[31merror:\x1b[0m bad\n")["errors"], 1)

    def test_incomplete_escape_is_safe(self):
        self.assertEqual(self.stats(b"\x1b[")["lines"], 1)

    def test_long_lines(self):
        result = self.stats(b"x" * 20000 + b" warning: long line\n")
        self.assertEqual(result["warnings"], 1)

    def test_one_severity_per_line(self):
        result = self.stats(b"warning: followed by error: bad\n")
        self.assertEqual((result["warnings"], result["errors"]), (0, 1))

    def test_token_boundary(self):
        result = self.stats(b"myerror: no\nwarning_count: no\n")
        self.assertEqual((result["warnings"], result["errors"]), (0, 0))

    def test_utf8_context(self):
        self.assertEqual(self.stats("编译器: warning: 提示\n".encode())["warnings"], 1)

    def test_fail_on_error(self):
        result = self.run_app("--fail-on-error", data=b"error: bad\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"errors=1", result.stdout)
        self.assertEqual(self.run_app("--fail-on-error", data=b"warning: fine\n").returncode, 0)

    def test_unknown_option(self):
        self.assertEqual(self.run_app("--unknown").returncode, 2)

    def test_multiple_files(self):
        self.assertEqual(self.run_app("a.log", "b.log").returncode, 2)

    def test_missing_file(self):
        self.assertEqual(self.run_app("does-not-exist.log").returncode, 3)

    def test_binary_input_is_rejected(self):
        self.assertEqual(self.run_app(data=b"warning: bad\x00tail").returncode, 3)

    def test_explicit_stdin(self):
        result = self.run_app("--json", "-", data=b"error: stdin\n")
        self.assertEqual(json.loads(result.stdout)["errors"], 1)

    def test_filename_after_double_dash(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(Path(directory).resolve().parent,
                             Path(tempfile.gettempdir()).resolve())
            path = Path(directory) / "input.log"
            path.write_text("warning: file\n", encoding="utf-8")
            result = self.run_app("--json", "--", str(path))
            self.assertEqual(json.loads(result.stdout)["warnings"], 1)

    def test_help_and_version(self):
        self.assertIn(b"Usage:", self.run_app("--help").stdout)
        self.assertEqual(self.run_app("--version").stdout.strip(), b"build-log-stats 0.1.0")


if __name__ == "__main__":
    unittest.main()
