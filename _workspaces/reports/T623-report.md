STATUS: COMPLETE round=0
# T623 Report — E15.6: LTO, Whole-Program Optimization, Section GC & PGO Conformance Suite

## Summary
Implemented the end-to-end E15.6 differential conformance suite in `tests/conformance/p15/e15_6_lto_pgo_gc/*` (`SPEC-75 §§1–11`, `AXS-LTO-001..030`, `AXS-PGO-001..015`, `REQ-OPT-246..250`):

1. **Unified Live E15.6 Engine Probe & Differential Oracle (`e15_6_lto_pgo_gc_probe.ax.in`, `e15_6_lto_pgo_gc_oracle.py`, `e15_6_lto_pgo_gc_oracle.test`)**:
   - Links `compiler.opt.lto` (`PASS_LTO = 18u16`), `compiler.link.gc_icf` (`PASS_SECTION_GC_ICF = 20u16`), and `compiler.opt.pgo` (`PASS_PGO = 19u16`) with `compiler.opt.devirt`, `compiler.opt.ipa`, `compiler.opt.inline`, `compiler.opt.sroa`, `compiler.opt.escape`, `compiler.opt.memopt`, `compiler.opt.alias`, `compiler.own.cap`, and `compiler.opt.passmgr`.
   - Verifies `.axmeta` summary serialization/deserialization, 64/128-bit semantic digests, and `ThinLTO` partition rebuild detection (`lto_thin_partition_needs_rebuild`).
   - Verifies closed-world vs open-world reachability, non-exported `pub` internalization, formal root retention (`Entry`, `@export`, `FfiCallback`, `Reflection`, `PinnedAt` MMIO), cross-module `OptIR` inlining/specialization/RTA devirtualization, `UnknownAlias`/`atomic`/`volatile` barriers, generic monomorphization deduplication (`LTO_DEDUP_EXACT_INSTANCE`, `LTO_DEDUP_REP_EQUIV_SHARED`, `LTO_DEDUP_KEPT_ADDRESS_TAKEN`, `LTO_DEDUP_KEPT_CUSTOM_DROP`), and `lto_print` determinism.
   - Verifies linker section GC (`COMDAT` resolution, `.pdata` reverse-dependency reclamation, unused import/runtime stripping), Safe `ICF` with 5-byte `0xE9` `jmp rel32` thunks for address-taken functions, `.rdata` constant/UTF-8 string pooling, `.bss` zero-data promotion, 3D binary size model (`file_size_bytes`, `mapped_size_bytes`, `working_set_bytes`), 128-bit `OptimizationCacheIdentity`, and `section_gc_print` determinism.
   - Verifies `--pgo-gen` -> weighted `pgo_merge_profiles` -> `.axprof` round-trip -> `--pgo-use`, stale-profile graceful fallback (`PGO_COMPAT_STALE`), strict `REQ-OPT-246..250` epistemic safety law (`CERTAINTY_UNKNOWN`/`CERTAINTY_POSSIBLE` never upgraded to `CERTAINTY_PROVEN`), constant-time secret (`zeroize`/`black_box`) & `atomic`/`volatile` barriers, transactional `PassManager` rollback, and `pgo_print` determinism.
   - Synthesizes a multi-module package (`main.ax`, `math_kernel.ax`, `generic_dedup.ax`) and verifies exact `--interp` vs `-O0`, `-O1`, and `-O2 --verify-each` equivalence (both via package directory discovery and explicit multi-file `axiomc build`), valid PE32+ headers, and byte-identical deterministic executable output.

2. **Standalone E15.6 Differential & `-O2 --verify-each` Conformance Programs**:
   - `lto_multimod_inline_spec_devirt_dedup.ax` and `o2_lto_multimod_inline_spec_devirt_dedup.ax`: Cross-boundary inlining, constant specialization, closed-world RTA trait dispatch, generic monomorphization deduplication, function-pointer identity preservation, and LIFO `Drop` order.
   - `section_gc_roots_and_safe_icf_identity.ax` and `o2_section_gc_roots_and_safe_icf_identity.ax`: Dead function/table stripping vs `@export`/live table roots, Safe `ICF` indirect call identity, and distinct mutable capability barrier.
   - `pgo_roundtrip_stale_and_safety_contracts.ax` and `o2_pgo_roundtrip_stale_and_safety_contracts.ax`: Speculative devirtualization guard fallback, zero-count cold branch preservation, constant-time secret zeroization barrier, and ordered MMIO sequence preservation (`REQ-OPT-246..250`).
   - `trap_pgo_lto_bounds_and_drop_order.ax` and `o2_trap_pgo_lto_bounds_and_drop_order.ax`: Verifies that 100%-observed in-bounds hot execution never elides cold panic/bounds traps (exit `101`) and preserves pre-trap observable stdout and LIFO `Drop` order across `--interp` and `-O0`/`-O1`/`-O2 --verify-each`.

## Files changed
- tests/conformance/p15/e15_6_lto_pgo_gc/e15_6_lto_pgo_gc_oracle.py
- tests/conformance/p15/e15_6_lto_pgo_gc/e15_6_lto_pgo_gc_oracle.test
- tests/conformance/p15/e15_6_lto_pgo_gc/e15_6_lto_pgo_gc_probe.ax.in
- tests/conformance/p15/e15_6_lto_pgo_gc/lto_multimod_inline_spec_devirt_dedup.ax
- tests/conformance/p15/e15_6_lto_pgo_gc/o2_lto_multimod_inline_spec_devirt_dedup.ax
- tests/conformance/p15/e15_6_lto_pgo_gc/o2_pgo_roundtrip_stale_and_safety_contracts.ax
- tests/conformance/p15/e15_6_lto_pgo_gc/o2_section_gc_roots_and_safe_icf_identity.ax
- tests/conformance/p15/e15_6_lto_pgo_gc/o2_trap_pgo_lto_bounds_and_drop_order.ax
- tests/conformance/p15/e15_6_lto_pgo_gc/pgo_roundtrip_stale_and_safety_contracts.ax
- tests/conformance/p15/e15_6_lto_pgo_gc/section_gc_roots_and_safe_icf_identity.ax
- tests/conformance/p15/e15_6_lto_pgo_gc/trap_pgo_lto_bounds_and_drop_order.ax

## Verification
- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T623` -> refreshed `build-snap-T623` with 11 changed files.
- `python tools/axtest.py -j 1 --root build-snap-T623 --build-dir build-snap-T623/build --compiler build-snap-T623/build/axiomc2.exe conformance/p15/e15_6_lto_pgo_gc run/opt_pgo_gc run/opt_lto run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax` -> `TOTAL 50 PASS 50 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
- Spot-proof: Mutated expected output of `o2_lto_multimod_inline_spec_devirt_dedup.ax` (`452` -> `999`) inside `build-snap-T623`, confirmed `FAIL conformance/p15/e15_6_lto_pgo_gc/o2_lto_multimod_inline_spec_devirt_dedup.ax [native]`, restored via `taskctl.py snapshot T623`, and re-verified `TOTAL 2 PASS 2 FAIL 0`.
- `python tools/archcheck.py` -> `archcheck: 194 files scanned, 0 violations` (exit 0).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T623` -> 0 refused files (exit 0).

STATUS: COMPLETE round=0
