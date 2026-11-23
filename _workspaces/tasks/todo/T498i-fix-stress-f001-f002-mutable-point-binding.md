---
id: T498i
title: Fix — fullrun-4 R1 conformance/stress/f001.ax and f002.ax declare immutable `let p` before taking `mut_view(p.x)`
phase: P12-numeric-floating-point-simd
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: []
priority: 0
status: todo
attempts: 0
paths: [tests/conformance/stress/f001.ax, tests/conformance/stress/f002.ax]
locks: []
spec: [spec/SPEC-02-grammar.md, spec/SPEC-03-core-semantics.md, spec/SPEC-11-capability.md]
covers: [REQ-TST-072]
---
# T498i — Update `conformance/stress/f001.ax` and `f002.ax` to declare `let mut p` (`fullrun-4` R1)

## Goal
Resolve `fullrun-4` regression R1 (`conformance/stress/f001.ax` in `interp`/`native`/`native-O1` and `conformance/stress/f002.ax` in `ui`) exposed after `T498f` (`2d69ea8d`). Under `SPEC-02 AXS-GRM-041` ("Bindings are immutable unless the pattern says `mut`"), `SPEC-11 AXS-CAP-002` (`mut_view<T>` grants exclusive read-write access), and `SPEC-03 AXS-SEM-047`, taking `mut_view(p.x)` on an immutable `let p` is rightly rejected with `AX_TYPE_ASSIGN_IMMUTABLE`. Both early stress tests intended to test capability disjointness (`f001.ax`) and capability conflict (`f002.ax`) on a mutable struct owner, not immutable-binding mutation.

Repro before fix (in an isolated snapshot):
```
python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --no-cache -v conformance/stress/f001.ax conformance/stress/f002.ax
```

## Scope
- Update `tests/conformance/stress/f001.ax`:
  - Change `let p = Point { x: 1, y: 2 };` to `let mut p = Point { x: 1, y: 2 };` so disjoint `mut_view(p.x)` and `mut_view(p.y)` capabilities are checked on a mutable owner.
  - Perform real mutations through both `mut_view<i32>` capabilities inside `mutate` (e.g. `*b = *b + 10;`), print the resulting fields (`print_int(p.x as i64); print(" "); print_int(p.y as i64); print("\n");`), add `// stdout: 11 12\n`, and return `if p.x == 11 && p.y == 12 { 0 } else { 1 }` so the modified run test executes in `interp`, `native`, and `native-O1` with `WEAK-NATIVE 0` (mandatory under `taskgate.py`).
- Update `tests/conformance/stress/f002.ax`:
  - Change `let p = Point { x: 1, y: 2 };` to `let mut p = Point { x: 1, y: 2 };` so `let a = mut_view(p);` followed by `let b = mut_view(p.x);` reaches the capability checker and emits `AX_CAP_CONFLICT_MUT` on the annotated line.

## Acceptance
- [ ] `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache -j 2 -v conformance/stress/f001.ax conformance/stress/f002.ax` passes all 4 mode results (`f001.ax` in `interp`, `native`, `native-O1`; `f002.ax` in `ui`) with `WEAK-NATIVE 0`.
- [ ] Mutation spot-proof inside `build-snap-T498i/` confirms `f001.ax` fails all 3 modes when expected stdout is perturbed, then restored byte-identical.
- [ ] `python tools/taskgate.py --task T498i --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2` exits 0 (`BASELINE OK`, `WEAK-NATIVE: 0 in the task's own/changed tests`, `archcheck` clean).
- [ ] Report `_workspaces/reports/T498i-report.md` written with exact `## Files changed` and `STATUS: COMPLETE round=0`.

## Out of scope
- Any changes to `compiler/`, `spec/`, `bootstrap/axiom0/`, or `docs/`.

## Log
- 2026-11-23 created by axiom-architect (fullrun-4 triage R1; culprit T498f `2d69ea8d`)
