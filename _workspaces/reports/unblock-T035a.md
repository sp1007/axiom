## Tóm tắt
Nhiệm vụ T035a bị chặn do thiếu quyền truy cập vào các tệp type-checking và lowering. Tuy nhiên, việc phân giải tên (name resolution) cho struct field đòi hỏi type-checking phải hoạt động. Do đó, phạm vi của T035a đã được mở rộng để bao gồm cả type-checking và HIR lowering thay vì chia nhỏ nhiệm vụ. Các đường dẫn `bootstrap/axiom0/src/hir` và `bootstrap/axiom0/src/types` đã được thêm vào `paths` của nhiệm vụ T035a.

## Decision
- **Option A**: Add missing paths (`hir` and `types`) to T035a so it can implement type-checking and lowering.
- **Option B**: Split T035a further to separate syntax from type-checking.

**Rationale**: Name resolution for struct field accesses (`x.y`) inherently depends on type-checking the base expression (`x`). Thus, separating syntax and name resolution from type-checking is impractical, especially since the UI tests require type-checking to pass. Expanding T035a's scope to include lowering and type-checking is the correct architectural decision. 
The task's scope description and `paths` have been updated accordingly, and the task has been unblocked.

## Files changed
- _workspaces/tasks/todo/T035a-struct-syntax.md
