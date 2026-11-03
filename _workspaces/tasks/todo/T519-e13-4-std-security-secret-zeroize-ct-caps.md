---
id: T519
title: E13.4 — std.security capability tokens, zeroize-on-drop Secret<T>, constant-time primitives & sandbox hooks
phase: P13-low-level-systems-unsafe-frees
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T517, T518]
priority: 168
status: todo
attempts: 0
paths: [std/security, tests/std/security, tests/selfhost]
spec: [spec/SPEC-53-safety-profiles-capability-security.md, tasks/0342, tasks/0449, tasks/0467, tasks/0703]
covers: [REQ-CAP-135, REQ-CAP-136, REQ-CAP-138, REQ-CAP-139]
---
# T519 — E13.4 — std.security capability tokens, zeroize-on-drop Secret<T>, constant-time primitives & sandbox hooks

## Goal
Implement `std/security` providing `Secret<T>` with guaranteed zeroize-on-drop, constant-time comparison and selection primitives (`ct_eq`, `ct_select`, `ct_copy_if`), and attenuated resource capability tokens (`FsCap`, `NetCap`, `EnvCap`) with lifetime-checked buffer views.

## Scope
- Implement `Secret<T>` and `Zeroize` in `std/security/secret.ax`: redact `Debug`/`Display` formatting (`"<secret>"`), forbid implicit `Copy`, and guarantee memory scrubbing via `zeroize_memory` in `impl Drop`.
- Implement constant-time primitives (`ct_eq_bytes`, `ct_select_u8..u64`, `ct_swap_if`) verified under `@constant_time`.
- Implement `FsCap` (directory-confined path capability), `NetCap`, and zero-copy I/O buffer lifetime guards ensuring scatter/gather and mapped views never outlive their backing storage (`REQ-CAP-135`, `REQ-CAP-136`, `REQ-CAP-138`, `REQ-CAP-139`).

## Acceptance
- [ ] Tests in `tests/std/security` verify `Secret<T>` zeroization on scope exit, redacted formatting, constant-time byte comparisons, and attenuated `FsCap`/`NetCap` capability bounds in both `--interp` and native execution.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T519-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T519/build` and `python tools/axtest.py --compiler build-snap-T519/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:03:00 created by T213 (P13 phase planning)
