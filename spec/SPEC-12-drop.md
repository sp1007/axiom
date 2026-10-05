# SPEC-12: Drop Semantics and Elaboration

## Tóm tắt
Đặc tả này quy định hệ thống Deterministic Destruction (Drop). Mọi control-flow edge (bao gồm early return, break, panic) đều phải dọn dẹp tài nguyên thông qua Drop elaboration. Phân biệt rõ Custom Drop (người dùng viết) và Compiler-derived Drop. Gọi `drop(x)` tường minh sẽ dọn dẹp tài nguyên nhưng không nhất thiết phải giải phóng bộ nhớ ngay lập tức (phụ thuộc vào MIR drop flags). Khi panic, chương trình thực hiện dọn dẹp theo drop stack; nếu panic trong lúc Drop đang unwind thì sẽ abort để tránh hậu quả khó lường.

## 1. Deterministic Destruction

### AXS-DROP-001: Automatic Cleanup on Every Edge
Destructors are automatically invoked when an owned place goes out of scope. This cleanup MUST occur on all control-flow edges, including normal returns, early returns, loop breaks, and panics.

### AXS-DROP-002: Deterministic Drop Order
Local variables are dropped in the exact reverse order of their declaration within the block. Fields of structs are dropped in the order they are declared in the struct definition.

### AXS-DROP-003: Uninitialized and Moved Places
Places in the `UNINIT` or `MOVED` state MUST NOT be dropped. If a place's state is dynamic (e.g., due to a branch), the compiler must elaborate *Drop Flags* to check the state at runtime before executing the destructor.

### AXS-DROP-004: Explicit `drop(x)`
An explicit call to `drop(x)` immediately triggers the destructor (per ADR-0006 §1). 
- It consumes ownership of `x` (transitions to `MOVED`/`DROPPED`).
- It does not imply immediate deallocation of memory, only the semantic execution of the drop logic.

### AXS-DROP-005: Generic Drop Glue and `drop_in_place`
When generic types or traits are dropped, the compiler synthesizes drop glue (`drop_in_place`) to recursively invoke destructors for inner fields.

### AXS-DROP-006: Panic Interaction
Drop is not a recoverable-error mechanism. If a panic occurs, the unwinder executes pending drops. If a destructor panics while the system is already unwinding (double panic), the process MUST immediately abort.

## 2. Requirements for MIR

The MIR must carry:
- **Drop Flags**: Boolean/bitfield indicators embedded by Drop Elaboration for places with dynamic initialization states.
- **Drop Terminators**: Specific MIR terminators or instructions indicating the cleanup path, separate from regular function calls.

## 3. Test Matrix (Drop)

| Rule | Program Pattern | Valid? | Task |
| --- | --- | --- | --- |
| AXS-DROP-001 | `let a = Droppable(); if c { return; }` | Yes (Compiler inserts drop at return) | T049 |
| AXS-DROP-002 | `let a = Droppable(); let b = Droppable();` | Yes (b drops before a) | T049 |
| AXS-DROP-003 | `let a = Droppable(); let b = a;` | Yes (a is not dropped at scope end) | T049 |
| AXS-DROP-004 | `let a = Droppable(); drop(a); drop(a);` | No (Double explicit drop/use after move) | T049 |
| AXS-DROP-005 | `struct S<T> { a: T }; let s = S(Droppable());` | Yes (Generic drop glue called) | T054b |
| AXS-DROP-006 | `impl Drop for S { panic(); } let s = S(); panic();` | Aborts on double panic | T049 |

## References
- `docs/base/specs/0178`, `docs/base/specs/0030`, `docs/base/specs/0118`, `docs/base/tasks/0674`
- [ADR-0014](../decisions/ADR-0014-ownership-capabilities-drop-semantics.md)
