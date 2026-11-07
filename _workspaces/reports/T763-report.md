STATUS: COMPLETE round=0
# T763 Report — E18.3 Parallel compilation thread-count invariance & byte-identical determinism conformance suite

## Summary
Implemented the `E18.3` conformance suite in `tests/conformance/p18/e18_3_parallel/` certifying `SPEC-23` (`AXS-PAR-001..005`, `AXS-PAR-010..014`, `AXS-PAR-020..024`, `AXS-PAR-030..033`, `AXS-PAR-040..041`, `AXS-PAR-050..053`, `INV-PAR-001..003`, `REQ-LNK-1004..1033`, `REQ-LNK-1204..1233`):
1. **Byte-identical `.obj`/`.exe` outputs & identical HIR/MIR/LIR dumps across `--jobs 1`, `--jobs 2`, `--jobs 4`, and `--jobs 8` (`jobs_1_2_4_8_byte_identical_artifacts_and_ir.ax` + `e18_3_parallel_probe.ax.in`)**:
   - Verifies `(ModuleId, LocalIndex)` `ScopedDefId` & `ScopedHirId` allocation-order invariance (`AXS-PAR-020`) and 64-shard content-addressed `ShardedInterner` canonical ID & sealed table fingerprint invariance (`AXS-PAR-021`).
   - Verifies identical 128-bit HIR, MIR, and LIR dump digests across `--jobs 1/2/4/8` and all 6 schedule policies (`Interactive`, `Balanced`, `Throughput`, `MemoryBound`, `LowPower`, `DeterministicDebug`).
   - Verifies deterministic multi-partition CGU splitting (`max_items_per_cgu = 2`), isolated per-worker 64-byte COFF `.obj` synthesis (`Machine = 0x8664`, `TimeDateStamp = 0`), post-codegen barrier sorting (`(module_rank, partition_index)`), and canonical linker archive ordering (`(link_order, archive_key)`) producing byte-identical `.obj` and `.exe` outputs across `--jobs 1/2/4/8`.
2. **Randomized worker scheduling delays, multi-file diagnostic ordering (`AXD-060`), and cross-worker cycle handling (`randomized_delay_multifile_diag_and_cycles.ax` + `e18_3_parallel_probe.ax.in`)**:
   - Verifies `DiagnosticCollector` canonical tuple sort `(severity_rank, file_id, byte_start, byte_end, code, message_hash, emission_seq)` across 5 distinct randomized worker completion schedules (`forward`, `reverse`, `interleaved`, `burst-delayed`, `starvation-skewed`).
   - Verifies `SingleFlightLatch` wait/notify deduplication (`executed = 1`, `coalesced_waiters = 3`) and `WaitForGraph` cross-worker mutual recursion cycle detection (`W1 -> Q20 -> W2 -> Q10 -> W1`, canonical rotation starting at minimum `QueryKey(1, 10)`, `E0701`).
   - Verifies `DeterministicDebug` (`--deterministic-debug`) topological tie-breaking and trace digest reproducibility.
3. **Combined parallel + incremental rebuild determinism (`parallel_incremental_hybrid_determinism.ax` + `e18_3_parallel_probe.ax.in`)**:
   - Verifies cold build (`cached = 0, executed = 4`), warm no-op fast path (`cached = 4, executed = 0`), private function body edit firewall (`cached = 3, executed = 1`), and public signature/const invalidation (`cached = 2, executed = 2`) under `--jobs 2/4/8` produce byte-identical `.exe` outputs to a clean `--jobs 1` build.
   - Verifies transient worker/resource fault retry (`FAULT_WORKER_FAILURE`, `FAULT_RESOURCE_FAILURE`), corrupt cached artifact checksum quarantine (`FAULT_ARTIFACT_FAILURE` -> `ARTIFACT_STAGE_QUARANTINED`), and finalization barrier gating (`LinkBarrier`, `PackageBarrier`, `SigningBarrier`).
4. **Live compiler differential & on-disk binary oracle (`e18_3_parallel_oracle.test` + `e18_3_parallel_oracle.py`)**:
   - Bundles `e18_3_parallel_probe.ax.in` with the live `compiler/parallel/scheduler/mod.ax`, `compiler/parallel/codegen/mod.ax`, and `compiler/incremental/*` modules, verifying identical 31-line stdout and exit code `0` across `--interp`, native `-O0`, native `-O1`, and native `-O2 --verify-each`.
   - Verifies on-disk `AXCACHE1` cache header magic (`0x3145484341435841`), COFF `.obj` header (`Machine = 0x8664`, `TimeDateStamp = 0`), and byte-identical native PE32+ executable emission across repeated builds (`0 WEAK-NATIVE`).

## Files changed
- tests/conformance/p18/e18_3_parallel/e18_3_parallel_oracle.py
- tests/conformance/p18/e18_3_parallel/e18_3_parallel_oracle.test
- tests/conformance/p18/e18_3_parallel/e18_3_parallel_probe.ax.in
- tests/conformance/p18/e18_3_parallel/jobs_1_2_4_8_byte_identical_artifacts_and_ir.ax
- tests/conformance/p18/e18_3_parallel/jobs_1_2_4_8_byte_identical_artifacts_and_ir.stdout
- tests/conformance/p18/e18_3_parallel/parallel_incremental_hybrid_determinism.ax
- tests/conformance/p18/e18_3_parallel/parallel_incremental_hybrid_determinism.stdout
- tests/conformance/p18/e18_3_parallel/randomized_delay_multifile_diag_and_cycles.ax
- tests/conformance/p18/e18_3_parallel/randomized_delay_multifile_diag_and_cycles.stdout

## Verification
- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T763`: Refreshed `build-snap-T763` cleanly.
- `python tools/axtest.py -j 1 --build-dir build-snap-T763 conformance/p18/e18_3_parallel run/parallel_codegen run/parallel_scheduler run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax`: `TOTAL 43 PASS 43 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
- `python tools/axtest.py -j 1 --compiler build-snap-T763/build/axiomc2.exe --build-dir build-snap-T763 conformance/p18/e18_3_parallel`: `TOTAL 10 PASS 10 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
- `python tools/archcheck.py`: `archcheck: 194 files scanned, 0 violations`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T763`: `0` path violations; all modified files strictly within `tests/conformance/p18/e18_3_parallel` and `_workspaces/reports/T763-report.md`.

STATUS: COMPLETE round=0
