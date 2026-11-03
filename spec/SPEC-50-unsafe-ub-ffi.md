# SPEC-50 — Canonical Unsafe, Undefined Behavior, Pointer Provenance, FFI/ABI & Address Introspection Specification

Status: draft (T500, 2026-11-03)
Owner: axiom-architect
Consolidates: `specs/0044`; `specs/0071`; `specs/0104`; `specs/0112 §84`; `specs/0114 §24–25`; `specs/0115 §34–36`; `specs/0118 §206`; `specs/0119 §215–259`; `specs/0121 §323–324`; `specs/0124 §9–87`; `specs/0126 §26–57`; `specs/0128 §60–66`; `specs/0129 §9, §62–101`; `specs/0131 §22, §78–88`; `specs/0132 §56–62`; `specs/0133 §69–87`; `specs/0138 Part XIX (§1–100)`; `specs/0151 §5, §24–25`; `specs/0159 §53, §66–67`; `specs/0160 §13–40`; `specs/0161 §14–18`; `specs/0162 §20–26, §43`; `specs/0163 §5, §32–47`; `specs/0177 §4–28`; `specs/0181`; `specs/0228 §14, §22`; `specs/0230 §8–11`; `specs/0266 §1–6`; `specs/0270 §8–28`; `specs/0292`; `specs/0300`; `tasks/0282`; `tasks/0339 (§1–100, ASAFE-20..100)`; `tasks/0367 (§1–82, AABI-20..70)`; `tasks/0395`; `tasks/0413 (§1–70, AFFI-20..64)`; `tasks/0416 §71`; `tasks/0426 §85`; `tasks/0429 §8–52`; `tasks/0431 §49–52`; `tasks/0432 §49–58`; `tasks/0436 §79–81`; `tasks/0437 §73`; `tasks/0441 §201`; `tasks/0442 §160–181`; `tasks/0445 §186.161`; `tasks/0451 §192.39`; `tasks/0452 §193.47`; `tasks/0459 §200.9–40`; `tasks/0468 §209.11–40`; `tasks/0470 §211.49–51`; `tasks/0476 §217.51–58`; `tasks/0482 §37–39`; `tasks/0484 §36–82`; `tasks/0486 §4–49`; `tasks/0517`; `tasks/0585 §1`; `tasks/0795 §573.71`; `spec/SPEC-03-core-semantics.md`; `spec/SPEC-04-core-extensibility.md`; `spec/SPEC-10-ownership.md`; `spec/SPEC-11-capability.md`; `spec/SPEC-12-drop.md`; `spec/decisions/ADR-0001-fixed-address-declarations.md`; `spec/decisions/ADR-0034-oracle-independence.md`; `spec/decisions/ADR-0036-view-autoderef-and-raw-pointer-capabilities.md`; `spec/requirements/OWNER.md` (`REQ-OWNER-008`).
Covers: `REQ-OWNER-008`, `REQ-ABI-005`, `REQ-ABI-006`, `REQ-ABI-007`, `REQ-ABI-008`, `REQ-ABI-013`, `REQ-ABI-014`, `REQ-ABI-015`, `REQ-ABI-016`, `REQ-ABI-017`, `REQ-ABI-020`, `REQ-ABI-021`, `REQ-ABI-023`, `REQ-ABI-025`, `REQ-ABI-026`, `REQ-ABI-027`, `REQ-ABI-028`, `REQ-ABI-029`, `REQ-ABI-030`, `REQ-ABI-034`, `REQ-ABI-035`, `REQ-ABI-037`, `REQ-ABI-038`, `REQ-ABI-040`, `REQ-ABI-042`, `REQ-ABI-043`, `REQ-ABI-051`, `REQ-ABI-058`, `REQ-ABI-062`, `REQ-ABI-068`, `REQ-ABI-073`, `REQ-ABI-086`, `REQ-ABI-087`, `REQ-ABI-088`, `REQ-CAP-004`, `REQ-CAP-006`, `REQ-CAP-008`, `REQ-CAP-009`, `REQ-CAP-011`, `REQ-CAP-012`, `REQ-CAP-014`, `REQ-CAP-016`, `REQ-CAP-017`, `REQ-CAP-020`, `REQ-CAP-021`, `REQ-CAP-022`, `REQ-CAP-023`, `REQ-CAP-024`, `REQ-CAP-028`, `REQ-CAP-029`, `REQ-CAP-030`, `REQ-CAP-035`, `REQ-CAP-036`, `REQ-CAP-039`, `REQ-CAP-042`, `REQ-CAP-043`, `REQ-CAP-044`, `REQ-CAP-045`, `REQ-CAP-050`, `REQ-CAP-052`, `REQ-CAP-053`, `REQ-CAP-054`, `REQ-CAP-055`, `REQ-CAP-057`, `REQ-CAP-058`, `REQ-CAP-060`, `REQ-CAP-063`, `REQ-CAP-064`, `REQ-CAP-066`, `REQ-CAP-068`, `REQ-CAP-072`, `REQ-CAP-074`, `REQ-CAP-075`, `REQ-CAP-076`, `REQ-CAP-077`, `REQ-CAP-079`, `REQ-CAP-080`, `REQ-CAP-081`, `REQ-CAP-082`, `REQ-CAP-089`, `REQ-CAP-090`, `REQ-CAP-092`, `REQ-CAP-094`, `REQ-CAP-096`, `REQ-CAP-097`, `REQ-CAP-099`, `REQ-CAP-100`, `REQ-CAP-101`, `REQ-CAP-104`, `REQ-CAP-106`, `REQ-CAP-108`, `REQ-CAP-110`, `REQ-CAP-112`, `REQ-CAP-113`, `REQ-CAP-114`, `REQ-CAP-115`, `REQ-CAP-116`, `REQ-CAP-117`, `REQ-CAP-119`, `REQ-CAP-120`, `REQ-CAP-121`, `REQ-CAP-128`, `REQ-CAP-134`, `REQ-CAP-142`, `REQ-CAP-147`, `REQ-RES-130`, `REQ-RES-131`, `REQ-RES-132`, `REQ-RES-138`, `REQ-RES-139`, `REQ-RES-140`, `REQ-RES-141`, `REQ-RES-144`, `REQ-RES-146`, `REQ-RES-147`, `REQ-RES-148`, `REQ-RES-149`, `REQ-RES-150`, `REQ-RES-151`, `REQ-RES-152`, `REQ-RES-153`, `REQ-RES-154`, `REQ-RES-155`, `REQ-RES-156`, `REQ-RES-157`, `REQ-RES-158`, `REQ-RES-162`, `REQ-RES-171`, `REQ-RES-172`, `REQ-RES-174`, `REQ-RES-175`, `REQ-RES-176`, `REQ-RES-177`, `REQ-RES-178`, `REQ-RES-179` (and specifies the E13.1 foundation for `T501`–`T505` and `E13.6` `T525`–`T529`).
Consumers: `compiler/hir/`, `compiler/sema/`, `compiler/types/`, `compiler/own/`, `compiler/mir/`, `compiler/verify/`, `compiler/interp/`, `compiler/opt/`, `compiler/lir/`, `compiler/abi/`, `compiler/target/x64/`, `compiler/obj/`, `compiler/link/`, `T501`–`T505`, `T525`–`T533`.

## Tóm tắt

Tài liệu `SPEC-50` chuẩn hóa ranh giới ngôn ngữ `unsafe`, danh mục hành vi bất định (`Undefined Behavior` — UB), mô hình nguồn gốc con trỏ thô (`strict pointer provenance`), hợp đồng giao tiếp ngoại ngữ và nhị phân (`FFI` / `ABI`), cùng đặc tả lấy địa chỉ và gắn địa chỉ cố định/động theo yêu cầu chủ dự án **`REQ-OWNER-008`** cho phân hệ `E13.1` (Phase `P13`). Các quyết định kiến trúc cốt lõi gồm:
- **`unsafe` là ranh giới nghĩa vụ chứng minh cục bộ, không phải chế độ tắt trình biên dịch (`ASAFE-20..40`, `INV-SEM-006`)**: Khối `unsafe { ... }`, hàm `unsafe fn`, và `unsafe trait` / `unsafe impl` chỉ cho phép các thao tác mức máy (giải tham chiếu `*const T` / `*mut T`, số học con trỏ, gọi `unsafe fn` / `extern`, truy cập `static mut`, khai báo `@addr` / `@at`). Bên trong `unsafe`, hệ thống kiểu, sở hữu (`ownership`), khởi tạo tất định, xung đột `view<T>` / `mut_view<T>`, hủy tất định (`Drop`), và kiểm tra ABI vẫn hoạt động đầy đủ. Ngay khi tạo `view<T>` hoặc `mut_view<T>` từ con trỏ thô qua lệnh MIR `MakeView` / `MakeMutView`, trình kiểm định an toàn (`verifier`) lập tức theo dõi provenance, vùng nhớ (`region`), và thời gian sống như bình thường.
- **Mô hình nguồn gốc con trỏ nghiêm ngặt (`Strict Provenance`) và phát hiện UB tất định trên Oracle (`T502`)**: Giá trị, vị trí (`Place`), quyền truy cập (`view`/`mut_view`), con trỏ thô (`*const T`/`*mut T`), và địa chỉ số (`usize`) là các tầng tách biệt (`Value != Address != Pointer != View`). Mỗi con trỏ mang `Provenance = (AllocId, Bounds, Permission, AddrSpace)`. Trình thông dịch MIR (`--interp`) gắn thẻ từng cấp phát và từng byte khởi tạo để bắt chính xác mọi lỗi UB (use-after-free, vượt biên, lệch căn chỉnh, đọc byte chưa khởi tạo, giả mạo provenance từ số nguyên, vi phạm độc quyền `mut_view`) bằng mã chẩn đoán `AX_UNSAFE_INTERP_UB` (mã thoát `125`).
- **Đặc tả đầy đủ `REQ-OWNER-008` (`fn_addr`, `static_addr`, `address_of(v) as usize`, `addr_of`, `@addr(<expr>)` / `@at(<expr>)`)**: Cho phép lấy địa chỉ của bất kỳ hàm (`fn_addr(f) -> usize`, `addr_of(f)`, `f as usize`), biến tĩnh (`static_addr(s) -> usize`), hoặc biến cục bộ/trường/phần tử (`address_of(v) -> *const T`, `address_of_mut(v) -> *mut T`, `address_of(v) as usize`, `addr_of(v) -> usize`), đồng thời đặt `static`, `let`, và `fn` tại địa chỉ cố định hoặc biểu thức động `@addr(<expr>)` / `@at(<expr>)` (ví dụ `let base = fn_addr(foo); @addr(base + 0x100) static mut REG: u32;`), bảo đảm đẳng thức khứ hồi `fn_addr(isr) == 0x2000_0000usize` và `static_addr(REG) == base + 0x100` trên cả `--interp` lẫn mã máy x86-64.
- **Tách biệt ABI nội bộ và hợp đồng FFI/ABI tường minh (`AABI-20..70`, `AFFI-20..64`, `ADR-0034 §8`)**: ABI mặc định của Axiom (`extern "axiom"`) do compiler kiểm soát để tối ưu hóa tối đa; khả năng hiển thị `pub` không đồng nghĩa xuất ký hiệu nhị phân (`@export`) hay ổn định ABI. Giao tiếp C/hệ thống đòi hỏi hợp đồng tường minh (`extern "C"`, `@repr(C)`, `@repr(transparent)`, `@abi(stable)`), kiểu an toàn FFI, hàm gọi lại `extern "C" fn`, mô hình hiệu ứng ngoại lai bảo thủ mặc định, và được kiểm chứng độc lập đối chiếu với DLL xây bằng `gcc -shared` cùng bảng `offsetof`/`sizeof` (`T503`) trước khi mở rộng codegen FFI (`T504`).

---

## 1. The Unsafe Boundary & Trusted Precondition Model (`AXS-UNS-001`..`007`)

### AXS-UNS-001 — Three-Tier Safety Architecture & Local Scope of `unsafe` (`ASAFE-20..40`, `INV-SEM-006`)

Axiom partitions program semantics into three explicit layers (`tasks/0339 §1–5`, `0071 §5`, `0151 §24–25`):

1. **Safe Layer (`SAFE`)**: The compiler statically proves memory, ownership, capability, initialization, type, and concurrency invariants (`SPEC-03 AXS-SEM-002`). Safe Axiom code cannot cause undefined behavior (`UB`): it cannot perform use-after-free, double drop, dangling `view<T>`/`mut_view<T>` creation, invalid ownership transfer, conflicting mutable capability access, unsynchronized data races, out-of-bounds memory corruption, use of moved or uninitialized values, or invalid scalar/enum/UTF-8 representation (`ASAFE-20..33`).
2. **Trusted Unsafe Boundary (`TRUSTED UNSAFE BOUNDARY`)**: Introduced locally by `unsafe { ... }`, `unsafe fn`, or `unsafe impl`. At this boundary, the programmer assumes responsibility for machine-level preconditions that cannot be decided statically by the compiler alone (`ASAFE-34..35`).
3. **Machine / System Layer (`MACHINE / SYSTEM BEHAVIOR`)**: Raw pointers (`*const T`, `*mut T`), hardware addresses (`usize`, `@addr`/`@at`), MMIO/volatile registers (`SPEC-51`), and foreign ABI boundaries (`extern "C"`).

`unsafe` is a **localized proof-obligation boundary, never a compiler-off switch** (`INV-SEM-006`, `ASAFE-36..40`). Entering an `unsafe` block or `unsafe fn` unlocks only the specific machine-level operations listed in `AXS-UNS-002`; it never disables syntax, type, ownership, initialization, capability conflict, `Drop`, or ABI verification on surrounding or enclosed expressions.
[tasks/0339 §1–5, §100 ASAFE-20..40; 0071 §5, §57–58 AMEM-06, AMEM-15; 0151 §24–25; SPEC-03 AXS-SEM-002]

### AXS-UNS-002 — Operations Requiring an `unsafe` Context (`AX_UNSAFE_REQUIRED`)

An expression or declaration requires an enclosing `unsafe` context (`unsafe { ... }` block, `unsafe fn` body unless restricted by profile lint, or `unsafe` item modifier on `@addr`/`@at`) if and only if it performs one of the following operations:

| # | Operation | Syntax / Intrinsic | Diagnostic Outside `unsafe` |
|---|---|---|---|
| 1 | Raw-pointer dereference (read, write, field, index, reborrow) | `*p`, `p->field`, `(*p)[i]` on `p: *const T` or `*mut T` | `AX_UNSAFE_REQUIRED` (`data.operation = "raw_deref"`) |
| 2 | Raw-pointer address-taking or offset arithmetic | `address_of(place)`, `address_of_mut(place)`, `ptr_add(p, n)`, `ptr_sub(p, n)`, `ptr_byte_add(p, n)`, `ptr_diff(p1, p2)`, `p + n`, `p - n` | `AX_UNSAFE_REQUIRED` (`data.operation = "ptr_op"`) |
| 3 | Calling an `unsafe fn` or raw memory intrinsic | `f(args...)` where `f` is `unsafe fn` (`drop_in_place`, `ptr_copy`, `ptr_copy_nonoverlapping`, `ptr_write_bytes`, `view_from_raw`, `mut_view_from_raw`, etc.) | `AX_UNSAFE_REQUIRED` (`data.operation = "unsafe_call"`) |
| 4 | Calling an unannotated foreign `extern` function | `ext_fn(args...)` declared inside `extern "<abi>" { ... }` without a safe wrapper | `AX_UNSAFE_REQUIRED` (`data.operation = "extern_call"`) |
| 5 | Reading, writing, or taking a capability/pointer to a `static mut` item | `GLOBAL_COUNT += 1`, `let x = GLOBAL_COUNT`, `mut_view(GLOBAL_COUNT)` | `AX_UNSAFE_REQUIRED` / `AX_CONC_UNSYNC_STATIC` (`SPEC-30 AXS-CONC-034`) |
| 6 | Reading a field of an untagged `union` (`E13.2`, `SPEC-51`) | `u.variant_field` (writing a non-Drop field is safe; reading is `unsafe`) | `AX_UNSAFE_REQUIRED` (`data.operation = "union_field"`) |
| 7 | Declaring or binding a fixed/dynamic address item (`@addr` / `@at`) | `@addr(expr) static ...`, `@addr(expr) let ...`, `@addr(expr) fn ...` | `AX_UNSAFE_REQUIRED` (if item/block is not marked `unsafe` when accessing raw memory) |
| 8 | Implementing an `unsafe trait` | `unsafe impl Trait for Type { ... }` | `AX_UNSAFE_TRAIT_IMPL` / `AX_CONC_SAFE_IMPL_MARKER` |

Pointer-to-pointer casts (`p as *const U`, `p as *mut U`), pointer-to-integer casts (`p as usize`, `p as isize`), integer-to-pointer casts (`addr as *const T`, `addr as *mut T`), null pointer construction (`null::<T>()`, `null_mut::<T>()`), `is_null(p)`, and address introspection (`fn_addr(f)`, `static_addr(s)`, `addr_of(place)`) do **not** dereference memory and may be evaluated without an `unsafe` block; dereferencing any resulting raw pointer requires `unsafe` (`SPEC-03 AXS-SEM-060`, `SPEC-04 AXS-EXT-102`).
[tasks/0339 §5–9, ASAFE-41..46; 0071 §4, §8–11; tasks/0282 §5–7; SPEC-03 AXS-SEM-060; SPEC-04 AXS-EXT-102]

### AXS-UNS-003 — `unsafe { ... }` Blocks & Unchanged Safe Verification Rules (`ASAFE-36..39`, `ASAFE-71..76`)

Inside an `unsafe { ... }` block (`ExprKind.UnsafeBlock`):

1. **Type checking remains strict (`ASAFE-36`)**: Every operand, call argument, assignment, and return value is type-checked identically to safe code. Implicit narrowing, invalid `as` casts (`AX_TYPE_INVALID_CAST`), and raw-pointer indexing `p[i]` (`AX_TYPE_CANNOT_INDEX`, `SPEC-03 AXS-SEM-047`) remain compile-time errors.
2. **Ownership and move checking remain strict (`ASAFE-37`)**: Moving a `!Copy` local binding inside `unsafe` transitions the place to `MOVED` (`SPEC-10 AXS-OWN-002`); using it again emits `AX_MOVE_USE_AFTER_MOVE`. Partial moves out of a type implementing custom `Drop` remain rejected (`AXS-OWN-005`).
3. **Definite initialization remains strict (`ASAFE-39`)**: Reading a local variable before it is definitely initialized on all incoming control-flow paths remains a compile-time error (`AX_INIT_UNINITIALIZED`, `INV-SEM-004`). Uninitialized raw storage must be managed explicitly through `MaybeUninit<T>` (`SPEC-51`) or raw pointers `*mut T`.
4. **Capability conflict and lifetime checking remain strict (`ASAFE-38`)**: Any `view<T>` or `mut_view<T>` created or used inside an `unsafe` block is checked by the capability engine (`SPEC-11 AXS-CAP-001..009`) and MIR verifier (`VCAP-01..04`). An `unsafe` block cannot create two overlapping `mut_view<T>` values from the same safe owner or return a `view<T>` that outlives a local owner (`AX_CAP_CONFLICT_MUT`, `AX_CAP_OUTLIVES_OWNER`).
5. **Checked arithmetic remains active (`ASAFE-72`, `ASAFE-82..83`)**: `+`, `-`, `*`, `/`, `%`, `<<`, `>>` on integers inside `unsafe` still perform checked arithmetic and panic on overflow or division by zero (`SPEC-03 AXS-SEM-030..034`). Unchecked or wrapping operations must be requested per operation (`wrapping_add`, `unsafe_get`, etc.), never assumed globally from `unsafe` (`ASAFE-75..76`).
6. **No optimizer fabrications (`ASAFE-71..74`)**: Entering `unsafe` does NOT grant the optimizer permission to assume `NoAlias`, `NoOverflow`, infinite lifetime, or data-race freedom on raw pointers (`SPEC-70 AXS-OPT-032`, `SPEC-71 AXS-ALIAS-003`).
[tasks/0339 §5, §8–9, §100 ASAFE-36..39, ASAFE-71..76, ASAFE-82..85; INV-SEM-006]

### AXS-UNS-004 — `unsafe fn` Declarations, Caller/Callee Obligations & `/// SAFETY:` Contracts (`ASAFE-34..35`, `ASAFE-77..78`)

1. **Declaration & Signature (`SPEC-04 AXS-EXT-022`)**: A function declared `unsafe fn name(...) -> R` sets `sig.is_unsafe = true` in its `FnSig` and `FnPtr` type (`unsafe fn(A) -> R`).
2. **Caller Obligation**: Calling an `unsafe fn` (directly or via an `unsafe fn(...) -> R` function pointer) outside an `unsafe` block or `unsafe fn` body is rejected with `AX_UNSAFE_REQUIRED`.
3. **Function-Pointer Coercion**: A safe function item or pointer `fn(A) -> R` may coerce to `unsafe fn(A) -> R` (weakening the guarantee: a safe function is trivially callable when the caller uses an `unsafe` call site). The converse coercion (`unsafe fn(A) -> R` to safe `fn(A) -> R`) is **forbidden** and rejected with `AX_TYPE_MISMATCH`, because calling it without `unsafe` would bypass its preconditions.
4. **Callee Body & Safe Wrappers (`ASAFE-77..78`)**: Inside an `unsafe fn` body, unsafe operations (`AXS-UNS-002`) are permitted in v1.0 Core (while `E13.4` safety profiles add `@deny(unsafe_op_in_unsafe_fn)` requiring explicit inner `unsafe { ... }` blocks). Safe library APIs (`std`) encapsulate minimal `unsafe { ... }` blocks inside safe `pub fn` wrappers only when the wrapper enforces all preconditions for every possible safe caller input.
5. **Documentation Convention (`tasks/0339 §7`)**: Every `unsafe fn` and `unsafe trait` in `std/` and `compiler/` documents its machine preconditions in a `/// SAFETY:` doc-comment block, and every `unsafe { ... }` block documents how those preconditions hold in a `// SAFETY:` comment. Comments are advisory documentation for humans and AI tools, never automatic compiler proofs (`ASAFE-34..35`).
[tasks/0339 §6–9, ASAFE-34..35, ASAFE-77..78; SPEC-04 AXS-EXT-022]

### AXS-UNS-005 — `unsafe trait` and `unsafe impl` Contracts (`AX_UNSAFE_TRAIT_IMPL`)

1. **`unsafe trait` Declaration (`SPEC-04 AXS-EXT-031`)**: A trait declaration preceded by `unsafe` (`pub unsafe trait Pod { ... }`, `pub unsafe auto trait Send {}`, `pub unsafe auto trait Share {}`) sets `trait_def.is_unsafe = true`. It declares a semantic invariant that the compiler cannot verify from method signatures alone.
2. **Mandatory `unsafe impl`**: Implementing an `unsafe trait` for any type `T` requires the `unsafe impl` modifier:
   ```axiom
   unsafe impl Send for RawBufferHandle {}
   ```
   - Writing `impl Trait for T` without `unsafe` when `Trait` is an `unsafe trait` is rejected at compile time with `AX_UNSAFE_TRAIT_IMPL` (or `AX_CONC_SAFE_IMPL_MARKER` for `Send` and `Share` per `SPEC-30 AXS-CONC-018`).
   - Writing `unsafe impl Trait for T` when `Trait` is a **safe** trait is rejected with `AX_UNSAFE_UNNECESSARY_IMPL` (`data.trait_name`), preventing misleading trust markers.
3. **Trait Methods remain Safe by Default**: Marking a trait `unsafe trait` makes *implementing* the trait `unsafe`; its methods remain ordinary safe methods unless individually declared `unsafe fn`. Calling a safe method of an `unsafe trait` does not require an `unsafe` block.
[tasks/0339 §6, ASAFE-34..36; SPEC-04 AXS-EXT-031; SPEC-30 AXS-CONC-018]

### AXS-UNS-006 — Resumption of Safe Verification Across `unsafe` Boundaries (`MakeView` / `MakeMutView`, `ASAFE-40`, `REQ-MIR-142`)

When `unsafe` code constructs a safe capability (`view<T>`, `mut_view<T>`, `view<[T]>`, `mut_view<[T]>`, or `Str`) from a raw pointer (`*const T` or `*mut T`):

1. **Trusted Preconditions at Construction (`ACAP-38`, `ASAFE-34`, `AFFI-36`, `AFFI-49`)**:
   - For `unsafe { view_from_raw(p) -> view<T> }` (or `slice_from_raw_parts(p, len) -> view<[T]>`): the programmer guarantees that `p` is non-null, aligned to `align_of::<T>()`, points to `1` (or `len`) initialized valid instances of `T` within a single live allocation, and that the underlying memory will not be mutated or deallocated for the entire semantic lifetime of the resulting `view`.
   - For `unsafe { mut_view_from_raw(p) -> mut_view<T> }` (or `slice_from_raw_parts_mut(p, len) -> mut_view<[T]>`): the programmer guarantees all of the above plus **exclusive access** — no other capability or raw pointer may read or write the target region while the `mut_view` (or any sub-capability projected from it) remains active (`REQ-FFI-044..045`).
2. **Explicit MIR Lowering (`MakeView` / `MakeMutView`, `REQ-MIR-142`, `REQ-CAP-087..088`, `REQ-CAP-103`)**:
   - In `compiler/mir/`, constructing a `view` or `mut_view` from a raw pointer (or from an owned/borrowed place) lowers to an explicit `MirRvalue.MakeView` (`VIEW`) or `MirRvalue.MakeMutView` (`VIEW_MUT`) instruction — never a bare pointer copy (`0161 §14–15`, `tasks/0484 §36–37 AMIR-35..36`).
   - The MIR instruction attaches a `CapabilityFact` (`ProvenanceId`, `RegionId`, `AccessMode = Read | Write`, `Origin = RawTrusted(span)`).
3. **Immediate Resumption of Safe Verification (`ASAFE-40`, `AFFI-37`, `REQ-CAP-071`, `REQ-FFI-089`)**:
   - Once `MakeView` / `MakeMutView` produces a `view<T>` or `mut_view<T>` binding `v`, **all safe capability rules resume immediately** on `v` both inside the remainder of the `unsafe` block and after the `unsafe` block exits:
     - `v` cannot conflict with another overlapping `mut_view` (`AX_CAP_CONFLICT_MUT`, `VCAP-02`).
     - If `v` is bound with a lifetime tied to a scope/owner/guard (`MappedRegion`, `IoBuf`, `MutexGuard`, parent slice), `v` cannot escape that owner (`AX_CAP_OUTLIVES_OWNER`, `VCAP-03`, `REQ-CAP-083..085`, `REQ-CAP-093`, `REQ-CAP-127..129`).
     - `v` cannot be held live across an `.await` suspension point (`AX_ASYNC_VIEW_ACROSS_AWAIT`, `VCAP-04`, `REQ-CAP-056`, `REQ-CAP-070`, `REQ-CAP-086`, `REQ-CAP-094`) or transferred across threads unless `Send`/`Share` obligations hold (`AX_CONC_ESCAPING_VIEW`, `AX_CONC_NOT_SHARE`, `REQ-CAP-048`, `REQ-CAP-050..051`).
[0124 §58–59; 0160 §28; 0161 §14–18 VCAP-01..04; 0228 §22; tasks/0339 ASAFE-40; tasks/0413 AFFI-36..37, AFFI-49; tasks/0484 AMIR-35..36; REQ-CAP-037..038, REQ-CAP-071, REQ-CAP-087..094, REQ-CAP-103, REQ-MIR-142, REQ-FFI-088..089]

### AXS-UNS-007 — Capability, Region & Aliasing Invariants Preserved Across Boundaries (`REQ-CAP-001`..`151`)

To anchor `SPEC-11` (`AXS-CAP-001..009`) and `SPEC-71` (`AXS-ALIAS-001..006`) across the unsafe and FFI boundaries, every compiler stage (`typeck`, `own`, `verify`, `opt`, `abi`) enforces the following canonical capability invariants:

1. **Two Non-Owning Capability Types (`REQ-CAP-004`, `REQ-CAP-013..018`, `REQ-CAP-039`, `REQ-CAP-044`, `REQ-CAP-072..073`, `REQ-CAP-079`, `REQ-CAP-104..107`, `REQ-CAP-144`, `REQ-CAP-151`)**:
   - `view<T>` (`AccessMode.Read`) and `mut_view<T>` (`AccessMode.Write`) are the only two source-level non-owning capability types; safe Axiom has no `&T` or `&mut T` operators (`AX_PARSE_REFERENCE_OPERATOR`).
   - Capabilities **never own** their referent (`ACAP-23`, `ACAP-36`, `ACAP-47`) and **never transition into an owning value** (`AMEM-64`); converting `view<T>` to an owned `T` requires `T: Copy` (explicit deref read) or an explicit `.clone()` call (`REQ-CAP-024`).
   - `view<T>` is **intrinsically duplicable** (`ACAP-30`, `ACAP-34`): duplicating a `view<T>` creates a second read capability over the same region without copying `T` and without classifying `view<T>` as a value `Copy` type (`REQ-CAP-006`, `REQ-CAP-008`, `REQ-CAP-016..017`, `REQ-CAP-060`).
   - `mut_view<T>` is **exclusive and move-only** (`ACAP-33`, `ACAP-35`, `ACAP-28`): duplicating `mut_view<T>` is forbidden (`REQ-CAP-009`, `REQ-CAP-018`, `REQ-CAP-061`, `REQ-CAP-151`); passing `mut_view<T>` by value moves the capability (or creates a scoped hierarchical reborrow until the callee returns).
   - Converting `view<T>` to `mut_view<T>` is unconditionally forbidden in both safe and unsafe cast tables (`REQ-CAP-126`).
2. **Ephemeral vs Persistent Capabilities (`REQ-CAP-011`, `REQ-CAP-036`, `REQ-CAP-058`, `REQ-CAP-065..066`, `REQ-CAP-082`, `REQ-CAP-096`, `REQ-CAP-150`, `REQ-TYP-349`)**:
   - Passing an owned argument `x` to a `view<T>` or `mut_view<T>` function parameter (or method receiver `x.m()`) automatically constructs an **ephemeral capability** without borrow syntax (`REQ-CAP-011`, `REQ-CAP-036`, `REQ-CAP-065`). An ephemeral capability cannot escape the called function or enclosing statement (`REQ-CAP-150`, `AXS-CAP-005`).
   - Binding a persistent capability to a local variable, struct field, or return value requires **explicit** construction via `view(place)` or `mut_view(place)` (`REQ-CAP-058`, `REQ-CAP-066`, `REQ-CAP-082`, `REQ-CAP-096`).
   - Pattern matching through a `view<T>` or `mut_view<T>` scruntinee never transfers ownership out of the referent; pattern bindings inside such a match produce only sub-capabilities (`view<Field>` / `mut_view<Field>`) or copies of `Copy` fields (`ACAP-31`, `REQ-CAP-012`).
   - Implicit coercions in `typeck` (`REQ-TYP-349`) are limited to the specification-defined set: `String -> Str`, `[N]T -> view<[T]>`, owner `T ->` ephemeral `view<T>`, `mut_view<T> -> view<T>`, and `never -> T`.
3. **Region Algebra, Disjointness & Conflict Verification (`REQ-CAP-020`, `REQ-CAP-022..023`, `REQ-CAP-028..035`, `REQ-CAP-042..043`, `REQ-CAP-052..054`, `REQ-CAP-062..064`, `REQ-CAP-074..077`, `REQ-CAP-092`, `REQ-CAP-099..102`, `REQ-CAP-108`, `REQ-CAP-110..121`, `REQ-CAP-142`, `REQ-CAP-146..148`)**:
   - A capability region (`MemoryRegion`) may address a single scalar/struct value (`REQ-CAP-022`), an array, a slice/subarray, a struct field or nested field projection (`REQ-CAP-023`), an external FFI buffer, or device/MMIO memory (`REQ-CAP-020`).
   - Capability verification runs on MIR (`compiler/own/` and `compiler/verify/`), **never** in Typed HIR (`ATHIR-41`, `REQ-CAP-057`).
   - For any two regions $R_1, R_2$, the region algebra evaluates $\text{rel}(R_1, R_2) \in \{\text{SAME}, \text{DISJOINT}, \text{CONTAINS}, \text{CONTAINED\_BY}, \text{OVERLAPS}, \text{UNKNOWN}\}$ (`REQ-CAP-029`, `REQ-CAP-063`).
   - **Conflict rule**: Multiple concurrent `READ` (`view<T>`) capabilities over overlapping or `SAME` regions are permitted (`REQ-CAP-030`, `REQ-CAP-074`, `REQ-CAP-108`, `REQ-CAP-147`). Any pair of active capabilities (`READ + WRITE`, `WRITE + WRITE`, or owner `MOVE`/`DROP`/mutation + active capability) whose region relation is **not** provably `DISJOINT` — including `SAME`, `CONTAINS`, `CONTAINED_BY`, `OVERLAPS`, and **`UNKNOWN`** — is rejected at compile time with `AX_CAP_CONFLICT_MUT` (corpus alias `AX_VIEW_0001`; `REQ-CAP-028`, `REQ-CAP-031..035`, `REQ-CAP-043`, `REQ-CAP-053..054`, `REQ-CAP-062`, `REQ-CAP-064`, `REQ-CAP-075..077`, `REQ-CAP-092`, `REQ-CAP-099..100`, `REQ-CAP-102`, `REQ-CAP-110`, `REQ-CAP-146`).
   - **Disjoint sub-regions**: Concurrent `mut_view` capabilities to distinct struct fields (`s.a` and `s.b`, `ADATA-46`) or provably disjoint slice partitions (`split_at_mut`, chunked parallel iterations, `APAR-49..51`) are proven `DISJOINT` and permitted concurrently (`REQ-CAP-033`, `REQ-CAP-052`, `REQ-CAP-101`, `REQ-CAP-124`, `REQ-CAP-133..134`, `REQ-CAP-142`, `REQ-CAP-148`).
   - **Safety vs Alias Analysis (`REQ-CAP-109..121`)**: Capability verification answers *"is this access legal?"* (`REQ-CAP-112`), whereas alias analysis (`SPEC-71`) consumes proven capability/provenance facts (`REQ-CAP-111`) to answer *"how do these two accesses relate (`MustAlias`, `NoAlias`, `MayAlias`) for optimization?"* (`REQ-CAP-113..121`). `UNKNOWN` overlap is never promoted to `NoAlias` (`REQ-CAP-110`).
4. **Provenance, Last-Use Lifetime & Relocation Prevention (`REQ-CAP-001..003`, `REQ-CAP-005`, `REQ-CAP-007`, `REQ-CAP-019`, `REQ-CAP-025..027`, `REQ-CAP-040..042`, `REQ-CAP-046..049`, `REQ-CAP-059`, `REQ-CAP-067..069`, `REQ-CAP-078`, `REQ-CAP-080..081`, `REQ-CAP-083..085`, `REQ-CAP-091`, `REQ-CAP-093`, `REQ-CAP-095`, `REQ-CAP-097..098`, `REQ-CAP-122`, `REQ-CAP-125`, `REQ-CAP-127..129`, `REQ-CAP-145`, `REQ-CAP-149`)**:
   - Every capability carries compiler-tracked provenance `(Owner, Region, AccessMode, SyncContext, Validity)` (`ACAP-20`, `ACAP-24`, `ACAP-29`, `ACAP-32`, `ACAP-37`, `VCAP-01`).
   - A capability's lifetime spans from creation to its **semantic last use** (not necessarily the end of the lexical block, `ACAP-22`, `ACAP-38`, `REQ-CAP-003`, `REQ-CAP-025`, `REQ-CAP-040`), and never artificially extends the lifetime of its owner (`REQ-CAP-027`).
   - While a capability is active, its owner cannot be moved, dropped, mutated, unmapped (`MappedRegion`), freed while async/network I/O is in flight (`IoBuf`, `ANET-32..33`), or have its backing container storage relocated (`Vec.push`/`reserve`, `ACOL-25`, `AESCAPE-25`) (`AX_CAP_OUTLIVES_OWNER` / corpus alias `AX_VIEW_0002`, `AX_CAP_CONTAINER_RELOC`, `AX_CONC_GUARD_ESCAPE`; `REQ-CAP-026`, `REQ-CAP-042`, `REQ-CAP-046..047`, `REQ-CAP-049`, `REQ-CAP-067..069`, `REQ-CAP-080..081`, `REQ-CAP-084..085`, `REQ-CAP-097..098`, `REQ-CAP-119`, `REQ-CAP-122`, `REQ-CAP-125`, `REQ-CAP-127..129`, `REQ-CAP-145`, `REQ-CAP-149`).
5. **Optimization-Level Invariance & Post-Verification Erasure (`REQ-CAP-002`, `REQ-CAP-021`, `REQ-CAP-045`, `REQ-CAP-055`, `REQ-CAP-089..090`, `REQ-RES-148..149`)**:
   - Whether a program is accepted or rejected by capability verification **never depends on the optimization level** (`-O0` vs `-O2`, `INV-SEM-002`, `REQ-CAP-055`).
   - After the Verified MIR checkpoint, capability provenance and region metadata are erased (`ACAP-21`, `REQ-CAP-002`, `REQ-CAP-089..090`, `REQ-RES-149`): at runtime, `view<T>` lowers to a single thin pointer (or `(ptr, len)` scalar pair for `view<[T]>` and `Str`, `REQ-ABI-085`) with zero runtime header or reference-counting cost (`REQ-CAP-021`, `REQ-CAP-045`, `REQ-RES-148`).

---

## 2. Raw Pointer Model, Strict Provenance & Undefined Behavior Taxonomy (`AXS-UNS-010`..`016`)

### AXS-UNS-010 — Raw Pointer Types (`*const T`, `*mut T`), Representation & Non-Capability Semantics (`SPEC-04 AXS-EXT-020`, `SPEC-11 AXS-CAP-008`, `AMEM-01..08`)

1. **Types & Physical Layout**:
   - `*const T` (`TypeKind.RawPtr { mutability: Const, pointee: T, addr_space: 0 }`) and `*mut T` (`TypeKind.RawPtr { mutability: Mut, pointee: T, addr_space: 0 }`) are raw machine pointers.
   - On `x86_64` targets (`x86_64-windows`, `x86_64-linux`), `*const T` and `*mut T` for sized `T` have `size = 8` bytes and `align = 8` bytes (`usize` width).
   - Both `*const T` and `*mut T` are trivially `Copy` (`SPEC-10 AXS-OWN-003`) and have no `Drop` glue. By `SPEC-30 AXS-CONC-012`, `*const T` and `*mut T` are `!Send` and `!Share` by default so types containing raw pointers must explicitly opt in via `unsafe impl Send` / `unsafe impl Share`.
2. **Separation of Concepts (`0071 §1–8 AMEM-01..08`)**:
   - **Value $\ne$ Address $\ne$ Pointer $\ne$ View**:
     - An ordinary value `x: T` has no guaranteed physical memory address unless its address is observed via `address_of(x)`, `@addr`/`@at`, or an FFI boundary (`AMEM-01`, `AMEM-13`, `REQ-ABI-040`).
     - A raw pointer `*const T` / `*mut T` is **not** a safe capability (`AMEM-03`, `AMEM-07`, `REQ-CAP-037`, `REQ-FFI-011`, `REQ-FFI-083`, `REQ-RES-171`): it carries no compile-time lifetime proof and cannot be passed where `view<T>` or `mut_view<T>` is expected without an explicit `unsafe` conversion (`AXS-UNS-006`).
     - Taking `address_of(place)` or `address_of_mut(place)` inside `unsafe` acquires only an ephemeral capability for that expression; the resulting raw pointer holds no capability (`SPEC-11 AXS-CAP-008`, `ADR-0036 §2`), so moving or dropping the owner afterwards never triggers `AX_CAP_OUTLIVES_OWNER`.
3. **No Raw-Pointer Index Auto-Deref & Raw Store Semantics (`SPEC-03 AXS-SEM-043, AXS-SEM-047`, `ADR-0036 §1, §4`)**:
   - Raw pointers are **never** auto-dereferenced for indexing: `p[i]` on `p: *const T`, `*mut T`, `*const [N]T`, or `*mut [N]T` is rejected at compile time with `AX_TYPE_CANNOT_INDEX` (with help `write (*p)[i] or *(ptr_add(p, i)) inside unsafe`).
   - Assigning to any place whose projection chain traverses a raw-pointer dereference (`*p = v`, `p->f = v`, `(*p)[i] = v`) is a **raw store**: it overwrites the target bytes without running `Drop` on the previous memory contents (which may be uninitialized). To drop an initialized value behind `*mut T`, unsafe code must call `drop_in_place(p)` explicitly.

### AXS-UNS-011 — Strict Pointer Provenance Model (`ProvId`, `AllocId`, `Bounds`, `Permission`) (`ASAFE-43..48`, `AMEM-02`, `AMEM-05`)

Every pointer value in the Axiom abstract machine is a pair $(a, \pi)$ consisting of a 64-bit numeric machine address $a \in [0, 2^{64} - 1]$ and a **provenance** $\pi$:

$$\pi = \text{None} \;\mid\; \text{Prov}(\text{alloc\_id}: \text{AllocId},\; \text{range}: [\text{lo}, \text{hi}],\; \text{perm}: \text{Perm},\; \text{space}: \text{AddrSpace})$$

where $\text{Perm} \in \{\text{ReadOnly}, \text{ReadWrite}, \text{FnCode}, \text{FixedOverlay}, \text{FixedPlace}\}$.

1. **Provenance Creation**:
   - Every stack local (`StorageLive`), static item, constant pool allocation, heap allocation (`host.heap_alloc`), `@addr`/`@at` fixed-address declaration, and function body receives a distinct `AllocId` and initial provenance covering its byte range $[0, \text{size}]$.
   - `address_of(place)` derives provenance with $\text{perm} = \text{ReadOnly}$ (unless `place` is an `UnsafeCell` / `Atomic` / `Volatile` / `Mmio` interior-mutable region) restricted to the sub-object range of `place` (or the enclosing allocation when pointer arithmetic across sibling array elements is performed).
   - `address_of_mut(place)` requires `place` to be mutable (`let mut`, `static mut`, `mut_view` deref, or `*mut` deref) and derives provenance with $\text{perm} = \text{ReadWrite}$. Passing an immutable place to `address_of_mut(place)` emits `AX_TYPE_ASSIGN_IMMUTABLE`.
2. **Provenance Preservation & Narrowing**:
   - Pointer casts `p as *const U` and `p as *mut U` preserve the exact address $a$ and provenance $\pi$ of `p`. Casting a `*const T` with $\text{perm} = \text{ReadOnly}$ to `*mut T` is syntactically permitted, but performing a store through the resulting `*mut T` when $\pi.\text{perm} = \text{ReadOnly}$ is **Undefined Behavior** (`UB-07`, caught as `AX_UNSAFE_INTERP_UB` in `--interp`).
   - Re-deriving a raw pointer from a `view<T>` yields $\text{perm} = \text{ReadOnly}$ bounded to `sizeof(T)`; re-deriving from `mut_view<T>` yields $\text{perm} = \text{ReadWrite}$ bounded to `sizeof(T)`.
3. **Pointer $\leftrightarrow$ Integer (`usize`) Provenance Rules (`SPEC-03 AXS-SEM-060`, `ADR-0002 §5`, `ASAFE-43..44`, `REQ-CAP-126`)**:
   - Casting a pointer or function item to `usize` (`p as usize`, `address_of(v) as usize`, `addr_of(v)`, `fn_addr(f)`, `static_addr(s)`) returns the numeric address $a$ and marks the provenance $\pi$ as **exposed** in the address table (`ADR-0002 §5`).
   - Casting a `usize` integer $a$ to a pointer (`a as *const T` / `a as *mut T`) or binding `@addr(a)` / `@at(a)`:
     - If $a$ falls within a declared `@addr`/`@at` fixed-address region or matches an exposed live allocation/function address (`fn_addr`, `static_addr`, `address_of(v) as usize`), it acquires the corresponding `FixedOverlay`/`FixedPlace` or exposed allocation provenance.
     - Otherwise, `a as *const T` has $\pi = \text{None}$ (or an unmapped integer provenance): it may be compared, cast back to `usize` (`(a as *const u8) as usize == a`), or checked for null, but **dereferencing** a pointer with $\pi = \text{None}$ (or forging an integer address into an unexposed local/heap allocation) is Undefined Behavior (`UB-01` / `UB-02`, reported by `--interp` as `AX_UNSAFE_INTERP_UB`, `data.ub_kind = "invalid_provenance"`).
[0071 §6–15, §58 AMEM-02, AMEM-05, AMEM-08; tasks/0339 ASAFE-43..48; tasks/0431 ACONV-52, ACONV-54; ADR-0002 §5; REQ-CAP-126]

### AXS-UNS-012 — Pointer Arithmetic & In-Bounds Offset Rules (`ptr_add`, `ptr_sub`, `ptr_byte_add`, `ptr_diff`)

1. **Element-Scaled Arithmetic (`ptr_add`, `ptr_sub`, `p + n`, `p - n`)**:
   - For `p: *const T` or `*mut T` and `n: usize` (or signed `offset: isize` via `ptr_offset(p, offset)`), the byte delta is $\Delta = n \times \text{size\_of}::\langle T \rangle()$.
   - The resulting pointer has address $a' = (a + \Delta) \bmod 2^{64}$ and inherits the provenance $\pi$ of `p`.
   - **In-bounds precondition (`SPEC-04 AXS-EXT-102`, `ASAFE-45`)**: For `ptr_add`, `ptr_sub`, `p + n`, and `p - n`, both the starting address $a$ and the resulting address $a'$ MUST lie within the bounds $[\text{base}, \text{base} + \text{size}]$ of the live allocation identified by $\pi.\text{alloc\_id}$ (inclusive of the **one-past-the-end** address $\text{base} + \text{size}$), and the arithmetic $a + \Delta$ MUST NOT wrap around the address space.
   - Forming a one-past-the-end pointer $a' = \text{base} + \text{size}$ is valid for loop termination comparisons (`p == end_ptr`), but **dereferencing** a one-past-the-end pointer (when $\text{size\_of}::\langle T \rangle() > 0$) is Undefined Behavior (`UB-02`).
   - For Zero-Sized Types (`size_of::<T>() == 0`), any element offset produces $\Delta = 0$ and preserves $a$ and $\pi$.
2. **Byte-Granular & Wrapping Pointer Arithmetic (`ptr_byte_add`, `ptr_byte_sub`, `wrapping_add`, `wrapping_sub`)**:
   - `ptr_byte_add(p, bytes: usize)` advances `p` by `bytes` bytes (preserving provenance $\pi$ of `p` without requiring a cast through `*const u8`), subject to the same in-bounds $[\text{base}, \text{base} + \text{size}]$ requirement.
   - `p.wrapping_add(n)` / `p.wrapping_byte_add(bytes)` computes $(a + \Delta) \bmod 2^{64}$ retaining provenance $\pi$ **without** requiring intermediate addresses to stay in bounds; UB occurs only if the final pointer is dereferenced while out of bounds of $\pi$.
3. **Pointer Difference (`ptr_diff(p1, p2) -> isize`)**:
   - `ptr_diff(p1, p2)` requires `p1` and `p2` to have the same pointee type `T` (`size_of::<T>() > 0`), belong to the **same live allocation** ($\pi_1.\text{alloc\_id} == \pi_2.\text{alloc\_id}$), and have $(a_1 - a_2)$ be an exact multiple of $\text{size\_of}::\langle T \rangle()$ that fits in `isize`. Violating same-allocation provenance on `ptr_diff` is UB (`UB-02`).
[0071 §16–22, §56; tasks/0282 §5; tasks/0339 ASAFE-45; SPEC-04 AXS-EXT-102]

### AXS-UNS-013 — Alignment, Initialization & Bit-Representation Validity Invariants (`ASAFE-49..62`, `AMEM-09`)

Every typed memory access (`*p` load or store, `MakeView(p)`, `MakeMutView(p)`, `drop_in_place(p)`, `ptr_copy`, `ptr_copy_nonoverlapping`) through a raw pointer `p` of pointee type `T` with byte size $S = \text{size\_of}::\langle T \rangle()$ and alignment $A = \text{align\_of}::\langle T \rangle()$ MUST satisfy four validity invariants:

1. **Non-Null & Alignment Validity (`ASAFE-49`, `AMEM-09`, `AFFI-47`)**:
   - $a \ne 0$ and $a \bmod A == 0$, even when $S == 0$ (zero-sized accesses still require non-null aligned pointers).
   - Unaligned memory may only be accessed via `std.mem.read_unaligned(p)` / `std.mem.write_unaligned(p, val)` or through direct field access on a `@repr(packed)` struct (`SPEC-51`, `ASAFE-61..62`, `REQ-RES-134`). Taking `view(s.unaligned_field)`, `mut_view(s.unaligned_field)`, or an unaligned `*const Field` / `*mut Field` used for aligned dereference on a `@repr(packed)` struct is rejected or requires `read_unaligned`.
2. **Allocation Liveness & In-Bounds Range (`ASAFE-47..48`)**:
   - If $S > 0$, $\pi$ must reference a currently **live** allocation ($\text{state}(\pi.\text{alloc\_id}) == \text{Live}$, not `Freed` or `StorageDead`), and the byte interval $[a, a + S)$ must lie entirely within $[\text{base}, \text{base} + \text{size})$.
3. **Initialization Validity (`ASAFE-50`, `ASAFE-52..55`)**:
   - Reading `*p` as a typed value `T` (or constructing `view<T>` / `mut_view<T>` over `*p`, or calling `drop_in_place(p)`) requires every non-padding byte of `T` in $[a, a + S)$ to be in the `Init` state.
   - Reading uninitialized bytes (`Uninit`) is permitted **only** via raw byte copy intrinsics (`ptr_copy`, `ptr_copy_nonoverlapping`) into an uninitialized destination (`*mut u8` / `MaybeUninit<T>`), never by loading a typed scalar, `bool`, enum, or capability (`ASAFE-53`).
   - `Drop` runs **only** on initialized live values (`ASAFE-55`).
4. **Bit-Representation Validity (`ASAFE-51`, `ASAFE-56..60`)**:
   - Loading a value of type `T` requires the initialized bytes in $[a, a + S)$ to form a valid bit pattern of `T`:
     - `bool`: byte must be `0x00` (`false`) or `0x01` (`true`) (`SPEC-03 AXS-SEM-012`, `ASAFE-31`); any byte `0x02..=0xFF` is immediate UB (`UB-05`).
     - `char`: 32-bit word must be a valid Unicode scalar value (`0..=0xD7FF` or `0xE000..=0x10FFFF`, `SPEC-03 AXS-SEM-013`).
     - `enum`: discriminant tag bytes must match a declared variant of the `enum` (`ASAFE-30`, `REQ-FFI-033`), and the active variant's payload fields must satisfy their own validity invariants.
     - `Str`: bytes must be valid UTF-8 (`ASAFE-32`).
     - `view<T>` / `mut_view<T>` / `fn(...) -> R`: must be non-null, properly aligned, and hold valid provenance (`ASAFE-41..42`).
     - `never`: uninhabited; loading a value of type `never` is unconditional UB.
[0071 §23–30, §58 AMEM-09; tasks/0339 §15–35, ASAFE-30..33, ASAFE-47..62; SPEC-03 AXS-SEM-012..015]

### AXS-UNS-014 — Aliasing Discipline Between Raw Pointers and Safe Capabilities (`ASAFE-38`, `ASAFE-71`, `SPEC-71 AXS-ALIAS-003`)

Axiom defines a clean two-regime aliasing discipline (without requiring programmer-written `restrict` annotations, `0044 §4–5`):

1. **Safe Capability Exclusivity Regime**:
   - While a read capability `v: view<T>` is active (between its `MakeView` creation and its semantic last use, `AXS-UNS-007`), the region $R(v)$ is **read-locked**: any write to bytes overlapping $R(v)$ through a raw pointer `*mut U` (unless inside an explicit `UnsafeCell` / `Atomic` / `Volatile` / `Mmio` interior-mutable sub-region) is Undefined Behavior (`UB-06`).
   - While a mutable capability `mv: mut_view<T>` is active (between its `MakeMutView` creation and its semantic last use), the region $R(mv)$ is **uniquely locked** by `mv`: any read or write to bytes overlapping $R(mv)$ through any raw pointer or capability **not derived from `mv`** is Undefined Behavior (`UB-06`).
   - A raw pointer `p_sub = unsafe { address_of_mut(*mv) }` derived from `mv` while `mv` is active borrows from `mv` in a stacked discipline: `p_sub` may read and write $R(mv)$ until `mv` is used directly again; once `mv` is used directly again, `p_sub` is invalidated for further writes.
2. **Raw-Pointer-Only Regime (`MayAlias` Conservative Freedom)**:
   - When **no** safe `view<T>` or `mut_view<T>` is currently active over an allocation region $R$, any number of raw pointers `*const T` and `*mut T` derived from the same mutable allocation root (`let mut`, `static mut`, `heap_alloc`, `@addr`/`@at`) may alias, interleave reads and writes, and overlap freely inside `unsafe` without UB (`ASAFE-71`, `SPEC-71 AXS-ALIAS-003`).
[0044 §4–18; 0071 §12–15; tasks/0339 ASAFE-38, ASAFE-71; SPEC-71 AXS-ALIAS-003]

### AXS-UNS-015 — Canonical Undefined Behavior (UB) Catalog (`UB-01`..`UB-12`) & Optimizer Boundaries (`ASAFE-98..100`)

The complete, closed catalog of Undefined Behavior in Axiom `unsafe` code is defined by the 12 classes below. No construct outside this table is UB; operations with defined failure semantics in safe code (checked integer overflow, division by zero, shift out of range, array/slice out-of-bounds indexing, `u32 as char` failure, saturating float-to-int cast) **always panic or saturate as specified in `SPEC-03`, `SPEC-40`, and `SPEC-41`, even inside an `unsafe` block** (`ASAFE-82..83`, `ASAFE-100`).

| UB ID | Category | Exact Condition Triggering UB | Oracle `data.ub_kind` |
|---|---|---|---|
| `UB-01` | Dangling / Use-After-Free / Forged Provenance | Dereferencing a null pointer (`0x0`), a pointer with $\pi = \text{None}$ (unexposed integer cast), or a pointer whose allocation $\pi.\text{alloc\_id}$ has ended (`StorageDead` local or `heap_free`d heap block). | `"dangling_or_freed"` / `"null_deref"` / `"invalid_provenance"` |
| `UB-02` | Out-of-Bounds Pointer Offset or Access | Performing `ptr_add`/`ptr_sub`/`ptr_diff` outside $[\text{base}, \text{base} + \text{size}]$ of $\pi.\text{alloc\_id}$, or dereferencing $[a, a + \text{size\_of}::\langle T \rangle())$ not contained in $[\text{base}, \text{base} + \text{size})$. | `"out_of_bounds"` |
| `UB-03` | Misaligned Typed Access | Dereferencing `*p` (or creating `view<T>`/`mut_view<T>`) when $a \bmod \text{align\_of}::\langle T \rangle() \ne 0$ without `read_unaligned`/`write_unaligned` or `@repr(packed)` projection. | `"misaligned_access"` |
| `UB-04` | Reading Uninitialized Memory | Loading a typed value from bytes marked `Uninit` (other than padding bytes during aggregate copy or raw byte copy into uninitialized storage). | `"uninitialized_read"` |
| `UB-05` | Invalid Bit Representation | Producing a typed value `T` whose bit pattern violates `AXS-UNS-013(4)` (invalid `bool` $\notin \{0, 1\}$, non-scalar `char`, invalid enum discriminant, invalid UTF-8 in `Str`, or inhabiting `never`). | `"invalid_value_repr"` |
| `UB-06` | Capability Aliasing Violation | Writing through a raw pointer to a region locked by an active `view<T>`, or reading/writing through an unrelated raw pointer to a region locked by an active `mut_view<T>` (`AXS-UNS-014`). | `"capability_alias_violation"` |
| `UB-07` | Mutating Read-Only Memory | Writing through a `*mut T` whose provenance has $\text{perm} \in \{\text{ReadOnly}, \text{FnCode}\}$ (e.g., cast from `*const T` of an immutable `let`, `const`, string literal, or code address). | `"write_to_readonly"` |
| `UB-08` | Unsynchronized Data Race | Concurrent accesses from two execution contexts to overlapping byte locations where at least one is a write and at least one is non-atomic (or not ordered by `Happens-Before`, `SPEC-30 AXS-CONC-042`, `SPEC-31 AXS-ATM-054`). | `"data_race"` |
| `UB-09` | Overlapping `ptr_copy_nonoverlapping` | Calling `ptr_copy_nonoverlapping(src, dst, count)` when $[src, src + count \cdot S)$ and $[dst, dst + count \cdot S)$ overlap in memory. | `"overlapping_copy"` |
| `UB-10` | Invalid `Drop` / Double Destruction | Calling `drop_in_place(p)` on uninitialized or already-dropped storage, or allowing an owner to drop a second time after a raw copy of a `!Copy` value without `forget` / `ManuallyDrop` (`ASAFE-22`, `ASAFE-55`). | `"double_or_invalid_drop"` |
| `UB-11` | Invalid Function Pointer or FFI Call | Calling a function pointer whose address does not point to a valid function body, calling across an ABI/signature mismatch (`extern "C"` vs `extern "axiom"` or mismatched parameter/return ABI layout), or unwinding a foreign exception across an `extern "C"` boundary without an unwind contract (`AFFI-41..42`). | `"invalid_fn_call"` |
| `UB-12` | Violated `unsafe trait` or `@addr`/`@at` Contract | Implementing `unsafe impl Send`/`Share` for a type whose operations race in safe code, or declaring `@addr(A)` / `@at(A)` at an unmapped, misaligned, or overlapping hardware/process address. | `"invalid_fixed_addr"` |

**Optimizer Boundary Rule (`ASAFE-99..100`, `SPEC-70 AXS-OPT-032`)**: Optimization passes (`OptIR`, `LIR`, `x64`) may rely on `Certainty.Proven` facts established by the type system and capability verifier, but MUST NOT speculate trapping instructions, hoist raw-pointer loads across unknown calls or volatile/atomic barriers, or treat unknown raw-pointer aliasing as `NoAlias`.
[tasks/0339 §10–99, §100 ASAFE-20..100; SPEC-03 AXS-SEM-092; SPEC-70 AXS-OPT-032]

### AXS-UNS-016 — Oracle (`--interp`) Strict-Provenance & UB Detection Contract (`T502`, `SPEC-03 AXS-SEM-092`)

In the MIR interpreter oracle (`compiler/interp/`, `T502`):

1. **Allocation & Byte-State Shadow Table**:
   - Every allocation in the interpreter maintains:
     - `alloc_id: u32`, `base_addr: u64` (deterministic synthetic virtual address in distinct non-overlapping address ranges for stack, static, const, heap, code, and `@addr` regions), `size: usize`, `align: usize`,
     - `perm: AllocPerm` (`ReadOnly`, `ReadWrite`, `FnCode`, `Fixed`),
     - `liveness: AllocState` (`Live`, `DeadStack`, `FreedHeap`),
     - `init_mask: Vec<u8>` (1 bit per byte: `0 = Uninit`, `1 = Init`),
     - `active_caps: Vec<ActiveCapLock>` (tracking active `MakeView` read locks and `MakeMutView` exclusive locks with their originating local/region).
2. **Deterministic Verdict**:
   - Whenever an interpreted instruction violates any condition of `UB-01`..`UB-12`, the interpreter halts immediately at the offending statement's span, emits `AX_UNSAFE_INTERP_UB` (severity `error`, with `data.ub_kind` set to the string in `AXS-UNS-015`), and exits with code **`125`** (`SPEC-03 AXS-SEM-082, AXS-SEM-092`).
   - Sanitizers and oracle UB checks detect violations deterministically without altering valid program semantics (`ASAFE-98`).

---

## 3. `REQ-OWNER-008`: Address Introspection & Fixed-Address Placement (`fn_addr`, `static_addr`, `address_of`, `@addr` / `@at`) (`AXS-UNS-020`..`025`)

### AXS-UNS-020 — `REQ-OWNER-008` Overview & Canonical Address Operations (`OWNER.md REQ-OWNER-008`, `ADR-0001 §7`)

To write kernels, embedded firmware, MMIO drivers, interrupt vector tables, dynamic hooks, and low-level system tests (`OWNER.md REQ-OWNER-003, REQ-OWNER-005, REQ-OWNER-008`; `ADR-0001 §1–7`), Axiom provides first-class operations to **inspect the runtime/link-time memory address** of any function, static, or variable place and to **place or overlay** `static`, `let`, and `fn` declarations at fixed or dynamically computed memory addresses:

| Construct / Intrinsic | Operand `x` | Result Type | Requires `unsafe`? | Semantics |
|---|---|---|---|---|
| `fn_addr(f)` | Any function item (`fn`, `unsafe fn`, `extern fn`, `@addr`/`@at` fn) or `fn(...) -> R` pointer | `usize` | No (address read only) | Returns the 64-bit entry address of `f` as `usize`. |
| `static_addr(s)` | Any `static`, `static mut`, or `@addr`/`@at` static item `s` | `usize` | No (address read only) | Returns the 64-bit runtime/link-time memory address of `s` as `usize`. |
| `address_of(v)` | Any place expression `v` (`let`, `static`, `@addr`/`@at` item, `s.f`, `a[i]`, `*p`) | `*const T` | Yes (or safe when immediately cast `address_of(v) as usize`) | Returns a raw read pointer `*const T` to `v` with provenance of `v`. |
| `address_of_mut(v)` | Any mutable place expression `v` (`let mut`, `static mut`, `*p_mut`, `mv.f`) | `*mut T` | Yes | Returns a raw mutable pointer `*mut T` to `v` with `ReadWrite` provenance. |
| `address_of(v) as usize` | Any place expression `v` | `usize` | Permitted in safe or `unsafe` code | Returns the numeric `usize` memory address of place `v` (exposing provenance). |
| `addr_of(x)` | Any function item, static item, or place expression `x` | `usize` | Permitted in safe or `unsafe` code | Unified address-to-`usize` intrinsic (`ADR-0001 §7`): equivalent to `fn_addr(x)` for functions, `static_addr(x)` for statics, and `address_of(x) as usize` for places. |
| `f as usize` | Any function item `f` or function pointer `fn(...) -> R` / `extern "C" fn(...) -> R` | `usize` | No | Casts a function item or function pointer directly to its `usize` code address (`ADR-0001 §7`). |
| `p as usize` / `p as isize` | Raw pointer `p: *const T` or `*mut T` | `usize` / `isize` | No | Casts raw pointer `p` to its numeric address (`SPEC-03 AXS-SEM-060`). |
| `@addr(<expr>)` / `@at(<expr>)` | Attached to `static`, `static mut`, local `let` / `let mut`, `fn`, or `extern fn` | Item / Local binding | Accessing overlay memory requires `unsafe` (or safe after `unsafe static` / `@addr` declaration per `ADR-0001 §2`) | Places or overlays the function, static, or local variable at the address `<expr>: usize` (constant or dynamic `base + offset`). |

[OWNER.md REQ-OWNER-003, REQ-OWNER-008; ADR-0001 §1–7; T213; T500–T505]

### AXS-UNS-021 — Function Address Introspection (`fn_addr(f) -> usize`, `addr_of(f)`, `f as usize`)

1. **Accepted Operands**:
   - `fn_addr(f)` (and `addr_of(f)` or `f as usize`) accepts:
     - any module-level function item `fn foo(...) -> R` or `unsafe fn foo(...) -> R`,
     - any foreign function declaration `extern "C" fn bar(...) -> R` or `extern "system" fn ...`,
     - any fixed-address function `@addr(addr) fn isr(...)` or `@at(addr) unsafe extern "C" fn rom_fn(...)`,
     - any monomorphized generic function instance `generic_fn.<T>`,
     - any first-class function-pointer value of type `fn(...) -> R`, `unsafe fn(...) -> R`, or `extern "C" fn(...) -> R`,
     - any non-capturing closure (which decays to a function pointer per `REQ-RES-154`, `REQ-FFI-106`).
   - Passing a **capturing closure** (which carries an environment and has no single code-only entry pointer, `REQ-ABI-014`, `REQ-ABI-051`) or a non-function value to `fn_addr` is rejected at compile time with `AX_TYPE_MISMATCH`.
2. **MIR & Native Lowering (`T501`, `T502`, `T504`)**:
   - In MIR (`compiler/mir/`), `fn_addr(f)` lowers to `MirRvalue.FnAddr(FnId)` (or `MirRvalue.Cast(MirCastKind.FnPtrToInt, operand, TY_USIZE)` when `f` is a function pointer variable).
   - If `f` carries a constant `@addr(C)` / `@at(C)` attribute, `fn_addr(f)` evaluates to `C as usize` in both constant evaluation, `--interp`, and native x86-64 codegen (`MOV rax, imm64` or absolute symbol value).
   - For ordinary compiled functions on x86-64 (`T504`), `fn_addr(f)` lowers to a RIP-relative `LEA rax, [rip + sym_f]` instruction (`Rel32` relocation to `sym_f`), yielding the exact runtime virtual address of `sym_f`.
   - In the MIR oracle (`--interp`, `T502`), every function `FnId` is assigned a unique, deterministic non-zero 64-bit code address in the synthetic `.text` segment (`0x1000_0000 + 0x100 * fn_index`), or its explicit `@addr(<expr>)` value when annotated, with a bidirectional lookup table `addr <-> FnId`.
3. **Address Observability (`SPEC-73`, `SPEC-75 AXS-LTO-022`, `REQ-ABI-040`, `REQ-ABI-086`)**:
   - Invoking `fn_addr(f)`, `addr_of(f)`, or `f as usize` marks `f` with `address_taken = true`. The linker and LTO/ICF passes (`SPEC-75 AXS-LTO-022`) MUST preserve a distinct entry address for `f` when `address_taken == true`.

### AXS-UNS-022 — Static & Variable Address Introspection (`static_addr`, `address_of(v) as usize`, `addr_of(v)`)

1. **`static_addr(s) -> usize`**:
   - Accepts the path of any `static` or `static mut` item (including `@addr(<expr>)` / `@at(<expr>)` and `@thread_local` statics).
   - Passing a non-static binding (such as a local `let` variable or a function) to `static_addr` is rejected with `AX_TYPE_MISMATCH` (with help `"use address_of(v) as usize or addr_of(v) for local variables, or fn_addr(f) for functions"`).
   - Lowers in MIR to `MirRvalue.StaticAddr(SymbolId)` (or `AddressOf(Static(SymbolId))` cast to `usize`), and in native x86-64 (`T504`) to `LEA rax, [rip + sym_s]` for regular statics, `MOV rax, imm64` for constant `@addr(C)` statics, or a load from the runtime address slot `__ax_addr_slot_<s>` for dynamic `@addr(<expr>)` statics (`AXS-UNS-024`).
2. **`address_of(v)`, `address_of_mut(v)`, `address_of(v) as usize`, and `addr_of(v)`**:
   - `address_of(v)` accepts any place expression `v` of type `T`:
     - local variable `let x: T` or `let mut x: T`,
     - `@addr(<expr>) let [mut] x: T`,
     - `static S: T` or `static mut S: T`,
     - struct field `s.field` or tuple field `t.0` (provided `s` is not a `@repr(packed)` unaligned field when forming a typed pointer; byte address `addr_of(s.field)` is always valid),
     - array or slice element `arr[i]` (evaluating `i` with bounds check per `SPEC-03 AXS-SEM-042`),
     - dereference `*v_view`, `*mv_view`, or `*p_raw`.
   - Calling `address_of` on a pure rvalue temporary (`address_of(1 + 2)`) is rejected at compile time with `AX_TYPE_NOT_A_PLACE`.
   - `address_of(v) as usize` and `addr_of(v)` evaluate the address of place `v` as a `usize` integer.
   - **Escape & Storage Pinning (`SPEC-71 AXS-ESC-004`, `REQ-ABI-040`, `ASAFE-87`)**: Taking `address_of(local)`, `address_of_mut(local)`, or `addr_of(local)` sets `address_observable = true` on `local`. Consequently, `SROA` and register-only scalar promotion MUST NOT eliminate the physical stack slot (or fixed `@addr` binding) of `local`, and in native x86-64 `address_of(local)` lowers to `LEA rax, [rbp - frame_offset]` (or the bound `@addr` value for an `@addr` local).

### AXS-UNS-023 — Fixed-Address Placement Attributes `@addr(<expr>)` and `@at(<expr>)` on `static`, `let`, and `fn` (`ADR-0001 §1–4, §7`, `REQ-OWNER-003`, `REQ-OWNER-008`)

1. **Attribute Spelling & Equivalence**:
   - `@addr(<expr>)` and `@at(<expr>)` are **canonical synonyms** in `axiomc` (`T501`–`T505`, `T525`–`T529`). Both lower to the same `Placement` attribute node in HIR/THIR (`SPEC-04 AXS-EXT-032`).
   - In the frozen Stage-0 compiler (`bootstrap/axiom0`), `@at(...)` is rejected with `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` (`ADR-0001`, `ADR-0011 §3`). In self-hosted `axiomc` (`T501`+), both `@addr(<expr>)` and `@at(<expr>)` are fully supported.
2. **Supported Target Declarations (`REQ-OWNER-008`)**:
   `@addr(<expr>)` / `@at(<expr>)` may be attached to three categories of declarations:

   - **(a) `static` and `static mut` items**:
     ```axiom
     // Overlay (no initializer): binds REG to existing memory at <expr>
     @addr(0x4000_1000usize)
     static mut UART_DR: u32

     // Dynamic overlay (computed from runtime/link-time base + offset):
     let base = fn_addr(foo)
     @addr(base + 0x100)
     static mut REG: u32

     // Placement (with initializer): initializes storage at <expr>
     @addr(0x2000_0100usize)
     static mut STATUS: u32 = 0xA5A5_0001u32
     ```
     - **Overlay** (no `= init` initializer): no zero-fill or data image is emitted at link time; every read or write of `REG` accesses the memory address `<expr>` directly, and `static_addr(REG) == <expr>` and `address_of(REG) as usize == <expr>`.
     - **Placement** (with `= init` initializer): places or initializes the value `init` at address `<expr>`, and `static_addr(STATUS) == <expr>`.

   - **(b) Local `let` and `let mut` bindings**:
     ```axiom
     @addr(0x2000_0200usize)
     let mut scratch: u64 = 0xDEAD_BEEFu64

     let buf_base = address_of(backing_buf) as usize
     @addr(buf_base + 16)
     let mut header: u32 = 7u32
     ```
     - Binds the local variable `scratch` or `header` directly to the memory location at `<expr>: usize` rather than allocating a fresh stack frame slot.
     - If an initializer `= init` is present, executing the `let` statement evaluates `<expr>` to address $A$, evaluates `init`, and stores `init` at address $A$. If no initializer is present (`@addr(expr) let mut reg: u32`), the binding overlays existing memory at $A$ without writing to it.
     - Subsequent reads `header`, writes `header = 9`, capabilities `view(header)` / `mut_view(header)`, and `address_of(header) as usize` operate directly on address $A$, guaranteeing `(address_of(header) as usize) == buf_base + 16`.
     - An `@addr` local binding never runs automatic scope-exit `Drop` glue unless explicitly dropped via `drop_in_place`, because it aliases an explicit external/overlay address (`ADR-0001 §3`).

   - **(c) `fn` and `extern fn` items**:
     ```axiom
     @addr(0x2000_0000usize)
     fn isr() -> u32 {
         return 42u32
     }

     @addr(0xFFFF_0400usize)
     unsafe extern "C" fn rom_crc32(data: *const u8, len: usize) -> u32
     ```
     - For a bodyless `extern fn` (overlay): binds the callable symbol directly to the target address `<expr>`, so calling `rom_crc32(...)` performs an indirect call to `<expr>` with the declared ABI, and `fn_addr(rom_crc32) == 0xFFFF_0400usize`.
     - For a defined `fn` with a body (placement): associates the function `isr` with the placed address `<expr>` (emitted into a pinned section at VMA `<expr>` in freestanding images or registered at virtual address `<expr>` in the address table for hosted/oracle verification), guaranteeing `fn_addr(isr) == 0x2000_0000usize` while remaining directly callable.

### AXS-UNS-024 — Dynamic Address Expressions (`base + offset`) in `@addr(<expr>)` / `@at(<expr>)` (`T501`, `T502`, `T504`)

1. **Constant vs Dynamic `<expr>` Classification**:
   - The argument `<expr>` of `@addr(<expr>)` / `@at(<expr>)` must type-check as `usize` (unsuffixed integer literals unify with `usize` per `SPEC-03 AXS-SEM-020`; narrower unsigned integers in binary expressions promote to `usize` per `SPEC-40 AXS-INT-053`). If `<expr>` does not have type `usize`, `typeck` emits `AX_TYPE_MISMATCH`.
   - **Compile-time constant address (`PlacementAddr.Const(u64)`)**: `<expr>` is a constant expression (`0x2000_0000usize`, `BASE_ADDR + 0x40`). Valid at both module scope and block/function scope.
   - **Dynamic runtime address (`PlacementAddr.Dynamic(ExprId)`)**: `<expr>` depends on runtime or link-time values such as `fn_addr(foo)`, `static_addr(bar)`, `address_of(v) as usize`, local bindings (`let base = fn_addr(foo); @addr(base + 0x100) static mut REG: u32;`), or `image("mod") + offset` (`E13.7`).
2. **Scoped `static` with Dynamic `@addr(base + offset)`**:
   - To support low-level relative register and hook declarations directly inside functions or init blocks (`T500`–`T505` scope):
     ```axiom
     let base = fn_addr(foo)
     @addr(base + 0x100) static mut REG: u32
     ```
     `parser` and `hir` permit `@addr(<expr>) static [mut] NAME: T [= init]` both at module level and inside function/block bodies.
   - When `<expr>` is a dynamic expression (`PlacementAddr.Dynamic`), the compiler lowers `REG` to a hidden runtime address slot `__ax_addr_slot_REG: usize`. At the point where the `@addr(<expr>) static` declaration is executed (or in the module initializer for module-level dynamic expressions), the compiler evaluates `<expr>` and stores the resulting `usize` address into `__ax_addr_slot_REG`.
   - Every subsequent evaluation of `static_addr(REG)`, `address_of(REG)`, `address_of_mut(REG)`, `addr_of(REG)`, or direct read/write of `REG` loads the resolved address from `__ax_addr_slot_REG`.
3. **Alignment & Layout Validation (`ADR-0001 §3`)**:
   - The type `T` of an `@addr(<expr>)` `static` or `let` declaration must have a defined layout (primitive scalar, pointer, function pointer, array `[N]T`, or `@repr(C)` / `@repr(transparent)` struct/enum/union). Using a layout-unspecified default Axiom `struct` or `enum` with multiple non-zero-sized fields on an `@addr`/`@at` hardware overlay emits `AX_UNSAFE_INVALID_AT_LAYOUT` (note: primitive scalars `u8..u128`, `i8..i128`, `usize`, `isize`, `f32`, `f64`, `bool`, raw pointers, and `[N]Scalar` always have defined layout).
   - If `<expr>` is a compile-time constant $C$ and $C == 0$ or $C \bmod \text{align\_of}::\langle T \rangle() \ne 0$, the compiler rejects the declaration at compile time with `AX_UNSAFE_MISALIGNED_AT` (`data.address`, `data.required_align`).
   - If `<expr>` is dynamic, the oracle (`--interp`) and debug assertions verify $A \ne 0 \land A \bmod \text{align\_of}::\langle T \rangle() == 0$ when the address is bound (`AX_UNSAFE_INTERP_UB`, `data.ub_kind = "invalid_fixed_addr"`).

### AXS-UNS-025 — Round-Trip Address Identity & Oracle/Native Backing Store (`T501`, `T502`, `T504`, `T505`)

1. **Normative Round-Trip Identities**:
   For every valid `@addr(E)` / `@at(E)` declaration where `E` evaluates to `A: usize`:
   - Function placement/overlay `@addr(A) fn f(...)`:
     $$\text{fn\_addr}(f) == A \quad\land\quad \text{addr\_of}(f) == A \quad\land\quad (f \text{ as usize}) == A$$
   - Static placement/overlay `@addr(A) static [mut] S: T`:
     $$\text{static\_addr}(S) == A \quad\land\quad \text{addr\_of}(S) == A \quad\land\quad (\text{address\_of}(S) \text{ as usize}) == A$$
   - Local placement/overlay `@addr(A) let [mut] v: T`:
     $$\text{addr\_of}(v) == A \quad\land\quad (\text{address\_of}(v) \text{ as usize}) == A$$
2. **Backing Memory in Oracle (`--interp`, `T502`) and Hosted Native (`T504`)**:
   - In the MIR oracle (`--interp`), the simulated address space maps every `@addr(A)` / `@at(A)` static or local region $[A, A + \text{size\_of}::\langle T \rangle())$ on demand in its virtual memory map (`FixedAddrMap`), so reading and writing `REG` or `v` after `@addr(base + 0x100) static mut REG: u32` works seamlessly without host OS segfaults and satisfies `static_addr(REG) == base + 0x100`.
   - In hosted native x86-64 builds (`T504`), constant or `fn_addr`-relative `@addr(A)` overlays where $A$ is not already backed by a writable data section are mapped via an on-demand runtime fixed-address backing table (or direct pointer access when $A$ points into a live stack/static/heap buffer such as `let base = address_of_mut(buf) as usize; @addr(base + 4) let mut slot: u32`), ensuring that both address introspection (`fn_addr(isr) == 0x2000_0000usize`, `static_addr(REG) == base + 0x100`) and value reads/writes through `@addr` declarations agree 100% between `--interp` and native execution (`INV-ORACLE-002`).

---

## 4. Physical Representation, ABI Stability & Foreign Function Interface (`AXS-UNS-030`..`036`)

### AXS-UNS-030 — Separation of Type Semantics, Physical Representation & Calling Conventions (`AABI-20..70`, `REQ-ABI-005..010`, `REQ-RES-130..179`)

Axiom strictly separates **source-level type semantics** from **physical memory layout** and **machine calling conventions** (`0104 §1–10`, `0119 §215–259`, `tasks/0367 §82 AABI-20..70`):

1. **Semantic Identity $\ne$ Physical Representation (`AABI-20`, `REQ-ABI-037`, `REQ-RES-130`)**:
   - Two types with identical physical size and alignment remain distinct semantic types unless unified by typing rules. The compiler never infers semantic ownership, capability validity, or thread safety from raw byte layout (`REQ-ABI-037`, `REQ-FFI-069`).
2. **Default Axiom Layout & ABI are Compiler-Controlled (`AABI-21`, `AABI-41..42`, `REQ-ABI-005..006`, `REQ-ABI-034..035`, `REQ-ABI-047`, `REQ-ABI-058..059`, `REQ-RES-131`, `REQ-RES-139`)**:
   - Without an explicit `@repr(...)` or `extern "<abi>"` contract, `Repr.Axiom` and `CallConv.Axiom` (`extern "axiom"`) are internal to the current compilation unit and compiler version:
     - The compiler may reorder struct fields to minimize padding, select compact enum discriminant widths, and apply **niche optimizations** (such as encoding `Option<view<T>>`, `Option<mut_view<T>>`, and `Option<fn(...) -> R>` in a single pointer word using the null-pointer niche `0`, `AABI-30..31`, `REQ-ABI-042`, `REQ-RES-140..141`) without changing source-level semantics.
     - Across internal `extern "axiom"` calls, the compiler may specialize, inline, scalarize aggregates (`SROA`), pass fields in registers, and eliminate unused parameters (`REQ-ABI-006`, `REQ-ABI-034`, `REQ-ABI-043`, `REQ-ABI-047`, `REQ-ABI-058`).
3. **Move/Copy Semantics vs Physical Memory Operations (`AABI-34..37`, `REQ-ABI-054`, `REQ-ABI-089..090`, `REQ-ABI-094`, `REQ-RES-144..147`, `REQ-RES-179`)**:
   - Parameter passing and returns follow source ownership semantics (`Copy` arguments do not consume the caller place; `!Copy` arguments transfer ownership, `REQ-ABI-089..090`).
   - Source-level `Move` and `Copy` do not mandate physical `memcpy` or heap allocation (`REQ-RES-146..147`): the backend may pass values in registers or construct large return aggregates directly into a caller-allocated stack slot (`RVO`/`NRVO`/`sret`, `REQ-ABI-054`, `REQ-ABI-094`, `REQ-RES-144`) without introducing hidden heap allocations, object headers, GC, or runtime services (`AABI-70`, `REQ-RES-179`).
4. **Abstraction Erasure Before Codegen (`AABI-38..48`, `REQ-RES-148..158`, `REQ-RES-174..175`, `REQ-ABI-104`)**:
   - `view<T>` and `mut_view<T>` erase to thin pointers or `(ptr, len)` pairs (`REQ-RES-148..149`, `REQ-ABI-085`).
   - Static trait dispatch (`T: Trait`) monomorphizes to direct calls without vtables (`AABI-40..41`, `REQ-RES-150..151`); dynamic dispatch metadata (vtables) exists only when `dyn Trait` (`REQ-RES-152`) or an explicit ABI vtable struct is used.
   - Closure representation is compiler-controlled (`REQ-RES-153`): non-capturing closures decay to plain function pointers (`REQ-RES-154`), and capturing closures store their environment inline on the stack/frame by default without mandatory heap allocation (`REQ-RES-155`).
   - Deterministic `Drop` glue (`REQ-RES-156`) emits zero code for trivially destructible types (`REQ-RES-157`) and eliminates dynamic drop flags whenever initialization/move state is statically known (`REQ-RES-158`).
   - ABI-lowered MIR (`ABI MIR` / `LIR`) contains no unresolved generic parameters or unlowered semantic abstractions (`AABI-65..66`, `REQ-RES-174..175`, `REQ-ABI-104`).
5. **Padding, Semantic Equality & Wire Representation (`AABI-27..28`, `AABI-52..53`, `REQ-RES-138`, `REQ-RES-162`)**:
   - Padding bytes are unspecified (`Uninit`) and are never part of semantic equality (`Eq`, `REQ-RES-138`). In-memory representation is distinct from external wire/serialization formats (`REQ-RES-162`).
6. **Semantic Function Identity & Resolution (`REQ-ABI-073`, `REQ-ABI-086..088`)**:
   - Function identity is semantic (`FnId`, `REQ-ABI-086`), module-level function declarations resolve before body analysis regardless of lexical order (`REQ-ABI-087`), and C++-style ad-hoc function overloading by parameter types is not part of Axiom v1 (`REQ-ABI-088`). Tail-call eligibility is verified by semantic analysis and ABI lowering prior to emitting `TAIL_CALL` (`REQ-ABI-073`).

### AXS-UNS-031 — Explicit Representation Contracts: `@repr(C)` and `@repr(transparent)` (`AABI-22..24`, `AABI-45`, `AABI-47`, `AFFI-24..25`, `REQ-ABI-009`, `REQ-ABI-011`, `REQ-ABI-023`, `REQ-ABI-038`, `REQ-RES-132..134`)

1. **`@repr(C)` on Structs (`AABI-23`, `AABI-45`, `AFFI-24..25`, `REQ-ABI-009`, `REQ-ABI-038`, `REQ-FFI-076..077`, `REQ-FFI-096`, `REQ-RES-132..133`)**:
   - `@repr(C)` freezes the physical field order, offsets, padding, size, and alignment of a `struct` to match the target platform's C ABI struct layout rules:
     - Fields are placed in exact source declaration order `f_0, f_1, ..., f_{k-1}`.
     - Starting at `offset = 0`, each field $f_i$ with size $S_i$ and alignment $A_i$ is placed at $\text{offset}_i = \lceil \text{offset} / A_i \rceil \cdot A_i$, advancing $\text{offset} \gets \text{offset}_i + S_i$.
     - The struct alignment is $A = \max(\{1\} \cup \{A_i\})$, and the total struct size is $S = \lceil \text{offset} / A \rceil \cdot A$.
   - `@repr(C)` governs **data layout only**, not calling convention (`AABI-45`, `REQ-ABI-009`): an ordinary `fn f(p: Point)` taking a `@repr(C)` struct still uses the Axiom calling convention unless declared `extern "C" fn`.
   - `@repr(C)` does **not** automatically make a nested non-FFI-safe field (such as a capturing closure, `dyn Trait`, or default-layout `Repr.Axiom` struct/enum) FFI-safe (`AFFI-25`, `REQ-ABI-038`, `REQ-FFI-077`). If a `@repr(C)` struct is used in an `extern "C"` signature and contains a field whose type is not FFI-safe (`AXS-UNS-033`), `typeck` emits `AX_FFI_BAD_TYPE`.
2. **`@repr(C)` on Fieldless Enums vs Axiom Payload ADTs (`AABI-59`, `AFFI-45`, `REQ-ABI-023`, `REQ-FFI-032..033`)**:
   - Axiom payload `enum`s (tagged unions) are **not** C enums (`AABI-59`, `REQ-ABI-023`) and cannot cross `extern "C"` boundaries unless given an explicit C-compatible representation.
   - A fieldless `enum` annotated with `@repr(C)` has the layout of the target's default C `enum` underlying integer (`i32` on `x86_64-windows` and `x86_64-linux`, `size = 4, align = 4`).
   - Because C code may produce arbitrary integer values not matching any declared enum variant, receiving an untrusted enum value from C across FFI should use the raw integer type (`i32` / `u32` / `c_int`) and validate the discriminant before constructing the safe Axiom `enum` (`ASAFE-30`, `REQ-FFI-033`).
3. **`@repr(transparent)` (`AABI-24`, `AABI-47`, `AABI-49`, `REQ-ABI-011`, `T504`)**:
   - `@repr(transparent)` may be applied to a `struct` that has **at most one field with non-zero size** (`size > 0`) and any number of zero-sized fields (`size == 0`, `align == 1`, such as `PhantomData<T>` or `()`).
   - Applying `@repr(transparent)` to an `enum`, a `union`, or a `struct` with two or more non-zero-sized fields (or a zero-sized field with `align > 1`) is rejected at compile time with `AX_FFI_INVALID_TRANSPARENT`.
   - A `@repr(transparent)` struct `Wrapper(Inner)` is guaranteed to have the **exact same physical size, alignment, memory layout, and `extern "C"` / `Win64` / `SysV64` register/stack parameter and return passing ABI** as `Inner` (for example, `@repr(transparent) struct Millimeters(f64)` is passed and returned in `XMM0` just like `f64`, and `@repr(transparent) struct NonNullPtr(*mut u8)` is passed in `RCX` just like `*mut u8`), while remaining a distinct type in `typeck` (`REQ-ABI-011`).

### AXS-UNS-032 — Explicit ABI Stability, Visibility Independence, Symbol Export & `@abi(stable)` Contracts (`AABI-43..66`, `REQ-ABI-007..008`, `REQ-ABI-014..027`, `REQ-ABI-030`, `REQ-ABI-039`, `REQ-ABI-049`, `REQ-ABI-051..068`, `REQ-ABI-092..101`)

1. **`pub` Visibility $\ne$ Binary Export $\ne$ ABI Stability (`AABI-44`, `AABI-54..58`, `REQ-ABI-008`, `REQ-ABI-018..019`, `REQ-ABI-039`, `REQ-ABI-049`, `REQ-ABI-097`, `REQ-FFI-103`)**:
   - `pub` controls only module/package source visibility during name resolution (`SPEC-02 §4`).
   - Emitting an unmangled or externally visible symbol into a DLL/shared object or object export table requires an explicit `@export` or `@export("custom_sym")` attribute (`SPEC-04 AXS-EXT-032, AXS-EXT-072`), and its binary contract is governed by its declared ABI (`extern "C"`, `extern "system"`, or `@abi(stable)`).
2. **Types Forbidden at Stable / Foreign ABI Boundaries (`AABI-50..53`, `REQ-ABI-014..017`, `REQ-ABI-051`, `REQ-ABI-053`, `REQ-ABI-066..068`, `REQ-ABI-092`, `REQ-FFI-059`, `REQ-FFI-104`)**:
   - Uninstantiated generic functions (`fn foo<T>(x: T)`) cannot be exported directly with `extern "C"` or `@export` (`AX_FFI_GENERIC_EXPORT`, `REQ-ABI-016`, `REQ-ABI-053`, `REQ-ABI-067`, `REQ-ABI-092`, `REQ-FFI-059`, `REQ-FFI-104`); only concrete monomorphic wrappers or type-erased handle interfaces (`REQ-ABI-017`) may cross a stable binary boundary.
   - Capturing closures (`Closure`, `REQ-ABI-014`, `REQ-ABI-051`), trait objects (`dyn Trait`, `REQ-ABI-015`, `REQ-ABI-066`, `REQ-ABI-068`), and layout-unspecified `Repr.Axiom` structs/enums (`REQ-ABI-023`) are rejected on `extern "C"` and `@abi(stable)` signatures with `AX_FFI_BAD_TYPE`.
3. **`@abi(stable)` / `@abi("axiom-stable-1")` Contract (`AABI-43`, `AABI-56..66`, `REQ-ABI-007`, `REQ-ABI-020..027`, `REQ-ABI-030`, `REQ-ABI-060`, `REQ-ABI-099`, `REQ-ABI-101`, `REQ-FFI-056`, `REQ-FFI-062`)**:
   - Items annotated with `@abi(stable)` (canonical shorthand for `@abi("axiom-stable-1")`) commit to a versioned, compiler-checked binary interface:
     - Every parameter and return type of an `@abi(stable)` function must be a primitive scalar (`i8..i128`, `u8..u128`, `isize`, `usize`, `f32`, `f64`, `bool`, `char`, `()`), a raw pointer `*const T` / `*mut T`, an `extern "C"` / `@abi(stable)` function pointer, a `@repr(C)` or `@repr(transparent)` aggregate of `@abi(stable)`-safe fields, or an opaque handle (`REQ-ABI-099`); otherwise `typeck` emits `AX_FFI_BAD_TYPE`.
     - Containers crossing `@abi(stable)` must explicitly specify their allocator/ownership transfer contract (`REQ-ABI-020`), and extensible ABI structs use explicit `version: u32, size: u32` header contracts (`REQ-ABI-021..022`, `REQ-FFI-054`).
     - `@abi(stable)` symbols carry versioned ABI fingerprints (`REQ-ABI-024..025`, `REQ-ABI-101`) and emit machine-readable ABI descriptors (`.axabi` / `--emit=abi`, `REQ-ABI-026..027`, `REQ-FFI-053`, `REQ-FFI-108`, `REQ-FFI-115`) without exposing internal compiler HIR/MIR data structures (`AABI-66`, `REQ-ABI-030`).

### AXS-UNS-033 — Foreign Function Interface (`extern "C"`, `extern "system"`), Target C Types & Opaque Foreign Types (`AFFI-20..35`, `REQ-ABI-010`, `REQ-ABI-045..050`, `REQ-FFI-016..040`, `REQ-FFI-068..126`)

1. **Explicit Calling Conventions (`AFFI-20..22`, `REQ-ABI-010`, `REQ-ABI-045`, `REQ-ABI-048`, `REQ-ABI-050`, `REQ-ABI-062`, `REQ-FFI-022`, `REQ-FFI-063`, `REQ-FFI-070..074`, `REQ-FFI-123`, `REQ-FFI-126`)**:
   - Every `extern "<abi>"` block and `extern "<abi>" fn` declaration or function pointer type carries an explicit ABI tag (`CallConv`):
     - `"axiom"` (default when `extern` is omitted): internal Axiom calling convention.
     - `"C"`: target platform C ABI (`Win64` on `x86_64-windows`, `SysV64` on `x86_64-linux`).
     - `"system"`: target OS system-call / Win32 API convention (identical to `"C"` / `Win64` on 64-bit Windows and Linux; `stdcall` on 32-bit x86).
   - Any unknown ABI string (`extern "pascal"`) is rejected at compile time with `AX_FFI_UNKNOWN_ABI` (`data.abi`).
   - Function pointers `fn(A) -> R` and `extern "C" fn(A) -> R` have distinct types (`REQ-ABI-050`); passing an `extern "axiom" fn` where `extern "C" fn` is required (without a non-capturing closure/item coercion generated with a C ABI entry) emits `AX_TYPE_MISMATCH` (`REQ-ABI-062`).
2. **FFI-Safe Type Matrix (`AFFI-23`, `REQ-ABI-028`, `REQ-FFI-075`)**:
   A type `T` is **FFI-safe** for `extern "C"` / `extern "system"` parameter and return positions if and only if `T` is one of:
   - Fixed-width integers `i8`, `i16`, `i32`, `i64`, `isize`, `u8`, `u16`, `u32`, `u64`, `usize` (and `i128`/`u128` via target 16-byte register-pair/pointer convention, `SPEC-40 AXS-INT-011`),
   - IEEE-754 floats `f32`, `f64` (`SPEC-41 AXS-FLT-041`),
   - `bool` (`1` byte, `0` or `1`), `()`, or `never` (return position only),
   - Raw pointers `*const U` and `*mut U` (where `U` may be any sized type or an opaque foreign type; note that `*const U` / `*mut U` is nullable at the machine level, while non-null pointer wrappers use `@repr(transparent)` or `Option<NonNull<U>>`, `AFFI-30`, `REQ-FFI-082`),
   - Function pointers `extern "C" fn(...) -> R` and `extern "system" fn(...) -> R` (and `Option<extern "C" fn(...) -> R>` via null-pointer niche),
   - `@repr(C)` structs/unions and `@repr(transparent)` wrappers whose non-ZST fields are recursively FFI-safe (`AXS-UNS-031`),
   - `@repr(C)` or `@repr(Int)` fieldless enums.
   Passing `Str`, `String`, `Vec<T>`, `view<T>`, `mut_view<T>`, `Slice` `[T]`, `[N]T` by value (C arrays decay to pointers in C signatures!), `Closure`, `dyn Trait`, or a default `Repr.Axiom` struct/enum directly across `extern "C"` emits `AX_FFI_BAD_TYPE` (`data.ty`).
3. **Target C Type Aliases (`std.ffi.c`, `REQ-FFI-016`, `REQ-FFI-030`)**:
   - Because C integer widths (`long`, `char` signedness) vary by target (`LLP64` on 64-bit Windows vs `LP64` on 64-bit Linux), Axiom never hardcodes a single global width for C `long` (`REQ-FFI-030`). Instead, `std.ffi.c` defines target-resolved aliases:
     - `c_char = i8`, `c_schar = i8`, `c_uchar = u8`, `c_short = i16`, `c_ushort = u16`, `c_int = i32`, `c_uint = u32`,
     - `c_long = i32` (`x86_64-windows` LLP64) / `i64` (`x86_64-linux` LP64), `c_ulong = u32` (Win64) / `u64` (Linux),
     - `c_longlong = i64`, `c_ulonglong = u64`, `c_size_t = usize`, `c_ssize_t = isize`, `c_float = f32`, `c_double = f64`,
     - `c_void` (opaque void pointee for `*const c_void` / `*mut c_void`).
4. **C Strings, Foreign Ownership & Opaque Foreign Types (`AFFI-26..31`, `AFFI-48..50`, `REQ-ABI-013`, `REQ-FFI-025..028`, `REQ-FFI-039..040`, `REQ-FFI-057`, `REQ-FFI-079..083`, `REQ-FFI-100..102`, `REQ-RES-167..169`, `REQ-RES-171`)**:
   - Axiom strings (`Str`, `String`) never implicitly convert to `*const c_char` (`AFFI-29`, `REQ-FFI-081`); foreign NUL-terminated strings are borrowed via `CStr` or owned via `CString` (`REQ-FFI-039`).
   - Raw pointers returned from or passed to C do **not** implicitly transfer Axiom ownership or create safe `view<T>` capabilities (`REQ-ABI-013`, `REQ-FFI-011`, `REQ-FFI-028`, `REQ-FFI-079`, `REQ-FFI-083`, `REQ-RES-171`). Memory allocated by a foreign allocator (`malloc`, `VirtualAlloc`, `CoTaskMemAlloc`) belongs to that foreign allocation domain and must be freed by its matching foreign deallocator wrapped in a dedicated RAII owner type (`AFFI-27..28`, `AFFI-48`, `REQ-FFI-057`, `REQ-FFI-100`, `REQ-RES-167`), and cannot be unmapped while dependent safe capabilities remain live (`AFFI-49..50`, `REQ-FFI-101..102`).
   - **Opaque foreign types**: Declaring `extern type Sqlite3;` inside an `extern "C"` block (or `@repr(C) pub struct Sqlite3 { _opaque: [0]u8 }`) defines an opaque foreign type (`AABI-48`, `AFFI-26`). Taking `*const Sqlite3` or `*mut Sqlite3` is valid, whereas constructing `Sqlite3` by value, querying `size_of::<Sqlite3>()`, or passing `Sqlite3` by value in a function signature is rejected with `AX_FFI_OPAQUE_BY_VALUE`.

### AXS-UNS-034 — Foreign Callbacks, Closure Decay & Reentrancy Contracts (`AFFI-38..42`, `AFFI-53..55`, `REQ-ABI-014`, `REQ-ABI-051`, `REQ-ABI-057`, `REQ-FFI-007`, `REQ-FFI-012`, `REQ-FFI-021`, `REQ-FFI-034..037`, `REQ-FFI-049..052`, `REQ-FFI-060`, `REQ-FFI-090..092`, `REQ-FFI-105..107`, `REQ-FFI-122`)

1. **`extern "C" fn` Callback Pointers (`REQ-ABI-057`, `REQ-FFI-034`)**:
   - Any top-level Axiom function declared `extern "C" fn cb(a: i32, ctx: *mut u8) -> i32` (or `unsafe extern "C" fn`) is compiled with a native target C ABI prologue/epilogue (preserving all callee-saved GPRs `RBX`, `RBP`, `RDI`, `RSI`, `R12`–`R15` and `XMM6`–`XMM15` on Win64) and may be passed as a function pointer to C libraries and invoked directly by C code (`T503`, `T504`).
   - Reentrant C -> Axiom -> C -> Axiom callback chains are supported without requiring any global runtime lock or hidden global constructor (`REQ-FFI-049..052`).
2. **Non-Capturing vs Capturing Closures (`AFFI-53..54`, `REQ-ABI-014`, `REQ-ABI-051`, `REQ-FFI-007`, `REQ-FFI-012`, `REQ-FFI-021`, `REQ-FFI-105..106`, `REQ-FFI-122`, `REQ-RES-154`)**:
   - A **non-capturing** closure (`|x: i32| -> i32 { x * 2 }`, with empty capture set) may coerce to `fn(i32) -> i32` or `extern "C" fn(i32) -> i32` when the expected type specifies that signature; the compiler synthesizes a stateless C-ABI entry thunk with zero heap allocation.
   - A **capturing** closure (`|x: i32| -> i32 { x + offset }`) carries a closure environment and **cannot** coerce or cast to `extern "C" fn(...)` (`AX_FFI_CAPTURING_CLOSURE_CALLBACK`). C APIs accepting stateful callbacks must use an explicit `(callback: extern "C" fn(*mut u8, ...), userdata: *mut u8)` adapter (`REQ-FFI-021`, `REQ-FFI-035`), where the caller keeps the environment alive for the full retention duration (`AFFI-38`, `REQ-FFI-036`, `REQ-FFI-060`, `REQ-FFI-090`) and requires `Send`/`Share` bounds if the foreign library may invoke the callback on another OS thread (`AFFI-39`, `REQ-FFI-037`, `REQ-FFI-091`). Foreign async completion callbacks require explicit `Waker`/`Future` adapters (`AFFI-40`, `REQ-FFI-092`).

### AXS-UNS-035 — Conservative Foreign-Call Modeling & Oracle Boundary (`AABI-65`, `AFFI-32..37`, `ADR-0002 §4`, `REQ-ABI-029`, `REQ-FFI-014`, `REQ-FFI-046..048`, `REQ-FFI-064..128`, `REQ-RES-172`)

1. **Default Conservative Effect & Alias Summary (`AABI-65`, `AFFI-32..33`, `REQ-ABI-029`, `REQ-FFI-014`, `REQ-FFI-048`, `REQ-FFI-064`, `REQ-FFI-067`, `REQ-FFI-084..085`, `REQ-FFI-113..114`, `REQ-FFI-128`, `REQ-RES-172`)**:
   - Unless an explicit, verified FFI contract attribute (`@ffi_pure`, `@ffi_readonly`, `@ffi_noescape`) is attached to a trusted declaration, the compiler models every `extern` function call conservatively:
     - **Effects**: `EffectSet = { Read, Write, Foreign, IO, MayTrap }`. Dead-code elimination (`DCE`), common subexpression elimination (`CSE`), and loop-invariant code motion (`LICM`) MUST NOT eliminate, deduplicate, or hoist unknown `extern` calls (`SPEC-70 AXS-OPT-021`).
     - **Aliasing & Escape**: Any pointer argument `*const T` or `*mut T` passed to an unannotated `extern` call is treated as `MayAlias` (`AFFI-33`, `REQ-FFI-085`) and `GlobalEscape` (`SPEC-71 AXS-ESC-003`).
     - **Synchronization**: Foreign calls do not implicitly establish atomic `Happens-Before` synchronization unless contracted (`AATOM-37`, `REQ-FFI-014`).
     - **Representation Freeze (`REQ-FFI-046..047`, `REQ-RES-178`)**: Optimizer passes may optimize freely before and after the FFI call, but the physical layout and register/stack representation at the `extern` call boundary are frozen by the target ABI and never weaken safe-code invariants.
2. **Oracle Behavior on Direct Foreign Calls (`ADR-0002 §4`, `spec/diagnostics.md §11`)**:
   - Under `--interp`, calls to compiler/OS host intrinsics (`host.*` in `std/core/host.ax`, `SPEC-04 AXS-EXT-110`) execute through the deterministic oracle host layer (`INV-ORACLE-003`).
   - Reaching a direct user `extern "C"` call to a native DLL/library symbol that has no Axiom body in `--interp` halts the interpreter and reports `AX_FFI_NOT_IN_ORACLE` (`data.symbol`), whereas `@addr`/`@at` functions with an Axiom body (or simulated oracle hook) execute normally in `--interp`.

### AXS-UNS-036 — Target ABI Lowering (`Win64` & `SysV64`) & Mandatory External Windows x64 ABI Oracle (`ADR-0034 §8 / OI-12`, `T503`, `T504`, `REQ-ABI-069..085`, `REQ-RES-142..143`)

1. **Deterministic Pre-Backend ABI Lowering (`ALIR-25..26`, `AX86-24..25`, `REQ-ABI-069..075`, `REQ-ABI-079..085`, `REQ-RES-142..143`, `REQ-RES-164..166`, `REQ-RES-176..177`)**:
   - ABI classification (`abi_class`) is distinct from general register allocation (`REQ-RES-164`) and is computed deterministically in `compiler/abi/` and `compiler/lir/` (`REQ-ABI-069..071`, `REQ-ABI-081`) while preserving source debug spans (`REQ-RES-176`) and target-independent Axiom semantics (`REQ-RES-177`).
   - Caller-saved and callee-saved register sets are read from `TargetDesc` metadata (`REQ-ABI-082`, `SPEC-04 AXS-EXT-060`).
2. **Windows x64 (`Win64`, `x86_64-windows`) Complete Parameter & Return Rules (`0181`, `T503`, `T504`)**:
   - **Positional Slots `0..3`**:
     - Integer/pointer arguments (and by-value aggregates of size `1, 2, 4, 8` bytes) in slots `0, 1, 2, 3` use `RCX`, `RDX`, `R8`, `R9`.
     - Scalar floating-point arguments (`f32`, `f64`, and `@repr(transparent)` wrappers around them) in slots `0, 1, 2, 3` use `XMM0`, `XMM1`, `XMM2`, `XMM3` (`SPEC-41 AXS-FLT-041`).
     - Arguments at positional index $k \ge 4$ are passed in 8-byte stack slots at `[RSP + 8 * k]` above the mandatory **32-byte shadow space ("home space")** `[RSP + 0 .. RSP + 24]`.
     - Stack pointer `RSP` is 16-byte aligned before every `CALL` instruction (`RSP % 16 == 0` prior to pushing the 8-byte return address).
   - **Aggregate (`@repr(C)` Struct) By-Value Passing & Return by Size (`1, 2, 3, 4, 8, 12, 16, 24` bytes)**:

     | `@repr(C)` Struct Size (bytes) | Win64 Parameter Passing (`extern "C"`) | Win64 Return Value (`extern "C"`) |
     |---|---|---|
     | `1` byte | Passed directly in low 8 bits of slot GPR (`CL`/`DL`/`R8B`/`R9B`) or 8-byte stack slot | Returned in `AL` (`RAX[7:0]`) |
     | `2` bytes | Passed directly in low 16 bits of slot GPR (`CX`/`DX`/`R8W`/`R9W`) or 8-byte stack slot | Returned in `AX` (`RAX[15:0]`) |
     | `4` bytes | Passed directly in low 32 bits of slot GPR (`ECX`/`EDX`/`R8D`/`R9D`) or 8-byte stack slot | Returned in `EAX` (`RAX[31:0]`) |
     | `8` bytes | Passed directly in 64-bit slot GPR (`RCX`/`RDX`/`R8`/`R9`) or 8-byte stack slot | Returned in `RAX` (`RAX[63:0]`) |
     | **`3`, `5`, `6`, `7` bytes** (non-power-of-two $< 8$) | Caller copies struct into a caller-allocated aligned stack temporary and passes the **64-bit pointer** to that copy in the slot GPR/stack | Caller allocates return slot on stack, passes hidden **`sret` pointer in `RCX`** (shifting explicit args to `RDX`, `R8`, `R9`, stack), callee writes struct to `*sret` and returns `sret` in `RAX` |
     | **`12`, `16`, `24`, `> 8` bytes** | Caller copies struct into a 16-byte-aligned caller stack temporary and passes the **64-bit pointer** in the slot GPR/stack | Hidden **`sret` pointer in `RCX`** (explicit args shifted by 1 slot); callee writes to `*sret` and returns `sret` in `RAX` |

3. **Linux x86-64 (`SysV64`, `x86_64-linux`) Reference Contract (`REQ-ABI-076..077`, `E16.9`)**:
   - Under the System V AMD64 ABI (`SPEC-04 AXS-EXT-052`), the first six integer/pointer arguments are passed in `RDI`, `RSI`, `RDX`, `RCX`, `R8`, `R9` and returned in `RAX` (`RDX` secondary eightbyte), while floating-point arguments start in `XMM0`–`XMM7` and return in `XMM0` (`XMM1` secondary).
4. **Mandatory External Windows x64 ABI Oracle (`ADR-0034 §8 / OI-12`, `T503`)**:
   - To guarantee that `axiomc` does not merely agree with itself on Windows x64 FFI (`ADR-0034 §1, §7, §8`), `T503` (`tests/ffi/win64_abi_oracle`) MUST verify `axiomc` natively against an external C shared library compiled with `gcc -shared`:
     1. **Mixed 1..8 Argument Matrix**: Exported C DLL functions taking 1 through 8 arguments mixing `i8`, `u16`, `i32`, `u64`, `f32`, `f64`, and `*const u8` across register slots `0..3` and stack slots `4..7`, called from Axiom via `@link` and returning a checksum verified against exact expected values.
     2. **Aggregate By-Value & Return Matrix (`1, 2, 3, 4, 8, 12, 16, 24` bytes)**: Exported C DLL functions accepting and returning `@repr(C)` structs of exact sizes **1, 2, 3, 4, 8, 12, 16, and 24 bytes** by value (testing both register-packed `1/2/4/8`-byte structs and indirect/pointer/`sret` `3/12/16/24`-byte structs).
     3. **Bidirectional Callback Verification**: Exported C DLL higher-order function invoking an Axiom `extern "C" fn` callback with mixed scalars and structs.
     4. **`offsetof` / `sizeof` / `_Alignof` Layout Oracle**: A C driver compiled by `gcc` that compares `sizeof(S)`, `_Alignof(S)`, and `offsetof(S, field)` for mixed-width `@repr(C)` structs against Axiom's `size_of::<S>()`, `align_of::<S>()`, and `addr_of(s.field) - addr_of(s)`.
     5. **`NDEBUG`-Safe C Driver Audit**: All C ABI test drivers in `tests/mc/isel/cdriver_abi*.c` and `tests/ffi/win64_abi_oracle/` MUST use explicit `if (actual != expected) return 1;` checks and contain zero `assert(...)` calls that could be stripped under `-DNDEBUG`.

---

## 5. Diagnostics, Canonical Examples & Requirement Traceability (`AXS-UNS-050`..`054`)

### AXS-UNS-050 — Diagnostic Codes Owned or Referenced by `SPEC-50`

| Code | Area | Sev | Emit Condition & Normative Rule |
|---|---|---|---|
| `AX_UNSAFE_REQUIRED` | `UNSAFE` | `error` | Performing a raw-pointer dereference (`*p`, `p->f`, `(*p)[i]`), pointer offset (`ptr_add`, `ptr_sub`, `p + n`), `address_of` / `address_of_mut`, `unsafe fn` call, unannotated `extern` call, or `static mut` access outside an `unsafe` context (`AXS-UNS-002`). |
| `AX_UNSAFE_TRAIT_IMPL` | `UNSAFE` | `error` | Implementing an `unsafe trait` without the `unsafe impl` modifier (`AXS-UNS-005`; `Send`/`Share` use `AX_CONC_SAFE_IMPL_MARKER` per `SPEC-30 AXS-CONC-018`). |
| `AX_UNSAFE_UNNECESSARY_IMPL` | `UNSAFE` | `error` | Writing `unsafe impl Trait for T` when `Trait` is not declared `unsafe trait` (`AXS-UNS-005`). |
| `AX_UNSAFE_INTERP_UB` | `UNSAFE` | `error` | MIR interpreter (`--interp`) detected Undefined Behavior (`UB-01`..`UB-12`: dangling/freed pointer, forged provenance, out-of-bounds offset/access, misaligned access, uninitialized read, invalid bit pattern, capability aliasing violation, write to read-only memory, data race, overlapping `ptr_copy_nonoverlapping`, double drop, or invalid `@addr`); exits with code `125` (`AXS-UNS-015..016`). |
| `AX_UNSAFE_AT_HOSTED` | `UNSAFE` | `error` | Fixed-address `@at` / `@addr` placement (emitting a pinned VMA section) used in the `hosted` profile where the target linker cannot pin arbitrary raw hardware VMAs (`ADR-0001 §3`, `ADR-0011 §3`). |
| `AX_UNSAFE_MISALIGNED_AT` | `UNSAFE` | `error` | `@addr(<expr>)` / `@at(<expr>)` specifies a null (`0`) or misaligned address for the target type's alignment (`AXS-UNS-024`). |
| `AX_UNSAFE_INVALID_AT_LAYOUT` | `UNSAFE` | `error` | `@addr(<expr>)` / `@at(<expr>)` applied to a composite type whose layout is not defined (`Repr.Axiom` multi-field struct/enum without `@repr(C)` or `@repr(transparent)`, `AXS-UNS-024`). |
| `AX_FFI_NOT_IN_ORACLE` | `FFI` | `error` | MIR interpreter (`--interp`) reached a direct foreign `extern` function call with no oracle host intrinsic or Axiom body (`AXS-UNS-035`, `ADR-0002 §4`). |
| `AX_FFI_UNKNOWN_ABI` | `FFI` | `error` | Unknown ABI string in `extern "<abi>"` (`AXS-UNS-033`). |
| `AX_FFI_BAD_TYPE` | `FFI` | `error` | Non-FFI-safe type (`Str`, `String`, `Vec`, `view`, `mut_view`, `[N]T` by value, `Closure`, `dyn Trait`, or `Repr.Axiom` struct/enum) used in an `extern "C"`, `extern "system"`, or `@abi(stable)` signature or `@repr(C)` FFI boundary (`AXS-UNS-031..033`). |
| `AX_FFI_INVALID_TRANSPARENT` | `FFI` | `error` | `@repr(transparent)` applied to a non-struct or a struct without exactly one non-zero-sized field (or with a ZST field of alignment $> 1$) (`AXS-UNS-031`). |
| `AX_FFI_OPAQUE_BY_VALUE` | `FFI` | `error` | Opaque foreign type (`extern type T`) instantiated, queried for `size_of`, or passed/returned by value instead of behind `*const T` / `*mut T` (`AXS-UNS-033`). |
| `AX_FFI_GENERIC_EXPORT` | `FFI` | `error` | Generic function exported directly with `extern "C"` or `@export` without concrete monomorphization (`AXS-UNS-032`). |
| `AX_FFI_CAPTURING_CLOSURE_CALLBACK` | `FFI` | `error` | Attempting to coerce or cast a capturing closure to an `extern "C" fn` pointer (`AXS-UNS-034`). |
| `AX_FFI_VARIADIC_NOT_EXTERN_C` | `FFI` | `error` | Variadic parameter `...` used on a non-`extern "C"` function declaration (`AXS-UNS-033`). |
| `AX_TYPE_CANNOT_INDEX` | `TYPE` | `error` | Indexing `p[i]` directly on a raw pointer `*const T` / `*mut T` / `*const [N]T` / `*mut [N]T` (`SPEC-03 AXS-SEM-047`, `AXS-UNS-010`). |
| `AX_TYPE_ASSIGN_IMMUTABLE` | `TYPE` | `error` | Mutating through `*p` when `p: *const T`, taking `address_of_mut(imm)` on an immutable binding, or mutating through an immutable `view<T>` (`AXS-UNS-011`). |
| `AX_CAP_CONFLICT_MUT` | `CAP` | `error` | Overlapping `READ + WRITE` or `WRITE + WRITE` capabilities (including `UNKNOWN` overlap or capabilities constructed via `MakeView`/`MakeMutView` inside `unsafe`) (`AXS-UNS-006..007`). |
| `AX_CAP_OUTLIVES_OWNER` | `CAP` | `error` | A `view<T>` or `mut_view<T>` escapes the lifetime of its owner, lock guard, or mapped region (`AXS-UNS-006..007`). |

### AXS-UNS-051 — Canonical Positive Examples (`=` and `.` Syntax)

#### Example 1 — `REQ-OWNER-008` Address Introspection (`fn_addr`, `static_addr`, `address_of(v) as usize`) & `@addr(<expr>)` Round-Trip
```axiom
module demo.unsafe_addr

static GLOBAL_CFG: u32 = 0x1234_5678u32

fn helper(x: u32) -> u32 {
    return x + 1u32
}

// Fixed-address function placement / binding (REQ-OWNER-008)
@addr(0x2000_0000usize)
fn isr() -> u32 {
    return 0xAA55u32
}

pub fn verify_req_owner_008() -> i32 {
    // 1. Round-trip verification on @addr function:
    let isr_a: usize = fn_addr(isr)
    assert(isr_a == 0x2000_0000usize)
    assert(addr_of(isr) == 0x2000_0000usize)
    assert((isr as usize) == 0x2000_0000usize)

    // 2. Function and static address introspection:
    let base: usize = fn_addr(helper)
    let cfg_a: usize = static_addr(GLOBAL_CFG)
    assert(base != 0usize)
    assert(cfg_a != 0usize)
    assert(( unsafe { address_of(GLOBAL_CFG) } as usize ) == cfg_a)

    // 3. Dynamic @addr(base + 0x100) on static mut (REQ-OWNER-008):
    @addr(base + 0x100usize)
    static mut REG: u32

    assert(static_addr(REG) == base + 0x100usize)
    assert(( unsafe { address_of(REG) } as usize ) == base + 0x100usize)
    unsafe {
        REG = 0xCAFE_BABEu32
        assert(REG == 0xCAFE_BABEu32)
    }

    // 4. Local variable address introspection and @addr(expr) local overlay:
    let mut local_buf: [4]u32 = [10u32, 20u32, 30u32, 40u32]
    let buf_addr: usize = unsafe { address_of_mut(local_buf) } as usize
    @addr(buf_addr + 8usize)
    let mut aliased_elem: u32 = 99u32

    assert(( unsafe { address_of(aliased_elem) } as usize ) == buf_addr + 8usize)
    assert(local_buf[2] == 99u32)
    return 0
}
```

#### Example 2 — Raw-Pointer-to-View Boundary (`MakeView` / `MakeMutView`) & FFI `@repr(C)` / `@repr(transparent)` Interop
```axiom
module demo.ffi_boundary

@repr(C)
pub struct CSliceHeader {
    pub ptr: *mut u32,
    pub len: usize,
}

@repr(transparent)
pub struct DeviceId {
    pub raw: u32,
}

@link("c_test_dll")
extern "C" {
    fn c_accumulate(id: DeviceId, hdr: CSliceHeader, cb: extern "C" fn(u32) -> u32) -> u32
}

extern "C" fn double_item(x: u32) -> u32 {
    return x * 2u32
}

pub fn safe_process_buffer(buf: mut_view<[4]u32>) -> u32 {
    // Re-establish a safe capability from a validated raw pointer inside unsafe:
    let p: *mut u32 = unsafe { address_of_mut(buf[0]) }
    let v: view<u32> = unsafe { view_from_raw(p) }
    let first_val: u32 = *v // last use of `v`; read lock ends here (AXS-UNS-007)

    let hdr = CSliceHeader { ptr: p, len: 4usize }
    let dev = DeviceId { raw: 7u32 }
    let res = unsafe { c_accumulate(dev, hdr, double_item) }
    return first_val + res
}
```

### AXS-UNS-052 — Canonical Negative Examples (`=` and `.` Syntax)

```axiom
module demo.unsafe_rejected

trait SafeTrait {
    fn compute(self: view<Self>) -> i32
}

unsafe trait TrustedMarker {}

struct Handle {
    ptr: *mut i32,
}

// ERROR [AX_UNSAFE_TRAIT_IMPL]: implementing `unsafe trait TrustedMarker` requires `unsafe impl` (AXS-UNS-005)
impl TrustedMarker for Handle {}

// ERROR [AX_UNSAFE_UNNECESSARY_IMPL]: `SafeTrait` is not an `unsafe trait` (AXS-UNS-005)
unsafe impl SafeTrait for Handle {
    fn compute(self: view<Handle>) -> i32 { return 0 }
}

// ERROR [AX_FFI_INVALID_TRANSPARENT]: `@repr(transparent)` requires exactly one non-zero-sized field (AXS-UNS-031)
@repr(transparent)
struct BadTransparent {
    a: u32,
    b: u32,
}

extern "C" {
    // ERROR [AX_FFI_BAD_TYPE]: `Str` and `view<i32>` are not C-ABI safe types; use `*const u8` + `usize` or `@repr(C)` (AXS-UNS-033)
    fn bad_ffi_sig(s: Str, v: view<i32>) -> i32
}

fn rejected_unsafe_and_cap_cases(p: *mut [2]i32, raw_i32: *mut i32) -> i32 {
    // ERROR [AX_UNSAFE_REQUIRED]: raw pointer dereference outside `unsafe` block (AXS-UNS-002)
    let x = *raw_i32

    // ERROR [AX_TYPE_CANNOT_INDEX]: raw pointers are never auto-dereferenced for indexing (AXS-UNS-010, AXS-SEM-047)
    let y = unsafe { p[0] }

    // Safe capability verification remains active inside `unsafe` (AXS-UNS-003, AXS-UNS-006):
    unsafe {
        let mut val: i32 = 10
        let v1: view<i32> = view(val)
        // ERROR [AX_CAP_CONFLICT_MUT]: cannot create `mut_view(val)` while `v1` is still live and used below
        let mv: mut_view<i32> = mut_view(val)
        *mv = 20
        return *v1 + x + y
    }
}
```

### AXS-UNS-053 — Requirement & Task Traceability Matrix (`T500`–`T505`)

Every requirement in `T500`'s `covers:` list (135 requirements) and the E13.1 implementation tasks (`T501`–`T505`) maps to the normative clauses of `SPEC-50` as follows:

| Requirement IDs | Domain / Summary | Normative Clauses in `SPEC-50` | Implementing / Verifying Tasks |
|---|---|---|---|
| `REQ-OWNER-008` | Obtain memory address of any `fn` (`fn_addr`, `addr_of`, `fn as usize`) or `static`/variable place (`static_addr`, `address_of(v) as usize`, `address_of_mut`, `addr_of`) and bind/place `static`, `let`, and `fn` via `@addr(<expr>)` / `@at(<expr>)` including dynamic `base + offset` and round-trip assertions | `AXS-UNS-020`, `AXS-UNS-021`, `AXS-UNS-022`, `AXS-UNS-023`, `AXS-UNS-024`, `AXS-UNS-025`, `AXS-UNS-051` | `T500` (spec), `T501` (sema/MIR), `T502` (oracle), `T504` (native x64), `T505` (conformance), `T525`–`T529` (`E13.6`) |
| `REQ-ABI-005`, `REQ-ABI-006`, `REQ-ABI-034`, `REQ-ABI-035`, `REQ-ABI-047`, `REQ-ABI-058`, `REQ-ABI-059`, `REQ-ABI-097`, `REQ-RES-130`, `REQ-RES-131`, `REQ-RES-139` | Default Axiom layout (`Repr.Axiom`) and ABI (`extern "axiom"`) are compiler-controlled and unstable by default, preserving internal optimization freedom | `AXS-UNS-030`, `AXS-UNS-032` | `T500`, `T503`, `T504` |
| `REQ-ABI-007`, `REQ-ABI-008`, `REQ-ABI-018`, `REQ-ABI-019`, `REQ-ABI-020`, `REQ-ABI-021`, `REQ-ABI-022`, `REQ-ABI-024`, `REQ-ABI-025`, `REQ-ABI-026`, `REQ-ABI-027`, `REQ-ABI-030`, `REQ-ABI-039`, `REQ-ABI-049`, `REQ-ABI-060`, `REQ-ABI-099`, `REQ-ABI-101` | Stable ABI (`@abi(stable)`) requires an explicit versioned contract; `pub` visibility is independent of `@export`; containers/evolution/fingerprints/`.axabi` metadata do not expose compiler internals | `AXS-UNS-032`, `AXS-UNS-050` | `T500`, `T503`, `T504` |
| `REQ-ABI-009`, `REQ-ABI-010`, `REQ-ABI-011`, `REQ-ABI-023`, `REQ-ABI-028`, `REQ-ABI-037`, `REQ-ABI-038`, `REQ-ABI-045`, `REQ-ABI-048`, `REQ-ABI-050`, `REQ-ABI-062`, `REQ-RES-132`, `REQ-RES-133`, `REQ-RES-134`, `REQ-RES-165`, `REQ-RES-166` | `@repr(C)` controls representation not calling convention; `@repr(transparent)` preserves layout/ABI and distinct type identity; Axiom ADTs are not C enums; calling conventions (`axiom`, `C`, `system`) are explicit in fn/FnPtr types | `AXS-UNS-030`, `AXS-UNS-031`, `AXS-UNS-033`, `AXS-UNS-036` | `T500`, `T503`, `T504`, `T505` |
| `REQ-ABI-013`, `REQ-ABI-029`, `REQ-FFI-011`, `REQ-FFI-014`, `REQ-FFI-027`, `REQ-FFI-028`, `REQ-FFI-044`, `REQ-FFI-045`, `REQ-FFI-048`, `REQ-FFI-057`, `REQ-FFI-064`, `REQ-FFI-067`, `REQ-FFI-068`, `REQ-FFI-079`, `REQ-FFI-083`, `REQ-FFI-084`, `REQ-FFI-085`, `REQ-FFI-086`, `REQ-FFI-087`, `REQ-FFI-088`, `REQ-FFI-089`, `REQ-FFI-100`, `REQ-FFI-101`, `REQ-FFI-102`, `REQ-FFI-112`, `REQ-FFI-113`, `REQ-FFI-114`, `REQ-FFI-128`, `REQ-RES-171`, `REQ-RES-172` | Raw FFI pointers do not implicitly become safe capabilities; foreign memory is a distinct domain; foreign calls are conservative (`MayAlias`, unknown effects, no implicit atomic synchronization) unless explicitly contracted; safe verification resumes after FFI boundary | `AXS-UNS-006`, `AXS-UNS-010`, `AXS-UNS-033`, `AXS-UNS-035` | `T500`, `T501`, `T502`, `T504`, `T505` |
| `REQ-ABI-014`, `REQ-ABI-015`, `REQ-ABI-016`, `REQ-ABI-017`, `REQ-ABI-051`, `REQ-ABI-053`, `REQ-ABI-057`, `REQ-ABI-066`, `REQ-ABI-067`, `REQ-ABI-068`, `REQ-ABI-092`, `REQ-FFI-007`, `REQ-FFI-012`, `REQ-FFI-021`, `REQ-FFI-034`, `REQ-FFI-035`, `REQ-FFI-036`, `REQ-FFI-037`, `REQ-FFI-049`, `REQ-FFI-050`, `REQ-FFI-051`, `REQ-FFI-052`, `REQ-FFI-059`, `REQ-FFI-060`, `REQ-FFI-090`, `REQ-FFI-091`, `REQ-FFI-092`, `REQ-FFI-103`, `REQ-FFI-104`, `REQ-FFI-105`, `REQ-FFI-106`, `REQ-FFI-107`, `REQ-FFI-122`, `REQ-RES-150`, `REQ-RES-151`, `REQ-RES-152`, `REQ-RES-153`, `REQ-RES-154`, `REQ-RES-155` | Closure, `dyn Trait`, and generic representations are not stable ABI; generics require specialization before export; capturing closures cannot implicitly convert to C callbacks; non-capturing closures decay to fn pointers; callbacks have explicit lifetime/threading/reentrancy contracts | `AXS-UNS-030`, `AXS-UNS-032`, `AXS-UNS-034`, `AXS-UNS-050` | `T500`, `T503`, `T504`, `T505` |
| `REQ-ABI-040`, `REQ-ABI-042`, `REQ-ABI-043`, `REQ-ABI-054`, `REQ-ABI-069`, `REQ-ABI-070`, `REQ-ABI-071`, `REQ-ABI-072`, `REQ-ABI-073`, `REQ-ABI-074`, `REQ-ABI-075`, `REQ-ABI-076`, `REQ-ABI-077`, `REQ-ABI-079`, `REQ-ABI-080`, `REQ-ABI-081`, `REQ-ABI-082`, `REQ-ABI-084`, `REQ-ABI-085`, `REQ-ABI-086`, `REQ-ABI-087`, `REQ-ABI-088`, `REQ-ABI-089`, `REQ-ABI-090`, `REQ-ABI-091`, `REQ-ABI-094`, `REQ-ABI-104`, `REQ-RES-138`, `REQ-RES-140`, `REQ-RES-141`, `REQ-RES-142`, `REQ-RES-143`, `REQ-RES-144`, `REQ-RES-146`, `REQ-RES-147`, `REQ-RES-156`, `REQ-RES-157`, `REQ-RES-158`, `REQ-RES-159`, `REQ-RES-162`, `REQ-RES-164`, `REQ-RES-167`, `REQ-RES-168`, `REQ-RES-169`, `REQ-RES-174`, `REQ-RES-175`, `REQ-RES-176`, `REQ-RES-177`, `REQ-RES-178`, `REQ-RES-179` | Observable physical address constrains storage optimization; niche optimization; small register vs large `sret` aggregate passing without heap allocation; deterministic Win64/SysV64 ABI lowering; `ADR-0034 §8` external gcc DLL oracle (`T503`); abstraction erasure before codegen | `AXS-UNS-021`, `AXS-UNS-022`, `AXS-UNS-030`, `AXS-UNS-036` | `T500`, `T501`, `T503`, `T504`, `T505` |
| `REQ-CAP-001`..`009`, `REQ-CAP-011`..`059`, `REQ-CAP-060`..`108`, `REQ-CAP-109`..`134`, `REQ-CAP-142`..`151`, `REQ-MIR-142`, `REQ-TYP-349` | Full capability model across safe and `unsafe` boundaries: `view<T>` (duplicable read capability, `MakeView`) vs `mut_view<T>` (move-only exclusive write capability, `MakeMutView`), non-owning semantics (`ACAP-23..47`), ephemeral vs persistent capabilities, region algebra (`SAME`, `DISJOINT`, `CONTAINS`, `CONTAINED_BY`, `OVERLAPS`, `UNKNOWN != DISJOINT`), provenance & semantic last-use lifetime (`VCAP-01..04`), container relocation & `.await`/thread escape prevention, optimization-level invariance (`REQ-CAP-055`), and post-verification capability erasure | `AXS-UNS-003`, `AXS-UNS-006`, `AXS-UNS-007`, `AXS-UNS-010`, `AXS-UNS-011`, `AXS-UNS-014`, `AXS-UNS-016` | `T500`, `T501`, `T502`, `T505` |

## Sources

- `spec/requirements/OWNER.md` (`REQ-OWNER-003`, `REQ-OWNER-005`, `REQ-OWNER-008`)
- `spec/decisions/ADR-0001-fixed-address-declarations.md` (`§1–7`)
- `spec/decisions/ADR-0002-oracle-host-interface.md` (`§4–5`)
- `spec/decisions/ADR-0011-diagnostic-code-taxonomy.md` (`§3`)
- `spec/decisions/ADR-0034-oracle-independence.md` (`§7–8, OI-12`)
- `spec/decisions/ADR-0036-view-autoderef-and-raw-pointer-capabilities.md` (`§1–4`)
- `docs/base/specs/0044 - AXIOM MEMORY ACCESS, POINTER & ALIASING v0.1.md`
- `docs/base/specs/0071 - Axiom Memory Access Model v0.1.md` (`§1–60, AMEM-01..15`)
- `docs/base/specs/0104 - Axiom — ABI Stability, FFI, Versioning & Binary Compatibility v0.1.md` (`§1–55, AABI-41..70`)
- `docs/base/specs/0112`, `0114`, `0115`, `0118`, `0119`, `0121`, `0124`, `0126`, `0128`, `0129`, `0131`, `0132`, `0133`, `0138 (Part XIX)`, `0151`, `0159`, `0160`, `0161`, `0162`, `0163`, `0177`, `0181`, `0228`, `0230`, `0266`, `0270`, `0292`, `0300`
- `docs/base/tasks/0282 - BOOTSTRAP-024 — Pointer, Reference, Handle & Access Syntax.md`
- `docs/base/tasks/0339 - BOOTSTRAP-080 — Axiom Security, Safety, Undefined Behavior & Trusted Unsafe Model.md` (`§1–100, ASAFE-20..100`)
- `docs/base/tasks/0367 - BOOTSTRAP-108 — Axiom ABI Lowering & Physical Representation.md` (`§1–82, AABI-20..70`)
- `docs/base/tasks/0395 - BOOTSTRAP-136 — Capability & Alias Analysis.md`
- `docs/base/tasks/0413 - BOOTSTRAP-154 — FFI, C ABI, System ABI & Foreign Function Interface Safety.md` (`§1–70, AFFI-20..64`)
- `docs/base/tasks/0416`, `0426`, `0429`, `0431`, `0432`, `0436`, `0437`, `0441`, `0442`, `0445`, `0451`, `0452`, `0459`, `0468`, `0470`, `0476`, `0482`, `0484`, `0486`, `0517`, `0585`, `0795`
- `spec/SPEC-03-core-semantics.md` (`AXS-SEM-002`, `AXS-SEM-042`..`047`, `AXS-SEM-060`, `AXS-SEM-092`)
- `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-020`..`025`, `AXS-EXT-030`..`035`, `AXS-EXT-041`..`044`, `AXS-EXT-050`..`052`, `AXS-EXT-070`..`074`, `AXS-EXT-091`, `AXS-EXT-102`, `AXS-EXT-110`)
- `spec/SPEC-10-ownership.md` (`AXS-OWN-001`..`007`)
- `spec/SPEC-11-capability.md` (`AXS-CAP-001`..`009`)
- `spec/SPEC-12-drop.md` (`AXS-DROP-001`..`007`)
