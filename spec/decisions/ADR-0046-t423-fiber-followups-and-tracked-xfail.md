# ADR-0046 — T423 fiber follow-ups: tracked xfail, SPEC-34 §5 deviations, suspended-fiber destroy

Status: accepted (2026-11-21, architect; owner-delegated decision). Type B (architecture clarification) for D1, D2, D4, D5;
Type C (semantic statement) for D3.

## Tóm tắt
- QA của T423 (`std.fiber`) phát hiện 4 việc ngoài phạm vi T423: `drop_in_place<T>` trên kiểu closure không drop giá trị bị
  bắt (rò rỉ, interp và native giống nhau); panic trong fiber native kết thúc cả tiến trình (exit 101) trong khi oracle trả
  `FiberState.Panicked`; lời gọi hàm generic không ghi kiểu bên trong thân closure báo `AX_TYPE_UNKNOWN`; ràng buộc của
  method nhắc tới generic của `impl` báo `AX_NAME_UNRESOLVED`. Mỗi việc thành một task sửa: T423a, T423b, T423c, T423d;
  thêm T423e (placeholder `__ax_*_self_entry` trùng tên giữa hai module làm chạy nhầm hàm) và T423f (`build_axiomc.py`
  seeded không tự lùi về full chain).
- D1: dòng `// xfail: <task>` trỏ tới một task sửa **đang mở do architect tạo** được chấp nhận cho lỗi compiler mà một task
  ngoài vùng compiler phát hiện (đúng tiền lệ ADR-0044); task sửa sở hữu file test và phải gỡ dòng `xfail`. Không bao giờ
  dùng cho lỗi trong chính change set của task. T423 đổi `xfail: T423` thành `xfail: T423c` / `xfail: T423d`.
- D2: các sai khác của T423 được đưa vào SPEC-34 §5 (hàng đợi heap thô, `FiberId` chỉ `@derive(Copy)` + method,
  `Fiber.new` tạm thiếu bound `FnOnce` đến T423d, tham số `resume_arg`, các trường/method công khai thêm).
- D3: huỷ một fiber đang treo (Yielded) giải phóng ngăn xếp nhưng **không** chạy Drop của biến cục bộ còn sống (rò rỉ an
  toàn bộ nhớ, như `DeleteFiber`); fiber chưa chạy (Created) phải drop closure (và giá trị bị bắt) đúng một lần.
  Huỷ hợp tác có unwind để sau (Revisit).
- D4: `fiber_panic_contained` dùng `// native-after: T423b` thay vì `modes: interp`. D5: handle fiber native phải duy nhất
  giữa các luồng (QA F2), sửa trong vòng sửa của T423.

## Context
- `_workspaces/reports/T423-qa.md` round 0: F1 (closure captures of a never-started fiber leak, root cause
  `drop_in_place<closure>` is a no-op), F2 (native fiber handles `(generation << 32) | slot` collide across threads),
  F3 (`fiber_panic_contained.ax` is `modes: interp`), F4 (`xfail: T423` names the task under gate), "Follow-ups for the
  architect" 1–6.
- `_workspaces/reports/T423-report.md` "Deviations from SPEC-34" 1–6 and Follow-ups F1–F5.
- `compiler/mir/builder.ax` `mb_scan_or_rewrite_calls`: `drop_in_place<T>` is rewritten into a call of the monomorphized
  `Drop` impl only when `T` has a direct `Drop` impl (`mb_instantiate_drop_for_ty` returns an instance); for any other
  type that needs drop (closures, tuples, structs/enums without their own `Drop` but with droppable fields) the call
  stays the builtin and does nothing. SPEC-12 AXS-DROP-005 requires recursive drop glue.
- axiom-testing "xfail" rule ("spec gap with an ADR and an open task, never an implementation bug") versus the accepted
  precedent ADR-0044 (compiler bugs found by the T455 std suite committed as `xfail: <fix task>`).
- `0204 §18` (fiber destroyed only when COMPLETED or after cancellation) versus SPEC-34 AXS-EXEC-051.2 (destroy allowed in
  `Created` / `Yielded`).

## Options
### D1 — xfail repro tests of compiler bugs found by a std task
1. Strict rule: delete the two repro tests from T423 and move them into the fix tasks. Loses a committed, runnable repro
   until the fix task starts; the fix task re-creates the same file.
2. **Keep the repro, `// xfail: <open fix task>`, the fix task owns the file and removes the line (chosen).** XPASS
   counts as FAIL, so a fix that lands elsewhere is noticed at once; `grep "xfail: T423c"` shows the open debt. Same as
   ADR-0044. The limit stays: a bug in the finding task's own change set is never xfailed, and the xfail must name an
   open task filed by the architect, never the task under gate.
3. Baseline list (`_workspaces/baseline-failures.txt`). Rejected: that list is for pre-existing failures found by a
   complete run, not for new repros.

### D3 — destroying a suspended fiber
1. **Leak the live locals of a suspended fiber (no Drop), memory-safe, documented (chosen).** Matches Win32 `DeleteFiber`
   and what both implementations do today; no hidden unwinding runtime (frozen semantic model: no hidden runtime).
2. Unwind the fiber's frames on destroy (cooperative cancellation: resume it with a cancel flag, run drops to the
   entry). Needs `--panic unwind` machinery (SPEC-54) on fiber stacks; out of P11 scope.
3. Forbid destroy of a suspended fiber (panic). Breaks `FiberScheduler` drop and generator-style early exit.

## Decision
- **D1.** An `// xfail: <task>` line is accepted when (a) the failure is a compiler/tooling implementation bug outside
  the owning area of the task that found it, (b) the named task is open and was filed by the architect with the test file
  in its `paths:`, and (c) the fix task's acceptance says it removes the line. It is never accepted for a bug in the
  finding task's own change, nor naming the task under gate. axiom-testing and axiom-qa are updated to say so.
  T423 (fix round) changes `tests/std/fiber/closure_generic_infer_xfail.ax` to `// xfail: T423c ...` and
  `tests/std/fiber/impl_generic_in_method_bound_xfail.ax` to `// xfail: T423d ...`.
- **D2.** SPEC-34 §5 records the T423 shape (AXS-EXEC-053 / 054 / 055 notes "T423 implementation shape").
- **D3.** AXS-EXEC-053 rule 2: dropping a `Fiber` in state `Created` drops its entry closure (and every captured value)
  exactly once without running it; in state `Yielded` it releases the stack and the host record, and the live locals of the
  fiber's frames are **not** dropped (leaked; memory-safe, never UB). `Completed` / `Panicked` fibers have nothing live.
  A yielded value already handed to the resumer is owned by the resumer. Cooperative cancellation with unwinding is a
  possible later extension (Revisit).
- **D4.** Native panic containment is required (AXS-EXEC-054 return `2`); until T423b, `fiber_panic_contained` runs with
  `// native-after: T423b` (T423 changes `tests/std/fiber/gen_tests.py` to emit that line instead of `modes: interp`).
- **D5.** AXS-EXEC-055: a native fiber handle identifies its owner thread; a handle of another thread returns `-4` even
  when the calling thread owns a slot with the same index (QA F2). Fixed by T423 in its fix round (its own paths).
- F1 workaround inside T423: `std.fiber` moves the closure out of its box into a local (`let _dead: F = *(c_ptr as *mut F);`)
  so it is dropped by scope, until T423a makes `drop_in_place<F>` correct.

## Consequences
- New tasks (phase P11, all `depends: [T423]` except T423f): **T423a** `drop_in_place<T>` drop glue for every needs-drop
  type (semantics), **T423b** native fiber panic containment (stdlib), **T423c** generic call inference inside closure
  bodies (semantics), **T423d** impl-level generic in a method bound (frontend; restores `F: FnOnce<R>` on
  `Fiber.new`/`Fiber.spawn`), **T423e** self-entry placeholder keyed by name (semantics), **T423f**
  `build_axiomc.py` seeded fallback to the full chain (qa). T311 (P11 gate) depends on all six.
- Specs amended: SPEC-34 §5 (AXS-EXEC-053, 054, 055 notes; rule 053.2). Harness text: `.claude/skills/axiom-testing/SKILL.md`
  and `.claude/agents/axiom-qa.md` xfail wording.
- Tests affected: `tests/std/fiber/fiber_panic_contained.ax` (T423 → `native-after: T423b`; T423b removes it),
  the two `*_xfail.ax` files (T423 renames the id; T423c/T423d remove the line), `tests/std/fiber/qa_fiber_drop.ax`
  (passes after the T423 workaround; T423a adds compiler-level tests under `tests/run/drop_in_place_glue`).

## Revisit
- D3: yes — if structured cancellation (T424 / SPEC-34 §3) needs fibers to release guards on cancel, add cooperative
  unwinding on destroy (Option D3.2).
- D1: no.

## Sources
- `_workspaces/reports/T423-qa.md`, `_workspaces/reports/T423-report.md`; `spec/SPEC-34-executors-fibers.md` AXS-EXEC-050..056;
  `spec/SPEC-12-drop.md` AXS-DROP-005; `spec/SPEC-54-panic-unwinding.md`; ADR-0044 (xfail precedent), ADR-0005 §1
  (`native-after`); `docs/base/specs/0204` §18; `compiler/mir/builder.ax` `mb_scan_or_rewrite_calls`.
