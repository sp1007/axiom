---
id: T212
title: Plan phase P12 — Numeric, floating point & SIMD (expand roadmap epics into tasks)
phase: P12-numeric-floating-point-simd
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T087]
priority: 6
status: todo
attempts: 0
paths: [_workspaces/tasks/todo, spec/requirements/CATALOG.md, spec/ROADMAP.md]
spec: [spec/ROADMAP.md, spec/requirements/CATALOG.md]
---
# T212 — Plan phase P12: Numeric, floating point & SIMD

## Goal
Expand the epics of phase P12 listed in `spec/ROADMAP.md` §3 into concrete board tasks following the
standard in ROADMAP §4, so that this phase looks exactly like every other phase and nothing outside
the roadmap is invented.

## Scope
- Read ROADMAP §3 (P12 epics), catalogue rows with `EPIC(E12.*)` (including `REQ-OWNER-007` below), the epics' sources, and the gate reports of the phases this one depends on.

## Complex Mixed-Type Expression Matrix (`REQ-OWNER-007`)
When expanding `E12.1` / `E12.2`, create dedicated spec + implementation + QA stress-test tasks for **complex expressions mixing unsuffixed literals and variables of different numeric types** without suffixes or manual `as` casts:
1. **Architectural rule (preventing ad-hoc backend promotion bugs):**
   - Resolve all unsuffixed literal unification (`IntVar` / `FloatVar`) and variable numeric promotions (`i8/u8 -> i16/u16 -> i32/u32 -> i64/isize -> f32 -> f64`) **exclusively in `typeck` + HIR->MIR lowering**.
   - Emit every implicit promotion as an explicit `MIR_RVALUE_CAST` temporary before the binary/indexing operation so that **MIR, MIR verifier, MIR interpreter, optimizer, LIR, and x86-64 codegen still see 100% homogeneous operand types on every instruction** (never mixing GPR and XMM or narrow/wide widths inside backend isel).
2. **Mandatory QA expression patterns (`tests/run/numeric/`):**
   - **Pattern A (multi-level rational/polynomial mixing `i16`, `u16`, `i32`, `i64`, `usize`, `f32`, `f64` + unsuffixed int/float literals):**
     ```axiom
     let a: f64 = 123.45;
     let w: f32 = 0.25;
     let i: i32 = -7;
     let k: i16 = 3;
     let u: u16 = 12;
     let n: usize = 5;
     let base: i64 = 1000;
     let y: f64 = ((a + i * k - 1) / (2 * n + u - 3)) * (w + 0.5)
                + (base - u * 4 + i) / (a * a / 6.0 - k + 2);
     ```
   - **Pattern B (bitwise & shift sub-trees feeding signed/unsigned & floating-point arithmetic):**
     ```axiom
     let mask: u32 = 0x0FF0;
     let sh: u8 = 4;
     let delta: i8 = -3;
     let step: isize = 9;
     let scale: f64 = 2.5;
     let z: f64 = (((mask >> sh) & 0x3F) + delta * step - 5) * scale / ((1 << sh) + 3);
     ```
   - **Pattern C (mixed-width array indexing, function/intrinsic arguments, and relational comparisons):**
     ```axiom
     let idx: u8 = 2;
     let off: isize = 1;
     let coeff: [4]f32 = [1.25, -0.5, 2.0, 4.5];
     let x: f64 = 10.0;
     let p: f64 = coeff[idx + off] * (x - 3) / (idx * 2 + 1) + coeff[idx - 1] * 4;
     let ok: bool = (p + i * 0.5) > (base / 10 - u + 1.25);
     ```
   - **Pattern D (pure integer multi-width signed/unsigned promotions with negative operands and literals):**
     ```axiom
     let b8: u8 = 200;
     let s8: i8 = -50;
     let u16v: u16 = 3000;
     let s32: i32 = -100000;
     let s64: i64 = 5000000000;
     let total: i64 = (s64 + s32 * 3) - (u16v + b8 * 2 + s8 - 7) / (4 - s8);
     ```
- Create 3–10 tasks per epic with ids in `T450`–`T499`, titles `E12.x <short title>`, owners by area, narrow `paths`, `spec:`, `covers:`, acceptance as tests; a spec task first where `spec/` lacks the area; a QA conformance task per epic exit criterion.
- Implementation happens in `compiler/` (Axiom) and `std/` — axiom0 is frozen (ROADMAP R3).
- Make gate task T312 depend on every new task; convert catalogue `EPIC(E12.*)` statuses to task ids.
- Scope not covered by an epic → ADR + new epic in ROADMAP (and change-log entry), never a stray task.
- Add `depends` on the gate task of every phase ROADMAP lists as a prerequisite of an epic (for example E15.5 tasks depend on T312); take ids with `taskctl.py new-id --phase <P>`.

## Acceptance
- [ ] Every new task file passes `taskctl.py lint`; `taskctl.py validate` OK, `reqcov.py --strict` exits 0 and `harness_check.py` exits 0.
- [ ] Every P12 epic has tasks; gate T312 depends on all of them.
- [ ] ROADMAP change log records the expansion (task count per epic).
- [ ] Report `_workspaces/reports/T212-report.md` listing new tasks under `## Files changed`.

## Out of scope
- Implementing anything; tasks of other phases.

## Notes
- Critical board task (priority < 10): runs alone.

