---
id: T076
title: Self-hosting plan: feature audit, compiler/ layout, differential strategy
phase: P10-selfhost
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T075]
priority: 110
status: todo
attempts: 0
paths: [spec/SPEC-20-selfhost.md, _workspaces/tasks/todo]
timeout_min: 300
spec: [0167, 0150, tasks/0260, tasks/0261, tasks/0371, tasks/0473]
covers: [REQ-DRV-022]
---
# T076 — Self-hosting plan: feature audit, compiler/ layout, differential strategy

## Goal
Plan the port of axiom0 to Axiom (axiomc).

## Scope
- Audit which language/library features the port needs vs implemented; create gap tasks; define compiler/ layout mirroring axiom0 modules; differential plan per module (tokens/AST/HIR/MIR/bytes).

## Acceptance
- [ ] SPEC-20 + gap tasks filed with dependencies (ids from `taskctl.py new-id --phase P9` / `P10`, i.e. T112–T199); every new task file passes `taskctl.py lint`; `taskctl.py validate` and `harness_check.py` pass.
- [ ] **Port split** (ADR-0005 §8): each of T077–T085 is split per C module into sub-tasks of ≤ ~1.5k lines of Axiom (`T077a`, `T077b`, … — kernel, source, diag, lexer, parser + AST, resolver, HIR, types, traits + mono, ownership/init, capability, drop, MIR build, verifier, interpreter + host, optimizer, LIR, ABI, isel + frame, encoder, object model + COFF, PE linker, driver); the original id stays as the group's integration + differential task and depends on its sub-tasks.
- [ ] Every port task names (a) its exact differential artefact (`inspect --emit=<x>` dump, `--json` diagnostics, object/image bytes) and (b) the harness entry that drives the Axiom module; models: opus for the ports of types, traits, ownership, capability, drop, MIR build, verifier, interpreter and optimizer, sonnet elsewhere.
- [ ] Post-self-host tasks T058, T063, T064, T066, T067, T068, T750, T751 are re-pathed to the chosen `compiler/<module>` layout.
- [ ] `spec/selfhost-subset.tsv` re-audited: every feature delivered and consumed; SPEC-20 fixes the self-compile budget of T086 (default: axiom0 → axiomc1 < 2 min, axiomc1 self-compile < 10 min, < 4 GB) and the flags of every stage.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T076-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Verify the self-host std subset defined in SPEC-00 (T003a) is fully implemented before porting starts; file gap tasks in P9 if not.
- ROADMAP R3: after T087 axiom0 is frozen (bug fixes for bootstrapping only); all P11+ work happens in compiler/ + std/. Design compiler/ so every later epic has a natural home.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-06 02:23:58 covers += REQ-DRV-022 (metadata only)
