---
id: T703
title: E17.1 Debug IR, CodeView C13 & deterministic PDB 7.00 conformance suite
phase: P17-debugging-runtime-introspectio
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T217, T316, T702]
priority: 173
status: todo
attempts: 0
paths: [tests/conformance/p17/e17_1_codeview_pdb]
spec: [spec/SPEC-92-debug-ir-codeview-pdb.md, 0190, 0191, tasks/0419, tasks/0525]
covers: [REQ-DBG-117, REQ-DBG-118]
---
# T703 — E17.1 Debug IR, CodeView C13 & deterministic PDB 7.00 conformance suite

## Goal
Certify the E17.1 exit criteria: Debug IR semantic invariance, CodeView C13 `.debug$S`/`.debug$T` fidelity, and deterministic PDB 7.00 generation on Windows.

## Scope
- Create `tests/conformance/p17/e17_1_codeview_pdb` covering:
-   - Semantic non-interference (`DEBUG-20`, `ADBG-20`): differential `-g` vs stripped builds at `-O0`, `-O1`, and `-O2` verifying identical `.text`/`.rdata` machine bytes and identical runtime outputs.
-   - CodeView `.debug$T` type layout verification for primitives, structs (with reordered/padded fields per `0190 §18`), payload enums, slices, views, tuples, and function pointers.
-   - CodeView `.debug$S` symbol, lexical scope (`S_BLOCK32`), register/stack variable range (`S_DEFRANGE_*`), explicit `OptimizedOut` (`ADBG-25`), and inline site (`S_INLINESITE` + `DEBUG_S_INLINEELINES`) verification.
-   - MSF v7 / PDB 7.00 structural verification, `RSDS` GUID/Age matching, mismatch detection (`ADEBUG-96`), and byte-for-byte determinism across repeated builds.

## Acceptance
- [ ] All conformance tests in `tests/conformance/p17/e17_1_codeview_pdb` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T703-report.md` with exact `## Files changed`.

## Out of scope
- DWARF v5 conformance (`T707`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)
