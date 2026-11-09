---
id: T317
title: Phase P17 gate — Debugging & runtime introspection
phase: P17-debugging-runtime-introspectio
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T217, T316, T068, T700, T701, T702, T703, T704, T705, T706, T707, T708, T709, T710, T711, T712, T713, T714, T715, T716, T717, T718, T719, T720, T721, T722, T723, T724, T725, T726, T727, T728, T729, T730, T731, T732, T733, T734]
priority: 317
status: todo
attempts: 0
paths: [tests/conformance/p17, _workspaces/reports/phase-P17-review.md]
spec: [spec/ROADMAP.md, spec/SPEC-92-debug-ir-codeview-pdb.md, spec/SPEC-93-dwarf-elf-macho.md, spec/SPEC-94-unwinding-backtraces.md, spec/SPEC-95-debugger-contract-symbolication.md, spec/SPEC-96-profiler-performance-introspection.md, spec/SPEC-97-sanitizers-runtime-verification.md, spec/SPEC-98-trace-replay.md]
covers: [REQ-DBG-116, REQ-DBG-117]
---
# T317 — Phase P17 gate: Debugging & runtime introspection

## Goal
Certify that phase P17 meets the exit criteria of every epic (`E17.1`–`E17.7`) in `spec/ROADMAP.md` §3 and that all requirements mapped to the phase are implemented.

## Scope
- Run the full suite on all targets supported at this point; run each epic's exit-criterion checks (`tests/conformance/p17/e17_1_codeview_pdb` through `tests/conformance/p17/e17_7_trace_replay`).
- `reqcov.py --phase P17-debugging-runtime-introspectio`: every requirement implemented or explicitly re-mapped (with note).
- Collect epic conformance results into `tests/conformance/p17` (index + missing cases added).
- Ask axiom-architect (via report Follow-ups) for the phase review items: spec drift, shortcuts to retire.

## Acceptance
- [ ] Every epic exit criterion (`E17.1`–`E17.7`, including step-through debugging in a standard debugger on Windows and Linux and the full sanitizer suite) demonstrated with commands and results in the QA report.
- [ ] Full suite green (gate rule: PASS or BLOCKED; only `xfail` entries for spec gaps with an ADR may remain); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T317-report.md` with exact `## Files changed`.

## Out of scope
- New features; fixes go to new tasks created by the architect.

## Notes
- Depends on the planning task T217, the P16 gate T316, pre-seeded task T068, and every P17 task T700–T726.

## Log
- 2026-10-06 02:23:56 covers += REQ-DBG-116, REQ-DBG-117 (metadata only)
- 2026-11-03 09:25:00 updated by T217 (added T316, T068, T700–T726 dependencies and SPEC-92..SPEC-98 spec refs)
