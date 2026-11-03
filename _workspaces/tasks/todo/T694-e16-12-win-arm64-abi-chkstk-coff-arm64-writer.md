---
id: T694
title: E16.12 — Windows ARM64 ABI, __chkstk (x15) frame lowering & COFF 0xAA64 object writer
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
priority: 137
status: todo
attempts: 0
depends: [T313, T662, T693]
paths: [compiler/abi/win_arm64, compiler/target/aarch64/win_frame, compiler/obj/coff_arm64, tests/obj/coff_arm64, tests/selfhost/abi, tests/selfhost/obj]
spec: [spec/SPEC-91-windows-arm64.md, 0181, 0185, 0193, tasks/0453, tasks/0521]
covers: [REQ-TGT-124, REQ-TGT-125, REQ-TGT-130, REQ-TGT-131, REQ-TGT-149]
---
# T694 — E16.12 — Windows ARM64 ABI, __chkstk (x15) frame lowering & COFF 0xAA64 object writer

## Goal

Implement the Windows ARM64 calling convention (`compiler/abi/win_arm64`), `__chkstk` (`x15` 16-byte unit) prologue/epilogue and `.pdata`/`.xdata` unwind emitter (`compiler/target/aarch64/win_frame`), and the COFF `IMAGE_FILE_MACHINE_ARM64` (`0xAA64`) object writer (`compiler/obj/coff_arm64`) in both `axiom0` and the self-hosted compiler.

## Scope

- Implement `compiler/abi/win_arm64` and `tests/selfhost/abi/win_arm64.ax`:
  - Lower parameters and returns per Windows ARM64 ABI: variadic arguments routed exclusively through GPRs `x0`–`x7` and stack, HFA/HVA classification on non-variadic calls, and `x18` pinned as non-allocatable TEB register.
- Implement `compiler/target/aarch64/win_frame`:
  - Emit `__chkstk` stack probe sequences loading `x15 = frame_bytes >> 4`, calling `bl __chkstk`, and subtracting `sp, sp, x15, lsl #4` for frames ≥ 4 KiB.
  - Emit Windows ARM64 `.pdata` (packed unwind for canonical frames, `.xdata` pointer otherwise) and `.xdata` unwind opcodes matching prologue/epilogue instructions in exact reverse order.
- Implement `compiler/obj/coff_arm64` and `tests/selfhost/obj/coff_arm64.ax`:
  - Emit COFF `0xAA64` object files with `IMAGE_REL_ARM64_BRANCH26`, `PAGEBASE_REL21`, `PAGEOFFSET_12A`, `PAGEOFFSET_12L`, `ADDR64`, `ADDR32NB`, and `SECREL` relocations.
- Add unit tests in `tests/obj/coff_arm64`.

## Acceptance
- [ ] `ctest --output-on-failure -R coff_arm64` passes.
- [ ] Generated COFF `0xAA64` objects and `.pdata`/`.xdata` unwind records pass structural inspection (`llvm-readobj --coff-directives --unwind` or internal validator).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T694-report.md` with exact `## Files changed`.

## Out of scope
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). All Axiom sources and test programs use canonical syntax (`axiom-syntax`): `=` only, `.` paths only, and `Xin ch?o th? gi?i` for greeting strings.

## Log
- 2026-11-03 08:50:00 created by T216 (P16 phase planning)
