---
id: T060
title: Modules & packages: multi-file, visibility, use, re-exports, prelude module
phase: P7-abstraction
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T044]
priority: 66
status: doing
attempts: 1
paths: [bootstrap/axiom0/src/resolve, bootstrap/axiom0/src/source, bootstrap/axiom0/src/driver, bootstrap/axiom0/src/hir, bootstrap/axiom0/src/types, tests/modules, tests/ui/modules, std/core/prelude.ax, std/README.md]
locks: [bootstrap/axiom0/src/diag/codes/NAME.def, bootstrap/axiom0/src/diag/codes/DRIVER.def]
spec: [0103, 0108, tasks/0357, tasks/0306, 0141, 0168, 0047]
started: 2026-10-10 13:54:31
agent: T060-impl
---
# T060 — Modules & packages: multi-file, visibility, use, re-exports, prelude module

## Goal
Real module system with dotted paths.

## Scope
- `module a.b` declarations and file→module mapping, package root and the minimal manifest `axiom.toml` (ADR-0006 §7: `[package] name`, `version`, `kind`; files under `src/` map to modules), `use` groups/aliases/re-exports, visibility pub/pub(package)/pub(module)/private enforcement, cycles handling.
- **Std root discovery** (ADR-0006 §8): `--std-root <dir>`, then `AXIOM_STD`, then `<exe dir>/../std`, then `<exe dir>/std`; otherwise AX_DRIVER_NO_STD. Absolute paths never reach an artifact or `--json` output (paths are package-relative or `<std>/…`).
- **Prelude mechanism**: the module `std.core.prelude` is loaded from the std root and imported implicitly. This task creates `std/core/prelude.ax` with the mechanism test only — Option/Result stay built-in until T054b moves them into std.
- Module-path naming hook for symbols (consumed by the mangling of T054b); HIR and type-checker changes for cross-module item lookup and visibility.

## Acceptance
- [ ] Multi-file test projects under tests/modules; ui tests for privacy and unresolved imports.
- [ ] Project tests (directory + `axiom.toml`, runner kind from T005) under tests/modules, in both modes.
- [ ] Std root tests: flag, environment variable, exe-relative default, and the missing-std diagnostic.
- [ ] Reproducibility: the same project built from two different directories gives byte-identical `--emit=obj` output and identical `--json` diagnostics.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T060-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Opens after the P5 gate and runs in parallel with P6 (ADR-0005 §13, ROADMAP R8): it needs no ownership feature, and the std chain (T065 → T070 → …) must not queue behind the P7 semantic chain.
- The manifest and std-root rules are decided (ADR-0006); nothing here needs an architect decision.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-10 13:54:31 started (attempt 1) T060-impl
