---
id: T063
title: E15.8 — Linear-scan register allocation, spill/reload & callee-saved frame integration
phase: P15-optimizer-2-0
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T215, T627]
priority: 90
status: doing
attempts: 1
paths: [compiler/target/x64, compiler/driver, tests/mc/regalloc, tests/selfhost, tests/perf]
spec: [spec/SPEC-77-regalloc-machine-opt.md, 0182, 0235, 0252, tasks/0406, tasks/0557]
covers: [REQ-OPT-203, REQ-OPT-204, REQ-OPT-212, REQ-OPT-218]
started: 2026-11-03 03:25:30
---
# T063 — E15.8 — Linear-scan register allocation, spill/reload & callee-saved frame integration

## Goal
Replace the fixed-register stack-slot baseline at `-O1`/`-O2` with linear-scan register allocation, move coalescing, spill/reload insertion, and callee-saved register frame integration in `compiler/target/x64` per `spec/SPEC-77-regalloc-machine-opt.md`.

## Scope
- Implement backward CFG liveness analysis and deterministic live-interval construction in `compiler/target/x64` (`REQ-OPT-203`, `REQ-OPT-204`, `REQ-OPT-218`).
- Implement linear-scan register allocation across ABI-driven register classes (`Gpr` and `Xmm`/`Vec` when present), honoring fixed-register operand constraints (`rcx` shifts, `rax`/`rdx` div/mul), call clobber masks, and loop-depth-weighted spill heuristics (`REQ-OPT-212`); keep the fast baseline allocator at `-O0`.
- Implement copy coalescing, stack spill-slot allocation/reuse, reload/spill code insertion, and `FrameLayout` prologue/epilogue callee-saved register save/restore verified by the Machine IR verifier.

## Acceptance
- [ ] Machine IR and differential run tests in `tests/mc/regalloc` verify register allocation under high register pressure, call clobbers, fixed-register instructions, and callee-saved preservation across `-O0`, `-O1`, and `-O2`; code-size and self-compile speedup recorded via `tools/perf.py`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T063-report.md` with exact `## Files changed`.

## Out of scope
- Pattern-matching instruction selection, branchless if-conversion, and post-RA peephole optimizations (`T628`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Paths re-pathed to canonical `compiler/<module>` layout by T076 (ADR-0005 §8, SPEC-20 §8).
- Roadmap epic E15.8 (moved out of the C core by ROADMAP R7: not needed for self-hosting). Implemented in `compiler/` (Axiom) after T087; refined by T215 so `T063` implements linear-scan register allocation while `T628` implements better instruction selection and post-RA machine peephole optimization.
- First implementation task of P15: improves the speed of code produced by `axiomc` itself.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T063/build` and `python tools/axtest.py --compiler build-snap-T063/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 02:44:30 refined scope, covers, and dependencies in T215 (P15 phase planning)
- 2026-11-03 03:25:30 started (attempt 1) 
