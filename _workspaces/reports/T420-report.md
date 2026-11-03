# T420 Report — E11.5 Canonical Executors, Structured Concurrency & Fiber Specification (`SPEC-34`)

## Tóm tắt
Báo cáo hoàn thành task `T420` (`E11.5`): biên soạn đặc tả chuẩn `spec/SPEC-34-executors-fibers.md` quy định
mô hình thực thi tác vụ bất đồng bộ (`Task`, `TaskHandle`, `TaskControlBlock`), bộ lập lịch đơn luồng
`LocalExecutor` (`spawn_local`), bộ lập lịch đa luồng đánh cắp công việc `Executor` (`spawn`), đồng thời có
cấu trúc `TaskGroup`, hủy bỏ hợp tác `CancellationToken`, hạn chót `Deadline`/`Timeout`, bộ quản trị tài
nguyên `ResourceGovernor`, các nguyên thủy đồng bộ hóa bất đồng bộ (`AsyncMutex<T>`, `AsyncRwLock<T>`,
`AsyncSemaphore`, kênh bất đồng bộ `std.async.channel`) và mô hình coroutine có ngăn xếp tường minh
`Fiber<Y, R>` (`std.fiber`, `host.fiber_*`). Tài liệu hợp nhất các nguồn `0202`, `0204`, `0205`,
`tasks/0277`, `tasks/0278`, `tasks/0620`, `tasks/0621`, `tasks/0834`, `tasks/0835`, `tasks/0836` cùng
`SPEC-04` và `SPEC-30`..`SPEC-33` thành các quy tắc định danh `AXS-EXEC-001`..`AXS-EXEC-056`. Đồng thời cập
nhật `spec/INDEX.md` và `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-110`, `AXS-EXT-130`).

## Summary of Deliverables

1. **`spec/SPEC-34-executors-fibers.md` (`AXS-EXEC-001`..`AXS-EXEC-056`)**:
   - **§1 Architectural Foundations (`AXS-EXEC-001`..`AXS-EXEC-007`)**: Establishes `Executor` and `Task` as link-on-demand library abstractions outside the language Core (`REQ-ASY-036`, `REQ-ASY-067`..`068`, `REQ-ASY-089`, `REQ-ASY-094`, `REQ-ASY-149`, `REQ-ASY-156`, `REQ-CONC-200`, `REQ-ASY-161`..`163`), strict separation of `Future<T>`, `Task`, `TaskHandle<T>`, and `Executor` (`REQ-CONC-023`, `REQ-ASY-164`), coalesced hot/cold `TaskControlBlock<F>` with intrusive `queue_next` linkage and generation-stamped `TaskId`, the atomic task wake state machine (`TASK_IDLE`, `TASK_POLLING`, `TASK_NOTIFIED`, `TASK_COMPLETED`, `TASK_CANCELLED`, `TASK_PANICKED`) with state-transition diagram guaranteeing idempotent `wake()` and zero lost wakeups, `Happens-Before` completion synchronization, and panic handling (`REQ-ASY-019`, `REQ-ASY-051`).
   - **§2 `LocalExecutor` vs Work-Stealing `Executor` (`AXS-EXEC-010`..`AXS-EXEC-016`)**: Specifies single-thread `LocalExecutor` (`spawn_local` pinning `!Send` futures to the creation thread while preserving ownership and aliasing rules across interleaved tasks, `REQ-CONC-034`..`035`), multi-thread work-stealing `Executor` (`spawn` requiring `F: Future + Send` and `F.Output: Send`, `REQ-ASY-040`, `REQ-CONC-148`), per-worker Chase-Lev/ring deques + bounded global injection queue, `spawn_blocking`, `yield_now()`, deterministic shutdown, and `DeterministicExecutor` oracle verification (`REQ-ASY-060`).
   - **§3 Structured Concurrency, Cancellation, Deadlines & `ResourceGovernor` (`AXS-EXEC-020`..`AXS-EXEC-025`)**: Specifies `TaskGroup<T>` (lexical lifetime containment, sibling cancellation on child failure/panic, deterministic join/drain), explicit `.detach()` vs handle drop cancellation, prohibition of forced thread/task termination (`REQ-CONC-149`), hierarchical `CancellationSource` / `CancellationToken`, `Deadline` / `Timeout<F>`, and `ResourceGovernor` quota/pressure accounting (`tasks/0834`).
   - **§4 Async-Aware Synchronization (`AXS-EXEC-030`..`AXS-EXEC-034`)**: Specifies `AsyncMutex<T>` (`AsyncMutexGuard<T>` safe across `.await`), `AsyncRwLock<T>`, `AsyncSemaphore`, and `AsyncSender<T>` / `AsyncReceiver<T>`, together with their waiter cancellation-safety contracts (baton forwarding on cancelled `AsyncMutexLockFuture`, permit forwarding on cancelled `AsyncSemaphoreAcquireFuture`, and zero message loss on cancelled `RecvFuture`).
   - **§5 Stackful `Fiber<Y, R>` & `host.fiber_*` (`AXS-EXEC-050`..`AXS-EXEC-056`)**: Specifies `Fiber<Y, R>`, `FiberState<Y, R>`, `FiberBuilder` (explicit stack commit/reserve contract), `yield_val` / `yield_now`, `FiberScheduler`, default `!Send`/`!Share` thread-pinned affinity (`REQ-CONC-151`, `REQ-CONC-189`), and the four host intrinsics (`host.fiber_create`, `host.fiber_resume`, `host.fiber_yield`, `host.fiber_destroy`) across Win32 (`ConvertThreadToFiberEx`, `CreateFiberEx`, `SwitchToFiber`, `DeleteFiber`) and the MIR interpreter oracle.
   - **§6–§8 Examples, Traceability & Sources**: Canonical Axiom examples (using `=` and `.`), requirement traceability matrix for all 17 `T420` `covers:` requirements and downstream tasks `T421`–`T424`, and sources.

2. **`spec/INDEX.md` & `spec/SPEC-04-core-extensibility.md` Updates**:
   - **`spec/INDEX.md`**: Added `spec/SPEC-34-executors-fibers.md` to `§2`, `AXS-EXEC-NNN` to `§4`, and updated the Concurrency & Async row in `§5`.
   - **`spec/SPEC-04-core-extensibility.md`**: Registered `fiber_create`, `fiber_resume`, `fiber_yield`, and `fiber_destroy` in `AXS-EXT-110` (`§11`) and updated the `E11.5 Executors & fibers` row in `AXS-EXT-130` (`§13`).

## Verification
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: PASS (100.0% requirement coverage)
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: PASS
- `python tools/gatecheck.py --no-run`: PASS
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T420`: PASS (`0 REFUSED`)

STATUS: COMPLETE

## Files changed
- `spec/SPEC-34-executors-fibers.md`
- `spec/INDEX.md`
- `spec/SPEC-04-core-extensibility.md`
