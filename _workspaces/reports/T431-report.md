# T431 report — artifact / link / encoder / build-path baseline fixes

## Summary
All 8 T431 baseline test IDs pass under `build-snap-T431/build/axiomc2.exe` (0 reclassified as `environment` since GNU `gcc`/`ld`/`objdump` are available via MSYS2 UCRT64 and `skip-unless: tool ...` guards were added for hosts where those tools are absent). In addition, `encode/axiom/gnu_as_vectors.ax`, `selfhost/link/qa_pe_headers_and_imports.ax`, all 34 `selfhost/**/bundles_current.test`, all 17 `driver/dep_file/*.test`, and a new focused regression test (`link/dll/rt_tls_and_std_reachability.test`) pass with `WEAK-NATIVE 0` and `archcheck` clean.

## Root cause per group

### Group A — Custom minimal `<std>/core/prelude.ax` stubs vs auto-loaded `std/future/{mod,block_on}.ax` (2 IDs)
- **IDs**:
  - `run/artifact_container/artifact_container_engine.test`
  - `conformance/p18/e18_4_artifacts/e18_4_artifacts_oracle.test`
- **Symptom at HEAD**: `error[AX_NAME_UNRESOLVED_IMPORT]: use path does not name an existing item or module --> std/future/mod.ax:27:9: pub use std.core.prelude.Poll` (plus `Future`, `Context`, `Waker`).
- **Cause**: Both test harnesses construct a minimal synthetic `mini_std/core/prelude.ax` (`pub fn prelude_loaded() -> i32 { 1 }`) and pass `--std-root mini_std` while running in a working directory where `std/future/mod.ax` and `std/future/block_on.ax` exist on disk. `pipe_append_std_future_files_if_needed` in `compiler/driver/pipeline.ax` unconditionally appended `std/future/mod.ax` and `std/future/block_on.ax` whenever `project_has_std_prelude(proj)` was true, failing name resolution against minimal custom preludes that do not define `Poll`.
- **Fix (`compiler/driver/pipeline.ax`)**: Added `project_std_prelude_defines_poll(proj)` to inspect the loaded `<std>/core/prelude.ax` buffer for `Poll`. Probe recording (`project_record_probe` for `--dep-file` reproducibility) remains unconditional, while `project_add_file` for `std/future/{mod,block_on}.ax` runs only when the loaded prelude actually defines `Poll`. Verified all 17 `driver/dep_file/*.test`, `modules/prelude_implicit`, and `typeck/async/async_basic_pos.ax` remain green.

### Group B — Unreferenced `<std>` helper emission into user `.obj` files & missing host-tool guards (2 IDs)
- **IDs**:
  - `driver/build_emit_obj.test`
  - `conformance/p18/e18_6_separate_compilation/e18_6_separate_compilation_oracle.test`
- **Symptom at HEAD**:
  - `driver/build_emit_obj.test` failed when cross-linking `math.obj` with a pure C `driver.c` via `gcc`: undefined reference to `__ax_host_print` (39 relocations inside `math.obj` even though `math.ax` performs pure integer arithmetic and no printing). Also lacked `skip-unless: tool gcc` / `skip-unless: tool objdump` guards.
  - `e18_6_separate_compilation_oracle.test` failed from bloated/duplicate unreferenced `<std>` `.text` definitions emitted into every separately compiled `.obj` unit.
- **Cause**: `driver_emit_objmodel_filtered_ex` in `compiler/driver/pipeline.ax` emitted every non-generic `<std>` function (`std/future/mod.ax`'s `trace_poll`, `trace_spawn`, `trace_wake`, `trace_park`, `trace_block_on`, `trace_cancel_drop` calling `print` -> `__ax_host_print`, and `std/core/prelude.ax`'s `prelude_loaded`) into every `.obj` regardless of whether user code referenced them.
- **Fix (`compiler/driver/pipeline.ax`, `tests/driver/build_emit_obj.test`)**:
  - Added a fixed-point `MIR_OP_CONST` symbol reachability worklist (`pipe_bodies_ref_sym` + `pipe_fid_is_std`) in `driver_emit_objmodel_filtered_ex` so non-generic `<std>` functions are lowered and emitted only when transitively referenced by emitted user/monomorphized MIR bodies.
  - Added `skip-unless: tool gcc` and `skip-unless: tool objdump` to `tests/driver/build_emit_obj.test`.

### Group C — Zero-function `--dll` monomorphization state & PE `--rt-obj` TLS runtime support under GNU `ld` (2 IDs)
- **IDs**:
  - `link/dll/pe_dll.test`
  - `link/dll/gnu_ld_run.test`
- **Symptom at HEAD**:
  - `link/dll/pe_dll.test` failed on case `9) Zero-export DLL (empty_dll.ax)`: `error[AX_SESSION_INTERNAL]: generic or malformed body reached native backend`.
  - `link/dll/gnu_ld_run.test` failed when GNU `ld` linked `tests/run/concurrency/tls/*.ax` against `axiom_rt.obj` (`--rt-obj`) due to undefined `_tls_index`, uninitialized PE TLS directory (`_tls_used`), missing `-lsynchronization` (`WaitOnAddress`/`WakeByAddressSingle`/`WakeByAddressAll`), and `gnu_ld_run_oracle.py` checking `t.id in baseline_ids` without the `run/` prefix returned by `axtest.discover(tests/run)`. Also lacked `skip-unless: tool` guards.
- **Cause**:
  1. When compiling a 0-function user module (`empty_dll.ax`) with `--dll`, `thir_is_mono_prepared(thir)` remained `false`, causing `mir_build_fn` to fall back to `mb_count_generic_params_in_hir == 0` instead of skipping uninstantiated generic templates (`block_on<F, T>`).
  2. `pe_build_runtime_coff_obj` in `compiler/link/import.ax` did not emit `_tls_index` (`.data`), `_tls_start`/`.tls$AAA`, `_tls_end`/`.tls$ZZZ`, `__xl_a`, or the 40-byte `IMAGE_TLS_DIRECTORY64` `_tls_used` in `.rdata` needed by GNU `ld` (`i386pep`) to populate PE DataDirectory[9] and initialize per-thread TLS slots at startup.
- **Fix (`compiler/driver/pipeline.ax`, `compiler/link/import.ax`, `tests/link/dll/gnu_ld_run.test`, `tests/link/dll/gnu_ld_run_oracle.py`)**:
  - Marked `thir_set_mono_prepared(thir, true)` at the start of `driver_emit_objmodel_filtered_ex` in `is_build_mode` when not yet set, and guarded own generic items via `pipe_item_has_own_generics`.
  - Extended `pe_build_runtime_coff_obj` (`compiler/link/import.ax`) to emit `.data` (`_tls_index`), `.tls$AAA` (`_tls_start`), `.tls$ZZZ` (`_tls_end`), and `.rdata` (`__xl_a`, `_tls_used` with `AX_RELOC_X86_64_64` relocations).
  - Updated `tests/link/dll/gnu_ld_run_oracle.py` to pass `-lsynchronization` when `libsynchronization.a` is present and check `f"run/{t.id}" in baseline_ids`; added `skip-unless: tool gcc`, `ld`, `objdump` to `tests/link/dll/gnu_ld_run.test`.
  - Added focused regression test `tests/link/dll/rt_tls_and_std_reachability.test` covering empty `--dll`, `--emit=obj` dead-`<std>` elimination, `--rt-obj` TLS sections/symbols/relocations, and GNU `ld` execution of `@thread_local` code.

### Group D — Build-graph probe `--interp` subprocess timeout (1 ID)
- **ID**:
  - `conformance/p20/e20_1_build_graph_driver/e20_1_build_graph_driver_oracle.test`
- **Symptom at HEAD**: `subprocess.TimeoutExpired` at `180s` while running the assembled multi-module `compiler.build.*` probe bundle under `axiomc2 run --interp`.
- **Cause**: As the embedded compiler modules grew, `--interp` execution of the `e20_1` probe bundle takes ~231 s wall time, exceeding the hard-coded `timeout=180` in `e20_1_build_graph_driver_oracle.py`.
- **Fix (`tests/conformance/p20/e20_1_build_graph_driver/e20_1_build_graph_driver_oracle.{py,test}`)**: Raised the `--interp` subprocess timeout from `180` to `600` s, the `-O0` build timeout from `120` to `300` s, and the `.test` manifest `timeout:` from `900` to `1800` s (matching T430). Assertions and expected stdout are unchanged.

### Group E — Encoder table freshness & `gnu_as_vectors.ax` twin sync (1 ID + twin)
- **ID**:
  - `encode/encode_tables_current.test` (plus `encode/axiom/gnu_as_vectors.ax`)
- **Symptom at HEAD**: `FAIL: verbatim copy of compiler/target/x64/encode.ax in tests/encode/axiom/gnu_as_vectors.ax does not match compiler/target/x64/encode.ax on disk.`
- **Cause**: `compiler/target/x64/encode.ax` gained XMM/SSE, `cmovcc`, atomic (`lock xadd`/`cmpxchg`/etc.), masked prologue/epilogue, `x64_emit_tls_addr_obj` (`AX_RELOC_X86_64_TLSREL`), and the `REX.WR` (`0x4C`) fix in `x64_lea_sym` (`AX0-FIX-ENC-LEA-SYM-REX`), without regenerating `tests/encode/axiom/gnu_as_vectors.ax` or updating `tools/gen_encode_tests.py`.
- **Fix (`tools/gen_encode_tests.py`, `tests/encode/axiom/gnu_as_vectors.ax`)**:
  - Added `RELOC_X86_64_TLSREL` and `AX_RELOC_X86_64_TLSREL` (`6u32`) to the inline `module compiler.obj.coff` stub in `tools/gen_encode_tests.py`.
  - Marked `AX0-FIX-ENC-LEA-SYM-REX` (`ax_x64_lea_sym` with `r8..r15`) as `ax_fixed=True` so `tests/encode/encode_tests.inc` preserves the frozen `bootstrap/axiom0` C expectation (`0x49`) while `tests/encode/axiom/gnu_as_vectors.ax` verifies `compiler/target/x64/encode.ax` against GNU `as`'s true `0x4C 0x8D ...` encoding across all 10,211 vectors.
  - Regenerated via `python tools/gen_encode_tests.py` (`encode_tests.inc` unchanged; `gnu_as_vectors.ax` updated cleanly with no hand edits).

### Selfhost bundle regeneration
- Regenerated `tests/selfhost/driver`, `tests/selfhost/link`, and `tests/selfhost/obj_link_driver` after editing `compiler/driver/pipeline.ax` and `compiler/link/import.ax`.
- Updated 5 `LinkerContext` struct literals in `tests/selfhost/link/qa_pe_headers_and_imports.ax.in` to initialize `tls_dir_rva: 0u32, tls_dir_size: 0u32` (added to `LinkerContext` in T413 before `selfhost/link` was regenerated) and re-ran `tests/selfhost/link/gen_link_tests.py`.

## Verification
- **Stage-2 build in `build-snap-T431`**:
  - Built cleanly with `python tools/build_axiomc.py --root build-snap-T431 --build-dir build-snap-T431/build --stage 1` followed by `--stage 2`.
  - `build-snap-T431/build/axiomc2.exe` (`8083968` bytes, `SHA256 = 0CC9D722CB36B5C743619D80D94669C6DA81C6AC445E13331CDAAB53EF136F82`) and `axiomc1.exe`, `axiomc.exe`, `axiomc2_O1.exe` copied to `<repo>/build/` (`axiom0.exe` untouched).
- **All 8 T431 IDs + new regression test (`axtest.py --root build-snap-T431 --compiler build-snap-T431/build/axiomc2.exe --exclude-requires axiom0-internal --no-cache -v -j 2`)**:
  - `PASS run/artifact_container/artifact_container_engine.test`
  - `PASS conformance/p18/e18_4_artifacts/e18_4_artifacts_oracle.test`
  - `PASS conformance/p18/e18_6_separate_compilation/e18_6_separate_compilation_oracle.test`
  - `PASS conformance/p20/e20_1_build_graph_driver/e20_1_build_graph_driver_oracle.test`
  - `PASS driver/build_emit_obj.test`
  - `PASS link/dll/gnu_ld_run.test` (500+ native `tests/run/` programs cross-linked with GNU `ld` against `axiom_rt.obj`, including all 8 `concurrency/tls/*.ax` tests)
  - `PASS link/dll/pe_dll.test`
  - `PASS encode/encode_tables_current.test`
  - `PASS link/dll/rt_tls_and_std_reachability.test`
- **Additional regression & bundle checks (`WEAK-NATIVE 0`, `FAIL 0`)**:
  - `PASS encode/axiom/gnu_as_vectors.ax` (`[interp]`, `[native]`, `[native-O1]` — 10,211 vectors)
  - `PASS encode/axiom/qa_encode_reloc_and_sym.ax`, `PASS encode/atomics/encode_atomics.ax`
  - `PASS selfhost/link/qa_pe_headers_and_imports.ax`, `qa_pe_linker_diff.ax`, `qa_pe_local_symbols.ax`
  - `PASS` all 34 `selfhost/**/bundles_current.test` (`TOTAL 57 PASS 56 FAIL 0 SKIP 1`, `WEAK-NATIVE 0`)
  - `PASS` all 17 `driver/dep_file/*.test`, `PASS modules/prelude_implicit` (`[interp]`, `[native]`, `[native-O1]`), `PASS typeck/async/async_basic_pos.ax`
  - `axiomc2 check` clean (`0 errors`) on all 4 regenerated `selfhost/driver/qa_driver_*.ax` bundles
- **1-byte temporary mutation proof**:
  - Mutated `RT-TLS-AND-STD-REACHABILITY-OK` -> `RT-TLS-AND-STD-REACHABILITY-OX` in `tests/link/dll/rt_tls_and_std_reachability.test`: `axtest.py` exited `1` (`FAIL link/dll/rt_tls_and_std_reachability.test: stdout differs at byte 29`). Restored original bytes and re-verified `PASS` (`rc=0`).
- **Architecture check**:
  - `python tools/archcheck.py --root build-snap-T431`: `229 files scanned, 0 violations`.

## Baseline
Removed the T431 section header, all 8 T431 test ID lines, and trailing blank line from `_workspaces/baseline-failures.txt`.

## Round 1
- **Finding F1 (`tests/selfhost/driver/qa_driver_*_b.ax` stale golden `BLOBS` & `FULL_MODULES` timeout headroom)**:
  - Re-ran `python tests/selfhost/driver/gen_driver_tests.py --refresh-goldens --axiom0 build-snap-T431/build/axiomc2.exe` so the embedded `BLOBS` reference tables in `tests/selfhost/driver/qa_driver_commands_b.ax` and `tests/selfhost/driver/qa_driver_inspect_diff_b.ax` reflect `T431`'s dead-`<std>` `.obj` pruning and `--rt-obj` TLS runtime sections, and raised `// timeout:` on the `FULL_MODULES` bundles (`qa_driver_inspect_diff_{a,b}.ax`, `qa_driver_commands_{a,b}.ax`) from `1200` to `1800` s (matching `gen_obj_link_driver_tests.py`) so concurrent `-j 2` `[native]` (`-O0`) builds (~1210 s wall time when paired head-to-head) do not time out at `1200` s. Verified `python tests/selfhost/driver/gen_driver_tests.py --check` exits `0` and both `_b` bundles pass in `[native]` and `[native-O1]`.
- **`WEAK-NATIVE` elimination in `tests/selfhost/obj_link_driver/qa_obj_link_driver_{diff,smoke}.ax`**:
  - Updated `tests/selfhost/obj_link_driver/gen_obj_link_driver_tests.py` (`MAIN_TEMPLATE` and `gen_diff_bundle`) to emit `print("OK %(tag)s\\n");` before returning `0` and `// stdout: OK <tag>\n` in the generated test headers (matching `tests/selfhost/driver/gen_driver_tests.py`), then regenerated `qa_obj_link_driver_diff.ax` and `qa_obj_link_driver_smoke.ax` and verified `gen_obj_link_driver_tests.py --check` exits `0`.

## Files changed
- _workspaces/baseline-failures.txt
- _workspaces/reports/T431-qa.md
- _workspaces/reports/T431-report.md
- compiler/driver/pipeline.ax
- compiler/link/import.ax
- tests/conformance/p20/e20_1_build_graph_driver/e20_1_build_graph_driver_oracle.py
- tests/conformance/p20/e20_1_build_graph_driver/e20_1_build_graph_driver_oracle.test
- tests/driver/build_emit_obj.test
- tests/encode/axiom/gnu_as_vectors.ax
- tests/link/dll/gnu_ld_run.test
- tests/link/dll/gnu_ld_run_oracle.py
- tests/link/dll/qa_t431_tls_and_std_reachability_bounds.test
- tests/link/dll/qa_t431_tls_and_std_reachability_bounds_oracle.py
- tests/link/dll/rt_tls_and_std_reachability.test
- tests/link/dll/rt_tls_and_std_reachability_oracle.py
- tests/selfhost/driver/gen_driver_tests.py
- tests/selfhost/driver/qa_driver_commands_a.ax
- tests/selfhost/driver/qa_driver_commands_b.ax
- tests/selfhost/driver/qa_driver_inspect_diff_a.ax
- tests/selfhost/driver/qa_driver_inspect_diff_b.ax
- tests/selfhost/link/qa_pe_headers_and_imports.ax
- tests/selfhost/link/qa_pe_headers_and_imports.ax.in
- tests/selfhost/link/qa_pe_linker_diff.ax
- tests/selfhost/link/qa_pe_local_symbols.ax
- tests/selfhost/obj_link_driver/gen_obj_link_driver_tests.py
- tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax
- tools/gen_encode_tests.py

STATUS: COMPLETE round=1
