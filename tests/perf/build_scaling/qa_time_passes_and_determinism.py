#!/usr/bin/env python3
"""T486 QA adversarial test:
1. Verifies `--time-passes` preserves all 9 existing top-level `time:` lines unchanged and emits
   all 15 `time-build:` sub-timers whose sum matches `time: build` at both `-O0` and `-O1`.
2. Stresses T486's hash-indexed symbol/const/mono tables, CSR liveness/loop detection, and
   regalloc merge-sort/spill-slot coloring on a program with 128+ functions, trait default methods,
   generic instantiations, const tables, nested loops, and high register pressure; verifies
   repeated `-O0` and `-O1` builds produce byte-identical `.exe` outputs (SPEC-76 INV-DET-004)
   and that the native executables print the exact expected result.
"""
import argparse
import hashlib
import os
import re
import subprocess
import sys

EXPECTED_TOP = [
    "source", "lex", "parse", "resolve", "hir", "typeck", "own", "mono", "build",
]
EXPECTED_SUB = [
    "async", "mir_build", "mir_drop", "mir_opt", "mir_callty",
    "collect", "consts", "lir", "abi", "isel", "frame",
    "mverify", "encode", "obj_final", "link_rest",
]

TOP_RE = re.compile(r"^time:\s+(\w+)\s+([0-9]+\.[0-9]{4})s$")
SUB_RE = re.compile(r"^time-build:\s+(\w+)\s+([0-9]+\.[0-9]{4})s$")


def gen_stress_program(n=64):
    """Generates a deterministic stress program exercising:
    - many similar/prefix-colliding function & const names (hash table probing & resize > 64)
    - trait with a default method + overrides (trait member table & mono clone table)
    - generic function instantiated at multiple types (mono worklist & item cache)
    - nested loops with back-edges & many live temporaries (CSR liveness + regalloc merge-sort/spilling)
    """
    out = []
    w = out.append
    w("trait Score {")
    w("    fn base(self: view<Self>) -> u64;")
    w("    fn bonus(self: view<Self>) -> u64 {")
    w("        self.base() + 7u64")
    w("    }")
    w("}")
    w("")
    w("fn mix_gen<T>(x: T, y: T, pick: bool) -> T {")
    w("    if pick { x } else { y }")
    w("}")
    w("")
    for i in range(n):
        w("struct Item_%03d { a: u64, b: u64 }" % i)
        w("const CTBL_%03d: [4]u64 = [%du64, %du64, %du64, %du64];" % (i, i + 1, i + 2, i + 3, i + 4))
        w("impl Score for Item_%03d {" % i)
        w("    fn base(self: view<Item_%03d>) -> u64 { self.a + self.b + CTBL_%03d[2] }" % (i, i))
        if i % 3 == 0:
            w("    fn bonus(self: view<Item_%03d>) -> u64 { self.base() + 11u64 }" % i)
        w("}")
        w("fn sym_collide_prefix_%03d(v: u64) -> u64 {" % i)
        w("    let it = Item_%03d { a: v, b: %du64 };" % (i, i))
        w("    let s = \"pfx_%03d\";" % i)
        w("    it.bonus() + (len(s) as u64)")
        w("}")
        w("")

    # Nested loop + high live-variable pressure function to exercise CSR liveness & regalloc merge sort/spill slots
    w("fn pressure_loops(iters: u64) -> u64 {")
    w("    let mut acc: u64 = 0u64;")
    w("    let mut i: u64 = 0u64;")
    w("    while i < iters {")
    w("        let v0 = i + 1u64;")
    w("        let v1 = v0 + 2u64;")
    w("        let v2 = v1 + 3u64;")
    w("        let v3 = v2 + 4u64;")
    w("        let v4 = v3 + 5u64;")
    w("        let v5 = v4 + 6u64;")
    w("        let v6 = v5 + 7u64;")
    w("        let v7 = v6 + 8u64;")
    w("        let v8 = v7 + 9u64;")
    w("        let v9 = v8 + 10u64;")
    w("        let v10 = v9 + 11u64;")
    w("        let v11 = v10 + 12u64;")
    w("        let v12 = v11 + 13u64;")
    w("        let v13 = v12 + 14u64;")
    w("        let v14 = v13 + 15u64;")
    w("        let v15 = v14 + 16u64;")
    w("        let mut j: u64 = 0u64;")
    w("        while j < 3u64 {")
    w("            let mut k: u64 = 0u64;")
    w("            while k < 2u64 {")
    w("                acc = acc + mix_gen<u64>(v0 + v2 + v4 + v6 + v8 + v10 + v12 + v14, v1 + v3 + v5 + v7 + v9 + v11 + v13 + v15, ((i + j + k) % 2u64) == 0u64);")
    w("                k = k + 1u64;")
    w("            }")
    w("            j = j + 1u64;")
    w("        }")
    w("        acc = acc + (mix_gen<u32>(v0 as u32, v15 as u32, i == 0u64) as u64);")
    w("        i = i + 1u64;")
    w("    }")
    w("    acc")
    w("}")
    w("")
    w("fn main() -> i32 {")
    w("    let mut total: u64 = pressure_loops(4u64);")
    for i in range(n):
        w("    total = total + sym_collide_prefix_%03d(%du64);" % (i, i))
    # Compute expected checksum in Python below and verify exact match in native executable!
    expected = compute_expected(n)
    w("    if total == %du64 {" % expected)
    w("        print(\"CHECKSUM_OK\\n\");")
    w("        0")
    w("    } else {")
    w("        print(\"CHECKSUM_BAD\\n\");")
    w("        1")
    w("    }")
    w("}")
    w("")
    return "\n".join(out)


def compute_expected(n):
    acc = 0
    for i in range(4):
        vs = []
        v = i + 1
        vs.append(v)
        for step in range(2, 17):
            v += step
            vs.append(v)
        even_sum = sum(vs[0::2])
        odd_sum = sum(vs[1::2])
        for j in range(3):
            for k in range(2):
                acc += even_sum if ((i + j + k) % 2 == 0) else odd_sum
        acc += vs[0] if i == 0 else vs[15]
    total = acc
    for i in range(n):
        base = i + i + (i + 3)
        bonus = base + (11 if i % 3 == 0 else 7)
        total += bonus + len("pfx_%03d" % i)
    return total


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def build_and_check_timers(compiler, src, exe, opt, env):
    cmd = [os.path.abspath(compiler), "build", "--time-passes", src, "-o", exe, "-" + opt]
    p = subprocess.run(cmd, capture_output=True, env=env, timeout=300)
    txt = (p.stdout + p.stderr).decode("utf-8", "replace")
    if p.returncode != 0:
        raise RuntimeError("compile failed (-%s, rc=%d):\n%s" % (opt, p.returncode, txt[-2000:]))
    top_seen = []
    top_vals = {}
    sub_seen = []
    sub_vals = {}
    build_idx = -1
    lines = txt.splitlines()
    for idx, ln in enumerate(lines):
        s = ln.strip()
        m_top = TOP_RE.match(s)
        if m_top:
            name, val = m_top.group(1), float(m_top.group(2))
            top_seen.append(name)
            top_vals[name] = val
            if name == "build":
                build_idx = idx
            continue
        m_sub = SUB_RE.match(s)
        if m_sub:
            if build_idx < 0:
                raise RuntimeError("time-build line appeared before `time: build`: %s" % s)
            name, val = m_sub.group(1), float(m_sub.group(2))
            sub_seen.append(name)
            sub_vals[name] = val

    if top_seen != EXPECTED_TOP:
        raise RuntimeError("-%s top-level time: stages mismatch: got %r, expected %r" % (opt, top_seen, EXPECTED_TOP))
    if sub_seen != EXPECTED_SUB:
        raise RuntimeError("-%s time-build: sub-timers mismatch: got %r, expected %r" % (opt, sub_seen, EXPECTED_SUB))
    sub_sum = sum(sub_vals.values())
    build_t = top_vals["build"]
    if abs(sub_sum - build_t) > 0.05:
        raise RuntimeError("-%s time-build sum %.4fs != time: build %.4fs" % (opt, sub_sum, build_t))
    return sha256_file(exe)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--compiler", required=True)
    ap.add_argument("--tmp", required=True)
    a = ap.parse_args()
    os.makedirs(a.tmp, exist_ok=True)
    src = os.path.join(a.tmp, "stress_t486.ax")
    with open(src, "w", encoding="utf-8", newline="\n") as f:
        f.write(gen_stress_program(64))

    env = dict(os.environ)
    env["SOURCE_DATE_EPOCH"] = "0"

    for opt in ("O0", "O1"):
        exe1 = os.path.join(a.tmp, "stress_%s_1.exe" % opt)
        exe2 = os.path.join(a.tmp, "stress_%s_2.exe" % opt)
        h1 = build_and_check_timers(a.compiler, src, exe1, opt, env)
        h2 = build_and_check_timers(a.compiler, src, exe2, opt, env)
        if h1 != h2:
            print("FAIL determinism (-%s): run1=%s run2=%s" % (opt, h1, h2))
            return 1
        for exe in (exe1, exe2):
            r = subprocess.run([exe], capture_output=True, timeout=60)
            out = r.stdout.decode("utf-8", "replace")
            if r.returncode != 0 or out != "CHECKSUM_OK\n":
                print("FAIL native exec (%s): rc=%d stdout=%r" % (exe, r.returncode, out))
                return 1
    sys.stdout.buffer.write(b"OK qa_time_passes_and_determinism\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
