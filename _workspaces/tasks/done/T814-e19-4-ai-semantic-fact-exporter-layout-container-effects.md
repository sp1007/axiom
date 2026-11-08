---
id: T814
title: E19.4 AI-agent semantic fact graph exporter, layout/container/std effect metadata inspector & .axmeta separation
phase: P19-developer-tooling
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T219, T752, T755, T756, T759, T813]
priority: 204
status: done
attempts: 1
paths: [compiler/ai_query, compiler/driver/query_cmd, std/meta_effects, tests/run/ai_query]
spec: [spec/SPEC-103-diagnostics-ux-ai-interface.md, spec/SPEC-24-artifact-format-module-interfaces.md, 0101, 0129, 0146, tasks/0374, tasks/0421, tasks/0425, tasks/0444, tasks/0448, tasks/0456]
covers: [REQ-TOOL-004, REQ-TOOL-180, REQ-TOOL-181, REQ-TOOL-182, REQ-TOOL-185, REQ-TOOL-186, REQ-TOOL-187, REQ-TOOL-190]
started: 2026-11-08 17:13:29
finished: 2026-11-08 17:47:35
---
# T814 — E19.4 AI-agent semantic fact graph exporter, layout/container/std effect metadata inspector & .axmeta separation

## Goal
Implement the versioned machine-readable AI semantic fact graph exporter, CLI layout inspector (`axiomc inspect layout`), container & `std` effect metadata `.axmeta` exporter, and strict runtime artifact separation per `spec/SPEC-103-diagnostics-ux-ai-interface.md`.

## Scope
- Implement `axiomc inspect layout` (`0129 §61`, `REQ-TOOL-004`) and `axiomc query` in `compiler/ai_query` and `compiler/driver/query_cmd` to export versioned JSON semantic fact graphs (ownership lifecycles, capability borrows, trait resolution why/why-not chains, unsafe boundary map, and module dependency graph; `0101 §27-32`, `0146 §46-48, §57-63`, `REQ-TOOL-180`, `REQ-TOOL-185`) without running codegen.
- Export container semantic properties (`storage_kind`, `relocatable`, `address_stable`, `invalidation_rules` for `Vec`, `HashMap`, `Slice`, `String`; `tasks/0425`, `REQ-TOOL-181`) and `std` API effect metadata (`allocates`, `blocks`, `synchronizes`, `panics`, `unsafe_preconditions`; `std/meta_effects`, `tasks/0456`, `REQ-TOOL-190`) into `.axmeta` and `CompilerDB` queries.
- Enforce identical compiler safety verification on AI-submitted source/patch candidates (`REQ-TOOL-180`, `REQ-TOOL-186`) and verify that `.axmeta`, `.axdb`, and debug metadata are excluded from production executable runtime requirements (`REQ-TOOL-182`, `REQ-TOOL-187`).

## Acceptance
- [ ] Run tests in `tests/run/ai_query` verify `axiomc inspect layout` (size, alignment, field offsets), `axiomc query` JSON fact graphs, `.axmeta` container and `std` effect metadata queries, rejection of unsafe AI patches by the compiler verifier, and absence of `.axmeta`/`.axdb` sections in production executables.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T814-report.md` with exact `## Files changed`.

## Out of scope
- Documentation generator and test runner UX (`T816`–`T819`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P19 (`P19-developer-tooling`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T814/build` and `python tools/axtest.py --compiler build-snap-T814/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 09:50:00 created by T219 (P19 phase planning)
- 2026-11-08 17:13:29 started (attempt 1) T814-impl
- 2026-11-08 17:47:35 accepted by QA -> done
