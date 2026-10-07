## Tóm tắt
Đã thêm T114 vào danh sách phụ thuộc (`depends`) của T116 để giải quyết xung đột file (lock conflict) do cả hai task cùng ghi vào các file `tests/mir/build/control_flow.ax` và `.mir`. T116 sẽ chờ T114 hoàn thành việc thay đổi các file này rồi mới chạy, tránh được lỗi QA. Trạng thái của T116 đã được chuyển về `todo` và các script kiểm tra đã chạy thành công.

## Files changed
- _workspaces/tasks/todo/T116-vs0-fix-mir-builder-bitnot-asserts.md
