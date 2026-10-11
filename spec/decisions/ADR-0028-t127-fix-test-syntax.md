# ADR-0028 — T127 Fix C-driver Test Syntax

## Tóm tắt
(Vietnamese summary)
Lỗi cú pháp trong chuỗi kiểm thử phân tích MIR của C-driver (`fn main` thay vì `mir_body`) đã gây ra ICE, khiến QA của T127 thất bại. Quyết định sửa đổi chuỗi mã trong kiểm thử để khớp với cú pháp chính xác mà `ax_mir_parse` mong đợi (sử dụng khối `mir_body`).

## Context
Task T127 was blocked because QA failed 3 times: "C-driver MIR parse test string uses wrong syntax (fn main instead of mir_body), causing ICE." The error stems from `tests/ui/drop/cdriver_mir_drop.c`, where a manually embedded MIR string used invalid syntax (`fn main() -> unit {`) instead of the required `mir_body {` wrapper.

Options considered:
1. Drop the test completely to reduce maintenance overhead.
2. Fix the syntax within the test string to align with `parse.c` expectations and keep testing the parser infrastructure.

## Decision
We chose option 2. The syntax within `cdriver_mir_drop.c` has been corrected to use `mir_body {` and valid `type#` and `bbX: {` blocks. This preserves the parser testing functionality without introducing complex new logic.

## Consequences
- The test now passes.
- We do not need to split or rescope T127; it can simply be unblocked after this inline fix.
