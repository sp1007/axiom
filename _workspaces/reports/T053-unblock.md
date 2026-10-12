## Tóm tắt
T053 đã bị block do yêu cầu implement trait và extension method resolution, nhưng hệ thống trait solver (T055) chưa được thực hiện vì T053 chạy trước T055 theo dependency graph. Quyết định: giới hạn scope của T053 chỉ xử lý inherent methods. Phần trait và extension methods được dời sang T055. Đã viết ADR và cập nhật file task T053.

## Decision
The implementation agent was correctly blocked because T053 was instructed to handle the full member call resolution order (`inherent → trait → imported extension → generic extension`), but the trait solver doesn't exist yet. According to the board, the trait solver is implemented in T055, which runs *after* T053 (via T054).

Options considered:
1. Make T053 implement the trait solver. (Rejected: Scope too large, duplicates T055).
2. Defer T053 to run after T055. (Rejected: Generics T054 depends on T053).
3. Narrow T053's scope to only handle inherent methods, and defer trait/extension methods to T055. (Accepted: Matches the natural evolution of the compiler).

I have modified the Scope of T053 to remove trait and extension method resolution, explicitly deferring them to T055. I have also codified this sequencing decision in `docs/adr/ADR-0008-method-resolution-sequencing.md` to prevent future confusion.

## Files changed
- _workspaces/tasks/doing/T053-methods-impl-blocks-member-call-resolution.md
- docs/adr/ADR-0008-method-resolution-sequencing.md
- _workspaces/reports/T053-unblock.md

STATUS: UNBLOCKED
