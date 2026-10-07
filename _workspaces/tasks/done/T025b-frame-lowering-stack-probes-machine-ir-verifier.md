---
id: T025b
title: Frame lowering, stack probes, machine-IR verifier, `--emit=mc`
phase: P4-native
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T025]
priority: 43
status: done
attempts: 1
paths: [bootstrap/axiom0/src/target/x64/frame, bootstrap/axiom0/src/target/x64/verify, tests/mc/frame, bootstrap/axiom0/src/driver/emit_mc.c]
spec: [0181, 0188, 0189, 0183, 0251, 0253, spec/decisions/ADR-0003-backend-pipeline-robustness.md]
covers: []
started: 2026-10-08 00:07:58
finished: 2026-10-08 00:35:55
---
# T025b — Frame lowering, stack probes, machine-IR verifier, `--emit=mc`

## Goal
Turn the machine IR of T025 into encoded functions that are safe on Windows: correct frames, page-by-page stack probing for large frames, and a verifier that turns an illegal instruction form into an ICE instead of a crashing executable (ADR-0003).

## Scope
- Frame lowering: slot offsets, prologue/epilogue (`push rbp; mov rbp, rsp; sub rsp, N`), shadow space and outgoing-argument area, 16-byte alignment, callee-saved registers the function uses.
- **Stack probes (ADR-0003 C1):** a frame larger than 4096 bytes gets an inline loop that touches each page from the top of the new frame downward before the final `sub rsp` (no CRT `__chkstk`, 0188 §12).
- **Machine-IR verifier (ADR-0003 B2, 0181 §31):** operand-form legality against the encoder tables, register classes, 16-byte alignment at every call site, shadow space present, frame-size consistency. Runs before the encoder in every build used by tools/axtest.py and CI; a violation is an ICE.
- Encode functions through the T024 encoder into the object model; emitter `src/driver/emit_mc.c`: `--emit=mc` (final instructions + hex bytes).

## Acceptance
- [ ] `mc` golden tests; encoded bytes of `fn main() -> i32 { return 42 }` match the expectation.
- [ ] Probe test through a C driver (`tests/mc/frame/cdriver_probe.c`): a function with a 64 KB frame emits the probe loop, and the disassembly touches every page in order; a 4000-byte frame emits none.
- [ ] Verifier negative unit tests: illegal operand form, misaligned call site, missing shadow space, wrong register class → ICE with the rule name.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T025b-report.md` with exact `## Files changed`.

## Out of scope
- Linear-scan register allocation (E15.8, after T087 — ROADMAP R7); unwind tables (E17.3); the round-trip decoder check (later).
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- New instruction forms are added to the encoder only with GNU-as validation tables (T024 method).
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-08 00:07:58 started (attempt 1) T025b-impl
- 2026-10-08 00:35:55 accepted by QA -> done
