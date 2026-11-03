---
id: T320
title: Phase P20 gate — Build system & package ecosystem
phase: P20-build-system-package-ecosystem
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T220, T316, T318, T850, T851, T852, T853, T854, T855, T856, T857, T858, T859, T860, T861, T862, T863, T864, T865, T866, T867, T868, T869, T870, T871, T872, T873, T874, T875, T876, T877]
priority: 320
status: todo
attempts: 0
paths: [tests/conformance/p20, _workspaces/reports/phase-P20-review.md]
spec: [spec/ROADMAP.md, spec/SPEC-110-build-graph-driver.md, spec/SPEC-111-package-manager-resolution-lockfiles.md, spec/SPEC-112-package-registry-distribution.md, spec/SPEC-113-hermetic-builds-supply-chain-trust.md, spec/SPEC-114-abi-stability-versioning-binary-compat.md, spec/SPEC-115-dynamic-components-plugins-hot-reload.md, spec/SPEC-116-sdk-sysroot-toolchain-distribution.md]
covers: [REQ-ECO-8734, REQ-ECO-8736, REQ-PKG-022]
---
# T320 — Phase P20 gate: Build system & package ecosystem

## Goal
Certify that phase P20 meets the exit criteria of every epic (`E20.1`–`E20.7`) in `spec/ROADMAP.md` §3 and that all
requirements mapped to the phase are implemented.

## Scope
- Run the full suite on all targets supported at this point; run each epic's exit-criterion checks (`tests/conformance/p20/e20_1_build_graph_driver` through `tests/conformance/p20/e20_6_sdk_toolchain_workspace`, including `e20_7_dynamic_components_hot_reload` and the two-machine lockfile reproducible multi-package workspace build).
- `reqcov.py --phase P20-build-system-package-ecosystem`: every requirement implemented or explicitly re-mapped (with note).
- Collect epic conformance results into `tests/conformance/p20` (index + missing cases added).
- Ask axiom-architect (via report Follow-ups) for the phase review items: spec drift, shortcuts to retire.

## Acceptance
- [ ] Every epic exit criterion (`E20.1`–`E20.7`, including multi-package workspace building reproducibly from `axiom.lock` across two isolated machine environments) demonstrated with commands and results in the QA report.
- [ ] Full suite green (gate rule: PASS or BLOCKED; only `xfail` entries for spec gaps with an ADR may remain); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T320-report.md` with exact `## Files changed`.

## Out of scope
- New features; fixes go to new tasks created by the architect.

## Notes
- Depends on the planning task T220, the P16 gate T316, the P18 gate T318, and every P20 task T850–T877.

## Log
- 2026-10-06 02:23:58 covers += REQ-ECO-8734, REQ-ECO-8736 (metadata only)
- 2026-10-06 02:24:26 covers += REQ-PKG-022 (metadata only)
- 2026-11-03 10:12:00 updated by T220 (wired T316, T318, and all 28 P20 tasks T850–T877 into depends and SPEC-110..SPEC-116 into spec)
