# T556 Report — E14.2 — Canonical compile-time reflection API, @derive framework & typed codegen boundary specification (SPEC-61)

## Tóm tắt
Đã biên soạn đặc tả chuẩn `spec/SPEC-61-reflection-derive.md` (`AXS-RFL-001`..`AXS-RFL-052`) cho phân hệ `E14.2` (Phase `P14`), bao phủ toàn bộ 26 yêu cầu trực tiếp của `T556` (`REQ-CTM-019`..`022`, `REQ-CTM-039`..`040`, `REQ-CORE-602`..`621`) cũng như hợp đồng kiến trúc đầy đủ cho `T557`–`T560` (`REQ-CTM-043`, `REQ-CTM-045`, `REQ-CORE-622`..`682`, `REQ-CORE-2143`..`2149`, `REQ-CORE-2170`..`2179`):
- Chốt kiến trúc 6 cơ chế tách biệt (`AXS-RFL-001`) và mô hình phản chiếu tại thời điểm biên dịch làm mặc định (`AXS-RFL-002`..`004`): `type_info<T>() -> TypeInfo`, `type_name<T>()`, `fields_of<T>()`, `variants_of<T>()`, `attributes_of<T>()`, `implements<T, Trait>()` đọc trực tiếp dữ liệu ngữ nghĩa của trình biên dịch (`CompilerDB`), xóa sạch ở runtime không cần header đối tượng hay RTTI ẩn, và bắt buộc opt-in tường minh (`@reflect(runtime)` / `AX_REFLECT_RUNTIME_NOT_ENABLED`) khi cần xuất siêu dữ liệu runtime.
- Chốt quy tắc bảo toàn phạm vi hiển thị (`AXS-RFL-010`, `AX_REFLECT_PRIVATE_FIELD`), thứ tự khai báo nguồn tất định (`AXS-RFL-011`, `AREFLECT-26..27`), và hợp đồng truy vấn bố cục (`AXS-RFL-012`: `size_of<T>()`, `align_of<T>()`, `offset_of<T, F>()` tuân thủ `@repr`, khóa thứ tự trường khi offset đã được quan sát theo `REQ-CTM-020..021`, và báo lỗi `AX_REFLECT_UNSPECIFIED_LAYOUT` khi bố cục không xác định).
- Chốt khung dẫn xuất có kiểu `@derive` và ranh giới sinh mã (`AXS-RFL-020`..`024`): cấm macro thay thế văn bản và cấm đột biến AST/HIR/MIR tùy ý (`REQ-CTM-019`, `AMETA-50..54`); bắt buộc mọi khai báo sinh ra đi qua toàn bộ quy trình phân giải tên, giải ràng buộc trait, kiểm tra kiểu, ownership, capability, đồng thời (`Send`/`Share`), FFI/ABI, GPU và `Verified MIR` (`REQ-CTM-040`, `AMETA-41..49`); gắn truy vết nguồn gốc `GenProvenanceId` (`AX_DERIVE_FIELD_BOUND`, `AX_DERIVE_CONFLICT`, `AX_DERIVE_CYCLE`, `AX_DERIVE_UNSUPPORTED_ITEM`); và định nghĩa `std.reflect` + `@derive(Debug, Eq, Ord, Hash, Clone, Default, Serialize, Deserialize)` với thuộc tính `@rename`, `@skip`, `@default`.
- Cập nhật `spec/INDEX.md`, `spec/diagnostics.md` (`AX_REFLECT_*`, `AX_DERIVE_*`), và `spec/invariants.md` (`INV-RFL-001`..`004`).

## Summary
Authored `spec/SPEC-61-reflection-derive.md` (`AXS-RFL-001`..`AXS-RFL-052`) and updated `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md` to establish the canonical compile-time reflection, `@derive`, and typed codegen boundary specification for E14.2 (`T556`–`T560`).

## Files changed
- ./spec/SPEC-61-reflection-derive.md
- ./spec/INDEX.md
- ./spec/diagnostics.md
- ./spec/invariants.md

## Tests
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `gaps: 0`, `COVERAGE OK`.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
- `python tools/gatecheck.py --no-run`: `MS-P1`..`MS-P10b PASS` (`exit 0`).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T556`: `0 REFUSED`.

## Spec deviations
none

## Follow-ups
none

STATUS: COMPLETE round=0
