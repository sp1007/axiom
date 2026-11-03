---
id: T463
title: E12.3 — Canonical portable SIMD, mask semantics & data-oriented tensor/matrix view specification (SPEC-42)
phase: P12-numeric-floating-point-simd
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T456]
priority: 153
status: doing
attempts: 1
paths: [spec/SPEC-42-simd.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-04-core-extensibility.md, 0095, tasks/0337, tasks/0341, tasks/0344, tasks/0347, tasks/0426, tasks/0427, tasks/0472]
covers: [REQ-SIMD-001, REQ-SIMD-002, REQ-SIMD-003, REQ-SIMD-004, REQ-SIMD-005, REQ-SIMD-006, REQ-SIMD-007, REQ-SIMD-008, REQ-SIMD-086, REQ-SIMD-087, REQ-SIMD-088, REQ-SIMD-089, REQ-SIMD-090, REQ-SIMD-091, REQ-SIMD-092, REQ-SIMD-096, REQ-SIMD-097, REQ-SIMD-166, REQ-SIMD-167, REQ-SIMD-168, REQ-SIMD-171, REQ-SIMD-333]
started: 2026-11-03 09:00:27
agent: T463-impl
---
# T463 — E12.3 — Canonical portable SIMD, mask semantics & data-oriented tensor/matrix view specification (SPEC-42)

## Goal
Consolidate the portable SIMD vector model (`Vector<T, N>`, `Mask<N>`), lane operations, reductions, masked memory/gather/scatter safety, and data-oriented `TensorView`/`MatrixView` capability abstractions into canonical `spec/SPEC-42-simd.md` (`AXS-SIMD-*`).

## Scope
- Write `spec/SPEC-42-simd.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-SIMD-NNN` rules.
- Define `Vector<T, N>` and `Mask<N>` (`SPEC-04 AXS-EXT-020`): supported scalar element types `T` (`i8..i64`, `u8..u64`, `isize`, `usize`, `f32`, `f64`), semantic lane counts `N` (`2, 4, 8, 16, 32, 64`), value semantics (`Copy`, distinct from `[N]T`), and target-independent semantics (`ANUM-21..27`, `ASIMD-20..25`).
- Specify lane-wise arithmetic (checked default, `wrapping_*`, `saturating_*`, IEEE-754 float per lane), bitwise/shift ops, explicit `splat`/`extract`/`insert`/`shuffle`, lane comparisons returning `Mask<N>`, mask algebra (`&`, `|`, `^`, `!`, `all`, `any`, `none`, `bitmask`, `select`), numeric `cast` vs representation-checked `bitcast`, and horizontal reductions (including ordered left-to-right FP `reduce_add_ordered` vs explicit associative reductions, `ANUM-31..42`, `ASIMD-28..43`).
- Specify safe capability-based SIMD memory access (`from_slice`, `copy_to_slice`, `load_unaligned`, `store_unaligned`, `load_masked`, `store_masked` where inactive lanes perform no semantic memory access, and bounds-checked `gather`/`scatter`, `ASIMD-34..36, 44..47`).
- Specify data-oriented `TensorView<T, R>`, `TensorMutView<T, R>`, and `MatrixView<T>` library abstractions built from a flat `view<[T]>`/`mut_view<[T]>` capability plus `shape`/`strides` metadata without nested views or mandatory runtime (`ANUM-64..95`, `ASIMD-83..96`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-42-simd.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-SIMD-NNN` rules, positive/negative canonical Axiom examples, and source citations.
- [ ] `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md` are updated consistently with `SPEC-42`.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T463-report.md` with exact `## Files changed`.

## Out of scope
- Compiler and `std.simd` implementation (`T464`–`T467`) and LIR/x86-64 SIMD backend (`E12.4`).
- Editing `docs/` or `bootstrap/axiom0/`.

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T463/build` and `python tools/axtest.py --compiler build-snap-T463/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
- 2026-11-03 09:00:27 started (attempt 1) T463-impl
