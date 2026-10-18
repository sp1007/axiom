# T083 Report — Port interpreter + optimizer to Axiom (integration + differential)

## Summary
- Integrated `compiler/interp` (`T083a`) and `compiler/opt` (`T083b`) with the frontend, typechecker/THIR, ownership/capability checker, drop elaborator, and MIR verifier (`T082`) via [`compiler/interp_opt/session.ax`](file:///d:/projects/compiler/new%20lang/compiler/interp_opt/session.ax) and [`compiler/interp_opt/mod.ax`](file:///d:/projects/compiler/new%20lang/compiler/interp_opt/mod.ax):
  - `session_is_valid_const_type` and `session_comptime_check_and_eval`: validates compile-time `const` and `static` item types (`AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP`), normalizes array-length constant evaluation errors (`AX_TYPE_ARRAY_SIZE`), evaluates all `const` items unconditionally via `session_eval_const_expr_into` (`AX_CONST_OVERFLOW`, `AX_CONST_DIV_ZERO`, `AX_CONST_CYCLE`, `AX_CONST_EVAL_LIMIT`) with full `CONST_AGGREGATE` local binding (`session_bind_mir_const_locals`) and signed scalar bit-pattern normalization (`TY_I8`/`TY_I16`/`TY_I32`), and populates `Thir.symbol_consts` with scalar and aggregate constant values.
  - `session_bind_mir_const_locals` and `session_is_host_intrinsic_fn`: binds `MIR_LOCAL_CONST` locals to `CONST_AGGREGATE` symbols in `Thir.symbol_consts` after `-O1` optimization while preserving `_0` (`MIR_LOCAL_RETURN`), `MIR_LOCAL_USER`, mutable locals, and projected/multi-assigned locals by synthesizing dedicated `MIR_LOCAL_CONST` helper locals when needed; filters `@intrinsic` host functions (`heap_alloc`, `stdio`, `write`, etc.) during MIR lowering.
  - `session_opt_body`, `session_interp_opt_fn`, `session_interp_opt_file`, and `session_emit_mir_opt`: executes per-function and per-file MIR building (`mir_build_fn`), pre-optimization structural verification (`verify_mir`), `-O1` MIR optimization (`opt_run_in_arena`: constant folding, dead code elimination, and CFG simplification with optional `--verify-each`), ownership/initialization/capability checking (`session_own_check_body`), drop elaboration (`session_drop_elaborate_body`), post-drop verification (`verify_mir_drop_flags`), and post-`-O1` aggregate constant local binding (`session_bind_mir_const_locals`).
  - `session_run_interp`: builds and verifies `-O0` or `-O1` MIR across a `HirFile` (including `impl` / `Drop` method alias registration in `MirBodyMap`), verifies the `main` entry point (`AX_TYPE_MAIN_MISSING`), and executes the program via `interp_run` with configurable step/call-depth limits (`AX_DRIVER_INTERP_STEP_LIMIT`, `AX_DRIVER_INTERP_STACK_LIMIT`), UB oracle enforcement (`AX_UNSAFE_INTERP_UB`), stdout capture, and panic message reporting.
  - `session_opt_mir_text` and `session_interp_mir_text`: standalone `.mir` text entry points for parsing, verifying, optimizing (`-O1`), printing, and interpreting `.mir` bodies (`AX_VERIFY_MIR_SYNTAX`).
  - `interp_opt_compile`, `interp_opt_run_source`, and `interp_opt_run_and_render_human`: end-to-end virtual-file compilation and execution helpers from source text through parser, resolver, HIR lowerer, typechecker, comptime evaluator, `-O0`/`-O1` MIR optimizer, ownership/drop elaborator, verifier, and MIR interpreter.

## Differential & Unit Test Suite (`tests/selfhost/interp_opt/`)
- [`tests/selfhost/interp_opt/gen_interp_opt_tests.py`](file:///d:/projects/compiler/new%20lang/tests/selfhost/interp_opt/gen_interp_opt_tests.py) generates 7 selfhost test bundles from [`tests/selfhost/interp_opt/harness_unit.ax.in`](file:///d:/projects/compiler/new%20lang/tests/selfhost/interp_opt/harness_unit.ax.in), [`tests/selfhost/interp_opt/harness_mir_opt_diff.ax.in`](file:///d:/projects/compiler/new%20lang/tests/selfhost/interp_opt/harness_mir_opt_diff.ax.in), and [`tests/selfhost/interp_opt/harness_run_diff.ax.in`](file:///d:/projects/compiler/new%20lang/tests/selfhost/interp_opt/harness_run_diff.ax.in):
  1. [`qa_interp_opt_unit.ax`](file:///d:/projects/compiler/new%20lang/tests/selfhost/interp_opt/qa_interp_opt_unit.ax) (`[interp]`, `[native]`, `[native-O1]`): standalone `.mir` unit tests for `session_opt_mir_text` and `session_interp_mir_text` covering constant folding + DCE + CFG simplification (`REQ-OPT-388`), `-O0` vs `-O1` equivalence (`REQ-OPT-387`), observable panic preservation on division by zero, arithmetic overflow, and shift out of range (`REQ-OPT-389`), step-limit enforcement (`AX_DRIVER_INTERP_STEP_LIMIT`), and malformed `.mir` syntax diagnostics (`AX_VERIFY_MIR_SYNTAX`).
  2. [`qa_interp_opt_diff_mir_a.ax`](file:///d:/projects/compiler/new%20lang/tests/selfhost/interp_opt/qa_interp_opt_diff_mir_a.ax) (`[interp]`, `[native]`, `[native-O1]` — 2 cases: `const_fold_run`, `qa_dce_run`): `-O1` optimized MIR differential check and post-drop verification with `verify_each = true`.
  3. [`qa_interp_opt_diff_mir_b.ax`](file:///d:/projects/compiler/new%20lang/tests/selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax) (`[native]`, `[native-O1]` — 22 cases across `tests/opt/*.ax`, `tests/mir/build/*.ax`, and `tests/selfhost/drop/fixtures/*.ax`): full `-O1` optimized MIR differential check and post-drop verification with `verify_each = true`.
  4. [`qa_interp_opt_diff_comptime_a.ax`](file:///d:/projects/compiler/new%20lang/tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_a.ax) (`[interp]`, `[native]`, `[native-O1]` — 2 lightweight cases: `comptime_pos_a`, `overflow_err`): comptime evaluation and diagnostic differential twin (~80s in `[interp]`).
  5. [`qa_interp_opt_diff_comptime_b.ax`](file:///d:/projects/compiler/new%20lang/tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_b.ax) (`[native]`, `[native-O1]` — 19 cases: all 14 comptime fixtures in `tests/ui/comptime/*.ax` and `tests/run/comptime/*.ax` plus 5 QA regression cases for signed comptime ops, 64-bit/intermediate/shift overflow diagnostics, and chained aggregate constants / return-by-value / mutable local copies): verifies exact diagnostic codes (`AX_CONST_CYCLE`, `AX_CONST_DIV_ZERO`, `AX_CONST_EVAL_LIMIT`, `AX_CONST_OVERFLOW`, `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP`, `AX_TYPE_ARRAY_SIZE`) and `-O0`/`-O1` execution parity against `axiom0`.
  6. [`qa_interp_opt_diff_run_a.ax`](file:///d:/projects/compiler/new%20lang/tests/selfhost/interp_opt/qa_interp_opt_diff_run_a.ax) (`[interp]`, `[native]`, `[native-O1]` — 2 cases: `qa_dce_run`, `missing_main`): `-O0` vs `-O1` execution and missing-`main` diagnostic differential twin.
  7. [`qa_interp_opt_diff_run_b.ax`](file:///d:/projects/compiler/new%20lang/tests/selfhost/interp_opt/qa_interp_opt_diff_run_b.ax) (`[native]`, `[native-O1]` — 21 cases spanning `tests/opt/*.ax`, `tests/mir/build/*.ax`, `tests/selfhost/drop/fixtures/*.ax`, and negative runtime panic / UB / limit fixtures): verifies `-O0` and `-O1` semantic equivalence (exit code, stdout, panic message, and diagnostic code) on defined programs, destructors, division-by-zero traps, arithmetic overflow traps, bounds-check traps, null-pointer dereference UB (`AX_UNSAFE_INTERP_UB`), step limits (`AX_DRIVER_INTERP_STEP_LIMIT`), and stack limits (`AX_DRIVER_INTERP_STACK_LIMIT`).

## Corpus Differential Counts
- **`-O1` MIR optimization + ownership + drop + verifier corpus (`22` fixtures)**:
  - `3 / 3` fixtures in `tests/opt/*.ax` (`const_fold_run`, `qa_dce_run`, `qa_edge_cases_run`): 100% match on `-O1` optimized MIR and 0 ownership/verifier diagnostics (`REQ-OPT-388`).
  - `9 / 9` fixtures in `tests/mir/build/*.ax` (`bitnot`, `calls`, `div_assert`, `first_mir`, `mul_assert`, `qa_eval_order`, `shift_assert`, `short_circuit`, `unary_neg_assert`): 100% match on `-O1` optimized MIR and 0 ownership/verifier diagnostics.
  - `10 / 10` fixtures in `tests/selfhost/drop/fixtures/*.ax` (`d01`–`d07`, `d09`–`d11`): 100% match on `-O1` optimized MIR and 0 ownership/verifier diagnostics.
- **Comptime evaluation & diagnostic corpus (`19` fixtures)**:
  - `10 / 10` negative fixtures (`7` in `tests/ui/comptime/*.ax` + `3` QA regression cases `qa_overflow_64bit_err`, `qa_overflow_interm_err`, `qa_shift_overflow_err`): 100% diagnostic code parity with `axiom0`.
  - `9 / 9` positive fixtures (`7` in `tests/run/comptime/*.ax` + `2` QA regression cases `qa_signed_comptime_ops`, `qa_const_agg_chain_mut_ret`): 100% `-O0` and `-O1` execution parity with `axiom0`.
- **End-to-end `-O0` vs `-O1` runtime execution & trap/UB/limit corpus (`22` fixtures)**:
  - `15 / 15` positive & runtime-trap fixtures across `tests/opt/*.ax`, `tests/mir/build/*.ax`, and `tests/selfhost/drop/fixtures/*.ax`: 100% `-O0` and `-O1` exit-code, stdout, and panic-message parity with `axiom0` (`REQ-OPT-387`).
  - `7 / 7` targeted runtime panic/UB/limit/diagnostic cases (`missing_main`, `panic_div_zero_o1`, `panic_overflow_o1`, `panic_bounds_o1`, `ub_null_deref_o1`, `step_limit_o1`, `stack_limit_o1`): 100% `-O0` and `-O1` parity on exit codes (`1`, `101`, `124`, `125`), panic messages (`division by zero`, `arithmetic overflow`, `index out of bounds`), and diagnostic codes (`AX_TYPE_MAIN_MISSING`, `AX_UNSAFE_INTERP_UB`, `AX_DRIVER_INTERP_STEP_LIMIT`, `AX_DRIVER_INTERP_STACK_LIMIT`) (`REQ-OPT-389`).
- **Standalone `.mir` optimizer & interpreter unit cases (`7` cases)**:
  - `7 / 7` unit checks in `qa_interp_opt_unit.ax` passing across `[interp]`, `[native]`, and `[native-O1]`.

## Round 1 Fixes
1. **`qa_interp_opt_diff_comptime_a.ax [interp]` timeout fixed**:
   - Replaced the heavy multi-const `scalar_const.ax` fixture in the `[interp]` twin `qa_interp_opt_diff_comptime_a.ax` with a compact positive comptime fixture (`comptime_pos_a.ax`) alongside `overflow_err.ax`, while keeping `scalar_const.ax` and all full comptime fixtures in `qa_interp_opt_diff_comptime_b.ax` (`// modes: native`). `qa_interp_opt_diff_comptime_a.ax [interp]` now completes in ~80s (well within the 1200s limit).
2. **Unconditional `compiler/interp` comptime evaluation for `HIR_ITEM_CONST`**:
   - Updated `session_comptime_check_and_eval` in [`compiler/interp_opt/session.ax`](file:///d:/projects/compiler/new%20lang/compiler/interp_opt/session.ax) so `HIR_ITEM_CONST` items are never skipped when `typeck`'s bootstrap constant folder pre-populates `CONST_INT` in `thir.symbol_consts`. Instead, every `HIR_ITEM_CONST` expression is evaluated through `session_eval_const_expr_into` (building the MIR body via `mir_build_expr_body`, binding `MIR_LOCAL_CONST` aggregate locals via `session_bind_mir_const_locals`, running `exec_mir_body`, and sign-extending `TY_I8`/`TY_I16`/`TY_I32` `CONST_INT` results). This catches 64-bit, intermediate, and shift overflow errors (`AX_CONST_OVERFLOW`) and accurately evaluates signed comparison/division/shift expressions (`>>`, `/`, `%`, `<`, `<=`, `>`, `>=`) and chained aggregate constant initializers (`const B: Pair = A`).
   - Also updated `mb_token_int_val` in the bundled `compiler.mir.builder` patch in [`tests/selfhost/interp_opt/gen_interp_opt_tests.py`](file:///d:/projects/compiler/new%20lang/tests/selfhost/interp_opt/gen_interp_opt_tests.py) to parse the token span first when `sv.len > 0 && (tok.flags & TOK_FLAG_BYTE_FORM) == 0u16`.
3. **Post-`-O1` aggregate constant local binding & preservation of `_0` / `MIR_LOCAL_USER` locals**:
   - Moved `session_bind_mir_const_locals` to run at the end of `session_interp_opt_fn` (after `-O1` optimization, ownership checking, and drop elaboration) so `-O1` DCE cannot strip `MIR_LOCAL_CONST` locals before `interp_run`.
   - Updated `session_bind_mir_const_locals` (`local_can_be_direct_const`, `get_or_add_const_agg_local`, `bind_const_agg_operand`) so only non-mutable `MIR_LOCAL_TEMP` (`local > 0`) locals with a single unprojected assignment and no projected reads are converted in-place to `MIR_LOCAL_CONST`. When a `CONST_AGGREGATE` is assigned to `_0` (`MIR_LOCAL_RETURN`), a `MIR_LOCAL_USER` variable (`let mut p = PAIR_C` / `let p = PAIR_C`), or a projected place, `bind_const_agg_operand` synthesizes a dedicated `MIR_LOCAL_CONST` local and rewrites the `OPERAND_CONSTANT` to `OPERAND_COPY` from that helper local.

## Verification
- `python tools/axtest.py --compiler build-snap-T083/build/axiom0.exe selfhost/interp_opt`: `18 / 18` PASS across `[interp]`, `[native]`, and `[native-O1]` (~300s total wall-clock time).
- `python tools/archcheck.py`: `188 files scanned, 0 violations`.

## Files changed
- compiler/interp_opt/mod.ax
- compiler/interp_opt/session.ax
- tests/selfhost/interp_opt/gen_interp_opt_tests.py
- tests/selfhost/interp_opt/harness_mir_opt_diff.ax.in
- tests/selfhost/interp_opt/harness_run_diff.ax.in
- tests/selfhost/interp_opt/harness_unit.ax.in
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_unit.ax

## Status
STATUS: COMPLETE round=1
