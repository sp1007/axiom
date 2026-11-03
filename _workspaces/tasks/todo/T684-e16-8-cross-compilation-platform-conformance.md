---
id: T684
title: E16.8 — Any-host-to-any-target cross-compilation, @cfg matrix & OS platform layer conformance suite
phase: P16-targets-platforms
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T313, T683]
priority: 127
status: todo
attempts: 0
paths: [tests/conformance/p16/e16_8_cross_compile]
spec: [spec/SPEC-88-cross-compilation-platform-layer.md, 0097, 0220, tasks/0336, tasks/0453, tasks/0587]
covers: [REQ-TOOL-001, REQ-TGT-318, REQ-TGT-326]
---
# T684 — E16.8 — Any-host-to-any-target cross-compilation, @cfg matrix & OS platform layer conformance suite

## Goal
Certify the E16.8 exit criterion (`ROADMAP.md` §3): any host builds for any supported target from one frontend without third-party C compilers (`REQ-TOOL-001`), `@cfg(...)` target-matrix pruning, host-vs-target comptime isolation, and the 3-level OS platform layer.

## Scope
- Create `tests/conformance/p16/e16_8_cross_compile` covering:
  - Full target-matrix cross-build sweep from the current host across all roadmap targets (`x86_64-windows`, `x86_64-linux`, `aarch64-linux`, `aarch64-macos`, `aarch64-android`, `wasm32`, `riscv64-linux`), verifying container headers, machine architectures, entry points, and byte-for-byte determinism without invoking external compilers (`REQ-TOOL-001`).
  - `@cfg(...)` boolean combinator (`all`, `any`, `not`) and target predicate (`target_arch`, `target_os`, `target_abi`, `target_pointer_width`, `profile`) positive and negative UI tests, including verification that syntax errors in inactive `@cfg` blocks are still diagnosed while type/name references inside inactive blocks are pruned before resolution.
  - Host-vs-target isolation tests proving `size_of.<usize>()`, `align_of.<*const u8>()`, and struct layout offsets in `const` items reflect the target (`wasm32` vs 64-bit targets) rather than the host.
  - Level-1 (`std.*`) vs Level-2 (`std.os.<platform>`) visibility tests proving `std.os.linux` is rejected when compiling for `--target x86_64-windows` and vice versa.

## Acceptance
- [ ] All conformance tests in `tests/conformance/p16/e16_8_cross_compile` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T684-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation changes (belong in `T682`–`T683`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). All Axiom test programs use canonical syntax (`axiom-syntax`): `=` only, `.` paths only, and `Xin chào thế giới` for greeting strings.

## Log
- 2026-11-03 08:43:00 created by T216 (P16 phase planning)
