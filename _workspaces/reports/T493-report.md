# T493 report — Perf: second-wave optimisation of the `own` pass

## Summary

Profiled the post-T486 `own` stage on native `axiomc2.exe` using a Win32 sampling profiler
(`_workspaces/artifacts/T493/sample_prof.py`, symbols mapped from `axiomc2_head.obj` COFF `.text`)
and added `time-own:` sub-timers under `--time-passes` in `compiler/driver/pipeline.ax` (keeping all
9 top-level `time:` lines unchanged).

### Baseline sampling profile (`own` phase only, `axiomc2_head.exe`, HEAD `19e5a45c`)

| Module / hot function (`own` phase only) | `qa_backend_unit.ax` (19.89 s, 7530 samples) | `axiomc_bundle_head.ax` (41.99 s, 13762 samples) | Cause |
|---|---:|---:|---|
| `compiler.own.cap` (`copy_cap_array`, `cap_check_invalidate`, `mir_cap_at*`) | **35.0% (~6.97 s)** | **33.1% (~13.90 s)** | Dense per-block `MirCap[local_count]` heap allocations + byte-loop copies even when 0–2 capabilities are active; linear scan over all `local_count` on every `COPY`/`MOVE` |
| `compiler.own.init` (`copy_own_states`) | **20.6% (~4.10 s)** | **19.3% (~8.09 s)** | Dense per-block `OwnStateInfo[node_count]` (16 B/node) heap allocations + byte-loop copies |
| `compiler.own.move_ck` (`merge_states`, `merge_state_val`) | **6.4% (~1.28 s)** | **6.6% (~2.76 s)** | Per-node 16-byte struct merge across every CFG join |
| `<external/OS>` (`HeapAlloc`/`HeapFree`, mostly per-BB rows in `cap`/`init`) | **6.7% (~1.33 s)** | **6.9% (~2.91 s)** | Separate heap alloc/free per basic block in `own_cap_check` & `own_check` |
| `compiler.verify.verifier` (`verify_own_push_target`, `verify_copy_bytes`, `verify_mir_cap`) | **12.7% (~2.52 s)** | **14.5% (~6.10 s)** | Outside T493 paths (filed under Follow-ups) |
| `compiler.mir.builder` + `compiler.mir.mir` + `compiler.mir.drop` | **~9.7% (~1.93 s)** | **~9.9% (~4.15 s)** | Outside T493 paths (filed under Follow-ups / T494) |
| `compiler.own.unsafe_ck` | **0.4% (~0.08 s)** | **0.4% (~0.17 s)** | Already indexed in T485 |

Together, `compiler/own` (`cap.ax` + `init.ax` + `move.ax`) plus its per-block OS heap allocations and
index arithmetic accounted for **~70–73%** of the entire `own` stage.

### Algorithmic fixes (purely algorithmic — zero semantic or diagnostic changes)

1. **`compiler/own/cap.ax` (`own_cap_check` — ~40×–55× speedup, ~7–14 s → 0.17–0.24 s):**
   - **Borrow-free fast exit:** linear scan checks whether any whole-local `MIR_RVALUE_REF` exists in
     the body; if none, no capability can ever become active and `own_cap_check` returns immediately
     with zero heap allocations.
   - **Compact capability-slot mapping:** single linear pass + BFS over whole-local `USE`/`AGGREGATE`
     copy edges computes the exact transitive closure of locals (`K << local_count`) that can ever
     hold a capability, numbered `0..K-1` in ascending original local order (`local_to_slot` /
     `slot_to_local`) so diagnostic iteration order is preserved identically.
   - **Active-slot `u64` bitset (`FastCapCtx`) + single flat allocation:** every block's state stores
     a `u64` active bitset (`words = (K + 63) >> 6`, usually 1 word) plus a compact `MirCap[K]` row
     inside one contiguous allocation (eliminating per-BB `HeapAlloc`/`HeapFree`). Inactive slots are
     never zeroed, copied, or scanned:
     - `cap_fast_copy` copies only set bits (typically 0–2 slots vs hundreds of locals).
     - `cap_fast_merge` computes `diff = src_word & (~dst_word)` per 64 slots in one bitwise op and
       copies only newly active slots.
     - `cap_fast_check_conflict` and `cap_fast_check_invalidate` iterate only set bits (via
       `cap_ctz_u64`), pre-filtering on `(*ci).place.local.v == target_l` before calling
       `own_region_relate_in_body`.
     - Lazy per-body `dropped_bits` bitset replaces `O(bb_count * stmts)` rescans in
       `cap_local_is_dropped`.
     - Skips diagnostic-only `cap_fast_visit_rvalue` during the non-reporting fixpoint pass, and gates
       `cap_is_inline_call_arg_closure` on at least one active capability operand.
   - **Iterative RPO worklist (`cap_compute_rpo`)** built natively in `cap.ax` (zero stack-overflow
     risk, sets `work_pending = true` only on back-edges `tgt_pos <= rpo_k`), followed by the
     canonical `0..bb_count` reporting pass.

2. **`compiler/own/init.ax` & `compiler/own/mod.ax` (`own_check` / `own_check_init_only` — ~30×–44× speedup, ~5–11 s → 0.17–0.26 s):**
   - **Exact 1-bit definite-ownership bitset fast path:** `h(state) = (state == OWN_OWNED)` is an
     exact homomorphism of the 4-state ownership lattice (`h(merge_state_val(a, b)) = h(a) & h(b)`,
     `h(update_parent) = AND(children)`, and `own_check_use` emits an error iff `h(state) == 0`).
     Packing 64 path nodes per `u64` reduces row size by **128×** (16 B/node → 1 bit/node) in a
     single flat allocation, replacing byte-loop `copy_own_states` and struct-loop `merge_states`
     with word-wise `u64` copies and bitwise `&=` merges.
   - **Direct place resolution (`own_bits_resolve`) & single-pass DAG/fixed-point check:** avoids
     `MirPlace` copies on `proj_count == 0`, combines `check_use + do_move` into one lookup,
     precomputes `ret_needs_check`, and checks uses during Pass 1 of iterative RPO (`own_compute_rpo`)
     so acyclic functions and loops whose back-edges leave `bb_in` unchanged finish in **one pass**.
   - **Exact 4-state fallback (`own_check_exact_fallback`):** whenever the 1-bit fast path detects any
     violation (`found_error == true`), it falls back to the full 4-state `OwnStateInfo` solver with
     `move_loc` spans in canonical `0..bb_count` reporting order, guaranteeing 100% byte-identical
     diagnostics and `"moved here"` labels.
   - Exported `own_check_init_only` (re-exported in `compiler/own/mod.ax`) so `pipeline.ax` can time
     `own_cap` and `own_init` independently while `own_check` retains its exact signature and behavior.

3. **`compiler/driver/pipeline.ax` (`time-own:` sub-timers):**
   - Added 9 `time-own:` sub-timer lines under `--time-passes` (`unsafe`, `async`, `mir_build`,
     `verify_mir`, `own_cap`, `own_init`, `verify_own`, `mir_drop`, `own_rest`) printed right after
     `time: own`, keeping all 9 top-level `time:` lines and all 15 `time-build:` lines unchanged.

4. **`tests/selfhost/bundle_common.py` patch-anchor hygiene:**
   - Verified `compiler/own/cap.ax` and `compiler/own/init.ax` match `[0, 0, 0]` of the 3 legacy
     fixpoint-loop text-patch anchors (zero partial/half-applied patches; native iterative RPO runs
     directly in both compiled `axiomc` and standalone bundles), while preserving `[1, 1]` matches
     for `_own_mir_shim` (`mir_bb_at` / `mir_stmt_at`) and leaving `move.ax` / `unsafe.ax` anchors
     untouched. All 154 regenerated bundles compile and pass cleanly.

5. **`tests/perf/own_scaling/` tests:**
   - Added `own_wave2_subtimers_and_scaling.py` / `.test` verifying the 9 `time-own:` sub-timers and
     sum accounting, intra-procedural scaling of `own_cap + own_init` (`n=40`: 0.0012 s / 0.0017 s →
     `n=160`: 0.0048 s / 0.0059 s, linear 4.0× / 3.5×), native execution correctness, and `-O0`/`-O1`
     byte-identical determinism (`INV-DET-004`).
   - Added UI diagnostic regression tests `own_wave2_diag_ui.ax`, `own_wave2_partial_move_ui.ax`, and
     `own_wave2_uninit_ui.ax` exercising loop back-edge moves, partial field moves, conditional
     uninit, and `view`/`mut_view` capability conflicts.

## Before / after `--time-passes` (3 large bundles, interleaved idle runs)

Measured with `_workspaces/artifacts/T493/bench3.py` (`SOURCE_DATE_EPOCH=0`, `--stack-reserve 67108864`,
`old = HEAD 19e5a45c axiomc2_head.exe`, `new = T493 axiomc2.exe`):

| Bundle | Command | `own` old | `own` new | `own` speedup | Byte-identical (`sha256[:16]`) |
|---|---|---:|---:|---:|---|
| `qa_backend_unit.ax` | `check` | 20.5600 s | **6.9529 s** | **2.96×** | — |
| `qa_backend_unit.ax` | `build -O0` | 19.4940 s | **6.0188 s** | **3.24×** | Yes (`356402328710c9a3`, 11,860,480 B) |
| `qa_backend_unit.ax` | `build -O1` | 18.4259 s | **7.1737 s** | **2.57×** | Yes (`dd3dacb7e0bf1625`, 6,046,720 B) |
| `qa_backend_unit.ax` | `inspect --emit=mir` | — | — | — | Yes (`c1737fdede5251b6`, 12,503,676 B) |
| `qa_driver_commands_b.ax` | `check` | 29.5178 s | **8.6662 s** | **3.41×** | — |
| `qa_driver_commands_b.ax` | `build -O0` | 31.4257 s | **11.5481 s** | **2.72×** | Yes (`277d76ea1bd87e78`, 16,889,856 B) |
| `qa_driver_commands_b.ax` | `build -O1` | 33.8077 s | **11.9360 s** | **2.83×** | Yes (`4b13c3ba9adfe85b`, 8,479,232 B) |
| `qa_driver_commands_b.ax` | `inspect --emit=mir` | — | — | — | Yes (`e7beddf570b7218e`, 18,179,902 B) |
| `axiomc_bundle_head.ax` | `check` | 26.4113 s | **9.8880 s** | **2.67×** (30.86 → 9.97 s = **3.09×** in run 1) | — |
| `axiomc_bundle_head.ax` | `build -O0` | 33.0172 s | **10.5540 s** | **3.13×** | Yes (`5004eb94cba389b7`, 16,658,944 B) |
| `axiomc_bundle_head.ax` | `build -O1` | 38.1091 s | **12.9304 s** | **2.95×** | Yes (`fb6e209d8d9c2405`, 8,360,448 B) |
| `axiomc_bundle_head.ax` | `inspect --emit=mir` | — | — | — | Yes (`952b611ae1657f4d`, 17,914,408 B) |

Post-fix `time-own:` sub-timer breakdown (from `bench3.py` `check --time-passes`):

| Sub-phase | `qa_backend_unit.ax` | `qa_driver_commands_b.ax` | `axiomc_bundle_head.ax` | Owner module |
|---|---:|---:|---:|---|
| `unsafe` | 0.2254 s | 0.2746 s | 0.3012 s | `compiler/own/unsafe.ax` |
| `async` | 0.0017 s | 0.0019 s | 0.0020 s | `compiler/mir/async_lower.ax` |
| `mir_build` | 2.6483 s | 3.2669 s | 3.7452 s | `compiler/mir/builder.ax` (outside T493 paths) |
| `verify_mir` | 0.4662 s | 0.5734 s | 0.6651 s | `compiler/verify/verifier.ax` (outside T493 paths) |
| **`own_cap`** | **0.1669 s** | **0.2110 s** | **0.2443 s** | `compiler/own/cap.ax` (~42×–55× faster) |
| **`own_init`** | **0.1731 s** | **0.2124 s** | **0.2592 s** | `compiler/own/init.ax` (~31×–44× faster) |
| `verify_own` | 2.7407 s | 3.2407 s | 3.7357 s | `compiler/verify/verifier.ax` (outside T493 paths) |
| `mir_drop` | 0.4721 s | 0.8046 s | 0.8567 s | `compiler/mir/drop.ax` (T494) |
| `own_rest` | 0.0584 s | 0.0808 s | 0.0786 s | `compiler/driver/pipeline.ax` |
| **Total `own`** | **6.9529 s** | **8.6662 s** | **9.8880 s** | (**2.96×–3.41×**, from ~28 s target to **6.0–7.2 s** on `qa_backend_unit.ax`) |

Note: `compiler/own` itself (`unsafe + own_cap + own_init`) is now only **0.57 s** on `qa_backend_unit.ax`
(down from ~14.4 s, a **~25×** speedup; `own_cap + own_init` alone dropped from ~12.4 s to **0.34 s**,
**~36×** faster). The remaining ~92% of `time: own` lives entirely outside `compiler/own/` in
`verify_own` (`compiler/verify/verifier.ax`, 38–39%) and `mir_build` (`compiler/mir/builder.ax`, 38%).

## Byte-identity verification (`INV-DET-004`)

Verified with `tests/perf/own_scaling/compare_outputs.py` (`SOURCE_DATE_EPOCH=0`, `--modes O0,O1,mir`,
comparing `axiomc2_head.exe` vs `build-snap-T493/build/axiomc2.exe`):
- All `tests/run/**`:
  `SUMMARY files=808 runs=2424 identical=2424 differ=0 nondet=0 timeout=0`
- All `tests/selfhost/**`:
  `SUMMARY files=172 runs=516 identical=516 differ=0 nondet=0 timeout=0`
- All 3 large bundles (`qa_backend_unit.ax`, `qa_driver_commands_b.ax`, `axiomc_bundle_head.ax`) via
  `_workspaces/artifacts/T493/bench3.py`: 9/9 builds & MIR dumps byte-identical (0 diffs).
- **Grand total: 2,949 / 2,949 builds and MIR dumps 100% byte-identical (`differ=0, nondet=0, timeout=0`).**

## Self-host bootstrap & fixed point

Built inside `build-snap-T493` via `python tools/build_axiomc.py --out build --stage 3`:
- `STAGE1 OK`: `axiomc1.exe` (27,399,168 B, `sha256=9495bea61fc7a5b3`, wall 87.63 s)
- `STAGE2 (O1) OK`: `axiomc2.exe` (8,455,680 B, `sha256=8ce0c3c2296e9e04`, wall 168.07 s, down from 230.65 s)
- `STAGE3 (O1) OK`: `axiomc3.exe` (8,455,680 B, `sha256=8ce0c3c2296e9e04`, wall **72.29 s**)
- `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == 8ce0c3c2296e9e043b9aa27a560e05a382c9423987f327d5c790154260cb1ae1`

## Files changed
- compiler/driver/pipeline.ax
- compiler/own/cap.ax
- compiler/own/init.ax
- compiler/own/mod.ax
- tests/perf/own_scaling/own_wave2_diag_ui.ax
- tests/perf/own_scaling/own_wave2_partial_move_ui.ax
- tests/perf/own_scaling/own_wave2_subtimers_and_scaling.py
- tests/perf/own_scaling/own_wave2_subtimers_and_scaling.test
- tests/perf/own_scaling/own_wave2_uninit_ui.ax
- _workspaces/reports/T493-report.md

## Tests

Inside `build-snap-T493` (refreshed to HEAD `f4b64ad5`, 154 regenerated bundles, `build/axiomc2.exe`):
- `python tools/taskgate.py --task T493 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`:
  - `own`: 7 ids, 9 results — **9 PASS, 0 FAIL**
  - `affected`: 133 ids, 224 results — **224 PASS, 0 FAIL** (all 46 `selfhost` tests including `own`, `cap`, `own_mir_verify`, `verify`, `opt`, `interp_opt`, `backend`, `driver`, `obj_link_driver`; all `ui/own`, `verify/own`, `conformance/adversarial`, `driver`, `perf`)
  - `smoke`: 30 ids, 51 results — **51 PASS, 0 FAIL**
  - **Total (dedup)**: 160 ids — **`TOTAL 270 PASS 270 FAIL 0 SKIP 0 XFAIL 0`**
  - `archcheck`: clean (exit 0) — 229 files scanned, 0 violations
  - `WEAK-NATIVE`: 0 in the task's own/changed tests
  - `Baseline`: `BASELINE OK`
  - **`TASKGATE T493 exit=0`**
- `python tools/axtest.py --compiler build/axiomc2.exe -j 2 --no-cache ui/own ui/cap ui/init ui/unsafe ui/conc ui/borrow ui/drop`:
  `TOTAL 65 PASS 65 FAIL 0 SKIP 0 XFAIL 0`
- `tests/selfhost/cap/qa_own_cap.ax` & `tests/selfhost/own/qa_own_init.ax` in `axiom0 run --interp`:
  `OK Own Cap`, `OK Own Init` (zero MIR interpreter UB / leak / bounds errors).
- `tests/perf/build_scaling/qa_time_passes_and_determinism.py`: `OK qa_time_passes_and_determinism`.
- `tests/perf/own_scaling/own_scaling.py --units 200 --limit 8 --print`:
  `own(200)=0.354s own(800)=1.908s ratio 5.39 limit 8.00` -> `OK own scaling`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T493`: exit 0, 0 `REFUSED` lines.

## Spec deviations
none

## Follow-ups
- **Perf — apply compact bitset dataflow to `compiler/verify/verifier.ax` (`verify_mir_own` / `verify_mir_cap`):**
  Now the #1 remaining sub-phase of `time: own` (38–39%, 2.74 s on `qa_backend_unit.ax`, 3.74 s on
  `axiomc_bundle`), still using dense byte-loop copies (`verify_own_push_target`, `verify_copy_bytes`,
  `verify_fill_bytes`). Applying the same 1-bit ownership / compact-slot capability bitsets there
  should cut `verify_own` by >10×.
- **Perf — eliminate remaining superlinear lookup in `compiler/mir/builder.ax` (`mir_build`):**
  Now the #2 remaining sub-phase of `time: own` (38%, 2.65 s on `qa_backend_unit.ax`, 3.75 s on
  `axiomc_bundle`; scales ~13× for 4× units on `own_scaling` with many structs/consts/fns).
- **Cleanup — retire legacy `own_check` / `own_cap_check` text patches in `tests/selfhost/bundle_common.py`:**
  Now that `compiler/own/{cap,init}.ax` implement iterative RPO natively, the old string-replacement
  blocks in `bundle_common.py` lines 889–1085 can be retired cleanly (outside T493 paths).

STATUS: COMPLETE round=0
