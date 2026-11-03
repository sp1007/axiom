---
id: T403
title: E11.1 — Synchronization & happens-before contracts in MIR optimizer & verifier
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T402]
priority: 124
status: todo
attempts: 0
paths: [compiler/opt, tests/mir/concurrency, tests/selfhost]
locks: [compiler/mir/mir.ax, compiler/verify/verifier.ax, tests/selfhost]
spec: [spec/SPEC-30-concurrency.md, 0033, 0126, 0136, tasks/0488, tasks/0685]
covers: [REQ-CONC-074, REQ-CONC-090, REQ-CONC-112, REQ-CONC-113, REQ-CONC-114, REQ-CONC-122, REQ-CONC-124, REQ-CONC-144, REQ-CONC-166, REQ-CONC-208, REQ-CONC-209, REQ-CONC-210, REQ-CONC-211, REQ-CONC-212, REQ-CONC-213, REQ-CONC-214, REQ-CONC-215, REQ-CONC-216]
---
# T403 — E11.1 — Synchronization & happens-before contracts in MIR optimizer & verifier

## Goal
Ensure MIR optimization passes (`const_fold`, `dce`, `cfg_simp`) and the MIR verifier preserve happens-before edges, synchronization boundaries, and zero-overhead erasure of compile-time concurrency proofs.

## Scope
- Annotate synchronization-bearing calls, atomic statements, and fences as memory barriers in `compiler/mir/mir.ax` and `compiler/opt/{const_fold,dce,cfg_simp}.ax` so optimizer passes never eliminate, reorder, or fold ordinary memory accesses across a synchronization boundary (`ACONC-27`, `ACONC-76`, `ACONCUR-195`).
- Verify in `compiler/verify/verifier.ax` that `Send`/`Share` proof obligations are completely erased at runtime with zero hidden metadata or runtime overhead (`ACONCUR-190..191`).
- Ensure concurrency verification and MIR optimization remain 100% deterministic (`ACONCUR-196`).

## Acceptance
- [ ] `tests/mir/concurrency/*.ax` golden/inspect tests verify at `-O0` and `-O1` (`inspect --emit=mir-opt`) that loads/stores separated by synchronization barriers are not folded or eliminated, while purely local non-escaping operations still optimize cleanly.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T403` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T403-report.md` with exact `## Files changed`.

## Out of scope
- OptIR SSA / MemorySSA passes (Phase 15 `E15.1`).

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T403/build` and `python tools/axtest.py --compiler build-snap-T403/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
