---
id: T486
title: Perf — the `build` phase (MIR build → LIR → isel/regalloc → encode → object/link) takes 286 s of a 464 s compile; profile and fix with byte-identical output
phase: P12-numeric-floating-point-simd
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T164]
priority: 10
status: done
attempts: 1
timeout_min: 900
paths: [compiler/backend, compiler/target/x64, compiler/objmodel, compiler/obj, compiler/link, tests/perf/build_scaling, tests/selfhost/link/qa_pe_headers_and_imports.ax.in]
locks: [compiler/lir/builder.ax, compiler/mir/builder.ax, compiler/abi, compiler/driver/pipeline.ax]
spec: [spec/SPEC-76-performance-contract.md, spec/SPEC-20-selfhost.md]
covers: [REQ-OPT-292]
started: 2026-11-19 09:33:02
finished: 2026-11-19 18:40:05
---
# T486 — Perf: make the `build` phase scale linearly

## Why (owner request 2026-11-17)
Same measurement as T485 (`build/axiomc2.exe build --time-passes tests/selfhost/backend/qa_backend_unit.ax`, ~95k lines):
**build 286.5 s** of 464 s total, while lex+parse+resolve take 3 s and the exe runs in 0.1 s. Native and native-O1
legs of the 179 selfhost ids cost 8 h of the 10.6 h serial suite; nearly all of it is this phase.

## Scope
- First split the time: add sub-timers under `--time-passes` for the parts of `build` (MIR construction, MIR opt at
  -O1, LIR lowering, ABI lowering, isel, frame/regalloc, verify, encode, object model, linker/PE write) — keep the
  existing top-level lines unchanged so tools that parse them still work. Record the split in the report.
- Fix the dominant superlinear parts (typical culprits: per-function work that scans all functions/symbols/strings,
  linear symbol or relocation lookup, section buffers grown by small steps, rdata/string dedup by linear search,
  repeated whole-program walks per function). Algorithmic changes only.
- Parts outside this task's `paths` that turn out to dominate (e.g. `compiler/mir/builder.ax`,
  `compiler/lir/builder.ax`): fix them if the change is local; otherwise report the measurement and let the architect
  create the follow-up.
- Add `tests/perf/build_scaling`: generated input at N and 4N; the build-phase time ratio stays ≤ ~5 (generous,
  single run).

## Acceptance (quality guards — mandatory, this is a compiler)
- **Byte-identical output**: every `tests/selfhost/**` bundle and every `tests/run/**` program produces byte-identical
  `.exe` at O0 and O1 before/after (deterministic output, SPEC-76 `INV-DET-004`); script + summary in the report.
- Normal gate (encode/obj/link/run suites unchanged); self-host fixpoint holds.
- Report before/after times for at least 3 large bundles; target: build phase ≥ 5× faster on `qa_backend_unit.ax`.

## Log
- 2026-11-19 03:36:56 started (attempt 1) T486-impl
- 2026-11-19 04:29:26 requeue: restart (not charged: attempt refunded)
- 2026-11-19 06:56:11 started (attempt 1) T486-impl
- 2026-11-19 08:46:11 requeue: RESOURCE_EXHAUSTED (code 429): Individual quota reached. Resets in 43m6s. (infrastructure failure: attempt refunded)
- 2026-11-19 09:33:02 started (attempt 1) T486-impl
- 2026-11-19 13:45 orchestrator: paths += tests/selfhost/link/qa_pe_headers_and_imports.ax.in (new LinkerContext.gindex field breaks its 5 exhaustive struct literals; mechanical fix, no other running task owns the file)
- 2026-11-19 18:40:05 accepted by QA -> done
