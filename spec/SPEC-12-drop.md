# SPEC-12: Drop Semantics and Elaboration

## Tóm tắt
Đặc tả này quy định hệ thống Deterministic Destruction (Drop). Mọi control-flow edge (bao gồm early return, break, panic) đều phải dọn dẹp tài nguyên thông qua Drop elaboration. Phân biệt rõ Custom Drop (người dùng viết) và Compiler-derived Drop. Gọi `drop(x)` tường minh sẽ dọn dẹp tài nguyên nhưng không nhất thiết phải giải phóng bộ nhớ ngay lập tức (phụ thuộc vào MIR drop flags). Khi panic, chương trình thực hiện dọn dẹp theo drop stack; nếu panic trong lúc Drop đang unwind thì sẽ abort để tránh hậu quả khó lường.
Phép gán drop giá trị cũ của place (kể cả qua `view`/`mut_view`), còn ghi qua con trỏ thô thì không bao giờ drop (AXS-DROP-007); trait `Drop` của ngôn ngữ được nhận diện theo phân giải tên, không theo hậu tố `.Drop` (AXS-DROP-008) — ADR-0036.

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

### AXS-DROP-007: Drop on Assignment; Raw-Pointer Stores Never Drop
An assignment `place = rhs` whose place type needs drop runs, in this order (SPEC-03 AXS-SEM-043):
evaluate `rhs` into a temporary; evaluate the place (base, indices, bounds checks); drop the old
value of the place (`DROP(place)`, drop-flag aware: an uninitialised or moved place is not dropped,
AXS-DROP-003); move the temporary in. This applies to locals, fields, tuple fields, array/slice
elements and to every place reached through a `view`/`mut_view` (explicit `*m = v`, `w.f = v`,
`self.f = v` with `self: mut_view<Self>`, nested `o.h.inner = v`, an element of a `mut_view<[T]>`):
a view is only created from an initialised owner place (SPEC-11 AXS-CAP-004), so its pointee holds
a live value. A store whose place goes through a `Deref` of a raw pointer (`*p = v`, `(*p).f = v`,
`p.f = v` with `p: *mut S`) is a **raw store**: the old bytes are overwritten and never dropped,
because a raw pointer may target uninitialised memory (`heap_alloc` results, `Vec` spare capacity).
Code that needs the old value dropped calls `drop_in_place(p)` before the store. The decision is
taken from the types along the place's projection path. [ADR-0036 §1; T141 round 2]

### AXS-DROP-008: Identity of the Language `Drop`
An `impl Drop for T` declares the destructor of `T` iff its trait path resolves to the prelude lang
item `Drop` (SPEC-04 AXS-EXT-023). In axiom0/axiomc v0.1 that is the bare name `Drop` when no item
named `Drop` is declared in or imported into the module. A qualified path to a user trait
(`impl m.Drop for T`) or a shadowing user `trait Drop` is an ordinary trait: its `drop` method is an
ordinary method, is not called at scope end, and makes `T` neither droppable nor non-`Copy`.
[ADR-0036 §5; T141 round 1]

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
| AXS-DROP-007 | `fn set(self: mut_view<Self>) { self.inner = make(7); }` (old inner id 1) | Yes (prints 7 then drops 1) | T141 |
| AXS-DROP-007 | `let p: *mut S = ...; unsafe { *p = S { id: 2 }; }` | Yes (old value not dropped) | T141 |
| AXS-DROP-008 | `trait Drop` in module `m`; `impl m.Drop for S { fn drop(...) { print } }` | Yes (no destructor output at scope end) | T158 |

## References
- `docs/base/specs/0178`, `docs/base/specs/0030`, `docs/base/specs/0118`, `docs/base/tasks/0674`
- [ADR-0014](../decisions/ADR-0014-ownership-capabilities-drop-semantics.md)
- [ADR-0036](../decisions/ADR-0036-assignment-drop-raw-store-cap-followups.md)
