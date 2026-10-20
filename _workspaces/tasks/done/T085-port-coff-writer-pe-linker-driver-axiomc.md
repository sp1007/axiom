---
id: T085
title: Port COFF writer, PE linker, driver → axiomc (integration + differential)
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T085a, T085b, T085c]
priority: 119
status: done
attempts: 1
paths: [compiler/obj_link_driver, tests/selfhost/obj_link_driver]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-CORE-3181]
started: 2026-10-19 22:54:14
finished: 2026-10-20 09:45:53
---
# T085 — Port COFF writer, PE linker, driver → axiomc (integration + differential)

## Goal
Integrate COFF object writer, PE linker, and driver in Axiom to produce a fully functional `axiomc` binary.

## Scope
- Integrate `compiler/obj`, `compiler/link`, and `compiler/driver`.
- Differential test harness comparing emitted COFF objects and linked executables with `axiom0`.
- Verify `axiomc` can compile programs from source to runnable PE32+ executables.

## Acceptance
- [ ] Differential equality over the corpus (documented counts); module tests pass in interp and native.
- [ ] Sub-tasks T085a, T085b, T085c integrated into a runnable `axiomc` compiler binary.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T085-report.md` with exact `## Files changed`.

## Out of scope
- Full self-hosting bootstrap pipeline (handled in T086 and T087).

## Notes
- Group integration task for T085a, T085b, T085c per ADR-0005 §8 and SPEC-20 §4.9.
- Exact differential artefact: `--emit=obj` object bytes and PE executable image bytes.
- Harness entry: `tests/selfhost/obj_link_driver`.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-19 20:34:35 started (attempt 1) T085-impl
- 2026-10-19 22:54:02 requeue: recovered after session restart (not charged: attempt refunded)
- 2026-10-19 22:54:14 started (attempt 1) T085-impl
- 2026-10-20 09:45:53 accepted by QA -> done
