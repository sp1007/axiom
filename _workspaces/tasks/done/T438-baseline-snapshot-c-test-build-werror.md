---
id: T438
title: Baseline fix — C test binaries (ct_*) build in a fresh snapshot (clang -Werror in cdriver_abi_qa2.c)
phase: P11-concurrency-async
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: []
priority: 18
status: done
attempts: 1
paths: [tests/mc/isel/cdriver_abi_qa2.c, tests/mc/isel/cdriver_abi.c, tests/mc/isel/cdriver_abi_qa.c, tests/mc/isel/cdriver_abi_edge.c, tests/mc/frame/cdriver_probe.c, tests/mc/frame/cdriver_probe_edge.c]
locks: [_workspaces/baseline-failures.txt]
spec: [spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md, spec/decisions/ADR-0041-complete-suite-baseline-and-test-cache.md]
covers: [REQ-TST-015, REQ-TST-004]
started: 2026-11-13 16:42:55
finished: 2026-11-13 18:44:44
---
# T438 — Baseline fix: C test binaries build in a fresh snapshot

## Goal
`cmake --build` of a fresh `build-snap-<ID>` succeeds with clang, so the C test drivers `build/tests/ct_*` exist and
`encode/encode.test` and `link/link.test` run in every gate snapshot again (ADR-0042 §1).

## Scope
- Observed (T430-qa): the snapshot cmake build stops on `tests/mc/isel/cdriver_abi_qa2.c:19: unused variable 'sig'`
  under clang `-Werror`; `encode/encode.test` and `link/link.test` then fail with `cannot execute build/tests/ct_*`.
- Fix the C test source only (use or remove the variable; keep the test's checks). Do not change compiler flags,
  `CMakeLists.txt` or `bootstrap/axiom0` (frozen).
- Build every `ct_*` target in a fresh snapshot; if another C test source breaks the same build, list it in the report
  (it becomes a follow-up; fix it here only if it is the same one-line class and inside `tests/mc/isel`).
- Remove the two `T438` lines from `_workspaces/baseline-failures.txt`.

## Acceptance
- [ ] In a fresh `build-snap-T438`, the cmake build completes with clang and builds every `build/tests/ct_*` target
  (build log tail in the report).
- [ ] `encode/encode.test` and `link/link.test` pass in the snapshot; the `cdriver_abi_qa2` test still passes.
- [ ] Gate per axiom-qa.md "Per-task gate scope" (`tools/taskgate.py`); failing ids ⊆ baseline after the removals.
- [ ] Report `_workspaces/reports/T438-report.md` with exact `## Files changed`.

## Out of scope
- Compiler flags, CMake files, `bootstrap/axiom0`, `docs/`.

## Notes
- Only C test code changes; no Axiom source changes, so no selfhost bundle regeneration.

## Log
- 2026-11-13 created by axiom-architect (ADR-0042 §1, architect inbox 1)
- 2026-11-13 16:42:55 started (attempt 1) T438-impl
- 2026-11-13 18:44:44 accepted by QA -> done
