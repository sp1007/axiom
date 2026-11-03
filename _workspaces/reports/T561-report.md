# T561 Report — E14.3 — Canonical generators, yield suspension, iterator state machines & MIR verification specification (SPEC-62)

## Summary

Authored `spec/SPEC-62-generators.md` (`AXS-GEN-001`..`024`, `AXS-GEN-050`..`052`) defining the canonical language and MIR semantics for synchronous generators (`gen fn`, `yield`), zero-heap pull-based iterator state machines, `LiveAcrossYield` ownership and capability rules (`AX_GEN_YIELD_OUTSIDE_GEN`, `AX_GEN_SELF_BORROW_ACROSS_YIELD`, `AX_GEN_VIEW_ACROSS_YIELD`, `AX_GEN_RETURN_VALUE`, `AX_GEN_RECURSIVE`, `AX_GEN_GPU_FORBIDDEN`), HIR → MIR structural and semantic preservation invariants (`REQ-CORE-2989`..`2998`, `AMIR-20..60`), terminal completion (`STATE_COMPLETE = u32.MAX`), deterministic per-state `Drop` cleanup, and `for-in` / `std.iter` lazy combinator integration (`AGEN-20..140`). Updated `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md` (`INV-GEN-001`..`004`).

## Files changed

- `spec/SPEC-62-generators.md`
- `spec/INDEX.md`
- `spec/diagnostics.md`
- `spec/invariants.md`

## Verification

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `COVERAGE OK` (0 gaps).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
- `python tools/gatecheck.py --no-run`: `GATECHECK OK`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T561`: 4 allowed files (`spec/SPEC-62-generators.md`, `spec/INDEX.md`, `spec/diagnostics.md`, `spec/invariants.md`), 0 `REFUSED` lines.

STATUS: COMPLETE round=0
