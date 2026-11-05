STATUS: COMPLETE round=1

# T606 Report — E15.2 Capability-Aware AliasInfo, Provenance Disjointness & MemorySSA Store-to-Load/DSE Optimization

## Summary

1. **Capability-Aware Alias Lattice, Region Provenance & Spatial Disjointness (`compiler/opt/alias/mod.ax`, `SPEC-71 §1.1-§1.6`, `AXS-ALIAS-001..005`, `AXS-ESC-017`)**:
   - Implemented the 5-value `AliasResult` lattice (`ALIAS_NO_ALIAS`, `ALIAS_MUST_ALIAS`, `ALIAS_MAY_ALIAS`, `ALIAS_PARTIAL_ALIAS`, `ALIAS_UNKNOWN`), 6-value `RegionRelation` (`REGION_DISJOINT`, `REGION_SAME`, `REGION_CONTAINS`, `REGION_CONTAINED_BY`, `REGION_OVERLAPS`, `REGION_UNKNOWN`), 9-domain `StorageDomain` (`DOMAIN_STACK_LOCAL`, `DOMAIN_HEAP_BOX`, `DOMAIN_VIEW_BORROW`, `DOMAIN_RAW_PTR`, `DOMAIN_CONST_RDATA`, `DOMAIN_GLOBAL_MUT`, `DOMAIN_FIXED_MMIO`, `DOMAIN_DEVICE_DMA`, `DOMAIN_UNKNOWN`), 5-mode `CapabilityMode`, 12 `AliasReason` provenance codes, `AliasRegion`, `AliasFact`, `LocalProvenance`, `ZeroCopyPin`, and `AliasInfo` (`REQ-OPT-358`).
   - Implemented `alias_init_info` and `alias_build_info`, running 4-round fixed-point provenance propagation across `MIR_RVALUE_REF`, copy/move aliases, `MIR_RVALUE_CAST` (`PtrToPtr` vs integer-to-pointer `Provenance.Unknown`), `address_of` / `address_of_mut`, `ptr_add` / `ptr_sub` constant element offsets, and external/FFI exposure.
   - Enforced Stack-Slot vs Pointee domain separation in `alias_extract_region` so non-deref local places (`_k`, `_k.f`, `_k[i]`) model the stack storage of `_k` (`DOMAIN_STACK_LOCAL`) while dereferenced places (`(*_k)...`) model referent provenance (`DOMAIN_VIEW_BORROW` / `DOMAIN_RAW_PTR` / `DOMAIN_FIXED_MMIO`).
   - Implemented `alias_query_regions` and `alias_query_places` covering:
     - Concurrent `mut_view<T>` disjointness (`ALIAS_REASON_CAP_MUT_DISJOINT`) gated by CFG capability-liveness window intersection (`al_caps_concurrently_active`, `SPEC-11 AXS-CAP-009`), degrading sequential reborrows after capability end to `MayAlias` / `MustAlias` rather than falsely claiming `NoAlias`.
     - Concurrent `view<T>` vs `mut_view<T>` non-overlap (`ALIAS_REASON_CAP_VIEW_READONLY`).
     - Distinct struct field (`ALIAS_REASON_FIELD_DISJOINT`), enum downcast variant, constant array index (`ALIAS_REASON_CONST_INDEX`), affine offset / range-disjoint index (`ALIAS_REASON_RANGE_DISJOINT`), adjacent half-open subslice (`[..mid)` vs `[mid..)`), and whole-vs-field `PartialAlias` (`REGION_CONTAINS` / `REGION_CONTAINED_BY`, `ALIAS_REASON_SUBREGION_CONTAINS`).
     - Fail-closed raw-pointer integer-to-pointer / unknown provenance (`ALIAS_UNKNOWN`, `CERTAINTY_UNKNOWN`, `ALIAS_REASON_RAW_PTR_PROVENANCE`) and shared-ownership `Arc<T>` / `Rc<T>` handles (`ALIAS_MAY_ALIAS`, `CERTAINTY_POSSIBLE`, `ALIAS_REASON_SHARED_OWNER`).
   - Implemented `alias_register_zero_copy_pin`, `alias_local_is_zero_copy_pinned_at`, and `alias_verify_zero_copy_path` (`REQ-OPT-347`), verifying `NoAlias` (`CERTAINTY_PROVEN`), non-MMIO domain, capability lifetime coverage `[transfer_start, transfer_end]`, and absence of overlapping mutations across the transfer window.
   - Implemented deterministic table materialization (`alias_populate_all_facts`) and byte-equal diagnostic formatting (`alias_print`, `AXS-ESC-017`) with zero string literals in compiler source.

2. **`MemAccessKind`, `MemDependence`, Store-to-Load Forwarding, `view<T>` RLE, DSE & Memory Intrinsics (`compiler/opt/memopt/mod.ax`, `SPEC-71 §1.7-§1.8 & §3.6-§3.7`, `AXS-ALIAS-006`, `AXS-ESC-016..017`)**:
   - Implemented all 17 `MemAccessKind` classifications (`MEM_ACCESS_NONE`, `LOAD`, `STORE`, `INIT`, `MOVE`, `COPY`, `DROP`, `VOLATILE_LOAD`, `VOLATILE_STORE`, `ATOMIC_LOAD`, `ATOMIC_STORE`, `ATOMIC_RMW`, `FENCE`, `MEMCPY`, `MEMMOVE`, `MEMSET`, `BARRIER`, `ALLOC`, `DEALLOC` in `memopt_classify_inst` / `memopt_classify_term`) and 4-value `MemDependence` (`NO_DEPEND`, `MUST_DEPEND`, `MAY_DEPEND`, `UNKNOWN_DEPEND` in `memopt_query_dependence`) (`REQ-OPT-365`).
   - Implemented CFG all-paths clobber verification (`memopt_place_clobbered_on_path`, `memopt_inst_clobbers_place`, `memopt_call_clobbers_place`) that traverses loop backedges entering dominating blocks so loop-carried stores block invalid cross-iteration forwarding (`REQ-OPT-366`).
   - Implemented dominator-walked Store-to-Load Forwarding and `view<T>` Redundant Load Elimination (`memopt_run_forwarding_and_rle`), requiring `MustAlias` (`CERTAINTY_PROVEN`), exact scalar `Copy` type compatibility, unclobbered source operand and loaded place across all CFG paths, and emitting `ProofProvenance` (`PROP_NO_ALIAS`, `CERTAINTY_PROVEN`, `ANALYSIS_ALIAS_INFO`) (`REQ-OPT-366`).
   - Implemented all-forward-paths BFS Dead Store Elimination (`memopt_prove_dead_store`, `memopt_run_dse`) for post-dominating `MustAlias` (`CERTAINTY_PROVEN`) full-type overwrites and `StorageDead` / `return` deaths of strict non-escaped stack locals (including array/struct/tuple/enum aggregates), recording `PROP_DEAD_STORE` provenance (`REQ-OPT-366`).
   - Enforced strict barrier preservation across forwarding, RLE, and DSE: volatile/MMIO loads & stores (`REQ-OPT-313`), atomic loads/stores/RMW & fences (`REQ-OPT-312`), foreign/FFI & unknown calls (`REQ-OPT-314`), active zero-copy/DMA pinned regions (`REQ-OPT-347`), `OPT_INST_ZEROIZE`, `OPT_INST_BLACK_BOX`, `Drop` terminators / drop flags, and panic/unwind-visible stores.
   - Implemented `memopt_can_promote_memmove_to_memcpy` and `memopt_run_mem_intrinsics` (`TY_BUILTIN_PTR_COPY` -> `TY_BUILTIN_PTR_COPY_NONOVERLAPPING` when `NoAlias` is `CERTAINTY_PROVEN`, plus zero-valid `TY_BUILTIN_PTR_WRITE_BYTES` `memset` recognition excluding MMIO).
   - Integrated `memopt_contract`, `memopt_run_pass_with_info`, `memopt_run_pass`, `memopt_run_pipeline`, `memopt_optimize_mir_body` (enforcing `-O0` strict no-op, `PassManager` snapshot/rollback, `optir_verify_contract`, and `verify_mir`), and deterministic `memopt_print` (`AXS-ESC-016`, `AXS-ESC-017`).

3. **Differential & Direct Engine Verification Suite (`tests/run/opt_alias/`)**:
   - Added positive, negative/barrier, and loop-backedge/partial-alias/sequential-reborrow/multi-origin differential fixtures (`cap_mut_view_forwarding_rle_dse.ax`, `raw_ptr_volatile_atomic_barriers.ax`, `loop_backedge_and_partial_alias_clobbers.ax`) with UTF-8 Vietnamese banners, `Drop` ordering, `ptr_copy` / `ptr_add` / `write_bytes` raw-pointer workflows, and multi-branch view origins.
   - Added `opt_alias_engine.test` (`opt_alias_oracle.py` + `opt_alias_probe.ax.in`) compiling and executing `compiler.opt.alias` and `compiler.opt.memopt` directly under `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each`, verifying the capability/provenance lattice, forwarding + RLE + overwrite/dead-local DSE, volatile/atomic/FFI/zero-copy barriers, `memmove -> memcpy` + `memset`, loop-backedge clobber blocking, deterministic `alias_print` / `memopt_print` / `--emit=optir` / `--emit=memssa`, and differential execution across `--interp`, `-O0`, `-O1`, and `-O2`.

## Requirement Coverage

| Requirement | Spec Anchor | Implementation & Verification |
| --- | --- | --- |
| `REQ-OPT-312` | `SPEC-71 §1.7-§1.8` (`AXS-ALIAS-006`) | Atomic loads, stores, RMW (`OPT_INST_ATOMIC`, `EFFECT_ATOMIC`), and fences classified as `MEM_ACCESS_ATOMIC_*` / `MEM_ACCESS_FENCE` (`MEM_DEP_UNKNOWN_DEPEND`) and preserved as strict barriers (`BARRIER_ATOMIC`) blocking forwarding, RLE, reordering, and DSE (`compiler/opt/memopt/mod.ax`, `opt_alias_probe.ax.in`). |
| `REQ-OPT-313` | `SPEC-71 §1.7-§1.8` (`AXS-ALIAS-006`) | Volatile accesses (`OPT_INST_VOLATILE_LOAD`, `OPT_INST_VOLATILE_STORE`, `EFFECT_VOLATILE`) and `DOMAIN_FIXED_MMIO` regions classified as `MEM_ACCESS_VOLATILE_*` (`MEM_DEP_UNKNOWN_DEPEND`) and preserved as strict barriers (`BARRIER_VOLATILE`) across forwarding, RLE, DSE, zero-copy pinning, and `memset` (`compiler/opt/alias/mod.ax`, `compiler/opt/memopt/mod.ax`, `opt_alias_probe.ax.in`). |
| `REQ-OPT-314` | `SPEC-71 §1.5, §1.7` (`AXS-ALIAS-005`, `AXS-ALIAS-006`) | `EFFECT_FFI` and `EFFECT_UNKNOWN` calls mark exposed pointer roots externally escaped, clobber caller/escaped memory (`BARRIER_FFI`), and block store-to-load forwarding, `view<T>` RLE, and DSE across foreign boundaries while keeping unborrowed `NoEscape` stack locals isolated (`compiler/opt/alias/mod.ax`, `compiler/opt/memopt/mod.ax`, `opt_alias_probe.ax.in`). |
| `REQ-OPT-347` | `SPEC-71 §1.6, §1.8` (`AXS-ALIAS-005`, `AXS-ALIAS-006`) | `ZeroCopyPin` tracking (`alias_register_zero_copy_pin`, `alias_local_is_zero_copy_pinned_at`, `alias_verify_zero_copy_path`) verifies `NoAlias` (`CERTAINTY_PROVEN`), non-MMIO storage, capability lifetime coverage, and zero overlapping writes across `[transfer_start, transfer_end]`, while pinning active buffers against DSE (`BARRIER_ZERO_COPY`) (`compiler/opt/alias/mod.ax`, `compiler/opt/memopt/mod.ax`, `opt_alias_probe.ax.in`). |
| `REQ-OPT-358` | `SPEC-71 §1.1-§1.6` (`AXS-ALIAS-001..005`) | Capability-aware `AliasInfo` proves `NoAlias` (`CERTAINTY_PROVEN`) for concurrently active `mut_view<T>` capabilities (`ALIAS_REASON_CAP_MUT_DISJOINT`), concurrent `view<T>` vs `mut_view<T>` (`ALIAS_REASON_CAP_VIEW_READONLY`), distinct struct fields, constant/range-disjoint array indices & subslices, and `NoEscape` stack allocations, while failing closed on raw pointers (`UnknownAlias`), `Shared<T>` (`MayAlias`), sequential reborrows, and `PartialAlias` (`compiler/opt/alias/mod.ax`, `cap_mut_view_forwarding_rle_dse.ax`, `loop_backedge_and_partial_alias_clobbers.ax`, `opt_alias_probe.ax.in`). |
| `REQ-OPT-365` | `SPEC-71 §1.7` (`AXS-ALIAS-006`) | 17-kind `MemAccessKind` (`memopt_classify_inst`, `memopt_classify_term`) and 4-value `MemDependence` (`memopt_query_dependence`) classify loads, stores, inits, moves, copies, drops, volatile/atomic ops, fences, `memcpy`/`memmove`/`memset`, and barriers (`compiler/opt/memopt/mod.ax`, `opt_alias_probe.ax.in`). |
| `REQ-OPT-366` | `SPEC-71 §1.8, §3.6-§3.7` (`AXS-ALIAS-006`, `AXS-ESC-016..017`) | Proof-gated MemorySSA store-to-load forwarding, `view<T>` redundant load elimination, post-dominating overwrite & dead-local DSE, and `memmove -> memcpy` / `memset` optimization with `PassManager` contract verification, `-O0` no-op, loop-backedge clobber safety, and deterministic `alias_print` / `memopt_print` (`compiler/opt/memopt/mod.ax`, `cap_mut_view_forwarding_rle_dse.ax`, `raw_ptr_volatile_atomic_barriers.ax`, `loop_backedge_and_partial_alias_clobbers.ax`, `opt_alias_probe.ax.in`). |

## Files changed

- compiler/opt/alias/mod.ax
- compiler/opt/memopt/mod.ax
- tests/run/opt_alias/cap_mut_view_forwarding_rle_dse.ax
- tests/run/opt_alias/loop_backedge_and_partial_alias_clobbers.ax
- tests/run/opt_alias/opt_alias_engine.test
- tests/run/opt_alias/opt_alias_oracle.py
- tests/run/opt_alias/opt_alias_probe.ax.in
- tests/run/opt_alias/qa_boundary_alias_clobbers.ax
- tests/run/opt_alias/raw_ptr_volatile_atomic_barriers.ax

## Verification

- Stage-1, Stage-2 (`O1`), and Stage-3 (`O1`) self-host fixed-point build in `build-snap-T606`:
  - `python build-snap-T606/tools/build_axiomc.py --root build-snap-T606 --out build-snap-T606/build --stage 3`:
    - `STAGE1 OK`: `19860480` bytes, `sha256=03a2ed6623553b59`
    - `STAGE2 (O1) OK`: `6142976` bytes, `sha256=3d2e5f3db21faa8f`
    - `STAGE3 (O1) OK`: `6142976` bytes, `sha256=3d2e5f3db21faa8f`
    - `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == 3d2e5f3db21faa8f70435d646a79a1dd02415b37ee57c41acc733a949620acb6`
- Capability alias & MemorySSA memopt suite (`-j 1`):
  - `python build-snap-T606/tools/axtest.py --root build-snap-T606 --compiler build-snap-T606/build/axiomc2.exe --build-dir build-snap-T606/build --exclude-requires axiom0-internal -j 1 --verbose run/opt_alias`: `WEAK-NATIVE 0`, `TOTAL 10 PASS 10 FAIL 0 SKIP 0 XFAIL 0` (including `opt_alias_engine.test` across `-O0 --verify-each`, `-O1 --verify-each`, `-O2 --verify-each`, and `--interp`).
- Optimizer, `OptIR`, `PassManager`, self-host optimizer, MIR, and verifier regression suites (`-j 1`):
  - `python build-snap-T606/tools/axtest.py --root build-snap-T606 --compiler build-snap-T606/build/axiomc2.exe --build-dir build-snap-T606/build --exclude-requires axiom0-internal -j 1 --verbose run/opt_passmgr run/optir_ssa selfhost/opt`: `WEAK-NATIVE 0`, `TOTAL 21 PASS 21 FAIL 0 SKIP 0 XFAIL 0`.
  - `python build-snap-T606/tools/axtest.py --root build-snap-T606 --compiler build-snap-T606/build/axiomc2.exe --build-dir build-snap-T606/build --exclude-requires axiom0-internal -j 1 mir/ verify/`: `WEAK-NATIVE 0`, `TOTAL 111 PASS 110 FAIL 0 SKIP 1 XFAIL 0`.
- Repository gates:
  - `python tools/archcheck.py`: `0 violations`.
  - `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `COVERAGE OK` (`gaps: 0`).
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T606`: exit `0` (`0 REFUSED`).

## Round 1

Resolved all 4 blocking QA findings from `_workspaces/reports/T606-qa.md` at their root causes:

1. **Finding 1 (Interior `MIR_PROJ_DEREF` after field/index projections — `*(s.mv)` / `*(w.p)`)**:
   - In `compiler/opt/alias/mod.ax`: Added `al_place_has_deref`, `al_place_last_deref_idx`, `al_place_prefix_ty`, and `AliasRegion.is_interior_deref`. Separated `alias_extract_region` and `alias_init_info` into `last_d == proj_count` (stack/rdata slot), `last_d == 0` (leading capability/pointer deref), and `last_d >= 1` (interior deref `is_interior_deref = true`, `alloc_root = ALLOC_ROOT_UNKNOWN`, `has_resolved_place = false`, capability/domain derived from the pointer prefix type before `last_d`). Guarded `alias_relate_projection_paths` (`MIR_PROJ_DEREF -> REGION_UNKNOWN`), `alias_query_regions` (never proving `MustAlias` or root-disjoint `NoAlias` on `is_interior_deref` regions), and `alias_is_view_readonly_region` (`!reg.is_interior_deref`), and lifted aggregate/projected borrow and raw-pointer exposure tracking outside `dst_pl.proj_count == 0`.
   - In `compiler/opt/memopt/mod.ax`: Updated `mo_place_is_strict_noescape_local` to reject any place containing `MIR_PROJ_DEREF`; guarded `view<T>` RLE against interior derefs (`!mo_place_has_deref_from(target_place, 1)`); added `mo_make_prefix_place`, `mo_inst_clobbers_any_dep_of_place`, and `mo_term_clobbers_any_dep_of_place` across `memopt_inst_clobbers_place`, `memopt_call_clobbers_place`, `mo_try_dominating_candidate_for_load`, `mo_dse_step_inst`, and `memopt_prove_dead_store`; and extended `mo_place_reads_aliasing` + `mo_lhs_place_deref_or_index_reads_aliasing` to recursively scan every `MIR_PROJ_DEREF` pointer prefix (`s.p` in `*(s.p)`), `MIR_PROJ_INDEX`, and `MIR_PROJ_SUB_SLICE` on both RHS reads and LHS writes.
2. **Finding 2 (`mut_view` reborrow chains, sibling sub-borrows, and capability concurrency intervals)**:
   - In `compiler/opt/alias/mod.ax`: Added `CAP_ROOT_NONE`, `CAP_ROOT_AMBIGUOUS`, `LocalProvenance.cap_root_local`, `has_cap_subplace`, and `cap_subplace`, propagating canonical root capability identity and composed projection subplaces across multi-hop capability reborrows (`_sub = &mut (*_m)`, `_sub2 = &mut (*_sub)`, `_f0 = &mut (*_p).0`) while marking multi-def/merged capabilities `CAP_ROOT_AMBIGUOUS`. Updated Step 4 of `alias_query_regions` to relate shared-`cap_root_local` regions structurally (`MustAlias` for `(*_m)` vs `(*_sub)`, `PartialAlias`/`REGION_CONTAINS` for `(*_p)` vs `(*_f0)`, `NoAlias`/`ALIAS_REASON_FIELD_DISJOINT` for `(*_f0)` vs `(*_f1)`), assigned distinct `ALLOC_ROOT_PARAM_BASE + l` roots to single-def `mut_view` args vs shared `ALLOC_ROOT_PARAM_BASE` for `view` args, replaced `al_caps_concurrently_active` with program-point-sensitive `al_caps_concurrently_active_at` (requiring distinct non-ambiguous `cap_root_local`s, `def_count == 1`, dominance, backward `StorageDead` non-kill check `al_cap_killed_before_point`, and live forward uses from `prog_pt`, without any `ALIAS_PT_WHOLE_END` bypass for local capabilities), and checked `[transfer_start, transfer_end]` against `[fact_start, fact_end]` in `alias_verify_zero_copy_path`.
3. **Finding 3 (Indirect mutation of index/base/pointer locals in `alias_count_local_defs` and `memopt`)**:
   - In `compiler/opt/alias/mod.ax`: Updated `alias_count_local_defs` (`al_body_has_raw_ptr_cast` + `indirect_hazard`) to count non-deref projected writes (`_s.0 = ...`), non-deref mutable borrows (`&mut loc_v`), non-deref shared borrows in bodies containing raw-pointer casts, and non-deref `address_of` / `address_of_mut` calls as multiple/indirect definitions (`cnt + 2u32`), preventing `al_local_single_const_u64`, `al_local_index_bounds`, `al_local_affine_offset`, and single-def provenance propagation from treating indirectly-mutated locals as constants.
   - In `compiler/opt/memopt/mod.ax`: Wired `mo_inst_clobbers_any_dep_of_place` and `mo_term_clobbers_any_dep_of_place` into candidate search, path clobber checks, and DSE (`OPT_TERM_CALL` checked before `mt.has_destination`).
4. **Finding 4 (`MIR_PROJ_DOWNCAST` enum variant overlap, variant field types, and unresolved `TypeId(0)` extent)**:
   - In `compiler/opt/alias/mod.ax`: Updated `alias_place_access_ty` and `al_place_prefix_ty` to resolve `MIR_PROJ_DOWNCAST` + `MIR_PROJ_FIELD` against `TY_ENUM` (`variant_count`, `variant_field_counts`, `variant_fields`, plus `TY_SLICE | TY_ARRAY` on `MIR_PROJ_DEREF`); changed `alias_relate_projection_paths` on `MIR_PROJ_DOWNCAST` with `va != vb` from `REGION_DISJOINT` to `REGION_OVERLAPS` (`ALIAS_REASON_SUBREGION_CONTAINS`); and tightened `al_fact_from_spatial_rel` so `REGION_SAME` requires `ty_a.v != 0u32 && ty_a.v == ty_b.v` before returning `ALIAS_MUST_ALIAS` (`CERTAINTY_PROVEN`), otherwise degrading to `ALIAS_PARTIAL_ALIAS` (`CERTAINTY_POSSIBLE`), and `REGION_OVERLAPS` uses `CERTAINTY_POSSIBLE`.

### Round 1 Verification

- Added `qa_boundary_alias_clobbers.ax` to `POSITIVE_FIXTURES` in `tests/run/opt_alias/opt_alias_oracle.py` and added MIR reproducer blobs `5..8` + `verify_qa_round1_regressions` in `tests/run/opt_alias/opt_alias_probe.ax.in` directly asserting all 4 QA root-cause invariants across `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each`.
- Stage-3 (`O1`) fixed-point build in `build-snap-T606`:
  - `STAGE1 OK`: `19860480` bytes, `sha256=03a2ed6623553b59`
  - `STAGE2 (O1) OK`: `6142976` bytes, `sha256=3d2e5f3db21faa8f`
  - `STAGE3 (O1) OK`: `6142976` bytes, `sha256=3d2e5f3db21faa8f`
  - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == 3d2e5f3db21faa8f70435d646a79a1dd02415b37ee57c41acc733a949620acb6`
- Regression suites (`-j 1`, `WEAK-NATIVE 0`):
  - `run/opt_alias`: `TOTAL 13 PASS 13 FAIL 0 SKIP 0 XFAIL 0`
  - `run/opt_passmgr run/optir_ssa run/opt_scalar run/opt_effects selfhost/opt run/intrinsics`: `TOTAL 71 PASS 71 FAIL 0 SKIP 0 XFAIL 0`
  - `mir/ verify/`: `TOTAL 111 PASS 110 FAIL 0 SKIP 1 XFAIL 0`

STATUS: COMPLETE round=1
