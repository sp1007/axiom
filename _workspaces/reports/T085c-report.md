# T085c Report — Port Driver & Pipeline CLI to Axiom

## Summary

Implemented the self-hosted Axiom compiler driver and pipeline CLI in `compiler/driver/` (`opts.ax`, `pipeline.ax`, `mod.ax`) and differential/integration test bundles in `tests/selfhost/driver/`, achieving byte-for-byte CLI, diagnostic, inspection emitter, multi-file package discovery, MIR interpreter execution, and native COFF `.obj` / PE32+ `.exe` build parity with `axiom0`.

### 1. Driver Options, Manifest Parser & Project Discovery (`compiler/driver/opts.ax`)
- **CLI Subcommands & Flags**: Implemented `driver_find_command`, `driver_find_emitter`, `driver_parse_options`, `driver_parse_cli`, `driver_validate_target`, and usage/version/features/emitter table formatters (`driver_format_usage`, `driver_format_version`, `driver_format_features`, `driver_format_emitters`) matching `src/driver/opts.c` and `src/driver/pipeline.c`.
- **Exit Codes & Driver Diagnostics**: Defined `AX_EXIT_OK` (`0`), `AX_EXIT_DIAG` (`1`), `AX_EXIT_USAGE` (`2`), `AX_EXIT_ICE` (`3`), `AX_EXIT_TIMEOUT` (`124`), and diagnostic helpers for `AX_IO_FILE_NOT_FOUND`, `AX_DRIVER_NO_STD`, `AX_DRIVER_BAD_MANIFEST`, and `AX_DRIVER_UNSUPPORTED_TARGET`.
- **Manifest Parser (`axiom.toml`)**: Implemented `manifest_parse` and `manifest_read_file` supporting `[package]` (`name`, `version`, `edition = "2026"`, `default_target`) and `[dependencies]` validation with exact diagnostic reporting on invalid syntax, unknown sections/keys, or non-`"2026"` editions.
- **Standard Library & Multi-File Package Discovery**: Implemented `find_std_root_with` / `find_std_root` (`--std-root`, `AXIOM_STD`, `<exe_dir>/../std`, `<exe_dir>/std`, CWD `std`), `derive_module_path`, `project_discover`, lexicographical user file sorting, implicit `std.core.{option,result,prelude}` loading, and conditional `std.sys.windows` host module loading when `std.host` / `std.sys` is referenced.

### 2. Full Compilation Pipeline & Inspection Emitters (`compiler/driver/pipeline.ax`, `compiler/driver/mod.ax`)
- **Stage Orchestration (`PipelineCtx`)**: Implemented `pipeline_stage_source`, `pipeline_stage_lex`, `pipeline_stage_parse` (with `session_ensure_module_header` for package files), `pipeline_stage_resolve`, `pipeline_stage_hir`, `pipeline_stage_typeck` (typechecking + monomorphization seeding + unsafe check + comptime evaluation), `pipeline_stage_own` (ownership/move/capability/init checking, MIR building, drop elaboration, and MIR verification, plus standalone `.mir` verification), `pipeline_stage_interp`, and `pipeline_run_stages` with `--time-passes` nanosecond timing (`format_pass_time`).
- **All 11 Inspection Emitters (`driver_execute_inspect`)**:
  - `tokens`: S-expression token stream (`emit_tokens_sexp`) with exact span and escape formatting.
  - `ast`: S-expression AST dump (`ax_ast_dump_filtered`) filtered to main file for single-file inputs and unfiltered for multi-file packages.
  - `resolved`: Resolved symbol table dump (`session_render_resolved_into`).
  - `hir`: Lowered HIR dump (`session_render_hir_into`).
  - `thir`: Typed HIR dump (`session_render_thir_into`).
  - `mir` / `mir-opt`: Unoptimized and `-O1` optimized MIR dumps (`session_own_mir_verify_file`, `session_interp_opt_file`, and standalone `.mir` support).
  - `lir`, `mi`, `mc`, `obj`: Full backend lowering (`driver_emit_backend_text` / `driver_emit_objmodel`) for both `.ax` and standalone `.mir` inputs, including `.rdata` string/constant tables and COFF object summary formatting (`driver_dump_objmodel`).
- **Top-Level Commands (`driver_execute_check`, `driver_execute_run`, `driver_execute_build`, `driver_run_args`, `driver_main`)**:
  - `check`: Runs stages through `STAGE_OWN` and flushes human or `--json` diagnostics.
  - `run`: Runs stages through `STAGE_INTERP` (for `.ax` packages/files and standalone `.mir`), forwarding panic messages (`panic: <msg>\n`) and exit codes.
  - `build`: Runs stages through `STAGE_MONO`, lowers all functions in `build.c` order with inline checked-arithmetic panic blocks (`driver_emit_build_mi_body_obj`), emits `__main` wrapper symbol, and writes either a COFF `.obj` (`--emit=obj`) or linked PE32+ `.exe` (`pe_link_objmodel_to_buf` with `--stack-reserve`).

## Verification

- `python tools/archcheck.py`: `188 files scanned, 0 violations`
- `python tools/axtest.py selfhost/driver driver`: `TOTAL 36 PASS 36 FAIL 0 SKIP 0 XFAIL 0`
  - `tests/selfhost/driver/qa_driver_cli_and_project.ax` (`[interp]`, `[native]`, `[native-O1]`): PASS
  - `tests/selfhost/driver/qa_driver_inspect_diff_a.ax` (`[interp]`, `[native]`, `[native-O1]`): PASS
  - `tests/selfhost/driver/qa_driver_inspect_diff_b.ax` (`[native]`, `[native-O1]`): PASS
  - `tests/selfhost/driver/qa_driver_commands_a.ax` (`[interp]`, `[native]`, `[native-O1]`): PASS
  - `tests/selfhost/driver/qa_driver_commands_b.ax` (`[native]`, `[native-O1]`): PASS

## Files changed

- `compiler/driver/opts.ax`
- `compiler/driver/pipeline.ax`
- `compiler/driver/mod.ax`
- `tests/selfhost/driver/gen_driver_tests.py`
- `tests/selfhost/driver/qa_driver_cli_and_project.ax`
- `tests/selfhost/driver/qa_driver_inspect_diff_a.ax`
- `tests/selfhost/driver/qa_driver_inspect_diff_b.ax`
- `tests/selfhost/driver/qa_driver_commands_a.ax`
- `tests/selfhost/driver/qa_driver_commands_b.ax`

## Status

STATUS: COMPLETE round=0
