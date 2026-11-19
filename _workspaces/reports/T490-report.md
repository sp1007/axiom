# T490 report

## Summary
Resolved all three baseline failures assigned to T490 (`mir/intrinsics/rotate_u8.ax`, `mir/intrinsics/wrapping_ops.ax`, and `selfhost/hir/qa_hir_desugar_and_drop.ax`) and removed their entries from `_workspaces/baseline-failures.txt`.

### 1. `mir/intrinsics/rotate_u8.ax` and `mir/intrinsics/wrapping_ops.ax`
- **Root cause & responsible commit**: Legitimate MIR lowering change from accepted task **T452** (`commit e0637c50bdd1feaa6790c003ec1c0f19577a124d`, *"T452: E12.1 — Oracle 128-bit evaluator, saturating/bit intrinsics & const folding"*).
  - In `T452`, `mb_intr_materialize` (`compiler/mir/builder.ax`) was deliberately changed to keep `MIR_OP_CONST` arguments inline (`if v.kind == MIR_OP_CONST { ... return out; }`) instead of spilling them into fresh temporary `let` locals, so that constant operands to `@intrinsic` operations reach `-O1` `const_fold.ax` directly (tested by `tests/opt/int128/const_fold_int128.test`).
  - `T452` was gated before `taskgate.py` existed and did not run `tests/mir/intrinsics/*`, leaving the `T134` (`e51e5890`) goldens `rotate_u8.mir` and `wrapping_ops.mir` un-updated.
  - The `TypeInterner` table order did **not** change (`type#2` = `unit`, `type#6` = `i8`, `type#8` = `i32`, `type#11` = `u8`, `type#13` = `u32`, `type#14` = `u64` in both the old and new goldens). Why `axtest.py` reported `type#13` vs expected `type#11` (byte offset 74 in `rotate_u8.mir`) and `type#8` vs expected `type#11` (byte offset 94 in `wrapping_ops.mir`): omitting the materialized constant temporaries (`_2 = const 129; _3 = const 1;` in `rotate_u8.ax`, and `_2 = const 250; _3 = const 10;` in `wrapping_ops.ax`) shifts subsequent local variable indices up by 2, so `let _2:` in `rotate_u8.mir` is now the `u32` (`type#13`) shift-mask temporary (`_2 = const 1 & const 7;`) instead of the `u8` (`type#11`) constant temporary, and `let _3:` in `wrapping_ops.mir` is now the `i32` (`type#8`) `wrapping_sub_i32` result temporary (`_3 = wrapping_sub(const 5, const 7);`) instead of the `u8` (`type#11`) constant temporary.
- **Diff & fix**: Updated `tests/mir/intrinsics/rotate_u8.mir` and `tests/mir/intrinsics/wrapping_ops.mir` to match the post-`T452` inline-`const` MIR output of `axiomc2`:
  - `rotate_u8.mir`: 10 locals (`_0`..`_10`) -> 8 locals (`_0`..`_8`); `_2 = const 129; _3 = const 1;` removed and `const 1` / `const 129` used directly in `_2 = const 1 & const 7;`, `_5 = const 129 << copy _2;`, `_6 = const 129 >> copy _4;`.
  - `wrapping_ops.mir`: 15 locals (`_0`..`_15`) -> 8 locals (`_0`..`_8`); constant temporaries removed and `const` operands passed directly to `wrapping_add(const 250, const 10)`, `wrapping_sub(const 5, const 7)`, `wrapping_mul(const 3, const 4)`, `wrapping_sub(const 0, const 1)`.

### 2. `selfhost/hir/qa_hir_desugar_and_drop.ax` (template `tests/selfhost/hir/qa_hir_desugar_and_drop.ax.in`)
- **Which assertion yielded exit 43**: `verify_case` returns `DIAG_MISMATCH_RC (40) + case_idx` on diagnostic mismatch and `OUTPUT_MISMATCH_RC (10) + case_idx` on HIR dump mismatch. Exit `43` was `DIAG_MISMATCH_RC (40) + 3` (case 3, `synth_unsupported_postfix.ax`).
- **Root cause**: Two accepted tasks made the embedded expectations in `tests/selfhost/hir/qa_hir_desugar_and_drop.ax.in` stale:
  1. **T416** (`commit abb00124`, 2026-11-08): `.await` became a valid postfix expression (`ExprAwait`). Case 3 (`synth_unsupported_postfix.ax`) used `x.await` expecting `error[AX_PARSE_EXPECTED_TOKEN]: Expected field or method name`, whereas the parser now lowers `x.await` to `(ExprAwait (ExprPath ...))` with 0 diagnostics, causing `verify_case(..., 3)` to return `40 + 3 = 43`.
  2. **T164** (`commit a8c458d1`, 2026-11-19, `AX0-FIX-10` one symbol-id space): `assign_prelude_trait_ids` allocates 4 symbol IDs after top-level item collection and `extern` symbols come from the same counter (`next_symbol_v`), shifting body-local symbol IDs (`Param`, `PatBinding`, `ExprPath`) by `+4` in cases 1–3 and `+5` in case 0 (where `extern "C" fn c_puts` takes `@29` instead of `@30000`). `T164` updated the `resolve_hir` templates but missed `hir/qa_hir_desugar_and_drop.ax.in` because it was already listed in `baseline-failures.txt`.
- **Fix**: Updated `CORPUS_DATA` (`[7560]u8` -> `[7541]u8`) and `CORPUS_OFF` in `tests/selfhost/hir/qa_hir_desugar_and_drop.ax.in`:
  - Cases 0–2: updated the expected HIR dumps for the post-`T164` single-counter symbol IDs (`@31..@33` -> `@36..@38` and `@30000` -> `@29` in case 0; `@29..@32` -> `@33..@36` in case 1; `@35..@45` -> `@39..@49` in case 2).
  - Case 3 (`synth_unsupported_postfix.ax`): replaced `x.await` in `pub fn test_await` with an actual invalid postfix `x.+` in `pub fn test_bad` so case 3 continues to test `error[AX_PARSE_EXPECTED_TOKEN]: Expected field or method name` at `synth_unsupported_postfix.ax:4:7` and recovery to `(ExprPath @32)`.

### 3. Baseline file
- Removed `mir/intrinsics/rotate_u8.ax`, `mir/intrinsics/wrapping_ops.ax`, and `selfhost/hir/qa_hir_desugar_and_drop.ax` from `_workspaces/baseline-failures.txt`.

## Files changed
- _workspaces/baseline-failures.txt
- tests/mir/intrinsics/rotate_u8.mir
- tests/mir/intrinsics/wrapping_ops.mir
- tests/selfhost/hir/qa_hir_desugar_and_drop.ax.in

## Tests
- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T490`: refreshed `build-snap-T490` (`HEAD dbc78f5 + 5 changed, 0 deleted file(s) of T490`; 36 selfhost bundle generators, 154 files regenerated).
- `python build-snap-T490/tools/axtest.py --root build-snap-T490 --compiler build-snap-T490/build/axiomc2.exe --build-dir build-snap-T490/build --exclude-requires axiom0-internal --no-cache -j 2 -v mir/intrinsics selfhost/hir/qa_hir_desugar_and_drop.ax`:
  `TOTAL 6 PASS 6 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0` (`mir/intrinsics/assert_panic.ax [mir]`, `mir/intrinsics/rotate_u8.ax [mir]`, `mir/intrinsics/wrapping_ops.ax [mir]`, `selfhost/hir/qa_hir_desugar_and_drop.ax [interp]`, `[native]`, `[native-O1]`).
- `python build-snap-T490/tools/taskgate.py --root build-snap-T490 --task T490 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`:
  - `own`: 3 ids / 3 results (3 PASS, 0 FAIL)
  - `affected`: 6 ids / 10 results (10 PASS, 0 FAIL — `mir/intrinsics/{assert_panic,rotate_u8,wrapping_ops}.ax`, `selfhost/hir/{bundles_current.test,qa_hir_corpus.ax,qa_hir_desugar_and_drop.ax}`)
  - `smoke`: 31 ids / 50 results (50 PASS, 0 FAIL)
  - `total (dedup)`: 37 ids / 60 results (`TOTAL 60 PASS 60 FAIL 0 SKIP 0 XFAIL 0`)
  - `archcheck`: clean (229 files scanned, 0 violations)
  - `WEAK-NATIVE`: 0 in own/changed tests
  - `Baseline`: `BASELINE OK`, `TASKGATE T490 exit=0`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T490`: stages the 4 changed files + report, 0 refused lines.

## Spec deviations
none

## Follow-ups
none

STATUS: COMPLETE round=0
