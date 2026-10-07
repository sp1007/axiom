## Tóm tắt
Tác vụ T116 bị chặn do 3 lỗi trong quá trình QA: sử dụng `fprintf`/`exit` sai quy định trong file của trình biên dịch (vi phạm INV-LAYER-006), dummy implementation của `OverflowsBinaryOp` trong interpreter bỏ qua tất cả assert, và thực hiện thay đổi trên `base.c` (không nằm trong danh sách được phép sửa). Giải pháp là cập nhật file T116 với hướng dẫn rõ ràng: dùng `AX_ICE` để văng lỗi, tự triển khai logic tràn số bằng C chuẩn trong `interp.c` (mà không đụng tới `base.c`), và xử lý in panic đúng quy cách mà không gọi `fprintf`.

## Files changed
- _workspaces/tasks/todo/T116-vs0-fix-mir-builder-bitnot-asserts.md
