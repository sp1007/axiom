# T458a QA Report (Round 0) — E12.2 Float Intrinsics: Registration, MIR, Oracle & Native Lowering

## Summary
Independent QA gate for **T458a** (`SPEC-41 AXS-FLT-026`, `ADR-0049`). Audited all 14 modified compiler files, existing test suites, and T458 native catch-up; added a 3-mode + `-O2` QA adversarial test (`tests/mir/float_intrinsics/qa_adversarial.ax`); verified snapshot parity, targeted suites, live mutation spot-proof, `bundles_current.test`, `taskgate.py`, and repo hygiene. All checks pass with zero regressions and zero weak-native entries in task tests.

## Code & Spec Audit
1. **Intrinsic Registration (`compiler/types/types.ax`, `compiler/types/mod.ax`)**:
   - Confirmed `INTR_OP_TO_BITS` (18), `INTR_OP_FROM_BITS` (19), `INTR_OP_SQRT` (20), `INTR_OP_ABS` (21), `INTR_OP_COPYSIGN` (22), float width tags `INTR_WIDTH_F32` (13), `INTR_WIDTH_F64` (14), `INTR_WIDTH_SUFFIXED_TABLE = 2u8` (float-only `_f32`/`_f64`), and `'U'` (`85u8`) unsigned-int-of-float-width signature token (`u32` for `f32`, `u64` for `f64`).
   - Verified wrong suffixes (`sqrt_i32`, `rotate_left_f64`), wrong signatures (including `i64`/`usize` mismatches and generic params), and all 10 derived op names (`floor_f64`, `ceil_f64`, `fma_f64`, etc.) are rejected with `AX_TYPE_UNKNOWN_INTRINSIC`.
2. **MIR & Verifier (`compiler/mir/{mir,mod,builder}.ax`, `compiler/verify/verifier.ax`)**:
   - Confirmed `MIR_CAST_FLOAT_BITS = 8u8` (disjoint from `VERIFY_CAST_UNSIZE = 7u8`), `MIR_UNOP_SQRT = 3u8`, `MIR_UNOP_FABS = 4u8`, text printer/parser support, `copysign` bit-cast + integer mask expansion, and discarded-call (`!has_dest`) temp destination handling.
   - Confirmed `verify_cast_ok` restricts `FloatBits` strictly to same-width `f32 <-> u32` or `f64 <-> u64` (rejecting unequal widths and signed integer endpoints) and restricts `Sqrt`/`Fabs` to float operands.
3. **Interpreter (`compiler/interp/interp.ax`)**:
   - Confirmed `MIR_UNOP_SQRT`, `MIR_UNOP_FABS`, and `MIR_CAST_FLOAT_BITS` dispatch through `sf_intrinsic`; removed divergent name-based float dispatch (`float_intrinsic_width` / `sf_intrinsic_kind`) from `eval_core_intrinsic`; identity `FloatConvert` (`f32 -> f32` / `f64 -> f64`) preserves bit patterns.
4. **Optimizer (`compiler/opt/{dce.ax,optir/mod.ax,scalar/mod.ax}`)**:
   - Confirmed `FloatBits`, `Sqrt`, and `Fabs` are treated as pure and non-foldable; `TY_F32`/`TY_F64`/`MIR_CONST_FLOAT` SSA values set `has_fp_hazard = true` in range analysis; identity cast folding in `scalar_run_inst_combine` is restricted to `MIR_CAST_INT_TO_INT` so `FloatBits` round-trips are never folded (preserving sNaN payloads).
5. **LIR & x64 Codegen (`compiler/lir/{lir,mod,builder}.ax`, `compiler/target/x64/isel.ax`)**:
   - Confirmed `LIR_INST_FBITCAST = 105u8` lowers via `MOVD` (32-bit, zero-extending GPR) / `MOVQ` (64-bit), `LIR_INST_FSQRT` via `SQRTSS`/`SQRTSD`, and `LIR_INST_FABS` via sign-bit mask `ANDPS`/`ANDPD` (preserving NaN/sNaN payloads).
6. **Catch-up & Scope Hygiene**:
   - `native-after: T458a` scan across `tests/`: **0 matches**.
   - `tests/mir/float_interp/intrinsics.ax`: retains the 10 derived operations for T460.
   - `git diff --stat -- docs/ bootstrap/axiom0/`: empty (no out-of-scope edits); no float usage introduced inside `compiler/`.

## QA Adversarial Test
Added `tests/mir/float_intrinsics/qa_adversarial.ax` (3-mode `interp` / `native -O0` / `native -O1` + explicit `-O2` native check, `WEAK-NATIVE 0`, exact `// stdout:`):
- Constant-operand & chained `FloatBits` round-trips on `f32`/`f64` sNaN bit patterns (`0x7F800001u32`, `0x7FF0000000000001u64`) verifying no folding or quieting.
- `to_bits_f32` widened to `u64` on bit-31-set inputs (`-0.0`, `-sNaN`) verifying `MOVD` zero-extends upper 32 bits cleanly.
- Identity `FloatConvert` (`as f32` / `as f64`) preserving sNaN and `-0.0` bit patterns.
- Dual-sNaN `copysign` and nested `abs(abs(snan))` preserving exact payload and quiet-bit=0.
- `sqrt(-0.0) == -0.0` bit-exact and `1.0 / sqrt(-0.0) == -inf`, plus largest subnormal (`0x007FFFFFu32` -> `0x1FFFFFFFu32`, `0x000FFFFFFFFFFFFFu64` -> `0x1FFFFFFFFFFFFFFFu64`) and max finite (`0x7F7FFFFFu32` -> `0x5F7FFFFFu32`, `0x7FEFFFFFFFFFFFFFu64` -> `0x5FEFFFFFFFFFFFFFu64`) `sqrt`.
- Discarded-result calls of all 5 intrinsics with side-effecting arguments verifying DCE preserves argument side effects (`side_cnt == 10`).
- Loop-carried alternating `from_bits` / `abs` / `copysign` / `to_bits` across backedges preserving positive sNaN bits.

## Independent Verification (inside `build-snap-T458a/`)
- **Snapshot Integrity**:
  - `build-snap-T458a/build/axiomc2.exe` SHA256 = `ef0a08fca39d09cb0bab74748f24c1b4e937d474d6df60f3b3cccd0dee94c830` (matches report).
  - All 14 modified `compiler/` files verified `14/14 byte-identical` between main repo and `build-snap-T458a/`.
- **Targeted Suites** (`--filter mir/float_intrinsics --filter ui/float_intrinsics --filter mir/float_interp --filter opt/float_strict --no-cache -j 2 --verbose`):
  - `TOTAL 49 PASS 49 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0` (`exit=0`).
- **Explicit `-O2` Native Check** (`build/axiomc2.exe build -O2 tests/mir/float_intrinsics/qa_adversarial.ax`):
  - `exit=0`, exact stdout match (`10 2139095041 9218868437227405313 4286578689 2147483648 536870911 2305843009213693951 1602224127 6913025428013711359`).
- **Live Mutation Spot-Proof** (inside `build-snap-T458a/tests/mir/float_intrinsics/qa_adversarial.ax` only):
  - Mutated expected stdout last digit (`...359` -> `...358`) -> all 3 modes (`interp`, `native`, `native-O1`) FAILED (`TOTAL 3 PASS 0 FAIL 3`, `exit=1`).
  - Restored byte-identical -> all 3 modes PASSED (`TOTAL 3 PASS 3 FAIL 0`, `WEAK-NATIVE 0`, `exit=0`).
- **Selfhost Bundles Check** (`--filter bundles_current --no-cache -j 2 --verbose`):
  - `TOTAL 34 PASS 34 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0` (`exit=0`).
- **Taskgate** (`python tools/taskgate.py --task T458a --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T458a.json`):
  - `TASKGATE T458a exit=0`
  - `axtest`: `TOTAL 1208 PASS 1194 FAIL 0 SKIP 14 XFAIL 0`
  - `WEAK-NATIVE`: 15 in the run; **0 in the task's own/changed tests**
  - `BASELINE OK`
  - `archcheck`: `clean (exit 0)` (`235 files scanned, 0 violations`)
  - `smoke-check (tests/smoke.list)`: `OK`
- **Main Repo Hygiene**:
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T458a`: 0 `REFUSED` (`exit=0`).
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK` (`exit=0`).

## Files changed
- `tests/mir/float_intrinsics/qa_adversarial.ax`
- `_workspaces/reports/T458a-qa.md`

## Verdict
VERDICT: PASS round=0
