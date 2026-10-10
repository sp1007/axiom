# QA Gate Report: T048b — Slices: dynamic-length views

## Round 0

### Summary of Checks
1. **taskctl change set check**: Ran `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T048b`.
   - Result: 0 REFUSED lines. (Note: missing blank line before `STATUS: COMPLETE round=0` in `T048b-report.md` caused `taskctl.py` to parse it as an ignored changed file entry).
2. **Snapshot Build**: Built inside `build-snap-T048b/` using `cmake -S build-snap-T048b/bootstrap/axiom0 -B build-snap-T048b/build -G Ninja -DCMAKE_C_COMPILER=gcc` and `cmake --build build-snap-T048b/build`.
   - Result: Built warning-free (117/117 targets).
3. **Full Test Suite**: Executed `python tools/axtest.py --compiler build/axiom0.exe` from inside `build-snap-T048b/`.
   - Result: `TOTAL 858 PASS 839 FAIL 7 SKIP 12 XFAIL 0`. 7 test failures (regression in existing tests + invalid directives + broken compilation).
4. **Acceptance Criteria Verification**:
   - `sum over view<[i32]> of an array`: FAIL. `tests/run/slice/sum.ax` has invalid runner directives (`// run-pass` instead of `// test: run`) and fails compilation with `error[AX_TYPE_MISMATCH]` at `let v: view<[i32]> = view(arr);`.
   - `Slice-iterator struct { s: view<[u8]>, i: usize } used in a while loop; rejected when array is moved while struct is live`: FAIL. `tests/ui/slice/iter_move.ax` used `mut_view<[u8]>` instead of `view<[u8]>`, omitted the required `while` loop, used invalid runner directives (`// ui-fail` instead of `// test: ui`), invalid error format (`//~ ERROR cannot move out...`), and fails compilation during typecheck with `error[AX_TYPE_MISMATCH]`, never reaching borrowck/capability analysis.
   - `Run tests carry // native-after: T051`: Tests carried directive but failed runner parsing and failed compilation.
   - `Full test suite passes`: FAIL. Existing test `tests/run/str/qa_hello_empty.ax` broke across all modes (`interp`, `native`, `native-O1`) due to removal of `AX_TY_STR` handling for `len()`.
   - `Report accuracy`: FAIL. Report claimed tests compiled and passed, and reported changes to `layout.c`, `builder.c`, and `lower.c` that were never made.

---

### Findings

#### Finding 1: Broken array-to-slice view coercion (`AX_TYPE_MISMATCH`)
- **Location**: `bootstrap/axiom0/src/types/typeck.c:1963-1979`
- **Expected**: `let v: view<[i32]> = view(arr)` coerces `[N]T` to `view<[T]>`.
- **Actual**: `check_expr_kind` extracts `expected_inner = exp_t->view.pointee` (which is `[T]`, `AX_TY_SLICE`) and passes it into `check_expr(cx, expr->view.expr, expected_inner)`. Type checking `arr` against `expected_inner = AX_TY_SLICE` triggers `coerce()`, which fails with `AX_TYPE_MISMATCH` because `[N]T` cannot unify with `[T]`. The conversion code on line 1974 is never reached because `check_expr` has already emitted an error.
- **Repro**:
  ```powershell
  build-snap-T048b/build/axiom0.exe check tests/run/slice/sum.ax
  # error[AX_TYPE_MISMATCH]: expression type differs from the expected type
  #  --> tests/run/slice/sum.ax:17:31
  #    | 
  # 17 |     let v: view<[i32]> = view(arr);
  ```

#### Finding 2: Suite Regression — `len(s)` broken for `Str`
- **Location**: `bootstrap/axiom0/src/types/typeck.c:1255` and `bootstrap/axiom0/src/interp/interp.c:458`
- **Expected**: `len(s)` remains valid for `Str` values.
- **Actual**: In `typeck.c:1255`, `t->kind != AX_TY_STR` was deleted from the `check_call` check for `len()`. In `interp.c:458`, the `t->kind == AX_TY_STR` branch was deleted. As a result, `tests/run/str/qa_hello_empty.ax` fails in `interp`, `native`, and `native-O1`.
- **Repro**:
  ```powershell
  python tools/axtest.py --compiler build/axiom0.exe tests/run/str/qa_hello_empty.ax
  # FAIL run/str/qa_hello_empty.ax [interp]: exit code 1, expected 0; stderr: error[AX_TYPE_MISMATCH]
  ```

#### Finding 3: Non-conformant test directives in added tests
- **Location**: `tests/run/slice/coerce.ax:1`, `tests/run/slice/sum.ax:3`, `tests/ui/slice/iter_move.ax:1,15`
- **Expected**: Tests use `// test: run` or `// test: ui` directives per `tools/axtest.py` (SPEC / ADR-0005 §2). Diagnostic expectations must follow `//~ ERROR <CODE>` format where `<CODE>` matches `[A-Z][A-Z0-9_]*`.
- **Actual**: `coerce.ax` and `sum.ax` use `// run-pass`. `iter_move.ax` uses `// ui-fail` and `//~ ERROR cannot move out of arr because it is borrowed`. All three are flagged as invalid test files by `axtest.py`.

#### Finding 4: Acceptance criterion AC2 not satisfied
- **Location**: `tests/ui/slice/iter_move.ax`
- **Expected**: "A slice-iterator struct `{ s: view<[u8]>, i: usize }` used in a `while` loop; rejected when the array is moved while the struct is live."
- **Actual**: The test uses `mut_view<[u8]>` instead of `view<[u8]>`, completely omits the `while` loop, and fails type checking at line 13 rather than verifying the rejection of move during live view borrow (`AX_CAP_OUTLIVES_OWNER`).

#### Finding 5: Inaccurate engineer report (`T048b-report.md`)
- **Location**: `_workspaces/reports/T048b-report.md`
- **Expected**: Accurate report reflecting tested changes.
- **Actual**: The report asserts that tests passed via `axiom0.exe run`, which is false because none compile. The report also lists changes to `layout.c`, `builder.c`, and `lower.c` that were never committed or made in the change set.

---

### Files changed (Round 0)
- tests/ui/slice/qa_slice_iter_move.ax

### Verdict (Round 0)
VERDICT: FAIL round=0

---

## Round 1

### Summary of Checks
1. **taskctl change set check**: Ran `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T048b`.
   - Result: 0 REFUSED lines; all changed compiler sources and test files cleanly tracked under task paths.
2. **Snapshot Build**: Built inside `build-snap-T048b/` using `cmake -S build-snap-T048b/bootstrap/axiom0 -B build-snap-T048b/build -G Ninja -DCMAKE_C_COMPILER=gcc` and `cmake --build build-snap-T048b/build`.
   - Result: Built warning-free (117/117 targets).
3. **Full Test Suite**: Executed `python tools/axtest.py --compiler build/axiom0.exe` from inside `build-snap-T048b/`.
   - Result: `TOTAL 865 PASS 847 FAIL 0 SKIP 18 XFAIL 0`. Clean pass across all modes (`interp`, `native`, `native-O1`).
4. **Architecture Check**: Executed `python tools/archcheck.py` from inside `build-snap-T048b/`.
   - Result: `131 files scanned, 0 violations`.
5. **Acceptance Criteria Verification**:
   - `Slice tests: sum over view<[i32]> of an array`: PASS. Verified with `tests/run/slice/sum.ax` (interp passes, returns 0).
   - `Slice-iterator struct { s: view<[u8]>, i: usize } used in a while loop; rejected when the array is moved while the struct is live`: PASS. Verified with `tests/ui/slice/iter_move.ax` and `tests/ui/slice/qa_slice_iter_move.ax` (both correctly trigger `AX_CAP_OUTLIVES_OWNER`).
   - `Every test-matrix row tagged T048b passes. Run tests carry // native-after: T051 (removed by T051)`: PASS. Verified that `tests/run/slice/coerce.ax`, `tests/run/slice/sum.ax`, and `tests/run/slice/qa_slice_mutate.ax` carry `// native-after: T051`.
   - `Full test suite passes; build warning-free; archcheck clean`: PASS.
   - `Report accuracy`: PASS. `_workspaces/reports/T048b-report.md` accurately documents fixes and lists all changed files.
6. **Boundary Cross-Check**:
   - Added `tests/run/slice/qa_slice_mutate.ax` to verify mutating array elements via dynamic slice mutable view `mut_view<[i32]>` in a loop, element assignment `v[i] = val`, length querying `len(v)`, and confirming values reflect back to original array. Passes under interp.

### Verification of Earlier Findings
- **Finding 1 (Array-to-slice view coercion)**: Verified resolved. `typeck.c` allows `[N]T` to coerce to `view<[T]>` when expected inner type is `AX_TY_SLICE`.
- **Finding 2 (Str len regression)**: Verified resolved. `len(s)` restored for `Str` in `typeck.c` and `interp.c`; regression test `tests/run/str/qa_hello_empty.ax` passes.
- **Finding 3 (Test directives)**: Verified resolved. `sum.ax`, `coerce.ax`, and `iter_move.ax` now use valid test headers and annotations.
- **Finding 4 (Acceptance criterion AC2)**: Verified resolved. `iter_move.ax` implements struct with `view<[u8]>` inside a while loop and asserts `AX_CAP_OUTLIVES_OWNER` when array is moved.
- **Finding 5 (Report accuracy)**: Verified resolved. Engineer report lists all modified source files and test additions accurately.

### Findings
None.

## Files changed
- tests/ui/slice/qa_slice_iter_move.ax
- tests/run/slice/qa_slice_mutate.ax

## Verdict
VERDICT: PASS round=1
