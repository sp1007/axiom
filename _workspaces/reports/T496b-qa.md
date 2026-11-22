# T496b QA Report

## Round 0

### Summary
Independent QA gate for T496b (Cleanup — report `a..=` / `..=` without an end bound in the parser, remove duplicate HIR lowering diagnostic, and test `str` inclusive sub-ranges). All acceptance criteria verified inside `build-snap-T496b/` (HEAD `4f2daaf` + T496b changes + QA boundary tests + regenerated selfhost bundles).

### Concrete Checks
1. **Parser diagnostic (`compiler/syntax/parse.ax`)**:
   - Verified `MSG_INCLUSIVE_RANGE_NO_END` (`PARSE_DATA[1636:1680]`) decodes to `"inclusive range needs an end bound after ..="` (44 bytes).
   - Verified `at_range_end(parser)` checks `is_range_end(kind) || (parser.no_struct && kind == TOK_LBRACE)` and that both `parse_prefix_range_expr` (`..=`) and `parse_binary_suffix` (`a..=`) emit `AX_PARSE_EXPECTED_EXPR` with `MSG_INCLUSIVE_RANGE_NO_END` and the `EXPR_RANGE` span.
   - Verified parse-only `build/axiomc2.exe inspect --emit=ast` rejects `a..=` / `..=` without an end bound with exit 1 and `AX_PARSE_EXPECTED_EXPR` across index brackets, `let`, `for`, `if`, `while`, call args, parens, array literals, match arms, and block-trailing `return`.
2. **HIR lowering cleanup (`compiler/hir/lower.ax`)**:
   - Verified `emit_inclusive_range_without_end`, `LOWER_INCLUSIVE_NO_END_MSG`, the duplicate `is_inclusive && end_expr == 0` check, and the unused `AX_PARSE_EXPECTED_EXPR` import were completely removed.
3. **Unchanged existing UI test**:
   - `git diff HEAD -- tests/ui/slice_inclusive/inclusive_without_end.ax` is empty.
   - `./build/axiomc2.exe check --std-root std tests/ui/slice_inclusive/inclusive_without_end.ax` emits 1 error (`AX_PARSE_EXPECTED_EXPR: inclusive range needs an end bound after ..=` at line 11:17).
4. **`str` sub-range investigation (`tests/ui/slice_inclusive/str_subrange_unsupported.ax`)**:
   - Confirmed `compiler/verify/verifier.ax:1037` rejects `MIR_PROJ_SUB_SLICE` when `tk != TY_ARRAY && tk != TY_SLICE` with `AX_VERIFY_TYPE_MISMATCH` (`subslice projection on non-slice/array type`).
   - Ran `./build/axiomc2.exe check --std-root std tests/ui/slice_inclusive/str_subrange_unsupported.ax`: emits 5 `AX_VERIFY_TYPE_MISMATCH` errors covering `s[0..=2]`, `s[..=2]`, `s[0..2]` on ASCII and multi-byte UTF-8 (`"Xin chào thế giới"`), matching the task scope ("if `str` sub-ranges are not supported, report it and test the diagnostic instead").
5. **Stage-2/3 fixed-point build (inside `build-snap-T496b/`)**:
   - `python tools/build_axiomc.py --out build --root . --stage 3`
   - `STAGE1 OK`, `STAGE2 (O1) OK`, `STAGE3 (O1) OK`, `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == 94c16b0438b9033c91ed88ba55ead3d1217c4fcc652f5eaa7d45560aad347aa2`.
6. **Boundary cross-check (step 5)**:
   - Added `tests/parse/range_inclusive/inclusive_edge_bounds.ax` (+ `.ast`) covering valid inclusive ranges with binary (`a..=n + 1`), unary (`a..=-1`), block (`a..={ 1 }`, `..={ 2 }` in non-header expression position where `no_struct` is false), `for` headers (`0..=n`, `..=n`), and open exclusive `for x in a.. {}`.
   - Added `tests/ui/slice_inclusive/inclusive_without_end_boundaries.ax` covering open inclusive ranges in array literals (`[a..=]`, `[..=]`), prefix call arg (`take(..=)`), `no_struct` `if`/`while` headers (`if a..= {}`, `while ..= {}`), match arm (`_ => a..=,`), and block-trailing `return a..=` before `}`.
   - Refreshed snapshot (`python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T496b`: 36 generators, 60 files, 28s, exit 0) and ran fresh `--no-cache` verification:
     `python tools/axtest.py --compiler build/axiomc2.exe --exclude-requires axiom0-internal --no-cache -j 2 --filter slice_inclusive/ --filter range_inclusive/`
     -> `TOTAL 76 PASS 76 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`, `UNCACHEABLE 0`.
7. **Per-task gate (`tools/taskgate.py` inside `build-snap-T496b/`)**:
   - Command: `python tools/taskgate.py --task T496b --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T496b.json`
   - Result: `TASKGATE T496b exit=0` (wall time 1299.0 s)
   - `own`: 8/8 PASS; `affected`: 203/204 PASS (1 pre-existing SKIP); `smoke`: 54/54 PASS; `total (dedup)`: `TOTAL 257 PASS 256 FAIL 0 SKIP 1 XFAIL 0`.
   - `WEAK-NATIVE: 3 in the run; 0 in the task's own/changed tests`.
   - `BASELINE OK` (`Failing ids: none`).
   - `archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations`.
   - `smoke-check (tests/smoke.list): OK`.
   - `Cache: CACHED 45, miss 37, uncacheable 83, stored 35, dep_source exact, verification sample seed=1150928775 n=20 of 51 hits, mismatch none`.
8. **Board & harness checks**:
   - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T496b`: 0 `REFUSED` lines (verified after listing QA-added tests).
   - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.

### Findings
None.

## Files changed
- tests/parse/range_inclusive/inclusive_edge_bounds.ax
- tests/parse/range_inclusive/inclusive_edge_bounds.ast
- tests/ui/slice_inclusive/inclusive_without_end_boundaries.ax

## Follow-ups
- Confirmed the engineer's follow-up: `str` sub-range slicing (`s[a..b]`, `s[a..=b]`, `s[..=b]`) is accepted by `typeck.ax:8832` and `mir/builder.ax:4033` but rejected by `compiler/verify/verifier.ax:1037` (`AX_VERIFY_TYPE_MISMATCH`). A dedicated follow-up task is needed to either support `MIR_PROJ_SUB_SLICE` on `TY_STR` end-to-end with SPEC-03 UTF-8 boundary checks or reject it in `typeck.ax`.

VERDICT: PASS round=0
