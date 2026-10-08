## Tóm tắt
Thêm đường dẫn `tests/mc/frame`, `tests/mir/build` vào `paths:` và file `bootstrap/axiom0/src/driver/emit_obj.c` vào `locks:` của T029 để cấp quyền sửa lỗi determinism của file PE (zero out timestamp) và cập nhật các test C bị hỏng, giúp tiếp tục thực thi T029.

## Quyết định và lý do
- Cập nhật phạm vi file (paths và locks) của T029 để bao gồm các file bị thiếu thay vì tạo một task nhỏ hoặc sửa lại task. Điều này là đơn giản nhất và giữ cho PR gọn gàng khi mục tiêu của T029 cần các thay đổi đó để sửa test C và determinism file PE.
- T029 được mở block (unblocked).

## Files changed
- _workspaces/tasks/todo/T029-vs1-gate-differential-interp-vs-native-determinism.md
