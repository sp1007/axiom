# T458a Report — E12.2 Float Intrinsics: Registration, MIR, Oracle & Native Lowering

## Summary
Implemented the five minimal IEEE-754 float intrinsics of `SPEC-41 AXS-FLT-026` / `ADR-0049` (`to_bits`, `from_bits`, `sqrt`, `abs`, `copysign` with `_f32` and `_f64` suffixes) end-to-end across type-checking, MIR, verifier, interpreter, optimizer, LIR, and x86-64 native codegen, completed T458 native catch-up by removing all `native-after: T458a` markers, and added comprehensive run, `-O2`, golden MIR, verifier-reject, and UI diagnostic tests.

### Key Changes
1. **Intrinsic Registration (`compiler/types/types.ax`, `compiler/types/mod.ax`)**
   - Added `INTR_OP_TO_BITS` (18), `INTR_OP_FROM_BITS` (19), `INTR_OP_SQRT` (20), `INTR_OP_ABS` (21), `INTR_OP_COPYSIGN` (22), and float width tags `INTR_WIDTH_F32` (13), `INTR_WIDTH_F64` (14).
   - Extended the intrinsic table (`INTR_TABLE_COUNT = 61`) with `INTR_WIDTH_SUFFIXED_TABLE = 2u8` (float-only `_f32`/`_f64` suffix resolution) and `'U'` (`85u8`) unsigned-int-of-float-width signature token (`u32` for `f32`, `u64` for `f64`).
   - Rejects wrong suffixes (`sqrt_i32`), integer names with float suffixes (`rotate_left_f64`), wrong signatures, and derived op names (`floor_f64`, `ceil_f64`, etc.) with `AX_TYPE_UNKNOWN_INTRINSIC`.
2. **MIR Representation, Lowering, Printer & Parser (`compiler/mir/mir.ax`, `compiler/mir/mod.ax`, `compiler/mir/builder.ax`)**
   - Added `MIR_UNOP_SQRT = 3u8`, `MIR_UNOP_FABS = 4u8`, and `MIR_CAST_FLOAT_BITS = 8u8` (disjoint from `VERIFY_CAST_UNSIZE = 7u8`).
   - Added MIR text printing and parsing for `(FloatBits)`, `sqrt(...)`, `fabs(...)`, and `f32`/`f64` types.
   - Lowered `to_bits`/`from_bits` -> `MIR_CAST_FLOAT_BITS`, `sqrt` -> `MIR_UNOP_SQRT`, `abs` -> `MIR_UNOP_FABS`, and inline-expanded `copysign` into two `MIR_CAST_FLOAT_BITS` casts + unsigned `&`/`|` bit masks + `MIR_CAST_FLOAT_BITS` back; handled discarded intrinsic statement calls (`!has_dest`) via temp destination allocation.
3. **MIR Verifier (`compiler/verify/verifier.ax`)**
   - Enforced `MIR_CAST_FLOAT_BITS` strictly between same-width float and unsigned int (`f32 <-> u32`, `f64 <-> u64`) and rejected width mismatches or signed integer endpoints.
   - Enforced `MIR_UNOP_SQRT` and `MIR_UNOP_FABS` strictly on float operands; added verifier MIR parser support for `(FloatBits)`, `sqrt(...)`, `fabs(...)`, `f32`, `f64`.
4. **Interpreter (`compiler/interp/interp.ax`)**
   - Evaluated `MIR_UNOP_SQRT`, `MIR_UNOP_FABS`, and `MIR_CAST_FLOAT_BITS` via the existing `sf_intrinsic` oracle kernel.
   - Removed the divergent name-based float dispatch (`float_intrinsic_width` / `sf_intrinsic_kind` branch) from `eval_core_intrinsic`.
   - Fixed pre-existing identity `MIR_CAST_FLOAT_CONVERT` (`f32 -> f32` / `f64 -> f64`) in `exec_assign_cast` to preserve bit patterns rather than widening/narrowing across widths (matching `compiler/lir/builder.ax`).
5. **Optimizer (`compiler/opt/dce.ax`, `compiler/opt/optir/mod.ax`, `compiler/opt/scalar/mod.ax`)**
   - Marked `MIR_UNOP_SQRT` and `MIR_UNOP_FABS` pure (and non-foldable) alongside `MIR_RVALUE_CAST`.
   - Marked `TY_F32`/`TY_F64`/`MIR_CONST_FLOAT` SSA values with `has_fp_hazard = true` in range analysis so no integer fast path touches float values.
   - Restricted identity cast folding in scalar opts strictly to `MIR_CAST_INT_TO_INT` so `FloatBits` round-trips are never folded (preserving sNaN payloads).
6. **LIR & x86-64 Codegen (`compiler/lir/lir.ax`, `compiler/lir/mod.ax`, `compiler/lir/builder.ax`, `compiler/target/x64/isel.ax`)**
   - Added `LIR_INST_FBITCAST = 105u8` (in `lir_kind_is_float_unary`, printed as `fbitcast `) and lowered `MIR_CAST_FLOAT_BITS` -> `LIR_INST_FBITCAST`, `MIR_UNOP_SQRT` -> `LIR_INST_FSQRT`, `MIR_UNOP_FABS` -> `LIR_INST_FABS`.
   - Lowered `LIR_INST_FBITCAST` in x64 isel via `MOVD` (32-bit, zero-extending GPR) and `MOVQ` (64-bit) between XMM and GPR; `FSQRT` (`SQRTSS`/`SQRTSD`) and `FABS` (`ANDPS`/`ANDPD` clearing only the sign bit) already preserve NaN/sNaN payloads.
7. **T458 Native Catch-Up & Test Suite**
   - Removed all `// native-after: T458a` markers from all 8 files in `tests/mir/float_interp/*` and `tests/opt/float_strict/*` (`0` remaining across `tests/`).
   - Split the 5 intrinsics (`to_bits`, `from_bits`, `sqrt`, `abs`, `copysign` for `f32`/`f64`, 1,460 oracle vectors) out of `tests/mir/float_interp/intrinsics.ax` into `tests/mir/float_intrinsics/oracle_vectors.ax`, keeping the 10 derived operations in `tests/mir/float_interp/intrinsics.ax` for T460.
   - Added run tests (`interp`, native `-O0`, `-O1`, `-O2`) covering specials/subnormals/qNaN/sNaN bit patterns and float+int register pressure, a golden `--emit=mir` test, 4 verifier reject tests, and 3 UI diagnostic tests.

## Build & Verification (inside `build-snap-T458a/`)
- **Stage-2 Fixed-Point Build** (`python tools/build_axiomc.py --out build --root . --stage 2`):
  - `STAGE1 OK`: `axiomc1.exe` (`34523648` bytes, `sha256=2967c5a97696e83b`)
  - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == ef0a08fca39d09cb0bab74748f24c1b4e937d474d6df60f3b3cccd0dee94c830` (`9237504` bytes)
  - `STAGE0-GUARD OK`: `axiomc1` and `B` produced byte-identical `.exe` on 6 smoke programs (`O1`, incl. `Xin chào thế giới`)
- **Targeted Tests** (`--filter mir/float_intrinsics --filter ui/float_intrinsics --filter mir/float_interp --filter opt/float_strict --no-cache -j 2 --verbose`):
  - `TOTAL 46 PASS 46 FAIL 0 SKIP 0 XFAIL 0`
  - `WEAK-NATIVE 0`
  - Explicit `-O2` verification on `tests/mir/float_intrinsics/oracle_vectors.ax`: `1460 ok` (exit 0)
- **Selfhost Bundles Check** (`--filter bundles_current --no-cache -j 2 --verbose`):
  - `TOTAL 34 PASS 34 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`
- **Taskgate** (`python tools/taskgate.py --task T458a --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T458a.json`):
  - `TASKGATE T458a exit=0`
  - `own`: 24 ids, 46 results, **46 PASS, 0 FAIL**
  - `affected`: 677 ids, 1170 results, **1156 PASS, 0 FAIL, 14 SKIP**
  - `smoke`: 34 ids, 57 results, **57 PASS, 0 FAIL**
  - `total (dedup)`: 700 ids, 1211 results, **1197 PASS, 0 FAIL, 14 SKIP, 0 XFAIL**
  - `WEAK-NATIVE`: 15 in the run; **0 in the task's own/changed tests**
  - `BASELINE OK`
  - `archcheck: clean (exit 0)` (`235 files scanned, 0 violations`)
  - `smoke-check (tests/smoke.list): OK`
- **Hygiene Checks (main repo root)**:
  - `native-after: T458a` scan across `tests/`: 0 matches (`NATIVE_AFTER_T458A_CLEAN`)
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T458a`: 0 `REFUSED`
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`

## Files changed
- `compiler/types/types.ax`
- `compiler/types/mod.ax`
- `compiler/mir/mir.ax`
- `compiler/mir/mod.ax`
- `compiler/mir/builder.ax`
- `compiler/verify/verifier.ax`
- `compiler/interp/interp.ax`
- `compiler/opt/dce.ax`
- `compiler/opt/optir/mod.ax`
- `compiler/opt/scalar/mod.ax`
- `compiler/lir/lir.ax`
- `compiler/lir/mod.ax`
- `compiler/lir/builder.ax`
- `compiler/target/x64/isel.ax`
- `tests/mir/float_interp/casts.ax`
- `tests/mir/float_interp/compare.ax`
- `tests/mir/float_interp/f32_arith.ax`
- `tests/mir/float_interp/f64_arith.ax`
- `tests/mir/float_interp/intrinsics.ax`
- `tests/mir/float_interp/owner007_exec.ax`
- `tests/mir/float_interp/qa_adversarial.ax`
- `tests/opt/float_strict/qa_flow_run.ax`
- `tests/opt/float_strict/strict_run.ax`
- `tests/mir/float_intrinsics/emit_mir.test`
- `tests/mir/float_intrinsics/emit_mir_src.ax`
- `tests/mir/float_intrinsics/oracle_vectors.ax`
- `tests/mir/float_intrinsics/reg_pressure.ax`
- `tests/mir/float_intrinsics/reg_pressure_o2.ax`
- `tests/mir/float_intrinsics/specials_snan_bits.ax`
- `tests/mir/float_intrinsics/specials_snan_o2.ax`
- `tests/mir/float_intrinsics/verify_floatbits_bad_width.mir`
- `tests/mir/float_intrinsics/verify_floatbits_bad_width.test`
- `tests/mir/float_intrinsics/verify_floatbits_bad_width_f64_u32.mir`
- `tests/mir/float_intrinsics/verify_floatbits_bad_width_f64_u32.test`
- `tests/mir/float_intrinsics/verify_floatbits_signed_int.mir`
- `tests/mir/float_intrinsics/verify_floatbits_signed_int.test`
- `tests/mir/float_intrinsics/verify_unop_non_float.mir`
- `tests/mir/float_intrinsics/verify_unop_non_float.test`
- `tests/ui/float_intrinsics/derived_not_intrinsic.ax`
- `tests/ui/float_intrinsics/wrong_signature.ax`
- `tests/ui/float_intrinsics/wrong_suffix.ax`

## Status
STATUS: COMPLETE round=0
