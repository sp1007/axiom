# T090 Report — E11.3 Host threading intrinsics & std.thread spawn/join/scope on Windows

## Summary

Implemented task **T090** (`REQ-CONC-219`, `spec/SPEC-32-threads-sync.md` §§1–2 `AXS-SYNC-001`..`AXS-SYNC-016`), delivering the complete host threading and futex intrinsics across the compiler (`typeck`, `lir`, `interp`), Windows x64 runtime (`std.sys.windows.thread`), standard library (`std.thread`), and multi-mode test suite (`tests/std/thread/*.ax`):

1. **Host Threading & Futex Intrinsics (`std/core/host.ax`, `compiler/types/typeck.ax`, `compiler/lir/builder.ax`)**:
   - Added `@lang("host_intrinsic")` declarations in `std/core/host.ax` for `thread_spawn`, `thread_join`, `thread_detach`, `thread_current_id`, `thread_yield`, `thread_sleep_ns`, `futex_wait`, and `futex_wake`.
   - Wired `@lang("host_intrinsic")` validation and signature checking (`tc_host_thread_intrinsic_sig_ok`), generic callable bound closure parameter/return inference (`tc_build_callable_hint_ty`, `check_callable_bound_outputs_for_call`), and structured `Scope.spawn` capture validation (`boundary_kind == 4u8`: shared `view<U>` where `U: Share`, disjoint `mut_view<U>` where `U: Send`) in `compiler/types/typeck.ax`.
   - Lowered `@lang("host_intrinsic")` calls to `__ax_host_<name>` in `compiler/lir/builder.ax` and resolved `__ax_thread_self_entry` inside monomorphized `ax_spawn_trampoline<F, T>` to the enclosing trampoline symbol so function-pointer entry arguments do not require unresolved generic symbol deductions.

2. **Windows x64 OS Threading, Panic Isolation & Futex Runtime (`std/sys/windows/thread.ax`)**:
   - Implemented `__ax_host_thread_spawn`, `__ax_host_thread_join`, `__ax_host_thread_detach`, `__ax_host_thread_current_id`, `__ax_host_thread_yield`, `__ax_host_thread_sleep_ns`, `__ax_host_futex_wait`, and `__ax_host_futex_wake` backed by Win32 `CreateThread`, `WaitForSingleObject`, `CloseHandle`, `SwitchToThread`, `Sleep`, and `api-ms-win-core-synch-l1-2-0` (`WaitOnAddress`, `WakeByAddressSingle`, `WakeByAddressAll`).
   - Assigned monotonically unique positive 64-bit `ThreadId`s (`1` for main thread, `>= 2` for spawned threads), synchronized handle/ID publication before child entry via per-slot atomic state, and installed a thread-aware `__ax_rt_exit_process_fn` hook that intercepts child-thread panics (`code == 101`), marks the shared `SpawnSlot` completion state with `Release` ordering, and exits only the panicking OS thread via `ExitThread(101)` so parent and sibling threads continue safely (`AXS-SYNC-015`).

3. **Deterministic Cooperative Multi-Thread & Futex Oracle (`compiler/interp/oracle.ax`, `compiler/interp/interp.ax`)**:
   - Extended `OracleState` in `compiler/interp/oracle.ax` with `oracle_thread_spawn_hb`, `oracle_thread_join_hb`, `oracle_thread_exit`, vector-clock reuse across `> 16` sequential thread spawns, and data-race tracking across `tid == 0` whenever spawned threads are active.
   - Implemented a deterministic seed-driven cooperative scheduler in `compiler/interp/interp.ax` executing `thread_spawn`, `thread_join`, `thread_detach`, `thread_current_id`, `thread_yield`, `thread_sleep_ns`, `futex_wait`, and `futex_wake`, including virtual monotonic deadline wakeups, deterministic deadlock detection when all live threads block without progress, and child-thread panic containment returning sentinel `-2` (`ERR_CHILD_PANICKED`) on `thread_join`.

4. **`std.thread` Public API (`std/thread/mod.ax`)**:
   - Implemented `ThreadId`, `Thread`, `ThreadError`, `ThreadPanic`, `Builder` (`new`, `stack_size`, `name`, `spawn`), `JoinHandle<T>` (`thread`, `is_finished`, `join() -> Result<T, ThreadPanic>`, `detach()`, and non-aborting `Drop` detachment), `spawn`, structured `Scope` / `ScopedJoinHandle<T>` / `scope` (borrowing parent stack data and joining all child threads prior to scope return), `current`, `current_id`, `yield_now`, `sleep`, `sleep_ms`, `sleep_ns`, and cooperative `CancelSource` / `CancelToken`.

5. **Selfhost Bundles & Multi-Mode Run Suite (`tests/selfhost/`, `tests/std/thread/`)**:
   - Regenerated all affected selfhost bundles in `tests/selfhost/`.
   - Added 5 multi-mode (`interp`, `native`, `native-O1`) tests in `tests/std/thread/`: `spawn_join_basic.ax`, `builder_and_detach.ax`, `panic_containment.ax`, `scoped_threads.ax`, and `futex_sleep_yield_cancel.ax`.

## Verification

- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T090` -> snapshot `build-snap-T090` refreshed with 163 changed files.
- `python build-snap-T090/tools/build_axiomc.py --out build-snap-T090/build` -> `STAGE1 OK` + `STAGE2 (O1) OK` (`BUILD-AXIOMC OK: build-snap-T090/build/axiomc2.exe`).
- `python tools/axtest.py --compiler build-snap-T090/build/axiomc2.exe --root build-snap-T090 --build-dir build-snap-T090/build -j 1 --exclude-requires axiom0-internal std/thread` -> `TOTAL 15 PASS 15 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`).
- `python tools/axtest.py --compiler build-snap-T090/build/axiomc2.exe --root build-snap-T090 --build-dir build-snap-T090/build -j 1 --exclude-requires axiom0-internal run/concurrency` -> `TOTAL 37 PASS 37 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`).
- `python tools/axtest.py --compiler build-snap-T090/build/axiomc2.exe --root build-snap-T090 --build-dir build-snap-T090/build -j 1 --exclude-requires axiom0-internal conformance/p11` -> `TOTAL 22 PASS 22 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`).
- `python tools/axtest.py --compiler build-snap-T090/build/axiomc2.exe --root build-snap-T090 --build-dir build-snap-T090/build -j 1 --exclude-requires axiom0-internal bundles_current` -> `TOTAL 34 PASS 34 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`).
- `python tools/archcheck.py` -> `archcheck: 204 files scanned, 0 violations`.
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` -> `requirements: 32308`, `gaps: 0`, `COVERAGE OK`.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> `HARNESS OK`.

## Files changed

- compiler/interp/interp.ax
- compiler/interp/oracle.ax
- compiler/lir/builder.ax
- compiler/types/typeck.ax
- std/core/host.ax
- std/sys/windows/thread.ax
- std/thread/mod.ax
- tests/selfhost/abi/qa_abi_boundary_seam.ax
- tests/selfhost/abi/qa_abi_lir_lower.ax
- tests/selfhost/abi/qa_abi_win64_classify.ax
- tests/selfhost/ast/qa_ast_derives.ax
- tests/selfhost/ast/qa_ast_exprs_a.ax
- tests/selfhost/ast/qa_ast_exprs_b.ax
- tests/selfhost/ast/qa_ast_items.ax
- tests/selfhost/ast/qa_ast_types_pats.ax
- tests/selfhost/backend/qa_backend_diff_lir_a.ax
- tests/selfhost/backend/qa_backend_diff_lir_b.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax
- tests/selfhost/backend/qa_backend_edge.ax
- tests/selfhost/backend/qa_backend_unit.ax
- tests/selfhost/cap/qa_own_cap.ax
- tests/selfhost/diag/qa_diag_codes.ax
- tests/selfhost/diag/qa_diag_emitter.ax
- tests/selfhost/diag/qa_diag_format_json.ax
- tests/selfhost/driver/qa_driver_boundary_edges.ax
- tests/selfhost/driver/qa_driver_cli_and_project.ax
- tests/selfhost/driver/qa_driver_commands_a.ax
- tests/selfhost/driver/qa_driver_commands_b.ax
- tests/selfhost/driver/qa_driver_inspect_diff_a.ax
- tests/selfhost/driver/qa_driver_inspect_diff_b.ax
- tests/selfhost/drop/qa_drop_d01.ax
- tests/selfhost/drop/qa_drop_d02.ax
- tests/selfhost/drop/qa_drop_d03.ax
- tests/selfhost/drop/qa_drop_d04.ax
- tests/selfhost/drop/qa_drop_d05.ax
- tests/selfhost/drop/qa_drop_d06.ax
- tests/selfhost/drop/qa_drop_d07.ax
- tests/selfhost/drop/qa_drop_d09.ax
- tests/selfhost/drop/qa_drop_d10.ax
- tests/selfhost/drop/qa_drop_d11.ax
- tests/selfhost/drop/qa_drop_d12.ax
- tests/selfhost/encode/qa_encode_edge_cases.ax
- tests/selfhost/encode/qa_encode_instructions.ax
- tests/selfhost/encode/qa_encode_relocs_and_frames.ax
- tests/selfhost/hir/qa_hir_corpus.ax
- tests/selfhost/hir/qa_hir_desugar_and_drop.ax
- tests/selfhost/interp/qa_interp_exec_a.ax
- tests/selfhost/interp/qa_interp_exec_b.ax
- tests/selfhost/interp/qa_interp_unit.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_unit.ax
- tests/selfhost/isel/qa_frame_layout_and_verify.ax
- tests/selfhost/isel/qa_isel_diff_golden.ax
- tests/selfhost/isel/qa_isel_frame_seam_and_edge_cases.ax
- tests/selfhost/isel/qa_isel_instructions_and_abi.ax
- tests/selfhost/kernel/qa_kernel_arena.ax
- tests/selfhost/kernel/qa_kernel_dynarray.ax
- tests/selfhost/kernel/qa_kernel_id.ax
- tests/selfhost/kernel/qa_kernel_interner.ax
- tests/selfhost/kernel_source_diag/qa_corpus_differential.ax
- tests/selfhost/kernel_source_diag/qa_session_integration.ax
- tests/selfhost/lex/qa_lex_differential.ax
- tests/selfhost/lex/qa_lex_tokens.ax
- tests/selfhost/lex/u64_max_literal.ax
- tests/selfhost/lexer/qa_lexer_corpus_neg_a.ax
- tests/selfhost/lexer/qa_lexer_corpus_neg_b.ax
- tests/selfhost/lexer/qa_lexer_corpus_pos_a.ax
- tests/selfhost/lexer/qa_lexer_corpus_pos_b.ax
- tests/selfhost/lexer/qa_lexer_session_integration.ax
- tests/selfhost/link/qa_pe_headers_and_imports.ax
- tests/selfhost/link/qa_pe_linker_diff.ax
- tests/selfhost/link/qa_pe_local_symbols.ax
- tests/selfhost/lir/qa_lir_from_ax_a.ax
- tests/selfhost/lir/qa_lir_from_ax_b.ax
- tests/selfhost/lir/qa_lir_from_ax_c.ax
- tests/selfhost/lir/qa_lir_from_ax_d.ax
- tests/selfhost/lir/qa_lir_from_ax_e.ax
- tests/selfhost/lir/qa_lir_from_mir.ax
- tests/selfhost/lir/qa_lir_seam_edge.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_a.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_b.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_c.ax
- tests/selfhost/mir/qa_mir_text_roundtrip.ax
- tests/selfhost/obj/qa_coff_edge_cases.ax
- tests/selfhost/obj/qa_coff_writer_diff.ax
- tests/selfhost/obj/qa_obj_model.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax
- tests/selfhost/opt/qa_opt_pipeline.ax
- tests/selfhost/opt/qa_opt_unit.ax
- tests/selfhost/own/qa_own_init.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_cap_ptr.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_init.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_verify_mir.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax
- tests/selfhost/parse/qa_parse_corpus_a.ax
- tests/selfhost/parse/qa_parse_corpus_b.ax
- tests/selfhost/parse/qa_parse_corpus_c.ax
- tests/selfhost/parse/qa_parse_corpus_d.ax
- tests/selfhost/parse/qa_parse_corpus_e.ax
- tests/selfhost/parse/qa_parse_corpus_f.ax
- tests/selfhost/parse/qa_parse_corpus_g.ax
- tests/selfhost/parse/qa_parse_corpus_h.ax
- tests/selfhost/parse/qa_parse_corpus_i.ax
- tests/selfhost/parse/qa_parse_corpus_j.ax
- tests/selfhost/parse/qa_parse_heavy_a.ax
- tests/selfhost/parse/qa_parse_heavy_b.ax
- tests/selfhost/parse/qa_parse_qa_edge.ax
- tests/selfhost/parse/qa_parse_qa_tuple_struct.ax
- tests/selfhost/parse/qa_parse_recovery_a.ax
- tests/selfhost/parse/qa_parse_recovery_b.ax
- tests/selfhost/parse/qa_parse_terminator_a.ax
- tests/selfhost/parse/qa_parse_terminator_b.ax
- tests/selfhost/parse/qa_parse_terminator_heavy.ax
- tests/selfhost/parser/qa_parser_diff_corpus_wide.ax
- tests/selfhost/parser/qa_parser_diff_neg_a.ax
- tests/selfhost/parser/qa_parser_diff_pos_a.ax
- tests/selfhost/parser/qa_parser_diff_pos_b.ax
- tests/selfhost/parser/qa_parser_session_integration.ax
- tests/selfhost/resolve/qa_resolve_corpus_neg_a.ax
- tests/selfhost/resolve/qa_resolve_corpus_neg_b.ax
- tests/selfhost/resolve/qa_resolve_corpus_neg_c.ax
- tests/selfhost/resolve/qa_resolve_corpus_pos.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_a.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_b.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_c.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_d.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_a.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_b.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_c.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_wide_a.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_wide_b.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_multifile_modules_a.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_multifile_modules_b.ax
- tests/selfhost/source/qa_source_manager.ax
- tests/selfhost/source/qa_source_span.ax
- tests/selfhost/traits/qa_traits_solver_mono.ax
- tests/selfhost/typeck/qa_typeck_a.ax
- tests/selfhost/typeck/qa_typeck_b.ax
- tests/selfhost/typeck/qa_typeck_c.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_a.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_b.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_c.ax
- tests/selfhost/types/qa_types_exhaust.ax
- tests/selfhost/types/qa_types_layout.ax
- tests/selfhost/verify/qa_verify_mir.ax
- tests/selfhost/verify/qa_verify_pipeline.ax
- tests/std/thread/builder_and_detach.ax
- tests/std/thread/futex_sleep_yield_cancel.ax
- tests/std/thread/panic_containment.ax
- tests/std/thread/scoped_threads.ax
- tests/std/thread/spawn_join_basic.ax

## Status

STATUS: COMPLETE round=0
