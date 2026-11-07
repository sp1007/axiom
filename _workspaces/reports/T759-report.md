# T759 — E18.2: Incremental Compilation, Edit-One-Private-Fn & <100ms No-Op Rebuild Conformance Suite

## Summary
Implemented the Phase 18 (`E18.2`) end-to-end conformance suite in `tests/conformance/p18/e18_2_incremental/` verifying the multi-tier cryptographic fingerprinting & Red-Green incremental engine (`compiler/incremental/fingerprint/mod.ax`), the persistent `.axiom-cache` artifact store, `<100ms` no-op rebuild fast path, Private-Body Firewall, selective invalidation, and incremental vs. clean `--no-incremental` byte-for-byte binary equivalence per `SPEC-22` (`AXS-INC-001..053`, `INV-INC-003`):

1. **Bundled `compiler.incremental.fingerprint` + `compiler.incremental.cache` End-to-End Conformance Oracle (`e18_2_incremental_oracle.test`, `e18_2_incremental_oracle.py`, `e18_2_incremental_probe.ax.in`)**:
   - Bundles the live `compiler/query/db/mod.ax`, `compiler/incremental/fingerprint/mod.ax`, and `compiler/incremental/cache/mod.ax` implementation modules with `e18_2_incremental_probe.ax.in` and executes the resulting probe across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each`, plus deterministic PE32+ build reproducibility (`TimeDateStamp == 0` and byte-for-byte identical binaries across clean builds).
   - Verifies a 4-module `axiomc` workspace (`math_lib`, `mid_layer`, `app_driver`, `util_mod`) across 11 incremental revisions:
     1. Cold build (`modules_typechecked=4`, `cgu_rebuilt=4`), `.axiom-cache/dep-graph.axcache` (`AXCACHE1`) and `.axiom-cache/objects/*.obj` serialization with atomic temp+rename discipline, and corrupt checksum / schema mismatch / truncation auto-eviction (`AX_INC_CACHE_CORRUPT`).
     2. Warm no-op rebuild via `stat` fast path (`elapsed_ns < 100ms`, `queries_recomputed=0`, `modules_typechecked=0`, `cgu_rebuilt=0`, `cgu_reused=4`) and canonical `AXD-060` warning replay.
     3. `touch` (updated `mtime` with unchanged content digest) still taking the no-op fast path (`queries_recomputed=0`, `modules_typechecked=0`).
     4. Comment/whitespace-only edit in `math_lib` backdating `AstFingerprint` (`ParseModule` Green, `modules_typechecked=0`, `cgu_rebuilt=0`, `cgu_reused=4`).
     5. Private function body edit (`fn internal_scale`) in `math_lib` enforcing the Private-Body Firewall (`modules_typechecked=1`, `0` downstream modules re-typechecked, `cgu_rebuilt=1`, `cgu_reused=3`) and byte-for-byte clean equivalence.
     6. Non-`@inline` `pub fn compute_metric` body edit in `math_lib` keeping `InterfaceFingerprint(math_lib)` Green (`modules_typechecked=1`, `cgu_rebuilt=1`, `cgu_reused=3`) and byte-for-byte clean equivalence.
     7. `pub const LIMIT` expression edit (`100` -> `60 + 40`) with unchanged `ConstValue` backdating `ConstEval(LIMIT)` to Green (`modules_typechecked=0`, `cgu_rebuilt=0`, `cgu_reused=4`).
     8. `pub const LIMIT` value edit (`60 + 40` -> `250`) selectively invalidating only `math_lib` and `mid_layer` (`modules_typechecked=2`, `cgu_rebuilt=2`, `cgu_reused=2`) with byte-for-byte clean equivalence.
     9. `@inline pub fn fast_step` and generic `pub fn transform<T>` body edits keeping `InterfaceFingerprint(math_lib)` Green (`modules_typechecked=1`) while selectively rebuilding `mid_layer`'s `CodegenUnit` via `DEP_KIND_INLINED_BODY` / `DEP_KIND_GENERIC_BODY` (`cgu_rebuilt=2`, `cgu_reused=2`) and byte-for-byte clean equivalence.
     10. `pub fn compute_metric` signature and `@repr(C) pub struct MetricHeader` layout edits invalidating `math_lib` and `mid_layer` while keeping `app_driver` (`mid_layer` API unchanged) and `util_mod` Green (`modules_typechecked=2`, `cgu_rebuilt=2`, `cgu_reused=2`) and byte-for-byte clean equivalence.
     11. Error non-pollution (`AXS-INC-024 §2`): a module with a body type error never publishes a `Ready` `.obj` or linked executable.
2. **No-Op Rebuild `<100ms` Fast Path, Atomic Cache Persistence & Corruption Recovery (`noop_rebuild_under_100ms.ax` + `.stdout`)**:
   - Verifies 5-tier domain-separated `BLAKE3-128` fingerprints (`SRC0..CGU0`), `ActionConfigDigest` flag/triple sensitivity, `<100ms` warm no-op fast path (`queries_recomputed=0`, `modules_typechecked=0`, `cgu_rebuilt=0`, `cgu_reused=5`), `touch` `mtime` fallback to `SourceFingerprint`, comment/whitespace `AstFingerprint` backdating, `AXCACHE1` header validation + corruption auto-eviction (`AX_INC_CACHE_CORRUPT`), and canonical `AXD-060` warning replay.
3. **Edit-One-Private-Fn Firewall & `--emit=incremental-stats` Verification (`edit_one_private_fn_firewall.ax` + `.stdout`)**:
   - Exercises a 4-module workspace (`math_lib`, `mid_layer`, `app_driver`, `util_mod`) across cold build (`R1`), private function body edit (`R2`), non-`@inline` `pub fn` body edit (`R3`), and private helper addition (`R4`), proving `modules_typechecked == 1` (`0` downstream modules re-typechecked), `cgu_rebuilt == 1`, `cgu_reused == 3`, canonical `SemanticKey` link order (`INV-INC-003`), and byte-identical output to `--no-incremental`.
4. **Public Signature, `const`, `@inline`, Generic Body & `@repr(C)` Layout Selective Invalidation (`sig_const_generic_invalidation_and_clean_equiv.ax` + `.stdout`)**:
   - Exercises unchanged-value `const` expression backdating (`R2`), changed-value `const` propagation (`R3`), `@inline` + generic body selective CGU rebuilds with `0` downstream `typeck_body` (`R4`), public signature + `@repr(C)` layout invalidation (`R5`), and error non-pollution (`R6`), proving byte-for-byte equivalence against clean `--no-incremental` builds at every revision.

## Files changed
- `tests/conformance/p18/e18_2_incremental/e18_2_incremental_oracle.py`
- `tests/conformance/p18/e18_2_incremental/e18_2_incremental_oracle.test`
- `tests/conformance/p18/e18_2_incremental/e18_2_incremental_probe.ax.in`
- `tests/conformance/p18/e18_2_incremental/edit_one_private_fn_firewall.ax`
- `tests/conformance/p18/e18_2_incremental/edit_one_private_fn_firewall.stdout`
- `tests/conformance/p18/e18_2_incremental/noop_rebuild_under_100ms.ax`
- `tests/conformance/p18/e18_2_incremental/noop_rebuild_under_100ms.stdout`
- `tests/conformance/p18/e18_2_incremental/sig_const_generic_invalidation_and_clean_equiv.ax`
- `tests/conformance/p18/e18_2_incremental/sig_const_generic_invalidation_and_clean_equiv.stdout`

## Verification
- Test suite (`-j 1`):
  `python build-snap-T759/tools/axtest.py --root build-snap-T759 --build-dir build-snap-T759/build --compiler build-snap-T759/build/axiomc2.exe -j 1 conformance/p18/e18_2_incremental run/incremental_cache run/incremental_fingerprint run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax`
  -> `TOTAL 40 PASS 40 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`).
- Architecture check: `python build-snap-T759/tools/archcheck.py` -> `193 files scanned, 0 violations`.
- Scope / path ownership check: `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T759` -> `0 REFUSED`.

STATUS: COMPLETE round=0
