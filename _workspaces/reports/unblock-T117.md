## Tóm tắt
Nhiệm vụ T117 bị nghẽn (blocked) do các bài kiểm tra trong `tests/conformance/vs0` báo lỗi `XPASS`, nhưng agent không được quyền sửa các bài test này vì thư mục `tests/conformance/vs0` chưa nằm trong `paths:`.
Để giải quyết, tôi đã thêm `tests/conformance/vs0` vào `paths:` trong file tác vụ T117, đồng thời xóa giới hạn "Do not edit" ở phần Out of scope. Nhiệm vụ T117 hiện đã được unblock thành công.

## Quyết định & Tùy chọn (Options & Rationale)
- **Tùy chọn A**: Thêm `tests/conformance/vs0` vào `paths:` của T117 để cho phép agent bỏ đánh dấu `xfail` cho các test đã được sửa thành công.
- **Tùy chọn B**: Tách nhiệm vụ thành 2 task riêng.
- **Quyết định**: Chọn tùy chọn A vì lỗi `XPASS` chứng tỏ agent đã sửa code thành công, việc cập nhật trạng thái test là hành động đi kèm hiển nhiên và nhanh nhất. Không cần tách task vì việc xóa `xfail` rất nhỏ.

## Files changed
- _workspaces/tasks/todo/T117-vs0-fix-interp-width-bitwise-panic.md
