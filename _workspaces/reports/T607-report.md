STATUS: COMPLETE round=2

# T607 Report — E15.2 Escape Analysis (`NoEscape`/`ArgEscape`/`ReturnEscape`/`GlobalEscape`) & Stack/Register Allocation Promotion

## Summary

1. **Escape Lattice, Value-vs-Allocation Separation, Interprocedural SCC Summaries & 8-Step Storage Hierarchy (`compiler/opt/escape/mod.ax`, `SPEC-71 §§2.1-2.7`, `AXS-ESC-001..004`, `AXS-ESC-010`)**:
   - Implemented the 7-bit `EscapeSet` flags (`ESC_NONE`, `ESC_ARGUMENT`, `ESC_RETURN`, `ESC_HEAP`, `ESC_THREAD`, `ESC_EXTERNAL`, `ESC_UNKNOWN`), 4-tier `EscapeClass` lattice (`ESCAPE_NO_ESCAPE < ESCAPE_ARG_ESCAPE < ESCAPE_RETURN_ESCAPE < ESCAPE_GLOBAL_ESCAPE`), `escape_class_from_set`, `escape_class_join`, `escape_class_at_most`, and `escape_no_escape_certainty` (`REQ-OPT-042`).
   - Separated scalar value escape (`val_escape`) from referent/indirection allocation escape (`ind_escape`) in `LocalEscapeState` (`AESCAPE-26`), ensuring scalar loads (`*b` returning `i32`/`i64`) and pure null-comparison pointer casts (`p as usize != 0`) keep the backing allocation `NoEscape` (`CERTAINTY_PROVEN`).
   - Implemented `FunctionEscapeSummary`, `EscapeSummaryTable`, HIR/extern summary seeding (`escape_seed_hir_summaries`), and multi-body call-graph SCC fixed-point propagation (`escape_solve_call_graph_summaries`), solving mutually recursive SCCs from bottom (`NoEscape` / `ESC_ARGUMENT`) via monotone join while propagating `ESC_EXTERNAL`/`ESC_THREAD`/`ESC_HEAP`/`ESC_UNKNOWN` as well as interprocedural pointer address observability and identity comparison flags across call edges and resolving contextual `ret_aliases_params_mask` (`passthrough_view`) at callers (`REQ-OPT-043`, `REQ-OPT-045`, `REQ-OPT-357`).
   - Implemented all `AXS-ESC-004` escape and observability barriers: interior/caller-visible deref stores (`*(s.mv) = p`, `esc_find_pointee_owner_local`), dereferenced pointer/box indirection loads (`*outer_box`, `*_slot`), returned active borrows (`has_active_view_escape`), spawned tasks (`ESC_THREAD`), `extern` FFI calls (`ESC_EXTERNAL`), indirect/unresolved calls (`ESC_UNKNOWN`), non-null-check `PtrToInt` casts (`REASON_ADDR_OBSERVABLE`), pointer identity comparisons `p == q` (`REASON_IDENTITY_COMPARED`), loop-carried allocations crossing CFG backedges (`REASON_LOOP_CARRIED`), unbalanced frees (`REASON_UNBALANCED_FREE`), dynamic `heap_realloc` (`REASON_DYNAMIC_REALLOC`), `@at(...)` `DOMAIN_FIXED_MMIO`, `ZeroCopyPin` DMA pins, volatile/atomic/`zeroize`/`black_box` barriers, and `@repr(C)` layout discipline.
   - Implemented the mandatory 8-step `PhysicalStorage` decision hierarchy (`escape_select_storage`, `esc_assign_storage_decisions`) with per-site (`MAX_STACK_PROMOTE_BYTES = 4096`) and cumulative per-function (`MAX_FN_PROMOTED_STACK_BYTES = 16384`) stack budgets, disjoint `StorageLive`/`StorageDead` slot-reuse accounting (`DisjointSlotPair`, `esc_compute_disjoint_slot_pairs`), and 20 `PromotionReason` diagnostic codes (`REQ-OPT-044`, `REQ-OPT-046`).

2. **Concrete IR Allocation Promotions, `PassManager` Rollback & Deterministic Inspection (`compiler/opt/escape/mod.ax`, `SPEC-71 §§3-4`, `AXS-ESC-011..017`)**:
   - Implemented `Box<T>` and balanced `heap_alloc`+`heap_free` promotion (`escape_promote_mir`): `NoEscape` scalar/unborrowed payloads with CFG-postdominating balanced drops/frees and no whole-value `Box` transfers promote directly to SSA-eligible locals (`STORAGE_DECISION_SSA_REGISTER`, `box_sroa_promotions`), and `ArgumentEscape` / borrowed payloads promote to typed local stack slots with `Box` / pointer reconstruction and normal+unwind `MIR_TERM_DROP` / `MIR_STMT_DROP` redirection to drop the payload without calling `heap_free` (`REQ-OPT-335`, `REQ-OPT-346`).
   - Implemented `NoEscape` closure capture environment scalarization and direct-call devirtualization (`esc_try_promote_closure_site`), verifying capture storage-lifetime domination across all CFG paths between construction and call/field uses before forwarding `closure.field` capture reads and rewriting `closure(args...)` to direct `MIR_CONST_FN` calls (`REQ-OPT-336`).
   - Implemented bounded `[C]T` inline buffer promotion (`ALLOC_KIND_BOUNDED_BUF`, `STORAGE_DECISION_INLINE_BUFFER`, `inline_buffer_promotions`) with typed `*mut [C]T -> *mut u8` pointer casting and `heap_free` elision, plus `ReturnEscape` aggregate `NRVO` (`esc_try_promote_nrvo`, `STORAGE_DECISION_CALLER_RET_SLOT`, `nrvo_promotions`) (`REQ-OPT-345`, `AXS-ESC-013..014`).
   - Integrated `escape_contract` (`PASS_ESCAPE_PROMOTE`), `escape_run_pass_internal`, `escape_run_pass`, `escape_run_pipeline` (chaining `memopt_run_pass` for post-promotion store-to-load forwarding), `escape_optimize_mir_body` (strict `-O0` no-op, `PassManager` snapshot/rollback on postcondition or `verify_mir` failure, `PROP_NO_ESCAPE` `ProofProvenance`), and zero-string-literal deterministic `escape_print` / `escape_promote_print` (`AXS-ESC-016`, `AXS-ESC-017`).

3. **Differential & Direct Engine Verification Suite (`tests/run/opt_escape/`)**:
   - Added 4 self-contained differential fixtures (`box_closure_buffer_promotion.ax`, `escape_barriers_and_retention.ax`, `drop_order_and_scope_parity.ax`, `qa_round1_soundness_regressions.ax`) verifying `Box<T>`, capturing closures, bounded buffers, loop-local vs loop-carried allocations, `> 4096 B` oversized retention, pointer identity/address observability, FFI/indirect call barriers, reverse LIFO `Drop` order parity, and all 6 QA Round 0 soundness corner cases across `--interp`, `-O0`, `-O1`, and `-O2`.
   - Added `opt_escape_engine.test` (`opt_escape_oracle.py` + `opt_escape_probe.ax.in`) testing `compiler.opt.escape` directly across 27 MIR blobs (`0..26`) under `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each`.

## Requirement Coverage

| Requirement | Spec Anchor | Implementation & Verification |
| --- | --- | --- |
| `REQ-OPT-042` | `SPEC-71 §2.1-§2.2` (`AXS-ESC-001`, `AXS-ESC-002`) | 4-tier `EscapeClass` lattice (`NoEscape`, `ArgumentEscape`, `ReturnEscape`, `GlobalEscape`), 7-bit `EscapeSet`, and `AESCAPE-26` value-vs-allocation escape separation including dereferenced pointer/box indirection tracking (`compiler/opt/escape/mod.ax`, `opt_escape_probe.ax.in`, `qa_round1_soundness_regressions.ax`). |
| `REQ-OPT-043` | `SPEC-71 §2.3` (`AXS-ESC-003`) | Interprocedural `FunctionEscapeSummary` (`param_escapes`, `ret_aliases_params_mask`, `param_addr_observed_mask`, `param_identity_compared_mask`, `returns_fresh_alloc`, `captures_into_global`, `spawns_escape`, `calls_ffi`, `has_unknown_call`) and contextual caller instantiation (`compiler/opt/escape/mod.ax`, `opt_escape_probe.ax.in`, `qa_round1_soundness_regressions.ax`). |
| `REQ-OPT-044` | `SPEC-71 §2.6` (`AXS-ESC-010`) | Mandatory 8-step `PhysicalStorage` decision hierarchy (`STORAGE_DECISION_*`) with `4096 B` per-site and `16384 B` per-function stack promotion budgets (`compiler/opt/escape/mod.ax`, `escape_barriers_and_retention.ax`, `opt_escape_probe.ax.in`). |
| `REQ-OPT-045` | `SPEC-71 §2.3-§2.4` (`AXS-ESC-003`, `AXS-ESC-004`) | Borrowed `view<T>` / `mut_view<T>` `ArgumentEscape` stack eligibility when callee summaries do not retain/return/thread-escape the capability, versus `REASON_ACTIVE_VIEW_ESCAPE` heap retention when returned (`compiler/opt/escape/mod.ax`, `box_closure_buffer_promotion.ax`, `opt_escape_probe.ax.in`). |
| `REQ-OPT-046` | `SPEC-71 §2.4, §2.6` (`AXS-ESC-004`, `AXS-ESC-010`) | Observability, ABI, and hardware barriers (`PtrToInt`, `p == q`, `DOMAIN_FIXED_MMIO`, `ZeroCopyPin`, volatile/atomic/`zeroize`, `@repr(C)`, post-dominating balanced free, loop-carried backedge) with 20 `PromotionReason` codes (`compiler/opt/escape/mod.ax`, `escape_barriers_and_retention.ax`, `opt_escape_probe.ax.in`, `qa_round1_soundness_regressions.ax`). |
| `REQ-OPT-335` | `SPEC-71 §3.2` (`AXS-ESC-011`, `AXS-ESC-015`) | `Box<T>` and balanced `heap_alloc`+`heap_free` promotion to local stack or SSA locals with post-dominating drop/free checks, whole-value transfer guards, `Drop` redirection, and unwind/scope parity (`compiler/opt/escape/mod.ax`, `box_closure_buffer_promotion.ax`, `drop_order_and_scope_parity.ax`, `qa_round1_soundness_regressions.ax`, `opt_escape_probe.ax.in`). |
| `REQ-OPT-336` | `SPEC-71 §3.3` (`AXS-ESC-012`) | `NoEscape` closure capture environment scalarization, CFG capture-lifetime safety checks, capture field forwarding, and direct `MIR_CONST_FN` call devirtualization (`compiler/opt/escape/mod.ax`, `box_closure_buffer_promotion.ax`, `qa_round1_soundness_regressions.ax`, `opt_escape_probe.ax.in`). |
| `REQ-OPT-345` | `SPEC-71 §3.4-§3.5` (`AXS-ESC-013`, `AXS-ESC-014`) | Bounded `[C]T` inline stack buffer promotion (`ALLOC_KIND_BOUNDED_BUF`, `inline_buffer_promotions`) and `ReturnEscape` caller return-slot `NRVO` (`nrvo_promotions`) (`compiler/opt/escape/mod.ax`, `box_closure_buffer_promotion.ax`, `opt_escape_probe.ax.in`). |
| `REQ-OPT-346` | `SPEC-71 §2.7, §3.2` (`AXS-ESC-010`, `AXS-ESC-011`) | Stack-to-SSA scalar promotion (`STORAGE_DECISION_SSA_REGISTER`, `box_sroa_promotions`) and disjoint `StorageLive`/`StorageDead` stack-slot reuse (`DisjointSlotPair`, `reused_stack_bytes`) gated on non-observability and strict interval confinement (`compiler/opt/escape/mod.ax`, `drop_order_and_scope_parity.ax`, `qa_round1_soundness_regressions.ax`, `opt_escape_probe.ax.in`). |
| `REQ-OPT-357` | `SPEC-71 §2.3.3` (`AXS-ESC-003.3`) | Call-graph SCC fixed-point summary solver (`escape_solve_call_graph_summaries`) converging from `NoEscape` across direct and mutual recursion while failing closed on indirect/external callees (`compiler/opt/escape/mod.ax`, `opt_escape_probe.ax.in`). |

## Files changed

- compiler/opt/escape/mod.ax
- tests/run/opt_escape/box_closure_buffer_promotion.ax
- tests/run/opt_escape/drop_order_and_scope_parity.ax
- tests/run/opt_escape/escape_barriers_and_retention.ax
- tests/run/opt_escape/opt_escape_engine.test
- tests/run/opt_escape/opt_escape_oracle.py
- tests/run/opt_escape/opt_escape_probe.ax.in
- tests/run/opt_escape/qa_round1_soundness_regressions.ax

## Verification

- Stage-1, Stage-2 (`O1`), and Stage-3 (`O1`) self-host fixed-point build in `build-snap-T607` (Round 0):
  - `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == 3d2e5f3db21faa8f70435d646a79a1dd02415b37ee57c41acc733a949620acb6`

STATUS: COMPLETE round=0

## Round 1

### Root-Cause Fixes for QA Round 0 Soundness Findings (`compiler/opt/escape/mod.ax`)

1. **Finding 1 — Dereferenced pointer/box/view indirection escapes (`AESCAPE-26`, `AXS-ESC-002..004`)**:
   - Added `esc_place_projected_type` and `esc_place_projected_has_indirection`, and updated `esc_propagate_to_operand`, `esc_operand_param_mask`, `esc_find_borrow_base_local_depth`, and `esc_run_escape_dataflow` (`OPTIR_OP_USE`, `OPTIR_OP_REF`, `OPTIR_OP_CAST`, `OPTIR_OP_AGGREGATE`, `OPTIR_OP_BINARY_OP`) so any dereferenced place whose projected value type still carries indirection (`*outer_box`, `*_slot`, `*pp` where pointee is `Box<T>` / `*T` / `view<T>`) propagates full allocation escape bits, parameter alias masks, and pointer identity/address observability back to the underlying owner/pointee locals, while preserving `NoEscape` on pure scalar dereference loads (`*b -> i32`).

2. **Finding 2 — Post-dominating balanced free/drop & whole-value `Box` transfer gates (`AXS-ESC-010`, `AXS-ESC-011`, `AXS-ESC-015`)**:
   - Added CFG post-dominance verification (`esc_free_set_postdominates`) checking that every normal exit path from the allocation block passes through a matching `heap_free` (for `RAW_HEAP`/`BOUNDED_BUF`) or `drop` (for `BOX_NEW`/`VEC_WITH_CAP`), plus post-free/post-drop use checks (`esc_raw_alloc_post_free_and_alias_safe`, `esc_box_post_drop_safe`) and whole-value `Box` copy/move guards (`esc_opt_box_no_whole_value_transfer`, `esc_mir_box_no_whole_value_transfer`).
   - Updated `escape_select_storage` to enforce `!has_matching_free -> REASON_UNBALANCED_FREE / STORAGE_DECISION_HEAP` across `ALLOC_KIND_BOX_NEW`, `ALLOC_KIND_VEC_WITH_CAP`, `ALLOC_KIND_RAW_HEAP`, and `ALLOC_KIND_BOUNDED_BUF`, and gated `escape_promote_mir` on `has_matching_free && esc_mir_box_no_whole_value_transfer`.

3. **Finding 3 — Disjoint stack-slot reuse gates (`AXS-ESC-004.5`, `AXS-ESC-010`, `REQ-OPT-346`)**:
   - Hardened `esc_compute_disjoint_slot_pairs` with `esc_slot_candidate_eligible` and `esc_slot_strictly_confined_to_interval`, requiring `alloc_site_idx == ESC_NONE_IDX`, `!identity_compared`, `!address_observable`, `!has_active_view_escape`, `!crosses_loop_backedge`, `escape_class <= ESCAPE_ARG_ESCAPE`, reachable non-cleanup blocks, and zero statement/terminator uses of either local outside its `[StorageLive, StorageDead]` interval.

4. **Finding 4 — Interprocedural pointer address observability & identity comparison summaries (`AXS-ESC-003`, `AXS-ESC-004.5`, `REQ-OPT-043`, `REQ-OPT-046`)**:
   - Extended `FunctionEscapeSummary` with `param_addr_observed_mask: u32`, `param_identity_compared_mask: u32`, and `extra_param_obs_flags: *mut u8` (for `>= 32` parameters), monotone fixed-point join in `escape_summary_join` / `escape_solve_call_graph_summaries`, `box_into_raw` seeding in `escape_seed_hir_summaries`, summary extraction in `esc_run_escape_dataflow`, caller propagation to pointer/`Box`/`view` arguments, and conservative observability marking on un-summarized calls.

5. **Finding 5 — Closure capture `StorageDead` lifetime & whole-closure move alias (`AXS-ESC-002`, `AXS-ESC-012`, `REQ-OPT-336`)**:
   - Updated `esc_type_has_indirection` to classify `TY_CLOSURE` as carrying environment indirection so whole-closure copies/moves (`_alias = move _clos; spawn(move _alias)`) propagate `ESC_THREAD` / `ESC_GLOBAL_MASK` back to the closure site, paired with `esc_callee_env_has_indirection` so direct calls on scalar-only closures without a lifted summary remain `NoEscape`.
   - Added `esc_bb_range_has_storage_marker_for`, `esc_path_has_storage_marker_for`, and `esc_mir_capture_safe_to_forward` in `esc_try_promote_closure_site` to reject capture forwarding whenever `StorageDead(cap)` or `StorageLive(cap)` can execute on any CFG path between closure construction and any closure call or field read, or when `cap` is mutably borrowed or dropped.

6. **Finding 6 — Exhaustive `esc_local_is_only_null_checked` & `MIR_TERM_ASSERT` `tm.cond` fix (`AXS-ESC-004.5`, `REQ-OPT-046`)**:
   - Added `esc_place_uses_local` (checking `local` plus `MIR_PROJ_INDEX.index_local` and `MIR_PROJ_SUB_SLICE.from_local`/`to_local`), `esc_term_uses_local` (fixing `MIR_TERM_ASSERT` to inspect `tm.cond`), and `esc_place_only_derefs_ptr`, rewriting `esc_local_is_only_null_checked` to whitelist exclusively `PtrToInt` definitions and bare `EQ`/`NE` against literal `0` while rejecting array indexing (`arr[int_loc]`, `&arr[int_loc]`), `LEN`, `DISCRIMINANT`, `DROP`, and all terminators.

### Regression Tests Added

- **Direct MIR/API Probes (`tests/run/opt_escape/opt_escape_oracle.py`, `tests/run/opt_escape/opt_escape_probe.ax.in`)**:
  - Added MIR Blobs `14..26` and `verify_qa_round1_soundness_regressions` (exit codes `70..102`) directly exercising all 6 QA findings under `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each`.
- **Standalone Differential Run Fixture (`tests/run/opt_escape/qa_round1_soundness_regressions.ax`)**:
  - Added end-to-end differential fixture covering all 6 scenarios (`F1_DEREF_ESCAPE=70`, `F2_UNBALANCED_FREE=93`, `F3_SLOT_IDENTITY=81`, `F4_INTERPROC_OBS=83`, `F5_CLOSURE_SOUNDNESS=85`, `F6_PTR_INT_NON_NULL=80`, `QA_R1_TOTAL=492`) across `--interp`, `-O0`, `-O1`, and `-O2`.

### Files changed

- compiler/opt/escape/mod.ax
- tests/run/opt_escape/box_closure_buffer_promotion.ax
- tests/run/opt_escape/drop_order_and_scope_parity.ax
- tests/run/opt_escape/escape_barriers_and_retention.ax
- tests/run/opt_escape/opt_escape_engine.test
- tests/run/opt_escape/opt_escape_oracle.py
- tests/run/opt_escape/opt_escape_probe.ax.in
- tests/run/opt_escape/qa_round1_soundness_regressions.ax

### Verification (Round 1)

- Stage-1, Stage-2 (`O1`), and Stage-3 (`O1`) self-host fixed-point build in `build-snap-T607`:
  - `python build-snap-T607/tools/build_axiomc.py --root build-snap-T607 --out build-snap-T607/build --stage 3`:
    - `STAGE1 OK`: `20468736` bytes, `sha256=86e62ef046c02b7f`
    - `STAGE2 (O1) OK`: `6334464` bytes, `sha256=15086a66d9926d32`
    - `STAGE3 (O1) OK`: `6334464` bytes, `sha256=15086a66d9926d32`
    - `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == 15086a66d9926d321e4ff36edef002a33e91445f9bbf591b4ffd94ea1bdfabfb`
- Required regression suites (`-j 1`):
  - `python build-snap-T607/tools/axtest.py --root build-snap-T607 --compiler build-snap-T607/build/axiomc2.exe --build-dir build-snap-T607/build --exclude-requires axiom0-internal -j 1 run/opt_escape run/opt_alias run/opt_passmgr run/optir_ssa run/opt_scalar run/opt_effects selfhost/opt run/intrinsics/ ui/intrinsics/unknown_intrinsic.ax`: `WEAK-NATIVE 0`, `TOTAL 98 PASS 98 FAIL 0 SKIP 0 XFAIL 0`.
  - `python build-snap-T607/tools/axtest.py --root build-snap-T607 --compiler build-snap-T607/build/dir_stage3_O1/axiomc3.exe --build-dir build-snap-T607/build --exclude-requires axiom0-internal -j 1 run/opt_escape`: `WEAK-NATIVE 0`, `TOTAL 13 PASS 13 FAIL 0 SKIP 0 XFAIL 0`.
- Repository gates:
  - `python tools/archcheck.py`: `0 violations`.
  - `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `COVERAGE OK` (`gaps: 0`).
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T607`: exit `0` (`0 REFUSED`).

STATUS: COMPLETE round=1

## Round 2

### Root-Cause Fixes for QA Round 1 Soundness & Integration Findings (`compiler/opt/escape/mod.ax`)

1. **Finding 1 — `verify_mir` & `passmgr` uninitialized-parameter rollback on every parameterized function (`arg_count >= 1`, `AXS-ESC-016`, `REQ-OPT-335`, `REQ-OPT-336`, `REQ-OPT-345`, `REQ-OPT-346`)**:
   - Added `esc_mir_effective_arg_count`, `esc_opt_body_has_args`, and `esc_ensure_fn_item_for_mir` (synthesizing an arena-allocated `HirItem` `HIR_ITEM_FN` with `argc` linked `HirParam`s whenever `fn_item == 0` and `argc > 0`) so `verify_mir(mir, eff_fn, ...)` never calls `verify_mir` with `fn_item == 0` on parameterized functions.
   - Because `verify_mir` skips its built-in `AX_VERIFY_UNINIT_USE` check whenever `fn_item != 0`, added `esc_verify_mir_definite_init` — an exact forward-intersection definite-initialization pass over `MirBody` that seeds `bb_in[0]` with `1..=argc`, `MIR_LOCAL_ARG`/`MIR_LOCAL_CONST`, and unit/error `_0`, and verifies all read places, projection index/subslice locals, rvalue operands, `MIR_STMT_DROP`, and terminator operands (`SWITCH_INT`, `CALL`, `DROP`, `ASSERT`, `RETURN`).
   - Added `esc_verify_mir_body_complete`, `esc_verify_body_capabilities`, and `esc_verify_postconditions_arg_aware`, and wired them into `escape_run_pass_internal` (both post-rewrite MIR verification and `verify_each` postcondition checks), `escape_run_pipeline` (`PASS_LOWER_MIR` check and arg-aware postcondition wrapper around `memopt_run_pass` when `pm.verify_each && esc_opt_body_has_args`), and `escape_optimize_mir_body` (entry and exit `eff_fn` + `esc_verify_mir_definite_init` verification with full rollback on failure).

2. **Finding 2 — Out-of-bounds `Arena` memory corruption in `FunctionEscapeSummary` for `>= 32` / `>= 64` parameters (`AXS-ESC-003`, `REQ-OPT-043`, `REQ-OPT-357`)**:
   - Extended `FunctionEscapeSummary` with `pub extra_escapes_cap: u32` and `pub extra_obs_cap: u32` (initialized in `escape_summary_zero` and new `pub fn escape_summary_init`).
   - Bounds-checked `escape_summary_param_escape` (returning `ESC_NONE` when `param_idx < sum.param_count` and unallocated/unset, and `ESC_UNKNOWN` when `param_idx >= sum.param_count`), `escape_summary_param_addr_observed`, and `escape_summary_param_identity_compared` against `extra_escapes_cap` / `extra_obs_cap`.
   - Added geometric Arena reallocation helpers `esc_ensure_extra_escapes_cap` and `esc_ensure_extra_obs_cap` that copy existing entries and zero-fill newly grown slots whenever `param_idx - 32` exceeds current capacity.
   - Fixed `escape_summary_join` to capture `prev_dst_cnt = dst.param_count` prior to updating `dst.param_count`, preventing OOB reads on `dst` and safely growing `dst` across arbitrary arities (`32`, `64`, `130+`).

3. **Finding 3 — `esc_try_promote_nrvo` ignoring terminator operand reads & leaving uninitialized `cand` reads (`AXS-ESC-014`, `REQ-OPT-345`)**:
   - Updated `esc_rvalue_uses_local` to inspect `MIR_RVALUE_REPEAT` `repeat_count_op` as well as all other rvalue forms.
   - Added `esc_rvalue_proj_or_dropflag_uses_local` and refactored `esc_try_promote_nrvo` into candidate-iterating `esc_try_promote_nrvo_for_local` (skipping `MIR_LOCAL_ARG` candidates and advancing to other eligible candidates on rejection).
   - Enforced exhaustive pre-checks across all statements and terminators: `ret_defs == 1`, `return_term_count == 1`, `cand_defs >= 1`, `!esc_term_uses_local(tm, 0u32)`, zero uses of `_0` or `cand` inside `MIR_PROJ_INDEX` / `MIR_PROJ_SUB_SLICE` projections or `drop_flag`, and zero `MIR_STMT_DROP` / `MIR_STMT_STORAGE_LIVE` / `MIR_STMT_STORAGE_DEAD` on `_0`.
   - Extended the NRVO `cand -> 0u32` rewrite across all terminators: `MIR_TERM_SWITCH_INT.discr`, `MIR_TERM_ASSERT.cond`, `MIR_TERM_CALL.func`, and `MIR_TERM_CALL.destination`.

### Regression Tests Added

- **Direct MIR/API Probes (`tests/run/opt_escape/opt_escape_oracle.py`, `tests/run/opt_escape/opt_escape_probe.ax.in`)**:
  - Added `type#52 = FlagPair`, MIR Blobs `27..32`, `probe_make_fn_2arg`, and `verify_qa_round2_regressions` (`PROBE_QA_ROUND2_REGRESSIONS=OK`, exit codes `110..134`) directly verifying under `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each`:
    - Parameterized 2-arg all-4-promotions (`box_sroa_promotions`, `closure_env_promotions`, `inline_buffer_promotions`, `nrvo_promotions`) across `escape_optimize_mir_body` (`fn_item == 0` and `fn_item == fn_2arg`, `verify_each = false` and `true`) with `pass_rollbacks == 0`.
    - Parameterized 1-arg `escape_run_pipeline` (`verify_each = true`) stack `Box` promotion + `memopt` store-to-load forwarding with `pass_rollbacks == 0`.
    - Negative parameterized definite-init enforcement (`esc_verify_mir_definite_init` rejecting uninitialized local read while `eff_fn != 0`, and `escape_run_pass_internal` rolling back an injected uninitialized-read corruption with `pass_rollbacks == 1`).
    - `FunctionEscapeSummary` dynamic capacity growth up to `arity = 130` (`escape_summary_set_param_escape` at `17, 36, 99, 129`, observability setters at `33, 68, 105, 129`, and `escape_summary_join` from a 12-arg summary into a 130-arg summary and vice versa) surrounded by `0x1234u16` / `0x55u8` / `0x7777u16` Arena canaries verified intact.
    - QA's exact `NRVO` + `switchInt(copy _4.0)` + `box_new<i32>` reproducer (`nrvo_promotions == 1`, `box_sroa_promotions == 1`, `pass_rollbacks == 0`), parameterized `NRVO` + `MIR_TERM_ASSERT(copy _5.0)` rewrite (`nrvo_promotions == 1`, `pass_rollbacks == 0`), and multi-`MIR_TERM_RETURN` `NRVO` rejection (`nrvo_promotions == 0`).
- **Standalone Differential Run Fixture (`tests/run/opt_escape/qa_round1_soundness_regressions.ax`)**:
  - Extended with `test_f7_param_promotions_and_verify` (`F7_PARAM_PROMOTIONS=100`) and `test_f8_nrvo_branch_switch_and_assert` (`F8_NRVO_TERMINATOR_READS=148`, `QA_R1_TOTAL=740`) verified identically across `--interp`, `-O0`, `-O1`, and `-O2`.

### Files changed

- compiler/opt/escape/mod.ax
- tests/run/opt_escape/box_closure_buffer_promotion.ax
- tests/run/opt_escape/drop_order_and_scope_parity.ax
- tests/run/opt_escape/escape_barriers_and_retention.ax
- tests/run/opt_escape/opt_escape_engine.test
- tests/run/opt_escape/opt_escape_oracle.py
- tests/run/opt_escape/opt_escape_probe.ax.in
- tests/run/opt_escape/qa_round1_soundness_regressions.ax

### Verification (Round 2)

- Stage-1, Stage-2 (`O1`), and Stage-3 (`O1`) self-host fixed-point build in `build-snap-T607`:
  - `python build-snap-T607/tools/build_axiomc.py --root build-snap-T607 --out build-snap-T607/build --stage 3`:
    - `STAGE1 OK`: `20468736` bytes, `sha256=86e62ef046c02b7f`
    - `STAGE2 (O1) OK`: `6334464` bytes, `sha256=15086a66d9926d32`
    - `STAGE3 (O1) OK`: `6334464` bytes, `sha256=15086a66d9926d32`
    - `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == 15086a66d9926d321e4ff36edef002a33e91445f9bbf591b4ffd94ea1bdfabfb`
- Required regression suites (`-j 1`):
  - `python build-snap-T607/tools/axtest.py --root build-snap-T607 --compiler build-snap-T607/build/axiomc2.exe --build-dir build-snap-T607/build --exclude-requires axiom0-internal -j 1 run/opt_escape run/opt_alias run/opt_passmgr run/optir_ssa run/opt_scalar run/opt_effects selfhost/opt run/intrinsics/ ui/intrinsics/unknown_intrinsic.ax`: `WEAK-NATIVE 0`, `TOTAL 98 PASS 98 FAIL 0 SKIP 0 XFAIL 0`.
  - `python build-snap-T607/tools/axtest.py --root build-snap-T607 --compiler build-snap-T607/build/dir_stage3_O1/axiomc3.exe --build-dir build-snap-T607/build --exclude-requires axiom0-internal -j 1 run/opt_escape`: `WEAK-NATIVE 0`, `TOTAL 13 PASS 13 FAIL 0 SKIP 0 XFAIL 0`.
- Repository gates:
  - `python tools/archcheck.py`: `0 violations`.
  - `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `COVERAGE OK` (`gaps: 0`).
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T607`: exit `0` (`0 REFUSED`).

STATUS: COMPLETE round=2
