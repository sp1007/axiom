# T761 Report — E18.3 Thread-Safe Immutable Compiler Snapshots, Sharded Interner & Work-Stealing Query Scheduler

## Summary

Implemented `compiler/parallel/scheduler/mod.ax` (`module compiler.parallel.scheduler`) and the `tests/run/parallel_scheduler/` verification suite per `spec/SPEC-23-parallel-compilation.md` (`§1 AXS-PAR-001..005`, `§2 AXS-PAR-010..015`, `§3 AXS-PAR-023`, `§5 AXS-PAR-050..053`, `INV-PAR-001`):

1. **Thread-Safe Immutable `CompilerDB` Snapshots & Per-Worker Arena Isolation (`AXS-PAR-003`)**:
   - Implemented `SnapshotEpoch`, `ParallelSnapshot`, `WorkerArenaState`, `parallel_snapshot_freeze`, `parallel_snapshot_fork_worker`, `parallel_snapshot_release_worker`, and `parallel_snapshot_compute_fingerprint` (canonicalized by `SemanticKey` order so snapshot fingerprints are invariant to worker registration order).
   - Enforced per-worker isolated arena allocation (`worker_arena_record_alloc`) and post-evaluation sealing (`worker_arena_freeze`).

2. **Module-Scoped `(ModuleId, LocalIndex)` Semantic IDs & 64-Shard Content-Addressed Interner (`AXS-PAR-004`, `AXS-PAR-005`)**:
   - Implemented `ScopedDefId` and `ScopedHirId` (`scoped_def_id_to_def_id`, `scoped_def_id_from_def_id`, `scoped_hir_id_to_hir_id`) encoding `(ModuleId, LocalIndex)` deterministically without any thread-arrival-dependent global counter.
   - Implemented `ShardedInterner`, `InternShard`, `ShardedInternEntry`, and `ShardedInternId` routing strings (`INTERN_DOMAIN_STR`) and canonicalized types (`INTERN_DOMAIN_TYPE`) across 64 independent shards by the top bits of their 64-bit `AXH64-v1` content hash (`sharded_interner_compute_hash64`, `sharded_interner_route_shard`) and maintaining canonical intra-shard sorted order + `sharded_interner_seal` global index assignment so `(shard_id, local_offset, canonical_index)` are identical under `--jobs 1`, `--jobs 2`, and `--jobs 8`.

3. **Single-Flight Query Deduplication (`InFlightLatch`) & Cross-Worker Cycle Detection (`WaitForGraph`) (`AXS-PAR-010`, `AXS-PAR-011`)**:
   - Implemented `InFlightLatch` (`Vacant -> Computing -> Ready | Poisoned`), `WaitForEdge`, `WorkerQueryStack`, `ParallelCycleRecord`, `wait_for_graph_claim_or_wait`, `wait_for_graph_detect_cycle`, `parallel_rotate_cycle_canonical`, and `wait_for_graph_complete_latch`.
   - Concurrent workers requesting an in-flight `QueryKey` register on its `InFlightLatch` (`CLAIM_WAIT_SINGLE_FLIGHT`) instead of running duplicate providers; cross-worker wait-for cycles (`W_0 -> W_1 -> ... -> W_0`) are detected deterministically before blocking, rotated to the unique lexicographical minimum `(QueryKind.order_rank, SemanticKey)` head (`AX_PARALLEL_QUERY_CYCLE` / `AX_QUERY_CYCLE` / `AX_CTM_CYCLE`), and poisoned without deadlocking.

4. **Work-Stealing Query Scheduler (`ParallelScheduler`, `--jobs <N>`) & Deterministic Post-Join Merging (`AXS-PAR-001`, `AXS-PAR-012..014`, `AXS-PAR-023`)**:
   - Implemented `ParallelScheduler`, `ScheduledTask`, `WorkerDeque`, `ResourceCostEstimate`, `parallel_scheduler_submit_query_task`, `parallel_scheduler_eval_query_on_worker`, and `parallel_scheduler_execute_all` supporting `--jobs 1` (`DeterministicDebug` single-thread fallback), `--jobs 2` (`Balanced`), and `--jobs 8` (`Throughput`) with priority ordering (`Critical > Interactive > Normal > Background`, descending `critical_cost`, ascending `QueryKey`) and tail-end work-stealing across worker deques.
   - Implemented post-join canonical formatters (`parallel_scheduler_emit_hir_mir_dump`, `parallel_scheduler_emit_cycles`, `parallel_scheduler_emit_diagnostics`, `parallel_scheduler_emit_equivalence_digest`) sorting HIR/MIR items and diagnostics by `SemanticKey` so `--jobs 1`, `--jobs 2`, and `--jobs 8` produce byte-for-byte identical outputs.

## Files changed

- `compiler/parallel/scheduler/mod.ax`
- `tests/run/parallel_scheduler/parallel_scheduler_engine.test`
- `tests/run/parallel_scheduler/parallel_scheduler_oracle.py`
- `tests/run/parallel_scheduler/parallel_scheduler_probe.ax.in`
- `tests/run/parallel_scheduler/sharded_interner_and_snapshots.ax`
- `tests/run/parallel_scheduler/sharded_interner_and_snapshots.stdout`
- `tests/run/parallel_scheduler/single_flight_and_cross_worker_cycles.ax`
- `tests/run/parallel_scheduler/single_flight_and_cross_worker_cycles.stdout`
- `tests/run/parallel_scheduler/work_stealing_jobs_equivalence.ax`
- `tests/run/parallel_scheduler/work_stealing_jobs_equivalence.stdout`

## Verification

- Synchronized isolated worktree `build-snap-T761`:
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T761`
- Executed `axtest.py -j 1` on `run/parallel_scheduler`, `run/query_db`, `run/query_cycles`, and targeted intrinsics canaries inside `build-snap-T761`:
  - `python build-snap-T761/tools/axtest.py --root build-snap-T761 --build-dir build-snap-T761/build -j 1 run/parallel_scheduler run/query_db run/query_cycles run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax`
  - Result: `WEAK-NATIVE 0`, `TOTAL 40 PASS 40 FAIL 0 SKIP 0 XFAIL 0` (including live `parallel_scheduler_oracle.py` bundling `compiler.query.db` + `compiler.parallel.scheduler` + `parallel_scheduler_probe.ax.in` across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`).
- Architecture & task scope checks:
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T761` -> `0 REFUSED`
  - `python build-snap-T761/tools/archcheck.py` -> `archcheck: 193 files scanned, 0 violations`

STATUS: COMPLETE round=0
