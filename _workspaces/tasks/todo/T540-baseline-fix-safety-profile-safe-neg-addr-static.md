---
id: T540
title: Baseline fix — ui/security_profiles/safety_profile_safe_neg (@addr static with initializer hits AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP)
phase: P13-low-level-systems-unsafe-frees
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: []
priority: 20
status: todo
attempts: 0
paths: [tests/ui/security_profiles]
locks: [compiler/types/typeck.ax, compiler/own/unsafe.ax, _workspaces/baseline-failures.txt]
spec: [spec/SPEC-53-safety-profiles-capability-security.md, spec/SPEC-50-unsafe-ub-ffi.md, spec/decisions/ADR-0001-fixed-address-declarations.md]
covers: [REQ-CAP-010, REQ-OWNER-008]
started: 2026-11-26 01:42:36
---
# T540 — Baseline fix: safety_profile_safe_neg vs the T501 `@addr` placement rule

## Why
`tests/ui/security_profiles/safety_profile_safe_neg.ax` (T517, SPEC-53 AXS-SEC-003) declares
`@addr(0x4000usize) static FIXED_PORT: u32 = 0u32;` and expects `AX_SEC_UNSAFE_FORBIDDEN`. T501 (accepted after
T517) made a `@addr` static **with an initializer** a pinned placement (ADR-0001 §1), which typeck rejects with
`AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` until T526/T528 (`tc_validate_addr_item` in `compiler/types/typeck.ax`). The
test now reports that diagnostic instead (T427-qa.md §3; identical at HEAD f9ecfc8d). Admitted to
`_workspaces/baseline-failures.txt` on 2026-11-25 with this task as its fix task.

## Decision (architect, triage 2026-11-25)
The test's intent is "a fixed-address declaration is forbidden under `--safety-profile safe`", not "pinned
placement works". Rewrite that declaration in the form T501 supports — the overlay form without an initializer,
with the `unsafe` modifier ADR-0001 §2 requires (`@addr(0x4000usize) unsafe static FIXED_PORT: u32;`) — and expect
`AX_SEC_UNSAFE_FORBIDDEN` on it. Pinned placement in a safe profile is re-covered by T526 when it lifts the
bootstrap rejection (T526 already owns the `@addr` UI tests).

## Scope
1. Update the declaration and its `//~` annotations as above. If the safety-profile check does not report
   `AX_SEC_UNSAFE_FORBIDDEN` on the overlay form (or reports an extra diagnostic), fix the check in the owning
   compiler file (`compiler/types/typeck.ax` / `compiler/own/unsafe.ax`, shared locks) so that a `@addr`/`@at`
   item under `@forbid_unsafe` / `--safety-profile safe` yields exactly one `AX_SEC_UNSAFE_FORBIDDEN`.
2. Add one companion case to `tests/ui/security_profiles/` that pins the interaction explicitly: an `@addr`
   overlay `fn` placement under `--safety-profile safe` gives `AX_SEC_UNSAFE_FORBIDDEN`.
3. Remove the T540 lines from `_workspaces/baseline-failures.txt` in the same change.
4. (Added 2026-11-26, `_workspaces/reports/unblock-T428m.md`.) The same defect hits
   `tests/ui/security_profiles/forbid_unsafe_constructs_neg.ax` (AXS-SEC-001): its line 45
   `@at(0x1000usize) static MMIO_REG: u32 = 0u32;` gives `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP`, which stops the
   pipeline before the `@forbid_unsafe` check, so all 15 expected `AX_SEC_UNSAFE_FORBIDDEN` are missing (identical
   with the HEAD compiler `axiomc2_O1_642250f08b7af786.exe`, T428m sweep). Apply the same rewrite (overlay form
   without initializer, `unsafe` modifier per ADR-0001 §2) and keep all 15 expectations.

## Acceptance
- [ ] `ui/security_profiles/safety_profile_safe_neg.ax`, `ui/security_profiles/forbid_unsafe_constructs_neg.ax` and
      the new case pass; all of `tests/ui/security_profiles`
      and `tests/ui/fixed_addr*` / `tests/ui/unsafe*` (if present) still pass.
- [ ] Baseline line removed.
- [ ] Normal gate. Report `_workspaces/reports/T540-report.md` with an exact `## Files changed`.

## Log
- 2026-11-25 created by architect (triage after T427 accept, `_workspaces/reports/triage-2026-11-25-T427.md`)
- 2026-11-26 01:42:36 started (attempt 1) T540-impl
- 2026-11-26 01:42:45 requeue: orchestrator: baseline-failures.txt has an uncommitted edit from blocked T428a (and its unblock); wait (not charged: attempt refunded)
- 2026-11-26 architect: scope item 4 added (forbid_unsafe_constructs_neg.ax, same cause; unblock-T428m.md)
