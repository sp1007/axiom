---
id: T003
title: Stage-0 bootstrap subset, milestone manifests, core execution semantics
phase: P0-foundation
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T001]
priority: 11
status: done
attempts: 1
paths: [spec/SPEC-00-bootstrap.md, spec/SPEC-03-core-semantics.md]
spec: [0263, tasks/0262, tasks/0494, tasks/0260, 0152, 0032, 0041, 0068, tasks/0327, 0010]
started: 2026-10-04 07:44:10
finished: 2026-10-05 11:52:37
---
# T003 — Stage-0 bootstrap subset, milestone manifests, core execution semantics

## Goal
Define exactly which language subset each milestone supports and freeze the core execution semantics the interpreter and backend must agree on.

## Scope
- SPEC-00-bootstrap.md: milestone ladder mapped to board phases (P2..P10) with features allowed/forbidden per milestone; first programs (exit 42, negative type test, MIR test, ABI test, struct test) from 0263 §32-37 in canonical syntax.
- SPEC-03-core-semantics.md: `main` signatures and exit-code mapping; integer types and literal defaulting; overflow behaviour (decide: trap/panic in all builds vs wrapping ops — cite docs); division by zero and INT_MIN/-1; shifts out of range; evaluation order (left-to-right, args, assignment); short-circuit; panic = abort in bootstrap and its exit code; bool representation; unit/never.
- SPEC-00: a **machine-readable milestone manifest** — per milestone a fenced block listing its must-pass test paths, parsed by `tools/gatecheck.py` (T022) (0264 §19-20).
- SPEC-00: the table BOOT-00..38 (0263 §51) → board task(s), or "deferred to <epic> by <R-rule>" (start from the table in `_workspaces/audit/2026-09-30/A2-ladder.md`): BOOT-26 comptime (const items only in T061, rest E14.1), BOOT-28 register allocation (E15.8), BOOT-29 full linker (E18.6), BOOT-30 AArch64 (P16), Linux-first of 0263 §4 inverted by 0181 and ROADMAP R6.
- SPEC-00: name map between the ladders: V0 (tasks/0262 §55) = T011/T013; V1 = VS0 = T022; V2 = VS1 (0263 §51 VS#1) = T029; P5 language-core gate = T044; V3 = T086; V4 = VS2 (0263 §51 BOOT-36..38) = T087.
- SPEC-03: non-trapping wrapping and bit operations (`wrapping_add/sub/mul/neg`, `rotate_left/right`, `leading_zeros`, `trailing_zeros`, `count_ones`, every integer width; ADR-0004 §1); the complete cast table incl. `u8 as char`, checked `u32 as char` (panics on a non-scalar value, ADR-0006 §2), `char as u32`, `enum as uN` for fieldless enums; the interpreter step-limit default and its diagnostic.

## Acceptance
- [ ] Both files exist with rule IDs; every semantic decision cites sources or an ADR.
- [ ] Each milestone lists its must-pass test programs.
- [ ] BOOT-00..38 table complete (every step has a task or a deferral with its R-rule); ladder name map present; milestone manifest blocks parse (format documented for T022).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T003-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- ADRs: reserve the number with `python .claude/skills/axiom-tasks/scripts/taskctl.py adr-next <slug>` (never pick one by listing the directory) and list the ADR file in the report.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-04 07:44:10 started (attempt 1) T003-impl
- 2026-10-05 11:52:37 accepted by QA -> done
