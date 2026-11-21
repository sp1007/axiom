# ADR-0044 — T455 integer-model gaps: 128-bit index bounds check, `~` in widening trees, `[N]T` Copy, `AX_TYPE_INDEX_NOT_INT`

Status: accepted (2026-11-21, architect; owner-delegated decision). Type C (semantic change) for §1-§3, Type A for §4.

## Tóm tắt
- Gate T455 (bộ test thuần số nguyên) phát hiện 4 lỗi/khoảng trống thật; engineer đã gỡ test bẫy khỏi bộ sinh thay vì
  nộp test hỏng. Quyết định: bộ T455 được chấp nhận (acceptance của T455 chỉ yêu cầu 12 kiểu, Pattern D, so interp/native;
  các test bị gỡ nằm ngoài danh sách phạm vi), nhưng mỗi lỗi có task sửa trong P12 và test tương ứng được thêm lại
  dưới dạng `// xfail: <task>` (khoảng trống đặc tả có ADR + task mở), task sửa phải gỡ dòng `xfail`.
- §1 Chỉ số 128-bit: `a[i]` với `i: u128/i128 >= 2^64` hiện bị cắt về `usize` rồi mới so sánh nên đọc nhầm phần tử
  (lỗi an toàn bộ nhớ-mức-logic). Spec AXS-INT-053/054 tự quy định thứ tự sai (Cast rồi so sánh). Quyết định: với kiểu chỉ
  số rộng hơn `usize`, so sánh biên (không dấu, trong chính kiểu của chỉ số, độ dài đã nới rộng) trước, rồi mới Cast.
  Task T496 (ưu tiên cao, semantics).
- §2 `~` trong cây mở rộng: `~b8` (u8) trong `let t: i64 = ~b8 + s64` hiện tính trong u8 rồi mới mở rộng, khác với mọi
  toán tử nhị phân và `-` (mở rộng trước). Quyết định: mở rộng toán hạng lên kiểu ngữ cảnh rồi mới `~` (giống C và
  AXS-INT-052 "mọi nút tính trong C"). `~b8` đứng riêng (không trong cây mở rộng) vẫn tính trong u8. Task T499.
- §3 Mảng `[N]T`: `type_is_copy` đã coi mảng của kiểu Copy là Copy, nhưng `mb_operand_from_place` (MIR builder) cứng
  nhắc phát `MIR_OP_MOVE` cho mọi `TY_ARRAY`, nên truyền mảng `[2]u8` hai lần báo `AX_VERIFY_USE_AFTER_MOVE`. Quyết định:
  `[N]T` là Copy khi và chỉ khi `T` là Copy; builder phải theo `type_is_copy`. Task T498.
- §4 `AX_TYPE_INDEX_NOT_INT` (2014) có trong SPEC-40 nhưng chưa có trong `compiler/diag/code.ax`: chỉ là thiếu cài đặt, task T497.
- Revisit: có cho §3 (nếu việc sao chép mảng lớn gây chi phí bất ngờ, thêm lint hoặc `@copy_large` chứ không đổi quy tắc Copy).

## Context
- Source: `_workspaces/reports/T455-report.md` (follow-ups 1-4) and `T455-qa.md`; the original repro files
  `repro_u128_index_alias.ax` and `repro_index_not_int_code.ax` (`tests/run/numeric/mixed_int_matrix`) were removed by their fix
  tasks; their cases now live in `index_trap_u128_alias.ax` / `index_trap_i128_alias.ax` (T496) and `tests/ui/index_not_int/bool.ax` (T497).
- SPEC-40 AXS-INT-053 and AXS-INT-054 §1 say the non-`usize` index is converted with `Cast(IntToInt, i, usize)`
  and then bounds-checked as `idx_usize < len`. For `T` wider than 64 bits the cast truncates, so
  `2^64 + 1` becomes `1`. For 64-bit `T` (`i64`, `u64`, `isize`) the cast is exact on the Windows x64 target; a negative
  `i64` sign-extends or reinterprets to a value `>= 2^63 > len` and traps. For narrower `T` sign/zero extension is exact.
- SPEC-40 AXS-INT-052.1 lists unary `~` as a node of a widening arithmetic tree and AXS-INT-050.2 forbids widening a
  *standalone* `~x`. The compiler (`compiler/types/typeck.ax` `check_unary_in_arith`) types `~` of a narrow unsigned
  leaf in the leaf's own type: `let t: i64 = ~b8 + s64` with `b8: u8 = 255`, `s64 = 1000` yields 1000 instead of 744.
- SPEC-10 AXS-OWN-003 says types implementing `Copy` do not move; it does not say which composite types are Copy.
  `compiler/types/types.ax` `type_is_copy` answers "array is Copy iff element is Copy" (and the same for tuples,
  closures); `compiler/mir/builder.ax` `mb_operand_from_place` ignores that and forces `MIR_OP_MOVE` for `TY_STR` and `TY_ARRAY`.

## Options
- §1: (a) widen `len` to the index type and compare there (unsigned compare after reinterpretation); (b) compare the
  128-bit index to `usize::MAX` first and then truncate; (c) forbid 128-bit index types (`AX_TYPE_INDEX_NOT_INT`).
- §2: (a) promote the operand first (C semantics, uniform with `-` and all binary operators); (b) keep `~` in the leaf type
  and amend AXS-INT-052.1 to remove `~` from the node list.
- §3: (a) `[N]T` Copy iff `T` Copy, builder follows `type_is_copy`; (b) arrays always move, `type_is_copy` changed to match;
  (c) arrays Copy only up to a size limit.

## Decision
1. **§1 = (a).** For an index expression whose integer type `T` has width `W(T) > 64`, the builder emits the bounds check
   in `T`'s own width: reinterpret `idx` as the unsigned type of width `W(T)` (a no-op for unsigned, a bit-cast for signed, so a
   negative value becomes `>= 2^(W-1)` and fails), compare `idx_u < Cast(len, u<W>)`, assert with the existing
   `index out of bounds` message, and only then `Cast(IntToInt, idx, usize)` for `MIR_PROJ_INDEX`. For `W(T) <= 64` the
   existing cast-then-compare lowering is exact and unchanged. The same rule applies at every site that lowers an index or a
   range bound to `usize` (`mb_emit_index_bounds_check`, `mb_emit_range_bounds_check`). SPEC-40 AXS-INT-053/054 are amended accordingly.
   Rejected (b): same result with a second compare; (c): breaks the "any concrete integer type" promise of AXS-INT-053.
2. **§2 = (a).** Inside a widening arithmetic tree of context type `C` every node, including unary `~` and unary `-`,
   is evaluated in `C`: the operand is first converted to `C` (zero-extend unsigned, sign-extend signed) and the operation
   is applied in `C`. `~b8` with `b8: u8 = 255` in an `i64` tree is `-256`, so `~b8 + s64` with `s64 = 1000` is `744`.
   A `~x` that is not inside a widening tree keeps its operand type (AXS-INT-050.2, 052.3). Unary `-` on an unsigned leaf
   stays `AX_TYPE_NEG_UNSIGNED`. SPEC-40 AXS-INT-052 gets rule 4 stating this.
3. **§3 = (a).** `[N]T` is `Copy` iff `T` is `Copy` (so `[N]T` of primitives, `view<...>`, raw pointers, `[N][M]u8` are Copy; an
   array of a non-Copy type moves). A by-value use of a Copy array emits `MIR_OP_COPY`. `str` stays non-Copy. The optimizer is free to
   elide the copy (AXS-OWN-001 note: move/copy need not be a physical copy). SPEC-10 AXS-OWN-003 gets the composite-type clause.
   Rejected (b): `T.from_le_bytes(arr)` would consume its argument, hostile for byte-array APIs; (c): a size threshold makes
   `Copy` depend on `N` and is hard to reason about.
4. **§4.** No semantic decision: implement `AX_TYPE_INDEX_NOT_INT` (2014) per SPEC-40 AXS-INT-053/060 (`bool`, floats, structs,
   tuples as index) in the next free code of `compiler/diag/code.ax`, with an `explain` entry.
5. **T455 completeness.** The acceptance criteria of T455 (12 types, boundary/overflow/wrapping/saturating/checked/overflowing/bit/endian/
   conversion, Pattern D, deep trees, MIR homogeneity, interp-vs-native) are met without the removed tests, which concern
   index lowering (AXS-INT-053) and unary `~`, array passing and diagnostic `2014`, not listed in the task scope. The suite is accepted
   with these follow-ups: the post-decision behaviour is committed as `// xfail: <task>` tests
   (`index_trap_u128_alias`, `index_trap_i128_alias`, `tilde_widening`, `array_copy`) which each fix task must un-xfail; `2014` has a helper repro that its task
   converts into a `ui` test.

## Consequences
- New tasks (P12, all depend on T455 so the xfail tests exist): **T496** (128-bit index bounds check, semantics, `compiler/mir/builder.ax`),
  **T497** (`AX_TYPE_INDEX_NOT_INT`, semantics), **T498** (array Copy in the MIR builder, semantics), **T499** (`~` promote-first in `typeck`).
- Specs amended: SPEC-40 AXS-INT-052 (rule 4), AXS-INT-053, AXS-INT-054; SPEC-10 AXS-OWN-003.
- Tests affected: `tests/run/numeric/mixed_int_matrix/gen_matrix.py` (xfail variants; regenerated), T496-T499 remove the xfail lines.
  Existing tests that rely on the old behaviour: none known (T455 never pinned `~` over an unsigned leaf and passed arrays as `view<[N]T>`);
  each fix task runs `tests/run/numeric`, `tests/conformance/p12`, `tests/conformance/vs0` and the selfhost typeck/mir groups.
- Compiler self-build risk: the compiler's own sources use `~` and arrays; T499 and T498 must keep the fixed point (stage 2 == stage 3) green.

## Sources
- `spec/SPEC-40-integers.md` AXS-INT-050..054, 060; `spec/SPEC-10-ownership.md` AXS-OWN-001..003;
  `spec/SPEC-03-core-semantics.md` AXS-SEM-042; `_workspaces/reports/T455-report.md`; tasks/0327, tasks/0334, tasks/0431;
  `compiler/mir/builder.ax` (`mb_operand_from_place`, `mb_emit_index_bounds_check`), `compiler/types/types.ax` (`type_is_copy`),
  `compiler/types/typeck.ax` (`check_unary_in_arith`).
