---
id: T143
title: GNU-as encoder oracle widened to every isel-emitted form, with an Axiom twin against compiler/target/x64/encode.ax
phase: P10-selfhost
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: []
priority: 110
status: done
attempts: 1
paths: [tools/gen_encode_tests.py, tests/encode]
spec: [spec/decisions/ADR-0034-oracle-independence.md, 0163, tasks/0361]
covers: [REQ-TST-015, REQ-CORE-255]
timeout_min: 240
started: 2026-10-24 16:33:45
finished: 2026-10-25 05:27:54
---
# T143 — GNU-as encoder oracle widened, with an Axiom twin

## Goal
Every machine-instruction form that instruction selection can emit is checked byte-for-byte against
GNU `as`, both for axiom0's C encoder and for the ported `compiler/target/x64/encode.ax`, and the
Axiom check runs with axiomc at T086 (ADR-0034 §1, §3).

Audit OI-08: `tests/encode/encode_tests.inc` (135 vectors) covers 9 of the 81 entry points of
`bootstrap/axiom0/src/target/x64/encode/encode.h` (mov_rr, add_rr, mov_rm addressing, cdq/cqo, int3,
jmp8, ret); movabs, lea, shl/shr/sar, setcc, div/idiv, imul/mul, push/pop and jcc — all used by real
programs — are not vector-checked; `encode.test` is `requires: axiom0-internal`, so the oracle
vanishes at T086, and `tests/selfhost/encode/qa_encode_instructions.ax` partly uses axiom0 bytes.

## Scope
- Extend `tools/gen_encode_tests.py` (Python 3 stdlib + `as`/`objdump` at generation time) to every
  encoder entry point used by isel (list them from the emit calls of `isel.c`/`frame.c` and of
  `compiler/target/x64/isel.ax`/`frame.ax`; the report lists any of the 81 left out and why) ×
  registers rax..r15 at each legal width (8/16/32/64, incl. spl/bpl/sil/dil and r8b..r15b) ×
  addressing {base, base+disp8, base+disp32, SIB with each scale, rsp/r12 base, rbp/r13 base,
  rip-relative} × immediate boundaries {0, 127, 128, -128, -129, 2^31-1, -2^31, 64-bit for movabs};
  `div`/`idiv`/`mul`/`imul` both signednesses; `jcc`/`setcc` every condition code; `call`/`jmp`
  rel32. GNU `as` missing → generation fails; the committed tables are the oracle.
- The generator writes (a) the C table `tests/encode/encode_tests.inc` (existing C driver,
  `requires: axiom0-internal`) and (b) an Axiom test `tests/encode/axiom/gnu_as_vectors.ax` that embeds
  `compiler/target/x64/encode.ax` verbatim (or builds it as a module if the runner supports it) and
  checks every vector, printing `OK <count>`; no `requires: axiom0-internal`, `modes: interp native`.
- `python tools/gen_encode_tests.py check` regenerates into a temp dir and byte-compares;
  `tests/encode/encode_tables_current.test` runs it (so a change to `encode.ax` that is not
  re-embedded fails).

## Acceptance
- [ ] `tests/encode/encode.test` (C) and `tests/encode/axiom/gnu_as_vectors.ax` (Axiom, both modes)
      pass inside `build-snap-T143` with `--compiler build/axiom0.exe`; the report gives the vector
      count per entry point and the coverage (entry points covered / 81, isel-emitted covered / total
      — the latter must be 100%).
- [ ] `tests/encode/encode_tables_current.test` passes; editing one byte of an embedded table or of
      `compiler/target/x64/encode.ax` makes it FAIL (shown in the report).
- [ ] Any mismatch between GNU as and either encoder is listed in `## Follow-ups` with the instruction,
      expected and actual bytes (the architect files the AX0-FIX / port fix); such vectors are
      `xfail: <fix task>` in the table until fixed, never removed.
- [ ] Full suite passes in `build-snap-T143`.
- [ ] Report `_workspaces/reports/T143-report.md` with exact `## Files changed`.

## Out of scope
- Fixing encoder bugs in `bootstrap/` or `compiler/` (follow-ups); SSE/AVX forms (E12).

## Notes
- No shared paths with T085/T134; can run now. T086 depends on it.
- Build fresh in the snapshot; `build/axiom0.exe` in the main tree is stale.

## Log
- 2026-10-24 16:33:45 started (attempt 1) T143-impl
- 2026-10-25 05:27:54 accepted by QA -> done
