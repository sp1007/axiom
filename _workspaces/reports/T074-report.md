# T074 — std.io / env / process for hosted Windows

## Summary of Work
Implemented `std.io`, `std.env`, and `std.process` for hosted Windows target (`x86_64-pc-windows-msvc`), backed by low-level Win32 FFI bindings in `std/sys/windows/io.ax` and `std/sys/windows/process.ax`.

1. **Win32 IO Syscalls (`std/sys/windows/io.ax`)**:
   - Implemented Win32 kernel32 handle operations: `CreateFileW`, `ReadFile`, `WriteFile`, `CloseHandle`, `GetFileSizeEx`, `SetFilePointer`, `GetConsoleMode`, `WriteConsoleW`, `GetStdHandle`.
   - Manages a 256-slot virtual file descriptor table in the process environment. Virtual handles 0, 1, 2 correspond to Win32 Standard Input (`STD_INPUT_HANDLE`), Standard Output (`STD_OUTPUT_HANDLE`), and Standard Error (`STD_ERROR_HANDLE`).
   - Implemented dual-mode console/pipe dispatch per ADR-0006 §9:
     - When writing to a genuine Windows console (`GetConsoleMode` succeeds), converts UTF-8 bytes to UTF-16 wide characters and writes using `WriteConsoleW`, rendering Vietnamese characters like `Xin chào thế giới` correctly without console codepage corruption.
     - When writing to a pipe, file, or redirected output (`GetConsoleMode` returns 0), writes raw UTF-8 bytes directly via `WriteFile`, ensuring byte-exact pipe streams.

2. **Win32 Process & Env Syscalls (`std/sys/windows/process.ax`)**:
   - Implemented Win32 kernel32/shell32 APIs: `GetCommandLineW`, `CommandLineToArgvW`, `GetEnvironmentVariableW`, `SetEnvironmentVariableW`, `GetModuleFileNameW`, `ExitProcess`, `LocalFree`, `HeapAlloc`, `HeapFree`.
   - Robust UTF-8 <-> UTF-16 conversion helpers:
     - `utf8_to_utf16`: Decodes multi-byte UTF-8 sequences (1-byte ASCII, 2-byte accented/Vietnamese, 3-byte CJK/Vietnamese, 4-byte astral characters) to UTF-16 code units / surrogate pairs, null-terminated.
     - `utf16_to_utf8`: Decodes UTF-16 code units (handling surrogate pairs) to UTF-8 byte streams.
   - Command line parsing via `CommandLineToArgvW` with proper cleanup via `LocalFree`.
   - Tracked heap allocation via `heap_alloc`/`heap_free` to satisfy interpreter memory validation.

3. **Standard IO Library (`std/io/io.ax`)**:
   - Implemented `IoError` error enum.
   - Implemented `File` resource struct with `impl Drop for File` closing open OS handles on exit/scope termination.
   - File manipulation functions: `file_open`, `file_create`, `file_append`, `file_read`, `file_write`, `file_size_of`, `file_close`.
   - Helper convenience functions: `read_to_string`, `write_string`, `write_file`.
   - Formatted output functions: `print`, `println`, `eprint`, `eprintln`.

4. **Standard Environment Library (`std/env/env.ax`)**:
   - Implemented `EnvError` error enum.
   - Implemented `get(name: Str) -> Option<String>` and `var(name: Str) -> Result<String, EnvError>`.
   - Supports full Unicode environment variable names and values (tested with Vietnamese UTF-8 strings).

5. **Standard Process Library (`std/process/process.ax`)**:
   - Implemented `ProcessError` error enum.
   - Implemented `args() -> Vec<String>` fetching Unicode command-line arguments.
   - Implemented `exit(code: i32)` terminating the current process.
   - Implemented `exe_path() -> Result<String, ProcessError>` retrieving current executable path via `GetModuleFileNameW`.

6. **Test Suite Updates & Additions**:
   - Converted all 5 existing tests in `tests/run/host/io/` (`args.ax`, `env.ax`, `exit7.ax`, `invalid_handle.ax`, `write_stdout_stderr.ax`) from disabled / native-only markers to passing in `interp`, `native`, and `native-O1` modes.
   - Created 4 comprehensive std test suites in `tests/std/io/`:
     - `qa_io_print.ax`: Validates `print`, `println`, `eprint`, `eprintln`, pipe byte exactness, and Vietnamese UTF-8 output (`Xin chào thế giới`).
     - `qa_file_roundtrip.ax`: Validates file create, write, open, read, append, size calculation, text and binary byte-exact roundtrips.
     - `qa_env_process.ax`: Validates `std.env.var`, `std.env.get`, `std.process.args`, `std.process.exe_path`, and Vietnamese Unicode roundtrips.
     - `qa_console.ax`: Validates console write behavior using `python tools/tests/console_check.py`.

## Files changed
- std/env/env.ax
- std/io/io.ax
- std/process/process.ax
- std/sys/windows/io.ax
- std/sys/windows/process.ax
- tests/run/host/io/args.ax
- tests/run/host/io/env.ax
- tests/run/host/io/exit7.ax
- tests/run/host/io/invalid_handle.ax
- tests/run/host/io/write_stdout_stderr.ax
- tests/std/io/qa_console.ax
- tests/std/io/qa_env_process.ax
- tests/std/io/qa_file_roundtrip.ax
- tests/std/io/qa_io_print.ax

## Verification
- **All 5 Host IO Tests Pass across all modes (15/15 PASS)**:
  - `tests/run/host/io/args.ax`: interp PASS, native PASS, native-O1 PASS.
  - `tests/run/host/io/env.ax`: interp PASS, native PASS, native-O1 PASS.
  - `tests/run/host/io/exit7.ax`: interp PASS, native PASS, native-O1 PASS.
  - `tests/run/host/io/invalid_handle.ax`: interp PASS, native PASS, native-O1 PASS.
  - `tests/run/host/io/write_stdout_stderr.ax`: interp PASS, native PASS, native-O1 PASS.
- **All 4 QA Test Suites Pass across all modes (12/12 PASS)**:
  - `tests/std/io/qa_io_print.ax`: interp PASS, native PASS, native-O1 PASS.
  - `tests/std/io/qa_file_roundtrip.ax`: interp PASS, native PASS, native-O1 PASS.
  - `tests/std/io/qa_env_process.ax`: interp PASS, native PASS, native-O1 PASS.
  - `tests/std/io/qa_console.ax`: interp PASS, native PASS, native-O1 PASS.
- **Console Check Verification**:
  - `python tools/tests/console_check.py` passed with status `PASS`.
- **Marker Retirement**:
  - `git grep -rn "native-after: T074" tests` returns 0 occurrences (only future task `T074b` remains).
- **Full Test Suite & Snapshot Verification**:
  - Full suite (`tools/axtest.py --compiler build/axiom0.exe`): zero regressions across all 1486 existing tests.
  - Snapshot verified and refreshed via `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T074`.

STATUS: COMPLETE round=0
