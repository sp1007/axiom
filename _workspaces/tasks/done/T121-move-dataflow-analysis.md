---
id: T121
title: Move dataflow analysis (use-after-move, partial moves) (T046 split)
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T120, T122]
priority: 66
status: done
attempts: 1
paths: [bootstrap/axiom0/src/own, tests/ui/own, tests/run/own, bootstrap/axiom0/src/driver/pipeline.c, tools/archcheck_rules.txt, tests/run/pattern/enum_struct_if_let.ax, spec/decisions/ADR-0022-allow-own-depend-on-mir.md]
locks: []
spec: [spec/SPEC-10-ownership.md, spec/decisions/ADR-0019-split-t046-move-analysis.md, spec/decisions/ADR-0020-rescope-t121-paths.md, spec/decisions/ADR-0022-allow-own-depend-on-mir.md]
started: 2026-10-10 17:55:39
unblocks: 0
unblock_failures: 0
finished: 2026-10-10 18:08:14
---
# T121 — Move dataflow analysis (use-after-move, partial moves) (T046 split)

## Goal
Ownership dataflow over MIR places.

## Scope
- Dataflow of UNINIT/OWNED/PARTIAL/MOVED per place.
- Diagnostics AX_MOVE_USE_AFTER_MOVE (with 'moved here' label), partial-move rules, moves in loops/branches.

## Acceptance
- [ ] Every SPEC-10 test-matrix row tagged T121 has passing positive + negative tests. Run tests carry `// native-after: T051` (removed by T051).
- [ ] Full test suite passes; build warning-free; archcheck clean.

## Log
- 2026-10-10 16:04:12 started (attempt 1) T121-impl
- 2026-10-10 16:08:02 block: Needs to modify bootstrap/axiom0/src/driver/pipeline.c but it is not in paths
- 2026-10-10 16:10:03 unblocked (cycle 1) 
- 2026-10-10 16:11:06 started (attempt 1) T121-impl
- 2026-10-10 16:30:01 block: MIR lacks location tracking (AxLocation) for statements/operands for diagnostics
- 2026-10-10 16:31:33 unblocked (cycle 2) 
- 2026-10-10 17:22:36 started (attempt 1) T121-impl
- 2026-10-10 17:53:09 block: Requires an ADR and path rescope for archcheck_rules.txt and enum_struct_if_let.ax
- 2026-10-10 17:53:14 parked: unblock cap reached (unblocks=2, failed unblock agents=0); needs the owner
- 2026-10-10 17:55:00 unblocked (owner-approved cycle 0) 
- 2026-10-10 17:55:39 started (attempt 1) T121-impl
- 2026-10-10 18:08:14 accepted by QA -> done
