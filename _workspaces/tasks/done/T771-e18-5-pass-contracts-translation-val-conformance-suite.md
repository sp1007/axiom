---
id: T771
title: E18.5 — Pass contracts, proof-carrying transformations & fail-closed verifier conformance suite
phase: P18-compiler-architecture-2-0
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T770]
priority: 721
status: done
attempts: 1
paths: [tests/conformance/p18/e18_5_pass_contracts]
spec: [spec/SPEC-25-pass-contracts-proof-carrying-ir.md, tasks/0545, tasks/0577, tasks/0578, tasks/0796, tasks/0797]
covers: [REQ-LNK-3384, REQ-LNK-3385, REQ-LNK-3386, REQ-LNK-3387, REQ-LNK-3388, REQ-LNK-3389, REQ-LNK-3390, REQ-LNK-3391, REQ-LNK-3392, REQ-LNK-3393, REQ-LNK-3394, REQ-LNK-3395, REQ-LNK-3396, REQ-LNK-3397, REQ-LNK-3398, REQ-LNK-3399, REQ-LNK-3400, REQ-LNK-3401, REQ-LNK-3402, REQ-LNK-3403, REQ-LNK-3404, REQ-LNK-3405, REQ-LNK-3406, REQ-LNK-3407, REQ-LNK-3408, REQ-LNK-3409, REQ-LNK-3410, REQ-LNK-3411, REQ-LNK-3412, REQ-LNK-3413, REQ-LNK-3414, REQ-LNK-3415, REQ-LNK-3416, REQ-LNK-3417, REQ-LNK-3418, REQ-LNK-3419, REQ-LNK-3420, REQ-LNK-3421, REQ-LNK-3422, REQ-LNK-3423, REQ-LNK-3424, REQ-LNK-3425, REQ-LNK-3426, REQ-LNK-3427, REQ-LNK-3428, REQ-LNK-3429, REQ-LNK-3430, REQ-LNK-3431, REQ-LNK-3432, REQ-LNK-3433]
started: 2026-11-07 17:49:55
finished: 2026-11-07 18:51:13
---
# T771 — E18.5 — Pass contracts, proof-carrying transformations & fail-closed verifier conformance suite

## Goal
Certify E18.5 exit criteria with an end-to-end conformance suite covering compiler pass contracts, proof-carrying IR transformations, fail-closed rollback on `Unknown` proofs, and bounded translation validation across optimization and backend passes.

## Scope
- Create conformance tests in `tests/conformance/p18/e18_5_pass_contracts` verifying:
  - `--verify-pass-contracts` and `--validate-translations` succeed cleanly across the conformance corpus at `-O0`, `-O1`, and `-O2`;
  - overflow, signed/unsigned comparison, `Drop`, atomic, `volatile`, and capability invariants are preserved across all passes (`tasks/0796`, `tasks/0797`);
  - differential equivalence between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p18/e18_5_pass_contracts` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T771-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P18 (`P18-compiler-architecture-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T771/build` and `python tools/axtest.py --compiler build-snap-T771/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:59:35 created by T218 (P18 phase planning)
- 2026-11-07 17:49:55 started (attempt 1) T771-impl
- 2026-11-07 18:51:13 accepted by QA -> done
