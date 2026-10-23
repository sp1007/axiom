---
id: T159
title: AX0-FIX-08 MIR verifier missing-drop and double-drop checks on real bodies after drop elaboration (axiom0 + port)
phase: P10-selfhost
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T158]
priority: 0
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/verify, compiler/verify, tests/verify/drop, tests/selfhost]
locks: [bootstrap/axiom0/src/driver/pipeline.c, compiler/driver/pipeline.ax]
spec: [spec/SPEC-12-drop.md, spec/decisions/ADR-0036-assignment-drop-raw-store-cap-followups.md, spec/decisions/ADR-0034-oracle-independence.md, 0161, 0178]
covers: [REQ-VER-001, REQ-MIR-095]
timeout_min: 240
---
# T159 — AX0-FIX-08: verifier drop checks on real code

## Goal
The verifier's drop checks protect real programs, not only hand-written MIR text. After drop
elaboration, every function body of every program is checked: an owned place that needs drop and is
still initialised on some path to `Return` without a `Drop` is `AX_VERIFY_MISSING_DROP` (or the
existing code name), and a `Drop` of a place that is moved/dropped on some path is
`AX_VERIFY_DOUBLE_DROP` — for implicit (elaborated) drops as well as explicit ones, drop-flag aware.

Confirmed gap (T141 QA round 0 notes): in `bootstrap/axiom0/src/verify/verify.c` (~L385, L567, L621,
L642) and `compiler/verify/verifier.ax` the missing-drop check runs only when `func == NULL`
(MIR-text tests); it was effectively dead for real types even before T141. `AX_VERIFY_DOUBLE_DROP`
is limited to explicit drops (`term->drop.is_explicit`).

## Scope
- In both compilers, in lockstep: run the drop checks on elaborated bodies (the verifier pass that
  follows `ax_mir_drop_elaborate` / its port twin in the pipeline; add that invocation if it does not
  exist). Drop flags: a place guarded by a drop flag is "maybe initialised"; a conditional drop on
  its flag satisfies the missing-drop check and does not count as a double drop.
- Raw stores (SPEC-12 AXS-DROP-007) are not drops and not moves; `forget`, `drop_in_place` and
  moves into calls follow their SPEC-04 intrinsic meanings.
- If the check finds real leaks/double drops in the corpus, std or `compiler/`, do not suppress
  them: fix them if the cause is in drop elaboration of this task's paths, otherwise list each in the
  report's `## Follow-ups` and mark the test `xfail: <task>` only after the architect files it.

## Acceptance
- [ ] `tests/verify/drop/` (new, MIR-text and `.ax` programs through `inspect`/`build`):
      (a) a hand-built elaborated body with a missing drop on one branch → the missing-drop code;
      (b) a duplicated implicit `Drop` → `AX_VERIFY_DOUBLE_DROP`; (c) a drop-flag-guarded conditional
      drop → accepted; (d) a raw store over a moved place → accepted. Each negative case is shown to
      be produced by a real-body run, not only by the `func == NULL` path (a mutation in the report:
      re-adding `func == NULL` makes a test FAIL).
- [ ] Every `tests/run/**` and `tests/std/**` program and the axiomc bundle pass the check in both
      compilers (full suite green, no new diagnostics).
- [ ] axiomc_e2e: no REGRESSION; `known_divergent.txt` gains no entry.
- [ ] Full suite passes in `build-snap-T159` with native legs; build warning-free; archcheck clean;
      self-compile time of the axiomc bundle not more than 10% slower (numbers in the report).
- [ ] Report `_workspaces/reports/T159-report.md` with exact `## Files changed` and regenerated bundles.

## Out of scope
- Capability (view/region) verification of VCAP invariants (E13.1); MIR construction changes.

## Notes
- AX0-FIX chain: priority 0, runs alone; after T158.
- Build fresh in the snapshot; `build/axiom0.exe` in the main tree is stale.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
