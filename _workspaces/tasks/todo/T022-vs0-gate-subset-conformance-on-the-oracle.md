---
id: T022
title: VS0 gate: subset conformance on the oracle
phase: P3-semantic-core
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T021, T016, T006, T013, T015b, T114, T115, T116, T117]
priority: 35
status: todo
attempts: 0
paths: [tests/conformance/vs0, tools/ci.sh, tools/ci.ps1, tools/gatecheck.py, tools/tests/gatecheck]
spec: [0263, 0114, 0017]
started: 2026-10-06 23:18:07
unblocks: 1
---
# T022 — VS0 gate: subset conformance on the oracle

## Goal
Prove the whole front half works end-to-end before any native code exists.

## Scope
- Port the 0263 first-test set and applicable 0114 E2E cases into tests/conformance/vs0 (canonical syntax).
- Seam review: parser↔HIR↔THIR↔MIR exhaustiveness (every node kind lowered or diagnosed).
- `tools/gatecheck.py` (Python standard library; ADR-0005 §3, 0264 §19-24): (a) every invariant in spec/invariants.md names an existing test directory or tool in its `verify:` field; (b) every milestone block of SPEC-00 up to the current gate lists existing tests and they pass; (c) every `xfail:` / `native-after:` directive names a board task that exists and is not done; (d) in `spec/selfhost-subset.tsv` each delivering task is an ancestor of its first consumer. Self-tests under tools/tests/gatecheck.

## Acceptance
- [ ] All VS0 tests pass in interp mode; seam review written in the QA report; every gap is fixed, or is an XFAIL with an ADR and a task.
- [ ] Gate rule (ADR-0005 §3): PASS or BLOCKED. Every non-passing test is an `xfail: <task-id>` for a spec gap that has an ADR; implementation bugs are fixed (their fix task done) before the gate closes; XPASS counts as a failure.
- [ ] `python tools/gatecheck.py`, `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T022-report.md` with exact `## Files changed`.
- [ ] `tools/ci.ps1` runs gatecheck with `--compiler` and the gatecheck self-tests, aligned with `tools/ci.sh`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Waits for T006 (archcheck), T013 (fuzz) and T015b (rest of the grammar in HIR), so the P2 work is closed by this gate.
- Unblock 2026-10-06 (ADR-0016): the implementation bugs found by attempt 1 are fixed by T114 (parser), T115 (typeck/driver), T116 (MIR builder) and T117 (interpreter); T022 depends on them. The suite delivered in attempt 1 stays as is (no relaxed expectations); after the fixes re-run `gatecheck --gate T022`. Rule (d) violation fixed on the board (T069 depends on T061).
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-06 15:21:15 started (attempt 1) T022-impl
- 2026-10-06 15:22:36 requeue: user requested stop (not charged: attempt refunded)
- 2026-10-06 23:18:07 started (attempt 1) T022-impl
- 2026-10-06 23:39:49 block: VS0 gate: impl bugs outside T022 paths (parser precedence/headers, typeck/driver, MIR builder ~/asserts, interp int32/bitwise/panic) + selfhost-subset.tsv rule (d): T061 not ancestor of T069
- 2026-10-06 23:43:46 unblocked (cycle 1) 
