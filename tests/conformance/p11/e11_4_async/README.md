# E11.4 — Async/Await, Future Layout & Cancellation Conformance Suite (`tests/conformance/p11/e11_4_async`)

Governing specification: `spec/SPEC-33-async.md` (Phase 11, Epic E11.4, Task `T419`).

## Suite Inventory

| Test File | Test Kind | Execution Modes | Purpose & Covered Rules |
|---|---|---|---|
| `async_control_flow.ax` | `run` | `interp`, `native`, `native-O1` | Sequential multi-await chains, conditional branching (`if`/`else`), and `while` loop control flow with suspension points (`REQ-ASY-064`, `REQ-ASY-065`, `REQ-ASY-070`, `REQ-ASY-079`, `REQ-ASY-142`, `AXS-ASY-001`, `AXS-ASY-002`, `AXS-ASY-033`, `AXS-ASY-043`). Verifies that loop accumulators and branch variables survive across state-machine boundaries without corruption or leakage. |
| `async_try_operator.ax` | `run` | `interp`, `native`, `native-O1` | Try operator `?` (`Result<T, E>`) desugaring across `.await` suspension points (`REQ-ASY-070`, `REQ-ASY-079`, `REQ-ASY-080`, `REQ-ASY-142`, `AXS-ASY-023`, `AXS-ASY-044`). Verifies both the success path and the early-return error path, ensuring active live locals in scope are dropped deterministically without memory leaks. |
| `async_generic_custom_future.ax` | `run` | `interp`, `native`, `native-O1` | Custom `Future` state machines (`YieldTwice`, `MultiStepFuture`) transitioning across multi-step `Poll.Pending` states, awaited from `async fn` and generic drivers (`REQ-ASY-011`, `REQ-ASY-070`, `REQ-ASY-079`, `REQ-ASY-142`, `AXS-ASY-013`, `AXS-ASY-014`, `AXS-ASY-043`). Proves state-machine composition and zero mandatory heap allocation. |
| `async_cancellation_drop_order.ax` | `run` | `interp`, `native`, `native-O1` | Mid-flight cancellation drop order dispatch (`REQ-ASY-011`, `REQ-ASY-079`, `REQ-ASY-080`, `AXS-ASY-044`). Suspends nested outer and inner async tasks at an in-flight leaf future, then drops the outer future. Verifies exact deterministic drop order: child in-flight sub-future dropped first, followed by live state locals in reverse declaration order, and captured parameters in reverse declaration order. |
| `async_lifecycle_trace_stack.ax` | `run` | `interp`, `native`, `native-O1` | Zero-heap stack polling via `block_on`, thread constancy, synchronization preservation, and deterministic lifecycle trace (`REQ-ASY-010`, `REQ-ASY-064`, `REQ-ASY-082`, `REQ-ASY-083`, `REQ-ASY-133`, `AXS-ASY-001`, `AXS-ASY-002`, `AXS-ASY-014`, `AXS-ASY-046`, `AXS-ASY-050`). Emits canonical trace events (`POLL`, `SUSPEND`, `WAKE`, `RESUME`, `COMPLETE`) in sequence and verifies identical thread execution context across sequential awaits. |
| `async_explicit_gpu_lifetime.ax` | `run` | `interp`, `native`, `native-O1` | Explicit device buffer lifetime contract simulation across asynchronous device events (`REQ-ASY-134`, `AXS-ASY-008`). Proves that buffer ownership is retained during in-flight device operations and cannot be mutated or freed on the host until completion. |
| `async_poll_completed_panic.ax` | `run` | `interp`, `native`, `native-O1` | Polling a completed `Future` state machine deterministically panics (`REQ-ASY-081`, `AXS-ASY-013`, `AXS-ASY-043`, `AXS-ASY-050`). Verifies `exit: 101` and stderr message `polling a completed Future state machine`. |
| `async_poll_cancelled_panic.ax` | `run` | `interp`, `native`, `native-O1` | Polling a cancelled `Future` state machine deterministically panics (`REQ-ASY-081`, `AXS-ASY-043`, `AXS-ASY-050`). Verifies `exit: 101` and stderr message `polling a completed Future state machine`. |
| `async_ui_view_across_await.ax` | `ui` | compile check | Negative compile-time check: rejects `view<T>` live across `.await` with `AX_ASYNC_VIEW_ACROSS_AWAIT` (`REQ-ASY-070`, `REQ-ASY-142`, `AXS-ASY-034`, `AXS-ASY-052`). |
| `async_ui_mut_view_across_await.ax` | `ui` | compile check | Negative compile-time check: rejects `mut_view<T>` live across `.await` with `AX_ASYNC_VIEW_ACROSS_AWAIT` (`REQ-ASY-070`, `REQ-ASY-142`, `AXS-ASY-034`, `AXS-ASY-052`). |
| `async_ui_guard_across_await.ax` | `ui` | compile check | Negative compile-time check: rejects `MutexGuard` held across `.await` with `AX_ASYNC_GUARD_ACROSS_AWAIT` (`REQ-ASY-070`, `REQ-ASY-142`, `AXS-ASY-035`, `AXS-ASY-052`). |
| `async_ui_send_bounds.ax` | `ui` | compile check | Negative compile-time check: rejects passing a `Future` holding a `!Send` value across `.await` to a `Send`-bounded consumer (`spawn`) with `AX_ASYNC_FUTURE_NOT_SEND` (`REQ-ASY-075`, `AXS-ASY-036`, `AXS-ASY-052`). |
| `async_ui_not_share.ax` | `ui` | compile check | Negative compile-time check: verifies that compiler-synthesized `Future` state machines are `!Share` and emit `AX_CONC_NOT_SHARE` when passed to a `Share` bound (`REQ-ASY-077`, `AXS-ASY-037`, `AXS-ASY-052`). |
| `async_ui_recursive_future.ax` | `ui` | compile check | Negative compile-time check: rejects unboxed recursive `async fn` state cycles with `AX_ASYNC_RECURSIVE_FUTURE` (`REQ-ASY-078`, `AXS-ASY-025`, `AXS-ASY-052`). |
| `async_ui_not_a_future.ax` | `ui` | compile check | Negative compile-time check: rejects `.await` on an operand that does not implement `Future` with `AX_ASYNC_NOT_A_FUTURE` (`REQ-ASY-142`, `AXS-ASY-022`, `AXS-ASY-052`). |
| `async_ui_await_outside_async.ax` | `ui` | compile check | Negative compile-time check: rejects `.await` expression outside an async function or block with `AX_ASYNC_AWAIT_OUTSIDE_ASYNC` (`REQ-ASY-065`, `REQ-ASY-142`, `AXS-ASY-022`, `AXS-ASY-052`). |
| `async_ui_await_in_drop.ax` | `ui` | compile check | Negative compile-time check: rejects `.await` expression inside `Drop.drop` with `AX_ASYNC_AWAIT_IN_DROP` (`REQ-ASY-080`, `REQ-ASY-142`, `AXS-ASY-022`, `AXS-ASY-052`). |
| `qa_async_nested_result_cancel_trace.ax` | `run` | `interp`, `native`, `native-O1` | Adversarial QA boundary test: combines nested `async fn` returning `Result<T, E>`, try operator `?` across multi-step `.await` with early return drop order verification, and mid-flight cancellation drop order dispatch (`REQ-ASY-011`, `REQ-ASY-070`, `REQ-ASY-079`, `REQ-ASY-080`, `REQ-ASY-082`, `REQ-ASY-142`, `AXS-ASY-023`, `AXS-ASY-044`, `AXS-ASY-050`). Verifies exact reverse declaration drop order of nested locals/parameters and deterministic lifecycle trace. |

## Requirement Traceability Matrix (`T419` Primary & `E11.4` Complete)

| Requirement ID | Summary (`spec/requirements/CATALOG.md`) | Conformance Test File(s) |
|---|---|---|
| `REQ-ASY-010` | Await does not imply thread migration (`AASYNC-26`). | `async_lifecycle_trace_stack.ax` |
| `REQ-ASY-011` | Future state owns live values across suspension (`AASYNC-27`). | `async_generic_custom_future.ax`, `async_cancellation_drop_order.ax`, `qa_async_nested_result_cancel_trace.ax` |
| `REQ-ASY-064` | Rule `AASYNC-20`: `async` must be a control-flow abstraction rather than an OS thread or runtime model. | `async_control_flow.ax`, `async_lifecycle_trace_stack.ax` |
| `REQ-ASY-065` | Rule `AASYNC-21`: `await` must serve as a suspension and resumption boundary without creating a new execution context. | `async_control_flow.ax`, `async_ui_await_outside_async.ax` |
| `REQ-ASY-070` | Rule `AASYNC-26`: Owned values may cross suspension boundaries via internal ownership transfer into Future state. | `async_control_flow.ax`, `async_try_operator.ax`, `async_generic_custom_future.ax`, `async_ui_view_across_await.ax`, `async_ui_mut_view_across_await.ax`, `async_ui_guard_across_await.ax`, `qa_async_nested_result_cancel_trace.ax` |
| `REQ-ASY-075` | Rule `AASYNC-31`: A Future passed to `spawn` may require `Send` conformance depending on the multi-threaded execution model. | `async_ui_send_bounds.ax` |
| `REQ-ASY-077` | Rule `AASYNC-33`: A Future must not implicitly implement `Share`. | `async_ui_not_share.ax` |
| `REQ-ASY-078` | Rule `AASYNC-34`: Async recursion must require a finite runtime representation. | `async_ui_recursive_future.ax` |
| `REQ-ASY-079` | Rule `AASYNC-35`: Async state lowering must preserve language ownership semantics across all state transitions. | `async_control_flow.ax`, `async_try_operator.ax`, `async_generic_custom_future.ax`, `async_cancellation_drop_order.ax`, `qa_async_nested_result_cancel_trace.ax` |
| `REQ-ASY-080` | Rule `AASYNC-36`: Async lowering must preserve deterministic Drop semantics for all state fields. | `async_try_operator.ax`, `async_cancellation_drop_order.ax`, `async_ui_await_in_drop.ax`, `qa_async_nested_result_cancel_trace.ax` |
| `REQ-ASY-081` | Rule `AASYNC-37`: Async lowering must preserve panic semantics according to active runtime profile. | `async_poll_completed_panic.ax`, `async_poll_cancelled_panic.ax` |
| `REQ-ASY-082` | Rule `AASYNC-38`: Async lowering must preserve synchronization semantics across suspension boundaries. | `async_lifecycle_trace_stack.ax`, `qa_async_nested_result_cancel_trace.ax` |
| `REQ-ASY-083` | Rule `AASYNC-39`: Async optimization must not alter observable suspension behavior where observable. | `async_lifecycle_trace_stack.ax` |
| `REQ-ASY-133` | Async is not thread. | `async_lifecycle_trace_stack.ax` |
| `REQ-ASY-134` | Rule `AASYNC-46`: GPU async lifetime must be explicit. | `async_explicit_gpu_lifetime.ax` |
| `REQ-ASY-142` | Await expressions MUST preserve Future semantics (`ATHIR-39`). | `async_control_flow.ax`, `async_try_operator.ax`, `async_generic_custom_future.ax`, `async_ui_not_a_future.ax`, `async_ui_view_across_await.ax`, `async_ui_mut_view_across_await.ax`, `async_ui_guard_across_await.ax`, `async_ui_await_outside_async.ax`, `async_ui_await_in_drop.ax`, `qa_async_nested_result_cancel_trace.ax` |

## `SPEC-33` Rule Traceability Matrix (`AXS-ASY-*`)

| Spec Rule | Summary | Tested In |
|---|---|---|
| `AXS-ASY-001`..`002` | Compile-time control-flow abstraction, zero mandatory runtime, separation of `Future`, `Thread`, `Task`. | `async_control_flow.ax`, `async_lifecycle_trace_stack.ax` |
| `AXS-ASY-008` | Explicit device/GPU asynchronous buffer lifetime contracts. | `async_explicit_gpu_lifetime.ax` |
| `AXS-ASY-010`..`014` | Core async lang items: `Poll<T>`, `Waker`, `Context`, `Future`, and `block_on` stack driver. | `async_generic_custom_future.ax`, `async_lifecycle_trace_stack.ax`, `async_cancellation_drop_order.ax` |
| `AXS-ASY-020`..`022` | Surface syntax, HIR lowering, type checking, and context validation of `async fn` and `.await`. | `async_control_flow.ax`, `async_ui_not_a_future.ax`, `async_ui_await_outside_async.ax`, `async_ui_await_in_drop.ax` |
| `AXS-ASY-023` | Desugaring of try operator `?` across `.await`. | `async_try_operator.ax` |
| `AXS-ASY-025` | Rejection of unboxed recursive `async fn` cycles (`AX_ASYNC_RECURSIVE_FUTURE`). | `async_ui_recursive_future.ax` |
| `AXS-ASY-033` | Owned values crossing `.await` via internal ownership transfer into state machine. | `async_control_flow.ax`, `async_try_operator.ax`, `async_generic_custom_future.ax` |
| `AXS-ASY-034` | Rejection of `view<T>` and `mut_view<T>` held across `.await` (`AX_ASYNC_VIEW_ACROSS_AWAIT`). | `async_ui_view_across_await.ax`, `async_ui_mut_view_across_await.ax` |
| `AXS-ASY-035` | Rejection of synchronous lock guards across `.await` (`AX_ASYNC_GUARD_ACROSS_AWAIT`). | `async_ui_guard_across_await.ax` |
| `AXS-ASY-036` | `Future: Send` derived strictly from parameters and live-across-await locals (`AX_ASYNC_FUTURE_NOT_SEND`). | `async_ui_send_bounds.ax` |
| `AXS-ASY-037` | `Future: !Share` by default (`AX_CONC_NOT_SHARE`). | `async_ui_not_share.ax` |
| `AXS-ASY-043` | State-machine lowering, `SwitchInt` dispatch, and terminal state transition invariants. | `async_control_flow.ax`, `async_poll_completed_panic.ax`, `async_poll_cancelled_panic.ax` |
| `AXS-ASY-044` | Per-state cancellation `Drop` glue: sub-future first, then live locals in reverse declaration order. | `async_cancellation_drop_order.ax`, `async_try_operator.ax` |
| `AXS-ASY-046` | Optimizer barrier and synchronization preservation across `.await`. | `async_lifecycle_trace_stack.ax` |
| `AXS-ASY-050` | Deterministic lifecycle trace verification (`POLL`, `SUSPEND`, `WAKE`, `RESUME`, `COMPLETE`, `CANCEL_DROP`). | `async_lifecycle_trace_stack.ax`, `async_cancellation_drop_order.ax` |
| `AXS-ASY-052` | Canonical `AX_ASYNC_*` diagnostic taxonomy. | All `async_ui_*.ax` tests |
