---
id: T567
title: E14.4 — Native vtable layout, .rdata vtable emission, fat-pointer ABI & indirect call codegen
phase: P14-comptime-2-0-reflection-genera
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T058]
priority: 188
status: todo
attempts: 0
paths: [compiler/lir, compiler/target/x64, compiler/obj, tests/run/dyn_native, tests/mc/dyn, tests/selfhost]
spec: [spec/SPEC-63-dyn-trait-vtables.md, tasks/0476, 0212]
covers: [REQ-CORE-3041, REQ-CORE-3042, REQ-CORE-3043, REQ-CORE-3044]
---
# T567 — E14.4 — Native vtable layout, .rdata vtable emission, fat-pointer ABI & indirect call codegen

## Goal
Implement native LIR and x86-64 lowering for `dyn Trait` fat pointers (`(data_ptr, vtable_ptr)`), deterministic read-only `.rdata` vtable emission with function relocations, and indirect method call codegen per `spec/SPEC-63-dyn-trait-vtables.md`.

## Scope
- Lower `(ImplType, TraitId)` vtable descriptors in `compiler/lir` and `compiler/obj` into deterministic read-only `.rdata` symbols containing `[drop_in_place, size, align, method_0, method_1, ...]` with 64-bit COFF function relocations (`IMAGE_REL_AMD64_ADDR64`).
- Lower 16-byte `dyn Trait` fat pointers (`view<dyn Trait>`, `mut_view<dyn Trait>`) across the Windows x64 ABI (register pair / by-ref argument passing and return) and emit indirect call instructions (`call [r_vtable + slot_offset]`) in `compiler/target/x64`.

## Acceptance
- [ ] Machine-code and differential (`--interp` and native) tests in `tests/mc/dyn` and `tests/run/dyn_native` verify `.rdata` vtable symbol emission, 16-byte fat-pointer ABI passing/returning, and indirect vtable dispatch across multiple implementing types.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`) with `0 WEAK-NATIVE`.
- [ ] Report `_workspaces/reports/T567-report.md` with exact `## Files changed`.

## Out of scope
- Owned `Box<dyn Trait>` and vtable `drop_in_place` destruction (`T568`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T567/build` and `python tools/axtest.py --compiler build-snap-T567/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:23:30 created by T214 (P14 phase planning)
