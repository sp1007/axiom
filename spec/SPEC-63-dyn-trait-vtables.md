# SPEC-63 — Canonical `dyn Trait` Object Safety, Fat-Pointer Coercion & Vtable ABI Specification

Status: draft (T566, 2026-11-03)
Owner: axiom-architect
Consolidates: `0212 (§1–55, ATRAIT-20..60)`; `0158 (§18–19)`; `0161 (§31)`; `tasks/0389 (§52–70, §87)`; `tasks/0476 (§217.43–50)`; `tasks/0539 (§40–43, §89 AMIR-60..82)`; `spec/SPEC-02-grammar.md`; `spec/SPEC-03-core-semantics.md`; `spec/SPEC-04-core-extensibility.md`; `spec/SPEC-10-ownership.md`; `spec/SPEC-11-capability.md`; `spec/SPEC-12-drop.md`; `spec/SPEC-30-concurrency.md`; `spec/SPEC-50-unsafe-ub-ffi.md`; `spec/SPEC-73-inlining-specialization-devirt.md`.
Covers: `REQ-CORE-3031`..`3035` (and specifies the E14.4 contract for `T058`, `T567`–`T569`: `REQ-CORE-3036`..`3052`, `REQ-PAT-015`..`020`, `REQ-ABI-068`).
Consumers: `compiler/traits/`, `compiler/types/`, `compiler/mir/`, `compiler/interp/`, `compiler/lir/`, `compiler/target/x64/`, `compiler/obj/`, `std/alloc/box.ax`, `T058`, `T567`–`T569`.

## Tóm tắt

Tài liệu `SPEC-63` chuẩn hóa quy tắc an toàn đối tượng (**object safety**) cho `dyn Trait`, biểu diễn con trỏ béo hai từ nhớ (**two-word fat pointer**: `data_ptr`, `vtable_ptr`) cho `view<dyn Trait>`, `mut_view<dyn Trait>` và `Box<dyn Trait>`, phép ép kiểu xóa kích thước tĩnh (**unsizing coercion**), cùng bố cục bảng phương thức ảo (**vtable ABI**) và hủy động (**dynamic `Drop`**) cho phân hệ `E14.4` (Phase `P14`):
- **Đa hình động tường minh, không có object header và tách biệt hoàn toàn với ownership (`0212 §2–3, §19–24, §48`, `ATRAIT-20..31`, `AMIR-60..63`, `AMIR-81..82`, `REQ-CORE-3031..3033`, `REQ-CORE-3051..3052`)**: Trong Axiom, mọi kiểu cụ thể (`struct`, `enum`, kiểu nguyên thủy) chỉ chứa dữ liệu thuần túy, tuyệt đối không mang `vptr` ẩn, không có object header, không cần GC và không cần runtime nguyên khối. Đa hình tĩnh qua generic (`fn f<T: Trait>(x: T)`) là mặc định; đa hình động chỉ xuất hiện khi lập trình viên viết tường minh `dyn Trait`. Bản thân `dyn Trait` không tự mang ngữ nghĩa sở hữu hay tự động cấp phát heap (`ATRAIT-30..31`, `ATRAIT-60`, `AMIR-60`): quyền truy cập và sở hữu được cung cấp trực giao bởi `view<dyn Trait>` (capability chỉ đọc), `mut_view<dyn Trait>` (capability đọc/ghi độc quyền) hoặc `Box<dyn Trait>` (sở hữu trên heap).
- **Quy tắc an toàn đối tượng (`Object Safety` / `AX_DYN_NOT_OBJECT_SAFE`) (`0212 §39–40`, `0389 §54–55`, `ATRAIT-32..33`, `REQ-PAT-020`, `T058`)**: Một trait `Trait` (cùng toàn bộ các supertrait bắc cầu của nó) chỉ được phép tạo `dyn Trait` khi thỏa mãn bốn điều kiện: (1) không yêu cầu ràng buộc `Self: Sized`; (2) không khai báo hằng số kết hợp (`const`); (3) mọi kiểu kết hợp (`type Item`) đều được gắn kiểu cụ thể tại vị trí `dyn`; và (4) mọi phương thức đều có tham số nhận `self` thuộc `{view<Self>, mut_view<Self>, Box<Self>}`, không có tham số kiểu generic hay `comptime` ở mức phương thức, và không nhắc tới `Self` ở vị trí giá trị/kiểu ngoài tham số `self`. Vi phạm bất kỳ quy tắc nào khi tạo `dyn Trait` bị từ chối tại thời điểm biên dịch với mã `AX_DYN_NOT_OBJECT_SAFE`.
- **Biểu diễn con trỏ béo 16 byte và phép ép kiểu `Unsize` bảo toàn capability/ownership (`0212 §21–22`, `0389 §67–69`, `SPEC-04 AXS-EXT-020/035/042`, `AMIR-31..37`, `AMIR-47..48`, `AMIR-76..78`, `T058`, `T568`)**: Mọi `view<dyn Trait>`, `mut_view<dyn Trait>` và `Box<dyn Trait>` có kích thước 16 byte (`align = 8`) trên đích 64-bit, gồm `(data_ptr, vtable_ptr)`. Phép ép kiểu `view<T> -> view<dyn Trait>`, `mut_view<T> -> mut_view<dyn Trait>`, `Box<T> -> Box<dyn Trait>` và ép kiểu lên supertrait (`view<dyn Sub> -> view<dyn Super>`) được hạ bậc tường minh thành `MirRvalue.UnsizeDyn` trong MIR (`AMIR-31..32`), giữ nguyên vùng nhớ (`region`), nguồn gốc (`provenance`) và quy tắc xung đột capability của biến gốc mà không phát sinh cấp phát bộ nhớ ẩn.
- **Bố cục vtable chuẩn trong `.rdata`, gọi gián tiếp x86-64 và hủy động `Box<dyn Trait>` (`0212 §23, §47`, `SPEC-04 AXS-EXT-044/071..073`, `SPEC-12`, `T567`, `T568`)**: Mỗi cặp `(ConcreteType, Trait)` tạo một bảng vtable bất biến đặt trong phân đoạn chỉ đọc `.rdata` với bố cục từ 8 byte xác định: `[drop_in_place, size, align, supertrait_vtables..., method_0, method_1, ...]`. Khi hủy `Box<dyn Trait>`, trình biên dịch gọi `vtable.drop_in_place(data_ptr)` để chạy hàm hủy của kiểu cụ thể rồi giải phóng khối nhớ heap qua `host.heap_free(data_ptr, vtable.size, vtable.align)` khi `size > 0`, bảo đảm kết quả đồng nhất tuyệt đối giữa `--interp` và mã máy x86-64 (`0 WEAK-NATIVE`).

---

## 1. Dynamic Trait Architecture & Object-Safety Rules (`AXS-DYN-001`..`004`)

### AXS-DYN-001 — Explicit Dynamic Dispatch, Orthogonal Ownership & Zero Object Headers (`0212 §2–6, §19–24, §48`, `ATRAIT-20..31`, `ATRAIT-40..41`, `AMIR-60..63`, `AMIR-81..82`, `REQ-CORE-3031`..`3033`, `REQ-CORE-3051`..`3052`, `REQ-PAT-015`..`019`)

1. **No Object Headers, No Hidden Vtables, No GC & No Monolithic Runtime (`0212 §2–3, §24, §48`, `ATRAIT-20..29`, `AMIR-61..63`, `REQ-CORE-3031..3033`)**:
   - In Axiom, structs and enums contain only their declared fields/payloads; traits define behavioral contracts (`ATRAIT-20`). Implementing a trait via `impl Trait for T` establishes a compile-time relationship and NEVER embeds a `vptr`, object header, or implicit runtime type information (`RTTI`) inside values of `T` (`0212 §3, §24, §48`, `ATRAIT-21..22`, `ATRAIT-29`).
   - MIR and runtime execution for `dyn Trait` require no garbage collection (`AMIR-61`, `REQ-CORE-3031`), no object headers on concrete values (`AMIR-62`, `REQ-CORE-3032`), and no monolithic runtime (`AMIR-63`, `REQ-CORE-3033`).
2. **Explicit `dyn Trait` vs Default Static Dispatch (`0212 §5, §19–22`, `tasks/0476 §217.49–50`, `ATRAIT-23..28`, `REQ-PAT-015..017`)**:
   - Generic functions (`fn render<T: Draw>(x: view<T>)`) use static dispatch (`Monomorphization`) by default (`ATRAIT-23..25`, `REQ-PAT-016`). Dynamic vtable dispatch occurs only when the programmer explicitly writes a `dyn Trait` type (`ATRAIT-27..28`, `REQ-PAT-015`, `REQ-PAT-017`).
3. **Orthogonality of Dynamic Dispatch and Storage/Ownership (`0212 §21–22`, `0389 §67–69`, `ATRAIT-30..31`, `ATRAIT-60`, `AMIR-60`, `AMIR-81..82`, `REQ-PAT-018..019`, `REQ-CORE-3030`, `REQ-CORE-3051..3052`)**:
   - Bare `dyn Trait` is an unsized dynamically dispatched type (`TypeKind.Dyn`, `SPEC-04 AXS-EXT-020`) and never implies ownership or implicit heap boxing (`0212 §21–22`, `ATRAIT-30`, `ATRAIT-60`, `AMIR-60`, `REQ-PAT-018..019`).
   - Ownership and access capabilities are supplied orthogonally by wrapping `dyn Trait` in a capability or smart pointer:
     - `view<dyn Trait>`: non-owning shared read capability (`SPEC-11`);
     - `mut_view<dyn Trait>`: non-owning exclusive mutable capability (`SPEC-11`);
     - `Box<dyn Trait>`: unique heap-owning pointer (`std.alloc.box.Box`, `T568`);
     - `Rc<dyn Trait>` / `Arc<dyn Trait>`: reference-counted shared pointers (`SPEC-32`).
   - MIR representation of `dyn Trait` operations remains independent of physical storage strategy and stack-versus-heap placement (`AMIR-81..82`, `REQ-CORE-3051..3052`).

### AXS-DYN-002 — Object-Safety Rules (`AX_DYN_NOT_OBJECT_SAFE`) (`0212 §39–40`, `0389 §54–55`, `ATRAIT-32..33`, `REQ-PAT-020`, `T058`)

1. **Compile-Time Object-Safety Verification (`0212 §39–40`, `0389 §54–55`, `ATRAIT-32..33`, `REQ-PAT-020`, `T058`)**:
   - Every occurrence of a `dyn Trait` type is checked by `compiler/traits` to verify that `Trait` and all of its transitive supertraits (`trait Sub: Super`) are **object-safe** (`dyn`-compatible). A trait `T` is object-safe if and only if all four rules below hold:
     1. **No `Self: Sized` requirement**: `T` (and its supertraits) must not carry a `Self: Sized` bound.
     2. **No associated constants**: `T` must not declare any associated `const` item (`const ZERO: Self` or `const ID: u32`), because associated constants are compile-time values (`0212 §10`, `ATRAIT-39`) rather than instance fields (`0389 §60–61`).
     3. **Fully specified associated types**: If `T` declares associated types (`type Item`), every associated type must be bound to a concrete type in the `dyn` bound (`dyn Iterator<Item = i32>`, `SPEC-02 AXS-GRM-080`). Leaving an associated type unbound on `dyn Trait` is rejected.
     4. **Object-safe methods**: Every method `m` declared in `T` (whether required or provided with a default body) must:
        - have an explicit `self` receiver as its first parameter whose type is `view<Self>`, `mut_view<Self>`, or `Box<Self>` (associated functions without a `self` parameter such as `fn default() -> Self` and by-value receivers `self: Self` are not object-safe);
        - declare **zero** method-level generic type parameters or `comptime` parameters (`fn convert<U>(self: view<Self>, x: U)` cannot be compiled into a fixed vtable slot and is rejected, `0212 §39`, `0389 §55`);
        - not reference `Self` in any parameter type, return type, or `where` bound outside the `self` receiver (`fn clone(self: view<Self>) -> Self` and `fn eq(self: view<Self>, other: view<Self>) -> bool` are rejected because the caller does not know the concrete size of `Self` or that two `dyn Trait` values share the same concrete type, `0212 §40`, `0389 §54`).
2. **Diagnostic Emission (`AX_DYN_NOT_OBJECT_SAFE`) (`T058`)**:
   - Forming `dyn Trait` when `Trait` violates any rule in (1) is rejected with `AX_DYN_NOT_OBJECT_SAFE` at the `dyn Trait` type span, attaching diagnostic `notes` that identify each non-object-safe member (e.g., `"method `create` has generic type parameters"`, `"method `clone` returns `Self` by value"`, `"trait `Numeric` has associated constant `ZERO`"`).

### AXS-DYN-003 — Multi-Trait Bounds (`dyn Trait + Send + Share`) & Supertrait Hierarchy (`SPEC-02 AXS-GRM-087`, `0212 §13–15`, `0389 §57–59`, `SPEC-30`, `T058`)

1. **Principal Trait + Auto-Trait Composition (`SPEC-02 AXS-GRM-087`, `SPEC-30 AXS-CONC-010`, `T058`)**:
   - A `DynType` `dyn B_1 + B_2 + ...` (`SPEC-02 AXS-GRM-087`) may contain **at most one principal non-auto trait** `Trait` together with zero or more marker auto-traits (`Send`, `Share`). Combining two non-auto traits (`dyn Draw + Log`) is rejected with `AX_DYN_NOT_OBJECT_SAFE` (`data.reason = "multiple_principal_traits"`).
   - Auto-trait bounds on `dyn Trait + Send + Share` require the concrete type `T` at the unsizing site to satisfy `T: Send` / `T: Share` (`AX_CONC_NOT_SEND`, `AX_CONC_NOT_SHARE`, `SPEC-30`), and determine whether `Box<dyn Trait + Send>` / `view<dyn Trait + Share>` satisfies `Send` and `Share`. Because `Send` and `Share` are zero-cost marker traits (`INV-CONC-001`), they add zero slots to the vtable.
2. **Supertrait Bounds (`trait Sub: Super`) (`0212 §14–15`, `0389 §57–59`, `T058`)**:
   - When `trait Sub: Super_0 + Super_1` is used as `dyn Sub`, every transitive supertrait `Super_i` must also be object-safe (`AXS-DYN-002`). Upcasting `view<dyn Sub>` -> `view<dyn Super_i>`, `mut_view<dyn Sub>` -> `mut_view<dyn Super_i>`, or `Box<dyn Sub>` -> `Box<dyn Super_i>` is a safe compile-time-checked coercion (`AXS-DYN-011`, `AXS-DYN-020`).

### AXS-DYN-004 — Default Trait Methods & Coherent Override Dispatch (`0212 §25–28, §36–38, §54`, `ATRAIT-34..36`, `ATRAIT-40..41`, `T058`)

1. **Default Method Specialization & Override in Vtables (`0212 §25, §36–38, §54`, `ATRAIT-40..41`, `T058`)**:
   - If an object-safe trait `Trait` declares a method `fn m(self: view<Self>, ...) -> R { ... }` with a default body, `impl Trait for Concrete` may either omit `m` (inheriting the default body, monomorphized for `Self = Concrete`) or provide a custom `fn m(...)` body that overrides the default (`0212 §37, §54`).
   - By global coherence (`0212 §26–28`, `ATRAIT-34..36`), at most one `impl Trait for Concrete` exists in a program, so every vtable slot for `(Concrete, Trait)` resolves deterministically to a single target function.

---

## 2. Fat-Pointer Representation, Unsizing Coercions & Capability Lifetimes (`AXS-DYN-010`..`012`)

### AXS-DYN-010 — Two-Word Fat-Pointer Representation (`data_ptr`, `vtable_ptr`) (`0212 §19, §22, §47–48`, `SPEC-04 AXS-EXT-020`, `REQ-ABI-068`, `T058`, `T567`, `T568`)

1. **16-Byte Fat-Pointer Layout (`0212 §19, §48`, `SPEC-04 AXS-EXT-020`, `T058`, `T567`, `T568`)**:
   - On 64-bit targets (`usize` = 8 bytes), `view<dyn Trait>`, `mut_view<dyn Trait>`, and `Box<dyn Trait>` are 16-byte (`size = 16, align = 8`) two-word fat pointers with identical field offsets:
     ```text
     DynFatPtr<Trait> (size = 16, align = 8):
       offset 0: data_ptr   : *const u8 (for view<dyn Trait>) | *mut u8 (for mut_view<dyn Trait>, Box<dyn Trait>)
       offset 8: vtable_ptr : *const VTable<Trait>
     ```
   - `data_ptr` points directly to the first byte of the underlying concrete value `T` in stack, static, or heap memory without any prepended object header (`0212 §48`, `AMIR-62`, `REQ-CORE-3032`).
   - `vtable_ptr` is a non-null pointer to the static read-only vtable descriptor for `(T, Trait)` (`AXS-DYN-020`).
2. **Internal Representation vs FFI Boundary (`0212 §47`, `REQ-ABI-068`, `SPEC-50 AXS-UNS-033`)**:
   - The `DynFatPtr` representation is an Axiom-internal ABI contract (`REQ-ABI-068`, `ATRAIT-58`). Passing or returning `view<dyn Trait>`, `mut_view<dyn Trait>`, or `Box<dyn Trait>` directly in an `extern "C"` signature without an explicit `@repr(C)` FFI wrapper struct is rejected with `AX_FFI_BAD_TYPE` (`SPEC-50 AXS-UNS-033`).

### AXS-DYN-011 — Unsizing Coercions & Supertrait Upcasting (`view<T> -> view<dyn Trait>`, `mut_view<T> -> mut_view<dyn Trait>`, `Box<T> -> Box<dyn Trait>`) (`0212 §21–22`, `0389 §67–69`, `SPEC-04 AXS-EXT-035, AXS-EXT-042`, `AMIR-31..32`, `AMIR-60`, `T058`, `T568`)

1. **Allowed Unsizing Sites & Forms (`SPEC-04 AXS-EXT-035, AXS-EXT-042`, `AMIR-31..32`, `T058`, `T568`)**:
   - When concrete type `T` implements `Trait` (`T: Trait`) and satisfies all auto-trait bounds on `dyn Trait`, the type checker (`compiler/types`, `compiler/traits`) permits unsizing at explicit `as` cast sites (`view(x) as view<dyn Trait>`) and typed coercion sites (`let` bindings with explicit type annotations, function/method call arguments, struct/tuple/array element initializers, and `return` expressions) for exactly:
     1. **Shared view unsizing**: `view<T>` -> `view<dyn Trait>` (including ephemeral `view(x)` at a call argument expecting `view<dyn Trait>`, `tasks/0476 §217.54`, and `mut_view<T>` -> `view<dyn Trait>`);
     2. **Mutable view unsizing**: `mut_view<T>` -> `mut_view<dyn Trait>`;
     3. **Owned `Box` unsizing**: `Box<T>` -> `Box<dyn Trait>`, transferring unique ownership of the existing heap allocation without reallocating or copying `*ptr` (`T568`);
     4. **Supertrait upcasting**: `view<dyn Sub>` -> `view<dyn Super>`, `mut_view<dyn Sub>` -> `mut_view<dyn Super>`, and `Box<dyn Sub>` -> `Box<dyn Super>` where `Sub: Super` (`T058`, `T568`).
   - Passing a bare value `x: T` directly to a parameter of bare type `dyn Trait` or expecting the compiler to implicitly allocate a `Box` is forbidden (`0212 §21`, `0389 §69`, `ATRAIT-60`, `AMIR-60`, `REQ-CORE-3030`).
   - If `T` does not implement `Trait`, the compiler emits `AX_TRAIT_UNSATISFIED_BOUND` (`compiler/diag/code.ax`).

### AXS-DYN-012 — Capability Lifetime, Provenance & Aliasing Enforcement on `dyn Trait` (`0389 §67`, `AMIR-34..37`, `AMIR-47..48`, `AMIR-76..78`, `REQ-CORE-3046`..`3048`, `SPEC-11`, `T058`, `T568`)

1. **Capability Provenance Preservation (`0389 §67`, `AMIR-35`, `AMIR-37`, `AMIR-47..48`, `AMIR-78`, `REQ-CORE-3048`, `SPEC-11`, `T058`)**:
   - Unsizing `view<T>` -> `view<dyn Trait>` or `mut_view<T>` -> `mut_view<dyn Trait>` preserves the source capability's `CapabilityKind` (`READ` vs `WRITE`), root owner (`LocalId`), region, and provenance in `compiler/own` and MIR verification:
     - A `view<dyn Trait>` or `mut_view<dyn Trait>` MUST NOT outlive or escape the lexical scope of its backing concrete owner (`AX_CAP_OUTLIVES_OWNER` / `AX_TYPE_STORED_VIEW_ESCAPE`);
     - While `mut_view<dyn Trait>` is live, any concurrent `view` or `mut_view` or direct read/write of the underlying owner place is rejected (`AX_CAP_CONFLICT_MUT`, `AX_CAP_CONFLICT_READ`);
     - While `view<dyn Trait>` is live, mutating or relocating the backing owner (`AMIR-48`) is rejected (`AX_CAP_CONFLICT_MUT`, `AX_CAP_CONTAINER_RELOC`).
2. **Reborrowing `Box<dyn Trait>` as `view<dyn Trait>` / `mut_view<dyn Trait>` (`T568`)**:
   - Given an owned `b: Box<dyn Trait>`, `view(b)` (or passing `b` to a `view<dyn Trait>` parameter) produces a non-owning `view<dyn Trait>` `{ data_ptr = b.data_ptr, vtable_ptr = b.vtable_ptr }` whose capability lifetime is bound to `b`.
   - Given `let mut b: Box<dyn Trait>`, `mut_view(b)` produces an exclusive `mut_view<dyn Trait>` `{ data_ptr = b.data_ptr, vtable_ptr = b.vtable_ptr }` that prevents reading, moving, or dropping `b` while the mutable view is live (`SPEC-11`).

---

## 3. Canonical Vtable Layout, MIR Lowering, Native Codegen & Dynamic `Drop` (`AXS-DYN-020`..`024`)

### AXS-DYN-020 — Canonical Vtable Layout (`drop_in_place`, `size`, `align`, Supertraits, Declaration-Ordered Methods) (`0212 §23`, `T058`, `T567`, `T568`)

1. **Deterministic 8-Byte Slot Layout (`0212 §23`, `T058`, `T567`, `T568`)**:
   - For every pair `(ConcreteType T, PrincipalTrait P)` where `P` has `S` direct/transitive supertrait vtable headers (in deterministic depth-first pre-order of `trait P: Super_0 + Super_1`) and `M` dispatchable methods declared on `P`, the vtable `VTable<T, P>` is a contiguous, 8-byte-aligned array of `(3 + S + M)` 64-bit words:
     ```text
     VTable<T, P> (align = 8, size = (3 + S + M) * 8 bytes):
       slot 0 (offset  0): drop_in_place : unsafe fn(*mut u8)
       slot 1 (offset  8): size          : usize = size_of<T>()
       slot 2 (offset 16): align         : usize = align_of<T>()
       slots 3 .. 3+S-1  : super_vtables : [*const VTable<T, Super_k>; S]
       slots 3+S ..      : methods       : [fn(*const/*mut u8, ...) -> Ret; M]
     ```
   - **Header slots (`0..2`)**:
     - `slot 0` (`drop_in_place`): function pointer to the compiler-synthesized in-place destructor shim `__ax_drop_in_place$<T>(ptr: *mut u8)` that executes `T`'s custom `Drop.drop` and/or recursive field destructors in declaration order (`SPEC-12 AXS-DROP-002, AXS-DROP-005`) without freeing the outer heap block. If `!needs_drop<T>()`, `slot 0` points to the shared no-op function `__ax_drop_noop(ptr: *mut u8)`.
     - `slot 1` (`size`): exact byte size `size_of<T>()` (`0` for zero-sized types).
     - `slot 2` (`align`): exact byte alignment `align_of<T>()` (power of two `>= 1`).
   - **Supertrait slots (`3 .. 3 + S - 1`)**:
     - Each slot `3 + k` holds a pointer to `&__ax_vtable$<Super_k>$<T>`. Upcasting `dyn P` to `dyn Super_k` loads `new_vtable_ptr = *(vtable_ptr + (3 + k) * 8)` while leaving `data_ptr` unchanged (`T058`, `T567`). (Flattening supertrait methods before `P`'s own methods is permitted internally when `S == 0`, provided upcasting produces a valid `VTable<T, Super_k>` pointer with header `[drop_in_place, size, align]` at offset `0`.)
   - **Method slots (`3 + S .. 3 + S + M - 1`)**:
     - Method pointers appear in the **exact source declaration order** of `P`'s methods (`method_0`, `method_1`, ..., `method_{M-1}`).
     - Each entry points to the concrete method implementation `T.method_i` (or monomorphized default method `P.method_i<T>`, `AXS-DYN-004`) ABI-adapted so its first parameter receives `data_ptr` (`view<T>` / `mut_view<T>` / `Box<T>`).

### AXS-DYN-021 — HIR → THIR → MIR Lowering, Determinism & Pipeline Verification Boundaries (`0161 §31`, `0539 §42, §89 AMIR-31..32, AMIR-64..82`, `SPEC-04 AXS-EXT-035, AXS-EXT-042, AXS-EXT-044`, `REQ-CORE-3034`..`3052`, `T058`, `T567`, `T568`)

1. **Explicit MIR Unsizing & Virtual Call Representation (`0161 §31`, `0539 §42`, `SPEC-04 AXS-EXT-035, AXS-EXT-042, AXS-EXT-044`, `AMIR-31..32`, `T058`)**:
   - THIR/MIR lowering never invents unvalidated implicit coercions (`AMIR-31..32`): every unsizing coercion lowers to an explicit `MirRvalue.UnsizeDyn` (or `MIR_RVALUE_CAST` with `MIR_CAST_UNSIZED` / `(ConcreteTypeId, TraitId)` metadata) constructing the `(data_ptr, vtable_ptr)` pair.
   - Every method call `recv.m(a_1, ..., a_k)` on a `dyn Trait` receiver evaluates `recv`, then `a_1 .. a_k` strictly left-to-right (`SPEC-03 AXS-SEM-041`, `AMIR-33`, `AMIR-79`, `REQ-CORE-3049`), and terminates the basic block with `MirTerminator.CallDyn` (`callee = Virtual { receiver, trait_id, slot_idx }`, `SPEC-04 AXS-EXT-044`).
2. **MIR Independence, Determinism & Verification Gate (`0539 §89 AMIR-64..82`, `REQ-CORE-3034..3052`, `T058`, `T567`, `T568`, `T569`)**:
   - MIR supports caller-allocated result construction (`RVO`/`sret`) across direct and dynamic calls (`AMIR-64`, `REQ-CORE-3034`) and permits physical move/copy elision (`AMIR-65`, `REQ-CORE-3035`).
   - MIR does not perform machine register allocation (`AMIR-66`, `REQ-CORE-3036`), target instruction selection (`AMIR-67`, `REQ-CORE-3037`), or final ABI register classification (`AMIR-68`, `REQ-CORE-3038`), and remains independent of physical storage strategy and stack-versus-heap placement (`AMIR-81..82`, `REQ-CORE-3051..3052`).
   - MIR preserves source and semantic provenance on all `UnsizeDyn`, `CallDyn`, and generated dynamic `Drop` cleanup constructs (`AMIR-69..70`, `REQ-CORE-3039..3040`).
   - MIR CFG construction is strictly deterministic (`AMIR-71`, `REQ-CORE-3041`) and independent of worker thread completion order (`AMIR-72`, `REQ-CORE-3042`).
   - Structural validation precedes semantic verification (`AMIR-73`, `REQ-CORE-3043`), invalid MIR is rejected and never enters optimization (`AMIR-74`, `REQ-CORE-3044`), only `Verified MIR` enters optimization (`AMIR-75`, `REQ-CORE-3045`), and all MIR/OptIR transformations (including `SPEC-73 AXS-INL-032` devirtualization) preserve semantic types (`AMIR-76`, `REQ-CORE-3046`), ownership (`AMIR-77`, `REQ-CORE-3047`), capabilities (`AMIR-78`, `REQ-CORE-3048`), evaluation order (`AMIR-79`, `REQ-CORE-3049`), and externally observable effects (`AMIR-80`, `REQ-CORE-3050`).

### AXS-DYN-022 — Oracle (`--interp`) Execution of Fat Pointers, Vtable Dispatch & Supertrait Upcasting (`compiler/interp`, `T058`, `T568`)

1. **Deterministic Oracle Vtable Registry & Dispatch (`compiler/interp`, `T058`, `T568`)**:
   - In `compiler/interp` (`--interp`), a `dyn Trait` fat pointer is represented as a two-component runtime value `(data_ptr: InterpPtr, vtable_id: VTableId)`.
   - Evaluating `UnsizeDyn` looks up or registers the canonical `VTableEntry { concrete_ty: TypeId, trait_id: TraitId, drop_fn: Option<FnId>, size: usize, align: usize, super_vtables: [VTableId], methods: [FnId] }` in the interpreter's deterministic table and pairs `vtable_id` with `data_ptr`.
   - Evaluating `CallDyn { receiver, trait_id, slot_idx, args, dest, target }` extracts `(data_ptr, vtable_id)` from `receiver`, indexes `vtable.methods[slot_idx]` to obtain the target `FnId`, passes `data_ptr` as the first argument (`self`) followed by `args`, and executes the target MIR body under the standard `--step-limit` and call-depth budgets (`SPEC-03`), producing identical stdout and exit codes to native execution (`INV-ORACLE-002`).

### AXS-DYN-023 — Native `.rdata` Vtable Emission, Windows x64 Fat-Pointer ABI & Indirect Call Codegen (`compiler/lir`, `compiler/target/x64`, `compiler/obj`, `SPEC-04 AXS-EXT-071..073`, `T567`)

1. **Deterministic `.rdata` Vtable Symbols & COFF Relocations (`SPEC-04 AXS-EXT-071..073`, `T567`)**:
   - For each unique `(ConcreteType T, PrincipalTrait P)` vtable lowered in `compiler/lir`, `compiler/obj` emits a read-only `.rdata` symbol with canonical mangled name `__ax_vtable$<TraitPath>$<TypePath>` (`align = 8`), deduplicated within each object module and across linked objects.
   - Words `1` (`size`) and `2` (`align`) are emitted as little-endian 64-bit integer constants; word `0` (`drop_in_place`), supertrait slots `3 .. 3+S-1`, and method slots `3+S .. 3+S+M-1` are initialized to `0` with 64-bit COFF `IMAGE_REL_AMD64_ADDR64` (`Addr64`, `SPEC-04 AXS-EXT-073`) relocations targeting the respective function or supertrait vtable symbols (`T567`).
2. **Windows x64 Fat-Pointer ABI & Indirect Call Sequence (`compiler/lir`, `compiler/target/x64`, `ADR-0003`, `T567`)**:
   - Under `CallConv.Win64` (`SPEC-04 AXS-EXT-052, AXS-EXT-060`), a 16-byte `dyn Trait` fat pointer (`view<dyn Trait>`, `mut_view<dyn Trait>`, `Box<dyn Trait>`) is classified as a 16-byte composite (`size = 16, align = 8`) and lowered by `abi_lower` identically to a two-field struct `{ data_ptr: *mut u8, vtable_ptr: *const u8 }` across arguments and return values.
   - To lower `CallDyn` on method slot `i` (`0 <= i < M`):
     1. Load `r_data = fat_ptr.data_ptr` (offset `0`) and `r_vtable = fat_ptr.vtable_ptr` (offset `8`);
     2. Place `r_data` into the first receiver parameter register (`rcx`, or `rdx` when a hidden `sret` return pointer occupies `rcx` per `AXS-DYN-021` / `AMIR-64`), and place remaining arguments into subsequent Win64 parameter registers/stack slots;
     3. Load the target function pointer from `[r_vtable + (3 + S + i) * 8]` into a scratch volatile register (e.g., `rax` or `r10`/`r11`) and emit an indirect `call rax` (or `call qword ptr [r_vtable + disp32]`) with standard 32-byte Win64 shadow space and 16-byte stack alignment (`T567`).

### AXS-DYN-024 — Owned `Box<dyn Trait>` & Vtable-Driven Dynamic `Drop` Elaboration (`std/alloc/box.ax`, `compiler/mir/drop.ax`, `SPEC-12`, `T568`)

1. **`Box<T> -> Box<dyn Trait>` Ownership Transfer (`std/alloc/box.ax`, `T568`)**:
   - `Box<dyn Trait>` is a 16-byte unique owning fat pointer (`!Copy`, movable, droppable). Unsizing `let b_dyn: Box<dyn Trait> = box_new(concrete_val)` moves `b.ptr as *mut u8` into `b_dyn.data_ptr`, pairs it with `&__ax_vtable$<Trait>$<T>`, and marks the source `Box<T>` as `MOVED` (`SPEC-12 AXS-DROP-003`, `AMIR-44`) so the heap allocation is owned exclusively by `b_dyn`.
   - For a zero-sized type `T` (`size_of<T>() == 0`), `box_new` allocates `0` heap bytes (`data_ptr` is the non-null aligned sentinel `align_of<T>() as *mut u8`), and dynamic drop checks `vtable.size > 0` before calling `host.heap_free`.
2. **Vtable-Driven Dynamic `Drop` Elaboration (`compiler/mir/drop.ax`, `SPEC-12 AXS-DROP-001..007`, `T568`)**:
   - Whenever an initialized `Box<dyn Trait>` place `b` is dropped (at scope exit, early `return`/`break`/`continue`, `drop(b)`, container `Vec<Box<dyn Trait>>` element destruction, or overwrite `b = rhs` per `SPEC-12 AXS-DROP-007`), `compiler/mir/drop.ax` emits the dynamic cleanup sequence:
     1. Check `b.data_ptr as usize != 0` (and active drop flag if conditionally moved);
     2. Load `drop_fn = *(b.vtable_ptr + 0)` and call `drop_fn(b.data_ptr)` to run the concrete type's `Drop.drop` and field destructors in place;
     3. Load `sz = *(b.vtable_ptr + 8)` and `al = *(b.vtable_ptr + 16)`;
     4. If `sz > 0`, call `host.heap_free(b.data_ptr, sz, al)` to release the heap allocation using the concrete type's exact size and alignment;
     5. Set `b.data_ptr = 0 as *mut u8` (or clear the drop flag) so no double-drop or double-free can occur (`INV-SEM-003`).

---

## 4. Diagnostic Taxonomy, Canonical Examples & Conformance Matrix (`AXS-DYN-050`..`052`)

### AXS-DYN-050 — Dynamic Trait Diagnostic Codes (`spec/diagnostics.md`, `T058`)

Self-hosted `axiomc` (`compiler/diag/code.ax`) defines `AX_DYN_NOT_OBJECT_SAFE` alongside the existing `TRAIT` and `CAP` diagnostic codes:

| Code | Sev | Task | Condition |
|---|---|---|---|
| `AX_DYN_NOT_OBJECT_SAFE` | E | T058 | `dyn Trait` formed with a trait that is not object-safe: has `Self: Sized`, declares an associated `const`, has an unbound associated `type`, declares a method without a `view<Self>`/`mut_view<Self>`/`Box<Self>` receiver, declares a generic method `fn m<U>(...)`, mentions `Self` in non-receiver parameter/return position, or combines multiple non-auto principal traits (`AXS-DYN-002..003`) |
| `AX_TRAIT_UNSATISFIED_BOUND` | E | T055/T058 | unsizing `view<T>`, `mut_view<T>`, or `Box<T>` to `dyn Trait` when `T` does not implement `Trait` (`AXS-DYN-011`) |
| `AX_CAP_OUTLIVES_OWNER` | E | T125/T058 | `view<dyn Trait>` or `mut_view<dyn Trait>` escapes or outlives its backing concrete owner (`AXS-DYN-012`) |
| `AX_CAP_CONFLICT_MUT` | E | T125/T058 | `mut_view<dyn Trait>` overlaps another live `view` / `mut_view` or owner access (`AXS-DYN-012`) |

### AXS-DYN-051 — Canonical Positive & Negative Examples (`axiom-syntax`: `=` and `.` only)

```axiom
module demo.dyn_trait

use std.alloc.box.Box
use std.alloc.box.box_new

pub trait Draw {
    fn area(self: view<Self>) -> i64
    fn scale(self: mut_view<Self>, factor: i64)

    fn doubled_area(self: view<Self>) -> i64 {
        return self.area() * 2
    }
}

pub struct Rect {
    pub w: i64,
    pub h: i64,
}

impl Draw for Rect {
    fn area(self: view<Rect>) -> i64 {
        return self.w * self.h
    }
    fn scale(self: mut_view<Rect>, factor: i64) {
        self.w *= factor
        self.h *= factor
    }
}

pub fn apply_and_measure(item: mut_view<dyn Draw>, factor: i64) -> i64 {
    item.scale(factor)
    return item.doubled_area()
}

pub fn run_demo() -> i64 {
    let mut r = Rect { w: 3, h: 4 }
    let v1 = apply_and_measure(mut_view(r), 2)
    let owned: Box<dyn Draw> = box_new(Rect { w: 5, h: 6 })
    let v2 = view(owned).area()
    return v1 + v2
}

// Negative examples (rejected at compile time):
// trait BadClone {
//     fn clone_val(self: view<Self>) -> Self
// }
// fn bad_return_self(x: view<dyn BadClone>) {} //~ ERROR AX_DYN_NOT_OBJECT_SAFE
//
// trait BadGeneric {
//     fn map_val<U>(self: view<Self>, v: U) -> i32
// }
// fn bad_generic_method(x: view<dyn BadGeneric>) {} //~ ERROR AX_DYN_NOT_OBJECT_SAFE
//
// trait BadConst {
//     const ID: u32
//     fn tag(self: view<Self>) -> u32
// }
// fn bad_assoc_const(x: view<dyn BadConst>) {} //~ ERROR AX_DYN_NOT_OBJECT_SAFE
```

### AXS-DYN-052 — E14.4 Conformance Verification Matrix (`T058`, `T567`–`T569`)

| Test ID | Verification Focus | Expected Outcome | Task |
|---|---|---|---|
| `DYN-T01` | Object-safety verification (`AX_DYN_NOT_OBJECT_SAFE`) & capability lifetime tracking on `view<dyn Trait>` / `mut_view<dyn Trait>` | Rejects generic methods, `Self`-by-value returns/args, associated `const`, and dangling/conflicting `dyn` views | T058, T569 |
| `DYN-T02` | Polymorphic dispatch across multiple concrete types, `mut_view<dyn Trait>` mutation, default methods & supertrait upcasting in `--interp` | Exact dynamic dispatch and state mutation in `tests/run/dyn` | T058, T569 |
| `DYN-T03` | Native `.rdata` vtable emission (`__ax_vtable$...`), 16-byte Win64 fat-pointer ABI & indirect `call [r_vtable + offset]` codegen | Byte-identical stdout and exit codes across `--interp` and native x86-64 (`0 WEAK-NATIVE`) in `tests/mc/dyn` and `tests/run/dyn_native` | T567, T569 |
| `DYN-T04` | Owned `Box<dyn Trait>`, heterogeneous `Vec<Box<dyn Trait>>`, `view`/`mut_view` reborrowing & vtable `drop_in_place` + `heap_free(size, align)` | Deterministic reverse-order concrete destructor execution and zero memory leaks on scope exit or overwrite in `tests/run/dyn_box` | T568, T569 |

---

## 5. Sources & Traceability

- **Corpus Specifications & Tasks**: `0212 (§1–55, ATRAIT-20..60)`; `0158 (§18–19)`; `0161 (§31)`; `tasks/0389 (§52–70, §87)`; `tasks/0476 (§217.43–50)`; `tasks/0539 (§40–43, §89 AMIR-60..82)`.
- **Canonical Specs & ADRs**: `ADR-0003` (LIR ABI lowering); `ADR-0007` (canonical `=` and `.` syntax); `ADR-0011` (diagnostic taxonomy); `ADR-0036` (assignment drop vs raw store); `spec/SPEC-02-grammar.md`; `spec/SPEC-03-core-semantics.md`; `spec/SPEC-04-core-extensibility.md`; `spec/SPEC-10-ownership.md`; `spec/SPEC-11-capability.md`; `spec/SPEC-12-drop.md`; `spec/SPEC-30-concurrency.md`; `spec/SPEC-50-unsafe-ub-ffi.md`; `spec/SPEC-73-inlining-specialization-devirt.md`.
- **Requirements Covered**: `REQ-CORE-3031`..`3052`, `REQ-PAT-015`..`020`, `REQ-ABI-068`.
