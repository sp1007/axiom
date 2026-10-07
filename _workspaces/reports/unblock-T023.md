## Tóm tắt
Tác vụ T023 bị chặn do lỗi phân tích cú pháp trong MIR parser (`bootstrap/axiom0/src/mir/parse.c`) nơi ký tự `<` được khớp trước `<<`, dẫn đến thất bại khi phân tích các tệp MIR hợp lệ. Thêm vào đó, tác nhân cần thêm chỉ thị `// emit: lir` vào các bài kiểm tra trong thư mục `tests/run/basic` nhưng đang bị khóa không thể truy cập.

Để gỡ lỗi (unblock), tệp `bootstrap/axiom0/src/mir/parse.c` đã được thêm vào danh sách `locks` (vì đây là tệp dùng chung) và `tests/run/basic` đã được thêm vào danh sách `paths` của tác vụ T023. Điều này cho phép tác nhân trực tiếp sửa lỗi trong parser và cập nhật các tệp kiểm tra cần thiết mà không phải tạo thêm tác vụ phụ. Tác vụ T023 đã được unblock thành công và chuyển về trạng thái sẵn sàng.

## Lựa chọn và lý do (Options and rationale)
- **Phương án 1 (Đã chọn):** Bổ sung `bootstrap/axiom0/src/mir/parse.c` vào `locks` và `tests/run/basic` vào `paths` trong T023. Đây là giải pháp đơn giản nhất, giữ nguyên phạm vi công việc hiện tại đồng thời loại bỏ rào cản kỹ thuật một cách nhanh chóng.
- **Phương án 2:** Tách một tác vụ riêng biệt để sửa lỗi parser và gán nó làm tiền điều kiện cho T023. Phương án này mất thêm thời gian chờ đợi và dư thừa cho một bản vá parser nhỏ.

## Files changed
- _workspaces/tasks/todo/T023-lir-naive-mir-lir-lowering.md
