# T540 report — Baseline fix: safety_profile_safe_neg / forbid_unsafe_constructs_neg vs the T501 `@addr` placement rule

## Summary
Both tests declared a fixed-address `static` **with an initializer** (`= 0u32`), which T501 treats as a pinned placement
that typeck rejects with `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` before the safety-profile pass runs. Per the architect's
decision both are rewritten to the overlay form without initializer, with the `unsafe` modifier required by ADR-0001 §2.
No compiler change was needed: `sec_check_item_header_forbid_unsafe` (`compiler/types/typeck.ax`) already reports exactly
one `AX_SEC_UNSAFE_FORBIDDEN` (`fixed_addr`) on an `@addr`/`@at` item.

## Changes
- `safety_profile_safe_neg.ax`: `@addr(0x4000usize) unsafe static FIXED_PORT: u32;` (expectation kept on the attribute line).
- `forbid_unsafe_constructs_neg.ax`: `@at(0x1000usize) unsafe static MMIO_REG: u32;`, all 15 `AX_SEC_UNSAFE_FORBIDDEN` kept.
  Once the pipeline no longer stopped early, a second latent defect in the fixture surfaced: `unsafe impl NormalTrait for Node`
  where `NormalTrait` is not an `unsafe trait` gives `AX_UNSAFE_UNNECESSARY_IMPL` (correct compiler behaviour). The fixture is
  fixed rather than the compiler: the `unsafe impl` now targets the `unsafe trait TrustedMarker` (still exactly one
  `AX_SEC_UNSAFE_FORBIDDEN`, class `unsafe_impl`), and a plain `impl NormalTrait for Node` is kept. Count of expectations unchanged (15).
- New `safety_profile_safe_addr_fn_neg.ax` (`--safety-profile safe`): `@addr(..) unsafe fn` overlay placement yields exactly one
  `AX_SEC_UNSAFE_FORBIDDEN`.
- `_workspaces/baseline-failures.txt`: removed both T540 lines (and the comment line that referred to the T540 cause).

## Decisions
- Fixture fix over compiler change for the `unsafe impl` issue: the diagnostic is right and the test's intent (unsafe impl is
  forbidden under `@forbid_unsafe`) is preserved.
- Pinned-placement-in-safe-profile coverage is left to T526 as stated in the task.

## Verification (snapshot `build-snap-T540`, HEAD 1401fb1 + these files; `tools/build_axiomc.py` O1 chain, fixed point OK)
- `axtest --no-cache -j 2 ui/security_profiles ui/unsafe ui/fixed_addr`: TOTAL 35; first run 34 PASS / 1 FAIL
  (`forbid_unsafe_constructs_neg`, `AX_UNSAFE_UNNECESSARY_IMPL` line 27), fixed as above; re-run of `ui/security_profiles/forbid`
  and `ui/security_profiles/safety`: TOTAL 7 PASS 7.
- No `tests/ui/fixed_addr*` directory exists; `tests/ui/unsafe` all pass.

## Files changed
- tests/ui/security_profiles/safety_profile_safe_neg.ax
- tests/ui/security_profiles/forbid_unsafe_constructs_neg.ax
- tests/ui/security_profiles/safety_profile_safe_addr_fn_neg.ax
- _workspaces/baseline-failures.txt

STATUS: COMPLETE round=0
