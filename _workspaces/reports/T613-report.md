# T613 Report — E15.4 — Canonical inlining, specialization, devirtualization & SROA specification (SPEC-73)

## Summary
- Consolidated the canonical specification for interprocedural call-graph (`CallGraph` / Tarjan `SCC`) analysis, compiler-derived function summaries (`EffectSummary`, `EscapeSummary`, `AliasSummary`), ownership-aware copy/move propagation, Scalar Replacement of Aggregates (`SROA`), caller return-slot construction (`RVO`/`NRVO`), function and closure inlining, call-site and generic specialization, `dyn Trait` and function-pointer devirtualization, and tail-call optimization (`@tailcall` and opportunistic TCO) into `spec/SPEC-73-inlining-specialization-devirt.md`.
- Added Vietnamese `## Tóm tắt` section, numbered `AXS-INL-001..035` rules, positive and negative canonical Axiom examples (`=` and `.` syntax), a complete requirement traceability matrix (`REQ-OPT-002..007`, `REQ-OPT-009`, `REQ-OPT-066..086`, and downstream `T064`/`T614`/`T615` requirements `REQ-TYP-001..006`, `REQ-OPT-087..124`, `REQ-OPT-315..318`), and source citations.
- Updated `spec/INDEX.md` (§2 document table, §4 `AXS-INL-NNN` namespace, §5 topic table), `spec/diagnostics.md` (`AXD-042` and `Sources`), and `spec/invariants.md` (`INV-PIPE-011` and `Sources`).

## Verification
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `COVERAGE OK` (`gaps: 0`)
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`
- `python tools/gatecheck.py --no-run`: `GATECHECK OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T613`: `0 REFUSED`

## Files changed
- `spec/SPEC-73-inlining-specialization-devirt.md`
- `spec/INDEX.md`
- `spec/diagnostics.md`
- `spec/invariants.md`

STATUS: COMPLETE
