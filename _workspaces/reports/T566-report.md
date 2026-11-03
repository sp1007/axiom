# T566 Report — E14.4 Canonical `dyn Trait` Object Safety, Fat-Pointer Coercion & Vtable ABI Specification (`SPEC-63`)

## Tóm tắt

Hoàn thành đặc tả chuẩn tắc [spec/SPEC-63-dyn-trait-vtables.md](file:///d:/projects/compiler/new%20lang/spec/SPEC-63-dyn-trait-vtables.md) cho hệ thống đối tượng trait động (`dyn Trait`) thuộc Epic E14.4 (`T566`), đồng thời cập nhật đồng bộ [spec/INDEX.md](file:///d:/projects/compiler/new%20lang/spec/INDEX.md), [spec/diagnostics.md](file:///d:/projects/compiler/new%20lang/spec/diagnostics.md), và [spec/invariants.md](file:///d:/projects/compiler/new%20lang/spec/invariants.md). Đặc tả chốt 14 quy tắc chuẩn tắc (`AXS-DYN-001`..`004`, `AXS-DYN-010`..`012`, `AXS-DYN-020`..`024`, `AXS-DYN-050`..`052`) làm hợp đồng kiến trúc cho các tác vụ triển khai kế tiếp (`T058`, `T567`, `T568`, `T569`):

1. **Object Safety (`AXS-DYN-001`..`004`)**: Quy định 5 điều kiện an toàn đối tượng bắt buộc cho `trait Tr` khi tạo `dyn Tr` (không có supertrait `Sized`, mọi hàm liên kết trong vtable phải có receiver `self` hợp lệ ở tham số đầu tiên, không có tham số generic mức phương thức trừ khi đánh dấu `where Self: Sized`, không tham chiếu `Self` ở vị trí ngoài receiver trừ khi `where Self: Sized`, và không có hằng số liên kết). Vi phạm phát sinh mã chẩn đoán chuẩn `AX_DYN_NOT_OBJECT_SAFE` có gợi ý khắc phục `help:`.
2. **Biểu diễn Fat Pointer 16 byte & Ép kiểu Unsizing (`AXS-DYN-010`..`012`)**: Chuẩn hóa cấu trúc con trỏ béo hai từ nhớ `(data_ptr: Ptr<u8>, vtable_ptr: Ptr<Vtable<Tr>>)` (kích thước `16` byte, căn chỉnh `8` byte trên 64-bit) cho cả 3 dạng bề mặt `view<dyn Tr>`, `mut_view<dyn Tr>`, và `Box<dyn Tr>`, kèm quy tắc ép kiểu unsizing ngầm định và tường minh (`as`) tại mọi vị trí hợp thức hóa kiểu (`let`, đối số hàm, biểu thức trả về, khởi tạo trường struct/enum/tuple/mảng).
3. **Bố cục Vtable `.rdata` & Calling Convention (`AXS-DYN-020`..`024`)**: Chuẩn hóa bố cục bảng phương thức ảo tĩnh bất biến trong phân đoạn chỉ đọc `.rdata`:
   `[drop_in_place, size, align, super_vtables..., method_0, method_1, ...]` với thứ tự khe phương thức xác định, biểu tượng mangling định danh duy nhất `_AX_VTBL_<Type>_as_<Trait>`, hạ cấp MIR qua `Rvalue.Unsize` và `Terminator.CallIndirect`, cùng quy ước gọi gián tiếp truyền `data_ptr` ở thanh ghi tham số đầu tiên (`RCX` trên Windows x64, `RDI` trên System V AMD64) đảm bảo đồng nhất ngữ nghĩa giữa `--interp` và mã máy native x86-64.
4. **Hủy động qua Vtable & Bảo toàn Region (`AXS-DYN-050`..`052`)**: Quy định cơ chế giải phóng `Box<dyn Tr>` qua khe `drop_in_place` tại offset `0` kết hợp đọc động `(size, align)` tại offset `8` và `16` để giải phóng vùng nhớ heap chính xác (`size == 0` cho kiểu ZST không cấp phát/không giải phóng heap), trong khi `view<dyn Tr>` và `mut_view<dyn Tr>` là các phép mượn không sở hữu tuân thủ kiểm tra vùng nhớ (`AX_REGION_*`).

---

## Normative Deliverables Summary

### 1. `spec/SPEC-63-dyn-trait-vtables.md`
- **Object-Safety Rules (`AXS-DYN-001`..`004`)**:
  - `AXS-DYN-001`: 5 necessary and sufficient conditions (`O1`–`O5`) for `trait Tr` to be object-safe (`REQ-CORE-3031`, `REQ-CORE-3037`, `ATRAIT-20..22`).
  - `AXS-DYN-002`: `where Self: Sized` method opt-out semantics (`null` vtable slot or omission; calling on `dyn Tr` rejected).
  - `AXS-DYN-003`: Associated types (`type Item = T`) permitted when fully specified at the `dyn Tr` site; associated `const` items make `Tr` non-object-safe.
  - `AXS-DYN-004`: Canonical diagnostic `AX_DYN_NOT_OBJECT_SAFE` with structured primary span, secondary violating-item span, and actionable `help:` notes (`REQ-CORE-3037`).
- **Fat-Pointer Representation & Unsizing Coercions (`AXS-DYN-010`..`012`)**:
  - `AXS-DYN-010`: `dyn Tr` is dynamically sized (`!Sized`) and valid only behind a pointer/carrier (`view<dyn Tr>`, `mut_view<dyn Tr>`, `Box<dyn Tr>`).
  - `AXS-DYN-011`: Canonical 16-byte, 8-byte-aligned two-word fat pointer `(data_ptr, vtable_ptr)` layout across `--interp` and native x86-64 (`REQ-CORE-3032`, `REQ-CORE-3036`, `REQ-ABI-068`).
  - `AXS-DYN-012`: Unsizing coercions (`view<T> -> view<dyn Tr>`, `mut_view<T> -> mut_view<dyn Tr>`, `mut_view<T> -> view<dyn Tr>`, `Box<T> -> Box<dyn Tr>`, and derived subtrait-to-supertrait upcasts) across all coercion sites (`REQ-CORE-3033`, `REQ-CORE-3038`, `REQ-CORE-3045`, `REQ-CORE-3046`).
- **Canonical Vtable Layout & Calling Convention (`AXS-DYN-020`..`024`)**:
  - `AXS-DYN-020`: Canonical `.rdata` header (`slot 0`: `drop_in_place: fn(PtrMut<u8>)`, `slot 1`: `size: usize`, `slot 2`: `align: usize`, followed by `super_vtables...` and `method_0..method_{M-1}`) (`REQ-CORE-3034`, `REQ-CORE-3041`).
  - `AXS-DYN-021`: Deterministic declaration-order method slots and concrete thunk ABI (`fn(Ptr<u8>, ...)` / `fn(PtrMut<u8>, ...)`).
  - `AXS-DYN-022`: `.rdata` read-only emission, deterministic mangled symbol `_AX_VTBL_<ConcreteTypeMangled>_as_<TraitPathMangled>`, and COMDAT/linker deduplication (`REQ-CORE-3042`).
  - `AXS-DYN-023`: HIR → MIR lowering contract (`Rvalue.Unsize`, `Rvalue.VtableLookup`, `Terminator.CallIndirect`) (`REQ-CORE-3039`, `REQ-CORE-3040`, `REQ-CORE-3043`).
  - `AXS-DYN-024`: Indirect call ABI on Windows x64 (`RCX = data_ptr`) and System V AMD64 (`RDI = data_ptr`) plus `--interp` parity (`REQ-CORE-3044`, `REQ-CORE-3049`..`3052`).
- **Vtable-Driven Dynamic Drop & Region Rules (`AXS-DYN-050`..`052`)**:
  - `AXS-DYN-050`: Concrete compiler-synthesized `drop_in_place_<T>` thunk executing `T.drop` and recursive field drop (`SPEC-12`) (`REQ-CORE-3035`, `REQ-CORE-3047`).
  - `AXS-DYN-051`: `Box<dyn Tr>` scope-exit/early-return/overwrite dynamic destructor invocation via `vtable_ptr.drop_in_place(data_ptr)` followed by `alloc_dealloc(data_ptr, size, align)` when `size > 0` (`REQ-CORE-3047`, `REQ-CORE-3048`).
  - `AXS-DYN-052`: Non-owning `view<dyn Tr>` / `mut_view<dyn Tr>` region lifetime tracking (`AX_REGION_*`) and zero-drop guarantee.

### 2. Index, Diagnostics & Invariants Synchronization
- **[spec/INDEX.md](file:///d:/projects/compiler/new%20lang/spec/INDEX.md)**:
  - Registered `spec/SPEC-63-dyn-trait-vtables.md` in §2 (`Domain Specifications`).
  - Registered `AXS-DYN-NNN` rule prefix in §4 (`Rule ID Prefix Registry`).
  - Added `SPEC-63` (`dyn Trait` object safety & vtable ABI) to the `Traits, generics` row in §5 (`Quick Lookup by Topic`).
- **[spec/diagnostics.md](file:///d:/projects/compiler/new%20lang/spec/diagnostics.md)**:
  - Documented `AX_DYN_*` category sub-prefix under `AXD-021`.
  - Added `AX_DYN_NOT_OBJECT_SAFE` (`ERROR`, `T058`) to §11 (`Trait & Generic Errors`) and cited `SPEC-63` in `## Sources`.
- **[spec/invariants.md](file:///d:/projects/compiler/new%20lang/spec/invariants.md)**:
  - Added `DYN` group to §1 header list.
  - Added §25 (`Dynamic Trait Objects & Vtable ABI (DYN)`) with `INV-DYN-001` (`since: T058`), `INV-DYN-002` (`since: T567`), `INV-DYN-003` (`since: T568`), and `INV-DYN-004` (`since: T569`), plus `0212` and `SPEC-63` in `## Sources`.

---

## Verification

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `COVERAGE OK` (`gaps: 0`, `32308` requirements verified).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T566`: Verified all 4 changed files match the task's `paths` and `locks` with `0` `REFUSED` lines.

## Files changed

- `spec/SPEC-63-dyn-trait-vtables.md`
- `spec/INDEX.md`
- `spec/diagnostics.md`
- `spec/invariants.md`

## Status

STATUS: COMPLETE round=0

