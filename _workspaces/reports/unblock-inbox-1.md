# unblock-inbox-1 — Architect inbox of the T421/T422/T430/T437a/T452 gates

## Tóm tắt
- Đã xử lý toàn bộ `_workspaces/architect-inbox.txt` (7 mục) và `_workspaces/baseline-candidates.txt` (16 id); quyết định
  ghi ở ADR-0042, nhật ký ROADMAP đã cập nhật. Hai file đầu vào được làm rỗng, giữ một dòng tiêu đề "processed on 2026-11-13".
- Baseline: thêm 18 id (16 ứng viên + `encode/encode.test`, `link/link.test` lỗi trong mọi snapshot vì test C bị clang
  `-Werror`), từ 72 lên 90 id, mỗi id có task sửa: T435 (d10–d12), T441, T442, T440 (`undiagnosed:maybe-timeout`, có chính
  sách timeout khi máy tải nặng), T438, T439.
- Task mới P11: T438–T443 (baseline/hạ tầng test, priority 18–20), T444–T449, T422a, T422b (lỗi compiler FU-1..6 của T421
  và FU-A..K của T422, gom theo nguyên nhân gốc, 21–24), T421a (std/async: race join-waker, livelock, vtable Waker, output
  task detached), T422c (API đúng SPEC-34 sau khi sửa lỗi generic). T311 phụ thuộc tất cả.
- P12: T481 sửa `saturating_*` native u8..i64 **trước** T453 (T453 giờ phụ thuộc T452 + T481, phải bỏ `native-after: T453`);
  T482 điều tra miscompile `neg_carry` ở O1; T483 đăng ký `AX_CONST_SHIFT_RANGE` (sửa SPEC-03 cho khớp SPEC-40/42) và
  literal MIN; T484 gấp hằng bit intrinsic ở -O1. P13: T536 bắt panic của task bằng `catch_unwind` sau T523.
- Harness: chép đoạn "Harness follow-up" của T437a vào `axiom-qa.md` và `axiom-testing/SKILL.md`; thêm quy tắc G1
  (`nocache:`/`cache-inputs:`), chạy đủ định kỳ với `--no-cache`, quy tắc timeout khi máy tải; G2 đưa vào phạm vi T437b.
- Thứ tự `taskctl next`: T437b (11), T438 (18), T421a (25) — task sửa đứng trước task tính năng; không có task mới < 10.
- Rủi ro: lần `accept` của T452 (commit e0637c50) đã gom luôn các file task mới/đã sửa của lượt này vào commit T452.

## Inputs read
`_workspaces/architect-inbox.txt`, `_workspaces/baseline-candidates.txt`, `_workspaces/baseline-failures.txt`, ADR-0041,
`_workspaces/reports/T421-report.md`, `T421-qa.md`, `T422-report.md`, `T422-qa.md`, `T430-report.md`, `T430-qa.md`,
`T437a-report.md`, `T437a-qa.md`, `T452-report.md`, `T452-qa.md`.

## Decisions (details and options: `spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md`)

### 1. Baseline admissions (ADR-0042 §1)
| candidate id(s) | class:tag | fix task |
|---|---|---|
| `selfhost/drop/qa_drop_d10/d11/d12.ax` | fixture-regen:drop-fixtures | T435 (existing; acceptance extended) |
| `selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax`, `selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax` | undiagnosed:mir-fixture | T441 (new, after T435) |
| `selfhost/obj_link_driver/qa_obj_link_driver_diff.ax`, `..._smoke.ax` | undiagnosed:obj-link-driver | T442 (new) |
| 7 `conformance/p18,p19,p20/*_oracle.test` + `run/lsp_vfs/lsp_vfs_engine.test` | undiagnosed:maybe-timeout | T440 (new; idle / `--timeout-scale 6` / loaded runs per id) |
| `tools/tests/gatecheck::test_gatecheck.GatecheckTest.test_check_without_command_blocks` | undiagnosed:gatecheck-selftest | T439 (new) |
| `encode/encode.test`, `link/link.test` (not on the candidate list; T430-qa shows they fail in every fresh snapshot) | environment:snapshot-cbuild | T438 (new) |
No candidate mapped to T431–T434/T436: none shares their root cause (`selfhost/driver` *_b are already T436's).

### 2. Inbox items -> tasks
| inbox item | task(s) |
|---|---|
| FINDING-3 native saturating u8..i64 | T481 (P12, priority 20); T453 depends on T452 + T481, scope reduced to 128-bit saturation, must remove `native-after: T453` (locks `tests/run/int128_interp`, `tests/opt/int128`), acceptance adds native legs of T452's tests and keeps `tests/run/saturating_native` green |
| Spec gap `AX_CONST_SHIFT_RANGE` | decided (register the code; SPEC-03 AXS-SEM-037 amended to agree with SPEC-40/42); implementation T483, also covers the `-9223372036854775808i64` panic seen by T452-qa |
| T437a G1/G2/G3, R1, R2, harness follow-up | axiom-qa.md + axiom-testing SKILL edits; G2 in T437b scope/acceptance; G3 addendum in ADR-0041 §4 S4; R2 -> T439 |
| ct_* C tests (`cdriver_abi_qa2.c` -Werror) | T438 (axiom-backend, C test only) |
| `bundle_common.py` duplicate modules | T443 (axiom-qa, depends T452) |
| neg_carry O1 miscompile | T482 (axiom-semantics, opus, recipe from T452-qa/report) |
| generator headers lack `// stdout:` | in T442 (generators of driver and obj_link_driver; depends T452 + T436) |
| T421 FU-1, FU-3 | T444 |
| T421 FU-4, FU-6 | T445 |
| T422 FU-F, FU-G | T446 |
| T422 FU-B, FU-C | T447 |
| T422 FU-D, FU-H + T421 FU-5 | T448 (after T446) |
| T422 FU-E | T449 |
| T422 FU-A, FU-J (parser) | T422a (axiom-frontend, after T434) |
| T421 FU-2, T422 FU-K | T422b |
| join-waker race, task_wake livelock, poll flag clobber, Waker vtable ignored, detached outputs not dropped | T421a (axiom-stdlib, no dependency: `std/async` is free) |
| SPEC-34 API deviations (TaskGroup<T>, Timeout<F>, spawn(fut)) | T422c (after T421a, T444–T449, T422a, T422b) |
| panic containment needs unwinding | T536 (P13, after T523 and T422c) |
| T452 FINDING-2 bit intrinsics not folded at -O1 | T484 (P12, feature priority 145) |
Gates: T311 depends on T438–T449, T421a, T422a–c; T312 on T481–T484; T313 on T536.

### 3. Ordering check (`taskctl.py next --max 10` after the changes, T452 now done)
`T437b` (11), `T438` (18), `T421a` (25). Todo priorities below 100: T437b 11, T434 12, T432 13, T435 14, T436 15, T431 16,
T433 17, T438/T439/T441/T442 18, T440 19, T443/T481 20, T444/T446 21, T445 22, T447/T448 23, T422a/T422b/T449 24, T421a 25,
T482 26, T483 27, T422c 30; every feature task is >= 93. No new task < 10 (T224 6 is the pre-existing deferred task).

### 4. Checks
`taskctl.py lint` OK for all 21 new and 3 edited task files; `taskctl.py validate` OK (694 tasks); `harness_check.py`
HARNESS OK (only the known optional guard-hook WARN); `reqcov.py --strict` gaps 0, COVERAGE OK. No test suite was run.

## Risks / notes for the orchestrator
- The T452 `accept` commit `e0637c50` already contains the new task files and the edits to T311/T312/T313/T435/T437b/T453
  made in this session (accept appears to stage the whole board directory). Content is final; `commit-report` will only
  add the remaining files below. Consider restricting `accept` to the task's own board file.
- `_workspaces/architect-inbox.txt` was untracked; it is listed below so it becomes tracked with its "processed" header.
- `maybe-timeout` (ADR-0042 Revisit): T440 may reclassify ids as `environment` or remove them.

## Files changed
- _workspaces/baseline-failures.txt
- _workspaces/baseline-candidates.txt
- _workspaces/architect-inbox.txt
- _workspaces/reports/unblock-inbox-1.md
- spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md
- spec/decisions/ADR-0041-complete-suite-baseline-and-test-cache.md
- spec/SPEC-03-core-semantics.md
- spec/ROADMAP.md
- .claude/agents/axiom-qa.md
- .claude/skills/axiom-testing/SKILL.md
- _workspaces/tasks/todo/T438-baseline-snapshot-c-test-build-werror.md
- _workspaces/tasks/todo/T439-baseline-gatecheck-selftest.md
- _workspaces/tasks/todo/T440-baseline-oracle-probes-maybe-timeout.md
- _workspaces/tasks/todo/T441-baseline-selfhost-mir-fixture-diffs-outside-drop.md
- _workspaces/tasks/todo/T442-baseline-obj-link-driver-panic-and-selfhost-stdout-evidence.md
- _workspaces/tasks/todo/T443-selfhost-bundle-common-reject-duplicate-modules.md
- _workspaces/tasks/todo/T444-fix-layout-forward-pointee-and-std-lang-item-fields.md
- _workspaces/tasks/todo/T445-fix-moves-through-mut-view-fields-and-receivers.md
- _workspaces/tasks/todo/T446-fix-impl-level-generics-monomorphisation.md
- _workspaces/tasks/todo/T447-fix-impl-generics-assoc-types-and-overlap-check.md
- _workspaces/tasks/todo/T448-fix-explicit-type-args-and-bound-inference.md
- _workspaces/tasks/todo/T449-fix-concurrency-checker-keyed-on-spawn-name.md
- _workspaces/tasks/todo/T421a-std-async-waker-races-vtable-detached-outputs.md
- _workspaces/tasks/todo/T422a-fix-parser-generic-args-ambiguity-and-generic-fn-values.md
- _workspaces/tasks/todo/T422b-fix-native-fn-pointer-field-call-and-oracle-stdout-flush.md
- _workspaces/tasks/todo/T422c-std-async-converge-api-on-spec-34-shape.md
- _workspaces/tasks/todo/T481-fix-native-saturating-arith-narrow-widths.md
- _workspaces/tasks/todo/T482-investigate-o1-neg-carry-miscompile-stage2.md
- _workspaces/tasks/todo/T483-const-shift-range-diag-and-min-literal-folding.md
- _workspaces/tasks/todo/T484-o1-const-folding-of-bit-intrinsics.md
- _workspaces/tasks/todo/T536-e13-5-async-task-panic-capture-via-catch-unwind.md
- _workspaces/tasks/todo/T453-e12-1-lir-i128-pair-lowering-x64-codegen.md
- _workspaces/tasks/todo/T435-baseline-selfhost-drop-bundles-hermetic-vs-prelude.md
- _workspaces/tasks/todo/T437b-compiler-dep-file-exact-test-deps.md
- _workspaces/tasks/todo/T311-phase-p11-gate-concurrency-async.md
- _workspaces/tasks/todo/T312-phase-p12-gate-numeric-floating-point-simd.md
- _workspaces/tasks/todo/T313-phase-p13-gate-low-level-systems-unsafe-freestanding-securit.md
