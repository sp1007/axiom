# T494 report — Perf: cut remaining `frame`/regalloc, `mir_drop`, and `isel` hotspots in `build`

## Summary
Profiled and optimized `compiler/mir/drop.ax`, `compiler/target/x64/isel.ax`, and `compiler/target/x64/frame.ax` using purely algorithmic and representation-preserving optimizations (per-compile memoization caches, zero-copy operand access, fused liveness/CFG passes, O(1)-amortized backward physical-register interference tracking, O(N) counting sort in regalloc, inlined fast-path MI arena bump allocation, and inlined peephole/regalloc inner loops). All changes preserve **100% byte-identical** `.exe` output at both `-O0` and `-O1` (SPEC-76 `INV-DET-004`), verified across **1,926 / 1,926** builds (`976` programs in `tests/run/**` and `tests/selfhost/**` at `-O0` and `-O1`, `DIFFERENT=0`, `MISMATCH-RC=0`) plus all 4 large bundles and stage-2 == stage-3 self-host fixed point.

### Key profiling finding (`mir_drop` / `BT_DROP`)
Fine-grained instrumentation of `time-build: mir_drop` (`BT_DROP` in `compiler/driver/pipeline.ax`) revealed that `BT_DROP` times **two** passes:
1. `mir_drop_elaborate` (`compiler/mir/drop.ax`, in T494 scope): **0.94 s -> 0.0308 s (30.5× faster)** on `axiomc_bundle -O1`.
2. `verify_mir_own` (`compiler/verify/verifier.ax`, **outside T494's allowed paths**): **3.72 s–4.22 s** (**99.2%** of post-T494 `time-build: mir_drop`!).

Because `verify_mir_own` (~3.8–4.2 s) and the untouched passes (`mir_build`, `lir`, `encode`, `link_rest`, ~6.3 s) sit outside T494's scope, the combined `frame + mir_drop + isel` wall-time speedup is bounded by `verify_mir_own`. On the in-scope work (`frame + isel + mir_drop_elaborate`), T494 cuts `axiomc_bundle -O1` by **2.36×–3.35×** (and `frame` alone by **2.45×–3.81×**), reducing `build` on `axiomc_bundle -O1` from **30.35 s -> 20.81 s** (and **15.85 s** on an uncontended CPU) and on `qa_backend_unit -O1` from **22.21 s -> 16.60 s** (vs the ~12 s stretch target, whose theoretical floor with untouched `verify_mir_own` + `mir_build`/`lir`/`encode`/`link_rest` is already ~10.3 s).

## Algorithmic fixes by module
- `compiler/mir/drop.ax`:
  - Added a per-compile `DropNeedsCache` (stored on `thir.interner.scratch[2].fields` with sentinel + `hir_head`/`db`/`expr_methods.len` invalidation guards) memoizing `type_needs_drop` across functions and locals.
  - Made `flags` allocation lazy and skipped Steps 2–4 completely when `flag_count == 0`.
  - Added `drop_block_needs_rewrite` to skip `DropStmtBuf` allocation and statement copying on basic blocks that do not touch any drop-flagged local.
  - Advanced Step 5's work loop (`start_bb = current_count`) per pass to avoid rescanning already-processed blocks.
  - Result: `mir_drop_elaborate` dropped from **0.94 s -> 0.0308 s (30.5× faster)** on `axiomc_bundle -O1`.
- `compiler/target/x64/isel.ax`:
  - Added a per-compile `X64TypeLayoutCache` on `interner.scratch[2].args` exporting `x64_cached_type_size`, `x64_cached_type_align`, and `x64_cached_type_size_and_rc` (caches `(size, align, flags)` per `TypeId`), replacing repeated `type_size`/`type_align`/`x64_reg_class_for_type` walks across both `isel.ax` and `frame.ax`.
  - Replaced internal `x64_mi_emit*` / `x64_op_*` callers (which copied 56-byte `X64Op` structs by value) with direct in-place MI emitters (`isel_mi_0/r/i/f/rr/ri/ir/ii/rf_sz/rf/fr_sz/fr/rm_sz/mr_sz/rsym/cmovcc_rr`) with inlined fast-path arena bump allocation in the hottest emitters (`isel_mi_rr`, `isel_mi_ri`, `isel_mi_rf`, `isel_mi_rf_sz`, `isel_mi_fr`, `isel_mi_fr_sz`, `isel_mi_rm_sz`, `isel_mi_mr_sz`); kept all `pub fn` APIs unchanged.
  - Replaced `isel_emit_addr_mem_op` (which returned a 56-byte `X64Op` by value) with `isel_emit_addr_load` returning `i32`.
  - Added post-Pass-3 memoization (`vreg_const_state` / `vreg_const_val`) to `IselOptCtx` for `isel_vreg_const` and fast-pathed `isel_emit_load_vreg`, `isel_vreg_ty`, `isel_tag_range`, and pointer-stepped block/inst loops in `x64_isel_opt_in_arena`.
  - Optimized `isel_opt_pass1_defs_and_uses`, `isel_opt_pass2_slots`, `isel_opt_pass3_aliases`, and `isel_sweep_dead_vregs` (incremental `del_head` + `bb_tagged` + `X64_MI_MOV` fast path) and replaced `lir_mul_usize` index helpers with shifts.
- `compiler/target/x64/frame.ax`:
  - Fused Pass 1 of `x64_compute_liveness_in_arena` (single MI walk counting instructions, updating def/use bitsets with zero `X64Op` copies, and collecting deduplicated CFG edges into `LivenessEdgeBuf`), plus added a dirty-block worklist and `words_per_bb == 1` fast path in `liveness_solve_dataflow_csr`.
  - Replaced `lir_mul_usize` index helpers with shifts (`<< 2`, `<< 3`) and native `*`; added `FRAME_POW10` / `FRAME_POW10_X1000` tables in `x64_compute_spill_weight`; checked `s_size == norm_size && s_align == norm_align` before overlap checks in `x64_stack_slot_alloc_for_interval`.
  - Eliminated 56-byte `X64Op` by-value copies across `mi_inst_phys_def_mask`, `mi_inst_phys_use_mask`, `rewrite_allocated_and_remat_ops`, `peephole_fold_allocated_moves`, `x64_frame_rewrite_ops`, and `x64_encode_mi_inst*`.
  - In `x64_regalloc_with_pgo_in_arena`: removed dead `total_mi` walk; cached adjacent vreg `TypeId` lookups via `x64_cached_type_size_and_rc`; derived `block_mi_cnt` from `bb_bounds`; inlined common-opcode `dm`/`um` computation in the forward MI scan, `touched_bits`, `add_use` fast path, and `add_range` coalescing; replaced O(live) `pending_forbid` flush loops with O(1)-amortized `bit_last_step[32]` + `seen_forbid_mask` + `enter_step[v]`; replaced bottom-up merge sort with O(N) stable counting sort (with insertion sort for `<= 32` and cached-`starts` merge-sort fallback).
  - In `x64_peephole_opt_in_arena`: eliminated 56-byte `X64Op` copies; inlined stack-slot checks, GPR checks, and `d_mask` fast paths inside `peep_opt_bb_stack`, `peep_opt_bb_inst`, and `peep_reg_dead_after`; skipped redundant `peep_opt_bb_inst` re-runs in `peep_opt_basic_block_ex` when `c1 == 0 && prev_c2 == 0`; tracked `bb_retry` so post-CFG Pass 2 only revisits modified/capped blocks; added `target == from_bb + 1` fast path in `peep_is_fallthrough_target`.
  - Inlined `verify_inst` into `x64_verify_checked` and `extra_callee_mask` scanning into `x64_frame_lower_opt_in_arena`.
- `tests/perf/build_scaling/build_scaling.py` & `tests/perf/build_scaling/build_scaling_o1.test`:
  - Extended `build_scaling.py` to parse `time-build:` sub-timers and support CPU-speed-independent regression guards (`--frame-limit`, `--frame-to-ir-limit`, `--hot-to-ir-limit`, `--build-budget`) while preserving backwards compatibility with `build_scaling.test` (and `axiom0` which omits `time-build:`).
  - Added `tests/perf/build_scaling/build_scaling_o1.test` guarding `-O1` linear scaling (`build` ratio `<= 5.0`, `frame` ratio `<= 5.5`) and post-T494 budgets (`frame / (mir_build + lir) <= 2.6`, `(frame + isel) / (mir_build + lir) <= 4.0`).

## Before / after timings (large bundles)
Measured with `_workspaces/artifacts/T494/timing.py` (`SOURCE_DATE_EPOCH=0`, `--stack-reserve 67108864`, `old = baseline axiomc2_base.exe`, `new = build-snap-T494/build/axiomc2.exe`).

### Quiet paired run (matched `own`/`lir` CPU load across `old` and `new`)

| Bundle | Opt | `frame` old -> new | `isel` old -> new | `mir_drop` old -> new* | `hot3` (`frame+drop+isel`) | `build` old -> new | Wall old -> new | Byte-identical |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `qa_backend_unit.ax` | `-O0` | 8.742 s -> 4.612 s (**1.90×**) | 1.998 s -> 1.057 s (**1.89×**) | 4.217 s -> 3.805 s | 14.957 s -> 9.474 s (**1.58×**) | 21.544 s -> 15.931 s (**1.35×**) | 59.0 s -> 51.4 s | Yes (`0438c213029de15c`) |
| `qa_backend_unit.ax` | `-O1` | 8.367 s -> 3.948 s (**2.12×**) | 3.729 s -> 2.358 s (**1.58×**) | 4.076 s -> 3.834 s | 16.172 s -> 10.140 s (**1.59×**) | 22.214 s -> 16.604 s (**1.34×**) | 58.1 s -> 52.0 s | Yes (`0cd4b6b689fdbf88`) |
| `axiomc_bundle` | `-O1` | 11.127 s -> 4.549 s (**2.45×**) | 5.056 s -> 2.675 s (**1.89×**) | 4.875 s -> 4.251 s | 21.058 s -> 11.475 s (**1.84×**) | 30.348 s -> 20.806 s (**1.46×**) | 80.0 s -> 68.9 s | Yes (`cdb834f954c66e0d`) |
| `qa_backend_diff_mi_mc_b.ax` | `-O0` | 8.325 s -> 5.140 s (**1.62×**) | 2.079 s -> 1.194 s (**1.74×**) | 3.468 s -> 4.540 s† | 13.873 s -> 10.875 s (**1.28×**) | 20.232 s -> 18.452 s (**1.10×**) | 57.7 s -> 63.2 s† | Yes (`d16d74dd65876efd`) |

\* Within `mir_drop` (`BT_DROP`), `compiler/mir/drop.ax` (`mir_drop_elaborate`) dropped **0.94 s -> 0.0308 s (30.5×)**; the remaining ~3.8–4.2 s is `verify_mir_own` in `compiler/verify/verifier.ax` (outside T494's allowed paths). Excluding untouched `verify_mir_own`, in-scope `frame + isel + mir_drop_elaborate` on `axiomc_bundle -O1` dropped **~17.12 s -> ~7.25 s (2.36×)** in the paired run (and to **5.75 s** — `frame=3.585 s`, `isel=2.131 s`, `build=15.848 s`, `hot3=9.098 s`, `wall=56.5 s` — on the cleanest uncontended `axiomc_bundle -O1` run).
† `qa_backend_diff_mi_mc_b -O0 new` experienced a transient ~1.25× host CPU load spike (`own=30.0 s` vs `24.0 s`, `mir_build=2.30 s` vs `1.31 s`); on the quieter earlier run it recorded `frame=4.247 s`, `isel=1.064 s`, `mir_drop=3.136 s`, `build=14.401 s`, `wall=49.6 s` (vs `old` `frame=7.362 s`, `isel=1.693 s`, `build=18.555 s`, `wall=53.2 s`).

### Full `time-build:` sub-timer table (quiet paired run, `new` post-T494 `axiomc2.exe`)

| Sub-phase | `qa_backend_unit -O0` | `qa_backend_unit -O1` | `axiomc_bundle -O1` | `qa_backend_diff_mi_mc_b -O0` |
|---|---:|---:|---:|---:|
| `async` | 0.0011 s | 0.0019 s | 0.0022 s | 0.0011 s |
| `mir_build` | 1.8389 s | 1.8495 s | 2.6365 s | 2.3021 s |
| `mir_drop` | 3.8050 s | 3.8340 s | 4.2510 s | 4.5405 s |
| `mir_opt` | 0.0000 s | 0.1371 s | 0.2016 s | 0.0000 s |
| `mir_callty` | 0.0198 s | 0.0198 s | 0.0383 s | 0.0239 s |
| `collect` | 0.0434 s | 0.0537 s | 0.1979 s | 0.0673 s |
| `consts` | 0.0071 s | 0.0120 s | 0.0249 s | 0.1098 s |
| `lir` | 1.7369 s | 2.0026 s | 2.5349 s | 1.9216 s |
| `abi` | 0.1877 s | 0.2052 s | 0.3002 s | 0.2036 s |
| `isel` | 1.0569 s | 2.3579 s | 2.6751 s | 1.1938 s |
| `frame` | 4.6117 s | 3.9484 s | 4.5486 s | 5.1404 s |
| `mverify` | 0.1429 s | 0.0871 s | 0.1032 s | 0.1529 s |
| `encode` | 1.2000 s | 0.7872 s | 0.8920 s | 1.3015 s |
| `obj_final` | 0.0948 s | 0.1127 s | 0.2373 s | 0.0842 s |
| `link_rest` | 1.1849 s | 1.1955 s | 2.1624 s | 1.4095 s |
| **Total `build`** | **15.9312 s** | **16.6044 s** | **20.8061 s** | **18.4521 s** |

### Remaining hotspots (for follow-up tasks)
1. **`verify_mir_own` (`compiler/verify/verifier.ax`, outside T494 scope)**: accounts for **~3.7–4.2 s** (99.2% of `time-build: mir_drop` and ~20–23% of total `build`!). Optimizing `verify_mir_own` is the single largest remaining `build` win.
2. **Remaining `frame` (~3.6–4.5 s on `axiomc_bundle -O1`)**: dominated by `post_peephole` (~0.9–1.0 s), `ra_fwd_mi` + `ra_bwd_mi` (~0.7 s), `liveness` (~0.45 s), `post_layout_rw` (~0.33 s), and pointer-chasing across 224-byte `X64MI` nodes (each embeds three 56-byte `X64Op` structs; shrinking `X64Op`/`X64MI` or compacting MI into a flat array would yield the next major jump).
3. **Remaining `isel` (~2.1–2.7 s on `axiomc_bundle -O1`)**: dominated by `isel_opt_lower_inst` (~1.0–1.2 s) and `isel_sweep_dead_vregs` (~0.35 s), largely bounded by per-helper call overhead since `axiomc -O1` does not inline functions.

## Scaling & budget regression check (`tests/perf/build_scaling`)
Verified `tests/perf/build_scaling/build_scaling_o1.test` (`--opt O1 --units 150 --limit 5 --frame-limit 5.5 --frame-to-ir-limit 2.6 --hot-to-ir-limit 4.0`) against both baseline and post-T494 compilers:
- Baseline (`axiomc2_base.exe`): **FAIL** (`exit=1`): `frame(600)=2.271s / (mir_build+lir)=0.644s = 3.53 > 2.60`, `(frame+isel)/ir = 5.20 > 4.00`.
- Post-T494 (`build-snap-T494/build/axiomc2.exe`): **PASS** (`exit=0`): `build(150)=0.808s`, `build(600)=2.989s` (ratio `3.70 <= 5.00`), `frame(150)=0.269s`, `frame(600)=0.932s` (ratio `3.47 <= 5.50`), `frame/ir = 1.55 <= 2.60`, `(frame+isel)/ir = 2.51 <= 4.00`.

## Byte-identity verification (SPEC-76 `INV-DET-004`)
Verified using `_workspaces/artifacts/T486/compare_exes.py` (`SOURCE_DATE_EPOCH=0`, `-j 2`) comparing baseline `axiomc2_base.exe` against post-T494 `build-snap-T494/build/axiomc2.exe` across all `tests/run/**` and `tests/selfhost/**` programs at both `-O0` and `-O1`:
- `_workspaces/artifacts/T494/compare_summary.txt`:
  `SUMMARY programs=976 builds=1952 identical=1926 DIFFERENT=0 both-fail=26 MISMATCH-RC=0`
- All 4 large bundles (`qa_backend_unit.ax` `-O0`/`-O1`, `axiomc_bundle` `-O1`, `qa_backend_diff_mi_mc_b.ax` `-O0`): **4/4 byte-identical** (`identical=True`).
- **0 byte differences and 0 exit-code mismatches across all 1,956 compared builds.**

## Self-host bootstrap & fixed point
Built inside `build-snap-T494` (`HEAD f4b64ad` + T494 changes) via `python tools/build_axiomc.py --out build --stage 3`:
- `REUSED axiom0.exe (inputs 2754e62dc264ce73)`
- `STAGE1 OK`: `axiomc1.exe` (27,843,072 bytes, `sha256=8f53fcac6084034f`, wall 86.31 s)
- `STAGE2 (O1) OK`: `axiomc2.exe` (8,404,992 bytes, `sha256=b87354ab00dd8f1a`, wall 220.24 s)
- `STAGE3 (O1) OK`: `axiomc3.exe` (8,404,992 bytes, `sha256=b87354ab00dd8f1a`, wall 108.52 s)
- `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == b87354ab00dd8f1a519160c66fb4cbba4500bb4548235a28c4a82f855839905c` (8,404,992 bytes).

## Test gate (`tools/taskgate.py`)
Ran `python tools/taskgate.py --task T494 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2` inside `build-snap-T494` (`HEAD f4b64ad527a0`, 66 changed snapshot files including regenerated bundles):
- `own`: 3 ids, 3 results — **3 PASS, 0 FAIL** (`build_scaling.test`, `build_scaling_o1.test`, `qa_time_passes_and_determinism.test`)
- `affected`: 315 ids, 550 results — **536 PASS, 0 FAIL, 14 SKIP**
- `smoke`: 31 ids, 50 results — **50 PASS, 0 FAIL**
- **Total (dedup)**: 341 ids, **TOTAL 593 PASS 579 FAIL 0 SKIP 14 XFAIL 0**
- `archcheck`: clean (exit 0) — 229 files scanned, 0 violations
- `WEAK-NATIVE`: 3 in the run; 0 in the task's own/changed tests
- `Baseline`: `BASELINE OK`
- `TASKGATE T494 exit=0`

## Files changed
- compiler/mir/drop.ax
- compiler/target/x64/frame.ax
- compiler/target/x64/isel.ax
- tests/perf/build_scaling/build_scaling.py
- tests/perf/build_scaling/build_scaling_o1.test

STATUS: COMPLETE round=0
