---
id: T516
title: E13.4 — Canonical safety profiles, ambient-authority ban, secure memory & constant-time specification (SPEC-53)
phase: P13-low-level-systems-unsafe-frees
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T213]
priority: 165
status: todo
attempts: 0
paths: [spec/SPEC-53-safety-profiles-capability-security.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-03-core-semantics.md, spec/SPEC-11-capability.md, tasks/0342, tasks/0449, tasks/0467, tasks/0703]
covers: [REQ-CAP-123, REQ-FFI-117, REQ-CAP-131, REQ-CAP-010]
---
# T516 — E13.4 — Canonical safety profiles, ambient-authority ban, secure memory & constant-time specification (SPEC-53)

## Goal
Specify Axiom's safety profiles (`@forbid_unsafe`, `--safety-profile safe|sandbox|system`), capability-based OS authority tokens (distinguishing resource authority from `view<T>`/`mut_view<T>` memory capabilities), secure memory zeroization (`Secret<T>`), and constant-time execution contracts (`@constant_time` / `@secret`) in `spec/SPEC-53-safety-profiles-capability-security.md` (`AXS-SEC-*` rule IDs).

## Scope
- Write `spec/SPEC-53-safety-profiles-capability-security.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-SEC-NNN` rules.
- Specify safety profiles (`safe`, `sandbox`, `system`) and module/package-level `@forbid_unsafe` / `@allow_unsafe` policy attributes.
- Specify resource authority capabilities (`FsCap`, `NetCap`, `EnvCap`, `ProcessCap`, `ClockCap`), the prohibition of ambient OS authority in `sandbox` and `comptime` profiles (`REQ-CAP-131`), and the distinction between raw pointers/integer addresses and capability provenance (`REQ-CAP-123`).
- Specify `Secret<T>` non-elidable zeroize-on-drop semantics and `@constant_time` / secret-value restrictions (forbidding secret-dependent conditional branches, variable-latency instructions such as hardware `DIV`/`IDIV`, and secret-indexed memory lookups).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-53-safety-profiles-capability-security.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-SEC-NNN` rules, positive/negative canonical Axiom examples, and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T516-report.md` with exact `## Files changed`.

## Out of scope
- Compiler or std implementation (handled by `T517`–`T519`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:03:00 created by T213 (P13 phase planning)
