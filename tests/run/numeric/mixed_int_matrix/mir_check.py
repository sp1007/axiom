#!/usr/bin/env python3
"""T455 oracle: `inspect --emit=mir` of mixed-width integer code is homogeneous and carries explicit promotion casts.

SPEC-40 AXS-INT-054: every implicit integer promotion is materialised as `_t = copy _narrow as <T_common>` before the
binary operation / index projection, and every MIR binary operation (except shifts) has operands of one identical type
(INV-INT-003).  This script runs the compiler, parses the textual MIR and checks

  body 0  `calc(b8: u8, s8: i8, u16v: u16, s32: i32, s64: i64) -> i64` (Pattern D): a cast from the type of each of
          b8, s8, u16v, s32 to the type of s64 exists, no cast has equal source and destination type, every binary
          operation is homogeneous, and the number of promotion casts is at least 5
  body 1  `idx(a, i: i16, j: u8, n: usize)`: the u8 operand is cast to i16, the i16 sum is cast to the type of `n`
          (usize) and that cast temporary, not the i16 value, is the projection index
  body 2  `sh(x: u32, n: u8)`: the shift keeps operands of different types (shifts are exempt)

usage: mir_check.py <compiler> <program.ax>          prints `MIR-HOMOGENEOUS OK` or the first violation (exit 1)
       mir_check.py --selftest                       proves the checker rejects a mixed-type add (exit 0 when it does)
"""

import re
import subprocess
import sys

LOCAL_RE = re.compile(r"^\s*let (?:mut )?_(\d+): (type#\d+);")
CAST_RE = re.compile(r"^\s*_(\d+) = (?:copy|move) _(\d+) as (type#\d+);")
BIN_RE = re.compile(r"(?:copy|move) _(\d+) (\+|-|\*|/|%|&|\||\^|<<|>>|<=|>=|<|>|==|!=) (?:copy|move) _(\d+)")
INDEX_RE = re.compile(r"\(\*\(_\d+\)\)\[_(\d+)\]|\b_\d+\[_(\d+)\]")


def split_bodies(text):
    bodies, cur = [], None
    for line in text.splitlines():
        if line.startswith("mir_body {"):
            cur = []
            bodies.append(cur)
        elif cur is not None:
            cur.append(line)
    return bodies


def analyse(body):
    types, casts, binops, indexes = {}, [], [], []
    for line in body:
        m = LOCAL_RE.match(line)
        if m:
            types[int(m.group(1))] = m.group(2)
            continue
        m = CAST_RE.match(line)
        if m:
            casts.append((int(m.group(1)), int(m.group(2)), m.group(3)))
        for m in BIN_RE.finditer(line):
            binops.append((int(m.group(1)), m.group(2), int(m.group(3)), line.strip()))
        m = INDEX_RE.search(line)
        if m:
            indexes.append(int(m.group(1) or m.group(2)))
    return types, casts, binops, indexes


def homogeneous(types, binops):
    """First violation message or None; shifts are exempt (AXS-INT-054.2)."""
    for (a, op, b, line) in binops:
        if op in ("<<", ">>"):
            continue
        if a in types and b in types and types[a] != types[b]:
            return "mixed-type operands %s vs %s in `%s`" % (types[a], types[b], line)
    return None


def fail(msg):
    sys.stderr.write("MIR-CHECK FAIL: %s\n" % msg)
    return 1


def selftest():
    bad = ["mir_body {", "    let mut _0: type#9;", "    let _1: type#9;", "    let _2: type#11;", "    bb0: {",
           "        _0 = copy _1 + copy _2;", "    }", "}"]
    types, casts, binops, _ = analyse(split_bodies("\n".join(bad))[0])
    if homogeneous(types, binops) is None:
        return fail("selftest: a mixed-type add was not detected")
    good = bad[:]
    good[3] = "    let _2: type#9;"
    types, casts, binops, _ = analyse(split_bodies("\n".join(good))[0])
    if homogeneous(types, binops) is not None:
        return fail("selftest: a homogeneous add was flagged")
    sys.stdout.buffer.write(b"MIR-CHECKER SELFTEST OK\n")
    return 0


def main(argv):
    if argv[:1] == ["--selftest"]:
        return selftest()
    compiler, program = argv[0], argv[1]
    proc = subprocess.run([compiler, "inspect", "--emit=mir", program], capture_output=True, timeout=300)
    if proc.returncode != 0:
        return fail("inspect exit %d: %s" % (proc.returncode, proc.stderr.decode("utf-8", "replace")[:1500]))
    bodies = split_bodies(proc.stdout.decode("utf-8", "replace"))
    if len(bodies) < 3:
        return fail("expected at least 3 mir_body blocks, got %d" % len(bodies))

    # body 0: Pattern D
    types, casts, binops, _ = analyse(bodies[0])
    v = homogeneous(types, binops)
    if v:
        return fail("calc: " + v)
    for (d, s, t) in casts:
        if types.get(s) == t:
            return fail("calc: identity cast _%d -> %s" % (s, t))
    i64 = types[5]
    for k in (1, 2, 3, 4):
        if not any(types.get(s) == types[k] and t == i64 for (d, s, t) in casts) and \
                not any(t == i64 and types.get(s) == types[k] for (d, s, t) in casts):
            return fail("calc: no promotion cast from %s (parameter _%d) to %s" % (types[k], k, i64))
    promos = [c for c in casts if c[2] == i64]
    if len(promos) < 5:
        return fail("calc: expected >= 5 promotion casts to %s, found %d" % (i64, len(promos)))

    # body 1: index promotion
    types, casts, binops, indexes = analyse(bodies[1])
    v = homogeneous(types, binops)
    if v:
        return fail("idx: " + v)
    i16, u8, usize = types[2], types[3], types[4]
    if not any(types.get(s) == u8 and t == i16 for (d, s, t) in casts):
        return fail("idx: the u8 operand is not cast to i16 before the add")
    if not indexes:
        return fail("idx: no index projection found")
    for k in indexes:
        if types.get(k) != usize:
            return fail("idx: projection index _%d has type %s, expected usize %s" % (k, types.get(k), usize))
    if not any(t == usize for (d, s, t) in casts):
        return fail("idx: no cast to usize")

    # body 2: shift with differently typed count
    types, casts, binops, _ = analyse(bodies[2])
    shifts = [b for b in binops if b[1] in ("<<", ">>")]
    if not shifts:
        return fail("sh: no shift found")
    if not any(types.get(a) != types.get(b) for (a, op, b, line) in shifts):
        return fail("sh: the shift count was converted to the left operand type")
    v = homogeneous(types, binops)
    if v:
        return fail("sh: " + v)
    sys.stdout.buffer.write(b"MIR-HOMOGENEOUS OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
