# SPEC-11: Capability and Views

## Tóm tắt
Đặc tả này quy định hệ thống Capability (`view<T>` và `mut_view<T>`). Axiom không đòi hỏi lập trình viên viết lifetime annotation, compiler sẽ tự động kiểm tra owner-outlives. Chấp nhận *implicit temporary views* cho biểu thức và method receiver (chỉ sống đến hết statement). Cho phép *stored views* (view nằm trong struct) với điều kiện struct không outlive owner và cấm self-reference. Capability có tính chất độc quyền rạch ròi: `view` chỉ được đọc, `mut_view` đọc/ghi độc quyền.

## 1. Capability Semantics

Capabilities in Axiom represent access rights without transferring ownership.

### AXS-CAP-001: Read-Only Views
A `view<T>` grants shared, read-only access to a place. Ownership is not transferred.

### AXS-CAP-002: Exclusive Mutable Views
A `mut_view<T>` grants exclusive read-write access to a place.

### AXS-CAP-003: Conflict Matrix
- **READ + READ**: Allowed simultaneously (multiple `view<T>`).
- **READ + WRITE**: Rejected. A `mut_view<T>` conflicts with any active `view<T>`.
- **WRITE + WRITE**: Rejected. Only one active `mut_view<T>` is permitted at a time.
- **Unknown Overlap**: Unknown overlaps (e.g., dynamic indices) are assumed to conflict unless statically proven disjoint.

### AXS-CAP-004: Provenance and Owner-Outlives
Every capability must have a valid provenance back to an owned place. The compiler enforces that the active capability cannot outlive its originating owner place. An owner cannot invalidate a live capability (e.g., cannot move or drop an owner while a view is alive).

### AXS-CAP-005: Implicit Temporary Views
Temporary views may be created implicitly (e.g., `a.method()`) for convenience. These views are **ephemeral** and their lifetime is strictly bounded to the end of the enclosing statement.

### AXS-CAP-006: Stored Views and Arena Escapes
Views can be stored inside custom struct fields ("stored views"). 
- The compiler statically verifies that instances of such structs do not outlive the owner of the referenced data.
- Self-referencing stored views within the same struct are strictly forbidden.
- For arena-owned values (T073a), the same outlives rule prevents arena-escape.

### AXS-CAP-007: `Str` and Slices
`Str` and generic slices (`[T]`) are implemented as views (not as bare pointer + length) and are subject to all standard capability conflict and lifetime rules.

## 2. Requirements for MIR

The MIR must carry:
- **View/Region Annotations**: To statically track overlapping accesses.
- **Storage Markers**: Differentiating ephemeral temporaries vs durable paths for region bounding.

## 3. Test Matrix (Capability)

| Rule | Program Pattern | Valid? | Task |
| --- | --- | --- | --- |
| AXS-CAP-001 | `let a = NonCopy(); view_fn(a); let b = a;` | Yes (Ownership kept) | T048 |
| AXS-CAP-003 | `let a = NonCopy(); let v1 = view(a); let v2 = mut_view(a);` | No (Conflict) | T048 |
| AXS-CAP-004 | `let v: view<i32>; { let a = 1; v = view(a); }; print(v);` | No (Outlives owner) | T048 |
| AXS-CAP-005 | `let a = Object(); a.method();` | Yes (Implicit ephemeral) | T048 |
| AXS-CAP-006 | `struct S { v: view<i32> }; let s: S; { let a = 1; s = S(view(a)); }` | No (Stored view escapes owner) | T048 |
| AXS-CAP-007 | `let arr = [1, 2]; let s = arr.slice(); let m = mut_view(arr);` | No (Slice conflict) | T048b |

## References
- `docs/base/specs/0177`, `docs/base/tasks/0541`, `docs/base/tasks/0270`
- [ADR-0014](../decisions/ADR-0014-ownership-capabilities-drop-semantics.md)
