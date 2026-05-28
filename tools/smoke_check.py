"""Small repository sanity check.

This script is intentionally simple: it compiles all Python files and checks
whether the main third-party dependencies are importable in the current Python
environment.
"""
from __future__ import annotations

import compileall
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ["customtkinter", "sqlalchemy", "openpyxl", "reportlab"]


def main() -> int:
    print("Project Tracker Desktop smoke check")
    print(f"Root: {ROOT}")
    print("\n[1/2] Compiling Python files...")
    ok = compileall.compile_dir(ROOT, quiet=1)
    if not ok:
        print("Compilation failed.")
        return 1
    print("Compilation OK.")

    print("\n[2/2] Checking dependencies...")
    missing = []
    for name in REQUIRED:
        found = importlib.util.find_spec(name) is not None
        print(f"- {name}: {'OK' if found else 'MISSING'}")
        if not found:
            missing.append(name)

    if missing:
        print("\nMissing dependencies. Run: pip install -r requirements.txt")
        return 2

    print("\nSmoke check OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
