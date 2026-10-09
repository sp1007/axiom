## Tóm tắt
T035c trước đó phụ thuộc vào T035b. Tuy nhiên, T035b đã được chia tách thành T035d (layout engine) và T035e (mir/oracle). Do đó, danh sách phụ thuộc của T035c cần được cập nhật lại để phụ thuộc trực tiếp vào T035d và T035e. Đã cập nhật depends trong file task của T035c thành [T035d, T035e].

## Decision and Rationale
- Option (c): Update prerequisite tasks. (Chosen) Since T035b was split into T035d and T035e, the blocked task T035c's dependency on T035b is obsolete. We replaced depends: [T035b] with depends: [T035d, T035e] so the task board scheduler will correctly wait for T035d and T035e to be done before T035c can be started.

## Files changed
- _workspaces/tasks/todo/T035c-struct-abi.md
