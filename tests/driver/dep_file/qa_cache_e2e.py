#!/usr/bin/env python3
"""QA T437b (adversarial): end-to-end cache soundness of `tools/axtest.py` fed by the real `--dep-file`.

Usage (from the repository root):
    python tests/driver/dep_file/qa_cache_e2e.py <tmp dir> <case> <compiler...>

Every case builds a private repository root in <tmp> (a copy of std/core, optionally std/future, and one
`modes: interp` run test under tests/qa/), then drives the real runner (`tools/axtest.py --root <tmp root>`) with a
private `--cache-dir`: run 1 must store, run 2 must be a hit (the cache is live), then one input of the test is
changed and run 3 must execute the test again (no `HITS 1`) with the expected verdict.

Cases:
    rtread   the program reads `data.txt` of its own test directory at RUN time (deterministic host file
             bindings, cacheable). ADR-0041 S4 addendum: only reads outside the test's own directory need
             `cache-inputs:`/`nocache:`. Changing data.txt must make run 3 FAIL (stdout differs), never a
             cached PASS; `--affected tests/qa/rt/data.txt` must select the test.
    stdedit  a comment appended to the implicitly loaded std/core/prelude.ax: run 3 must re-run (PASS, not HITS).
    newstd   the std copy has no std/future; creating std/future/{mod,block_on}.ax (absence facts in the
             dependency list) must make run 3 re-run (no HITS).
  Round 1 (re-gate after the F1 fix):
    rtsub    as rtread, the data file in a SUBdirectory of the test directory (tests/qa/rt/in/deep.txt);
             `--affected` must select the test or at least report the file UNMATCHED.
    rtdecl   as rtread, the data file OUTSIDE the test directory (data/in.txt) declared by `cache-inputs:`;
             `--affected data/in.txt` must select the test.
    rtcreate the program reads data/later.txt, declared by `cache-inputs:` and ABSENT on runs 1-2 (expected
             `exit: 3`); creating it must make run 3 re-run and FAIL (exit 0).
    stdunused editing a std file the compiler did NOT load (std/core/cmp.ax) must stay a HIT on run 3 (the gain of
             the exact mode over the superset mode).
"""

import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
FAILURES = []


def fail(msg):
    FAILURES.append(msg)
    print("FAIL: " + msg)


def ascii_bytes(s):
    return ", ".join("%du8" % b for b in s.encode("ascii"))


def rt_program(rel_path, header="// stdout: data-v1\\n\n"):
    n = len(rel_path)
    return """// test: run
""" + header + """// modes: interp
use std.core.host.open
use std.core.host.read
use std.core.host.write
use std.core.host.close
use std.core.host.stdio

@intrinsic pub unsafe fn address_of<T>(val: T) -> *const T { 0 as *const T }
@intrinsic pub unsafe fn address_of_mut<T>(val: T) -> *mut T { 0 as *mut T }

const DATA_PATH: [%d]u8 = [%s];

fn main() -> i32 {
    let h = unsafe { open(address_of(DATA_PATH[0]), %d, 0u32) };
    if h < 0i64 {
        return 3;
    }
    let mut buf: [64]u8 = [0u8; 64];
    let n = unsafe { read(h, address_of_mut(buf[0]), 64) };
    let _ = close(h);
    if n <= 0i64 {
        return 4;
    }
    let _ = unsafe { write(stdio(1u32), address_of(buf[0]), n as usize) };
    0
}
""" % (n, ascii_bytes(rel_path), n)


HELLO = """// test: run
// stdout: ok\\n
// modes: interp
use std.core.host.write
use std.core.host.stdio

@intrinsic pub unsafe fn address_of<T>(val: T) -> *const T { 0 as *const T }

const MSG: [3]u8 = [111u8, 107u8, 10u8];

fn main() -> i32 {
    let _ = unsafe { write(stdio(1u32), address_of(MSG[0]), 3) };
    0
}
"""


def make_root(tmp, with_future):
    r = os.path.join(tmp, "root")
    if os.path.isdir(r):
        shutil.rmtree(r)
    shutil.copytree(os.path.join(ROOT, "std", "core"), os.path.join(r, "std", "core"))
    if with_future:
        shutil.copytree(os.path.join(ROOT, "std", "future"), os.path.join(r, "std", "future"))
    os.makedirs(os.path.join(r, "tests", "qa", "rt"))
    return r


def write(path, text):
    with open(path, "wb") as f:
        f.write(text.encode("utf-8"))


def axtest(compiler, root, tmp, extra):
    cmd = [sys.executable, os.path.join(ROOT, "tools", "axtest.py"), "--root", root, "--compiler", compiler[0],
           "--build-dir", os.path.join(tmp, "build"), "--cache-dir", os.path.join(tmp, "cache"), "-j", "1"] + extra
    r = subprocess.run(cmd, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                       timeout=1200)
    return r.stdout.decode("utf-8", "replace")


def summary(out):
    tot = re.search(r"^TOTAL (\d+) PASS (\d+) FAIL (\d+)", out, re.M)
    cache = re.search(r"^CACHED (\d+) HITS (\d+) MISS (\d+) UNCACHEABLE (\d+) STORED (\d+)", out, re.M)
    if not tot or not cache:
        return None
    return {"total": int(tot.group(1)), "pass": int(tot.group(2)), "fail": int(tot.group(3)),
            "hits": int(cache.group(2)), "stored": int(cache.group(5))}


def three_runs(compiler, root, tmp, change, want_fail, label, want_hit=False):
    sel = ["qa/rt/"]
    s1 = summary(axtest(compiler, root, tmp, sel))
    s2 = summary(axtest(compiler, root, tmp, sel))
    if s1 is None or s2 is None:
        fail("%s: runner output without TOTAL/CACHED lines" % label)
        return
    print("%s: run1 %s" % (label, s1))
    print("%s: run2 %s" % (label, s2))
    if s1["pass"] != 1 or s1["stored"] != 1:
        fail("%s: run 1 did not pass and store: %s" % (label, s1))
        return
    if s2["hits"] != 1:
        fail("%s: run 2 is not a cache hit (cache not live): %s" % (label, s2))
        return
    change()
    s3 = summary(axtest(compiler, root, tmp, sel))
    print("%s: run3 after the change %s" % (label, s3))
    if s3 is None:
        fail("%s: run 3 output without TOTAL/CACHED lines" % label)
        return
    if want_hit:
        if s3["hits"] != 1 or s3["pass"] != 1:
            fail("%s: run 3 should stay a cache hit (unrelated input changed): %s" % (label, s3))
        return
    if s3["hits"] != 0:
        fail("%s: run 3 answered from the cache after an input changed (false hit): %s" % (label, s3))
    if want_fail and s3["fail"] != 1:
        fail("%s: run 3 should FAIL (stdout differs) but reported %s" % (label, s3))
    if not want_fail and s3["pass"] != 1:
        fail("%s: run 3 should PASS on a fresh run but reported %s" % (label, s3))


def case_rtread(compiler, tmp):
    root = make_root(tmp, True)
    rel = "tests/qa/rt/data.txt"
    write(os.path.join(root, "tests", "qa", "rt", "rt_read.ax"), rt_program(rel))
    write(os.path.join(root, rel), "data-v1\n")
    three_runs(compiler, root, tmp, lambda: write(os.path.join(root, rel), "data-v2\n"), True, "rtread")
    out = axtest(compiler, root, tmp, ["--affected", rel, "--list"])
    if "qa/rt/rt_read.ax" not in out:
        fail("rtread: --affected %s does not select qa/rt/rt_read.ax:\n%s" % (rel, out.strip()))


def case_stdedit(compiler, tmp):
    root = make_root(tmp, True)
    write(os.path.join(root, "tests", "qa", "rt", "hello.ax"), HELLO)
    prelude = os.path.join(root, "std", "core", "prelude.ax")

    def change():
        with open(prelude, "ab") as f:
            f.write(b"\n// qa_cache_e2e stdedit\n")
    three_runs(compiler, root, tmp, change, False, "stdedit")


def case_newstd(compiler, tmp):
    root = make_root(tmp, False)
    write(os.path.join(root, "tests", "qa", "rt", "hello.ax"), HELLO)

    def change():
        shutil.copytree(os.path.join(ROOT, "std", "future"), os.path.join(root, "std", "future"))
    three_runs(compiler, root, tmp, change, False, "newstd")


def affected_selects(compiler, root, tmp, rel, tid, label):
    out = axtest(compiler, root, tmp, ["--affected", rel, "--list"])
    if tid not in out:
        fail("%s: --affected %s does not select %s:\n%s" % (label, rel, tid, out.strip()))


def case_rtsub(compiler, tmp):
    root = make_root(tmp, True)
    rel = "tests/qa/rt/in/deep.txt"
    os.makedirs(os.path.join(root, "tests", "qa", "rt", "in"))
    write(os.path.join(root, "tests", "qa", "rt", "rt_read.ax"), rt_program(rel))
    write(os.path.join(root, rel), "data-v1\n")
    three_runs(compiler, root, tmp, lambda: write(os.path.join(root, rel), "data-v2\n"), True, "rtsub")
    # --affected: rule 2a maps a file to the tests of ITS OWN directory only (T437a design, unchanged by T437b),
    # so a file in a subdirectory without tests is not selected; it must then at least be reported UNMATCHED
    # (visible to the gate), never silently dropped. Follow-up filed in the T437b round-1 QA file.
    out = axtest(compiler, root, tmp, ["--affected", rel, "--list"])
    if "qa/rt/rt_read.ax" not in out and not re.search(r"^UNMATCHED .*" + re.escape(rel), out, re.M):
        fail("rtsub: --affected %s neither selects the test nor reports UNMATCHED:\n%s" % (rel, out.strip()))


def case_rtdecl(compiler, tmp):
    root = make_root(tmp, True)
    rel = "data/in.txt"
    os.makedirs(os.path.join(root, "data"))
    write(os.path.join(root, "tests", "qa", "rt", "rt_read.ax"),
          rt_program(rel, "// stdout: data-v1\\n\n// cache-inputs: data/in.txt\n"))
    write(os.path.join(root, rel), "data-v1\n")
    three_runs(compiler, root, tmp, lambda: write(os.path.join(root, rel), "data-v2\n"), True, "rtdecl")
    affected_selects(compiler, root, tmp, rel, "qa/rt/rt_read.ax", "rtdecl")


def case_rtcreate(compiler, tmp):
    root = make_root(tmp, True)
    rel = "data/later.txt"
    os.makedirs(os.path.join(root, "data"))
    write(os.path.join(root, "tests", "qa", "rt", "rt_read.ax"),
          rt_program(rel, "// exit: 3\n// cache-inputs: data/later.txt\n"))
    three_runs(compiler, root, tmp, lambda: write(os.path.join(root, rel), "data-v2\n"), True, "rtcreate")
    affected_selects(compiler, root, tmp, rel, "qa/rt/rt_read.ax", "rtcreate")


def case_stdunused(compiler, tmp):
    root = make_root(tmp, True)
    write(os.path.join(root, "tests", "qa", "rt", "hello.ax"), HELLO)
    cmp_ax = os.path.join(root, "std", "core", "cmp.ax")

    def change():
        with open(cmp_ax, "ab") as f:
            f.write(b"\n// qa_cache_e2e stdunused\n")
    three_runs(compiler, root, tmp, change, False, "stdunused", want_hit=True)


CASES = {"rtread": case_rtread, "stdedit": case_stdedit, "newstd": case_newstd, "rtsub": case_rtsub,
         "rtdecl": case_rtdecl, "rtcreate": case_rtcreate, "stdunused": case_stdunused}


def main(argv):
    if len(argv) < 4 or argv[2] not in CASES:
        print("usage: qa_cache_e2e.py <tmp> <%s> <compiler...>" % "|".join(sorted(CASES)))
        return 2
    tmp = os.path.abspath(argv[1])
    os.makedirs(tmp, exist_ok=True)
    compiler = argv[3:]
    if not os.path.isabs(compiler[0]):
        compiler[0] = os.path.join(ROOT, compiler[0])
    CASES[argv[2]](compiler, tmp)
    if FAILURES:
        print("qa-cache-e2e %s: %d failure(s)" % (argv[2], len(FAILURES)))
        return 1
    print("qa-cache-e2e %s: OK" % argv[2])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
