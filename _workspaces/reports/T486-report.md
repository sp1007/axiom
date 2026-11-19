# T486 report — Perf: make the `build` phase scale linearly

## Summary
Profiled and eliminated the superlinear bottlenecks in the `build` phase (MIR build -> drop elaboration -> MIR opt ->
LIR lowering -> ABI lowering -> isel -> frame/regalloc -> machine-IR verify -> encode -> object model -> PE link).
All changes are purely algorithmic (hash indexes, per-compile caches, CSR/worklist liveness, sorted enclosing-function
lookup, and pre-built symbol/item tables) and preserve **byte-identical** `.exe` output at both `-O0` and `-O1`
(SPEC-76 `INV-DET-004`).

On `tests/selfhost/backend/qa_backend_unit.ax` (~95k lines), `build`-phase time drops from **373.3 s to 32.2 s
(11.6x faster)** at `-O0` and from **516.3 s to 25.6 s (20.2x faster)** at `-O1` (target: >= 5x). On the full
self-hosted compiler bundle (`axiomc_bundle`, `-O1`), `build`-phase time drops from **1041.9 s to 50.3 s (20.7x faster)**
with identical output SHA-256 (`fa1d7d6dc3d4e41c...`).

## Sub-timers (`--time-passes`)
Added `time-build:` sub-timer lines under `--time-passes` in `compiler/driver/pipeline.ax` and
`compiler/backend/session.ax` (`backend_lower_fn_to_mc_checked_timed`) while leaving all existing top-level `time:`
lines unchanged:
- `async`, `mir_build`, `mir_drop`, `mir_opt`, `mir_callty`, `collect`, `consts`, `lir`, `abi`, `isel`, `frame`,
  `mverify`, `encode`, `obj_final`, `link_rest`.

## Algorithmic fixes by module
- `compiler/mir/builder.ax`:
  - Indexed `MonoInstance` lookup in `mb_mono_find_or_create` and `mb_find_inst_by_new_item` via the per-compile item
    hash map instead of linear linked-list walks over all mono instances.
  - Indexed callee/trait-method resolution in `mb_scan_or_rewrite_calls` using the pre-built `expr_methods` table,
    eliminating repeated full-HIR walks per call site.
- `compiler/lir/builder.ax`:
  - Added per-compile `LirSymCache` (open-addressing hash tables for `sym_v -> fn item / formatted symbol name` and
    `sym_v -> const item`) cached on the interner arena so `get_fn_sym_name` and `get_const_table_sym_name` run in O(1)
    instead of scanning all HIR items per call/const reference.
- `compiler/backend/session.ax`:
  - Added per-compile `BackendSymCache` (open-addressing hash tables for `sym_v -> fn/const HirItem`) used by
    `backend_format_const_sym_name_cached` and `backend_find_fn_item_by_sym_cached` (eliminating O(F*N) walks in
    `backend_emit_const_tables` and `backend_resolve_body_call_types`).
  - Added `backend_lower_fn_to_mc_checked_timed` to accumulate per-pass sub-timers (`lir`, `abi`, `isel`, `frame`,
    `mverify`) across all functions.
- `compiler/target/x64/frame.ax`:
  - Rewrote liveness dataflow (`x64_compute_liveness_in_arena` / `liveness_solve_dataflow_csr`) and natural-loop
    detection (`liveness_mark_natural_loop_csr`) to use a CSR predecessor/successor edge layout with a dirty-bit
    worklist and bit-scanning (`frame_ctz_u64`), replacing dense O(B^2) block-pair scans.
  - Optimized spill-slot coloring range merging (`colored_slot_add_range`) and register-allocation loops in
    `x64_regalloc_with_pgo_in_arena`.
- `compiler/obj/coff.ax`:
  - Added lazy-synced open-addressing hash index `ObjSymIndex` on `ObjModel` mapping symbol name -> lowest-index
    `SymbolId` (exact match to prior linear search semantics), with invalidation via `objmodel_symbol_names_changed`.
  - Implemented `objsym_index_find_view` for `objmodel_find_symbol_str` to hash/compare directly through `view<[u8]>`
    (avoiding raw-pointer extraction from `Str`, which triggers MIR interpreter UB on `selfhost/obj/qa_obj_model.ax`
    and `selfhost/encode/qa_encode_relocs_and_frames.ax`).
- `compiler/link/pe.ax`:
  - Added lazy-synced open-addressing hash index `LinkerGlobalIndex` (`LinkerContext.gindex`) for `linker_find_global`
    and `linker_find_global_str`, with `lgi_find_view` hashing/comparing via `view<[u8]>` for MIR-interpreter safety.
  - Added per-name hash-chained index (`nx_slots` / `link_v2_next_same_name`) on `LinkV2Context` so
    `link_v2_find_def_meta`, `link_v2_find_def_meta_in_obj`, and `link_v2_find_ref_meta` walk only same-name chains.
- `compiler/link/linker.ax`:
  - Replaced O(S^2) per-object symbol deduplication and enclosing-function scans in `linker_load_coff_object_v2` with a
    per-object open-addressing name table (`lnk_name_probe`) and sorted section/offset binary search
    (`lnk_sort_cands` / `lnk_enclosing_fn`).
  - Replaced O(M^2) ABI-compat pair checks in `link_v2_check_abi_compat_all` with same-name chain iteration via
    `link_v2_next_same_name`.
- `compiler/driver/pipeline.ax`:
  - Replaced per-function linear walks in `driver_emit_objmodel_filtered_ex`, `pipe_emit_axmeta_section`,
    `pipe_format_demangled_sym`, and `pipe_bodies_ref_sym` with open-addressing hash tables built once per compile
    (mono clone table, trait member table, item-by-symbol table, and single-pass std-symbol reachability marking).
  - Invalidated `ObjSymIndex` after in-place symbol prefix stripping in `pipe_strip_unlinked_extern_c_prefixes`.
  - Added `time-build:` sub-timer accounting and formatting.
- `tests/selfhost/link/qa_pe_headers_and_imports.ax.in`:
  - Added `gindex: 0 as *mut compiler.link.pe.LinkerGlobalIndex,` to the 5 exhaustive `LinkerContext` struct literals.
- `tests/perf/build_scaling/build_scaling.py` & `tests/perf/build_scaling/build_scaling.test`:
  - Added scaling regression test verifying `build(4N) / build(N) <= 5.0` (with N=150, 4N=600) and executable exit 0.

## Before / after timings (large bundles)
Measured with `_workspaces/artifacts/T486/timing.py` (`SOURCE_DATE_EPOCH=0`, `--stack-reserve 67108864`,
`old = HEAD axiomc2`, `new = T486 axiomc2`):

| Bundle | Opt | `build` old | `build` new | `build` speedup | Wall old | Wall new | Byte-identical |
|---|---:|---:|---:|---:|---:|---:|---|
| `qa_backend_unit.ax` | `-O0` | 373.3 s | 32.2 s | **11.6x** | 421.6 s | 74.2 s | Yes (`30e90ce5e21bccf3`) |
| `qa_backend_unit.ax` | `-O1` | 516.3 s | 25.6 s | **20.2x** | 563.0 s | 66.6 s | Yes (`462923f0b71ef653`) |
| `axiomc_bundle(HEAD)` | `-O1` | 1041.9 s | 50.3 s | **20.7x** | 1128.3 s | 129.0 s | Yes (`fa1d7d6dc3d4e41c`) |
| `qa_backend_diff_mi_mc_b.ax` | `-O0` | 431.8 s | 26.9 s | **16.0x** | 489.3 s | 77.3 s | Yes (`98aec88922c62fec`) |

Post-fix sub-timer breakdown (`time-build:` lines from `_workspaces/artifacts/T486/timing.log`):

| Sub-phase | `qa_backend_unit -O0` | `qa_backend_unit -O1` | `axiomc_bundle -O1` | `qa_backend_diff_mi_mc_b -O0` |
|---|---:|---:|---:|---:|
| `async` | 0.002 s | 0.001 s | 0.003 s | 0.002 s |
| `mir_build` | 2.552 s | 1.845 s | 3.526 s | 1.805 s |
| `mir_drop` | 5.433 s | 4.299 s | 8.272 s | 4.359 s |
| `mir_opt` | 0.000 s | 0.160 s | 0.307 s | 0.000 s |
| `mir_callty` | 0.031 s | 0.024 s | 0.064 s | 0.026 s |
| `collect` | 0.121 s | 0.081 s | 0.109 s | 0.057 s |
| `consts` | 0.070 s | 0.014 s | 0.018 s | 0.075 s |
| `lir` | 2.835 s | 2.197 s | 4.916 s | 2.447 s |
| `abi` | 0.385 s | 0.299 s | 0.582 s | 0.336 s |
| `isel` | 3.139 s | 4.291 s | 8.396 s | 2.558 s |
| `frame` | 12.856 s | 9.737 s | 18.802 s | 10.931 s |
| `mverify` | 0.283 s | 0.122 s | 0.265 s | 0.253 s |
| `encode` | 2.044 s | 0.915 s | 1.746 s | 1.793 s |
| `obj_final` | 0.152 s | 0.136 s | 0.243 s | 0.138 s |
| `link_rest` | 2.253 s | 1.498 s | 3.044 s | 2.163 s |
| **Total `build`** | **32.157 s** | **25.616 s** | **50.292 s** | **26.942 s** |

## Scaling test (`tests/perf/build_scaling`)
Direct run with final `build-snap-T486/build/axiomc2.exe`:
- `units=150`: `build=2.122s`, `wall=4.481s`
- `units=600`: `build=6.852s`, `wall=24.492s`
- Ratio: `build(600) / build(150) = 3.23` (limit `<= 5.00`; linear ideal = `4.00`) -> `OK build scaling`.

## Byte-identity verification (SPEC-76 `INV-DET-004`)
Verified using `_workspaces/artifacts/T486/compare_exes.py` (with `SOURCE_DATE_EPOCH=0`) comparing HEAD `axiomc2`
against T486 `axiomc2` at both `-O0` and `-O1`:
- `tests/run/**` (`_workspaces/artifacts/T486/compare_run.txt`):
  `SUMMARY programs=803 builds=1606 identical=1584 DIFFERENT=0 both-fail=22 MISMATCH-RC=0`
- `tests/selfhost/**` (`_workspaces/artifacts/T486/compare_selfhost.log`):
  189 builds compared (`187 identical`, `2 both-fail` for `qa_pe_headers_and_imports.ax` prior to the `.ax.in` struct
  literal update, `0 DIFFERENT`, `0 MISMATCH-RC`).
- Post-final-build spot check with final `build-snap-T486/build/axiomc2.exe` (`sha256=7ea65ebb770b0ff2`) via
  `_workspaces/artifacts/T486/final_verify.py`:
  - `qa_pe_headers_and_imports.ax -O0`: `old(37.1s 140553f25d338fa4)` == `new(10.3s 140553f25d338fa4)` -> `identical=True`
  - `qa_pe_headers_and_imports.ax -O1`: `old(41.4s 20d05011f196f3f3)` == `new(11.0s 20d05011f196f3f3)` -> `identical=True`
  - `axiomc_bundle(HEAD) -O1`: `new(97.0s fa1d7d6dc3d4e41c)` matches recorded `old(fa1d7d6dc3d4e41c)` -> `identical=True`
- **0 byte differences and 0 exit-code mismatches across all compared builds.**

## Self-host bootstrap & fixed point
Built in `build-snap-T486` via `python tools/build_axiomc.py --out build --stage 3`:
- `REUSED axiom0.exe (inputs 2754e62dc264ce73)`
- `STAGE1 OK`: `axiomc1.exe` (26,883,072 bytes, `sha256=edbe5c78145d5dfd`, wall 74.59 s)
- `STAGE2 (O1) OK`: `axiomc2.exe` (8,304,128 bytes, `sha256=7ea65ebb770b0ff2`, wall 227.73 s)
- `STAGE3 (O1) OK`: `axiomc3.exe` (8,304,128 bytes, `sha256=7ea65ebb770b0ff2`, wall 81.67 s)
- `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == 7ea65ebb770b0ff28e173734d40e59d7d265b86227dce08a27aadafef9e21662` (8,304,128 bytes).

## Test gate (`tools/taskgate.py`)
Ran `python tools/taskgate.py --task T486 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2` inside `build-snap-T486` (HEAD `bd13d0c95a5a`, 80 changed snapshot files including regenerated bundles):
- `own`: 1 id, 1 result — **1 PASS, 0 FAIL** (`perf/build_scaling/build_scaling.test`)
- `affected`: 409 ids, 686 results — **668 PASS, 0 FAIL, 18 SKIP** (all 90 `selfhost` tests including `selfhost/link/qa_pe_headers_and_imports.ax`, `selfhost/obj/qa_obj_model.ax`, and `selfhost/encode/qa_encode_relocs_and_frames.ax` passed all legs)
- `smoke`: 31 ids, 52 results — **52 PASS, 0 FAIL**
- **Total (dedup)**: 426 ids, **TOTAL 716 PASS 698 FAIL 0 SKIP 18 XFAIL 0**
- `archcheck`: clean (exit 0) — 229 files scanned, 0 violations
- `WEAK-NATIVE`: 3 in the run; 0 in the task's own/changed tests
- `Baseline`: `BASELINE OK`
- `TASKGATE T486 exit=0`

## Files changed
- compiler/backend/session.ax
- compiler/driver/pipeline.ax
- compiler/link/linker.ax
- compiler/link/pe.ax
- compiler/lir/builder.ax
- compiler/mir/builder.ax
- compiler/obj/coff.ax
- compiler/target/x64/frame.ax
- tests/perf/build_scaling/build_scaling.py
- tests/perf/build_scaling/build_scaling.test
- tests/selfhost/link/qa_pe_headers_and_imports.ax.in

STATUS: COMPLETE round=0
