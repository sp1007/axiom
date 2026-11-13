#!/usr/bin/env python3
"""Checks `axiomc <cmd> --dep-file=<path>` (T437b, ADR-0041 §4 S2) on the fixtures of this directory.

Usage (from the repository root, as the `cmd:` manifests of this directory do):
    python tests/driver/dep_file/check_dep_file.py <tmp dir> <case> <compiler>

The expected lists are computed independently here: the sha256 of every file is taken with hashlib from the
bytes on disk. The format checked is the one documented in compiler/driver/opts.ax section 10:
    `<path> <sha256>` (loaded file), `<path> -` (probed, absent), `<dir>/ dir` (listing used);
one per line, LF only, sorted by the path bytes, unique paths, paths as the compiler opened them (relative to
the working directory, `/` separators).

Cases:
    prelude      a file with no `std.` text: the implicitly loaded std files (core option/result/prelude and the
                 `future` lang-item modules) are listed with their hashes, and they are exactly
                 tools/axtest_cache.py IMPLICIT_STD_FILES minus `core/host.ax` (G2: one list, checked here)
    std_import   `use std.core.host...`: `std/core/host.ax` is listed too
    package      a multi-file package (directory input): every module file, `axiom.toml`, the listed directories
    src_file     the package's `src/main.ax` as input: the `axiom.toml` probe finds the package
    absent       a file under `src/` without `axiom.toml`: the absence fact `<dir>/axiom.toml -`
    fail         a failing compile still writes the list; a missing input writes `<input> -`
    commands     `run`, `build`, `inspect` and the separate-argument form `--dep-file <path>` write the same list
                 as `check`; an object input of `build` is listed
    format       an unknown flag value form and the line format rules on a package list
"""

import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
FIX = "tests/driver/dep_file/fixtures"
STD = "std"
LINE_RE = re.compile(r"^(.*\S) ([0-9a-f]{64}|-|dir)$")

sys.path.insert(0, os.path.join(ROOT, "tools"))
import axtest_cache  # noqa: E402

FAILURES = []


def fail(msg):
    FAILURES.append(msg)
    print("FAIL: " + msg)


def sha(rel):
    with open(os.path.join(ROOT, rel), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def implicit_std(with_host):
    out = {}
    for rel in axtest_cache.IMPLICIT_STD_FILES:
        if rel == "core/host.ax" and not with_host:
            continue
        p = STD + "/" + rel
        out[p] = sha(p)
    return out


def run(compiler, args, dep):
    if os.path.exists(dep):
        os.remove(dep)
    r = subprocess.run(compiler + args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       stdin=subprocess.DEVNULL, timeout=600)
    return r.returncode, r.stdout, r.stderr


def read_dep(dep, label):
    """{path: tag} after checking the format rules; None when missing/malformed (a failure is recorded)."""
    if not os.path.isfile(dep):
        fail("%s: no dependency file written" % label)
        return None
    data = open(dep, "rb").read()
    if b"\r" in data:
        fail("%s: CR byte in the dependency file" % label)
    if data and not data.endswith(b"\n"):
        fail("%s: last line not terminated by LF" % label)
    text = data.decode("utf-8")
    paths = []
    out = {}
    for line in text.split("\n")[:-1] if text else []:
        m = LINE_RE.match(line)
        if not m:
            fail("%s: malformed line %r" % (label, line))
            return None
        p, tag = m.group(1), m.group(2)
        if "\\" in p:
            fail("%s: backslash in path %r" % (label, p))
        if (tag == "dir") != p.endswith("/"):
            fail("%s: directory marker mismatch in %r" % (label, line))
        paths.append(p)
        out[p] = tag
    if paths != sorted(paths, key=lambda s: s.encode("utf-8")):
        fail("%s: lines not sorted by path bytes" % label)
    if len(set(paths)) != len(paths):
        fail("%s: duplicate paths" % label)
    # the runner's parser accepts it
    if axtest_cache.parse_dep_file(dep) is None:
        fail("%s: tools/axtest_cache.py parse_dep_file rejects the file" % label)
    return out


def expect_eq(label, got, want):
    if got is None:
        return
    if got != want:
        missing = sorted(set(want) - set(got))
        extra = sorted(set(got) - set(want))
        wrong = sorted(k for k in set(got) & set(want) if got[k] != want[k])
        fail("%s: dependency list differs; missing %s; extra %s; wrong tag %s"
             % (label, missing, extra, ["%s got %s want %s" % (k, got[k], want[k]) for k in wrong]))


def case_prelude(compiler, tmp):
    dep = os.path.join(tmp, "prelude.txt")
    src = FIX + "/plain.ax"
    rc, _o, e = run(compiler, ["check", "--dep-file=" + dep, "--std-root", STD, src], dep)
    if rc != 0:
        fail("prelude: check exit %d: %r" % (rc, e[:300]))
    got = read_dep(dep, "prelude")
    want = {src: sha(src)}
    want.update(implicit_std(False))
    expect_eq("prelude", got, want)
    if got is not None:
        std_listed = {p[len(STD) + 1:] for p in got if p.startswith(STD + "/")}
        implicit = set(axtest_cache.IMPLICIT_STD_FILES) - {"core/host.ax"}
        if std_listed != implicit:
            fail("prelude: implicitly loaded std files %s != IMPLICIT_STD_FILES %s"
                 % (sorted(std_listed), sorted(implicit)))
        if "std/core/prelude.ax" not in got:
            fail("prelude: std/core/prelude.ax not listed")


def case_std_import(compiler, tmp):
    dep = os.path.join(tmp, "std_import.txt")
    src = FIX + "/uses_std.ax"
    rc, _o, e = run(compiler, ["check", "--dep-file=" + dep, "--std-root", STD, src], dep)
    if rc != 0:
        fail("std_import: check exit %d: %r" % (rc, e[:300]))
    want = {src: sha(src)}
    want.update(implicit_std(True))
    expect_eq("std_import", read_dep(dep, "std_import"), want)


def package_want():
    pkg = FIX + "/pkg"
    want = {
        pkg + "/axiom.toml": sha(pkg + "/axiom.toml"),
        pkg + "/src/main.ax": sha(pkg + "/src/main.ax"),
        pkg + "/src/util/calc.ax": sha(pkg + "/src/util/calc.ax"),
        pkg + "/src/util/text.ax": sha(pkg + "/src/util/text.ax"),
        pkg + "/": "dir",
        pkg + "/src/": "dir",
        pkg + "/src/util/": "dir",
    }
    want.update(implicit_std(False))
    return want


def case_package(compiler, tmp):
    dep = os.path.join(tmp, "package.txt")
    rc, _o, e = run(compiler, ["check", "--dep-file=" + dep, "--std-root", STD, FIX + "/pkg"], dep)
    if rc != 0:
        fail("package: check exit %d: %r" % (rc, e[:300]))
    expect_eq("package", read_dep(dep, "package"), package_want())


def case_src_file(compiler, tmp):
    dep = os.path.join(tmp, "src_file.txt")
    rc, _o, e = run(compiler, ["check", "--dep-file=" + dep, "--std-root", STD, FIX + "/pkg/src/main.ax"], dep)
    if rc != 0:
        fail("src_file: check exit %d: %r" % (rc, e[:300]))
    expect_eq("src_file", read_dep(dep, "src_file"), package_want())


def case_absent(compiler, tmp):
    dep = os.path.join(tmp, "absent.txt")
    src = FIX + "/nopkg/src/main.ax"
    rc, _o, e = run(compiler, ["check", "--dep-file=" + dep, "--std-root", STD, src], dep)
    if rc != 0:
        fail("absent: check exit %d: %r" % (rc, e[:300]))
    want = {src: sha(src), FIX + "/nopkg/axiom.toml": "-"}
    want.update(implicit_std(False))
    expect_eq("absent", read_dep(dep, "absent"), want)


def case_fail(compiler, tmp):
    dep = os.path.join(tmp, "fail.txt")
    src = FIX + "/bad.ax"
    rc, _o, _e = run(compiler, ["check", "--dep-file=" + dep, "--std-root", STD, src], dep)
    if rc == 0:
        fail("fail: check of %s succeeded" % src)
    want = {src: sha(src)}
    want.update(implicit_std(False))
    expect_eq("fail", read_dep(dep, "fail"), want)

    dep2 = os.path.join(tmp, "missing.txt")
    src2 = FIX + "/missing_input.ax"
    rc, _o, _e = run(compiler, ["check", "--dep-file=" + dep2, "--std-root", STD, src2], dep2)
    if rc == 0:
        fail("fail: check of a missing input succeeded")
    expect_eq("fail/missing", read_dep(dep2, "fail/missing"), {src2: "-"})


def case_commands(compiler, tmp):
    src = FIX + "/plain.ax"
    want = {src: sha(src)}
    want.update(implicit_std(False))
    dep = os.path.join(tmp, "run.txt")
    rc, _o, e = run(compiler, ["run", "--dep-file=" + dep, "--std-root", STD, src], dep)
    if rc != 0:
        fail("commands/run: exit %d: %r" % (rc, e[:300]))
    expect_eq("commands/run", read_dep(dep, "commands/run"), want)

    dep = os.path.join(tmp, "inspect.txt")
    rc, _o, e = run(compiler, ["inspect", "--dep-file=" + dep, "--emit=tokens", "--std-root", STD, src], dep)
    if rc != 0:
        fail("commands/inspect: exit %d: %r" % (rc, e[:300]))
    expect_eq("commands/inspect", read_dep(dep, "commands/inspect"), want)

    dep = os.path.join(tmp, "build.txt")
    exe = os.path.join(tmp, "plain.exe")
    rc, _o, e = run(compiler, ["build", "--dep-file", dep, "--std-root", STD, "-o", exe, src], dep)
    if rc != 0:
        fail("commands/build: exit %d: %r" % (rc, e[:300]))
    expect_eq("commands/build", read_dep(dep, "commands/build"), want)

    # an object input of `build` is an input too (listed with its hash)
    obj = os.path.join(tmp, "plain.obj")
    rc, _o, e = run(compiler, ["build", "--kind=obj", "--std-root", STD, "-o", obj, src], os.path.join(tmp, "x"))
    if rc == 0 and os.path.isfile(obj):
        obj_rel = os.path.relpath(obj, ROOT).replace("\\", "/") if os.path.splitdrive(obj)[0].lower() == \
            os.path.splitdrive(ROOT)[0].lower() else obj
        dep = os.path.join(tmp, "build_obj.txt")
        exe2 = os.path.join(tmp, "plain2.exe")
        rc, _o, e = run(compiler, ["build", "--dep-file=" + dep, "--std-root", STD, "-o", exe2, src, obj_rel], dep)
        got = read_dep(dep, "commands/build_obj")
        if got is not None:
            hit = [p for p in got if p.endswith("plain.obj")]
            with open(obj, "rb") as f:
                obj_sha = hashlib.sha256(f.read()).hexdigest()
            if not hit or got[hit[0]] != obj_sha:
                fail("commands/build_obj: object input not listed with its hash: %s" % sorted(got))
    else:
        fail("commands: building the object input failed (exit %d): %r" % (rc, e[:300]))


def case_format(compiler, tmp):
    # `--dep-file` without a value is a usage error (exit 2) and writes nothing
    rc, _o, _e = run(compiler, ["check", "--std-root", STD, FIX + "/plain.ax", "--dep-file"],
                     os.path.join(tmp, "none"))
    if rc != 2:
        fail("format: `--dep-file` without a value: exit %d, expected 2" % rc)
    # without the flag nothing is written next to the input
    before = set(os.listdir(os.path.join(ROOT, FIX)))
    rc, _o, _e = run(compiler, ["check", "--std-root", STD, FIX + "/plain.ax"], os.path.join(tmp, "none"))
    if rc != 0 or set(os.listdir(os.path.join(ROOT, FIX))) != before:
        fail("format: a plain check changed the fixture directory or failed (exit %d)" % rc)


CASES = {
    "prelude": case_prelude,
    "std_import": case_std_import,
    "package": case_package,
    "src_file": case_src_file,
    "absent": case_absent,
    "fail": case_fail,
    "commands": case_commands,
    "format": case_format,
}


def main(argv):
    if len(argv) < 4 or argv[2] not in CASES:
        print("usage: check_dep_file.py <tmp> <%s> <compiler...>" % "|".join(sorted(CASES)))
        return 2
    tmp = os.path.abspath(argv[1])
    os.makedirs(tmp, exist_ok=True)
    compiler = argv[3:]
    if not os.path.isabs(compiler[0]):
        compiler[0] = os.path.join(ROOT, compiler[0])
    CASES[argv[2]](compiler, tmp)
    if FAILURES:
        print("dep-file %s: %d failure(s)" % (argv[2], len(FAILURES)))
        return 1
    print("dep-file %s: OK" % argv[2])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
