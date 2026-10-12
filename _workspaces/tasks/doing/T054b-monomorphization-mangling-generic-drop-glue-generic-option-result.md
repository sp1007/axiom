---
id: T054b
title: Monomorphization, mangling, generic drop glue, generic Option/Result
phase: P7-abstraction
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T054, T060]
priority: 74
status: doing
attempts: 0
paths: [bootstrap/axiom0/src, std/core, tests/run, tests/ui/mono]
locks: [bootstrap/axiom0/src/driver/project.c, bootstrap/axiom0/src/diag/codes/TYPE.def, bootstrap/axiom0/src/diag/codes/DROP.def, bootstrap/axiom0/src/driver/pipeline.c, bootstrap/axiom0/src/driver/driver.h, bootstrap/axiom0/src/driver/build_native/build.c, bootstrap/axiom0/src/resolve/resolve.c]
spec: [0083, tasks/0271, tasks/0506, tasks/0354, 0042, 0178]
covers: []
---
# T054b — Monomorphization, mangling, generic drop glue, generic Option/Result

## Goal
Static dispatch for generics: one MIR body per instance, deterministic symbols, and correct destruction of generic values (split from T054; ADR-0004 §5).

## Scope
- Instance collection (worklist from `main`), MIR instantiation, instance deduplication, deterministic symbol mangling (spec'd scheme; uses the kernel hash only through its documented algorithm; module path hook from T060).
- **Drop elaboration per monomorphized instance**: drop glue for `Vec<T>`-like generic types, generic `impl<T> Drop for S<T>`; `needs_drop` information per instance (consumed by T061a's `drop_in_place<T>` / `needs_drop<T>`).
- Option<T> / Result<T, E> become real generic enums in `std/core/option.ax` and `std/core/result.ax`, exported by `std/core/prelude.ax` (prelude mechanism of T060); the built-in non-generic items of T039 are removed (retires that `BOOTSTRAP-SHORTCUT`).

## Acceptance
- [ ] run + ui tests; instance dedup test; mangling deterministic (two runs, byte-identical MIR dump and symbol list).
- [ ] Drop-count test: a generic container struct holding values with destructors drops each exactly once, in order (interp).
- [ ] Every existing run test that uses Option/Result (tests/run/result and later ones) still passes in **both** modes with Option/Result coming from std: instantiated bodies are ordinary MIR bodies in the program's body table with mangled symbol names, so the existing LIR lowering and backend compile them unchanged. Existing tests are not re-marked `native-after`.
- [ ] New generic run tests of this task carry `// native-after: T059` only where they need backend work that T059 owns (closure environments, indirect calls); plain generic functions and types run natively here.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T054b-report.md` with exact `## Files changed`.

## Out of scope
- Trait bounds checking and trait-dispatched calls (T055); dyn (E14.4); const generics (E14.1).
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- If moving Option/Result to std exposes a backend gap for instantiated bodies, report BLOCKED with the repro (the architect adds a backend fix task before this one) — do not keep the built-in items alive in one mode only.
- Depends on T060 for the std root and the prelude module.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
