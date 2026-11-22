# T496b report

## Summary
- Moved the `a..=` / `..=` without an end bound diagnostic from HIR lowering (`compiler/hir/lower.ax`) into the parser (`compiler/syntax/parse.ax`), matching SPEC-02 AXS-GRM-070 and ADR-0045 so parse-only tools (`inspect --emit=ast`, formatter, LSP) also reject open inclusive ranges.
- In `compiler/syntax/parse.ax`:
  - Added `MSG_INCLUSIVE_RANGE_NO_END` (`"inclusive range needs an end bound after ..="`, 44 bytes) to `PARSE_DATA`/`PARSE_OFF`.
  - Added `at_range_end(parser)` checking `is_range_end(peek_kind(parser)) || (parser.no_struct && peek_kind(parser) == TOK_LBRACE)`, so `for x in a..= { ... }` and `for x in ..= { ... }` diagnose the missing end bound cleanly without consuming `{` or cascading.
  - Updated `parse_prefix_range_expr` (`..=`) and `parse_binary_suffix` (`a..=`) to emit `AX_PARSE_EXPECTED_EXPR` with `MSG_INCLUSIVE_RANGE_NO_END` and the same `EXPR_RANGE` span (`(*expr).span` / `(*binary).span`) whenever `is_inclusive` is true and `at_range_end` holds.
- In `compiler/hir/lower.ax`:
  - Removed `emit_inclusive_range_without_end`, `LOWER_INCLUSIVE_NO_END_MSG`, the lowering-side `is_inclusive && end_expr == 0` check, and the now-unused `AX_PARSE_EXPECTED_EXPR` import so there is a single source of the diagnostic.
- `str[a..=b]` / `str[..=b]` investigation:
  - `compiler/types/typeck.ax:8832` and `compiler/mir/builder.ax:4033` (`mb_range_base_is_checked`) accept `TY_STR` sub-ranges, but `compiler/verify/verifier.ax:1037` rejects `MIR_PROJ_SUB_SLICE` on any type other than `TY_ARRAY` / `TY_SLICE` with `AX_VERIFY_TYPE_MISMATCH` (`subslice projection on non-slice/array type`).
  - Per the task scope ("if `str` sub-ranges are not supported, report it and test the diagnostic instead"), added `tests/ui/slice_inclusive/str_subrange_unsupported.ax` testing `AX_VERIFY_TYPE_MISMATCH` for `s[0..=2]`, `s[..=2]`, and `s[0..2]` on ASCII and multi-byte UTF-8 (`"Xin chào thế giới"`), and filed a follow-up below.
- Kept `tests/ui/slice_inclusive/inclusive_without_end.ax` unchanged and passing.

## Files changed
- compiler/syntax/parse.ax
- compiler/hir/lower.ax
- tests/parse/range_inclusive/inclusive_no_end_contexts.ax
- tests/parse/range_inclusive/inclusive_no_end_contexts.ast
- tests/parse/range_inclusive/inclusive_no_end_contexts_diag.test
- tests/parse/range_inclusive/inclusive_valid.ax
- tests/parse/range_inclusive/inclusive_valid.ast
- tests/ui/slice_inclusive/inclusive_without_end_contexts.ax
- tests/ui/slice_inclusive/str_subrange_unsupported.ax

## Tests
All builds and tests were run inside `build-snap-T496b/` (HEAD `4f2daaf` + T496b changes + regenerated selfhost bundles):

- Stage-2/3 fixed-point build:
  `python tools/build_axiomc.py --out build --root . --stage 2`
  -> `STAGE1 OK`, `STAGE2 (O1) OK`, `STAGE3 (O1) OK`, `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == 94c16b0438b9033c91ed88ba55ead3d1217c4fcc652f5eaa7d45560aad347aa2`, `STAGE0-GUARD OK`.
- Own/new + existing inclusive slice tests (`--no-cache`):
  `python tools/axtest.py --compiler build/axiomc2.exe --exclude-requires axiom0-internal --no-cache -j 2 --filter slice_inclusive/ --filter range_inclusive/`
  -> `TOTAL 74 PASS 74 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`, `UNCACHEABLE 0`.
  (Includes unchanged `tests/ui/slice_inclusive/inclusive_without_end.ax`, `tests/parse/range_inclusive/inclusive_no_end_contexts_diag.test` running parse-only `inspect --emit=ast`, and `tests/run/slice_inclusive/` in all 3 modes.)
- Acceptance groups (`tests/parse`, `tests/ui`, `tests/run/slice_inclusive`, `selfhost/parse`, `selfhost/hir`):
  `python tools/axtest.py --compiler build/axiomc2.exe --exclude-requires axiom0-internal --baseline _workspaces/baseline-failures.txt -j 2 --filter parse/ --filter ui/ --filter run/slice_inclusive/ --filter selfhost/parse --filter selfhost/hir`
  -> `TOTAL 519 PASS 519 FAIL 0 SKIP 0 XFAIL 0`, `BASELINE OK`, `WEAK-NATIVE 0`.
- Per-task gate:
  `python tools/taskgate.py --task T496b --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`
  -> `TOTAL 255 PASS 254 FAIL 0 SKIP 1 XFAIL 0` (`own` 6/6, `affected` 201/202 with 1 pre-existing skip, `smoke` 54/54), `BASELINE OK`, `WEAK-NATIVE: 3 in the run; 0 in the task's own/changed tests`, `archcheck: clean (232 files scanned, 0 violations)`, `smoke-check: OK`, `TASKGATE T496b exit=0`.

## Spec deviations
none

## Follow-ups
- `str` sub-range slicing (`s[a..b]`, `s[a..=b]`, `s[..=b]`): `compiler/types/typeck.ax:8832` and `compiler/mir/builder.ax:4033` accept `TY_STR`, but `compiler/verify/verifier.ax:1037` rejects `MIR_PROJ_SUB_SLICE` on `TY_STR` with `AX_VERIFY_TYPE_MISMATCH` (`subslice projection on non-slice/array type`). Needs a follow-up task (owning `compiler/verify/`, `compiler/interp/`, native backend if needed, and `tests/run/slice_inclusive_str/`) to either enable `MIR_PROJ_SUB_SLICE` on `TY_STR` end-to-end (with SPEC-03 UTF-8 boundary rules) or reject `TY_STR` sub-ranges in `typeck.ax` with `AX_TYPE_CANNOT_INDEX`.

STATUS: COMPLETE round=0
