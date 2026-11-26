# T544 report — repair the interner's allocation sizes, drop `_interner_shim`

## Summary
`compiler/kernel/interner.ax` carried five garbled size expressions (`old_(mcap << 3)`, `old_(mcap << 2)`,
`new_(((cap as isize) * ...))`, `cur_(((cap as isize) * ...))`, `cur_(cap << 2)`) that only compiled through the
`_interner_shim` module injected by `tests/selfhost/bundle_common.py` (`new_(x)` = fixed 1 MiB). Restored the
intended expressions with the local variables that exist at each site, removed the shim and its injection, and
added a regression that interns past the old 65,536-string limit.

## Changes
- `compiler/kernel/interner.ax`
  - `interner_grow_map` and `u32_interner_grow_map`: `heap_free(old_hashes, (old_mcap << 3), 8)` and
    `heap_free(old_ids, (old_mcap << 2), 4)`.
  - `interner_intern_bytes`: grow allocates `new_cap * size_of<StrView>()`, frees `cur_cap * size_of<StrView>()`.
  - `u32_intern`: grow frees `(cur_cap << 2)`.
- `tests/selfhost/bundle_common.py`: removed `INTERNER_SHIM_MODULE`, its `parts.append`, and the five
  `use _interner_shim.*` injection lines (the `@derive(Copy)` injection on `StrView` is kept). Docstring updated.
  This file is under the task's `locks:` only; it is listed below so that the snapshot copies it.
- `tests/selfhost/kernel/qa_kernel_interner.ax.in`: added `test_many_strings()` (70,000 distinct 8-byte strings,
  ids checked, then a second pass that looks every string up by bytes, re-interns it, fetches it by id and compares
  the bytes; absent string stays absent) and `test_many_u32()` (100,000 distinct values: ids, lookup, re-intern,
  get-by-id; absent value). Exact stdout unchanged (`OK Kernel Interner`). Directives `timeout: 120`, `modes: native`
  (see Decisions).

## Verification (all in `build-snap-T544`)
- Acceptance grep: `grep -nE "old_\(|cur_\(|new_\(" compiler/kernel/interner.ax` finds nothing; no `_interner_shim`
  left in `tests/selfhost/*.py`, templates or the regenerated bundle (`grep -c` = 0).
- New regression: `selfhost/kernel/qa_kernel_interner.ax` PASS in native and native-O1; the whole `selfhost/kernel`
  group (20 results) PASS.
- Fails on HEAD: the same bundle with the old interner (shim restored, garbled expressions restored) built with
  `axiom0 build` crashes at run time in both `-O0` and `-O1` (access violation, shell status 139) instead of printing
  `OK Kernel Interner`.
- Stage-2 build: `tools/build_axiomc.py --out build` OK; fixed point `axiomc2 == axiomc3` at -O1
  (sha256 `ab15b62bbfdd21dc70f505f948585436c395b28d444d97e139f26fb20feac744`) and at -O0
  (`0125dd1796db6cd0b9bcad06ef14d0f1efda3d4ead73e8e01ff18a7e0416d627`, `--check-both-opt`). Stage-0 guard OK.
- Gate: `python tools/taskgate.py --task T544 --compiler build/axiomc2.exe --build-dir build
  --exclude-requires axiom0-internal -j 2` (the same invocation as the T543 gate; the affected set contains every
  selfhost group because they all embed `compiler.kernel.interner`): `TOTAL 280 PASS 269 FAIL 2 SKIP 9`; archcheck
  clean; smoke-check OK; WEAK-NATIVE 0 in the task's own tests. The two failing ids are not caused by this change and
  are not in the baseline file:
  - `selfhost/obj_link_driver/qa_t442_obj_link_driver_bounds.test` — the oracle script fails with
    "`_workspaces/baseline-failures.txt` still has active lines": it asserts the baseline file is empty, which is
    false on HEAD whenever any baseline entry is active (entries from T540, T428g, ... are active now).
  - `selfhost/stage1/stage1_bootstrap.test` — `check --json` mismatch on `tests/ui/typeck/bug_float_unsupported.ax`:
    axiom0 reports three `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP`, the Axiom typeck reports one `AX_TYPE_MISMATCH`. The
    HEAD-built seed compiler (`_workspaces/artifacts/compiler-cache/axiomc2_O1_c8d9621632f121f5.exe`) prints
    byte-identical JSON to the new axiomc2, so the divergence is on HEAD.

## Decisions
- The regression is `// modes: native` (runs native and native-O1; precedent `tests/selfhost/parse/qa_parse_heavy_*`).
  In the MIR interpreter the interner is roughly quadratic in practice: 200 strings already take ~27 s, 2,000 do not
  finish in 120 s, so the 65,536-string threshold cannot be reached in interp mode. The oracle therefore gets no
  large-size run of this test; the interner is still exercised in interp by every other selfhost group that embeds it.
  This also removes the previous small interp coverage of this one bundle (`qa_kernel_interner.ax` ran in interp
  before). Follow-up below.
- Free sizes use the exact allocation sizes (`old_mcap << 3`, `old_mcap << 2`, `cur_cap << 2`,
  `cur_cap * size_of<StrView>()`), matching `interner_free`/`u32_interner_free`, so a sized allocator or the
  oracle's free-size check sees consistent sizes.

## Follow-ups (for the architect)
1. Interp twin: add a second small template (for example `qa_kernel_interner_small.ax.in`, the old test body with
   counts of a few dozen) to `BUNDLES` in `tests/selfhost/kernel/gen_kernel_tests.py` and `generated-files.txt`
   (outside this task's paths) to keep an all-modes run of the interner.
2. Interp performance: 200 interned strings take ~27 s in the MIR interpreter (about linear up to ~100, then far
   worse); worth a profile task (likely oracle bookkeeping that scales with the number of live heap blocks/bytes).
3. Baseline: `selfhost/stage1/stage1_bootstrap.test` (float diagnostic divergence axiom0 vs Axiom typeck) and
   `selfhost/obj_link_driver/qa_t442_obj_link_driver_bounds.test` (asserts an empty baseline file) fail on HEAD and
   are missing from `_workspaces/baseline-failures.txt`; each needs a baseline entry with a fixing task, or the t442
   oracle must ignore the baseline file.
4. Process note: while stopping my first (axiom0-based, interp-heavy) gate run I terminated processes by a
   command-line match on `taskgate`; they were this task's own runner and wait loops (all started from this
   session), no other task's snapshot was touched.

## Files changed
- compiler/kernel/interner.ax
- tests/selfhost/bundle_common.py
- tests/selfhost/kernel/qa_kernel_interner.ax.in
- _workspaces/reports/T544-report.md

STATUS: COMPLETE round=0
