# T413 Report — E11.3: @thread_local statics, COFF/PE .tls emission & thread-local storage

## Summary
Task T413 implements `@thread_local` statics, `std.thread.LocalKey<T>`, and Windows x64 COFF/PE `.tls` backend per `spec/SPEC-32-threads-sync.md`, `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-071`, `AXS-EXT-073`, `AXS-EXT-091`), and `_workspaces/reports/unblock-T413.md`.

In Round 1, all 5 findings from QA Gate Round 0 (`_workspaces/reports/T413-qa.md`) were fully resolved and verified on Stage-1 (`axiomc1.exe`) and Stage-2 (`axiomc2.exe`).

### Key Implementations:
1. **Frontend & Diagnostics (`compiler/diag/code.ax`, `compiler/diag/format.ax`, `compiler/hir/hir.ax`, `compiler/hir/lower.ax`, `compiler/types/typeck.ax`, `compiler/own/unsafe.ax`)**:
   - Added `AX_CONC_TLS_ESCAPE` (`166`) and `AX_TYPE_INVALID_TLS_DECL` (`167`).
   - Parsed `@thread_local` attribute and tagged HIR static items with `is_tls: bool`.
   - Validated that `@thread_local` only applies to static items with constant initializers in `compiler/types/typeck.ax`.
   - Evaluated TLS static initializers into `symbol_consts` during type checking.
   - Added support for aggregate constant evaluation of `LocalKey<T>` in `compiler/types/typeck.ax` with `ADDR64` relocations for `init_fn` and `drop_fn`.
   - Enforced in `compiler/own/unsafe.ax` that thread-local borrows (`view<T>` / `mut_view<T>`) cannot escape enclosing functions or cross thread boundaries (`AX_CONC_TLS_ESCAPE`).
   - Allowed safe reads and mutations of `@thread_local static mut` without requiring `unsafe` blocks.

2. **MIR, Verifier & Interpreter (`compiler/mir/mir.ax`, `compiler/mir/builder.ax`, `compiler/verify/verifier.ax`, `compiler/interp/interp.ax`)**:
   - Added `MIR_LOCAL_TLS` (`5`) and mapped thread-local static places to local declarations tagged with `const_sym` and `mut_flag = true`.
   - Fixed closure capture in `compiler/mir/builder.ax`: mutable TLS statics are identified via THIR item lookup and emitted as TLS locals rather than erroneously captured into closure frames.
   - Updated verifier to consider TLS local declarations initialized on function entry.
   - In the interpreter oracle, implemented per-thread isolated TLS storage (`InterpTlsSlot`) tied to `current_tid`. Initialized each slot lazily from its constant initializer upon first thread access, ensuring spawned threads see isolated static storage.

3. **Backend LIR, x64 Codegen, COFF & PE Linker (`compiler/backend/session.ax`, `compiler/lir/lir.ax`, `compiler/lir/builder.ax`, `compiler/target/x64/mod.ax`, `compiler/target/x64/encode.ax`, `compiler/target/x64/frame.ax`, `compiler/target/x64/isel.ax`, `compiler/obj/coff.ax`, `compiler/obj/writer.ax`, `compiler/driver/pipeline.ax`, `compiler/link/linker.ax`, `compiler/link/pe.ax`, `compiler/link/mod.ax`)**:
   - Added `LIR_INST_TLS_ADDR` and `X64_MI_TLS_ADDR`.
   - Lowered TLS local addresses in `lir/builder.ax` to `emit_tls_addr_inst`.
   - Fixed `compiler/backend/session.ax`: guarded constant table emission into `.rdata` to ignore mutable TLS locals (`!(unsafe { (*ldecl).mut_flag })`), preventing duplicate offset-0 symbol definitions that corrupted SECREL relocation calculations.
   - Extended `backend_format_const_sym_name` in `session.ax` to format static symbol names with name suffixes (`.Lconst_<sym>_<name>`) identically to MIR and LIR lowering.
   - In `frame.ax` / `encode.ax`, emitted the Windows x64 TLS address calculation sequence:
     `mov rax, gs:[0x58]` (reading the Thread Environment Block TLS vector via GS override prefix `0x65`),
     `mov edx, dword ptr [rip + _tls_index]` (with `IMAGE_REL_AMD64_REL32` relocation),
     `mov rax, qword ptr [rax + rdx*8]` (indexing TLS array pointer),
     `lea rax, [rax + sym@SECREL32]` (with `IMAGE_REL_AMD64_SECREL` relocation).
   - In `driver/pipeline.ax`, emitted `@thread_local static` data into COFF `.tls$` sections (`SEC_TLS`, `IMAGE_SCN_CNT_INITIALIZED_DATA`) with `SYM_GLOBAL` linkage so cross-section relocations resolve cleanly in the PE linker.
   - In `link/linker.ax`, merged `.tls$` sections into PE `.tls`, synthesized `_tls_index` (in `.data`) and `_tls_callbacks` (in `.rdata`), emitted the 40-byte `IMAGE_TLS_DIRECTORY64` (`_tls_used`) descriptor, and populated PE Data Directory 9 (`IMAGE_DIRECTORY_ENTRY_TLS`).

4. **Standard Library (`std/thread/local.ax`, `std/thread/mod.ax`)**:
   - Implemented `LocalKey<T>` (`local_key_new`, `with`, `with_mut`, `get`, `set`).
   - Implemented dynamic reentrancy tracking per `SPEC-32 AXS-SYNC-021.1`: `borrow_state: i32` (`0` = unborrowed, `> 0` = active shared borrow count, `-1` = active exclusive borrow), panicking on conflicting borrows (`cannot borrow immutably while mutably borrowed`, `cannot borrow mutably while already borrowed`).
   - Implemented lazy per-thread node allocation in `LOCAL_SLOTS_HEAD` with proper drop handling on thread termination: safely checks function pointer addresses (`dfn_addr != 0usize`) before invoking drops.
   - Registered `thread_local_cleanup()` in `std/thread/mod.ax` to be called deterministically at thread termination in `ax_spawn_trampoline`.

5. **Self-Host Discipline & Performance**:
   - Refactored large x64 frame/isel functions and liveness dataflow solvers into standalone helper functions with <= 4 parameters to adhere strictly to frozen `axiom0` stack bounds (`fixups[1024]`).
   - Optimized `UnsafeChecker.has_tls` and MIR builder identifier lookups to short-circuit in O(1) when no TLS statics are present, ensuring zero compilation regressions across the 150,000-line selfhost compiler bundle.

---

## Round 1 QA Findings Resolution

### Finding 1: `LocalKey<T>` Const-Evaluable Aggregate Emission
- **Root Cause**: `compiler/types/typeck.ax` did not support constructing constant aggregate values containing function pointers (`init_fn`, `drop_fn`), causing `LocalKey::new` invocations at file scope to fail type checking or drop function addresses.
- **Fix**: Implemented const aggregate evaluation for struct instances in `typeck.ax` with `ADDR64` relocations referencing the target function symbols.

### Finding 2: `LocalKey<T>` Dynamic Reentrancy Tracking (`SPEC-32 AXS-SYNC-021.1`)
- **Root Cause**: `LocalSlotNode` previously had a boolean `is_borrowed` flag which could not track multiple concurrent shared `with` borrows or distinguish shared vs mutable borrows.
- **Fix**: Replaced with `borrow_state: i32`:
  - `with()`: panics if `borrow_state < 0`, increments `borrow_state` before calling `f`, decrements after `f` returns.
  - `with_mut()`: panics if `borrow_state != 0`, sets `borrow_state = -1` before calling `f`, restores `0` after `f` returns.
  - `get()` and `set()` enforce the same borrow state invariants.

### Finding 3: `LocalKey<T>` Multi-Thread Isolation & Thread-Exit Drop Cleanup
- **Root Cause**: Multi-thread tests in `tests/run/concurrency/tls/tls_threads.ax` hit a SECREL offset 0 collision from `.rdata`, and `tls_local_key_drop.ax` needed to verify deterministic cleanup.
- **Fix**:
  - Filtered out mutable TLS locals from `.rdata` constant tables in `compiler/backend/session.ax:1059`.
  - Added null function pointer check in `std/thread/local.ax:185` (`let dfn_addr = unsafe { *(address_of(dfn) as *const usize) }; if dfn_addr != 0usize && (vp as usize) != 0 { dfn(vp); }`).
  - Implemented and verified `tests/run/concurrency/tls/tls_threads.ax` and `tls_local_key_drop.ax` across all 3 execution modes (`interp`, `native`, `native-O1`).

### Finding 4: Exhaustive Negative UI Tests for TLS Invariants
- **Root Cause**: Only 2 UI tests existed; missing negative coverage for returning TLS references, spawning threads with TLS references, and accessing unsynchronized non-Send types across threads.
- **Fix**: Created 5 negative UI tests in `tests/ui/concurrency/tls/`:
  - `invalid_tls_decl.ax`: Non-static or non-const `@thread_local` declaration -> `AX_TYPE_INVALID_TLS_DECL`.
  - `tls_escape.ax`: Assigning TLS view/mut_view to an outer variable -> `AX_CONC_TLS_ESCAPE`.
  - `tls_escape_return.ax`: Returning a view into a thread-local static -> `AX_CONC_TLS_ESCAPE`.
  - `tls_escape_spawn.ax`: Capturing/passing a thread-local view into `std.thread.spawn` -> `AX_CONC_TLS_ESCAPE`.
  - `tls_escape_unsync.ax`: Attempting to send a non-`Send` `LocalKey<T>` across thread boundary.

### Finding 5: `std/sync` and `std/channel` Test Bundles Freshness
- **Root Cause**: Because `std/thread/mod.ax` imports `std.thread.local`, the generated single-file test bundles in `tests/std/sync` and `tests/std/channel` required `std/thread/local.ax` in `COMMON_PREREQS`.
- **Fix**:
  - Added `"std/thread/local.ax"` to `COMMON_PREREQS` in `tests/std/sync/gen_tests.py` and `tests/std/channel/gen_tests.py`.
  - Regenerated all 15 test bundles across `tests/std/sync/` and `tests/std/channel/`.
  - Verified `python tests/std/sync/gen_tests.py --check` and `python tests/std/channel/gen_tests.py --check` pass cleanly.
  - Verified all 51 test runs pass with `0 FAIL`.

---

## Files changed
- `compiler/backend/session.ax`
- `compiler/diag/code.ax`
- `compiler/diag/format.ax`
- `compiler/driver/pipeline.ax`
- `compiler/hir/hir.ax`
- `compiler/hir/lower.ax`
- `compiler/interp/interp.ax`
- `compiler/link/linker.ax`
- `compiler/link/mod.ax`
- `compiler/link/pe.ax`
- `compiler/lir/builder.ax`
- `compiler/lir/lir.ax`
- `compiler/mir/builder.ax`
- `compiler/mir/mir.ax`
- `compiler/obj/coff.ax`
- `compiler/obj/writer.ax`
- `compiler/own/unsafe.ax`
- `compiler/target/x64/encode.ax`
- `compiler/target/x64/frame.ax`
- `compiler/target/x64/isel.ax`
- `compiler/target/x64/mod.ax`
- `compiler/types/typeck.ax`
- `compiler/verify/verifier.ax`
- `std/thread/local.ax`
- `std/thread/mod.ax`
- `tests/run/concurrency/tls/tls_local_key_drop.ax`
- `tests/run/concurrency/tls/tls_multi_static.ax`
- `tests/run/concurrency/tls/tls_static_basic.ax`
- `tests/run/concurrency/tls/tls_threads.ax`
- `tests/selfhost/abi/qa_abi_boundary_seam.ax`
- `tests/selfhost/abi/qa_abi_lir_lower.ax`
- `tests/selfhost/abi/qa_abi_win64_classify.ax`
- `tests/selfhost/ast/qa_ast_derives.ax`
- `tests/selfhost/ast/qa_ast_exprs_a.ax`
- `tests/selfhost/ast/qa_ast_exprs_b.ax`
- `tests/selfhost/ast/qa_ast_items.ax`
- `tests/selfhost/ast/qa_ast_types_pats.ax`
- `tests/selfhost/backend/qa_backend_diff_lir_a.ax`
- `tests/selfhost/backend/qa_backend_diff_lir_b.ax`
- `tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax`
- `tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax`
- `tests/selfhost/backend/qa_backend_edge.ax`
- `tests/selfhost/backend/qa_backend_unit.ax`
- `tests/selfhost/cap/qa_own_cap.ax`
- `tests/selfhost/diag/qa_diag_codes.ax`
- `tests/selfhost/diag/qa_diag_emitter.ax`
- `tests/selfhost/diag/qa_diag_format_json.ax`
- `tests/selfhost/driver/qa_driver_boundary_edges.ax`
- `tests/selfhost/driver/qa_driver_cli_and_project.ax`
- `tests/selfhost/driver/qa_driver_commands_a.ax`
- `tests/selfhost/driver/qa_driver_commands_b.ax`
- `tests/selfhost/driver/qa_driver_inspect_diff_a.ax`
- `tests/selfhost/driver/qa_driver_inspect_diff_b.ax`
- `tests/selfhost/drop/qa_drop_d01.ax`
- `tests/selfhost/drop/qa_drop_d02.ax`
- `tests/selfhost/drop/qa_drop_d03.ax`
- `tests/selfhost/drop/qa_drop_d04.ax`
- `tests/selfhost/drop/qa_drop_d05.ax`
- `tests/selfhost/drop/qa_drop_d06.ax`
- `tests/selfhost/drop/qa_drop_d07.ax`
- `tests/selfhost/drop/qa_drop_d09.ax`
- `tests/selfhost/drop/qa_drop_d10.ax`
- `tests/selfhost/drop/qa_drop_d11.ax`
- `tests/selfhost/drop/qa_drop_d12.ax`
- `tests/selfhost/encode/qa_encode_edge_cases.ax`
- `tests/selfhost/encode/qa_encode_instructions.ax`
- `tests/selfhost/encode/qa_encode_relocs_and_frames.ax`
- `tests/selfhost/hir/qa_hir_corpus.ax`
- `tests/selfhost/hir/qa_hir_desugar_and_drop.ax`
- `tests/selfhost/interp/qa_interp_exec_a.ax`
- `tests/selfhost/interp/qa_interp_exec_b.ax`
- `tests/selfhost/interp/qa_interp_unit.ax`
- `tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_a.ax`
- `tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_b.ax`
- `tests/selfhost/interp_opt/qa_interp_opt_diff_mir_a.ax`
- `tests/selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax`
- `tests/selfhost/interp_opt/qa_interp_opt_diff_run_a.ax`
- `tests/selfhost/interp_opt/qa_interp_opt_diff_run_b.ax`
- `tests/selfhost/interp_opt/qa_interp_opt_unit.ax`
- `tests/selfhost/isel/qa_frame_layout_and_verify.ax`
- `tests/selfhost/isel/qa_isel_diff_golden.ax`
- `tests/selfhost/isel/qa_isel_frame_seam_and_edge_cases.ax`
- `tests/selfhost/isel/qa_isel_instructions_and_abi.ax`
- `tests/selfhost/kernel_source_diag/qa_corpus_differential.ax`
- `tests/selfhost/kernel_source_diag/qa_session_integration.ax`
- `tests/selfhost/lex/qa_lex_differential.ax`
- `tests/selfhost/lex/qa_lex_tokens.ax`
- `tests/selfhost/lex/u64_max_literal.ax`
- `tests/selfhost/lexer/qa_lexer_corpus_neg_a.ax`
- `tests/selfhost/lexer/qa_lexer_corpus_neg_b.ax`
- `tests/selfhost/lexer/qa_lexer_corpus_pos_a.ax`
- `tests/selfhost/lexer/qa_lexer_corpus_pos_b.ax`
- `tests/selfhost/lexer/qa_lexer_session_integration.ax`
- `tests/selfhost/link/qa_pe_headers_and_imports.ax`
- `tests/selfhost/link/qa_pe_linker_diff.ax`
- `tests/selfhost/link/qa_pe_local_symbols.ax`
- `tests/selfhost/lir/qa_lir_from_ax_a.ax`
- `tests/selfhost/lir/qa_lir_from_ax_b.ax`
- `tests/selfhost/lir/qa_lir_from_ax_c.ax`
- `tests/selfhost/lir/qa_lir_from_ax_d.ax`
- `tests/selfhost/lir/qa_lir_from_ax_e.ax`
- `tests/selfhost/lir/qa_lir_from_mir.ax`
- `tests/selfhost/lir/qa_lir_seam_edge.ax`
- `tests/selfhost/mir/qa_mir_builder_and_drop_a.ax`
- `tests/selfhost/mir/qa_mir_builder_and_drop_b.ax`
- `tests/selfhost/mir/qa_mir_builder_and_drop_c.ax`
- `tests/selfhost/mir/qa_mir_text_roundtrip.ax`
- `tests/selfhost/obj/qa_coff_edge_cases.ax`
- `tests/selfhost/obj/qa_coff_writer_diff.ax`
- `tests/selfhost/obj/qa_obj_model.ax`
- `tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax`
- `tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax`
- `tests/selfhost/opt/qa_opt_pipeline.ax`
- `tests/selfhost/opt/qa_opt_unit.ax`
- `tests/selfhost/own/qa_own_init.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_build_a.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_build_b.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_cap_ptr.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_init.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_a.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_b.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_verify_mir.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_a.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax`
- `tests/selfhost/parse/qa_parse_corpus_a.ax`
- `tests/selfhost/parse/qa_parse_corpus_b.ax`
- `tests/selfhost/parse/qa_parse_corpus_c.ax`
- `tests/selfhost/parse/qa_parse_corpus_d.ax`
- `tests/selfhost/parse/qa_parse_corpus_e.ax`
- `tests/selfhost/parse/qa_parse_corpus_f.ax`
- `tests/selfhost/parse/qa_parse_corpus_g.ax`
- `tests/selfhost/parse/qa_parse_corpus_h.ax`
- `tests/selfhost/parse/qa_parse_corpus_i.ax`
- `tests/selfhost/parse/qa_parse_corpus_j.ax`
- `tests/selfhost/parse/qa_parse_heavy_a.ax`
- `tests/selfhost/parse/qa_parse_heavy_b.ax`
- `tests/selfhost/parse/qa_parse_qa_edge.ax`
- `tests/selfhost/parse/qa_parse_qa_tuple_struct.ax`
- `tests/selfhost/parse/qa_parse_recovery_a.ax`
- `tests/selfhost/parse/qa_parse_recovery_b.ax`
- `tests/selfhost/parse/qa_parse_terminator_a.ax`
- `tests/selfhost/parse/qa_parse_terminator_b.ax`
- `tests/selfhost/parse/qa_parse_terminator_heavy.ax`
- `tests/selfhost/parser/qa_parser_diff_corpus_wide.ax`
- `tests/selfhost/parser/qa_parser_diff_neg_a.ax`
- `tests/selfhost/parser/qa_parser_diff_pos_a.ax`
- `tests/selfhost/parser/qa_parser_diff_pos_b.ax`
- `tests/selfhost/parser/qa_parser_session_integration.ax`
- `tests/selfhost/resolve/qa_resolve_corpus_neg_a.ax`
- `tests/selfhost/resolve/qa_resolve_corpus_neg_b.ax`
- `tests/selfhost/resolve/qa_resolve_corpus_neg_c.ax`
- `tests/selfhost/resolve/qa_resolve_corpus_pos.ax`
- `tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_a.ax`
- `tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_b.ax`
- `tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_c.ax`
- `tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_d.ax`
- `tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_a.ax`
- `tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_b.ax`
- `tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_c.ax`
- `tests/selfhost/resolve_hir/qa_resolve_hir_corpus_wide_a.ax`
- `tests/selfhost/resolve_hir/qa_resolve_hir_corpus_wide_b.ax`
- `tests/selfhost/resolve_hir/qa_resolve_hir_multifile_modules_a.ax`
- `tests/selfhost/resolve_hir/qa_resolve_hir_multifile_modules_b.ax`
- `tests/selfhost/traits/qa_traits_solver_mono.ax`
- `tests/selfhost/typeck/qa_typeck_a.ax`
- `tests/selfhost/typeck/qa_typeck_b.ax`
- `tests/selfhost/typeck/qa_typeck_c.ax`
- `tests/selfhost/typeck_traits/qa_typeck_traits_a.ax`
- `tests/selfhost/typeck_traits/qa_typeck_traits_b.ax`
- `tests/selfhost/typeck_traits/qa_typeck_traits_c.ax`
- `tests/selfhost/types/qa_types_exhaust.ax`
- `tests/selfhost/types/qa_types_layout.ax`
- `tests/selfhost/verify/qa_verify_mir.ax`
- `tests/selfhost/verify/qa_verify_pipeline.ax`
- `tests/std/channel/channel_big_struct.ax`
- `tests/std/channel/channel_boundary_edge.ax`
- `tests/std/channel/channel_bounded_basic.ax`
- `tests/std/channel/channel_move_only_drop.ax`
- `tests/std/channel/channel_mpmc_threads.ax`
- `tests/std/channel/channel_mpsc_threads.ax`
- `tests/std/channel/channel_spsc_threads.ax`
- `tests/std/channel/channel_unbounded_basic.ax`
- `tests/std/channel/gen_tests.py`
- `tests/std/sync/arc_mutex_threads.ax`
- `tests/std/sync/barrier_rendezvous.ax`
- `tests/std/sync/big_struct_sync.ax`
- `tests/std/sync/condvar_signaling.ax`
- `tests/std/sync/gen_tests.py`
- `tests/std/sync/once_cell_init.ax`
- `tests/std/sync/rwlock_readers_writer.ax`
- `tests/ui/concurrency/tls/invalid_tls_decl.ax`
- `tests/ui/concurrency/tls/tls_escape.ax`
- `tests/ui/concurrency/tls/tls_escape_return.ax`
- `tests/ui/concurrency/tls/tls_escape_spawn.ax`
- `tests/ui/concurrency/tls/tls_escape_unsync.ax`

## Verification & Test Results

### 1. Compiler Bootstrap
- **Stage-1 Compiler**:
  - Binary: `build-snap-T413/build/axiomc1.exe`
  - Size: 24,439,296 bytes
  - SHA256: `ab2fc171694ab0ad`
  - Wall clock: 77.45s
- **Stage-2 Compiler (O1)**:
  - Binary: `build-snap-T413/build/axiomc2.exe` (also `build-snap-T413/build/axiomc.exe`)
  - Size: 7,580,160 bytes
  - SHA256: `6b81edc783025b286874bf1e9c0aac2d7acf46a93bbf104d5dca528016b31e6c`
  - Status: STAGE2 (O1) OK, BUILD-AXIOMC OK

### 2. Concurrency TLS Test Suite (`axiomc2.exe`)
- `python tools/axtest.py --compiler build-snap-T413/build/axiomc2.exe --exclude-requires axiom0-internal -j 1 run/concurrency/tls`
  - `tls_static_basic.ax`: PASS (interp, native, native-O1)
  - `tls_multi_static.ax`: PASS (interp, native, native-O1)
  - `tls_threads.ax`: PASS (interp, native, native-O1)
  - `tls_local_key_drop.ax`: PASS (interp, native, native-O1)
  - Result: `TOTAL 12 PASS 12 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`)

### 3. Negative Concurrency UI Test Suite (`axiomc2.exe`)
- `python tools/axtest.py --compiler build-snap-T413/build/axiomc2.exe --exclude-requires axiom0-internal -j 1 ui/concurrency/tls`
  - `invalid_tls_decl.ax`: PASS
  - `tls_escape.ax`: PASS
  - `tls_escape_return.ax`: PASS
  - `tls_escape_spawn.ax`: PASS
  - `tls_escape_unsync.ax`: PASS
  - Result: `TOTAL 5 PASS 5 FAIL 0 SKIP 0 XFAIL 0`

### 4. Standard Library Test Suites (`axiomc2.exe`)
- `python tools/axtest.py --compiler build-snap-T413/build/axiomc2.exe --exclude-requires axiom0-internal -j 1 std/sync std/channel`
  - Result: `TOTAL 51 PASS 51 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`)
- `python tools/axtest.py --compiler build-snap-T413/build/axiomc2.exe --exclude-requires axiom0-internal -j 1 std/thread`
  - Result: `TOTAL 18 PASS 18 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`)

### 5. Self-Host Bundles Suite (`axiomc2.exe`)
- `python tools/axtest.py --compiler build-snap-T413/build/axiomc2.exe -j 1 bundles_current.test`
  - Result: `TOTAL 34 PASS 34 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`)

### 6. Canaries Suite (`axiomc2.exe`)
- `python tools/axtest.py --compiler build-snap-T413/build/axiomc2.exe -j 1 intrinsics`
  - Result: `TOTAL 51 PASS 51 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`)

### 7. Governance, Architecture & Lock Compliance Gates
- `python tools/archcheck.py`
  - Output: `archcheck: 218 files scanned, 0 violations`
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`
  - Output: `requirements: 32308`, `gaps: 0`, `COVERAGE OK`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`
  - Output: `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T413`
  - Output: `0 REFUSED`, all modified files staged in task paths/locks.

STATUS: COMPLETE round=1
