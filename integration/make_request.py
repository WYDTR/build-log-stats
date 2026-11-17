"""Prepare E12 request, candidate and provenance from the uploaded project history."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit, urlunsplit

PROJECT = Path(__file__).resolve().parents[1]


def git(*arguments):
    return subprocess.check_output(["git", *arguments], cwd=PROJECT, text=True).strip()


def source_url():
    value = git("remote", "get-url", "origin")
    if value.startswith(("https://", "http://")):
        parsed = urlsplit(value)
        value = urlunsplit((parsed.scheme, parsed.netloc.rsplit("@", 1)[-1],
                            parsed.path, "", ""))
    return value


def prepare(lab_root):
    lab_root = Path(lab_root).resolve()
    data_root = (lab_root / "data").resolve()
    if not (lab_root / "run_e11e12.py").is_file() or not PROJECT.is_relative_to(data_root):
        raise ValueError("Clone this project below the lab's data/ and pass the A-buildchecker root")
    adapter = lab_root / "labs/e11e12/build_log_stats_adapter.py"
    pipeline = lab_root / "labs/e11e12/pipeline.py"
    if not adapter.is_file() or "build-log-stats-v1" not in pipeline.read_text(encoding="utf-8"):
        raise ValueError("Install the build-log-stats adapter before preparing its request")
    metadata = json.loads((PROJECT / "integration/commits.json").read_text(encoding="utf-8"))
    for field in ("base_commit", "target_commit", "fixed_commit"):
        sha = metadata[field]
        if len(sha) != 40 or git("rev-parse", "--verify", sha + "^{commit}") != sha:
            raise ValueError(f"Missing complete commit: {field}")
    subprocess.run(["git", "merge-base", "--is-ancestor", metadata["base_commit"],
                    metadata["target_commit"]], cwd=PROJECT, check=True)
    candidate = (PROJECT / "integration/candidate.Dockerfile").read_bytes()
    broken = git("show", metadata["target_commit"] + ":Dockerfile.broken")
    sys.path.insert(0, str(lab_root / "labs/e11e12/vendor"))
    from draft.autobuild import prepare_candidate
    prepare_candidate(broken, candidate.decode("utf-8"))

    request = {
        "mode": "e12",
        "repo": "/course/" + PROJECT.relative_to(lab_root).as_posix(),
        "base": metadata["base_commit"], "target": metadata["target_commit"],
        "candidate": "/course/data/real-candidate.Dockerfile",
        "expected_output": metadata["expected_output"],
        "build_timeout": 1800, "validation_profile": "build-log-stats-v1",
    }
    dataset = dict(metadata, source_repository=source_url(),
                   candidate_source="Project-owned dependency-install candidate; mirror configuration follows the course environment",
                   candidate_sha256=hashlib.sha256(candidate).hexdigest(),
                   request_sha256=hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest())
    outputs = {
        data_root / "real-request.json": (json.dumps(request, indent=2) + "\n").encode(),
        data_root / "real-dataset.json": (json.dumps(dataset, indent=2) + "\n").encode(),
        data_root / "real-candidate.Dockerfile": candidate,
    }
    for path, content in outputs.items():
        if path.resolve().parent != data_root:
            raise ValueError(f"Output must stay inside the lab data directory: {path}")
        if path.exists() and path.read_bytes() != content:
            raise ValueError(f"Preserve existing evidence before changing this dataset: {path}")
    for path, content in outputs.items():
        path.write_bytes(content)
    return request


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lab_root", type=Path)
    arguments = parser.parse_args()
    print(json.dumps(prepare(arguments.lab_root), indent=2))
    print("REAL_REQUEST_READY")
