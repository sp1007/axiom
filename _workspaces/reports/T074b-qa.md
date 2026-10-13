# QA Report: T074b

## Round 0
- 4/4 host FS tests (clock, dir, file_io, metadata) pass across interp, native, and native-O1 modes (12/12 PASS).
- 4/4 std.fs test targets (qa_binary_file_buf, qa_path, qa_time_clock, qa_unicode_paths) pass across interp, native, and native-O1 modes (12/12 PASS).
- Unicode paths tested: create, list, read back, and delete "thư mục/tệp_tiếng_Việt.ax" and emoji file names.
- Binary streaming with ByteBuf round-trips byte-identical.
- Directory listing is lexicographically sorted and deterministic.
- Instant monotonic clock measures non-negative nanoseconds; 50 ms loop within expected bounds.
- native-after: T074b retired (0 hits in tests/).
- archcheck: 188 files scanned, 0 violations.
- taskctl changes: 0 refused files.

VERDICT: PASS round=0
