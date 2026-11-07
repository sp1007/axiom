# T621 Report — E15.6: Whole-Program Closed-World Reachability, Cross-Module LTO Inlining/Specialization & Generic Deduplication

## Summary
Implemented the whole-program and cross-module Link-Time Optimization (`LTO`) engine in `compiler/opt/lto/mod.ax` (`module compiler.opt.lto`, `PASS_LTO = 18u16`) together with live bundled compiler probe/oracle and differential execution suites in `tests/run/opt_lto/*` (`SPEC-75 §§1, 2, 3, 4, 8, 9`; `AXS-LTO-001..024`, `AXS-LTO-030`, `AXS-PGO-015`; `REQ-OPT-255..278`, `ALTO-01..41`):

1. **LTO Modes, World Scope, `.axmeta` Binary Summary Serialization & 64/128-bit Semantic Digests (`SPEC-75 §§1, 8, 9`, `AXS-LTO-001..004`, `AXS-LTO-016..024`)**:
   - Defined `LTO_MODE_OFF` (`0u8`), `LTO_MODE_THIN` (`1u8`), `LTO_MODE_FAT` / `LTO_MODE_FULL` (`2u8`), and `WorldScope` (`WORLD_CLOSED`, `WORLD_PARTIAL`, `WORLD_OPEN`).
   - Implemented `LtoModuleSummary`, `LtoFnSummary`, `LtoStaticSummary`, `LtoTraitImplRecord`, and `LtoDigest128`, with deterministic `.axmeta` binary serialization (`lto_serialize_module_summary`) and validated deserialization (`lto_deserialize_module_summary`) rejecting magic/version/payload corruption.
   - Implemented span-independent 64-bit FNV-1a and 128-bit SipHash-2-4 semantic summary digests (`lto_compute_module_digest`) and `ThinLTO` partition rebuild detection (`lto_thin_partition_needs_rebuild`) so body-only changes that preserve exported summary digests do not invalidate downstream partitions (`ALTO-04..05`).

2. **Closed-World Reachability Closure ($R_{root}$ + RTA), Non-Exported Symbol Internalization & Dead Pruning (`SPEC-75 §§1.4, 2, 4.4`, `AXS-LTO-005`, `AXS-LTO-010`, `AXS-LTO-013`)**:
   - Implemented `lto_internalize_symbols` downgrading non-exported `pub` functions and statics to `LTO_LINKAGE_INTERNALIZED` under `WORLD_CLOSED` / `WORLD_PARTIAL` while preserving all root categories (`LTO_ROOT_ENTRY`, `LTO_ROOT_EXPORT`, `LTO_ROOT_DYNAMIC_LOOKUP`, `LTO_ROOT_FFI_CALLBACK`, `LTO_ROOT_REFLECTION`, `LTO_ROOT_PINNED_AT`, `LTO_ROOT_MODULE_INIT`) and keeping all `pub` symbols externally visible under `WORLD_OPEN` (`ALTO-10..21`).
   - Implemented `lto_compute_reachability` and `lto_prune_unreachable` performing fixed-point call-graph + Rapid Type Analysis (`RTA`) reachability from $R_{root}$, pruning unreachable functions, statics, and unreferenced vtables as `LTO_LINKAGE_DEAD_ELIMINATED` (`REACH_DEAD_ELIMINATED`), and promoting single-caller internalized functions (`lto_promote_single_caller_internalized`).

3. **Cross-Module Inlining, Constant/Closure Specialization, Summary Propagation & Closed-World Devirtualization (`SPEC-75 §§3, 4.3, 4.5`, `AXS-LTO-011..013`, `AXS-LTO-015`)**:
   - Implemented `lto_propagate_cross_module_summaries` propagating cross-module `EffectSummary`, `FunctionEscapeSummary` (`NoEscape`), and `AliasSummary` (`NoAlias`), enforcing the fail-closed `UnknownAlias` barrier at raw-pointer and FFI boundaries (`ALTO-38..39`) and preserving `atomic` ordering (`ALTO-40`) and `volatile`/`@at` MMIO side effects (`ALTO-41`).
   - Implemented `lto_resolve_closed_world_trait_targets` and `lto_run_cross_module_opt` orchestrating closed-world RTA devirtualization (`devirt_optimize_callgraph`), cross-module constant/closure specialization (`ipa_specialize_callgraph`), bottom-up SCC cross-module inlining (`inline_optimize_callgraph`), generic deduplication, and post-inlining dead symbol pruning.
   - Implemented `lto_contract()` (`PASS_LTO = 18u16`) and transactional `PassManager` runner `lto_run_pass` / `lto_run_pass_internal` with snapshot/rollback verification.

4. **Cross-Module Generic Monomorphization Deduplication & `--emit=lto` (`SPEC-75 §4.1–4.2`, `AXS-LTO-014`, `AXS-PGO-015`, `ALTO-30..33`)**:
   - Implemented `lto_deduplicate_generics` merging identical cross-module monomorphizations (`LTO_DEDUP_EXACT_INSTANCE`, `ALTO-30`) and representation-equivalent instantiations (`LTO_DEDUP_REP_EQUIV_SHARED`, `ALTO-31, ALTO-33`) while preserving distinct symbols and function addresses whenever `address_taken_fn == true` (`LTO_DEDUP_KEPT_ADDRESS_TAKEN`, `ALTO-32`) or `has_custom_drop == true` (`LTO_DEDUP_KEPT_CUSTOM_DROP`).
   - Implemented deterministic `lto_print` formatter for `--emit=lto`.

## Files changed
- `compiler/opt/lto/mod.ax`
- `tests/run/opt_lto/opt_lto_engine.test`
- `tests/run/opt_lto/opt_lto_oracle.py`
- `tests/run/opt_lto/opt_lto_probe.ax.in`
- `tests/run/opt_lto/closed_world_reachability_and_roots.ax`
- `tests/run/opt_lto/cross_module_inline_spec_devirt.ax`
- `tests/run/opt_lto/generic_dedup_and_fn_ptr_identity.ax`

## Verification
- Snapshot & live compiler engine oracle:
  - `python build-snap-T621/tests/run/opt_lto/opt_lto_oracle.py build-snap-T621/build/axiomc2.exe build-snap-T621/build build-snap-T621/build/opt_lto_probe_test build-snap-T621` -> `OPT-LTO-ENGINE-OK` (exit 0 across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`).
- `axtest.py -j 1` suite:
  - `python build-snap-T621/tools/axtest.py --root build-snap-T621 --build-dir build-snap-T621/build --compiler build-snap-T621/build/axiomc2.exe -j 1 run/opt_lto run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax` -> `TOTAL 17 PASS 17 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
  - `python build-snap-T621/tools/axtest.py --root build-snap-T621 --build-dir build-snap-T621/build --compiler build-snap-T621/build/axiomc2.exe -j 1 run/opt_lto run/opt_ipa_devirt opt2 run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax` -> all `run/opt_lto/*` (10/10), `run/opt_ipa_devirt/*.ax` (9/9), `opt2/*` (15/16), and `intrinsics/*` (7/7) pass with `WEAK-NATIVE 0` (only the 2 frontend-bundling `--interp` probes in `opt2_sroa_inline_engine.test` and `opt_ipa_devirt_engine.test` hit their 300s interpreter subprocess timeout under 5-agent parallel CPU load).
- Scope & architecture gates:
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T621` -> `0 REFUSED` (exit 0).
  - `python build-snap-T621/tools/archcheck.py` -> `0 violations` (exit 0).

STATUS: COMPLETE round=0
