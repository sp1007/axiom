---
id: T653
title: E16.1 — Canonical declarative TargetDesc, ISA tables & backend conformance specification (SPEC-81)
phase: P16-targets-platforms
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T216, T313, T650]
priority: 96
status: todo
attempts: 0
paths: [spec/SPEC-81-target-desc-isa-conformance.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-04-core-extensibility.md, 0162, 0163, tasks/0472, tasks/0518, tasks/0520, tasks/0521, tasks/0524, tasks/0784]
covers: [REQ-TGT-004, REQ-TGT-005, REQ-TGT-006, REQ-TGT-007, REQ-TGT-008, REQ-TGT-009, REQ-TGT-010, REQ-TGT-011, REQ-TGT-285, REQ-TGT-286]
---
# T653 — E16.1 — Canonical declarative TargetDesc, ISA tables & backend conformance specification (SPEC-81)

## Goal
Consolidate the canonical specification for Axiom's declarative target description (`TargetDesc` / `TargetSpec`), ISA instruction and register tables, legalizer contract, and target-independent backend conformance formalization into `spec/SPEC-81-target-desc-isa-conformance.md` (`AXS-TGTD-*` rule IDs).

## Scope
- Write `spec/SPEC-81-target-desc-isa-conformance.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-TGTD-NNN` rules.
- Specify the declarative `TargetDesc` schema (`0163 §1–7`, `tasks/0784 §562.2–16`): canonical `TargetId` and `TargetFingerprint`, architecture/OS/environment/ABI identity, pointer width, endianness, natural and stack alignment, `ObjectFormat`, `ArchiveFormat`, `ImageFormat`, and `TargetFeatureSet` hierarchy (`AVX2`, `AVX-512`, `NEON`, `SVE`, `RVV`, `RVC`, `LSE`, WASM features).
- Specify the declarative `RegisterFile` model (`tasks/0518`, `tasks/0784 §562.11–16`): physical registers, `RegUnit` overlap bitmasks, explicit subregister/superregister aliasing (`RAX`/`EAX`/`AX`/`AL`, `X0`/`W0`, `Q0`/`D0`/`S0`), reserved architectural registers (`RSP`, `SP`, `XZR`, `X18`, `x0`, `gp`, `tp`), register classes, and caller/callee-saved sets.
- Specify the declarative `IsaTable` and `Legalizer` contract (`tasks/0518 §46, §151`, `tasks/0524 §1–19`): pattern-based instruction descriptors, operand constraints, implicit register uses/defs, condition-code modeling (supporting both flags-based ISAs and flagless ISAs), legalizer expansion rules preserving overflow/atomic/volatile/trap-vs-panic semantics (`AMACHINE-20..120`, `ABACKEND-61..100`), and pre-encoding Machine IR verification.
- Specify the backend conformance contract: Axiom LIR is the semantic portability boundary (`ABACKEND-99..100`); assembly golden files are implementation tests rather than semantic authority (`ABACKEND-90`); all backends pass common differential/reference conformance suites (`ABACKEND-91..93`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-81-target-desc-isa-conformance.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-TGTD-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T653-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation of `TargetDesc` tables, `IsaTable`, or Machine IR verifier (`T654`, `T655`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 08:36:00 created by T216 (P16 phase planning)
