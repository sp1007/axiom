# T818 Report — E19.5 Test Runner UX 2.0 (`axiomc test`), MIR Differential Harness, Optimization Pass Replay/Bisection & Debug/Trace Audit

STATUS: COMPLETE

## Summary

Implemented the self-hosted Phase 19 E19.5 test framework UX 2.0 (`compiler/test_runner/mod.ax`), optimization pass fuel-limiter, `O(log2 M)` binary-search bisection, and self-contained pass replay engine (`compiler/opt/bisect/mod.ax`), `axiomc test` CLI subcommand driver (`compiler/driver/test_cmd/mod.ax`), and differential verification suite (`tests/run/test_ux/`) per `spec/SPEC-104-docgen-test-framework-ux.md` (`INV-TST-001`):

1. **Integrated Test Runner UX 2.0, Isolated Test Binary & Build-Feature Invariance (`AXS-TST-001..004`, `REQ-TOOL-002`, `REQ-TOOL-187`)**:
   - Implemented deterministic 128-bit `test_id = BLAKE3_128("AXIOM-TEST-ID-v1" || module_path || canonical_test_name)` (`test_runner_compute_test_id`), deterministic per-test PRNG seed derivation (`test_runner_derive_prng_seed`), and isolated per-test temporary directory formatting (`target/test-tmp/<test_id_hex>/`, `test_runner_format_tempdir`).
   - Implemented `test_runner_verify_binary_isolation_and_feature_invariance` querying `CompilerDB` (`query_parse_module`, `query_module_def_map`, `query_resolve_module`, `query_item_signature`, `query_typeck_body`, `query_mir_body`) to verify that `axiomc test` emits an isolated test binary (`target/<triple>/test/<pkg>-test.exe`), `axiomc build` strips 100% of test items/strings from production binaries, build features (`--feature`, `--cfg test`, `--interp`, `--opt-bisect`, `-g`, `--trace`) never alter core language semantics, and disabled `debug_assert` never lowers to an unsafe `unreachable` optimizer hint.
   - Implemented parallel worker result buffering and deterministic `(module_path, span.start, test_id)` canonical sorting (`test_runner_sort_results`, `test_runner_execute_suite`) so `--jobs=1` and `--jobs=N` emit byte-identical human and `AXTEST` JSON reports (`test_runner_render_suite_human`, `test_runner_render_suite_json`).

2. **Verified-MIR Reference Interpreter Oracle & Differential Execution Harness (`AXS-TST-010..012`, `REQ-TOOL-003`, `REQ-TOOL-009`)**:
   - Implemented 6-tuple observable outcome comparison `O(T) = (exit_code, return_value, stdout_bytes, stderr_bytes, panic_kind, drop_sequence)` (`test_runner_compare_differential`), automatically setting `handoff_to_opt_bisect = true` when `O_interp == O_native_O0` and `O_native_opt != O_interp`.
   - Implemented `test_runner_verify_zero_oracle_runtime_overhead` and PE binary inspection in `test_ux_oracle.py` confirming zero `.axmir`, `.axoracle`, `.axmeta`, or `.axdb` sections/markers leak into production executables.

3. **Optimization Pass Provenance Indexing, `O(log2 M)` Bisection & Self-Contained Replay (`AXS-TST-020..022`, `REQ-TOOL-179`)**:
   - Implemented canonical `(cgu_index, fn_semantic_key, pass_ordinal, iteration_index)` sorting and 1-based monotonic `step_id` assignment (`opt_bisect_sort_steps`), fuel-gated pass execution (`--opt-bisect-limit=<N>`, `opt_bisect_should_run_step`, `opt_bisect_eval_pipeline_at_limit`), and `O(log2 M)` binary search (`opt_bisect_run_binary_search`).
   - Verified on the canonical 16-step seeded pipeline (`opt_bisect_build_seeded_demo_pipeline`) that binary search tests limits `8 -> 4 -> 6 -> 5` (`4` evaluations) and isolates `step_id = 6` (`pass = "gvn"`, `fn = "bisect_demo.compute_window"`), rendering both canonical terminal logs (`opt_bisect_render_terminal`) and JSON (`opt_bisect_render_json`).
   - Implemented self-contained `AX_OPT_REPLAY` manifest export and execution (`opt_replay_from_bisect_report`, `opt_replay_export_manifest_json`, `opt_replay_execute`) with zero workspace file access (`workspace_files_accessed == 0`) and `--verify-each` `AX_ICE_MIR_VERIFY` enforcement (`exit_code == 3`).

4. **Target-Independent Debug Model, `.debug_line`, Logical Inlined Frames, `OptimizedOut` Honesty & Zero-Cost Disabled Tracing (`AXS-TST-030..035`, `REQ-TOOL-005..008`, `REQ-TOOL-010..011`, `REQ-TST-112`)**:
   - Implemented target-neutral `SemanticDebugModel` and container projection across PE/COFF, ELF, Mach-O, and WASM (`test_runner_project_debug_container_sections`), `-O0` monotonic `.debug_line` range verification (`test_runner_verify_o0_debug_line_monotonic`), tiered DWARF section verification (`test_runner_verify_tiered_dwarf_sections`), 3-level nested inlined frame synthesis (`f -> g -> h` at 1 physical PC, `test_runner_verify_logical_inline_frames`), `OptimizedOut` honesty with zero `-g` machine-code drift (`code_hash_without_g == code_hash_with_g`, `test_runner_verify_optimized_out_honesty`), and zero-cost disabled trace verification (`test_runner_verify_zero_cost_disabled_trace`, `test_runner_audit_debug_and_trace`).

5. **`axiomc test` CLI Subcommand Driver (`compiler/driver/test_cmd/mod.ax`, `AXS-TST-050`)**:
   - Implemented `test_parse_cli_args` and `test_cmd_execute` supporting `--doc`, `--diff`, `--interp`, `--opt-bisect`, `--opt-bisect-limit=<N>`, `--opt-replay=<manifest>`, `--audit-debug`, `--trace`, `--seed=<u64>`, `--jobs=<N>`, `--include-ignored`, and `--format=json|jsonl` with deterministic exit codes (`0` passed, `1` test/bisect/audit failure, `2` CLI usage error, `3` ICE/verifier failure).

## Verification

Executed:
```
python tools/axtest.py --compiler build/axiomc2.exe -j 1 --exclude-requires axiom0-internal run/test_ux
```
Result:
```
WEAK-NATIVE 0
TOTAL 10 PASS 10 FAIL 0 SKIP 0 XFAIL 0
```

## Files changed

- compiler/opt/bisect/mod.ax
- compiler/test_runner/mod.ax
- compiler/driver/test_cmd/mod.ax
- tests/run/test_ux/test_ux.test
- tests/run/test_ux/test_ux_oracle.py
- tests/run/test_ux/test_ux_probe.ax.in
- tests/run/test_ux/test_discovery_filter_and_mir_diff.ax
- tests/run/test_ux/test_discovery_filter_and_mir_diff.stdout
- tests/run/test_ux/opt_bisect_and_replay_isolation.ax
- tests/run/test_ux/opt_bisect_and_replay_isolation.stdout
- tests/run/test_ux/debug_metadata_inline_and_trace_audit.ax
- tests/run/test_ux/debug_metadata_inline_and_trace_audit.stdout
- _workspaces/reports/T818-report.md
