# SPEC-32 — Threads, Thread-Local Storage (`@thread_local`), Synchronization Library (`std.sync`) & Channels (`std.sync.channel`)

## Tóm tắt

Đặc tả chính tắc (`SPEC-32`) cho mô hình luồng hệ điều hành (`std.thread`), bộ nhớ cục bộ theo luồng (`@thread_local` và `std.thread.LocalKey<T>`), thư viện đếm tham chiếu và đồng bộ hóa (`std.sync`: `Rc<T>`, `Arc<T>`, `Weak<T>`, `Mutex<T>`, `RwLock<T>`, `Condvar`, `Once`, `OnceCell<T>`, `Barrier`), kênh truyền thông điệp chuyển giao quyền sở hữu (`std.sync.channel`), cùng các hàm nội tại giao tiếp host (`std.core.host`) cho `E11.3`. Tài liệu này hợp nhất các quy tắc từ `docs/base/specs/0136`, `0203`, `0206`, `0207`, `0209` và các đặc tả tác vụ `0278`, `0329`, `0621`, `0623`, `0837`, nối tiếp `SPEC-30` (`E11.1`), `SPEC-31` (`E11.2`) và hợp đồng mở rộng lõi `SPEC-04` (`AXS-EXT-071`, `AXS-EXT-073`, `AXS-EXT-091`, `AXS-EXT-110`).
Các quyết định cốt lõi:
- Mở rộng `std.core.host` (`SPEC-04 §11`) với 8 hàm nội tại đa luồng và đồng bộ hóa (`thread_spawn`, `thread_join`, `thread_detach`, `thread_current_id`, `thread_yield`, `thread_sleep_ns`, `futex_wait`, `futex_wake`), ánh xạ trực tiếp xuống Win32 API (`CreateThread`, `WaitForSingleObject`, `WaitOnAddress`/`WakeByAddress*`) trên Windows x64 và bộ lập lịch luồng hợp tác tất định trong trình thông dịch `oracle` (`T090`).
- Định nghĩa `std.thread` (`Thread`, `ThreadId`, `Builder`, `JoinHandle<T>`, `spawn`, `scope` có cấu trúc, `detach` tường minh): `spawn` tạo ngữ cảnh thực thi độc lập (`REQ-CONC-022`), `join` thiết lập biên `Happens-Before` và trả về `Result<T, ThreadPanic>` để cô lập lỗi `panic` ở luồng con mà không làm sập hay tháo ngăn xếp luồng cha (`REQ-CONC-037`, `REQ-CONC-081`), hủy bỏ luồng hoàn toàn mang tính hợp tác (`CancelToken`) và nghiêm cấm giết luồng cưỡng bức trong mã an toàn (`REQ-CONC-003`, `REQ-CONC-080`, `REQ-CONC-198`).
- Định nghĩa `@thread_local` và `LocalKey<T>` (`T413`): mỗi luồng sở hữu bản sao độc lập (`!Share`), không có vòng đời toàn cục của tiến trình (`REQ-CONC-030`, `REQ-CONC-110`), cấm rò rỉ `view<T>`/`mut_view<T>` ra ngoài luồng hiện tại (`AX_CONC_TLS_ESCAPE`), và quy định chuẩn phát sinh section COFF `.tls$`, relocation `IMAGE_REL_AMD64_SECREL`, bảng `IMAGE_DIRECTORY_ENTRY_TLS` trong PE32+ cùng chuỗi lệnh truy cập `gs:[0x58]` trên Windows x64.
- Định nghĩa `std.sync` (`T411`) và `std.sync.channel` (`T412`): tách biệt quyền sở hữu chia sẻ (`Rc<T>` đơn luồng vs `Arc<T>` nguyên tử đa luồng, `REQ-CONC-070`, `REQ-CONC-071`) khỏi cơ chế khóa bảo vệ (`Mutex<T>`, `RwLock<T>`); các guard (`MutexGuard<T>`, `RwLockReadGuard<T>`, `RwLockWriteGuard<T>`) đều là `!Copy`, `!Send`, tự mở khóa trong `Drop` và không được sống qua điểm `.await` (`REQ-CONC-010`, `REQ-CONC-015`, `REQ-CONC-044`..`047`); kênh `channel_bounded` / `channel_unbounded` chuyển giao quyền sở hữu bằng `Move` không sao chép ngầm hay tuần tự hóa (`REQ-CONC-007`, `REQ-CONC-011`, `REQ-CONC-041`..`043`, `REQ-CONC-185`..`186`), trả lại quyền sở hữu khi gửi thất bại (`SendError<T>`) và tự hủy tất định mọi phần tử tồn đọng khi đóng kênh.

Status: draft (T410, 2026-11-03)
Owner: axiom-architect
Consolidates: `docs/base/specs/0136 - AXIOM LANGUAGE SPECIFICATION v0.1.md`, `docs/base/specs/0203 - THREAD-001 — Axiom OS Thread Model.md`, `docs/base/specs/0206 - CHANNEL-001.md`, `docs/base/specs/0207 - SYNCHRONIZATION-001.md`, `docs/base/specs/0209 - ARC-001.md`, `docs/base/tasks/0278 - BOOTSTRAP-020 — CHANNEL + LOCK-FREE RUNTIME PRIMITIVES.md`, `docs/base/tasks/0329 - BOOTSTRAP-070 — Axiom Standard Concurrency & Synchronization Library.md`, `docs/base/tasks/0621 - BOOTSTRAP-362 — Axiom Synchronization Primitives & AsyncSync Coordination Engine.md`, `docs/base/tasks/0623 - BOOTSTRAP-364 — Axiom Thread, Execution Domain & Native Threading Engine.md`, `docs/base/tasks/0837 - BOOTSTRAP-608 — Native Synchronization, Atomics, Channels, Lock-Free Structures & Concurrency Memory Semantics 5.0.md`
Covers: `REQ-CONC-003`, `REQ-CONC-022`, `REQ-CONC-080`, `REQ-CONC-123`, `REQ-CONC-198`
Consumers: `T090` (host threading intrinsics & `std.thread`), `T411` (`std.sync`: `Arc`, `Rc`, `Mutex`, `RwLock`, `Condvar`, `Once`, `OnceCell`, `Barrier`), `T412` (`std.sync.channel`: bounded & unbounded channels), `T413` (`@thread_local` statics, `LocalKey<T>`, COFF/PE `.tls` emission), `T414` (`E11.3` multi-threaded stress & synchronization conformance suite), `E11.4`–`E11.6`

---

## 1. Architectural Foundations & Host Threading Intrinsics (`std.core.host`)

**AXS-SYNC-001** (Library-level threading & synchronization without a mandatory runtime; `REQ-CONC-099`, `REQ-CONC-219`, `0136 §1–2, §101 ACONC-40..43, ACONC-75`, `0203 §1–2, §23, §28 ATHREAD-20..21, ATHREAD-36..42`, `tasks/0329 §1–2, ACLIB-20..27, ACLIB-84..93`).
1. **Concurrency as a type-system and library contract (`REQ-CONC-099`, `ACONC-75`)**: Concurrency safety in Axiom is enforced by the core ownership, capability (`view<T>`, `mut_view<T>`), auto-trait (`Send`, `Share`), and atomic memory ordering rules (`SPEC-30`, `SPEC-31`), while OS threads (`std.thread`), synchronization primitives (`std.sync`), and message-passing channels (`std.sync.channel`) are modular, link-on-demand standard library components (`REQ-CONC-219`, `ACLIB-84..86`). Sequential programs pay zero binary-size, object-header, or runtime initialization cost for threading or synchronization (`ATHREAD-40`, `ACLIB-88..90`).
2. **Strict separation of `Thread`, `Fiber`, `Task`, and `Future` (`0136 §1 ACONC-40..42`, `0203 §1 ATHREAD-20, 36..38`, `tasks/0623 §1–2`)**:
   - **`Thread` (`std.thread.Thread`)**: Preemptive OS execution resource with an OS-scheduled kernel context, dedicated call stack, and per-thread storage (`@thread_local`).
   - **`Fiber`**: User-space stackful execution context with explicit stack storage (`ATHREAD-38..39`, `E11.5`).
   - **`Task`**: Logical schedulable asynchronous or work-stealing unit of computation (`ACONC-41`, `E11.5`).
   - **`Future<T>`**: Compiler-synthesized state machine value representing a suspended computation (`ACONC-42`, `E11.4`).
   Using `std.thread` does not start an async task executor (`ATHREAD-36`), and polling a `Future` does not implicitly spawn an OS thread (`ATHREAD-37`).

**AXS-SYNC-002** (Host-interface threading and address-wait intrinsics in `std.core.host`; `T090`, `SPEC-04 AXS-EXT-110`, `ADR-0002`, `0203 §27`, `tasks/0278 §34–35`, `tasks/0837 §30, §94, §191, §196`).
In accordance with `ADR-0002` and `SPEC-04 AXS-EXT-110`, all OS thread lifecycle and contention park/wake operations cross a single well-defined host-intrinsic boundary in `std/core/host.ax` (`module std.core.host`), implemented natively in `std/sys/windows/thread.ax` (`__ax_host_<name>`) and deterministically in `compiler/interp/oracle.ax`:

```axiom
module std.core.host

@intrinsic
pub unsafe fn thread_spawn(entry: fn(*mut u8) -> i64, ctx: *mut u8, stack_size: usize) -> i64 {
    0
}

@intrinsic
pub unsafe fn thread_join(h: i64, out_ret: *mut i64) -> i64 {
    0
}

@intrinsic
pub fn thread_detach(h: i64) -> i64 {
    0
}

@intrinsic
pub fn thread_current_id() -> u64 {
    0
}

@intrinsic
pub fn thread_yield() {
}

@intrinsic
pub fn thread_sleep_ns(ns: u64) {
}

@intrinsic
pub unsafe fn futex_wait(addr: *const u32, expected: u32, timeout_ns: u64) -> i64 {
    0
}

@intrinsic
pub unsafe fn futex_wake(addr: *const u32, count: u32) -> i64 {
    0
}
```

The normative contract of each intrinsic is:

| Intrinsic | Signature | Return & Error Contract |
|---|---|---|
| `host.thread_spawn` | `unsafe fn(entry: fn(*mut u8) -> i64, ctx: *mut u8, stack_size: usize) -> i64` | Creates a new thread executing `entry(ctx)`. `stack_size == 0` uses the platform default stack reservation; `stack_size > 0` requests at least `stack_size` bytes. Returns a positive handle `h > 0` on success, `-4` (`InvalidInput`) if `entry` is null, or `-9` (`Other`) if OS thread creation fails. |
| `host.thread_join` | `unsafe fn(h: i64, out_ret: *mut i64) -> i64` | Blocks the calling thread until thread handle `h` finishes, writes the child's `i64` exit value into `*out_ret` (when `out_ret != null`), consumes and closes `h`, and establishes `Happens-Before` from child completion to caller continuation (`REQ-CONC-036`, `REQ-CONC-187`). Returns `0` on success, or `-4` (`InvalidInput`) if `h <= 0`, `h` was already joined/detached, or `h` refers to the calling thread itself (self-join rejection). |
| `host.thread_detach` | `fn(h: i64) -> i64` | Detaches thread handle `h` so its control block and OS handle are released automatically upon thread termination without requiring `thread_join`. Returns `0` on success, or `-4` if `h <= 0` or already joined/detached. |
| `host.thread_current_id` | `fn() -> u64` | Returns a non-zero 64-bit identifier unique to the calling thread for its lifetime (`1u64` for the main thread in the oracle, `2u64, 3u64, ...` monotonically assigned at spawn). |
| `host.thread_yield` | `fn()` | Cooperatively yields the current thread's execution slice to other runnable threads. |
| `host.thread_sleep_ns` | `fn(ns: u64)` | Suspends the calling thread for at least `ns` nanoseconds (`0` returns immediately or yields). |
| `host.futex_wait` | `unsafe fn(addr: *const u32, expected: u32, timeout_ns: u64) -> i64` | Atomically checks whether the naturally aligned 32-bit word at `addr` equals `expected`: if unequal, returns `0` immediately; if equal, suspends the calling thread until woken by `futex_wake` on `addr`, a spurious wakeup (returning `0`), or timeout expiration (`timeout_ns` nanoseconds; `0xFFFF_FFFF_FFFF_FFFFu64` = infinite wait, returning `-5` `TimedOut` on timeout). Returns `-4` if `addr` is null or not 4-byte aligned. |
| `host.futex_wake` | `unsafe fn(addr: *const u32, count: u32) -> i64` | Wakes up to `count` threads blocked in `futex_wait` on `addr` (`count == 1` wakes one waiter; `count == 0xFFFF_FFFFu32` wakes all waiters on `addr`). Returns `>= 0` on success, or `-4` if `addr` is null or not 4-byte aligned. |

**AXS-SYNC-003** (Windows x64 native implementation of host threading intrinsics in `std/sys/windows/thread.ax`; `T090`, `0203 §27`, `tasks/0623 §3, §40`, `tasks/0837 §30, §94, §191`).
On `x86_64-windows` (`std/sys/windows/thread.ax`), the host intrinsics lower to `__ax_host_thread_*` and `__ax_host_futex_*` backed by Win32 system libraries (`@link("kernel32")` and `@link("synchronization")`):
1. **Thread control block (`WinThreadSlot`) and `CreateThread` trampoline**:
   - Because Win32 `CreateThread` expects `extern "system" fn(lpParameter: *mut u8) -> u32` while Axiom's `entry` has signature `fn(*mut u8) -> i64`, `__ax_host_thread_spawn` allocates a heap control block holding:
     - `entry: fn(*mut u8) -> i64`, `ctx: *mut u8`,
     - `ret_val: i64` (written by the child before exit),
     - `os_handle: *mut u8` (`HANDLE` returned by `CreateThread`),
     - `state: Atomic<u32>` (tracking handle ownership between parent `join`/`detach` and child completion so the control block is freed by whichever finishes last without use-after-free).
   - Calls `CreateThread(null, stack_size, win32_thread_trampoline, slot_ptr, 0, address_of_mut(tid))`.
2. **`__ax_host_thread_join` and `__ax_host_thread_detach`**:
   - `__ax_host_thread_join` calls `WaitForSingleObject(slot.os_handle, 0xFFFF_FFFFu32)` (`INFINITE`), reads `slot.ret_val` into `*out_ret` ( acquiring child writes via the OS thread termination barrier + `Acquire` load on `slot.state`), calls `CloseHandle(slot.os_handle)`, and frees `slot`.
   - `__ax_host_thread_detach` calls `CloseHandle(slot.os_handle)` and atomically transitions `slot.state` to detached so the child frees `slot` upon exit (or frees `slot` immediately if the child already exited).
3. **`__ax_host_futex_wait` and `__ax_host_futex_wake` (`WaitOnAddress` / `WakeByAddress*`)**:
   - `__ax_host_futex_wait(addr, expected, timeout_ns)` converts `timeout_ns` to milliseconds (`0xFFFF_FFFFu32` `INFINITE` when `timeout_ns == 0xFFFF_FFFF_FFFF_FFFFu64`, otherwise `max(1u32, (timeout_ns / 1_000_000u64) as u32)` when `timeout_ns > 0`, or `0u32` when `timeout_ns == 0`) and invokes `WaitOnAddress(addr as *const u8, address_of(expected) as *const u8, 4, timeout_ms)`. If `WaitOnAddress` fails with `ERROR_TIMEOUT` (`1460u32`), it returns `-5`; otherwise it returns `0`.
   - `__ax_host_futex_wake(addr, count)` invokes `WakeByAddressSingle(addr as *const u8)` when `count == 1u32`, and `WakeByAddressAll(addr as *const u8)` when `count > 1u32` (and is a no-op returning `0` when `count == 0u32`).

**AXS-SYNC-004** (MIR interpreter oracle cooperative thread scheduler & futex semantics; `T090`, `T408`, `compiler/interp/oracle.ax`, `compiler/interp/interp.ax`, `SPEC-31 AXS-ATM-050..054`, `tasks/0278 ARUNTIME-53..55`, `tasks/0329 ACLIB-59`).
In the MIR interpreter (`compiler/interp/`), multi-threaded programs execute deterministically on a single host OS thread via the oracle's cooperative thread table (`INV-DET-003`):
1. **Logical thread table**: The interpreter maintains a table of logical threads `InterpThread`:
   - Thread `0` (ID `1u64`) is the initial `main` thread.
   - `host.thread_spawn(entry, ctx, stack_size)` validates `entry` as a valid function pointer, creates a new `InterpThread` with deterministic handle `h = next_thread_handle` (`1, 2, ...`) and thread ID `tid = (h + 1) as u64`, initializes its call frame to `entry(ctx)`, copies the parent's current vector clock `clock[child] = clock[parent]` (`SPEC-30 AXS-CONC-041`), initializes an empty per-thread TLS table (`AXS-SYNC-024`), and marks the thread `Runnable`.
2. **Join, detach, and deadlock detection**:
   - `host.thread_join(h, out_ret)` validates `h` and `out_ret` (`interp_validate_raw_ptr(ctx, out_ret, 8)` if non-null). If child `h` has not yet terminated, the caller transitions to `BlockedOnJoin(h)` and the scheduler runs runnable threads until `h` finishes. When `h` finishes, the oracle joins the child's vector clock into the caller (`clock[caller] = clock[caller] \sqcup clock[child]`), writes the child's `ret_val` to `*out_ret`, and marks `h` `Joined`.
   - If the calling thread blocks on `thread_join` or `futex_wait` with infinite timeout and **zero** threads in the interpreter are `Runnable` (and no finite-timeout sleeper exists), the oracle deterministically detects a total deadlock and halts with a diagnostic rather than looping infinitely.
3. **Oracle `futex_wait` and `futex_wake` (`ACLIB-59`, `SPEC-30 AXS-CONC-043`)**:
   - `futex_wait(addr, expected, timeout_ns)` validates that `addr` is a live, 4-byte-aligned allocation (`AX_UNSAFE_INTERP_UB` otherwise) and inspects the current 32-bit value at `addr`: if `!= expected`, it returns `0`; if `== expected` and `timeout_ns == 0`, it returns `-5`; otherwise it parks the calling thread in `BlockedOnFutex { addr, deadline_ns }`.
   - `futex_wake(addr, count)` transitions up to `count` threads in `BlockedOnFutex { addr, .. }` (in deterministic FIFO wait order) back to `Runnable`.
   - **Wait/wake does not substitute for atomic publication (`tasks/0329 ACLIB-59`, `SPEC-30 AXS-CONC-043`)**: In the oracle's vector-clock memory model (`SPEC-31 AXS-ATM-051`), `futex_wake` does **not** transfer the waker's vector clock to woken threads; memory publication across a futex wait MUST be established by the caller's `Release`/`Acquire` operations on the `Atomic<u32>` state word at `addr`.

---

## 2. OS Threads, Structured Scopes, Panic Containment & Cancellation (`std.thread`)

**AXS-SYNC-010** (Canonical `std.thread` surface types and functions; `T090`, `REQ-CONC-022`, `0136 §2, §12–19`, `0203 §2, §4, §7, §10–14, §27, ATHREAD-20..45`, `tasks/0329 §2–3, §31–35`).
The module `std.thread` (`std/thread/mod.ax`) defines the canonical OS thread abstractions below (using canonical Axiom syntax):

```axiom
module std.thread

@derive(Copy, Clone, Eq, PartialEq, Ord, Hash)
pub struct ThreadId {
    pub id: u64,
}

pub struct Thread {
    id: ThreadId,
    name: Option<String>,
}

pub struct Builder {
    stack_size: usize,
    name: Option<String>,
}

@derive(Copy, Clone, Eq, PartialEq)
pub enum ThreadError {
    SpawnFailed,
    InvalidConfig,
}

pub struct ThreadPanic {
    pub message: String,
    pub thread_id: ThreadId,
}

pub struct JoinHandle<T> {
    raw_handle: i64,
    thread_info: Thread,
    slot: *mut u8,
}
```

The canonical operations exposed by `std.thread` are:

| Item / Method | Signature | Semantic Contract |
|---|---|---|
| `spawn` | `pub fn spawn<F, T>(f: F) -> JoinHandle<T> where F: FnOnce() -> T + Send + 'static, T: Send + 'static` | Spawns a new OS thread with default `Builder` configuration executing `f()` (`REQ-CONC-022`); panics if the OS refuses thread creation (use `Builder.spawn` for fallible creation). |
| `Builder.new` | `pub fn new() -> Builder` | Creates a default thread configuration (`stack_size = 0` platform default, `name = Option.None`). |
| `Builder.stack_size` | `pub fn stack_size(self, size: usize) -> Builder` | Configures the minimum stack reservation in bytes for the spawned thread (`ATHREAD-26`). |
| `Builder.name` | `pub fn name(self, name: Str) -> Builder` | Configures a human-readable diagnostic thread name (`ATHREAD-43`). |
| `Builder.spawn` | `pub fn spawn<F, T>(self, f: F) -> Result<JoinHandle<T>, ThreadError> where F: FnOnce() -> T + Send + 'static, T: Send + 'static` | Fallibly spawns a new OS thread with the configured stack size and name (`0203 §27`). |
| `JoinHandle.thread` | `pub fn thread(self: view<JoinHandle<T>>) -> view<Thread>` | Borrows the descriptor (`ThreadId` and optional name) of the spawned thread. |
| `JoinHandle.join` | `pub fn join(self) -> Result<T, ThreadPanic>` | Consumes `self`, waits for thread termination, establishes `Happens-Before`, and returns `Ok(val)` or `Err(ThreadPanic)` (`REQ-CONC-036`, `REQ-CONC-037`). |
| `JoinHandle.detach` | `pub fn detach(self)` | Consumes `self` and explicitly detaches the thread to run independently until completion (`REQ-CONC-038`). |
| `JoinHandle.is_finished` | `pub fn is_finished(self: view<JoinHandle<T>>) -> bool` | Non-blockingly queries whether the child thread has completed execution (`Acquire` load on completion state). |
| `current` / `current_id` | `pub fn current() -> Thread` / `pub fn current_id() -> ThreadId` | Returns the descriptor or `ThreadId` of the calling thread (`0203 §27`). |
| `yield_now` | `pub fn yield_now()` | Cooperatively yields the calling thread (`host.thread_yield()`). |
| `sleep` / `sleep_ms` / `sleep_ns` | `pub fn sleep(d: Duration)` / `pub fn sleep_ms(ms: u64)` / `pub fn sleep_ns(ns: u64)` | Suspends the calling thread for at least the specified duration (`host.thread_sleep_ns`). |
| `scope` | `pub fn scope<F, R>(f: F) -> R where F: FnOnce(mut_view<Scope>) -> R` | Executes a structured concurrency scope that joins all child threads spawned via `Scope` before returning (`AXS-SYNC-014`). |

**AXS-SYNC-011** (`spawn` creates an independent execution context with move capture and `Send` bounds; `T090`, `REQ-CONC-022`, `0126 §2`, `0136 §3, §12, §63, ACONC-45, ACONC-78`, `0203 §7–9, ATHREAD-28`).
1. **Independent execution context (`REQ-CONC-022`)**: Calling `std.thread.spawn(f)` or `Builder.spawn(f)` MUST create a new execution context that is scheduled independently by the operating system (or by the oracle scheduler in `--interp` mode) (`0126 §2`).
2. **Ownership and `Send` obligations (`ATHREAD-28`, `SPEC-30 AXS-CONC-020..024`)**:
   - The closure type `F` and return type `T` MUST satisfy `F: Send + 'static` and `T: Send + 'static` (`AX_CONC_CAPTURE_NOT_SEND`, `AX_CONC_NOT_SEND`).
   - All `!Copy` values captured by `f` are moved into the child thread's environment (`SPEC-30 AXS-CONC-022`), invalidating the bindings in the parent thread without implicit copying.
   - No non-`'static` stack-borrowed `view<U>` or `mut_view<U>` may escape into an unscoped `spawn` (`AX_CONC_ESCAPING_VIEW`, `SPEC-30 AXS-CONC-023`).
3. **Spawn `Happens-Before` (`0136 §63`, `SPEC-30 AXS-CONC-041`)**: All memory writes performed by the parent thread sequenced-before `spawn(f)` happen-before ($\prec_{\text{hb}}$) the start of `f()` in the child thread.

**AXS-SYNC-012** (`JoinHandle<T>.join()` completion synchronization and result ownership transfer; `T090`, `T414`, `REQ-CONC-036`, `REQ-CONC-187`, `0126 §16`, `0136 §14–15, §64, ACONC-52`, `0203 §10, ATHREAD-23`, `tasks/0623 §10–11`).
1. **Linear handle ownership (`0136 §15`)**: `JoinHandle<T>` is `!Copy` (`impl<T> !Copy for JoinHandle<T> {}`), implements `Send` when `T: Send`, and is `!Share`. Calling `handle.join()` consumes `handle` by value so a thread can be joined at most once (`AX_MOVE_USE_AFTER_MOVE` on a second `join` or `detach`).
2. **Completion `Happens-Before` and result transfer (`REQ-CONC-036`, `REQ-CONC-187`)**: A return from `handle.join()` establishes a `Synchronizes-With` ($\prec_{\text{sw}}$) edge from the child thread's completion to the parent thread's continuation (`REQ-CONC-036`, `REQ-CONC-187`):
   - Every memory write and every local/TLS `Drop` destructor executed by the child thread happens-before ($\prec_{\text{hb}}$) every read or write in the parent thread sequenced-after `handle.join()`.
   - When the child thread returns normally, ownership of its result `val: T` is transferred by move into `Result.Ok(val)` on the parent thread without copying (`REQ-CONC-036`).

**AXS-SYNC-013** (Explicit thread detachment and `JoinHandle<T>` drop semantics; `T090`, `T414`, `REQ-CONC-038`, `REQ-CONC-039`, `0126 §18`, `0136 §16–17, §65, ACONC-53, ACONC-80`, `0203 §12–13, ATHREAD-22, ATHREAD-24, ATHREAD-45`, `tasks/0623 §12–13`).
1. **Explicit `detach()` (`REQ-CONC-038`, `ACONC-53`, `ATHREAD-45`)**: Thread detachment is performed explicitly via `handle.detach()`, which consumes `JoinHandle<T>` (`AX_MOVE_USE_AFTER_MOVE` if used afterwards). The parent execution context MUST NOT assume that a detached thread has completed or that its side effects are visible without separate explicit synchronization (`REQ-CONC-038`, `ACONC-80`).
2. **Task-bound resource lifecycle (`REQ-CONC-039`, `ATHREAD-24`)**: The ownership of all values moved into a detached thread, together with its call stack and thread-local storage, is bound strictly to the detached thread's own execution lifecycle (`REQ-CONC-039`). When the detached thread finishes executing its body, it runs `Drop` on its return value `T`, its captured closure environment, and its TLS variables before the OS/runtime reclaims its stack and kernel handle.
3. **Dropping `JoinHandle<T>` without `join()` (`ATHREAD-22`)**: Dropping a `JoinHandle<T>` without calling `.join()` does **not** forcibly kill or abort the child thread (`ATHREAD-22`); `Drop` on `JoinHandle<T>` detaches the underlying handle (`host.thread_detach`) so the child thread continues safely to completion.

**AXS-SYNC-014** (Structured thread scopes `std.thread.scope`, `Scope`, and `ScopedJoinHandle<T>`; `T090`, `T414`, `0136 §18–19`, `0203 §14, ATHREAD-44`, `SPEC-30 AXS-CONC-023..025, AXS-CONC-033`).
`std.thread.scope` provides lexically bounded structured concurrency for OS threads:
```axiom
pub struct Scope {
    active_count: usize,
    first_panic: Option<ThreadPanic>,
    handles_head: *mut u8,
}

pub struct ScopedJoinHandle<T> {
    raw_handle: i64,
    slot: *mut u8,
}
```
1. **Scoped borrowing of parent stack data (`SPEC-30 AXS-CONC-023(3), AXS-CONC-033`)**: Inside `thread.scope(|s| { ... })`, calls to `s.spawn(f) -> ScopedJoinHandle<T>` allow the child closure `f` to capture stack-bound capabilities from the enclosing parent frame—specifically shared `view<U>` (where `U: Share`) and provably `DISJOINT` `mut_view<U>` projections (where `U: Send`, such as distinct struct fields or `slice.split_at_mut(mid)` sub-slices)—provided their referent lifetimes outlive the `scope` call.
2. **No detachment inside `Scope`**: `ScopedJoinHandle<T>` provides `.join(self) -> Result<T, ThreadPanic>` and `impl !Copy`, and intentionally omits `.detach()`.
3. **Mandatory join barrier prior to scope exit (`ATHREAD-44`)**: Before `thread.scope(f)` returns to its caller, the `Scope` epilogue MUST join every child thread spawned through `s` that has not already been joined by user code. This barrier establishes a `Happens-Before` edge from all child threads to the parent code following `thread.scope(...)` and statically guarantees that no child thread can access borrowed parent stack memory after `thread.scope` returns.
4. **Scoped panic propagation**: If `f(s)` or any unjoined child thread spawned in `s` panics, `thread.scope` still waits for **all** other spawned child threads in `s` to finish (preventing dangling stack borrows during cleanup!) and then propagates the panic.

**AXS-SYNC-015** (Child thread panic containment at the `JoinHandle` boundary; `T090`, `T414`, `REQ-CONC-037`, `REQ-CONC-081`, `0126 §17, §70`, `0136 §66–68`, `0203 §11, ATHREAD-30`).
1. **No implicit parent unwinding (`REQ-CONC-081`, `ATHREAD-30`)**: Under the standard hosted profile, a panic inside a spawned child thread MUST NOT implicitly unwind or immediately terminate the parent thread (`REQ-CONC-081`). Instead, the thread entry wrapper catches the panic at the top of the child thread's call stack, runs deterministic local/TLS cleanup for the child thread, records the panic payload in the thread's shared completion slot, and exits the child thread with a panic status sentinel.
2. **Value-based failure reporting via `JoinHandle.join()` (`REQ-CONC-037`)**: When a parent (or other joining thread) calls `handle.join()` on a panicked child thread, `join()` returns `Result.Err(ThreadPanic { message, thread_id })` as an ordinary Axiom value without requiring a language-level exception runtime (`REQ-CONC-037`).
3. **Explicit `panic = abort` profile exception (`REQ-CONC-081`, `0136 §67`)**: Only when a binary is compiled under an explicit whole-process `panic = abort` profile (`SPEC-04 AXS-EXT-062`) does an unhandled panic in any thread immediately abort the entire process.

**AXS-SYNC-016** (Cooperative thread cancellation & prohibition of safe forced thread termination; `T410`, `REQ-CONC-003`, `REQ-CONC-080`, `REQ-CONC-198`, `0105 §35`, `0126 §67`, `0136 §20–22, ACONC-54..55`, `0203 §28 ATHREAD-31`, `tasks/0329 §41–43`, `tasks/0623 §14–15`).
1. **Forbidden forced thread termination in safe code (`REQ-CONC-003`, `REQ-CONC-080`, `REQ-CONC-198`, `ACONC-54`, `ATHREAD-31`)**: Safe Axiom code and the standard library MUST NOT support forced, asynchronous thread termination (`TerminateThread`, `pthread_kill`/`PTHREAD_CANCEL_ASYNCHRONOUS`) that interrupts a thread at an arbitrary instruction (`REQ-CONC-003`, `REQ-CONC-198`). Asynchronous thread killing leaves held `Mutex`/`RwLock` guards permanently locked or inconsistent, skips `Drop` destructors, corrupts allocator metadata, and violates capability invariants.
2. **Cooperative cancellation protocol (`REQ-CONC-080`, `ACONC-55`)**: Thread cancellation in Axiom Core is strictly cooperative (`REQ-CONC-080`). `std.thread` / `std.sync` provides `CancelSource` and `CancelToken`:
   ```axiom
   pub struct CancelSource {
       flag: Arc<Atomic<bool>>,
   }

   @derive(Clone)
   pub struct CancelToken {
       flag: Arc<Atomic<bool>>,
   }
   ```
   - `CancelSource.new() -> CancelSource` creates a cancellation controller; `source.token() -> CancelToken` (`Send`, `Share`, `Clone`) hands a read-only token to worker threads; `source.cancel()` sets the atomic flag (`Ordering.Release`); and worker threads poll `token.is_cancelled() -> bool` (`Ordering.Acquire`) at well-defined loop, I/O, or wait boundaries so they exit cleanly while running all normal `Drop` destructors (`tasks/0329 §43`).

**AXS-SYNC-017** (Stack policy, CPU affinity/priority hints, and explicit reentrancy contracts; `T410`, `REQ-CONC-123`, `0136 §57–60, §97`, `0203 §3–6, §18–20, ATHREAD-25..27, ATHREAD-34..35`, `tasks/0623 §5–6, §18`).
1. **Stack lifetime and configuration (`ATHREAD-25..27`)**: A thread's stack is allocated/reserved before the thread entry function begins and remains valid until the thread exits and its join/detach contract resolves (`ATHREAD-25`). Stack size is a policy configured via `Builder.stack_size(bytes)` (`ATHREAD-26`), not a fixed language constant.
2. **CPU affinity and priority do not alter safety (`ATHREAD-34..35`, `tasks/0623 §6`)**: Thread affinity and priority are platform scheduling hints. The compiler MUST NEVER rely on CPU affinity (e.g., pinning two threads to the same core) to elide `Send`/`Share` checks or excuse unsynchronized shared mutation (`tasks/0623 §6`).
3. **Reentrancy is an explicit contract (`REQ-CONC-123`, `0136 §97`)**: Thread safety across concurrent threads (`Send`/`Share`) is orthogonal to *reentrancy* (invoking a function or acquiring a lock recursively on the **same** call stack while an outer invocation is already in progress, such as via callbacks or interrupt/signal handlers). Standard `Mutex<T>` and `RwLock<T>` are **non-reentrant**; any FFI function, callback interface, or system API where reentrancy is required or guaranteed MUST declare that contract explicitly (`REQ-CONC-123`).

---

## 3. Thread-Local Storage (`@thread_local`, `LocalKey<T>`, COFF `.tls$` & PE TLS Directory)

**AXS-SYNC-020** (`@thread_local` static semantics, `!Share` isolation, and per-thread lifetime; `T413`, `REQ-CONC-030`, `REQ-CONC-110`, `SPEC-04 AXS-EXT-091`, `SPEC-30 AXS-CONC-004, AXS-CONC-034`, `0126 §8`, `0136 §52–53, ACONC-73`, `0203 §15–17, ATHREAD-32..33`, `tasks/0623 §7–8`).
1. **Per-thread storage identity (`ACONC-73`, `ATHREAD-32`)**: A `@thread_local` static declaration:
   ```axiom
   @thread_local
   static TLS_COUNTER: i64 = 0
   ```
   defines a thread-local storage slot with semantic identity `(ThreadId, ItemId)`. Each OS thread (and each oracle thread) owns a distinct instance of `TLS_COUNTER` initialized independently on that thread.
2. **TLS does NOT have global process lifetime (`REQ-CONC-110`, `0136 §53`)**: Unlike an ordinary `static` item (which lives for the entire process execution `'static`), a `@thread_local` instance lives only for the lifetime of its owning thread (`'thread`). When a thread exits, its TLS instances are destroyed and their backing memory is reclaimed (`REQ-CONC-110`, `ATHREAD-33`).
3. **`!Share` default and explicit `Send` contract for extracted values (`REQ-CONC-030`, `0126 §8`)**:
   - Thread-local storage descriptors (`LocalKey<T>`) and thread-local places are unconditionally **`!Share`** (and `!Send` for thread-bound descriptors/views) (`REQ-CONC-030`).
   - Safe code MUST NOT share a `view<T>` or `mut_view<T>` of a `@thread_local` item across execution contexts, store a TLS view in a global `static` or heap struct that outlives the scoped access, return a TLS view from a thread, or hold a TLS view across an async `.await` suspension point (`AX_CONC_TLS_ESCAPE` / `AX_CONC_UNSYNC_STATIC`).
   - A value read/copied or moved *out* of thread-local storage by value (`let val: T = ...`) may be sent to another execution context if and only if the value's own type `T` satisfies `T: Send` (`REQ-CONC-030`).

**AXS-SYNC-021** (`std.thread.LocalKey<T>` scoped access and deterministic per-thread cleanup; `T413`, `REQ-CONC-030`, `REQ-CONC-110`, `0136 §52–53`, `0203 §15–17, ATHREAD-32..33`).
`std/thread/local.ax` (`re-exported by std.thread`) provides `LocalKey<T>` for safe, scoped access and lazy per-thread initialization/destruction of thread-local values:
```axiom
module std.thread.local

pub struct LocalKey<T> {
    init_fn: fn() -> T,
    slot_id: u32,
}

impl<T> !Send for LocalKey<T> {}
impl<T> !Share for LocalKey<T> {}
```
1. **Scoped callback access (`with` / `with_mut`)**:
   - `pub fn local_key_new<T>(init_fn: fn() -> T) -> LocalKey<T>`
   - `pub fn with<F, R>(self: view<LocalKey<T>>, f: F) -> R where F: FnOnce(view<T>) -> R`: Lazily initializes the calling thread's instance of `T` via `(self.init_fn)()` on first access by that thread, and invokes `f(view(tls_val))`.
   - `pub fn with_mut<F, R>(self: view<LocalKey<T>>, f: F) -> R where F: FnOnce(mut_view<T>) -> R`: Invokes `f(mut_view(tls_val))` on the calling thread's instance (panicking if reentrantly invoked on the same `LocalKey<T>` while an outer `with` or `with_mut` borrow on the same thread is active, preserving `mut_view` exclusivity).
   - `pub fn get(self: view<LocalKey<T>>) -> T where T: Copy` and `pub fn set(self: view<LocalKey<T>>, val: T)`: Convenience value accessors for `Copy` / replaceable thread-local state.
2. **Compile-time escape prevention (`REQ-CONC-110`)**: Because `view<T>` and `mut_view<T>` are scoped to the parameter of `f`, the capability checker (`compiler/own/cap.ax` & `compiler/types/typeck.ax`) rejects any closure `f` that attempts to return the borrowed `view<T>` / `mut_view<T>` in `R` or store it into an outer binding (`AX_CONC_TLS_ESCAPE` / `AX_CAP_OUTLIVES_OWNER`).
3. **Deterministic per-thread destructor execution (`ATHREAD-33`)**: When a spawned thread finishes executing its body (before signaling completion to `thread_join`), the thread runtime iterates all initialized `LocalKey<T>` slots for the exiting thread in reverse initialization order (LIFO) and runs `drop_in_place<T>()` if `needs_drop<T>()` is true (`ATHREAD-33`).

**AXS-SYNC-022** (`@thread_local` HIR/MIR/LIR lowering and compile-time validation; `T413`, `SPEC-04 AXS-EXT-071, AXS-EXT-073, AXS-EXT-091`, `tasks/0623 §7–8, §35–36`).
1. **Attribute target and initializer validation (`compiler/hir/lower.ax`, `compiler/types/typeck.ax`)**:
   - `@thread_local` is allowed **only** on `static` items (`SPEC-04 AXS-EXT-091`). Attaching `@thread_local` to a `fn`, `struct`, `enum`, `const`, `type`, or local `let` binding is rejected at compile time with `AX_TYPE_INVALID_TLS_DECL`.
   - The initializer expression of a `@thread_local static` item MUST be evaluable at compile time (`ConstValue`, `SPEC-04 AXS-EXT-024`) so its initial bytes can be emitted into the `.tls$` image template (`tasks/0623 §8`).
2. **Direct access vs escaping borrow rules (`compiler/types/typeck.ax`)**:
   - Within a function, reading or writing a `@thread_local static` by value (when `T: Copy`) or passing a temporary `view<T>`/`mut_view<T>` that does not escape the current statement/call on the current thread is valid in safe code because the storage is private to the executing OS thread (`tasks/0623 §7`).
   - Returning a `view<T>` or `mut_view<T>` rooted at a `@thread_local static` item from a function, storing it into a struct/heap/global place, capturing it into a `spawn` closure, or holding it across `.await` is rejected at compile time with `AX_CONC_TLS_ESCAPE`.
3. **MIR and LIR representation (`compiler/mir/builder.ax`, `compiler/lir/builder.ax`)**:
   - In MIR (`SPEC-04 AXS-EXT-041`), a `@thread_local static` item is marked with `is_tls = true` on its `Static(SymbolId)` place/global descriptor.
   - In LIR (`compiler/lir/builder.ax`), loading the address of a `@thread_local` symbol emits `LIR_INST_TLS_ADDR` (or `LirGlobal` with `is_tls = true` placed in section kind `AX_SEC_TLS = 4u32`), never a plain RIP-relative `LEA [rip + sym]`.

**AXS-SYNC-023** (Windows x64 `gs:[0x58]` TLS codegen, COFF `.tls$` section, `IMAGE_REL_AMD64_SECREL`, and PE32+ `IMAGE_DIRECTORY_ENTRY_TLS`; `T413`, `SPEC-04 AXS-EXT-071, AXS-EXT-073`, `compiler/target/x64/isel.ax`, `compiler/obj/coff.ax`, `compiler/link/pe.ax`).
On `x86_64-windows`, native `@thread_local` storage is lowered and linked according to the Microsoft PE/COFF x64 TLS specification:
1. **Object model & COFF constants (`compiler/obj/coff.ax`)**:
   - Section kind: `AX_SEC_TLS = 4u32` (`SEC_TLS = 4u32`), emitted as COFF section `.tls$` with characteristics `IMAGE_SCN_CNT_INITIALIZED_DATA | IMAGE_SCN_MEM_READ | IMAGE_SCN_MEM_WRITE` and natural alignment (`IMAGE_SCN_ALIGN_8BYTES` or symbol alignment).
   - Relocation kind: `AX_RELOC_X86_64_TLSREL = 6u32` (`RELOC_X86_64_TLSREL = 6u32`), mapped by `coff_reloc_type` to `IMAGE_REL_AMD64_SECREL = 0x000Bu16` (32-bit unsigned/signed offset of the target TLS symbol from the beginning of the `.tls` section).
2. **x86-64 instruction selection & encoding (`compiler/target/x64/isel.ax`, `encode.ax`)**:
   - On Windows x64, `gs:[0x58]` holds `TEB.ThreadLocalStoragePointer` (`*const *mut u8`), an array of per-module TLS block pointers indexed by the module's `_tls_index: u32`.
   - To compute the address of `@thread_local` symbol `sym` into destination register `r_dst`:
     ```text
     mov     r_tmp, qword ptr gs:[0x58]           ; 65 48 8B 04 25 58 00 00 00 (for RAX)
     mov     r_idx32, dword ptr [rip + _tls_index]; 8B 0D <disp32: IMAGE_REL_AMD64_REL32(_tls_index)>
     mov     r_base, qword ptr [r_tmp + r_idx*8]  ; 48 8B 04 C8
     lea     r_dst, [r_base + sym@SECREL32]       ; 48 8D 80 <disp32: IMAGE_REL_AMD64_SECREL(sym)>
     ```
     (In a standalone `.exe` where `_tls_index` is guaranteed to be `0` or resolved through `_tls_index`, loading `[rip + _tls_index]` works uniformly across both `.exe` and `.dll` images.)
3. **PE32+ linker `.tls` merging and `IMAGE_TLS_DIRECTORY64` (`compiler/link/pe.ax`)**:
   - When the PE linker (`compiler/link/pe.ax` / `linker.ax`) encounters any input `.tls` or `.tls$` section:
     - It merges all `.tls` / `.tls$` raw data in deterministic input order into the output `.tls` section at RVA `tls_rva` of size `tls_size`.
     - It resolves every `IMAGE_REL_AMD64_SECREL` (`0x000B`) relocation against symbol `S` to the 32-bit offset `(S.rva - tls_rva)`.
     - It synthesizes `_tls_index` (4-byte zero-initialized slot in `.data`) and `_tls_callbacks` (8-byte zero terminator `0u64` in `.rdata`), and emits the 40-byte `IMAGE_TLS_DIRECTORY64` table (`_tls_used`) in `.rdata`:
       | Offset | Field | Size | Value |
       |---|---|---|---|
       | `0` | `StartAddressOfRawData` | `u64` | `image_base + (tls_rva as u64)` |
       | `8` | `EndAddressOfRawData` | `u64` | `image_base + ((tls_rva + tls_size) as u64)` |
       | `16` | `AddressOfIndex` | `u64` | `image_base + (tls_index_rva as u64)` |
       | `24` | `AddressOfCallBacks` | `u64` | `image_base + (tls_callbacks_rva as u64)` |
       | `32` | `SizeOfZeroFill` | `u32` | `0u32` |
       | `36` | `Characteristics` | `u32` | `IMAGE_SCN_ALIGN_8BYTES` (`0x00400000u32`) |
     - It sets `OptionalHeader.DataDirectory[PE_DIR_TLS]` (`PE_DIR_TLS = 9`) to `PeDataDirectory { virtual_address: tls_dir_rva, size: 40u32 }`. When the Windows loader creates each OS thread (`CreateThread` or process startup), the loader automatically allocates a fresh copy of `[StartAddressOfRawData, EndAddressOfRawData)` and stores its pointer at `(*(gs:[0x58]))[_tls_index]`.

**AXS-SYNC-024** (MIR interpreter oracle per-thread TLS isolation; `T413`, `compiler/interp/interp.ax`).
1. In `compiler/interp/interp.ax`, each logical thread `t` holds a private `tls_slots` map from `SymbolId` / `DefId` (for `@thread_local static` items) and `u32` key ID (for `LocalKey<T>`) to a thread-private allocation ID `alloc_id`.
2. When thread `t` evaluates a `@thread_local static` place for the first time, the interpreter allocates a fresh block of `size_of<T>()` bytes tagged with `owner_thread = t.tid`, copies the static item's constant initializer bytes into it, and caches `alloc_id` in `t.tls_slots`.
3. Subsequent reads and writes to that `@thread_local` symbol on thread `t` access `t`'s private `alloc_id` while thread `t' != t` accesses its own disjoint `alloc_id'`. When thread `t` exits, all allocations in `t.tls_slots` are marked freed (after running `LocalKey<T>` destructors per `AXS-SYNC-021(3)`), so any dangling raw pointer to `t`'s TLS dereferenced by another thread triggers `AX_UNSAFE_INTERP_UB` deterministically.


---

## 4. Reference Counting & Synchronization Primitives (`std.sync`: `Rc`, `Arc`, `Weak`, `Mutex`, `RwLock`, `Condvar`, `Once`, `OnceCell`, `Barrier`)

**AXS-SYNC-030** (`Rc<T>`, `Arc<T>`, and `Weak<T>` reference counting, `Send`/`Share` conditional auto-traits, and memory-ordering contracts; `T411`, `REQ-CONC-070`, `REQ-CONC-071`, `SPEC-30 AXS-CONC-004, AXS-CONC-005`, `0136 §61–62, ACONC-83`, `0209 §1–32, AARC-01..55`, `tasks/0623 §19–22`).
1. **Single-threaded `Rc<T>` (`std/sync/rc.ax`, re-exported by `std.sync`)**:
   - `Rc<T>` provides heap-allocated shared ownership within a single execution context using non-atomic strong/weak reference counts (`AARC-10..11`).
   - **Auto-trait bounds (`REQ-CONC-070`, `SPEC-30 AXS-CONC-004`)**:
     ```axiom
     impl<T> !Send for Rc<T> {}
     impl<T> !Share for Rc<T> {}
     ```
     Because `Rc<T>` mutates its control block without atomic synchronization, `Rc<T>` is unconditionally `!Send` and `!Share` regardless of `T`. Passing `Rc<T>` or `view<Rc<T>>` across `spawn`, `scope.spawn`, or channel `send` is rejected at compile time with `AX_CONC_NOT_SEND` / `AX_CONC_NOT_SHARE` (`AARC-11`).
   - **Move-only handle (`!Copy`, `Clone`)**: `Rc<T>` is `!Copy` (`AARC-03`); duplicating an `Rc<T>` requires an explicit `.clone()` call (`AARC-03`).
   - **Surface API**:
     - `pub fn rc_new<T>(val: T) -> Rc<T>` (and `Rc.new(val: T) -> Rc<T>`)
     - `pub fn clone(self: view<Rc<T>>) -> Rc<T>`
     - `pub fn get_view(self: view<Rc<T>>) -> view<T>`: Grants shared read-only `view<T>` access (`AARC-23`). Safe code NEVER obtains a `mut_view<T>` from `Rc<T>` while `strong_count > 1` (`AARC-07`).
     - `pub fn get_mut(self: mut_view<Rc<T>>) -> Option<mut_view<T>>`: Returns `Option.Some(mut_view(payload))` if and only if `strong_count == 1` and `weak_count == 0`, and `Option.None` otherwise (`AARC-25`).
     - `pub fn strong_count(self: view<Rc<T>>) -> usize`
2. **Thread-safe `Arc<T>` and `Weak<T>` (`std/sync/arc.ax`, re-exported by `std.sync`)**:
   - `Arc<T>` provides thread-safe shared ownership backed by a single heap control block (`ArcInner<T>`) holding `strong: Atomic<usize>`, `weak: Atomic<usize>`, and the inline payload `data: T` (`AARC-20..21`).
   - **Conditional auto-trait bounds (`REQ-CONC-070`, `REQ-CONC-071`, `SPEC-30 AXS-CONC-005`, `ACONC-83`, `AARC-12..13`)**:
     ```axiom
     impl<T: Send + Share> Send for Arc<T> {}
     impl<T: Send + Share> Share for Arc<T> {}
     impl<T: Send + Share> Send for Weak<T> {}
     impl<T: Send + Share> Share for Weak<T> {}
     ```
     - **Why both `T: Send` and `T: Share` are required**: Multiple threads holding cloned `Arc<T>` handles concurrently obtain `view<T>` to the same payload (`requiring T: Share`), and the arbitrary last thread to drop its `Arc<T>` takes exclusive ownership to run `Drop.drop` on `T` (`requiring T: Send`, `REQ-CONC-071`).
     - If `T` is `Send` but `!Share` (for example `Cell<i32>` or `RefCell<i32>`), `Arc<T>` is **neither `Send` nor `Share`** (`AARC-12`). To share mutable state across threads through `Arc`, the payload MUST be wrapped in a thread-safe interior-mutability primitive such as `Arc<Mutex<T>>` or `Arc<RwLock<T>>` (`REQ-CONC-105`, `AARC-07`, `AARC-13`).
   - **Atomic reference-count ordering protocol (`AARC-20..22`, `AARC-30..31`, `SPEC-31 AXS-ATOM-022`)**:
     - `Arc.new(val: T) -> Arc<T>`: Allocates `ArcInner<T>` with `strong = Atomic.new(1usize)` and `weak = Atomic.new(1usize)` (the implicit collective weak reference representing all strong references).
     - `Arc.clone(self: view<Arc<T>>) -> Arc<T>`: Increments `strong` with `fetch_add(1usize, Ordering.Relaxed)` (`Relaxed` suffices because the caller already holds a live `Arc<T>` whose creation happened-before the clone; overflow past `isize.MAX as usize` aborts immediately).
     - `Arc.drop(self: mut_view<Arc<T>>)`: Decrements `strong` with `fetch_sub(1usize, Ordering.Release)`. If the previous count was `> 1`, `drop` returns immediately. If the previous count was `1` (this thread was the last strong owner):
       1. Execute `fence(Ordering.Acquire)` (or use `Ordering.AcqRel` on the `fetch_sub`) so that all reads and writes performed via `view<T>` on every other thread before their `Release` decrements **Happen-Before** `T`'s destructor on this thread (`AARC-22`, `SPEC-31 AXS-ATOM-022`).
       2. Run `drop_in_place<T>(&mut inner.data)`.
       3. Decrement the collective weak reference (`weak.fetch_sub(1usize, Ordering.Release)` + `Acquire` fence on `1 -> 0`) and deallocate the `ArcInner<T>` allocation if `weak` reaches `0`.
     - `Arc.downgrade(self: view<Arc<T>>) -> Weak<T>`: Atomically increments `weak` (`Ordering.Relaxed`) and returns a `Weak<T>` handle that does not keep `T` alive (`AARC-30`).
     - `Weak.upgrade(self: view<Weak<T>>) -> Option<Arc<T>>`: Uses a `compare_exchange_weak` loop (`Ordering.Acquire` on success, `Ordering.Relaxed` on failure) to increment `strong` if and only if `strong > 0`. If `strong == 0`, returns `Option.None` (`AARC-31`).
     - `Arc.get_view(self: view<Arc<T>>) -> view<T>`, `Arc.get_mut(self: mut_view<Arc<T>>) -> Option<mut_view<T>>` (succeeds via `Ordering.Acquire` check only when `strong == 1` and `weak == 1`, `AARC-25`), `Arc.strong_count(self: view<Arc<T>>) -> usize`, `Arc.weak_count(self: view<Arc<T>>) -> usize`.

**AXS-SYNC-031** (`Mutex<T>` and `MutexGuard<T>` mutual exclusion, guard-bound capability lifetimes, and lock-to-unlock `Happens-Before`; `T411`, `REQ-CONC-010`, `REQ-CONC-015`, `REQ-CONC-044`, `REQ-CONC-045`, `REQ-CONC-047`, `REQ-CONC-105`, `REQ-CONC-106`, `REQ-CONC-180`, `SPEC-30 AXS-CONC-005, AXS-CONC-015, AXS-CONC-034`, `0136 §63–67, ACONC-84..85`, `0206 §1–13, ASYNC-PRIM-01..23`, `tasks/0623 §23–25`).
1. **Payload-carrying container (`ASYNC-PRIM-03`, `REQ-CONC-105`)**:
   - `Mutex<T>` owns its protected payload `T` directly inside the lock allocation (`Mutex<T>` is a data-carrying container, never an unassociated raw lock). Safe code cannot touch `T` without first acquiring a `MutexGuard<T>` (`ASYNC-PRIM-03`, `REQ-CONC-010`).
2. **Conditional auto-trait bounds (`REQ-CONC-105`, `REQ-CONC-106`, `SPEC-30 AXS-CONC-005`, `ACONC-84`)**:
   ```axiom
   impl<T: Send> Send for Mutex<T> {}
   impl<T: Send> Share for Mutex<T> {}
   impl<T> !Copy for Mutex<T> {}

   impl<T> !Copy for MutexGuard<T> {}
   impl<T> !Send for MutexGuard<T> {}
   impl<T: Share> Share for MutexGuard<T> {}
   ```
   - `Mutex<T>` is `Send` and `Share` if and only if `T: Send` (`REQ-CONC-105`, `REQ-CONC-106`). Because `Mutex<T>` serializes all access so only one thread holds `mut_view<T>` at a time, `T` does **not** need to be `Share` for `Mutex<T>` to be `Share`, but `T` MUST be `Send` because different threads effectively pass exclusive access to `T` from one lock holder to the next (`REQ-CONC-106`).
   - `MutexGuard<T>` is unconditionally **`!Copy`** and **`!Send`** (`REQ-CONC-044`, `SPEC-30 AXS-CONC-004`): a lock guard MUST be unlocked on the same OS thread that acquired it and MUST NEVER be transferred across thread boundaries or held across an async `.await` suspension point (`REQ-CONC-015`, `SPEC-30 AXS-CONC-034`, `AX_CONC_AWAIT_HOLD_NON_SEND` / `AX_CONC_GUARD_ESCAPE`).
3. **Surface API (`std/sync/mutex.ax`, re-exported by `std.sync`)**:
   - `pub fn mutex_new<T>(val: T) -> Mutex<T>` (and `Mutex.new(val: T) -> Mutex<T>`)
   - `pub fn lock(self: view<Mutex<T>>) -> MutexGuard<T>`: Blocks the calling thread until exclusive ownership of the lock is acquired with `Acquire` ordering, then returns `MutexGuard<T>` (`REQ-CONC-044`).
   - `pub fn try_lock(self: view<Mutex<T>>) -> Option<MutexGuard<T>>`: Attempts a non-blocking acquisition (`compare_exchange(UNLOCKED, LOCKED, Ordering.Acquire, Ordering.Relaxed)`). Returns `Option.Some(guard)` on success or `Option.None` immediately if the lock is currently held (`ASYNC-PRIM-12`).
   - `pub fn into_inner(self: Mutex<T>) -> T`: Consumes the `Mutex<T>` by value (when exclusively owned, so no other thread or borrow can hold it) and returns `T` without locking overhead.
   - `MutexGuard.get(self: view<MutexGuard<T>>) -> view<T>` and `MutexGuard.get_mut(self: mut_view<MutexGuard<T>>) -> mut_view<T>`: Grant scoped shared or exclusive access to the protected payload (`REQ-CONC-010`, `REQ-CONC-045`).
   - `impl<T> Drop for MutexGuard<T>`: Releases the lock with `Release` ordering (`REQ-CONC-045`, `REQ-CONC-180`) and wakes one waiting thread via `host.futex_wake(&self.mutex.state, 1u32)` if the lock state indicates contended waiters.
4. **Guard-bound capability lifetime and non-escape (`REQ-CONC-010`, `REQ-CONC-044`, `REQ-CONC-045`, `REQ-CONC-047`, `ACONC-85`)**:
   - Any `view<T>` or `mut_view<T>` obtained via `guard.get()` or `guard.get_mut()` is region-bound to the lifetime of `guard` (`REQ-CONC-045`).
   - Dropping `guard` (either explicitly via `drop(guard)` or at the end of its lexical block) immediately invalidates all views derived from `guard` (`REQ-CONC-045`).
   - Any attempt to return `MutexGuard<T>` or a view derived from `MutexGuard<T>` out of the scope of the borrowed `Mutex<T>`, store it in an outer structure, or use a derived view after `guard` is dropped is rejected at compile time with `AX_CONC_GUARD_ESCAPE` or `AX_CAP_USE_AFTER_MOVE` (`REQ-CONC-047`).
5. **Lock-to-unlock `Happens-Before` (`REQ-CONC-180`, `SPEC-30 AXS-CONC-015`, `ASYNC-PRIM-10`)**:
   - Unlocking a `Mutex<T>` (`MutexGuard.drop`) performs a `Release` operation on the lock state; the subsequent successful `lock()` or `try_lock()` on the same `Mutex<T>` performs an `Acquire` operation that reads from the `Release` sequence (`REQ-CONC-180`). Therefore, all mutations to `T` (and any other memory operations) before `drop(guard)` on thread $A$ **Happen-Before** all reads and writes after `lock()` returns on thread $B$.
6. **Non-reentrant & non-poisoning policy (`REQ-CONC-123`, `0206 §13`, `tasks/0623 §25`)**:
   - `Mutex<T>` is **non-reentrant**: attempting to call `mutex.lock()` on the same thread while a `MutexGuard<T>` for the same `Mutex<T>` is already live on the call stack deadlocks (or panics under debug/oracle deadlock detection).
   - Because `MutexGuard<T>` is `!Send` and Axiom enforces panic isolation at task/thread boundaries (`AXS-SYNC-014`), Core `Mutex.lock()` returns `MutexGuard<T>` directly without a Rust-style `PoisonError` wrapper (`0206 §13`, `tasks/0623 §25`).
7. **Three-state futex implementation (`std/sync/mutex.ax`, `T411`)**:
   - `Mutex<T>` stores `state: Atomic<u32>` with states `0u32` (`UNLOCKED`), `1u32` (`LOCKED_UNCONTENDED`), and `2u32` (`LOCKED_CONTENDED`).
   - Uncontended `lock()` executes a single `state.compare_exchange(0u32, 1u32, Ordering.Acquire, Ordering.Relaxed)` in user space with zero kernel transitions. Only on contention does `lock()` transition `state` to `2u32` and sleep in `host.futex_wait(&self.state, 2u32, -1i64)`. Uncontended `drop()` executes `state.swap(0u32, Ordering.Release)` and only calls `host.futex_wake(&self.state, 1u32)` if the previous state was `2u32`.

**AXS-SYNC-032** (`RwLock<T>`, `RwLockReadGuard<T>`, and `RwLockWriteGuard<T>` shared-read / exclusive-write semantics; `T411`, `REQ-CONC-010`, `REQ-CONC-046`, `REQ-CONC-047`, `SPEC-30 AXS-CONC-005`, `0136 §63–67`, `0206 §14–21, ASYNC-PRIM-20..23`, `tasks/0623 §26–27`).
1. **Conditional auto-trait bounds (`SPEC-30 AXS-CONC-005`, `0206 §17`)**:
   ```axiom
   impl<T: Send> Send for RwLock<T> {}
   impl<T: Send + Share> Share for RwLock<T> {}
   impl<T> !Copy for RwLock<T> {}

   impl<T> !Copy for RwLockReadGuard<T> {}
   impl<T> !Send for RwLockReadGuard<T> {}
   impl<T: Share> Share for RwLockReadGuard<T> {}

   impl<T> !Copy for RwLockWriteGuard<T> {}
   impl<T> !Send for RwLockWriteGuard<T> {}
   impl<T: Share> Share for RwLockWriteGuard<T> {}
   ```
   - **Why `RwLock<T>: Share` requires `T: Send + Share`**: Unlike `Mutex<T>`, `RwLock<T>.read()` allows multiple threads to hold `RwLockReadGuard<T>` simultaneously and obtain concurrent `view<T>` references to `T` (`requiring T: Share`), while `RwLock<T>.write()` transfers exclusive `mut_view<T>` access between threads (`requiring T: Send`).
2. **Surface API (`std/sync/rwlock.ax`, re-exported by `std.sync`)**:
   - `pub fn rwlock_new<T>(val: T) -> RwLock<T>` (and `RwLock.new(val: T) -> RwLock<T>`)
   - `pub fn read(self: view<RwLock<T>>) -> RwLockReadGuard<T>`: Acquires shared read access (`Acquire` ordering). Multiple readers may hold `RwLockReadGuard<T>` concurrently when no writer holds the lock (`REQ-CONC-046`).
   - `pub fn try_read(self: view<RwLock<T>>) -> Option<RwLockReadGuard<T>>`
   - `pub fn write(self: view<RwLock<T>>) -> RwLockWriteGuard<T>`: Acquires exclusive write access (`Acquire` ordering), waiting until all active readers and any active writer release their guards (`REQ-CONC-046`). To prevent writer starvation under continuous reader arrival, `write()` sets a writer-pending bit in the lock state word that blocks new incoming `read()` calls until the pending writer completes (`0206 §19`).
   - `pub fn try_write(self: view<RwLock<T>>) -> Option<RwLockWriteGuard<T>>`
   - `RwLockReadGuard.get(self: view<RwLockReadGuard<T>>) -> view<T>`: Grants shared read-only `view<T>` bound to the read guard's lifetime (`REQ-CONC-046`, `REQ-CONC-047`).
   - `RwLockWriteGuard.get(self: view<RwLockWriteGuard<T>>) -> view<T>` and `RwLockWriteGuard.get_mut(self: mut_view<RwLockWriteGuard<T>>) -> mut_view<T>`: Grant shared or exclusive access bound to the write guard's lifetime (`REQ-CONC-046`, `REQ-CONC-047`).
   - `Drop` on `RwLockReadGuard<T>` and `RwLockWriteGuard<T>` releases the lock with `Release` ordering (`ASYNC-PRIM-23`), establishing a `Happens-Before` edge from every write guard unlock to subsequent read or write guard acquisitions, and from every read guard unlock to subsequent write guard acquisitions.

**AXS-SYNC-033** (`Condvar` condition variable wait/notify protocol and predicate-loop contract; `T411`, `0136 §68`, `0206 §22–28, ASYNC-PRIM-30..32`, `tasks/0623 §28`).
1. **Type and auto-traits (`std/sync/condvar.ax`, re-exported by `std.sync`)**:
   ```axiom
   pub struct Condvar {
       seq: Atomic<u32>,
   }
   impl Send for Condvar {}
   impl Share for Condvar {}
   impl !Copy for Condvar {}
   ```
2. **Surface API**:
   - `pub fn condvar_new() -> Condvar` (and `Condvar.new() -> Condvar`)
   - `pub fn wait<T>(self: view<Condvar>, guard: MutexGuard<T>) -> MutexGuard<T>`:
     1. Snapshots `seq_val = self.seq.load(Ordering.Relaxed)` while still holding `guard`.
     2. Atomically unlocks `guard`'s underlying `Mutex<T>` (`Release` ordering) and blocks in `host.futex_wait(&self.seq, seq_val, -1i64)`.
     3. Upon wakeup, reacquires the `Mutex<T>` (`Acquire` ordering) before returning the restored `MutexGuard<T>` (`ASYNC-PRIM-30`).
   - `pub fn wait_timeout_ms<T>(self: view<Condvar>, guard: MutexGuard<T>, timeout_ms: u64) -> CondvarWaitResult<T>`: Same unlock-wait-relock protocol using `timeout_ns = (timeout_ms as i64) * 1_000_000i64`, returning `CondvarWaitResult { guard: MutexGuard<T>, timed_out: bool }`.
   - `pub fn notify_one(self: view<Condvar>)`: Increments `self.seq.fetch_add(1u32, Ordering.Release)` and calls `host.futex_wake(&self.seq, 1u32)`.
   - `pub fn notify_all(self: view<Condvar>)`: Increments `self.seq.fetch_add(1u32, Ordering.Release)` and calls `host.futex_wake(&self.seq, 0x7FFF_FFFFu32)`.
3. **Mandatory predicate loop (`ASYNC-PRIM-31`)**: Underlying OS wait primitives (`WaitOnAddress`, `futex`) and concurrent notifications permit spurious wakeups. Callers MUST always invoke `Condvar.wait` inside a predicate loop inspecting the state protected by the `MutexGuard<T>`:
   ```axiom
   let mut guard = mtx.lock()
   while !(*guard.get()).ready {
       guard = cv.wait(guard)
   }
   ```

**AXS-SYNC-034** (`Once` and `OnceCell<T>` one-time initialization and happens-before publication; `T411`, `SPEC-30 AXS-CONC-015`, `0136 §69`, `0206 §29–35, ASYNC-PRIM-40..43`, `tasks/0623 §29`).
1. **`Once` (`std/sync/once.ax`, re-exported by `std.sync`)**:
   - State machine over `state: Atomic<u32>` with states `0u32` (`INCOMPLETE`), `1u32` (`RUNNING`), `2u32` (`COMPLETE`).
   - `Once.new() -> Once` (`const`-constructible so `Once` can be placed in a `static` item).
   - `Once.call_once<F>(self: view<Once>, f: F) where F: FnOnce()`:
     - Fast path: `if self.state.load(Ordering.Acquire) == 2u32 { return }`.
     - Contended path: The first thread to win `compare_exchange(0u32, 1u32, Ordering.Acquire, Ordering.Acquire)` runs `f()`, stores `2u32` with `Ordering.Release`, and calls `host.futex_wake(&self.state, 0x7FFF_FFFFu32)`. Concurrent callers seeing `1u32` wait in `host.futex_wait(&self.state, 1u32, -1i64)` until `state == 2u32` is observed with `Ordering.Acquire`.
     - **Publication guarantee (`ASYNC-PRIM-41`)**: All memory writes performed inside `f()` by the initializing thread **Happen-Before** `call_once()` returns on any thread (`Ordering.Release` on completion pairs with `Ordering.Acquire` on every observer).
   - `Once.is_completed(self: view<Once>) -> bool`: Returns `self.state.load(Ordering.Acquire) == 2u32`.
2. **`OnceCell<T>` (`std/sync/once.ax`, re-exported by `std.sync`)**:
   - Thread-safe write-once cell owning an optional initialized payload `T`:
     ```axiom
     impl<T: Send> Send for OnceCell<T> {}
     impl<T: Send + Share> Share for OnceCell<T> {}
     impl<T> !Copy for OnceCell<T> {}
     ```
   - `OnceCell.new() -> OnceCell<T>`: Creates an uninitialized cell.
   - `OnceCell.get(self: view<OnceCell<T>>) -> Option<view<T>>`: Loads initialization state with `Ordering.Acquire`; if `COMPLETE`, returns `Option.Some(view(payload))` bound to `self`'s lifetime, otherwise `Option.None`.
   - `OnceCell.set(self: view<OnceCell<T>>, val: T) -> Result<(), T>`: Atomically initializes the cell if uninitialized (returning `Result.Ok(())`), or returns ownership of the rejected value in `Result.Err(val)` if another thread already initialized it (`ASYNC-PRIM-42`).
   - `OnceCell.get_or_init<F>(self: view<OnceCell<T>>, init: F) -> view<T> where F: FnOnce() -> T`: Runs `init()` at most once across all racing threads and returns `view<T>` to the initialized value.
   - `OnceCell.into_inner(self: OnceCell<T>) -> Option<T>` and `Drop`: Runs `T`'s destructor if and only if the cell reached the `COMPLETE` state (`ASYNC-PRIM-43`).

**AXS-SYNC-035** (`Barrier` reusable multi-thread rendezvous and all-to-all `Happens-Before`; `T411`, `SPEC-30 AXS-CONC-015`, `0206 §36–40, ASYNC-PRIM-50..52`, `tasks/0623 §30`).
1. **Type and auto-traits (`std/sync/barrier.ax`, re-exported by `std.sync`)**:
   ```axiom
   pub struct BarrierWaitResult {
       is_leader: bool,
   }
   impl Copy for BarrierWaitResult {}
   impl Send for Barrier {}
   impl Share for Barrier {}
   impl !Copy for Barrier {}
   ```
2. **Surface API & semantics**:
   - `pub fn barrier_new(count: usize) -> Barrier` (and `Barrier.new(count: usize) -> Barrier`, panicking if `count == 0`): Configures a rendezvous barrier for `count` participating threads.
   - `pub fn wait(self: view<Barrier>) -> BarrierWaitResult`:
     - Uses a generation counter (`generation: Atomic<u32>`) paired with an arrival counter under an internal lock/atomic word so the same `Barrier` can be reused across back-to-back phases without ABA wakeups (`ASYNC-PRIM-51`).
     - The first `count - 1` arriving threads block on the current generation via `host.futex_wait`.
     - The `count`-th arriving thread resets the arrival counter to `0`, advances `generation` with `Ordering.Release`, wakes all `count - 1` waiting threads via `host.futex_wake`, and returns `BarrierWaitResult { is_leader: true }`. All other `count - 1` threads return `BarrierWaitResult { is_leader: false }` (`ASYNC-PRIM-52`).
   - **All-to-all `Happens-Before` (`ASYNC-PRIM-50`)**: For every pair of participating threads $(A, B)$ in the same barrier generation, everything before `barrier.wait()` on thread $A$ **Happens-Before** everything after `barrier.wait()` returns on thread $B$.

---

## 5. Ownership-Transferring Channels (`std.sync.channel`: Bounded & Unbounded)

**AXS-SYNC-040** (Move-only ownership transfer boundary across channels; `T412`, `REQ-CONC-007`, `REQ-CONC-011`, `REQ-CONC-041`, `REQ-CONC-042`, `REQ-CONC-099`, `REQ-CONC-104`, `REQ-CONC-143`, `REQ-CONC-185`, `REQ-CONC-186`, `SPEC-30 AXS-CONC-004, AXS-CONC-005`, `0126 §11`, `0136 §70–77, ACONC-65..67, ACONC-86`, `0207 §1–22, ACHAN-01..40`, `tasks/0621 §1–40`).
1. **Channels as primary inter-context communication (`REQ-CONC-007`, `REQ-CONC-099`, `ACHAN-01`)**:
   - Channels in `std.sync.channel` (`std/sync/channel.ax`, re-exported by `std.sync`) provide typed, ownership-transferring message passing between threads and tasks without requiring user-managed locks around message payloads.
2. **Mandatory `T: Send` and move-by-value transfer (`REQ-CONC-011`, `REQ-CONC-041`, `REQ-CONC-042`, `REQ-CONC-104`, `REQ-CONC-143`, `REQ-CONC-186`)**:
   - Every channel constructor and endpoint requires `T: Send` (`REQ-CONC-104`, `REQ-CONC-186`). Attempting to instantiate a channel with a `!Send` type (such as `Rc<i32>`, `MutexGuard<i32>`, or a borrowed `view<T>`) is rejected at compile time with `AX_CONC_NOT_SEND`.
   - Note that `T` does **not** need to implement `Share` (`T: Send` alone is sufficient, e.g. `Box<Buffer>` or `Vec<u8>`), because sending a message moves exclusive ownership from the sender to a single receiving consumer (`REQ-CONC-041`, `REQ-CONC-186`).
   - **Sender loses access on `send` (`REQ-CONC-011`, `REQ-CONC-041`, `REQ-CONC-042`, `REQ-CONC-143`, `ACHAN-04`)**: `Sender.send(self: view<Sender<T>>, msg: T)` and `UnboundedSender.send(self: view<UnboundedSender<T>>, msg: T)` consume `msg: T` **by value**. For any move-only (`!Copy`) type `T`, the ownership and capability checker (`compiler/own/moveck.ax`, `cap.ax`) transitions the caller's binding to `Moved` at the `send` call site and forbids any active `view<T>` or `mut_view<T>` borrow of `msg` from surviving past `send` (`AX_OWN_USE_AFTER_MOVE`, `AX_CAP_BORROW_CONFLICT`).

**AXS-SYNC-041** (Canonical channel types, constructors, and capacity contracts; `T412`, `REQ-CONC-099`, `REQ-CONC-103`, `REQ-CONC-104`, `0207 §5–16, ACHAN-10..25`, `tasks/0621 §5–25`).
`std/sync/channel.ax` defines explicit bounded and unbounded channel pairs (`REQ-CONC-103`):
```axiom
module std.sync.channel

pub struct Sender<T: Send> { ... }
pub struct Receiver<T: Send> { ... }

pub struct UnboundedSender<T: Send> { ... }
pub struct UnboundedReceiver<T: Send> { ... }

pub struct SendError<T> {
    pub val: T,
}

pub enum TrySendError<T> {
    Full(T),
    Disconnected(T),
}

pub enum RecvError {
    Disconnected,
}

pub enum TryRecvError {
    Empty,
    Disconnected,
}

pub fn channel_bounded<T: Send>(capacity: usize) -> (Sender<T>, Receiver<T>)
pub fn channel_unbounded<T: Send>() -> (UnboundedSender<T>, UnboundedReceiver<T>)
```
1. **Explicit bounded vs unbounded selection (`REQ-CONC-103`, `ACHAN-10..12`)**:
   - The type system and constructor names distinguish bounded channels (`channel_bounded<T>(capacity)`, backpressure-enforcing fixed capacity) from unbounded channels (`channel_unbounded<T>()`, dynamically growing queue limited only by allocator capacity) so resource bounds are explicit in signatures and call sites (`REQ-CONC-103`).
   - `channel_bounded<T>(capacity)` requires `capacity >= 1usize` (panicking at construction if `capacity == 0usize`; zero-capacity rendezvous handoff is reserved for explicit rendezvous primitives, keeping ring-buffer indexing invariant-clean in `T412`).

**AXS-SYNC-042** (SPSC, MPSC, and MPMC topologies and endpoint auto-traits; `T412`, `REQ-CONC-099`, `REQ-CONC-104`, `0207 §17–20, ACHAN-15..19`, `tasks/0621 §15–20`).
1. **Auto-trait and copy/clone rules**:
   ```axiom
   impl<T: Send> Send for Sender<T> {}
   impl<T: Send> Share for Sender<T> {}
   impl<T: Send> !Copy for Sender<T> {}
   impl<T: Send> Clone for Sender<T> { ... }

   impl<T: Send> Send for Receiver<T> {}
   impl<T: Send> Share for Receiver<T> {}
   impl<T: Send> !Copy for Receiver<T> {}
   impl<T: Send> Clone for Receiver<T> { ... }
   ```
   (Identical `Send`, `Share`, `!Copy`, and `Clone` implementations hold for `UnboundedSender<T>` and `UnboundedReceiver<T>`.)
2. **Supported topologies (`ACHAN-15..19`)**:
   - **SPSC (Single-Producer Single-Consumer)**: Created directly by `channel_bounded` / `channel_unbounded` when neither `Sender` nor `Receiver` is cloned.
   - **MPSC (Multi-Producer Single-Consumer)**: Obtained by calling `sender.clone()` to distribute `Sender<T>` handles across multiple producer threads while keeping a single `Receiver<T>`. The internal channel state maintains an atomic `sender_count: usize`.
   - **MPMC (Multi-Producer Multi-Consumer)**: Obtained by also calling `receiver.clone()` to distribute `Receiver<T>` handles across multiple worker threads (`receiver_count: usize`).
3. **Single-consumer delivery invariant (`ACHAN-18`, `REQ-CONC-041`)**: Even in MPMC mode with multiple cloned `Receiver<T>` handles, each sent message `msg: T` is dequeued and owned by **at most one** consumer call (`recv` or `try_recv`). Messages are never implicitly cloned or broadcast across consumers.

**AXS-SYNC-043** (`send`, `try_send`, `recv`, `try_recv`, and `close` state machine and zero ownership ambiguity on error; `T412`, `REQ-CONC-115`, `REQ-CONC-116`, `0136 §74–76, ACONC-67`, `0207 §21–32, ACHAN-20..35`, `tasks/0621 §21–35`).
1. **Bounded `Sender<T>` operations**:
   - `Sender.send(self: view<Sender<T>>, msg: T) -> Result<(), SendError<T>>`:
     - If the channel is closed (`closed == true` or `receiver_count == 0`), does **not** enqueue `msg`; returns `Result.Err(SendError { val: msg })` immediately, returning full ownership of `msg` to the caller (`REQ-CONC-115`, `REQ-CONC-116`).
     - If the bounded ring buffer has `len < capacity`, moves `msg` into the tail slot, increments `len`, wakes one blocked receiver via `not_empty` condition/futex, and returns `Result.Ok(())`.
     - If `len == capacity` and the channel is open, blocks the calling producer on `not_full` until either a receiver dequeues an item ( freeing a slot) or the channel closes. If the channel closes while the producer is waiting, `send` wakes up and returns `Result.Err(SendError { val: msg })` without dropping or duplicating `msg` (`REQ-CONC-116`).
   - `Sender.try_send(self: view<Sender<T>>, msg: T) -> Result<(), TrySendError<T>>`:
     - Non-blocking: if closed (`receiver_count == 0` or `closed`), returns `Result.Err(TrySendError.Disconnected(msg))`; if `len == capacity`, returns `Result.Err(TrySendError.Full(msg))`; otherwise enqueues `msg` and returns `Result.Ok(())` (`REQ-CONC-115`, `REQ-CONC-116`).
2. **Unbounded `UnboundedSender<T>` operations**:
   - `UnboundedSender.send(self: view<UnboundedSender<T>>, msg: T) -> Result<(), SendError<T>>` and `try_send(self: view<UnboundedSender<T>>, msg: T) -> Result<(), TrySendError<T>>`:
     - Never block on capacity (never return `TrySendError.Full`). If closed (`receiver_count == 0` or `closed`), return `Result.Err(SendError { val: msg })` / `Result.Err(TrySendError.Disconnected(msg))` returning ownership of `msg`; otherwise append `msg` to the queue, wake one waiting receiver, and return `Result.Ok(())`.
3. **`Receiver<T>` and `UnboundedReceiver<T>` operations (`REQ-CONC-115`)**:
   - `recv(self: view<Receiver<T>>) -> Result<T, RecvError>`:
     - **Drain-before-disconnect rule (`ACHAN-26`)**: If the queue is non-empty (`len > 0`), `recv` ALWAYS dequeues the head item, wakes one blocked bounded sender (if any), and returns `Result.Ok(msg)`—**even if** all `Sender` handles have already been dropped or `close()` has been called.
     - If the queue is empty (`len == 0`) and `sender_count == 0` (or `closed == true`), `recv` immediately returns `Result.Err(RecvError.Disconnected)`.
     - If the queue is empty and `sender_count > 0` and `!closed`, `recv` blocks on `not_empty` until a message is enqueued or the last `Sender` drops / `close()` is called.
   - `try_recv(self: view<Receiver<T>>) -> Result<T, TryRecvError>`:
     - Non-blocking: if `len > 0`, dequeues and returns `Result.Ok(msg)`; else if `sender_count == 0` or `closed`, returns `Result.Err(TryRecvError.Disconnected)`; else returns `Result.Err(TryRecvError.Empty)`.
4. **Explicit `close()` and endpoint `Drop` (`REQ-CONC-115`, `ACHAN-25..28`)**:
   - `Sender.close(self: view<Sender<T>>)` / `Receiver.close(self: view<Receiver<T>>)`: Marks the channel closed for new sends (`closed = true`) and wakes all blocked senders and receivers via `notify_all()`. Already-buffered messages remain readable via `recv()` / `try_recv()` until the queue is drained (`ACHAN-26`).
   - `Drop` on `Sender<T>` / `UnboundedSender<T>`: Decrements `sender_count`. When `sender_count` transitions `1 -> 0`, sets `closed = true` and wakes all waiting receivers so no receiver can deadlock waiting on a dead producer set (`ACHAN-27`).
   - `Drop` on `Receiver<T>` / `UnboundedReceiver<T>`: Decrements `receiver_count`. When `receiver_count` transitions `1 -> 0`, sets `closed = true`, wakes all waiting bounded senders (which return `Err(SendError { val: msg })`), and **drains and drops all remaining buffered messages `T` in FIFO order** before releasing the queue memory (`REQ-CONC-116`, `ACHAN-28`).
5. **Exact ownership accounting invariant (`REQ-CONC-116`, `ACONC-67`, `ACHAN-30`)**:
   - For every value `v: T` passed into `send(v)` or `try_send(v)`, **exactly one** of the following three outcomes occurs across the execution:
     1. `v` is returned to a single consumer via `Ok(v)` from `recv()` or `try_recv()`;
     2. `v` is returned to the calling producer via `Err(SendError { val: v })` or `Err(TrySendError.Full(v) | TrySendError.Disconnected(v))`; or
     3. `v` was buffered in the channel when the last `Receiver` dropped and its destructor `Drop.drop(&mut v)` is executed exactly once during channel teardown.
   - Under no circumstance—including contention, timeout, channel closure, or thread cancellation—is `v` ever duplicated (double-dropped) or leaked without running `Drop` (`REQ-CONC-116`).

**AXS-SYNC-044** (Channel `Release`/`Acquire` `Happens-Before` and per-sender FIFO ordering; `T412`, `REQ-CONC-043`, `REQ-CONC-185`, `SPEC-30 AXS-CONC-015`, `0136 §73, ACONC-66`, `0207 §11–14, ACHAN-05..08`).
1. **Send-to-receive `Happens-Before` (`REQ-CONC-043`, `REQ-CONC-185`, `SPEC-30 AXS-CONC-015`, `ACONC-66`)**:
   - Enqueuing a message `m` via `send(m)` or `try_send(m)` performs a `Release` operation on the channel queue state, and dequeuing that message `m` via `recv()` or `try_recv()` performs an `Acquire` operation that observes that `Release` (`REQ-CONC-185`).
   - Consequently, all memory writes (including initializing the heap allocations owned by `m: T`) performed by the sending thread before `send(m)` **Happen-Before** the receiving thread's observation and mutation of `m` after `recv()` returns `Ok(m)` (`REQ-CONC-043`).
2. **Bounded slot-freed `Happens-Before` (`ACHAN-07`)**:
   - In a bounded channel of capacity $K$, the $i$-th dequeue (`recv`) **Happens-Before** the completion of the $(i + K)$-th enqueue (`send`).
3. **Per-sender FIFO ordering (`ACHAN-08`)**:
   - If a single producer thread sends message $m_1$ before message $m_2$ on the same channel (`send(m1)` sequenced-before `send(m2)`), $m_1$ is enqueued ahead of $m_2$ in the channel queue. When consumed by a single receiver, $m_1$ is always observed before $m_2$.

---

## 6. Diagnostics, Conformance Stress Scenarios & Canonical Examples

**AXS-SYNC-050** (Canonical diagnostic codes for threads, TLS, guards, and channels; `T410`, `T411`, `T412`, `T413`, `SPEC-30 AXS-CONC-042`, `spec/diagnostics.md AXD-021`).
Implementations of `SPEC-32` emit the following stable diagnostic codes registered in `spec/diagnostics.md`:

| Code | Severity | Category | Trigger Condition (`SPEC-32` Rule) |
|---|---|---|---|
| `AX_CONC_NOT_SEND` | `E` | `AX_CONC_*` | Capturing a `!Send` type (`Rc<T>`, `MutexGuard<T>`, `RwLockReadGuard<T>`, `RwLockWriteGuard<T>`, `LocalKey<T>`, `*const T`, `*mut T`) into `spawn` / `scope.spawn`, returning a `!Send` type from a spawned thread closure, or instantiating/sending a `!Send` type over `Sender<T>` / `Receiver<T>` (`AXS-SYNC-010`, `AXS-SYNC-030`, `AXS-SYNC-031`, `AXS-SYNC-040`). |
| `AX_CONC_NOT_SHARE` | `E` | `AX_CONC_*` | Sharing `view<T>` across thread boundaries where `T: !Share` (e.g., `Rc<T>`, `Cell<T>`, `LocalKey<T>`, or `Arc<T>` / `RwLock<T>` when `T: !Share`) (`AXS-SYNC-010`, `AXS-SYNC-030`, `AXS-SYNC-032`). |
| `AX_CONC_BORROW_ESCAPE_SPAWN` | `E` | `AX_CONC_*` | Capturing a non-`'static` `view<T>` or `mut_view<T>` into an unscoped `std.thread.spawn` closure, or capturing a borrow rooted inside a `std.thread.scope` body that does not outlive the `Scope` (`AXS-SYNC-010`, `AXS-SYNC-012`). |
| `AX_CONC_GUARD_ESCAPE` | `E` | `AX_CONC_*` | Returning a `MutexGuard<T>`, `RwLockReadGuard<T>`, `RwLockWriteGuard<T>`, or a `view<T>`/`mut_view<T>` derived from a guard out of the lexical scope of the guard/lock, or holding a guard across `.await` (`AXS-SYNC-031`, `AXS-SYNC-032`). |
| `AX_CONC_TLS_ESCAPE` | `E` | `AX_CONC_*` | Returning a `view<T>` or `mut_view<T>` rooted at a `@thread_local static` item or `LocalKey<T>.with` callback out of its lexical scope, storing a TLS view into a global/heap place, capturing a TLS view into `spawn`, or holding a TLS view across `.await` (`AXS-SYNC-020`, `AXS-SYNC-021`, `AXS-SYNC-022`). |
| `AX_TYPE_INVALID_TLS_DECL` | `E` | `AX_TYPE_*` | Attaching `@thread_local` to a non-`static` item (`fn`, `struct`, `enum`, `const`, `type`, or local `let`), or using a non-constant initializer on a `@thread_local static` item (`AXS-SYNC-022`). |
| `AX_CONC_UNSYNC_STATIC` | `E` | `AX_CONC_*` | Accessing a mutable `static` item without `@thread_local` or `Share`-safe synchronization (`Mutex<T>`, `OnceCell<T>`, `Atomic<T>`) in safe code (`SPEC-30 AXS-CONC-004`, `AXS-SYNC-020`). |

**AXS-SYNC-051** (Conformance & multi-threaded stress verification matrix; `T414`, `REQ-CONC-036`, `REQ-CONC-037`, `REQ-CONC-038`, `REQ-CONC-039`, `REQ-CONC-081`, `REQ-CONC-187`, `tasks/0837`).
The conformance and stress verification suite (`T414`, `tests/conformance/concurrency/`) MUST verify all five synchronization pillars under both the deterministic MIR interpreter oracle (`compiler/interp/interp.ax` + `oracle.ax`) and native `x86_64-windows` PE execution:
1. **Memory ordering & `Happens-Before` stress (`REQ-CONC-036`, `REQ-CONC-081`)**:
   - Store-buffering, message-passing, and release-sequence litmus tests across `Atomic<T>`, `Mutex<T>`, `RwLock<T>`, `Once`/`OnceCell<T>`, `Barrier`, `Condvar`, `JoinHandle.join()`, `scope()`, and `channel` `send`/`recv`, verifying zero stale reads and deterministic `Happens-Before` visibility under both the exhaustive DPOR/seed schedule explorer (`REQ-CONC-081`) and multi-core OS threads.
2. **Thread lifecycle, structured `scope`, panic containment & cancellation (`REQ-CONC-037`, `REQ-CONC-022`, `REQ-CONC-080`, `REQ-CONC-187`, `REQ-CONC-198`)**:
   - Multi-thread `spawn` + `join` return value propagation; structured `scope` borrowing stack `view<T>` across multiple readers and disjoint `mut_view<T>` slices across writers with mandatory join-before-return; child thread panic caught at `JoinHandle.join() -> Result.Err(PanicPayload)` without corrupting sibling threads; cooperative `CancelSource` / `CancelToken` shutdown running all stack and TLS `Drop` destructors.
3. **Channel SPSC / MPSC / MPMC stress & ownership accounting (`REQ-CONC-038`, `REQ-CONC-115`, `REQ-CONC-116`)**:
   - High-contention bounded (`capacity = 1`, `capacity = 8`) and unbounded SPSC, MPSC ($N$ producers $\to 1$ consumer), and MPMC ($N$ producers $\to M$ consumers) stress runs with move-only drop-tracked payloads (`DropCounter`), asserting that `constructed_count == received_count + returned_on_err_count + dropped_in_channel_count` and `double_drop_count == 0`.
4. **`Arc<T>`, `Mutex<T>`, `RwLock<T>`, `Condvar`, `Once`, `Barrier` & `@thread_local` isolation (`REQ-CONC-039`, `REQ-CONC-030`, `REQ-CONC-070`, `REQ-CONC-071`, `REQ-CONC-105`, `REQ-CONC-110`)**:
   - `N` threads cloning and dropping `Arc<Mutex<Counter>>` (`N * M` increments reaches exact total `N * M` and runs `Counter.drop` exactly once when the last `Arc` drops); `RwLock<T>` concurrent readers vs writers with zero torn reads; `@thread_local static` and `LocalKey<T>` mutated concurrently across `N` threads with zero cross-thread interference and exact per-thread destructor counts.
5. **Compile-fail negative diagnostics (`REQ-CONC-037`, `REQ-CONC-038`, `REQ-CONC-039`)**:
   - Every negative rule in `AXS-SYNC-050` (`Rc<T>` across threads or channels, `MutexGuard<T>` across threads or escaping scope, non-`'static` view escaping into `spawn`, `@thread_local` view escaping function or thread) MUST have a dedicated `tests/conformance/concurrency/*_fail.ax` test asserting the exact `AX_CONC_*` / `AX_TYPE_*` diagnostic code.

### 6.1 Canonical Positive & Negative Examples

#### Positive Example 1: Shared Mutable State with `Arc<Mutex<T>>` and Scoped Threads (`std.thread`, `std.sync`)
```axiom
module example.sync_demo

use std.thread.(scope, Scope)
use std.sync.(Arc, Mutex)

pub fn parallel_accumulate() -> i64 {
    let data: [4]i64 = [10, 20, 30, 40]
    let total = Arc.new(Mutex.new(0i64))

    scope(|s: view<Scope>| {
        let data_v: view<[4]i64> = view(data)
        let total_a = total.clone()
        let total_b = total.clone()

        s.spawn(move || {
            let mut g = total_a.get_view().lock()
            *g.get_mut() = *g.get() + data_v[0] + data_v[1]
        })

        s.spawn(move || {
            let mut g = total_b.get_view().lock()
            *g.get_mut() = *g.get() + data_v[2] + data_v[3]
        })
    })

    let final_guard = total.get_view().lock()
    return *final_guard.get()
}
```

#### Positive Example 2: Move-Only Ownership Transfer over a Bounded Channel (`std.sync.channel`)
```axiom
module example.channel_demo

use std.thread.spawn
use std.sync.channel.channel_bounded
use std.alloc.box.Box

pub struct Job {
    pub id: u64,
    pub payload: Box<i64>,
}

pub fn run_pipeline() -> i64 {
    let (tx, rx) = channel_bounded<Job>(4usize)

    let producer = spawn(move || {
        let job = Job { id: 1u64, payload: Box.new(42i64) }
        let _ = tx.send(job)
        // `job` has been moved into `tx.send`; producer can no longer touch `job`.
    })

    let received = rx.recv().unwrap()
    let _ = producer.join()
    return *received.payload.get_view()
}
```

#### Negative Example 1: Rejecting `Rc<T>` and `MutexGuard<T>` Transfer Across Threads (`AX_CONC_NOT_SEND`)
```axiom
module example.reject_non_send

use std.thread.spawn
use std.sync.(Rc, Mutex)

pub fn bad_rc_spawn() {
    let rc = Rc.new(7i32)
    let _ = spawn(move || {          // ERROR [AX_CONC_NOT_SEND]: `Rc<i32>` does not implement `Send`
        let _ = rc.get_view()
    })
}

pub fn bad_guard_spawn(mtx: view<Mutex<i32>>) {
    let guard = mtx.lock()
    let _ = spawn(move || {          // ERROR [AX_CONC_NOT_SEND]: `MutexGuard<i32>` does not implement `Send`
        let _ = guard.get()
    })
}
```

#### Negative Example 2: Rejecting `@thread_local` View Escape (`AX_CONC_TLS_ESCAPE`)
```axiom
module example.reject_tls_escape

@thread_local
static TLS_BUF: [16]u8 = [0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8]

pub fn leak_tls_view() -> view<[16]u8> {
    return view(TLS_BUF)             // ERROR [AX_CONC_TLS_ESCAPE]: thread-local borrow cannot escape function
}
```

---

## 7. Requirement & Conformance Traceability Matrix

### 7.1 Primary Requirements Covered by `T410` (`covers:`)

| Requirement ID | Summary (`spec/requirements/CATALOG.md`) | Governing Rules in `SPEC-32` |
|---|---|---|
| `REQ-CONC-003` | Concurrency spans language surface, runtime/scheduler, memory model, and FFI/ABI without circular layer dependencies. | `AXS-SYNC-001`, `AXS-SYNC-002`, `AXS-SYNC-003`, `AXS-SYNC-004` |
| `REQ-CONC-022` | Structured concurrency scopes ensure child tasks/threads complete or cancel before scope exit and propagate panics deterministically. | `AXS-SYNC-012`, `AXS-SYNC-013`, `AXS-SYNC-014`, `AXS-SYNC-015`, `AXS-SYNC-016` |
| `REQ-CONC-080` | Cancellation and panic propagation preserve resource safety (`Drop` execution and zero lock/channel corruption). | `AXS-SYNC-014`, `AXS-SYNC-015`, `AXS-SYNC-016`, `AXS-SYNC-043` |
| `REQ-CONC-123` | Reentrancy is an explicit contract distinct from `Send`/`Share` thread safety; standard locks are non-reentrant. | `AXS-SYNC-017`, `AXS-SYNC-021`, `AXS-SYNC-031` |
| `REQ-CONC-198` | Thread/task execution semantics distinguish OS threads (`1:1`), structured scopes, and cooperative cancellation without conflating them with `M:N` async fibers. | `AXS-SYNC-001`, `AXS-SYNC-010`, `AXS-SYNC-012`, `AXS-SYNC-016`, `AXS-SYNC-017` |

### 7.2 Downstream `E11.3` Implementation Requirements Specified by `SPEC-32`

| Consumer Task | Requirement IDs | Governing Rules in `SPEC-32` |
|---|---|---|
| `T090` (`std.thread` + host threading intrinsics) | `REQ-CONC-219`, `REQ-CONC-022`, `REQ-CONC-080`, `REQ-CONC-198` | `AXS-SYNC-001`..`AXS-SYNC-004`, `AXS-SYNC-010`..`AXS-SYNC-017` |
| `T411` (`std.sync`: `Rc`, `Arc`, `Mutex`, `RwLock`, `Condvar`, `Once`, `Barrier`) | `REQ-CONC-010`, `REQ-CONC-015`, `REQ-CONC-044`, `REQ-CONC-045`, `REQ-CONC-046`, `REQ-CONC-047`, `REQ-CONC-070`, `REQ-CONC-071`, `REQ-CONC-105`, `REQ-CONC-106`, `REQ-CONC-180` | `AXS-SYNC-030`..`AXS-SYNC-035`, `AXS-SYNC-050` |
| `T412` (`std.sync.channel`: bounded & unbounded channels) | `REQ-CONC-007`, `REQ-CONC-011`, `REQ-CONC-041`, `REQ-CONC-042`, `REQ-CONC-043`, `REQ-CONC-099`, `REQ-CONC-103`, `REQ-CONC-104`, `REQ-CONC-115`, `REQ-CONC-116`, `REQ-CONC-143`, `REQ-CONC-185`, `REQ-CONC-186` | `AXS-SYNC-040`..`AXS-SYNC-044`, `AXS-SYNC-050` |
| `T413` (`@thread_local` TLS & `std.thread.LocalKey<T>`) | `REQ-CONC-030`, `REQ-CONC-110` | `AXS-SYNC-020`..`AXS-SYNC-024`, `AXS-SYNC-050` |
| `T414` (`E11.3` conformance & multi-threaded stress suite) | `REQ-CONC-036`, `REQ-CONC-037`, `REQ-CONC-038`, `REQ-CONC-039`, `REQ-CONC-081`, `REQ-CONC-187` | `AXS-SYNC-050`, `AXS-SYNC-051` |

---

## 8. Sources

- `spec/SPEC-04-core-extensibility.md` — `AXS-EXT-041` (`Static(SymbolId)` in MIR), `AXS-EXT-071` (`AX_SEC_TLS = 4`, `.tls$` section), `AXS-EXT-073` (`AX_RELOC_X86_64_TLSREL = 6`), `AXS-EXT-091` (`@thread_local` attribute reservation), `AXS-EXT-110` (`std/core/host.ax` host intrinsic boundary).
- `spec/SPEC-30-concurrency.md` — `AXS-CONC-001`..`AXS-CONC-042` (`Send`/`Share` auto-traits, `Happens-Before` relation, `spawn`/`scope` capture rules, panic isolation, concurrency diagnostics).
- `spec/SPEC-31-atomics.md` — `AXS-ATOM-001`..`AXS-ATOM-042` (`Atomic<T>`, `Ordering`, `fence`, `Release`/`Acquire` synchronization and reference-counting fence protocol).
- `spec/diagnostics.md` — `AXD-021` (`AX_CONC_*` diagnostic namespace) and `§11` (fixed diagnostic names for `E11`).
- `docs/base/specs/0136_axiom_concurrency_parallelism_sync_async_spec.md` — §§46–98 (`ACONC-65..90`: threads, TLS, `Rc`/`Arc`, `Mutex`/`RwLock`, `Condvar`, `Once`, channels, panic isolation, cancellation, reentrancy).
- `docs/base/specs/0203_axiom_threads_os_thread_parking_tls_affinity_spec.md` — §§1–24 (`ATHREAD-01..40`: `ThreadId`, `Builder`, `JoinHandle`, `park`/`unpark`, `@thread_local`, `LocalKey<T>`, stack policy, affinity/priority).
- `docs/base/specs/0206_axiom_sync_primitives_mutex_rwlock_condvar_once_barrier_spec.md` — §§1–42 (`ASYNC-PRIM-01..55`: `Mutex<T>`, `MutexGuard<T>`, `RwLock<T>`, `Condvar`, `Once`, `OnceCell<T>`, `Barrier`).
- `docs/base/specs/0207_axiom_channels_spsc_mpsc_mpmc_select_spec.md` — §§1–35 (`ACHAN-01..40`: bounded and unbounded channels, SPSC/MPSC/MPMC topologies, `SendError`/`TrySendError`/`RecvError`/`TryRecvError`, ownership accounting).
- `docs/base/specs/0209_axiom_arc_rc_hazard_epoch_reclamation_spec.md` — §§1–35 (`AARC-01..55`: `Rc<T>`, `Arc<T>`, `Weak<T>`, atomic reference counting ordering and `Send`/`Share` rules).
- `docs/base/tasks/0278_p6_t3_std_thread_spawn_join_sync_primitives.md`, `0329_phase2_std_thread_channels_cancellation_task_Breakdown.md`, `0621_concurrency_channels_task_spec.md`, `0623_concurrency_threads_tls_sync_task_spec.md`, `0837_concurrency_test_matrix_task_spec.md` — Phase-level task specifications for `std.thread`, `@thread_local`, `std.sync`, `std.sync.channel`, and the concurrency verification matrix.
