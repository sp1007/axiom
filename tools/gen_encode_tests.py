#!/usr/bin/env python3
"""Generate and verify x86-64 machine-code encoding oracle tables against GNU as.

Deliverables (T143 / ADR-0034 OI-08):
  1. tests/encode/encode_tests.inc       — C vector table included by tests/encode/cdriver_encode.c
  2. tests/encode/axiom/gnu_as_vectors.ax — Self-contained Axiom twin embedding
     compiler/target/x64/encode.ax verbatim and checking every vector in interp + native modes.

Usage:
  python tools/gen_encode_tests.py         # regenerate both tables using GNU as + objdump
  python tools/gen_encode_tests.py check   # verify committed tables & embedded encode.ax are current
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INC_PATH = os.path.join(ROOT, "tests", "encode", "encode_tests.inc")
AX_VEC_PATH = os.path.join(ROOT, "tests", "encode", "axiom", "gnu_as_vectors.ax")
ENCODE_AX_PATH = os.path.join(ROOT, "compiler", "target", "x64", "encode.ax")

EMBED_BEGIN_MARKER = "// === BEGIN VERBATIM compiler/target/x64/encode.ax ==="
EMBED_END_MARKER = "// === END VERBATIM compiler/target/x64/encode.ax ==="

REG_NAMES = [
    "RAX", "RCX", "RDX", "RBX", "RSP", "RBP", "RSI", "RDI",
    "R8", "R9", "R10", "R11", "R12", "R13", "R14", "R15",
]

REGS_ASM = {
    1: [
        "%al", "%cl", "%dl", "%bl", "%spl", "%bpl", "%sil", "%dil",
        "%r8b", "%r9b", "%r10b", "%r11b", "%r12b", "%r13b", "%r14b", "%r15b",
    ],
    2: [
        "%ax", "%cx", "%dx", "%bx", "%sp", "%bp", "%si", "%di",
        "%r8w", "%r9w", "%r10w", "%r11w", "%r12w", "%r13w", "%r14w", "%r15w",
    ],
    4: [
        "%eax", "%ecx", "%edx", "%ebx", "%esp", "%ebp", "%esi", "%edi",
        "%r8d", "%r9d", "%r10d", "%r11d", "%r12d", "%r13d", "%r14d", "%r15d",
    ],
    8: [
        "%rax", "%rcx", "%rdx", "%rbx", "%rsp", "%rbp", "%rsi", "%rdi",
        "%r8", "%r9", "%r10", "%r11", "%r12", "%r13", "%r14", "%r15",
    ],
}

SZ_SUFFIX = {1: "b", 2: "w", 4: "l", 8: "q"}

CC_LIST = [
    (0x0, "O", "o"),
    (0x1, "NO", "no"),
    (0x2, "B", "b"),
    (0x3, "AE", "ae"),
    (0x4, "E", "e"),
    (0x5, "NE", "ne"),
    (0x6, "BE", "be"),
    (0x7, "A", "a"),
    (0x8, "S", "s"),
    (0x9, "NS", "ns"),
    (0xA, "P", "p"),
    (0xB, "NP", "np"),
    (0xC, "L", "l"),
    (0xD, "GE", "ge"),
    (0xE, "LE", "le"),
    (0xF, "G", "g"),
]


def c_reg(reg_id: int) -> str:
    return f"AX_REG_{REG_NAMES[reg_id]}"


def ax_reg(reg_id: int) -> str:
    return f"AX_REG_{REG_NAMES[reg_id]}"


def c_i32(val: int) -> str:
    if val == -2147483648:
        return "(-2147483647 - 1)"
    return str(val)


def c_i64(val: int) -> str:
    if val == -9223372036854775808:
        return "(-9223372036854775807LL - 1LL)"
    if val < -2147483648 or val > 2147483647:
        return f"{val}LL"
    return str(val)


def ax_i32(val: int) -> str:
    if val == -2147483648:
        return "(-2147483647 - 1)"
    return str(val)


def ax_i8(val: int) -> str:
    return f"({val} as i8)"


def ax_i64(val: int) -> str:
    if val == -9223372036854775808:
        return "(-9223372036854775807i64 - 1i64)"
    return f"{val}i64"


# Memory operand specification:
# (ctor_kind, base, index, scale, disp, is_rip)
# ctor_kind in {"base", "base_disp", "index", "index_disp", "rip"}
MEM_SPECS = [
    # 1. Base only (ax_x64_mem_base / x64_mem_base) — incl. rsp/r12 and rbp/r13
    ("base", 0, -1, 1, 0, False),    # 0: (%rax)
    ("base", 4, -1, 1, 0, False),    # 1: (%rsp) - SIB 0x24
    ("base", 5, -1, 1, 0, False),    # 2: (%rbp) - disp8=0
    ("base", 8, -1, 1, 0, False),    # 3: (%r8)  - REX.B
    ("base", 12, -1, 1, 0, False),   # 4: (%r12) - REX.B + SIB 0x24
    ("base", 13, -1, 1, 0, False),   # 5: (%r13) - REX.B + disp8=0
    ("base", 15, -1, 1, 0, False),   # 6: (%r15) - REX.B
    # 2. Base + disp8 (ax_x64_mem_base_disp / x64_mem_base_disp)
    ("base_disp", 0, -1, 1, 0, False),       # 7: 0(%rax) -> mod=0
    ("base_disp", 0, -1, 1, 127, False),     # 8: 127(%rax)
    ("base_disp", 0, -1, 1, -128, False),    # 9: -128(%rax)
    ("base_disp", 4, -1, 1, -8, False),      # 10: -8(%rsp)
    ("base_disp", 5, -1, 1, 127, False),     # 11: 127(%rbp)
    ("base_disp", 12, -1, 1, -128, False),   # 12: -128(%r12)
    ("base_disp", 13, -1, 1, 8, False),      # 13: 8(%r13)
    # 3. Base + disp32 (ax_x64_mem_base_disp / x64_mem_base_disp)
    ("base_disp", 0, -1, 1, 128, False),          # 14: 128(%rax)
    ("base_disp", 0, -1, 1, -129, False),         # 15: -129(%rax)
    ("base_disp", 4, -1, 1, -129, False),         # 16: -129(%rsp)
    ("base_disp", 5, -1, 1, 2147483647, False),   # 17: 2147483647(%rbp)
    ("base_disp", 12, -1, 1, -2147483648, False), # 18: -2147483648(%r12)
    ("base_disp", 13, -1, 1, 128, False),         # 19: 128(%r13)
    # 4. SIB no-disp (ax_x64_mem_index / x64_mem_index) — scales 1, 2, 4, 8
    ("index", 0, 1, 1, 0, False),    # 20: (%rax,%rcx,1)
    ("index", 0, 1, 2, 0, False),    # 21: (%rax,%rcx,2)
    ("index", 0, 1, 4, 0, False),    # 22: (%rax,%rcx,4)
    ("index", 0, 1, 8, 0, False),    # 23: (%rax,%rcx,8)
    ("index", 4, 0, 1, 0, False),    # 24: (%rsp,%rax,1)
    ("index", 5, 1, 2, 0, False),    # 25: (%rbp,%rcx,2)
    ("index", 12, 8, 4, 0, False),   # 26: (%r12,%r8,4)
    ("index", 13, 15, 8, 0, False),  # 27: (%r13,%r15,8)
    # 5. SIB + disp8 / disp32 (ax_x64_mem_index_disp / x64_mem_index_disp)
    ("index_disp", 0, 1, 4, 127, False),          # 28: 127(%rax,%rcx,4)
    ("index_disp", 4, 8, 2, -128, False),         # 29: -128(%rsp,%r8,2)
    ("index_disp", 5, 9, 8, 16, False),           # 30: 16(%rbp,%r9,8)
    ("index_disp", 12, 15, 1, 128, False),        # 31: 128(%r12,%r15,1)
    ("index_disp", 13, 14, 8, -129, False),       # 32: -129(%r13,%r14,8)
    # 6. RIP-relative (ax_x64_mem_rip / x64_mem_rip)
    ("rip", -1, -1, 1, 0, True),            # 33: 0(%rip)
    ("rip", -1, -1, 1, 127, True),          # 34: 127(%rip)
    ("rip", -1, -1, 1, -128, True),         # 35: -128(%rip)
    ("rip", -1, -1, 1, 128, True),          # 36: 128(%rip)
    ("rip", -1, -1, 1, -129, True),         # 37: -129(%rip)
    ("rip", -1, -1, 1, 2147483647, True),   # 38: 2147483647(%rip)
    ("rip", -1, -1, 1, -2147483648, True),  # 39: -2147483648(%rip)
]

# Core 12 memory modes covering all 5 constructors, all 4 SIB scales (1,2,4,8),
# rsp/r12 base, rbp/r13 base, disp8 (-128, 127), disp32 (128, -129, 2^31-1, -2^31), and rip-relative
MEM_CORE = [
    MEM_SPECS[0],   # (%rax)
    MEM_SPECS[1],   # (%rsp)
    MEM_SPECS[2],   # (%rbp)
    MEM_SPECS[4],   # (%r12)
    MEM_SPECS[5],   # (%r13)
    MEM_SPECS[8],   # 127(%rax)
    MEM_SPECS[9],   # -128(%rax)
    MEM_SPECS[17],  # 2147483647(%rbp)
    MEM_SPECS[18],  # -2147483648(%r12)
    MEM_SPECS[20],  # (%rax,%rcx,1)
    MEM_SPECS[21],  # (%rax,%rcx,2)
    MEM_SPECS[26],  # (%r12,%r8,4)
    MEM_SPECS[32],  # -129(%r13,%r14,8)
    MEM_SPECS[34],  # 127(%rip)
]


def mem_asm(m) -> str:
    _, base, index, scale, disp, is_rip = m
    if is_rip:
        return f"{disp}(%rip)"
    b_s = REGS_ASM[8][base]
    if index == -1:
        if disp == 0:
            return f"({b_s})"
        return f"{disp}({b_s})"
    i_s = REGS_ASM[8][index]
    if disp == 0:
        return f"({b_s},{i_s},{scale})"
    return f"{disp}({b_s},{i_s},{scale})"


def mem_c(m) -> str:
    kind, base, index, scale, disp, _ = m
    if kind == "base":
        return f"ax_x64_mem_base({c_reg(base)})"
    if kind == "base_disp":
        return f"ax_x64_mem_base_disp({c_reg(base)}, {c_i32(disp)})"
    if kind == "index":
        return f"ax_x64_mem_index({c_reg(base)}, {c_reg(index)}, {scale})"
    if kind == "index_disp":
        return f"ax_x64_mem_index_disp({c_reg(base)}, {c_reg(index)}, {scale}, {c_i32(disp)})"
    if kind == "rip":
        return f"ax_x64_mem_rip({c_i32(disp)})"
    raise ValueError(f"unknown mem kind: {kind}")


def mem_ax(m) -> str:
    kind, base, index, scale, disp, _ = m
    if kind == "base":
        return f"x64_mem_base({ax_reg(base)})"
    if kind == "base_disp":
        return f"x64_mem_base_disp({ax_reg(base)}, {ax_i32(disp)})"
    if kind == "index":
        return f"x64_mem_index({ax_reg(base)}, {ax_reg(index)}, {scale}u8)"
    if kind == "index_disp":
        return f"x64_mem_index_disp({ax_reg(base)}, {ax_reg(index)}, {scale}u8, {ax_i32(disp)})"
    if kind == "rip":
        return f"x64_mem_rip({ax_i32(disp)})"
    raise ValueError(f"unknown mem kind: {kind}")


# Reference simulation of encode.c / encode.ax to identify known xfail vectors
def u16_le(v: int) -> list[int]:
    v &= 0xFFFF
    return [v & 0xFF, (v >> 8) & 0xFF]


def u32_le(v: int) -> list[int]:
    v &= 0xFFFFFFFF
    return [(v >> (8 * i)) & 0xFF for i in range(4)]


def u64_le(v: int) -> list[int]:
    v &= 0xFFFFFFFFFFFFFFFF
    return [(v >> (8 * i)) & 0xFF for i in range(8)]


def sim_sz(sz: int) -> list[int]:
    return [0x66] if sz == 2 else []


def sim_rex_rr(sz: int, reg: int, rm: int) -> list[int]:
    w = sz == 8
    r = reg != -1 and reg >= 8
    b = rm != -1 and rm >= 8
    force = sz == 1 and ((reg != -1 and reg >= 4) or (rm != -1 and rm >= 4))
    if w or r or b or force:
        return [0x40 | (8 if w else 0) | (4 if r else 0) | (1 if b else 0)]
    return []


def sim_rex_rm(sz: int, reg: int, m) -> list[int]:
    _, base, index, _, _, _ = m
    w = sz == 8
    r = reg != -1 and reg >= 8
    x = index != -1 and index >= 8
    b = base != -1 and base >= 8
    force = sz == 1 and (reg != -1 and reg >= 4)
    if w or r or x or b or force:
        return [0x40 | (8 if w else 0) | (4 if r else 0) | (2 if x else 0) | (1 if b else 0)]
    return []


def sim_mem_op(reg_op: int, m) -> list[int]:
    _, base, index, scale, disp, is_rip = m
    if is_rip:
        return [((reg_op & 7) << 3) | 5] + u32_le(disp)
    has_sib = (index != -1) or ((base & 7) == 4)
    if disp == 0 and (base & 7) != 5:
        mod = 0
    elif -128 <= disp <= 127:
        mod = 1
    else:
        mod = 2
    rm = 4 if has_sib else (base & 7)
    out = [((mod & 3) << 6) | ((reg_op & 7) << 3) | (rm & 7)]
    if has_sib:
        ss = {1: 0, 2: 1, 4: 2, 8: 3}[scale]
        idx_bits = 4 if index == -1 else (index & 7)
        out.append(((ss & 3) << 6) | (idx_bits << 3) | (base & 7))
    if mod == 1:
        out.append(disp & 0xFF)
    elif mod == 2:
        out.extend(u32_le(disp))
    return out


def sim_alu_ri(sz: int, ext: int, dst: int, imm: int) -> list[int]:
    out = sim_sz(sz) + sim_rex_rr(sz, -1, dst)
    if sz == 1:
        if dst == 0:
            out.extend([(ext << 3) | 4, imm & 0xFF])
        else:
            out.extend([0x80, 0xC0 | (ext << 3) | (dst & 7), imm & 0xFF])
    else:
        if dst == 0:
            out.append((ext << 3) | 5)
            out.extend(u16_le(imm) if sz == 2 else u32_le(imm))
        elif -128 <= imm <= 127:
            out.extend([0x83, 0xC0 | (ext << 3) | (dst & 7), imm & 0xFF])
        else:
            out.extend([0x81, 0xC0 | (ext << 3) | (dst & 7)])
            out.extend(u16_le(imm) if sz == 2 else u32_le(imm))
    return out


def rr_pairs_compact() -> list[tuple[int, int]]:
    """Covers every register 0..15 as dst and every register 0..15 as src,
    including low (0..3), spl..dil (4..7), and high r8..r15 (8..15) combinations."""
    seen = set()
    pairs = []
    # Bijection (dst, (dst * 5 + 4) & 15) covers all 16 dsts and all 16 srcs
    for dst in range(16):
        src = (dst * 5 + 4) & 15
        seen.add((dst, src))
        pairs.append((dst, src))
    # Explicit low/byte-rex/high cross pairs
    for dst in [0, 4, 8, 15]:
        for src in [0, 4, 5, 6, 7, 8, 12, 15]:
            if (dst, src) not in seen:
                seen.add((dst, src))
                pairs.append((dst, src))
    return pairs


class Vector:
    __slots__ = ("entry", "asm", "c_stmt", "ax_stmt", "reset_relocs", "xfail_task", "xfail_enc")

    def __init__(
        self,
        entry: str,
        asm: str,
        c_stmt: str,
        ax_stmt: str,
        reset_relocs: bool = False,
        xfail_task: str | None = None,
        xfail_enc: list[int] | None = None,
    ):
        self.entry = entry
        self.asm = asm
        self.c_stmt = c_stmt
        self.ax_stmt = ax_stmt
        self.reset_relocs = reset_relocs
        self.xfail_task = xfail_task
        self.xfail_enc = xfail_enc


def build_vectors() -> list[Vector]:
    vecs: list[Vector] = []
    pairs = rr_pairs_compact()

    # 1. mov_rr (all widths 1, 2, 4, 8 x register pairs covering 0..15 in both positions)
    for sz in [1, 2, 4, 8]:
        suf = SZ_SUFFIX[sz]
        for dst, src in pairs:
            vecs.append(Vector(
                "ax_x64_mov_rr",
                f"mov{suf} {REGS_ASM[sz][src]}, {REGS_ASM[sz][dst]}",
                f"ax_x64_mov_rr(&sec, {sz}, {c_reg(dst)}, {c_reg(src)});",
                f"x64_mov_rr(mut_view(*sec), {sz}u8, {ax_reg(dst)}, {ax_reg(src)});",
            ))

    # 2. mov_rm & 3. mov_mr (all widths 1, 2, 4, 8; full MEM_SPECS + all 16 regs)
    for sz in [1, 2, 4, 8]:
        suf = SZ_SUFFIX[sz]
        for reg in [0, 4, 12]:
            for m in MEM_SPECS:
                vecs.append(Vector(
                    "ax_x64_mov_rm",
                    f"mov{suf} {mem_asm(m)}, {REGS_ASM[sz][reg]}",
                    f"ax_x64_mov_rm(&sec, {sz}, {c_reg(reg)}, {mem_c(m)});",
                    f"x64_mov_rm(mut_view(*sec), {sz}u8, {ax_reg(reg)}, {mem_ax(m)});",
                ))
                vecs.append(Vector(
                    "ax_x64_mov_mr",
                    f"mov{suf} {REGS_ASM[sz][reg]}, {mem_asm(m)}",
                    f"ax_x64_mov_mr(&sec, {sz}, {mem_c(m)}, {c_reg(reg)});",
                    f"x64_mov_mr(mut_view(*sec), {sz}u8, {mem_ax(m)}, {ax_reg(reg)});",
                ))
        for reg in range(16):
            for m in [MEM_SPECS[0], MEM_SPECS[1], MEM_SPECS[33]]:
                vecs.append(Vector(
                    "ax_x64_mov_rm",
                    f"mov{suf} {mem_asm(m)}, {REGS_ASM[sz][reg]}",
                    f"ax_x64_mov_rm(&sec, {sz}, {c_reg(reg)}, {mem_c(m)});",
                    f"x64_mov_rm(mut_view(*sec), {sz}u8, {ax_reg(reg)}, {mem_ax(m)});",
                ))
                vecs.append(Vector(
                    "ax_x64_mov_mr",
                    f"mov{suf} {REGS_ASM[sz][reg]}, {mem_asm(m)}",
                    f"ax_x64_mov_mr(&sec, {sz}, {mem_c(m)}, {c_reg(reg)});",
                    f"x64_mov_mr(mut_view(*sec), {sz}u8, {mem_ax(m)}, {ax_reg(reg)});",
                ))

    # 4. mov_ri (all widths 1, 2, 4, 8 x all 16 regs x immediate boundaries incl. 64-bit movabs)
    for reg in range(16):
        for imm in [0, 127, -128]:
            vecs.append(Vector(
                "ax_x64_mov_ri",
                f"movb ${imm}, {REGS_ASM[1][reg]}",
                f"ax_x64_mov_ri(&sec, 1, {c_reg(reg)}, {c_i64(imm)});",
                f"x64_mov_ri(mut_view(*sec), 1u8, {ax_reg(reg)}, {ax_i64(imm)});",
            ))
        for imm in [0, 127, 128, -128, -129, 32767, -32768]:
            vecs.append(Vector(
                "ax_x64_mov_ri",
                f"movw ${imm}, {REGS_ASM[2][reg]}",
                f"ax_x64_mov_ri(&sec, 2, {c_reg(reg)}, {c_i64(imm)});",
                f"x64_mov_ri(mut_view(*sec), 2u8, {ax_reg(reg)}, {ax_i64(imm)});",
            ))
        for imm in [0, 127, 128, -128, -129, 2147483647, -2147483648]:
            vecs.append(Vector(
                "ax_x64_mov_ri",
                f"movl ${imm}, {REGS_ASM[4][reg]}",
                f"ax_x64_mov_ri(&sec, 4, {c_reg(reg)}, {c_i64(imm)});",
                f"x64_mov_ri(mut_view(*sec), 4u8, {ax_reg(reg)}, {ax_i64(imm)});",
            ))
        for imm in [
            0, 127, 128, -128, -129, 2147483647, -2147483648,
            0x0102030405060708, -0x0102030405060708, -9223372036854775808,
        ]:
            vecs.append(Vector(
                "ax_x64_mov_ri",
                f"movabsq ${imm}, {REGS_ASM[8][reg]}",
                f"ax_x64_mov_ri(&sec, 8, {c_reg(reg)}, {c_i64(imm)});",
                f"x64_mov_ri(mut_view(*sec), 8u8, {ax_reg(reg)}, {ax_i64(imm)});",
            ))

    # 5. mov_mi (widths 1, 2, 4, 8 x memory modes x immediate boundaries)
    for m in MEM_CORE[:8]:
        for imm in [0, 127, -128]:
            vecs.append(Vector(
                "ax_x64_mov_mi",
                f"movb ${imm}, {mem_asm(m)}",
                f"ax_x64_mov_mi(&sec, 1, {mem_c(m)}, {c_i32(imm)});",
                f"x64_mov_mi(mut_view(*sec), 1u8, {mem_ax(m)}, {ax_i32(imm)});",
            ))
        for imm in [0, 127, 128, -128, -129, 32767, -32768]:
            vecs.append(Vector(
                "ax_x64_mov_mi",
                f"movw ${imm}, {mem_asm(m)}",
                f"ax_x64_mov_mi(&sec, 2, {mem_c(m)}, {c_i32(imm)});",
                f"x64_mov_mi(mut_view(*sec), 2u8, {mem_ax(m)}, {ax_i32(imm)});",
            ))
        for sz in [4, 8]:
            suf = SZ_SUFFIX[sz]
            for imm in [0, 127, 128, -128, -129, 2147483647, -2147483648]:
                vecs.append(Vector(
                    "ax_x64_mov_mi",
                    f"mov{suf} ${imm}, {mem_asm(m)}",
                    f"ax_x64_mov_mi(&sec, {sz}, {mem_c(m)}, {c_i32(imm)});",
                    f"x64_mov_mi(mut_view(*sec), {sz}u8, {mem_ax(m)}, {ax_i32(imm)});",
                ))

    # 6. movzx_rr, 7. movzx_rm, 8. movsx_rr, 9. movsx_rm
    for dst_sz, src_sz, op2 in [(2, 1, 0xB6), (4, 1, 0xB6), (8, 1, 0xB6), (4, 2, 0xB7), (8, 2, 0xB7)]:
        mnem = f"movz{SZ_SUFFIX[src_sz]}{SZ_SUFFIX[dst_sz]}"
        for dst, src in pairs:
            xfail_task = None
            xfail_enc = None
            if src_sz == 1 and dst_sz in (2, 4) and dst < 8 and (4 <= src <= 7):
                xfail_task = "AX0-FIX-ENC-MOVX-REX"
                xfail_enc = sim_sz(dst_sz) + sim_rex_rr(dst_sz, dst, src) + [0x0F, op2, 0xC0 | ((dst & 7) << 3) | (src & 7)]
            vecs.append(Vector(
                "ax_x64_movzx_rr",
                f"{mnem} {REGS_ASM[src_sz][src]}, {REGS_ASM[dst_sz][dst]}",
                f"ax_x64_movzx_rr(&sec, {dst_sz}, {src_sz}, {c_reg(dst)}, {c_reg(src)});",
                f"x64_movzx_rr(mut_view(*sec), {dst_sz}u8, {src_sz}u8, {ax_reg(dst)}, {ax_reg(src)});",
                xfail_task=xfail_task,
                xfail_enc=xfail_enc,
            ))
        for dst in [0, 8, 15]:
            for m in MEM_CORE[:5]:
                vecs.append(Vector(
                    "ax_x64_movzx_rm",
                    f"{mnem} {mem_asm(m)}, {REGS_ASM[dst_sz][dst]}",
                    f"ax_x64_movzx_rm(&sec, {dst_sz}, {src_sz}, {c_reg(dst)}, {mem_c(m)});",
                    f"x64_movzx_rm(mut_view(*sec), {dst_sz}u8, {src_sz}u8, {ax_reg(dst)}, {mem_ax(m)});",
                ))

    for dst_sz, src_sz in [(2, 1), (4, 1), (8, 1), (4, 2), (8, 2)]:
        mnem = f"movs{SZ_SUFFIX[src_sz]}{SZ_SUFFIX[dst_sz]}"
        op2 = 0xBE if src_sz == 1 else 0xBF
        for dst, src in pairs:
            xfail_task = None
            xfail_enc = None
            if src_sz == 1 and dst_sz in (2, 4) and dst < 8 and (4 <= src <= 7):
                xfail_task = "AX0-FIX-ENC-MOVX-REX"
                xfail_enc = sim_sz(dst_sz) + sim_rex_rr(dst_sz, dst, src) + [0x0F, op2, 0xC0 | ((dst & 7) << 3) | (src & 7)]
            vecs.append(Vector(
                "ax_x64_movsx_rr",
                f"{mnem} {REGS_ASM[src_sz][src]}, {REGS_ASM[dst_sz][dst]}",
                f"ax_x64_movsx_rr(&sec, {dst_sz}, {src_sz}, {c_reg(dst)}, {c_reg(src)});",
                f"x64_movsx_rr(mut_view(*sec), {dst_sz}u8, {src_sz}u8, {ax_reg(dst)}, {ax_reg(src)});",
                xfail_task=xfail_task,
                xfail_enc=xfail_enc,
            ))
        for dst in [0, 8, 15]:
            for m in MEM_CORE[:5]:
                vecs.append(Vector(
                    "ax_x64_movsx_rm",
                    f"{mnem} {mem_asm(m)}, {REGS_ASM[dst_sz][dst]}",
                    f"ax_x64_movsx_rm(&sec, {dst_sz}, {src_sz}, {c_reg(dst)}, {mem_c(m)});",
                    f"x64_movsx_rm(mut_view(*sec), {dst_sz}u8, {src_sz}u8, {ax_reg(dst)}, {mem_ax(m)});",
                ))

    # 10. lea & 11. lea_sym
    for sz in [2, 4, 8]:
        suf = SZ_SUFFIX[sz]
        for reg in [0, 4, 12]:
            for m in MEM_SPECS:
                vecs.append(Vector(
                    "ax_x64_lea",
                    f"lea{suf} {mem_asm(m)}, {REGS_ASM[sz][reg]}",
                    f"ax_x64_lea(&sec, {sz}, {c_reg(reg)}, {mem_c(m)});",
                    f"x64_lea(mut_view(*sec), {sz}u8, {ax_reg(reg)}, {mem_ax(m)});",
                ))
        for reg in range(16):
            vecs.append(Vector(
                "ax_x64_lea",
                f"lea{suf} {mem_asm(MEM_SPECS[0])}, {REGS_ASM[sz][reg]}",
                f"ax_x64_lea(&sec, {sz}, {c_reg(reg)}, {mem_c(MEM_SPECS[0])});",
                f"x64_lea(mut_view(*sec), {sz}u8, {ax_reg(reg)}, {mem_ax(MEM_SPECS[0])});",
            ))

    for reg in range(16):
        xfail_task = None
        xfail_enc = None
        if reg >= 8:
            # encode.c and encode.ax pass dst as rm (REX.B=0x49) instead of reg (REX.R=0x4C)
            xfail_task = "AX0-FIX-ENC-LEA-SYM-REX"
            xfail_enc = [0x49, 0x8D, 0x05 | ((reg & 7) << 3), 0x00, 0x00, 0x00, 0x00]
        vecs.append(Vector(
            "ax_x64_lea_sym",
            f"leaq 0(%rip), {REGS_ASM[8][reg]}",
            f"ax_x64_lea_sym(&sec, {c_reg(reg)}, sym);",
            f"x64_lea_sym(mut_view(*sec), {ax_reg(reg)}, sym);",
            reset_relocs=True,
            xfail_task=xfail_task,
            xfail_enc=xfail_enc,
        ))

    # 12..35. Binary ALU: add, or, and, sub, xor, cmp (_rr, _rm, _mr, _ri)
    alu_ops = [
        ("add", 0),
        ("or", 1),
        ("and", 4),
        ("sub", 5),
        ("xor", 6),
        ("cmp", 7),
    ]
    for name, ext in alu_ops:
        for sz in [1, 2, 4, 8]:
            suf = SZ_SUFFIX[sz]
            for dst, src in pairs:
                vecs.append(Vector(
                    f"ax_x64_{name}_rr",
                    f"{name}{suf} {REGS_ASM[sz][src]}, {REGS_ASM[sz][dst]}",
                    f"ax_x64_{name}_rr(&sec, {sz}, {c_reg(dst)}, {c_reg(src)});",
                    f"x64_{name}_rr(mut_view(*sec), {sz}u8, {ax_reg(dst)}, {ax_reg(src)});",
                ))
            mem_list = MEM_CORE if name in ("add", "cmp") else MEM_CORE[:6]
            for reg in [0, 4, 12]:
                for m in mem_list:
                    vecs.append(Vector(
                        f"ax_x64_{name}_rm",
                        f"{name}{suf} {mem_asm(m)}, {REGS_ASM[sz][reg]}",
                        f"ax_x64_{name}_rm(&sec, {sz}, {c_reg(reg)}, {mem_c(m)});",
                        f"x64_{name}_rm(mut_view(*sec), {sz}u8, {ax_reg(reg)}, {mem_ax(m)});",
                    ))
                    vecs.append(Vector(
                        f"ax_x64_{name}_mr",
                        f"{name}{suf} {REGS_ASM[sz][reg]}, {mem_asm(m)}",
                        f"ax_x64_{name}_mr(&sec, {sz}, {mem_c(m)}, {c_reg(reg)});",
                        f"x64_{name}_mr(mut_view(*sec), {sz}u8, {mem_ax(m)}, {ax_reg(reg)});",
                    ))
            if sz == 1:
                imms = [0, 127, -128]
            elif sz == 2:
                imms = [0, 127, 128, -128, -129, 32767, -32768]
            else:
                imms = [0, 127, 128, -128, -129, 2147483647, -2147483648]
            for reg in range(16):
                reg_imms = imms if reg in (0, 4, 5, 8, 12, 15) else ([0, -128] if sz == 1 else [0, 128])
                for imm in reg_imms:
                    xfail_task = None
                    xfail_enc = None
                    if sz in (2, 4, 8) and reg == 0 and -128 <= imm <= 127:
                        xfail_task = "AX0-FIX-ENC-ALU-RAX-IMM8"
                        xfail_enc = sim_alu_ri(sz, ext, reg, imm)
                    vecs.append(Vector(
                        f"ax_x64_{name}_ri",
                        f"{name}{suf} ${imm}, {REGS_ASM[sz][reg]}",
                        f"ax_x64_{name}_ri(&sec, {sz}, {c_reg(reg)}, {c_i32(imm)});",
                        f"x64_{name}_ri(mut_view(*sec), {sz}u8, {ax_reg(reg)}, {ax_i32(imm)});",
                        xfail_task=xfail_task,
                        xfail_enc=xfail_enc,
                    ))

    # 36..38. test_rr, test_rm, test_ri
    for sz in [1, 2, 4, 8]:
        suf = SZ_SUFFIX[sz]
        for left, right in pairs:
            vecs.append(Vector(
                "ax_x64_test_rr",
                f"test{suf} {REGS_ASM[sz][right]}, {REGS_ASM[sz][left]}",
                f"ax_x64_test_rr(&sec, {sz}, {c_reg(left)}, {c_reg(right)});",
                f"x64_test_rr(mut_view(*sec), {sz}u8, {ax_reg(left)}, {ax_reg(right)});",
            ))
        for left in [0, 4, 12]:
            for m in MEM_CORE:
                vecs.append(Vector(
                    "ax_x64_test_rm",
                    f"test{suf} {mem_asm(m)}, {REGS_ASM[sz][left]}",
                    f"ax_x64_test_rm(&sec, {sz}, {c_reg(left)}, {mem_c(m)});",
                    f"x64_test_rm(mut_view(*sec), {sz}u8, {ax_reg(left)}, {mem_ax(m)});",
                ))
        if sz == 1:
            imms = [0, 127, -128]
        elif sz == 2:
            imms = [0, 127, 128, -128, -129, 32767, -32768]
        else:
            imms = [0, 127, 128, -128, -129, 2147483647, -2147483648]
        for left in range(16):
            reg_imms = imms if left in (0, 4, 5, 8, 12, 15) else ([0, -128] if sz == 1 else [0, 128])
            for imm in reg_imms:
                vecs.append(Vector(
                    "ax_x64_test_ri",
                    f"test{suf} ${imm}, {REGS_ASM[sz][left]}",
                    f"ax_x64_test_ri(&sec, {sz}, {c_reg(left)}, {c_i32(imm)});",
                    f"x64_test_ri(mut_view(*sec), {sz}u8, {ax_reg(left)}, {ax_i32(imm)});",
                ))

    # 39..40. imul_rr, imul_rm (widths 2, 4, 8)
    for sz in [2, 4, 8]:
        suf = SZ_SUFFIX[sz]
        for dst, src in pairs:
            vecs.append(Vector(
                "ax_x64_imul_rr",
                f"imul{suf} {REGS_ASM[sz][src]}, {REGS_ASM[sz][dst]}",
                f"ax_x64_imul_rr(&sec, {sz}, {c_reg(dst)}, {c_reg(src)});",
                f"x64_imul_rr(mut_view(*sec), {sz}u8, {ax_reg(dst)}, {ax_reg(src)});",
            ))
        for dst in [0, 4, 12]:
            for m in MEM_CORE:
                vecs.append(Vector(
                    "ax_x64_imul_rm",
                    f"imul{suf} {mem_asm(m)}, {REGS_ASM[sz][dst]}",
                    f"ax_x64_imul_rm(&sec, {sz}, {c_reg(dst)}, {mem_c(m)});",
                    f"x64_imul_rm(mut_view(*sec), {sz}u8, {ax_reg(dst)}, {mem_ax(m)});",
                ))

    # 41..52. mul_r, mul_m, cqo, cdq, idiv_r, idiv_m, div_r, div_m, neg_r, neg_m, not_r, not_m
    vecs.append(Vector("ax_x64_cqo", "cqto", "ax_x64_cqo(&sec);", "x64_cqo(mut_view(*sec));"))
    vecs.append(Vector("ax_x64_cdq", "cltd", "ax_x64_cdq(&sec);", "x64_cdq(mut_view(*sec));"))

    for name in ["mul", "idiv", "div", "neg", "not"]:
        for sz in [1, 2, 4, 8]:
            suf = SZ_SUFFIX[sz]
            for reg in range(16):
                vecs.append(Vector(
                    f"ax_x64_{name}_r",
                    f"{name}{suf} {REGS_ASM[sz][reg]}",
                    f"ax_x64_{name}_r(&sec, {sz}, {c_reg(reg)});",
                    f"x64_{name}_r(mut_view(*sec), {sz}u8, {ax_reg(reg)});",
                ))
            for m in MEM_CORE[:8]:
                vecs.append(Vector(
                    f"ax_x64_{name}_m",
                    f"{name}{suf} {mem_asm(m)}",
                    f"ax_x64_{name}_m(&sec, {sz}, {mem_c(m)});",
                    f"x64_{name}_m(mut_view(*sec), {sz}u8, {mem_ax(m)});",
                ))

    # 53..58. shl_rcl, shl_ri, shr_rcl, shr_ri, sar_rcl, sar_ri
    for name in ["shl", "shr", "sar"]:
        for sz in [1, 2, 4, 8]:
            suf = SZ_SUFFIX[sz]
            for reg in range(16):
                vecs.append(Vector(
                    f"ax_x64_{name}_rcl",
                    f"{name}{suf} %cl, {REGS_ASM[sz][reg]}",
                    f"ax_x64_{name}_rcl(&sec, {sz}, {c_reg(reg)});",
                    f"x64_{name}_rcl(mut_view(*sec), {sz}u8, {ax_reg(reg)});",
                ))
                for imm in [0, 1, 2, 7, 31, 63]:
                    vecs.append(Vector(
                        f"ax_x64_{name}_ri",
                        f"{name}{suf} ${imm}, {REGS_ASM[sz][reg]}",
                        f"ax_x64_{name}_ri(&sec, {sz}, {c_reg(reg)}, {imm});",
                        f"x64_{name}_ri(mut_view(*sec), {sz}u8, {ax_reg(reg)}, {imm}u8);",
                    ))

    # 59..63 & 69. setcc_r, setcc_m, jcc, jcc_sym, jcc8 (all 16 condition codes 0x0..0xF)
    for cc_val, cc_enum, cc_mnem in CC_LIST:
        for reg in range(16):
            vecs.append(Vector(
                "ax_x64_setcc_r",
                f"set{cc_mnem} {REGS_ASM[1][reg]}",
                f"ax_x64_setcc_r(&sec, AX_CC_{cc_enum}, {c_reg(reg)});",
                f"x64_setcc_r(mut_view(*sec), AX_CC_{cc_enum}, {ax_reg(reg)});",
            ))
        for m in MEM_CORE[:6]:
            vecs.append(Vector(
                "ax_x64_setcc_m",
                f"set{cc_mnem} {mem_asm(m)}",
                f"ax_x64_setcc_m(&sec, AX_CC_{cc_enum}, {mem_c(m)});",
                f"x64_setcc_m(mut_view(*sec), AX_CC_{cc_enum}, {mem_ax(m)});",
            ))
        for rel32 in [0, 127, 128, -128, -129, 2147483647, -2147483648]:
            vecs.append(Vector(
                "ax_x64_jcc",
                f"{{disp32}} j{cc_mnem} .+6+{rel32}",
                f"ax_x64_jcc(&sec, AX_CC_{cc_enum}, {c_i32(rel32)});",
                f"x64_jcc(mut_view(*sec), AX_CC_{cc_enum}, {ax_i32(rel32)});",
            ))
        vecs.append(Vector(
            "ax_x64_jcc_sym",
            f"{{disp32}} j{cc_mnem} .+6",
            f"ax_x64_jcc_sym(&sec, AX_CC_{cc_enum}, sym);",
            f"x64_jcc_sym(mut_view(*sec), AX_CC_{cc_enum}, sym);",
            reset_relocs=True,
        ))
        for rel8 in [0, 1, 127, -1, -128]:
            vecs.append(Vector(
                "ax_x64_jcc8",
                f"j{cc_mnem} .+2+{rel8}",
                f"ax_x64_jcc8(&sec, AX_CC_{cc_enum}, {rel8});",
                f"x64_jcc8(mut_view(*sec), AX_CC_{cc_enum}, {ax_i8(rel8)});",
            ))

    # 64..68 & 70. jmp, jmp_sym, call, call_sym, call_r, call_m, jmp8
    for rel32 in [0, 127, 128, -5, -128, -129, 2147483647, -2147483648]:
        vecs.append(Vector(
            "ax_x64_jmp",
            f"{{disp32}} jmp .+5+{rel32}",
            f"ax_x64_jmp(&sec, {c_i32(rel32)});",
            f"x64_jmp(mut_view(*sec), {ax_i32(rel32)});",
        ))
        vecs.append(Vector(
            "ax_x64_call",
            f"call .+5+{rel32}",
            f"ax_x64_call(&sec, {c_i32(rel32)});",
            f"x64_call(mut_view(*sec), {ax_i32(rel32)});",
        ))

    vecs.append(Vector(
        "ax_x64_jmp_sym",
        "{disp32} jmp .+5",
        "ax_x64_jmp_sym(&sec, sym);",
        "x64_jmp_sym(mut_view(*sec), sym);",
        reset_relocs=True,
    ))
    vecs.append(Vector(
        "ax_x64_call_sym",
        "call .+5",
        "ax_x64_call_sym(&sec, sym);",
        "x64_call_sym(mut_view(*sec), sym);",
        reset_relocs=True,
    ))

    for rel8 in [0, 1, 127, -2, -128]:
        vecs.append(Vector(
            "ax_x64_jmp8",
            f"jmp .+2+{rel8}",
            f"ax_x64_jmp8(&sec, {rel8});",
            f"x64_jmp8(mut_view(*sec), {ax_i8(rel8)});",
        ))

    for reg in range(16):
        vecs.append(Vector(
            "ax_x64_call_r",
            f"callq *{REGS_ASM[8][reg]}",
            f"ax_x64_call_r(&sec, {c_reg(reg)});",
            f"x64_call_r(mut_view(*sec), {ax_reg(reg)});",
            xfail_task="AX0-FIX-ENC-CALL-REXW",
            xfail_enc=sim_rex_rr(8, 2, reg) + [0xFF, 0xD0 | (reg & 7)],
        ))

    for m in MEM_SPECS:
        vecs.append(Vector(
            "ax_x64_call_m",
            f"callq *{mem_asm(m)}",
            f"ax_x64_call_m(&sec, {mem_c(m)});",
            f"x64_call_m(mut_view(*sec), {mem_ax(m)});",
            xfail_task="AX0-FIX-ENC-CALL-REXW",
            xfail_enc=sim_rex_rm(8, 2, m) + [0xFF] + sim_mem_op(2, m),
        ))

    # 71..76. ret, push_r, push_m, pop_r, pop_m, int3
    for reg in range(16):
        vecs.append(Vector(
            "ax_x64_push_r",
            f"pushq {REGS_ASM[8][reg]}",
            f"ax_x64_push_r(&sec, {c_reg(reg)});",
            f"x64_push_r(mut_view(*sec), {ax_reg(reg)});",
        ))
        vecs.append(Vector(
            "ax_x64_pop_r",
            f"popq {REGS_ASM[8][reg]}",
            f"ax_x64_pop_r(&sec, {c_reg(reg)});",
            f"x64_pop_r(mut_view(*sec), {ax_reg(reg)});",
        ))

    for m in MEM_SPECS:
        vecs.append(Vector(
            "ax_x64_push_m",
            f"pushq {mem_asm(m)}",
            f"ax_x64_push_m(&sec, {mem_c(m)});",
            f"x64_push_m(mut_view(*sec), {mem_ax(m)});",
        ))
        vecs.append(Vector(
            "ax_x64_pop_m",
            f"popq {mem_asm(m)}",
            f"ax_x64_pop_m(&sec, {mem_c(m)});",
            f"x64_pop_m(mut_view(*sec), {mem_ax(m)});",
        ))

    vecs.append(Vector("ax_x64_ret", "retq", "ax_x64_ret(&sec);", "x64_ret(mut_view(*sec));"))
    vecs.append(Vector("ax_x64_int3", "int3", "ax_x64_int3(&sec);", "x64_int3(mut_view(*sec));"))

    return vecs


def assemble_all_gnu_as(vecs: list[Vector]) -> list[list[int]]:
    as_bin = shutil.which("as")
    objdump_bin = shutil.which("objdump")
    if not as_bin or not objdump_bin:
        raise RuntimeError(
            "GNU binutils ('as' and 'objdump') are required to generate or check encode tables "
            f"(found as={as_bin!r}, objdump={objdump_bin!r})."
        )

    with tempfile.TemporaryDirectory() as td:
        s_file = os.path.join(td, "vectors.s")
        o_file = os.path.join(td, "vectors.o")
        with open(s_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(".text\n")
            for idx, v in enumerate(vecs):
                f.write(f"v_{idx}:\n    {v.asm}\n")
            f.write("v_end:\n    nop\n")

        res_as = subprocess.run([as_bin, "--64", "-o", o_file, s_file], capture_output=True, text=True)
        if res_as.returncode != 0:
            raise RuntimeError(f"GNU as failed:\n{res_as.stderr}")

        res_od = subprocess.run([objdump_bin, "-d", "-w", "-z", o_file], capture_output=True, text=True)
        if res_od.returncode != 0:
            raise RuntimeError(f"GNU objdump failed:\n{res_od.stderr}")

        out: dict[int, list[int]] = {}
        cur: int | None = None
        label_re = re.compile(r"^[0-9a-fA-F]+\s+<v_(\d+|end)>:$")
        for line in res_od.stdout.splitlines():
            line_s = line.strip()
            m = label_re.match(line_s)
            if m:
                tag = m.group(1)
                if tag == "end":
                    cur = None
                else:
                    cur = int(tag)
                    out[cur] = []
                continue
            if cur is not None and ":\t" in line_s:
                parts = line_s.split(":\t", 1)[1]
                hex_part = parts.split("\t")[0].strip()
                for h in hex_part.split():
                    out[cur].append(int(h, 16))

        result = []
        for idx in range(len(vecs)):
            if idx not in out or not out[idx]:
                raise RuntimeError(f"Failed to extract bytes for vector {idx}: {vecs[idx].asm!r}")
            result.append(out[idx])
        return result


def fmt_hex_list_c(bs: list[int]) -> str:
    return ", ".join(f"0x{b:02x}" for b in bs)


def fmt_hex_list_ax(bs: list[int]) -> str:
    return ", ".join(f"0x{b:02x}u8" for b in bs)


def fmt_hex_space(bs: list[int]) -> str:
    return " ".join(f"{b:02x}" for b in bs)


def render_c_inc(vecs: list[Vector], gnu_bytes_list: list[list[int]]) -> str:
    lines = [
        "/* GENERATED BY tools/gen_encode_tests.py using GNU as + objdump. DO NOT EDIT. */",
        f"/* Total vectors: {len(vecs)} */",
        "#include <stdlib.h>",
        "static void run_encode_tests(void) {",
        "    ax_section_t sec = {0};",
        "    ax_symbol_id_t sym = {1};",
        "    (void)sym;",
    ]
    for i, (v, gnu_b) in enumerate(zip(vecs, gnu_bytes_list)):
        c_desc = v.asm.replace("\\", "\\\\").replace('"', '\\"')
        reset = "sec.bytes_len = 0; sec.relocs_len = 0;" if v.reset_relocs else "sec.bytes_len = 0;"
        if v.xfail_task is not None:
            assert v.xfail_enc is not None
            assert v.xfail_enc != gnu_b, f"Vector marked xfail({v.xfail_task}) now matches GNU as: {v.asm}"
            lines.append(
                f"    // xfail: {v.xfail_task} — {v.asm} "
                f"(gnu_as: {fmt_hex_space(gnu_b)}; actual: {fmt_hex_space(v.xfail_enc)})"
            )
            lines.append(f"    {reset}")
            lines.append(f"    {v.c_stmt}")
            lines.append(f"    static const uint8_t gnu_as_{i}[] = {{ {fmt_hex_list_c(gnu_b)} }};")
            lines.append(f"    static const uint8_t xfail_{i}[] = {{ {fmt_hex_list_c(v.xfail_enc)} }};")
            lines.append(f"    (void)gnu_as_{i};")
            lines.append(
                f"    assert_bytes_eq(xfail_{i}, sizeof(xfail_{i}), sec.bytes, sec.bytes_len, "
                f"\"xfail({v.xfail_task}): {c_desc}\");"
            )
        else:
            lines.append(f"    // {v.asm}")
            lines.append(f"    {reset}")
            lines.append(f"    {v.c_stmt}")
            lines.append(f"    static const uint8_t expected_{i}[] = {{ {fmt_hex_list_c(gnu_b)} }};")
            lines.append(
                f"    assert_bytes_eq(expected_{i}, sizeof(expected_{i}), sec.bytes, sec.bytes_len, \"{c_desc}\");"
            )
    lines.append("    free(sec.bytes);")
    lines.append("    free(sec.relocs);")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


AX_PRELUDE = """\
// Auto-generated by tools/gen_encode_tests.py using GNU as + objdump.
// DO NOT EDIT MANUALLY — run `python tools/gen_encode_tests.py` to regenerate.
//
// test: run
// modes: interp native
// timeout: 600
// stdout: OK __TOTAL_VECTORS__\\n

module compiler.obj.coff

@derive(Copy)
pub struct SectionId {
    pub v: u32,
}

impl SectionId {
    pub fn none() -> SectionId { SectionId { v: 0u32 } }
}

@derive(Copy)
pub struct SymbolId {
    pub v: u32,
}

impl SymbolId {
    pub fn none() -> SymbolId { SymbolId { v: 0u32 } }
    pub fn is_some(self: view<SymbolId>) -> bool { self.v != 0u32 }
}

pub struct Reloc {
    pub offset: u32,
    pub kind: u32,
    pub symbol_id: SymbolId,
    pub addend: i64,
}

pub struct Section {
    pub bytes: *mut u8,
    pub bytes_len: usize,
    pub relocs_len: usize,
    pub buf: [32]u8,
}

pub struct ObjSymbol {
    pub v: u32,
}

pub struct ObjModel {
    pub dummy: u32,
}

pub const RELOC_NONE: u32 = 0u32;
pub const RELOC_X86_64_PC32: u32 = 1u32;
pub const RELOC_X86_64_32: u32 = 2u32;
pub const RELOC_X86_64_64: u32 = 3u32;
pub const RELOC_X86_64_GOT32: u32 = 4u32;
pub const RELOC_X86_64_PLT32: u32 = 5u32;

pub const AX_RELOC_NONE: u32 = 0u32;
pub const AX_RELOC_X86_64_PC32: u32 = 1u32;
pub const AX_RELOC_X86_64_32: u32 = 2u32;
pub const AX_RELOC_X86_64_64: u32 = 3u32;
pub const AX_RELOC_X86_64_GOT32: u32 = 4u32;
pub const AX_RELOC_X86_64_PLT32: u32 = 5u32;

pub const SYM_LOCAL: u32 = 0u32;
pub const SYM_GLOBAL: u32 = 1u32;
pub const SYM_EXTERNAL: u32 = 2u32;

pub const AX_SYM_LOCAL: u32 = 0u32;
pub const AX_SYM_GLOBAL: u32 = 1u32;
pub const AX_SYM_EXTERNAL: u32 = 2u32;

pub fn section_add_byte(sec: mut_view<Section>, b: u8) {
    let idx = sec.bytes_len;
    sec.buf[idx] = b;
    sec.bytes_len = idx + 1;
}

pub fn section_add_bytes(sec: mut_view<Section>, data: *const u8, count: usize) {
    let mut i: usize = 0;
    while i < count {
        let b = unsafe { *(data + i) };
        section_add_byte(mut_view(*sec), b);
        i = i + 1;
    }
}

pub fn section_append_slice(sec: mut_view<Section>, data: view<[u8]>) {
    let n = len(data);
    let mut i: usize = 0;
    while i < n {
        section_add_byte(mut_view(*sec), data[i]);
        i = i + 1;
    }
}

pub fn section_add_reloc(sec: mut_view<Section>, offset: u32, kind: u32, symbol_id: SymbolId, addend: i64) {
    let _ = offset;
    let _ = kind;
    let _ = symbol_id;
    let _ = addend;
    sec.relocs_len = sec.relocs_len + 1;
}

pub fn coff_write_u32_le(dst: *mut u8, offset: usize, val: u32) {
    if (dst as usize) == 0 {
        return;
    }
    unsafe {
        let p = dst + offset;
        *p = (val & 0xFFu32) as u8;
        *(p + 1) = ((val >> 8) & 0xFFu32) as u8;
        *(p + 2) = ((val >> 16) & 0xFFu32) as u8;
        *(p + 3) = ((val >> 24) & 0xFFu32) as u8;
    }
}

pub fn objmodel_find_symbol(obj: view<ObjModel>, name: *const u8) -> SymbolId {
    let _ = obj;
    let _ = name;
    SymbolId { v: 0u32 }
}

pub fn objmodel_find_symbol_str(obj: view<ObjModel>, name: Str) -> SymbolId {
    let _ = obj;
    let _ = name;
    SymbolId { v: 0u32 }
}

pub fn objmodel_add_symbol(obj: mut_view<ObjModel>, name: *const u8, section_id: SectionId, value: u64, size: u64, linkage: u32) -> SymbolId {
    let _ = obj;
    let _ = name;
    let _ = section_id;
    let _ = value;
    let _ = size;
    let _ = linkage;
    SymbolId { v: 1u32 }
}

pub fn objmodel_add_symbol_str(obj: mut_view<ObjModel>, name: Str, section_id: SectionId, value: u64, size: u64, linkage: u32) -> SymbolId {
    let _ = obj;
    let _ = name;
    let _ = section_id;
    let _ = value;
    let _ = size;
    let _ = linkage;
    SymbolId { v: 1u32 }
}
"""


def render_ax_vectors(vecs: list[Vector], gnu_bytes_list: list[list[int]], encode_ax_src: str) -> str:
    prelude = AX_PRELUDE.replace("__TOTAL_VECTORS__", str(len(vecs)))
    used_entries = sorted({v.entry.removeprefix("ax_") for v in vecs})
    lines = [
        prelude.rstrip("\n"),
        "",
        EMBED_BEGIN_MARKER,
        encode_ax_src.rstrip("\n"),
        EMBED_END_MARKER,
        "",
        "module main",
        "",
        "use compiler.obj.coff.Section",
        "use compiler.obj.coff.SymbolId",
    ]

    for rname in REG_NAMES:
        lines.append(f"use compiler.target.x64.encode.AX_REG_{rname}")
    for _, cc_enum, _ in CC_LIST:
        lines.append(f"use compiler.target.x64.encode.AX_CC_{cc_enum}")
    for m_fn in ["x64_mem_base", "x64_mem_base_disp", "x64_mem_index", "x64_mem_index_disp", "x64_mem_rip"]:
        lines.append(f"use compiler.target.x64.encode.{m_fn}")
    for fn_name in used_entries:
        lines.append(f"use compiler.target.x64.encode.{fn_name}")

    lines.append("")

    max_len = max(
        max(len(b) for b in gnu_bytes_list),
        max((len(v.xfail_enc) for v in vecs if v.xfail_enc is not None), default=1),
    )
    for k in range(1, max_len + 1):
        params = ", ".join(f"b{i}: u8" for i in range(k))
        conds = " || ".join([f"sec.bytes_len != {k}"] + [f"sec.buf[{i}] != b{i}" for i in range(k)])
        lines.append(f"fn chk{k}(sec: mut_view<Section>, c: mut_view<i64>, fail: mut_view<i64>, {params}) {{")
        lines.append(f"    if {conds} {{")
        lines.append("        *fail = *fail + 1;")
        lines.append("    }")
        lines.append("    sec.bytes_len = 0;")
        lines.append("    *c = *c + 1;")
        lines.append("}")
        lines.append(f"fn xfail_chk{k}(sec: mut_view<Section>, c: mut_view<i64>, fail: mut_view<i64>, {params}) {{")
        lines.append(f"    if {conds} {{")
        lines.append("        *fail = *fail + 1;")
        lines.append("    }")
        lines.append("    sec.bytes_len = 0;")
        lines.append("    *c = *c + 1;")
        lines.append("}")

    lines.append("")

    batch_size = 150
    num_batches = (len(vecs) + batch_size - 1) // batch_size
    for b_idx in range(num_batches):
        chunk = list(zip(
            vecs[b_idx * batch_size : (b_idx + 1) * batch_size],
            gnu_bytes_list[b_idx * batch_size : (b_idx + 1) * batch_size],
        ))
        lines.append(
            f"fn run_batch_{b_idx}(sec: mut_view<Section>, count: mut_view<i64>, "
            f"fail: mut_view<i64>, sym: SymbolId) {{"
        )
        lines.append("    let _ = sym;")
        for v, gnu_b in chunk:
            if v.reset_relocs:
                lines.append("    sec.relocs_len = 0;")
            if v.xfail_task is not None:
                assert v.xfail_enc is not None
                lines.append(
                    f"    // xfail: {v.xfail_task} — {v.asm} "
                    f"(gnu_as: {fmt_hex_space(gnu_b)}; actual: {fmt_hex_space(v.xfail_enc)})"
                )
                lines.append(f"    {v.ax_stmt}")
                lines.append(
                    f"    xfail_chk{len(v.xfail_enc)}(mut_view(*sec), mut_view(*count), "
                    f"mut_view(*fail), {fmt_hex_list_ax(v.xfail_enc)});"
                )
            else:
                lines.append(f"    // {v.asm}")
                lines.append(f"    {v.ax_stmt}")
                lines.append(
                    f"    chk{len(gnu_b)}(mut_view(*sec), mut_view(*count), "
                    f"mut_view(*fail), {fmt_hex_list_ax(gnu_b)});"
                )
        lines.append("}")
        lines.append("")

    lines.append("pub fn main() -> i32 {")
    lines.append("    let mut sec = Section {")
    lines.append("        bytes: 0 as *mut u8,")
    lines.append("        bytes_len: 0,")
    lines.append("        relocs_len: 0,")
    lines.append("        buf: [0u8; 32],")
    lines.append("    };")
    lines.append("    let sym = SymbolId { v: 1u32 };")
    lines.append("    let mut count: i64 = 0;")
    lines.append("    let mut fail: i64 = 0;")
    for b_idx in range(num_batches):
        lines.append(f"    run_batch_{b_idx}(mut_view(sec), mut_view(count), mut_view(fail), sym);")
    lines.append(f"    if fail != 0i64 || count != {len(vecs)}i64 {{")
    lines.append("        return 1;")
    lines.append("    }")
    lines.append(f'    print("OK {len(vecs)}\\n");')
    lines.append("    0")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def generate_all() -> tuple[str, str, str, list[Vector], list[list[int]]]:
    if not os.path.isfile(ENCODE_AX_PATH):
        raise RuntimeError(f"Missing encoder source file: {ENCODE_AX_PATH}")
    with open(ENCODE_AX_PATH, "r", encoding="utf-8") as f:
        encode_ax_src = f.read()

    vecs = build_vectors()
    gnu_bytes_list = assemble_all_gnu_as(vecs)
    c_inc = render_c_inc(vecs, gnu_bytes_list)
    ax_vec = render_ax_vectors(vecs, gnu_bytes_list, encode_ax_src)
    return c_inc, ax_vec, encode_ax_src, vecs, gnu_bytes_list


def run_check() -> int:
    try:
        c_inc_expected, ax_vec_expected, encode_ax_src, vecs, _ = generate_all()
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    ok = True
    if not os.path.isfile(INC_PATH):
        print(f"FAIL: missing {INC_PATH}", file=sys.stderr)
        ok = False
    else:
        with open(INC_PATH, "r", encoding="utf-8") as f:
            c_inc_actual = f.read()
        if c_inc_actual != c_inc_expected:
            print(
                f"FAIL: {INC_PATH} is out of date with tools/gen_encode_tests.py / GNU as.",
                file=sys.stderr,
            )
            ok = False

    if not os.path.isfile(AX_VEC_PATH):
        print(f"FAIL: missing {AX_VEC_PATH}", file=sys.stderr)
        ok = False
    else:
        with open(AX_VEC_PATH, "r", encoding="utf-8") as f:
            ax_vec_actual = f.read()
        expected_embed = f"{EMBED_BEGIN_MARKER}\n{encode_ax_src.rstrip(chr(10))}\n{EMBED_END_MARKER}"
        if expected_embed not in ax_vec_actual:
            print(
                f"FAIL: verbatim copy of compiler/target/x64/encode.ax in {AX_VEC_PATH} "
                "does not match compiler/target/x64/encode.ax on disk.",
                file=sys.stderr,
            )
            ok = False
        if ax_vec_actual != ax_vec_expected:
            print(
                f"FAIL: {AX_VEC_PATH} is out of date with tools/gen_encode_tests.py / GNU as.",
                file=sys.stderr,
            )
            ok = False

    if not ok:
        print("Run `python tools/gen_encode_tests.py` to regenerate.", file=sys.stderr)
        return 1

    print(f"OK encode tables current ({len(vecs)} vectors)")
    return 0


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] in ("check", "--check"):
        return run_check()
    if len(sys.argv) > 1 and sys.argv[1] not in ("generate", "--generate"):
        print(f"Usage: {sys.argv[0]} [check]", file=sys.stderr)
        return 2

    c_inc, ax_vec, _, vecs, _ = generate_all()
    os.makedirs(os.path.dirname(INC_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(AX_VEC_PATH), exist_ok=True)
    with open(INC_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(c_inc)
    with open(AX_VEC_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(ax_vec)

    xfails = sum(1 for v in vecs if v.xfail_task is not None)
    entries = len({v.entry for v in vecs})
    print(
        f"Generated {len(vecs)} vectors across {entries} instruction emitters "
        f"(+ 5 memory constructors = {entries + 5} entry points; {xfails} xfail vectors)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
