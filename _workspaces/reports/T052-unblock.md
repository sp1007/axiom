# T052 Unblock

## Tóm tắt
QA phát hiện hai vấn đề trong quá trình port test: (1) compiler cho phép dùng biến sau khi đã move một phần (partial move), (2) test e003 mong muốn NLL (last-use analysis) cho view.
Giải pháp: Tuân thủ mô hình semantic đơn giản (không borrow checker).
- Viết ADR 0006: Khẳng định view chỉ có lexical scope (không có NLL) và partial move làm mất giá trị (invalidate) cả struct.
- Tạo task `T052a` để sửa compiler về vấn đề partial move.
- Thêm `T052a` vào dependency của T052 và cập nhật Implementation Plan cho test e003.

## Decision and Rationale
The failing tests revealed confusion around Axiom's semantic model. A strict, simple capability model ("ownership ≠ borrow checker") dictates:
1. No Non-Lexical Lifetimes (NLL): The `e003.ax` test erroneously assumes last-use analysis. Views are strictly bound to their lexical scope, so the test should either explicitly scope the view or expect `AX_CAP_CONFLICT_MUT`.
2. Partial move invalidation: The compiler's acceptance of `partial_002.ax` is an implementation bug. A partial move out of an aggregate invalidates the entire aggregate for by-value use.

I have created `docs/adr/0006-ownership-semantics.md` to codify this architecture decision.
I split out the compiler fix into `_workspaces/tasks/todo/T052a-fix-partial-moves.md` and made T052 depend on it. T052's implementation plan was also updated to address the `e003.ax` test.

## Files changed
- docs/adr/0006-ownership-semantics.md
- _workspaces/tasks/todo/T052a-fix-partial-moves.md
- _workspaces/tasks/doing/T052-p6-gate-adversarial-semantic-suite.md
- _workspaces/reports/T052-unblock.md

STATUS: UNBLOCKED
