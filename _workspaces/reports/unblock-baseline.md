# Unblock — complete-suite baseline (owner decision 2026-11-13)

## Tóm tắt
- Chủ dự án quyết định mọi QA gate chạy **toàn bộ** bộ test. Đã lập `_workspaces/baseline-failures.txt` gồm **87 id**
  lỗi có sẵn: 78 id từ `T421-qa.md` (§4, §B, §C) + 9 id do tác tử T452 báo (`selfhost/drop` d02..d07, d09;
  `selfhost/driver` commands_b, inspect_diff_b). Mỗi dòng: id, lớp:nhãn, task sửa. Gate chỉ PASS khi tập id lỗi là tập
  con của baseline; id lỗi có sẵn phát hiện sau (155 id `tests/selfhost` T421 chưa chạy) → gate BLOCKED, architect thêm.
- 7 task sửa theo nguyên nhân gốc (ADR-0041): T434 dump AST/resolve/HIR lẫn impl `@derive(Copy)` của prelude (41 id;
  golden đúng, sửa compiler), T435 fixture `selfhost/drop` lệch type id do prelude lớn lên (8), T436 `selfhost/driver`
  *_b + `stage1_bootstrap` (3), T430 probe build của engine/oracle tối ưu (15), T431 artifact/link/encode (8), T432
  prelude/std sau T406/T416, gồm trùng tên `Ordering` (5), T433 thiếu chẩn đoán + int128 (7). Ưu tiên 12–17, chạy trước
  tính năng mới. Chỉ T430 (chỉ sửa test) chạy được ngay; các task khác phụ thuộc T452 và khoá `tests/selfhost`; không
  task nào đụng `std/async` của T422.
- T437 (ưu tiên 11): bộ nhớ đệm kết quả từng test trong `tools/axtest.py`, khoá theo hash compiler + mọi file compiler
  thực sự nạp (cờ mới `--dep-file`) + dòng lệnh/mode/runner; 8 điều kiện đúng đắn S1–S8 trong ADR-0041 §4 (chỉ lưu PASS,
  không cache test đa luồng/thời gian/`cmd:`, gate chỉ dùng entry từ snapshot có commit gốc là tổ tiên HEAD, luôn chạy
  lại mẫu kiểm chứng, gate phase chạy `--no-cache`); kèm `--baseline`, đo `--time-passes` một bundle 30k dòng, xếp lịch
  dài nhất trước.
- Thêm một quy tắc vào `axiom-tasks` SKILL.md; T311 (gate P11) phụ thuộc 7 task sửa. Chưa có `bundles.log`/báo cáo
  T452 (đã kiểm `_workspaces/reports/`, `build-snap-T452/`); id mới từ đó sẽ được nhận theo ADR-0041 §3.

## Classification
TYPE B (architecture/process clarification of the owner decision) with board changes; no language semantics change.
The prelude naming rule in T432 (D4) is flagged "Revisit: yes" in ADR-0041.

## Decision, options and rationale
See `spec/decisions/ADR-0041-complete-suite-baseline-and-test-cache.md`:
- Baseline representation: a single named list + per-root-cause fix tasks (chosen) vs sampling (owner-rejected),
  in-place `xfail` (rejected: edits 87 tests, some in running tasks' paths, hides failures), one big fix task
  (rejected: four owners, too large).
- Root-cause grouping (architect reading of the evidence):
  - Dump goldens: the 209 extra bytes are the `@derive(Copy)` impls of `Ordering`/`CasResult` that T406 added to
    `std/core/prelude.ax`; derive bodies are re-parsed from generated text in `compiler/syntax/parse.ax` and attributed
    to the main file, so the `FileId` filter of the dumps lets them through. Regression, goldens stay authoritative.
  - Drop bundles: the +4 type-id shift matches the type items added to the implicitly loaded prelude; the test is made
    independent of std contents rather than re-blessed after every prelude change.
  - Probe builds, artifact/link, driver/stage1: undiagnosed; each task diagnoses with `-v` first, fixes in its own
    area, reports anything outside for a split.
- Cache: compiler-reported dependency list (sound and precise) vs whole-tree key (sound, no hits) vs `std/` superset
  (fallback only) vs Python `use` scanning (unsound, rejected).
- Sequencing: every fix that edits `compiler/` must regenerate the selfhost bundles embedding it, so those tasks
  depend on T452 and lock `tests/selfhost`; all fix tasks lock the baseline file (so `accept` never commits another
  task's edit of it). T432 after T434; T435 and T433 after T432. Ids come from the P11 block (`new-id --phase P11`):
  the first draft used P10 ids T164–T167, which `harness_check.py` rejected (a core task may not depend on the
  post-self-host T452), so they were renumbered T434–T437 before anything was committed.
- Process rule (item 4): needed, one line in `axiom-tasks` SKILL.md; `taskctl accept` already refuses a non-PASS
  verdict, so no script change.

## Checks
- `taskctl.py lint` OK for all 8 new task files; `taskctl.py validate`: `OK (671 tasks)`; `harness_check.py`:
  `HARNESS OK` (only the standing optional-hook warning); `reqcov.py --strict`: `gaps: 0`, `COVERAGE OK`.
- `taskctl.py next`: T430 is ready now; all others wait for T452 (and their chains).
- No test suite was run (shared machine; reading and board edits only).

## Notes for the orchestrator
- Gates of T452 and T422 should apply the subset check by hand against `_workspaces/baseline-failures.txt` until T437
  delivers `axtest.py --baseline`.
- After T437 is accepted, its report's "Harness follow-up" section lists the new axtest flags; the architect then
  updates `.claude/skills/axiom-testing/SKILL.md` and `.claude/agents/axiom-qa.md` (cache use in gates per ADR-0041 §4).

## Files changed
- _workspaces/baseline-failures.txt
- spec/decisions/ADR-0041-complete-suite-baseline-and-test-cache.md
- spec/ROADMAP.md
- .claude/skills/axiom-tasks/SKILL.md
- _workspaces/tasks/todo/T311-phase-p11-gate-concurrency-async.md
- _workspaces/tasks/todo/T430-baseline-optimizer-probe-bundle-builds.md
- _workspaces/tasks/todo/T431-baseline-artifact-link-encode-driver-failures.md
- _workspaces/tasks/todo/T432-baseline-prelude-std-regressions-after-p11.md
- _workspaces/tasks/todo/T433-baseline-missing-diagnostics-and-int128-typeck.md
- _workspaces/tasks/todo/T434-baseline-derive-items-leak-into-root-file-dumps.md
- _workspaces/tasks/todo/T435-baseline-selfhost-drop-bundles-hermetic-vs-prelude.md
- _workspaces/tasks/todo/T436-baseline-selfhost-driver-b-and-stage1-parity.md
- _workspaces/tasks/todo/T437-axtest-incremental-result-cache-dep-file.md
- _workspaces/reports/unblock-baseline.md
