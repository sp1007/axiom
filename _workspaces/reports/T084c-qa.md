# T084c QA Report — Port x64 Instruction Selection and Frame Lowering to Axiom

## Round 0

### Scope & Audit Check

- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T084c`: 0 `REFUSED` lines.
  - Changed files in scope:
    - `compiler/target/x64/frame.ax`
    - `compiler/target/x64/isel.ax`
    - `compiler/target/x64/mod.ax`
    - `tests/selfhost/isel/qa_frame_layout_and_verify.ax`
    - `tests/selfhost/isel/qa_isel_diff_golden.ax`
    - `tests/selfhost/isel/qa_isel_instructions_and_abi.ax`
  - QA test added:
    - `tests/selfhost/isel/qa_isel_frame_seam_and_edge_cases.ax`

### Commands Executed (in `build-snap-T084c`)

- `python tools/archcheck.py --root .` -> `188 files scanned, 0 violations`
- `ctest --test-dir build --output-on-failure` -> `18/18 PASS`
- `python tools/axtest.py --compiler build/axiom0.exe --filter selfhost/encode` -> `9/9 PASS`
- `python tools/axtest.py --compiler build/axiom0.exe --filter selfhost/abi` -> `9/9 PASS`
- `python tools/axtest.py --compiler build/axiom0.exe --filter selfhost/lir` -> `12/12 PASS`
- `python tools/axtest.py --compiler build/axiom0.exe --filter mc/` -> `9/9 PASS`
- `python tools/axtest.py --compiler build/axiom0.exe --filter encode/` -> `10/10 PASS`
- `python tools/axtest.py --compiler build/axiom0.exe --filter selfhost/isel` -> `9 PASS, 3 FAIL` (`tests/selfhost/isel/qa_isel_frame_seam_and_edge_cases.ax` fails in `[interp]`, `[native]`, and `[native-O1]`)

### Findings

1. **`x64_mi_add_string` corrupts the Machine IR string table when growing past 16 entries (`compiler/target/x64/isel.ax:582`)**
   - **Location**: [`compiler/target/x64/isel.ax:573-586`](file:///d:/projects/compiler/new%20lang/compiler/target/x64/isel.ax#L573-L586) (`x64_mi_add_string`)
   - **Root Cause**: When `body.string_count >= body.string_cap` and `body.strings` is reallocated from capacity `16` to `32`, line 582 copies existing entries via:
     ```axiom
     ptr_copy_nonoverlapping(body.strings as *const X64MIStr, new_strings, body.string_count);
     ```
     without an explicit type argument `<X64MIStr>` (or `<u8>` with byte count `lir_mul_usize(body.string_count, size_of<X64MIStr>())`). In `axiom0` (`bootstrap/axiom0/src/mir/build/builder.c:2206-2215`), calling `@intrinsic fn ptr_copy_nonoverlapping<T>` without explicit `<T>` leaves `substs->args[0]` as an unresolved `TY_INFER` type variable whose `ax_type_size` is `0` (clamped to `1` byte in `interp.c:1402` and `lir/lower.c:1019`). Consequently, when the 17th string constant (`LIR_INST_CONST_STR`) is added, `ptr_copy_nonoverlapping` copies only `16 * 1 = 16` bytes instead of `16 * 24 = 384` bytes, zeroing `strings[0].sym_id` (`0` instead of `100000`) and wiping `strings[1..15]` (`bytes = NULL`, `len = 0`, `sym_id = 0`).
   - **Expected vs Actual**: After lowering a `LirBody` with 20 `LIR_INST_CONST_STR` instructions, `strings[i]` for `i in 0..20` must preserve its `bytes`, `len`, and `sym_id = 100000 + i`. Instead, `strings[0].sym_id` becomes `0` and `strings[1..15]` are zeroed (`test_string_table_growth` returns exit code `102`).
   - **Fix**: Copy bytes explicitly with `ptr_copy_nonoverlapping<u8>(body.strings as *const u8, new_strings as *mut u8, lir_mul_usize(body.string_count, size_of<X64MIStr>()))` (or pass explicit `<X64MIStr>`).

2. **`x64_mi_print_op` misformats negative displacement-only `X64_OP_MEM` operands in `--interp` (`compiler/target/x64/isel.ax:877`)**
   - **Location**: [`compiler/target/x64/isel.ax:875-878`](file:///d:/projects/compiler/new%20lang/compiler/target/x64/isel.ax#L875-L878) (`x64_mi_print_op`)
   - **Root Cause**: For a displacement-only memory operand (`base == REG_NONE && index == REG_NONE && !is_rip`), line 877 writes:
     ```axiom
     push_i64_dec(mut_view(*out), op.mem.disp as i64);
     ```
     In `axiom0`'s MIR interpreter (`bootstrap/axiom0/src/interp/interp.c:1212-1214`), `AX_MIR_RVALUE_CAST` on a projected field place (`op.mem.disp`) looks up `frame.body->locals[loc.v].ty` (the outer struct `X64Op` rather than the `i32` field), treating `src_signed = false; src_bits = 64` and zero-extending `-16` (`0xFFFFFFF0`) to `4294967280`.
   - **Expected vs Actual**: `x64_mi_print_op(x64_op_mem(REG_NONE, REG_NONE, 1, -16, false), ...)` must format `"[-16]"` (matching `fprintf(out, "%d", op.mem.disp)` in `bootstrap/axiom0/src/target/x64/mir/mi.c:45`). In `[interp]`, it formats `"[4294967280]"` (`test_printer_and_overflow_edges` returns exit code `403`).
   - **Fix**: Bind the field to a scalar `i32` local before casting (`let disp_i32: i32 = op.mem.disp; push_i64_dec(mut_view(*out), disp_i32 as i64);`), or format via `push_i32_abs` with a leading `'-'` when `op.mem.disp < 0`.

3. **`push_u64_dec` / `push_i64_dec` panics with `arithmetic overflow` in `[native]` / `[native-O1]` when formatting `INT64_MIN` (`compiler/target/x64/isel.ax:758-760`)**
   - **Location**: [`compiler/target/x64/isel.ax:750-779`](file:///d:/projects/compiler/new%20lang/compiler/target/x64/isel.ax#L750-L779) (`push_u64_dec`, `push_i64_dec`)
   - **Root Cause**: `x64_isel` emits `x64_op_imm((0x8000000000000000u64) as i64)` (`INT64_MIN`) for 64-bit `LIR_INST_SDIV_OVERFLOW` and `LIR_INST_SREM_OVERFLOW` (`compiler/target/x64/isel.ax:1263,1279`). When `x64_mi_print_op` / `x64_mi_print` formats this immediate, `push_i64_dec` computes `mag = 9223372036854775808u64` (`0x8000000000000000u64`) and passes it to `push_u64_dec`. However, in `axiom0` native codegen (`bootstrap/axiom0/src/target/x64/isel/isel.c:336-349`, as well as `compiler/target/x64/isel.ax:1291-1305`), `u64` `/` and `%` lower to signed 64-bit `IDIV` (`SAR RDX, 63; IDIV`). When `v` has bit 63 set (`0x8000000000000000u64`), `v % 10u64` yields signed remainder `-8` (`248u8` when cast to `u8`), and line 759 (`digits[n] = 48u8 + rem`) panics with `panic: arithmetic overflow` (`48u8 + 248u8 = 296 > 255`).
   - **Expected vs Actual**: `x64_mi_print_op(x64_op_imm((0x8000000000000000u64) as i64), ...)` must format `"-9223372036854775808"` in `[interp]`, `[native]`, and `[native-O1]`. In `[native]` and `[native-O1]`, it aborts with `exit code 101; stderr: panic: arithmetic overflow`.
   - **Fix**: In `push_u64_dec`, avoid `u64` division/modulo when bit 63 is set — for example, for any `v: u64`, `let half = v >> 1u64; let q = half / 5u64; let rem = ((half % 5u64) * 2u64 + (v & 1u64)) as u8;` (since `half` always has bit 63 cleared, signed `IDIV` and unsigned division are identical on `half`).

### Reproduction Command

```powershell
python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T084c
python build-snap-T084c/tools/axtest.py --compiler build-snap-T084c/build/axiom0.exe --root build-snap-T084c --filter selfhost/isel/qa_isel_frame_seam_and_edge_cases.ax
```

## Files changed

- tests/selfhost/isel/qa_isel_frame_seam_and_edge_cases.ax

## Round 1

### Verification of Round 0 Fixes

1. **Finding 1 (`x64_mi_add_string` string table growth past 16 entries — [`compiler/target/x64/isel.ax:580-585`](file:///d:/projects/compiler/new%20lang/compiler/target/x64/isel.ax#L580-L585))**:
   - **Resolved**: `x64_mi_add_string` now computes `let copy_bytes = lir_mul_usize(body.string_count, size_of<X64MIStr>());` and calls `ptr_copy_nonoverlapping<u8>(body.strings as *const u8, new_strings as *mut u8, copy_bytes);`. `test_string_table_growth` (20 string literals across capacity growth `16 -> 32`) passes in `[interp]`, `[native]`, and `[native-O1]`.
2. **Finding 2 (`x64_mi_print_op` negative displacement-only `X64_OP_MEM` in `--interp` — [`compiler/target/x64/isel.ax:854-891`](file:///d:/projects/compiler/new%20lang/compiler/target/x64/isel.ax#L854-L891))**:
   - **Resolved**: `x64_mi_print_op` binds `let disp_i32: i32 = op.mem.disp;` (and other `X64Op` fields) to scalar locals before casting to `i64`. `x64_mi_print_op(x64_op_mem(REG_NONE, REG_NONE, 1, -16, false), ...)` formats `"[-16]"` identically across `[interp]`, `[native]`, and `[native-O1]`.
3. **Finding 3 (`push_u64_dec` / `push_i64_dec` `INT64_MIN` formatting in `[native]` / `[native-O1]` — [`compiler/target/x64/isel.ax:758-785`](file:///d:/projects/compiler/new%20lang/compiler/target/x64/isel.ax#L758-L785))**:
   - **Resolved**: `push_u64_dec` clears bit 63 via `let half = v >> 1u64; let r5 = (half % 5u64) as u8; let odd = (v & 1u64) as u8; let rem = r5 + r5 + odd; v = half / 5u64;` before division/modulo. `x64_mi_print_op(x64_op_imm((0x8000000000000000u64) as i64), ...)` formats `"-9223372036854775808"` without overflow across `[interp]`, `[native]`, and `[native-O1]`.

### Scope & Audit Check

- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T084c`: 0 `REFUSED` lines (9 files staged).

### Commands Executed (in `build-snap-T084c`)

- `python tools/archcheck.py --root .` -> `188 files scanned, 0 violations`
- `ctest --test-dir build --output-on-failure` -> `18/18 PASS`
- `python tools/axtest.py --compiler build/axiom0.exe --filter selfhost/isel` -> `12/12 PASS` (`[interp]`, `[native]`, `[native-O1]`, including `qa_isel_frame_seam_and_edge_cases.ax`)
- `python tools/axtest.py --compiler build/axiom0.exe --filter selfhost/encode` -> `9/9 PASS`
- `python tools/axtest.py --compiler build/axiom0.exe --filter selfhost/abi` -> `9/9 PASS`
- `python tools/axtest.py --compiler build/axiom0.exe --filter selfhost/lir` -> `21/21 PASS`
- `python tools/axtest.py --compiler build/axiom0.exe --filter mc/` -> `9/9 PASS`
- `python tools/axtest.py --compiler build/axiom0.exe --filter encode/` -> `10/10 PASS`

VERDICT: PASS round=1
