# T218 Report — Plan phase P18: Compiler architecture 2.0

## Tóm tắt
Đã mở rộng toàn bộ giai đoạn P18 (`P18-compiler-architecture-2-0`) từ 7 epic (`E18.1`–`E18.7`) trong `spec/ROADMAP.md` thành 28 task cụ thể (`T067`, `T750`, `T751` được tinh chỉnh tại chỗ và 25 task mới `T752`–`T776` trong dải `T750`–`T799` của P18, 4 task mỗi epic), bao gồm sắp lịch `E18.7` (`T772`, `T750`, `T751`, `T773`) chạy đầu tiên trong P18 cho yêu cầu `REQ-OWNER-006` (`.lib`, `.dll` + import `.lib` trên Windows x64 và oracle liên kết chéo GNU `ld` theo `ADR-0034` §4 OI-07b), chuyển toàn bộ 5.523 dòng `EPIC(E18.*)` trong `spec/requirements/CATALOG.md` sang ID task cụ thể (`T067`, `T750`–`T776`), cập nhật `T318` phụ thuộc vào tất cả task P18, và ghi nhận vào `spec/ROADMAP.md`.

## Summary
Expanded Phase P18 (`P18-compiler-architecture-2-0`) across all seven roadmap epics (`E18.1`–`E18.7`) into 28 concrete, single-sitting tasks (25 new tasks `T752`–`T776` in the `T750`–`T799` P18 block plus refined existing tasks `T067`, `T750`, and `T751`), converted all 5,523 `EPIC(E18.*)` rows in `spec/requirements/CATALOG.md` to concrete `T067` and `T750`–`T776` task IDs with matching `covers:` lists, wired `T318` (`depends: [T218, T067, T750..T776]`), and updated `spec/ROADMAP.md`.

### Epic breakdown
1. **E18.1 Query engine / semantic database** (4 tasks: `T752`–`T755`):
   - `T752` (`axiom-architect`): Canonical `spec/SPEC-21-query-engine-semantic-db.md` (`CompilerDB` semantic database, demand-driven queries, cycle handling, snapshot-bound diagnostics, and invalidation rules; 1,039 reqs).
   - `T753` (`axiom-frontend`): `CompilerDB` tables, demand-driven query execution, memoization, and `--emit=query-graph` (137 reqs).
   - `T754` (`axiom-semantics`): Deterministic query cycle detection, recovery, snapshot-bound diagnostics, and dependency invalidation (182 reqs).
   - `T755` (`axiom-qa`): Query engine, cycle recovery & semantic database conformance suite (50 reqs).
2. **E18.2 Incremental compilation** (4 tasks: `T756`–`T759`):
   - `T756` (`axiom-architect`): Canonical `spec/SPEC-22-incremental-compilation.md` (AST/API/body/codegen fingerprints `0152 §78`, red-green propagation, and persistent cache invariants; 162 reqs).
   - `T757` (`axiom-semantics`): Fine-grained AST/API/body/codegen fingerprints & red-green `try_mark_green` change propagation (90 reqs).
   - `T758` (`axiom-backend`): Persistent on-disk query/codegen cache, hermetic action digest validation & `< 100 ms` no-op rebuild fast path (190 reqs).
   - `T759` (`axiom-qa`): Incremental compilation, edit-one-private-fn & `< 100 ms` no-op rebuild conformance suite (60 reqs).
3. **E18.3 Parallel compilation** (4 tasks: `T760`–`T763`):
   - `T760` (`axiom-architect`): Canonical `spec/SPEC-23-parallel-compilation.md` (parallel DAG scheduling, thread-count-independent IDs, and deterministic merging; 46 reqs).
   - `T761` (`axiom-frontend`): Thread-safe immutable compiler snapshots, sharded interner & work-stealing query scheduler (131 reqs).
   - `T762` (`axiom-backend`): Parallel per-module/per-CGU codegen & deterministic diagnostic/artifact merging (140 reqs).
   - `T763` (`axiom-qa`): Parallel compilation thread-count invariance & byte-identical determinism conformance suite (60 reqs).
4. **E18.4 Artifact format & module interface files** (4 tasks: `T764`–`T767`):
   - `T764` (`axiom-architect`): Canonical `spec/SPEC-24-artifact-format-module-interfaces.md` (`.axmi` module interfaces and `.axmeta`/`.axlto` container sections; 74 reqs).
   - `T765` (`axiom-semantics`): Module interface metadata (`.axmi`) serializer, loader & exported symbol/generic summaries (70 reqs).
   - `T766` (`axiom-backend`): Axiom object/LTO/semantic package container sections & schema-versioned reader/writer (150 reqs).
   - `T767` (`axiom-qa`): Artifact format, module interface (`.axmi`) & LTO section round-trip conformance suite (61 reqs).
5. **E18.5 Pass contracts & proof-carrying transformations** (4 tasks: `T768`–`T771`):
   - `T768` (`axiom-architect`): Canonical `spec/SPEC-25-pass-contracts-proof-carrying-ir.md` (pass pre/postcondition contracts, proof-carrying certificates, and translation validation; 498 reqs).
   - `T769` (`axiom-semantics`): IR pass pre/postcondition declarations, effect/dataflow proof certificates & fail-closed gate (600 reqs).
   - `T770` (`axiom-backend`): Translation validation witness checker across MIR/`OptIR`/LIR/machine passes (750 reqs).
   - `T771` (`axiom-qa`): Pass contracts, proof-carrying transformations & fail-closed verifier conformance suite (50 reqs).
6. **E18.7 Windows x64 artifact kinds: static `.lib`, `.dll` + import `.lib`** (4 tasks: `T772`, `T750`, `T751`, `T773`, scheduled first in P18 at `priority: 699`–`702`):
   - `T772` (`axiom-architect`): Canonical `spec/SPEC-26-windows-artifact-kinds.md` (`--kind exe|obj|lib|dll`, COFF `.lib`, PE32+ `.dll`, and short-import `.lib`; 23 reqs).
   - `T750` (`axiom-backend`): Static libraries: COFF archive (`.lib`) writer and reader, `--kind` (33 reqs including `REQ-OWNER-006`).
   - `T751` (`axiom-backend`): PE DLL output: exports, `DllMain` initialiser, base relocations, import library & `ADR-0034` §4 OI-07b GNU `ld` cross-link support (41 reqs including `REQ-OWNER-006`).
   - `T773` (`axiom-qa`): Windows x64 static `.lib`, PE DLL, import library & GNU `ld` cross-link conformance suite (9 reqs).
7. **E18.6 Separate compilation, multiple objects, archives, section GC** (4 tasks: `T774`, `T067`, `T775`, `T776`):
   - `T774` (`axiom-architect`): Canonical `spec/SPEC-27-separate-compilation-linker-v2.md` (`LinkIR` separate compilation, multi-object/archive linking, `COMDAT`, and section GC; 295 reqs).
   - `T067` (`axiom-backend`): Linker v2: separate compilation, per-module objects & cross-object symbol resolution (314 reqs).
   - `T775` (`axiom-backend`): Linker v2 reachability graph, `COMDAT` deduplication & unreferenced section GC (231 reqs).
   - `T776` (`axiom-qa`): Separate compilation, multi-object archives, section GC & P18 exit conformance suite (39 reqs).

## Files changed
- ./_workspaces/tasks/todo/T067-linker-v2-separate-compilation-multiple-objects-ar.md
- ./_workspaces/tasks/todo/T218-plan-phase-p18-compiler-architecture-2-0.md
- ./_workspaces/tasks/todo/T318-phase-p18-gate-compiler-architecture-2-0.md
- ./_workspaces/tasks/todo/T750-e18-7-static-libraries-coff-archive.md
- ./_workspaces/tasks/todo/T751-e18-7-pe-dll-output-import-library.md
- ./_workspaces/tasks/todo/T752-e18-1-query-engine-semantic-db-spec.md
- ./_workspaces/tasks/todo/T753-e18-1-compilerdb-tables-demand-driven-queries.md
- ./_workspaces/tasks/todo/T754-e18-1-query-cycle-detection-diagnostics-invalidation.md
- ./_workspaces/tasks/todo/T755-e18-1-query-engine-semantic-db-conformance-suite.md
- ./_workspaces/tasks/todo/T756-e18-2-incremental-compilation-fingerprinting-spec.md
- ./_workspaces/tasks/todo/T757-e18-2-api-body-codegen-fingerprints-red-green.md
- ./_workspaces/tasks/todo/T758-e18-2-persistent-incremental-cache-noop-fastpath.md
- ./_workspaces/tasks/todo/T759-e18-2-incremental-compilation-conformance-suite.md
- ./_workspaces/tasks/todo/T760-e18-3-parallel-compilation-dag-scheduling-spec.md
- ./_workspaces/tasks/todo/T761-e18-3-immutable-snapshots-sharded-interner-scheduler.md
- ./_workspaces/tasks/todo/T762-e18-3-parallel-cgu-codegen-deterministic-merge.md
- ./_workspaces/tasks/todo/T763-e18-3-parallel-compilation-determinism-conformance-suite.md
- ./_workspaces/tasks/todo/T764-e18-4-artifact-format-module-interface-spec.md
- ./_workspaces/tasks/todo/T765-e18-4-axmi-module-interface-serializer-loader.md
- ./_workspaces/tasks/todo/T766-e18-4-object-lto-semantic-container-sections.md
- ./_workspaces/tasks/todo/T767-e18-4-artifact-format-axmi-conformance-suite.md
- ./_workspaces/tasks/todo/T768-e18-5-pass-contracts-proof-carrying-ir-spec.md
- ./_workspaces/tasks/todo/T769-e18-5-pass-contracts-proof-certificates-fail-closed.md
- ./_workspaces/tasks/todo/T770-e18-5-translation-validation-witness-checker.md
- ./_workspaces/tasks/todo/T771-e18-5-pass-contracts-translation-val-conformance-suite.md
- ./_workspaces/tasks/todo/T772-e18-7-windows-artifact-kinds-lib-dll-spec.md
- ./_workspaces/tasks/todo/T773-e18-7-windows-lib-dll-import-conformance-suite.md
- ./_workspaces/tasks/todo/T774-e18-6-separate-compilation-linker-v2-spec.md
- ./_workspaces/tasks/todo/T775-e18-6-linker-reachability-comdat-section-gc.md
- ./_workspaces/tasks/todo/T776-e18-6-separate-compilation-section-gc-conformance-suite.md
- ./spec/ROADMAP.md
- ./spec/requirements/CATALOG.md

## Tests
- `python .claude/skills/axiom-tasks/scripts/taskctl.py lint` on `T067`, `T318`, and `T750`–`T776`: `OK` (29 files).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py validate`: `OK (413 tasks)`.
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `gaps: 0`, `COVERAGE OK` (all 5,523 `EPIC(E18.*)` rows converted to concrete `T067` and `T750`–`T776` tasks; `v1-full planned=7667`).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T218`: `0 REFUSED`.

## Spec deviations
none

## Follow-ups
none

STATUS: COMPLETE round=1
STATUS: COMPLETE
