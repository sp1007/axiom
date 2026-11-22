# SPEC-10: Ownership and Place Model

## Tóm tắt
Đặc tả này chuẩn hóa mô hình Ownership của Axiom (lưu ý: Ownership ≠ Borrow Checker). Nó định nghĩa Place Model, các trạng thái khởi tạo (UNINIT, OWNED, MOVED) và quy tắc partial move, copy vs move semantics. Điểm quan trọng là Move không bắt buộc sinh ra physical copy trong MIR, tuỳ thuộc vào backend. Custom Drop ngăn cấm partial move. Phải thiết kế sao cho compiler đảm nhiệm tính đúng đắn thay vì bắt lập trình viên viết annotation. Gán lại chỉ khôi phục đúng đường dẫn được gán; ghi qua chỉ số (`a[i] = v`, `a[i].f = v`) không bao giờ khôi phục mảng và bị từ chối nếu mảng đã bị move (AXS-OWN-006, triage-1122).

## 1. Place Model & Ownership State

Axiom separates the syntactic expression from the semantic "Place".
A **Place** is a path to a memory location (e.g., `x`, `x.field`, `*p`, `arr[0]`).

### AXS-OWN-001: Unique Active State
Every owned value or place has a unique active ownership state. The fundamental states are:
- `UNINIT`: Uninitialized.
- `OWNED`: Fully owned and initialized.
- `MOVED`: The ownership has been transferred to another place.
- `PARTIAL`: The place is partially moved (some fields moved, some owned).

### AXS-OWN-002: Move Semantics
Assignment `x = y` or passing by value transfers ownership if `y`'s type is not `Copy`.
A moved value cannot be read or moved again.

### AXS-OWN-003: Copy Semantics
Types implementing the `Copy` trait do not transfer ownership upon assignment or argument passing. The original place remains `OWNED`.
Composite types: a fixed array `[N]T` is `Copy` if and only if `T` is `Copy` (an array of a non-Copy type moves); tuples and closures likewise follow their components. A by-value use of a Copy array emits `MIR_OP_COPY` (the backend may elide the physical copy). `str` is never `Copy`. Consequence: moving a Copy array does not invalidate a view into it (the owner stays `OWNED`), so AXS-CAP-004 `AX_CAP_OUTLIVES_OWNER` tests must move a non-Copy owner. (ADR-0044 §3; implemented by T498; tests `tests/run/numeric/mixed_int_matrix/array_copy.ax`, `tests/run/slice/copy_array_owner_view.ax` (T498d).)

### AXS-OWN-004: Partial Move
A struct value can be partially moved if specific fields are accessed and moved. The remaining unmoved fields retain their `OWNED` state. The parent struct transitions to `PARTIAL`.

### AXS-OWN-005: Custom Drop Forbids Invalid Partial Move
If a struct implements a *Custom Drop*, partial moves are strictly forbidden. The compiler relies on the wholeness of the object to guarantee custom invariants inside the destructor. (Compiler-derived drops allow partial moves).

### AXS-OWN-006: Reinitialization
A `MOVED` or `UNINIT` place can be assigned to again. Reinitialization restores the state to `OWNED`.
Reinitialization restores ownership only for the assigned path, never for a wider place
[0540 §130 AOWNENG-30 (REQ-OWN-267); 0124 §15 AOWN-37 (REQ-OWN-048)]:
- Assigning a field `s.f = v` of a `MOVED`/`PARTIAL` struct reinitializes `s.f` only; `s` becomes
  `OWNED` again once every moved field has been reinitialized (AOWN-37). Reading another still-moved
  field stays `AX_MOVE_USE_AFTER_MOVE`.
- Array elements are not tracked individually (element-level tracking is post-v1, REQ-OWN-049) and
  an index is dynamic, so a write through an index — `a[i] = v`, `a[i].f = v`, `a[i][j] = v`,
  compound `a[i] op= v` — never reinitializes anything: it requires the array place `a` to be
  definitely `OWNED` at that point. If `a` is (maybe-)`MOVED` or `PARTIAL` the write is rejected with
  `AX_MOVE_USE_AFTER_MOVE` (span: the indexed place; note: where `a` was moved); if `a` is (maybe-)
  `UNINIT` it is `AX_INIT_USE_UNINIT`. Only a whole assignment `a = [...]` reinitializes the array.
  (Clarification from triage-1122; implemented by T498e.)

### AXS-OWN-007: Path Sensitivity at Control-Flow Joins
Ownership analysis must track state across branches. If a place is `OWNED` on one branch and `MOVED` on another, its state at the join point is conditionally moved, and any subsequent unconditional read is invalid without reinitialization.

## 2. Requirements for MIR

The MIR (Mid-level IR) must carry enough structural information to enact these rules:
- **Place Projections**: MIR must express place trees (e.g., `Local(x) -> Field(y)`) to track partial moves.
- **Move/Copy Distinctions**: MIR must clearly annotate `MOVE(place)` vs `COPY(place)`.

## 3. Test Matrix (Ownership)

| Rule | Program Pattern | Valid? | Task |
| --- | --- | --- | --- |
| AXS-OWN-002 | `let a = NonCopy(); let b = a; let c = a;` | No (Use of moved value) | T046 |
| AXS-OWN-003 | `let a = 1; let b = a; let c = a;` | Yes | T046 |
| AXS-OWN-004 | `let u = User(); let n = u.name; let a = u.age;` | Yes | T046 |
| AXS-OWN-005 | `let f = CustomDrop(); let h = f.handle;` | No | T046 |
| AXS-OWN-001 | `let a: i32; print(a);` | No (Uninitialized) | T047 |
| AXS-OWN-006 | `let a = NonCopy(); let b = a; a = NonCopy(); let c = a;` | Yes | T047 |
| AXS-OWN-006 | `let mut hs: [2]H = [mk(), mk()]; let t = hs; hs[0] = mk(); let u = hs[1].n;` | No (`AX_MOVE_USE_AFTER_MOVE` at `hs[0]`) | T498e |
| AXS-OWN-006 | `let mut hs: [2]H = [mk(), mk()]; let t = hs; hs = [mk(), mk()]; let u = hs[1].n;` | Yes | T498e |
| AXS-OWN-007 | `let a = NonCopy(); if c { let b = a; } let d = a;` | No (Maybe moved) | T046 |

## References
- `docs/base/specs/0176`, `docs/base/specs/0005`, `docs/base/specs/0160`
- [ADR-0014](../decisions/ADR-0014-ownership-capabilities-drop-semantics.md)
