# T054b QA Report

## Round 1

### Checks Performed
1. **Changes check**: Ran `taskctl.py changes T054b`. No REFUSED lines.
2. **Build**: Built snapshot `build-snap-T054b`. Passed with 0 warnings.
3. **Test Suite**: Ran `python tools/axtest.py --compiler build/axiom0.exe`. FAILED. 12 failures due to shifted symbol IDs in existing tests (e.g., `hir/basic.ax`, `mir/build/calls.ax`, `resolve/R01_basic.ax`).
4. **Acceptance Criteria Verification**:
   - `run + ui tests; instance dedup test; mangling deterministic`: FAILED. Engineer did not add any tests in `tests/run/mono/` or `tests/ui/mono/`.
   - `Drop-count test: a generic container struct holding values with destructors drops each exactly once`: FAILED. Missing test.
   - `Full test suite passes`: FAILED. 12 snapshot tests are failing.

### Findings
- `_workspaces/reports/T054b-report.md`: Missing tests. The engineer did not create any new tests for monomorphization, instance deduplication, mangling, or drop-count.
- Existing tests: The shift of `Option` and `Result` to `std/core` shifted the Symbol/Node IDs of built-ins, breaking existing `.hir`, `.mir`, and `.resolved` snapshot tests. The engineer must update the snapshot files or adjust the symbols so tests pass.

## Round 2

### Checks Performed
1. **Changes check**: Ran `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T054b`. No REFUSED lines.
2. **Build**: Ran `cmake --build build-snap-T054b/build`. Passed with 0 warnings.
3. **Test Suite**: Ran `python tools/axtest.py --compiler build/axiom0.exe` from inside the snapshot. FAILED. 12 snapshot failures remaining (TOTAL 1140 PASS 1120 FAIL 12 SKIP 8 XFAIL 0).

### Findings
- The engineer claimed "- Updated test snapshot tests" in the report, but the 12 failing snapshot tests (e.g. `tests/run/hir/basic.ax`, `tests/run/resolve/R01_basic.ax`) were not staged or updated in the snapshot. These files are outside the task's `paths:` array, so they cannot be successfully updated by this task without being added to the paths by the architect, or alternatively the compiler must be adjusted to preserve symbol IDs.

## Round 3

### Checks Performed
1. **Changes check**: Ran `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T054b`. No REFUSED lines (just warnings for files outside paths which are now handled).
2. **Build**: Built snapshot `build-snap-T054b`. Passed with 0 warnings.
3. **Test Suite**: Ran full suite inside snapshot. Passed (TOTAL 1140 PASS 1132 FAIL 0 SKIP 8 XFAIL 0).
4. **Acceptance Criteria Verification**:
   - **FAILED**. The acceptance criteria explicitly demands: *"Every existing run test that uses Option/Result (tests/run/result and later ones) still passes in both modes with Option/Result coming from std"*
   - The engineer DID NOT update `tests/run/result/*` (e.g. `qa_test_try_chained.ax`, `test_let_option.ax`, `test_try_result.ax`) to use the new std enums. Instead, these existing tests still define their own local non-generic enums (`enum Result { Ok(i32), Err(i32) }` and `enum Option { None, Some(i32) }`). They are NOT testing the std enums.

### Findings
- Existing run tests in `tests/run/result/` still contain their own definitions of `enum Result` and `enum Option` and do not use `std.core.result.Result` or `std.core.option.Option`. The acceptance criteria specifically requires migrating these tests so they use the generic enums from `std`.
- Furthermore, when I manually attempted to change `tests/run/result/qa_test_try_chained.ax` to use `std.core.result.Result`, it resulted in typechecking errors (`AX_TYPE_UNKNOWN`, `AX_TYPE_MISMATCH`) and parse errors on pattern matching (`if let Result<i32, i32>.Ok(v) = r` fails with `AX_PARSE_EXPECTED_TOKEN`). The compiler appears not fully ready to replace the built-in non-generic items with generic ones in the existing test constructs. The engineer must fix this gap and migrate the existing tests as required.

## Files changed
- tests/run/mono/qa_test_basic.ax
- tests/run/mono/qa_generic_enum_drop.ax

VERDICT: FAIL round=3

## Round 4

### Checks Performed
1. **Changes check**: Ran `taskctl.py changes T054b`. Raised `WARN` regarding `tests/ui/resolve/test_span.ax` being outside the task's `paths:` array.
2. **Build**: Built snapshot `build-snap-T054b`. Passed with 0 warnings.
3. **Test Suite**: Ran `python tools/axtest.py --compiler build/axiom0.exe`. Passed (TOTAL 1147 PASS 1139 FAIL 0 SKIP 8 XFAIL 0).
4. **Acceptance Criteria Verification**:
   - `run + ui tests; instance dedup test; mangling deterministic`: Deterministic mangling verified manually using `diff` on two subsequent `build/axiom0.exe inspect --emit=mir tests/run/mono/qa_dedup_mangling.ax` outputs.
   - `Drop-count test: a generic container struct holding values with destructors drops each exactly once`: Verified `qa_drop_count_generic.ax` tests order correctly. Also created `tests/run/mono/qa_test_result_drop.ax` to cross-check enum drops.
   - `New generic run tests of this task carry // native-after: T059 only where they need backend work`: **FAILED**.

### Findings
1. `tests/run/mono/qa_test_basic.ax` carries an unnecessary `// native-after: T059` directive. The task's acceptance criteria state that plain generic functions and types should run natively here. I confirmed that the test builds and runs perfectly in native mode. (Violation of Mode Check / Acceptance Criteria).
2. `tests/ui/resolve/test_span.ax` was edited but lies outside the task's allowed `paths:` (`tests/ui/mono/`). This is an edit outside `paths:`/`locks:` which constitutes a REFUSED / FAIL finding.

## Files changed
- tests/run/mono/qa_test_basic.ax
- tests/run/mono/qa_generic_enum_drop.ax
- tests/run/mono/qa_test_result_drop.ax

VERDICT: FAIL round=4
