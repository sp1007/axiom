---
id: T664a
title: E16.3 — AArch64 NEON (LirType.V128), ARM64 unsafe asm(...) & ARM64 PAC+BTI lowering
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T662, T663, T534]
priority: 108
status: todo
attempts: 0
paths: [compiler/target/aarch64, compiler/lir, tests/lir/aarch64_simd, tests/run/aarch64_asm]
spec: [spec/SPEC-83-aarch64-linux.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-TGT-155, REQ-TGT-157]
---
# T664a — E16.3 — AArch64 NEON (LirType.V128), ARM64 unsafe asm(...) & ARM64 PAC+BTI lowering

## Goal
Implement AArch64 NEON vector instruction lowering for `LirType.V128`, ARM64 register constraints for `unsafe asm(...)`, and ARM64 Pointer Authentication (PAC) + Branch Target Identification (BTI) binary hardening.

## Scope
- In `compiler/target/aarch64`, lower `LirType.V128` vector arithmetic, bitwise, load/store, and permute operations to AArch64 NEON instructions (`V0..V31`, `LD1`, `ST1`, `FADD`, `FMUL`, `ADD`, `SUB`, `DUP`, `ZIP1/2`, `EXT`).
- Implement ARM64 `unsafe asm(...)` support in `compiler/lir` and `compiler/target/aarch64` parsing standard ARM64 register constraints (`x0..x30`, `w0..w30`, `v0..v31`, `sp`, `memory`, `cc`), validating clobbers and rejecting undefined registers.
- Under `--hardened` on AArch64 targets (`+pauth`, `+bti`), emit `BTI C` / `BTI J` landing pads at function entries and indirect branch targets, and emit `PACIASP` / `AUTIASP` key-A return-address signing in function prologues/epilogues to thwart ROP/JOP attacks.

## Acceptance
- [ ] LIR and machine-code tests in `tests/lir/aarch64_simd` verify NEON `V128` instruction selection and encoding.
- [ ] Run tests in `tests/run/aarch64_asm` verify ARM64 `unsafe asm(...)` evaluation and PAC/BTI sequence validity under `--hardened` (disassembly checked or run via `qemu-aarch64`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T664a-report.md` with exact `## Files changed`.

## Out of scope
- SVE/SVE2 scalable vectors (reserved for post-v1).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`), depends on P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T664a/build` and `python tools/axtest.py --compiler build-snap-T664a/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:10:00 created by axiom-architect (ADR-0039 P16 AArch64 NEON/PAC/BTI expansion)
