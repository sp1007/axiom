---
id: T162
title: Stage-1 selfhost suite fixes - port interpreter, typeck array-repeat UF, MIR bare-place parser, and gatecheck cleanup
phase: P10-selfhost
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T085, T143, T144, T156, T159, T161]
priority: 119
status: done
attempts: 1
paths: [compiler/interp, compiler/interp_opt, compiler/mir, compiler/syntax, compiler/types, compiler/verify, compiler/driver, tools/gen_encode_tests.py, tests/selfhost, tests/encode/axiom, tests/run/parity]
spec: [0167, 0150, tasks/0371, spec/decisions/ADR-0034-oracle-independence.md, spec/decisions/ADR-0035-axiomc-parity-symbols.md]
covers: [REQ-OWN-001, REQ-OWN-002]
timeout_min: 300
started: 2026-11-01 10:24:50
finished: 2026-11-02 08:29:23
---
# T162 — Stage-1 selfhost suite fixes: port interpreter, typeck array-repeat UF, MIR bare-place parser, and gatecheck cleanup

## Goal
Resolve the 8 implementation and test-hygiene defects uncovered by the Stage-1 gate (`T086`, see `_workspaces/reports/T086-report.md` lines 111–201) so that `axiomc1.exe` (built by `axiom0` from the `axiomc` bundle) passes 100% of the non-`axiom0-internal` test suite in all declared modes (`[interp]`, `[native]`, `[native-O1]`, `ui`, `golden`, `diff`, `exec`) and `python tools/gatecheck.py` exits 0.

## Scope
1. **Wrapping binary ops in port MIR interpreter (`compiler/interp/interp.ax`)**:
   - Import `MIR_BINOP_WRAPPING_ADD`, `MIR_BINOP_WRAPPING_SUB`, and `MIR_BINOP_WRAPPING_MUL` in `compiler/interp/interp.ax` (around lines 105–122) and handle them in both the signed and unsigned branches of `exec_assign_binop` (`compiler/interp/interp.ax:1389-1607`) using `w_add_u64(ua, ub)`, `w_sub_u64(ua, ub)`, and `w_mul_u64(ua, ub)` without setting `overflow` (matching `bootstrap/axiom0/src/interp/interp.c:837-846`).
2. **Unterminated unreachable join blocks (`bb_end`) in `mir_build_fn` (`compiler/mir/builder.ax` & `tests/selfhost/bundle_common.py`)**:
   - Ensure basic blocks left with `terminator.kind == MIR_TERM_NONE` (`0`) when `mir_build_fn` finishes (e.g., pre-allocated `bb_end` after an `if / else` or exhaustive `match` where all arms return/diverge) are patched to `MIR_TERM_UNREACHABLE` (or `MIR_TERM_RETURN` for an empty entry block) at the end of `mir_build_fn` in `compiler/mir/builder.ax:9665` and/or by including `"compiler.interp_opt.session"` and `"compiler.interp.interp"` in `_shim_mir_build_fn` (`tests/selfhost/bundle_common.py:505`).
3. **`AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` (`2021u16`) diagnostic preservation (`tests/selfhost/bundle_common.py` & `compiler/types/typeck.ax`)**:
   - Remove the blanket `if code == 2021u16 { return }` suppression in `_shim_diag_sink_report` (`tests/selfhost/bundle_common.py:90-95`) that silenced float type/literal/pattern and `.await` bootstrap diagnostics in `compiler.types.typeck`.
   - Remove the duplicate `HIR_ITEM_STATIC` `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` emission at `compiler/types/typeck.ax:6754` (since `HIR_ITEM_STATIC` is already reported in `compiler/interp_opt/session.ax:706` and `compiler/own_mir_verify/session.ax`, matching `axiom0`).
4. **Array repeat `[val; N]` `TY_INT_VAR` resolution (`compiler/types/typeck.ax` & `compiler/verify/verifier.ax`)**:
   - In `check_expr_array_or_index` (`compiler/types/typeck.ax:5556`), resolve `elem_ty = uf_resolve_ty(ctx, elem_ty)` after `coerce` and before `type_intern_array`.
   - In `resolve_deep_ty` (`compiler/types/typeck.ax:6644`), recurse into `TY_ARRAY` element types and re-intern `[len]resolved_elem` when the element type changes.
   - In `verify_types_compatible` (`compiler/verify/verifier.ax:580`), recurse into `ka == TY_ARRAY && kb == TY_ARRAY` when lengths match.
5. **Bare-place `MIR_OP_COPY` fallback in `.mir` text parser (`compiler/mir/mir.ax`)**:
   - In `mp_parse_operand` (`compiler/mir/mir.ax:2232-2351`), add the `else` fallback branch that sets `(*out).kind = MIR_OP_COPY` and parses a bare place via `mp_parse_place(mut_view(*p), mut_view((*out).place))` (matching `bootstrap/axiom0/src/mir/parse.c` and `vp_parse_operand` in `compiler/verify/verifier.ax`).
6. **Interpreter exit codes (`124`/`125`) and host CLI arguments in `run --interp` (`compiler/driver/pipeline.ax` & `compiler/interp_opt/session.ax`)**:
   - In `driver_execute_run_ctx` (`compiler/driver/pipeline.ax:1966-1970`), preserve interpreter exit codes `124` (step/call-depth limit) and `125` (UB detected) instead of overwriting `ctx.interp_rc` with `AX_EXIT_DIAG` (`1`) when `session_has_errors(view(ctx.sess))` is true.
   - In `session_run_interp` (`compiler/interp_opt/session.ax:1401`) and `driver_run_CheckCtx` (`compiler/driver/pipeline.ax:896`), populate the interpreter host CLI arguments (`[main_path, ...run_args]`) via `interp_host_push_arg` so `args_count()` and `arg_at()` in `compiler/interp/oracle.ax:669-700` see the interpreted program's arguments (`argc == 1 + run_args.len`) instead of the host `axiomc` process CLI arguments.
7. **Trait default method per-impl instances in `session_interp_opt_file` (`compiler/interp_opt/session.ax`)**:
   - Fix `insert_impl_alias_in_mir_map` (`compiler/interp_opt/session.ax:1132-1157`) and `session_interp_opt_file` (`compiler/interp_opt/session.ax:1220-1281`) so `T161` synthesized per-impl default-method instances (`HIR_ITEM_IMPL` members) are not aliased to an un-instantiated `HIR_ITEM_TRAIT` default method's `MirBody` (or across distinct `impl` blocks) in `mir_map`.
8. **`gatecheck.py` rule (c) inline `xfail` cleanup & `qa_axiomc_cli_edges.test` (`tests/encode/axiom` & `tests/selfhost/obj_link_driver`)**:
   - In `tests/encode/axiom/gnu_as_vectors.ax` (and `tests/encode/axiom/gen_gnu_as_twin.py`), replace the 154 inline `// xfail: AX0-FIX-ENC-...` comments inside `fn main()` with `// skip-enc: AX0-FIX-ENC-...` so `python tools/gatecheck.py` rule (c) exits 0.
   - In `tests/selfhost/obj_link_driver/qa_axiomc_cli_edges.test` (and/or `qa_axiomc_cli_edges_oracle.py`), update the test (`requires: axiom0-internal` or updated divergence expectation after `T154`) so it passes under both `axiom0` and `axiomc1`.
9. **Regenerate all selfhost bundles**:
   - Regenerate all affected selfhost bundles (`gen_*_tests.py` and `python tests/selfhost/drop/gen_drop_tests.py bundles`) so `tests/selfhost/bundles_current.test` passes.

## Acceptance
- [ ] All 7 wrapping-intrinsic interpreter tests pass under `axiomc1`: `tests/run/numeric/intrinsic_ops.ax`, `tests/run/intrinsics/native_repro.ax`, `tests/run/intrinsics/ops_table.ax`, `tests/run/parity/intrinsics/qa_intrinsics_ptr_edges.ax`, `tests/run/parity/intrinsics/wrapping.ax`, `tests/selfhost/kernel/hash_native.ax`, `tests/std/core/qa_hash_vectors.ax`.
- [ ] All 43 previously failing `AX_VERIFY_UNTERMINATED_BLOCK` `[interp]` tests (`tests/conformance/vs0/cf_if_else_chain.ax`, `tests/run/pattern/{lexer_interp,qa_nested_match,u8_exhaustive}.ax`, `tests/run/trait2/test_derive.ax`, and all 38 `tests/selfhost/**` tests) pass under `axiomc1`.
- [ ] `tests/conformance/vs0/float_unsupported.ax`, `tests/ui/numeric/float_bootstrap.ax`, and `tests/ui/typeck/bug_float_unsupported.ax` pass under `axiomc1`.
- [ ] `tests/conformance/std/0169_std_collections_map.ax` passes under `axiomc1`.
- [ ] `tests/lir/load.test` passes under `axiomc1`.
- [ ] `tests/run/basic/008-step-limit.ax`, `tests/run/basic/009-call-depth.ax`, `tests/run/host/heap/use_after_free.ax`, and `tests/run/host/io/args.ax` pass in `[interp]` mode under `axiomc1`.
- [ ] All 9 `tests/run/parity/trait_default/*.ax` tests pass in `[interp]`, `[native]`, and `[native-O1]` modes under both `axiom0` and `axiomc1`.
- [ ] `tests/selfhost/bundles_current.test` and `tests/selfhost/obj_link_driver/axiomc_e2e.test` pass (`known_divergent.txt` remains at 0 entries).
- [ ] `python tools/gatecheck.py`, `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`, and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Full test suite passes in `build-snap-T162` under `axiom0` and under a freshly built `axiomc1.exe` (`--exclude-requires axiom0-internal`); build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T162-report.md` with exact `## Files changed`.

## Out of scope
- Stage-1/Stage-2 bootstrap script (`tools/bootstrap.py`) and performance CSV (`tests/perf/selfhost.csv`), which belong to `T086`.

## Notes
- Read `_workspaces/reports/T086-report.md` lines 111–201 for exact file/line diagnostics of all 8 root causes.
- After editing `compiler/**` or `tests/selfhost/bundle_common.py`, regenerate every selfhost bundle (including `python tests/selfhost/drop/gen_drop_tests.py bundles` and `tests/selfhost/*/gen_*_tests.py`) and verify `tests/selfhost/bundles_current.test`.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-11-01 10:24:50 started (attempt 1) T162-impl
- 2026-11-02 08:29:23 accepted by QA -> done
