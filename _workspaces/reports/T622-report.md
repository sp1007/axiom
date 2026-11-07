STATUS: COMPLETE round=0
# T622 Report — E15.6: Linker Section GC (COMDAT/Dead Stripping), Safe Identical Code Folding (ICF) & Deterministic PGO Pipeline

## Summary
Implemented the linker section garbage collection & Safe Identical Code Folding (`ICF`) engine in `compiler/link/gc_icf/mod.ax` (`module compiler.link.gc_icf`, `PASS_SECTION_GC_ICF = 20u16`) and the deterministic Profile-Guided Optimization (`PGO`) pipeline in `compiler/opt/pgo/mod.ax` (`module compiler.opt.pgo`, `PASS_PGO = 19u16`), together with the live bundled engine probe/oracle and differential execution suites in `tests/run/opt_pgo_gc/*` (`SPEC-04` `AXS-EXT-071`, `SPEC-75 §§5–11`, `AXS-LTO-025..029`, `AXS-PGO-001..015`):

1. **Function/Data Section Partitioning, Linker Section GC & Formal Root Set (`SPEC-75 §§5.1, 6`, `AXS-LTO-026..027`, `AXS-PGO-009..011`)**:
   - Defined `SectionGraph`, `SectionNode`, `RelocEdge`, `ComdatGroup`, `SectionGcIcfStats`, and `BinarySizeModel` in `compiler/link/gc_icf/mod.ax`.
   - Implemented per-function `.text$<symbol>`, `.text.cold$<symbol>`, `.rdata$<symbol>`, `.data$<symbol>`, `.bss$<symbol>`, and `.pdata`/`.xdata` section partitioning with explicit `.pdata`/`.xdata` unwind reverse-dependency metadata (`SEC_FLAG_REVERSE_DEP`, `AXS-PGO-010.3`) so unwind tables do not artificially keep dead `.text$<fn>` sections alive and are reclaimed iff their target `.text$<fn>` is discarded.
   - Implemented deterministic COMDAT selection (`COMDAT_NODUPLICATES`, `COMDAT_ANY`, `COMDAT_EXACT_MATCH`, `COMDAT_LARGEST`) with fail-closed `COMDAT_EXACT_MATCH` size/digest mismatch detection (`section_graph_resolve_comdats`) and worklist mark-sweep reachability (`section_graph_mark_live_and_sweep`) from $R_{\text{root}}$ (`ROOT_ENTRY`, `ROOT_EXPORT`, `ROOT_USED_ATTR`, `ROOT_PINNED_AT_MMIO`, `ROOT_TLS_CTOR_DTOR`, `ROOT_UNWIND_KEEP`, `ROOT_LTO_LIVE`).

2. **Safe Identical Code Folding (ICF), Read-Only Constant/String Pooling, Zero-Initialized `.bss` Promotion & 3D Size Model (`SPEC-75 §§5.2–5.3, 7, 10`, `AXS-LTO-025`, `AXS-LTO-028`, `AXS-PGO-012`)**:
   - Implemented `section_graph_compute_icf_hash` and `section_graph_run_safe_icf` folding byte-for-byte + relocation-equivalent read-only `.text$<fn>` sections when not address-taken (`ICF_DECISION_FOLDED`), emitting a 5-byte relative jump thunk (`0xE9 rel32`, `ICF_DECISION_THUNKED_ADDR_TAKEN`) when `address_taken_fn == true` so distinct function pointer identities (`f as usize != g as usize`) are preserved while sharing implementation bodies (`AXS-PGO-012.2`).
   - Enforced strict no-fold barriers (`ICF_DECISION_KEPT_MUTABLE_OR_PINNED`) for mutable `.data`/`.bss`, `@at(addr)` / `volatile` MMIO, and custom linker sections.
   - Implemented read-only `.rdata` constant/UTF-8 string pooling (`section_graph_merge_readonly_data`), all-zero initialized `.data` -> `.bss` promotion (`section_graph_promote_zero_data_to_bss`), 3D binary size accounting (`file_size_bytes`, `mapped_size_bytes`, `working_set_bytes`), 128-bit link cache identity (`link_compute_cache_identity`), and deterministic `--emit=section-gc` output (`section_gc_print`).

3. **Deterministic PGO (`--pgo-gen` / `--pgo-use`), `.axprof` Binary Schema, Weighted Merging & Stale-Profile Fallback (`SPEC-75 §11`, `AXS-PGO-001..005`)**:
   - Implemented `PgoProfileData`, `PgoFnProfile`, `PgoBranchRecord`, `PgoCallTargetRecord`, `PgoLoopRecord`, and `PgoValueSiteRecord` in `compiler/opt/pgo/mod.ax`.
   - Implemented `--pgo-gen` CFG structural fingerprinting (`pgo_compute_cfg_fingerprint`) and instrumentation planning (`pgo_instrument_body`), `.axprof` binary serialization (`pgo_serialize_profile`) and bounds-checked deserialization (`pgo_deserialize_profile`) with canonical `fn_sym.v` ordering and 64-bit FNV-1a integrity digest (`pgo_compute_profile_digest`), saturating 64-bit weighted profile merging (`pgo_merge_profiles`), and 4-level function compatibility classification (`PGO_COMPAT_EXACT`, `PGO_COMPAT_COMPATIBLE`, `PGO_COMPAT_STALE`, `PGO_COMPAT_INCOMPATIBLE`, `pgo_classify_and_bind_function`) with graceful stale-profile fallback.

4. **PGO Epistemic Safety Law, Cost-Model Guidance, Security Barriers & PassManager Integration (`SPEC-75 §11.2, §11.6–11.8`, `AXS-PGO-002`, `AXS-PGO-006..008`, `AXS-PGO-015`)**:
   - Enforced the PGO epistemic invariant (`pgo_verify_epistemic_law`): 0-count cold blocks keep all IR instructions and safety checks intact (`!is_unreachable`) and are never rewritten to `OPT_TERM_UNREACHABLE`.
   - Implemented profile-guided inlining multiplier (`pgo_compute_inline_multiplier`), indirect/trait speculative devirtualization with mandatory type/fn-ptr guard (`pgo_evaluate_callsite_devirt`), branch layout + unpredictable 50/50 branchless `cmovcc` (`pgo_evaluate_branch_layout`), loop unroll/peel/vectorize guidance (`pgo_evaluate_loop_policy`), hot/cold `.text.cold$<symbol>` splitting (`pgo_compute_hot_cold_split`), constant-time secret (`zeroize`/`black_box`) and `atomic`/`volatile` barriers, transactional `PassManager` runners (`pgo_run_pass_internal`), and deterministic `--emit=pgo` output (`pgo_print`).

## Files changed
- compiler/link/gc_icf/mod.ax
- compiler/opt/pgo/mod.ax
- tests/run/opt_pgo_gc/opt_pgo_gc_engine.test
- tests/run/opt_pgo_gc/opt_pgo_gc_oracle.py
- tests/run/opt_pgo_gc/opt_pgo_gc_probe.ax.in
- tests/run/opt_pgo_gc/pgo_epistemic_safety_barriers.ax
- tests/run/opt_pgo_gc/pgo_gen_use_and_stale_fallback.ax
- tests/run/opt_pgo_gc/safe_icf_and_fn_ptr_identity.ax
- tests/run/opt_pgo_gc/section_gc_dead_strip_and_roots.ax

## Verification
- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T622` -> refreshed `build-snap-T622` with 9 changed files.
- `python build-snap-T622/tools/axtest.py -j 1 --root build-snap-T622 --build-dir build-snap-T622/build --compiler build-snap-T622/build/axiomc2.exe run/opt_pgo_gc run/opt_lto run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax` -> `TOTAL 33 PASS 33 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
- `python tools/archcheck.py` -> `archcheck: 194 files scanned, 0 violations`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T622` -> 0 refused files.

STATUS: COMPLETE round=0
