"""Remove only this project's four known build outputs."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
for name in ("app", "app.exe", "main.o", "helper.o"):
    output = root / name
    if output.resolve().parent != root:
        raise SystemExit(f"Refusing output outside the project: {name}")
    output.unlink(missing_ok=True)
