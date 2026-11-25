#!/usr/bin/env python3
"""T461a QA (adversarial): relocation-count boundary of the COFF NumberOfRelocations field.

The engineer's tests use 66 / 200 / 330 / 500 chunks. They never sit ON the 16-bit boundary. This
script tunes a generated program so that its largest section (.text) carries exactly 0xFFFE, 0xFFFF
and 0x10000 relocations (the three values around the overflow switch of `coff_reloc_entries`), then
for each target:

  * emits the `.obj` and checks the header form: <= 0xFFFE -> plain count, no flag; >= 0xFFFF ->
    NumberOfRelocations = 0xFFFF + IMAGE_SCN_LNK_NRELOC_OVFL, first entry = real entries + 1;
  * checks GNU `objdump -r` lists exactly as many relocations as the header says;
  * checks GNU `ld -r` accepts the object (reads and re-writes the relocation table);
  * builds natively at -O0, runs, and compares stdout byte for byte with a Python IEEE-754 reference.

The program is: K chunk functions (100 `pr(plain_f32(from_bits_f32(N)))` statements each), a tail
function with M such statements, and a `main` that calls every chunk, the tail, and E extra times
chunk_0 (each extra call is one more `call rel32` and so one more relocation, used to adjust parity).

Usage (exec manifest): qa_reloc_boundary.py <compiler> <root> <tmp>
Prints `RELOC-BOUNDARY PASS` on success. Python stdlib only.
"""

import os
import random
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_large  # noqa: E402

OVFL = 0x01000000
CHUNKS = 320


def generate(m, e):
    rng = random.Random(4610)
    src = [
        "module large.program",
        "use std.core.float.to_bits_f32",
        "use std.core.float.from_bits_f32",
        "fn pr(x: f32) -> i32 {",
        "    print_int(to_bits_f32(x) as i64);",
        '    print("\\n");',
        "    0",
        "}",
        "fn plain_f32(x: f32) -> f32 {",
        "    x * 1.5 + 1.0",
        "}",
    ]
    want = []

    def stmt(out_src, out_want):
        v = 0x3F800000 + rng.randint(0, 0x1000000)
        out_src.append("    pr(plain_f32(from_bits_f32(%du32)));" % v)
        r = run_large.f32(run_large.f32(run_large.bits_f32(v) * 1.5) + 1.0)
        out_want.append("%d\n" % run_large.f32_bits(r))

    chunk_want = []
    for c in range(CHUNKS):
        src.append("fn chunk_%d() -> i32 {" % c)
        w = []
        for _ in range(100):
            stmt(src, w)
        chunk_want.append(w)
        src.append("    0")
        src.append("}")
    src.append("fn tail() -> i32 {")
    tail_want = []
    for _ in range(m):
        stmt(src, tail_want)
    src.append("    0")
    src.append("}")
    src.append("fn main() -> i32 {")
    for c in range(CHUNKS):
        src.append("    chunk_%d();" % c)
        want.extend(chunk_want[c])
    src.append("    tail();")
    want.extend(tail_want)
    for _ in range(e):
        src.append("    chunk_0();")
        want.extend(chunk_want[0])
    src.append("    0")
    src.append("}")
    return "\n".join(src) + "\n", "".join(want).encode("ascii")


def sections(path):
    """[(name, n_real_relocs, form)] with form in {'plain','ovfl'}; validates the overflow entry."""
    with open(path, "rb") as f:
        b = f.read()
    nsec = struct.unpack_from("<H", b, 2)[0]
    out = []
    for s in range(nsec):
        h = 20 + 40 * s
        name = b[h:h + 8].rstrip(b"\0").decode("ascii", "replace")
        ptr, = struct.unpack_from("<I", b, h + 24)
        n16, = struct.unpack_from("<H", b, h + 32)
        chars, = struct.unpack_from("<I", b, h + 36)
        if chars & OVFL:
            assert n16 == 0xFFFF, "%s: OVFL flag with count %d" % (name, n16)
            entries, sym, typ = struct.unpack_from("<IIH", b, ptr)
            assert sym == 0 and typ == 0, "%s: overflow entry sym/type" % name
            assert ptr + 10 * entries <= len(b), "%s: table past EOF" % name
            out.append((name, entries - 1, "ovfl"))
        else:
            assert n16 != 0xFFFF, "%s: 0xFFFF without OVFL flag" % name
            out.append((name, n16, "plain"))
    return out


def text_relocs(path):
    return max(n for (_, n, _) in sections(path))


def build_obj(compiler, std_root, work, tag, src):
    sp = os.path.join(work, tag + ".ax")
    with open(sp, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    obj = os.path.join(work, tag + ".obj")
    r = subprocess.run([compiler, "build", "--emit", "obj", "--std-root", std_root, sp, "-o", obj],
                       capture_output=True, timeout=3000)
    if r.returncode != 0:
        print("obj build %s failed rc=%d: %s" % (tag, r.returncode, r.stderr.decode("utf-8", "replace")[:2000]))
        sys.exit(1)
    return sp, obj


def main():
    if len(sys.argv) != 4:
        print("usage: qa_reloc_boundary.py <compiler> <root> <tmp>", file=sys.stderr)
        return 2
    compiler, root, tmp = (os.path.abspath(a) for a in sys.argv[1:4])
    std_root = os.path.join(root, "std")
    os.makedirs(tmp, exist_ok=True)
    work = tempfile.mkdtemp(prefix="qa_reloc_", dir=tmp)

    # Calibrate R(m, e) = base + a*m + e.
    _, o0 = build_obj(compiler, std_root, work, "cal0", generate(0, 0)[0])
    r0 = text_relocs(o0)
    _, o1 = build_obj(compiler, std_root, work, "cal1", generate(10, 1)[0])
    r1 = text_relocs(o1)
    # r1 - r0 = 10*a + 1 (a statements cost the same each); a must be an integer.
    a, rem = divmod(r1 - r0 - 1, 10)
    if rem != 0 or a <= 0:
        print("calibration failed: r0=%d r1=%d" % (r0, r1))
        return 1
    print("calibration: base=%d relocs per statement=%d" % (r0, a))

    for target in (0xFFFE, 0xFFFF, 0x10000):
        need = target - r0
        if need < 0:
            print("base %d already above target %d" % (r0, target))
            return 1
        m, e = divmod(need, a)
        # e < a extra single-reloc calls adjust the remainder (each extra call is one relocation).
        tag = "t%x" % target
        src, want = generate(m, e)
        sp, obj = build_obj(compiler, std_root, work, tag, src)
        secs = sections(obj)
        biggest = max(secs, key=lambda x: x[1])
        if biggest[1] != target:
            print("%s: wanted %d relocations in the largest section, got %s" % (tag, target, biggest))
            return 1
        want_form = "ovfl" if target >= 0xFFFF else "plain"
        if biggest[2] != want_form:
            print("%s: %d relocations encoded as %s, expected %s" % (tag, target, biggest[2], want_form))
            return 1
        total = sum(n for (_, n, _) in secs)
        rr = subprocess.run(["objdump", "-r", obj], capture_output=True)
        if rr.returncode != 0:
            print("%s: objdump -r failed: %s" % (tag, rr.stderr.decode("utf-8", "replace")[:500]))
            return 1
        seen = sum(1 for ln in rr.stdout.decode("utf-8", "replace").splitlines() if "IMAGE_REL_AMD64_" in ln)
        if seen != total:
            print("%s: objdump lists %d relocations, header says %d" % (tag, seen, total))
            return 1
        lo = os.path.join(work, tag + "_ld.obj")
        rl = subprocess.run(["ld", "-r", "-o", lo, obj], capture_output=True)
        if rl.returncode != 0:
            print("%s: ld -r rejected the object: %s" % (tag, rl.stderr.decode("utf-8", "replace")[:500]))
            return 1
        exe = os.path.join(work, tag + ".exe")
        rb = subprocess.run([compiler, "build", "--std-root", std_root, sp, "-o", exe],
                            capture_output=True, timeout=3000)
        if rb.returncode != 0:
            print("%s: native build failed: %s" % (tag, rb.stderr.decode("utf-8", "replace")[:2000]))
            return 1
        rx = subprocess.run([exe], capture_output=True, timeout=300)
        got = rx.stdout.replace(b"\r\n", b"\n")
        if rx.returncode != 0 or got != want:
            print("%s: native rc=%d (0x%08X)" % (tag, rx.returncode, rx.returncode & 0xFFFFFFFF))
            run_large.diff_report(tag, got, want)
            return 1
        print("%s: %d relocs (%s), objdump/ld -r ok, native stdout %d lines ok" % (tag, target, want_form, want.count(b"\n")))
    print("RELOC-BOUNDARY PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
