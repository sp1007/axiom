---
id: T490
title: Baseline fix — mir/intrinsics rotate_u8 + wrapping_ops golden type ids, selfhost/hir qa_hir_desugar_and_drop exit 43
phase: P12-numeric-floating-point-simd
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: []
priority: 13
status: todo
attempts: 0
paths: [tests/mir/intrinsics, tests/selfhost/hir/qa_hir_desugar_and_drop.ax.in, _workspaces/baseline-failures.txt]
locks: []
spec: [spec/SPEC-20-selfhost.md]
covers: [REQ-TST-072]
started: 2026-11-19 03:55:12
---
# T490 — Baseline fix: MIR intrinsic goldens and qa_hir_desugar_and_drop

## Why
Pre-existing failures found by the T481a and T485 gates (identical with the HEAD compiler), admitted to
`_workspaces/baseline-failures.txt` on 2026-11-18 with this task as their fix task:
- `mir/intrinsics/rotate_u8.ax`, `mir/intrinsics/wrapping_ops.ax`: golden MIR differs (`type#13` vs expected
  `type#11`; `type#8` vs `type#11`; byte offsets 74/94). Goldens date from T134 (AX0-FIX-01).
- `selfhost/hir/qa_hir_desugar_and_drop.ax`: exit 43 in interp, native and native-O1.

## Scope
- MIR goldens: decide whether the type-id change is legitimate (type table order changed by a later accepted task —
  find which commit) or a regression. Legitimate → regenerate the goldens and record the commit that changed them;
  regression → fix the cause (if it is outside this task's paths, report BLOCKED with the evidence).
  Do not regenerate blindly: show the diff and the reason in the report.
- qa_hir_desugar_and_drop: find which assertion yields 43, root-cause it (test expectation stale vs compiler bug), fix
  it in the right place (template `*.ax.in` / generator, or report BLOCKED with a precise culprit if it is compiler
  code outside the paths).
- Remove the fixed ids from `_workspaces/baseline-failures.txt` in the same commit.

## Acceptance
- [ ] The three ids pass in every mode; baseline file updated.
- [ ] Normal gate. Report `_workspaces/reports/T490-report.md` with exact `## Files changed`.

## Log
- 2026-11-18 created by orchestrator (T485 gate follow-up F-4, T481a gate observations)
- 2026-11-19 03:55:12 started (attempt 1) T490-impl
- 2026-11-19 04:29:27 requeue: restart (not charged: attempt refunded)
