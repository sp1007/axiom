# T537 Unblock Report — Widening `paths:`/`locks:` for Process-Wide Statics & Reconciling `AX_CONC_UNSYNC_STATIC`

## Tóm tắt

Đã thẩm định toàn bộ các điểm nối mã nguồn của `T537` (`E13.1 — Process-wide static and static mut items`) xuyên suốt các tầng `driver`, `typeck`, `interp_opt`, `own`, `mir`, `verify`, `opt` (`-O1` lẫn `-O2`), `interp`, `lir`, `backend`, `obj`, và `link` theo `SPEC-02 AXS-GRM-035`, `SPEC-30 AXS-CONC-034`, `SPEC-50 AXS-UNS-002`, `ADR-0004`, và quy tắc phân tầng `INV-LAYER-002`. Báo cáo kiểm toán của kỹ sư (`T537-report.md`) hoàn toàn chính xác, và việc rà soát mở rộng của kiến trúc sư đã phát hiện thêm **cụm tối ưu hóa `-O2` trong `compiler/opt/`** (`optir`, `alias`, `escape`, `sroa`, `inline`, `ipa`) cùng đường quét ký hiệu `std` trong `compiler/driver/pipeline.ax` mà nếu thiếu sẽ khiến `MIR_LOCAL_STATIC` bị hạ nhầm thành biến ngăn xếp / SSA hoặc bị loại bỏ ở `-O2`.

Hai quyết định kiến trúc dứt điểm để `T537` triển khai trọn vẹn trong một lượt duy nhất và không bao giờ bị chặn lần thứ hai:
1. **Mở rộng `paths:` và `locks:` (`widen_paths_and_clarify_spec`)**: mở rộng `compiler/mir/builder.ax` thành `compiler/mir` trong `paths:` (bao gồm `mir.ax`, `mod.ax`, `builder.ax`, `drop.ax`) và bổ sung vào `locks:` các file xuyên tầng bắt buộc gồm `compiler/driver/pipeline.ax`, `compiler/interp_opt/session.ax`, `compiler/backend/session.ax`, `compiler/verify/verifier.ax`, `compiler/own/init.ax`, cùng toàn bộ `compiler/opt` (0 xung đột với mọi thẻ `ready` trên bảng công việc, bảo đảm xử lý sạch cả `-O1` lẫn `-O2`). Đồng thời bổ sung `T537` vào `depends: [T512, T537]` của `T513` để `T513` kế thừa trực tiếp `MIR_LOCAL_STATIC` thay vì tạo nhánh hạ mã `MIR_LOCAL_CONST` chồng chéo.
2. **Chuẩn hóa mã chẩn đoán truy cập `static mut` ngoài `unsafe` (`AX_CONC_UNSYNC_STATIC`)**: giữ nguyên mã `AX_CONC_UNSYNC_STATIC` (`compiler/own/unsafe.ax:3162`) khi đọc, ghi, chiếu trường/phần tử, hoặc tạo `view`/`mut_view` trên `static mut` không-`@thread_local` ở mã an toàn (trong khi lời gọi `address_of(S)` / `address_of_mut(S)` ngoài `unsafe` đồng thời phát `AX_UNSAFE_REQUIRED` trên intrinsic), khớp tuyệt đối với `SPEC-30 AXS-CONC-034`, `SPEC-50 AXS-UNS-002` (dòng 5) và bảo toàn nguyên vẹn cả 4 bài kiểm thử P11/T433/T485 đã nghiệm thu mà không cần chạm `compiler/own/unsafe.ax`.

---

## 1. Complete Seam Verification & Widened `paths:` / `locks:`

Because `INV-LAYER-002` forbids `compiler/obj/` and `compiler/link/` from importing `compiler/hir/` or `compiler/mir/`, `ObjModel` section/symbol materialization and comptime/MIR wiring span the driver and session layers. Read-only inspection across `compiler/` verified every seam in `T537-report.md` plus additional `-O2` optimizer, mutability, and `std`-symbol seams:

1. **`compiler/driver/pipeline.ax`** *(added to `locks:`)*:
   - `pipeline_mask_allowed_statics` (`lines 3013–3039, 3163–3173`) masks only freestanding/TLS statics before `session_comptime_check_and_eval`, leaving hosted non-TLS `HIR_ITEM_STATIC` items exposed to the bootstrap rejection in `interp_opt/session.ax`.
   - `driver_emit_objmodel_filtered_ex` (`lines 7266–7953`) emits only `@thread_local static` (`pipe_emit_tls_statics`, `line 5485`) and `@export const` (`pipe_emit_exported_consts`, `line 5525`). It must emit immutable non-TLS `static` items into `.rdata` (`SEC_RODATA`), non-zero `static mut` items into `.data` (`SEC_DATA`, `SEC_FLAG_READ | SEC_FLAG_WRITE`), and all-zero `static mut` items into `.bss` (`SEC_BSS`, `SEC_FLAG_READ | SEC_FLAG_WRITE`) with relocations for `Str` slices and function pointers, non-`.L` symbol names (since `lines 7848–7851` demote `.L*` symbols to `SYM_LOCAL` in per-module/lib builds), and `.axmeta` `SYM_ABI_KIND_DATA` entries (`line 6705`) when exported.
   - **Additional seam caught (`lines 6995, 7179`)**: `pipe_bodies_ref_sym` and `pipe_mark_body_std_refs` currently scan statement/terminator `MIR_OP_CONST` operands only and ignore `(*body).locals[i].const_sym`. Scanning `(*body).locals` for `MIR_LOCAL_STATIC` / `MIR_LOCAL_TLS` `const_sym` references (and retaining referenced `std` statics) ensures process-wide statics inside `std/sys/windows/{fiber,thread}.ax` (`T538`) are emitted and linked cleanly.
2. **`compiler/interp_opt/session.ax`** *(added to `locks:`)*:
   - `session_comptime_check_and_eval` (`lines 716–718`) unconditionally emits `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` on unmasked `HIR_ITEM_STATIC`, and `lines 780–826` only const-validate/evaluate `HIR_ITEM_CONST`. Hosted non-TLS `HIR_ITEM_STATIC` initializers must be validated as constant expressions and evaluated into `thir.symbol_consts`.
3. **`compiler/backend/session.ax`** *(added to `locks:`)*:
   - `backend_populate_hir_const_aggregates` (`line 1137`) filters on `(*it).kind == HIR_ITEM_CONST` only, skipping `HIR_ITEM_STATIC` aggregate initializers (`struct`, `[N]T`, tuple).
   - `session_emit_objmodel_hir` (`lines 2837–3044`) and `session_emit_mc_hir` (`lines 2721–2807`) must also emit `.rdata`/`.data`/`.bss` static sections/symbols for `inspect --emit=obj` and `inspect --emit=mc`.
4. **`compiler/types/typeck.ax`** *(already in `paths:`)*:
   - Const-evaluation into `thir.symbol_consts` is gated on `ik == HIR_ITEM_CONST || (ik == HIR_ITEM_STATIC && (*it).is_tls)` at three sites (`lines 3219, 12888, 13836`); all three must include non-TLS `HIR_ITEM_STATIC`.
   - **Additional seam caught (`lines 10054, 10089, 8912`)**: `check_stmt_assign` (`line 10089`) and `tc_check_place_mutable` (`line 10054`) check `cx.vars` for local mutability (`AX_TYPE_ASSIGN_IMMUTABLE`) without checking immutable `HIR_ITEM_STATIC` (or `HIR_ITEM_CONST`) items on `S = v`, `S.f = v`, `S[i] = v`, `address_of_mut(S)`, and `mut_view(S.f)`. Also keep the standalone `unsafe_check_expr` helper (`line 14292`, used only if `typeck_with_evaluator` is called directly) consistent with `AX_CONC_UNSYNC_STATIC` if touched.
5. **`compiler/mir` (`mir.ax`, `mod.ax`, `builder.ax`, `drop.ax`)** *(widened from `compiler/mir/builder.ax` to `compiler/mir` in `paths:`)*:
   - Define `pub const MIR_LOCAL_STATIC: u8 = 6u8;` next to `MIR_LOCAL_TLS` (`5u8`) in `mir.ax` (with text printer/parser support alongside `MIR_LOCAL_TLS`) and re-export in `mod.ax`.
   - Route non-TLS `HIR_ITEM_STATIC` places in `builder.ax` (`mir_build_lvalue` at `5278` and `mb_build_expr_as_operand_raw` at `5630, 5714`) to a `MirLocalDecl { kind: MIR_LOCAL_STATIC, mut_flag: (*hit).is_mut, const_sym: sym }`.
   - Skip `MIR_LOCAL_STATIC`, `MIR_LOCAL_TLS`, and `MIR_LOCAL_CONST` in `mir_drop_elaborate` (`drop.ax:2858` and `drop_collect_sub_flags` at `2906`) so static storage never receives scope-exit or overwrite drop flags.
6. **`compiler/verify/verifier.ax`** *(added to `locks:`)*:
   - Seed `VERIFY_ST_OWNED` at `line 3264` for `MIR_LOCAL_STATIC` alongside `MIR_LOCAL_ARG`, `MIR_LOCAL_CONST`, and `MIR_LOCAL_TLS`.
   - Exclude `MIR_LOCAL_STATIC`, `MIR_LOCAL_TLS`, and `MIR_LOCAL_CONST` from `is_droppable` scope-exit drop obligations (`line 3051`) so `!Copy` statics with `Drop` types do not trigger `AX_VERIFY_MISSING_DROP` on `return`.
   - Include `MIR_LOCAL_STATIC` in `verify_mir_cap` (`line 3692`: `(lk == MIR_LOCAL_USER || lk == MIR_LOCAL_ARG || lk == MIR_LOCAL_STATIC) && !is_mut`) so `MIR_BORROW_MUT` on an immutable `static` is rejected.
7. **`compiler/own/init.ax`** *(added to `locks:`)*:
   - Seed `OWN_OWNED` at `lines 1096, 1266` for `MIR_LOCAL_STATIC` and `MIR_LOCAL_TLS` alongside `MIR_LOCAL_ARG` and `MIR_LOCAL_CONST`.
   - Immediately reject any `!Copy` move rooted at `MIR_LOCAL_STATIC` or `MIR_LOCAL_TLS` (when there is no `MIR_PROJ_DEREF` in the place prefix) in `own_do_move` (`line 384`) and `own_bits_use_and_move` (`line 788`) with `AX_MOVE_USE_AFTER_MOVE` (matching borrowed-place moves in `tests/ui/own_mut_view_receiver/qa_guard_arm_view_place_move.ax`).
8. **`compiler/opt` (`-O1` and `-O2` passes)** *(locked as `compiler/opt` in `locks:`)*:
   - **`-O1` (`const_fold.ax`, `dce.ax`)**:
     - `const_fold.ax:1524`: mark `MIR_LOCAL_STATIC` as `is_bad = 1u8` alongside `MIR_LOCAL_CONST` and `MIR_LOCAL_TLS`.
     - `dce.ax:253`: seed `uses[lv] = 1u32` for `MIR_LOCAL_STATIC` and `MIR_LOCAL_TLS` (and mutable `MIR_LOCAL_CONST`) so helper functions whose final action is storing to a `static mut` do not have their global store stripped as dead code.
   - **Additional `-O2` seams caught (`optir`, `alias`, `escape`, `sroa`, `inline`, `ipa`)**:
     - `optir/mod.ax:1070`: set `local_addr_taken[i] = true` for `MIR_LOCAL_STATIC`, `MIR_LOCAL_TLS`, and `MIR_LOCAL_CONST` so `optir/mod.ax:1339` assigns `OPT_LOCAL_MEMORY` rather than promoting globals into SSA scalar slots (`OPT_LOCAL_SCALAR`) or SROA field slots (`OPT_LOCAL_SROA`).
     - `alias/mod.ax:1650, 2173`: classify `MIR_LOCAL_STATIC` (and `MIR_LOCAL_TLS` / mutable `MIR_LOCAL_CONST`) as `DOMAIN_GLOBAL_STATIC` when `mut_flag` is true (with `escaped_external = true` / `raw_addr_exposed = true` so `memopt` DSE keeps stores at function exit and calls clobber cached loads) and `DOMAIN_CONST_RDATA` when immutable, with `root = ALLOC_ROOT_GLOBAL_BASE + const_sym.v`.
     - `sroa/mod.ax:1401, 1796, 3096, 3343` and `escape/mod.ax:6814`: exclude `MIR_LOCAL_STATIC` / `MIR_LOCAL_TLS` / `MIR_LOCAL_CONST` from copy-prop, aggregate SROA, and NRVO, and seed them in `sroa_mir_init_check` and `esc_mir_init_check`.
     - `inline/mod.ax:791, 2287` and `ipa/mod.ax:924`: preserve `MIR_LOCAL_STATIC` and `MIR_LOCAL_TLS` when cloning callee locals into a caller during inlining (instead of rewriting them to `MIR_LOCAL_TEMP`!), and guard `const_sym` function-pointer specialization on `!(*ldecl).mut_flag && (*ldecl).kind == MIR_LOCAL_CONST`.
   - *Concurrency check*: Zero ready tasks on the board (`T457`, `T426`, `T507`, `T513`, `T518`, `T522`, `T551`, `T562`, `T058`, `T571`) touch `compiler/opt`, so locking `compiler/opt` has zero scheduler contention cost while eliminating any risk of `-O2` miscompilation or a second block.
9. **`compiler/interp` (`interp.ax`, `frame.ax`)** *(already in `paths:`)*:
   - All interpreter threads spawned via `std.thread` share one `InterpCtx` (`ctx.oracle.last_thread_callee[15]`). Keying `MIR_LOCAL_STATIC` slots in `interp_init_frame_tls` (`interp.ax:342`) on a process-wide sentinel (`tid = 0xFFFFFFFFu32`, while `MIR_LOCAL_TLS` uses `ctx.oracle.current_tid`), initializing all scalar/string/fn-ptr/aggregate `ConstValue` kinds, and registering `host_buf` via `interp_register_alloc(..., call_depth = 0)` provides one shared allocation with a stable address across all functions and threads.
   - Guard `get_local_ptr` in `interp/frame.ax:414` (`lkind == MIR_LOCAL_CONST && !(unsafe { (*decl).mut_flag })`) so `MIR_LOCAL_STATIC` and mutable TLS/static aggregate slots always resolve through `frm.local_ptrs[loc.v]`.
10. **`compiler/lir/builder.ax`, `compiler/target/x64/*`, `compiler/obj`, `compiler/link/{linker,pe}.ax`**:
    - `compiler/lir/builder.ax` *(already in `paths:`)* lowers `MIR_LOCAL_STATIC` addresses via RIP-relative `emit_fn_addr_inst` (`LIR_INST_FN_ADDR`) and permits stores to `MIR_LOCAL_STATIC`.
    - `compiler/target/x64/*` *(verified `0` edits needed)* already lowers `LIR_INST_FN_ADDR` to RIP-relative `X64_MI_LEA` (`RELOC_X86_64_PC32` / `IMAGE_REL_AMD64_REL32`).
    - `compiler/obj/writer.ax` (`lines 71–91, 173–185`) already computes `SEC_BSS` `size_of_raw_data` with `pointer_to_raw_data = 0`, and `compiler/link/{linker,pe}.ax` *(already in `paths:`)* handles `.rdata`, `.data`, and `.bss` merging and PE32+ emission.

---

## 2. Architectural Decision: Safe `static mut` Diagnostic (`AX_CONC_UNSYNC_STATIC` vs `AX_UNSAFE_REQUIRED`)

- **Normative specification**:
  - `SPEC-30 AXS-CONC-034(2)` (`REQ-CONC-012`) explicitly mandates: *"Unsynchronized mutable global variables (`static mut`) cannot be read or written in safe Axiom code (`AX_CONC_UNSYNC_STATIC`). ... Direct access to raw `static mut` ... is restricted to `unsafe` blocks"*.
  - `SPEC-50 AXS-UNS-002` (row 5) lists *"Reading, writing, or taking a capability/pointer to a `static mut` item -> `AX_UNSAFE_REQUIRED` / `AX_CONC_UNSYNC_STATIC` (`SPEC-30 AXS-CONC-034`)"*, cross-referencing `SPEC-30 AXS-CONC-034` for the `static mut` code while row 2 (`address_of` / `address_of_mut`) emits `AX_UNSAFE_REQUIRED`.
- **Implementation & Conformance Baseline**:
  - `compiler/own/unsafe.ax:3157–3166` (invoked by `pipeline_stage_typeck` at `pipeline.ax:3134` and `pipeline_stage_own` at `pipeline.ax:3199`) already rejects every safe path reference to a non-`@thread_local` `static mut` (read, write, field/index projection, `view`, `mut_view`) with `AX_CONC_UNSYNC_STATIC`, while `address_of(S)` / `address_of_mut(S)` outside `unsafe` additionally emits `AX_UNSAFE_REQUIRED` on the intrinsic call (`unsafe.ax:3238–3241`).
  - Four accepted UI tests enforce exact 1-to-1 `//~ ERROR AX_CONC_UNSYNC_STATIC` matches:
    1. `tests/conformance/p11/e11_1_concurrency/ui_unsync_mutable_statics.ax:50–51`
    2. `tests/ui/concurrency/data_race/unsync_static_and_unsafe_reentry.ax:24–25`
    3. `tests/ui/concurrency/data_race/tls_struct_init_and_scoped_view_not_share.ax:55–56`
    4. `tests/perf/own_scaling/qa_unsafe_index_ui.ax:18–19`
- **Decision**:
  - Keep **`AX_CONC_UNSYNC_STATIC`** as the canonical diagnostic for reading, writing, projecting, or taking `view`/`mut_view` of a non-`@thread_local` `static mut` outside `unsafe` (with `address_of` / `address_of_mut` outside `unsafe` also reporting `AX_UNSAFE_REQUIRED` on the intrinsic call).
  - Updated `T537`'s `## Scope` explicitly to reflect this contract — zero edits needed in `compiler/own/unsafe.ax` and zero churn to accepted P11 conformance tests.

---

## 3. Coordination with `T513` (`depends: [T512, T537]`)

`T513` (`priority: 162`, `E13.3 — Freestanding startup, static init order, custom section layout & CRT-free native image emission`) previously carried a fallback note from `T513-unblock` suggesting `MirLocalDecl { kind: MIR_LOCAL_CONST, mut_flag: true }` in case `T513` ran before `T537`. Because `T537` (`priority: 140`) delivers first-class `MIR_LOCAL_STATIC` (`6u8`) and hosted `.rdata`/`.data`/`.bss` emission first, adding `T537` to `T513`'s `depends: [T512, T537]` and updating `T513`'s `## Notes` guarantees strict ordering even across `--infra` requeues and lets `T513` layer freestanding `@section("...")`, `@used`, `@no_mangle`, and `@global_allocator` semantics directly onto `MIR_LOCAL_STATIC` without duplicate plumbing.

---

## Files changed

- _workspaces/tasks/todo/T537-e13-1-process-wide-static-and-static-mut-items.md
- _workspaces/tasks/todo/T513-e13-3-freestanding-startup-sections-crt-free-link.md

UNBLOCK_OUTCOME: widen_paths_and_clarify_spec
