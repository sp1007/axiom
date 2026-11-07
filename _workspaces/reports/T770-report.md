# T770 Report — E18.5 Translation Validation Witness Checker Across MIR/OptIR/LIR/Machine Passes

## Summary

Implemented the bounded translation validation and witness checker (`compiler/verify/translation_val/mod.ax`) and end-to-end verification suite (`tests/run/translation_val/*`) for **E18.5** per `spec/SPEC-25-pass-contracts-proof-carrying-ir.md` (`§3 AXS-PCT-020..024`, `§4 AXS-PCT-050..053`, `INV-PCT-002`):

1. **Five-Tier Observable Semantic Equivalence Hierarchy & `TranslationWitness` (`AXS-PCT-020`)**:
   - Defined `EquivalenceLevel` (`Level0Structural`, `Level1Value`, `Level2MemoryResource`, `Level3EffectTrap`, `Level4ObservableSemantic`) and `tval_evaluate_equivalence_tier` / `tval_meets_mandatory_criterion` enforcing Level 4 (conjunction of Levels 1–3) as the mandatory pass correctness criterion.
   - Implemented `TranslationWitness`, `TranslationValEngine`, `tval_compute_mir_fingerprint`, `tval_compute_stage_fingerprint`, and `tval_check_proof_cert_kind`.

2. **Middle-End Translation Validation (`AXS-PCT-021`)**:
   - **Scalar & Algebraic Rewrites (`AXS-PCT-021.1`)**: `ScalarRewriteWitnessDesc` and `tval_validate_scalar_rewrite` verify exact bit-width, signed/unsigned comparison/division/shift polarity (`REQ-CORE-3268`), IEEE-754 `NaN` and `-0.0` preservation on floating-point rewrites, and checked-arithmetic trap preservation (`NoSignedOverflow`/`NoUnsignedOverflow`, `NonZero`, `ShiftInRange`, `InBounds`) backed by `Certainty.Proven` `ProofCertificate`s in `ProofStore`.
   - **CFG Canonicalization & Unreachable Block Removal (`AXS-PCT-021.2`)**: `CfgTransformWitnessDesc` and `tval_validate_cfg_transform` enforce `CERTAINTY_PROVEN` `ReachableEdge` conditions before edge/block removal, `phi`/`MemoryPhi` predecessor completeness, valid dominance, MIR structural/capability invariants, and preservation of observable `Drop`/effect counts.
   - **Memory & Loop Transformations (`AXS-PCT-021.3`)**: `MemoryLoopTransformWitnessDesc` and `tval_validate_memory_loop_transform` validate `DSE`, `LoadForward`, `SROA`, `LICM`, and `BCE` against `DeadStore`, `MustAlias`, `NoAlias`, `NoEscape`, `LoopInvariant`, and `InBounds` certificates while rejecting elimination or reordering of `volatile`/`MMIO`, `atomic`, `Drop`, or capability barriers.

3. **Target Legalization & Register Allocation Witness Validation (`AXS-PCT-022`)**:
   - **Target Legalization (`AXS-PCT-022.1`)**: `TargetLegalizationWitnessDesc` and `tval_validate_target_legalization` verify narrow-integer promotion, 128-bit `(lo, hi)` pair splitting with carry/borrow chains (`SPEC-40`), and SIMD vector splitting (`SPEC-43`).
   - **Register Allocation & Spill/Reload (`AXS-PCT-022.2`)**: `tval_phys_reg_unit` (mapping `RAX`/`EAX`/`AX`/`AL`/`AH` to unit `0` and `XMMi`/`YMMi` to unit `16 + i`), `tval_is_win64_caller_saved_unit`, `LiveRangeAllocEntry`, `SpillSlotEntry`, `RegAllocWitnessDesc`, and `tval_validate_regalloc_witness` verify zero remaining virtual registers, no overlapping live intervals sharing a physical register unit unless move-coalesced with identical `value_provenance`, dominating spill stores to dedicated stack slots without aliasing user locals or `volatile`/`MMIO`, fixed-register ISA constraints (`RCX` shifts, `RAX:RDX` `div`/`mul`), and caller/callee-save ABI contracts.

4. **Instruction Scheduling Dependency & Barrier Witness Validation (`AXS-PCT-023`)**:
   - `ScheduleNodeEntry`, `ScheduleDepEdge`, `ScheduleWitnessDesc`, and `tval_validate_schedule_witness` verify conservative fallback on unknown latency models, topological preservation of `RAW`/`WAR`/`WAW` edges across GPR, XMM/vector, stack slots, and `EFLAGS`, and strict ordering barriers for `volatile`/`MMIO`, `atomic`, `fence`, `call`, trapping `Assert`/`idiv`/`div`, and non-`NoAlias` memory accesses.

5. **Machine Code Finalization Gate (`AXS-PCT-024`)**:
   - `FinalMachineGateDesc` and `tval_validate_machine_finalization_gate` enforce `allocated -> scheduled -> framed -> unwindable -> security-valid -> encodable` (`FINAL_STAGE_COMPLETE_MASK = 0x3F`), zero remaining virtual registers or abstract stack slots, 16-byte Win64 call-site `RSP` alignment, `__chkstk` probes on frames `>= 4096` bytes (`ADR-0003`), `Secret<T>` zeroization barriers, and `.pdata`/`.xdata` unwind & callee-save symmetry.

6. **Diagnostic Trap Reporting & Deterministic Witness Formatter (`AXS-PCT-050..052`)**:
   - `tval_emit_validation_trap_diagnostic` emits `AX_ICE_MIR_VERIFY` (middle-end) or `AX_ICE_INTERNAL` (backend) with structured `data.stage = "translation_val"`, `data.pass_id`, and `data.detail`.
   - `tval_format_pass_witness_report` formats deterministic `inspect --emit=pass-witness` summaries combining pass-contract and translation-witness records.

## Files changed

- compiler/verify/translation_val/mod.ax
- tests/run/translation_val/translation_val_engine.test
- tests/run/translation_val/translation_val_equivalence.ax
- tests/run/translation_val/translation_val_oracle.py
- tests/run/translation_val/translation_val_probe.ax.in

## Verification

- Built `axiom0.exe`, `axiomc1.exe`, and `axiomc2.exe` in isolated snapshot `build-snap-T770/build`.
- Ran `python build-snap-T770/tools/axtest.py --root build-snap-T770 --build-dir build-snap-T770/build --compiler build-snap-T770/build/axiomc2.exe -j 1 run/translation_val run/pass_contracts run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax`: `TOTAL 18 PASS 18 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`).
- Verified `python tools/archcheck.py` and `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T770`.

STATUS: COMPLETE round=0
