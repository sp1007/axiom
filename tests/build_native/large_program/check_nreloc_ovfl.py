#!/usr/bin/env python3
"""T461a: the linker reads IMAGE_SCN_LNK_NRELOC_OVFL relocation tables from `.obj` inputs.

Emits a small program as a COFF object (`build --kind obj`), rewrites the relocation table of every
section that has relocations into the overflow form (NumberOfRelocations = 0xFFFF, flag
IMAGE_SCN_LNK_NRELOC_OVFL, first entry = real entry count including itself; PE/COFF spec section
"Section Flags") and links the rewritten object:

  * well-formed overflow table   -> links, runs, prints the Python-reference output;
  * overflow count 0             -> rejected with AX_LINK_BAD_OBJECT (no image);
  * overflow count past the file -> rejected with AX_LINK_BAD_OBJECT (no image).

Linking a real >65,535-relocation object standalone takes minutes (pre-existing linker cost, see the
T461a report), so the overflow form is exercised here on a small object; run_large.py covers the
real overflow through the normal build path.

Usage (exec manifest): check_nreloc_ovfl.py <compiler> <root> <tmp>
Prints `NRELOC-OVFL PASS <sections>` on success. Python stdlib only.
"""

import os
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_large  # noqa: E402

IMAGE_SCN_LNK_NRELOC_OVFL = 0x01000000


def rewrite(obj, count_override=None):
    """Returns (new bytes, number of sections rewritten)."""
    b = bytearray(obj)
    nsec = struct.unpack_from("<H", b, 2)[0]
    tail = bytearray()
    done = 0
    for s in range(nsec):
        h = 20 + 40 * s
        ptr, = struct.unpack_from("<I", b, h + 24)
        n16, = struct.unpack_from("<H", b, h + 32)
        chars, = struct.unpack_from("<I", b, h + 36)
        if n16 == 0 or chars & IMAGE_SCN_LNK_NRELOC_OVFL:
            continue
        new_ptr = len(b) + len(tail)
        count = n16 + 1 if count_override is None else count_override
        tail += struct.pack("<IIH", count, 0, 0)
        tail += b[ptr:ptr + 10 * n16]
        struct.pack_into("<I", b, h + 24, new_ptr)
        struct.pack_into("<H", b, h + 32, 0xFFFF)
        struct.pack_into("<I", b, h + 36, chars | IMAGE_SCN_LNK_NRELOC_OVFL)
        done += 1
    return bytes(b + tail), done


def main():
    if len(sys.argv) != 4:
        print("usage: check_nreloc_ovfl.py <compiler> <root> <tmp>", file=sys.stderr)
        return 2
    compiler, root, tmp = (os.path.abspath(a) for a in sys.argv[1:4])
    std_root = os.path.join(root, "std")
    os.makedirs(tmp, exist_ok=True)
    work = tempfile.mkdtemp(prefix="nreloc_ovfl_", dir=tmp)
    src, want = run_large.generate(2)
    src_path = os.path.join(work, "small.ax")
    with open(src_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    obj = os.path.join(work, "small.obj")
    r = subprocess.run([compiler, "build", "--kind", "obj", "--std-root", std_root, "-o", obj, src_path],
                       capture_output=True, timeout=600)
    if r.returncode != 0:
        print("obj build failed rc=%d: %s" % (r.returncode, r.stderr.decode("utf-8", "replace")[:2000]))
        return 1
    with open(obj, "rb") as f:
        orig = f.read()

    good, nsec = rewrite(orig)
    if nsec == 0:
        print("no section with relocations in %s" % obj)
        return 1
    cases = [("good", good, True)]
    cases.append(("count0", rewrite(orig, 0)[0], False))
    cases.append(("past_eof", rewrite(orig, 0x7FFFFFFF)[0], False))
    for name, data, ok in cases:
        p = os.path.join(work, name + ".obj")
        exe = os.path.join(work, name + ".exe")
        with open(p, "wb") as f:
            f.write(data)
        r = subprocess.run([compiler, "build", "--std-root", std_root, "-o", exe, p], capture_output=True, timeout=600)
        err = r.stderr.decode("utf-8", "replace") + r.stdout.decode("utf-8", "replace")
        if ok:
            if r.returncode != 0:
                print("%s: link failed rc=%d: %s" % (name, r.returncode, err[:2000]))
                return 1
            x = subprocess.run([exe], capture_output=True, timeout=120)
            got = x.stdout.replace(b"\r\n", b"\n")
            if x.returncode != 0 or got != want:
                print("%s: run rc=%d (0x%08X)" % (name, x.returncode, x.returncode & 0xFFFFFFFF))
                run_large.diff_report(name, got, want)
                return 1
        else:
            if r.returncode == 0 or "AX_LINK_BAD_OBJECT" not in err:
                print("%s: expected AX_LINK_BAD_OBJECT, rc=%d: %s" % (name, r.returncode, err[:2000]))
                return 1
            if os.path.exists(exe):
                print("%s: an image was written for a malformed object" % name)
                return 1
    print("NRELOC-OVFL PASS %d" % nsec)
    return 0


if __name__ == "__main__":
    sys.exit(main())
