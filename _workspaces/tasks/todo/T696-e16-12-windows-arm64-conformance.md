---
id: T696
title: E16.12 — Windows ARM64 conformance suite
phase: P16-targets-platforms
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
priority: 139
status: todo
attempts: 0
depends: [T313, T688, T695]
paths: [tests/conformance/p16/e16_12_windows_arm64]
spec: [spec/SPEC-91-windows-arm64.md, 0181, 0193, tasks/0453, tasks/0521]
covers: [REQ-TGT-124, REQ-TGT-157, REQ-TGT-197, REQ-TGT-318]
---
# T696 — E16.12 — Windows ARM64 conformance suite

## Goal

Build the end-to-end conformance suite (`tests/conformance/p16/e16_12_windows_arm64`) verifying `aarch64-pc-windows-msvc` compilation, Windows ARM64 variadic/HFA calling convention, `x15` `__chkstk` large-frame probing, `.pdata`/`.xdata` unwind metadata, and PE32+ ARM64 `.exe`/`.dll` linking.

## Scope

- Create `tests/conformance/p16/e16_12_windows_arm64` testing:
  - `Xin chào thế giới` console executable (`WriteFile` / `GetStdHandle` via `kernel32.dll`), exit codes, and CLI UTF-16 argument decoding (`GetCommandLineW`).
  - Windows ARM64 ABI torture tests: variadic C FFI calls passing floats/doubles in GPRs `x0`–`x7`, HFA structs in `v0`–`v3` on non-variadic calls, `x18` TEB preservation across calls, and large-frame (`> 4 KiB` and `> 64 KiB`) `__chkstk` stack probing.
  - PE32+ ARM64 DLL export/import round-trip (`.dll` + `.lib` + `.exe` consumer), TLS (`@[thread_local]` via `x18` TEB), and `.pdata`/`.xdata` unwind verification.
  - Native execution on Windows ARM64 hosts or structural + instruction-emulator verification on x86-64 hosts.

## Acceptance
- [ ] `ctest --output-on-failure -R e16_12_windows_arm64` passes 100%.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T696-report.md` with exact `## Files changed`.

## Out of scope
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). All Axiom sources and test programs use canonical syntax (`axiom-syntax`): `=` only, `.` paths only, and `Xin ch?o th? gi?i` for greeting strings.

## Log
- 2026-11-03 08:50:00 created by T216 (P16 phase planning)
