---
id: T691
title: E16.11 — Driver multi-arch universal build pipeline & slice inspection tooling
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
priority: 134
status: todo
attempts: 0
depends: [T313, T682, T690]
paths: [compiler/driver/universal, compiler/driver/emit_universal, tests/driver/universal, tests/selfhost/driver]
spec: [spec/SPEC-90-universal-multiarch-artifacts.md, tasks/0453, tasks/0587]
covers: [REQ-TGT-001, REQ-TGT-154, REQ-TGT-200, REQ-TGT-319]
---
# T691 — E16.11 — Driver multi-arch universal build pipeline & slice inspection tooling

## Goal

Implement the compiler driver's multi-architecture universal build pipeline (`compiler/driver/universal`) and binary slice inspection/extraction subcommands (`compiler/driver/emit_universal`) in both `axiom0` and the self-hosted driver.

## Scope

- Implement `compiler/driver/universal` and `tests/selfhost/driver/universal.ax`:
  - Orchestrate parallel/sequential per-slice compilation and linking for `--universal-targets <triple1>,<triple2>` (e.g., `x86_64-apple-darwin,aarch64-apple-darwin`), running per-target `@cfg` evaluation, codegen, Mach-O linking, and ad-hoc code signing before invoking the Universal 2 composer.
- Implement `compiler/driver/emit_universal` and `tests/selfhost/driver/emit_universal.ax`:
  - Provide native `lipo`-equivalent operations (`--inspect-slices`, `--extract-slice <arch>`, `--verify-arch <arch>`) for CI and developer workflows without requiring external Xcode command-line tools.
- Add driver tests in `tests/driver/universal`.

## Acceptance
- [ ] `ctest --output-on-failure -R driver_universal` passes.
- [ ] Building with `--universal-targets x86_64-apple-darwin,aarch64-apple-darwin` produces a valid Universal 2 binary whose slices can be inspected and extracted via `--inspect-slices` and `--extract-slice`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T691-report.md` with exact `## Files changed`.

## Out of scope
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). All Axiom sources and test programs use canonical syntax (`axiom-syntax`): `=` only, `.` paths only, and `Xin ch?o th? gi?i` for greeting strings.

## Log
- 2026-11-03 08:50:00 created by T216 (P16 phase planning)
