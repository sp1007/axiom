#!/usr/bin/env python3
"""QA (T449a): structural check of the generated std/async bundles.

For every bundle under tests/std/async/{executor,structured,waker,waker_qa}: each `module std.*` section
appears exactly once and every std module a section imports (longest dotted prefix naming a std module,
std.core.* excluded) appears EARLIER in the bundle. Also runs bundle_closure.bundle_sources twice for a seed
and demands identical output without duplicates (determinism), and that an unknown seed is rejected.
Prints "OK bundle structure <n>" or one line per violation and exits non-zero on any.
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)
import bundle_closure  # noqa: E402

MODULE_RE = re.compile(r"^module\s+([A-Za-z0-9_.]+)", re.MULTILINE)
USE_RE = re.compile(r"^use\s+([A-Za-z0-9_.]+)", re.MULTILINE)


def main():
    index = bundle_closure.module_index(ROOT)
    problems = []
    checked = 0
    for d in ("executor", "structured", "waker", "waker_qa"):
        for path in sorted(glob.glob(os.path.join(ROOT, "tests", "std", "async", d, "*.ax"))):
            with open(path, encoding="utf-8", newline="") as f:
                text = f.read().replace("\r\n", "\n")
            mods = [(m.group(1), m.start()) for m in MODULE_RE.finditer(text)]
            if not any(n.startswith("std.") for n, _ in mods):
                continue  # not a bundle
            checked += 1
            rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
            seen = {}
            for name, pos in mods:
                if name in seen:
                    problems.append("%s: module %s bundled twice" % (rel, name))
                seen[name] = pos
            bounds = [pos for _, pos in mods] + [len(text)]
            for i, (name, pos) in enumerate(mods):
                section = text[pos:bounds[i + 1]]
                for u in USE_RE.finditer(section):
                    parts = u.group(1).split(".")
                    for cut in range(len(parts), 1, -1):
                        dep = ".".join(parts[:cut])
                        if dep in index:
                            if not dep.startswith("std.core.") and dep != name:
                                if dep not in seen or seen[dep] >= pos:
                                    problems.append("%s: %s imports %s which is not bundled before it" % (rel, name, dep))
                            break
    seed = ["std/async/executor.ax", "std/async/waker.ax"]
    prog = "use std.asyn.group.TaskGroup\n"
    a = bundle_closure.bundle_sources(ROOT, seed, prog)
    b = bundle_closure.bundle_sources(ROOT, seed, prog)
    if a != b or len(set(a)) != len(a):
        problems.append("bundle_sources not deterministic / has duplicates: %r vs %r" % (a, b))
    try:
        bundle_closure.bundle_sources(ROOT, ["std/async/does_not_exist.ax"], "")
        problems.append("bundle_sources accepted an unknown seed file")
    except FileNotFoundError:
        pass
    if checked < 20:
        problems.append("only %d bundles inspected (expected >= 20)" % checked)
    for p in problems:
        print(p)
    if problems:
        return 1
    print("OK bundle structure %d" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
