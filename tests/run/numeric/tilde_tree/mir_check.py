#!/usr/bin/env python3
"""T499 oracle: `~` of a narrow leaf inside a widening tree lowers to `Cast(IntToInt, leaf, C)` followed by the
bit-not in `C` (ADR-0044 section 2, SPEC-40 AXS-INT-052 rule 4, INV-INT-003).

usage: mir_check.py <compiler> <program.ax>     prints `TILDE-MIR OK` or the first violation (exit 1)
       mir_check.py --selftest                  proves the checker rejects the pre-T499 shape (exit 0 when it does)

<program.ax> is tests/run/numeric/tilde_tree/mir_shapes.ax:
  body 0  `tree(b8: u8, s64: i64) -> i64 { let r: i64 = ~b8 + s64; r }`: there is a cast from the u8 parameter to
          the type of s64, the bit-not reads that cast temporary and writes a local of the type of s64, and every
          binary operation is homogeneous
  body 1  `alone(b8: u8) -> u8 { let r: u8 = ~b8; r }`: no cast at all, the bit-not reads the u8 parameter
"""

import re
import subprocess
import sys

LOCAL_RE = re.compile(r"^\s*let (?:mut )?_(\d+): (type#\d+);")
CAST_RE = re.compile(r"^\s*_(\d+) = (?:copy|move) _(\d+) as (type#\d+);")
NOT_RE = re.compile(r"^\s*_(\d+) = ~\(?\s*(?:copy|move) _(\d+)")
BIN_RE = re.compile(r"(?:copy|move) _(\d+) (\+|-|\*|/|%|&|\||\^|<=|>=|<|>|==|!=) (?:copy|move) _(\d+)")


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
    types, casts, nots, binops = {}, [], [], []
    for line in body:
        m = LOCAL_RE.match(line)
        if m:
            types[int(m.group(1))] = m.group(2)
            continue
        m = CAST_RE.match(line)
        if m:
            casts.append((int(m.group(1)), int(m.group(2)), m.group(3)))
        m = NOT_RE.match(line)
        if m:
            nots.append((int(m.group(1)), int(m.group(2))))
        for m in BIN_RE.finditer(line):
            binops.append((int(m.group(1)), m.group(2), int(m.group(3)), line.strip()))
    return types, casts, nots, binops


def check_tree(body):
    """Locals: _0 return, _1 b8, _2 s64 (parameters first)."""
    types, casts, nots, binops = analyse(body)
    if 1 not in types or 2 not in types:
        return "tree: parameters _1/_2 not found"
    ctx = types[2]
    promo = [d for (d, s, t) in casts if s == 1 and t == ctx]
    if not promo:
        return "tree: no cast of the u8 leaf _1 to the context type %s" % ctx
    if len(nots) != 1:
        return "tree: expected exactly one bit-not, found %d" % len(nots)
    dst, src = nots[0]
    if src not in promo:
        return "tree: the bit-not reads _%d, not the promotion cast temporary %s" % (src, promo)
    if types.get(dst) != ctx or types.get(src) != ctx:
        return "tree: the bit-not is not homogeneous in %s (dst %s, src %s)" % (ctx, types.get(dst), types.get(src))
    for (a, op, b, line) in binops:
        if a in types and b in types and types[a] != types[b]:
            return "tree: mixed-type operands in `%s`" % line
    return None


def check_alone(body):
    types, casts, nots, _ = analyse(body)
    if casts:
        return "alone: unexpected cast(s) %s" % casts
    if len(nots) != 1 or nots[0][1] != 1:
        return "alone: the bit-not does not read the u8 parameter directly (%s)" % nots
    if types.get(nots[0][0]) != types.get(1):
        return "alone: the bit-not result type differs from the operand type"
    return None


def fail(msg):
    sys.stderr.write("TILDE-MIR FAIL: %s\n" % msg)
    return 1


def selftest():
    # The pre-T499 lowering: ~ applied to the u8 leaf, the u8 result cast afterwards.
    old = ["mir_body {", "    let mut _0: type#9;", "    let _1: type#3;", "    let _2: type#9;",
           "    let _3: type#3;", "    let _4: type#9;", "    bb0: {", "        _3 = ~copy _1;",
           "        _4 = copy _3 as type#9;", "        _0 = copy _4 + copy _2;", "    }", "}"]
    if check_tree(split_bodies("\n".join(old))[0]) is None:
        return fail("selftest: the pre-T499 shape (not, then cast) was accepted")
    new = ["mir_body {", "    let mut _0: type#9;", "    let _1: type#3;", "    let _2: type#9;",
           "    let _3: type#9;", "    let _4: type#9;", "    bb0: {", "        _3 = copy _1 as type#9;",
           "        _4 = ~copy _3;", "        _0 = copy _4 + copy _2;", "    }", "}"]
    msg = check_tree(split_bodies("\n".join(new))[0])
    if msg is not None:
        return fail("selftest: the promote-first shape was rejected: " + msg)
    sys.stdout.buffer.write(b"TILDE-MIR SELFTEST OK\n")
    return 0


def main(argv):
    if len(argv) == 2 and argv[1] == "--selftest":
        return selftest()
    if len(argv) != 3:
        sys.stderr.write(__doc__)
        return 2
    p = subprocess.run([argv[1], "inspect", "--emit=mir", argv[2]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        return fail("inspect exited %d: %s" % (p.returncode, p.stderr.decode("utf-8", "replace")[:400]))
    bodies = split_bodies(p.stdout.decode("utf-8", "replace"))
    if len(bodies) < 2:
        return fail("expected at least 2 MIR bodies, got %d" % len(bodies))
    for (chk, body) in ((check_tree, bodies[0]), (check_alone, bodies[1])):
        msg = chk(body)
        if msg is not None:
            return fail(msg)
    sys.stdout.buffer.write(b"TILDE-MIR OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
