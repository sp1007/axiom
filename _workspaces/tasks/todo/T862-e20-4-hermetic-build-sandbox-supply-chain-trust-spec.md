---
id: T862
title: E20.4 Canonical build sandbox, hermetic/reproducible compilation, Ed25519 signing & supply-chain trust specification (SPEC-113)
phase: P20-build-system-package-ecosystem
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T220, T316, T318]
priority: 212
status: todo
attempts: 0
paths: [spec/SPEC-113-hermetic-builds-supply-chain-trust.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-53-safety-profiles-capability-security.md, tasks/0590, tasks/0449, tasks/0772, tasks/0661, tasks/1065]
covers: [REQ-PKG-022, REQ-PKG-024]
---
# T862 — E20.4 Canonical build sandbox, hermetic/reproducible compilation, Ed25519 signing & supply-chain trust specification (SPEC-113)

## Goal
Consolidate the canonical specification for Axiom's hermetic build sandbox, bit-for-bit cross-machine reproducibility contract, dependency capability-escalation policy, Ed25519 package/toolchain signing, build provenance attestation, and Diverse Double-Compilation (DDC) bootstrap trust verification into `spec/SPEC-113-hermetic-builds-supply-chain-trust.md` (`AXS-HERM-*` rule IDs).

## Scope
- Write `spec/SPEC-113-hermetic-builds-supply-chain-trust.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-HERM-NNN` rules.
- Specify the supply-chain trust model (`tasks/0449 §1-21`, `tasks/0590 §1-16`, `tasks/0772 §550.1-24`): `Safe ≠ Trusted`, package capability declarations (`unsafe`, `ffi`, `net`, `fs`, `process`, `asm`), transitive dependency trust policies, and explicit capability-escalation rejection when a dependency requests capabilities not granted by the root workspace policy (`REQ-PKG-024`).
- Specify the hermetic build sandbox (`tasks/0590 §5-19`, `REQ-PKG-022`): read-only source tree, output confined to the package's designated build artifact directory, zero network access during compilation/comptime, sanitized environment allowlist, fixed virtual timestamp/seed, canonical path prefix remapping (`--remap-path-prefix`), and deterministic symbol/section/archive ordering so identical inputs + `axiom.lock` yield bit-for-bit identical binaries across different checkout directories and machines.
- Specify Ed25519 package and toolchain signing (`tasks/0590 §20-24`, `tasks/0772 §550.8-18`), JSON provenance attestation manifests (builder identity, `CompilerFingerprint`, `SdkFingerprint`, `axiom.lock` digest, output artifact SHA-256 digests), and `axiomc trust|audit|verify-repro` verification commands.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-113-hermetic-builds-supply-chain-trust.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-HERM-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T862-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of the hermetic build sandbox, reproducibility checker, and trust/signing CLI (`T863`–`T864`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
