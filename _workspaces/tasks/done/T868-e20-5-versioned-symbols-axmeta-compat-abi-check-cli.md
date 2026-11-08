---
id: T868
title: E20.5 Versioned symbol mangling/export tables, .axmeta binary compatibility checker & axiomc abi-check SemVer diff CLI
phase: P20-build-system-package-ecosystem
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T220, T681, T685, T318, T866, T867]
priority: 218
status: done
attempts: 1
paths: [compiler/abi/compat_diff, compiler/driver/abi_cmd, tests/run/abi_compat_diff]
spec: [spec/SPEC-114-abi-stability-versioning-binary-compat.md, spec/SPEC-24-artifact-format-module-interfaces.md, 0104, tasks/0452, tasks/0583, tasks/0739]
covers: [REQ-ECO-8734, REQ-PKG-022, REQ-PKG-024]
started: 2026-11-08 21:29:37
finished: 2026-11-08 22:17:17
---
# T868 — E20.5 Versioned symbol mangling/export tables, .axmeta binary compatibility checker & axiomc abi-check SemVer diff CLI

## Goal
Implement versioned symbol export emission, `.axmeta` binary compatibility verification, and the `axiomc abi-check` SemVer/ABI compatibility diff engine per `spec/SPEC-114-abi-stability-versioning-binary-compat.md`.

## Scope
- Implement `compiler/abi/compat_diff` comparing baseline and candidate `.axmeta` / `@abi(stable)` descriptors to classify changes into `identical`, `implementation-only`, `minor-additive` (new exports, appended extensible struct fields with version bump), and `major-breaking` (removed symbols, altered field offsets/sizes/alignments, changed calling conventions, tightened capability/ownership contracts; `tasks/0452 §193.14-21`, `tasks/0583 §324.9-20`, `tasks/0739 §493.18-24`).
- Implement versioned symbol mangling and export table metadata (`@symbol_version("1.0")`) so multiple ABI versions of an exported function can coexist in a shared library (`tasks/0452 §193.19`, `tasks/0583 §324.13`, `REQ-ECO-8734`).
- Implement `compiler/driver/abi_cmd` providing `axiomc abi-check --old <base.axmeta> --new <cand.axmeta> --semver <old_ver>:<new_ver>` (failing when a breaking ABI/API change occurs without a major SemVer bump; `REQ-PKG-022`, `REQ-PKG-024`).
- Add run tests in `tests/run/abi_compat_diff`.

## Acceptance
- [ ] Run tests in `tests/run/abi_compat_diff` verify `axiomc abi-check` detection of field offset/size/alignment breaks, signature/ownership breaks, legal additive evolution, SemVer policy enforcement, and versioned symbol coexistence in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T868-report.md` with exact `## Files changed`.

## Out of scope
- Dynamic component hot-reload state migration (`T870`–`T873`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T868/build` and `python tools/axtest.py --compiler build-snap-T868/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
- 2026-11-08 21:29:37 started (attempt 1) T868-impl
- 2026-11-08 22:17:17 accepted by QA -> done
