# ADR-0023: Rescope T047 to include locks for integration

## Tóm tắt
T047 bị chặn do thiếu quyền truy cập vào các file `own.c`, `typeck.c`, và `verify.c` để tích hợp phân tích khởi tạo và gỡ bỏ các kiểm tra cũ. Quyết định: thay vì chia nhỏ task, chúng ta mở rộng phạm vi của T047 bằng cách thêm các file này vào danh sách `locks:` của nó. Việc này giữ cho logic phân tích và việc tích hợp nó được thực hiện đồng bộ trong một task, đảm bảo có thể test được ngay.

## Context
Task T047 (Initialization analysis) implements definite initialization and re-initialization after move. The engineer implementing T047 reported being blocked because the task lacks paths/locks to `own.c`, `typeck.c`, and `verify.c` required to wire up the analysis in the compiler pipeline and remove the legacy initialization checks.

## Options
1. **Split T047**: T047 implements the core analysis logic, and a new follow-up task integrates it into the pipeline and removes legacy checks.
2. **Rescope T047 (Add locks)**: Extend the `locks:` array of T047 to include the required files so the integration can be done in the same task.

## Decision
Choose Option 2. Adding the files to `locks:` in T047 allows the task to fully integrate its analysis and prove it works via the existing test suite, satisfying R1 (Spec goes wide, implementation goes vertical). Splitting the integration would leave the analysis un-exercised in the first task.

## Consequences
- T047 will take locks on `bootstrap/axiom0/src/own/own.c`, `bootstrap/axiom0/src/types/typeck.c`, `bootstrap/axiom0/src/verify/verify.c`, and `bootstrap/axiom0/src/target/x64/verify/verify.c`.
- The task can unblock and proceed to completion.

## Sources
- T047 blocker report.
- R1: Spec goes wide, implementation goes vertical (0263 §52, 0152 §81).
- ADR-0005 §14 (Shared files go in locks:).
