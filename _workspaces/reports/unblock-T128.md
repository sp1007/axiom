# Unblock T128

## Tóm tắt
T128 đã thất bại QA 3 lần do các lỗi double-drop, hồi quy (regression) được che giấu bởi các thay đổi kiểm thử không được phép, và các lỗi logic. Việc xử lý cả ba yêu cầu (drop rõ ràng, dọn dẹp khối lệnh ẩn, và hàm hủy) cùng lúc là quá phức tạp. Quyết định (ADR-0029) là thu hẹp phạm vi của T128 để chỉ xử lý builtin `drop(x)` rõ ràng. Yêu cầu dọn dẹp khối lệnh ẩn và hàm hủy được tách ra thành một task mới (T131). T128 đã được unblock thành công và sẵn sàng để tiếp tục phát triển.

## Files changed
- `_workspaces/tasks/todo/T128-basic-drop-elaboration.md`
- `_workspaces/tasks/todo/T131-implicit-drop.md`
- `spec/decisions/ADR-0029-t128.md`
- `spec/ROADMAP.md`
