# Triage — T423 follow-ups (architect, 2026-11-21)

## Tóm tắt
- Tạo 7 task sửa ở P11 từ QA/báo cáo của T423 và yêu cầu bổ sung của orchestrator; tất cả nằm trong `depends` của gate P11 (T311).
- Mục 1–4 theo yêu cầu: T423a (`drop_in_place` trên closure không drop giá trị bị bắt), T423b (panic trong fiber native phải
  trả `Panicked`), T423c (gọi hàm generic không ghi kiểu trong thân closure), T423d (bound của method nhắc generic của `impl`).
  Thêm T423e (placeholder self-entry trùng tên giữa hai module chạy nhầm hàm) và T423f (`build_axiomc.py` seeded không tự lùi về
  full chain) vì QA liệt kê là follow-up 4 và 5 — để board phản ánh đúng.
- Mục 5: quyết định bằng ADR-0047 — binding theo giá trị trong arm `match`/`if let`/`while let` bị drop **ở cuối arm** (theo
  `0134 §26` APATTERN-28, `0159 §26`), thêm quy tắc SPEC-12 AXS-DROP-009; task sửa T445a (kèm sửa test
  `resource_governor_limits` đang dựa vào hành vi cũ).
- ADR-0046: (D1) cho phép `// xfail: <task sửa đang mở>` với repro lỗi compiler do task ngoài vùng compiler phát hiện (đúng
  tiền lệ ADR-0044) — **chấp nhận** ở T423; (D2) đưa các sai khác của T423 vào SPEC-34 §5; (D3) huỷ fiber đang treo không drop
  biến cục bộ (rò rỉ an toàn, Revisit); (D4) `native-after: T423b`; (D5) handle native phải gắn với luồng.
- Không sửa file nào thuộc paths/locks của T423.

## Mapping
| Item | Task | Owner / model | Priority | Depends |
|---|---|---|---|---|
| 1 `drop_in_place<closure>` no-op (QA F1, FU-1) | **T423a** | axiom-semantics / opus | 30 | T423 |
| 2 native fiber panic containment (QA F3, report F1) | **T423b** | axiom-stdlib / opus | 40 | T423 |
| 3 generic call inference in closure body (report F2) | **T423c** | axiom-semantics / opus | 45 | T423 |
| 4 impl-level generic in method bound (report F3) | **T423d** | axiom-frontend / opus | 45 | T423 |
| 5 match-arm binding drop scope (T445 dev. 2, T444b F2) | **T445a** (+ ADR-0047) | axiom-semantics / opus | 25 | T445, T444b, T423 |
| extra: self-entry placeholder keyed by name (QA FU-4, report F4) | T423e | axiom-semantics / opus | 50 | T423 |
| extra: seeded bootstrap fallback (QA FU-5, report F5) | T423f | axiom-qa / sonnet | 35 | — |

The P11 block T400–T449 is full (`new-id` reports no free id), so suffix ids of the originating tasks are used.

## What T423 must do in its fix round (decided)
- **xfail (QA F4): acceptable with the new ids.** These are compiler implementation bugs found by a std task, outside its
  owning area; ADR-0046 D1 (precedent ADR-0044) accepts `// xfail: <open fix task>` when the fix task was filed by the
  architect, owns the test file in `paths:` and must remove the line. Change
  `tests/std/fiber/closure_generic_infer_xfail.ax` to `// xfail: T423c ...` and
  `tests/std/fiber/impl_generic_in_method_bound_xfail.ax` to `// xfail: T423d ...`. `axiom-testing` and `axiom-qa` now
  state this rule explicitly.
- **QA F3:** `tests/std/fiber/gen_tests.py` emits `// modes: interp native` plus `// native-after: T423b` for
  `fiber_panic_contained` (no `modes: interp`); regenerate.
- **QA F1:** in `std/fiber/mod.ax` move the closure out of its box into a local (`let _dead: F = *(c_ptr as *mut F);`) instead of
  `drop_in_place<F>` (phase 2 of the trampoline and `Drop for Fiber`), so `qa_fiber_drop` passes; T423a fixes the compiler.
- **QA F2:** make native handles identify their owner thread (SPEC-34 AXS-EXEC-055.4), keep `-4` for a foreign handle.
- If any fiber test expectation depends on where an arm binding (`Yielded(_g)`) is dropped, write it so it does not depend on
  it (bind into a `let` or drop explicitly); T445a changes the drop point to the end of the arm.

## Spec changes
- `spec/SPEC-34-executors-fibers.md`: Tóm tắt bullet; AXS-EXEC-053 rules 2 (destroy per state) and 3 (T423 implementation
  shape: raw heap queue, `FiberId` `@derive(Copy)` + `eq/clone/as_u64`, `Fiber.new` without `FnOnce` bound until T423d,
  explicit type args in closures until T423c, extra pub items); AXS-EXEC-054 code block `resume_arg` and notes (parameter name,
  temporary native panic divergence); AXS-EXEC-055 rules 4 (per-thread table, owner-identifying handle) and 5 (panic
  containment, T423b).
- `spec/SPEC-12-drop.md`: AXS-DROP-009 (drop scope of pattern bindings), Tóm tắt line.

## Checks
- `taskctl.py lint` OK for the 7 new tasks and T311; `taskctl.py validate` OK (731 tasks); `harness_check.py` HARNESS OK;
  `reqcov.py --strict` COVERAGE OK (gaps 0).

## Files changed
- spec/decisions/ADR-0046-t423-fiber-followups-and-tracked-xfail.md
- spec/decisions/ADR-0047-match-arm-binding-drop-scope.md
- spec/SPEC-34-executors-fibers.md
- spec/SPEC-12-drop.md
- spec/ROADMAP.md
- .claude/skills/axiom-testing/SKILL.md
- .claude/agents/axiom-qa.md
- _workspaces/tasks/todo/T423a-fix-drop-in-place-no-op-for-closure-and-glue-only-types.md
- _workspaces/tasks/todo/T423b-native-fiber-panic-containment-windows.md
- _workspaces/tasks/todo/T423c-fix-generic-call-inference-inside-closure-body.md
- _workspaces/tasks/todo/T423d-fix-method-bound-naming-impl-level-generic-unresolved.md
- _workspaces/tasks/todo/T423e-fix-self-entry-placeholder-keyed-by-name.md
- _workspaces/tasks/todo/T423f-build-axiomc-seeded-bootstrap-fallback-full-chain.md
- _workspaces/tasks/todo/T445a-fix-match-arm-binding-dropped-at-end-of-arm.md
- _workspaces/tasks/todo/T311-phase-p11-gate-concurrency-async.md
- _workspaces/reports/triage-t423.md
