# Unblock T009

## Tóm tắt
Tạo một task mới (T112) thuộc quyền sở hữu của `axiom-kernel` để thêm các pragma `archcheck:allow` vào `bootstrap/axiom0/src/kernel/base.c` vì các hàm ICE thực sự cần in ra stderr và gọi `abort()`. T009 hiện đã phụ thuộc vào T112 và được đánh dấu là unblocked (todo).

## Options and Rationale
The blocked task T009 failed QA's archcheck due to `bootstrap/axiom0/src/kernel/base.c` calling I/O and process termination functions (violating INV-LAYER-006). Since `base.c` is outside T009's `paths:` scope, T009 cannot resolve it directly.

**Option 1: Add a missing prerequisite task (Selected)**
Create `T112` to explicitly add `archcheck:allow` pragmas to `kernel/base.c` where the ICE failure functions are implemented. Make T009 depend on T112. This correctly delegates the kernel file changes to the `axiom-kernel` domain while preserving the archcheck intent.

**Option 2: Update `archcheck_rules.txt`**
Modify the rules to blanket exclude `kernel/base.c`. This would weaken the architecture invariants since only the `ax_ice_failv` function is meant to do I/O, not the entire file.

**Option 3: Modify T009's scope**
Add `base.c` to T009's `paths:`. This is rejected because it mixes frontend diagnostics implementation with kernel foundation code ownership.

**Decision:** Applied Option 1. T112 was created, T009 depends on it, and T009 was successfully unblocked.

## Files changed
- _workspaces/tasks/todo/T009-diagnostics-engine-model-code-registry-human-json.md
- _workspaces/tasks/todo/T112-kernel-base-archcheck-allow.md
