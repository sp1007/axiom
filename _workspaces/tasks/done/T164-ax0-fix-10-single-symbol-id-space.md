---
id: T164
title: AX0-FIX-10 one symbol-id space — user/std/extern ids from a single counter, std/extern stored per symbol (axiom0 + port)
phase: P10-selfhost
owner: axiom-frontend
reviewer: axiom-qa
model: opus
gate_model: opus
depends: []
priority: 0
status: done
attempts: 1
timeout_min: 600
paths: [bootstrap/axiom0/src/resolve, compiler/resolve, compiler/hir/hir.ax, compiler/hir/lower.ax, compiler/driver/pipeline.ax, compiler/traits/solver.ax, tests/run/symbol_id_space, tests/resolve, tests/hir/basic.hir, tests/hir/control.hir, tests/hir/exprs.hir, tests/hir/more.hir, tests/typeck/basic.thir, tests/typeck/generic/generic_subst.thir, tests/typeck/async/async_basic_pos.thir, tests/selfhost/hir/qa_hir_corpus.ax.in, tests/selfhost/resolve/qa_resolve_corpus_neg_a.ax.in, tests/selfhost/resolve/qa_resolve_corpus_neg_b.ax.in, tests/selfhost/resolve/qa_resolve_corpus_neg_c.ax.in, tests/selfhost/resolve/qa_resolve_corpus_pos.ax.in, tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_a.ax.in, tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_b.ax.in, tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_c.ax.in, tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_d.ax.in, tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_a.ax.in, tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_b.ax.in, tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_c.ax.in, tests/selfhost/resolve_hir/qa_resolve_hir_corpus_wide_a.ax.in, tests/selfhost/resolve_hir/qa_resolve_hir_corpus_wide_b.ax.in, tests/selfhost/resolve_hir/qa_resolve_hir_multifile_modules_b.ax.in, tests/selfhost/typeck/qa_typeck_a.ax.in]
locks: [bootstrap/axiom0/src/driver/mono.c]
spec: [spec/decisions/ADR-0043-cyclic-type-graphs-and-symbol-id-space.md, spec/decisions/ADR-0034-oracle-independence.md, spec/decisions/ADR-0035-axiomc-parity-symbols.md, spec/SPEC-20-selfhost.md]
covers: [REQ-RES-060]
started: 2026-11-18 13:46:59
finished: 2026-11-19 03:35:43
---
# T164 — AX0-FIX-10: one symbol-id space

## Goal
Two distinct symbols never share a `SymbolId`, whatever the program size, in axiom0 and in axiomc (ADR-0043 §2,
INV-BOOT-005). Today both compilers number user symbols from 1, std symbols from 10000 and extern symbols from 30000;
the axiomc bundle has more than 30000 user symbols, so ids already overlap. When the overlap puts a generic parameter
on the id of a called extern, axiom0 types the call as a type parameter and stage 1 fails with
`AX_TYPE_NOT_CALLABLE` at `CloseHandle`/`ReadFile`/`WriteFile`/`WriteConsoleW` (T444 report B2: 12 symbols of
headroom before `compiler.obj.writer` in bundle order). This is a bootstrap time bomb for every task, hence priority 0.

## Scope
- axiom0 `bootstrap/axiom0/src/resolve/resolve.c`: `new_symbol` and `new_symbol_extern` draw from one counter
  (`resolve_map.next_symbol_v`, allocation order unchanged, so ids stay deterministic); remove `next_std_symbol_v`
  and `next_extern_symbol_v` (or leave them unused with a comment if a header field must stay). `driver/mono.c`
  (`++st->resolve_map.next_symbol_v`) then continues after every symbol; touch it only if needed.
- Port `compiler/resolve/resolver.ax` (~407, ~426, ~2360, ~2506), `symtab.ax` (~69 comment, ~392), and
  `compiler/driver/pipeline.ax` (~618): same single counter. `compiler/hir/lower.ax` (~1425
  `resolve_next_sym_v`) must keep giving mono the first free id after **all** symbols.
- `compiler/traits/solver.ax` `sym_is_std_item` (`v >= 10000 && v < 30000`, used by the trait-item lookup ~530 and the
  coherence check ~2608) reads a stored per-symbol property instead (a std flag recorded when the symbol is created,
  or the module path the symtab naming table already stores). Search both compilers for any other comparison of a
  symbol id against a constant (`grep -E "[<>]=? *(10000|30000)"`) and remove it the same way.
- Goldens that print symbol ids (`@Sym(n)` in `tests/resolve/*.resolved`, the only ones today) may change when std
  and user symbols share the counter; regenerate them and explain the shift in the report. Any other golden that
  changes means behaviour changed: stop and report.
- Regression `tests/run/symbol_id_space/`: a generator `gen_symbol_id_space.py` (Python stdlib, `--check` mode)
  writes `many_symbols.ax` with more than 30100 user symbols (e.g. functions with 50 parameters; file at most 1 MB)
  followed by generic functions `fn id<T>(x: T) -> T` and calls of kernel32 externs and std functions; the program
  prints exact `// stdout:` in interp, native and native-O1. Record in the report whether it fails on baseline in
  axiom0 (`axiom0 run`/`check`), in axiomc2, or neither (then also the T444 reproduction below is the evidence).

## Acceptance
- [ ] `tests/run/symbol_id_space/` passes in interp, native, native-O1 (exact `// stdout:`, WEAK-NATIVE 0).
- [ ] T444 reproduction: in the task snapshot, a dummy function with 60 locals inserted in a module before
      `compiler.obj.writer` in bundle order makes stage 1 fail on baseline axiom0 and succeed with the fix (temporary
      edit, not committed; both runs logged in the report).
- [ ] Bootstrap stage 1-3 succeeds from a **rebuilt** axiom0 (`tools/build_axiomc.py --force` into a fresh out dir —
      the script reuses an existing `axiom0.exe`, see T444c); the stage-2/stage-3 fixed point holds.
- [ ] axiom0 C unit tests and archcheck pass; `harness_check.py` passes (commit subject names AX0-FIX-10).
- [ ] Gate per axiom-qa.md "Per-task gate scope"; failing ids ⊆ baseline.
- [ ] Report `_workspaces/reports/T164-report.md` with exact `## Files changed` and the measured highest symbol id
      of the axiomc bundle before/after.

## Out of scope
- Any other axiom0 change (frozen; ROADMAP R3). Type-graph cycles (T444). `docs/`, `std/`.

## Notes
- axiom0 `symbol_nodes` and the naming table are dense arrays indexed by id: a single counter makes them smaller,
  never larger. Do not move the bases to large constants (ADR-0043 §2 option a, rejected).
- Lockstep with the port per ADR-0034 §2; ADR-0035 generated names must stay identical between the two compilers.
- Canonical syntax (`=`, `.`), see axiom-syntax.

## Log
- 2026-11-17 created by axiom-architect (unblock of T444, B2; ADR-0043 §2)
- 2026-11-18 12:26:45 started (attempt 1) T164-impl
- 2026-11-18 13:46:44 requeue: restart: impl agent unreachable, no work on disk (not charged: attempt refunded)
- 2026-11-18 13:46:59 started (attempt 1) T164-impl
- 2026-11-18 18:40 rescoped by orchestrator: impl reported BLOCKED only for paths (7 HIR/THIR goldens + 16 selfhost harness templates print/bake symbol ids that shift by ids only); paths extended, solver.ax/pipeline.ax moved from locks to paths; not charged
- 2026-11-18 23:00 gate round 0 FAIL (solver std/user trait guess: F1 full std path bound, F2 user trait via module path vs prelude name, F3 re-export); orchestrator adds compiler/hir/hir.ax + lower.ax to paths for the QA-recommended HirPath domain field (no HirPath struct literals exist elsewhere)
- 2026-11-19 03:35:43 accepted by QA -> done
