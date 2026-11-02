# T624 Report — E15.7 — Canonical performance contract, benchmark suite & compile-time/code-size budget specification (SPEC-76)

## Summary
- Consolidated the canonical specification for Axiom's execution semantics and runtime performance contract (`Defined` vs. `Panic`/`Trap` vs. `InvalidUnsafe`, zero safe UB, safety without mandatory runtime overhead, cross-profile semantic equivalence), optimization profiles (`-O0`, `-O1`, `-O2`, `-Os`, `-Oz`), three-dimensional binary footprint metrics (`FileSize`, `MappedSize`, `WorkingSet`), binary layout for startup/I-cache/page locality, `--time-passes` and `--size-report` telemetry schemas, the canonical benchmark suite (`tools/bench`), and CI regression budgets (`tools/perf.py --check-budgets`) into `spec/SPEC-76-performance-contract.md`.
- Added Vietnamese `## Tóm tắt` section, numbered `AXS-PERF-001..044` rules, positive and negative canonical Axiom examples (`=` and `.` syntax), a complete requirement traceability matrix (`REQ-OPT-292..295`, `REQ-OPT-334`, `REQ-OPT-381`, `REQ-OPT-382`, and downstream `T625`/`T626` requirements `REQ-OPT-242..245`, `REQ-OPT-251..256`), and source citations.
- Updated `spec/INDEX.md` (§2 document table, §4 `AXS-PERF-NNN` namespace, §5 topic table), `spec/diagnostics.md` (`AXD-042` and `Sources`), and `spec/invariants.md` (`INV-PIPE-013` and `Sources`).

## Verification
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `COVERAGE OK` (`gaps: 0`)
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`
- `python tools/gatecheck.py --no-run`: `GATECHECK OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T624`: `0 REFUSED`

## Files changed
- `spec/SPEC-76-performance-contract.md`
- `spec/INDEX.md`
- `spec/diagnostics.md`
- `spec/invariants.md`

## Status
STATUS: COMPLETE
