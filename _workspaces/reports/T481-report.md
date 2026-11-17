# T481 Implementation Report — Fix Native Saturating Integer Arithmetic

STATUS: COMPLETE round=0

## Summary

Implemented native (`-O0` and `-O1`) code generation for `MIR_BINOP_SAT_ADD` (`20`), `MIR_BINOP_SAT_SUB` (`21`), and `MIR_BINOP_SAT_MUL` (`22`) across all ten 8..64-bit integer widths (`u8`, `u16`, `u32`, `u64`, `usize`, `i8`, `i16`, `i32`, `i64`, `isize`) per `SPEC-40` (`AXS-INT-023`) and `REQ-LIR-007`, and converted unknown `MIR_BINOP_*` codes in `compiler/lir/builder.ax` from a silent `LIR_INST_ADD` fallback into an explicit internal compiler error (`AX_ICE_INTERNAL` / null `LirBody` aborting codegen).

## Root Cause & Design

1. **Root cause**: `lower_binop` in `compiler/lir/builder.ax` ended with `_ => LIR_INST_ADD` without arms for `MIR_BINOP_SAT_ADD` (`20`), `MIR_BINOP_SAT_SUB` (`21`), or `MIR_BINOP_SAT_MUL` (`22`). Every native `saturating_add`, `saturating_sub`, and `saturating_mul` call silently lowered to two's-complement wrapping addition (`LIR_INST_ADD`), corrupting both narrow (`u8`, `u16`, `u32`, `i8`, `i16`, `i32`) and pointer/64-bit (`u64`, `usize`, `i64`, `isize`) widths.
2. **Explicit LIR expansion (`lower_saturating_binop`)**:
   - Kept LIR instruction opcodes and x64 isel minimal by expanding `MIR_BINOP_SAT_ADD/SUB/MUL` inside `compiler/lir/builder.ax` using existing `LIR_INST_ADD/SUB/MUL` + `LIR_INST_{U,S}{ADD,SUB,MUL}_OVERFLOW` + branchless mask selection (`mask_ovf = 0 - ovf`, `wrap ^ ((sat ^ wrap) & mask_ovf)`).
   - **Narrow constant & upper-bit cleanliness**: `compiler/opt/const_fold.ax` masks folded narrow constants (`-1i8` stored as `0xFFu64`), and narrowing casts can leave dirty upper bits in registers. `lb_norm_int_const` normalizes `MIR_OP_CONST` integers to canonical 64-bit sign/zero-extended values, and `lower_sat_operand` emits `LIR_INST_BIT_OR(raw, 0)` at `int_ty_v` for `< 64`-bit non-constant operands so `isel_emit_trunc` establishes clean 64-bit sign/zero-extension prior to overflow flags and sign extraction.
   - **Unsigned saturation**:
     - `SatAdd` / `SatMul`: saturates to `uN.MAX` (`0xFF`, `0xFFFF`, `0xFFFF_FFFF`, `0xFFFF_FFFF_FFFF_FFFF`) when unsigned overflow (`CF`) is `1`.
     - `SatSub`: saturates to `0` (`wrap & (ovf - 1)`) when unsigned borrow (`CF`) is `1`.
   - **Signed saturation**:
     - Since `~iN.MAX == sign_ext64(iN.MIN)` in 64-bit two's complement across all widths (`8, 16, 32, 64`), `SAR(sign_src, 63) ^ iN.MAX` yields `iN.MAX` when `sign_src >= 0` and `iN.MIN` when `sign_src < 0`.
     - For `SatAdd` and `SatSub`, signed overflow (`OF = 1`) occurs only when the mathematical result overflows in the direction of `lhs`'s sign (`pos + pos > MAX`, `neg + neg < MIN`, `pos - neg > MAX`, `neg - pos < MIN`, including `0 - MIN > MAX` and `MIN - 1 < MIN`), so `sign_src = lhs`.
     - For `SatMul`, true mathematical sign on non-zero overflow is the sign of `lhs ^ rhs` (handling `MIN * -1 -> +MAX`, `MIN * MIN -> +MAX`, `MAX * -2 -> MIN`), so `sign_src = lhs ^ rhs`.
3. **Explicit ICE on unknown `MIR_BINOP_*` (`has_ice` + `AX_ICE_INTERNAL`)**:
   - Replaced `lower_binop` with `lower_binop_checked`, setting `b.has_ice = true` on any unrecognized `MIR_BINOP_*` (and similarly in `MIR_RVALUE_OVERFLOWS_BINARY_OP` and unsupported `MIR_BINOP_SAT_*` widths such as 16-byte `i128`/`u128` prior to `T453`).
   - `lir_lower_ext_opt` returns `0 as *mut LirBody` when `b.has_ice` is `true`, and `compiler/backend/session.ax` emits `AX_ICE_INTERNAL` (`130`) via `backend_report_ice` whenever LIR/MI/MC/ObjModel lowering fails without a prior error diagnostic.
   - Added unit coverage `test_unknown_binop_ice_and_sat_lowering` in `tests/selfhost/lir/qa_lir_seam_edge.ax.in`.

## Test Coverage & Verification

1. **Native saturating test suite (`tests/run/saturating_native/*.ax`)**:
   - Created 10 end-to-end test files (`u8`, `u16`, `u32`, `u64`, `usize`, `i8`, `i16`, `i32`, `i64`, `isize`) running in `modes: interp native` (`[interp]`, `[native]`, `[native-O1]`) with exact `SPEC-40`-derived `// stdout:` expectations (`WEAK-NATIVE 0`, `0` CR bytes).
   - Covers `6x6` unsigned (`0, 1, 2, HALF, MAX-1, MAX`) and `9x9` signed (`MIN, MIN+1, -2, -1, 0, 1, 2, MAX-1, MAX`) runtime matrices across `saturating_add`, `saturating_sub`, and `saturating_mul`, plus `MIR_OP_CONST` constant-operand folding/lowering paths and dirty upper-bit narrowing-cast inputs (`0xDEAD_BEEFu32 as T`).
   - Verified pre-T481 `axiomc2.exe` failed `20/20` native legs (`[native]` and `[native-O1]`), and post-T481 `axiomc2.exe` (`sha256=9c4385babf21531d`, `8117248` bytes) + self-hosted `axiomc1.exe` (`sha256=9caa2acbc96325a5`, `16145920` bytes) pass `31/31` legs (`run/saturating_native` + `run/int128_interp/saturating.ax` `[interp]`, `FAIL 0`, `WEAK-NATIVE 0`).
2. **Selfhost bundles & full gate suite (`build-snap-T481`)**:
   - Regenerated the 5 affected selfhost generators (`abi`, `lir`, `backend`, `driver --refresh-goldens`, `obj_link_driver --refresh-goldens`) against `build-snap-T481/build/axiomc2.exe`; verified all 36 `tests/selfhost/**/gen_*.py --check` exit `0` with `0` diffs and `0` stderr.
   - Ran cache-warming verification suite in `build-snap-T481`:
     `TOTAL 206 PASS 192 FAIL 0 SKIP 14 XFAIL 0` (`WEAK-NATIVE 0`), including `selfhost/obj_link_driver/axiomc_e2e.test` (`120/120` corpus programs equal).
3. **1-byte mutation proof**:
   - Mutated 1 byte at offset `158` (`255` -> `254` in `// stdout:`) in `build-snap-T481/tests/run/saturating_native/u8_saturating.ax` and ran `axtest.py --no-cache -v -j 2`: confirmed all 3 legs (`[interp]`, `[native]`, `[native-O1]`) failed (`TOTAL 3 PASS 0 FAIL 3`), then restored `build-snap-T481` via `taskctl.py snapshot T481`.

## Files changed

- compiler/backend/session.ax
- compiler/lir/builder.ax
- tests/run/saturating_native/i16_saturating.ax
- tests/run/saturating_native/i32_saturating.ax
- tests/run/saturating_native/i64_saturating.ax
- tests/run/saturating_native/i8_saturating.ax
- tests/run/saturating_native/isize_saturating.ax
- tests/run/saturating_native/u16_saturating.ax
- tests/run/saturating_native/u32_saturating.ax
- tests/run/saturating_native/u64_saturating.ax
- tests/run/saturating_native/u8_saturating.ax
- tests/run/saturating_native/usize_saturating.ax
- tests/selfhost/abi/qa_abi_lir_lower.ax
- tests/selfhost/backend/qa_backend_diff_lir_a.ax
- tests/selfhost/backend/qa_backend_diff_lir_b.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax
- tests/selfhost/backend/qa_backend_edge.ax
- tests/selfhost/backend/qa_backend_unit.ax
- tests/selfhost/driver/qa_driver_commands_a.ax
- tests/selfhost/driver/qa_driver_commands_b.ax
- tests/selfhost/driver/qa_driver_inspect_diff_a.ax
- tests/selfhost/driver/qa_driver_inspect_diff_b.ax
- tests/selfhost/lir/qa_lir_from_ax_a.ax
- tests/selfhost/lir/qa_lir_from_ax_b.ax
- tests/selfhost/lir/qa_lir_from_ax_c.ax
- tests/selfhost/lir/qa_lir_from_ax_d.ax
- tests/selfhost/lir/qa_lir_from_ax_e.ax
- tests/selfhost/lir/qa_lir_from_mir.ax
- tests/selfhost/lir/qa_lir_seam_edge.ax
- tests/selfhost/lir/qa_lir_seam_edge.ax.in
- tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax
