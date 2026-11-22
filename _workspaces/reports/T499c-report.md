# T499c report — Unify match exhaustiveness checker in `compiler/types/exhaust.ax`

## Summary
Unified match exhaustiveness and reachability checking into a single column-wise Maranget usefulness checker in `compiler/types/exhaust.ax` (`match_check_exhaustiveness` / `match_check_exhaustiveness_with_tv`, `SPEC-03`), routed all `match` scrutinees through it from `compiler/types/typeck.ax`, and deleted the duplicate checker copy (`tc_match_check_exhaust_bool_or_enum` and interval/byte helpers) and dead `if false {}` reference from `compiler/types/typeck.ax`.

### Key design choices
1. **Single Maranget usefulness engine for all scrutinee types (`compiler/types/exhaust.ax`)**:
   - `SINGLE` (`TY_TUPLE`, `TY_STRUCT`, `TY_UNIT`): single constructor with one column per tuple element or declared struct field (`0` for `()`). Struct fields are matched by declared field name; omitted fields (`..`) become wildcards.
   - `BOOL` (`TY_BOOL`): two constructors (`false` = `0`, `true` = `1`).
   - `ENUM` (`TY_ENUM`): one constructor per variant, resolving variant indices from `thir_get_pat_variant` (populated by `typeck` for `HIR_PAT_PATH` and `HIR_PAT_STRUCT`) with a symbol/span-text/interned-name fallback (`ex_resolve_variant_fallback`) when `thir.pat_variants` is unpopulated (preserving direct HIR unit tests such as `tests/selfhost/types/qa_types_exhaust.ax`). Variant tuple and struct payloads specialise recursively, closing the bare-enum soundness gap where `Opt.Some(1)` + `Opt.None` was previously accepted, and eliminating false `AX_PAT_UNREACHABLE` warnings on multiple refutable payload arms (`Opt.Some(1)`, `Opt.Some(2)`, `Opt.Some(x)`).
   - `INT` (`i8..i128`, `u8..u128`, `isize`, `usize`, unconstrained `TY_INT_VAR` defaulting to `i32`, and `char`): extended interval splitting to exact 128-bit biased unsigned `(lo: u64, hi: u64)` segments (`ExPt128`). Signed values XOR `hi` with `0x8000000000000000u64` to preserve signed order across all widths up to `i128`/`u128`. For `char` (`SPEC-03 AXS-SEM-013`), the domain is `0..=0x10FFFF` with surrogate segment `0xD800..=0xDFFF` skipped as uninhabited. Inverted/empty intervals (`a..b` with `a >= b`) produce `EXH_EMPTY` (`AX_PAT_UNREACHABLE`), while out-of-domain literals leave `EXH_UNKNOWN` so they never falsely satisfy exhaustiveness or trigger spurious cascade warnings.
   - `OPAQUE` (`str`, slices, arrays, pointers, views, functions, closures, `never`, etc.): covered only by wildcards and bindings; `TY_ERROR` returns early without cascade diagnostics.
   - Type inference integration: `match_check_exhaustiveness_with_tv` resolves column types through `TypeVarTable` (`type_vars_resolve`), so scrutinees and generic enum/struct fields unified during `check_pat` (e.g. `let n = Option.None; match n { ... }` or unsuffixed integer scrutinees) have their inferred types visible during specialization.
   - Interpreter-safe diagnostics: `emit_pat_unreachable` (`AX_PAT_UNREACHABLE`, warning) and `emit_pat_non_exhaustive` (`AX_PAT_NON_EXHAUSTIVE`, error at match expression span) allocate their message bytes directly in `sink.arena` without raw `Str` pointer casts.
2. **Thin delegation in `compiler/types/typeck.ax`**:
   - Reduced `tc_match_check_exhaustiveness` to a 1-line call to `match_check_exhaustiveness_with_tv`; deleted `tc_match_check_exhaust_bool_or_enum`, `tc_pat_interval128_at*`, `tc_exhaust_*`, `tc_is_int_or_char_kind`, unused imports, and the `if false {}` reference.
   - Superseded `match_check_exhaust_bool_or_enum`, `match_check_tuple_exhaustiveness`, and unused interval array helpers in `compiler/types/exhaust.ax` were deleted while preserving `PatInterval`, `PatInterval128`, `get_pat_interval`, and `get_pat_interval_128`.
3. **Existing expectations & tree-wide check**:
   - No existing `tests/ui` expectations changed, and no existing `compiler/`, `std/`, or `tests/` sources relied on the closed `Some(1)` + `None` soundness gap.

## Files changed
- compiler/types/exhaust.ax
- compiler/types/typeck.ax
- tests/ui/exhaust_unified/enum_refutable_payload.ax
- tests/ui/exhaust_unified/nested_enum_in_enum.ax
- tests/ui/exhaust_unified/struct_refutable_field.ax
- tests/ui/exhaust_unified/u8_range_gap.ax
- tests/ui/exhaust_unified/unreachable_after_full_cover.ax
- tests/run/exhaust_unified/enum_payloads_and_nested.ax
- tests/run/exhaust_unified/structs_and_ranges.ax
- _workspaces/reports/T499c-report.md

## Tests
All builds and test runs were executed inside `build-snap-T499c/` (`HEAD c64480a9` + 9 T499c files + regenerated selfhost bundles):

1. **Stage-2/3 compiler build & fixed point**:
   `python tools/build_axiomc.py --out build --root . --stage 2` -> `BUILD-AXIOMC OK`.
   - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == 5b5d4d11a5105b0c962c13f25dea85d5d37821187d8ce9d1f81f8c5d85cf9749` (9,004,544 bytes, `[seeded B==C]`).
   - `STAGE0-GUARD OK`: `axiomc1` and `B` produced byte-identical `.exe` on 6 smoke programs (`O1`, incl. `Xin chào thế giới`).
2. **Own, tuple, and direct selfhost exhaustiveness tests (`--no-cache`)**:
   `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache --filter exhaust_unified --filter exhaust_tuple --filter selfhost/types/qa_types_exhaust -j 2 --verbose`
   -> `TOTAL 32 PASS 32 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
   - Verified `run/exhaust_unified/*`, `run/exhaust_tuple/*`, and `selfhost/types/qa_types_exhaust.ax` PASS across `interp`, `native`, and `native-O1` with exact `stdout:`.
   - Verified `ui/exhaust_unified/*` report exact `AX_PAT_NON_EXHAUSTIVE` and `AX_PAT_UNREACHABLE` diagnostics.
3. **Mutation liveness spot-proof**:
   Mutated `stdout:` in `build-snap-T499c/tests/run/exhaust_unified/enum_payloads_and_nested.ax` (`10 20 77 0` -> `99 20 77 0`) and ran `--no-cache --filter run/exhaust_unified/enum_payloads_and_nested --verbose`:
   - Mutated: `TOTAL 3 PASS 0 FAIL 3` (`interp`, `native`, `native-O1` all failed with `stdout differs at byte 0`).
   - Restored: `TOTAL 3 PASS 3 FAIL 0` (`interp`, `native`, `native-O1` all PASS).
4. **Full `tests/ui/`, `tests/run/`, and `tests/typeck/` suites (`--gate -j 2`)**:
   `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --gate --baseline _workspaces/baseline-failures.txt --filter ui/ --filter run/ --filter typeck/ -j 2`
   -> `TOTAL 3641 PASS 3641 FAIL 0 SKIP 0 XFAIL 0`, `BASELINE OK`.
   - Also swept `tests/std/`, `tests/conformance/`, `tests/programs/`, and `tests/diff/`: zero `AX_PAT_NON_EXHAUSTIVE` or `AX_PAT_UNREACHABLE` failures across all 1,857 results.
5. **Per-task gate (`taskgate.py` at `-j 2`)**:
   `python tools/taskgate.py --task T499c --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`
   -> `TASKGATE T499c exit=0` (`wall time: 856.0 s`).
   - `axtest`: `TOTAL 175 PASS 174 FAIL 0 SKIP 1 XFAIL 0` (`own` 7 ids / 11 results; `affected` 79 ids / 124 results incl. `selfhost/typeck`, `selfhost/typeck_traits`, `selfhost/types/qa_types_exhaust.ax`, and all affected selfhost bundles; `smoke` 32 ids / 53 results; 109 dedup ids).
   - `WEAK-NATIVE: 3 in the run; 0 in the task's own/changed tests`.
   - `Baseline: BASELINE OK`, `Failing ids: none`.
   - `archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations`.
   - `smoke-check (tests/smoke.list): OK; est. worst-case draw 18 s`, `unmatched changed files: none`.
6. **Board & harness hygiene**:
   - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T499c` -> exit 0, 0 `REFUSED`.
   - `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> `HARNESS OK`.

## Spec deviations
none

## Follow-ups
none

STATUS: COMPLETE round=0
