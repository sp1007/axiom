---
id: T857
title: E20.2 AXPACKAGE dependency resolution, monotonic feature unification, axiom.lock & offline vendoring conformance suite
phase: P20-build-system-package-ecosystem
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T220, T681, T685, T318, T856]
priority: 207
status: todo
attempts: 0
paths: [tests/conformance/p20/e20_2_package_manager_lockfile]
spec: [spec/SPEC-111-package-manager-resolution-lockfiles.md, 0098, tasks/0412, tasks/0446, tasks/0661, tasks/1065]
covers: [REQ-ECO-8736, REQ-PKG-022, REQ-PKG-024, REQ-PKG-025]
---
# T857 — E20.2 AXPACKAGE dependency resolution, monotonic feature unification, axiom.lock & offline vendoring conformance suite

## Goal
Certify E20.2 exit criteria with an end-to-end conformance suite covering `AXPACKAGE` SemVer 2.0 constraint resolution, conflict diagnostics, monotonic feature unification, side-by-side major version isolation, `axiom.lock` reproducibility, and air-gapped vendored builds.

## Scope
- Create conformance tests in `tests/conformance/p20/e20_2_package_manager_lockfile` verifying:
  - SemVer 2.0 diamond dependency resolution, pre-release rules, and human-readable conflict explanation traces (`REQ-PKG-022`, `REQ-PKG-024`, `REQ-ECO-8736`);
  - declaration-order and filesystem-order invariance of resolved dependency graphs and `axiom.lock` bytes;
  - monotonic additive feature unification across `normal`/`dev`/`build` scopes and explicit rejection when a required feature is unavailable (`REQ-PKG-025`);
  - side-by-side major version isolation (`pkg v1` and `pkg v2` in the same workspace) and `--locked`/`--offline`/`--vendor` air-gapped builds;
  - differential equivalence between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p20/e20_2_package_manager_lockfile` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T857-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T857/build` and `python tools/axtest.py --compiler build-snap-T857/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
