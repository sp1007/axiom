---
id: T146
title: AX0-FIX-04 statement terminator (AXS-GRM-011) enforced - parser no longer drops the rest of a line (axiom0 + port)
phase: P10-selfhost
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: opus
depends: [T085, T141]
priority: 0
status: done
attempts: 1
paths: [bootstrap/axiom0/src/syntax, compiler, std, tests]
spec: [spec/SPEC-02-grammar.md, spec/decisions/ADR-0034-oracle-independence.md, tasks/0476]
covers: [REQ-GRM-148]
timeout_min: 240
started: 2026-10-23 18:54:46
finished: 2026-10-24 00:56:32
---
# T146 — AX0-FIX-04: statement terminator enforced

## Goal
A statement that is not followed by `;`, a line break, `}` or EOF is rejected with
`AX_PARSE_EXPECTED_TERMINATOR` (SPEC-02 AXS-GRM-011), in axiom0 and in the port
`compiler/syntax/parse.ax`; the parser never silently discards tokens (ADR-0034 §2 lockstep rule).

Confirmed defect (architect probe 2026-10-20, from the audit's cross-lens note):
`fn f(c: bool) -> i32 { if c { return 5; } return 6; }` parses as if `return 6;` did not exist
(`inspect --emit=ast` shows only the `if`) and fails later with `AX_TYPE_RETURN`;
`let a = 1 let b = 2` on one line silently drops `let b = 2` (then `AX_NAME_UNRESOLVED` on `b`).
`AX_PARSE_EXPECTED_TERMINATOR` exists in `diag/codes/PARSE.def` but no parser emits it. A program
whose dropped tail still type-checks is miscompiled without any diagnostic.

## Scope
- axiom0 `bootstrap/axiom0/src/syntax/parse.c` and port `compiler/syntax/parse.ax`: after every
  statement, item and trait/impl/extern member, require `Term` per AXS-GRM-010/011 (block-like
  expression statements included — SPEC-02 has no exemption for them); on failure report
  `AX_PARSE_EXPECTED_TERMINATOR` at the next token and recover by continuing to parse it as the next
  statement (no token is skipped silently).
- Sweep: build every source under `std/`, `compiler/` and `tests/` with the fixed parser. Each source
  that now fails had code silently dropped: fix it by inserting a line break or `;`, and record in
  the report each place where the dropped code changes behaviour (that is a latent bug; expected
  outputs that change are re-derived by hand, not re-captured). Selfhost bundles embedding changed
  `compiler/` code are regenerated with their generators.
- ui tests `tests/ui/parse/terminator_*.ax`: two statements on one line, `if {...} stmt` on one line,
  `loop {...} stmt`, `match`, items on one line, and the accepted forms (`;`, line break, `}`).

## Acceptance
- [ ] `tests/ui/parse/terminator_*.ax` pass with `AX_PARSE_EXPECTED_TERMINATOR` at the right span;
      the accepted forms compile and run (a run test shows `if c { return 5; }; return 6;` returns 6
      for `c == false`).
- [ ] A selfhost test built from the real `compiler/syntax/parse.ax` reports the same diagnostic for
      the same inputs (ADR-0034 §2).
- [ ] The sweep result is in the report: number of sources changed per directory and every
      behaviour-changing site.
- [ ] Full suite passes in `build-snap-T146` with native legs; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T146-report.md` with exact `## Files changed`.

## Out of scope
- Any other grammar change; formatter behaviour (E19).

## Notes
- Gates T086 (ADR-0034 §5): silently dropped code in `compiler/` or `std/` would make axiomc wrong in
  a way no differential check sees (axiom0 and the port share the parser design).
- Broad paths (all of `tests/`): runs after T085 and T141 (last writers of `compiler/` and `std/` before T086);
  priority 0 runs alone. T144 and T145 run after it.
- Build fresh in the snapshot; `build/axiom0.exe` in the main tree is stale.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
- Parity registry (ADR-0035 §4, added 2026-10-20): the full suite runs `tests/selfhost/obj_link_driver/axiomc_e2e.test`,
  which fails on XPASS/IMPROVED. Remove (by explicit line deletion) every `known_divergent.txt` entry this task makes
  identical, update in place an entry that only improves, list the paths in the report; never add an entry (a newly
  divergent program is a regression of this task).

## Log
- 2026-10-23 18:54:46 started (attempt 1) T146-impl
- 2026-10-24 00:56:32 accepted by QA -> done
