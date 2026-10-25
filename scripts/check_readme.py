#!/usr/bin/env python3
"""Lightweight README sanity checks; intentionally does not make network requests."""
from pathlib import Path
import re
import sys

path = Path("README.md")
if not path.exists():
    sys.exit("README.md is missing")
text = path.read_text(encoding="utf-8")
required = [
    "<!-- PROJECTS:START -->", "<!-- PROJECTS:END -->",
    "<!-- ACTIVITY:START -->", "<!-- ACTIVITY:END -->",
    "https://kaustavworks.tech",
]
missing = [item for item in required if item not in text]
if missing:
    sys.exit("README check failed; missing: " + ", ".join(missing))
for section in ("PROJECTS", "ACTIVITY"):
    if text.count(f"<!-- {section}:START -->") != 1 or text.count(f"<!-- {section}:END -->") != 1:
        sys.exit(f"README check failed: {section} markers must each appear exactly once")
if not re.search(r"^#\s+.+", text, re.MULTILINE):
    sys.exit("README check failed: missing top-level heading")
print("README structure checks passed.")
