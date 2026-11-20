#!/usr/bin/env python3
"""T453: byte-exact encoding check for the 128-bit multi-precision and bit-manipulation instruction forms of
`compiler/target/x64/encode.ax` (ADC, SBB, SHLD, SHRD, BSWAP, BSF, BSR, LZCNT, TZCNT, POPCNT, one-operand
MUL/IMUL/DIV, NEG, NOT, CMOVcc, SETcc, TEST r, imm).

Usage (exec manifest): encode_int128.py <compiler> <root> <tmp>

1. Every vector's expected bytes were produced by GNU `as` + `objdump`; when both tools are on PATH the
   table is re-assembled and compared again (vector table drift is a failure), otherwise that step is
   reported as skipped.
2. A program embedding the *live* `compiler/target/x64/encode.ax` (plus the `compiler.obj.coff` stub of
   `coff_stub.ax.in`) calls each encoder and checks its bytes; it runs in --interp, native -O0 and native -O1.
Prints `ENCODE-INT128 PASS <n>` on success.
"""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

# (AT&T assembly, Axiom encoder call, expected bytes)
VECTORS = [
    # ADC
    ("adc %rax,%rdx", "x64_adc_rr(mut_view(sec), 8u8, AX_REG_RDX, AX_REG_RAX)", "48 11 c2"),
    ("adc %r8,%r9", "x64_adc_rr(mut_view(sec), 8u8, AX_REG_R9, AX_REG_R8)", "4d 11 c1"),
    ("adc %rdx,%r10", "x64_adc_rr(mut_view(sec), 8u8, AX_REG_R10, AX_REG_RDX)", "49 11 d2"),
    ("adc %r11d,%ecx", "x64_adc_rr(mut_view(sec), 4u8, AX_REG_RCX, AX_REG_R11)", "44 11 d9"),
    ("adc -8(%rbp),%rdx", "x64_adc_rm(mut_view(sec), 8u8, AX_REG_RDX, x64_mem_base_disp(AX_REG_RBP, -8))", "48 13 55 f8"),
    ("adc 0x100(%r12),%r11", "x64_adc_rm(mut_view(sec), 8u8, AX_REG_R11, x64_mem_base_disp(AX_REG_R12, 256))", "4d 13 9c 24 00 01 00 00"),
    ("adc %r9,8(%rsp)", "x64_adc_mr(mut_view(sec), 8u8, x64_mem_base_disp(AX_REG_RSP, 8), AX_REG_R9)", "4c 11 4c 24 08"),
    ("adc $0,%r10", "x64_adc_ri(mut_view(sec), 8u8, AX_REG_R10, 0)", "49 83 d2 00"),
    ("adc $-1,%r15", "x64_adc_ri(mut_view(sec), 8u8, AX_REG_R15, -1)", "49 83 d7 ff"),
    ("adc $0x12345,%rax", "x64_adc_ri(mut_view(sec), 8u8, AX_REG_RAX, 74565)", "48 15 45 23 01 00"),
    ("adc $0x12345,%rbx", "x64_adc_ri(mut_view(sec), 8u8, AX_REG_RBX, 74565)", "48 81 d3 45 23 01 00"),
    ("adc $300,%ecx", "x64_adc_ri(mut_view(sec), 4u8, AX_REG_RCX, 300)", "81 d1 2c 01 00 00"),
    # SBB
    ("sbb %rax,%rdx", "x64_sbb_rr(mut_view(sec), 8u8, AX_REG_RDX, AX_REG_RAX)", "48 19 c2"),
    ("sbb %r11,%r9", "x64_sbb_rr(mut_view(sec), 8u8, AX_REG_R9, AX_REG_R11)", "4d 19 d9"),
    ("sbb %rdx,%r10", "x64_sbb_rr(mut_view(sec), 8u8, AX_REG_R10, AX_REG_RDX)", "49 19 d2"),
    ("sbb %eax,%r8d", "x64_sbb_rr(mut_view(sec), 4u8, AX_REG_R8, AX_REG_RAX)", "41 19 c0"),
    ("sbb -16(%rbp),%rdx", "x64_sbb_rm(mut_view(sec), 8u8, AX_REG_RDX, x64_mem_base_disp(AX_REG_RBP, -16))", "48 1b 55 f0"),
    ("sbb 0x200(%r13),%r14", "x64_sbb_rm(mut_view(sec), 8u8, AX_REG_R14, x64_mem_base_disp(AX_REG_R13, 512))", "4d 1b b5 00 02 00 00"),
    ("sbb %rcx,(%rax)", "x64_sbb_mr(mut_view(sec), 8u8, x64_mem_base(AX_REG_RAX), AX_REG_RCX)", "48 19 08"),
    ("sbb $0,%rdx", "x64_sbb_ri(mut_view(sec), 8u8, AX_REG_RDX, 0)", "48 83 da 00"),
    ("sbb $127,%r11", "x64_sbb_ri(mut_view(sec), 8u8, AX_REG_R11, 127)", "49 83 db 7f"),
    ("sbb $0x7fffffff,%rax", "x64_sbb_ri(mut_view(sec), 8u8, AX_REG_RAX, 2147483647)", "48 1d ff ff ff 7f"),
    ("sbb $-129,%rsi", "x64_sbb_ri(mut_view(sec), 8u8, AX_REG_RSI, -129)", "48 81 de 7f ff ff ff"),
    # SHLD / SHRD
    ("shld %cl,%rax,%rdx", "x64_shld_rrcl(mut_view(sec), 8u8, AX_REG_RDX, AX_REG_RAX)", "48 0f a5 c2"),
    ("shld %cl,%r8,%r9", "x64_shld_rrcl(mut_view(sec), 8u8, AX_REG_R9, AX_REG_R8)", "4d 0f a5 c1"),
    ("shld %cl,%edx,%eax", "x64_shld_rrcl(mut_view(sec), 4u8, AX_REG_RAX, AX_REG_RDX)", "0f a5 d0"),
    ("shld %cl,%dx,%ax", "x64_shld_rrcl(mut_view(sec), 2u8, AX_REG_RAX, AX_REG_RDX)", "66 0f a5 d0"),
    ("shld $7,%rax,%rdx", "x64_shld_rri(mut_view(sec), 8u8, AX_REG_RDX, AX_REG_RAX, 7u8)", "48 0f a4 c2 07"),
    ("shld $63,%r10,%r11", "x64_shld_rri(mut_view(sec), 8u8, AX_REG_R11, AX_REG_R10, 63u8)", "4d 0f a4 d3 3f"),
    ("shrd %cl,%rdx,%rax", "x64_shrd_rrcl(mut_view(sec), 8u8, AX_REG_RAX, AX_REG_RDX)", "48 0f ad d0"),
    ("shrd %cl,%r15,%rbx", "x64_shrd_rrcl(mut_view(sec), 8u8, AX_REG_RBX, AX_REG_R15)", "4c 0f ad fb"),
    ("shrd %cl,%esi,%r12d", "x64_shrd_rrcl(mut_view(sec), 4u8, AX_REG_R12, AX_REG_RSI)", "41 0f ad f4"),
    ("shrd $1,%rdx,%rax", "x64_shrd_rri(mut_view(sec), 8u8, AX_REG_RAX, AX_REG_RDX, 1u8)", "48 0f ac d0 01"),
    ("shrd $33,%r9,%r8", "x64_shrd_rri(mut_view(sec), 8u8, AX_REG_R8, AX_REG_R9, 33u8)", "4d 0f ac c8 21"),
    # BSWAP
    ("bswap %rax", "x64_bswap_r(mut_view(sec), 8u8, AX_REG_RAX)", "48 0f c8"),
    ("bswap %r9", "x64_bswap_r(mut_view(sec), 8u8, AX_REG_R9)", "49 0f c9"),
    ("bswap %ecx", "x64_bswap_r(mut_view(sec), 4u8, AX_REG_RCX)", "0f c9"),
    ("bswap %r12d", "x64_bswap_r(mut_view(sec), 4u8, AX_REG_R12)", "41 0f cc"),
    # Bit scan / count
    ("bsf %rdx,%rax", "x64_bsf_rr(mut_view(sec), 8u8, AX_REG_RAX, AX_REG_RDX)", "48 0f bc c2"),
    ("bsf %r15,%r8", "x64_bsf_rr(mut_view(sec), 8u8, AX_REG_R8, AX_REG_R15)", "4d 0f bc c7"),
    ("bsr %rdx,%rax", "x64_bsr_rr(mut_view(sec), 8u8, AX_REG_RAX, AX_REG_RDX)", "48 0f bd c2"),
    ("bsr %eax,%r10d", "x64_bsr_rr(mut_view(sec), 4u8, AX_REG_R10, AX_REG_RAX)", "44 0f bd d0"),
    ("lzcnt %rdx,%rax", "x64_lzcnt_rr(mut_view(sec), 8u8, AX_REG_RAX, AX_REG_RDX)", "f3 48 0f bd c2"),
    ("lzcnt %r11,%r9", "x64_lzcnt_rr(mut_view(sec), 8u8, AX_REG_R9, AX_REG_R11)", "f3 4d 0f bd cb"),
    ("lzcnt %ecx,%eax", "x64_lzcnt_rr(mut_view(sec), 4u8, AX_REG_RAX, AX_REG_RCX)", "f3 0f bd c1"),
    ("tzcnt %rdx,%rax", "x64_tzcnt_rr(mut_view(sec), 8u8, AX_REG_RAX, AX_REG_RDX)", "f3 48 0f bc c2"),
    ("tzcnt %r8,%rcx", "x64_tzcnt_rr(mut_view(sec), 8u8, AX_REG_RCX, AX_REG_R8)", "f3 49 0f bc c8"),
    ("popcnt %rdx,%rax", "x64_popcnt_rr(mut_view(sec), 8u8, AX_REG_RAX, AX_REG_RDX)", "f3 48 0f b8 c2"),
    ("popcnt %r10,%r11", "x64_popcnt_rr(mut_view(sec), 8u8, AX_REG_R11, AX_REG_R10)", "f3 4d 0f b8 da"),
    ("popcnt %esi,%edi", "x64_popcnt_rr(mut_view(sec), 4u8, AX_REG_RDI, AX_REG_RSI)", "f3 0f b8 fe"),
    ("popcnt %dx,%ax", "x64_popcnt_rr(mut_view(sec), 2u8, AX_REG_RAX, AX_REG_RDX)", "66 f3 0f b8 c2"),
    # One-operand MUL / IMUL / DIV, NEG, NOT
    ("mulq %r11", "x64_mul_r(mut_view(sec), 8u8, AX_REG_R11)", "49 f7 e3"),
    ("mulq %rcx", "x64_mul_r(mut_view(sec), 8u8, AX_REG_RCX)", "48 f7 e1"),
    ("imulq %r11", "x64_imul1_r(mut_view(sec), 8u8, AX_REG_R11)", "49 f7 eb"),
    ("imulq %rdx", "x64_imul1_r(mut_view(sec), 8u8, AX_REG_RDX)", "48 f7 ea"),
    ("imulq -16(%rbp)", "x64_imul1_m(mut_view(sec), 8u8, x64_mem_base_disp(AX_REG_RBP, -16))", "48 f7 6d f0"),
    ("divq %r10", "x64_div_r(mut_view(sec), 8u8, AX_REG_R10)", "49 f7 f2"),
    ("divq -8(%rbp)", "x64_div_m(mut_view(sec), 8u8, x64_mem_base_disp(AX_REG_RBP, -8))", "48 f7 75 f8"),
    ("neg %rdx", "x64_neg_r(mut_view(sec), 8u8, AX_REG_RDX)", "48 f7 da"),
    ("neg %r9", "x64_neg_r(mut_view(sec), 8u8, AX_REG_R9)", "49 f7 d9"),
    ("not %rax", "x64_not_r(mut_view(sec), 8u8, AX_REG_RAX)", "48 f7 d0"),
    ("not %r10", "x64_not_r(mut_view(sec), 8u8, AX_REG_R10)", "49 f7 d2"),
    # Saturation selects (CMOVcc), flag materialization (SETcc), shift-count limb test (TEST r, imm)
    ("cmovb %r8,%rax", "x64_cmovcc_rr(mut_view(sec), 8u8, AX_CC_B, AX_REG_RAX, AX_REG_R8)", "49 0f 42 c0"),
    ("cmovb %r8,%rdx", "x64_cmovcc_rr(mut_view(sec), 8u8, AX_CC_B, AX_REG_RDX, AX_REG_R8)", "49 0f 42 d0"),
    ("cmovo %r9,%rax", "x64_cmovcc_rr(mut_view(sec), 8u8, AX_CC_O, AX_REG_RAX, AX_REG_R9)", "49 0f 40 c1"),
    ("cmovo %r10,%rdx", "x64_cmovcc_rr(mut_view(sec), 8u8, AX_CC_O, AX_REG_RDX, AX_REG_R10)", "49 0f 40 d2"),
    ("cmovne %r10,%rcx", "x64_cmovcc_rr(mut_view(sec), 8u8, AX_CC_NE, AX_REG_RCX, AX_REG_R10)", "49 0f 45 ca"),
    ("cmovne %r11,%r8", "x64_cmovcc_rr(mut_view(sec), 8u8, AX_CC_NE, AX_REG_R8, AX_REG_R11)", "4d 0f 45 c3"),
    ("cmovne %rax,%rdx", "x64_cmovcc_rr(mut_view(sec), 8u8, AX_CC_NE, AX_REG_RDX, AX_REG_RAX)", "48 0f 45 d0"),
    ("cmovl %rcx,%rax", "x64_cmovcc_rr(mut_view(sec), 8u8, AX_CC_L, AX_REG_RAX, AX_REG_RCX)", "48 0f 4c c1"),
    ("seto %al", "x64_setcc_r(mut_view(sec), AX_CC_O, AX_REG_RAX)", "0f 90 c0"),
    ("setb %r9b", "x64_setcc_r(mut_view(sec), AX_CC_B, AX_REG_R9)", "41 0f 92 c1"),
    ("setne %al", "x64_setcc_r(mut_view(sec), AX_CC_NE, AX_REG_RAX)", "0f 95 c0"),
    ("test $64,%rcx", "x64_test_ri(mut_view(sec), 8u8, AX_REG_RCX, 64)", "48 f7 c1 40 00 00 00"),
    ("test %r11,%r11", "x64_test_rr(mut_view(sec), 8u8, AX_REG_R11, AX_REG_R11)", "4d 85 db"),
]

IMPORTS = [
    "AX_REG_RAX", "AX_REG_RCX", "AX_REG_RDX", "AX_REG_RBX", "AX_REG_RSP", "AX_REG_RBP", "AX_REG_RSI",
    "AX_REG_RDI", "AX_REG_R8", "AX_REG_R9", "AX_REG_R10", "AX_REG_R11", "AX_REG_R12", "AX_REG_R13",
    "AX_REG_R14", "AX_REG_R15", "AX_CC_O", "AX_CC_B", "AX_CC_NE", "AX_CC_L", "x64_mem_base",
    "x64_mem_base_disp", "x64_adc_rr", "x64_adc_rm", "x64_adc_mr", "x64_adc_ri", "x64_sbb_rr", "x64_sbb_rm",
    "x64_sbb_mr", "x64_sbb_ri", "x64_shld_rrcl", "x64_shld_rri", "x64_shrd_rrcl", "x64_shrd_rri",
    "x64_bswap_r", "x64_bsf_rr", "x64_bsr_rr", "x64_lzcnt_rr", "x64_tzcnt_rr", "x64_popcnt_rr", "x64_mul_r",
    "x64_imul1_r", "x64_imul1_m", "x64_div_r", "x64_div_m", "x64_neg_r", "x64_not_r", "x64_cmovcc_rr",
    "x64_setcc_r", "x64_test_ri", "x64_test_rr",
]


def gnu_check(tmp):
    as_exe = shutil.which("as")
    od_exe = shutil.which("objdump")
    if not as_exe or not od_exe:
        return "skipped", []
    src = os.path.join(tmp, "v.s")
    obj = os.path.join(tmp, "v.o")
    with open(src, "w", encoding="utf-8", newline="\n") as f:
        f.write(".text\n")
        for asm, _, _ in VECTORS:
            f.write(asm + "\n")
    r = subprocess.run([as_exe, "--64", "-o", obj, src], capture_output=True, text=True)
    if r.returncode != 0:
        return "error", ["GNU as failed: " + r.stderr.strip()]
    r = subprocess.run([od_exe, "-d", "--insn-width=16", obj], capture_output=True, text=True)
    got = []
    for line in r.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3 and parts[0].strip().endswith(":"):
            got.append(parts[1].strip())
    errs = []
    # COFF pads .text to its alignment with NOPs after the last vector; only the first len(VECTORS) count.
    if len(got) < len(VECTORS):
        return "error", ["objdump listed %d instructions, expected %d" % (len(got), len(VECTORS))]
    got = got[:len(VECTORS)]
    for (asm, _, exp), g in zip(VECTORS, got):
        if g != exp:
            errs.append("vector table drift for `%s`: GNU as gives %s, table says %s" % (asm, g, exp))
    return "checked", errs


def build_program(root):
    with open(os.path.join(HERE, "coff_stub.ax.in"), encoding="utf-8") as f:
        stub = f.read()
    with open(os.path.join(root, "compiler", "target", "x64", "encode.ax"), encoding="utf-8") as f:
        enc = f.read()
    out = [stub.rstrip("\n"), "", enc.rstrip("\n"), "", "module main", ""]
    out.append("use compiler.obj.coff.Section")
    for name in IMPORTS:
        out.append("use compiler.target.x64.encode." + name)
    out.append("")
    out.append("fn chk(sec: mut_view<Section>, idx: i64, exp: view<[u8]>) -> i64 {")
    out.append("    let n = len(exp);")
    out.append("    let mut bad = sec.bytes_len != n;")
    out.append("    let mut i: usize = 0;")
    out.append("    while !bad && i < n {")
    out.append("        if sec.buf[i] != exp[i] {")
    out.append("            bad = true;")
    out.append("        }")
    out.append("        i = i + 1;")
    out.append("    }")
    out.append("    sec.bytes_len = 0;")
    out.append("    if bad {")
    out.append('        print("FAIL vector ");')
    out.append("        print_int(idx);")
    out.append('        print("\\n");')
    out.append("        return 1i64;")
    out.append("    }")
    out.append("    0i64")
    out.append("}")
    out.append("")
    out.append("fn main() -> i32 {")
    out.append("    let mut sec = Section {")
    out.append("        bytes: 0 as *mut u8,")
    out.append("        bytes_len: 0,")
    out.append("        relocs_len: 0,")
    out.append("        buf: [0u8; 32],")
    out.append("    };")
    out.append("    let mut fail: i64 = 0i64;")
    for i, (asm, call, exp) in enumerate(VECTORS):
        bs = ", ".join("0x%su8" % b for b in exp.split())
        n = len(exp.split())
        out.append("    // " + asm)
        out.append("    " + call + ";")
        out.append("    let e%d: [%d]u8 = [%s];" % (i, n, bs))
        out.append("    fail = fail + chk(mut_view(sec), %di64, view(e%d));" % (i, i))
    out.append("    if fail != 0i64 {")
    out.append("        return 1;")
    out.append("    }")
    out.append('    print("OK encode_int128 %d\\n");' % len(VECTORS))
    out.append("    0")
    out.append("}")
    return "\n".join(out) + "\n"


def main():
    if len(sys.argv) < 4:
        print("usage: encode_int128.py <compiler> <root> <tmp>", file=sys.stderr)
        return 2
    compiler, root, tmp = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
    os.makedirs(tmp, exist_ok=True)
    work = tempfile.mkdtemp(prefix="enc128_", dir=tmp)
    status, errs = gnu_check(work)
    for e in errs:
        print(e)
    if errs:
        return 1
    prog = os.path.join(work, "encode_int128_main.ax")
    with open(prog, "w", encoding="utf-8", newline="\n") as f:
        f.write(build_program(root))
    std_root = os.path.join(root, "std")
    want = "OK encode_int128 %d\n" % len(VECTORS)
    r = subprocess.run([compiler, "run", "--interp", "--std-root", std_root, prog], capture_output=True)
    out = r.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
    if r.returncode != 0 or out != want:
        print("interp: rc=%d stdout=%r stderr=%s" % (r.returncode, out, r.stderr.decode("utf-8", "replace")[:2000]))
        return 1
    for opt in ("-O0", "-O1"):
        exe = os.path.join(work, "enc128%s.exe" % opt)
        r = subprocess.run([compiler, "build", opt, "--std-root", std_root, prog, "-o", exe], capture_output=True)
        if r.returncode != 0:
            print("build %s failed: %s" % (opt, r.stderr.decode("utf-8", "replace")[:2000]))
            return 1
        r = subprocess.run([exe], capture_output=True)
        out = r.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
        if r.returncode != 0 or out != want:
            print("native %s: rc=%d stdout=%r" % (opt, r.returncode, out))
            return 1
    print("ENCODE-INT128 PASS %d gnu_as=%s" % (len(VECTORS), status))
    return 0


if __name__ == "__main__":
    sys.exit(main())
