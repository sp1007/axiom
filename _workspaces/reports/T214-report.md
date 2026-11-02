# T214 Report — Plan phase P14: Comptime 2.0, reflection, generators

## Tóm tắt
Đã mở rộng toàn bộ giai đoạn P14 (`P14-comptime-2-0-reflection-genera`) từ 5 epic (`E14.1`–`E14.5`) trong `spec/ROADMAP.md` thành 24 task cụ thể (`T058` được tinh chỉnh tại chỗ và 23 task mới `T550`–`T572` trong dải `T550`–`T599` của P14, từ 3 đến 6 task mỗi epic), bao gồm mở rộng đầy đủ **`E14.5` (`ADR-0036` §4 / `SPEC-03 AXS-SEM-047`)** cho tự động giải tham chiếu khi đánh chỉ mục `a[i]` qua `view<[N]T>` và `mut_view<[N]T>` trong `axiomc` (xóa ghi chú v0.1 trong `AXS-SEM-047`, cài đặt trong `typeck` + MIR builder, kiểm thử đọc/ghi/drop phần tử cũ qua `view`/`mut_view` và kiểm thử âm tính cho ghi qua `view` bất biến hoặc `p[i]` trên con trỏ thô); chuyển toàn bộ 512 dòng `EPIC(E14.*)` trong `spec/requirements/CATALOG.md` sang ID task cụ thể (`T058`, `T550`–`T572`), cập nhật `T314` phụ thuộc vào tất cả task P14, và ghi nhận vào `spec/ROADMAP.md`.

## Summary
Expanded Phase P14 (`P14-comptime-2-0-reflection-genera`) across all five roadmap epics (`E14.1`–`E14.5`) into 24 concrete, single-sitting tasks (23 new tasks `T550`–`T572` in the `T550`–`T599` P14 block plus refined existing task `T058`), converted all 512 `EPIC(E14.*)` rows in `spec/requirements/CATALOG.md` to concrete `T058` and `T550`–`T572` task IDs with matching `covers:` lists, wired `T314` (`depends: [T214, T058, T550..T572]`), and updated `spec/ROADMAP.md`.

### Epic breakdown
1. **E14.1 Comptime completion** (6 tasks: `T550`–`T555`):
   - `T550` (`axiom-architect`): Canonical `spec/SPEC-60-comptime-2-0.md` (Comptime 2.0 execution model, value lifting & no-escape barrier, partial evaluation, specialization, and `const` vs `static` vs TLS initialization semantics; 88 reqs).
   - `T551` (`axiom-frontend`): `comptime fn`, `comptime { ... }` blocks, `comptime` parameters, unified type/ownership/capability checking, and sandboxed compile-time authority (42 reqs).
   - `T552` (`axiom-semantics`): Comptime MIR evaluator, transient compiler-heap allocation + deterministic `Drop`, value lifting / `AX_CTM_RESOURCE_ESCAPE` barrier, and deterministic `const`/`static` initialization ordering (77 reqs).
   - `T553` (`axiom-semantics`): Partial evaluation, `comptime` argument & closure specialization, and dependency-tracked comptime caching (47 reqs).
   - `T554` (`axiom-backend`): Native materialization of lifted comptime aggregates, static lookup tables, and `.rdata`/`.data`/`.bss` emission without runtime comptime-VM overhead (42 reqs).
   - `T555` (`axiom-qa`): Comptime 2.0, partial evaluation & `const`/`static` initialization conformance suite (38 reqs).
2. **E14.2 Reflection & derive** (5 tasks: `T556`–`T560`):
   - `T556` (`axiom-architect`): Canonical `spec/SPEC-61-reflection-derive.md` (`TypeInfo` compile-time reflection API, visibility/layout rules, typed `@derive` framework, and code generation boundary without textual macros; 26 reqs).
   - `T557` (`axiom-semantics`): Compile-time `TypeInfo` reflection intrinsics (`type_info<T>()`, `fields_of<T>()`, `variants_of<T>()`, `attributes_of<T>()`, `offset_of<T, F>()`, `implements<T, Trait>()`), visibility enforcement, and layout queries (20 reqs).
   - `T558` (`axiom-semantics`): Typed `@derive` expansion engine, `GenProvenanceId` diagnostic provenance tracking, and full semantic/ownership/capability/MIR re-verification (37 reqs).
   - `T559` (`axiom-stdlib`): `std.reflect` API and reflection-driven `derive(Debug, Eq, Ord, Hash, Clone, Default, Serialize, Deserialize)` in `std/derive` (13 reqs).
   - `T560` (`axiom-qa`): Reflection, typed codegen boundary & `std` derive conformance suite (10 reqs).
3. **E14.3 Generators & `yield`** (5 tasks: `T561`–`T565`):
   - `T561` (`axiom-architect`): Canonical `spec/SPEC-62-generators.md` (`gen fn`, `yield`, zero-heap iterator state machines, live-across-`yield` ownership/capability rules, and per-state `Drop` cleanup; 10 reqs).
   - `T562` (`axiom-frontend`): Generator syntax (`gen fn`, `yield`), HIR lowering, and live-across-`yield` capability/ownership analysis (`AX_GEN_VIEW_ACROSS_YIELD`, `AX_GEN_SELF_BORROW_ACROSS_YIELD`; 9 reqs).
   - `T563` (`axiom-semantics`): Generator MIR state-machine lowering (`compiler/mir/gen_lower.ax`), per-state `Drop` cleanup, MIR verification, and oracle (`--interp`) execution (11 reqs).
   - `T564` (`axiom-stdlib`): Iterator state-machine integration, `for x in gen(...)` loops, and lazy `std.iter` combinators (7 reqs).
   - `T565` (`axiom-qa`): Generators, `yield` state machines & lazy control-flow conformance suite (5 reqs).
4. **E14.4 `dyn Trait` & vtables** (5 tasks: `T566`, `T058`, `T567`–`T569`):
   - `T566` (`axiom-architect`): Canonical `spec/SPEC-63-dyn-trait-vtables.md` (`dyn Trait` object-safety rules, 16-byte `(data_ptr, vtable_ptr)` fat-pointer coercion, and vtable layout/drop ABI; 5 reqs).
   - `T058` (`axiom-semantics`): `dyn Trait` object-safety checker (`AX_DYN_NOT_OBJECT_SAFE`), unsizing coercion (`view<T>` / `mut_view<T>` -> `view<dyn Trait>` / `mut_view<dyn Trait>`), and MIR/oracle dynamic dispatch (5 reqs).
   - `T567` (`axiom-backend`): Native vtable layout, read-only `.rdata` vtable symbol emission, Windows x64 fat-pointer ABI, and indirect call codegen (4 reqs).
   - `T568` (`axiom-stdlib`): Owned `Box<dyn Trait>`, `view<dyn Trait>`, `mut_view<dyn Trait>`, and vtable-driven `drop_in_place` + sized deallocation (4 reqs).
   - `T569` (`axiom-qa`): `dyn Trait` object safety, vtable layout & dynamic dispatch conformance suite (4 reqs).
5. **E14.5 Surface ergonomics deferred by R7** (3 tasks: `T570`–`T572`):
   - `T570` (`axiom-architect`): Finalize `spec/SPEC-03-core-semantics.md` `AXS-SEM-047` index auto-deref through `view<[N]T>` and `mut_view<[N]T>`, removing the temporary v0.1 deferral note and adding §10 test cases (3 reqs).
   - `T571` (`axiom-semantics`): Implement index auto-deref through `view<[N]T>` and `mut_view<[N]T>` in `axiomc` (`compiler/sema` `typeck` + `compiler/mir` MIR builder) with read/write/drop tests (`a[i]` read on `view`/`mut_view`, write on `mut_view`) and negative UI tests (write through `view`, `p[i]` on raw pointer; 3 reqs).
   - `T572` (`axiom-qa`): Index auto-deref through `view`/`mut_view` conformance suite (`AXS-SEM-047`; 2 reqs).

## Files changed
- ./_workspaces/tasks/todo/T058-dyn-trait-vtables-and-dynamic-dispatch.md
- ./_workspaces/tasks/todo/T214-plan-phase-p14-comptime-2-0-reflection-generators.md
- ./_workspaces/tasks/todo/T314-phase-p14-gate-comptime-2-0-reflection-generators.md
- ./_workspaces/tasks/todo/T550-e14-1-comptime-2-0-partial-eval-const-static-spec.md
- ./_workspaces/tasks/todo/T551-e14-1-comptime-fn-blocks-const-generics-sema.md
- ./_workspaces/tasks/todo/T552-e14-1-comptime-mir-eval-no-escape-const-static-init.md
- ./_workspaces/tasks/todo/T553-e14-1-partial-evaluation-specialization-caching.md
- ./_workspaces/tasks/todo/T554-e14-1-native-materialization-comptime-tables-sections.md
- ./_workspaces/tasks/todo/T555-e14-1-comptime-partial-eval-conformance-suite.md
- ./_workspaces/tasks/todo/T556-e14-2-reflection-derive-codegen-boundary-spec.md
- ./_workspaces/tasks/todo/T557-e14-2-compile-time-typeinfo-reflection-intrinsics.md
- ./_workspaces/tasks/todo/T558-e14-2-typed-derive-expansion-provenance-reverify.md
- ./_workspaces/tasks/todo/T559-e14-2-std-reflect-and-derive-debug-eq-hash-serialize.md
- ./_workspaces/tasks/todo/T560-e14-2-reflection-derive-conformance-suite.md
- ./_workspaces/tasks/todo/T561-e14-3-generators-yield-state-machines-spec.md
- ./_workspaces/tasks/todo/T562-e14-3-generator-syntax-hir-live-across-yield-own.md
- ./_workspaces/tasks/todo/T563-e14-3-generator-mir-state-machine-drop-oracle.md
- ./_workspaces/tasks/todo/T564-e14-3-iterator-integration-for-in-lazy-combinators.md
- ./_workspaces/tasks/todo/T565-e14-3-generators-yield-conformance-suite.md
- ./_workspaces/tasks/todo/T566-e14-4-dyn-trait-object-safety-vtable-abi-spec.md
- ./_workspaces/tasks/todo/T567-e14-4-native-vtable-layout-rdata-indirect-call-codegen.md
- ./_workspaces/tasks/todo/T568-e14-4-owned-box-dyn-trait-views-dynamic-drop.md
- ./_workspaces/tasks/todo/T569-e14-4-dyn-trait-vtable-dispatch-conformance-suite.md
- ./_workspaces/tasks/todo/T570-e14-5-spec-03-axs-sem-047-index-autoderef-view.md
- ./_workspaces/tasks/todo/T571-e14-5-typeck-mir-index-autoderef-view-mut-view.md
- ./_workspaces/tasks/todo/T572-e14-5-index-autoderef-view-conformance-suite.md
- ./spec/ROADMAP.md
- ./spec/requirements/CATALOG.md

## Tests
- `python .claude/skills/axiom-tasks/scripts/taskctl.py lint` on `T058`, `T314`, and `T550`–`T572`: `OK` (25 files).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py validate`: `OK (358 tasks)`.
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `gaps: 0`, `COVERAGE OK` (all 512 `EPIC(E14.*)` rows converted to concrete `T058` and `T550`–`T572` tasks; `v1-full planned=1739`).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T214`: `0 REFUSED`.

## Spec deviations
none

## Follow-ups
none

STATUS: COMPLETE
