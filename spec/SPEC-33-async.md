# SPEC-33 — Async/Await, `Future<T>`, Live-Across-Await Analysis & Coroutine State-Machine Lowering

## Tóm tắt

Đặc tả chính tắc (`SPEC-33`) cho mô hình bất đồng bộ (`async fn`, `async { }`, `.await`), giao diện `Future<T>` / `Poll<T>` / `Waker` / `Context` (`std.future`), phân tích biến sống qua điểm tạm dừng (`live-across-await analysis`), phép hạ bậc máy trạng thái hữu hạn trên MIR (`compiler/mir/async_lower.ax`), cơ chế hủy bỏ tất định qua `Drop` (`cancellation drop glue`), và truy vết vòng đời `Future` trên trình thông dịch `oracle` cho `E11.4`. Tài liệu này hợp nhất các quy tắc từ `docs/base/specs/0093`, `0127`, `0135`, `0159`, `0161`, `0201`, `0202`, `0248` và các đặc tả tác vụ `0275`, `0297`, `0619`, nối tiếp `SPEC-30` (`E11.1`), `SPEC-31` (`E11.2`), `SPEC-32` (`E11.3`) và hợp đồng mở rộng lõi `SPEC-04` (`AXS-EXT-020`, `AXS-EXT-023`, `AXS-EXT-031`, `AXS-EXT-033`, `AXS-EXT-040`, `AXS-EXT-044`).
Các quyết định cốt lõi:
- **`async/await` là phép biến đổi luồng điều khiển và lưu trữ ở thời điểm biên dịch, không phải mô hình runtime bắt buộc (`0093`, `0127`, `0135`, `0202`)**: Gọi `async fn` chỉ tạo một giá trị máy trạng thái `Future<Output = T>` (không tự tạo luồng OS, không tự `spawn` tác vụ, không bắt buộc cấp phát heap, không cần `Pin<T>` trong lõi ngôn ngữ v1.0, và không kéo theo bộ lập lịch toàn cục). Các `Future` không thoát khỏi phạm vi cục bộ có thể được cấp phát hoàn toàn trên ngăn xếp (stack) và chạy đến khi hoàn tất qua `std.future.block_on` với chi phí cấp phát heap bằng `0`.
- **Phân tích `live-across-await` chính xác (`0127 §9–20`, `tasks/0619`)**: Chỉ các biến có vùng sống thực sự đi qua biên tạm dừng `.await` (`SuspensionPointId`) mới được lưu vào khung trạng thái của `Future`; các biến chết trước `.await` được giải phóng (`Drop`) ngay trước khi tạm dừng. Trong v1.0, mọi năng lực mượn (`view<T>`, `mut_view<T>`), view vào `@thread_local`, và các khóa đồng bộ (`MutexGuard<T>`, `RwLockReadGuard<T>`, `RwLockWriteGuard<T>`) đều bị từ chối tĩnh nếu sống qua `.await` (`AX_ASYNC_VIEW_ACROSS_AWAIT`, `AX_ASYNC_GUARD_ACROSS_AWAIT`). Tính chất `Future: Send` chỉ phụ thuộc vào tham số hàm và tập biến sống qua `.await` (biến `!Send` đã hủy trước `.await` không làm `Future` mất tính chất `Send`), và mọi `Future` do trình biên dịch sinh ra đều là `!Share`.
- **Hạ bậc máy trạng thái MIR và hủy bỏ tất định (`0161 §29`, `0248`, `tasks/0619`)**: Trước pha kiểm chứng MIR và tối ưu hóa, `compiler/mir/async_lower.ax` biến đổi thân hàm `Coroutine` chứa các terminator `Suspend` thành kiểu cấu trúc trạng thái tường minh (`state_tag: u32` cùng các trường sống qua `.await`), sinh hàm `Future.poll` nhảy theo `SwitchInt(state_tag)` và sinh mã dọn dẹp `Drop` theo từng trạng thái để khi một `Future` đang `Pending` bị hủy bỏ, đúng các tài nguyên đang sở hữu ở trạng thái đó được gọi `Drop` theo thứ tự ngược khai báo mà không rò rỉ hay hủy kép.

Status: draft (T415, 2026-11-03)
Owner: axiom-architect
Consolidates: `docs/base/specs/0093 - Axiom — Async  Coroutine Model v0.1.md`, `docs/base/specs/0127 - AXIOM LANGUAGE SPECIFICATION v0.1 — Part VI.md`, `docs/base/specs/0135 - AXIOM LANGUAGE SPECIFICATION v0.1.md` (Part XVI–XVII), `docs/base/specs/0159 - AXIOM TYPED HIR + EXPRESSION SEMANTICS v0.1.md` (§§52–59), `docs/base/specs/0161 - AXIOM MIR v0.1.md` (§29), `docs/base/specs/0201 - 2. Async Task mới là nơi cần cực kỳ nhỏ.md`, `docs/base/specs/0202 - ASYNC-TASK-001 — Axiom TaskFutureScheduler Model.md`, `docs/base/specs/0248 - COMPILER-006 — CLOSURE + ASYNC LOWERING.md`, `docs/base/tasks/0275 - BOOTSTRAP-017 — ASYNC  FUTURE.md`, `docs/base/tasks/0297 - BOOTSTRAP-038 — Async  Future  Await  Cancellation Audit & Freeze.md`, `docs/base/tasks/0619 - BOOTSTRAP-360 — Axiom AsyncAwait Lowering & Coroutine State Machine Engine.md`
Covers: `REQ-CONC-020`, `REQ-CONC-024`, `REQ-CONC-096`, `REQ-ASY-022`, `REQ-ASY-024`, `REQ-ASY-026`, `REQ-ASY-033`, `REQ-ASY-039`, `REQ-ASY-045`, `REQ-ASY-055`, `REQ-ASY-085`, `REQ-ASY-092`, `REQ-ASY-100`, `REQ-ASY-103`, `REQ-ASY-104`, `REQ-ASY-105`, `REQ-ASY-116`, `REQ-ASY-119`, `REQ-ASY-120`, `REQ-ASY-122`, `REQ-ASY-124`, `REQ-ASY-125`, `REQ-ASY-126`, `REQ-ASY-127`, `REQ-ASY-137`, `REQ-ASY-138`, `REQ-ASY-144`, `REQ-ASY-145`, `REQ-ASY-146`, `REQ-ASY-147`, `REQ-CONC-146`, `REQ-CONC-191`, `REQ-CONC-217`
Consumers: `T416` (frontend & typeck for `async fn`, `.await`, `std.future`), `T417` (live-across-await analysis, view/guard rejection, `Future: Send`), `T088` (MIR state-machine lowering, per-state `Drop` glue, `std.future.block_on`), `T418` (oracle async lifecycle trace & `inspect --emit=async-layout`), `T419` (`E11.4` conformance suite), `E11.5` (`T420`–`T424`), `E11.6` (`T425`–`T428`)

---

## 1. Architectural Foundations: Control-Flow Abstraction & Zero-Mandatory-Runtime Model

**AXS-ASY-001** (Async as a compile-time control-flow and storage transformation; `REQ-ASY-064`, `REQ-ASY-099`, `REQ-ASY-100`, `REQ-ASY-137`, `REQ-ASY-138`, `REQ-ASY-144`, `0093 §1–3`, `0127 §1–5, §64 AASYNC-20..24`, `0135 §1–7, §66 AASYNC-20`, `tasks/0275 §1–5`, `tasks/0297 §1–8, §80`, `tasks/0619 §1–3`).
1. In Axiom, `async` and `.await` are a **compile-time control-flow and storage transformation**, not a runtime object model or an operating-system scheduling primitive (`REQ-ASY-064`, `REQ-ASY-099`, `REQ-ASY-144`).
2. Writing or calling an `async fn` does **not** mandate heap allocation, a garbage collector, reference counting, virtual dispatch tables (`vtable`), hidden object headers, OS thread creation, or a global runtime scheduler (`REQ-ASY-100`, `REQ-ASY-137`, `REQ-ASY-138`).
3. The compiler provides sufficient static semantics to verify ownership, capabilities, `Drop` cleanup, and thread-migration safety (`Send`/`Share`) across suspension points, while leaving task scheduling, thread pools, and I/O event loops to modular, link-on-demand library executors (`REQ-ASY-138`, `SPEC-30 AXS-CONC-005`).

**AXS-ASY-002** (Strict separation of `ExecutionContext`, `Thread`, `Fiber`, `Task`, `Future`, and `Executor`; `REQ-CONC-020`, `REQ-CONC-024`, `REQ-CONC-146`, `REQ-ASY-010`, `REQ-ASY-038`, `REQ-ASY-039`, `REQ-ASY-065`, `REQ-ASY-096`, `REQ-ASY-133`, `REQ-ASY-145`, `REQ-ASY-146`, `0126 §1, §4`, `0127 §1, §29–30`, `0201 §1–9`, `0202 §1`, `tasks/0275 §1–3`, `tasks/0297 §1–3, §19, §74`).
The compiler and standard library strictly distinguish six concepts (`REQ-CONC-020`, `REQ-CONC-024`, `REQ-CONC-146`, `REQ-ASY-133`):

| Concept | Semantic Role | Created / Invoked By |
|---|---|---|
| `ExecutionContext` | Abstract locus of sequential execution, local stack frames, and capability environment (`SPEC-30 AXS-CONC-003`). | Any active `Thread`, `Task`, `Fiber`, or `GPUKernel` |
| `Thread` (`std.thread.Thread`) | Preemptively scheduled OS kernel thread with a dedicated OS stack and `@thread_local` storage (`SPEC-32`). | `std.thread.spawn`, `Scope.spawn` |
| `Fiber` (`std.fiber.Fiber`) | User-space stackful coroutine with explicit contiguous stack storage (`SPEC-34`). | `Fiber.new` / `Fiber.resume` |
| `Task` (`std.async.Task`) | Schedulable unit of asynchronous execution binding a `Future` to executor scheduling, wake, join, and cancellation metadata (`SPEC-34`). | `Executor.spawn`, `LocalExecutor.spawn_local`, `TaskGroup.spawn` |
| `Future<T>` (`std.future.Future`) | Passive, stackless state-machine value representing a computation that may suspend and resume (`E11.4`). | Calling an `async fn` or evaluating an `async { }` block |
| `Executor` | Library-level scheduler that polls runnable `Task`s and processes `Waker` notifications (`SPEC-34`). | `block_on`, `LocalExecutor.run`, `Executor.run` |

From this separation, three hard invariants follow:
1. **Calling an `async fn` does not create a thread or spawn a task (`REQ-ASY-096`, `REQ-ASY-145`, `REQ-ASY-146`)**: Evaluating `let fut = compute(x)` merely constructs and returns the passive `Future` state-machine value `fut`.
2. **`.await` does not spawn a task or create an execution context (`REQ-ASY-010`, `REQ-ASY-038`, `REQ-ASY-065`)**: Evaluating `fut.await` polls `fut` in place within the caller's current execution context and suspends/resumes the caller if `fut` returns `Poll.Pending`. Sequential awaits (`a().await; b().await`) execute strictly sequentially (`0135 §12`, `tasks/0297 §20`).
3. **Concurrent task execution requires explicit `spawn` (`REQ-ASY-039`)**: Only an explicit scheduling call (`spawn`, `spawn_local`, or a multi-future combinator such as `join`) introduces concurrent asynchronous execution (`0127 §30`, `tasks/0297 §21`).

**AXS-ASY-003** (Unified ownership, capability, and concurrency model across sync, thread, async, and GPU domains; `REQ-CONC-096`, `REQ-CONC-191`, `REQ-CONC-217`, `REQ-ASY-092`, `0126 §80`, `0131 §61`, `tasks/0488 §130`).
1. Axiom maintains a **single unified ownership and capability model** across synchronous functions, OS threads, async state machines, and GPU invocations (`REQ-CONC-096`, `REQ-CONC-217`).
2. Every `Future<T>` is a first-class value governed by standard single-owner move semantics (`SPEC-10`), capability projections (`SPEC-11`), deterministic `Drop` (`SPEC-12`), and `Send` / `Share` marker auto-traits (`SPEC-30`), without hidden garbage-collected objects or implicit reference-counted wrappers (`REQ-ASY-092`).
3. Every state transition and value crossing an `.await` boundary is verified for initialization, ownership transfer, capability lifetime containment, storage stability, and cross-thread migration safety (`REQ-CONC-191`).

**AXS-ASY-004** (Storage independence & zero mandatory heap allocation; `REQ-ASY-016`, `REQ-ASY-021`, `REQ-ASY-046`, `REQ-ASY-066`, `REQ-ASY-100`, `0093 §2–3, §14`, `0127 §4, §40–41`, `0135 §5–7`, `0201 §2–7 AASYNC-51..55`, `0202 §2, §13–16`).
1. `Future<T>` defines a semantic computation state machine, never a mandatory heap allocation (`REQ-ASY-016`, `REQ-ASY-066`, `REQ-ASY-100`).
2. Depending on caller usage and escape analysis (`SPEC-71`), a `Future` value may reside in CPU registers, a caller's stack frame, an inline struct field of a parent `Future`, caller-provided static/stack `TaskStorage`, an arena/slab pool, or a `Box<F>` heap allocation (`REQ-ASY-021`).
3. A `Future` that does not escape its lexical scope (such as `let x = work().await` or `block_on(work())`) MUST be eligible for direct stack/inline placement and complete heap-allocation elimination (`REQ-ASY-046`).

**AXS-ASY-005** (No `Pin<T>` in Core v1.0 & explicit stable-address storage contracts; `REQ-ASY-047`, `REQ-ASY-119`, `REQ-ASY-120`, `REQ-ASY-121`, `REQ-ASY-122`, `0127 §42–43`, `0135 §47–50, §66 AASYNC-43..44`, `0202 §3`, `0248 §26`, `tasks/0275 §21`).
1. **No `Pin<T>` in Core v1.0 (`REQ-ASY-047`, `REQ-ASY-121`)**: Axiom does not introduce `Pin<T>` or `Unpin` into the core type system. Because v1.0 forbids holding `view<T>` or `mut_view<T>` capabilities across `.await` suspension boundaries (`AXS-ASY-034`), compiler-generated state machines contain no raw self-referential pointers across states and remain safely relocatable by value move (`Move`) between polls unless an explicit address-observability contract is active.
2. **No implicit semantic lifetime extension (`REQ-ASY-119`)**: The compiler never silently extends the semantic ownership or capability lifetime of a borrowed local variable to satisfy an async suspension; while the optimizer may adjust physical stack/frame slot lifetimes, semantic owner and capability rules are enforced strictly (`0135 §47`).
3. **Explicit stable-address contract (`REQ-ASY-120`, `REQ-ASY-122`)**: When an asynchronous operation (such as an OS I/O completion port buffer, DMA transfer, or raw pointer derived via `address_of` / `address_of_mut`) requires a stable physical memory address across suspension, that requirement is represented as an explicit storage contract (`Box<T>`, `StableStorage<T>`, or reactor-owned buffer transfer in `SPEC-35`) (`REQ-ASY-120`). Once a storage location's address is observable (`address_observable == true`, `SPEC-71 AXS-ESC-004`), the compiler and optimizer MUST NOT relocate or promote that storage across `.await` in a way that violates address stability (`REQ-ASY-122`).

**AXS-ASY-006** (Creation of a `Future` vs starting an external operation; `REQ-ASY-103`, `REQ-ASY-104`, `REQ-ASY-105`, `0135 §13`, `tasks/0297 §2`).
1. Constructing a `Future` value is semantically distinct from starting an external asynchronous operation (`REQ-ASY-103`).
2. **Compiler-synthesized `async fn` futures are cold (lazy)**: Calling an `async fn` captures its arguments into the initial state (`state_tag = 0`) and executes **zero** statements of the function body until the returned `Future` is first polled (`REQ-ASY-020`, `REQ-ASY-147`).
3. **Library-defined `Future` types may be lazy or eager (`REQ-ASY-104`, `REQ-ASY-105`)**: Axiom does not force every custom library `Future` type to be strictly cold or strictly eager (for example, an I/O or timer handle may initiate registration on creation or on first `poll`), provided each library API explicitly documents its initiation, polling, and cancellation contract (`REQ-ASY-105`).

**AXS-ASY-007** (Suspension-free `async fn` optimization & public type contract preservation; `REQ-ASY-022`, `REQ-ASY-023`, `REQ-ASY-083`, `0093 §3`, `0127 §5–6, §64 AASYNC-39`).
1. **Public semantic type consistency (`REQ-ASY-023`)**: Even if the body of `async fn foo() -> T` contains zero `.await` expressions, its surface and HIR/THIR type contract remains an asynchronous function returning `Future<Output = T>`. The compiler MUST NOT alter the observable type signature of `foo`.
2. **Unobservable state-machine erasure (`REQ-ASY-022`, `REQ-ASY-083`)**: When `foo()` is awaited or inlined at a call site (`SPEC-73`) and the compiler proves that `foo` never suspends (or its `Future` object identity is never observed independently), the optimizer may collapse the `Future` state machine into direct synchronous evaluation, provided observable ordering, side effects, panics, and trace events (when tracing is enabled) are preserved (`REQ-ASY-083`).

**AXS-ASY-008** (Explicit GPU and heterogeneous device async lifetime contracts; `REQ-ASY-124`, `REQ-ASY-125`, `REQ-ASY-126`, `REQ-ASY-134`, `0135 §53–54, §66 AASYNC-46`, `tasks/0297 §50`).
1. When an asynchronous computation launches a GPU kernel or asynchronous device DMA transfer (`E22`), the resulting waitable handle (`GpuEvent` or `DeviceFuture<T>`) MUST explicitly track ownership or capability dependencies on all participating `DeviceBuffer<T>` and host-pinned buffers (`REQ-ASY-124`, `REQ-ASY-134`).
2. The compiler MUST NOT guess or infer hidden asynchronous GPU lifetimes (`REQ-ASY-125`).
3. The ownership and type contract of device futures MUST statically prevent dropping, freeing, or mutating a `DeviceBuffer` on the host while an in-flight device operation still references it (`REQ-ASY-126`).

---

## 2. Core Async Lang Items: `Poll<T>`, `Waker`, `Context` & `Future` (`std.future`)

**AXS-ASY-010** (`Poll<T>` lang-item enum in `std/future/mod.ax`; `T416`, `0093 §11`, `0127 §3`, `0202 §4`, `tasks/0275 §10`, `tasks/0297 §12`, `tasks/0619 §9`).
The outcome of polling a `Future` is represented by the compiler-known enum `Poll<T>` in module `std.future` (`std/future/mod.ax`):

```axiom
module std.future

@lang("poll")
pub enum Poll<T> {
    Ready(T),
    Pending,
}
```

1. **Discriminants (`SPEC-04 AXS-EXT-021`)**: `Poll.Ready(T)` has implicit discriminant `0` and payload `T`; `Poll.Pending` has implicit discriminant `1` and no payload.
2. **Helper methods on `Poll<T>`**:
   - `pub fn is_ready(self: view<Poll<T>>) -> bool` — returns `true` iff `self` is `Poll.Ready(_)`.
   - `pub fn is_pending(self: view<Poll<T>>) -> bool` — returns `true` iff `self` is `Poll.Pending`.
3. **Marker traits**: `Poll<T>: Send` iff `T: Send`; `Poll<T>: Share` iff `T: Share`; `Poll<T>: Copy` iff `T: Copy`.

**AXS-ASY-011** (`RawWaker`, `RawWakerVTable`, and `Waker` lang item in `std/future/mod.ax`; `T416`, `0093 §21–22`, `0127 §27–28`, `0202 §5`, `tasks/0275 §11`, `tasks/0297 §13–16, §72`, `tasks/0619 §10`).
To decouple compiler-generated state machines from concrete executor implementations (`LocalExecutor`, work-stealing `Executor`, custom embedded loops, or `block_on`), wakeup notifications use an executor-supplied two-word `Waker` handle in `std/future/mod.ax`:

```axiom
pub struct RawWakerVTable {
    pub clone: fn(*const u8) -> RawWaker,
    pub wake: fn(*const u8),
    pub wake_by_ref: fn(*const u8),
    pub drop: fn(*const u8),
}

pub struct RawWaker {
    pub data: *const u8,
    pub vtable: *const RawWakerVTable,
}

@lang("waker")
pub struct Waker {
    raw: RawWaker,
}
```

1. **Size and representation**: `Waker` is exactly two machine words (`16` bytes, alignment `8` on x86-64) with zero mandatory heap allocation (`0202 §5`). A stack-local, pool-indexed, or static waker sets `data` to a task/thread pointer or integer index cast to `*const u8` and `vtable` to a static `RawWakerVTable`.
2. **Methods on `Waker`**:
   - `pub unsafe fn from_raw(raw: RawWaker) -> Waker` — constructs a `Waker` from a `RawWaker` whose `vtable` functions uphold thread-safety and lifetime invariants.
   - `pub fn noop() -> Waker` — returns a zero-allocation no-op `Waker` whose `clone`, `wake`, `wake_by_ref`, and `drop` entries do nothing (`data = null`).
   - `pub fn wake(self: Waker)` — consumes `self` and invokes `(self.raw.vtable.wake)(self.raw.data)` without running `Drop` a second time.
   - `pub fn wake_by_ref(self: view<Waker>)` — invokes `(self.raw.vtable.wake_by_ref)(self.raw.data)` without consuming `self`.
   - `pub fn will_wake(self: view<Waker>, other: view<Waker>) -> bool` — returns `true` iff `self.raw.data == other.raw.data && self.raw.vtable == other.raw.vtable`.
   - `impl Clone for Waker` invokes `(self.raw.vtable.clone)(self.raw.data)`; `impl Drop for Waker` invokes `(self.raw.vtable.drop)(self.raw.data)`.
3. **Scheduling semantics (`0127 §28`, `tasks/0275 §11`, `tasks/0297 §14–16, §72`)**:
   - Calling `wake()` or `wake_by_ref()` signals that the associated task is ready to be polled again; it does **not** spawn an OS thread and does **not** synchronously poll the `Future` inside `wake()` unless the executor's documented policy does so (`tasks/0297 §14`).
   - `wake()` and `wake_by_ref()` MUST be idempotent: multiple wake calls before the next `poll` transition the target task to `READY` at most once (recording a sticky wake permit if the task is currently `RUNNING` so no wakeup is lost, `tasks/0297 §15–16`).
   - `Waker` is `unsafe impl Send for Waker` and `unsafe impl Share for Waker`; it carries wakeup capability only, never ownership of or mutable access to the `Future` state (`tasks/0297 §72`).

**AXS-ASY-012** (`Context` polling context in `std/future/mod.ax`; `T416`, `0093 §11`, `0202 §4–5`).
`Context` wraps a borrowed `view<Waker>` for the duration of a single `Future.poll` invocation:

```axiom
@lang("context")
pub struct Context {
    waker_ref: view<Waker>,
}

impl Context {
    pub fn from_waker(waker: view<Waker>) -> Context {
        Context { waker_ref: waker }
    }

    pub fn waker(self: view<Context>) -> view<Waker> {
        self.waker_ref
    }
}
```

Because `Context` holds a `view<Waker>`, it is confined to the synchronous call stack of `poll` and cannot be stored across `.await` (`AXS-ASY-034`); a leaf `Future` that suspends clones the `Waker` (`cx.waker().clone()`) into its waiter registration slot before returning `Poll.Pending`.

**AXS-ASY-013** (`Future` lang-item trait & exclusive polling invariant; `T416`, `REQ-ASY-043`, `REQ-ASY-101`, `REQ-ASY-150`, `SPEC-04 AXS-EXT-023`, `0093 §11, §20`, `0127 §3, §37`, `0135 §8`).
The `Future` trait is declared in `std/future/mod.ax` as a compiler-known `@lang("future")` trait:

```axiom
@lang("future")
pub trait Future {
    type Output
    fn poll(self: mut_view<Self>, cx: mut_view<Context>) -> Poll<Self.Output>
}
```

1. **Exclusive `mut_view<Self>` receiver (`REQ-ASY-043`, `REQ-ASY-150`, `0093 §20`, `0127 §37`)**: `Future.poll` requires an exclusive mutable capability `self: mut_view<Self>` and `cx: mut_view<Context>`. The capability checker (`SPEC-11`, `SPEC-30`) statically forbids two execution contexts from polling the same `Future` concurrently.
2. **Surface ergonomics (`REQ-ASY-101`)**: `poll` is the compiler/executor boundary protocol, not mandatory surface syntax for ordinary application code; users write `async fn` and `.await`, while executors and low-level leaf primitives invoke or implement `Future.poll`.
3. **Completion finality (`T418`, `tasks/0619 §31–32`)**: Once `fut.poll(cx)` returns `Poll.Ready(val)` (or unwinds/panics), the `Future` has reached its terminal state (`COMPLETED` or `PANICKED`). Polling a `Future` again after it has returned `Poll.Ready` is a contract violation that deterministically panics (`AXS-ASY-043`, `AXS-ASY-051`).

**AXS-ASY-014** (Executor-free stack poll driver `std.future.block_on`; `T088`, `REQ-ASY-016`, `REQ-ASY-021`, `REQ-ASY-036`, `0093 §10`, `0127 §25–26`, `tasks/0297 §54`).
Module `std.future` (`std/future/block_on.ax`, re-exported from `std/future/mod.ax`) provides a minimal, single-future synchronous driver `block_on`:

```axiom
pub fn block_on<F: Future>(mut fut: F) -> F.Output
```

1. **Zero-heap stack execution**: `block_on` places `fut` directly in its stack frame, constructs a stack-allocated `Waker` backed by an atomic park state (`Atomic<u32>` + `host.futex_wait` / `host.futex_wake`, or `Waker.noop()` for immediate/yield polling), constructs `let mut cx = Context.from_waker(view(waker))`, and loops calling `fut.poll(mut_view(cx))`:
   - If `Poll.Ready(output)` is returned, `block_on` drops `waker`, drops `fut` (whose `state_tag` is now `COMPLETED`, making its `Drop` glue a no-op), and returns `output`.
   - If `Poll.Pending` is returned, `block_on` waits if not yet woken (or yields in cooperative single-threaded tests) and re-polls until `Poll.Ready(output)`.
2. **No mandatory scheduler dependency**: Programs using `async fn`, `.await`, and `block_on` do not link `std.async`'s multi-task work-stealing `Executor` or I/O reactor unless explicitly imported (`REQ-ASY-016`, `tasks/0297 §53–55`).

**AXS-ASY-015** (Prelude exports in `std/core/prelude.ax`; `T416`).
`std/core/prelude.ax` re-exports `std.future.Future` and `std.future.Poll` (including `Poll.Ready` and `Poll.Pending`) so all Axiom modules can name `Future` and `Poll<T>` without explicit `use` declarations.

---

## 3. Surface Syntax, Type Checking & Trait Lowering of `async fn`, `async { }` & `.await`

**AXS-ASY-020** (Surface grammar and HIR lowering of `async fn`, `async { }`, and `.await`; `T416`, `SPEC-02 AXS-GRM-003`, `SPEC-04 AXS-EXT-031, AXS-EXT-033`).
In the self-hosted compiler `axiomc` (`compiler/syntax/parse.ax`, `compiler/hir/lower.ax`):
1. **`async fn` items and methods (`AXS-EXT-031`)**: The `async` function modifier is accepted on free functions (`pub async fn f(...) -> T { ... }`), inherent `impl` methods, and `trait` / trait-`impl` methods (`async` precedes `fn`, or `pub async unsafe fn` when combined with `unsafe`). HIR lowering sets `hir_fn.is_async = true` rather than emitting `AX_PARSE_UNSUPPORTED_IN_BOOTSTRAP`.
2. **`async` and `async move` blocks (`AXS-EXT-033`)**: `async { stmts }` and `async move { stmts }` parse as `AstExprKind.AsyncBlock { is_move: bool, body: Block }` and lower to `HirExprKind.AsyncBlock` (equivalent to an immediately invoked anonymous `async` closure taking zero arguments).
3. **Postfix `.await` expressions (`AXS-EXT-033`)**: `expr.await` parses as a postfix operator at the same precedence tier as field access (`.field`), method calls (`.m()`), indexing (`[i]`), and `?` (`SPEC-02`), chaining naturally Left-to-Right (e.g., `client.fetch(id).await?.parse().await?`). HIR lowering produces `HirExprKind.Await(operand)`.

**AXS-ASY-021** (Anonymous `Coroutine` / `Future` type synthesis for `async fn` and `async` blocks; `T416`, `REQ-ASY-020`, `REQ-ASY-027`, `REQ-ASY-056`, `REQ-ASY-088`, `REQ-ASY-136`, `REQ-ASY-141`, `REQ-ASY-147`, `REQ-ASY-148`, `SPEC-04 AXS-EXT-020`, `0127 §2, §13, §54`, `0159 §59`, `0248 §16–18`).
1. **Return type transformation (`REQ-ASY-088`, `REQ-ASY-141`, `REQ-ASY-147`, `REQ-ASY-148`)**: For a function declared as `async fn f<G...>(p_1: T_1, ..., p_n: T_n) -> Ret`, its callable signature returns a distinct, anonymous compiler-generated state-machine type `TypeKind.Coroutine { def_id: CoroutineId, substs: G..., output_ty: Ret }` (`SPEC-04 AXS-EXT-020`). If `-> Ret` is omitted, `Ret` defaults to `()` (`Unit`).
2. **Automatic `Future` trait satisfaction (`REQ-ASY-056`, `REQ-ASY-141`)**: Every `TypeKind.Coroutine { output_ty: Ret, .. }` automatically satisfies the trait bound `Future<Output = Ret>` in the trait solver (`compiler/traits/solver.ax`) without introducing auxiliary effect wrapper types (`Async<T>`, `Awaitable<T>`, etc., `REQ-ASY-056`).
3. **Body return checking**: Inside the body of `async fn f(...) -> Ret`, `return expr` and the trailing tail expression of the body are type-checked against `Ret` (not against `Future<Output = Ret>`).
4. **No explicit lifetime syntax (`REQ-ASY-027`, `REQ-ASY-136`)**: Axiom has no `Future<'a>` or `async fn f<'a>` lifetime annotations; the compiler tracks provenance and capability regions automatically (`0127 §13`, `0135 §Quyết định quan trọng`).

**AXS-ASY-022** (Type checking and context validation of `expr.await`; `T416`, `REQ-ASY-115`, `REQ-ASY-116`, `REQ-ASY-139`, `REQ-ASY-142`, `0135 §38`, `0159 §52, §66 ATHIR-39`, `tasks/0619 §11`).
When type-checking `expr.await` (`compiler/types/typeck.ax`):
1. **Enclosing async context check**: `expr.await` MUST occur inside the body of an `async fn` or `async { }` block (and MUST NOT cross the boundary of a nested synchronous closure `|...| { ... }` or local item). Using `.await` in a synchronous function or closure emits `AX_ASYNC_AWAIT_OUTSIDE_ASYNC`.
2. **Prohibition of `.await` inside `Drop.drop` (`REQ-ASY-115`, `REQ-ASY-116`, `0135 §36–38`)**: `impl Drop` (`fn drop(self: mut_view<Self>)`) is strictly synchronous and deterministic; declaring `async fn drop` or using `.await` inside `drop` is rejected with `AX_ASYNC_AWAIT_IN_DROP` so destructors never introduce hidden scheduler dependencies (`REQ-ASY-116`). Resources requiring asynchronous teardown provide an explicit `async fn close(self) -> Result<(), Error>` method before `Drop` (`0135 §37`).
3. **`Future` trait obligation (`REQ-ASY-139`, `REQ-ASY-142`)**: The operand `expr` of `expr.await` is type-checked to type `F`. The type checker verifies `F: Future` via the trait solver:
   - If `F` satisfies `Future<Output = Out>`, the type of `expr.await` is `Out` (`REQ-ASY-139`).
   - If `F` does not implement `Future`, the type checker emits `AX_ASYNC_NOT_A_FUTURE` (`data.found = F`) and assigns `TypeKind.Error` to prevent cascading diagnostics (`AXD-044`).

**AXS-ASY-023** (`?` operator lowering inside `async fn`; `T416`, `REQ-ASY-050`, `0127 §48`, `0135 §39`, `tasks/0275 §28`, `tasks/0297 §43`, `tasks/0619 §42`).
1. Inside an `async fn` declared with return type `Result<T, E>` (or `Option<T>`), the try operator `sub_expr?` (most commonly `fut.await?`) validates `typeof(sub_expr)` against the declared inner output type `Result<T, E>` (or `Option<T>`).
2. In MIR and state-machine lowering (`T088`), `let v = fut.await?` lowers to ordinary control-flow branching (`SwitchInt`):
   - First, `fut` is polled via `.await` (`Poll.Pending` suspends the outer `Future`; `Poll.Ready(res)` continues).
   - Next, `res` is branched on: `Result.Ok(v)` assigns `v` and continues execution; `Result.Err(e)` executes drop elaboration for all currently initialized locals in reverse declaration order, sets `state_tag = COMPLETED`, and returns `Poll.Ready(Result.Err(e))` from the outer `Future.poll`.
3. No exception unwinding runtime or hidden allocation is ever invoked for `?` in `async fn` (`REQ-ASY-050`).

**AXS-ASY-024** (`async fn` in traits: static monomorphization vs explicit `dyn Trait` dispatch; `T416`, `REQ-ASY-048`, `REQ-ASY-049`, `REQ-ASY-084`, `0093 §13`, `0127 §44–47, §64 AASYNC-40`, `0248 §42–43`, `tasks/0297 §45–47`, `tasks/0619 §29`).
1. **Trait declaration & impl (`REQ-ASY-048`)**: Traits and their `impl` blocks may declare `async fn` methods:
   ```axiom
   pub trait Service {
       async fn handle(self: view<Self>, req: i64) -> Result<i64, i32>
   }
   ```
   Semantically, each concrete implementation `impl Service for MyService` synthesizes its own concrete state-machine type `__Async_MyService_handle` implementing `Future<Output = Result<i64, i32>>`.
2. **Static generic dispatch by default (`REQ-ASY-048`, `REQ-ASY-084`)**: Calling `svc.handle(req).await` on a concrete type or generic parameter `S: Service` monomorphizes the call to `__Async_S_handle`, inlining the child state machine directly into the caller's state machine without heap allocation or virtual call overhead.
3. **Dynamic async dispatch (`REQ-ASY-049`, `REQ-ASY-084`)**: Static async dispatch and dynamic async dispatch (`dyn Trait`) have distinct representations and cost models (`REQ-ASY-084`). Because concrete `Future` state machines of different `impl`s have different sizes and layouts, calling an `async fn` through a type-erased `dyn Trait` requires an explicit dynamically allocated or type-erased `Future` wrapper (such as `Box<dyn Future<Output = T>>` once `E14.4` `dyn Trait` is active) and MUST NOT be assumed to be zero-allocation (`REQ-ASY-049`).

**AXS-ASY-025** (Rejection of unboxed recursive `async fn` state cycles; `T416`, `REQ-ASY-044`, `REQ-ASY-078`, `REQ-ASY-117`, `REQ-ASY-118`, `REQ-ASY-135`, `0127 §38, §64 AASYNC-34`, `0135 §43–44, §66 AASYNC-49`, `0248 §40–41`, `tasks/0275 §30`, `tasks/0619 §26`).
1. **Finite representation requirement (`REQ-ASY-078`, `REQ-ASY-118`, `REQ-ASY-135`)**: Every `Future` state machine MUST have a statically finite byte size and alignment.
2. **Cycle detection (`REQ-ASY-044`, `REQ-ASY-117`)**: If `async fn A` directly orindirectly awaits `async fn B` (including `A` awaiting `A`) without pointer/heap indirection (`Box`), then `A`'s state machine would inline `B`'s state machine as a sub-future field across `.await`, which in turn contains `A`'s state machine, creating an infinite-size type cycle:
   $$\text{sizeof}(\text{Future}_A) \ge \text{sizeof}(\text{Future}_B) + c > \text{sizeof}(\text{Future}_A)$$
3. The type checker / call-graph analyzer detects any cycle in the unboxed awaited-`Coroutine` containment graph and rejects it with diagnostic `AX_ASYNC_RECURSIVE_FUTURE` (`data.cycle = ["A", ...]`), instructing the user to break the cycle with explicit finite indirection (`Box<...>`) (`REQ-ASY-044`, `REQ-ASY-118`). The compiler never inserts hidden heap allocation to make recursive `async fn` compile implicitly (`0248 §40`).

**AXS-ASY-026** (FFI and ABI restrictions on `async fn`; `T416`, `REQ-ASY-123`, `0135 §51, §66 AASYNC-45`, `tasks/0297 §11, §48`, `tasks/0619 §40–41`).
1. Compiler-generated `Future` state machines have compiler-controlled layout (`Repr.Axiom`) and do not have a C-compatible ABI (`REQ-ASY-123`, `tasks/0297 §11`).
2. Declaring an `async fn` with an external ABI (`extern "C" async fn ...`) or inside an `extern "..." { ... }` block is rejected at compile time with `AX_ASYNC_EXTERN_ABI`.
3. Foreign C APIs that perform asynchronous work are bridged into Axiom via explicit FFI handles, completion callbacks, or OS completion ports wrapped in standard Axiom structs implementing `Future` (`0135 §51`, `tasks/0619 §40`).

**AXS-ASY-027** (`AsyncSuspend` vs `Blocking` effect tracking & diagnostics; `T416`, `REQ-ASY-055`, `REQ-VER-025`, `0127 §53`, `tasks/0297 §60`, `tasks/0487 AEFFECT-30`).
1. The semantic analyzer distinguishes cooperative asynchronous suspension (`AsyncSuspend`, introduced by `.await`) from synchronous OS-thread blocking (`Blocking`, introduced by functions annotated `@blocking` or known blocking primitives such as `std.thread.sleep`, `JoinHandle.join`, and blocking `Mutex.lock` when called directly in an async body where `AsyncMutex` is expected) (`REQ-VER-025`).
2. Invoking a `@blocking`-marked synchronous operation directly inside an `async fn` or `async` block emits diagnostic `AX_ASYNC_BLOCKING_IN_ASYNC` (`REQ-ASY-055`), advising the caller to use the corresponding non-blocking async API or offload blocking work via `spawn_blocking`.

---

## 4. Live-Across-Await Dataflow Analysis, Capability Prohibition & `Future: Send` / `!Share`

**AXS-ASY-030** (Suspension boundaries and `SuspensionPointId` representation in MIR; `T417`, `REQ-ASY-032`, `REQ-ASY-160`, `SPEC-04 AXS-EXT-040, AXS-EXT-044`, `0127 §19`, `0161 §29`, `0248 §21`, `tasks/0297 §9`, `tasks/0478 §34 ASEM-44`, `tasks/0619 §5`).
1. During initial MIR construction (`compiler/mir/builder.ax`), an `async fn` or `async` block is built as a MIR body with `BodyKind.Coroutine` (`SPEC-04 AXS-EXT-040`).
2. Each `fut_expr.await` expression is assigned a deterministic, sequential 0-based `SuspensionPointId` (`SP_0, SP_1, ..., SP_{N-1}`) in source/HIR traversal order (`REQ-ASY-160`, `tasks/0297 §9`) and lowers to an explicit `Suspend` terminator (`SPEC-04 AXS-EXT-044`):
   ```text
   bb_suspend_k:
       Suspend { id: SP_k, fut_place: _fut_k, dest_place: _out_k, resume: bb_resume_k, drop: bb_drop_k }
   ```
   where:
   - `id: SuspensionPointId` uniquely identifies the $k$-th suspension point ($k \in \{0, \dots, N-1\}$, mapping to state tag $k + 1$);
   - `fut_place: Place` holds the evaluated operand `Future` being awaited (evaluated exactly once before entering the poll loop, `tasks/0619 §11`);
   - `dest_place: Place` receives the `Poll.Ready(v)` output upon resumption;
   - `resume: BlockId` is the continuation basic block entered when `_fut_k` completes with `Poll.Ready(v)`;
   - `drop: BlockId` is the cleanup basic block entered if the enclosing `Future` is dropped while suspended at `SP_k`.
3. Every `Suspend` terminator acts as a mandatory semantic verification barrier where pre-suspension drops, ownership transfers, capability expiration, lock-guard checks, and `Send` obligations are validated before state-machine lowering (`REQ-ASY-032`).

**AXS-ASY-031** (Live-across-await dataflow analysis; `T417`, `REQ-ASY-005`, `REQ-ASY-008`, `REQ-ASY-024`, `REQ-ASY-025`, `REQ-ASY-069`, `REQ-ASY-090`, `REQ-ASY-150`, `0093 §5–6`, `0127 §9–11, §64 AASYNC-25`, `0248 §22–23`, `tasks/0275 §7–8`, `tasks/0297 §6–7, §32`, `tasks/0619 §6–7`).
To ensure that a `Future` state machine stores **only** the minimal state semantically required across suspension (`REQ-ASY-005`, `REQ-ASY-008`, `REQ-ASY-069`, `REQ-ASY-150`), the compiler performs **Live-Across-Await Analysis** over the `Coroutine` MIR CFG (`T417`) by combining three dataflow analyses (`REQ-ASY-025`):
1. **Backward Liveness (`LiveIn` / `LiveOut`)**: A local variable $v \in \text{Locals}$ is *use-live* across $SP_k$ (`v \in UseLive(SP_k)`) iff there exists a CFG path from `bb_resume_k` (excluding paths that reassign $v$ before reading it) that reads $v$.
2. **Forward Definite Initialization & Move State (`InitOut` / `MaybeInitOut`)**: A local $v$ is *initialized/unmoved* at $SP_k$ (`v \in MaybeInit(SP_k)`) iff along at least one CFG path reaching `bb_suspend_k`, $v$ has been assigned a value and has not yet been moved out (`Move`) or dropped (`StorageDead` / `Drop`).
3. **Drop Obligation Liveness (`DropLive`)**: If $v$'s type requires destruction (`needs_drop(typeof(v)) == true`), $v$ is *drop-live* across $SP_k$ (`v \in DropLive(SP_k)`) iff $v \in MaybeInit(SP_k)$ and $v$'s lexical scope encloses `SP_k` (so $v$ will be dropped on either the normal continuation path from `bb_resume_k` or the cancellation path `bb_drop_k`).
4. **Exact Live-Across-Await Set**: For each suspension point $SP_k$, the set of locals persisted in state $k + 1$ is:
   $$\text{LiveAcross}(SP_k) = \bigl(\text{UseLive}(SP_k) \cap \text{MaybeInit}(SP_k)\bigr) \cup \text{DropLive}(SP_k) \cup \{\text{fut\_place}(SP_k)\}$$
   - Any local $u \notin \text{LiveAcross}(SP_k)$ whose live range and lexical scope end prior to $SP_k$ MUST be excluded from the state machine's saved fields for $SP_k$ (`REQ-ASY-024`, `REQ-ASY-090`).
   - Function parameters $p_1, \dots, p_n$ are live in the initial unpolled state (`state_tag = 0`) and remain in $\text{LiveAcross}(SP_k)$ only for those $SP_k$ where $p_i \in \text{UseLive}(SP_k) \cup \text{DropLive}(SP_k)$.

**AXS-ASY-032** (Pre-suspension drop elaboration for locals dying before `.await`; `T417`, `REQ-ASY-024`, `REQ-ASY-033`, `REQ-ASY-132`, `0093 §5`, `0127 §9, §20`, `0135 §62`, `tasks/0297 §32`).
1. Local resources whose lexical scope closes before an `.await` suspension point MUST be dropped (`Drop` + `StorageDead`) **before** the `Suspend` terminator executes, rather than held until the `async fn` exits (`REQ-ASY-033`, `REQ-ASY-132`).
2. Furthermore, any temporary value constructed while evaluating expressions prior to `.await` (other than the awaited `Future` operand itself) is dropped at the end of its enclosing statement before `Suspend` (`REQ-ASY-024`).

**AXS-ASY-033** (Owned values crossing `.await` via internal ownership transfer; `T417`, `REQ-ASY-006`, `REQ-ASY-007`, `REQ-ASY-011`, `REQ-ASY-026`, `REQ-ASY-058`, `REQ-ASY-070`, `REQ-ASY-091`, `REQ-ASY-097`, `REQ-ASY-140`, `0093 §7–8`, `0127 §12, §56, §64 AASYNC-26`, `0131 §60, §88 AFN-49`, `0159 §54`).
1. Any owned value `v: T` (where `T` is not a borrowed capability or synchronous lock guard forbidden by `AXS-ASY-034`–`AXS-ASY-035`) may cross an `.await` boundary (`REQ-ASY-006`, `REQ-ASY-026`, `REQ-ASY-070`, `REQ-ASY-140`).
2. Semantically, suspending at $SP_k$ transfers ownership of every $v \in \text{LiveAcross}(SP_k)$ from the local activation frame into the `Future` state machine, and resuming at `bb_resume_k` transfers ownership back from the `Future` state machine into the local frame (`REQ-ASY-007`, `REQ-ASY-011`, `REQ-ASY-026`, `REQ-ASY-091`, `REQ-ASY-097`).
3. A value that was moved (`Move`) before $SP_k$ is not in $\text{MaybeInit}(SP_k)$ and can never be resurrected or used after $SP_k$ (`REQ-ASY-058`, `AX_MOVE_USE_AFTER_MOVE`).

**AXS-ASY-034** (Rejection of `view<T>`, `mut_view<T>`, and TLS views across `.await` in v1.0; `T417`, `REQ-ASY-003`, `REQ-ASY-004`, `REQ-ASY-012`, `REQ-ASY-015`, `REQ-ASY-028`, `REQ-ASY-029`, `REQ-ASY-030`, `REQ-ASY-031`, `REQ-ASY-071`, `REQ-ASY-072`, `REQ-ASY-106`, `0093 §8`, `0127 §14–18, §64 AASYNC-27..28`, `0135 §16–20, §55, §66 AASYNC-28..29`, `0159 §53`, `tasks/0619 §18, §20`).
1. **No `view<T>` or `mut_view<T>` across `.await` in v1.0 (`REQ-ASY-003`, `REQ-ASY-004`, `REQ-ASY-012`, `REQ-ASY-015`, `REQ-ASY-028`, `REQ-ASY-029`, `REQ-ASY-071`, `REQ-ASY-072`, `REQ-ASY-106`)**:
   - If any variable $v \in \text{LiveAcross}(SP_k)$ (or any function parameter of an `async fn` that contains at least one `.await` or whose `Future` escapes the call expression before polling) has type `view<T>`, `mut_view<T>`, or an ADT containing a stored `view<T>` / `mut_view<T>`, the capability checker (`compiler/own/cap.ax`) rejects the program with diagnostic `AX_ASYNC_VIEW_ACROSS_AWAIT`.
   - This rule applies equally when `view<T>` or `mut_view<T>` borrows a caller's stack value or borrows another owned local inside the same `async fn` (`REQ-ASY-031`, preventing self-referential `Future` state machines).
   - If the view is rooted at a `@thread_local static` or `LocalKey<T>.with` callback (`SPEC-32 AXS-SYNC-020`), holding it across `.await` is also rejected (`AX_CONC_TLS_ESCAPE` / `AX_ASYNC_VIEW_ACROSS_AWAIT`).
2. **Synchronous segments and re-borrowing after `.await` (`REQ-ASY-030`, `0127 §17–18`, `0135 §20, §55`)**:
   - Creating a `view<T>` or `mut_view<T>` from an owned value `x: T` and consuming its last use **before** reaching `.await` is completely legal ($v \notin \text{LiveAcross}(SP_k)$).
   - After `.await` resumes, the `async fn` may create a fresh `view(x)` or `mut_view(x)` from the owned value `x` (which survived `.await` in the `Future` state) for use within the next synchronous segment (`REQ-ASY-030`).

**AXS-ASY-035** (Rejection of synchronous lock guards and `@no_suspend_hold` types across `.await`; `T417`, `REQ-CONC-017`, `REQ-CONC-048`, `REQ-CONC-093`, `REQ-ASY-003`, `REQ-ASY-053`, `REQ-ASY-128`, `SPEC-30 AXS-CONC-035`, `SPEC-32 AXS-SYNC-031..032`, `0105 §52`, `0126 §30, §75 ACONC-29`, `0127 §51–52`, `0135 §58–60, §66 AASYNC-41`).
1. **Synchronous guards forbidden across `.await` (`REQ-CONC-017`, `REQ-CONC-048`, `REQ-CONC-093`, `REQ-ASY-003`, `REQ-ASY-053`, `REQ-ASY-128`)**: Holding a synchronous lock guard—specifically `std.sync.MutexGuard<T>`, `std.sync.RwLockReadGuard<T>`, `std.sync.RwLockWriteGuard<T>`, or any type annotated with `@no_suspend_hold`—across an `.await` suspension point ($g \in \text{LiveAcross}(SP_k)$) risks deadlocking worker threads and violating OS thread-ownership invariants on unlock. The compiler rejects any such program with `AX_ASYNC_GUARD_ACROSS_AWAIT`.
2. **Scoped lock before `.await` is permitted (`REQ-ASY-053`, `0127 §51`)**: Holding an `Arc<Mutex<T>>` or `Mutex<T>` across `.await` is valid provided every `MutexGuard<T>` acquired from it is dropped before `.await` (either via an explicit block `{ let g = m.lock(); ... }` or an explicit `drop(g)` call prior to `.await`).
3. **Async-aware locks (`0127 §52`, `0135 §59`, `SPEC-34`)**: When a critical section must span `.await`, code must use an async-aware primitive (`std.async.AsyncMutex<T>` / `AsyncMutexGuard<T>` in `SPEC-34`) whose acquisition suspends via `.await` rather than blocking the OS worker thread.

**AXS-ASY-036** (`Future: Send` derived strictly from parameters and live-across-await state; `T417`, `REQ-ASY-042`, `REQ-ASY-075`, `REQ-ASY-085`, `REQ-ASY-107`, `0093 §17–18`, `0127 §31–35, §64 AASYNC-31..32`, `0131 §51`, `0135 §22–23, §66 AASYNC-36..38`, `tasks/0275 §15–17`, `tasks/0297 §24–27`, `tasks/0619 §21, §23–25`).
1. **Exact `Send` criterion (`REQ-ASY-042`, `REQ-ASY-107`)**: A compiler-generated `Coroutine` / `Future` type $F$ for an `async fn` (or `async` block) implements `Send` (`F: Send`) if and only if:
   - Every function parameter (or `async` block capture) $p_i$ satisfies $T(p_i): \text{Send}$; and
   - For every suspension point $SP_k$ in the body, every variable $v \in \text{LiveAcross}(SP_k)$ satisfies $T(v): \text{Send}$ (including the awaited sub-future `fut_place(SP_k): Send`).
2. **Dead-before-await `!Send` locals do not taint `Future: Send` (`REQ-ASY-042`, `REQ-ASY-107`, `0127 §34–35`, `0135 §23`)**: If a local variable $u$ has a `!Send` type (for example, `Rc<T>` or `*mut u8`), but $u$'s live range and lexical scope end before reaching any `.await` suspension point ($u \notin \bigcup_k \text{LiveAcross}(SP_k)$), then $u$ is never stored in the `Future` across a suspension boundary where worker-thread migration can occur; therefore $u$ MUST NOT disqualify $F$ from implementing `Send`.
3. **`spawn` vs `spawn_local` obligations (`REQ-ASY-075`, `REQ-ASY-085`, `0093 §17–18`, `0127 §32–33`, `SPEC-34`)**:
   - Work-stealing / multi-threaded `spawn(fut)` requires `F: Future + Send` and `F.Output: Send` (`REQ-ASY-075`, `REQ-ASY-085`). Passing a `!Send` future or closure to `spawn` is a compile-time error (`AX_CONC_NOT_SEND` / `AX_ASYNC_FUTURE_NOT_SEND`), with secondary diagnostic labels identifying the specific `!Send` local variable and the `.await` suspension point across which it is held.
   - Single-threaded `spawn_local(fut)` and stack-local `block_on(fut)` do **not** require `F: Send` (`0127 §33`).

**AXS-ASY-037** (`Future: !Share` by default; `T417`, `REQ-ASY-043`, `REQ-ASY-077`, `REQ-ASY-127`, `0093 §19–20`, `0127 §36–37, §64 AASYNC-33`, `0135 §57`, `tasks/0297 §70–71`, `tasks/0619 §22`).
1. Compiler-generated `Coroutine` / `Future` state machines encapsulate mutable control-flow state (`state_tag`, in-flight sub-futures, and partially initialized locals) mutated on every `poll(mut_view<Self>, cx)`.
2. Consequently, every compiler-synthesized `Coroutine` / `Future` type is unconditionally `!Share` (`REQ-ASY-043`, `REQ-ASY-077`).
3. Concurrent observation or shared polling of an asynchronous result across multiple tasks or threads requires an explicit synchronization or broadcast abstraction (`Arc<Mutex<F>>`, `OnceCell<T>`, or an explicit `Shared<F>` combinator, `REQ-ASY-127`).

---

## 5. MIR State-Machine Lowering (`compiler/mir/async_lower.ax`), State Layout & Cancellation `Drop` Glue

**AXS-ASY-040** (Pipeline placement of `compiler/mir/async_lower.ax`; `T088`, `REQ-ASY-143`, `0127 §55`, `0161 §29`, `0248 §1, §38`, `tasks/0297 §10`, `tasks/0619 §4, §46, §48`).
1. In the compiler pipeline (`compiler/driver/pipeline.ax`), async state-machine lowering (`compiler/mir/async_lower.ax`) runs after HIR-to-MIR construction (`compiler/mir/builder.ax`), ownership/capability checking (`compiler/own/`), drop elaboration (`compiler/mir/drop.ax`), and live-across-await analysis (`T417`), and **before** the MIR verifier (`compiler/verify/verifier.ax`), `OptIR` optimization (`SPEC-70`), and LIR/x86-64 code generation:
   ```text
   Typed HIR
     → Ownership / Capability / Live-Across-Await Check (T417)
     → Pre-Lowering Coroutine MIR (Suspend terminators + Pre-Suspend Drops)
     → Async State-Machine Lowering (compiler/mir/async_lower.ax, T088)
     → Verified MIR (SwitchInt + ordinary Struct/Call/Drop ops)
     → { MIR Interpreter Oracle (T418) | OptIR Optimizer → LIR → x86-64 Native }
   ```
2. After `async_lower.ax` completes, no `Suspend` terminator remains in any lowered `async fn` body (`REQ-ASY-143`): every `async fn` has been split into (a) a synchronous constructor function returning the concrete state-machine struct, (b) a generated `Future.poll` MIR body using standard `SwitchInt` control flow, and (c) a generated per-state `Drop.drop` MIR body. Consequently, LIR, ABI lowering, register allocation, and the x86-64 encoder require zero async-specific logic (`0248 §38`, `tasks/0619 §4`).

**AXS-ASY-041** (Structural state-machine ADT layout & state tags; `T088`, `REQ-ASY-058`, `REQ-ASY-063`, `REQ-ASY-143`, `0127 §7–8, §60–61`, `0201 §2`, `0202 §2`, `0248 §20, §35–38`, `tasks/0619 §8, §30–31, §36–37`).
For an `async fn f(p_0: P_0, ..., p_{m-1}: P_{m-1}) -> Ret` with $N$ suspension points $SP_0, \dots, SP_{N-1}$, `async_lower.ax` synthesizes a structural state-machine ADT (`__AsyncState_f`):

```text
+-----------------------------------------------------------------------+
| __AsyncState_f (Repr.Axiom)                                           |
+-----------------------------------------------------------------------+
| state_tag: u32                                                        |
|   0                  = STATE_UNPOLLED (initial call arguments saved)  |
|   1 .. N             = STATE_SUSPENDED_0 .. STATE_SUSPENDED_{N-1}     |
|   0xFFFF_FFFF        = STATE_COMPLETED (Poll.Ready returned)          |
|   0xFFFF_FFFE        = STATE_PANICKED / STATE_CANCELLED (terminal)    |
+-----------------------------------------------------------------------+
| Saved Parameters: param_0: P_0, ..., param_{m-1}: P_{m-1}             |
+-----------------------------------------------------------------------+
| Live-Across-Await Locals: live_0: L_0, ..., live_{r-1}: L_{r-1}       |
|   (only locals v in U_{k=0..N-1} LiveAcross(SP_k))                    |
+-----------------------------------------------------------------------+
| In-Flight Sub-Futures: sub_fut_0: F_0, ..., sub_fut_{N-1}: F_{N-1}    |
+-----------------------------------------------------------------------+
```

1. **Discriminant conventions (`state_tag: u32`)**:
   - `0u32` (`STATE_UNPOLLED`): Initial state produced by calling `f(p_0, ..., p_{m-1})`. Only `param_0 .. param_{m-1}` are initialized.
   - `(k + 1) as u32` (`STATE_SUSPENDED_k`, for $0 \le k < N$): Suspended at `SP_k` (`SuspensionPointId(k)`). Exactly `sub_fut_k` and the locals in $\text{LiveAcross}(SP_k)$ are initialized.
   - `0xFFFF_FFFFu32` (`u32.MAX`, `STATE_COMPLETED`): Terminal state entered immediately before returning `Poll.Ready(output)`. Zero fields remain owned in the state machine.
   - `0xFFFF_FFFEu32` (`u32.MAX - 1`, `STATE_PANICKED` / `STATE_CANCELLED`): Terminal state entered when the `Future` unwinds/panics during `poll` or after its `Drop` glue has executed.
2. **State field minimization and storage reuse (`REQ-ASY-063`, `0127 §61`, `tasks/0619 §30, §36–37`)**:
   - Every field in `__AsyncState_f` MUST trace to an explicit source: a parameter, an in-flight `sub_fut_k`, or a local variable in $\bigcup_k \text{LiveAcross}(SP_k)$ (`tasks/0619 §30`). Locals that never cross any `SP_k` remain pure stack/register temporaries inside `poll`.
   - When a local variable's value across `SP_k` is a compile-time constant determined solely by the state transition edge, the optimizer may encode it directly in the transition block and elide the runtime state field (`REQ-ASY-063`).
   - When two locals $v_a \in \text{LiveAcross}(SP_a)$ and $v_b \in \text{LiveAcross}(SP_b)$ (or two sub-futures `sub_fut_a` and `sub_fut_b`) have disjoint state liveness sets ($\{k \mid v_a \in \text{LiveAcross}(SP_k)\} \cap \{k \mid v_b \in \text{LiveAcross}(SP_k)\} = \emptyset$), layout packing may share their physical byte offset if their types and alignments permit (`tasks/0619 §37`).

**AXS-ASY-042** (Constructor function lowering for `async fn`; `T088`, `REQ-ASY-020`, `REQ-ASY-088`, `REQ-ASY-147`, `0248 §16–18, §39`).
The original function symbol `f(p_0: P_0, ..., p_{m-1}: P_{m-1}) -> __AsyncState_f` is lowered into a non-suspending constructor function that:
1. Allocates the return place `_0: __AsyncState_f` directly in the caller-provided return slot (`RVO`, `SPEC-73 AXS-INL-015`).
2. Writes `(*_0).state_tag = 0u32` (`STATE_UNPOLLED`).
3. Moves each argument `p_i` into `(*_0).param_i` (leaving `live_*` and `sub_fut_*` slots uninitialized until their respective states are entered).
4. Returns `_0` immediately without polling or executing any statement of `f`'s source body (`REQ-ASY-020`, `REQ-ASY-088`, `REQ-ASY-147`).

**AXS-ASY-043** (Generated `Future.poll` MIR body and state-transition invariants; `T088`, `REQ-ASY-058`, `REQ-ASY-079`, `REQ-ASY-081`, `REQ-ASY-082`, `REQ-ASY-143`, `0127 §56, §64 AASYNC-35..38`, `0248 §38`, `tasks/0619 §8, §11, §32, §46`).
For each `__AsyncState_f`, `async_lower.ax` synthesizes the `Future.poll(self: mut_view<__AsyncState_f>, cx: mut_view<Context>) -> Poll<Ret>` MIR body:

```text
                       +-------------------------------+
                       | Entry: SwitchInt(self.tag)    |
                       +---------------+---------------+
                                       |
         +--------------------+--------+--------+--------------------+
         | tag == 0           | tag == k + 1    | tag == COMPLETED   |
         v                    v                 v   or PANICKED      |
+------------------+ +------------------+ +--------------------------+
| Restore params   | | bb_poll_k:       | | bb_invalid_poll:         |
| from *self;      | | Poll self.fut_k  | | Assert/Panic:            |
| goto bb_entry    | | with cx          | | AX_ASYNC_POLL_AFTER_     |
+--------+---------+ +--------+---------+ | COMPLETE                 |
         |                    |           +--------------------------+
         v                    +--------------------+
+------------------+          | Ready(val)         | Pending
| Execute sync     |          v                    v
| segment up to    | +------------------+ +------------------+
| SP_k:            | | Drop self.fut_k; | | Keep tag = k + 1;|
| 1. Drop dead     | | Restore live     | | Return           |
|    locals        | | locals from      | | Poll.Pending     |
| 2. Eval fut_k    | | *self;           | +------------------+
|    into self     | | _out_k = val;    |
| 3. Save live     | | goto bb_resume_k |
|    locals to self| +------------------+
| 4. self.tag = k+1|
| 5. goto bb_poll_k|
+------------------+
```

The generated `poll` body enforces six state-transition invariants (`REQ-ASY-058`, `REQ-ASY-079`, `REQ-ASY-081`, `REQ-ASY-082`):
1. **Entry dispatch**: `bb_dispatch` reads `(*self).state_tag` and branches via `SwitchInt`:
   - `0u32`: moves/copies `(*self).param_i` into the function's parameter locals, sets `(*self).state_tag = 0xFFFF_FFFEu32` (so an unexpected panic during the synchronous segment knows the fields are currently owned by local frame variables rather than `*self`), and jumps to `bb0`.
   - `(k + 1) as u32` ($0 \le k < N$): jumps directly to `bb_poll_k`.
   - `0xFFFF_FFFFu32` (`STATE_COMPLETED`) or `0xFFFF_FFFEu32` (`STATE_PANICKED`) or any out-of-range tag: jumps to `bb_invalid_poll`, which triggers a deterministic panic (`AX_ASYNC_POLL_AFTER_COMPLETE`).
2. **Entering suspension point $SP_k$ (`bb_suspend_k`)**:
   - All locals whose lexical scope ended before $SP_k$ have already been dropped (`AXS-ASY-032`).
   - The awaited operand `fut_k` is evaluated **exactly once** and moved into `(*self).sub_fut_k` (`tasks/0619 §11`).
   - Every local $v \in \text{LiveAcross}(SP_k)$ is moved from its local frame slot into `(*self).live_v` (`REQ-ASY-079`).
   - `(*self).state_tag` is set to `(k + 1) as u32`, and control transfers to `bb_poll_k`.
3. **Polling at $SP_k$ (`bb_poll_k`)**:
   - Invokes `Future.poll(mut_view((*self).sub_fut_k), cx)` into a temporary `_poll_res_k: Poll<Out_k>`.
   - Branches on the discriminant of `_poll_res_k`:
     - **`Poll.Pending`**: Returns `Poll.Pending` immediately from the outer `poll`. Because `(*self).state_tag == (k + 1) as u32` and all live locals + `sub_fut_k` reside in `*self`, the suspended `Future` is self-contained and ready for either a subsequent `poll` (resuming at `bb_poll_k`) or cancellation `Drop`.
     - **`Poll.Ready(val)`**: Runs `Drop` glue on `(*self).sub_fut_k` (a no-op if `sub_fut_k` is a state machine in `STATE_COMPLETED`), moves every $v \in \text{LiveAcross}(SP_k)$ from `(*self).live_v` back into its local frame variable, sets `(*self).state_tag = 0xFFFF_FFFEu32` while running the synchronous segment, assigns `dest_place = val`, and jumps to `bb_resume_k`.
4. **Completion (`Return`)**:
   - When the body reaches `Return` with return value `_0: Ret`, all remaining initialized local variables in scope are dropped in reverse declaration order, `(*self).state_tag` is set to `0xFFFF_FFFFu32` (`STATE_COMPLETED`), and `poll` returns `Poll.Ready(_0)`.
5. **Panic preservation (`REQ-ASY-081`)**:
   - If an assertion, arithmetic overflow trap, division by zero, bounds check, or explicit `panic(...)` fires while executing a synchronous segment inside `poll`, `(*self).state_tag` remains `0xFFFF_FFFEu32` (`STATE_PANICKED`) and the panic unwinds or aborts according to the active target panic profile (`SPEC-03`, `SPEC-30 AXS-CONC-006`).
6. **Synchronization preservation (`REQ-ASY-082`)**:
   - Lowering preserves the exact `Ordering` and sequence of all `MIR_STMT_ATOMIC`, fences, channel operations, and host calls on both side of every `.await` transition.

**AXS-ASY-044** (State-derived cancellation `Drop` glue; `T088`, `REQ-ASY-009`, `REQ-ASY-013`, `REQ-ASY-018`, `REQ-ASY-034`, `REQ-ASY-052`, `REQ-ASY-073`, `REQ-ASY-080`, `REQ-ASY-110`, `REQ-ASY-111`, `REQ-ASY-114`, `0093 §24–25`, `0118 §173–174, §210 AASYNC-25, 29`, `0126 §69`, `0127 §21–22, §50, §64 AASYNC-29, 36`, `0135 §30–35, §62`, `0248 §28, §36–37`, `tasks/0619 §15–17`).
1. **Cancellation is deterministic ownership destruction, not a panic or thread kill (`REQ-ASY-013`, `REQ-ASY-034`, `REQ-ASY-110`, `REQ-ASY-111`)**:
   - In Axiom, cancelling a suspended `Future` at the language level occurs when its owner drops the `Future` value while it is in `STATE_UNPOLLED` (`0`) or `STATE_SUSPENDED_k` (`1..N`) instead of polling it to `Poll.Ready`.
   - Dropping a `Pending` `Future` executes synchronously without panicking, without unwinding the caller, and without forcibly terminating the current OS thread (`REQ-ASY-034`, `REQ-ASY-110`).
2. **Per-state `Drop` dispatch (`REQ-ASY-009`, `REQ-ASY-018`, `REQ-ASY-052`, `REQ-ASY-073`, `REQ-ASY-080`, `REQ-ASY-114`, `0248 §36–37`)**:
   - Rather than storing a separate boolean drop flag per local variable when the state tag already determines initialization (`0248 §36–37`), `compiler/mir/drop.ax` and `compiler/mir/async_lower.ax` generate a state-driven `Drop.drop(self: mut_view<__AsyncState_f>)` body that switches on `(*self).state_tag`:
     - **`state_tag == 0u32` (`STATE_UNPOLLED`)**: Drops each captured parameter `(*self).param_{m-1} .. (*self).param_0` (for which `needs_drop` is true) in **reverse parameter declaration order**, and sets `(*self).state_tag = 0xFFFF_FFFEu32`.
     - **`state_tag == (k + 1) as u32` (`STATE_SUSPENDED_k`, $0 \le k < N$)**:
       1. First drops the active child sub-future `Drop.drop(mut_view((*self).sub_fut_k))` (so nested awaited futures clean up from innermost to outermost).
       2. Next drops every owned local $v \in \text{DropLive}(SP_k)$ stored in `(*self).live_v` in **reverse lexical declaration order** (matching synchronous scope-exit drop order, `REQ-ASY-052`, `REQ-ASY-080`). If a local $v \in \text{DropLive}(SP_k)$ is only conditionally initialized across incoming paths to $SP_k$, its conditional drop flag is consulted before dropping `(*self).live_v`.
       3. Sets `(*self).state_tag = 0xFFFF_FFFEu32` so no field can ever be dropped twice (`REQ-ASY-058`).
     - **`state_tag == 0xFFFF_FFFFu32` (`STATE_COMPLETED`) or `0xFFFF_FFFEu32` (`STATE_PANICKED` / `STATE_CANCELLED`)**: Performs no field drops and returns `()` immediately.

**AXS-ASY-045** (Dropping a `Future` vs cancelling an external operation; `REQ-ASY-014`, `REQ-ASY-074`, `REQ-ASY-093`, `REQ-ASY-098`, `REQ-ASY-112`, `REQ-ASY-113`, `REQ-ASY-131`, `0121 §339 AASYNC-30`, `0127 §23–24, §64 AASYNC-30`, `0131 §62, §88 AFN-50`, `0135 §33–34, §60`, `0248 §29–30`, `tasks/0275 §23–25`, `tasks/0297 §34–39`).
1. **Drop $\ne$ external cancellation (`REQ-ASY-014`, `REQ-ASY-074`, `REQ-ASY-093`, `REQ-ASY-098`, `REQ-ASY-112`)**: Dropping a `Future` destroys the in-memory state machine and runs `Drop` on its owned Axiom values, but the compiler does **not** assume that dropping a `Future` automatically halts an external kernel syscall, DMA transfer, network request, or GPU command.
2. **Explicit API cancellation and resource safety (`REQ-ASY-113`, `REQ-ASY-131`)**:
   - Cooperative task and operation cancellation is expressed through explicit library handles (`CancellationToken`, `TaskHandle.cancel()` in `SPEC-34`, and `CancelIoEx` / completion-safe buffer ownership in `SPEC-35`) (`REQ-ASY-113`).
   - Synchronizing external completion upon early `Future` drop (for example, transferring an in-flight I/O buffer to the reactor until OS completion so the kernel never writes to freed memory, or releasing an `AsyncMutex` waiter slot cleanly on cancellation) is the explicit responsibility of the owning library abstraction (`REQ-ASY-131`, `0135 §60`).

**AXS-ASY-046** (Optimizer barrier and transformation legality across `.await`; `REQ-ASY-082`, `REQ-ASY-083`, `SPEC-30 AXS-CONC-040..047`, `SPEC-72 AXS-LOOP-017`, `0127 §56, §60`, `tasks/0619 §33–35`).
1. **Suspension barrier (`tasks/0619 §33`)**: Every `.await` (`Suspend` / `bb_poll_k` boundary) is an observable control-flow and potential thread-migration boundary. Optimization passes (`SPEC-70`–`SPEC-75`) MUST NOT:
   - Hoist or sink `@thread_local` address computations across a suspension boundary (since a `Send` task may resume on a different OS worker thread);
   - Reorder `MIR_STMT_ATOMIC`, fences, `volatile` accesses, host I/O calls, or `Drop` side effects across a suspension boundary (`REQ-ASY-082`, `REQ-ASY-083`);
   - Hoist trapping arithmetic out of a conditionally executed post-await continuation into a pre-await block (`SPEC-72 AXS-LOOP-017`).
2. **Permitted async optimizations (`0127 §60–61`, `0248 §34, §53`, `tasks/0619 §34–37`)**: When observable side effects, drop order, synchronization, and trace semantics (when `--trace-async` is off) are preserved, the optimizer MAY inline child `Future.poll` calls, fold known-`Poll.Ready` awaits (`AwaitFusion` / `ReadyPathSpecialization`), scalarize state structs (`SROA`, `SPEC-73`), and eliminate dead state fields (`REQ-ASY-063`, `REQ-ASY-083`).

---

## 6. Oracle Deterministic Lifecycle Tracing, Layout Inspection & Diagnostics

**AXS-ASY-050** (Oracle deterministic async lifecycle trace events; `T418`, `REQ-ASY-057`, `REQ-ASY-059`, `0127 §57–58`).
The MIR interpreter oracle (`compiler/interp/oracle.ax` and `compiler/interp/interp.ax`) tracks every `Future` state machine instance with a deterministic monotonic 1-based identifier (`fut_id: u64 = 1, 2, ...`) and records six canonical lifecycle events (`REQ-ASY-057`, `REQ-ASY-059`):

| Event Kind | Emitted When | Canonical Trace Format |
|---|---|---|
| `POLL` | Entering `Future.poll` on `fut_id` in `state_tag` | `POLL fut=<id> fn=<name> state=<tag>` |
| `SUSPEND` | `Future.poll` transitions to `STATE_SUSPENDED_k` and returns `Poll.Pending` at `SP_k` | `SUSPEND fut=<id> fn=<name> sp=<k> state=<k+1>` |
| `WAKE` | `Waker.wake` or `Waker.wake_by_ref` is invoked for the task/driver polling `fut_id` | `WAKE fut=<id>` |
| `RESUME` | A subsequent `Future.poll` enters `bb_poll_k` for a suspended `fut_id` at `SP_k` | `RESUME fut=<id> fn=<name> sp=<k> state=<k+1>` |
| `COMPLETE` | `Future.poll` transitions `fut_id` to `STATE_COMPLETED` and returns `Poll.Ready` | `COMPLETE fut=<id> fn=<name>` |
| `CANCEL_DROP` | `Drop.drop` is invoked on `fut_id` while `state_tag` is `0` (`UNPOLLED`) or `1..N` (`SUSPENDED_k`) | `CANCEL_DROP fut=<id> fn=<name> state=<tag>` |

1. **Deterministic single-threaded oracle execution (`0127 §58`, `INV-DET-003`)**: Given the same program and inputs, the sequence of `POLL`, `SUSPEND`, `WAKE`, `RESUME`, `COMPLETE`, and `CANCEL_DROP` events in the oracle is 100% deterministic across runs.
2. **Lifecycle invariant verification in the oracle (`T418`)**:
   - The oracle verifies that every `RESUME` on `(fut_id, sp_k)` is preceded by a matching `SUSPEND` on `(fut_id, sp_k)`.
   - The oracle verifies that no `POLL` occurs on `fut_id` after `COMPLETE` or `CANCEL_DROP` (deterministically raising the poll-after-completion panic).
   - The oracle verifies that when `CANCEL_DROP` fires in state `k + 1`, every owned resource live in state `k + 1` is dropped exactly once in reverse declaration order and zero resources from other states or already-moved locals are dropped (`REQ-ASY-034`, `REQ-ASY-052`, `REQ-ASY-058`).

**AXS-ASY-051** (`inspect --emit=async-layout` state-machine layout reporting; `T418`, `REQ-ASY-045`, `0127 §39`, `0248 §55`, `tasks/0619 §30, §44`).
To give systems programmers visibility into generated `Future` memory footprints (`REQ-ASY-045`), `axiomc inspect --emit=async-layout <file.ax>` (and state-layout annotations in `inspect --emit=mir`) prints a deterministic report for each `async fn` in source declaration order:

```text
async_fn <module.fn_name>:
  future_type: __AsyncState_<fn_name>
  size: <total_bytes>
  align: <align_bytes>
  states: <N + 2> (unpolled=0, suspend_points=<N>, completed=4294967295)
  state 0 (UNPOLLED):
    param <name>: <type> (offset=<off>, size=<sz>)
  state <k+1> (SUSPEND sp=<k> at <line>:<col>):
    sub_future: <sub_fut_type> (offset=<off>, size=<sz>)
    live <name>: <type> (offset=<off>, size=<sz>, needs_drop=<bool>)
```

**AXS-ASY-052** (Canonical `AX_ASYNC_*` diagnostic codes; `T415`, `T416`, `T417`, `T418`, `spec/diagnostics.md AXD-021`, `0248 §57`).
For `E11.4` (`SPEC-33`), the `ASYNC` diagnostic area (`AX_ASYNC_*`) is established in `spec/diagnostics.md` (`AXD-021` and `§11`) and `compiler/diag/code.ax`:

| Code | Sev | Task | Trigger Condition (`SPEC-33` Rule) |
|---|---|---|---|
| `AX_ASYNC_AWAIT_OUTSIDE_ASYNC` | `E` | `T416` | `.await` expression used outside an `async fn` or `async { }` block (including inside a synchronous closure nested within an `async fn`) (`AXS-ASY-022`). |
| `AX_ASYNC_NOT_A_FUTURE` | `E` | `T416` | Operand of `expr.await` has a type `T` that does not implement `std.future.Future` (`REQ-ASY-139`, `AXS-ASY-022`). |
| `AX_ASYNC_EXTERN_ABI` | `E` | `T416` | `async fn` declared with a non-Axiom ABI (`extern "C" async fn`) or inside an `extern` block (`REQ-ASY-123`, `AXS-ASY-026`). |
| `AX_ASYNC_RECURSIVE_FUTURE` | `E` | `T416` | Direct or mutually recursive `async fn` call chain awaited without explicit pointer/heap indirection (`Box`), resulting in an infinite-size `Future` state machine (`REQ-ASY-044`, `REQ-ASY-117`, `REQ-ASY-135`, `AXS-ASY-025`). |
| `AX_ASYNC_AWAIT_IN_DROP` | `E` | `T416` | `Drop.drop` declared `async` or containing an `.await` suspension point (`REQ-ASY-115`, `REQ-ASY-116`, `AXS-ASY-022`). |
| `AX_ASYNC_BLOCKING_IN_ASYNC` | `W` | `T416` | Calling a `@blocking` synchronous operation directly inside an `async fn` or `async` block (`REQ-ASY-055`, `REQ-VER-025`, `AXS-ASY-027`). |
| `AX_ASYNC_VIEW_ACROSS_AWAIT` | `E` | `T417` | A borrowed capability (`view<T>`, `mut_view<T>`, or composite containing a stored view) is live across an `.await` suspension point (`REQ-ASY-003`, `REQ-ASY-004`, `REQ-ASY-012`, `REQ-ASY-015`, `REQ-ASY-028`..`031`, `REQ-ASY-071`..`072`, `AXS-ASY-034`). |
| `AX_ASYNC_GUARD_ACROSS_AWAIT` | `E` | `T417` | A synchronous lock guard (`MutexGuard<T>`, `RwLockReadGuard<T>`, `RwLockWriteGuard<T>`) or `@no_suspend_hold` value is held across an `.await` suspension point (`REQ-CONC-017`, `REQ-CONC-048`, `REQ-CONC-093`, `REQ-ASY-053`, `REQ-ASY-128`, `AXS-ASY-035`). |
| `AX_ASYNC_FUTURE_NOT_SEND` | `E` | `T417` | A `Future` required to satisfy `Send` (e.g., passed to cross-thread `spawn`) holds a `!Send` parameter or live-across-await local across a suspension point (`REQ-ASY-042`, `REQ-ASY-085`, `REQ-ASY-107`, `AXS-ASY-036`). |
| `AX_ASYNC_POLL_AFTER_COMPLETE` | `E` | `T418` | A `Future` is polled again after already reaching `STATE_COMPLETED` (`Poll.Ready`) or `STATE_PANICKED`/`STATE_CANCELLED` (`AXS-ASY-013`, `AXS-ASY-043`, `AXS-ASY-050`). |

### 6.1 Canonical Positive & Negative Examples

#### Positive Example 1: Zero-Heap Stack `async fn`, `.await` Chain, Re-Borrow After `.await` & `block_on`
```axiom
module example.async_stack_demo

use std.future.block_on

pub async fn fetch_value(base: i64) -> Result<i64, i32> {
    if base < 0i64 {
        return Result.Err(1i32)
    }
    return Result.Ok(base + 10i64)
}

pub async fn compute_total(seed: i64) -> Result<i64, i32> {
    let mut acc: [2]i64 = [seed, 0i64]

    // `view` created and consumed strictly before `.await` is valid:
    let initial = {
        let v: view<[2]i64> = view(acc)
        v[0]
    }

    let first = fetch_value(initial).await?

    // Re-borrowing owned `acc` via `mut_view` after `.await` is valid:
    {
        let mv: mut_view<[2]i64> = mut_view(acc)
        mv[1] = first
    }

    let second = fetch_value(acc[1]).await?
    return Result.Ok(acc[0] + second)
}

pub fn main() -> i32 {
    let res = block_on(compute_total(5i64))
    match res {
        Result.Ok(v) => {
            if v == 30i64 { return 0i32 }
            return 1i32
        }
        Result.Err(e) => return e,
    }
}
```

#### Positive Example 2: Scoped `MutexGuard` and `!Send` `Rc<T>` Dropped Before `.await` Preserves `Future: Send`
```axiom
module example.async_send_clean

use std.sync.(Arc, Mutex, Rc)

pub async fn step_async(v: i32) -> i32 {
    return v + 1i32
}

pub async fn worker_task(shared: Arc<Mutex<i32>>) -> i32 {
    let snapshot = {
        // `local_rc` (!Send) and `guard` (!Send, MutexGuard) live only inside this block:
        let local_rc = Rc.new(10i32)
        let guard = shared.get_view().lock()
        *guard.get() + *local_rc.get_view()
    }
    // Both `guard` and `local_rc` are dropped BEFORE `.await`.
    // Only `shared: Arc<Mutex<i32>>` (Send) and `snapshot: i32` (Send) cross `.await`.
    // Therefore `worker_task(shared)` implements `Future<Output = i32> + Send`!
    let next = step_async(snapshot).await
    return next
}
```

#### Negative Example 1: Rejecting `view<T>` and `mut_view<T>` Held Across `.await` (`AX_ASYNC_VIEW_ACROSS_AWAIT`)
```axiom
module example.reject_view_across_await

pub async fn tick() -> i32 {
    return 1i32
}

pub async fn bad_borrow_across_await() -> i32 {
    let mut data: i32 = 42i32
    let v: view<i32> = view(data)
    let _ = tick().await                 // ERROR [AX_ASYNC_VIEW_ACROSS_AWAIT]: `view<i32>` `v` cannot be held across `.await`
    return *v
}
```

#### Negative Example 2: Rejecting `MutexGuard<T>` Held Across `.await` (`AX_ASYNC_GUARD_ACROSS_AWAIT`)
```axiom
module example.reject_guard_across_await

use std.sync.Mutex

pub async fn yield_once() {}

pub async fn bad_lock_across_await(m: Mutex<i32>) -> i32 {
    let guard = m.get_view().lock()
    yield_once().await                   // ERROR [AX_ASYNC_GUARD_ACROSS_AWAIT]: synchronous `MutexGuard<i32>` held across `.await`
    return *guard.get()
}
```

#### Negative Example 3: Rejecting Unboxed Recursive `async fn` (`AX_ASYNC_RECURSIVE_FUTURE`)
```axiom
module example.reject_recursive_async

pub async fn countdown(n: i32) -> i32 { // ERROR [AX_ASYNC_RECURSIVE_FUTURE]: recursive `async fn` `countdown` creates an infinite-size Future state machine
    if n <= 0i32 {
        return 0i32
    }
    return countdown(n - 1i32).await
}
```

---

## 7. Requirement & Conformance Traceability Matrix

### 7.1 Primary Requirements Covered by `T415` (`covers:`)

| Requirement ID | Summary (`spec/requirements/CATALOG.md`) | Governing Rules in `SPEC-33` |
|---|---|---|
| `REQ-CONC-020` | Distinguish execution context from concrete scheduling abstractions (`Thread`, `Task`, `Future`, `Fiber`, `GPUKernel`). | `AXS-ASY-002` |
| `REQ-CONC-024` | Do not equate async tasks/futures with OS threads; treat them as independent abstractions. | `AXS-ASY-001`, `AXS-ASY-002` |
| `REQ-CONC-096` | Maintain a single unified ownership model across threads, async tasks, and GPU invocations. | `AXS-ASY-003` |
| `REQ-CONC-146` | OS thread execution is distinct from async task execution; cross-thread ownership transfer requires `Send`. | `AXS-ASY-002`, `AXS-ASY-036` |
| `REQ-CONC-191` | `Future` state crossing `.await` is checked for lifetime, capability, storage, and migration safety. | `AXS-ASY-003`, `AXS-ASY-030`..`AXS-ASY-037` |
| `REQ-CONC-217` | Concurrency model composes with ownership, capability, effect, async, and GPU semantics. | `AXS-ASY-003`, `AXS-ASY-008`, `AXS-ASY-027` |
| `REQ-ASY-022` | Lowering a suspension-free `async fn` to a synchronous function is permitted when unobservable. | `AXS-ASY-007`, `AXS-ASY-046` |
| `REQ-ASY-024` | Drop variables whose live ranges end prior to `.await` before suspension and exclude them from `Future` state. | `AXS-ASY-031`, `AXS-ASY-032` |
| `REQ-ASY-026` | Owned values may cross `.await` via internal ownership transfer into `Future` state and back on resumption. | `AXS-ASY-033`, `AXS-ASY-043` |
| `REQ-ASY-033` | Local resources whose lexical scope closes before `.await` must be dropped before suspension. | `AXS-ASY-032`, `AXS-ASY-043` |
| `REQ-ASY-039` | Concurrent task execution must be created explicitly via `spawn` rather than implicitly via `.await`. | `AXS-ASY-002` |
| `REQ-ASY-045` | Toolchain inspection command (`inspect --emit=async-layout`) reports `Future` memory layout and state sizes. | `AXS-ASY-051` |
| `REQ-ASY-055` | Tooling provides diagnostics (`AX_ASYNC_BLOCKING_IN_ASYNC`) when blocking operations are called in an async context. | `AXS-ASY-027`, `AXS-ASY-052` |
| `REQ-ASY-085` | A closure or `Future` spawned across threads must satisfy `Send`; capturing a `!Send` value across `.await` is an error. | `AXS-ASY-036`, `AXS-ASY-052` |
| `REQ-ASY-092` | `Future` is a first-class value governed by standard value, `Drop`, and `Send` semantics without hidden GC objects. | `AXS-ASY-003`, `AXS-ASY-044` |
| `REQ-ASY-100` | `Future` is a semantic abstraction, not a mandatory runtime heap allocation. | `AXS-ASY-001`, `AXS-ASY-004` |
| `REQ-ASY-103` | Creating a `Future` is distinct from starting an external operation. | `AXS-ASY-006` |
| `REQ-ASY-104` | Axiom does not force all library futures to be uniformly lazy or eager across every API. | `AXS-ASY-006` |
| `REQ-ASY-105` | Initiation, polling, and cancellation semantics of external futures must be explicitly defined by the API. | `AXS-ASY-006`, `AXS-ASY-045` |
| `REQ-ASY-116` | `Drop` is synchronous and cannot `.await`, preventing hidden scheduler dependencies in destructors. | `AXS-ASY-022`, `AXS-ASY-044` |
| `REQ-ASY-119` | No implicit semantic lifetime extension across `.await`; physical storage optimization preserves owner/capability rules. | `AXS-ASY-005` |
| `REQ-ASY-120` | Operations requiring stable physical addresses across suspension must use an explicit stable-storage contract. | `AXS-ASY-005` |
| `REQ-ASY-122` | Once a storage address is observable, the compiler must not relocate storage in violation of the contract. | `AXS-ASY-005` |
| `REQ-ASY-124` | GPU async events (`GpuEvent`) must retain necessary resource dependencies across suspension. | `AXS-ASY-008` |
| `REQ-ASY-125` | The compiler must not guess hidden asynchronous GPU lifetimes. | `AXS-ASY-008` |
| `REQ-ASY-126` | The API/ownership model must statically prevent dropping GPU buffers while an async device operation is in flight. | `AXS-ASY-008` |
| `REQ-ASY-127` | `Future` is `!Share` by default; sharing async state across threads requires an explicit synchronization abstraction. | `AXS-ASY-037` |
| `REQ-ASY-137` | Thread/task creation and async execution preserve C/C++-class performance without mandating a heavy runtime. | `AXS-ASY-001`, `AXS-ASY-004`, `AXS-ASY-014` |
| `REQ-ASY-138` | The compiler knows enough to verify safety statically without carrying a monolithic runtime scheduler. | `AXS-ASY-001`, `AXS-ASY-003`, `AXS-ASY-040` |
| `REQ-ASY-144` | `async` is a control-flow abstraction. | `AXS-ASY-001` |
| `REQ-ASY-145` | `async` does not imply OS thread creation. | `AXS-ASY-002` |
| `REQ-ASY-146` | `async` does not imply task spawning. | `AXS-ASY-002` |
| `REQ-ASY-147` | Calling an `async fn` produces a `Future` state machine. | `AXS-ASY-006`, `AXS-ASY-021`, `AXS-ASY-042` |

### 7.2 Downstream `E11.4` Implementation Requirements Specified by `SPEC-33`

| Consumer Task | Requirement IDs | Governing Rules in `SPEC-33` |
|---|---|---|
| `T416` (`std/future`, parser, HIR & typeck for `async fn` and `.await`) | `REQ-ASY-023`, `REQ-ASY-027`, `REQ-ASY-044`, `REQ-ASY-048`, `REQ-ASY-049`, `REQ-ASY-050`, `REQ-ASY-084`, `REQ-ASY-117`, `REQ-ASY-118`, `REQ-ASY-123`, `REQ-ASY-135`, `REQ-ASY-139`, `REQ-ASY-141`, `REQ-VER-025` | `AXS-ASY-010`..`AXS-ASY-015`, `AXS-ASY-020`..`AXS-ASY-027`, `AXS-ASY-052` |
| `T417` (Live-across-await analysis, `view` / lock-guard rejection & `Future: Send`) | `REQ-ASY-003`..`006`, `REQ-ASY-008`, `REQ-ASY-012`, `REQ-CONC-017`, `REQ-ASY-015`, `REQ-CONC-048`, `REQ-CONC-093`, `REQ-ASY-025`, `REQ-ASY-028`..`031`, `REQ-ASY-042`, `REQ-ASY-053`, `REQ-ASY-069`, `REQ-ASY-071`..`072`, `REQ-ASY-087`, `REQ-ASY-090`..`091`, `REQ-ASY-095`, `REQ-ASY-097`, `REQ-ASY-106`..`107`, `REQ-ASY-128`, `REQ-ASY-150`, `REQ-ASY-160` | `AXS-ASY-030`..`AXS-ASY-037`, `AXS-ASY-052` |
| `T088` (MIR state-machine lowering, per-state `Drop` glue & `std.future.block_on`) | `REQ-ASY-167`, `REQ-ASY-168` (plus lowering implementation of `AXS-ASY-014`, `AXS-ASY-040`..`AXS-ASY-046`) | `AXS-ASY-014`, `AXS-ASY-040`..`AXS-ASY-046` |
| `T418` (Oracle async lifecycle trace, `inspect --emit=async-layout` & poll-after-complete check) | `REQ-ASY-007`, `REQ-ASY-009`, `REQ-ASY-013`..`014`, `REQ-ASY-016`..`018`, `REQ-ASY-020`..`021`, `REQ-ASY-032`, `REQ-ASY-034`, `REQ-ASY-038`, `REQ-ASY-043`, `REQ-ASY-046`..`047`, `REQ-ASY-052`, `REQ-ASY-056`..`059`, `REQ-ASY-063`, `REQ-ASY-066`, `REQ-ASY-073`..`074`, `REQ-ASY-088`, `REQ-ASY-093`, `REQ-ASY-096`, `REQ-ASY-098`..`099`, `REQ-ASY-101`, `REQ-ASY-110`..`115`, `REQ-ASY-121`, `REQ-ASY-131`..`132`, `REQ-ASY-136`, `REQ-ASY-140`, `REQ-ASY-143`, `REQ-ASY-148` | `AXS-ASY-040`..`AXS-ASY-045`, `AXS-ASY-050`..`AXS-ASY-052` |
| `T419` (`E11.4` async/await, layout & cancellation conformance suite) | `REQ-ASY-010`..`011`, `REQ-ASY-064`..`065`, `REQ-ASY-070`, `REQ-ASY-075`, `REQ-ASY-077`..`083`, `REQ-ASY-133`..`134`, `REQ-ASY-142` | `AXS-ASY-001`..`AXS-ASY-052` |

---

## 8. Sources

- `spec/SPEC-02-grammar.md` — `AXS-GRM-003` (`async fn` and `.await` surface forms).
- `spec/SPEC-04-core-extensibility.md` — `AXS-EXT-020` (`TypeKind.Coroutine`), `AXS-EXT-023` (`Future`, `Waker` lang items), `AXS-EXT-031` (`is_async` flag), `AXS-EXT-033` (`Await`, `AsyncBlock` HIR expressions), `AXS-EXT-040` (`BodyKind.Coroutine`), `AXS-EXT-044` (`Suspend` terminator).
- `spec/SPEC-30-concurrency.md` — `AXS-CONC-001`..`AXS-CONC-050` (unified concurrency model, `Send`/`Share` auto-traits, `Happens-Before` barriers, guard escape rules).
- `spec/SPEC-31-atomics.md` — `AXS-ATM-001`..`AXS-ATM-066` (`Atomic<T>`, memory orderings, optimizer barrier preservation).
- `spec/SPEC-32-threads-sync.md` — `AXS-SYNC-001`..`AXS-SYNC-051` (`std.thread`, `@thread_local` TLS escape rules, `MutexGuard`/`RwLock*Guard` `!Send` and suspension restrictions, `host.futex_wait`/`host.futex_wake`).
- `docs/base/specs/0093 - Axiom — Async  Coroutine Model v0.1.md` — §§1–25 (`Future<T>`, `Poll<T>`, `Waker`, live-across-await, cancellation drop, `spawn` vs `spawn_local`, `Future: !Share`).
- `docs/base/specs/0127 - AXIOM LANGUAGE SPECIFICATION v0.1 — Part VI.md` — §§1–66 (`AASYNC-20..40`: zero-overhead `Future`, live-across-await, `view`/`mut_view`/`MutexGuard` prohibition across `.await`, `Future: Send` from live state, recursion rejection, `inspect` state size, oracle trace events).
- `docs/base/specs/0135 - AXIOM LANGUAGE SPECIFICATION v0.1.md` — Part XVI–XVII §§1–66 (`AASYNC-20..50`: cold vs eager futures, no `AsyncDrop`, `Drop` cannot `.await`, no `Pin<T>`, stable-address contracts, FFI, GPU async lifetimes).
- `docs/base/specs/0159 - AXIOM TYPED HIR + EXPRESSION SEMANTICS v0.1.md` — §§52–59, §66 (`ATHIR-39`: typing of `async fn` and `.await`).
- `docs/base/specs/0161 - AXIOM MIR v0.1.md` — §29 (`SUSPEND` / `RESUME` MIR lowering and ownership analysis ordering).
- `docs/base/specs/0201 - 2. Async Task mới là nơi cần cực kỳ nhỏ.md` — §§1–10 (`AASYNC-51..55`: minimal `Future` state size, zero mandatory heap allocation).
- `docs/base/specs/0202 - ASYNC-TASK-001 — Axiom TaskFutureScheduler Model.md` — §§1–18 (`Future` vs `Task` vs `TaskHandle`, `Poll`, `Waker`, no `Pin`).
- `docs/base/specs/0248 - COMPILER-006 — CLOSURE + ASYNC LOWERING.md` — §§1, 16–59 (`AASYNC-75..97`: `SuspensionPointId`, `LiveAcrossSuspension`, state-derived drop glue, `AX16xx` async diagnostics).
- `docs/base/tasks/0275 - BOOTSTRAP-017 — ASYNC  FUTURE.md`, `0297 - BOOTSTRAP-038 — Async  Future  Await  Cancellation Audit & Freeze.md`, `0619 - BOOTSTRAP-360 — Axiom AsyncAwait Lowering & Coroutine State Machine Engine.md` — Frozen audit and state-machine lowering specifications (`AASYNC-01..30`).
