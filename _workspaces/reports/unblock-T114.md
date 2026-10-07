## Tóm tắt
Tác vụ T114 bị chặn do không có quyền cập nhật file kiểm thử `.mir` (do file này thuộc phạm vi của T116 đang chạy song song và T116 đã xoá file này). Quyết định: Cập nhật `paths` và `scope` của T114 để cho phép T114 xoá file `tests/mir/build/control_flow.ax` và `.mir` tương ứng, giúp tránh xung đột thay vì yêu cầu cập nhật file. Tác vụ đã được bỏ chặn (unblocked) thành công.

## Files changed
- _workspaces/tasks/todo/T114-vs0-fix-parser-expression-precedence-headers.md
