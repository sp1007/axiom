---
id: T500
title: E13.1 — Canonical unsafe, UB, pointer provenance, FFI/ABI & REQ-OWNER-008 address specification (SPEC-50)
phase: P13-low-level-systems-unsafe-frees
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T213]
priority: 150
status: done
attempts: 1
paths: [spec/SPEC-50-unsafe-ub-ffi.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md, spec/SPEC-03-core-semantics.md]
spec: [spec/SPEC-03-core-semantics.md, spec/SPEC-10-ownership.md, spec/SPEC-11-capability.md, spec/decisions/ADR-0001-fixed-address-declarations.md, spec/decisions/ADR-0034-oracle-independence.md, 0071, 0044, 0104, tasks/0339, tasks/0282]
covers: [REQ-OWNER-008, REQ-ABI-005, REQ-ABI-006, REQ-ABI-007, REQ-ABI-008, REQ-ABI-013, REQ-ABI-014, REQ-ABI-015, REQ-ABI-016, REQ-ABI-017, REQ-ABI-020, REQ-ABI-021, REQ-ABI-023, REQ-ABI-025, REQ-ABI-026, REQ-ABI-027, REQ-ABI-028, REQ-ABI-029, REQ-ABI-030, REQ-ABI-034, REQ-ABI-035, REQ-CAP-004, REQ-CAP-006, REQ-ABI-037, REQ-ABI-038, REQ-ABI-040, REQ-ABI-042, REQ-ABI-043, REQ-CAP-008, REQ-CAP-009, REQ-CAP-011, REQ-CAP-012, REQ-CAP-014, REQ-CAP-016, REQ-CAP-017, REQ-CAP-020, REQ-CAP-021, REQ-CAP-022, REQ-CAP-023, REQ-CAP-024, REQ-CAP-028, REQ-CAP-029, REQ-CAP-030, REQ-CAP-035, REQ-CAP-036, REQ-CAP-039, REQ-CAP-042, REQ-CAP-043, REQ-CAP-044, REQ-CAP-045, REQ-CAP-050, REQ-ABI-051, REQ-ABI-058, REQ-ABI-062, REQ-CAP-052, REQ-CAP-053, REQ-CAP-054, REQ-ABI-068, REQ-CAP-055, REQ-CAP-057, REQ-CAP-058, REQ-CAP-060, REQ-CAP-063, REQ-CAP-064, REQ-CAP-066, REQ-CAP-068, REQ-CAP-072, REQ-CAP-074, REQ-CAP-075, REQ-CAP-076, REQ-CAP-077, REQ-CAP-079, REQ-CAP-080, REQ-CAP-081, REQ-CAP-082, REQ-CAP-089, REQ-CAP-090, REQ-CAP-092, REQ-CAP-094, REQ-ABI-073, REQ-CAP-096, REQ-CAP-097, REQ-CAP-099, REQ-CAP-100, REQ-CAP-101, REQ-ABI-086, REQ-ABI-087, REQ-ABI-088, REQ-CAP-104, REQ-CAP-106, REQ-CAP-108, REQ-CAP-110, REQ-CAP-112, REQ-CAP-113, REQ-CAP-114, REQ-CAP-115, REQ-CAP-116, REQ-CAP-117, REQ-CAP-119, REQ-CAP-120, REQ-CAP-121, REQ-RES-130, REQ-RES-131, REQ-RES-132, REQ-RES-138, REQ-RES-139, REQ-RES-140, REQ-RES-141, REQ-RES-144, REQ-RES-146, REQ-RES-147, REQ-RES-148, REQ-RES-149, REQ-RES-150, REQ-RES-151, REQ-RES-152, REQ-RES-153, REQ-RES-154, REQ-RES-155, REQ-RES-156, REQ-RES-157, REQ-RES-158, REQ-RES-162, REQ-RES-171, REQ-RES-172, REQ-RES-174, REQ-RES-175, REQ-RES-176, REQ-RES-177, REQ-RES-178, REQ-RES-179, REQ-CAP-128, REQ-CAP-134, REQ-CAP-142, REQ-CAP-147]
started: 2026-11-03 08:40:42
finished: 2026-11-03 08:59:37
---
# T500 — E13.1 — Canonical unsafe, UB, pointer provenance, FFI/ABI & REQ-OWNER-008 address specification (SPEC-50)

## Goal
Consolidate the full unsafe language boundary, undefined-behavior (UB) taxonomy, raw pointer provenance model, FFI/C ABI stability contracts, and `REQ-OWNER-008` address introspection and fixed-address placement (`fn_addr`, `static_addr`, `address_of(v) as usize`, `@addr(<expr>)`) into canonical `spec/SPEC-50-unsafe-ub-ffi.md` (`AXS-UNS-*` rule IDs).

## Scope
- Write `spec/SPEC-50-unsafe-ub-ffi.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-UNS-NNN` rules.
- Specify full `unsafe` blocks, `unsafe fn`, `unsafe trait`, and `unsafe impl` rules, trusted-unsafe precondition contracts, and the rule that safe verification (`view<T>`, `mut_view<T>`, ownership, drop) resumes immediately across an `unsafe` boundary.
- Specify the raw pointer (`*const T`, `*mut T`) strict-provenance model, pointer arithmetic/offset bounds, alignment/validity invariants, raw-pointer-to-`view<T>`/`mut_view<T>` conversion preconditions, and comprehensive UB catalog.
- Specify **`REQ-OWNER-008`** address introspection and `@addr(<expr>)` / `@at(<expr>)` fixed-address placement: `fn_addr(f) -> usize`, `static_addr(s) -> usize`, `address_of(v)` / `address_of_mut(v)`, `addr_of(v) -> usize`, `address_of(v) as usize`, pointer/fn-pointer `as usize`, and `@addr(<expr>)` fixed-address placement for `static`, `let`, and `fn`, including dynamic expression support (`let base = fn_addr(foo); @addr(base + 0x100) static mut REG: u32;`) and round-trip address equality (`fn_addr(isr) == 0x2000_0000usize`).
- Specify FFI and ABI boundary contracts (`extern "C"`, `@repr(C)`, `@repr(transparent)`, `@abi(stable)`, opaque foreign types, explicit C callback adapters, conservative foreign-call effect modeling, and the ADR-0034 §8 / OI-12 external Windows x64 ABI oracle requirements).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-50-unsafe-ub-ffi.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-UNS-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `REQ-OWNER-008` (`fn_addr`, `static_addr`, `address_of(v) as usize`, and `@addr(<expr>)` on `static`, `let`, and `fn` including dynamic `base + offset` and round-trip assertions) is normatively specified.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T500-report.md` with exact `## Files changed`.

## Out of scope
- Compiler or library implementation (handled by `T501`–`T504`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T500/build` and `python tools/axtest.py --compiler build-snap-T500/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 01:58:00 created by T213 (P13 phase planning)
- 2026-11-03 08:40:42 started (attempt 1) T500-impl
- 2026-11-03 08:59:37 accepted by QA -> done
