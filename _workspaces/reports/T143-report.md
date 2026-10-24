# T143 Report — GNU `as` Encoder Table Widened + Axiom Twin (`OI-08`)

## Summary

Extended [`tools/gen_encode_tests.py`](file:///d:/projects/compiler/new%20lang/tools/gen_encode_tests.py) to batch-assemble **10,211 instruction vectors** through GNU `as --64` and `objdump -d -w -z` in a single pass (~1.8s) and emit two synchronized oracle artefacts:

1. [`tests/encode/encode_tests.inc`](file:///d:/projects/compiler/new%20lang/tests/encode/encode_tests.inc) — C vector table included by [`tests/encode/cdriver_encode.c`](file:///d:/projects/compiler/new%20lang/tests/encode/cdriver_encode.c) and executed by [`tests/encode/encode.test`](file:///d:/projects/compiler/new%20lang/tests/encode/encode.test) (`requires: axiom0-internal`).
2. [`tests/encode/axiom/gnu_as_vectors.ax`](file:///d:/projects/compiler/new%20lang/tests/encode/axiom/gnu_as_vectors.ax) — Self-contained Axiom twin (`modes: interp native`, no `requires: axiom0-internal`) that embeds [`compiler/target/x64/encode.ax`](file:///d:/projects/compiler/new%20lang/compiler/target/x64/encode.ax) **verbatim**, runs all 10,211 vectors in both `interp` and `native` (`-O0` and `-O1`) modes, and prints `OK 10211`.
3. [`tests/encode/encode_tables_current.test`](file:///d:/projects/compiler/new%20lang/tests/encode/encode_tables_current.test) — Runs `python {root}/tools/gen_encode_tests.py check`, which regenerates both files in memory using GNU `as`/`objdump` and `compiler/target/x64/encode.ax` on disk, verifying byte-for-byte equality of both tables and of the verbatim embedded `compiler/target/x64/encode.ax` block.

---

## Coverage & Vector Counts per Entry Point (81 / 81 = 100%)

All **81** entry points in `bootstrap/axiom0/src/target/x64/encode/encode.h` and `compiler/target/x64/encode.ax` (5 memory addressing constructors + 76 instruction emitters) are covered, including **100% (71 / 71)** of the entry points emitted by `isel`, `frame`, `emit_mc`, `emit_obj`, and `build_native` plus all **10 / 10** remaining entry points in `encode.h` (`movzx_{rr,rm}`, `movsx_{rr,rm}`, `neg_{r,m}`, `not_{r,m}`, `jcc_sym`, `jmp_sym`). Zero entry points of the 81 are left out.

### Dimensions Covered

- **Registers**: All 16 general-purpose registers `rax..r15` (`0..15`) at every legal operand width:
  - 8-bit: `al, cl, dl, bl, spl, bpl, sil, dil, r8b..r15b` (testing forced `0x40` byte-REX for `spl..dil` and `REX.R`/`REX.B` for `r8b..r15b`)
  - 16-bit: `ax..di, r8w..r15w` (testing `0x66` operand-size prefix + REX)
  - 32-bit: `eax..edi, r8d..r15d`
  - 64-bit: `rax..rdi, r8..r15` (testing `REX.W` + `REX.R`/`REX.B`)
- **Addressing Modes (40 `MEM_SPECS` forms across all 5 memory constructors)**:
  - `base`: `(%rax)`, `(%rsp)` (forced SIB `0x24`), `(%rbp)` (forced `mod=01, disp8=0`), `(%r8)`, `(%r12)` (`REX.B` + SIB `0x24`), `(%r13)` (`REX.B` + `disp8=0`), `(%r15)`
  - `base+disp8`: `0(%rax)`, `127(%rax)`, `-128(%rax)`, `-8(%rsp)`, `127(%rbp)`, `-128(%r12)`, `8(%r13)`
  - `base+disp32`: `128(%rax)`, `-129(%rax)`, `-129(%rsp)`, `2147483647(%rbp)`, `-2147483648(%r12)`, `128(%r13)`
  - `SIB` (`scale` $\in \{1, 2, 4, 8\}$ with and without displacement): `(%rax,%rcx,1..8)`, `(%rsp,%rax,1)`, `(%rbp,%rcx,2)`, `(%r12,%r8,4)`, `(%r13,%r15,8)`, `127(%rax,%rcx,4)`, `-128(%rsp,%r8,2)`, `16(%rbp,%r9,8)`, `128(%r12,%r15,1)`, `-129(%r13,%r14,8)`
  - `rip-relative`: `0(%rip)`, `127(%rip)`, `-128(%rip)`, `128(%rip)`, `-129(%rip)`, `2147483647(%rip)`, `-2147483648(%rip)`
- **Immediate Boundaries**: `{0, 127, 128, -128, -129, 32767, -32768, 2147483647, -2147483648}` at legal widths, plus 64-bit immediates `{0x0102030405060708, -0x0102030405060708, -9223372036854775808}` for `movabsq` (`mov_ri` width 8).
- **Multiply/Divide**: Unsigned (`mul_r`, `mul_m`, `div_r`, `div_m`) and signed (`imul_rr`, `imul_rm`, `idiv_r`, `idiv_m`, `cqo`, `cdq`) at all legal widths `1, 2, 4, 8`.
- **Condition Codes**: All 16 condition codes `0x0..0xF` (`O, NO, B, AE, E, NE, BE, A, S, NS, P, NP, L, GE, LE, G`) across `setcc_r`, `setcc_m`, `jcc` (`rel32`), `jcc8` (`rel8`), and `jcc_sym`.

### Vector Count by Entry Point

| # | Entry Point (`encode.h` / `encode.ax`) | Used by `isel`/`frame` | Vectors | `xfail` |
|---|----------------------------------------|:----------------------:|--------:|--------:|
| 1 | `ax_x64_mem_base` / `x64_mem_base` | Yes | 1,831 (in mem ops) | 0 |
| 2 | `ax_x64_mem_base_disp` / `x64_mem_base_disp` | Yes | 988 (in mem ops) | 0 |
| 3 | `ax_x64_mem_index` / `x64_mem_index` | Yes | 495 (in mem ops) | 0 |
| 4 | `ax_x64_mem_index_disp` / `x64_mem_index_disp` | Yes | 249 (in mem ops) | 0 |
| 5 | `ax_x64_mem_rip` / `x64_mem_rip` | Yes | 449 (in mem ops) | 0 |
| 6 | `ax_x64_mov_rr` / `x64_mov_rr` | Yes | 176 | 0 |
| 7 | `ax_x64_mov_rm` / `x64_mov_rm` | Yes | 672 | 0 |
| 8 | `ax_x64_mov_mr` / `x64_mov_mr` | Yes | 672 | 0 |
| 9 | `ax_x64_mov_ri` / `x64_mov_ri` | Yes | 432 | 0 |
| 10 | `ax_x64_mov_mi` / `x64_mov_mi` | Yes | 192 | 0 |
| 11 | `ax_x64_movzx_rr` / `x64_movzx_rr` | No (isel uses `and`/`shl`+`shr`) | 220 | 18 |
| 12 | `ax_x64_movzx_rm` / `x64_movzx_rm` | No | 75 | 0 |
| 13 | `ax_x64_movsx_rr` / `x64_movsx_rr` | No (isel uses `shl`+`sar`) | 220 | 18 |
| 14 | `ax_x64_movsx_rm` / `x64_movsx_rm` | No | 75 | 0 |
| 15 | `ax_x64_lea` / `x64_lea` | Yes | 408 | 0 |
| 16 | `ax_x64_lea_sym` / `x64_lea_sym` | Yes | 16 | 8 |
| 17 | `ax_x64_add_rr` / `x64_add_rr` | Yes | 176 | 0 |
| 18 | `ax_x64_add_rm` / `x64_add_rm` | Yes | 168 | 0 |
| 19 | `ax_x64_add_mr` / `x64_add_mr` | Yes | 168 | 0 |
| 20 | `ax_x64_add_ri` / `x64_add_ri` | Yes | 224 | 9 |
| 21 | `ax_x64_or_rr` / `x64_or_rr` | Yes | 176 | 0 |
| 22 | `ax_x64_or_rm` / `x64_or_rm` | Yes | 72 | 0 |
| 23 | `ax_x64_or_mr` / `x64_or_mr` | Yes | 72 | 0 |
| 24 | `ax_x64_or_ri` / `x64_or_ri` | Yes | 224 | 9 |
| 25 | `ax_x64_and_rr` / `x64_and_rr` | Yes | 176 | 0 |
| 26 | `ax_x64_and_rm` / `x64_and_rm` | Yes | 72 | 0 |
| 27 | `ax_x64_and_mr` / `x64_and_mr` | Yes | 72 | 0 |
| 28 | `ax_x64_and_ri` / `x64_and_ri` | Yes | 224 | 9 |
| 29 | `ax_x64_sub_rr` / `x64_sub_rr` | Yes | 176 | 0 |
| 30 | `ax_x64_sub_rm` / `x64_sub_rm` | Yes | 72 | 0 |
| 31 | `ax_x64_sub_mr` / `x64_sub_mr` | Yes | 72 | 0 |
| 32 | `ax_x64_sub_ri` / `x64_sub_ri` | Yes | 224 | 9 |
| 33 | `ax_x64_xor_rr` / `x64_xor_rr` | Yes | 176 | 0 |
| 34 | `ax_x64_xor_rm` / `x64_xor_rm` | Yes | 72 | 0 |
| 35 | `ax_x64_xor_mr` / `x64_xor_mr` | Yes | 72 | 0 |
| 36 | `ax_x64_xor_ri` / `x64_xor_ri` | Yes | 224 | 9 |
| 37 | `ax_x64_cmp_rr` / `x64_cmp_rr` | Yes | 176 | 0 |
| 38 | `ax_x64_cmp_rm` / `x64_cmp_rm` | Yes | 168 | 0 |
| 39 | `ax_x64_cmp_mr` / `x64_cmp_mr` | Yes | 168 | 0 |
| 40 | `ax_x64_cmp_ri` / `x64_cmp_ri` | Yes | 224 | 9 |
| 41 | `ax_x64_test_rr` / `x64_test_rr` | Yes | 176 | 0 |
| 42 | `ax_x64_test_rm` / `x64_test_rm` | Yes | 168 | 0 |
| 43 | `ax_x64_test_ri` / `x64_test_ri` | Yes | 224 | 0 |
| 44 | `ax_x64_imul_rr` / `x64_imul_rr` | Yes | 132 | 0 |
| 45 | `ax_x64_imul_rm` / `x64_imul_rm` | Yes | 126 | 0 |
| 46 | `ax_x64_mul_r` / `x64_mul_r` | Yes | 64 | 0 |
| 47 | `ax_x64_mul_m` / `x64_mul_m` | Yes | 32 | 0 |
| 48 | `ax_x64_cqo` / `x64_cqo` | Yes | 1 | 0 |
| 49 | `ax_x64_cdq` / `x64_cdq` | Yes | 1 | 0 |
| 50 | `ax_x64_idiv_r` / `x64_idiv_r` | Yes | 64 | 0 |
| 51 | `ax_x64_idiv_m` / `x64_idiv_m` | Yes | 32 | 0 |
| 52 | `ax_x64_div_r` / `x64_div_r` | Yes | 64 | 0 |
| 53 | `ax_x64_div_m` / `x64_div_m` | Yes | 32 | 0 |
| 54 | `ax_x64_neg_r` / `x64_neg_r` | No (isel uses `0 - x`) | 64 | 0 |
| 55 | `ax_x64_neg_m` / `x64_neg_m` | No | 32 | 0 |
| 56 | `ax_x64_not_r` / `x64_not_r` | No (isel uses `-1 - x`) | 64 | 0 |
| 57 | `ax_x64_not_m` / `x64_not_m` | No | 32 | 0 |
| 58 | `ax_x64_shl_rcl` / `x64_shl_rcl` | Yes | 64 | 0 |
| 59 | `ax_x64_shl_ri` / `x64_shl_ri` | Yes | 384 | 0 |
| 60 | `ax_x64_shr_rcl` / `x64_shr_rcl` | Yes | 64 | 0 |
| 61 | `ax_x64_shr_ri` / `x64_shr_ri` | Yes | 384 | 0 |
| 62 | `ax_x64_sar_rcl` / `x64_sar_rcl` | Yes | 64 | 0 |
| 63 | `ax_x64_sar_ri` / `x64_sar_ri` | Yes | 384 | 0 |
| 64 | `ax_x64_setcc_r` / `x64_setcc_r` | Yes | 256 | 0 |
| 65 | `ax_x64_setcc_m` / `x64_setcc_m` | Yes | 96 | 0 |
| 66 | `ax_x64_jcc` / `x64_jcc` | Yes | 112 | 0 |
| 67 | `ax_x64_jcc_sym` / `x64_jcc_sym` | No (branches use `jcc` + fixup) | 16 | 0 |
| 68 | `ax_x64_jmp` / `x64_jmp` | Yes | 8 | 0 |
| 69 | `ax_x64_jmp_sym` / `x64_jmp_sym` | No (jumps use `jmp` + fixup) | 1 | 0 |
| 70 | `ax_x64_call` / `x64_call` | Yes | 8 | 0 |
| 71 | `ax_x64_call_sym` / `x64_call_sym` | Yes | 1 | 0 |
| 72 | `ax_x64_call_r` / `x64_call_r` | Yes | 16 | 16 |
| 73 | `ax_x64_call_m` / `x64_call_m` | Yes | 40 | 40 |
| 74 | `ax_x64_jcc8` / `x64_jcc8` | Yes | 80 | 0 |
| 75 | `ax_x64_jmp8` / `x64_jmp8` | Yes | 5 | 0 |
| 76 | `ax_x64_ret` / `x64_ret` | Yes | 1 | 0 |
| 77 | `ax_x64_push_r` / `x64_push_r` | Yes | 16 | 0 |
| 78 | `ax_x64_push_m` / `x64_push_m` | Yes | 40 | 0 |
| 79 | `ax_x64_pop_r` / `x64_pop_r` | Yes | 16 | 0 |
| 80 | `ax_x64_pop_m` / `x64_pop_m` | Yes | 40 | 0 |
| 81 | `ax_x64_int3` / `x64_int3` | Yes | 1 | 0 |
| **Total** | **81 / 81 entry points (76 emitters + 5 mem ctors)** | **71 / 71 (100%)** | **10,211** | **154** |

---

## Mutation Verification (`encode_tables_current.test`)

Mutating 1 byte in `tests/encode/encode_tests.inc`, 1 byte in `tests/encode/axiom/gnu_as_vectors.ax`, or 1 byte in `compiler/target/x64/encode.ax` inside `build-snap-T143` causes `encode/encode_tables_current.test` to fail immediately:

```text
=== Mutated 1 byte in build-snap-T143/tests/encode/encode_tests.inc (exit=1) ===
FAIL    encode/encode_tables_current.test: exit code 1, expected 0; stderr: FAIL: D:\projects\compiler\new lang\build-snap-T143\tests\encode\encode_tests.inc is out of date with tools/gen_encode_tests.py / GNU as.
Run `python tools/gen_encode_tests.py` to regenerate.
TOTAL 1 PASS 0 FAIL 1 SKIP 0 XFAIL 0

=== Mutated 1 byte in build-snap-T143/tests/encode/axiom/gnu_as_vectors.ax (exit=1) ===
FAIL    encode/encode_tables_current.test: exit code 1, expected 0; stderr: FAIL: verbatim copy of compiler/target/x64/encode.ax in D:\projects\compiler\new lang\build-snap-T143\tests\encode\axiom\gnu_as_vectors.ax does not match compiler/target/x64/encode.ax on disk.
FAIL: D:\projects\compiler\new lang\build-snap-T143\tests\encode\axiom\gnu_as_vectors.ax is out of date with tools/gen_encode_tests.py / GNU as.
TOTAL 1 PASS 0 FAIL 1 SKIP 0 XFAIL 0

=== Mutated 1 byte in build-snap-T143/compiler/target/x64/encode.ax (exit=1) ===
FAIL    encode/encode_tables_current.test: exit code 1, expected 0; stderr: FAIL: verbatim copy of compiler/target/x64/encode.ax in D:\projects\compiler\new lang\build-snap-T143\tests\encode\axiom\gnu_as_vectors.ax does not match compiler/target/x64/encode.ax on disk.
FAIL: D:\projects\compiler\new lang\build-snap-T143\tests\encode\axiom\gnu_as_vectors.ax is out of date with tools/gen_encode_tests.py / GNU as.
TOTAL 1 PASS 0 FAIL 1 SKIP 0 XFAIL 0

=== Restored all files (exit=0) ===
TOTAL 1 PASS 1 FAIL 0 SKIP 0 XFAIL 0
```

---

## Follow-ups

Widening the GNU `as` oracle table exposed **4 classes of discrepancies** (present identically in both `bootstrap/axiom0/src/target/x64/encode/encode.c` and `compiler/target/x64/encode.ax`). All 154 affected vectors are retained in `tests/encode/encode_tests.inc` and `tests/encode/axiom/gnu_as_vectors.ax` and annotated with `// xfail: <task>`:

| Follow-up Task ID | Entry Points Affected | Vectors | Representative Instruction | Expected (GNU `as`) | Actual (`encode.c` & `encode.ax`) | Root Cause |
|---|---|---:|---|---|---|---|
| `AX0-FIX-ENC-LEA-SYM-REX` | `ax_x64_lea_sym`, `x64_lea_sym` (`dst` $\in$ `r8..r15`) | 8 | `leaq 0(%rip), %r8`<br>`leaq 0(%rip), %r15` | `4c 8d 05 00 00 00 00`<br>`4c 8d 3d 00 00 00 00` | `49 8d 05 00 00 00 00`<br>`49 8d 3d 00 00 00 00` | **Real encoding bug**: `encode.c:154` and `encode.ax:743` call `emit_rex_rr(sec, 8, AX_REG_NONE, dst)` passing `dst` in `rm` (`REX.B = 0x49`) instead of `reg` (`REX.R = 0x4C`), even though `dst` is encoded in `ModRM.reg` (`0x05 \| ((dst & 7) << 3)`). For `r8..r15`, this silently loads into `rax..rdi`. |
| `AX0-FIX-ENC-MOVX-REX` | `ax_x64_movzx_rr`, `ax_x64_movsx_rr`, `x64_movzx_rr`, `x64_movsx_rr` (`src_sz == 1`, `sz` $\in \{2,4\}$, `dst` $\in$ `0..7`, `src` $\in$ `spl..dil`) | 36 | `movzbw %spl, %ax`<br>`movzbl %dil, %eax`<br>`movsbw %bpl, %ax`<br>`movsbl %sil, %eax` | `66 40 0f b6 c4`<br>`40 0f b6 c7`<br>`66 40 0f be c5`<br>`40 0f be c6` | `66 0f b6 c4`<br>`0f b6 c7`<br>`66 0f be c5`<br>`0f be c6` | **Real encoding bug**: `encode.c:122,136` and `encode.ax:688,712` call `emit_rex_rr(sec, sz, dst, src)` with `sz` (`2` or `4`) instead of accounting for `src_sz == 1`. When `sz != 8`, `dst < 8`, and `src` $\in \{4..7\}$, the mandatory `0x40` REX prefix is omitted, encoding `ah/ch/dh/bh` instead of `spl/bpl/sil/dil`. (Also note: `movsx_{rr,rm}` only implements `src_sz` $\in \{1, 2\}$ and lacks `0x63` `movslq` for `src_sz == 4`.) |
| `AX0-FIX-ENC-ALU-RAX-IMM8` | `ax_x64_{add,or,and,sub,xor,cmp}_ri`, `x64_{add,or,and,sub,xor,cmp}_ri` (`sz` $\in \{2,4,8\}$, `dst == RAX`, `imm` $\in [-128, 127]$) | 54 | `addw $0, %ax`<br>`addl $127, %eax`<br>`addq $-128, %rax`<br>`cmpq $0, %rax` | `66 83 c0 00`<br>`83 c0 7f`<br>`48 83 c0 80`<br>`48 83 f8 00` | `66 05 00 00`<br>`05 7f 00 00 00`<br>`48 05 80 ff ff ff`<br>`48 3d 00 00 00 00` | **Suboptimal length**: `encode.c:178` (`DEF_ALU`) and `encode.ax:836` (`emit_alu_ri`) check `if (dst == AX_REG_RAX)` before `else if (imm >= -128 && imm <= 127)`, emitting the 2/4-byte accumulator immediate form (`05/0D/25/2D/35/3D`) instead of the shorter sign-extended `imm8` form (`83 /ext ib`) chosen by GNU `as`. |
| `AX0-FIX-ENC-CALL-REXW` | `ax_x64_call_r`, `ax_x64_call_m`, `x64_call_r`, `x64_call_m` | 56 | `callq *%rax`<br>`callq *%r8`<br>`callq *(%rax)`<br>`callq *(%r12)` | `ff d0`<br>`41 ff d0`<br>`ff 10`<br>`41 ff 14 24` | `48 ff d0`<br>`49 ff d0`<br>`48 ff 10`<br>`49 ff 14 24` | **Redundant `REX.W`**: `encode.c:319,324` and `encode.ax:1063,1073` pass `sz = 8` instead of `sz = 4` to `emit_rex_rr`/`emit_rex_rm` (unlike `push_m`/`pop_m`). Near indirect `CALL r/m64` (`FF /2`) defaults to 64-bit operand size in 64-bit mode without `REX.W`. |

---

## Verification

- ** Snapshot & C builds (`gcc` 16.1.0 and `clang` 22.1.4)**:
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T143`
  - `cmake -S build-snap-T143/bootstrap/axiom0 -B build-snap-T143/build -G Ninja -DCMAKE_C_COMPILER=gcc && cmake --build build-snap-T143/build` -> 0 warnings, 0 errors.
  - `cmake -S build-snap-T143/bootstrap/axiom0 -B build-snap-T143/build-clang -G Ninja -DCMAKE_C_COMPILER=clang && cmake --build build-snap-T143/build-clang` -> 0 warnings, 0 errors.
- **`encode/` test filter**:
  - `python build-snap-T143/tools/axtest.py --compiler build-snap-T143/build/axiom0.exe --root build-snap-T143 --filter encode/`
  - Result: `TOTAL 14 PASS 14 FAIL 0 SKIP 0 XFAIL 0`
- **Full test suite (`-j 1`)**:
  - `python build-snap-T143/tools/axtest.py --compiler build-snap-T143/build/axiom0.exe --root build-snap-T143 -j 1`
  - Result: `TOTAL 2693 PASS 2692 FAIL 1 SKIP 0 XFAIL 0` (the 1 failure is an unrelated pre-existing 600s timeout on `selfhost/typeck/qa_typeck_b.ax [interp]` under unoptimized `-g` `axiom0.exe`; `qa_typeck_b.ax [native]` and `[native-O1]` pass).

## Files changed

- `tools/gen_encode_tests.py`
- `tests/encode/encode_tests.inc`
- `tests/encode/axiom/gnu_as_vectors.ax`
- `tests/encode/encode_tables_current.test`

STATUS: COMPLETE round=0
