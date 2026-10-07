## Tóm tắt
Tác vụ T118 bị chặn do lỗi Catch-22: các thay đổi từ T114 chưa được merge khiến một số test (`tests/hir/control.ax`, `tests/hir/control.hir`, và `tests/mir/build/control_flow.ax`) bị lỗi, nhưng T118 lại không được phép sửa hay xfail các file này vì chúng nằm ngoài `paths:` đã quy định.
Giải pháp là bổ sung các file test này vào `paths:` của T118 trong file task, cho phép agent phụ trách T118 xfail chúng một cách hợp lệ mà không vi phạm quy tắc phạm vi (scope).
Các script kiểm tra `taskctl.py validate` và `harness_check.py` đã chạy thành công. Trạng thái của tác vụ T118 đã được cập nhật thành unblocked.

## Files changed
- _workspaces/tasks/todo/T118-fix-parser-missing-fn-body.md
