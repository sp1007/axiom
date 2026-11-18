---
id: T485
title: Perf — ownership/borrow analysis (`own` pass) is superlinear on large inputs (141 s of a 464 s compile); profile and fix with byte-identical output
phase: P12-numeric-floating-point-simd
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: opus
depends: []
priority: 15
status: done
attempts: 1
timeout_min: 900
paths: [compiler/own, tests/perf/own_scaling]
locks: [compiler/mir/builder.ax, compiler/types/typeck.ax]
spec: [spec/SPEC-76-performance-contract.md, spec/SPEC-20-selfhost.md, spec/SPEC-03-core-semantics.md]
covers: [REQ-OPT-292]
started: 2026-11-17 19:46:03
finished: 2026-11-18 11:56:02
---
# T485 — Perf: make the `own` pass scale linearly

## Why (owner request 2026-11-17)
Test/QA time grows with the code base. Measured 2026-11-17 on HEAD `56b7c63c` (`build/axiomc2.exe build --time-passes
tests/selfhost/backend/qa_backend_unit.ax`, ~95k lines): source 0.6 s, lex 0.9 s, parse 1.1 s, resolve 0.3 s, hir 0.4 s,
typeck 30.4 s, **own 141.5 s**, build 286.5 s; the produced exe runs in 0.1 s. The 179 `tests/selfhost/**` ids are 9.2 h of
the 10.6 h serial suite, and almost all of it is compiler time. Lex+parse+resolve of the same input take 3 s, so the
`own` pass (and typeck) are far from linear. Making the compiler fast is the only speed-up that costs no test coverage.

## Scope
- Profile the `own` pass on the largest selfhost bundles (sampling profiler on the native axiomc, or instrumented
  counters): find the superlinear parts (per-function work proportional to whole-file size, repeated scans of all
  locals/places/blocks, quadratic dataflow, linear lookups that should be hashed, re-allocation in loops, …).
- Fix the hot spots with algorithmic changes (worklists, bitsets, per-body indices, hashing). No semantic change:
  the same diagnostics in the same order, the same MIR/drop elaboration.
- Add `tests/perf/own_scaling`: a generated input at sizes N and 4N; the `own` time ratio must stay ≤ ~5 (linear
  with noise), checked with `--time-passes` (keep the test robust: generous bound, single run, skip on timeout).

## Acceptance (quality guards — mandatory, this is a compiler)
- **Byte-identical output**: for every `tests/selfhost/**` bundle and every `tests/run/**` program, the produced
  `.exe` (O0 and O1), and `--emit=mir` dumps, are byte-identical between the compiler before and after the change.
  Write the comparison script under `tests/perf/own_scaling/` and include its summary in the report.
- Diagnostics: `tests/ui/**` and `tests/conformance/**` outputs unchanged (normal gate).
- Self-host fixpoint still holds (stage-2 == stage-3 as in the existing selfhost check).
- Report before/after `--time-passes` for at least 3 large bundles; target: `own` ≥ 5× faster on
  `qa_backend_unit.ax`. If a target is not reached, explain what remains.

## Log
- 2026-11-17 19:46:03 started (attempt 1) T485-impl
- 2026-11-18 11:56:02 accepted by QA -> done
