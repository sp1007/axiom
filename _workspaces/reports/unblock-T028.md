## Tóm tắt
Đã thêm `tests/run/basic` và `tests/conformance/vs0` vào mảng `paths` của task T028 để cho phép xoá các chỉ thị `native-after: T028` trong các test này, qua đó tháo gỡ khó khăn cho quá trình build native end-to-end. Đã chạy `taskctl.py unblock T028` thành công.

## Quyết định và Căn cứ
- **Lựa chọn:** Bổ sung trực tiếp thư mục `tests/run/basic` và `tests/conformance/vs0` vào cấu hình `paths` của T028 thay vì tạo task mới hay ghi đè toàn bộ cấu trúc.
- **Căn cứ:** Theo báo cáo từ agent, sự cố block xảy ra do T028 cần truy cập vào hai đường dẫn này để gỡ bỏ cờ `native-after: T028` khi backend native đã hoàn thiện. Đây là một sửa đổi phạm vi nhỏ phù hợp nhất với việc chỉnh sửa thuộc tính `paths` của file cấu hình task T028.

## Files changed
- _workspaces/tasks/todo/T028-axiom0-build-end-to-end-first-native-axiom-program.md
