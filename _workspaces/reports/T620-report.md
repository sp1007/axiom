# T620 Report — E15.6 — Canonical LTO, whole-program optimization, section GC & PGO specification (SPEC-75)

## Summary
- Consolidated the canonical specification for Link-Time Optimization (`LTO`), whole-program closed-world reachability (`WPO`), non-exported symbol internalization, cross-module `OptIR` summaries (`.axmeta`), cross-module inlining/constant propagation/escape/alias/devirtualization, generic instance deduplication (`ALTO-30..33`), linker section garbage collection (`COMDAT` / mark-sweep dead code and data stripping), safe Identical Code Folding (`ICF`) respecting observable function-pointer identity, and deterministic Ahead-of-Time Profile-Guided Optimization (`--pgo-gen` / `--pgo-use`) into `spec/SPEC-75-lto-wpo-section-gc-pgo.md`.
- Added Vietnamese `## Tóm tắt` section, numbered `AXS-LTO-001..030` and `AXS-PGO-001..015` rules, positive and negative canonical Axiom examples (`=` and `.` syntax), a complete requirement traceability matrix (`REQ-OPT-223..235`, `REQ-OPT-257..270`, `REQ-OPT-319..320`, and downstream `T621`–`T626` requirements `REQ-OPT-236..256`, `REQ-OPT-271..294`, `REQ-OPT-375..384`), and source citations.
- Updated `spec/INDEX.md` (§2 document table, §4 `AXS-LTO-NNN` and `AXS-PGO-NNN` namespaces, §5 topic table), `spec/diagnostics.md` (`AXD-042` and `Sources`), and `spec/invariants.md` (`INV-PIPE-012` and `Sources`).

## Verification
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `COVERAGE OK` (`gaps: 0`)
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`
- `python tools/gatecheck.py --no-run`: `GATECHECK OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T620`: `0 REFUSED`

## Files changed
- `spec/SPEC-75-lto-wpo-section-gc-pgo.md`
- `spec/INDEX.md`
- `spec/diagnostics.md`
- `spec/invariants.md`

## Status
STATUS: COMPLETE
