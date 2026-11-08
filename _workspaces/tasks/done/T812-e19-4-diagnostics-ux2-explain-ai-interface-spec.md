---
id: T812
title: E19.4 Canonical Diagnostics UX 2.0, explain registry, machine-applicable fixes & AI-agent fact protocol specification (SPEC-103)
phase: P19-developer-tooling
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T219, T752, T755, T756, T759]
priority: 202
status: done
attempts: 1
paths: [spec/SPEC-103-diagnostics-ux-ai-interface.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-21-query-engine-semantic-db.md, spec/SPEC-24-artifact-format-module-interfaces.md, 0101, 0129, 0146, tasks/0360, tasks/0374, tasks/0421, tasks/0425, tasks/0444, tasks/0448, tasks/0456, tasks/0693]
covers: [REQ-TOOL-004, REQ-TOOL-180, REQ-TOOL-181, REQ-TOOL-182, REQ-TOOL-185, REQ-TOOL-186, REQ-TOOL-187, REQ-TOOL-190, REQ-TOOL-298]
started: 2026-11-08 15:28:53
finished: 2026-11-08 16:17:47
---
# T812 — E19.4 Canonical Diagnostics UX 2.0, explain registry, machine-applicable fixes & AI-agent fact protocol specification (SPEC-103)

## Goal
Consolidate the canonical specification for Axiom's Diagnostics UX 2.0, `axiomc explain`, machine-applicable fix-its, layout/container/effect inspection, and the AI-agent semantic fact protocol into `spec/SPEC-103-diagnostics-ux-ai-interface.md` (`AXS-DIAG-*` and `AXS-AI-*` rule IDs).

## Scope
- Write `spec/SPEC-103-diagnostics-ux-ai-interface.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-DIAG-NNN` / `AXS-AI-NNN` rules.
- Specify Diagnostics UX 2.0 (`0146`, `tasks/0360`, `tasks/0421`, `REQ-TOOL-298`): multi-span causal ownership/capability provenance chains, root-cause error tainting to suppress cascading artificial failures, deterministic diagnostic fingerprints, confidence-graded machine-applicable fix suggestions (`MachineApplicable`, `HasPlaceholders`, `MaybeIncorrect`, `Unspecified`), and `axiomc explain <CODE>` linked to canonical spec rule IDs.
- Specify the versioned machine-readable AI-agent & developer query protocol (`0101 §25-32`, `0146 §38-48, §57-63`, `REQ-TOOL-180`, `REQ-TOOL-185`): exporting structured semantic fact graphs (ownership/capability graphs, trait resolution traces, command-line type layout inspection via `axiomc inspect layout` for `REQ-TOOL-004`, container semantic properties in `.axmeta` for `REQ-TOOL-181`, and `std` API allocation/blocking/synchronization/effect metadata for `REQ-TOOL-190`).
- Specify the AI verification & zero-runtime-overhead invariants: AI-proposed patches and AI-generated code undergo full compiler verification without safety bypass (`REQ-TOOL-180`, `REQ-TOOL-186`), and `.axmeta`, `.axdb`, and debug metadata remain separate from production executables (`REQ-TOOL-182`, `REQ-TOOL-187`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-103-diagnostics-ux-ai-interface.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-DIAG-NNN` and `AXS-AI-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T812-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of Diagnostics UX 2.0, `axiomc explain`, and the AI fact exporter (`T813`–`T814`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P19 (`P19-developer-tooling`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 09:50:00 created by T219 (P19 phase planning)
- 2026-11-08 15:28:53 started (attempt 1) T812-impl
- 2026-11-08 16:17:47 accepted by QA -> done
