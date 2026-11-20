# T444a report — mixed-size tuple-variant payload offsets

## Root cause
`compiler/types/layout.ax` had two independent walks over an enum variant's payload:
- `type_enum_field_offset` (used by construction in the interpreter and LIR lowering, and by
  pattern/field projection in `interp/frame.ax` and `lir/builder.ax`) placed the sorted payload
  fields **after the 4-byte discriminant** (base offset 4).
- `type_size` for `TY_ENUM` placed the same sorted fields **from offset 0** and then added 4.

The two disagree whenever the first sorted field needs alignment > 4: for `Pair(u8, u64)` the
offsets are u64@8, u8@16 (end 17) but `type_size` returned `align8(4 + 9) = 16`. The u8 was written
past the end of the object, and every whole-value copy (`_2 = copy _1`, argument passing, match
scrutinee temporaries) dropped it — so `Pair(a, _)` read `a = 0`, in the oracle and natively.
The MIR builder already emits `(x as variant#k).i` projections with declared field indices; it was
not at fault.

## Fix
One placement routine, `place_variant_fields` (layout.ax), is now the single source of truth: tag
at [0, 4), payload fields in `sort_fields` order, each aligned, returning both the requested field
offset and the payload end. `type_enum_field_offset` returns its `field_offset`; `type_size` for an
enum is `align_up(max over variants of end, type_align(enum))`. No other ordering/base rule remains;
interp, MIR builder and LIR builder keep calling `type_enum_field_offset` unchanged.

Effect: `size_of<enum { Pair(u8, u64), .. }>` is 24 (was 16). Enums whose old size already covered
the payload (e.g. `A(u8, u16)` = 8, `Single(u32)` = 8) are unchanged. `bootstrap/axiom0` has the
same latent bug but is frozen and out of scope (stage 1 output is not part of the fixed point).

## Tests
`tests/run/enum_payload_mixed/` (interp, native, native-O1; exact `// stdout:`):
- `two_field_orders.ax` — 10 orders of u8/u16/u32/u64 pairs, each field bound alone.
- `three_field_orders.ax` — all 6 orders of (u8,u16,u64) and of (u8,u32,u64), each field alone and
  all three together.
- `pointer_and_struct.ax` — raw pointer and struct (u16,u64) payload fields mixed with u8.
- `nested_pointer_iflet_size.ax` — enum inside a struct, enum behind a raw pointer (read/overwrite),
  `if let`, `size_of`.

## Verification
- `build-snap-T444a`: stage-3 bootstrap `FIXED-POINT (O1) OK`, `STAGE0-GUARD OK`.
- Own tests (`tests/run/enum_payload_mixed/*`, `--no-cache -j 2`): 12/12 PASS (`WEAK-NATIVE 0`) on
  patched `build/axiomc2.exe`; 0/12 PASS (12 FAIL) on HEAD cache compiler.
- `tests/selfhost/types/qa_types_layout.ax.in` updated (`16u32` -> `24u32` for `enum { V0, V1(u8, u64) }`).
- `taskgate.py --task T444a`: exit 0 (`TOTAL 183 PASS 182 FAIL 0 SKIP 1 XFAIL 0`, `BASELINE OK`,
  `WEAK-NATIVE 0` in own/changed tests, `archcheck` 0 violations).
- `taskctl.py changes T444a`: exit 0, 0 `REFUSED`.

## Files changed
- compiler/types/layout.ax
- tests/run/enum_payload_mixed/two_field_orders.ax
- tests/run/enum_payload_mixed/three_field_orders.ax
- tests/run/enum_payload_mixed/pointer_and_struct.ax
- tests/run/enum_payload_mixed/nested_pointer_iflet_size.ax
- tests/selfhost/types/qa_types_layout.ax.in
- _workspaces/reports/T444a-report.md

## Status
STATUS: COMPLETE round=0
