---
id: T859
title: E20.3 Deterministic .axpkg archive packer/unpacker, Merkle content verifier & sparse/local registry repository client
phase: P20-build-system-package-ecosystem
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T220, T681, T685, T318, T856, T858]
priority: 209
status: todo
attempts: 0
paths: [std/pkg/archive, std/pkg/registry, tests/run/pkg_registry]
spec: [spec/SPEC-112-package-registry-distribution.md, tasks/0412, tasks/0665, tasks/0858, tasks/1065]
covers: [REQ-ECO-8736, REQ-PKG-024]
---
# T859 — E20.3 Deterministic .axpkg archive packer/unpacker, Merkle content verifier & sparse/local registry repository client

## Goal
Implement the deterministic `.axpkg` archive packer/unpacker, SHA-256 Merkle content verifier, and sparse/local package registry repository client per `spec/SPEC-112-package-registry-distribution.md`.

## Scope
- Implement `std/pkg/archive` packing and unpacking deterministic `.axpkg` archives with lexicographically sorted entries, normalized paths (rejecting `..` and symlink escapes), zeroed timestamps, embedded `axiom.toml` + `.axmeta` headers, and SHA-256 Merkle tree digest verification (`tasks/0412 §9-10`, `tasks/0858 §15-17`).
- Implement `std/pkg/registry` supporting sparse JSON/line-delimited index queries, immutable version publication checks, local filesystem/directory repositories, offline-first cache lookups, and transactional package installation/rollback (`tasks/0665 §5-12`, `tasks/0858 §6-14, 25-40`, `REQ-ECO-8736`, `REQ-PKG-024`).
- Add run tests in `tests/run/pkg_registry`.

## Acceptance
- [ ] Run tests in `tests/run/pkg_registry` verify bit-for-byte deterministic `.axpkg` packing independent of host filesystem order/timestamps, path-traversal rejection, Merkle digest verification, sparse index lookup, and transactional rollback in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T859-report.md` with exact `## Files changed`.

## Out of scope
- Precompiled `.axmeta` binary package consumption in the compiler driver and `axiomc pkg publish|fetch|mirror` CLI (`T860`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T859/build` and `python tools/axtest.py --compiler build-snap-T859/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
