## Tóm tắt
T114 bị chặn do lỗi phân tích cú pháp khi gặp hàm thiếu phần thân `fn n()`, dẫn đến sự cố sập chương trình ở giai đoạn tạo MIR. Lỗi này đã bị mất trong quá trình tái cấu trúc mã (refactoring) của T114. Để giải quyết vấn đề, tôi đã tạo một task mới (T118) chuyên trách sửa lỗi thiếu thân hàm này, và thiết lập để T114 phụ thuộc vào T118. Việc tách riêng giúp giảm độ phức tạp cho T114 và đảm bảo lỗi được sửa triệt để. T114 hiện đã được mở khóa (unblocked) thành công.

## Quyết định
- **Tùy chọn đã xem xét**:
  - (a) Mở rộng phạm vi của T114 để bao gồm việc sửa lỗi `fn n()`.
  - (b) Tạo một task tiền quyết định (prerequisite task) riêng biệt để xử lý lỗi này và đặt T114 phụ thuộc vào nó.
- **Lý do**: Lỗi trình phân tích cú pháp không báo lỗi khi thiếu thân hàm là một vấn đề độc lập, không liên quan trực tiếp đến việc xử lý độ ưu tiên biểu thức và cấu trúc điều khiển của T114. Việc tách thành task T118 (tùy chọn b) giúp giảm thiểu rủi ro, không làm quá tải T114, và giúp tập trung khắc phục chính xác lỗi đã bị mất trong quá trình refactoring trước đó.
- **Hành động**: Đã tạo task T118, thêm T118 vào danh sách `depends` của T114 và chạy `taskctl.py unblock T114`.

## Files changed
- _workspaces/tasks/todo/T114-vs0-fix-parser-expression-precedence-headers.md
- _workspaces/tasks/todo/T118-fix-parser-missing-fn-body.md
