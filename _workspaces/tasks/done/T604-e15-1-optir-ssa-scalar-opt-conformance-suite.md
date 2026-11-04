---
id: T604
title: E15.1 — OptIR SSA/MemorySSA, pass-contract verifier & scalar optimization conformance suite
phase: P15-optimizer-2-0
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T603]
priority: 97
status: done
attempts: 1
paths: [tests/conformance/p15/e15_1_optir_ssa]
spec: [spec/SPEC-70-optir-ssa-memoryssa.md, 0165, tasks/0366, tasks/0398, tasks/0399, tasks/0423]
covers: [REQ-OPT-037, REQ-OPT-038, REQ-OPT-039, REQ-OPT-040, REQ-OPT-041, REQ-OPT-343]
started: 2026-11-04 17:00:03
finished: 2026-11-04 20:15:42
---
# T604 — E15.1 — OptIR SSA/MemorySSA, pass-contract verifier & scalar optimization conformance suite

## Goal
Certify E15.1 exit criteria with an end-to-end differential conformance suite covering `OptIR` SSA/`MemorySSA` construction, `EffectInfo` and pass-contract verification, and scalar optimizations (SCCP, GVN, CSE, DCE).

## Scope
- Create differential conformance tests in `tests/conformance/p15/e15_1_optir_ssa` verifying:
  - exact observable equivalence between `--interp`, `-O0`, `-O1`, and `-O2` (`REQ-OPT-343`) across complex diamond/loop CFGs, checked vs wrapping arithmetic, panic paths, and deterministic `Drop` ordering;
  - `MemorySSA` def-use and phi integrity under `--verify-each`;
  - preservation of `black_box`, `volatile`, atomics, I/O ordering, and secure zeroization against aggressive DCE/GVN (`REQ-OPT-037..041`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p15/e15_1_optir_ssa` pass in `--interp` and native `-O0`/`-O1`/`-O2` modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T604-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T604/build` and `python tools/axtest.py --compiler build-snap-T604/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:38:00 created by T215 (P15 phase planning)
- 2026-11-04 17:00:03 started (attempt 1) T604-impl
- 2026-11-04 20:15:42 accepted by QA -> done
