STATUS: COMPLETE round=0

# T626 Implementation Report — E15.7 Performance Contract, `-O2` Differential Equivalence & CI Regression Budget Conformance Suite

## Summary

Implemented the end-to-end E15.7 performance contract, `-O2` differential equivalence, optimization provenance, and CI regression budget conformance suite in `tests/conformance/p15/e15_7_perf_contract/`, verifying `SPEC-76` (`AXS-PERF-001..044`) and requirements `REQ-OPT-242..245`, `REQ-OPT-251..256`, `REQ-OPT-292..295`, `REQ-OPT-334`, `REQ-OPT-381`, and `REQ-OPT-382`:

1. **Combined Multi-Pass Differential Equivalence Across All Optimization Tiers (`REQ-OPT-251..256`, `REQ-OPT-292..295`)**:
   - `multipass_stress_all_tiers.ax` & `o2_multipass_stress_all_tiers.ax`: exercises `OptIR` SSA/MemorySSA, `SCCP`, `GVN`/`CSE`, `SROA`, escape promotion, `SCEV`/`RangeInfo` proven `BCE`, `LICM`, call-graph SCC inlining, constant specialization, closed-world devirtualization, 4-lane loop & straight-line `SLP` auto-vectorization with scalar epilogue, and high-pressure linear-scan register allocation + instruction selection (`LEA`, magic-multiply division, branchless `cmov`) across `--interp`, `-O0`, `-O1`, `-O2 --verify-each`, and `-Oz`.
   - `perf_profiles_zero_cost_vs_size_sharing.ax` & `o2_perf_profiles_zero_cost_vs_size_sharing.ax`: verifies zero-cost abstraction erasure (`WeightKernel` devirtualization, `Accumulator` SROA, proven `BCE`), `-O2` specialization vs `-Oz` shared code folding (`fold_window_3`), generic representation sharing (`SharedSlot<T>`), zero monolithic runtime dependency (`REQ-OPT-334`), and deterministic LIFO `Drop` order across `--interp`, `-O0`, `-O1`, `-O2 --verify-each`, and `-Oz`.

2. **Bounded Auto-Tuning, Provenance Determinism, PGO Optionality & 3D Binary Footprint (`REQ-OPT-242..245`, `REQ-OPT-251..256`, `REQ-OPT-381`, `REQ-OPT-382`)**:
   - `provenance_determinism_and_pgo_optionality.ax` & `o2_provenance_determinism_and_pgo_optionality.ax`: verifies valid execution without PGO profile data (`REQ-OPT-251`, `REQ-OPT-252`), legality-first auto-tuning candidate filtering (`!legality_proven` rejected unconditionally, `REQ-OPT-242`), hard candidate/wall-clock budgets (`REQ-OPT-243`), telemetry orthogonality (`elapsed_us` excluded from deterministic counter digests, `REQ-OPT-244`, `REQ-OPT-245`), and `OptOrigin` provenance chain preservation (`REQ-OPT-254`, `REQ-OPT-256`).
   - `binary_footprint_3d_and_layout_contract.ax` & `o2_binary_footprint_3d_and_layout_contract.ax`: verifies the three-dimensional binary footprint contract (`FileSize`, `MappedSize`, `StartupWorkingSet`, `PeakWorkingSet`), `.bss` zero-file-bytes invariant (`bss_file_bytes == 0`), `.text` thermal section layout (`StartupEntrySet` -> `HotCluster` -> `WarmNormal` -> `ColdSplit`), alignment padding budget (`<= 2%` in `-O2`, `0` in `-Oz`), and `startup_allocations == 0`.

3. **Safety-Barrier & Trap Preservation Under `-O2` / `-Oz` / PGO / Auto-Tuning (`AXS-PERF-001`, `AXS-PERF-003`, `AXS-PERF-004`, `REQ-OPT-242`, `REQ-OPT-252`, `REQ-OPT-256`, `REQ-OPT-295`)**:
   - `trap_multipass_unproven_bounds_and_drop_order.ax` & `o2_trap_multipass_unproven_bounds_and_drop_order.ax`: verifies that unproven dynamic indexing (`idx == 5` on `[5]i64`) after hot in-bounds loop iterations retains its bounds check and traps with exit code `101` after flushing LIFO `Drop` side effects.
   - `trap_checked_overflow_preserved_under_o2_oz.ax` & `o2_trap_checked_overflow_preserved_under_o2_oz.ax`: verifies that checked integer overflow (`i32.MAX + 1`) followed by algebraic cancellation (`- 1`) never folds away and traps with exit code `101` across `--interp`, `-O0`, `-O1`, `-O2`, and `-Oz`.
   - `trap_pgo_autotune_never_weakens_verified_mir.ax` & `o2_trap_pgo_autotune_never_weakens_verified_mir.ax`: verifies that cold division-by-zero (`denom == 0`) after 100%-taken fast-path iterations is never hoisted or erased and traps with exit code `101`.

4. **End-to-End Live Engine Probe & CI Regression Budget Oracle (`e15_7_conformance.test`, `e15_7_conformance_oracle.py`, `e15_7_conformance_probe.ax.in`)**:
   - Bundles `compiler.driver.perf_telemetry` + `compiler.link.gc_icf` + `compiler.obj.coff` with `e15_7_conformance_probe.ax.in` and executes the probe under `--interp`, `-O0 --verify-each`, and `-O2 --verify-each`.
   - Verifies differential equivalence across `--interp`, `-O0`, `-O1`, `-O2 --verify-each`, and `-Oz` on all positive and trap conformance fixtures.
   - Verifies byte-for-byte deterministic PE32+ output across repeated `-O2 --verify-each` builds (`det_a == det_b`), telemetry orthogonality (`--time-passes`), and deterministic `axiomc inspect --emit=optir` / `--emit=memssa` output.
   - Executes `tools/perf.py --check-budgets --tune --json-out ... --time-passes-json ... --size-report-json ...` and `--compare`, verifying all 7 canonical benchmarks (`BENCH-STARTUP-001`..`BENCH-COMPILE-001`) and all 9 quantitative `SPEC-76` budgets (`BUDGET-CTIME-001`, `BUDGET-SPEED-001`, `BUDGET-IR-001`, `BUDGET-SIZE-001`, `BUDGET-SIZE-002`, `BUDGET-START-001`, `BUDGET-DET-001`, `BUDGET-SELF-001`, `BUDGET-SELF-002`) pass with 0 regressions.

## Files changed

- tests/conformance/p15/e15_7_perf_contract/binary_footprint_3d_and_layout_contract.ax
- tests/conformance/p15/e15_7_perf_contract/e15_7_conformance.test
- tests/conformance/p15/e15_7_perf_contract/e15_7_conformance_oracle.py
- tests/conformance/p15/e15_7_perf_contract/e15_7_conformance_probe.ax.in
- tests/conformance/p15/e15_7_perf_contract/multipass_stress_all_tiers.ax
- tests/conformance/p15/e15_7_perf_contract/o2_binary_footprint_3d_and_layout_contract.ax
- tests/conformance/p15/e15_7_perf_contract/o2_multipass_stress_all_tiers.ax
- tests/conformance/p15/e15_7_perf_contract/o2_perf_profiles_zero_cost_vs_size_sharing.ax
- tests/conformance/p15/e15_7_perf_contract/o2_provenance_determinism_and_pgo_optionality.ax
- tests/conformance/p15/e15_7_perf_contract/o2_trap_checked_overflow_preserved_under_o2_oz.ax
- tests/conformance/p15/e15_7_perf_contract/o2_trap_multipass_unproven_bounds_and_drop_order.ax
- tests/conformance/p15/e15_7_perf_contract/o2_trap_pgo_autotune_never_weakens_verified_mir.ax
- tests/conformance/p15/e15_7_perf_contract/perf_profiles_zero_cost_vs_size_sharing.ax
- tests/conformance/p15/e15_7_perf_contract/provenance_determinism_and_pgo_optionality.ax
- tests/conformance/p15/e15_7_perf_contract/trap_checked_overflow_preserved_under_o2_oz.ax
- tests/conformance/p15/e15_7_perf_contract/trap_multipass_unproven_bounds_and_drop_order.ax
- tests/conformance/p15/e15_7_perf_contract/trap_pgo_autotune_never_weakens_verified_mir.ax

## Verification

- `python tools/axtest.py --compiler build-snap-T626/build/axiomc2.exe --root build-snap-T626 --build-dir build-snap-T626/build -j 1 --exclude-requires axiom0-internal conformance/p15/e15_7_perf_contract` -> `WEAK-NATIVE 0`, `TOTAL 22 PASS 22 FAIL 0 SKIP 0 XFAIL 0`.
- `python tools/perf.py --compiler build-snap-T626/build/axiomc2.exe --check-budgets` -> exit `0`, all 7 canonical benchmarks `PASS`, all 9 quantitative `SPEC-76` budgets (`BUDGET-CTIME-001`..`BUDGET-SELF-002`) `PASS`.

STATUS: COMPLETE round=0
