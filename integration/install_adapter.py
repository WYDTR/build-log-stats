"""Install an opt-in validator in an existing E11-E12 integration checkout."""
import argparse
import hashlib
import json
from pathlib import Path

OLD = "            verdict=validate(target,patchfile,out/'validation')"
NEW = """            profile = request.get('validation_profile')
            if profile == 'build-log-stats-v1':
                from build_log_stats_adapter import validate_build_log_stats
                verdict = validate_build_log_stats(target, patchfile, out/'validation')
            elif profile is None:
                verdict=validate(target,patchfile,out/'validation')
            else:
                raise Failure('INVALID_REQUEST', 'Unknown validation_profile')"""


def install(lab_root):
    lab_root = Path(lab_root).resolve()
    target = lab_root / "labs/e11e12/pipeline.py"
    module_source = Path(__file__).resolve().with_name("build_log_stats_adapter.py")
    if not (lab_root / "run_e11e12.py").is_file() or not target.is_file():
        raise ValueError("Pass the A-buildchecker directory containing run_e11e12.py")
    before = target.read_bytes()
    text = before.decode("utf-8")
    if NEW in text:
        updated = text
    elif text.count(OLD) == 1:
        updated = text.replace(OLD, NEW, 1)
    else:
        raise ValueError("Unknown pipeline layout; no files were changed")
    compile(updated, str(target), "exec")
    module = module_source.read_bytes()
    compile(module, str(module_source), "exec")
    contract = module_source.with_name("INTERFACE.md").read_bytes()
    contract_target = lab_root / "docs/e11e12-build-log-stats-contract.md"
    if contract_target.exists() and contract_target.read_bytes() != contract:
        raise ValueError("Existing profile contract differs; preserve and review it before updating")
    backup_dir = lab_root / "work/adapter-install"
    backup_dir.mkdir(parents=True, exist_ok=True)
    before_hash = hashlib.sha256(before).hexdigest()
    backup = backup_dir / f"pipeline.before.{before_hash}.py"
    if not backup.exists():
        backup.write_bytes(before)
    (target.parent / "build_log_stats_adapter.py").write_bytes(module)
    after = updated.encode("utf-8")
    if after != before:
        target.write_bytes(after)
    contract_target.parent.mkdir(parents=True, exist_ok=True)
    contract_target.write_bytes(contract)
    receipt = {
        "profile": "build-log-stats-v1", "backup": str(backup),
        "pipeline_before_sha256": before_hash,
        "pipeline_after_sha256": hashlib.sha256(after).hexdigest(),
        "adapter_sha256": hashlib.sha256(module).hexdigest(),
    }
    (backup_dir / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lab_root", type=Path)
    arguments = parser.parse_args()
    print(json.dumps(install(arguments.lab_root), indent=2))
    print("ADAPTER_INSTALL_PASS")
