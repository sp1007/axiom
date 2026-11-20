---
id: T820
title: Fix regression (fullrun-1 / T434) — formatter emits synthetic @derive ITEM_IMPL nodes after zero-length span attribution
phase: P19-developer-experience-tooling
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T434]
priority: 0
status: todo
attempts: 0
paths: [compiler/fmt/cst/mod.ax, tools/affected_map.txt, tests/run/fmt_engine, tests/run/fmt_cli, tests/conformance/p19/e19_2_formatter]
locks: [compiler/syntax/parse.ax]
spec: [spec/SPEC-61-reflection-derive.md, spec/SPEC-20-selfhost.md]
covers: [REQ-TST-072]
---
# T820 — Fix regression: formatter emits synthetic `@derive(...)` `ITEM_IMPL` nodes

## Why
Detected and bisected by periodic Tier-1 sweep `fullrun-1` (`_workspaces/reports/fullrun-1.md`, Regression Cluster A) on HEAD `0b9ff70a`:

3 failing test IDs outside `_workspaces/baseline-failures.txt`:
1. `run/fmt_engine/fmt_engine.test` (`probe[ex_fmt_01] exact_match=false idempotent=false`)
2. `run/fmt_cli/fmt_cli.test` (`probe[ast_verify] ok_exit=99 ast_equiv=false idempotent=false`)
3. `conformance/p19/e19_2_formatter/e19_2_formatter_oracle.test` (`all_idempotent=false`)

Culprit commit: `bda3bb63` (`T434`). Before `T434`, `parse_synthetic_item()` in `compiler/syntax/parse.ax` stamped synthetic `@derive(...)` `ITEM_IMPL` items with `FileId { v: 0u32 }` and offsets starting at `0`. `T434` changed `parse_synthetic_item()` to attribute them to `source_span.file.v` with a zero-length span (`sp.start == source_span.start`, `sp.end == source_span.start`). However, `cst_is_synthetic_item()` in `compiler/fmt/cst/mod.ax:535-548` still only checks `sp.file.v == 0u32` or `(!is_first && k == ITEM_IMPL && sp.start == 0u32)`, so synthetic `@derive(...)` impl items now leak into formatted output and break exact-match, idempotence, and AST equivalence.

## Scope
- Update `cst_is_synthetic_item()` in `compiler/fmt/cst/mod.ax` (and check any other callers/helpers in `compiler/fmt/` that filter synthetic `@derive` items) so zero-length-span synthetic `ITEM_IMPL` nodes produced by `parse_synthetic_item()` (`sp.start == sp.end`, or `sp.end <= sp.start`, while still handling legacy `sp.file.v == 0` / `sp.start == 0` cases safely) are recognized as synthetic and never emitted by the formatter.
- Verify no legitimate source `ITEM_IMPL` can have `sp.end <= sp.start` (a real `impl ... {}` always spans > 0 bytes), and verify `T434`'s AST/resolve/HIR dump behaviour (`tests/parse`, `tests/resolve`, `tests/hir`) remains completely intact.
- Add `tests/run/fmt_engine`, `tests/run/fmt_cli`, and `tests/conformance/p19/e19_2_formatter` to the `compiler/syntax` row in `tools/affected_map.txt` (and confirm `python tools/axtest_affected.py --check-map` passes) so future `compiler/syntax/parse.ax` edits catch formatter regressions during per-task gates.
- Add or verify a regression case in the formatter tests exercising `@derive(...)` formatting idempotence + AST equivalence (and confirming non-`@derive` `impl` items are still formatted normally).

## Acceptance
- [ ] `run/fmt_engine/fmt_engine.test`, `run/fmt_cli/fmt_cli.test`, and `conformance/p19/e19_2_formatter/e19_2_formatter_oracle.test` all PASS with `--no-cache`.
- [ ] `python tools/axtest_affected.py --check-map` prints `MAP-CHECK OK` (exit 0).
- [ ] Fresh bootstrap (`stage 2` / `stage 3`) fixed-point holds in `build-snap-T820`.
- [ ] `taskgate.py --task T820` exits 0 (`FAIL 0`, `BASELINE OK`, `WEAK-NATIVE 0` in own/changed tests, `archcheck` 0 violations).
- [ ] Report `_workspaces/reports/T820-report.md` with exact `## Files changed` and `STATUS: COMPLETE round=0`.

## Out of scope
- `bootstrap/axiom0` (frozen), `docs/`, reverting `T434`'s `FileId` attribution fix.

## Log
- 2026-11-20 created from fullrun-1 bisect (Cluster A, culprit bda3bb63 T434)
