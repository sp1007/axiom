# Unblock — split of T437 (gate tooling first, compiler --dep-file after T452)

## Tóm tắt
- Chủ dự án (2026-11-13) muốn gate theo task chỉ khoảng 60-90 phút và T437 chạy đầu tiên. T437 bị kẹt sau T452 chỉ
  vì phần cờ `--dep-file` trong compiler và việc sinh lại bundle `tests/selfhost` (T452 đang giữ khoá này).
- Quyết định: tách T437 theo quyền sở hữu file (ADR-0041 §6).
  - **T437a** (axiom-qa, opus, không phụ thuộc, ưu tiên 10, chỉ sửa `tools/` và `tests/smoke.list`): cache kết quả
    S1-S8 với danh sách phụ thuộc dự phòng; `axtest --affected` (dùng phụ thuộc chính xác khi có, không thì quy tắc
    grep + bảng `tools/affected_map.txt`, in cách suy ra); `--smoke` (danh sách `tests/smoke.list`, ~20 phút ở `-j 2`);
    chạy dài nhất trước + đo profile một bundle selfhost; `--baseline`; `tools/taskgate.py` chạy cả gate một lệnh, xuất
    tóm tắt Markdown/JSON cho file QA.
  - **T437b** (axiom-stdlib, opus, phụ thuộc T452 + T437a, ưu tiên 11): cờ `--dep-file` của compiler, sinh lại bundle,
    đo cache nóng/lạnh với phụ thuộc chính xác.
- T437 đóng dạng superseded; không task nào phụ thuộc T437. `taskctl next` hiện trả T437a trước T430.

## Decision
Classification: TYPE B (process/tooling architecture). Options considered:
1. Keep T437 whole and wait for T452 — rejected: delays the tool that shortens every later gate.
2. Start T437 now with `--force` — rejected: collides with T452's `tests/selfhost` lock and `compiler/driver/pipeline.ax`.
3. **Split by file ownership (chosen).** The runner/gate tooling needs no compiler change; the cache is built with the
   ADR-0041 §4 S2 superset fallback plus a stub-tested exact path, so T437b only adds the flag and regenerates bundles.

Details:
- T437a priority 10: lowest non-critical value (critical `< 10` would drain other slots and run alone). Verified:
  `taskctl.py next --max 5` returns `T437a` then `T430`; their paths are disjoint, so both can run in parallel.
- T437a does not touch T452 files (`compiler/*`, `tests/selfhost`, `std/core/prelude.ax`) nor T422 files (`std/async/*`).
  It reads one selfhost bundle for the `--time-passes` profile only, inside its snapshot.
- The per-task gate tool is `tools/taskgate.py` (not `gate.py`) to stay distinct from the phase-gate checker
  `tools/gatecheck.py` (T022).
- `--smoke` rotation vs checked-in list: `tests/smoke.list` holds per-group pools + `always:` cases; each run draws one
  per group with a printed seed (default = hash of the change set), meeting both "checked-in, validated" and "a
  different pick each time" from axiom-qa.md.
- T437's dependency on T452 moved to T437b; the superseded T437 file now has `depends: []` (validate rejects a done
  task with an unfinished dependency).
- `axiom-qa.md` "Per-task gate scope" now points to `tools/taskgate.py` once T437a is done (pointer sentence only).
- Checks: `taskctl.py lint` (both new files) OK; `taskctl.py validate` OK (673 tasks); `harness_check.py` HARNESS OK;
  `reqcov.py --strict` COVERAGE OK (gaps 0). No test suite was run.

## Files changed
- _workspaces/tasks/todo/T437a-axtest-gate-tooling-cache-affected-smoke-taskgate.md
- _workspaces/tasks/todo/T437b-compiler-dep-file-exact-test-deps.md
- _workspaces/tasks/done/T437-axtest-incremental-result-cache-dep-file.md
- _workspaces/tasks/todo/T437-axtest-incremental-result-cache-dep-file.md
- spec/decisions/ADR-0041-complete-suite-baseline-and-test-cache.md
- spec/ROADMAP.md
- .claude/agents/axiom-qa.md
- _workspaces/reports/unblock-split-t437.md
