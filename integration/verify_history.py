"""Rebuild recorded commits and replay the actual missing-dependency repair."""
import argparse
import difflib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from build_log_stats_adapter import executable, make_command, validate_build_log_stats

ROOT = Path(__file__).resolve().parents[1]


def verify(output):
    output = Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("Choose a fresh history output directory")
    output.mkdir(parents=True, exist_ok=True)
    metadata = json.loads((ROOT / "integration/commits.json").read_text(encoding="utf-8"))
    summary = {"schema_version": "build-log-stats-history-1", "versions": {}}
    make = make_command()

    def run(name, command, cwd, expected=0):
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                                errors="replace", timeout=120)
        (output / (name + ".log")).write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode != expected:
            raise ValueError(f"{name}: exit {result.returncode}; see its log")
        return result.stdout + result.stderr

    with tempfile.TemporaryDirectory(prefix="build-log-history-") as directory:
        temporary_root = Path(directory).resolve()
        if temporary_root.parent != Path(tempfile.gettempdir()).resolve():
            raise ValueError("Unexpected temporary directory")
        projects = {}
        for label in ("base", "target", "fixed"):
            project = temporary_root / label
            sha = metadata[label + "_commit"]
            run(label + "-clone", ["git", "clone", "--no-hardlinks", "--no-checkout",
                                   str(ROOT), str(project)], ROOT)
            run(label + "-checkout", ["git", "checkout", "--detach", sha], project)
            run(label + "-build", [make, "clean", "app"], project)
            tests = run(label + "-tests", [sys.executable, "-m", "unittest", "discover",
                                           "-s", "tests", "-p", "test_cli.py", "-v"], project)
            dependency_exit = 1 if label == "target" else 0
            dependencies = json.loads(run(label + "-dependencies",
                [sys.executable, "scripts/check_dependencies.py", "--json"], project, dependency_exit))
            stats = json.loads(run(label + "-output", [str(executable(project)), "--json",
                                                       "tests/fixtures/compiler.log"], project))
            expected_findings = [{"type": "MISSING", "target": "helper.o", "dependency": "rules.h"}] if label == "target" else []
            if dependencies["findings"] != expected_findings:
                raise ValueError(f"Unexpected {label} dependency findings")
            expected_stats = {"lines": 9, "warnings": 1, "errors": 2} if label == "base" else {
                "lines": 9, "warnings": 2, "errors": 2, "notes": 2}
            if stats != expected_stats:
                raise ValueError(f"Unexpected {label} output")
            summary["versions"][label] = {
                "commit": sha, "findings": dependencies["findings"], "output": stats,
                "functional_tests": int(re.search(r"Ran (\d+) tests?", tests)[1]),
            }
            projects[label] = project

        target = projects["target"]
        broken = (target / "Makefile").read_text(encoding="utf-8")
        repaired = broken.replace("helper.o: helper.c helper.h\n",
                                  "helper.o: helper.c helper.h rules.h\n", 1)
        if repaired == broken:
            raise ValueError("Expected the controlled target dependency omission")
        patchfile = output / "candidate.patch"
        patchfile.write_text("".join(difflib.unified_diff(
            broken.splitlines(True), repaired.splitlines(True),
            fromfile="a/Makefile", tofile="b/Makefile")), encoding="utf-8")
        verdict = validate_build_log_stats(target, patchfile, output / "validation")
        if not verdict["accepted"]:
            raise ValueError(f"Historical repair rejected: {verdict}")
        summary["repair"] = verdict
        summary["passed"] = True
        (output / "result.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "work/history-01")
    arguments = parser.parse_args()
    print(json.dumps(verify(arguments.out), indent=2))
    print("HISTORY_REPAIR_PASS")
