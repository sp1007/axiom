---
slug: unblock-t131-drop-destructors
date: 2026-10-12
status: accepted
---
# ADR-0032: Unblock T131 - Destructor mangling and Array drops

## Tóm tắt
T131 bị thất bại QA do 3 nguyên nhân chính: (1) Trùng lặp symbol `drop` khi build native cho các struct có custom destructor; (2) QA kiểm thử drop cho mảng (array) trong khi tính năng này thuộc phạm vi của T130 (Aggregates); (3) Lỗi không khai báo các file đã sửa trong `paths` và report.
Quyết định:
1. Quy định rõ việc mangling symbol cho destructor: hàm `drop` của type `T` phải được đổi tên thành `T_drop` trong MIR/LIR để tránh trùng lặp linker symbol.
2. Khẳng định drop cho mảng và aggregate được hoãn sang T130. T131 không được yêu cầu hỗ trợ drop cho mảng.
3. Bổ sung `tests/run/slice` vào `paths` của T131 để kỹ sư có thể bỏ qua (xfail) các test bị lỗi sẵn.

## Context
Task T131 (Implicit Block Drop and Destructors) failed QA twice. The reported issues include:
1. **Duplicate symbol `drop`:** In native compilation, implementing `impl Drop for S` results in a function named `drop`. Multiple structs implementing `Drop` cause linker symbol collisions (`duplicate symbol: drop`).
2. **Array Drops failed:** QA added `qa_array_drop.ax` and failed the task because arrays were not dropped element-wise. However, arrays are aggregates, and aggregate drop is explicitly deferred to T130 (Aggregates and Conditional Moves) according to ADR-0027.
3. **Pre-existing test failures:** Pre-existing failures in `tests/run/slice/*.ax` block the test suite, but the engineer could not add `// xfail: T126` to them because `tests/run/slice` was not in the task's `paths`.
4. **Report inaccuracies:** The engineer modified files within the `paths` (`driver.h`, `builder.c`) but failed to list them in the task report, causing a taskctl refusal.

## Options Considered
**Destructor Mangling:**
- **Option A:** Introduce general C++-like mangling for all methods. (Overkill for current stage).
- **Option B:** Explicitly mangle destructors as `<TypeName>_drop` (e.g., `S_drop`) at the MIR/LIR level.

**Array Drops:**
- **Option A:** Expand T131 to support array drops. (Violates ADR-0027 task split).
- **Option B:** Strictly enforce the ADR-0027 task boundaries and defer array drops to T130.

## Decision
1. **Adopt Option B for Mangling:** Custom destructors defined via `impl Drop for T { fn drop(...) }` must have their symbol emitted as `T_drop` (e.g., `S_drop`) in MIR and native code.
2. **Adopt Option B for Array Drops:** Array and aggregate element-wise dropping is strictly out-of-scope for T131. QA must not test array drops until T130.
3. **Update T131 Task:** Add `tests/run/slice` to the task `paths`. Clarify the scope to explicitly exclude array drops.

## Consequences
- Resolves the duplicate symbol linking error.
- Reduces the complexity of T131 back to its intended scope (nominal types only).
- Allows the engineer to `xfail` the blocking slice tests.
- Re-enforces strict adherence to file tracking in the task report.

## Sources
- ADR-0027 (Split Drop Elaboration Task)
- T131 QA and Implementation Reports
