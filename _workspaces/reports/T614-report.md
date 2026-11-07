# T614 Report: E15.4 — Interprocedural Call-Site/Constant/Closure Specialization, Devirtualization & Tail-Call Optimization

## Summary

Implemented Task `T614` (`E15.4`, `SPEC-73` §§5, 6, 7, 8, 9; `AXS-INL-027..035`, `REQ-OPT-002..003`, `REQ-OPT-087..107`, `REQ-OPT-112..113`, `REQ-OPT-315`) across `compiler/opt/ipa/mod.ax`, `compiler/opt/devirt/mod.ax`, and `tests/run/opt_ipa_devirt/*`:

1. **Interprocedural Call-Site Constant & Closure Specialization (`compiler/opt/ipa/mod.ax`, `module compiler.opt.ipa`)**:
   - Implemented canonical `SpecializationKey` (`SpecArgBinding`: `SPEC_ARG_CONST_INT`, `SPEC_ARG_CONST_BOOL`, `SPEC_ARG_ENUM_TAG`, `SPEC_ARG_CLOSURE_SYM`, `SPEC_ARG_FN_PTR_SYM`), 64-bit FNV-1a fingerprinting (`ipa_spec_key_fingerprint`), equality (`ipa_spec_key_equals`), and deterministic clone symbol mangling (`ipa_spec_clone_sym`, `AXS-INL-028`, `AXS-INL-030`, `REQ-OPT-087..092`).
   - Implemented representation-equivalent code sharing (`RepEquivDesc`, `ipa_can_share_representation`) with strict function-pointer identity preservation (`address_taken_fn == true` never merges distinct functions, `AXS-INL-029`, `REQ-OPT-098..099`).
   - Implemented `SpecializationBudget` (`max_clones_per_fn`: `0` at `-O0`/`-Os`/`-Oz`, `2` at `-O1`, `8` at `-O2`, `16` at `-O3`; `max_module_growth_pct`: `25%` at `-O2`; `min_benefit_score`) and specialization benefit scoring across constant branch folding, arithmetic constant folding, and indirect closure/fn-ptr call devirtualization (`AXS-INL-030..031`, `REQ-OPT-093..097`).
   - Implemented transactional call-site specialization (`ipa_specialize_callsite`, `ipa_specialize_callgraph`), post-specialization cleanup (`ConstFold` + `SROA` + `SimplifyCFG` + `DCE`), `EffectSummary` / `EscapeSummary` tightening (`REQ-OPT-100..102`), `PASS_IPA_SPECIALIZE = 15u16` (`ipa_specialize_contract()`, `ipa_run_specialize_pass`), and deterministic `--emit=specialize` formatting (`ipa_specialize_print`, `AXS-INL-034..035`).

2. **Three-Tier Concrete-Receiver Devirtualization (`compiler/opt/devirt/mod.ax`, `module compiler.opt.devirt`)**:
   - Implemented provenance analysis (`devirt_collect_local_provenance_targets`, `devirt_classify_callsite`) across local SSA/constructor provenance, specialized parameter provenance, and closed-world target sets (`AXS-INL-032.1`, `REQ-OPT-103..107`, `REQ-OPT-112..113`, `REQ-OPT-315`).
   - Implemented Tier 1 (`DEVIRT_TIER_EXACT`: single proven concrete target -> rewrites indirect call in `MirBody` to direct `MIR_CONST_FN` call and cascades into `compiler.opt.inline` + `compiler.opt.sroa`), Tier 2 (`DEVIRT_TIER_GUARDED`: finite target set $2 \le m \le 4$ -> rewrites callsite into `MIR_TERM_SWITCH_INT` guarded direct calls with closed-world/open-world fallback), and Tier 3 (`DEVIRT_TIER_RETAINED_DYNAMIC`: fail-closed dynamic dispatch retention under `-O0`, open-world, `@export` boundaries, or `dynamic_loading_active`) (`AXS-INL-032.1..3`).
   - Implemented `PASS_DEVIRT = 16u16` (`devirt_contract()`, `devirt_run_pass`, `devirt_run_pass_internal`) with transactional 4-verifier (`verify_mir`, `verify_mir_own`, `verify_mir_cap`, `verify_mir_drop_flags`) rollback and deterministic `--emit=devirt` formatting (`devirt_print`, `AXS-INL-034..035`).

3. **Tail-Recursion Loop Lowering & Sibling Tail-Call Optimization (`compiler/opt/ipa/mod.ax`)**:
   - Implemented `ipa_check_tco_legality` (`TCO_LEGAL` vs `TCO_ILLEGAL` with `TCO_REASON_NOT_TAIL_POS`, `TCO_REASON_LIVE_DROP_AFTER_CALL`, `TCO_REASON_STACK_VIEW_ESCAPE`, `TCO_REASON_VOLATILE_OR_ATOMIC_AFTER`, `TCO_REASON_ABI_MISMATCH`, `TCO_REASON_INDIRECT_UNRESOLVED`, `TCO_REASON_PROFILE_O0`), strictly rejecting tail-call optimization when caller locals require post-call `Drop` cleanup or when stack-borrowed `view<T>` / `mut_view<T>` / raw pointers to caller stack slots escape to the callee (`AXS-INL-033`, `REQ-OPT-002..003`).
   - Implemented `O(1)` stack self-tail-recursion loop lowering (`ipa_lower_self_tail_recursion_in_mir`) with simultaneous parallel parameter staging (`_tco_arg_1..k`) before jumping back to loop header `bb0`, sibling tail-call qualification, explicit `@tailcall` legality verification (`ipa_verify_tailcall_attr` -> `TCO_DECISION_REJECTED_DIAG`), `PASS_TAILCALL = 17u16` (`tailcall_contract()`, `ipa_run_tailcall_pass`), and deterministic `--emit=inline` TCO reporting (`ipa_tailcall_print`, `AXS-INL-033..035`).

4. **Differential & Live-Engine Oracle Tests (`tests/run/opt_ipa_devirt/*`)**:
   - Added differential `.ax` tests (`callsite_const_closure_spec.ax`, `dyn_trait_and_fnptr_devirt.ax`, `tailcall_loop_lowering_and_drop_guards.ax`) and the live engine probe + oracle (`opt_ipa_devirt_engine.test`, `opt_ipa_devirt_oracle.py`, `opt_ipa_devirt_probe.ax.in`) exercising `compiler.opt.ipa` and `compiler.opt.devirt` end-to-end across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`.

## Files changed

- compiler/opt/devirt/mod.ax
- compiler/opt/ipa/mod.ax
- tests/run/opt_ipa_devirt/callsite_const_closure_spec.ax
- tests/run/opt_ipa_devirt/dyn_trait_and_fnptr_devirt.ax
- tests/run/opt_ipa_devirt/opt_ipa_devirt_engine.test
- tests/run/opt_ipa_devirt/opt_ipa_devirt_oracle.py
- tests/run/opt_ipa_devirt/opt_ipa_devirt_probe.ax.in
- tests/run/opt_ipa_devirt/tailcall_loop_lowering_and_drop_guards.ax

## Verification

- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T614`: `0 REFUSED` (exit 0)
- `python build-snap-T614/tools/archcheck.py`: `193 files scanned, 0 violations`
- `python build-snap-T614/tools/axtest.py --root build-snap-T614 --build-dir build-snap-T614/build -j 1 run/opt_ipa_devirt opt2 run/opt_escape run/opt_alias run/opt_passmgr run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax`: `PASS` (`0 WEAK-NATIVE`)

STATUS: COMPLETE round=0
