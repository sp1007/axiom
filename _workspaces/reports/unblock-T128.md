# T128 unblock report

## Tóm tắt
Việc triển khai hàm `drop` (Explicit Drop) trong T128 gặp lỗi do vi phạm phạm vi (scope): các file `resolve.c`, `typeck.c` bị sửa đổi nhưng không có trong `paths`, đồng thời làm hỏng 11 golden tests do thứ tự ID của symbol thay đổi khi thêm `drop` vào prelude. Ngoài ra, yêu cầu in kết quả để kiểm chứng (acceptance criteria) không được thực hiện.
Giải pháp: Tạo task tiền đề T132 để xử lý phần frontend (thêm `drop` vào prelude, xử lý name resolution, typeck, và cập nhật các golden tests). T128 được chuyển về trạng thái unblocked, thiết lập phụ thuộc vào T132, và làm rõ scope chỉ xử lý phần sinh mã MIR, LIR, cùng việc thực thi trong trình thông dịch (bắt buộc phải ghi log rõ ràng để đáp ứng tiêu chí nghiệm thu). Quyết định được ghi nhận trong ADR-0030.

## Files changed
- spec/decisions/ADR-0030-unblock-t128-drop-frontend.md
- _workspaces/tasks/todo/T132-frontend-drop.md
- _workspaces/tasks/todo/T128-basic-drop-elaboration.md
