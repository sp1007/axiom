---
id: T517
title: E13.4 — Safety profile enforcement (@forbid_unsafe, capability-only IO/net/fs, sandbox verification)
phase: P13-low-level-systems-unsafe-frees
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T516]
priority: 166
status: todo
attempts: 0
paths: [compiler/driver, compiler/sema, tests/ui/security_profiles, tests/selfhost]
spec: [spec/SPEC-53-safety-profiles-capability-security.md, tasks/0342, tasks/0449, tasks/0703]
covers: [REQ-CAP-010, REQ-CAP-123, REQ-CAP-131]
---
# T517 — E13.4 — Safety profile enforcement (@forbid_unsafe, capability-only IO/net/fs, sandbox verification)

## Goal
Implement `--safety-profile safe|sandbox|system`, `@forbid_unsafe` module/crate enforcement, and ambient-authority ban verification in `compiler/driver` and `compiler/sema`.

## Scope
- Enforce `@forbid_unsafe` and `--safety-profile safe|sandbox` in `compiler/sema`: reject `unsafe` blocks, `unsafe fn` definitions, raw pointer dereferences, `extern` blocks, and `@at`/`@addr` declarations with `AX_SEC_UNSAFE_FORBIDDEN`.
- Enforce the `sandbox` and `comptime` ambient-authority ban (`REQ-CAP-131`): reject calls to ambient OS APIs unless an explicit authority capability token (`FsCap`, `NetCap`, `EnvCap`, `ProcessCap`) is passed.
- Reject attempts to forge safe capabilities from integer addresses or raw pointers outside `unsafe` (`REQ-CAP-123`).

## Acceptance
- [ ] Positive and negative UI tests in `tests/ui/security_profiles` verify `@forbid_unsafe`, `--safety-profile sandbox` ambient-authority rejection, and explicit capability-token acceptance.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T517-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T517/build` and `python tools/axtest.py --compiler build-snap-T517/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:03:00 created by T213 (P13 phase planning)
