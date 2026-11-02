---
id: T503
title: E13.1 — External Windows x64 ABI oracle (gcc DLL 1..8 mixed args, 1..24B structs, offsetof table; ADR-0034 §8 OI-12)
phase: P13-low-level-systems-unsafe-frees
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T500]
priority: 152
status: todo
attempts: 0
paths: [tests/ffi/win64_abi_oracle, tests/mc/isel]
spec: [spec/SPEC-50-unsafe-ub-ffi.md, spec/decisions/ADR-0034-oracle-independence.md, 0181, 0104]
covers: [REQ-ABI-009, REQ-ABI-010, REQ-ABI-022, REQ-ABI-045, REQ-ABI-047, REQ-ABI-048, REQ-ABI-050, REQ-ABI-054, REQ-ABI-066, REQ-ABI-069, REQ-ABI-070, REQ-ABI-071, REQ-ABI-072, REQ-ABI-074, REQ-ABI-075, REQ-ABI-076, REQ-ABI-077, REQ-ABI-079, REQ-ABI-080, REQ-ABI-081, REQ-ABI-082, REQ-ABI-084, REQ-ABI-085, REQ-ABI-089, REQ-ABI-090, REQ-RES-142, REQ-RES-143, REQ-RES-164, REQ-RES-165, REQ-RES-166, REQ-ABI-092, REQ-ABI-094, REQ-ABI-104]
---
# T503 — E13.1 — External Windows x64 ABI oracle (gcc DLL 1..8 mixed args, 1..24B structs, offsetof table; ADR-0034 §8 OI-12)

## Goal
Implement the ADR-0034 §8 (audit 2026-10-19 OI-12) external Windows x64 ABI oracle before FFI breadth: a gcc-built shared library (`gcc -shared`) and `offsetof`/`sizeof` verification suite.

## Scope
- Build a C shared library fixture with `gcc -shared` exporting functions with 1..8 mixed-width scalar/pointer/float arguments (`i8`, `u16`, `i32`, `u64`, `f32`, `f64`, `*const u8`) and `@repr(C)` structs of size 1, 2, 3, 4, 8, 12, 16, and 24 bytes passed by value and returned by value.
- Write Axiom test programs calling every exported DLL function via `@link` and verifying argument/return bit patterns in both directions (Axiom -> C DLL and C DLL -> Axiom `extern "C" fn` callback).
- Generate and execute a gcc `offsetof`/`sizeof`/`_Alignof` verification table against Axiom `@repr(C)` struct layouts across mixed field widths and alignments.
- Audit and update `tests/mc/isel/cdriver_abi*.c` so no C ABI driver relies on `assert()` (which is compiled out under `NDEBUG`); replace with explicit `if (...) return 1;` checks.

## Acceptance
- [ ] `tests/ffi/win64_abi_oracle` builds the test DLL via `gcc -shared` (failing hard if `gcc` is missing per ADR-0034 §7) and verifies 1..8 mixed-width args and size 1/2/3/4/8/12/16/24 struct by-value parameter passing and returns via `@link`.
- [ ] `offsetof`/`sizeof`/`alignof` table matches gcc across all tested `@repr(C)` structs.
- [ ] `tests/mc/isel/cdriver_abi*.c` contains zero `assert(...)` calls that could be stripped by `-DNDEBUG`.
- [ ] Report `_workspaces/reports/T503-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T503/build` and `python tools/axtest.py --compiler build-snap-T503/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 01:58:00 created by T213 (P13 phase planning)
