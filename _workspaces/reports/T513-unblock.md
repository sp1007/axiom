# T513 Unblock Report — Widening `locks:` for E13.3 Freestanding Backend & Linker Pipeline

## Tóm tắt

Đã kiểm tra toàn bộ các điểm nối mã nguồn của `T513` (`E13.3 — Freestanding startup, static init order, custom section layout & CRT-free native image emission`) theo `SPEC-52` và quy tắc phân tầng `INV-LAYER-002` (`compiler/obj` và `compiler/link` nằm dưới tầng HIR/MIR, không được đọc HIR trực tiếp). Chẩn đoán của kỹ sư trong `T513-report.md` là hoàn toàn chính xác: để hạ tầng `--profile freestanding|kernel`, `@entry`, `@naked`, `@section("...")`, `@used`, `@no_mangle`, `@panic_handler`, `@global_allocator`, `extern "interrupt"` (`IRETQ`, `REQ-ABI-078`) và các biến `static`/`static mut` khởi tạo hằng hoạt động xuyên suốt cả ảnh PE32+ không CRT (`0` DLL import) lẫn `--interp` (`0 WEAK-NATIVE`), `T513` bắt buộc phải đi qua driver, backend session, const-eval trong `typeck`, MIR builder, Win64/interrupt ABI và interpreter.

Quyết định kiến trúc: **mở rộng `locks:` (`widen_locks`)** trên thẻ `T513` với đúng **9 file cụ thể** (8 file kỹ sư đã chỉ ra cộng thêm `compiler/interp/frame.ax` phát hiện khi kiểm tra đường đọc `CONST_AGGREGATE` của biến tĩnh/TLS khả biến) và nâng `timeout_min: 480`, giữ nguyên `depends: [T512]` để không phá vỡ chuỗi phụ thuộc của `T514` và `T515`. Đồng thời chỉ rõ cách biểu diễn `HIR_ITEM_STATIC` không-TLS bằng `MirLocalDecl { kind: MIR_LOCAL_CONST, mut_flag: true, const_sym: sym }` để **không phải chạm** vào `compiler/own/`, `compiler/verify/`, `compiler/opt/`, `compiler/diag/code.ax` hay các file facade `mod.ax`, đảm bảo `T513` không bị chặn lần thứ hai sau khi `T517` hoàn tất.

---

## 1. Root Cause & Seam Verification (`SPEC-52`, `INV-LAYER-002`)

`T513` originally owned only `paths: [compiler/lir, compiler/target/x64, compiler/obj, compiler/link, tests/link/freestanding]`. Because `INV-LAYER-002` forbids `compiler/obj/` and `compiler/link/` from importing `compiler/hir/` or `compiler/mir/`, `ObjModel` section/symbol construction and linker invocation happen in `compiler/driver/pipeline.ax` and `compiler/backend/session.ax`. Read-only verification of `compiler/` confirmed every seam cited in `T513-report.md` plus two subtle spots that would otherwise have tripped implementation:

1. **`compiler/driver/pipeline.ax`**:
   - `driver_emit_objmodel_filtered_ex` (`lines 7266–7953`) hardcodes emitted functions into `.text` (`lines 7663–7742`), emits only `@thread_local static` (`pipe_emit_tls_statics`, `line 7607`) and `@export const` (`pipe_emit_exported_consts`, `line 7804`), emits `KERNEL32.dll`-backed `axiom_panic` on `X64_MI_ASSERT` (`lines 4479–4495`) instead of a user `@panic_handler` or freestanding `UD2` trap fallback (`AXS-FRE-011`), and lacks `@section("...")` custom COFF section creation, `@used` root marking (`LGC_ROOT_USED`), and `@global_allocator` static dispatch shims (`AXS-FRE-012`, `AXS-FRE-014`).
   - `driver_execute_build_into_ctx` (`lines 8752–8928`) calls `pe_link_objmodel_to_buf` and `pe_link_multi_objs_and_libs_to_buf` without forwarding `ctx.eff_profile` or the `@entry` symbol name, causing `compiler/link/` to unconditionally synthesize `axiom_start` and `KERNEL32.dll` imports (`AXS-FRE-010.2`, `AXS-FRE-023`).
   - `pipeline_stage_interp` (`lines 3498–3554`) must forward `ctx.eff_profile` so `--interp` runs `@entry` under `freestanding`/`kernel`.
2. **`compiler/backend/session.ax`**:
   - `backend_populate_hir_const_aggregates` (`line 1137`) filters on `(*it).kind == HIR_ITEM_CONST` only, skipping `HIR_ITEM_STATIC` aggregate initializers (`BootHeader`, `Atomic<u64>`, arrays/tuples).
   - `backend_lower_fn_to_mc_checked*`, `session_emit_mc_hir`, and `session_emit_objmodel_hir` (`lines 2721–3044`) must forward `is_naked` and `extern "interrupt"` calling-convention metadata into ABI/frame lowering.
3. **`compiler/types/typeck.ax`**:
   - Const-evaluation into `thir.symbol_consts` is gated on `ik == HIR_ITEM_CONST || (ik == HIR_ITEM_STATIC && (*it).is_tls)` at **three** sites: `evaluate_const_item_in_impl` (`line 3217`), `check_item_body` (`line 12664`), and the top-level pass (`line 13612`). All three must include allowed non-TLS `HIR_ITEM_STATIC` items (`AXS-FRE-004`).
4. **`compiler/mir/mir.ax` & `compiler/mir/builder.ax`**:
   - `mir_build_lvalue` (`builder.ax:5278`) and `mb_build_expr_as_operand_raw` (`builder.ax:5630, 5714–5720`) only route `(*hit).is_tls` statics to addressable places; non-TLS `static` / `static mut` items fall through to `out_op.constant.val = sym.v as u64`.
5. **`compiler/abi/win64.ax`**:
   - `lir_lower_abi_in_arena` (`line 474`) requires `CallingConventionDescription` / `ABI_KIND_INTERRUPT` classification (`REQ-ABI-078`, `AXS-FRE-015.2`) so `extern "interrupt"` binds `(frame)` and optional `(error_code: u64)` to the hardware interrupt stack frame rather than Win64 `RCX`/`RDX`, and supplies the full preserved-GPR set to `compiler/target/x64/frame.ax`.
6. **`compiler/interp_opt/session.ax`, `compiler/interp/interp.ax`, and `compiler/interp/frame.ax` (additional catch)**:
   - `session_comptime_check_and_eval` (`interp_opt/session.ax:716`) unconditionally rejects unmasked `HIR_ITEM_STATIC`, and `session_find_main_fn` / `session_run_interp_with_args` (`lines 1353–1468`) hardcodes `fn main` (`AX_TYPE_MAIN_MISSING`).
   - `interp_init_frame_tls` (`interp/interp.ax:342–410`) already backs `(kind == MIR_LOCAL_CONST && mut_flag && const_sym.v != 0)` locals with heap-backed slots; keying non-TLS `HIR_ITEM_STATIC` items on a process-wide sentinel (`tid = 0xFFFFFFFFu32`) and registering `host_buf` via `interp_register_alloc(..., call_depth = 0)` provides shared static storage with valid provenance across frames/threads, alongside `@panic_handler` and `@global_allocator` hooks.
   - **Additional seam caught (`compiler/interp/frame.ax:414–425`)**: `get_local_ptr` currently short-circuits `if lkind == MIR_LOCAL_CONST` whenever `cval.kind == CONST_AGGREGATE`, returning `cval.agg_data` directly instead of `frm.local_ptrs[loc.v]`. Guarding line 414 with `!(unsafe { (*decl).mut_flag })` ensures aggregate `static` / `static mut` (e.g. `static IRQ_TICKS: Atomic<u64>`) and `@thread_local` struct slots read/write their dedicated runtime slot in `frm.local_ptrs`.

### Why NO Extra Locks Are Needed (`own/`, `verify/`, `opt/`, `diag/`, `mod.ax`)

- **`compiler/own/`, `compiler/verify/verifier.ax`, `compiler/opt/*`**: Every pass already treats `MirLocalDecl { kind: MIR_LOCAL_CONST, mut_flag: true, const_sym: sym }` as a pre-initialized, non-scalarizable, non-escaping static/global place (`own/init.ax:1096, 1266`, `verify/verifier.ax:3264`, `opt/sroa/mod.ax:3343`, `opt/escape/mod.ax:6814`, `opt/alias/mod.ax:1650`, `opt/inline/mod.ax:791, 2287`, `opt/ipa/mod.ax:924`, `opt/const_fold.ax:1524`), while `backend/session.ax:1372`, `lir/builder.ax:2349`, and `interp/interp.ax:3811` already exempt `mut_flag == true` from `const`-table promotion and write suppression. Both `LirBuilder` (`b.hir`) and `InterpCtx` (`ctx.hir`) already hold `*const HirFile` to distinguish `(*it).is_tls` (`emit_tls_addr_inst` vs RIP-relative `emit_fn_addr_inst`). Meanwhile, `compiler/own/unsafe.ax` (`lines 1300, 3408–3480`) already enforces `unsafe` on `static mut` accesses and `Share` on immutable `static` items.
- **`compiler/diag/code.ax`**: Verified that `T512` already registered `AX_TYPE_INVALID_NAKED_FN` (`180u32`), `AX_TYPE_INVALID_SECTION` (`181u32`), `AX_TYPE_ENTRY_MISSING` (`173u32`), and `AX_DRIVER_PROFILE_FORBIDDEN_CAP` (`171u32`). `DmaBuffer<T>` / `ForeignBox<T, A>` wrapper types belong to `T514` (`std/core`, `std/alloc`).
- **Module index facades (`compiler/*/mod.ax`)**: Verified `compiler/driver/pipeline.ax` (`lines 155–235`) and `compiler/backend/session.ax` (`lines 108–140`) import directly from leaf submodules (`compiler.backend.session.*`, `compiler.interp_opt.session.*`, `compiler.abi.win64.*`, `compiler.mir.mir.*`, `compiler.mir.builder.*`). Keeping existing public signatures intact and adding `_ex` / profile-aware helpers requires zero edits to `mod.ax`.

---

## 2. Options Considered & Decision Rationale

- **Option A — Widen `T513`'s `locks:` to the exact 9 verified files (`widen_locks`)**:
  - Keeps `T513` cohesive as the single compiler/linker delivery task of Epic `E13.3` (`T514` and `T515` already depend on `[T512, T513]`).
  - Uses 9 file-granular locks (`<= 10` files) rather than whole-directory locks on `compiler/driver`, `compiler/types`, or `compiler/mir`.
  - Automatically serializes `T513` after active `T517` (`compiler/driver`, `compiler/types`) and prevents parallel collision with `T537` (`priority: 140`, process-wide `static` / `static mut` items). Note: if the scheduler runs `T537` before `T513`, `T513` builds cleanly on top of it; if `T513` runs first, `T513` is self-sufficient without waiting on `T537`. *(Side note for coordinator awareness: `T537` in `todo/` will itself likely need `locks:` on `compiler/driver/pipeline.ax`, `compiler/backend/session.ax`, and `compiler/interp_opt/session.ax` when scheduled.)*
- **Option B — Split `T513` into frontend/MIR vs LIR/linker sub-tasks (`split`)**:
  - Rejected: `T513`'s acceptance criteria (`tests/link/freestanding` zero-import PE32+ executable + native/`--interp` parity) require the driver, MIR/LIR static & entry lowering, and PE32+ linker changes to land together; splitting would create artificial intermediate plumbing and churn `T514`/`T515` dependencies.

**Selected**: **Option A (`widen_locks`)**, with `timeout_min: 480` added to accommodate the cross-layer build, Stage-2/Stage-3 fixed-point check, and `taskgate.py` verification.

### Exact Verified `locks:` Added to `T513`

```yaml
locks: [compiler/driver/pipeline.ax, compiler/backend/session.ax, compiler/types/typeck.ax, compiler/mir/mir.ax, compiler/mir/builder.ax, compiler/abi/win64.ax, compiler/interp_opt/session.ax, compiler/interp/interp.ax, compiler/interp/frame.ax]
```

---

## Files changed

- _workspaces/tasks/todo/T513-e13-3-freestanding-startup-sections-crt-free-link.md

UNBLOCK_OUTCOME: widen_locks
