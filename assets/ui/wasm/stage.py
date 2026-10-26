#!/usr/bin/env python3
"""Stage browser sources without C++ bridge sources or generated output."""

from pathlib import Path
import shutil
import sys

source = Path("assets/ui")
destination = Path(sys.argv[1])
destination.mkdir(parents=True, exist_ok=True)
for entry in source.iterdir():
    if entry.name in {"wasm", "renders"} or entry.suffix == ".md":
        continue
    target = destination / entry.name
    if entry.is_dir():
        shutil.copytree(entry, target, dirs_exist_ok=True)
    else:
        shutil.copy2(entry, target)
