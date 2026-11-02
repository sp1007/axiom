---
id: T163
title: Stage-1 final suite fixes — InterpValue 256-byte capacity, TY_STRUCT/TY_ENUM typeck finalization & verification, and write_bytes_1mb timeout
phase: P10-selfhost
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T162]
blocks: [T086]
priority: 119
status: todo
attempts: 0
paths: [compiler/interp, compiler/types, compiler/verify, tests/selfhost, tests/run/native_ptr/write_bytes_1mb.ax]
spec: [0167, 0150, tasks/0371, spec/SPEC-06-types.md, spec/SPEC-07-mir.md, spec/SPEC-20-architecture.md, spec/decisions/ADR-0001-triple-test-model.md, spec/decisions/ADR-0005-bootstrap-verification-protocol.md]
spec_refs: [SPEC-06, SPEC-07, SPEC-20]
adr_refs: [ADR-0001, ADR-0005]
inv_refs: [INV-BOOT-001, INV-SEM-001, INV-MIR-001]
req_refs: [REQ-BOOT-001, REQ-STD-001]
covers: [REQ-BOOT-001, REQ-STD-001]
timeout_min: 300
---
# T163 — Stage-1 final suite fixes: InterpValue 256-byte capacity, TY_STRUCT/TY_ENUM typeck finalization & verification, and write_bytes_1mb timeout

## Goal
Resolve the final 3 root causes (8 test files / 11 entries out of 2,887 active entries) uncovered by the Stage-1 gate (`T086`, see `_workspaces/reports/T086-report.md` Section 7) so that `axiomc1.exe` passes 100% of the non-`axiom0-internal` test suite in all declared modes (`[interp]`, `[native]`, `[native-O1]`, `ui`, `golden`, `diff`, `exec`).

## Scope
1. **`InterpValue` 256-byte capacity in port MIR interpreter (`compiler/interp/value.ax` & `compiler/interp/interp.ax`)**:
   - In `bootstrap/axiom0/src/interp/host.h:57`, `AxInterpValue` has `uint64_t vals[32]` (**256 bytes**).
   - In `compiler/interp/value.ax:210`, `InterpValue` currently has `pub vals: [8]u64` (**64 bytes**), causing any interpreted by-value struct argument or local aggregate copy larger than 64 bytes (e.g., `Diagnostic` = 104 bytes in `emit_lex_diag` in `qa_lexer_corpus_neg_b.ax`, or structs in `qa_drop_d05.ax`, `qa_drop_d06.ax`, `qa_hir_desugar_and_drop.ax`, `qa_interp_opt_diff_mir_a.ax`, `qa_own_mir_diff_diag_verify_mir.ax`) to be silently truncated to 64 bytes at `compiler/interp/interp.ax:2265` and `compiler/interp/frame.ax:269,630`.
   - Increase `InterpValue.vals` from `[8]u64` to `[32]u64` (`256` bytes, matching `AxInterpValue` in `bootstrap/axiom0/src/interp/host.h:57`) in `compiler/interp/value.ax` (`value_undef` initializer `[0u64; 32]`, `value_struct` loop bound `32u32`, `vals_ptr` helper) and `compiler/interp/interp.ax` (`arg_vals: [64]InterpValue` initializer `[0u64; 32]` at line 2224), and investigate/fix any remaining interpreter issue in those 6 `selfhost/*` tests.
2. **`TY_STRUCT` / `TY_ENUM` typeck finalization & MIR verifier compatibility (`compiler/types/typeck.ax` & `compiler/verify/verifier.ax`)**:
   - `tests/std/alloc/qa_box.ax:69` declares `pub fn box_new<T>(val: T) -> Box` (unparameterized `Box`), allocating a `TY_VAR` (`?var#0`) for `Box`'s type argument (`fn(?T#0) -> Box<?var#0>`). Body checking unifies `?var#0 -> ?T#0`, but `finalize_types` (`compiler/types/typeck.ax:6830-6906`) does not resolve `TY_STRUCT` (`args`, `fields`) or `TY_ENUM` (`args`, `variant_fields`) in-place before freeing `cx.type_vars`.
   - Update `finalize_types` in `compiler/types/typeck.ax` to resolve `TY_STRUCT` (`args` and `fields[j].ty`) and `TY_ENUM` (`args` and `variants[v].fields[j].ty`) in-place via `resolve_deep_ty` without allocating new `TypeInterner` entries (preserving `TypeId` numbering and `.obj` byte-identity).
   - Update `verify_types_compatible` in `compiler/verify/verifier.ax` (`597-636`) to recurse structurally on `TY_STRUCT` and `TY_ENUM` `args` when `def_id` and `arg_count` match.
3. **Explicit timeout directive for `tests/run/native_ptr/write_bytes_1mb.ax`**:
   - `let mut buf: [1048576]u8 = [0u8; 1048576]` lowers to 3.15M LIR instructions (`6.29M` `X64MI` nodes), which `axiomc1.exe` (built at `-O0`) compiles in `39.39s` (`-O0`) and `25.88s` (`-O1`), exceeding `axtest.py`'s default `10s` timeout while producing 100% byte-identical `.obj`/`.exe` output with `axiom0`.
   - Add `// timeout: 120` to `tests/run/native_ptr/write_bytes_1mb.ax` so `[native]` and `[native-O1]` complete without timing out under `axiomc1.exe`.
4. **Regenerate all affected selfhost bundles**:
   - Regenerate all affected selfhost bundles (`tests/selfhost/bundles_current.test` 34/34 PASS) and verify `tests/selfhost/obj_link_driver/axiomc_e2e.test` passes.

## Acceptance
- [ ] All 6 `selfhost/*` tests (`tests/selfhost/drop/qa_drop_d05.ax`, `tests/selfhost/drop/qa_drop_d06.ax`, `tests/selfhost/hir/qa_hir_desugar_and_drop.ax`, `tests/selfhost/interp_opt/qa_interp_opt_diff_mir_a.ax`, `tests/selfhost/lexer/qa_lexer_corpus_neg_b.ax`, `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_verify_mir.ax`) pass in `[interp]`, `[native]`, and `[native-O1]` under both `axiom0.exe` and the rebuilt `axiomc1.exe`.
- [ ] `tests/std/alloc/qa_box.ax` passes in `[interp]`, `[native]`, and `[native-O1]` under both `axiom0.exe` and `axiomc1.exe`.
- [ ] `tests/run/native_ptr/write_bytes_1mb.ax` passes in `[interp]`, `[native]`, and `[native-O1]` under both `axiom0.exe` and `axiomc1.exe`.
- [ ] `tests/selfhost/bundles_current.test` (34/34) and `tests/selfhost/obj_link_driver/axiomc_e2e.test` pass (`known_divergent.txt` remains at 0 entries).
- [ ] `python tools/gatecheck.py`, `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`, and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T163-report.md` with exact `## Files changed`.

## Out of scope
- Stage-1/Stage-2 bootstrap script (`tools/bootstrap.py`) and performance CSV (`tests/perf/selfhost.csv`), which belong to `T086`.

## Notes
- Read `_workspaces/reports/T086-report.md` Section 7 for exact file/line diagnostics of all 3 root causes.
- In `finalize_types` (`compiler/types/typeck.ax`), resolve `TY_STRUCT` and `TY_ENUM` `args`/`fields` in-place on the existing `Type` node in `cx.interner` rather than calling `type_intern_struct`/`type_intern_enum` inside `resolve_deep_ty`, because allocating new `TypeId` entries during `resolve_deep_ty` shifts `TypeId` numbering for subsequent monomorphization types.
- After editing `compiler/**`, regenerate every affected selfhost bundle (`python tests/selfhost/drop/gen_drop_tests.py bundles` and `tests/selfhost/*/gen_*_tests.py`) and verify `tests/selfhost/bundles_current.test`.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
