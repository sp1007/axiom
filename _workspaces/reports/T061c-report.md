# T061c Report: Host-interface intrinsics: oracle implementation + native call lowering

## Summary
Implemented the 21 host-interface intrinsics (ADR-0002 §1, SPEC-04 §11 / AXS-EXT-110) in the MIR interpreter (oracle) and lowered them to `__ax_host_X` calls in native code:
- **Intrinsic Declarations (`std/core/host.ax`)**: Declared the full 21-intrinsic set (`heap_alloc`, `heap_realloc`, `heap_free`, `stdio`, `open`, `read`, `write`, `close`, `file_size`, `args_count`, `arg`, `env_get`, `exe_path`, `exit`, `remove`, `mkdir`, `metadata`, `dir_open`, `dir_next`, `dir_close`, `monotonic_ns`).
- **Interpreter Host Implementation (`host.c`, `host.h`)**:
  - Implemented all 21 intrinsics in C using Win32 W APIs internally with UTF-8 at the boundary.
  - Heap intrinsics register/resize/free interpreter allocations tracked in `InterpCtx->allocs`; raw pointer accesses are validated against bounds and allocation liveness.
  - Converted CLI arguments after `--` into true UTF-8 via `GetCommandLineW()` + `CommandLineToArgvW()` + `WideCharToMultiByte(CP_UTF8, ...)`.
  - Stored all host state (`args`, `file_table`, `dir_table`, `last_monotonic_ns`) in `ctx->host` (`InterpHostState`), strictly adhering to `INV-LAYER-006` with 0 mutable file-scope variables.
- **Interpreter Engine Integration (`interp.c`, `interp.h`)**:
  - Integrated `ax_interp_host_init` and `ax_interp_host_cleanup` inside `ax_interp_run` and `ax_interp_eval_const_expr`.
  - Added clean freeing of heap allocations on interp exit and exposed raw pointer validation helpers.
- **Native Call Lowering (`lower.c`)**:
  - In `get_fn_sym_name`, recognized host intrinsic names and lowered them to direct symbol calls to `__ax_host_<name>`.
- **Driver Pipeline (`pipeline.c`)**:
  - In `ax_options_parse`, captured CLI arguments after `--` and forwarded `argc` and `argv` directly to `ax_interp_run`.
  - Automatically discovered `<std_root>/core/host.ax` when source code mentions host intrinsics.
  - Skipped MIR body generation for host intrinsics.
- **Test Suite (`tests/run/host/`)**:
  - Added full test suite covering heap allocation/realloc/free, use-after-free oracle detection, stdout/stderr byte-exact UTF-8 writes, file create/write/read/file_size/close/remove, directory create/iterate/remove, CLI args with UTF-8 `"xin chào"`, env retrieval (`AXIOM_TEST_HOST`), `exit(7)`, and monotonic clock non-decreasing behavior.
  - Tests carry `// native-after: T070`, `T074`, or `T074b` respectively.
  - Verified native undefined symbol link diagnostics via `native_undefined_symbol.test`.

## Files changed
- bootstrap/axiom0/src/driver/pipeline.c
- bootstrap/axiom0/src/interp/host.c
- bootstrap/axiom0/src/interp/host.h
- bootstrap/axiom0/src/interp/interp.c
- bootstrap/axiom0/src/interp/interp.h
- bootstrap/axiom0/src/lir/lower.c
- std/core/host.ax
- tests/run/host/fs/clock.ax
- tests/run/host/fs/dir.ax
- tests/run/host/fs/file_io.ax
- tests/run/host/heap/alloc.ax
- tests/run/host/heap/use_after_free.ax
- tests/run/host/io/args.ax
- tests/run/host/io/env.ax
- tests/run/host/io/exit7.ax
- tests/run/host/io/write_stdout_stderr.ax
- tests/run/host/native_undefined_symbol.test

## Verification
- `python tools/archcheck.py`: 145 files scanned, 0 violations.
- `ninja -C build-snap-T061c/build`: built cleanly without warnings.
- `build-snap-T061c/build/axiom0-unit.exe`: 71/71 tests PASS.
- `python tools/axtest.py --compiler build-snap-T061c/build/axiom0.exe --filter host`: 10/10 PASS, 0 FAIL, 18 SKIP.
- Full test suite run (`python tools/axtest.py --compiler build-snap-T061c/build/axiom0.exe`): 1291 PASS, 0 FAIL.

STATUS: COMPLETE round=0
