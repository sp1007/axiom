# T064 Report: Optimizer Ladder 2 — Copy/Move Propagation, Inlining, and SROA/RVO/NRVO

## Summary

Implemented Task `T064` (`E15.3`, `SPEC-73` §§1, 2, 3, 4, 8, 9; `AXS-INL-001..026`, `AXS-INL-034`, `AXS-INL-035`) across `compiler/opt/sroa/mod.ax`, `compiler/opt/inline/mod.ax`, and `tests/opt2/*`:

1. **Ownership- and Capability-Aware Copy/Move Propagation, Deep `SROA`, and `RVO`/`NRVO` (`compiler/opt/sroa/mod.ax`)**:
   - Implemented `CopyMoveCandidate` (`COPY_PROP_VALUE`, `MOVE_PROP_COALESCE`, `COPY_MOVE_BLOCKED`) and `sroa_propagate_copies_and_moves`, enforcing type/representation equality, domination, capability/region preservation (`view<T>` / `mut_view<T>`), `AliasInfo` / `MemorySSA` intervening clobber rejection, single-consumption linear ownership coalescing, and `DropFlagId` retargeting (`AXS-INL-006..009`, `REQ-OPT-060..063`).
   - Implemented recursive `SroaLayoutTree` (`SroaCandidate`, `SroaLeafSlot`), eligibility & barrier classification (`SROA_BLOCK_ADDR_OBSERVABLE`, `SROA_BLOCK_ESCAPE_NON_LOCAL`, `SROA_BLOCK_DROP_GLUE_WHOLE`, `SROA_BLOCK_DYNAMIC_INDEX`, `SROA_BLOCK_UNION_REINTERPRET`, `SROA_BLOCK_VOLATILE_OR_ATOMIC`, `SROA_BLOCK_OPAQUE_WHOLE_USE`, `SROA_BLOCK_LEAF_CAP_EXCEEDED`), and `sroa_promote_aggregates` across structs, tuples, fixed-size arrays (`<= 16` constant-indexed elements), `Option<T>` / `Result<T, E>` (synthetic `_disc` + payload scalar locals), and non-escaping closure environment structs (`AXS-INL-010..014`, `REQ-OPT-064..066`, `REQ-OPT-075`, `REQ-OPT-083`).
   - Implemented `RvoNrvoCandidate` (`RVO_DIRECT_CONSTRUCT`, `NRVO_SINGLE_NAMED_LOCAL`, `NRVO_BLOCKED`) and `sroa_construct_rvo_nrvo`, rewriting eligible direct temporaries (`RVO`) and single-local return paths (`NRVO`) directly into caller-allocated `_0` while rejecting multiple-candidate paths, post-divergence clobbers, address/view escapes, and unwind-drop partial-init hazards (`AXS-INL-015..019`, `REQ-OPT-069..070`, `REQ-OPT-084..085`).
   - Added `PASS_COPY_MOVE_SROA = 13u16`, `sroa_contract()`, transactional `sroa_run_pass` / `sroa_run_pass_internal` with 4-verifier (`verify_mir`, `verify_mir_own`, `verify_mir_cap`, `verify_mir_drop_flags`) + `optir_verify_contract` rollback (`AXS-INL-034`), and deterministic `sroa_print` (`--emit=inline` SROA/RVO/NRVO section, `AXS-INL-035`).

2. **Semantic `CallGraph`, Tarjan `SCC` Summaries, 2-Stage Inliner, and Post-Inline `SROA` Cascade (`compiler/opt/inline/mod.ax`)**:
   - Implemented multi-kind `CallGraph` (`DISPATCH_DIRECT`, `DISPATCH_CLOSURE`, `DISPATCH_FN_PTR`, `DISPATCH_DYN_TRAIT`, `DISPATCH_FFI_EXTERN`, `DISPATCH_ASYNC_SPAWN`, `DISPATCH_GPU_LAUNCH`), deterministic Tarjan `SCC` decomposition (`CallGraphScc`), bottom-up reverse topological ordering, closed-world reachability (`REACH_ROOT`, `REACH_INTERNAL`, `REACH_DEAD_ELIMINATED`), and `address_taken_fn` tracking (`AXS-INL-002..005`, `REQ-OPT-057..059`, `REQ-OPT-086`).
   - Implemented compiler-derived `EffectSummary` (`Pure` vs `Result<T, E>` / `Option<T>` normal return vs `MayPanic`) and `FunctionEscapeSummary` fixed-point propagation (`AXS-INL-004`, `REQ-OPT-067..068`).
   - Implemented the two-stage inlining engine strictly separating Stage 1 (`InlineLegality`: `INLINE_LEGAL` vs `INLINE_ILLEGAL` with `InlineBlockReason`) from Stage 2 (`CostModel` / `InlineBudget` across `-O0`, `-O1`, `-O2`, `-O3`, `-Os`, `-Oz`, `@inline`, `@inline(always)`, `@inline(never)`, and `InlineHistoryChain` recursive `SCC` cycle bounding) (`AXS-INL-020..023`, `REQ-OPT-071..073`, `REQ-OPT-082`, `REQ-OPT-087`).
   - Implemented transactional callsite cloning (`inline_clone_callsite_in_mir`) with left-to-right once-only argument evaluation, local/drop-flag/basic-block remapping, return-block joining, unwind edge redirection, post-inlining `SROA` + `ConstFold` + `SimplifyCFG` + `DCE` cleanup cascade (`AXS-INL-024..026`, `REQ-OPT-074`), `PASS_INLINE = 14u16` (`inline_contract()`, `inline_run_pass`), and deterministic `callgraph_print` (`--emit=callgraph`) / `inline_print` (`--emit=inline`) formatters (`AXS-INL-035`, `REQ-OPT-081`).

3. **Differential & Live-Engine Oracle Tests (`tests/opt2/*`)**:
   - Added differential `.ax` tests (`copy_move_prop_and_sroa.ax`, `rvo_nrvo_and_drop_parity.ax`, `inline_scc_and_attributes.ax`) and the live engine probe + oracle (`opt2_sroa_inline_engine.test`, `opt2_sroa_inline_oracle.py`, `opt2_sroa_inline_probe.ax.in`) directly compiling and exercising `compiler/opt/sroa/mod.ax` and `compiler/opt/inline/mod.ax` with `axiomc2.exe`.

## Files changed

- compiler/opt/inline/mod.ax
- compiler/opt/sroa/mod.ax
- tests/opt2/copy_move_prop_and_sroa.ax
- tests/opt2/inline_scc_and_attributes.ax
- tests/opt2/opt2_sroa_inline_engine.test
- tests/opt2/opt2_sroa_inline_oracle.py
- tests/opt2/opt2_sroa_inline_probe.ax.in
- tests/opt2/rvo_nrvo_and_drop_parity.ax

## Verification

- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T064`: `0 REFUSED` (exit 0)
- `python build-snap-T064/tools/archcheck.py --root build-snap-T064`: `193 files scanned, 0 violations`
- `python build-snap-T064/tools/axtest.py --root build-snap-T064 --compiler build-snap-T064/build/axiomc2.exe -j 1 opt2`: `TOTAL 10 PASS 10 FAIL 0`
- `python build-snap-T064/tools/axtest.py --root build-snap-T064 --compiler build-snap-T064/build/axiomc2.exe -j 1 run/opt_escape run/opt_alias run/opt_passmgr run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax`: `PASS`

STATUS: COMPLETE round=0
