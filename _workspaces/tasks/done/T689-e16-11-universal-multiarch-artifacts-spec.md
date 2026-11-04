---
id: T689
title: E16.11 — Universal / multi-arch artifacts specification (SPEC-90)
phase: P16-targets-platforms
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
priority: 132
status: done
attempts: 1
depends: [T216, T511, T665, T685]
paths: [spec/SPEC-90-universal-multiarch-artifacts.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-04-core-extensibility.md, spec/SPEC-84-macos-aarch64-macho.md, spec/SPEC-89-artifact-library-matrix.md, 0196, tasks/0453, tasks/0587]
covers: [REQ-TGT-001, REQ-TGT-104, REQ-TGT-105, REQ-TGT-200]
started: 2026-11-04 06:53:50
finished: 2026-11-04 08:11:31
---
# T689 — E16.11 — Universal / multi-arch artifacts specification (SPEC-90)

## Goal

Author `spec/SPEC-90-universal-multiarch-artifacts.md` — the normative specification for universal / multi-architecture binary artifacts in Axiom, including Mach-O Fat / Universal 2 (`FAT_MAGIC`/`0xcafebabe` and `FAT_MAGIC_64`/`0xcafebabf`) executables, `.dylib`s, and static archives combining `x86_64-apple-darwin` and `aarch64-apple-darwin` slices, plus multi-target package bundles and CLI inspection commands.

## Scope

- Create `spec/SPEC-90-universal-multiarch-artifacts.md` covering:
  - Mach-O Fat header (`fat_header`, big-endian `magic` and `nfat_arch`) and `fat_arch` / `fat_arch_64` descriptor layout (`cputype`, `cpusubtype`, `offset`, `size`, `align`).
  - Slice alignment requirements (`2^14` = 16 KiB for `CPU_TYPE_ARM64`, `2^12` = 4 KiB for `CPU_TYPE_X86_64`), deterministic slice ordering (ascending `cputype`), and zero-filled padding between slices.
  - Universal static archive layout (Fat container wrapping per-architecture BSD `!<arch>\n` archives with `__.SYMDEF SORTED` tables) and universal `.dylib` / executable code-signing interaction (per-slice `LC_CODE_SIGNATURE` embedded before Fat packaging).
  - `x86_64-apple-darwin` Mach-O slice delta (SysV x86-64 ABI on Darwin, `_` symbol prefix, 4 KiB page size, `X86_64_RELOC_*` relocations).
  - Driver CLI flags (`--universal-targets x86_64-apple-darwin,aarch64-apple-darwin`, `axiom obj inspect --slices`) and diagnostic codes (`E9000–E9014`).
- Register `SPEC-90`, diagnostics, and invariants (`INV-UNIV-01..04`) in `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `python .claude/skills/axiom-tasks/scripts/harness_check.py` exits 0.
- [ ] `spec/SPEC-90-universal-multiarch-artifacts.md` defines Universal 2 Fat headers, slice alignment, and multi-arch static/dynamic library packaging.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T689-report.md` with exact `## Files changed`.

## Out of scope
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). All Axiom sources and test programs use canonical syntax (`axiom-syntax`): `=` only, `.` paths only, and `Xin ch?o th? gi?i` for greeting strings.

## Log
- 2026-11-03 08:50:00 created by T216 (P16 phase planning)
- 2026-11-04 06:53:50 started (attempt 1) T689-impl
- 2026-11-04 08:11:31 accepted by QA -> done
