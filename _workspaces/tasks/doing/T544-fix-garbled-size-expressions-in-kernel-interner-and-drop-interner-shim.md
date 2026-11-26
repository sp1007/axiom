---
id: T544
title: Fix — compiler/kernel/interner.ax carries garbled size expressions (`old_(mcap << 3)`, `new_(...)`, `cur_(...)`) that only compile through `_interner_shim`; the shipped axiomc over-allocates and overflows the string table past 65,536 strings
phase: P13-low-level-systems-unsafe-frees
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: []
priority: 15
status: doing
attempts: 1
paths: [compiler/kernel/interner.ax, tests/selfhost/kernel/qa_kernel_interner.ax.in]
locks: [tests/selfhost/bundle_common.py]
spec: [spec/SPEC-20-selfhost.md, spec/SPEC-50-unsafe-ub-ffi.md]
covers: [REQ-CAP-037]
started: 2026-11-26 20:23:22
agent: T544-impl
---
# T544 — Repair the interner's allocation sizes and remove the bundle shim that hides them

## Why
Found during `_workspaces/reports/triage-2026-11-26-T502-regression.md` (already noted in `T082d-report.md` §4, never
fixed). Since T081 (d57fb098) `compiler/kernel/interner.ax` contains mangled size arguments:
- `StrInterner`: `heap_alloc(new_(((cap as isize) * (size_of<StrView>() as isize)) as usize), ...)` (~line 179),
  `heap_free(old_strings, cur_(((cap as isize) * ...)), ...)` (~189), `heap_free(old_hashes, old_(mcap << 3), 8)` and
  `heap_free(old_ids, old_(mcap << 2), 4)` (~130);
- `U32Interner`: the same `old_(mcap << …)` pair (~370) and `heap_free(old_items, cur_(cap << 2), 4)` (~412).

They compile only because `tests/selfhost/bundle_common.py` injects `INTERNER_SHIM_MODULE`
(`cap = 1`, `mcap = 1`, `old_(x) = x`, `cur_(x) = x`, `new_(x) = 1048576`) and this shim is also in the bundle that
builds the production compiler (`tools/bootstrap.py` → `gen_obj_link_driver_tests.axiomc_bundle_text()`; checked:
the axiomc bundle contains `module _interner_shim`). Consequences in the shipped `axiomc`:
- every growth of the string table allocates exactly 1 MiB (65,536 `StrView`s) whatever `new_cap` is, so when the
  65,537th distinct string is interned the table (cap 131,072 on paper) is written past its 1 MiB block: heap
  corruption for a large enough program;
- every `heap_free` passes a wrong size (8, 4 or 16 bytes). Native `HeapFree` ignores it today; a sized allocator or
  the oracle's free-size check would not.

## Scope
1. Restore the intended expressions in `compiler/kernel/interner.ax`: `new_cap * size_of<StrView>()`,
   `cur_cap * size_of<StrView>()`, `old_mcap << 3`, `old_mcap << 2`, `cur_cap << 2` (use the local variables that
   exist at each site; no shim names remain).
2. Remove `INTERNER_SHIM_MODULE` and its injection (the `use _interner_shim.*` lines) from
   `tests/selfhost/bundle_common.py`; keep the `@derive(Copy)` injection on `StrView` if still needed. Do not edit or
   list generated bundles: the harness regenerates them at snapshot/accept.
3. Regression in `tests/selfhost/kernel/qa_kernel_interner.ax.in`: intern ≥ 70,000 distinct strings (and a second pass
   that finds each of them again by id/bytes), plus a `U32Interner` growth past several doublings; exact stdout, run in
   interp, native and native-O1.

## Acceptance
- [ ] `grep -nE "old_\(|cur_\(|new_\(" compiler/kernel/interner.ax` and `grep -n "_interner_shim" tests/` find nothing.
- [ ] The new regression passes in all three modes (the oracle reports no UB); it fails (crash or UB) on HEAD — show it.
- [ ] Stage-2 build succeeds; stage-2 == stage-3 fixed point at `-O0` and `-O1`.
- [ ] Gate: task tests + every selfhost group whose bundle embeds `compiler.kernel.interner` (they are all
      regenerated) + smoke; failing ids ⊆ `_workspaces/baseline-failures.txt`.
- [ ] Report `_workspaces/reports/T544-report.md` with an exact `## Files changed`.

## Out of scope
- `std/collections/idtable/id_table.ax` (its interner is a separate copy without the garbling).
- Any interner redesign or API change.

## Log
- 2026-11-26 created by architect (`_workspaces/reports/triage-2026-11-26-T502-regression.md`)
- 2026-11-26 20:23:22 started (attempt 1) T544-impl
