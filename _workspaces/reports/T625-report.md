STATUS: COMPLETE round=0

# T625 Implementation Report — Compiler Pass-Timing (`--time-passes`), Code-Size (`--size-report`) Telemetry & `SPEC-76` Benchmark Harness Enforcement (E15.7)

## Summary

Implemented the Axiom 2.0 Performance, Optimization, Code Size & Tuning Contract (`SPEC-76`, `AXS-PERF-001..044`, `REQ-OPT-242..245`, `REQ-OPT-253`, `REQ-OPT-255`, `REQ-OPT-292..295`, `REQ-OPT-334`, `REQ-OPT-381..382`) across `compiler/driver/perf_telemetry/mod.ax`, `tools/bench/*`, `tools/perf.py`, and `tests/run/perf_contract/*`:

1. **`compiler/driver/perf_telemetry/mod.ax` (`module compiler.driver.perf_telemetry`)**:
   - **Five Canonical Optimization Profiles (`AXS-PERF-010..014`, `REQ-OPT-292..295`, `REQ-OPT-334`)**: `PERF_OPT_O0`, `PERF_OPT_O1`, `PERF_OPT_O2`, `PERF_OPT_OS`, and `PERF_OPT_OZ` with explicit `ProfileCostPolicy` inline cost thresholds (`inline_base_cost`, `inline_hot_cost`, `inline_cold_cost`, `max_caller_growth_pct`), loop unroll budgets (`max_unroll_factor`, `max_unroll_insts`), auto-vectorization policies (`autovec_enabled`, `autovec_allow_expansion`), monomorphization body-sharing profitability (`perf_can_share_monomorphized_body`), and `requires_monolithic_runtime == false` across all profiles.
   - **Bounded Auto-Tuning & Legality-Before-Profitability (`AXS-PERF-004`, `REQ-OPT-242..243`)**: `AutoTuneBudget`, `AutoTuneCandidate`, `AutoTuneResult`, `perf_autotune_default_budget`, and `perf_autotune_evaluate` enforcing strict rejection of any candidate where `!is_legality_proven`, deterministic tie-breaking by lowest `candidate_id` (`TUNE-05`), and hard budget caps on candidate count, iteration count, wall-clock microseconds, and scratch memory bytes.
   - **Deterministic Provenance & Telemetry Orthogonality (`AXS-PERF-004`, `AXS-PERF-032`, `REQ-OPT-244..245`)**: `ArtifactProvenanceHeader`, `perf_compute_artifact_provenance`, and `perf_verify_telemetry_orthogonality` ensuring that enabling `--time-passes` or `--size-report` never alters `provenance_digest`, `cache_key_digest`, or `emitted_binary_hash`.
   - **Structured `--time-passes` Telemetry (`AXS-PERF-030`, `REQ-OPT-253`)**: `PassTimingRecord`, `TimePassesReport`, `time_passes_deterministic_digest` (hashing only structural IR/section transformation counters and never wall-clock `elapsed_us`), `time_passes_format_human`, and `time_passes_format_json`.
   - **Structured `--size-report` 3D Binary Footprint & Symbol Attribution (`AXS-PERF-020..022`, `AXS-PERF-031`, `REQ-OPT-381..382`)**: `SymbolSizeEntry`, `SizeReport`, `size_report_build_from_section_graph` (integrating directly with `compiler.link.gc_icf.SectionGraph` and `GcIcfStats`), `size_report_check_alignment_budget` (`alignment_padding_bytes <= 2%` of `.text`, `0` under `-Oz`), `size_report_sort_symbols` (sorted by descending `size_bytes`, breaking ties by ascending `name_id` then `sym_id`), `size_report_format_human`, and `size_report_format_json`.

2. **Canonical Benchmark Suite (`tools/bench/*` — `AXS-PERF-040`)**:
   - `tools/bench/bench_minimal_startup.ax` (`BENCH-STARTUP-001`): minimal freestanding-ready startup, zero-allocation entry path, and dead-code stripping target.
   - `tools/bench/bench_scalar_loops_bce.ax` (`BENCH-SCALAR-001`): integer/bitwise loop induction and range-proven bounds-check elimination (`BCE`).
   - `tools/bench/bench_escape_sroa_alloc.ax` (`BENCH-MEM-001`): non-escaping aggregate construction, `SROA`, and allocation promotion.
   - `tools/bench/bench_iter_inline_devirt.ax` (`BENCH-IPA-001`): stateful iterator pipeline `map`/`filter`/`fold` fusion and monomorphized dispatch.
   - `tools/bench/bench_simd_autovec_kernel.ax` (`BENCH-SIMD-001`): contiguous dot-product, AXPY, and 1D stencil reduction kernels.
   - `tools/bench/bench_sort_hash_parse.ax` (`BENCH-ALGO-001`): comb-sort, FNV-1a open-addressing probe table, and integer lexer/parser state machine.
   - `tools/bench/bench_compile_throughput.ax` (`BENCH-COMPILE-001`): synthetic compiler pipeline stress test (lexer + Pratt expression parser + SSA value numbering).

3. **Benchmark & Budget Enforcement Harness (`tools/perf.py` — `AXS-PERF-041..044`, `REQ-OPT-255`)**:
   - Compiles and executes the canonical `tools/bench/*.ax` suite across `-O0`, `-O1`, `-O2`, `-Os`, `-Oz`.
   - Enforces golden output & exit-code verification against `--interp` before accepting any timing sample (`AXS-PERF-041`).
   - Computes non-parametric statistical distributions (`min_us`, `median_us`, `p90_us`, `max_us`, `mean_us`, `rel_mad_pct`, `stability`) (`AXS-PERF-042`).
   - Parses PE32+ section headers (`.text`, `.rdata`, `.data`, `.bss`, `.pdata`/`.xdata`, `.idata`) to compute 3D footprint metrics (`file_size_bytes`, `stripped_file_size_bytes`, `mapped_size_bytes`, `startup_working_set_bytes`, `peak_working_set_bytes`).
   - Enforces all 9 quantitative `SPEC-76` budgets (`BUDGET-CTIME-001`, `BUDGET-SPEED-001`, `BUDGET-IR-001`, `BUDGET-SIZE-001`, `BUDGET-SIZE-002`, `BUDGET-START-001`, `BUDGET-DET-001`, `BUDGET-SELF-001`, `BUDGET-SELF-002`) under `--check-budgets`, supports baseline regression comparison (`--compare`), and emits machine-readable schema v1 JSON reports (`--json-out`, `--time-passes-json`, `--size-report-json`).

4. **Verification Suite (`tests/run/perf_contract/*`)**:
   - `tests/run/perf_contract/perf_contract_engine.test`, `tests/run/perf_contract/perf_contract_oracle.py`, and `tests/run/perf_contract/perf_contract_probe.ax.in`: live end-to-end probe of `compiler.driver.perf_telemetry` in `--interp` and native x86-64 modes plus full `tools/perf.py` budget and JSON schema verification.
   - `tests/run/perf_contract/perf_profiles_zero_cost_and_traps.ax`: verifies zero-cost iterator/tuple/slice abstractions and safety-barrier preservation across `[interp]`, `[native]`, and `[native-O1]`.
   - `tests/run/perf_contract/perf_size_sharing_and_startup.ax`: verifies monomorphization body-sharing profitability, section GC reachability, cold panic splitting, `.bss` zero-file-size invariants, and bounded auto-tuning legality across `[interp]`, `[native]`, and `[native-O1]`.

## Files changed

- compiler/driver/perf_telemetry/mod.ax
- tests/run/perf_contract/perf_contract_engine.test
- tests/run/perf_contract/perf_contract_oracle.py
- tests/run/perf_contract/perf_contract_probe.ax.in
- tests/run/perf_contract/perf_profiles_zero_cost_and_traps.ax
- tests/run/perf_contract/perf_size_sharing_and_startup.ax
- tools/bench/bench_compile_throughput.ax
- tools/bench/bench_escape_sroa_alloc.ax
- tools/bench/bench_iter_inline_devirt.ax
- tools/bench/bench_minimal_startup.ax
- tools/bench/bench_scalar_loops_bce.ax
- tools/bench/bench_simd_autovec_kernel.ax
- tools/bench/bench_sort_hash_parse.ax
- tools/perf.py

## Verification

- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T625` -> synced 14 changed files cleanly into `build-snap-T625`.
- `python tools/axtest.py -j 1 --compiler build-snap-T625/build/axiomc2.exe --build-dir build-snap-T625 run/perf_contract run/opt_pgo_gc run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax` -> `WEAK-NATIVE 0`, `TOTAL 30 PASS 30 FAIL 0 SKIP 0 XFAIL 0`.
- `python tools/perf.py --compiler build-snap-T625/build/axiomc2.exe --bench-dir tools/bench --check-budgets --tune` -> exit `0`, all 7 canonical benchmarks `[PASS]`, all 9 `SPEC-76` quantitative budgets `PASS`.
- `python tools/archcheck.py` -> `archcheck: 194 files scanned, 0 violations`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T625` -> verified all 14 task files accounted for and within scope.

STATUS: COMPLETE round=0
