## Tóm tắt
Đã thêm `tests/typeck` và `tests/mir` vào mảng `paths` của task T034 để tác nhân (agent) có quyền cập nhật các tệp golden bị thay đổi do việc đánh số lại biến trong MIR.

## Quyết định và Giải trình (Decision & Rationale)
**Tình trạng chặn (Blocker):** Tác nhân báo cáo `STATUS: BLOCKED need paths for tests/typeck and tests/mir to update golden files shifted by MIR variable numbering`.
**Tùy chọn đã xem xét:**
1. Thêm `tests/typeck` và `tests/mir` vào mảng `paths` của file cấu hình tác vụ T034.
2. Chia nhỏ tác vụ hoặc tạo tác vụ mới (supersede).
**Quyết định (Decision):** Áp dụng Tùy chọn 1. Việc các tệp golden thay đổi khi triển khai mã là một hệ quả bình thường của việc đánh số lại trong MIR, do đó chỉ cần mở rộng quyền truy cập thư mục cho tác vụ hiện tại là đủ và phù hợp với giao thức gỡ chặn (unblocking protocol).

## Files changed
- _workspaces/tasks/todo/T034-numeric-types-casts-checked-arithmetic-panic-abort.md
