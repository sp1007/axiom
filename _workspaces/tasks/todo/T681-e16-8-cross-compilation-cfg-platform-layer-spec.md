---
id: T681
title: E16.8 — Canonical cross-compilation, @cfg target matrix, sysroot/SDK & 3-level OS platform layer specification (SPEC-88)
phase: P16-targets-platforms
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T216, T313, T653]
priority: 124
status: todo
attempts: 0
paths: [spec/SPEC-88-cross-compilation-platform-layer.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-04-core-extensibility.md, spec/SPEC-81-target-desc-isa-conformance.md, 0097, 0220, tasks/0336, tasks/0453, tasks/0587]
covers: [REQ-TOOL-001, REQ-TGT-080, REQ-TGT-081, REQ-TGT-082, REQ-TGT-083, REQ-TGT-084]
---
# T681 — E16.8 — Canonical cross-compilation, @cfg target matrix, sysroot/SDK & 3-level OS platform layer specification (SPEC-88)

## Goal
Consolidate the canonical specification for Axiom's any-host-to-any-target cross-compilation model, `@cfg(...)` conditional compilation predicates, hermetic SDK/sysroot & built-in OS import stubs (`REQ-TOOL-001`), and the 3-level OS platform architecture (`0220`) into `spec/SPEC-88-cross-compilation-platform-layer.md` (`AXS-XCMP-*` and `AXS-PLAT-*` rule IDs).

## Scope
- Write `spec/SPEC-88-cross-compilation-platform-layer.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-XCMP-NNN` and `AXS-PLAT-NNN` rules (`0220`, `tasks/0336`, `tasks/0453`, `tasks/0587`).
- Specify unified single-binary cross-compilation (`tasks/0453 §194.1–20`, `tasks/0587 §1–8`): any host `axiomc` binary compiles for any supported target from one frontend; `Host` environment and `Target` environment remain strictly distinct during `const`/comptime evaluation (`size_of::<usize>()`, `align_of::<T>()`, pointer width, endianness, and layout queries always reflect `TargetDesc`, never the host compiler binary).
- Specify `@cfg(...)` conditional compilation (`SPEC-04 AXS-EXT-091`, `tasks/0587 §9–11`):
  - Allowed predicates: `target_arch = "x86_64"|"aarch64"|"wasm32"|"riscv64"`, `target_os = "windows"|"linux"|"macos"|"android"|"wasi"|"none"`, `target_env = "msvc"|"gnu"|"musl"|"bionic"|""`, `target_abi = "win64"|"sysv64"|"aapcs64"|"apple_arm64"|"win_arm64"|"wasm"|"lp64d"`, `target_endian = "little"|"big"`, `target_pointer_width = "32"|"64"`, `target_feature = "..."`, `profile = "hosted"|"freestanding"|"kernel"|"system"`, `debug_assertions`, and boolean combinators `all(...)`, `any(...)`, `not(...)`.
  - Parse-all, prune-before-resolve rule: all `@cfg`-annotated items, fields, and statements are parsed by S0/S1 grammar first (so syntax errors in inactive target branches are still caught), then pruned before name resolution and type checking; unknown `@cfg` keys or invalid target literals are rejected with `AX_NAME_INVALID_CFG_PREDICATE`.
- Specify hermetic SDK/sysroot and zero-third-party-compiler linking (`REQ-TOOL-001`, `0097 §27`, `tasks/0587 §13–15`): `--sysroot <dir>` and `--target-sdk <dir>` flags for third-party C libraries, combined with built-in Axiom OS import stubs (`kernel32.dll`, `libc.so.6`, `Bionic`, `libSystem.B.dylib`, `wasi_snapshot_preview1`) so standard Axiom programs cross-compile and link out-of-the-box without GCC/Clang/MSVC/Xcode/NDK installed.
- Specify the 3-level OS & Platform Layer (`0220 §1–16`):
  - **Level 1 (`std.io`, `std.fs`, `std.process`, `std.env`, `std.time`, `std.thread`, `std.net`)**: Portable safe standard library APIs.
  - **Level 2 (`std.os.windows`, `std.os.linux`, `std.os.macos`, `std.os.android`, `std.os.wasi`)**: Explicit platform-specific extensions (handles, file descriptors, Mach ports, epoll/IOCP/kqueue).
  - **Level 3 (`std.sys.*`)**: Raw OS ABI / syscall / system-DLL boundary implementing `std/core/host.ax`.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-88-cross-compilation-platform-layer.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-XCMP-NNN` and `AXS-PLAT-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T681-report.md` with exact `## Files changed`.

## Out of scope
- Compiler and stdlib implementation (`T682`, `T683`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 08:43:00 created by T216 (P16 phase planning)
