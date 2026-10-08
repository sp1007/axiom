## Tóm tắt
Kỹ sư báo cáo task T035a bị block do không thể chỉnh sửa `emit_ast.c` và `emit_hir.c` để xử lý các variant enum mới (`AX_EXPR_TUPLE`, v.v.) vì các file này không nằm trong `locks` hay `paths`. Việc cập nhật các hàm in AST/HIR này gắn liền với việc thêm các node AST/HIR mới để tránh lỗi `-Werror=switch`. Do đó, tôi đã quyết định thêm các file này vào danh sách `locks:` của T035a để kỹ sư có thể hoàn thành task. T035a đã được unblock lần 2.

## Quyết định và Lý do (Decision & Rationale)
**Options considered:**
1. Split the AST/HIR emit changes into a separate prerequisite task.
2. Add `emit_ast.c` and `emit_hir.c` to `locks:` of T035a so the current task can handle it.

**Decision:** Option 2.

**Rationale:** Modifying AST and HIR nodes inherently breaks `-Werror=switch` in the emit functions. Handling this in a separate task would either require intermediate broken builds or complex coordination. Allowing T035a to lock and edit the driver's emit functions is standard practice and keeps the AST addition atomically tied to its stringification. T035a's scope was extended to include these locks.

## Files changed
- _workspaces/tasks/todo/T035a-struct-syntax.md
