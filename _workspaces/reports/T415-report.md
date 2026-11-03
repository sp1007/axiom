# T415 Report — E11.4 Canonical `async`/`await`, `Future` & State-Machine Specification (`SPEC-33`)

## Tóm tắt
Báo cáo hoàn thành task `T415` (`E11.4`): biên soạn đặc tả chuẩn `spec/SPEC-33-async.md` quy định toàn bộ
mô hình lập trình bất đồng bộ không tốn chi phí ẩn (`zero-overhead async/await`) của Axiom cho compiler
tự thân `axiomc` và thư viện chuẩn `std.future`. Tài liệu hợp nhất các nguồn `0093`, `0127`, `0135`,
`0159 §8`, `0161`, `0201`, `0202`, `0248`, `tasks/0275`, `tasks/0297`, `tasks/0619` cùng `SPEC-04`,
`SPEC-30`, `SPEC-31`, `SPEC-32` thành các quy tắc định danh `AXS-ASY-001`..`AXS-ASY-052`. Đặc tả ấn định
giao diện `Poll<T>`/`Waker`/`Context`/`Future` (không dùng `Pin<T>` trong Core v1.0), hạ tầng hạ bậc HIR
và MIR (`compiler/mir/async_lower.ax`), phân tích biến sống qua điểm tạm dừng (`live-across-await`),
sinh mã hủy theo từng trạng thái (`cancellation Drop glue`), và giao thức kiểm thử đối chiếu với trình
thông dịch MIR (`oracle`). Đồng thời cập nhật `spec/INDEX.md`, `spec/diagnostics.md` và `spec/invariants.md`.

## Summary of Deliverables

1. **`spec/SPEC-33-async.md` (`AXS-ASY-001`..`AXS-ASY-052`)**:
   - **§1 Architectural Foundations (`AXS-ASY-001`..`AXS-ASY-008`)**: Defines `ExecutionContext` decoupling (`Thread` vs `Fiber` vs `Task` vs `Future` vs `Executor`), unified ownership and race-safety across sync/async code, zero mandatory heap allocation and no hidden runtime threads, elimination of `Pin<T>` in Core v1.0 via explicit stable-address polling contracts and self-view reconstruction on resume, cold compiler-generated futures vs eager spawned tasks, suspension-free straight-line optimization (`K == 0`), and GPU async stream/event lifetime compatibility.
   - **§2 Core Lang Items & `std.future.block_on` (`AXS-ASY-010`..`AXS-ASY-015`)**: Specifies exact Axiom signatures in `std/future/mod.ax` (`Poll<T>`, `RawWaker`, `RawWakerVTable`, `Waker`, `Context`, `Future`), single-threaded deterministic `std.future.block_on` in `std/future/block_on.ax` using atomic wake flags and `Thread.park()`/`Thread.unpark()`, and `std/core/prelude.ax` re-exports (`Future`, `Poll`).
   - **§3 Surface Syntax, HIR Desugaring & Type/Effect Rules (`AXS-ASY-020`..`AXS-ASY-027`)**: Specifies lowering of `async fn` and `async { ... }` to anonymous `Coroutine(DefId, Substs)` types, `.await` operand/context validation (`AX_ASYNC_AWAIT_OUTSIDE_ASYNC`, `AX_ASYNC_AWAIT_IN_DROP`, `AX_ASYNC_NOT_A_FUTURE`), `?` interaction inside `async` bodies, static vs `dyn` dispatch for trait `async fn`, compile-time call-graph cycle rejection (`AX_ASYNC_RECURSIVE_FUTURE`), FFI ABI prohibition (`AX_ASYNC_EXTERN_ABI`), and `AsyncSuspend` vs `Blocking` effect diagnostics (`AX_ASYNC_BLOCKING_IN_ASYNC`).
   - **§4 Suspension Points & Live-Across-Await Analysis (`AXS-ASY-030`..`AXS-ASY-037`)**: Defines the pre-lowering MIR `Suspend` terminator and `SuspensionPointId`, exact dataflow equation `LiveAcross(s) = Gen(s) ∪ (LiveIn(bb_resume(s)) \ Def(bb_resume(s)))` after pre-suspension drop elaboration, owned value storage, unconditional prohibition of `view<T>`/`mut_view<T>` (`AX_ASYNC_VIEW_ACROSS_AWAIT`) and synchronous lock guards (`AX_ASYNC_GUARD_ACROSS_AWAIT`) across `.await`, `Future: Send` derivation strictly from parameters + `LiveAcross(s)` fields (`AX_ASYNC_FUTURE_NOT_SEND`), and `Future: !Share`.
   - **§5 MIR State-Machine Lowering & Cancellation Drop Glue (`AXS-ASY-040`..`AXS-ASY-046`)**: Specifies `compiler/mir/async_lower.ax` synthesis of `__AsyncState_f` (`state_tag: u32` with `0 = Unstarted`, `1..K = Suspended(s)`, `0xFFFF_FFFE = Complete`, `0xFFFF_FFFF = Poisoned`), cold constructor lowering, `Future.poll` `SwitchInt` dispatch and loop-free resume edges, state-specific cancellation `Drop` glue (dropping active sub-future first, then saved locals in reverse declaration order), separation of internal cleanup from external cancellation triggers, and the optimizer barrier contract for `Suspend`.
   - **§6–§8 Oracle Execution, Diagnostics & Traceability (`AXS-ASY-050`..`AXS-ASY-052`)**: Defines deterministic oracle `Future.poll` stepping, `POLL`/`SUSPEND`/`WAKE`/`RESUME`/`COMPLETE`/`CANCEL_DROP` trace events, `inspect --emit=async-layout`, the 10 `AX_ASYNC_*` diagnostic codes, canonical positive/negative examples, and full traceability across all 33 `T415` `covers:` requirements and downstream tasks `T416`, `T417`, `T088`, `T418`, and `T419`.

2. **Index, Diagnostics & Invariants Updates**:
   - **`spec/INDEX.md`**: Added `spec/SPEC-33-async.md` to `§2`, `AXS-ASY-NNN` to `§4`, and updated the Concurrency & Async row in `§5`.
   - **`spec/diagnostics.md`**: Updated `AXD-021` for `E11.4` (`AX_ASYNC_*` in `compiler/diag/code.ax`) and registered all 10 `AX_ASYNC_*` codes in `§11`.
   - **`spec/invariants.md`**: Added `INV-CONC-008` (`since: T416`), `INV-CONC-009` (`since: T417`), and `INV-CONC-010` (`since: T418`) in `§11`.

## Verification
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: PASS (100.0% requirement coverage)
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: PASS
- `python tools/gatecheck.py --no-run`: PASS
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T415`: PASS (`0 REFUSED`)

STATUS: COMPLETE

## Files changed
- `spec/SPEC-33-async.md`
- `spec/INDEX.md`
- `spec/diagnostics.md`
- `spec/invariants.md`
