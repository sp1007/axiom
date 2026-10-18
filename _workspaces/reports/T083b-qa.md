# T083b QA Report — Port MIR optimizer (-O1 const folding, DCE, CFG simplify) to Axiom

## Round 0

### Checks Performed & Evidence

1. **`taskctl.py changes T083b`**:
   - Command: `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T083b`
   - Exit code: `1`
   - Output:
     ```
     REFUSED 9 changed file(s) under the task's own paths/locks are not in any '## Files changed' list (work would be lost): compiler/opt/cfg_simp.ax, compiler/opt/const_fold.ax, compiler/opt/dce.ax, compiler/opt/mod.ax, tests/selfhost/opt/gen_opt_tests.py, tests/selfhost/opt/harness_opt_pipeline.ax.in, tests/selfhost/opt/harness_opt_unit.ax.in, tests/selfhost/opt/qa_opt_pipeline.ax, tests/selfhost/opt/qa_opt_unit.ax — add them to the report, or rerun with --include-unlisted (stage them) / --allow-unlisted (leave them)
     REFUSED no parsable '## Files changed' entries in the reports of T083b (bullets '- path', numbered '1. path' or table rows)
     stage _workspaces/reports/T083b-report.md
     ```
2. **Snapshot build (`build-snap-T083b/build`)**:
   - Command: `cmake -S bootstrap/axiom0 -B build -G Ninja -DCMAKE_C_COMPILER=gcc && cmake --build build`
   - Result: 127/127 targets built, 0 warnings, 0 errors.
3. **Unit & CDriver tests (`ctest`)**:
   - Command: `ctest --test-dir build --output-on-failure`
   - Result: `18/18 passed (100%)`.
4. **Architecture layer check (`archcheck.py`)**:
   - Command: `python tools/archcheck.py` (in `build-snap-T083b`)
   - Result: `archcheck: 188 files scanned, 0 violations`.
5. **Test suites (`axtest.py`)**:
   - Command: `python tools/axtest.py --compiler build/axiom0.exe --filter selfhost/opt` -> `TOTAL 6 PASS 6 FAIL 0 SKIP 0 XFAIL 0`
   - Command: `python tools/axtest.py --compiler build/axiom0.exe --filter opt` -> `TOTAL 30 PASS 30 FAIL 0 SKIP 0 XFAIL 0`
6. **Code, Spec & Boundary Cross-Check (`compiler/opt/` vs `bootstrap/axiom0/src/opt/opt.c`)**:
   - Audited `compiler/opt/const_fold.ax`, `compiler/opt/dce.ax`, `compiler/opt/cfg_simp.ax`, `compiler/opt/mod.ax`, and `tests/selfhost/opt/*` against `bootstrap/axiom0/src/opt/opt.c` and the acceptance criteria in `_workspaces/tasks/doing/T083b-port-optimizer-to-axiom.md`.
   - Canonical syntax (`=`, `.`) verified across all `.ax` files; module sizes well within the ~1.5k LOC split guide (`const_fold.ax`: 779, `dce.ax`: 282, `cfg_simp.ax`: 458, `mod.ax`: 253).
   - Identified 5 FAIL findings detailed below.

---

### Findings

#### Finding 1 — Missing `## Files changed` section in `_workspaces/reports/T083b-report.md` (`taskctl.py changes T083b` REFUSED)
- **Location**: `_workspaces/reports/T083b-report.md:6-33`
- **Expected**: Acceptance criterion 5 requires `Report _workspaces/reports/T083b-report.md with exact ## Files changed`, and `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T083b` must exit 0 with zero `REFUSED` lines.
- **Actual**: `_workspaces/reports/T083b-report.md` uses `## Files Created` instead of `## Files changed`, causing `taskctl.py changes T083b` to fail with two `REFUSED` errors for all 9 created files.
- **Repro**:
  ```
  python .claude/skills/axiom-tasks/scripts/taskctl.py changes T083b
  ```
  Add a `## Files changed` section to `_workspaces/reports/T083b-report.md` listing each file as a literal `- <path>` bullet:
  - `compiler/opt/cfg_simp.ax`
  - `compiler/opt/const_fold.ax`
  - `compiler/opt/dce.ax`
  - `compiler/opt/mod.ax`
  - `tests/selfhost/opt/gen_opt_tests.py`
  - `tests/selfhost/opt/harness_opt_pipeline.ax.in`
  - `tests/selfhost/opt/harness_opt_unit.ax.in`
  - `tests/selfhost/opt/qa_opt_pipeline.ax`
  - `tests/selfhost/opt/qa_opt_unit.ax`

#### Finding 2 — Soundness bug in `opt_const_fold`: blindly rewrites the next `MIR_RVALUE_OVERFLOWS_BINARY_OP` statement to `const 0` without checking its operands
- **Location**: `compiler/opt/const_fold.ax:693-713`
- **Expected**: Each `MIR_RVALUE_OVERFLOWS_BINARY_OP` statement must only be folded to `const 0` (`false`) if its own `lhs` and `rhs` operands are scalar constants whose operation does not overflow (`do_const_fold_binop` returns `true`), matching `bootstrap/axiom0/src/opt/opt.c:183-201`.
- **Actual**: Inside the `if rv_kind == MIR_RVALUE_BINARY_OP` branch (`const_fold.ax:672-714`), after folding statement `j`, lines `693-713` inspect `next_stmt` (`j + 1`) and check only:
  ```axiom
  (*next_stmt).kind == MIR_STMT_ASSIGN &&
  (*next_stmt).rvalue.kind == MIR_RVALUE_OVERFLOWS_BINARY_OP &&
  (*next_stmt).rvalue.bin_op == orig_op
  ```
  without checking `(*next_stmt).rvalue.lhs` or `(*next_stmt).rvalue.rhs` at all. If statement `j` is a foldable constant binary op (e.g., `_1 = const 1: type#6 + const 2: type#6`) and statement `j + 1` is an `overflows(...)` check with the same `bin_op` — even one with **overflowing constants** (`_2 = overflows(const 127: type#6 + const 1: type#6)`) or **non-constant runtime locals** (`_2 = overflows(copy _3 + copy _4)`) — `opt_const_fold` unconditionally overwrites `next_stmt` with `_2 = const 0: type#4` (no overflow), silently eliminating runtime overflow traps.
- **Repro**:
  In a MIR block containing:
  ```
  _1 = const 1: type#6 + const 2: type#6;
  _2 = overflows(const 127: type#6 + const 1: type#6);
  ```
  or:
  ```
  _1 = const 1: type#6 + const 2: type#6;
  _2 = overflows(copy _3 + copy _4);
  ```
  `opt_const_fold` rewrites `_2` to `_2 = const 0` instead of leaving it unfolded. Remove lines `693-713` (lines `715-741` already fold valid constant `MIR_RVALUE_OVERFLOWS_BINARY_OP` statements on their own iteration `j`).

#### Finding 3 — `opt_dce` and `opt_rvalue_is_pure` diverge from `bootstrap/axiom0/src/opt/opt.c` and delete trapping/unfolded unary operations
- **Location**: `compiler/opt/dce.ax:128-138`, `compiler/opt/dce.ax:164-220`, `compiler/opt/dce.ax:224-272`
- **Expected**:
  1. In `bootstrap/axiom0/src/opt/opt.c:340-348`, `rvalue_is_pure` returns `true` only for `MIR_RVALUE_USE`, `MIR_RVALUE_REF`, `MIR_RVALUE_CAST`, `MIR_RVALUE_AGGREGATE`, `MIR_RVALUE_DISCRIMINANT`, and `MIR_RVALUE_LEN` (returning `false` for `MIR_RVALUE_UNARY_OP` and `MIR_RVALUE_REPEAT`). Note that `_workspaces/reports/T083b-report.md:15` also claims `opt_rvalue_is_pure` "preserves potentially trapping binary (`DIV`, `REM`, `SHL`, `SHR`) and unary (`NEG`) operations on non-constants".
  2. In `bootstrap/axiom0/src/opt/opt.c:363` and `421`, `ax_opt_dce` skips basic blocks whose terminator is `AX_MIR_TERM_UNREACHABLE` (`if (bb->terminator.kind == AX_MIR_TERM_UNREACHABLE) continue;`).
- **Actual**:
  1. `compiler/opt/dce.ax:136-137` unconditionally includes `k == MIR_RVALUE_REPEAT || k == MIR_RVALUE_UNARY_OP` in `opt_rvalue_is_pure`. Consequently, when `opt_const_fold` intentionally leaves an overflowing constant negation unfolded (e.g., `_1 = -const 128: type#6` for `-INT8_MIN`) or when a MIR body has an unused `_1 = -copy _2` or `_1 = !copy _2`, `opt_dce` deletes the statement, whereas `axiom0` (`opt.c`) preserves it.
  2. `compiler/opt/dce.ax:164-220` and `224-272` do not skip basic blocks with `terminator.kind == MIR_TERM_UNREACHABLE`, so uses in already-unreachable blocks keep dead locals in reachable blocks alive during `opt_dce` (which runs before `opt_cfg_simplify` in `opt_run`).
- **Repro**:
  Run `opt_mir_text` on:
  ```
  mir_body {
      let mut _0: type#6;
      let _1: type#6;
      bb0: {
          _1 = -const 128: type#6;
          _0 = const 0: type#6;
          return;
      }
  }
  ```
  `axiom0` (`ax_opt_run`) preserves `_1 = -const 128;`, whereas `compiler/opt` deletes `_1 = -const 128;`.

#### Finding 4 — `do_const_fold_binop`, `do_const_fold_unop`, `opt_const_fold`, and `opt_cfg_simplify` diverge from `bootstrap/axiom0/src/opt/opt.c`
- **Location**: `compiler/opt/const_fold.ax:411-419`, `compiler/opt/const_fold.ax:614-621`, `compiler/opt/const_fold.ax:641-771`, `compiler/opt/cfg_simp.ax:432-436`
- **Expected**:
  1. `bootstrap/axiom0/src/opt/opt.c:9` checks `if (lhs->ty.v != rhs->ty.v) return false;` in `do_const_fold_binop`.
  2. `bootstrap/axiom0/src/opt/opt.c:140-143` checks `if (operand->ty.v != in->t_bool.v) return false;` for `AX_MIR_UNOP_NOT` (bitwise NOT on integers uses `AX_MIR_UNOP_BITNOT`).
  3. `bootstrap/axiom0/src/opt/opt.c:174-216` (`ax_opt_const_fold`) and `opt.c:220-315` (`ax_opt_cfg_simplify`) iterate `while (changed)` to a fixed point, and `opt.c:192` uses the destination local's type (`body->locals[stmt->assign.place.local.v].ty`, falling back to `bool_ty`) when folding `AX_MIR_RVALUE_OVERFLOWS_BINARY_OP`.
- **Actual**:
  1. `do_const_fold_binop` (`const_fold.ax:411-419`) does not check `lhs.constant.ty.v == rhs.constant.ty.v`, folding binary ops with mismatched operand types.
  2. `do_const_fold_unop` (`const_fold.ax:614-621`) folds `MIR_UNOP_NOT` on non-`bool` integer types as bitwise NOT instead of returning `false` (note: update `harness_opt_unit.ax.in:255` accordingly so `MIR_UNOP_NOT` on `i8` is tested with `check_unop_ovf` while `MIR_UNOP_BITNOT` on `i8` is tested with `check_unop_ok`).
  3. `opt_const_fold` and `opt_cfg_simplify` run only a single pass instead of `while changed`.

#### Finding 5 — Incomplete differential test coverage on `tests/opt/` fixtures
- **Location**: `tests/selfhost/opt/gen_opt_tests.py:200-425`, `tests/selfhost/opt/harness_opt_unit.ax.in:338-465`, `tests/selfhost/opt/harness_opt_pipeline.ax.in:131-241`
- **Expected**: Acceptance criterion 3 requires `Optimized MIR matches axiom0 inspect --emit=mir-opt on optimization test fixtures`. All optimization test fixtures under `tests/opt/` (`tests/opt/const_fold_run.ax`, `tests/opt/qa_dce_run.ax`, `tests/opt/qa_edge_cases_run.ax`) should be verified against `axiom0`'s post-`-O1` MIR output, plus regression tests for Findings 2, 3, and 4.
- **Actual**:
  - `UNIT_MIR_SNIPPETS` in `tests/selfhost/opt/gen_opt_tests.py` only includes `tests/opt/qa_dce_run.ax` and omits `tests/opt/const_fold_run.ax` and `tests/opt/qa_edge_cases_run.ax`.
  - `harness_opt_pipeline.ax.in` runs `mir_drop_elaborate` *before* `opt_run` (whereas `bootstrap/axiom0/src/driver/pipeline.c:446-508` runs `ax_opt_run` right after `ax_mir_build` + `ax_verify_mir` in `stage_typeck`, before `stage_own` / `ax_mir_drop_elaborate`) and only checks boolean flags (`saw_unreachable_bb`, `saw_folded_42`) on a synthetic snippet rather than comparing optimized MIR output on the `tests/opt/` fixtures.

VERDICT: FAIL round=0

## Round 1

### Checks Table

| Check | Command | Exit | Evidence |
|---|---|---|---|
| Path Gate | `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T083b` | `0` | 11 `stage` lines (`_workspaces/reports/T083b-qa.md`, `_workspaces/reports/T083b-report.md`, `compiler/opt/cfg_simp.ax`, `compiler/opt/const_fold.ax`, `compiler/opt/dce.ax`, `compiler/opt/mod.ax`, `tests/selfhost/opt/gen_opt_tests.py`, `tests/selfhost/opt/harness_opt_pipeline.ax.in`, `tests/selfhost/opt/harness_opt_unit.ax.in`, `tests/selfhost/opt/qa_opt_pipeline.ax`, `tests/selfhost/opt/qa_opt_unit.ax`), `0` `REFUSED` lines |
| Engineer Report | `_workspaces/reports/T083b-report.md` | PASS | Contains `## Files changed` listing all 9 task files and ends with `STATUS: COMPLETE round=1` |
| Architecture Check (in `build-snap-T083b/`) | `python tools/archcheck.py` | `0` | `archcheck: 188 files scanned, 0 violations` |
| CTest Suite (in `build-snap-T083b/`) | `ctest --test-dir build --output-on-failure` | `0` | `100% tests passed, 0 tests failed out of 18 (2.80 sec)` |
| Optimizer & Selfhost Opt Suite (in `build-snap-T083b/`) | `python tools/axtest.py --compiler build/axiom0.exe --filter opt` | `0` | `TOTAL 30 PASS 30 FAIL 0 SKIP 0 XFAIL 0` (including `selfhost/opt/qa_opt_unit.ax` and `selfhost/opt/qa_opt_pipeline.ax` across `[interp]`, `[native]`, `[native-O1]`) |
| QA Boundary Tests | `tests/selfhost/opt/harness_opt_unit.ax.in` + `tests/selfhost/opt/qa_opt_unit.ax` | `0` | Added boundary cases in `test_const_fold_scalars` (`return 250..260`): `MIR_UNOP_NEG` rejection on `bool`/`char`, `MIR_UNOP_NOT` rejection on `u32`/`char`, `INT8_MIN / 1` and `INT8_MIN % 1` folding vs `INT16_MIN % -1` overflow rejection, negative shift counts (`-1` two's complement) rejection on signed integers, and non-integer `TypeId` (`unit`, `str`, `type#99`) rejection |

### Verification of Round 0 Findings

1. **Finding 1 (Resolved)**: `_workspaces/reports/T083b-report.md` now includes `## Files changed` listing all 9 files in `compiler/opt/` and `tests/selfhost/opt/`, and ends with `STATUS: COMPLETE round=1`. `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T083b` exits `0` with `0` `REFUSED` lines.
2. **Finding 2 (Resolved)**: `compiler/opt/const_fold.ax:654-755` removed the broken `j + 1` statement lookahead from the `MIR_RVALUE_BINARY_OP` branch; `MIR_RVALUE_OVERFLOWS_BINARY_OP` now folds solely via `do_const_fold_binop` on its own `lhs`/`rhs` operands, matching `bootstrap/axiom0/src/opt/opt.c:183-201`. Regression Case 5 (`blobs 9 -> 10` in `tests/selfhost/opt/harness_opt_unit.ax.in:469-473`) verifies that a foldable `MIR_RVALUE_BINARY_OP` followed by an overflowing or runtime `MIR_RVALUE_OVERFLOWS_BINARY_OP` does not clobber the subsequent overflow check.
3. **Finding 3 (Resolved)**: `compiler/opt/dce.ax:130-138` (`opt_rvalue_is_pure`) now returns `true` only for `MIR_RVALUE_USE`, `MIR_RVALUE_REF`, `MIR_RVALUE_LEN`, `MIR_RVALUE_CAST`, `MIR_RVALUE_DISCRIMINANT`, and `MIR_RVALUE_AGGREGATE` (matching `opt.c:340-348`), and `opt_dce_in_arena` (`dce.ax:166,228`) skips `MIR_TERM_UNREACHABLE` blocks in both use-counting and statement-removal loops (matching `opt.c:363,421`). Regression Case 6 (`blobs 11 -> 12` in `tests/selfhost/opt/harness_opt_unit.ax.in:475-480`) verifies both behaviors.
4. **Finding 4 (Resolved)**:
   - `do_const_fold_binop` (`compiler/opt/const_fold.ax:415-423`) verifies `lhs.constant.ty.v == rhs.constant.ty.v` and `bits > 0 && bits <= 64`.
   - `do_const_fold_unop` (`compiler/opt/const_fold.ax:610-624`) verifies `bits > 0 && bits <= 64` and restricts `MIR_UNOP_NOT` to `bool` (`opt_type_is_bool`).
   - `opt_const_fold` (`compiler/opt/const_fold.ax:665-754`) and `opt_cfg_simplify_in_arena` (`compiler/opt/cfg_simp.ax:441-452`) iterate `while pass_changed` to a fixed point, and `MIR_RVALUE_OVERFLOWS_BINARY_OP` folding (`const_fold.ax:714-732`) uses `body.locals[dst_loc].ty` with `bool_ty` fallback.
5. **Finding 5 (Resolved)**: Both `tests/selfhost/opt/qa_opt_unit.ax` (Cases 4, 7, 8) and `tests/selfhost/opt/qa_opt_pipeline.ax` (full `parse -> resolve -> HIR -> typeck -> mir_build -> verify_mir -> opt_run_in_arena -> mir_print` before `stage_own` / `mir_drop_elaborate`) verify byte-for-byte post-`-O1` MIR parity against `axiom0 -O1` across all 3 optimization test fixtures (`tests/opt/const_fold_run.ax`, `tests/opt/qa_dce_run.ax`, `tests/opt/qa_edge_cases_run.ax`).

## Files changed
- `tests/selfhost/opt/harness_opt_unit.ax.in`
- `tests/selfhost/opt/qa_opt_unit.ax`

VERDICT: PASS round=1

