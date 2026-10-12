## Tóm tắt

Task T052a bị chặn (blocked) vì file bài test yêu cầu trong mục Acceptance (`tests/conformance/adversarial/partial_002.ax`) nằm ngoài danh sách `paths` được cấu hình cho task. Điều này khiến quá trình QA báo lỗi do thay đổi file không được phép.

## Decision and Rationale

The implementation correctly identified that the compiler already implements the requested behavior (propagating `AX_OWN_PARTIAL` to the parent struct), so no C code changes are needed. However, the test must still be added to satisfy the acceptance criteria.

I have updated `_workspaces/tasks/doing/T052a-fix-partial-moves.md` to include `tests/conformance/adversarial` in its `paths:` array. This resolves the QA path violation and allows the implementation agent to successfully submit the required test file.

## Files changed
- _workspaces/tasks/doing/T052a-fix-partial-moves.md

STATUS: UNBLOCKED
