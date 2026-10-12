# ADR 0008: Method Resolution Task Sequencing

## Tóm tắt
T053 đã bị block do yêu cầu implement trait và extension method resolution trong khi hệ thống trait solver (T055) chưa được thực hiện. Quyết định: tách method resolution thành hai giai đoạn. T053 chỉ xử lý inherent methods. Việc xử lý trait và extension methods được dời sang T055.

## Context
Task T053 (Methods, impl blocks, member-call resolution) included the full member call resolution order (`inherent → trait → imported extension → generic extension`). However, T053 depends only on T052 and runs before T055 (Trait solver). The implementation agent correctly identified that the trait solver foundation was missing in `bootstrap/axiom0/src/traits`, blocking the task.

## Decision
Method call resolution will be implemented in two phases to match the task dependency graph:
1. **T053 (Methods)**: Implements method call syntax, receivers, and **inherent method resolution** only.
2. **T055 (Traits & Solver)**: Implements the trait solver and extends method resolution to support **trait methods and extension methods**, completing the full resolution order.

The scope of T053 has been narrowed accordingly to prevent this architectural confusion.

## Consequences
- Unblocks T053 by removing the dependency on the trait solver.
- T055 will need to augment the method resolution logic introduced in T053 to handle traits.
- Tests in T053 will only cover inherent methods; trait method tests are deferred to T055.

## Sources
- Tasks: T053, T055
