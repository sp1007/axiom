# T498f QA report — index assignment into immutable bindings; operand spans

## Round 0

### Checks performed

1. **Change-set & harness hygiene (`taskctl.py changes T498f`, `harness_check.py`)**:
   - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T498f`: 0 `REFUSED` lines after listing the 7 QA-added test files below; all staged files are within T498f's `paths:` (`compiler/types/typeck.ax`, `compiler/mir/builder.ax`, `tests/ui/assign_immutable_index/*`, `tests/ui/own_operand_span/*`, reports). No `bootstrap/axiom0`, `spec/`, `docs/`, or shared-file edits.
   - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK` (axiom0 freeze clean).

2. **Stage-2 / Stage-3 fixed-point build in `build-snap-T498f/`**:
   - `python tools/build_axiomc.py --out build --root . --stage 2` → `BUILD-AXIOMC OK` (`axiomc2.exe`, 8,833,536 bytes).
   - `python tools/build_axiomc.py --out build --root . --stage 3` → `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == 60c096c3ff5c8ab75676806a99421ed8a2d147b2f4ac433e15725d09dbebfb68 (8833536 bytes)`.

3. **Concrete acceptance & boundary verification (`build-snap-T498f/build/axiomc2.exe check --std-root std`)**:
   - Architect repro 1 (`hs[0].n = 5u32` and `a[0] = 9u32` on immutable `let`): emits two `AX_TYPE_ASSIGN_IMMUTABLE` diagnostics at `5:5` and `7:5`.
   - Architect repro 2 (`let u = 1u32 + hs[i].n` after `take(hs)`): emits `AX_MOVE_USE_AFTER_MOVE` at `8:20` (pointing at `hs[i].n`, not `1u32`).
   - Additional boundary checks verified directly: `(*mv)[0] = 1u32` on `mv: mut_view<view<[u32]> >` emits `AX_TYPE_ASSIGN_IMMUTABLE` at `5:5`; `mut_view(a[0..2])` on immutable `let a: [3]u32` emits `AX_TYPE_ASSIGN_IMMUTABLE` at `9:25`.
   - Own + QA UI suite fresh (`--no-cache`): `python tools/axtest.py --compiler build/axiomc2.exe --filter ui/assign_immutable_index --filter ui/own_operand_span --no-cache -j 2 --verbose` → `TOTAL 19 PASS 19 FAIL 0 SKIP 0 XFAIL 0` (12 engineer tests + 7 QA tests).
   - Native-evidence check (step 4a): not applicable to T498f's own/changed tests (all 19 are `test: ui` compile-fail / compile-pass checks; `WEAK-NATIVE: 0 in the task's own/changed tests`).

4. **Per-task gate (`taskgate.py` in `build-snap-T498f/`, `-j 2`)**:

### taskgate T498f (`tools/taskgate.py`)

- root `D:/projects/compiler/new lang/build-snap-T498f`, HEAD `9750b5f679b6`, compiler `D:/projects/compiler/new lang/build-snap-T498f/build/axiomc2.exe`, `-j 2`
- change set: 41 file(s) (working tree of `build-snap-T498f` vs HEAD: `compiler/types/typeck.ax`, `compiler/mir/builder.ax`, 19 generated selfhost bundles, 12 engineer UI tests, 7 QA UI tests, `_workspaces/reports/T498f-report.md`)
- wall time: 903.9 s (axtest 886.6 s)

| part | ids | results | PASS | FAIL | SKIP | XFAIL | CACHED |
|---|---|---|---|---|---|---|---|
| own | 19 | 19 | 19 | 0 | 0 | 0 | 0 |
| affected | 222 | 379 | 377 | 0 | 2 | 0 | 163 |
| smoke | 32 | 53 | 53 | 0 | 0 | 0 | 22 |
| **total (dedup)** | 250 | 428 | 426 | 0 | 2 | 0 | 183 |

Counts per group: `mir` (46/0), `run` (54/0), `selfhost` (40/0), `ui` (33/0), `verify` (29/0), `typeck` (23/0), `diff` (2/0), and 1/0 across all 23 remaining smoke groups (`build_native`, `conformance`, `driver`, `encode`, `fuzz`, `hir`, `inspect`, `lex`, `link`, `link2`, `lir`, `mc`, `modules`, `obj`, `opt`, `opt2`, `parse`, `perf`, `programs`, `resolve`, `std`, `tools`, `unit`).

- Affected-set derivation: `compiler/types/typeck.ax` → `tests/typeck`, `tests/ui`, `tests/selfhost/typeck*`; `compiler/mir/builder.ax` → `tests/mir`, `tests/verify`, `tests/run`, `tests/selfhost/mir*`, plus all 19 regenerated selfhost bundles; `unmatched changed files: none`.
- Smoke: `seed=2306937947`, always `run/str/hello.ax`, `ui/typeck/type_unknown.ax`, `diff/002-arithmetic.ax`.
- Cache: `CACHED 183, miss 28, uncacheable 115, stored 26, dep_source exact, verification sample seed=1090110282 n=20 of 107 hits, mismatch none, rejected {}, producer snapshot`.
- `WEAK-NATIVE: 3 in the run; 0 in the task's own/changed tests`.
- `Baseline: BASELINE OK`, `Failing ids: none`.
- `archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations`.
- `smoke-check (tests/smoke.list): OK; est. worst-case draw 27 s`.
- `axtest: TOTAL 428 PASS 426 FAIL 0 SKIP 2 XFAIL 0 (exit 0)`.
- `TASKGATE T498f exit=0`.

### Code review & boundary cross-check
- `compiler/types/typeck.ax`: `tc_check_place_mutable` cleanly handles `HIR_EXPR_FIELD`, `UNOP_DEREF`, `HIR_EXPR_TUPLE_INDEX`, and `HIR_EXPR_INDEX` (local `TY_ARRAY`, range sub-slices via `tc_expr_is_range_index`, and multi-level `TY_VIEW`/`TY_MUT_VIEW` chains per AXS-SEM-047) while preserving raw-pointer, `str`, and user `Index` behaviour. Deferred projection writes are rejected regardless of `is_init`, while whole-binding deferred init stays intact in `check_stmt_assign`. `mut_view(projection)` reuses the same walk with `AX_CAP_CONFLICT_MUT` for read-only views and `AX_TYPE_ASSIGN_IMMUTABLE` for immutable bindings.
- `compiler/mir/builder.ax`: `mb_operand_set_span` stamps `MIR_OP_COPY` / `MIR_OP_MOVE` operands with their own HIR expression span (preserving explicitly set locations and clearing stale ones in `mb_build_expr_as_operand` / `mb_build_operand`), without disturbing constants or MIR dumps.

### Findings
None.

## Files changed
- tests/ui/assign_immutable_index/qa_accepted_more.ax
- tests/ui/assign_immutable_index/qa_all_compound_ops.ax
- tests/ui/assign_immutable_index/qa_params_tuples_ranges.ax
- tests/ui/own_operand_span/qa_logical.ax
- tests/ui/own_operand_span/qa_paren_nested.ax
- tests/ui/own_operand_span/qa_rhs_sub.ax
- tests/ui/own_operand_span/qa_unary.ax

VERDICT: PASS round=0
