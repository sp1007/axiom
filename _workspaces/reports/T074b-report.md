# T074b — std.fs / path / directories / monotonic clock for hosted Windows

## Summary of Work
Implemented `std.fs`, `std.path`, and `std.time` for hosted Windows (`x86_64-pc-windows-msvc`), backed by native Win32 FFI host functions in `std/sys/windows/fs.ax` and `std/sys/windows/time.ax`.

1. **Win32 Host System Layer (`std/sys/windows/fs.ax` & `std/sys/windows/time.ax`)**:
   - Implemented high-resolution monotonic clock via `QueryPerformanceCounter` and `QueryPerformanceFrequency` (`__ax_host_monotonic_nanos`).
   - Implemented Unicode wide-character path operations using UTF-8 to UTF-16 conversion (`utf8_to_wpath`):
     - `__ax_host_open`, `__ax_host_read`, `__ax_host_write`, `__ax_host_close`, `__ax_host_file_size`.
     - `__ax_host_remove`: supports both file deletion (`DeleteFileW`) and empty directory removal (`RemoveDirectoryW`).
     - `__ax_host_mkdir`: creates directory (`CreateDirectoryW`) returning `-3` on already existing directory.
     - `__ax_host_metadata`: queries file/directory attributes and size (`GetFileAttributesExW`).
     - `__ax_host_dir_open`, `__ax_host_dir_next`, `__ax_host_dir_close`: directory enumeration with 64-slot table over `FindFirstFileW`/`FindNextFileW`/`FindClose`, filtering out `.` and `..` and converting wide-character entry names back to UTF-8.

2. **Standard Path Library (`std/path/path.ax`)**:
   - Normalisation: converts `/` and `\\` to canonical separators, handles `.` and `..` components.
   - Manipulation utilities: `join`, `parent`, `file_name`, `extension`, `has_extension`, `is_absolute`.

3. **Standard Time Library (`std/time/time.ax`)**:
   - `Duration` struct (nanoseconds, non-negative arithmetic, saturating subtract, duration conversions to ms/seconds).
   - `Instant` struct (monotonic timestamps backed by `__ax_host_monotonic_nanos`, `Instant::now()`, `elapsed()`, and difference computation `duration_since`).

4. **Standard File System Library (`std/fs/fs.ax`)**:
   - `FsError` error enum (`NotFound`, `PermissionDenied`, `AlreadyExists`, `InvalidInput`, `Other`).
   - `Metadata` and `FileType` representation (`is_file`, `is_dir`, `is_symlink`, `len`).
   - File manipulation: `create_dir`, `remove_file`, `remove_dir`, `metadata`, `exists`.
   - Streaming binary buffer `ByteBuf` writer and reader.
   - Deterministic sorted directory listing (`read_dir` sorting entries lexicographically).

5. **Test Suite Updates & Conformance Tests**:
   - Updated existing host tests in `tests/run/host/fs/` (`clock.ax`, `dir.ax`, `file_io.ax`, `metadata.ax`), retiring all `native-after: T074b` annotations and passing across `interp`, `native`, and `native-O1` modes.
   - Added comprehensive QA tests in `tests/std/fs/`:
     - `qa_time_clock.ax`: Validates monotonic `Instant`, non-negative diffs, and 50 ms busy loop measuring between 20 and 2000 ms.
     - `qa_path.ax`: Validates path normalisation, join, parent, file_name, extension, and Windows backslash canonicalisation.
     - `qa_binary_file_buf.ax`: Validates binary file writer + reader using `ByteBuf` byte-identical roundtrip and deterministic directory sorting.
     - `qa_unicode_paths.ax`: Validates creating, listing, reading back, and deleting `thư mục/tệp_tiếng_Việt.ax` and emoji name containing U+1F600 (`😀`) with concurrency safety across test runners.

## Files changed
- std/fs/fs.ax
- std/path/path.ax
- std/sys/windows/fs.ax
- std/sys/windows/time.ax
- std/time/time.ax
- tests/run/host/fs/clock.ax
- tests/run/host/fs/dir.ax
- tests/run/host/fs/file_io.ax
- tests/run/host/fs/metadata.ax
- tests/std/fs/qa_binary_file_buf.ax
- tests/std/fs/qa_path.ax
- tests/std/fs/qa_time_clock.ax
- tests/std/fs/qa_unicode_paths.ax

## Verification
- **Host FS Tests (12/12 PASS across all 3 executors)**:
  - `tests/run/host/fs/clock.ax`: interp PASS, native PASS, native-O1 PASS.
  - `tests/run/host/fs/dir.ax`: interp PASS, native PASS, native-O1 PASS.
  - `tests/run/host/fs/file_io.ax`: interp PASS, native PASS, native-O1 PASS.
  - `tests/run/host/fs/metadata.ax`: interp PASS, native PASS, native-O1 PASS.
- **QA Test Suites (12/12 PASS across all 3 executors)**:
  - `tests/std/fs/qa_time_clock.ax`: interp PASS, native PASS, native-O1 PASS.
  - `tests/std/fs/qa_path.ax`: interp PASS, native PASS, native-O1 PASS.
  - `tests/std/fs/qa_binary_file_buf.ax`: interp PASS, native PASS, native-O1 PASS.
  - `tests/std/fs/qa_unicode_paths.ax`: interp PASS, native PASS, native-O1 PASS.
- **Marker Retirement**:
  - `git grep -rn "native-after: T074b" tests` returns 0 hits.
- **Full Test Suite & Compiler Verification**:
  - Full suite (`tools/axtest.py`): 1498/1498 PASS, 0 FAIL, 0 REGRESSIONS.
  - Clean, warning-free build in both `build-snap-T074b` and `build/`.

STATUS: COMPLETE round=0
