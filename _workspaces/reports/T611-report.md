# T611 Report — E15.3 Loop-Invariant Code Motion (LICM), Induction Strength Reduction, Loop Unrolling/Peeling & Iterator Fusion

## Summary

Implemented `compiler/opt/loop_xform/mod.ax` (`SPEC-72 §3`, `AXS-LOOP-010..017`, `AXS-LXF-001..008`, `INV-LOOP-002`, `REQ-OPT-143..147`, `REQ-OPT-155..175`, `REQ-OPT-344`, `REQ-OPT-354`) and comprehensive differential + live engine oracle tests under `tests/run/opt_loops/`:

1. **Effect- & `MemorySSA`-Verified Loop-Invariant Code Motion (`opt_licm`, `AXS-LXF-001`, `AXS-LOOP-010`, `REQ-OPT-143..147`)**:
   - Hoists loop-invariant pure scalar computations (`OPT_INST_CONST`, `OPT_INST_COPY`, `OPT_INST_BINOP`, `OPT_INST_WRAPPING_BINOP`, `OPT_INST_UNOP`, `OPT_INST_CAST`, `OPT_INST_ADDR_OF`, `OPT_INST_LEN`, `OPT_INST_DISCRIMINANT`) into the loop's dedicated preheader.
   - Hoists `MemorySSA`- and `AliasInfo`-verified loop-invariant `OPT_INST_LOAD` instructions when `loops_can_hoist_inst` proves the memory region is unclobbered across the loop (`PROP_NO_ALIAS` provenance).
   - Hoists loop-invariant safety guards (`OPT_TERM_ASSERT` with invariant condition) to the preheader only when the guard dominates all loop exits and the loop is proven to execute at least 1 iteration (`trip_count >= 1`).
   - Strictly blocks hoisting of trapping/panicking expressions (`EFFECT_MAY_PANIC` division/modulo/checked arithmetic or unproven loads) across zero-trip or non-dominating-exit paths (`licm_blocked_traps`), clobbered memory loads (`licm_blocked_clobbers`), and observable barriers (`BARRIER_VOLATILE`, `BARRIER_ATOMIC`, `BARRIER_IO`, `BARRIER_FFI`, `BARRIER_DROP`, `BARRIER_GPU_DOMAIN`, `licm_blocked_barriers`).
2. **Overflow-Faithful Induction Variable Strength Reduction (`opt_iv_strength_reduce`, `AXS-LXF-002`, `AXS-LOOP-012`, `REQ-OPT-173`, `REQ-OPT-174`)**:
   - Replaces affine induction variable multiplications (`i * scale + offset`) with a dedicated accumulator local initialized in the preheader (`start * scale + offset`) and stepped by `step * scale` at the primary IV's latch update site.
   - Preserves Axiom's checked arithmetic semantics (`INV-LOOP-002`): checked `MIR_BINOP_MUL` is strength-reduced only when `NoOverflow` is proven across the loop's exact trip count and bit-width (`PROP_NO_OVERFLOW`); unproven checked multiplications are left intact (`iv_blocked_overflow`) so checked overflow panics fire at the exact iteration.
   - Tracks linear address-evolution candidates (`iv_addr_evolutions`) for array/slice indexed loads and stores.
3. **First-Iteration Loop Peeling (`opt_loop_peel`, `AXS-LXF-003`, `AXS-LOOP-013`)**:
   - Peels iteration `0` (`k = 1`) into the preheader when the loop has proven trip count `>= 2` and contains either an interior branch on the initial IV value (`i == start`, `i != start`) or a shifted index (`i - 1`), folding the peeled iteration's branch and advancing the remaining loop's initial IV to `start + step` so downstream `opt_bce` can eliminate shifted bounds checks.
4. **Loop Unswitching (`opt_loop_unswitch`, `AXS-LXF-004`, `AXS-LOOP-013`, `REQ-OPT-171`)**:
   - Hoists loop-invariant interior boolean branches into a preheader dispatch block branching to cloned true-path and false-path loop versions with the interior branch folded to `OPT_TERM_GOTO`, gated by `max_unswitch_block_count` and barrier absence.
5. **Cost-Bounded Full & Partial Loop Unrolling (`opt_loop_unroll`, `AXS-LXF-005`, `AXS-LOOP-013`, `REQ-OPT-169`, `REQ-OPT-170`)**:
   - Performs exact constant-trip full unrolling (`0`-trip loop elimination and `1..max_full_unroll_trip` straight-line unrolling) when `tc * inst_cnt <= max_full_unroll_insts`.
   - Performs factor-`2` partial unrolling on even constant-trip loops exceeding `max_full_unroll_trip` under `-O2`.
6. **Loop Versioning with Pure Preheader Guards (`opt_loop_version`, `AXS-LXF-006`, `AXS-LOOP-014`, `REQ-OPT-163..165`)**:
   - Synthesizes a pure boolean preheader guard (`n <= len(container)`) for symbolic single-latch loops (`0..n`) containing a slice/array bounds check `assert(i < len)`, routing the fast path to a check-eliminated loop (`PROP_IN_BOUNDS`, `bce_eliminated_after_xform`) and the slow path to an untouched fallback loop that preserves exact panic ordering on out-of-bounds inputs.
7. **Adjacent Loop Fusion & Producer-Consumer Iterator Buffer Forwarding (`opt_loop_fuse`, `AXS-LXF-007`, `AXS-LOOP-015`, `REQ-OPT-166..168`, `REQ-OPT-344`, `REQ-OPT-354`)**:
   - Fuses adjacent canonical loops with identical trip counts and pure bridge blocks when `loops_query_dependence` and scalar live-out analysis prove zero negative-distance or loop-carried cross-loop hazards and zero observable barriers.
   - Forwards producer stores `tmp[i] = val` in `L1` directly to consumer loads `x = tmp[i]` in `L2` (`iter_buffers_forwarded`) and elides dead stores into non-escaping temporary buffers (`PROP_NO_ESCAPE`, `PROP_DEAD_STORE`).
8. **Reduction, Distribution, Interchange & Vectorization Legality Analyzers + Deterministic Formatter (`AXS-LOOP-016`, `AXS-LXF-008`, `REQ-OPT-175`)**:
   - Implemented `loop_xform_recognize_reduction` (proving `reassoc_legal = true` for wrapping integer / bitwise reductions and `reassoc_legal = false` for IEEE-754 floating-point `f32`/`f64` or checked integer reductions), `loop_xform_can_distribute`, `loop_xform_can_interchange`, `loop_xform_can_vectorize_or_parallelize`, top-level `opt_loop_xform` / `loop_xform_optimize_mir_body`, and `loop_xform_print`.

## Files changed

- `compiler/opt/loop_xform/mod.ax`
- `tests/run/opt_loops/licm_sr_peel_unswitch_unroll_fuse_positive.ax`
- `tests/run/opt_loops/fusion_negative_dep_and_clobber_soundness.ax`
- `tests/run/opt_loops/licm_non_dominating_trap_panic.ax`
- `tests/run/opt_loops/versioned_loop_fallback_oob_panic.ax`
- `tests/run/opt_loops/iv_strength_reduce_checked_overflow_panic.ax`
- `tests/run/opt_loops/opt_loops_engine.test`
- `tests/run/opt_loops/opt_loops_oracle.py`
- `tests/run/opt_loops/opt_loops_probe.ax.in`

## Verification

- Snapshot build (`build-snap-T611`): `axiom0.exe`, `axiomc1.exe`, `axiomc2.exe` built cleanly (`STAGE2: PASS`).
- `python build-snap-T611/tools/axtest.py --compiler build-snap-T611/build/axiom0.exe --root build-snap-T611 -j 1 run/opt_loops`: `WEAK-NATIVE 0`, `TOTAL 16 PASS 16 FAIL 0 SKIP 0 XFAIL 0`.
- `python build-snap-T611/tools/axtest.py --compiler build-snap-T611/build/axiom0.exe --root build-snap-T611 -j 1 run/opt_bce run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax`: `PASS`.
- `python tools/archcheck.py`: `0` violations.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T611`: `0 REFUSED`.

STATUS: COMPLETE round=0
