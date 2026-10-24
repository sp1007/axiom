#!/usr/bin/env python3
"""QA T147 boundary test (ADR-0035 section 2): STATIC symbols never enter the global name table.

usage: qa_check_static_not_global.py <build_dir> <tmp_dir>

Hand-built COFF objects (bytes from the PE/COFF spec via gen_local_symbols_obj.build_coff, not from
either compiler), linked with the axiom0 PE linker through the T147 C driver:

  hidden.obj   defines STATIC `hk` (.rdata+0 = 11) and EXTERNAL `vis` (.rdata+8 = 2); no code.
  user.obj     main: exit code = byte [hk] + 16 * byte [vis], both relocations against UNDEFINED
               EXTERNAL symbols (SectionNumber 0) resolved by name.
  shadow.obj   defines EXTERNAL `hk` (.rdata+0 = 7) and its own STATIC `vis` (.rdata+8 = 13), never
               referenced.

  1. hidden.obj + user.obj must FAIL with AX_LINK_UNDEFINED_SYMBOL: the only `hk` definition is
     STATIC in another object, so a by-name reference must not see it.
  2. hidden.obj + shadow.obj + user.obj must link and exit 7 + 16 * 2 = 39: `hk` resolves to the
     EXTERNAL in shadow.obj (not hidden.obj's STATIC 11 -> 43), `vis` to the EXTERNAL in hidden.obj
     (not shadow.obj's STATIC 13 -> 215).
  3. shadow.obj + hidden.obj (link order swapped) + user.obj: same exit code 39 (order-independent).
"""

import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_local_symbols_obj as gen  # noqa: E402

EXPECTED = 7 + 16 * 2


def run(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)


def data_obj(static_name, static_val, ext_name, ext_val):
    rdata = bytearray(16)
    rdata[0] = static_val if static_name == "hk" else ext_val
    rdata[8] = ext_val if ext_name == "vis" else static_val
    syms = []
    if static_name == "hk":
        syms.append(gen.sym_record("hk", 0, 1, gen.IMAGE_SYM_CLASS_STATIC))
        syms.append(gen.sym_record("vis", 8, 1, gen.IMAGE_SYM_CLASS_EXTERNAL))
    else:
        syms.append(gen.sym_record("hk", 0, 1, gen.IMAGE_SYM_CLASS_EXTERNAL))
        syms.append(gen.sym_record("vis", 8, 1, gen.IMAGE_SYM_CLASS_STATIC))
    return gen.build_coff([(".rdata", bytes(rdata), [], gen.SCN_DATA_X8_R)], syms)


def user_obj():
    main = bytes([
        0x0F, 0xB6, 0x05, 0, 0, 0, 0,        # movzx eax, byte [rip+hk]   (reloc at +3)
        0x0F, 0xB6, 0x0D, 0, 0, 0, 0,        # movzx ecx, byte [rip+vis]  (reloc at +10)
        0xC1, 0xE1, 0x04,                    # shl ecx, 4
        0x01, 0xC8,                          # add eax, ecx
        0xC3,                                # ret
    ])
    syms = [
        gen.sym_record("main", 0, 1, gen.IMAGE_SYM_CLASS_EXTERNAL, 0x20),
        gen.sym_record("hk", 0, 0, gen.IMAGE_SYM_CLASS_EXTERNAL),   # undefined
        gen.sym_record("vis", 0, 0, gen.IMAGE_SYM_CLASS_EXTERNAL),  # undefined
    ]
    return gen.build_coff([(".text", main, [(3, 1), (10, 2)], gen.SCN_CODE_X16_RX)], syms)


def main():
    build_dir, tmp = sys.argv[1], sys.argv[2]
    os.makedirs(tmp, exist_ok=True)
    driver = os.path.join(build_dir, "tests", "ct_link_local_symbols_cdriver_link_objs")
    if sys.platform == "win32":
        driver += ".exe"
    objs = {
        "hidden.obj": data_obj("hk", 11, "vis", 2),
        "shadow.obj": data_obj("vis", 13, "hk", 7),
        "user.obj": user_obj(),
    }
    for name, data in objs.items():
        with open(os.path.join(tmp, name), "wb") as f:
            f.write(data)
    p = lambda n: os.path.join(tmp, n)  # noqa: E731

    r = run([driver, p("undef.exe"), p("hidden.obj"), p("user.obj")])
    if r.returncode == 0 or r.stdout.strip() != "LINK-FAILED AX_LINK_UNDEFINED_SYMBOL":
        print("FAIL: STATIC `hk` of another object satisfied a by-name reference: rc=%d out=%r"
              % (r.returncode, r.stdout))
        return 1

    for tag, order in (("a", ["hidden.obj", "shadow.obj", "user.obj"]),
                       ("b", ["shadow.obj", "hidden.obj", "user.obj"])):
        exe = p("shadow_%s.exe" % tag)
        r = run([driver, exe] + [p(o) for o in order])
        if r.returncode != 0 or r.stdout.strip() != "LINKED":
            print("FAIL: link %s: rc=%d out=%r err=%r" % (order, r.returncode, r.stdout, r.stderr))
            return 1
        q = run([exe])
        if q.returncode != EXPECTED:
            print("FAIL: link %s: image exit %d, expected %d (a by-name reference bound to a STATIC)"
                  % (order, q.returncode, EXPECTED))
            return 1
    print("QA-STATIC-NOT-GLOBAL ok exit=%d" % EXPECTED)
    return 0


if __name__ == "__main__":
    sys.exit(main())
