# T134 — AX0-FIX-01: native lowering of wrapping/bit intrinsics, assert and panic

## Tóm tắt
- Thiết lập bảng intrinsic duy nhất (`bootstrap/axiom0/src/mir/build/intrinsics.h`, `intrinsics.c`) gồm 4 nhóm hạ tầng (`AX_INTR_BUILTIN`, `AX_INTR_HOST`, `AX_INTR_MIR_OP`, `AX_INTR_MIR_TERM`), quy tắc chữ ký `AxIntrinsicSig` và mã kiểu builtin `AX_TY_BUILTIN_*`, được tra cứu thống nhất tại `pipeline.c`, `typeck.c`, `mir/build/builder.c`, `lir/lower.c` và `interp/interp.c`.
- Hạ tầng MIR builder (`builder.c`) hạ trực tiếp `wrapping_add/sub/mul/neg_<w>`, `rotate_left/right_<w>`, `leading_zeros_<w>`, `trailing_zeros_<w>`, `count_ones_<w>` (đủ 10 độ rộng `i8..i64`, `u8..u64`, `isize`, `usize`), hạ `assert(c)` thành `AX_MIR_TERM_ASSERT` và `panic(...)` / `unreachable()` thành đường abort mã thoát 101; bỏ hoàn toàn việc biên dịch thân hàm giả (`{}` / `{ 0 }`) cho mọi hàm `@intrinsic` hợp lệ và báo lỗi `AX_TYPE_UNKNOWN_INTRINSIC` nếu tên hoặc chữ ký không khớp bảng.
- Phát hiện và sửa lỗi hạ tầng LIR (`bootstrap/axiom0/src/lir/lower.c`) khi đích của lệnh gọi hàm (`AX_MIR_TERM_CALL`) có phép chiếu trường (`b.curr_bb = mb_new_bb(...)`) từng bị lộ ra nhờ `assert` thật trong `qa_interp_exec_a.ax` và `qa_interp_exec_b.ax`.
- Kiểm chứng độc lập với bảng vector Python (`tests/unit/kernel/hash_vectors.txt`, `gen_ops_table.py`, `gen_hash_native.py`), gỡ giới hạn `modes: interp` trên `tests/run/numeric/intrinsic_ops.ax` và `tests/std/core/qa_hash_vectors.ax`, vượt qua toàn bộ 1973/1973 bài kiểm thử trong `build-snap-T134`.

## Design & Lowering Choices (TYPE A)
1. **Single Intrinsic Table (`intrinsics.h`, `intrinsics.c`):**
   - `AxIntrinsicClass`: `AX_INTR_BUILTIN` (15 typeck-retyped builtins: `print`, `print_int`, `size_of`, `align_of`, `null`, `null_mut`, `is_null`, `address_of`, `address_of_mut`, `ptr_add`, `ptr_sub`, `ptr_copy`, `ptr_copy_nonoverlapping`, `ptr_write_bytes`, `needs_drop`, `drop_in_place`, `forget`), `AX_INTR_HOST` (15 `__ax_host_*` runtime hooks), `AX_INTR_MIR_OP` (80 per-width rows = 8 operations × 10 integer widths), and `AX_INTR_MIR_TERM` (`assert`, `panic`, `panic_str`, `panic_fmt`, `unreachable`).
   - `driver/pipeline.c` (`validate_intrinsic_items`) validates every `@intrinsic` function against the table (emitting `AX_TYPE_UNKNOWN_INTRINSIC` on unknown name or mismatched parameter/return/generic signature) and stores `((uint64_t)ref.desc->builtin_ty << 32) | (uint64_t)ax_intrinsic_encode(&ref)` in the `@intrinsic` attribute's `annotation` field.
   - `types/typeck.c` reads the `AX_TY_BUILTIN_*` tag from the high 32 bits of the `@intrinsic` attribute annotation (replacing the 17-way hardcoded `ax_sv_eq_cstr` chain) and records the encoded `AxIntrinsicRef` on call expressions in `Thir` (`ax_thir_set_intrinsic_callee`).
   - Both `driver/pipeline.c` (`build_mir_for_item`) and `mir/build/builder.c` (`ax_mir_build`) skip building MIR for any function with a valid `@intrinsic` annotation so no placeholder intrinsic body is ever compiled or executed.
2. **MIR Operations & Baseline x86-64 Bit-Intrinsic Expansions (TYPE A):**
   - Added `AX_MIR_BINOP_WRAPPING_ADD`, `AX_MIR_BINOP_WRAPPING_SUB`, and `AX_MIR_BINOP_WRAPPING_MUL` across `mir/mir.h`, `mir/print.c`, `mir/parse.c`, `opt/opt.c` (width-masked two's-complement constant folding), `lir/lower.c` (direct lowering to `AX_LIR_INST_ADD/SUB/MUL` without overflow checks), and `interp/interp.c` (modular two's-complement arithmetic truncated/sign-extended to target width).
   - `wrapping_neg_<w>(a)` lowers in `mir/build/builder.c` to `wrapping_sub(0, a)`.
   - Bit intrinsics (`rotate_left_<w>`, `rotate_right_<w>`, `count_ones_<w>`, `leading_zeros_<w>`, `trailing_zeros_<w>`) expand in `mir/build/builder.c` into MIR statements over the matching unsigned carrier type `U<w>` (`u8..u64`), avoiding any dependency on optional x86-64 CPUID features (`POPCNT`/`LZCNT`/`TZCNT`) and ensuring identical execution across the MIR interpreter, `-O0`, and `-O1`:
     - `rotate_left_<w>(a, b)` / `rotate_right_<w>(a, b)`: masks `s = (b as U<w>) & (W - 1)`; branches on `s == 0` so `(u << s) | (u >> (W - s))` never executes a shift by `W` (which would trap in checked MIR shift).
     - `count_ones_<w>(a)`: SWAR parallel bit-count in `U<w>` returning `u32`.
     - `leading_zeros_<w>(a)` / `trailing_zeros_<w>(a)`: binary-search tree over bit halves in `U<w>` returning `W as u32` when `a == 0` and the exact `u32` count otherwise.
3. **Assert & Panic Lowering:**
   - `assert(c)` lowers to `AX_MIR_TERM_ASSERT` (`expected = true`, `"assertion failed"`).
   - `panic(...)`, `panic_str(...)`, `panic_fmt(...)`, and `unreachable()` evaluate their arguments for side effects and emit an unconditional `AX_MIR_TERM_ASSERT` (`cond = false, expected = true`, `"explicit panic"` or `"entered unreachable code"`), setting `b->is_diverged = true` so trailing statements in the block are not emitted and execution aborts with exit code 101 in both modes.
4. **LIR Call Destination Projection Fix (`bootstrap/axiom0/src/lir/lower.c`):**
   - In `AX_MIR_TERM_CALL`, `lower.c` previously allocated the return vreg `res` with `mir->locals[mbb->terminator.call.destination.local.v].ty` (the base local's type) instead of the projected destination place's type (`dst_ty` from `lower_place_addr`). When a call wrote directly into a struct field projection (such as `b.curr_bb = mb_new_bb(...)` where `b` is a 200-byte `MirBuilder` and `curr_bb` is a 4-byte `MirBbId` at offset 184), `emit_store` copied 200 bytes into `&b.curr_bb`, corrupting `b.is_diverged` at offset 196. Using `dst_ty` fixes the stack corruption.
5. **Interpreter Return & By-Value Argument Buffer Sizing Fix (`bootstrap/axiom0/src/interp/host.h`, `bootstrap/axiom0/src/interp/interp.c` — Round 1):**
   - `AxInterpValue` in `host.h` was previously 64 bytes (`uint64_t vals[8]`), and `eval_call` truncated callee return copies to `sizeof(AxInterpValue)` while `exec_mir_body` at `AX_MIR_TERM_CALL` copied `ax_type_size(dest_ty, ...)` bytes out of a 64-byte stack `AxInterpValue ret_val`, reading past `ret_val` on the C stack when returning structs larger than 64 bytes (such as 80-byte `U32Set` / `AxRawSet` in `qa_hash_set.ax` and 88-byte `U32Map` / `AxRawMap` in `qa_hash_map_growth.ax` and `qa_hash_map_order.ax`).
   - Widened `AxInterpValue` to `uint64_t vals[32]` (256 bytes) with explicit capacity assertions on by-value arguments and closure captures, and updated `eval_call` / `exec_mir_body` to allocate and pass an explicit `ret_buf` of size `max(dest_sz, sizeof(AxInterpValue))` so return values of any size are copied without truncation or out-of-bounds stack reads.

## Regenerated / Updated Goldens
- `tests/mir/intrinsics/assert_panic.mir`, `tests/mir/intrinsics/rotate_u8.mir`, `tests/mir/intrinsics/wrapping_ops.mir`: new MIR goldens verifying that `@intrinsic` declarations emit no MIR body and calls lower to `wrapping_add/sub/mul`, guarded shift-or rotate blocks, and `assert(...)` terminators.
- `tests/mir/wrapping_roundtrip.mir`: new MIR print/parse roundtrip golden for `wrapping_add`, `wrapping_sub`, and `wrapping_mul`.
- `tests/lir/wrapping_add.lir`, `tests/lir/wrapping_mul.lir`, `tests/lir/wrapping_sub.lir`: new MIR-to-LIR lowering goldens for `wrapping_add`, `wrapping_mul`, and `wrapping_sub`.
- `tests/run/intrinsics/ops_table.ax`: generated by `tests/run/intrinsics/gen_ops_table.py` (verified by `ops_table_current.test`) from Python reference arithmetic across all 9 operations × 10 widths.
- `tests/selfhost/kernel/hash_native.ax`: generated by `tests/selfhost/kernel/gen_hash_native.py` (verified by `hash_native_current.test`), embedding `compiler/kernel/hash.ax` verbatim and checking all 10 vectors of `tests/unit/kernel/hash_vectors.txt` plus `"Xin chào thế giới"` UTF-8 bytes in `modes: interp native`. Replaced `tests/selfhost/kernel/qa_kernel_hash.ax` (deleted).

## Vacuous-Test Sweep
1. `tests/run/numeric/intrinsic_ops.ax`: previously `// modes: interp` (`// native-after: T085`); upgraded to `// modes: interp native`, checking all 10 integer widths (`i8..i64`, `u8..u64`, `isize`, `usize`) at MIN/MAX/edge values in both interpreter and native (`-O0` and `-O1`).
2. `tests/std/core/qa_hash_vectors.ax`: previously `// modes: interp`; upgraded to `// modes: interp native`, verifying `std/core/hash.ax` (`fnv1a64`, `Hasher64`) natively against the independent Python vectors from `tests/unit/kernel/hash_vectors.txt`.
3. `tests/selfhost/kernel/qa_kernel_hash.ax` → replaced by `tests/selfhost/kernel/hash_native.ax` (`// modes: interp native`), replacing the hand-copied non-intrinsic `wrapping_mul_u64 { a * b }` with the verbatim `compiler/kernel/hash.ax` `@intrinsic fn wrapping_mul_u64` implementation verified against `tests/unit/kernel/hash_vectors.txt`.
4. `tests/selfhost/interp/qa_interp_exec_a.ax` and `tests/selfhost/interp/qa_interp_exec_b.ax`: both use `fn check(cond: bool) { if !cond { assert(false); } }` and were previously vacuous in native mode because `assert(false)` compiled to `{}`. With real native `assert`, step 5 of `qa_interp_exec_a.ax` (`test_hir_to_mir_on_demand_lowering`) and step 8 of `qa_interp_exec_b.ax` (`test_comptime_const_eval`) caught the `bootstrap/axiom0/src/lir/lower.c` projected call-destination type bug on `b.curr_bb = mb_new_bb(...)`. Fixed in `lower.c`; both tests now pass in `interp`, `native`, and `native-O1`.
5. Existing native-enabled tests using `@intrinsic fn assert` (`tests/run/numeric/qa_char_ordering.ax`, `tests/selfhost/{lex,ast,hir,resolve,typeck,mir,mir_analysis,opt,lir,x64,backend,driver}/qa_*.ax`, and `tests/std/**`): all `assert(...)` calls now lower to `AX_MIR_TERM_ASSERT` in native mode and pass in `interp`, `native`, and `native-O1`.

## Parity Registry (`known_divergent.txt`)
- All 144 pre-existing entries in `tests/selfhost/obj_link_driver/known_divergent.txt` are unchanged.
- Because T134 fixes `@intrinsic` lowering in `axiom0` only (`compiler/` is out of scope for T134 and assigned to `T150`), the 6 new tests added under `tests/run/intrinsics/*.ax` (`assert_false.ax`, `assert_true.ax`, `native_repro.ax`, `ops_table.ax`, `panic_abort.ax`, `panic_in_branch.ax`) and `tests/run/numeric/qa_char_ordering.ax` (which declares `@intrinsic fn assert(c: bool) {}` and previously matched only because both `axiom0` and `axiomc` compiled the `{}` placeholder body) diverge between `axiom0` and `axiomc` until `T150` ports the intrinsic table to `compiler/`. These 7 entries are recorded in `known_divergent.txt` for removal in `T150` (and `T155` for the 20-digit `u64` literal in `ops_table.ax`).
- Added `SetErrorMode(0x0001 | 0x0002)` on Windows in `tests/selfhost/obj_link_driver/axiomc_e2e_oracle.py` so child `axiomc.exe` crashes on `no-image` tests do not block in `WerFault.exe`.

## Follow-ups
- **T150 (`compiler/mir/builder.ax`, `compiler/types/typeck.ax`, `compiler/driver/pipeline.ax`):** Port the single intrinsic table and native lowering of `wrapping_*`, `rotate_*`, `leading_zeros_*`, `trailing_zeros_*`, `count_ones_*`, `assert`, `panic`, and `unreachable` to `compiler/`, and remove the 7 entries (`tests/run/intrinsics/{assert_false,assert_true,native_repro,ops_table,panic_abort,panic_in_branch}.ax` and `tests/run/numeric/qa_char_ordering.ax`) from `tests/selfhost/obj_link_driver/known_divergent.txt`.
- **Ported LIR call destination projection type (`compiler/lir/builder.ax` ~lines 1954–1956):** `compiler/lir/builder.ax` has the same bug that `bootstrap/axiom0/src/lir/lower.c` had on `MIR_TERM_CALL`: it looks up `dest_place.local` instead of using the projected place type from `lower_place_addr(mut_view(*b), dest_place, address_of_mut(res_ty_v))` when creating the `LIR_INST_ABI_RESULT` vreg. Port the 3-line fix to `compiler/lir/builder.ax` (in T148/T154).

## Verification
- Built in `build-snap-T134/build` with `cmake` + `ninja`: 0 warnings, 0 errors.
- `python tests/run/intrinsics/gen_ops_table.py --check`: OK (`90` width × operation checks).
- `python tests/selfhost/kernel/gen_hash_native.py --check`: OK (`10` `hash_vectors.txt` vectors + `"Xin chào thế giới"` UTF-8 bytes).
- `python tools/axtest.py --compiler build/axiom0.exe` in `build-snap-T134`: all 1,973 test executions pass (`0 FAIL`, including `tests/run/intrinsics/*`, `tests/run/numeric/intrinsic_ops.ax`, `tests/ui/intrinsics/unknown_intrinsic.ax`, `tests/selfhost/kernel/hash_native.ax`, `tests/std/core/qa_hash_vectors.ax`, `tests/selfhost/interp/qa_interp_exec_{a,b}.ax`, and `tests/selfhost/obj_link_driver/axiomc_e2e.test`).
- `python tools/archcheck.py`: `190 files scanned, 0 violations`.

## Files changed
- bootstrap/axiom0/src/diag/codes/TYPE.def
- bootstrap/axiom0/src/driver/pipeline.c
- bootstrap/axiom0/src/interp/host.h
- bootstrap/axiom0/src/interp/interp.c
- bootstrap/axiom0/src/lir/lower.c
- bootstrap/axiom0/src/mir/build/builder.c
- bootstrap/axiom0/src/mir/build/intrinsics.c
- bootstrap/axiom0/src/mir/build/intrinsics.h
- bootstrap/axiom0/src/mir/mir.h
- bootstrap/axiom0/src/mir/parse.c
- bootstrap/axiom0/src/mir/print.c
- bootstrap/axiom0/src/opt/opt.c
- bootstrap/axiom0/src/types/typeck.c
- tests/lir/wrapping_add.lir
- tests/lir/wrapping_add.mir
- tests/lir/wrapping_add.test
- tests/lir/wrapping_mul.lir
- tests/lir/wrapping_mul.mir
- tests/lir/wrapping_mul.test
- tests/lir/wrapping_sub.lir
- tests/lir/wrapping_sub.mir
- tests/lir/wrapping_sub.test
- tests/mir/intrinsics/assert_panic.ax
- tests/mir/intrinsics/assert_panic.mir
- tests/mir/intrinsics/rotate_u8.ax
- tests/mir/intrinsics/rotate_u8.mir
- tests/mir/intrinsics/wrapping_ops.ax
- tests/mir/intrinsics/wrapping_ops.mir
- tests/mir/wrapping_roundtrip.mir
- tests/mir/wrapping_roundtrip.test
- tests/run/intrinsics/assert_false.ax
- tests/run/intrinsics/assert_true.ax
- tests/run/intrinsics/gen_ops_table.py
- tests/run/intrinsics/native_repro.ax
- tests/run/intrinsics/ops_table.ax
- tests/run/intrinsics/ops_table_current.test
- tests/run/intrinsics/panic_abort.ax
- tests/run/intrinsics/panic_in_branch.ax
- tests/selfhost/intrinsics/qa_intrinsic_seams.ax
- tests/selfhost/intrinsics/qa_unreachable_abort.ax
- tests/selfhost/kernel/gen_hash_native.py
- tests/selfhost/kernel/hash_native.ax
- tests/selfhost/kernel/hash_native_current.test
- tests/selfhost/kernel/qa_kernel_hash.ax
- tests/selfhost/obj_link_driver/axiomc_e2e_oracle.py
- tests/selfhost/obj_link_driver/known_divergent.txt
- tests/std/core/qa_hash_vectors.ax
- tests/ui/intrinsics/qa_intrinsic_sig_edges.ax
- tests/ui/intrinsics/unknown_intrinsic.ax

## Status
STATUS: COMPLETE round=1

