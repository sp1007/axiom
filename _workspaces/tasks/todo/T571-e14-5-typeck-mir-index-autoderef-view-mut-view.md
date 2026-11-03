---
id: T571
title: E14.5 — Index auto-deref through view<[N]T> and mut_view<[N]T> in typeck and MIR builder
phase: P14-comptime-2-0-reflection-genera
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T570]
priority: 192
status: todo
attempts: 0
paths: [compiler/types, compiler/mir, tests/run/index_autoderef, tests/ui/index_autoderef, tests/selfhost/typeck, tests/selfhost/mir]
spec: [spec/SPEC-03-core-semantics.md, spec/SPEC-12-drop.md, spec/decisions/ADR-0036-assignment-drop-raw-store-cap-followups.md]
covers: [REQ-CORE-3056, REQ-CORE-3057, REQ-CORE-3058]
---
# T571 — E14.5 — Index auto-deref through view<[N]T> and mut_view<[N]T> in typeck and MIR builder

## Goal
Implement index auto-deref through `view<[N]T>` and `mut_view<[N]T>` (`SPEC-03 AXS-SEM-047`, `ADR-0036 §4`) in `axiomc`'s type checker (`compiler/types`) and MIR builder (`compiler/mir`), with positive run tests and negative UI tests.

## Scope
- In `compiler/types` (`typeck.ax`), when indexing `base[i]` where `base` has type `view<X>` or `mut_view<X>` and `X` resolves (after one or more view levels) to `[N]T` (or slice `[T]`), implicitly dereference `base` one level at a time just like field access (`a[i]` -> `(*a)[i]`).
- Enforce mutability rules: reading `a[i]` is valid on both `view<[N]T>` and `mut_view<[N]T>`; assigning `a[i] = v`, compound-assigning `a[i] += v`, or taking `mut_view(a[i])` requires every traversed view level to be `mut_view` (rejecting writes through `view<[N]T>` with the immutable-place diagnostic).
- Never auto-dereference raw pointers for indexing: `p[i]` on `p: *const [N]T` or `p: *mut [N]T` (or `*const T` / `*mut T`) remains a compile error `AX_TYPE_CANNOT_INDEX` with hint `write (*p)[i]` inside `unsafe`.
- In `compiler/mir` (`builder.ax`), emit the implicit `PlaceElem.Deref` projections before `PlaceElem.Index` on the place projection chain so bounds checks (`AXS-SEM-042`) and old-element drop on assignment (`AXS-SEM-043` / `SPEC-12 AXS-DROP-007`) work identically to `(*a)[i]`.

## Acceptance
- [ ] Differential (`--interp` and native) tests in `tests/run/index_autoderef` verify `a[i]` reads on `view<[N]T>` and `mut_view<[N]T>`, `a[i] = v` and `a[i] += v` writes on `mut_view<[N]T>`, old-value `Drop` when assigning `a[i] = new_s` on `a: mut_view<[N]S>` where `S: Drop`, and bounds-check panic on out-of-range `i`.
- [ ] Negative UI tests in `tests/ui/index_autoderef` verify that writing `a[i] = v` through `a: view<[N]T>` is rejected and that `p[i]` on a raw pointer `p: *mut [N]T` or `p: *const [N]T` is rejected with `AX_TYPE_CANNOT_INDEX`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`) with `0 WEAK-NATIVE`.
- [ ] Report `_workspaces/reports/T571-report.md` with exact `## Files changed`.

## Out of scope
- Changing `bootstrap/axiom0/` (frozen at `axiom0-frozen` per ROADMAP R3; `compiler/` continues to use `(*a)[i]` if needed so Stage 1 builds with `axiom0`).
- Editing `docs/`.

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`), epic `E14.5` (`ADR-0036` §4, `T141` QA N3).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T571/build` and `python tools/axtest.py --compiler build-snap-T571/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:24:30 created by T214 (P14 phase planning)
