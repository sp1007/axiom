## Tóm tắt
(Vietnamese)
Việc triển khai hàm `drop` (Explicit Drop) trong T128 gặp lỗi do vi phạm phạm vi (scope): các file `resolve.c`, `typeck.c` bị sửa đổi nhưng không có trong `paths`, đồng thời làm hỏng 11 golden tests do thứ tự ID của symbol thay đổi khi thêm `drop` vào prelude. Ngoài ra, tiêu chí nghiệm thu yêu cầu phải in ra màn hình để kiểm chứng nhưng phần implement chưa thực hiện.
Giải pháp: Tạo task tiền đề T132 để xử lý phần frontend (thêm `drop` vào prelude, resolve, typeck, và cập nhật 11 golden tests). T128 sẽ phụ thuộc vào T132 và chỉ tập trung vào phần MIR/LIR cùng trình thông dịch, với yêu cầu in log `drop` rõ ràng khi thực thi.

## Context
T128 (Explicit Drop Builtin) failed QA in Round 2 because:
1. It illegally modified `resolve.c`, `typeck.c`, and `types.h` (outside its locked/owned paths) to introduce the `"drop"` builtin.
2. Adding `"drop"` shifted symbol IDs, breaking 11 golden tests, which were not fixed.
3. The acceptance criterion "observable via print" was not met because dropping a primitive just compiled to a GOTO without runtime observability.

## Options
1. **Rescope T128**: Expand T128's `paths` to include frontend files and golden tests, and instruct the engineer to fix the tests and AC.
2. **Prerequisite Task (Chosen)**: Extract the frontend addition of the `"drop"` builtin and the associated golden test updates into a new prerequisite task T132. T128 then focuses solely on MIR generation, lowering, and interpreter implementation of drop semantics.

## Decision
Create T132 "Frontend explicit drop builtin" as a prerequisite for T128. T132 will add `"drop"` to the prelude, handle name resolution and type checking, and update all affected golden tests. T128 will be unblocked and will depend on T132, with a clarified requirement to add interpreter logging or similar mechanisms to make `drop(x)` observable.

## Consequences
- Keeps tasks focused and limits the blast radius of changes.
- Frontend changes and golden test updates are cleanly separated from middle-end semantics.
- Fixes the scope violation and explicitly guides the engineer on how to satisfy the acceptance criteria.

## Sources
- [T128-qa.md, Round 2 findings]
