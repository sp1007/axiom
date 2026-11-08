STATUS: COMPLETE round=0

# T617 Report: E15.5 — Loop Auto-Vectorization Legality, Capability-Disjoint Dependence Proving, Reduction Recognition & Scalar Tail/Epilogue Generation

## Summary

Implemented `compiler/opt/vectorize/mod.ax` (`module compiler.opt.vectorize`) and the verification suite in `tests/run/opt_loop_vec/` per `spec/SPEC-74-auto-vectorization.md` (`REQ-OPT-206`, `REQ-OPT-209`, `REQ-OPT-210`, `REQ-OPT-211`, `AXS-VEC-001..064`).

1. **Capability-Disjoint & SCEV Memory Dependence Proving (`SPEC-74 §4.2`, `AXS-VEC-010..017`)**:
   - Implemented `vec_prove_memory_dep_pair` and `vec_analyze_loop_legality` combining `AliasInfo` capability disjointness (`mut_view<[T]>` vs `view<[T]>` or distinct `mut_view<[T]>`, `VEC_ALIAS_CAP_DISJOINT`), `SCEV` affine iteration-space distance analysis (`VEC_ALIAS_SCEV_DISJOINT` for loop-independent `d = 0`, forward recurrences with `d >= VF`, and backward anti-dependencies `a[i] = a[i + d] + ...` where load precedes store), and raw-pointer runtime overlap guard planning (`VEC_ALIAS_RUNTIME_GUARD`).
   - Enforced hard rejection of loop-carried flow/output recurrences with `0 < d < VF` (`REASON_LOOP_CARRIED_DEP`), unproven aliasing (`REASON_UNKNOWN_ALIAS`), interior atomics/fences (`REASON_ATOMIC_BARRIER`), volatile/MMIO accesses (`REASON_VOLATILE_BARRIER`), and interior calls/drops/unwinds (`REASON_INTERIOR_CALL_OR_DROP`).

2. **Associative Integer Reduction Recognition, Strict FP Ordering & Checked Overflow Gates (`SPEC-74 §4.4`, `REQ-OPT-206`, `AXS-VEC-018..024`)**:
   - Implemented `vec_detect_reductions` recognizing single-cycle header `phi` reduction recurrences for wrapping integer `+`, `*`, `&`, `|`, `^`, `min`, `max` (`VEC_REDUCE_ADD..MAX`), assigning exact horizontal tree identity elements (`0`, `1`, `!0`, `MIN`, `MAX`), and rejecting non-associative subtraction/division/shift reductions (`REASON_NON_ASSOC_REDUCTION`), strict IEEE-754 floating-point reductions (`REASON_STRICT_FP_REDUCTION`), and trapping checked arithmetic without proven non-overflow (`REASON_CHECKED_OVERFLOW_TRAP`).

3. **Target SIMD Width Selection, Cost Model & Loop Vectorization Lowering (`SPEC-74 §5–§7`, `REQ-OPT-209..211`, `AXS-VEC-030..064`)**:
   - Implemented `vec_query_target_caps`, `vec_select_best_vf`, and `vec_evaluate_cost` querying x86-64 SSE2 (`128`-bit baseline) and AVX2 (`256`-bit when enabled) capabilities, enforcing `-O0` and `-Os` gates, and computing profitability across vector body, horizontal reduction tree, and runtime guard costs.
   - Implemented `opt_loop_vec` and `loop_vec_optimize_mir_body` with CFG construction (`trip_check`, `rt_guard`, `vec_preheader`, `vec_header`, `vec_body`, `vec_latch`, `vec_reduction_epilogue`, `scalar_tail_preheader`, and original scalar loop as the exact `N % VF` tail/fallback) and SIMD `OptInst` emission (`OPT_INST_VEC_SPLAT`, `OPT_INST_VEC_STEP_VEC`, `OPT_INST_VEC_LOAD`, `OPT_INST_VEC_STORE`, `OPT_INST_VEC_ARITH`, `OPT_INST_VEC_CMP`, `OPT_INST_VEC_SELECT`, `OPT_INST_VEC_HREDUCE`).

## Files changed

- compiler/opt/vectorize/mod.ax
- tests/run/opt_loop_vec/associative_int_reductions_and_tail.ax
- tests/run/opt_loop_vec/cap_disjoint_elementwise_and_epilogue.ax
- tests/run/opt_loop_vec/checked_overflow_in_loop_panic.ax
- tests/run/opt_loop_vec/epilogue_tail_oob_panic.ax
- tests/run/opt_loop_vec/opt_loop_vec_engine.test
- tests/run/opt_loop_vec/opt_loop_vec_oracle.py
- tests/run/opt_loop_vec/opt_loop_vec_probe.ax.in
- tests/run/opt_loop_vec/rejected_recurrence_alias_fp_and_barriers.ax

## Verification

- `python build-snap-T617/tools/axtest.py -j 1 --root build-snap-T617 --build-dir build-snap-T617/build --compiler build-snap-T617/build/axiomc2.exe run/opt_loop_vec run/opt_loops run/opt_bce run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax` -> `WEAK-NATIVE 0`, `TOTAL 73 PASS 73 FAIL 0 SKIP 0 XFAIL 0`
- `python tools/archcheck.py` -> `archcheck: 196 files scanned, 0 violations`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T617` -> verified 9 changed files within scope.

STATUS: COMPLETE round=0
