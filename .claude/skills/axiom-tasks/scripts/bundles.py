#!/usr/bin/env python3
"""bundles — regenerate the committed selfhost bundles of a tree (harness, owner decision 2026-11-17).

The generators `tests/selfhost/**/gen_*.py` concatenate `compiler/` (and some `std/`) modules into
committed `.ax` bundles. Tasks never write or commit those files by hand: `taskctl.py snapshot`
regenerates them inside the task snapshot (so the gate tests exactly what will be committed) and
`taskctl.py accept` regenerates them again on the current HEAD + the task's change set and stages
them in the task's single commit. This module is that one regeneration routine.

Every generator resolves ROOT from its own file location, so running `<tree>/tests/selfhost/x/gen.py`
regenerates the bundles of <tree> from <tree>'s sources only. Plain write mode never runs a compiler
(axiom0-captured goldens are extracted from the bundle already on disk; only `--refresh-goldens` /
`--axiom0` re-capture them), so a regeneration is a pure function of the tree.

Generators of one directory run one after another (some import a sibling and write the same files);
directories run in parallel (-j). The set of generated files is the "wrote <path>" output of a write
run; it is kept in the committed manifest MANIFEST (itself a generated file).

Usage (from anywhere):
    python bundles.py regen [--root DIR] [-j N]   write every bundle of DIR (default: repo root)
    python bundles.py check [--root DIR] [-j N]   every generator in --check mode
    python bundles.py list  [--root DIR]          the generated-file set the harness uses
Exit 0 ok, 1 a generator failed / a bundle differs.
"""
import concurrent.futures as _cf
import glob
import os
import re
import subprocess
import sys
import time

MANIFEST = "tests/selfhost/generated-files.txt"
GEN_GLOB = ("tests", "selfhost", "**", "gen_*.py")
TEMPLATE_ROOT = "tests/selfhost"
DEFAULT_JOBS = 3
GEN_TIMEOUT_S = 1800
_FAIL_RX = re.compile(r"\b(DIFFERS|MISSING)\b")


def _rel(tree, p):
    p = p.strip().strip('"').strip("'")
    if os.path.isabs(p):
        p = os.path.relpath(p, tree)
    return p.replace("\\", "/")


def generators(tree):
    """Relative paths of every generator of the tree, sorted."""
    out = glob.glob(os.path.join(tree, *GEN_GLOB), recursive=True)
    return sorted(_rel(tree, g) for g in out if "__pycache__" not in g)


def _groups(gens):
    by_dir = {}
    for g in gens:
        by_dir.setdefault(os.path.dirname(g), []).append(g)
    return [by_dir[k] for k in sorted(by_dir)]


def _run_group(tree, group, check):
    """Run one directory's generators in order. Returns (outputs, failures, seconds)."""
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    outputs, failures, t0 = [], [], time.time()
    for g in group:
        args = [sys.executable, os.path.join(tree, g)] + (["--check"] if check else [])
        try:
            r = subprocess.run(args, cwd=tree, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", env=env, timeout=GEN_TIMEOUT_S)
            text, rc = (r.stdout or "") + (r.stderr or ""), r.returncode
        except subprocess.TimeoutExpired:
            text, rc = f"timeout after {GEN_TIMEOUT_S}s", 124
        bad = [ln for ln in text.splitlines() if _FAIL_RX.search(ln)]
        if rc != 0 or (check and bad):
            tail = "\n".join((bad or text.strip().splitlines())[-12:])
            failures.append((g, rc, tail))
        if not check:
            for ln in text.splitlines():
                if ln.startswith("wrote "):
                    outputs.append(_rel(tree, ln[len("wrote "):]))
    return outputs, failures, time.time() - t0


class Result:
    def __init__(self, ok, outputs, failures, seconds, ngen):
        self.ok, self.outputs, self.failures, self.seconds, self.ngen = ok, outputs, failures, seconds, ngen

    def summary(self, what):
        s = f"bundles {what}: {self.ngen} generator(s), {len(self.outputs)} file(s), {self.seconds:.0f}s"
        return s + ("" if self.ok else f", {len(self.failures)} FAILED")

    def failure_text(self):
        return "\n".join(f"  {g} (exit {rc}):\n    " + tail.replace("\n", "\n    ")
                         for g, rc, tail in self.failures)


def run(tree, check=False, jobs=DEFAULT_JOBS):
    tree = os.path.abspath(tree)
    gens = generators(tree)
    t0 = time.time()
    outputs, failures = set(), []
    with _cf.ThreadPoolExecutor(max_workers=max(1, int(jobs))) as ex:
        for o, f, _s in ex.map(lambda grp: _run_group(tree, grp, check), _groups(gens)):
            outputs.update(o)
            failures += f
    escaped = sorted(o for o in outputs if o.startswith("../") or o == "..")
    for o in escaped:
        failures.append(("(manifest)", 1, f"a generator wrote outside the tree: {o}"))
        outputs.discard(o)
    return Result(not failures, sorted(outputs), failures, time.time() - t0, len(gens))


def write_manifest(tree, outputs):
    lines = ["# Files written by tests/selfhost/**/gen_*.py (harness: .claude/skills/axiom-tasks/scripts/bundles.py).",
             "# Generated: tasks never edit, list or commit these by hand; `taskctl snapshot` and `taskctl accept`",
             "# regenerate them. This manifest is regenerated with them."]
    data = "\n".join(lines + sorted(set(outputs) - {MANIFEST})) + "\n"
    path = os.path.join(tree, MANIFEST)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(data)


def regen(tree, jobs=DEFAULT_JOBS):
    """Write every bundle of `tree` and its manifest. Result.outputs includes the manifest."""
    r = run(tree, check=False, jobs=jobs)
    if r.ok and r.ngen:
        write_manifest(tree, r.outputs)
        r.outputs = sorted(set(r.outputs) | {MANIFEST})
    return r


def _manifest_entries(text):
    return {ln.strip() for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")}


def known_generated(root, head_text=None):
    """The generated-file set of a tree, cheap (no generator runs): the manifest of the working copy
    and of HEAD (`head_text`), every `X` with an `X.in` template under tests/selfhost, the manifest."""
    out = {MANIFEST}
    try:
        with open(os.path.join(root, MANIFEST), encoding="utf-8") as fh:
            out |= _manifest_entries(fh.read())
    except OSError:
        pass
    if head_text:
        out |= _manifest_entries(head_text)
    for tpl in glob.glob(os.path.join(root, *TEMPLATE_ROOT.split("/"), "**", "*.in"), recursive=True):
        out.add(_rel(root, tpl[:-3]))
    return out


def main(argv):
    if not argv or argv[0] not in ("regen", "check", "list"):
        print(__doc__)
        return 2
    root = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "..", ".."))
    jobs = DEFAULT_JOBS
    i = 1
    while i < len(argv):
        if argv[i] == "--root" and i + 1 < len(argv):
            root, i = os.path.abspath(argv[i + 1]), i + 2
        elif argv[i] in ("-j", "--jobs") and i + 1 < len(argv):
            jobs, i = int(argv[i + 1]), i + 2
        else:
            print(f"unknown argument {argv[i]}")
            return 2
    if argv[0] == "list":
        for p in sorted(known_generated(root)):
            print(p)
        return 0
    r = regen(root, jobs) if argv[0] == "regen" else run(root, check=True, jobs=jobs)
    print(r.summary(argv[0]))
    if not r.ok:
        print(r.failure_text())
    return 0 if r.ok else 1


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    sys.exit(main(sys.argv[1:]))
