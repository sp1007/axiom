---
id: T668
title: E16.4 — macOS AArch64 ABI, Mach-O 64 container, chained fixups & ad-hoc codesign conformance suite
phase: P16-targets-platforms
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T313, T667]
priority: 111
status: todo
attempts: 0
paths: [tests/conformance/p16/e16_4_macos_aarch64]
spec: [spec/SPEC-84-macos-aarch64-macho.md, 0196, tasks/0563]
covers: [REQ-TGT-314, REQ-TGT-315, REQ-TGT-316, REQ-TGT-317]
---
# T668 — E16.4 — macOS AArch64 ABI, Mach-O 64 container, chained fixups & ad-hoc codesign conformance suite

## Goal
Certify the E16.4 exit criterion (`ROADMAP.md` §3): Apple ARM64 ABI compliance, Mach-O 64 `MH_OBJECT`/`MH_EXECUTE`/`MH_DYLIB` container and load-command validity, `dyld` chained fixups / export trie correctness, and SHA-256 ad-hoc `LC_CODE_SIGNATURE` verification.

## Scope
- Create `tests/conformance/p16/e16_4_macos_aarch64` covering:
  - Apple ARM64 ABI tests: `X18` never allocated or modified across register pressure, caller sign/zero extension of `i8`/`u8`/`i16`/`u16`, packed natural-alignment stack arguments vs 8-byte variadic stack slots (`printf`-style FFI), `X29` frame record chain, and `_` symbol prefixing.
  - Mach-O 64 structural validator tests: 16 KiB segment alignment (`__PAGEZERO`, `__TEXT`, `__DATA_CONST`, `__DATA`, `__LINKEDIT`), `LC_MAIN`, `LC_LOAD_DYLINKER`, `LC_LOAD_DYLIB`, `LC_DYLD_CHAINED_FIXUPS` pointer walk, `LC_DYLD_EXPORTS_TRIE` lookup of `@export` symbols, and `LC_CODE_SIGNATURE` `CodeDirectory` SHA-256 page hash recomputation check.
  - Cross-build determinism tests (running on any host) and native execution tests (when running on `aarch64-macos`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p16/e16_4_macos_aarch64` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T668-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation changes (belong in `T666`–`T667`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). All Axiom test programs use canonical syntax (`axiom-syntax`): `=` only, `.` paths only, and `Xin chào thế giới` for greeting strings.

## Log
- 2026-11-03 08:39:00 created by T216 (P16 phase planning)
