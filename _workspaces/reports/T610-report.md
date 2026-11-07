# T610 Report — E15.3 Natural Loop Discovery, Loop Canonicalization, Scalar Evolution (SCEV) & Range/Bounds-Check Elimination (BCE)

## Summary

1. **CFG Natural Loop Discovery, Irreducible SCC Detection, `LoopSimplify` & `LCSSA` (`compiler/opt/loops/mod.ax`, `SPEC-72 §1.1-§1.4`, `AXS-LOOP-001..005`, `AXS-LOOP-017`)**:
   - Implemented `loops_discover` (`LoopTree`, `LoopDesc`, `LoopId`), identifying natural loops from dominator backedges `(latch -> header)` where `header` dominates `latch`, constructing loop block sets by reverse CFG BFS, detecting irreducible multi-entry cycles via iterative Tarjan SCC without dominator headers (`has_irreducible_cfg` / `irreducible_count`, failing closed without unsafe transformation), assembling the deterministic RPO-ordered loop nesting forest (`parent`, `first_child`, `next_sibling`, `depth`, `block_loop_map`), and computing loop exit edges and blocks (`REQ-OPT-155`, `REQ-OPT-156`, `REQ-OPT-162`, `REQ-OPT-367`).
   - Implemented `opt_loop_simplify` (`PASS_LOOP_SIMPLIFY`) and `loops_simplify_mir_body`:
     - Safely hoists `bb0` entry loop headers (`lp_hoist_entry_header_block`) so entry-header loops acquire dedicated preheaders cleanly.
     - Inserts dedicated preheaders (`lp_ensure_preheader`), merges multi-backedge loops into a single canonical latch (`lp_ensure_single_latch`), splits shared non-loop exit targets into dedicated loop-exit blocks (`lp_ensure_dedicated_exits`), and places 1-operand LCSSA `OptPhi` nodes on loop-exiting values used outside the loop (`lp_ensure_lcssa`, `REQ-OPT-159..161`).
     - Preserves `Drop` scopes, ownership move/drop-flag invariants, active `view<T>` / `mut_view<T>` capability lifetimes, `@stable_address` pins, `volatile`, `atomic`, `await`, FFI calls, and `EXEC_DOMAIN_KERNEL` GPU barriers (`BARRIER_VOLATILE`, `BARRIER_ATOMIC`, `BARRIER_IO`, `BARRIER_AWAIT`, `BARRIER_FFI`, `BARRIER_DROP`, `BARRIER_STABLE_ADDR`, `BARRIER_GPU_DOMAIN`, `AXS-LOOP-004`, `AXS-LOOP-005`).
     - Enforces `-O0` strict no-op (`OPT_PROFILE_DEBUG_O0`), `PassManager` snapshot/rollback (`passmgr_snapshot_body` / `passmgr_rollback_body`), postcondition verification (`optir_verify_contract`, `verify_mir`), and deterministic byte-equal `loops_print` with zero string literals in compiler source (`AXS-LOOP-017`).

2. **`MemorySSA`, `AliasInfo` & `EffectInfo` Loop Invariance & Loop-Carried Dependence Queries (`compiler/opt/loops/mod.ax`, `SPEC-72 §3.1-§3.3`, `AXS-LOOP-010..011`, `REQ-OPT-143..147`)**:
   - Implemented `loops_is_value_invariant`, `loops_region_clobbered_in_loop`, `loops_can_hoist_inst`, and `loops_query_dependence` (`LoopMemDep`: `DEP_NONE`, `DEP_LOOP_INDEPENDENT`, `DEP_RAW_FLOW`, `DEP_WAR_ANTI`, `DEP_WAW_OUTPUT`, `DEP_UNKNOWN`).
   - Enforces purity (`EFFECT_PURE` / `EFFECT_READ_ONLY` without `EFFECT_PANIC`, `EFFECT_DIV_ZERO`, `EFFECT_NON_TERM`, `EFFECT_VOLATILE`, `EFFECT_ATOMIC`, `EFFECT_IO`, `EFFECT_FFI`, `EFFECT_AWAIT`, or unchecked traps unless dominating all loop exits), `MemorySSA` loop-external `mem_use` / `AliasInfo` `NoAlias` (`CERTAINTY_PROVEN`) clobber checks across all loop instructions and `OPT_TERM_CALL` / `OPT_TERM_DROP` terminators, and exact affine stride/offset distance & GCD disambiguation (`eo[i*2]` vs `eo[i*2+1]` -> `DEP_NONE`, `dep[i+1]` vs `dep[i]` -> `DEP_RAW_FLOW` with `distance = 1`, `CERTAINTY_PROVEN`) while rejecting indirectly mutated local indices.

3. **Overflow-Faithful Scalar Evolution (`SCEV`) (`compiler/opt/loops/mod.ax`, `SPEC-72 §1.5-§1.7`, `AXS-LOOP-006`, `REQ-OPT-155..158`, `REQ-OPT-190`, `REQ-OPT-368`)**:
   - Implemented `scev_analyze_tree` and `scev_classify_value` (`ScevExpr`: `SCEV_CONST`, `SCEV_INVARIANT`, `SCEV_ADD_REC`, `SCEV_ADD`, `SCEV_MUL`, `SCEV_MAX`, `SCEV_UNKNOWN`; `InductionVar`; `ScevTripCount`: `TRIP_CONST`, `TRIP_SYMBOLIC`, `TRIP_UPPER_BOUNDED`, `TRIP_INFINITE`, `TRIP_UNKNOWN`).
   - Strictly separates `ARITH_CHECKED`, `ARITH_WRAPPING`, `ARITH_SATURATING`, and `ARITH_PROVEN_NSW_NUW`: `wrapping_add` / `wrapping_sub` / `wrapping_mul` recurrences never receive `no_wrap_proven = true`, whereas checked latch arithmetic guarded by dominating `!overflow` assertions (`OPT_INST_CHECKED_BINOP` -> `OPT_TERM_ASSERT`) or strict loop-exit comparisons (`i < bound` with unit step `+1` / `k > 0` with unit step `-1`) upgrades to `ARITH_PROVEN_NSW_NUW`.
   - Computes proven constant, symbolic, upper-bounded, infinite, and unknown trip counts across both canonical `OPT_TERM_BRANCH` and frontend-lowered `OPT_TERM_SWITCH_INT` (`switch_vals[0] == 1`) boolean loop guards, plus derived affine induction variables (`a * i + b`).

4. **Dominating `RangeInfo`, Sub-Range Disjointness & Proof-Gated Bounds-Check Elimination (`compiler/opt/bce/mod.ax`, `SPEC-72 §2`, `AXS-BCE-001..006`, `REQ-OPT-001`, `REQ-OPT-026`, `REQ-OPT-125..142`, `REQ-OPT-189`, `REQ-OPT-190`, `REQ-OPT-311`, `REQ-OPT-342`)**:
   - Implemented `range_build_info` (`RangeInfo`, `ValueRange`, `SymbolicBound`, `LengthFact`, `SubsliceRangeFact`), propagating constant intervals, bitwise masks (`idx & mask`), unsigned remainders (`idx % c`), unsigned right shifts (`idx >> sh`), widening integer casts, `SCEV` induction bounds, and dominating branch/assert guards (including recursive short-circuit `&&` / `||` 2-arm boolean `OptPhi` trees).
   - Tracks `LEN_KIND_FIXED_ARRAY` (`[N]T`), `LEN_KIND_SLICE_VIEW` (`view<[T]>`, `mut_view<[T]>`, `str`), and `LEN_KIND_VEC_LEN` (both concrete and pre-monomorphization generic `Vec<T>.len`), proving cross-read length equivalence (`bce_lengths_equal_at`) via CFG dominance + backward all-paths clobber verification (`bce_path_unclobbered_between`) as well as non-escaped immutable parameter/local slice descriptors across short-circuit `&&` guards, while rejecting mutable non-SSA inline `Vec.len` reads when `v.len` can be mutated in the loop (`oob_vec_shrink_in_loop_panic`).
   - Implemented `bce_prove_diff_le` (bounded DFS over proven non-negative affine difference chains `x <= y + d`) and `bce_prove_subrange_disjoint` (`[0..mid)` vs `[mid..len)` -> `ALIAS_NO_ALIAS`, `REGION_DISJOINT`, `CERTAINTY_PROVEN`, `ALIAS_REASON_RANGE_DISJOINT`; raw pointers -> `ALIAS_UNKNOWN`, `ALIAS_REASON_RAW_PTR_PROVENANCE`).
   - Implemented `opt_bce` (`PASS_BCE`) and `bce_optimize_mir_body`, rewriting `OPT_TERM_ASSERT` to `OPT_TERM_GOTO` **only** at `CERTAINTY_PROVEN`, recording `ProofProvenance` (`PROP_IN_BOUNDS`, `CERTAINTY_PROVEN`, `ANALYSIS_RANGE_INFO`, `PASS_BCE`), pruning unreachable panic blocks cleanly, preserving `-O0` checks verbatim, verifying postconditions with `PassManager` rollback protection, and providing deterministic `bce_print`.

5. **Differential Execution & Direct Compiler Engine Verification (`tests/run/opt_bce/`)**:
   - Added 2 positive fixtures (`canonical_loops_and_bce_positive.ax`, `vec_bounds_and_descending_loops.ax`) covering UTF-8 Vietnamese banners, fixed-array bitmask indexing, 3-way zipped slice loops, guarded signed indices, descending `Vec<T>` / slice loops, multi-latch / entry-header canonicalization, and per-iteration + nested `Drop` ordering.
   - Added 5 negative panic fixtures (`oob_dynamic_index_panic.ax`, `oob_signed_negative_index_panic.ax`, `oob_wrapping_stride_panic.ax`, `oob_indirect_mut_index_panic.ax`, `oob_vec_shrink_in_loop_panic.ax`) asserting identical out-of-bounds panic behavior across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`.
   - Added `opt_bce_engine.test` (`opt_bce_oracle.py` + `opt_bce_probe.ax.in`) directly exercising `compiler.opt.loops` and `compiler.opt.bce` across `-O0 --verify-each`, `-O1`, and `-O2 --verify-each`, checking all loop discovery/irreducible/canonicalization/LCSSA/barrier invariants, `MemorySSA`/`AliasInfo`/`EffectInfo` hoisting & dependence queries, `SCEV` overflow modes & trip-count lattice, positive BCE eliminations + post-pass `verify_mir` / `verify_mir_own` / `verify_mir_cap` / `mir_drop_elaborate` / `verify_mir_drop_flags`, zero false-positive eliminations across all 6 negative hazard patterns, and deterministic `--emit=optir` / `--emit=memssa`.

## Requirement Coverage

| Requirement | Spec Anchor | Implementation & Verification |
| --- | --- | --- |
| `REQ-OPT-143` | `SPEC-72 §1.4, §3.2` (`AXS-LOOP-005`, `AXS-LOOP-010`) | `lp_scan_loop_barriers` & `loops_can_hoist_inst` enforce `volatile`, `atomic`, `io`, `await`, `ffi`, `Drop`, `@stable_address`, GPU domain, and trap-safety barriers (`compiler/opt/loops/mod.ax`, `opt_bce_probe.ax.in`). |
| `REQ-OPT-144..147` | `SPEC-72 §3.1-§3.3` (`AXS-LOOP-010..011`) | `loops_region_clobbered_in_loop`, `loops_can_hoist_inst`, and `loops_query_dependence` integrate `MemorySSA`, `AliasInfo`, `EffectInfo`, and affine IV stride/distance disambiguation (`DEP_NONE`, `DEP_RAW_FLOW` dist=1, indirect-mutation rejection) (`compiler/opt/loops/mod.ax`, `opt_bce_probe.ax.in`). |
| `REQ-OPT-155..158` | `SPEC-72 §1.1-§1.7` (`AXS-LOOP-001`, `AXS-LOOP-006`) | `loops_discover`, `scev_analyze_tree`, and `scev_classify_value` construct `LoopTree`, affine add-recurrences `{start, +, step}`, derived IVs, and `ScevTripCount` (`TRIP_CONST`, `TRIP_SYMBOLIC`, `TRIP_UPPER_BOUNDED`, `TRIP_INFINITE`, `TRIP_UNKNOWN`) (`compiler/opt/loops/mod.ax`, `opt_bce_probe.ax.in`). |
| `REQ-OPT-159..162` | `SPEC-72 §1.2-§1.4` (`AXS-LOOP-002..004`) | `opt_loop_simplify` inserts preheaders (including `bb0` header hoisting), merges latches, splits dedicated exits, places LCSSA phis, skips irreducible SCCs safely, and preserves ownership/capability/`Drop` invariants (`compiler/opt/loops/mod.ax`, `opt_bce_probe.ax.in`). |
| `REQ-OPT-189` | `SPEC-72 §2.1-§2.6` (`AXS-BCE-001..006`) | `range_build_info`, `opt_bce`, and `bce_optimize_mir_body` prove dominating guard/IV bounds for `[N]T`, `view<[T]>`, `mut_view<[T]>`, and `Vec<T>`, emit `PROP_IN_BOUNDS` `ProofProvenance`, preserve `-O0` checks, and retain all unproven checks (`compiler/opt/bce/mod.ax`, `tests/run/opt_bce/*`). |
| `REQ-OPT-190` | `SPEC-72 §1.5, §2.3` (`AXS-LOOP-006`, `AXS-BCE-003`) | Strict checked vs wrapping/saturating separation (`ARITH_WRAPPING` never marked `no_wrap_proven`; signed negative & wrapping stride indices never eliminated) (`compiler/opt/loops/mod.ax`, `compiler/opt/bce/mod.ax`, `oob_signed_negative_index_panic.ax`, `oob_wrapping_stride_panic.ax`). |
| `REQ-OPT-342` | `SPEC-72 §2.4-§2.5` (`AXS-BCE-004..005`) | Zero-cost safe `[N]T` / `view<[T]>` / `mut_view<[T]>` / `Vec<T>` bounds elimination and `[0..mid)` / `[mid..len)` half-open subslice `NoAlias` disjointness (`bce_prove_subrange_disjoint`) (`compiler/opt/bce/mod.ax`, `opt_bce_probe.ax.in`). |

## Files changed

- compiler/opt/bce/mod.ax
- compiler/opt/loops/mod.ax
- tests/run/opt_bce/canonical_loops_and_bce_positive.ax
- tests/run/opt_bce/oob_dynamic_index_panic.ax
- tests/run/opt_bce/oob_indirect_mut_index_panic.ax
- tests/run/opt_bce/oob_signed_negative_index_panic.ax
- tests/run/opt_bce/oob_sroa_vec_branch_shrink_panic.ax
- tests/run/opt_bce/oob_sroa_vec_loop_shrink_panic.ax
- tests/run/opt_bce/oob_vec_shrink_in_loop_panic.ax
- tests/run/opt_bce/oob_wrapping_stride_panic.ax
- tests/run/opt_bce/opt_bce_engine.test
- tests/run/opt_bce/opt_bce_oracle.py
- tests/run/opt_bce/opt_bce_probe.ax.in
- tests/run/opt_bce/qa_round1_soundness_regressions.ax
- tests/run/opt_bce/vec_bounds_and_descending_loops.ax

## Verification

- Stage-1, Stage-2 (`O1`), and Stage-3 (`O1`) self-host fixed-point build in `build-snap-T610`:
  - `python build-snap-T610/tools/build_axiomc.py --root build-snap-T610 --out build-snap-T610/build --stage 3 --force`:
    - `STAGE1 OK`: `19860480` bytes, `sha256=03a2ed6623553b59`
    - `STAGE2 (O1) OK`: `6142976` bytes, `sha256=3d2e5f3db21faa8f`
    - `STAGE3 (O1) OK`: `6142976` bytes, `sha256=3d2e5f3db21faa8f`
    - `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == 3d2e5f3db21faa8f70435d646a79a1dd02415b37ee57c41acc733a949620acb6`
- Direct oracle & differential suite (`-j 1`):
  - `python build-snap-T610/tests/run/opt_bce/opt_bce_oracle.py build-snap-T610/build/axiomc2.exe build-snap-T610/build build-snap-T610/build/tmp_bce build-snap-T610`: `OPT-LOOPS-SCEV-BCE-ENGINE-OK` (exit `0`).
  - `python build-snap-T610/tools/axtest.py --root build-snap-T610 --compiler build-snap-T610/build/axiomc2.exe --build-dir build-snap-T610/build --exclude-requires axiom0-internal -j 1 -v run/opt_bce`: `WEAK-NATIVE 0`, `TOTAL 22 PASS 22 FAIL 0 SKIP 0 XFAIL 0`.
- Optimizer, `OptIR`, `PassManager`, alias/memopt, self-host optimizer, MIR, verifier, and intrinsics regression suites (`-j 1`):
  - `python build-snap-T610/tools/axtest.py --root build-snap-T610 --compiler build-snap-T610/build/axiomc2.exe --build-dir build-snap-T610/build --exclude-requires axiom0-internal -j 1 run/opt_alias run/opt_passmgr run/optir_ssa selfhost/opt mir verify run/intrinsics`: `WEAK-NATIVE 0`, `TOTAL 198 PASS 192 FAIL 0 SKIP 6 XFAIL 0`.
- Repository gates:
  - `python tools/archcheck.py`: `0 violations`.
  - `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `COVERAGE OK` (`gaps: 0`).
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T610`: exit `0` (`0 REFUSED`).

## Round 1

### Root-Cause Fixes for Round 0 QA Findings

1. **Finding 1 — `Vec<T>.len` Soundness Across SROA-Promoted `OptPhi`s & Mutated Memory Paths (`compiler/opt/bce/mod.ax`, `SPEC-72 §2 AXS-BCE-002`, `AXS-BCE-004`, `REQ-OPT-189`)**:
   - Added `is_sroa_ssa: bool` on `LengthFact` and set `is_readonly_view: false` on all `LEN_KIND_VEC_LEN` facts (removing the unsound inline `OPT_INST_BINOP` block that previously attached `LengthFact` onto view/struct container `OptValueId`s).
   - Tightened `bce_lengths_equal_at`: peels trivial copies and 1-arity LCSSA phis via `lp_peel_copy_and_lcssa`, checks `opt_type_bits > 0` before `pv1.v == pv2.v`, immediately returns `false` whenever `pv1.v != pv2.v` and either side is `is_sroa_ssa` or `OPT_LOCAL_SROA` (preventing distinct SROA SSA `.len` values or join/header `OptPhi`s from ever being conflated across `v.len = 0` mutations), and enforces `check_mem = (k1 == LEN_KIND_VEC_LEN)` so non-SROA `Vec.len` facts never fall back to `bce_local_immutable_at`.
   - Updated `bce_op_is_non_ssa_mem_read` to mirror `opt_place_to_slot` (`local_modes`, `local_addr_taken`, `local_sroa_count`) and hardened `bce_inst_clobbers_len_state` via `bce_place_writes_local_directly` (catching projected field writes `v.len = 0` where `proj_count == 1, MIR_PROJ_FIELD`).
   - Added `InlineVecBound` + `bce_prove_against_inline_vec_bounds` so inline non-SSA `i < (*v).len` guards are tracked with exact `(cmp_bb, cmp_inst_idx, region_place)` provenance and proven **only** when `bce_path_unclobbered_between(..., check_mem = true, ...)` holds both from the guard to the check read and from the check read to the `OPT_TERM_ASSERT` site.

2. **Finding 2 — `bce_prove_subrange_disjoint` Base Slice SSA Identity & Rebinding Soundness (`compiler/opt/bce/mod.ax`, `SPEC-72 §2 AXS-BCE-005`, `REQ-OPT-141`, `REQ-OPT-142`)**:
   - Added `bce_local_is_single_def_unescaped(body, info, loc)` (verifying unescaped single direct definition across reachable instructions/terminators while allowing dereferenced slice element writes `(*sub)[i] = x`) and restricted `bce_resolve_root_local_chain` so `cur -> next_loc` only traverses unescaped single-def copies/whole-container borrows.
   - Extended `SubsliceRangeFact` with `def_inst_idx`, `base_ssa: OptValueId`, and `is_array_root: bool`, resolving the exact scalar SSA value of the base slice view at sub-slice creation via clobber-aware `bce_resolve_ssa_local_at` (which also checks `OPT_TERM_CALL` / `OPT_TERM_DROP` terminators along `idom`).
   - Updated `bce_extract_place_slice_or_index` and `bce_prove_subrange_disjoint` to require `opt_dominates(sf.def_bb, at_bb)`, safe projection shapes, single-def unescaped base locals for direct deref slice/index places, and `root_a == root_b && is_arr_a == is_arr_b && (is_arr_a || (base_ssa_a.v != OPT_VALUE_NONE && base_ssa_a.v == base_ssa_b.v))`. Rebinding `mv` between `left = mv[0..2]` and `right = mv[2..4]` now produces distinct `base_ssa` values and conservatively returns `ALIAS_MAY_ALIAS`.

3. **Finding 3 — `loops_query_dependence` Exact SSA Affine IV Resolution & Base Container Stability (`compiler/opt/loops/mod.ax`, `SPEC-72 §1.5 AXS-LOOP-010`, `REQ-OPT-146`)**:
   - Replaced `MirLocalId`-based index peeling (`lp_peel_index_local_copy` / `lp_extract_local_affine_iv`) with program-point-exact SSA resolution `lp_resolve_ssa_local_at(lp, body, info, loc, pt)` and `lp_extract_ssa_affine_iv(tree, lp, body, idx_val, ...)` matching `InductionVar.ssa_val` strictly by `OptValueId`.
   - Registered proven non-wrapping primary IV `latch_val` (`%i_phi + step`) as a derived IV (`offset_expr = step_idx`) in `scev_analyze_loop` (with commutative `c + piv` support and `ssa_val` deduplication), so `dep[i] = 99; i = i + 1; after_inc = dep[i];` resolves `%i_phi` (`off = 0`) vs `%i_latch` (`off = 1`) and proves `DEP_WAR_ANTI` with `distance = 1` (`CERTAINTY_PROVEN`) instead of unsound `DEP_LOOP_INDEPENDENT`.
   - Added `lp_base_container_stable_in_loop` to reject loop-rebound slice views (`proj_count == 2` with `loops_local_written_in_loop`) and whole-local array overwrites/drops, returning `DEP_UNKNOWN` on `mv[odd] = 11; mv = mv[1..n]; mv[even] = 22;`.

4. **Finding 4 — 1-Based `LoopDesc.depth` Contract (`compiler/opt/loops/mod.ax`, `SPEC-72 §1.1`)**:
   - Initialized `let mut d: u32 = 1u32;` in `loops_discover` so top-level natural loops have `depth == 1` and nested loops have `depth == parent.depth + 1` (`2, 3, ...`), and updated inner-to-outer LCSSA iteration bounds accordingly (`while d_iter > 1u32`).

### Round 1 Verification

- **New Regression Tests (`tests/run/opt_bce/`)**:
  - Extended `opt_bce_oracle.py` and `opt_bce_probe.ax.in` with direct API assertions for Finding 1 (`pos_sroa_vec_read`, `neg_sroa_vec_len_branch`, `neg_sroa_vec_shrink_in_loop`, `neg_mem_vec_len_branch`), Finding 2 (`bug2_rebound_subslice_overlap` -> `ALIAS_MAY_ALIAS`), Finding 3a (`bug3a_post_inc_dep` -> `DEP_WAR_ANTI`, `distance = 1`, `CERTAINTY_PROVEN`), Finding 3b (`bug3b_rebound_slice_dep` -> `DEP_UNKNOWN`), and Finding 4 (`(*lp3).depth == 1`, `(*outer_lp).depth == 1`, `(*inner_lp).depth == 2`).
  - Added standalone differential run/panic fixtures: `qa_round1_soundness_regressions.ax` (`stdout` verified across `--interp`, `-O0`, `-O1`, `-O2 --verify-each`), `oob_sroa_vec_branch_shrink_panic.ax` (`exit: 101`), and `oob_sroa_vec_loop_shrink_panic.ax` (`exit: 101`).
- **Stage-3 (`O1`) Fixed-Point Bootstrap (`build-snap-T610`)**:
  - `python build-snap-T610/tools/build_axiomc.py --root build-snap-T610 --out build-snap-T610/build --stage 3 --opt O1 --force`:
    - `STAGE1 OK`: `20468736` bytes, `sha256=86e62ef046c02b7f`
    - `STAGE2 (O1) OK`: `6334464` bytes, `sha256=15086a66d9926d32`
    - `STAGE3 (O1) OK`: `6334464` bytes, `sha256=15086a66d9926d32`
    - `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == 15086a66d9926d321e4ff36edef002a33e91445f9bbf591b4ffd94ea1bdfabfb`
- **Test Suites (`-j 1` inside `build-snap-T610`)**:
  - `python build-snap-T610/tools/axtest.py --root build-snap-T610 --compiler build-snap-T610/build/axiomc2.exe --build-dir build-snap-T610/build --exclude-requires axiom0-internal -j 1 -v run/opt_bce`: `WEAK-NATIVE 0`, `TOTAL 31 PASS 31 FAIL 0 SKIP 0 XFAIL 0`.
  - `python build-snap-T610/tools/axtest.py --root build-snap-T610 --compiler build-snap-T610/build/axiomc2.exe --build-dir build-snap-T610/build --exclude-requires axiom0-internal -j 1 run/opt_alias run/opt_passmgr run/optir_ssa run/opt_scalar run/opt_effects selfhost/opt run/intrinsics/ ui/intrinsics/unknown_intrinsic.ax`: `WEAK-NATIVE 0`, `TOTAL 85 PASS 85 FAIL 0 SKIP 0 XFAIL 0`.
- **Repository Gates**:
  - `python tools/archcheck.py`: `0 violations`.
  - `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `COVERAGE OK` (`gaps: 0`).
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T610`: exit `0` (`0 REFUSED`).

## Round 2

### Root-Cause Fixes for Round 1 QA Findings

1. **Shared Root Cause — Pruned SSA Omission of Join/Header `OptPhi`s on `MirPlace`-Only Local Reads (`compiler/opt/optir/mod.ax:2768`)**:
   - `optir_construct_ssa` builds Cytron pruned SSA (`live_in[y, slot]` gated on scalar `OptValueId` uses). When a `MirLocalId` (`mv`, `lo`/`hi`, or `idx`) is read only inside a `MirPlace` (`&(*mv)[2..4]`, `buf[lo..4]`, `dep[idx]`) without any downstream scalar `OptValueId` read, `optir_construct_ssa` omits the `OptPhi` at diamond join blocks and loop headers (`phi_count == 0`). Walking `idom` alone therefore skipped non-dominating diamond branches (`if c { mv = buf; }`, `if c { idx = i + 1; }`) and loop backedges (`while k < n { mv = buf; ... }`).

2. **Finding 1 — All-CFG-Paths Clobber Verification for `bce_resolve_ssa_local_at` & Sub-Slice Facts (`compiler/opt/bce/mod.ax`, `SPEC-72 §2.5 AXS-BCE-005`, `REQ-OPT-141`, `REQ-OPT-142`, `REQ-OPT-342`)**:
   - Added `BCE_DEF_NONE..BCE_DEF_PARAM`, `bce_inst_clobbers_scalar_local`, `bce_term_clobbers_scalar_local`, `bce_block_range_clobbers_scalar_local`, and `bce_scalar_local_unclobbered_from_def` (backward BFS over all reachable CFG predecessors from `(at_bb, before_inst)` to `(def_kind, def_bb, def_i)`, covering diamond branches, loop backedges, `OPT_TERM_CALL` continuation vs unwind edges, `StorageLive`/`StorageDead`, and entry-block backedges for `BCE_DEF_PARAM`).
   - Updated `bce_resolve_ssa_local_at` to reject address-taken, non-`OPT_LOCAL_SCALAR`, `mut_borrow_taken`, `raw_addr_exposed`, `escaped_external`, or `is_fixed_mmio` locals, skip synthetic LCSSA `OptPhi`s (`slot_idx == OPT_PROJ_NONE`), and require `bce_scalar_local_unclobbered_from_def` on every candidate definition (`base_ssa`, `from_local`, `to_local`, and `index_local`).
   - Hardened `bce_collect_length_and_subslice_facts`, `bce_extract_place_slice_or_index`, `bce_inst_clobbers_len_state` (`OPT_FLAG_STORAGE_LIVE | OPT_FLAG_STORAGE_DEAD`), `bce_local_immutable_at` (`bce_place_writes_local_directly`), and `bce_path_unclobbered_between` (`src_loc1` and `src_loc2` checked across all intermediate CFG blocks).

3. **Finding 2 — All-CFG-Paths Clobber Verification for `lp_resolve_ssa_local_at` & Loop Dependence/Hoisting (`compiler/opt/loops/mod.ax`, `SPEC-72 §3.2-§3.3 AXS-LOOP-010`, `REQ-OPT-145..147`)**:
   - Added `LP_DEF_NONE..LP_DEF_PARAM`, `lp_place_writes_local_directly`, `lp_inst_clobbers_scalar_local`, `lp_term_clobbers_scalar_local`, `lp_block_range_clobbers_scalar_local`, and `lp_scalar_local_unclobbered_from_def`, and updated `lp_resolve_ssa_local_at` so `loops_query_dependence` verifies zero clobbers across all reachable CFG paths (returning `OPT_VALUE_NONE` -> `DEP_UNKNOWN` / `CERTAINTY_UNKNOWN` whenever `index_local` is rebound on a diamond branch or loop path without a join `OptPhi`).
   - Hardened `loops_local_has_indirect_mutation`, `loops_local_written_in_loop` (`StorageLive`/`StorageDead`, `OPT_INST_VOLATILE_STORE`, `OPT_INST_INSERT_FIELD`, `OPT_INST_BLACK_BOX`, `OPT_INST_ZEROIZE`), `loops_can_hoist_inst` (`MIR_PROJ_SUB_SLICE` `from_local`/`to_local` loop-write check), and `lp_base_container_stable_in_loop`.

### Files changed

- compiler/opt/bce/mod.ax
- compiler/opt/loops/mod.ax
- tests/run/opt_bce/opt_bce_oracle.py
- tests/run/opt_bce/opt_bce_probe.ax.in
- tests/run/opt_bce/qa_round1_soundness_regressions.ax

### Round 2 Verification

- **New Regression Tests (`tests/run/opt_bce/`)**:
  - `opt_bce_oracle.py` + `opt_bce_probe.ax.in`:
    - Added Synthetic MIR Blob 8 (`2A2`) constructing a loop with a diamond rebind of `MirProjection.index_local` `_3` where `bb4.phi_count == 0` is explicitly asserted alongside `loops_query_dependence == DEP_UNKNOWN` (`CERTAINTY_UNKNOWN`).
    - Added frontend-lowered Blob 7 regression probes (`probe_verify_rebound_subslice_may_alias` and `2B` `fn_seen == 9..13`) verifying `ALIAS_MAY_ALIAS` on conditional diamond rebind (`bug2a_cond_rebind`), intervening loop rebind (`bug2b_loop_rebind`), loop backedge rebind (`bug2c_backedge_rebind`), conditional `from_local` bound rebind (`bug2d_cond_rebind_lo`), and `DEP_UNKNOWN` (`CERTAINTY_UNKNOWN`) on frontend conditional `index_local` rebind (`bug_r1_f2_cond_idx_dep`).
  - `qa_round1_soundness_regressions.ax`: extended differential execution fixture (`--interp`, `-O0`, `-O1`) with `bug2a_cond_rebind`, `bug2b_loop_rebind`, and `bug_r1_f2_cond_idx_dep` (`QA_R1_TOTAL=813`).
- **Stage-3 (`O1`) Fixed-Point Bootstrap (`build-snap-T610`)**:
  - `python build-snap-T610/tools/build_axiomc.py --root build-snap-T610 --out build-snap-T610/build --stage 3 --force`:
    - `STAGE1 OK`: `20468736` bytes, `sha256=86e62ef046c02b7f`
    - `STAGE2 (O1) OK`: `6334464` bytes, `sha256=15086a66d9926d32`
    - `STAGE3 (O1) OK`: `6334464` bytes, `sha256=15086a66d9926d32`
    - `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == 15086a66d9926d321e4ff36edef002a33e91445f9bbf591b4ffd94ea1bdfabfb`
- **Test Suites (`-j 1` inside `build-snap-T610`)**:
  - `python build-snap-T610/tools/axtest.py --root build-snap-T610 --compiler build-snap-T610/build/axiomc2.exe --build-dir build-snap-T610/build --exclude-requires axiom0-internal -j 1 -v run/opt_bce`: `WEAK-NATIVE 0`, `TOTAL 31 PASS 31 FAIL 0 SKIP 0 XFAIL 0`.
  - `python build-snap-T610/tools/axtest.py --root build-snap-T610 --compiler build-snap-T610/build/axiomc2.exe --build-dir build-snap-T610/build --exclude-requires axiom0-internal -j 1 run/opt_alias run/opt_passmgr run/optir_ssa run/opt_scalar run/opt_effects selfhost/opt run/intrinsics/ ui/intrinsics/unknown_intrinsic.ax`: `WEAK-NATIVE 0`, `TOTAL 85 PASS 85 FAIL 0 SKIP 0 XFAIL 0`.
- **Repository Gates**:
  - `python tools/archcheck.py`: `0 violations`.
  - `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `COVERAGE OK` (`gaps: 0`).
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T610`: exit `0` (`0 REFUSED`).

## Post-Unblock Fixes (`ADR-0037` / Round 2 QA Findings 1 & 2)

1. **Finding 1 — `OPT_INST_DISCRIMINANT` Memory-Read Hoisting Gate in `loops_can_hoist_inst` (`compiler/opt/loops/mod.ax:3017-3059`, `SPEC-72 §1.5 AXS-LOOP-011`, `ADR-0037 §1`, `REQ-OPT-143..147`)**:
   - Imported `OPT_INST_DISCRIMINANT` and `OPT_INST_AGGREGATE` from `compiler.opt.optir` in `compiler/opt/loops/mod.ax`.
   - Included `opc == OPT_INST_DISCRIMINANT` (and `OPT_INST_EXTRACT_FIELD`) alongside `OPT_INST_LOAD` and `OPT_INST_LEN` in `loops_can_hoist_inst` (`compiler/opt/loops/mod.ax:3017`) so `_d = discriminant(place)` checks `loops_local_written_in_loop` on `inst.rhs_place.local` and any dynamic `MIR_PROJ_INDEX` / `MIR_PROJ_SUB_SLICE` operand locals, enforces the `rreg.cap_mode == CAP_MODE_RAW_PTR` zero-trip trap guard (`proven_nonzero_trip && lp_dominates_all_exits`), and runs `loops_region_clobbered_in_loop`.

2. **Finding 2 — Whole-Aggregate `MemoryDef` (`OPT_INST_AGGREGATE` with `place.proj_count == 0`) Clobber Checks (`compiler/opt/bce/mod.ax:1200-1220`, `compiler/opt/loops/mod.ax:2837-2869`, `compiler/opt/loops/mod.ax:3770-3774`, `SPEC-72 AXS-BCE-004`, `AXS-LOOP-011`, `ADR-0037 §2`, `REQ-OPT-146`, `REQ-OPT-189`, `REQ-OPT-342`)**:
   - In `bce_inst_clobbers_len_state` (`compiler/opt/bce/mod.ax`), imported `OPT_INST_AGGREGATE` and updated `writes_mem_or_proj` so any `MIR_STMT_ASSIGN` (`opc != OPT_INST_NOP`) with `inst.mem_def.v != MEM_SSA_NONE`, `opc == OPT_INST_AGGREGATE`, `inst.place.proj_count > 0`, or `inst.orig_stmt.place.proj_count > 0` runs `alias_query_places(unsafe { view(*info) }, body, mut_view(*arena), view(inst.place), region_place, pt)` (falling back to `view(inst.orig_stmt.place)` if `inst.place.local.v == 0`), and `bce_term_clobbers_len_state` runs `alias_query_places` on `OPT_TERM_DROP` (`bb.term.drop_place`) and `OPT_TERM_CALL` (`bb.term.call_dest`) when `can_mutate_root` holds.
   - In `loops_region_clobbered_in_loop` (`compiler/opt/loops/mod.ax`), updated the `MIR_STMT_ASSIGN` branch (`is_mem_or_agg_write`) to run `alias_extract_region` + `alias_query_regions` whenever `dpl.proj_count > 0`, `(unsafe { (*inst).place.proj_count }) > 0`, `(unsafe { (*inst).mem_def.v }) != MEM_SSA_NONE`, `opc == OPT_INST_AGGREGATE`, `opc == OPT_INST_INSERT_FIELD`, `loops_local_has_indirect_mutation(body, info, wr_loc)`, or `wr_loc` matches `reg.base_local.v` / `reg.resolved_place.local.v`. Also included `opc == OPT_INST_AGGREGATE` in `lp_base_container_stable_in_loop` when checking whole-local overwrites of `base_loc`.
   - Extended `tests/run/opt_bce/opt_bce_oracle.py`, `tests/run/opt_bce/opt_bce_probe.ax.in`, and `tests/run/opt_bce/qa_round1_soundness_regressions.ax` with regression coverage for `OPT_INST_DISCRIMINANT` hoisting (Synthetic MIR Blob 6 `_13.._16` and frontend-lowered `pos_discriminant_view` -> `true`; `bug_discriminant_local_mut`, `bug_discriminant_mut_view`, and `bug_discriminant_zero_trip_raw` -> `false`) and whole-aggregate `MemoryDef` clobbers (`neg_agg_vec_clobber_via_alias` and `bug_bce_agg_vec` -> `vec_checks_eliminated == 0`; `bug_loops_agg_clobber` and `bug_loops_agg_clobber_raw` -> `loops_can_hoist_inst == false`).

STATUS: COMPLETE round=0
