# Task T071c: UTF-8 ↔ UTF-16 conversion (for Windows W APIs)

## Summary
Implemented text conversion at the OS boundary (UTF-8 ↔ UTF-16) for Windows W APIs per Spec 0089 and task T071c:
- Created `std/text/utf16/utf16.ax`:
  - Constants: `REPLACEMENT_CHARACTER` ('\u{FFFD}'), `REPLACEMENT_CODE_UNIT` (0xFFFDu16).
  - Error enum: `Utf16Error` (`InvalidUtf8`, `LoneSurrogate`, `InvalidScalarValue`, `InvalidCodeUnit`).
  - Surrogate helpers: `is_high_surrogate`, `is_low_surrogate`, `is_surrogate`, `surrogate_high`, `surrogate_low`, `decode_surrogate_pair`.
  - UTF-8 and UTF-16 decoders/encoders:
    - `decode_utf8_char`, `decode_utf8_char_lossy`, `utf8_char_len`
    - `decode_utf16_char`, `decode_utf16_char_lossy`, `encode_utf16_char`
    - `encode_utf8_char`
  - Dynamic buffer helpers:
    - `WideString`: dynamic UTF-16 buffer with geometric growth, `with_capacity`, `reserve`, `as_ptr`, `as_slice`, `push`, `push_char`, `into_slice`, and `free`. Maintains the Windows NUL terminator invariant `*(ws.as_ptr() + ws.len) == 0u16` after every operation.
    - `String`: dynamic byte buffer helper for conversion results with `with_capacity`, `reserve`, `as_str`, `as_slice`, `push_byte`, `push_char`, `free`.
  - Conversion functions:
    - `utf8_to_utf16`: strict conversion from UTF-8 string to `WideString` (rejects invalid UTF-8 with `Utf16Error.InvalidUtf8`).
    - `utf8_to_utf16_lossy`: lossy conversion replacing invalid UTF-8 bytes with `0xFFFD`.
    - `utf16_to_utf8`: strict conversion from UTF-16 slice to `String` (rejects lone surrogates with `Utf16Error.LoneSurrogate`).
    - `utf16_to_utf8_lossy`: lossy conversion replacing lone surrogates with `\u{FFFD}`.
    - `to_wide_null`, `to_wide_null_lossy`: conversions directly producing NUL-terminated wide strings for Windows API calls (`LPCWSTR`).
    - `utf16_null_len`: measures length of a NUL-terminated wide string pointer (`*const u16`).
    - `utf16_ptr_to_utf8`, `utf16_ptr_to_utf8_lossy`: decodes wide string pointer + length.
    - `utf16_null_to_utf8`, `utf16_null_to_utf8_lossy`: decodes NUL-terminated wide string pointer to UTF-8 `String`.
- Created comprehensive test suite in `tests/std/utf16/`:
  - `qa_utf16_roundtrip.ax`: Round-trip testing of ASCII strings, `Xin chào thế giới` (Vietnamese diacritics), and U+1F600 (surrogate pair `0xD83D`, `0xDE00`), in both strict and lossy modes.
  - `qa_utf16_surrogates.ax`: Strict mode rejection of lone high surrogate (`0xD800`) and lone low surrogate (`0xDC00`), lossy mode replacement with `U+FFFD`, surrogate boundary handling (`U+10000`, `U+10FFFF`), and invalid UTF-8 strict rejection and lossy substitution.
  - `qa_utf16_wide_buffer.ax`: `WideString` construction, dynamic growth, `reserve`, `push_char` with BMP and supplementary code points, NUL-termination invariant, `to_wide_null`, and `utf16_null_to_utf8`.
- All tests pass 100% across interpreter (`interp`), native (`native`), and optimized native (`native-O1`) modes.

## Files changed
- std/text/utf16/utf16.ax
- tests/std/utf16/qa_utf16_roundtrip.ax
- tests/std/utf16/qa_utf16_surrogates.ax
- tests/std/utf16/qa_utf16_wide_buffer.ax

## Verification
- All 3 tests in tests/std/utf16/ pass across interp, native, and native-O1 (9/9 PASS).
- Round-trip "Xin chào thế giới" and U+1F600 verified across all execution modes.
- Lone surrogate strict error and lossy U+FFFD substitution verified.
- WideString buffer NUL-termination invariant verified.
- Isolated snapshot build-snap-T071c verified.

STATUS: COMPLETE round=0
