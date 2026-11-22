# Unblock T422d — widen `paths:` for generic `Future` `.await` monomorphisation and generic `async fn`

## Tóm tắt
- Lượt chạy 1 của `T422d` (`_workspaces/reports/T422d-report.md`) chưa sửa mã nguồn nhưng đã chẩn đoán đầy đủ nguyên nhân gốc khiến `.await` ở chế độ native trên `impl<T> Future for Wrap<T>`, future generic lồng nhau (`Wrap<Wrap2<T>>`) và `.await` bên trong `async fn` generic bị lỗi liên kết hoặc segfault.
- Năm đường dẫn cần bổ sung đều nằm gọn trong đúng một lát cắt kỹ thuật của `T422d`: hạ tầng hạ bậc async sang máy trạng thái và kết nối monomorphisation (`compiler/mir/async_lower.ax`, `compiler/own_mir_verify/session.ax`), thế kiểu / suy diễn tham số kiểu cho `TY_COROUTINE` và mẫu kiểu tự thân lồng nhau (`compiler/traits/mono.ax`, `compiler/traits/solver.ax`), cùng thư mục test `tests/std/async/structured` để gỡ chỉ thị `native-after: T422d` theo đúng tiêu chí nghiệm thu của task.
- Quyết định: giữ nguyên phạm vi một task và mở rộng `paths:` của `T422d` thêm 5 đường dẫn trên, bổ sung mục `## Resume after unblock`, rồi gỡ chặn (`taskctl.py unblock T422d`). Không tách nhỏ task vì cả 6 file compiler đều phục vụ chung đường ống hạ bậc `.await` + monomorphisation với quy mô thay đổi vừa phải (một lượt làm việc).
- Về điều phối song song: không trùng đường dẫn với `T423h` hay `T494a`; trùng `compiler/types/typeck.ax` và `tests/std/async/structured` với `T422e` đang chạy trong `doing/`, nên `taskctl next` tự động xếp `T422d` chạy ngay sau khi `T422e` hoàn tất mà không cần thêm phụ thuộc ngữ nghĩa giả tạo vào `depends:`.
- Không cần ADR mới vì đây là sửa lỗi cài đặt theo đúng đặc tả `spec/SPEC-33-async.md` và `spec/SPEC-34-executors-fibers.md` (phân loại TYPE A). `taskctl.py validate`, `reqcov.py --strict` và `harness_check.py` đều đạt.

## Classification
TYPE A implementation defect + initial `paths:` underestimate on the board (`T422d` explicitly noted *"The paths list is a best guess; if the fix lives elsewhere … report BLOCKED naming the file so the orchestrator widens paths"*). No language or architectural semantics change; `spec/SPEC-33-async.md` and `spec/SPEC-34-executors-fibers.md` already specify `.await` on generic `Future` implementations and generic `async fn`s. No ADR required.

## Decision & Options Considered

### Scope & `paths:` decision
1. **Option 1 — Widen `T422d`'s `paths:` with all five diagnosed paths (chosen):**
   - `compiler/mir/async_lower.ax` (`mir_lower_async_body`, `async_resolve_poll_calls`): stop overwriting `Future.poll` terminators with unmonomorphised generic `HirItem`s, request concrete `MonoInstance`s, and preserve generic `args` on `TY_COROUTINE`.
   - `compiler/own_mir_verify/session.ax` (`session_lower_all_async`): run async lowering in a fixpoint with `MonoEngine` over concrete `MonoInstance` clones of generic `async fn`s (registering synthesized `poll_it` items in `MonoEngine` so `compiler/driver/pipeline.ax`'s existing `pipe_is_mono_clone` check includes them without editing `pipeline.ax`).
   - `compiler/traits/mono.ax` (`type_contains_param`, `subst_ty_self`, `deduce_args`): add `TY_COROUTINE` handling so generic coroutine return types are substituted and deduced during monomorphisation.
   - `compiler/traits/solver.ax` (`type_matches_impl_self_exact`, `type_satisfies_auto_trait`): match nested generic impl self-types (`Wrap<Wrap2<T>>`) structurally and inspect `TY_COROUTINE.fields` for auto-trait checks (`Send`/`Sync`) once `TY_COROUTINE.args` holds generic type arguments.
   - `tests/std/async/structured`: required by `T422d`'s existing scope to remove `"native-after: T422d"` from `tests/std/async/structured/gen_tests.py` and regenerate `tests/std/async/structured/spec34_task_group_example.ax`.
   - Verification against downstream pipeline stages (`compiler/driver/pipeline.ax`, `compiler/types/types.ax`, `compiler/interp/interp.ax`, `compiler/interp_opt/session.ax`) confirms no additional files outside the 8 widened `paths:` are needed.
2. **Option 2 — Split `T422d` into sub-tasks (rejected):**
   - Splitting `.await` on generic `Future` impls from nested generic futures / generic `async fn` would touch the exact same async-lowering ↔ `MonoEngine` boundary across the same files, doubling stage-2 rebuild and `taskgate` overhead for a cohesive single-sitting fix.

### Scheduling & `depends:` decision
- `T423h` and `T494a` (both in `doing/`) have zero path overlap with widened `T422d`.
- `T422e` (in `doing/`) holds `compiler/types/typeck.ax` and `tests/std/async/structured`. Because `T422d` has no semantic dependency on `T422e` (`AsyncMutexGuard` `@no_suspend_hold` policy), `depends: [T422c]` is kept unchanged while `taskctl next` cleanly serialises `T422d` after `T422e` via `paths:` edit locks.

## Board & Verification Checks
- Updated `_workspaces/tasks/todo/T422d-fix-native-await-on-generic-future-impl.md` (`paths:` widened to 8 entries + `## Resume after unblock` guidance) and ran `taskctl.py unblock T422d` (`status: todo`, `unblocks: 1`).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py lint _workspaces/tasks/todo/T422d-fix-native-await-on-generic-future-impl.md` → `OK`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py validate` → `OK (747 tasks)`.
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → `COVERAGE OK`.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → `HARNESS OK`.

## Files changed
- _workspaces/tasks/todo/T422d-fix-native-await-on-generic-future-impl.md
- _workspaces/reports/unblock-T422d.md
