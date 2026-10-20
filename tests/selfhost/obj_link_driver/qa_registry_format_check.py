#!/usr/bin/env python3
"""QA (T085 gate): static well-formedness of known_divergent.txt.

The e2e oracle compares the registry with the live behaviour; this check guards the file itself so that a
hand edit cannot hide a problem: every row is `path<TAB>stage<TAB>behaviour`, the stage and behaviour come from
the closed vocabularies, paths are unique, sorted, exist in the repository and belong to the oracle's corpus
patterns. The row count is printed (not pinned): the e2e oracle enforces the live count.
"""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STAGES = {"tokens", "ast", "resolved", "hir", "thir", "mir", "lir", "mi", "mc", "obj", "backend-build"}
BEHAVIOURS = {"same-behaviour", "different-behaviour", "no-image"}
PATTERNS = [
    "tests/run/**/*.ax", "tests/programs/*.ax", "tests/mc/**/*.ax",
    "tests/modules/*/src/main.ax", "tests/opt/*.ax", "tests/driver/*.ax",
]


def main():
    root = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    corpus = set()
    for pat in PATTERNS:
        for p in glob.glob(os.path.join(root, pat), recursive=True):
            corpus.add(os.path.relpath(p, root).replace("\\", "/"))
    rows = []
    problems = []
    with open(os.path.join(HERE, "known_divergent.txt"), "rb") as f:
        raw = f.read()
    if b"\r" in raw:
        problems.append("CR byte in known_divergent.txt (must be LF)")
    for n, line in enumerate(raw.decode("utf-8").split("\n"), 1):
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            problems.append("line %d: expected 3 tab-separated fields, got %d" % (n, len(parts)))
            continue
        path, stage, beh = parts
        if stage not in STAGES:
            problems.append("line %d: unknown stage %r" % (n, stage))
        if beh not in BEHAVIOURS:
            problems.append("line %d: unknown behaviour %r" % (n, beh))
        if path not in corpus:
            problems.append("line %d: %s is not a corpus program" % (n, path))
        rows.append(path)
    if len(set(rows)) != len(rows):
        problems.append("duplicate paths")
    if rows != sorted(rows):
        problems.append("rows not sorted")
    if not rows:
        problems.append("empty registry")
    for p in problems:
        print("PROBLEM", p)
    if problems:
        return 1
    print("REGISTRY-FORMAT ok rows=%d" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
