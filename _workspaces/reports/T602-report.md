# T602 Report — E15.1 Optimization Pass Manager, Effect/Proof Summaries & Transformation Contract Verifier

## Summary of Changes

1. **`EffectInfo` Summary, Call-Graph Propagation & Domain Verifier (`compiler/opt/effects/mod.ax`)**:
   - Implemented canonical, deterministic, conservative `EffectSummary` (`EFFECT_PURE`, `EFFECT_READS_MEM`, `EFFECT_WRITES_MEM`, `EFFECT_MAY_PANIC`, `EFFECT_ALLOCATES`, `EFFECT_IO`, `EFFECT_ATOMIC`, `EFFECT_VOLATILE`, `EFFECT_FFI`, `EFFECT_NONTERM`, `EFFECT_UNKNOWN`) and instruction/terminator/block/body inference over `OptBody` (`effect_infer_inst`, `effect_infer_term_with_table`, `effect_infer_block_with_table`, `effect_infer_body_with_table`, `effect_infer_body`) per `SPEC-70` (`AXS-OPT-023`, `AXS-OPT-024`, `AXS-OPT-044`, `REQ-OPT-348`, `REQ-OPT-349`, `REQ-OPT-393`, `REQ-OPT-395`).
   - Enforced fail-closed `EFFECT_UNKNOWN != EFFECT_PURE` purity predicates (`effect_is_pure`, `effect_pure_certainty`) and verified-annotation resolution (`effect_annotation_matches_inferred`, `effect_resolve_declared_flags`) so unverified annotations never weaken inferred effects or turn `EFFECT_UNKNOWN` into `EFFECT_PURE` (`REQ-OPT-348`, `REQ-OPT-396`).
   - Implemented `EffectCallTable` and bottom-up SCC-safe call-graph fixed-point propagation (`EffectCallGraph`, `effect_call_graph_propagate`) with arena-allocated arbitrary-size node scratch arrays (`node_cap`, supporting `> 64` nodes) plus incremental reverse-edge summary invalidation (`effect_call_graph_update_node_local`) so body-local edits that preserve a function's or SCC's summary return `0` without caller reanalysis and summary-changing edits re-evaluate only reverse-reachable callers (`REQ-OPT-394`).
   - Implemented legality query helpers (`effect_can_dce`, `effect_can_dce_inst`, `effect_can_reorder`, `effect_call_clobbers_region`, and `EFFECT_MASK_NON_STORE_OBSERVABLE`) preserving I/O, OS, volatile, atomic, allocation, drop, and panic ordering (`REQ-OPT-061`, `REQ-OPT-062`, `REQ-OPT-063`) and execution-domain boundary verification (`effect_verify_execution_domain`) for `EXEC_DOMAIN_HOST`, `EXEC_DOMAIN_COMPTIME`, and `EXEC_DOMAIN_KERNEL` (`REQ-VER-027`, `REQ-OPT-349`).

2. **Optimization Pass Manager, Fact-Driven Scheduler & Transformation Contract Verifier (`compiler/opt/passmgr/mod.ax`, `compiler/opt/optir/mod.ax`)**:
   - Implemented `PassManager`, `TransformationContract`, `OptBudget`, `BodyFacts`, `CandidateRewrite`, and `OptBodySnapshot` per `SPEC-70 §8` (`AXS-OPT-030..034`, `REQ-OPT-355`, `REQ-OPT-356`).
   - Implemented explicit analysis dependency and invalidation DAG closures (`analysis_expand_required`, `analysis_expand_invalidated`, `passmgr_invalidate_analyses`, `passmgr_ensure_analyses`) over `CFG`, `Dominators`, `SSA`, `MemorySSA`, `EffectInfo`, `AliasInfo`, `EscapeInfo`, `RangeInfo`, and `LoopInfo`, invalidating both `invalidated_analyses` and all non-preserved analyses on IR mutation (`REQ-CORE-447`, `REQ-OPT-350`) and guarding `RangeInfo` consumers (`pm_value_is_const_int`, `pm_value_has_fp_hazard`) against stale `body.ranges` reads (`AXS-OPT-030`).
   - Implemented `OptProfile` (`-O0`, `-O1`, `-O2`, `-Os`) and `OptBudget` fact-driven pass scheduling (`opt_budget_for_profile`, `passmgr_collect_body_facts`, `passmgr_should_schedule_pass`) and bounded fixed-point pipeline execution with early termination on convergence (`passmgr_run_pass`, `passmgr_run_pipeline`, `REQ-OPT-065`, `REQ-OPT-373`, `REQ-OPT-374`).
   - Implemented trap-free integer/boolean constant folding in `pm_exec_sccp` (supporting checked arithmetic, `OPT_INST_WRAPPING_BINOP`, bitwise ops, and comparisons with `MIR_CONST_BOOL` emission for `TY_BOOL` and operand clearing on folded `OPT_INST_CONST`), algebraic identity folding in `pm_exec_inst_combine`, clobber-safe `EffectInfo`-gated CSE in `pm_exec_gvn_cse`, `MemorySSA` `Proven DeadStore` and dead value instruction elimination in `pm_exec_dce`, and constant branch simplification in `pm_exec_cfg_simplify`.
   - Implemented the two-stage candidate rewrite protocol (`passmgr_verify_candidate_legality`, `passmgr_evaluate_candidate`) enforcing `CERTAINTY_PROVEN` proof records (`CERTAINTY_POSSIBLE` and `CERTAINTY_UNKNOWN` fail closed even when cost is profitable), current IR revision matching, capability preservation (`view<T>` is never promoted to `mut_view<T>`, `REQ-OPT-064`), observable effect preservation (`REQ-OPT-060..063`), and cost-model profitability (`REQ-OPT-405`, `REQ-OPT-406`).
   - Implemented pre-pass `OptBody` snapshotting (`passmgr_snapshot_body`), automatic rollback on postcondition failure (`passmgr_rollback_body`), post-pass contract verification (`passmgr_verify_postconditions`), and fault-injection contract verification (`passmgr_inject_fault_and_verify` for `FAULT_CORRUPT_IDOM`, `FAULT_DROP_VOLATILE_INST`, `FAULT_DROP_ATOMIC_INST`, and `FAULT_PROMOTE_VIEW_TO_MUT`) including clean `OPT_INST_NOP` omission in `optir_reconstruct_mir` and `verify_mir` validation under `--verify-each` (`REQ-OPT-404`).

3. **Round 1 QA Fixes (`_workspaces/reports/T602-qa.md` Findings #1–#4)**:
   - **Finding #1 (`tests/run/opt_passmgr` live execution, atomic effects, and `mir_body` negative gate)**:
     - Added `tests/run/opt_passmgr/passmgr_contract_probe.ax.in` and updated `tests/run/opt_passmgr/passmgr_verify_each_oracle.py` to assemble `CORE_MODULES` (`compiler/opt/optir/mod.ax`, `compiler/opt/effects/mod.ax`, `compiler/opt/passmgr/mod.ax`, etc.) with `passmgr_contract_probe.ax.in`, compile the bundle via `axiomc build --stack-reserve=67108864 -O0/-O1/-O2 --verify-each`, and execute all three compiled binaries (`-O0`, `-O1`, `-O2`).
     - Directly exercised and verified `PassManager` caching/transitive invalidation, `EffectInfo` local and 80-node call-graph propagation preserving I/O, **atomic** (`OPT_INST_ATOMIC`, `CALL_KIND_ATOMIC_INTRINSIC`, `FAULT_DROP_ATOMIC_INST`), `volatile`, and `MayPanic` effects, incremental `effect_call_graph_update_node_local`, candidate legality/profitability checks, capability-promotion rejection, postcondition checking, and snapshot rollback across `-O0`, `-O1`, and `-O2`.
     - Replaced the malformed MIR snippet in `passmgr_verify_each_oracle.py` with valid `mir_body { ... }` fixtures (`verified_ok.mir` positive gate; `unverified_uninit.mir` reading uninitialized `_1` and `unverified_ill_typed.mir` copying `type#4` to `type#8` as `verify_mir` entry-gate failures).
   - **Finding #2 (`pm_exec_gvn_cse` clobbered-local miscompilation fix)**:
     - Added `pm_mir_local_clobbered_between` and place/move/drop/storage-liveness guards in `pm_exec_gvn_cse` (`compiler/opt/passmgr/mod.ax`) so `inst_i` is rewritten to `MIR_OP_COPY` of `(*inst_j).place` only when `(*inst_j).place.local.v != 0`, `proj_count == 0`, `view_kind == 0`, `drop_flag == MIR_DROP_FLAG_NONE`, neither `inst_j` nor `inst_i` has move/barrier semantics, and no instruction in `j + 1 .. i - 1` writes to, moves from, drops, or changes storage liveness of `(*inst_j).place.local`. Added regression tests in `harness_opt_unit.ax.in` (`5.1`, snippet `19`) and `passmgr_contract_probe.ax.in`.
   - **Finding #3 (`EffectInfo` non-`GOTO` loop backedges, `> 64`-node call graphs, and incremental SCC updates)**:
     - Updated `effect_infer_body_with_table` (`compiler/opt/effects/mod.ax`) to conservatively join `EFFECT_NONTERM` on **every** reachable CFG backedge (`v_rpo <= u_rpo`) across all terminator kinds (`OPT_TERM_GOTO`, `OPT_TERM_BRANCH`, `OPT_TERM_SWITCH_INT`), and included `OPT_INST_BINOP` / `OPT_INST_CHECKED_BINOP` in `effect_infer_inst`'s scalar opcode classification after trap/overflow checks.
     - Replaced `eff_cg_can_reach`'s 64-node `u64` bitmask with arena-allocated scratch arrays (`scratch_visited`, `scratch_queue`, `scratch_affected`, `scratch_saved_prop`) sized to `cg.node_cap` on `EffectCallGraph`, supporting arbitrary `node_count` (`> 64`).
     - Updated `effect_call_graph_update_node_local` (`REQ-OPT-394`) to short-circuit with `0u32` when `(new_local_effects, unresolved_call)` is unchanged, isolate `node_idx`'s SCC first, and return `0u32` without touching callers whenever no node's `prop_flags` changed. Added 80-node mutual/self-recursion and `BRANCH`/`SWITCH_INT` backedge regression tests.
   - **Finding #4 (Stale `RangeInfo` guard, `SPEC-70` contract masks, `pm_exec_sccp`, and `pm_exec_dce`)**:
     - Guarded `pm_value_is_const_int` and `pm_value_has_fp_hazard` with `passmgr_is_analysis_valid(view(*pm), ANALYSIS_RANGE_INFO)` (`SPEC-70 AXS-OPT-030`), snapshotted `ranges_ptr` in `OptBodySnapshot`, and cleared `body.ranges` on invalidation in `passmgr_run_pass`.
     - Updated `passmgr_contract_for_pass` (`SPEC-70 AXS-OPT-031`) to include `ANALYSIS_MASK_EFFECT_INFO` on `PASS_SCCP`, `ANALYSIS_MASK_CFG` on `PASS_INST_COMBINE`, `ANALYSIS_MASK_ESCAPE_INFO` on `PASS_DCE`, `ANALYSIS_MASK_SSA` on `PASS_CFG_SIMPLIFY`, and `ANALYSIS_MASK_ALIAS_INFO` in `PASS_SROA`'s `invalidated_analyses`.
     - Updated `pm_exec_sccp` to clear `(*inst).lhs` and `(*inst).rhs` to `OPT_VALUE_NONE` on folded `OPT_INST_CONST`, emit `MIR_CONST_BOOL` when folding `TY_BOOL` (`type#4`) expressions, and fold pure bitwise/comparison ops (`optir_query_no_overflow_certainty` returning `CERTAINTY_PROVEN` for non-trapping bitwise/comparison ops; `optir_print` printing `(*inst).result` when `OPT_INST_CONST` has `lhs == OPT_VALUE_NONE`).
     - Updated `pm_exec_dce` and `optir_reconstruct_mir` to replace magic `1020u16` with `EFFECT_MASK_NON_STORE_OBSERVABLE`, wire `passmgr_can_dce_value_inst` in a fixed-point loop gated by `passmgr_evaluate_candidate`, match `PROP_DEAD_STORE` provenance by `(OptBbId, OptInstId)` with wildcard `subject_val = OPT_VALUE_NONE`, and turn eliminated instructions into clean `OPT_INST_NOP` (`flags = 0u16`) omitted during `MirBody` reconstruction instead of emitting `MIR_STMT_STORAGE_LIVE`.

## Files changed

- `compiler/opt/effects/mod.ax`
- `compiler/opt/optir/mod.ax`
- `compiler/opt/passmgr/mod.ax`
- `tests/run/opt_passmgr/drop_raw_ptr_io_order.ax`
- `tests/run/opt_passmgr/effect_preserve_io_volatile_panic.ax`
- `tests/run/opt_passmgr/passmgr_contract_probe.ax.in`
- `tests/run/opt_passmgr/passmgr_verify_each.test`
- `tests/run/opt_passmgr/passmgr_verify_each_oracle.py`
- `tests/selfhost/opt/gen_opt_tests.py`
- `tests/selfhost/opt/harness_opt_pipeline.ax.in`
- `tests/selfhost/opt/harness_opt_unit.ax.in`
- `tests/selfhost/opt/qa_opt_pipeline.ax`
- `tests/selfhost/opt/qa_opt_unit.ax`

## Verification (Round 1)

- Stage-1 & Stage-2 self-host compiler build inside `build-snap-T602`:
  - `python build-snap-T602/tools/build_axiomc.py --root build-snap-T602 --out build-snap-T602/build`: `STAGE1 OK` (`17303552` bytes, `sha256=3a0011394e04002f`), `STAGE2 (O1) OK` (`10572800` bytes, `sha256=d4fd9b56148d874460905cfe94be7550d11802be676fea9b9605cbf8045af419`), `BUILD-AXIOMC OK`.
- Targeted `T602`, `OptIR`, and selfhost bundle test suites inside `build-snap-T602` (`-j 1`):
  - `python tools/axtest.py --compiler build/axiomc2.exe --exclude-requires axiom0-internal -j 1 run/opt_passmgr run/optir_ssa selfhost/opt selfhost/bundles_current.test`: `WEAK-NATIVE 0`, `TOTAL 21 PASS 21 FAIL 0 SKIP 0 XFAIL 0`.
  - `python tools/axtest.py --compiler build/axiomc2.exe --exclude-requires axiom0-internal -j 1 opt/const_fold_run.ax opt/qa_dce_run.ax opt/qa_edge_cases_run.ax`: `PASS 6/6, FAIL 0`.
- Empirical Revert-Sensitivity & Live Mutation Verification on `tests/run/opt_passmgr` inside `build-snap-T602`:
  - Temporarily renaming `build-snap-T602/compiler/opt/passmgr/mod.ax` or `build-snap-T602/compiler/opt/effects/mod.ax` causes `run/opt_passmgr/passmgr_verify_each.test` to **FAIL** (`rc_passmgr=1`, `rc_effects=1`); restored immediately.
  - Temporarily mutating `effect_is_pure` (`flags == EFFECT_PURE` -> `flags == EFFECT_PURE || flags == EFFECT_UNKNOWN`) inside `build-snap-T602/compiler/opt/effects/mod.ax` causes `run/opt_passmgr/passmgr_verify_each.test` to compile the mutated module and **FAIL** at runtime (`passmgr_contract_probe -O0 failed with exit code 11`, `MUT_RC=1`); restored via `taskctl.py snapshot T602` and re-verified `TOTAL 21 PASS 21 FAIL 0`.
- Repository gates:
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T602`: exit `0` (`15` staged files, `0 REFUSED`).
  - `python build-snap-T602/tools/archcheck.py`: `archcheck: 193 files scanned, 0 violations`.
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
  - `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `requirements: 32308`, `gaps: 0`, `COVERAGE OK`.
  - `python build-snap-T602/tests/selfhost/opt/gen_opt_tests.py --check`: `tests/selfhost/opt/qa_opt_unit.ax up to date`, `tests/selfhost/opt/qa_opt_pipeline.ax up to date`.

STATUS: COMPLETE round=1
