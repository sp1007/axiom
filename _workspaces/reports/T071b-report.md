# T071b report: ByteBuf, integer formatting and parsing, format helpers

## Summary
Completed the byte-level and integer formatting/parsing half of the self-host std subset (T071b):
1. **`ByteBuf` (`std/bytes/byte_buf.ax`)**:
   - Implemented growable byte buffer with little-endian primitive integer writers: `put_u8`, `put_u16`, `put_u32`, `put_u64`, `put_i8`, `put_i16`, `put_i32`, `put_i64`, `put_usize`, `put_isize`, and `put_bytes(bytes: view<[u8]>)`.
   - Implemented in-place relocation/header patching: `patch_u32_at`, `patch_u8_at`, `patch_u16_at`, `patch_u64_at` with strict bounds checking returning `Result<(), ByteBufError>`.
   - Implemented alignment padding: `pad_to(align, pad_byte)` and `align_to(align)`.
   - Implemented buffer management and byte-slice views: `len`, `capacity`, `is_empty`, `clear`, `reserve`, `get`, `set`, `clone`, `slice`, and `eq`.

2. **Integer Formatting (`std/text/fmt/int.ax`)**:
   - Implemented formatting into string buffers (`format_*_into`) for all 10 integer widths (`u8`, `u16`, `u32`, `u64`, `usize`, `i8`, `i16`, `i32`, `i64`, `isize`).
   - Supports arbitrary radix (2 to 36), decimal, hex, and binary formatting with custom field width and zero/space padding.
   - Accurately formats MIN and MAX edge values for every width. Handled Axiom0 signed division constraints by implementing a two-step unsigned division algorithm (`u64_div_u32`) for large values with bit 63 set.
   - Handled Axiom0 integer widening cast masking across all signed/unsigned sub-widths.

3. **Integer Parsing (`std/text/fmt/int.ax`)**:
   - Implemented parsing (`parse_*_radix` and `parse_*`) for all 10 integer widths taking byte slice views (`view<[u8]>`).
   - Detailed error reporting with `ParseIntError`: `Empty`, `InvalidDigit`, and `Overflow`.
   - Handles prefixes: `0x`/`0X` (hex), `0b`/`0B` (binary), `0o`/`0O` (octal), and signs `+`/`-`.
   - Complete overflow detection across arbitrary radices (2 to 36) without relying on signed division.

4. **Format Helpers (`std/text/fmt/format.ax`) & Hex Dump (`std/text/fmt/hex_dump.ax`)**:
   - Implemented `format_into_bool`, `format_into_char`, `format_into_bytes`, `format_into_int`, `format_into_uint`, `format_into_hex`, `format_into_bin`, `repeat_char_into`, `pad_left_into`, and `pad_right_into`.
   - Implemented canonical `write_hex_dump` and `hex_dump` output matching standard hexdump format (8-byte hex offset, two 8-byte hex columns with middle separator, and ASCII representation).

## Files changed
- `std/bytes/byte_buf.ax`
- `std/text/fmt/int.ax`
- `std/text/fmt/format.ax`
- `std/text/fmt/hex_dump.ax`
- `tests/std/bytes/qa_byte_buf.ax`
- `tests/std/fmt/qa_int_format.ax`
- `tests/std/fmt/qa_int_parse.ax`
- `tests/std/fmt/qa_fmt_helpers.ax`
- `tests/std/fmt/qa_hex_dump.ax`

## Tests
All tests pass cleanly in all 3 modes (`interp`, `native`, and `native-O1`):
```
python tools/axtest.py --compiler build/axiom0.exe --filter std/fmt/
TOTAL 12 PASS 12 FAIL 0 SKIP 0 XFAIL 0

python tools/axtest.py --compiler build/axiom0.exe --filter std/bytes/
TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0
```
- `tests/std/bytes/qa_byte_buf.ax`: PASS (3/3)
- `tests/std/fmt/qa_int_format.ax`: PASS (3/3)
- `tests/std/fmt/qa_int_parse.ax`: PASS (3/3)
- `tests/std/fmt/qa_fmt_helpers.ax`: PASS (3/3)
- `tests/std/fmt/qa_hex_dump.ax`: PASS (3/3)

## Spec deviations
None. All implementations conform to the canonical Axiom language specification and self-host std subset.

## Follow-ups
None.

STATUS: COMPLETE round=1
