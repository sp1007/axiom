---
id: T570
title: E14.5 — Finalize SPEC-03 AXS-SEM-047 index auto-deref through view/mut_view (retire bootstrap v0.1 note)
phase: P14-comptime-2-0-reflection-genera
owner: axiom-architect
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T214]
priority: 191
status: done
attempts: 1
paths: [spec/SPEC-03-core-semantics.md]
locks: [spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-03-core-semantics.md, spec/SPEC-12-drop.md, spec/decisions/ADR-0036-assignment-drop-raw-store-cap-followups.md]
covers: [REQ-CORE-3053, REQ-CORE-3054, REQ-CORE-3055]
started: 2026-11-03 07:37:44
finished: 2026-11-03 07:49:17
---
# T570 — E14.5 — Finalize SPEC-03 AXS-SEM-047 index auto-deref through view/mut_view (retire bootstrap v0.1 note)

## Goal
Update `spec/SPEC-03-core-semantics.md` `AXS-SEM-047` to mark one-level-at-a-time index auto-deref through `view<[N]T>` and `mut_view<[N]T>` as active in `axiomc`, remove the temporary v0.1 deferral note, and add normative test table rows in `SPEC-03` §10.

## Scope
- Edit `spec/SPEC-03-core-semantics.md` (`AXS-SEM-047`): remove the temporary bootstrap v0.1 deferral note (`"Until then AX_TYPE_CANNOT_INDEX with the hint write (*a)[i] is conforming for axiom0 and axiomc v0.1"`) and record delivery by `E14.5` (`T571`) in `axiomc` (while `bootstrap/axiom0` stays frozen at `axiom0-frozen` per ROADMAP R3).
- Confirm the exact interaction between `AXS-SEM-047` (`a[i]` -> `(*a)[i]` on `view<[N]T>`/`mut_view<[N]T>`), `AXS-SEM-042` (left-to-right base then index evaluation + bounds check), `AXS-SEM-043` / `SPEC-12 AXS-DROP-007` (assigning `a[i] = v` through `mut_view<[N]T>` drops the old element value), and the prohibition on auto-dereferencing raw pointers (`p[i]` on `p: *const [N]T` or `*mut [N]T` remains `AX_TYPE_CANNOT_INDEX`; `(*p)[i]` inside `unsafe` stays explicit).
- Add normative test rows in `spec/SPEC-03-core-semantics.md` §10 covering read through `view<[N]T>`, write through `mut_view<[N]T>`, rejected write through `view<[N]T]`, and rejected `p[i]` on raw pointer.

## Acceptance
- [ ] `spec/SPEC-03-core-semantics.md` `AXS-SEM-047` has its temporary v0.1 note removed and normative test cases added in §10.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T570-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation in `compiler/sema` and `compiler/mir` (`T571`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`), epic `E14.5` (added by `ADR-0036` §4).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:24:30 created by T214 (P14 phase planning)
- 2026-11-03 07:37:44 started (attempt 1) 
- 2026-11-03 07:49:17 accepted by QA -> done
