---
id: T767
title: E18.4 — Artifact format, module interface (.axmi) & LTO section round-trip conformance suite
phase: P18-compiler-architecture-2-0
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T766]
priority: 717
status: done
attempts: 1
paths: [tests/conformance/p18/e18_4_artifacts]
spec: [spec/SPEC-24-artifact-format-module-interfaces.md, tasks/0739, tasks/0787, tasks/0803]
covers: [REQ-LNK-614, REQ-LNK-615, REQ-LNK-616, REQ-LNK-617, REQ-LNK-618, REQ-LNK-619, REQ-LNK-620, REQ-LNK-621, REQ-LNK-622, REQ-LNK-623, REQ-LNK-624, REQ-LNK-625, REQ-LNK-626, REQ-LNK-627, REQ-LNK-628, REQ-LNK-629, REQ-LNK-630, REQ-LNK-631, REQ-LNK-632, REQ-LNK-633, REQ-LNK-3744, REQ-LNK-3745, REQ-LNK-3746, REQ-LNK-3747, REQ-LNK-3748, REQ-LNK-3749, REQ-LNK-3750, REQ-LNK-3751, REQ-LNK-3752, REQ-LNK-3753, REQ-LNK-3754, REQ-LNK-3755, REQ-LNK-3756, REQ-LNK-3757, REQ-LNK-3758, REQ-LNK-3759, REQ-LNK-3760, REQ-LNK-3761, REQ-LNK-3762, REQ-LNK-3763, REQ-LNK-3764, REQ-LNK-3765, REQ-LNK-3766, REQ-LNK-3767, REQ-LNK-3768, REQ-LNK-3769, REQ-LNK-3770, REQ-LNK-3771, REQ-LNK-3772, REQ-LNK-3773, REQ-LNK-3774, REQ-LNK-3775, REQ-LNK-3776, REQ-LNK-3777, REQ-LNK-3778, REQ-LNK-3779, REQ-LNK-3780, REQ-LNK-3781, REQ-LNK-3782, REQ-LNK-3783, REQ-LNK-3784]
started: 2026-11-08 04:53:42
finished: 2026-11-08 05:35:42
---
# T767 — E18.4 — Artifact format, module interface (.axmi) & LTO section round-trip conformance suite

## Goal
Certify E18.4 exit criteria with an end-to-end conformance suite covering `.axmi` module interface files, embedded `.axmeta`/`.axlto` object sections, schema/checksum verification, and separate-compilation consumption without upstream source files.

## Scope
- Create conformance tests in `tests/conformance/p18/e18_4_artifacts` verifying:
  - multi-module compilation using `.axmi` and embedded `.axmeta` sections across generics, traits, capabilities, and `const` items;
  - byte-identical `.axmi` and `.obj` emission across repeated runs;
  - negative diagnostic tests for version mismatch, target mismatch, and corrupted `.axmi`/`.axmeta` payloads;
  - differential equivalence between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p18/e18_4_artifacts` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T767-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P18 (`P18-compiler-architecture-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T767/build` and `python tools/axtest.py --compiler build-snap-T767/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:58:55 created by T218 (P18 phase planning)
- 2026-11-08 04:53:42 started (attempt 1) T767-impl
- 2026-11-08 05:35:42 accepted by QA -> done
