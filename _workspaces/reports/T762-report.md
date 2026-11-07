# T762 Report — E18.3: Parallel Per-Module / Per-CGU Codegen & Deterministic Diagnostic / Artifact Merging

## Summary

Implemented `compiler/parallel/codegen/mod.ax` (`module compiler.parallel.codegen`) and its verification suite in `tests/run/parallel_codegen/` satisfying `SPEC-23` (`§3 AXS-PAR-020..024`, `§4 AXS-PAR-050..053`, `INV-PAR-002`):

1. **Deterministic Codegen Unit (`CGU`) Partitioning & Canonical Indexing (`AXS-PAR-020`)**:
   - `parallel_codegen_partition_cgus` sorts workspace modules lexicographically by canonical `SemanticKey`, sorts each module's functions/statics/consts by `SemanticKey`, and partitions them into deterministic `CGU_0 .. CGU_{M-1}` chunks (`(module SemanticKey, partition_ordinal)`) independent of `--jobs <N>` or worker arrival order.
   - Computes 128-bit `cgu_fp` (`FP_TIER_CODEGEN`) over the sorted items' `abi_fp` and `body_fp` alongside `ActionDigest.env_digest`. For single-partition modules (`module_partition_count == 1`), `cgu_fp` matches `IncrementalCache`'s module `codegen_fp` 100%.

2. **Isolated Per-Worker LIR Lowering, Register Allocation, Encoding & COFF `.obj` Emission (`AXS-PAR-021`, `INV-DET-001`, `INV-DET-002`)**:
   - `parallel_codegen_compile_cgu_on_worker` executes isolated per-CGU lowering, linear-scan register allocation, post-RA peephole, `x64_verify_checked`, and COFF x86-64 `.obj` emission (`Machine = 0x8664`, `TimeDateStamp = 0`, 64-byte header + 32 bytes per sorted item) into the worker's private `WorkerArenaState` without cross-worker mutation or host/thread identity leakage.
   - Implements fail-closed error gating (`FAULT_SOURCE_FAILURE`), automatic lease/resource retry (`FAULT_WORKER_FAILURE`, `FAULT_RESOURCE_FAILURE`), duplicate execution digest verification (`parallel_codegen_verify_duplicate_cgu` -> `DIAG_AX_ICE_PARALLEL_VERIFY`), and artifact checksum corruption quarantine (`FAULT_ARTIFACT_FAILURE` -> `ARTIFACT_STAGE_QUARANTINED`).

3. **Hybrid Incremental Cache + Parallel Work-Stealing CGU Execution (`AXS-PAR-022`)**:
   - `parallel_codegen_execute_workspace` integrates with `compiler.incremental.fingerprint` (`T757`) and `compiler.incremental.cache` (`T758`):
     - Clean CGUs (`NODE_COLOR_GREEN` with verified `.obj` digest in `.axiom-cache`) transition `CacheCheck -> Hit -> Verified` (`pcgu_load_clean_cgu_from_cache`) without redundant lowering.
     - Dirty CGUs (`CacheCheck -> Miss -> Ready`) are scheduled across `--jobs <N>` worker deques with priority/critical-path ordering and tail work-stealing, then published back into `.axiom-cache`.

4. **Canonical Post-Join Diagnostic Buffer Merging (`AXD-060`, `AXS-PAR-023`)**:
   - Workers append diagnostics only to their private `WorkerCodegenSlot.local_diags` buffers.
   - `parallel_codegen_merge_diagnostics` joins all per-worker buffers at the post-codegen barrier, deduplicates by `(has_primary_span, file_id, byte_offset, line, col, code, primary_key, message)`, and stably sorts into canonical `AXD-060` order (`FileId ASC, byte_offset ASC, line ASC, col ASC, code ASC, SemanticKey ASC`), ignoring worker ID and completion tick (`AXS-PAR-052`).

5. **Canonical Linker Input Ordering, Finalization Barriers & CLI Telemetry (`AXS-PAR-024`, `AXS-PAR-050`)**:
   - `parallel_codegen_link_canonical_artifacts` feeds `.obj` buffers in strict canonical CGU index order `[CGU_0.obj, CGU_1.obj, ..., CGU_{M-1}.obj]` followed by external archives in CLI argument order (`0 .. ext_archive_count - 1`), enforces `LinkBarrier` / `PackageBarrier` / `SigningBarrier` (`BARRIER_PASSED` vs `BARRIER_BLOCKED_BY_ERROR`), and promotes the PE32+ executable (`"MZ"`, `TimeDateStamp = 0`) through `Produced -> Verified -> Trusted -> Published`.
   - Implements `--jobs <N>` CLI validation (`parallel_codegen_validate_cli_jobs(0) == DIAG_AX_DRIVER_USAGE`) and `build --emit=parallel-stats` telemetry (`parallel_codegen_emit_stats`, `parallel_codegen_emit_cgu_summary`, `parallel_codegen_emit_diagnostics`).

## Verification

- Executed in `build-snap-T762` with `-j 1`:
  - `python build-snap-T762/tools/axtest.py --root build-snap-T762 --build-dir build-snap-T762/build --compiler build-snap-T762/build/axiomc2.exe -j 1 run/parallel_codegen run/parallel_scheduler run/incremental_cache` -> `TOTAL 33 PASS 33 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`).
  - Verified byte-for-byte `.obj`, `.exe`, LIR/MIR dump, and diagnostic stream equivalence across `--jobs 1`, `--jobs 2`, `--jobs 4`, and `--jobs 8` under `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`, plus on-disk `.axiom-cache` persistence.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T762` -> `0 REFUSED`.
- `python build-snap-T762/tools/archcheck.py` -> `194 files scanned, 0 violations`.

## Files changed

- `compiler/parallel/codegen/mod.ax`
- `tests/run/parallel_codegen/cgu_partition_and_jobs_obj_exe_equivalence.ax`
- `tests/run/parallel_codegen/cgu_partition_and_jobs_obj_exe_equivalence.stdout`
- `tests/run/parallel_codegen/hybrid_incremental_cache_parallel_cgu.ax`
- `tests/run/parallel_codegen/hybrid_incremental_cache_parallel_cgu.stdout`
- `tests/run/parallel_codegen/parallel_codegen_engine.test`
- `tests/run/parallel_codegen/parallel_codegen_oracle.py`
- `tests/run/parallel_codegen/parallel_codegen_probe.ax.in`
- `tests/run/parallel_codegen/post_join_diagnostic_and_linker_order.ax`
- `tests/run/parallel_codegen/post_join_diagnostic_and_linker_order.stdout`

## Status

STATUS: COMPLETE round=0
