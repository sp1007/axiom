# Task T071: Text core: Str, String, UTF-8, char primitives

## Summary
Implemented the core UTF-8 sequence and text model for Axiom adhering to Spec 0089 and tasks/0332:
- Created `std/text/utf8.ax` with `Utf8Error` enum, `DecodeResult` struct, `char.len_utf8(self: char)`, `char.encode_utf8(self: char, dst: *mut u8)`, `decode_char_at`, `is_char_boundary`, `char_count`, and RFC 3629 compliant `validate_utf8`.
- Created `std/text/string.ax` with owned dynamic `String` struct, RAII `impl Drop for String`, dynamic geometric growth (`with_capacity`, `reserve`), `StringBuilder`-style operations (`push_char`, `push_str`, `push_bytes`), `clone`, `clear`, `concat`, `eq`, `cmp`, char-boundary querying (`is_char_boundary`, `char_count`), and char-boundary slicing (`slice`) with robust validation.
- Created `std/text/str.ax` providing `is_empty` and `byte_len` for borrowed `Str` views.
- Created comprehensive test suite in `tests/std/text/`:
  - `qa_text_roundtrip.ax`: Round-tripping `Xin chào thế giới` (22 bytes, 17 Unicode scalar values), full UTF-8 validation, char boundary querying across all positions, slicing on char boundaries ("Xin ", "chào", "thế", "giới"), rejecting non-boundary slices with `Utf8Error.InvalidBoundary`, and rejecting invalid UTF-8 (lone continuation, overlong 2-byte, surrogates, truncated sequences, out-of-range).
  - `qa_char_primitives.ax`: 1/2/3/4-byte `len_utf8` and `encode_utf8`, `decode_char_at` returning `DecodeResult`, `is_char_boundary`, and `char_count`.
  - `qa_string_builder.ax`: `String` construction, geometric growth, `reserve`, `push_char`, `push_str`, `push_bytes`, `clone`, `clear`, `concat`, `eq`, and `cmp`.
  - `qa_utf8_validation.ax`: Comprehensive RFC 3629 validation (valid 1/2/3/4-byte boundaries, overlong rejection, surrogate 0xD800..0xDFFF rejection, out of range > 0x10FFFF rejection, truncated sequences, lone continuation bytes).
- All tests pass 100% across interpreter (`interp`), native (`native`), and optimized native (`native-O1`) modes.
- Full test suite verified passing (1403 tests passed, 0 failures, 18 skipped).

## Files changed
- std/text/str.ax
- std/text/string.ax
- std/text/utf8.ax
- tests/std/text/qa_char_primitives.ax
- tests/std/text/qa_string_builder.ax
- tests/std/text/qa_text_roundtrip.ax
- tests/std/text/qa_utf8_validation.ax

## Verification
- All 4 tests in tests/std/text/ pass across interp, native, and native-O1 (12/12 PASS).
- Round-trip "Xin chào thế giới" verified with 22 bytes and 17 Unicode scalars.
- Full test suite inside build-snap-T071 passes: TOTAL 1421 PASS 1403 FAIL 0 SKIP 18 XFAIL 0.

STATUS: COMPLETE round=0
