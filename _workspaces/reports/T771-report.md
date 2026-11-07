# T771 Implementation Report (Round 0)

## Summary
Implemented the end-to-end E18.5 Pass Contracts, Proof-Carrying IR & Translation Validation Conformance Suite in `tests/conformance/p18/e18_5_pass_contracts` per `spec/SPEC-25-pass-contracts-proof-carrying-ir.md` (`AXS-PCT-001..053`, `INV-PCT-001..003`) and `REQ-LNK-3384..3433`:

1. **Differential `.ax` Conformance Programs & `-O2 --verify-each` Variants (`0 WEAK-NATIVE`)**:
   - `overflow_and_signed_unsigned_polarity.ax` + `o2_overflow_and_signed_unsigned_polarity.ax`: Exercises checked vs wrapping arithmetic, shift-in-range, congruence-proven non-zero divisor proofs, signed vs unsigned comparison/division/remainder/shift polarity (`REQ-CORE-3268`), narrow integer sign/zero extension, 128-bit `(lo, hi)` multi-limb carry chains, and fail-closed rollback on `Certainty.Unknown` obligations inside untaken loop branches across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`.
   - `drop_capability_and_effect_barriers.ax` + `o2_drop_capability_and_effect_barriers.ax`: Exercises deterministic LIFO `Drop` ordering across nested scopes and early returns, capability exclusivity (`view<T>` vs `mut_view<T>`, sequential reborrowing, SROA, DSE, and store-to-load forwarding), and multi-category `EffectSummary` barriers (higher-order callback effect propagation and preservation of impure calls with unused return values).
   - `volatile_atomic_and_schedule_invariants.ax` + `o2_volatile_atomic_and_schedule_invariants.ax`: Exercises `volatile`/MMIO load-store ordering barriers (`REQ-CORE-3254`), `atomic` state-machine synchronization ordering (`REQ-CORE-3255`, `REQ-CORE-3272`), raw-pointer may-alias conservative barriers (`REQ-CORE-3252..3253`), high register-allocation live-range pressure across calls with fixed `RCX` shift and `RAX:RDX` `idiv`/`irem` constraints, and instruction scheduling `RAW`/`WAR`/`WAW` + `EFLAGS` condition-code dependencies across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`.
   - `final_machine_ir_and_frame_reproducibility.ax` + `o2_final_machine_ir_and_frame_reproducibility.ax`: Exercises Final Machine IR 3.0 invariants (`AXS-PCT-024`, `REQ-LNK-3384..3433`) across Win64 8-argument calls (4 register + 4 stack arguments, 16-byte `RSP` alignment), multi-array stack frame layouts with dynamic indexing, shrink-wrap early-return + unwind `Drop` guard paths, and `Secret<T>` zeroization barriers that must not be eliminated by DSE or finalization passes.

2. **Live Bundled Conformance Probe & Oracle (`e18_5_conformance.test`, `e18_5_conformance_oracle.py`, `e18_5_conformance_probe.ax.in`)**:
   - Compiles and runs all 4 differential conformance programs across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each`, verifying exact bit-identical stdout, exit code `0`, and byte-for-byte deterministic repeated `--verify-each` PE builds (`INV-PCT-003`).
   - Bundles `compiler.mir.mir`, `compiler.verify.pass_contracts`, and `compiler.verify.translation_val` with `e18_5_conformance_probe.ax.in` via `axiomc2.exe` at `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each` to verify end-to-end `--verify-pass-contracts` and `--validate-translations` execution, fail-closed rollback on `Unknown`/`Possible` obligations, deterministic canonical JSON `--emit=pass-witness` serialization, and synthetic pass-bug rejection (`AX_OPT_POSTCOND_FAILED`, `AX_OPT_PROOF_INVALID`, `AX_OPT_WITNESS_CORRUPT`, `AX_TV_EQUIV_FAILED`, `AX_TV_OVERFLOW_MISMATCH`, `AX_TV_ALIAS_VIOLATED`, `AX_TV_EFFECT_ORDER_BROKEN`, `AX_TV_DROP_MISMATCH`, `AX_TV_CAP_VIOLATED`, `AX_TV_BACKEND_MISMATCH`, `AX_TV_WITNESS_INCOMPLETE`) across optimization and backend passes (`INV-PCT-001..003`).

## Files changed
- `tests/conformance/p18/e18_5_pass_contracts/drop_capability_and_effect_barriers.ax`
- `tests/conformance/p18/e18_5_pass_contracts/e18_5_conformance.test`
- `tests/conformance/p18/e18_5_pass_contracts/e18_5_conformance_oracle.py`
- `tests/conformance/p18/e18_5_pass_contracts/e18_5_conformance_probe.ax.in`
- `tests/conformance/p18/e18_5_pass_contracts/final_machine_ir_and_frame_reproducibility.ax`
- `tests/conformance/p18/e18_5_pass_contracts/o2_drop_capability_and_effect_barriers.ax`
- `tests/conformance/p18/e18_5_pass_contracts/o2_final_machine_ir_and_frame_reproducibility.ax`
- `tests/conformance/p18/e18_5_pass_contracts/o2_overflow_and_signed_unsigned_polarity.ax`
- `tests/conformance/p18/e18_5_pass_contracts/o2_volatile_atomic_and_schedule_invariants.ax`
- `tests/conformance/p18/e18_5_pass_contracts/overflow_and_signed_unsigned_polarity.ax`
- `tests/conformance/p18/e18_5_pass_contracts/volatile_atomic_and_schedule_invariants.ax`

## Verification
- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T771` -> `snapshot D:\projects\compiler\new lang\build-snap-T771 (refreshed: HEAD df99205 + 11 changed, 0 deleted file(s) of T771)`
- `python build-snap-T771/tools/build_axiomc.py --root build-snap-T771 --out build-snap-T771/build` -> `BUILD-AXIOMC OK: D:\projects\compiler\new lang\build-snap-T771\build\axiomc2.exe`
- `python build-snap-T771/tools/axtest.py --root build-snap-T771 --build-dir build-snap-T771/build --compiler build-snap-T771/build/axiomc2.exe -j 1 conformance/p18/e18_5_pass_contracts run/pass_contracts run/translation_val run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax` -> `WEAK-NATIVE 0`, `TOTAL 42 PASS 42 FAIL 0 SKIP 0 XFAIL 0`
- `python tools/archcheck.py` -> `archcheck: 193 files scanned, 0 violations`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T771` -> `0 REFUSED`

STATUS: COMPLETE round=0
