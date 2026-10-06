# unblock-T022 — VS0 gate blocked by implementation bugs

## Tóm tắt
T022 (cổng VS0) bị chặn vì 68 test vs0 thất bại do lỗi cài đặt ở parser, typeck/driver, MIR builder
và interpreter, cộng một vi phạm quy tắc (d) trên bảng task. Đây là lỗi cài đặt chứ không phải lỗ hổng
đặc tả, nên không nới tiêu chí và không dùng xfail.
Quyết định (ADR-0016, phương án (c) — thêm task tiên quyết): tạo 4 task sửa lỗi theo chủ sở hữu module,
đường dẫn tách rời: T114 parser (frontend), T115 typeck/driver (frontend), T116 MIR builder (semantics),
T117 interpreter (semantics, sau T116). T114/T115/T116 sẵn sàng chạy song song ngay.
T022 phụ thuộc cả bốn task, giữ nguyên bộ test đã giao, và nhận thêm `tools/ci.ps1` để căn chỉnh với
`ci.sh`. T069 thêm phụ thuộc T061 để sửa quy tắc (d). Không yêu cầu OWNER.md nào bị bỏ; T224 vẫn deferred;
không đụng `docs/`.

## Decision
Options considered (details in `spec/decisions/ADR-0016-vs0-gate-fix-tasks.md`):
1. Relax T022 / xfail — rejected (R9: xfail only for spec gaps with ADR).
2. Widen T022's paths so QA fixes compiler code — rejected (owner grades own fixes; 4 modules in one sitting).
3. Reopen done tasks T011/T017/T019/T021 — rejected (no reopen; committed history).
4. **Chosen:** one fix task per owning area with disjoint paths; the gate depends on all.

| Task | Owner | Fixes | Paths / locks | Depends |
|---|---|---|---|---|
| T114 | axiom-frontend (sonnet) | parser P1–P5 | syntax, tests/parse, tests/ui/parse, tests/hir, tests/resolve; lock PARSE.def | T013, T015b |
| T115 | axiom-frontend (opus) | typeck/driver T1–T5 + typeck exhaustive default | types, tests/typeck, tests/ui/typeck, driver/cmd_check.c, tests/driver; locks TYPE.def, pipeline.c | T021 |
| T116 | axiom-semantics (opus) | MIR builder M1–M3, FP-03 golden regen, minimal TERM_ASSERT dispatch in interp | mir/build, tests/mir/build; lock interp/interp.c | T021 |
| T117 | axiom-semantics (opus) | interpreter I1–I5 | interp, tests/run/basic, driver/cmd_run.c; locks pipeline.c, DRIVER.def | T116 |

- T022: depends += T114, T115, T116, T117; paths += tools/ci.ps1; acceptance item for ci.ps1 alignment; note recording the unblock. Suite delivered in attempt 1 stays uncommitted in the tree and remains T022's.
- T069: depends += T061 (selfhost-subset.tsv:45 F-CONST.SCALAR, rule (d)).
- ROADMAP §5 change log row added.
- `taskctl.py unblock T022` run (status todo; it becomes ready after T114–T117 are done).

Checks: `taskctl.py lint` OK for all new/edited task files; `taskctl.py validate` OK (161 tasks);
`harness_check.py` HARNESS OK (2 pre-existing WARNs: guard hook not enabled, docs/ owner changes);
`reqcov.py --strict` COVERAGE OK. Ready now: T114, T115, T116.

Risk: T115 and T117 both lock `pipeline.c` (serialised by the scheduler). T116 touches
`interp.c` only for the Assert terminator; T117 must keep it consistent.

## Files changed
- spec/decisions/ADR-0016-vs0-gate-fix-tasks.md
- spec/ROADMAP.md
- _workspaces/tasks/todo/T114-vs0-fix-parser-expression-precedence-headers.md
- _workspaces/tasks/todo/T115-vs0-fix-typeck-diagnostics-literal-range-main.md
- _workspaces/tasks/todo/T116-vs0-fix-mir-builder-bitnot-asserts.md
- _workspaces/tasks/todo/T117-vs0-fix-interp-width-bitwise-panic.md
- _workspaces/tasks/todo/T022-vs0-gate-subset-conformance-on-the-oracle.md
- _workspaces/tasks/todo/T069-core-library-v1-axiom-source.md
- _workspaces/reports/unblock-T022.md
