---
id: T692
title: E16.11 — Universal / multi-arch artifacts conformance suite
phase: P16-targets-platforms
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
priority: 135
status: todo
attempts: 0
depends: [T313, T691]
paths: [tests/conformance/p16/e16_11_universal_artifacts]
spec: [spec/SPEC-90-universal-multiarch-artifacts.md, 0196, tasks/0453]
covers: [REQ-TGT-001, REQ-TGT-199, REQ-TGT-318, REQ-TGT-320]
---
# T692 — E16.11 — Universal / multi-arch artifacts conformance suite

## Goal

Build the end-to-end conformance suite (`tests/conformance/p16/e16_11_universal_artifacts`) verifying Universal 2 Mach-O executables, `.dylib`s, and static `.a` archives across `x86_64-apple-darwin` and `aarch64-apple-darwin` slices, slice extraction, per-slice code signature integrity, and deterministic reproduction.

## Scope

- Create `tests/conformance/p16/e16_11_universal_artifacts` testing:
  - Universal 2 executable, `.dylib`, and `.a` archive emission containing both `CPU_TYPE_X86_64` and `CPU_TYPE_ARM64` slices with target-specific `@cfg(target_arch = ...)` code paths.
  - Big-endian `fat_header` and `fat_arch` / `fat_arch_64` layout verification, 16 KiB ARM64 / 4 KiB x86_64 slice alignment, and per-slice `LC_CODE_SIGNATURE` SHA-256 page hash verification.
  - Negative diagnostic tests for duplicate architecture slices, incompatible artifact kinds across slices, and unaligned slice offsets (`E9000–E9014`).
  - Bit-for-bit determinism across repeated universal builds.

## Acceptance
- [ ] `ctest --output-on-failure -R e16_11_universal_artifacts` passes 100%.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T692-report.md` with exact `## Files changed`.

## Out of scope
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). All Axiom sources and test programs use canonical syntax (`axiom-syntax`): `=` only, `.` paths only, and `Xin ch?o th? gi?i` for greeting strings.

## Log
- 2026-11-03 08:50:00 created by T216 (P16 phase planning)
