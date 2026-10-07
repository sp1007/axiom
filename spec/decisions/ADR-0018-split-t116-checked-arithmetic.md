# ADR-0018: Split T116 Checked Arithmetic and Text Parser

## Tóm tắt
Nhiệm vụ T116 quá lớn và liên tục gặp lỗi QA (thất bại 3 lần do lỗi kiểm tra tràn số nguyên 32-bit trong `interp.c` và thiếu hỗ trợ `~`, `overflows(...)` trong `parse.c`). ADR này quyết định chia nhỏ T116: T116 sẽ tập trung vào việc thay đổi builder, đổi tên thành `AX_MIR_RVALUE_OVERFLOWS_BINARY_OP`, thêm `AX_MIR_TERM_ASSERT` vào verifier và print. Còn việc hỗ trợ text parser (trong `parse.c`) và interpreter semantics chi tiết (trong `interp.c`) sẽ được chuyển sang một task mới (T119) để giảm rủi ro và chia nhỏ công việc.

## Context
Task T116 was created to fix VS0 MIR builder issues, including bit-not lowering, exhaustive lowering (ICE), and adding checked-arithmetic asserts. During implementation, the task became too large and repeatedly failed QA due to:
1. `interp.c` incorrectly checking 32-bit unsigned overflow using `int32_t`, causing false panics for large additions.
2. `parse.c` lacking support for the bitwise NOT `~` operator.
3. `parse.c` lacking support for the new `overflows(...)` rvalue.

## Options Considered
1. **Force all fixes into T116**: Rescope T116 to clarify the exact fixes required for `interp.c` and `parse.c`. This risks the task remaining too large and complex for a single sitting.
2. **Split T116**: Move the `parse.c` text parser support and `interp.c` accurate overflow semantics into a new task (T119). T116 will only handle the builder changes, verifier updates, and basic struct additions.

## Decision
We choose Option 2. We will rescope T116 to cover:
- M1 (builder ~ lowers to bitwise NOT)
- M3 (exhaustive ICE)
- M2 (Rename `AX_MIR_RVALUE_CHECKED_BINARY_OP` to `AX_MIR_RVALUE_OVERFLOWS_BINARY_OP`, add `Assert` terminator to MIR structs, printer, and verifier).
- Basic `interp.c` dummy implementation (if needed to compile) but accurate overflow semantics are out of scope.

We will create T119 to cover:
- `parse.c` text parser support for `~` and `overflows(...)`.
- `interp.c` accurate unsigned/signed overflow semantics using `__builtin_*_overflow`.

## Consequences
- T116 becomes smaller and more focused, making it easier to pass QA.
- T119 will need to depend on T116.
- The full checked arithmetic end-to-end functionality will be completed after T119.

## Sources
- T116 QA failure report.
- `_workspaces/reports/T116-report.md`
- Unblocking protocol requirements.
