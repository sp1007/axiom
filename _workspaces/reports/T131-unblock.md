## Tóm tắt
T131 bị thất bại QA do 3 nguyên nhân chính: (1) Trùng lặp symbol `drop` khi build native cho các struct có custom destructor; (2) QA kiểm thử drop cho mảng (array) trong khi tính năng này thuộc phạm vi của T130 (Aggregates); (3) Lỗi không khai báo các file đã sửa trong `paths` và report, cũng như không thể bỏ qua (xfail) các test bị lỗi sẵn do thiếu `paths`.
Giải pháp: Ban hành ADR-0032 quy định hàm `drop` của type `T` phải được đổi tên thành `T_drop` trong MIR/LIR để tránh trùng lặp symbol. Cập nhật task T131 để đưa `tests/run/slice` vào `paths`, và xác định rõ việc drop mảng/aggregate không nằm trong scope của T131 mà được hoãn sang T130. Kỹ sư cần đảm bảo liệt kê đầy đủ các file đã sửa trong report.

## Decision
- **Array Drops**: Array and aggregate drops are explicitly deferred to T130 as per ADR-0027. T131's scope is updated to exclude them, and QA is informed not to test them yet.
- **Destructor Mangling**: A new architectural decision (ADR-0032) mandates that custom destructors (`impl Drop for T`) must be emitted as `T_drop` in MIR and native code to resolve the duplicate symbol link errors.
- **Task Paths**: Added `tests/run/slice` to T131's `paths` so the engineer can mark the pre-existing failures as `xfail`.

## Files changed
- spec/decisions/ADR-0032-unblock-t131-drop-destructors.md
- _workspaces/tasks/doing/T131-implicit-drop.md

STATUS: UNBLOCKED
