#!/usr/bin/env python3
"""Refresh the embedded `compiler/own/cap.ax` section of the hand-written selfhost bundles (T157).

Usage: python tests/selfhost/cap/refresh_cap_bundles.py [--check]

`tests/selfhost/cap/qa_own_cap.ax` and `tests/selfhost/own/qa_own_init.ax` (T082c/T082d) have no
generator: each embeds `compiler/own/cap.ax` between the marker line `// --- compiler/own/cap.ax ---`
and the next `// --- ` marker, with its `module` / `use` lines and the `@intrinsic` declarations
that the bundle declares once elsewhere removed, followed by one blank line. This script rewrites
that section from the current file (ADR-0034 section 2: bundles that embed a changed port module are
regenerated with the change). It is idempotent; `--check` only reports stale bundles (exit 1).
Run it after any change to `compiler/own/cap.ax`.
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
SOURCE = "compiler/own/cap.ax"
MARKER = "// --- compiler/own/cap.ax ---\n"
BUNDLES = [
    "tests/selfhost/cap/qa_own_cap.ax",
    "tests/selfhost/own/qa_own_init.ax",
]
DROPPED_PREFIXES = (
    "module ",
    "use ",
    "@intrinsic fn size_of<",
    "@intrinsic fn align_of<",
    "@intrinsic unsafe fn ptr_copy_nonoverlapping<",
)


def embedded_text():
    with open(os.path.join(ROOT, SOURCE), "r", encoding="utf-8", newline="") as f:
        lines = f.read().splitlines(keepends=True)
    kept = [ln for ln in lines if not ln.startswith(DROPPED_PREFIXES)]
    text = "".join(kept)
    if not text.endswith("\n"):
        text += "\n"
    return text + "\n"


def refresh(path, body, check):
    full = os.path.join(ROOT, path)
    with open(full, "r", encoding="utf-8", newline="") as f:
        text = f.read()
    start = text.find(MARKER)
    if start < 0:
        raise SystemExit("%s: marker %r not found" % (path, MARKER.strip()))
    begin = start + len(MARKER)
    end = text.find("\n// --- ", begin)
    if end < 0:
        raise SystemExit("%s: no section marker after the cap.ax section" % path)
    end += 1
    new_text = text[:begin] + body + text[end:]
    if new_text == text:
        return False
    if not check:
        with open(full, "w", encoding="utf-8", newline="") as f:
            f.write(new_text)
    return True


def main():
    check = "--check" in sys.argv[1:]
    body = embedded_text()
    stale = [p for p in BUNDLES if refresh(p, body, check)]
    for p in stale:
        print(("stale: " if check else "refreshed: ") + p)
    if not stale:
        print("up to date")
    return 1 if (check and stale) else 0


if __name__ == "__main__":
    sys.exit(main())
