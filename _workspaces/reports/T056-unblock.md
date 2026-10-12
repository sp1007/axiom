## Tóm tắt
T056 bị chặn do sự nhầm lẫn giữa tên file (chứa `dynamic-dispatch-vtables`) và nội dung thực tế của task (chỉ bao gồm associated items, default methods, v.v.). Quyết định: Thêm ghi chú vào task T056 để xác nhận dynamic dispatch nằm ngoài phạm vi, và tạo ADR-0009 để làm rõ việc hoãn triển khai dynamic dispatch sang giai đoạn sau. T056 hiện đã sẵn sàng để tiếp tục.

## Analysis
The implementation agent was confused by the mismatch between the file name (`T056-traits-dynamic-dispatch-vtables.md`) and the task scope. It attempted to implement dynamic dispatch and vtables in C11, but couldn't find the relevant specs, causing it to block. 

To unblock:
1. Updated `T056-traits-dynamic-dispatch-vtables.md` to explicitly state in the `Out of scope` section that dynamic dispatch, trait objects, and vtables are out of scope, despite the legacy filename.
2. Created `docs/adr/ADR-0009-trait-dynamic-dispatch.md` to codify the decision that dynamic dispatch is deferred to a future task and requires its own explicit C11 implementation spec.

## Files changed
- _workspaces/tasks/doing/T056-traits-dynamic-dispatch-vtables.md
- docs/adr/ADR-0009-trait-dynamic-dispatch.md

STATUS: UNBLOCKED
