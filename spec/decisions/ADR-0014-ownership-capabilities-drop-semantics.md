---
slug: ownership-capabilities-drop-semantics
date: 2026-10-05
status: accepted
---
# ADR-0014: Ownership, Capabilities, and Drop Semantics Consolidation

## Tóm tắt
Quyết định hợp nhất các quy tắc về Ownership, Capability (view) và Drop từ các tài liệu cơ sở (0176, 0177, 0178, 0004, 0005, 0160) thành các đặc tả chuẩn mực (SPEC-10, SPEC-11, SPEC-12). Các quyết định chính: (1) Cho phép implicit temporary views đối với method receiver để tránh nhiễu cú pháp, nhưng chúng chỉ là ephemeral (chết ở cuối statement); (2) Các view được lưu trong struct (stored views) hợp lệ với điều kiện owner outlives và không có self-reference; (3) Partial move bị cấm đối với kiểu dữ liệu có Custom Drop, nhưng được phép đối với Compiler-derived Drop; (4) Move không bắt buộc là memory copy (phụ thuộc MIR/Backend).

## Context
Task T045 requires consolidating the Axiom memory model (ownership ≠ borrow checker, capabilities as `view`/`mut_view`, deterministic drop, no GC) into testable canonical specs. There were open questions in the base docs (e.g., docs/base/specs/0005 §31 regarding implicit temporary views) and contradictions around partial moves under destruction.

## Options Considered

### Implicit Temporary Views
* **Option A**: Disallow completely. Requires creating a local variable for every intermediate result before taking a view. (Safe but noisy).
* **Option B**: Allow implicit temporary views for expressions and method receivers. They live until the end of the statement. (Aligns with pragmatic UX without compromising memory safety).

### Partial Moves with Drop
* **Option A**: Prohibit all partial moves if a destructor is present anywhere in the hierarchy.
* **Option B**: Prohibit partial moves on types with *Custom Drop* (because invariants of the whole object might be violated), but allow partial moves on types with *Compiler-derived Drop* where the compiler knows exactly which fields are still owned.

### Stored Views
* **Option A**: Views can only be ephemeral parameters.
* **Option B**: Views can be stored in structs (`stored views`). Requires static owner-outlives checking at instantiation and forbids self-referential structs.

## Decision
1. **Implicit Temporary Views**: Adopt Option B. Temporary views are allowed and destroyed at the statement boundary.
2. **Partial Moves**: Adopt Option B. Custom `Drop` blocks partial moves. Compiler-derived drop allows it.
3. **Stored Views**: Adopt Option B. Structs can hold views. The compiler will check that the referred owner strictly outlives the struct holding the view. Self-references are prohibited.

## Consequences
* Simplifies method calls and field access.
* Clarifies the boundary for the capability analyzer.
* `SPEC-10`, `SPEC-11`, and `SPEC-12` will use these semantics to define canonical rules `AXS-OWN-NNN`, `AXS-CAP-NNN`, and `AXS-DROP-NNN`.

## Sources
* `docs/base/specs/0004`
* `docs/base/specs/0005`
* `docs/base/specs/0160`
* `docs/base/specs/0176`
* `docs/base/specs/0177`
* `docs/base/specs/0178`
* ADR-0004 §3
* ADR-0006 §1
* `docs/base/tasks/0541` §96
