---
id: T690
title: E16.11 — Mach-O x86_64-apple-darwin slice & Fat/Universal 2 binary composer
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
priority: 133
status: todo
attempts: 0
depends: [T313, T667, T686, T689]
paths: [compiler/obj/macho_universal, compiler/target/x64/macos, tests/obj/macho_universal, tests/selfhost/obj]
spec: [spec/SPEC-90-universal-multiarch-artifacts.md, 0196, tasks/0453]
covers: [REQ-TGT-001, REQ-TGT-104, REQ-TGT-106, REQ-TGT-153]
---
# T690 — E16.11 — Mach-O x86_64-apple-darwin slice & Fat/Universal 2 binary composer

## Goal

Implement the `x86_64-apple-darwin` Mach-O slice emitter (`compiler/target/x64/macos`) and the Universal 2 (`FAT_MAGIC` / `FAT_MAGIC_64`) multi-architecture binary and archive composer (`compiler/obj/macho_universal`) in both `axiom0` and the self-hosted compiler.

## Scope

- Implement `compiler/target/x64/macos`:
  - Configure `x86_64-apple-darwin` target descriptor (SysV x86-64 register convention with Darwin `_` C symbol prefix, 4 KiB page alignment, `X86_64_RELOC_UNSIGNED`/`SIGNED`/`BRANCH`/`GOT_LOAD`/`TLV` relocations, and Mach-O 64-bit `CPU_TYPE_X86_64` header).
- Implement `compiler/obj/macho_universal` and `tests/selfhost/obj/macho_universal.ax`:
  - Compose single-architecture Mach-O executables, `.dylib`s, and BSD `.a` static archives into `FAT_MAGIC` (`0xcafebabe`, 32-bit offsets) or `FAT_MAGIC_64` (`0xcafebabf`, 64-bit offsets when any slice offset/size ≥ 4 GiB) universal containers.
  - Enforce 16 KiB (`align = 14`) slice alignment for `CPU_TYPE_ARM64` and 4 KiB (`align = 12`) for `CPU_TYPE_X86_64`, deterministic `cputype` sorting, zero padding, and disjoint architecture validation (`E9000–E9014`).
- Add unit tests in `tests/obj/macho_universal`.

## Acceptance
- [ ] `ctest --output-on-failure -R macho_universal` passes.
- [ ] Universal binaries pass `FAT_MAGIC`/`FAT_MAGIC_64` big-endian header and per-slice Mach-O + `LC_CODE_SIGNATURE` validation.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T690-report.md` with exact `## Files changed`.

## Out of scope
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). All Axiom sources and test programs use canonical syntax (`axiom-syntax`): `=` only, `.` paths only, and `Xin ch?o th? gi?i` for greeting strings.

## Log
- 2026-11-03 08:50:00 created by T216 (P16 phase planning)
