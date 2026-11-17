"""Cross-check this project's explicit object dependencies with GCC -MM."""
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def check():
    text = (ROOT / "Makefile").read_text(encoding="utf-8")
    actual, declared, findings = {}, {}, []
    compiler = shlex.split(os.environ.get("CC", "gcc"))
    for target, source in (("main.o", "main.c"), ("helper.o", "helper.c")):
        match = re.search(r"^" + re.escape(target) + r":\s*([^\n]*)$", text, re.M)
        if match is None or "$" in match[1]:
            raise ValueError(f"Expected an explicit dependency rule for {target}")
        declared[target] = sorted(set(match[1].split()))
        process = subprocess.run(
            [*compiler, "-O0", "-MM", "-MT", target, source], cwd=ROOT,
            capture_output=True, text=True, check=True, timeout=30,
        )
        dependencies = process.stdout.replace("\\\n", " ").partition(":")[2].split()
        actual[target] = sorted(set(dependencies))
        for kind, dependencies in (
            ("MISSING", set(actual[target]) - set(declared[target])),
            ("REDUNDANT", set(declared[target]) - set(actual[target])),
        ):
            findings.extend({"type": kind, "target": target, "dependency": name}
                            for name in sorted(dependencies))
    return {"actual": actual, "declared": declared, "findings": findings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = check()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for finding in report["findings"]:
            print(f"{finding['type']} {finding['target']} -> {finding['dependency']}")
        if not report["findings"]:
            print("DEPENDENCIES_PASS")
    return int(any(item["type"] == "MISSING" for item in report["findings"]))


if __name__ == "__main__":
    raise SystemExit(main())
