# T615 Report — E15.4: Inlining, Specialization, Devirtualization & SROA Conformance Suite

## Summary

Implemented the **E15.4 (`SPEC-73`)** end-to-end conformance and differential verification suite in `tests/conformance/p15/e15_4_inline_specialize_devirt/` covering ownership/capability-aware copy/move propagation, deep Scalar Replacement of Aggregates (`SROA`), caller-allocated `RVO`/`NRVO`, Tarjan SCC call-graph construction, 2-stage legality/cost-model inlining, interprocedural constant/closure specialization (`SpecializationKey`), three-tier concrete-receiver devirtualization (`DEVIRT_TIER_EXACT`, `DEVIRT_TIER_GUARDED`, `DEVIRT_TIER_RETAINED_DYNAMIC`), and tail-recursion loop lowering (`TCO_LEGAL` vs drop/stack-view guards).

1. **Unified Live Optimizer Engine Conformance Probe (`e15_4_inline_specialize_devirt_oracle.test`, `e15_4_inline_specialize_devirt_oracle.py`, `e15_4_inline_specialize_devirt_probe.ax.in`)**:
   - Links and executes `compiler.opt.sroa`, `compiler.opt.inline`, `compiler.opt.ipa`, `compiler.opt.devirt`, `compiler.opt.escape`, `compiler.opt.memopt`, `compiler.opt.alias`, `compiler.own.cap`, and `compiler.opt.passmgr` against frontend-lowered `MirBody`/`OptBody` fixtures.
   - Verifies all 5 E15.4 `PassManager` `TransformationContract`s (`PASS_COPY_MOVE_SROA = 13u16`, `PASS_INLINE = 14u16`, `PASS_IPA_SPECIALIZE = 15u16`, `PASS_DEVIRT = 16u16`, `PASS_TAILCALL = 17u16`).
   - Verifies deep struct/enum/fixed-array `SROA`, `RVO`/`NRVO` promotion, `SROA_BLOCK_ADDR_OBSERVABLE` and `SROA_BLOCK_DYNAMIC_INDEX` barriers, transactional verification rollback (`pass_rollbacks`), and deterministic `sroa_print`.
   - Verifies Tarjan SCC call-graph construction, `EffectSummary`/`EscapeSummary` propagation (`EFFECT_PURE` vs `Result<T, E>` normal return without `EFFECT_MAY_PANIC`), 2-stage `InlineLegality` vs `CostModel` (`INLINE_REASON_ATTR_INLINE_NEVER`, `INLINE_REASON_EXTERN_NO_BODY`, `INLINE_REASON_INDIRECT_UNPROVEN`, `INLINE_REASON_DOMAIN_MISMATCH`, `INLINE_REASON_ASYNC_AWAIT_BOUNDARY`, `INLINE_REASON_RECURSIVE_SCC_LIMIT`), bottom-up `inline_optimize_callgraph` with post-inline `SROA` cascade, dead internal function marking (`REACH_DEAD_ELIMINATED`), and deterministic `callgraph_print` & `inline_print`.
   - Verifies canonical `SpecializationKey` ordering/hashing, deterministic `ipa_spec_clone_sym` mangling, representation-equivalent sharing with function-pointer identity preservation (`ipa_can_share_representation`, never merging when `address_taken_fn == true`), `SpecializationBudget` (`max_clones_per_fn`, `max_module_growth_pct`), post-specialization cleanup, transactional rollback, and deterministic `ipa_specialize_print`.
   - Verifies 3-tier devirtualization (`DEVIRT_TIER_EXACT`, `DEVIRT_TIER_GUARDED`, `DEVIRT_TIER_RETAINED_DYNAMIC` across `DEVIRT_REASON_DYNAMIC_LOADING`, `DEVIRT_REASON_OPEN_WORLD`, `DEVIRT_REASON_EXPORT_BOUNDARY`, and `DEVIRT_REASON_TOO_MANY_TARGETS`), direct rewrite + inline/SROA cascade (`inlined_after_devirt > 0`), transactional rollback, and deterministic `devirt_print`.
   - Verifies tail-call legality (`TCO_LEGAL` self-tail-recursion and sibling tail calls vs `TCO_REASON_NOT_TAIL_POS`, `TCO_REASON_LIVE_DROP_AFTER_CALL`, and `TCO_REASON_STACK_VIEW_ESCAPE`), self-tail-recursion loop lowering (`out_edge_count == 0`, `call_count == 0`, `loop_backedge_count >= 1`), `@tailcall` diagnostic rejection, transactional rollback, and deterministic `ipa_tailcall_print`.
   - Verifies differential equivalence across `--interp`, `-O0`, `-O1 --verify-each`, and `-O2 --verify-each`, plus byte-identical `axiomc inspect --emit=optir` and `axiomc inspect --emit=memssa` dumps.

2. **Full-Pipeline Differential & `-O2 --verify-each` Conformance Fixtures (`0 WEAK-NATIVE`)**:
   - `abstraction_erasure_sroa_rvo_inline.ax` & `o2_abstraction_erasure_sroa_rvo_inline.ax`: Nested generic/closure pipelines, deep `SROA`, caller-allocated `RVO`/`NRVO` with LIFO `Drop` ordering, `Result<T, E>` normal return vs panic-free purity, and `@inline(never)` / recursive SCC termination boundaries.
   - `devirt_and_open_world_boundaries.ax` & `o2_devirt_and_open_world_boundaries.ax`: Tier 1 exact devirtualization, Tier 2 guarded polymorphic switch devirtualization, Tier 3 retained dynamic dispatch (>4 targets and opaque parameter boundaries), and function-pointer identity preservation (`address_taken_fn`).
   - `tailcall_constant_stack_and_drop_guards.ax` & `o2_tailcall_constant_stack_and_drop_guards.ax`: Deep self-tail-recursion lowered to constant-stack loop (`25,000` iterations without stack overflow), sibling tail calls, post-call `Drop` guard LIFO preservation (`TCO_REASON_LIVE_DROP_AFTER_CALL`), and stack-borrowed `view<T>`/`mut_view<T>` escape guards (`TCO_REASON_STACK_VIEW_ESCAPE`).
   - `trap_inlined_panic_and_drop_order.ax` & `o2_trap_inlined_panic_and_drop_order.ax`: Strict left-to-right call-site argument evaluation order and inner LIFO `Drop` execution before a deterministic panic (`exit: 101`).

## Files changed

- tests/conformance/p15/e15_4_inline_specialize_devirt/abstraction_erasure_sroa_rvo_inline.ax
- tests/conformance/p15/e15_4_inline_specialize_devirt/o2_abstraction_erasure_sroa_rvo_inline.ax
- tests/conformance/p15/e15_4_inline_specialize_devirt/devirt_and_open_world_boundaries.ax
- tests/conformance/p15/e15_4_inline_specialize_devirt/o2_devirt_and_open_world_boundaries.ax
- tests/conformance/p15/e15_4_inline_specialize_devirt/tailcall_constant_stack_and_drop_guards.ax
- tests/conformance/p15/e15_4_inline_specialize_devirt/o2_tailcall_constant_stack_and_drop_guards.ax
- tests/conformance/p15/e15_4_inline_specialize_devirt/trap_inlined_panic_and_drop_order.ax
- tests/conformance/p15/e15_4_inline_specialize_devirt/o2_trap_inlined_panic_and_drop_order.ax
- tests/conformance/p15/e15_4_inline_specialize_devirt/e15_4_inline_specialize_devirt_oracle.test
- tests/conformance/p15/e15_4_inline_specialize_devirt/e15_4_inline_specialize_devirt_oracle.py
- tests/conformance/p15/e15_4_inline_specialize_devirt/e15_4_inline_specialize_devirt_probe.ax.in

## Verification

- `python build-snap-T615/tools/axtest.py --root build-snap-T615 --build-dir build-snap-T615/build --compiler build-snap-T615/build/axiomc2.exe -j 1 conformance/p15/e15_4_inline_specialize_devirt` -> `TOTAL 14 PASS 14 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T615` -> exits `0` (`0 REFUSED`).
- `python build-snap-T615/tools/archcheck.py` -> exits `0`.

STATUS: COMPLETE round=0
