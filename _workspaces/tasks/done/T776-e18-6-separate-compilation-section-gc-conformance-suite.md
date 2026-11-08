---
id: T776
title: E18.6 — Separate compilation, multi-object archives, section GC & P18 exit conformance suite
phase: P18-compiler-architecture-2-0
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T775, T759, T763, T767, T771, T773]
priority: 725
status: done
attempts: 1
paths: [tests/conformance/p18/e18_6_separate_compilation]
spec: [spec/SPEC-27-separate-compilation-linker-v2.md, 0099, 0164, 0217, tasks/0369, tasks/0526, tasks/0786, tasks/0804]
covers: [REQ-LNK-3945, REQ-LNK-3946, REQ-LNK-3947, REQ-LNK-3948, REQ-LNK-3949, REQ-LNK-3950, REQ-LNK-3951, REQ-LNK-3952, REQ-LNK-3953, REQ-LNK-3954, REQ-LNK-3955, REQ-LNK-3956, REQ-LNK-3957, REQ-LNK-3958, REQ-LNK-3959, REQ-LNK-3960, REQ-LNK-3961, REQ-LNK-3962, REQ-LNK-3963, REQ-LNK-3964, REQ-LNK-3965, REQ-LNK-3966, REQ-LNK-3967, REQ-LNK-3968, REQ-LNK-3969, REQ-LNK-3970, REQ-LNK-3971, REQ-LNK-3972, REQ-LNK-3973, REQ-LNK-3974, REQ-LNK-3975, REQ-LNK-3976, REQ-LNK-3977, REQ-LNK-3978, REQ-LNK-3979, REQ-LNK-3980, REQ-LNK-3981, REQ-LNK-3982, REQ-LNK-3983]
started: 2026-11-08 14:22:06
finished: 2026-11-08 14:44:01
---
# T776 — E18.6 — Separate compilation, multi-object archives, section GC & P18 exit conformance suite

## Goal
Certify E18.6 and the integrated P18 Compiler Architecture 2.0 pipeline with an end-to-end conformance suite covering separate per-module `.obj` + `.axmi` compilation, `.lib` archive linking, `COMDAT` generic deduplication, section GC, and incremental/parallel rebuilds.

## Scope
- Create conformance tests in `tests/conformance/p18/e18_6_separate_compilation` verifying:
  - multi-module workspaces compiled separately to `.obj` + `.axmi` and linked with `.lib` and `.dll` artifacts produce byte-identical executables to whole-workspace builds;
  - `COMDAT` deduplication and section GC strip unused library code and preserve all live/exported/unwind sections;
  - editing one private function in a multi-module separate-compilation project re-typechecks and re-emits only that module's `.obj` (`< 100 ms` no-op rebuild on the compiler itself);
  - differential equivalence between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p18/e18_6_separate_compilation` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T776-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated phases; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P18 (`P18-compiler-architecture-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T776/build` and `python tools/axtest.py --compiler build-snap-T776/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 03:01:00 created by T218 (P18 phase planning)
- 2026-11-08 14:22:06 started (attempt 1) T776-impl
- 2026-11-08 14:44:01 accepted by QA -> done
