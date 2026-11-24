#!/usr/bin/env python3
"""T459: byte-exact encoding check for the SSE2 scalar floating-point and x87 remainder forms of
`compiler/target/x64/encode.ax` (MOVSS/MOVSD, MOVD/MOVQ, ADD/SUB/MUL/DIV/SQRT SS/SD, UCOMISS/UCOMISD,
CVTSI2SS/SD, CVTTSS2SI/CVTTSD2SI, CVTSS2SD/CVTSD2SS, XORPS/XORPD, ANDPS/ANDPD, FLD/FSTP/FPREM/FNSTSW and
the complete `%` remainder sequence `x64_emit_fprem_seq`). SPEC-41 AXS-FLT-042..044.

Usage (exec manifest): encode_sse2.py <compiler> <root> <tmp>

1. Every vector's expected bytes were produced by GNU `as` (+ `objcopy -O binary`). The table is
   re-assembled on every run and compared (vector table drift is a failure; GNU as is required).
2. A program embedding the *live* `compiler/target/x64/encode.ax` (plus the `compiler.obj.coff` stub of
   `coff_stub.ax.in`) calls each encoder and checks its bytes; it runs in --interp, native -O0 and native -O1.
Prints `ENCODE-SSE2 PASS <n>` on success.
"""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

# (AT&T assembly, Axiom encoder call, expected bytes)
VECTORS = [
    ('movss %xmm1,%xmm0', 'x64_movss_rr(mut_view(sec), AX_REG_XMM0, AX_REG_XMM1)', 'f3 0f 10 c1'),
    ('movsd %xmm15,%xmm8', 'x64_movsd_rr(mut_view(sec), AX_REG_XMM8, AX_REG_XMM15)', 'f2 45 0f 10 c7'),
    ('movss -8(%rbp),%xmm0', 'x64_movss_rm(mut_view(sec), AX_REG_XMM0, x64_mem_base_disp(AX_REG_RBP, -8))', 'f3 0f 10 45 f8'),
    ('movsd -16(%rbp),%xmm1', 'x64_movsd_rm(mut_view(sec), AX_REG_XMM1, x64_mem_base_disp(AX_REG_RBP, -16))', 'f2 0f 10 4d f0'),
    ('movsd 0x200(%rbp),%xmm9', 'x64_movsd_rm(mut_view(sec), AX_REG_XMM9, x64_mem_base_disp(AX_REG_RBP, 512))', 'f2 44 0f 10 8d 00 02 00 00'),
    ('movsd (%rsp),%xmm0', 'x64_movsd_rm(mut_view(sec), AX_REG_XMM0, x64_mem_base(AX_REG_RSP))', 'f2 0f 10 04 24'),
    ('movsd 8(%r12),%xmm3', 'x64_movsd_rm(mut_view(sec), AX_REG_XMM3, x64_mem_base_disp(AX_REG_R12, 8))', 'f2 41 0f 10 5c 24 08'),
    ('movss 0(%r13),%xmm12', 'x64_movss_rm(mut_view(sec), AX_REG_XMM12, x64_mem_base(AX_REG_R13))', 'f3 45 0f 10 65 00'),
    ('movss %xmm0,-4(%rbp)', 'x64_movss_mr(mut_view(sec), x64_mem_base_disp(AX_REG_RBP, -4), AX_REG_XMM0)', 'f3 0f 11 45 fc'),
    ('movsd %xmm1,8(%rsp)', 'x64_movsd_mr(mut_view(sec), x64_mem_base_disp(AX_REG_RSP, 8), AX_REG_XMM1)', 'f2 0f 11 4c 24 08'),
    ('movsd %xmm14,(%rax)', 'x64_movsd_mr(mut_view(sec), x64_mem_base(AX_REG_RAX), AX_REG_XMM14)', 'f2 44 0f 11 30'),
    ('movd %eax,%xmm0', 'x64_movd_xr(mut_view(sec), AX_REG_XMM0, AX_REG_RAX)', '66 0f 6e c0'),
    ('movd %r9d,%xmm10', 'x64_movd_xr(mut_view(sec), AX_REG_XMM10, AX_REG_R9)', '66 45 0f 6e d1'),
    ('movd %xmm0,%eax', 'x64_movd_rx(mut_view(sec), AX_REG_RAX, AX_REG_XMM0)', '66 0f 7e c0'),
    ('movd %xmm11,%ecx', 'x64_movd_rx(mut_view(sec), AX_REG_RCX, AX_REG_XMM11)', '66 44 0f 7e d9'),
    ('movq %rax,%xmm0', 'x64_movq_xr(mut_view(sec), AX_REG_XMM0, AX_REG_RAX)', '66 48 0f 6e c0'),
    ('movq %r15,%xmm1', 'x64_movq_xr(mut_view(sec), AX_REG_XMM1, AX_REG_R15)', '66 49 0f 6e cf'),
    ('movq %rbx,%xmm13', 'x64_movq_xr(mut_view(sec), AX_REG_XMM13, AX_REG_RBX)', '66 4c 0f 6e eb'),
    ('movq %xmm0,%rax', 'x64_movq_rx(mut_view(sec), AX_REG_RAX, AX_REG_XMM0)', '66 48 0f 7e c0'),
    ('movq %xmm9,%r11', 'x64_movq_rx(mut_view(sec), AX_REG_R11, AX_REG_XMM9)', '66 4d 0f 7e cb'),
    ('addss %xmm1,%xmm0', 'x64_addss_rr(mut_view(sec), AX_REG_XMM0, AX_REG_XMM1)', 'f3 0f 58 c1'),
    ('addsd %xmm1,%xmm0', 'x64_addsd_rr(mut_view(sec), AX_REG_XMM0, AX_REG_XMM1)', 'f2 0f 58 c1'),
    ('addsd %xmm0,%xmm0', 'x64_addsd_rr(mut_view(sec), AX_REG_XMM0, AX_REG_XMM0)', 'f2 0f 58 c0'),
    ('addsd %xmm15,%xmm7', 'x64_addsd_rr(mut_view(sec), AX_REG_XMM7, AX_REG_XMM15)', 'f2 41 0f 58 ff'),
    ('addsd -24(%rbp),%xmm2', 'x64_addsd_rm(mut_view(sec), AX_REG_XMM2, x64_mem_base_disp(AX_REG_RBP, -24))', 'f2 0f 58 55 e8'),
    ('subss %xmm1,%xmm0', 'x64_subss_rr(mut_view(sec), AX_REG_XMM0, AX_REG_XMM1)', 'f3 0f 5c c1'),
    ('subsd %xmm8,%xmm2', 'x64_subsd_rr(mut_view(sec), AX_REG_XMM2, AX_REG_XMM8)', 'f2 41 0f 5c d0'),
    ('mulss %xmm1,%xmm0', 'x64_mulss_rr(mut_view(sec), AX_REG_XMM0, AX_REG_XMM1)', 'f3 0f 59 c1'),
    ('mulsd %xmm1,%xmm0', 'x64_mulsd_rr(mut_view(sec), AX_REG_XMM0, AX_REG_XMM1)', 'f2 0f 59 c1'),
    ('mulss 4(%rsp),%xmm6', 'x64_mulss_rm(mut_view(sec), AX_REG_XMM6, x64_mem_base_disp(AX_REG_RSP, 4))', 'f3 0f 59 74 24 04'),
    ('divss %xmm1,%xmm0', 'x64_divss_rr(mut_view(sec), AX_REG_XMM0, AX_REG_XMM1)', 'f3 0f 5e c1'),
    ('divsd %xmm12,%xmm11', 'x64_divsd_rr(mut_view(sec), AX_REG_XMM11, AX_REG_XMM12)', 'f2 45 0f 5e dc'),
    ('sqrtss %xmm0,%xmm0', 'x64_sqrtss_rr(mut_view(sec), AX_REG_XMM0, AX_REG_XMM0)', 'f3 0f 51 c0'),
    ('sqrtsd %xmm3,%xmm2', 'x64_sqrtsd_rr(mut_view(sec), AX_REG_XMM2, AX_REG_XMM3)', 'f2 0f 51 d3'),
    ('sqrtsd %xmm9,%xmm10', 'x64_sqrtsd_rr(mut_view(sec), AX_REG_XMM10, AX_REG_XMM9)', 'f2 45 0f 51 d1'),
    ('ucomiss %xmm1,%xmm0', 'x64_ucomiss_rr(mut_view(sec), AX_REG_XMM0, AX_REG_XMM1)', '0f 2e c1'),
    ('ucomisd %xmm1,%xmm0', 'x64_ucomisd_rr(mut_view(sec), AX_REG_XMM0, AX_REG_XMM1)', '66 0f 2e c1'),
    ('ucomisd %xmm0,%xmm1', 'x64_ucomisd_rr(mut_view(sec), AX_REG_XMM1, AX_REG_XMM0)', '66 0f 2e c8'),
    ('ucomisd %xmm0,%xmm0', 'x64_ucomisd_rr(mut_view(sec), AX_REG_XMM0, AX_REG_XMM0)', '66 0f 2e c0'),
    ('ucomiss %xmm14,%xmm9', 'x64_ucomiss_rr(mut_view(sec), AX_REG_XMM9, AX_REG_XMM14)', '45 0f 2e ce'),
    ('ucomisd -8(%rbp),%xmm0', 'x64_ucomis_rm(mut_view(sec), 8u8, AX_REG_XMM0, x64_mem_base_disp(AX_REG_RBP, -8))', '66 0f 2e 45 f8'),
    ('cvtsi2ss %eax,%xmm0', 'x64_cvtsi2ss_rr(mut_view(sec), 4u8, AX_REG_XMM0, AX_REG_RAX)', 'f3 0f 2a c0'),
    ('cvtsi2ss %rax,%xmm0', 'x64_cvtsi2ss_rr(mut_view(sec), 8u8, AX_REG_XMM0, AX_REG_RAX)', 'f3 48 0f 2a c0'),
    ('cvtsi2sd %eax,%xmm0', 'x64_cvtsi2sd_rr(mut_view(sec), 4u8, AX_REG_XMM0, AX_REG_RAX)', 'f2 0f 2a c0'),
    ('cvtsi2sd %rax,%xmm0', 'x64_cvtsi2sd_rr(mut_view(sec), 8u8, AX_REG_XMM0, AX_REG_RAX)', 'f2 48 0f 2a c0'),
    ('cvtsi2sd %r8,%xmm0', 'x64_cvtsi2sd_rr(mut_view(sec), 8u8, AX_REG_XMM0, AX_REG_R8)', 'f2 49 0f 2a c0'),
    ('cvtsi2sd %r9,%xmm12', 'x64_cvtsi2sd_rr(mut_view(sec), 8u8, AX_REG_XMM12, AX_REG_R9)', 'f2 4d 0f 2a e1'),
    ('cvtsi2ss %rcx,%xmm15', 'x64_cvtsi2ss_rr(mut_view(sec), 8u8, AX_REG_XMM15, AX_REG_RCX)', 'f3 4c 0f 2a f9'),
    ('cvttss2si %xmm0,%eax', 'x64_cvttss2si_rr(mut_view(sec), 4u8, AX_REG_RAX, AX_REG_XMM0)', 'f3 0f 2c c0'),
    ('cvttss2si %xmm0,%rax', 'x64_cvttss2si_rr(mut_view(sec), 8u8, AX_REG_RAX, AX_REG_XMM0)', 'f3 48 0f 2c c0'),
    ('cvttsd2si %xmm0,%eax', 'x64_cvttsd2si_rr(mut_view(sec), 4u8, AX_REG_RAX, AX_REG_XMM0)', 'f2 0f 2c c0'),
    ('cvttsd2si %xmm0,%rax', 'x64_cvttsd2si_rr(mut_view(sec), 8u8, AX_REG_RAX, AX_REG_XMM0)', 'f2 48 0f 2c c0'),
    ('cvttsd2si %xmm2,%rcx', 'x64_cvttsd2si_rr(mut_view(sec), 8u8, AX_REG_RCX, AX_REG_XMM2)', 'f2 48 0f 2c ca'),
    ('cvttsd2si %xmm13,%r10', 'x64_cvttsd2si_rr(mut_view(sec), 8u8, AX_REG_R10, AX_REG_XMM13)', 'f2 4d 0f 2c d5'),
    ('cvttss2si %xmm8,%r14', 'x64_cvttss2si_rr(mut_view(sec), 8u8, AX_REG_R14, AX_REG_XMM8)', 'f3 4d 0f 2c f0'),
    ('cvtss2sd %xmm0,%xmm0', 'x64_cvtss2sd_rr(mut_view(sec), AX_REG_XMM0, AX_REG_XMM0)', 'f3 0f 5a c0'),
    ('cvtss2sd %xmm9,%xmm1', 'x64_cvtss2sd_rr(mut_view(sec), AX_REG_XMM1, AX_REG_XMM9)', 'f3 41 0f 5a c9'),
    ('cvtsd2ss %xmm0,%xmm0', 'x64_cvtsd2ss_rr(mut_view(sec), AX_REG_XMM0, AX_REG_XMM0)', 'f2 0f 5a c0'),
    ('cvtsd2ss %xmm2,%xmm11', 'x64_cvtsd2ss_rr(mut_view(sec), AX_REG_XMM11, AX_REG_XMM2)', 'f2 44 0f 5a da'),
    ('xorps %xmm1,%xmm0', 'x64_xorps_rr(mut_view(sec), AX_REG_XMM0, AX_REG_XMM1)', '0f 57 c1'),
    ('xorpd %xmm1,%xmm0', 'x64_xorpd_rr(mut_view(sec), AX_REG_XMM0, AX_REG_XMM1)', '66 0f 57 c1'),
    ('xorps %xmm3,%xmm3', 'x64_xorps_rr(mut_view(sec), AX_REG_XMM3, AX_REG_XMM3)', '0f 57 db'),
    ('xorpd %xmm10,%xmm2', 'x64_xorpd_rr(mut_view(sec), AX_REG_XMM2, AX_REG_XMM10)', '66 41 0f 57 d2'),
    ('xorpd 0x10(%rip),%xmm0', 'x64_fxor_rm(mut_view(sec), 8u8, AX_REG_XMM0, x64_mem_rip(16))', '66 0f 57 05 10 00 00 00'),
    ('andps %xmm1,%xmm0', 'x64_andps_rr(mut_view(sec), AX_REG_XMM0, AX_REG_XMM1)', '0f 54 c1'),
    ('andpd %xmm1,%xmm0', 'x64_andpd_rr(mut_view(sec), AX_REG_XMM0, AX_REG_XMM1)', '66 0f 54 c1'),
    ('andpd %xmm15,%xmm15', 'x64_andpd_rr(mut_view(sec), AX_REG_XMM15, AX_REG_XMM15)', '66 45 0f 54 ff'),
    ('andps -32(%rbp),%xmm4', 'x64_fand_rm(mut_view(sec), 4u8, AX_REG_XMM4, x64_mem_base_disp(AX_REG_RBP, -32))', '0f 54 65 e0'),
    ('flds (%rsp)', 'x64_fld_m(mut_view(sec), 4u8, x64_mem_base(AX_REG_RSP))', 'd9 04 24'),
    ('fldl 8(%rsp)', 'x64_fld_m(mut_view(sec), 8u8, x64_mem_base_disp(AX_REG_RSP, 8))', 'dd 44 24 08'),
    ('fldl -8(%rbp)', 'x64_fld_m(mut_view(sec), 8u8, x64_mem_base_disp(AX_REG_RBP, -8))', 'dd 45 f8'),
    ('fstps (%rsp)', 'x64_fstp_m(mut_view(sec), 4u8, x64_mem_base(AX_REG_RSP))', 'd9 1c 24'),
    ('fstpl (%rsp)', 'x64_fstp_m(mut_view(sec), 8u8, x64_mem_base(AX_REG_RSP))', 'dd 1c 24'),
    ('fstpl 0x10(%r8)', 'x64_fstp_m(mut_view(sec), 8u8, x64_mem_base_disp(AX_REG_R8, 16))', '41 dd 58 10'),
    ('fprem', 'x64_fprem(mut_view(sec))', 'd9 f8'),
    ('fnstsw %ax', 'x64_fnstsw_ax(mut_view(sec))', 'df e0'),
    ('fstp %st(0)', 'x64_fstp_st0(mut_view(sec))', 'dd d8'),
    ('movsd %xmm1,8(%rsp); fldl 8(%rsp); movsd %xmm0,(%rsp); fldl (%rsp); 1: fprem; fnstsw %ax; test $0x400,%eax; jne 1b; fstpl (%rsp); fstp %st(0); movsd (%rsp),%xmm0', 'x64_emit_fprem_seq(mut_view(sec), 8u8)', 'f2 0f 11 4c 24 08 dd 44 24 08 f2 0f 11 04 24 dd 04 24 d9 f8 df e0 a9 00 04 00 00 75 f5 dd 1c 24 dd d8 f2 0f 10 04 24'),
    ('movss %xmm1,8(%rsp); flds 8(%rsp); movss %xmm0,(%rsp); flds (%rsp); 1: fprem; fnstsw %ax; test $0x400,%eax; jne 1b; fstps (%rsp); fstp %st(0); movss (%rsp),%xmm0', 'x64_emit_fprem_seq(mut_view(sec), 4u8)', 'f3 0f 11 4c 24 08 d9 44 24 08 f3 0f 11 04 24 d9 04 24 d9 f8 df e0 a9 00 04 00 00 75 f5 d9 1c 24 dd d8 f3 0f 10 04 24'),
    ('push %rbp; mov %rsp,%rbp; push %rbx; sub $0x40,%rsp; movaps %xmm6,-0x20(%rbp); movaps %xmm15,-0x30(%rbp)', 'x64_emit_prologue_masked(mut_view(sec), 64u32, 0x80400008u32, -32)', '55 48 89 e5 53 48 83 ec 40 0f 29 75 e0 44 0f 29 7d d0'),
    ('movaps -0x20(%rbp),%xmm6; movaps -0x30(%rbp),%xmm15; add $0x40,%rsp; pop %rbx; pop %rbp', 'x64_emit_epilogue_masked(mut_view(sec), 64u32, 0x80400008u32, -32)', '0f 28 75 e0 44 0f 28 7d d0 48 83 c4 40 5b 5d'),
    ('push %rbp; mov %rsp,%rbp; sub $0x60,%rsp; movaps %xmm7,-0x10(%rbp); movaps %xmm8,-0x20(%rbp); movaps %xmm9,-0x30(%rbp)', 'x64_emit_prologue_masked(mut_view(sec), 96u32, 0x03800000u32, -16)', '55 48 89 e5 48 83 ec 60 0f 29 7d f0 44 0f 29 45 e0 44 0f 29 4d d0'),
    ('movaps -0x10(%rbp),%xmm7; movaps -0x20(%rbp),%xmm8; movaps -0x30(%rbp),%xmm9; add $0x60,%rsp; pop %rbp', 'x64_emit_epilogue_masked(mut_view(sec), 96u32, 0x03800000u32, -16)', '0f 28 7d f0 44 0f 28 45 e0 44 0f 28 4d d0 48 83 c4 60 5d'),
]

IMPORTS = [
    "x64_emit_prologue_masked",
    "x64_emit_epilogue_masked",
    "AX_REG_R10",
    "AX_REG_R11",
    "AX_REG_R12",
    "AX_REG_R13",
    "AX_REG_R14",
    "AX_REG_R15",
    "AX_REG_R8",
    "AX_REG_R9",
    "AX_REG_RAX",
    "AX_REG_RBP",
    "AX_REG_RBX",
    "AX_REG_RCX",
    "AX_REG_RSP",
    "AX_REG_XMM0",
    "AX_REG_XMM1",
    "AX_REG_XMM10",
    "AX_REG_XMM11",
    "AX_REG_XMM12",
    "AX_REG_XMM13",
    "AX_REG_XMM14",
    "AX_REG_XMM15",
    "AX_REG_XMM2",
    "AX_REG_XMM3",
    "AX_REG_XMM4",
    "AX_REG_XMM6",
    "AX_REG_XMM7",
    "AX_REG_XMM8",
    "AX_REG_XMM9",
    "x64_addsd_rm",
    "x64_addsd_rr",
    "x64_addss_rr",
    "x64_andpd_rr",
    "x64_andps_rr",
    "x64_cvtsd2ss_rr",
    "x64_cvtsi2sd_rr",
    "x64_cvtsi2ss_rr",
    "x64_cvtss2sd_rr",
    "x64_cvttsd2si_rr",
    "x64_cvttss2si_rr",
    "x64_divsd_rr",
    "x64_divss_rr",
    "x64_emit_fprem_seq",
    "x64_fand_rm",
    "x64_fld_m",
    "x64_fnstsw_ax",
    "x64_fprem",
    "x64_fstp_m",
    "x64_fstp_st0",
    "x64_fxor_rm",
    "x64_mem_base",
    "x64_mem_base_disp",
    "x64_mem_rip",
    "x64_movd_rx",
    "x64_movd_xr",
    "x64_movq_rx",
    "x64_movq_xr",
    "x64_movsd_mr",
    "x64_movsd_rm",
    "x64_movsd_rr",
    "x64_movss_mr",
    "x64_movss_rm",
    "x64_movss_rr",
    "x64_mulsd_rr",
    "x64_mulss_rm",
    "x64_mulss_rr",
    "x64_sqrtsd_rr",
    "x64_sqrtss_rr",
    "x64_subsd_rr",
    "x64_subss_rr",
    "x64_ucomis_rm",
    "x64_ucomisd_rr",
    "x64_ucomiss_rr",
    "x64_xorpd_rr",
    "x64_xorps_rr",
]


def gnu_check(tmp):
    as_exe = shutil.which("as")
    oc_exe = shutil.which("objcopy")
    if not as_exe or not oc_exe:
        return "error", ["GNU as / objcopy not on PATH (they are the oracle of this test)"]
    errs = []
    for i, (asm, _, exp) in enumerate(VECTORS):
        src = os.path.join(tmp, "v%d.s" % i)
        obj = os.path.join(tmp, "v%d.o" % i)
        binf = os.path.join(tmp, "v%d.bin" % i)
        with open(src, "w", encoding="utf-8", newline="\n") as f:
            f.write(".text\n" + asm.replace("; ", "\n") + "\n")
        r = subprocess.run([as_exe, "--64", "-o", obj, src], capture_output=True, text=True)
        if r.returncode != 0:
            return "error", ["GNU as failed on `%s`: %s" % (asm, r.stderr.strip())]
        r = subprocess.run([oc_exe, "-O", "binary", "-j", ".text", obj, binf], capture_output=True, text=True)
        if r.returncode != 0:
            return "error", ["objcopy failed: " + r.stderr.strip()]
        with open(binf, "rb") as f:
            got = f.read()
        # COFF pads .text to its alignment with NOPs; every vector here ends with a non-NOP byte.
        got = got.rstrip(b"\x90")
        g = " ".join("%02x" % b for b in got)
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
    out.append("        buf: [0u8; 64],")
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
    out.append('    print("OK encode_sse2 %d\\n");' % len(VECTORS))
    out.append("    0")
    out.append("}")
    return "\n".join(out) + "\n"


def main():
    if len(sys.argv) < 4:
        print("usage: encode_sse2.py <compiler> <root> <tmp>", file=sys.stderr)
        return 2
    compiler, root, tmp = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
    os.makedirs(tmp, exist_ok=True)
    work = tempfile.mkdtemp(prefix="encsse2_", dir=tmp)
    status, errs = gnu_check(work)
    for e in errs:
        print(e)
    if errs:
        return 1
    prog = os.path.join(work, "encode_sse2_main.ax")
    with open(prog, "w", encoding="utf-8", newline="\n") as f:
        f.write(build_program(root))
    std_root = os.path.join(root, "std")
    want = "OK encode_sse2 %d\n" % len(VECTORS)
    r = subprocess.run([compiler, "run", "--interp", "--std-root", std_root, prog], capture_output=True)
    out = r.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
    if r.returncode != 0 or out != want:
        print("interp: rc=%d stdout=%r stderr=%s" % (r.returncode, out, r.stderr.decode("utf-8", "replace")[:2000]))
        return 1
    for opt in ("-O0", "-O1"):
        exe = os.path.join(work, "encsse2%s.exe" % opt)
        r = subprocess.run([compiler, "build", opt, "--std-root", std_root, prog, "-o", exe], capture_output=True)
        if r.returncode != 0:
            print("build %s failed: %s" % (opt, r.stderr.decode("utf-8", "replace")[:2000]))
            return 1
        r = subprocess.run([exe], capture_output=True)
        out = r.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
        if r.returncode != 0 or out != want:
            print("native %s: rc=%d stdout=%r" % (opt, r.returncode, out))
            return 1
    print("ENCODE-SSE2 PASS %d gnu_as=%s" % (len(VECTORS), status))
    return 0


if __name__ == "__main__":
    sys.exit(main())
