---
id: T863
title: E20.4 Hermetic build sandbox, filesystem/env/network/clock isolation, --remap-path-prefix & bit-for-bit reproducibility verifier
phase: P20-build-system-package-ecosystem
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T220, T681, T685, T318, T852, T862]
priority: 213
status: todo
attempts: 0
paths: [compiler/build/sandbox, compiler/build/repro, tests/run/build_hermetic]
spec: [spec/SPEC-113-hermetic-builds-supply-chain-trust.md, tasks/0590, tasks/0449, tasks/0772, tasks/0661]
covers: [REQ-PKG-022, REQ-PKG-024]
---
# T863 — E20.4 Hermetic build sandbox, filesystem/env/network/clock isolation, --remap-path-prefix & bit-for-bit reproducibility verifier

## Goal
Implement the hermetic build sandbox enforcing filesystem, environment, network, and clock/entropy isolation, workspace path prefix remapping (`--remap-path-prefix`), and the bit-for-bit reproducibility verifier per `spec/SPEC-113-hermetic-builds-supply-chain-trust.md`.

## Scope
- Implement `compiler/build/sandbox` enforcing hermetic compilation rules (`tasks/0590 §5-19`): forbidding reads/writes outside declared package roots and build output directories, blocking network and unauthorized subprocess spawning during compilation/comptime, scrubbing undeclared host environment variables, and fixing virtual timestamps/seeds.
- Implement `compiler/build/repro` normalizing all embedded source/debug/panic paths via `--remap-path-prefix` (defaulting to `@pkg/<name>@<version>/...` in hermetic workspace builds) and providing double-build differential verification (`axiomc build --verify-repro`) across distinct workspace directories and worker counts (`REQ-PKG-022`, `REQ-PKG-024`, `tasks/0772 §550.11-18`).
- Add run and negative sandbox violation tests in `tests/run/build_hermetic`.

## Acceptance
- [ ] Run tests in `tests/run/build_hermetic` verify sandbox rejection of path escapes/undeclared env/network access, path prefix normalization across different checkout paths, and byte-identical artifact emission under `--verify-repro` in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T863-report.md` with exact `## Files changed`.

## Out of scope
- Ed25519 package signing, provenance attestation JSON, and dependency capability-escalation CLI (`T864`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T863/build` and `python tools/axtest.py --compiler build-snap-T863/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
