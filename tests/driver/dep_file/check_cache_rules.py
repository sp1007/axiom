#!/usr/bin/env python3
"""Runner-side rules fed by `--dep-file` (T437b): G2 and the dependency-file vocabulary of tools/axtest_cache.py.

Usage (from the repository root):
    python tests/driver/dep_file/check_cache_rules.py <tmp dir> <case> <compiler>

Cases:
    g2      ADR-0042 §5 G2 (T437a-qa): a synthetic prelude function that calls the nondeterministic leaf binding
            `monotonic_ns`, used by a program with no `std.` text, makes the program uncacheable
              * in superset mode: `StdIndex.nondet_reason` over the program text (the implicitly loaded std
                files seed the traversal), and
              * in exact mode: `exact_deps_nondet` over the list the real compiler writes with `--dep-file`
                (the prelude is in that list);
            on an unmodified scratch copy of std both say "cacheable" (control). The std copy lives in <tmp>.
    vocab   `parse_dep_file` maps `<path> -` and `<dir>/ dir` to the runner's `file` digests (`absent`, the
            listing sentinel); `dep_matches_change` (`--affected` rule 1) matches a file created inside a listed
            directory and at an absent path; malformed lines are rejected.
"""

import os
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import axtest_cache  # noqa: E402

FAILURES = []

PROGRAM = "fn main() -> i32 {\n    let t = qa_now();\n    if t == 0u64 {\n        return 1;\n    }\n    0\n}\n"
PRELUDE_ADDITION = "\n// T437b G2 probe (scratch copy only)\npub fn qa_now() -> u64 {\n    monotonic_ns()\n}\n"


def fail(msg):
    FAILURES.append(msg)
    print("FAIL: " + msg)


def make_std(dst, poisoned):
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(os.path.join(ROOT, "std"), dst,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if poisoned:
        with open(os.path.join(dst, "core", "prelude.ax"), "ab") as f:
            f.write(PRELUDE_ADDITION.encode("utf-8"))


def exact_reason(compiler, std_dir, src, dep):
    if os.path.exists(dep):
        os.remove(dep)
    subprocess.run(compiler + ["check", "--dep-file=" + dep, "--std-root", std_dir, src], cwd=ROOT,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, timeout=600)
    lst = axtest_cache.parse_dep_file(dep)
    if lst is None:
        fail("g2: the compiler wrote no (valid) dependency file for %s" % src)
        return None, []
    rels = [axtest_cache.posix_rel(os.path.join(ROOT, p), ROOT) for p, d in lst if d != "absent"]
    std_rel = axtest_cache.posix_rel(std_dir, ROOT)
    idx = axtest_cache.StdIndex(std_dir)
    return axtest_cache.exact_deps_nondet(rels, std_rel, idx, ROOT), rels


def case_g2(compiler, tmp):
    src = os.path.join(tmp, "g2_program.ax")
    with open(src, "wb") as f:
        f.write(PROGRAM.encode("utf-8"))
    if "std." in PROGRAM or "host" in PROGRAM:
        fail("g2: the probe program must not mention std")
    for poisoned in (False, True):
        label = "poisoned" if poisoned else "control"
        std_dir = os.path.join(tmp, "std_" + label)
        make_std(std_dir, poisoned)
        sup = axtest_cache.StdIndex(std_dir).nondet_reason([PROGRAM])
        ex, rels = exact_reason(compiler, std_dir, src, os.path.join(tmp, "deps_%s.txt" % label))
        prelude_listed = any(r.endswith("core/prelude.ax") for r in rels)
        if not prelude_listed:
            fail("g2/%s: the prelude is not in the compiler's dependency list %s" % (label, rels))
        if poisoned:
            if not sup or "prelude" not in sup:
                fail("g2/poisoned: superset mode did not flag the prelude (%r)" % sup)
            if not ex or "prelude" not in ex:
                fail("g2/poisoned: exact mode did not flag the prelude (%r)" % ex)
        else:
            if sup is not None:
                fail("g2/control: superset mode flags an unmodified std (%r)" % sup)
            if ex is not None:
                fail("g2/control: exact mode flags an unmodified std (%r)" % ex)
        print("g2/%s: superset=%r exact=%r" % (label, sup, ex))
        shutil.rmtree(std_dir, ignore_errors=True)


def case_vocab(_compiler, tmp):
    dep = os.path.join(tmp, "vocab.txt")
    good = ("a/b c/x.ax " + "0" * 64 + "\n" + "a/pkg/src/ dir\n" + "a/pkg/axiom.toml -\n").encode("utf-8")
    with open(dep, "wb") as f:
        f.write(good)
    lst = axtest_cache.parse_dep_file(dep)
    want = [("a/b c/x.ax", "0" * 64),
            ("a/pkg/src/" + axtest_cache.DIRLIST_SENTINEL, "absent"),
            ("a/pkg/axiom.toml", "absent")]
    if lst != want:
        fail("vocab: parse_dep_file -> %r, expected %r" % (lst, want))
    for bad in ("x.ax 123\n", "dir-without-slash dir\n", "file-with-slash/ " + "0" * 64 + "\n", "x.ax\n"):
        with open(dep, "wb") as f:
            f.write(bad.encode("utf-8"))
        if axtest_cache.parse_dep_file(dep) is not None:
            fail("vocab: malformed line accepted: %r" % bad)
    sentinel = "a/pkg/src/" + axtest_cache.DIRLIST_SENTINEL
    checks = [
        (sentinel, "a/pkg/src/new.ax", True),
        (sentinel, "a/pkg/src/sub/new.ax", True),
        (sentinel, "a/pkg/other.ax", False),
        ("a/pkg/axiom.toml", "a/pkg/axiom.toml", True),
        ("a/pkg/axiom.toml", "a/pkg/axiom.toml.bak", False),
    ]
    for d, ch, exp in checks:
        if axtest_cache.dep_matches_change(d, ch) != exp:
            fail("vocab: dep_matches_change(%r, %r) != %r" % (d, ch, exp))


CASES = {"g2": case_g2, "vocab": case_vocab}


def main(argv):
    if len(argv) < 4 or argv[2] not in CASES:
        print("usage: check_cache_rules.py <tmp> <%s> <compiler...>" % "|".join(sorted(CASES)))
        return 2
    tmp = os.path.abspath(argv[1])
    os.makedirs(tmp, exist_ok=True)
    compiler = argv[3:]
    if not os.path.isabs(compiler[0]):
        compiler[0] = os.path.join(ROOT, compiler[0])
    CASES[argv[2]](compiler, tmp)
    if FAILURES:
        print("cache-rules %s: %d failure(s)" % (argv[2], len(FAILURES)))
        return 1
    print("cache-rules %s: OK" % argv[2])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
