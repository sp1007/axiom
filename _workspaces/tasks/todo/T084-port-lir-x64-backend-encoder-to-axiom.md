---
id: T084
title: Port LIR + x64 backend + encoder to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T083]
priority: 118
status: todo
attempts: 0
paths: [compiler/backend, tests/selfhost/backend]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-ABI-106, REQ-ABI-107, REQ-ABI-108, REQ-LAY-298, REQ-LIR-030, REQ-TGT-327, REQ-X64-001]
---
# T084 — Port LIR + x64 backend + encoder to Axiom

## Goal
Port LIR + x64 backend + encoder to Axiom, keeping behaviour identical to the C implementation.

## Scope
- Idiomatic canonical Axiom port of the corresponding axiom0 modules; same data model and diagnostics codes.
- Differential test harness comparing outputs with axiom0 over the whole tests/ corpus.

## Acceptance
- [ ] Differential equality over the corpus (documented counts); module tests pass in interp and native.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T084-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Template task: T076 splits it per C module (≤ ~1.5k lines of Axiom per task), names the exact differential artefact and harness entry, and may change these `paths` (ADR-0005 §8). This id stays as the group's integration + differential task.
- Module tests run in both modes: OS and heap access go through std (host intrinsics, ADR-0002); maps iterate in insertion order and hash like axiom0 (ADR-0004 §4), so dumps are byte-identical.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-06 02:23:53 covers += REQ-ABI-106, REQ-ABI-107, REQ-ABI-108 (metadata only)
- 2026-10-06 02:24:21 covers += REQ-LAY-298, REQ-LIR-030 (metadata only)
- 2026-10-06 02:31:21 covers += REQ-TGT-327, REQ-X64-001 (metadata only)
