# SPEC-30 — Concurrency Semantics, Send/Share Auto-Traits, Compile-Time Data-Race Freedom & Memory Model

## Tóm tắt

Đặc tả chính tắc (`SPEC-30`) cho mô hình đồng thời và bộ nhớ của ngôn ngữ Axiom (E11.1): hợp nhất quyền sở hữu (`ownership`), năng lực truy cập (`view<T>` / `mut_view<T>`), hai auto-trait đánh dấu độc lập `Send` và `Share`, quy tắc bắt giữ biến của closure khi vượt ranh giới `spawn` / `spawn_local`, bộ kiểm chứng không tranh chấp dữ liệu ở thời điểm biên dịch (`compile-time data-race freedom`), và mô hình bộ nhớ `Happens-Before` cùng hợp đồng bảo toàn rào cản đồng bộ trong bộ tối ưu hóa MIR (`SPEC-70`). Tài liệu này hợp nhất các quy tắc nền tảng từ `docs/base/specs/0033`, `0079`, `0091`, `0105`, `0126`, `0136` và các đặc tả tác vụ `0298`, `0488`, `0685`, làm nguồn chuẩn duy nhất cho `T089`, `T401`, `T402`, `T403`, `T404` và toàn bộ chuỗi epic `E11.2`–`E11.6`.

Status: draft (T400, 2026-11-03)
Owner: axiom-architect
Consolidates: `docs/base/specs/0033_concurrency_parallism.md`, `docs/base/specs/0040_gpu_heterogeneous_compute.md` (host-device synchronization boundary), `docs/base/specs/0079_concurrency_scheduler_design.md`, `docs/base/specs/0091_structured_concurrency_cancellation.md`, `docs/base/specs/0105_memory_model_ownership_interaction.md`, `docs/base/specs/0126_ownership_concurrency_interaction_spec.md`, `docs/base/specs/0136_concurrency_synchronization_spec.md`, `docs/base/tasks/0298_concurrency_marker_traits_send_share_rules.md`, `docs/base/tasks/0488_ownership_lifetime_region_capability_checker.md`, `docs/base/tasks/0685_concurrency_race_safety_checker.md`
Covers: `REQ-CONC-019`, `REQ-CONC-021`, `REQ-CONC-025`, `REQ-CONC-026`, `REQ-CONC-027`, `REQ-CONC-028`, `REQ-CONC-050`, `REQ-CONC-055`, `REQ-CONC-067`, `REQ-CONC-068`, `REQ-CONC-073`, `REQ-CONC-082`, `REQ-CONC-083`, `REQ-CONC-095`, `REQ-CONC-101`, `REQ-CONC-102`, `REQ-CONC-107`, `REQ-CONC-109`, `REQ-CONC-117`, `REQ-CONC-119`, `REQ-CONC-120`, `REQ-CONC-126`, `REQ-CONC-127`, `REQ-CONC-128`, `REQ-CONC-131`, `REQ-RT-022`, `REQ-CONC-136`, `REQ-CONC-137`, `REQ-CONC-138`, `REQ-CONC-139`, `REQ-CONC-140`, `REQ-CONC-141`, `REQ-CONC-145`, `REQ-CONC-156`
Consumers: `T089`, `T401`, `T402`, `T403`, `T404`, `E11.2` (`T405`–`T409`), `E11.3` (`T410`–`T414`), `E11.4` (`T415`–`T419`), `E11.5` (`T420`–`T424`), `E11.6` (`T425`–`T429`), `spec/SPEC-10-ownership.md`, `spec/SPEC-11-capability.md`, `spec/SPEC-70-optir-ssa-memoryssa.md`

---

## 1. Unified Concurrency Architecture & Execution Contexts

**AXS-CONC-001** (Unified semantic model across sequential and concurrent code; `REQ-CONC-019`, `REQ-CONC-095`).
Axiom does not introduce a secondary memory model, separate concurrent pointer hierarchy (such as `ThreadRef<T>` or `SharedRef<T>`), or disconnected concurrency type system. Safe concurrency is defined directly as the composition of single-owner value semantics (`SPEC-10`), `view<T>` / `mut_view<T>` capability projections (`SPEC-11`), marker auto-traits (`Send`, `Share`), and explicit happens-before synchronization boundaries:

$$\text{Concurrency Safety} = \text{Ownership} \times \text{Capabilities} \times \text{Regions/Lifetimes} \times \text{Synchronization} \times \text{Execution Domains}$$

Safe Axiom programs are free of data races on ordinary (non-atomic) memory by construction. Every value and capability analyzed by the sequential ownership/capability verifier is governed by the exact same aliasing and lifetime laws when crossing or operating across execution contexts.

**AXS-CONC-002** (Six orthogonal semantic axes; `0126 §Part V`, `0136 §6`).
The compiler and standard library separate concurrency semantics into six orthogonal axes that must never be conflated:

| Axis | Semantic Question | Canonical Representation |
|---|---|---|
| Ownership (`SPEC-10`) | Who is responsible for the value's lifecycle and destruction? | Owned value `T`, move transfer, `Drop` |
| Capability (`SPEC-11`) | What operations are currently permitted on a memory place/region? | Shared read `view<T>`, exclusive write `mut_view<T>` |
| Mobility (`Send`) | Can ownership of a value be transferred to another execution context? | `T: Send` |
| Shareability (`Share`) | Can multiple execution contexts concurrently access the value via `view<T>`? | `T: Share` |
| Synchronization | How are conflicting accesses ordered in time and made visible in memory? | `Atomic<T>`, `Mutex<T>`, `RwLock<T>`, `Channel<T>`, `Barrier`, `Scope` |
| Execution Context | Which scheduling and state domain executes the computation? | `Thread`, `Task`, `Fiber`, `GPUKernel`, `InterruptContext` |

**AXS-CONC-003** (Execution contexts and storage domains; `REQ-CONC-021`, `REQ-RT-022`).
An *execution context* is an independent locus of control flow encapsulating its own local call frames, capability environment, and owned values. The specification distinguishes the following execution contexts and storage domains:
1. **`Thread` (`OSThread`)**: Preemptively scheduled OS kernel thread with a dedicated call stack and thread-local storage (`@thread_local`).
2. **`Task` (`AsyncTask` / `WorkerTask`)**: Lightweight, cooperatively or work-stealing scheduled unit of execution with small, deterministic task state (`REQ-RT-022`). A `Task` may migrate between OS worker threads at suspension points (`.await` or yield) unless created as a thread-pinned local task (`spawn_local`).
3. **`Fiber`**: Stackful coroutine with explicit or scheduler-managed context switching; treated as an execution context migration boundary if movable across worker threads, or as a thread-pinned context if restricted to a single OS thread.
4. **`Future<T>`**: First-class suspended state machine representing an asynchronous computation before or during polling. Polling a `Future<T>` across worker threads requires the future's captured state to satisfy `Send`.
5. **`GPUKernel` / Device Domain**: Heterogeneous accelerator execution domain (`SPEC-04`, `0040`). Memory transfers or shared buffers crossing host-device boundaries require both explicit device buffer capabilities and explicit host-device synchronization events.
6. **`InterruptContext`**: Hardware or software interrupt handler context. Blocking synchronization primitives (`Mutex`, `RwLock`, `Condvar`) are forbidden inside `InterruptContext`; only lock-free `Atomic<T>` operations and interrupt-safe queues are permitted.

**AXS-CONC-004** (Storage domains and concurrency visibility; `0105 §2`, `0126 §1`).
Every memory location belongs to a storage domain that governs its baseline reachability:
- `StackLocal`: Private to the creating execution context's stack frame; may only be accessed by child contexts within a lexically bounded structured concurrency `scope` that outlives all spawned children.
- `ThreadLocal` (`@thread_local`): Private to a single OS `Thread`; addresses or views into `@thread_local` storage are unconditionally `!Send` and `!Share` across threads.
- `TaskLocal`: Private to a single `Task` activation.
- `HeapShared` / `ArenaRegion`: Dynamically allocated storage; cross-context transfer requires `Send` and concurrent shared access requires `Share`.
- `GlobalStatic`: Program-lifetime storage; immutable `static` items require `T: Share`, while mutable global state obeys `AXS-CONC-034`.
- `DeviceShared` / `ExternalMMIO`: Governed by explicit device synchronization or `volatile` hardware access rules (`AXS-CONC-036`).

**AXS-CONC-005** (No monolithic concurrency runtime; link-on-demand modularity; `REQ-CONC-145`).
Axiom imposes no mandatory monolithic runtime for concurrency. Sequential programs pay zero runtime or binary-size overhead for threading or async schedulers. OS threading (`std.sync`, `std.thread`), work-stealing task executors (`std.task`), and structured channels are independent, link-on-demand library components built atop the language's ownership, capability, and atomic intrinsics.

**AXS-CONC-006** (Panic vs cooperative cancellation separation; `REQ-CONC-082`, `0091 §4`).
Panic (unrecoverable fault or contract failure within a task/thread) and cancellation (cooperative request for early termination via `CancelToken` / `TaskScope`) are distinct operational states (`REQ-CONC-082`):
1. Cancellation is cooperative, explicit, and propagates downward through a `TaskScope` tree via cancellation tokens and cancellation-aware suspension points.
2. Panic is an abnormal failure state that unwinds or aborts the failing execution context and reports a fault outcome (`TaskResult.Panicked`) at the `join` or `TaskScope` boundary without silently masquerading as normal cancellation.

**AXS-CONC-007** (Deadlock, livelock, starvation, and false sharing scope; `REQ-CONC-083`, `REQ-CONC-120`).
1. **Deadlock / livelock / starvation**: The Axiom compiler guarantees memory safety and data-race freedom at compile time, but is not required to statically decide arbitrary dynamic lock-acquisition graphs or enforce mandatory global lock hierarchies across all user code (`REQ-CONC-083`). Optional local lints may diagnose obvious single-function lock-order inversions (`AX_CONC_LOCK_ORDER`), while structured concurrency (`scope`) and channel message passing are the recommended deadlock-avoidance patterns.
2. **False sharing**: Cache-line contention between independent variables residing on the same hardware cache line is a performance concern, not a memory-safety or data-race violation (`REQ-CONC-120`). Systems code may eliminate false sharing explicitly using alignment attributes (e.g., `@align(64)` or cache-padded wrappers).

**AXS-CONC-008** (Synchronization contracts reside at the type/abstraction boundary; `REQ-CONC-050`).
Synchronization is a property of a type or capability boundary (`Mutex<T>`, `RwLock<T>`, `Atomic<T>`, `Channel<T>`, `Barrier`), never an ad-hoc annotation on an arbitrary unsynchronized variable (`REQ-CONC-050`). Protected data `T` inside a synchronization container cannot be read or mutated without acquiring the container's synchronization guard or executing an atomic protocol operation.

---

## 2. Send and Share Marker Auto-Traits

**AXS-CONC-010** (Semantic definitions of `Send` and `Share`; `REQ-CONC-025`, `REQ-CONC-027`, `REQ-CONC-073`, `REQ-CONC-136`, `REQ-CONC-137`, `REQ-CONC-140`).
Axiom defines two fundamental concurrency marker traits in `std.core.marker`:
1. **`Send`** (`REQ-CONC-025`, `REQ-CONC-136`): Marks a type `T` whose **ownership** may be safely transferred (moved) from one execution context to another. Moving a `T: Send` across a context boundary transfers exclusive responsibility for `T` (including its eventual `Drop` execution) to the receiving context while invalidating the source binding.
2. **`Share`** (`REQ-CONC-027`, `REQ-CONC-073`, `REQ-CONC-137`, `REQ-CONC-140`): Marks a type `T` that may be **concurrently accessed via shared read capability `view<T>`** from multiple execution contexts at the same time. `T: Share` permits concurrent read-only inspection (or synchronized interior operations explicitly exposed on `view<T>`, such as `Atomic<T>` or `Mutex<T>.lock()`), and never permits unsynchronized mutation of `T`.

**AXS-CONC-011** (Orthogonality and independence of `Send` and `Share`; `REQ-CONC-026`, `REQ-CONC-131`, `REQ-CONC-138`, `REQ-CONC-156`).
`Send` and `Share` are strictly distinct semantic properties (`Send != Share`):
1. `T: Send` does **not** imply `T: Share` (for example, an owned buffer with unsynchronized interior state or a single-consumer channel endpoint may be moved to another thread (`Send`), yet cannot be accessed concurrently by two threads via `view<T>` (`!Share`)).
2. `T: Share` does **not** imply `T: Send` (for example, a scope-pinned guard or handle whose destruction must occur on the originating OS thread may allow concurrent read inspection (`Share`) while prohibiting ownership transfer to another thread (`!Send`)).
3. The compiler's type and trait resolution tables (`compiler/sema`) MUST track `Send` and `Share` as independent semantic properties (`REQ-CONC-131`, `REQ-CONC-156`).

**AXS-CONC-012** (View and mutable-view bridge laws; `0126 §6–7`, `0298 §4–6`).
The marker traits of capability projections (`SPEC-11`) relate to their referent type `T` as follows:
1. **`view<T>: Send` if and only if `T: Share`**: Sending a shared read capability `view<T>` to another execution context allows both contexts to read `T` concurrently; therefore `view<T>` can cross an execution context boundary only when `T: Share`.
2. **`view<T>: Share` if and only if `T: Share`**: Sharing a `view<T>` across contexts is equivalent to sharing read access to `T`.
3. **`mut_view<T>: Send` if and only if `T: Send`**: Transferring an exclusive `mut_view<T>` to a single child context (within a valid lifetime bound) transfers exclusive access to `T` for the duration of the borrow, requiring `T: Send`.
4. **`mut_view<T>: !Share` for all `T`**: An exclusive mutable capability `mut_view<T>` can **never** be shared concurrently across multiple execution contexts (`mut_view<T>` is unconditionally `!Share`); concurrent contexts cannot simultaneously use the same `mut_view<T>`.

**AXS-CONC-013** (Lang-item declarations in `std/core/marker.ax`; `T089`, `REQ-CONC-218`).
`Send` and `Share` are declared in `std/core/marker.ax` as compiler-known marker auto-traits via `@lang`:
```axiom
@lang("send")
pub unsafe auto trait Send {}

@lang("share")
pub unsafe auto trait Share {}
```
1. Both traits have empty method sets (pure compile-time semantic markers).
2. Both are marked `auto` (`is_auto = true` in trait metadata) so the compiler automatically synthesizes implementations structurally unless opted out or blocked by a negative field.
3. Both are marked `unsafe` (`is_unsafe = true` in trait metadata) so manual positive overrides require an explicit `unsafe impl` boundary (`AXS-CONC-017`).

**AXS-CONC-014** (Structural auto-derivation rules; `T089`, `REQ-CONC-219`, `0298 §10`).
For any composite nominal type (`struct`, `enum`, `union`), tuple `(T_1, ..., T_n)`, fixed-size array `[T; N]`, or slice `[T]` that does not have an explicit manual or negative implementation:
1. `Composite: Send` holds automatically if and only if every constituent field or variant payload `F_i` satisfies `F_i: Send`.
2. `Composite: Share` holds automatically if and only if every constituent field or variant payload `F_i` satisfies `F_i: Share`.
3. Recursive type definitions are resolved coinductively during auto-trait synthesis: a cycle of nominal field references holds if no reachable constituent fails the trait obligation.
4. Generic wrapper types derive conditional auto-trait bounds over their type parameters according to their fields or explicit `where` clauses.

**AXS-CONC-015** (Canonical `Send` / `Share` derivation matrix for built-in and standard types; `REQ-CONC-028`, `REQ-CONC-101`, `REQ-CONC-102`, `REQ-CONC-141`).
The following table defines the normative `Send` and `Share` status of built-in primitives, capabilities, pointers, smart pointers, synchronization wrappers, and standard collections:

| Type / Category | `Send` Condition | `Share` Condition | Normative Rationale |
|---|---|---|---|
| Primitives (`Bool`, `I8`..`I128`, `U8`..`U128`, `Isize`, `Usize`, `F32`, `F64`, `Char`, `Never`, `()`) | Always `Send` | Always `Share` | Immutable value representation; no interior unsynchronized aliasing |
| Immutable `Str` / `String` (value-owned) | Always `Send` | Always `Share` | Owned buffer (`Send`); shared `view` only exposes immutable UTF-8 bytes (`Share`) |
| `[T; N]`, `(T1, ..., Tn)` | `T_i: Send` | `T_i: Share` | Structural over elements |
| `view<T>` | `T: Share` | `T: Share` | Cross-context read capability requires referent `T: Share` (plus lifetime checks at `spawn`) |
| `mut_view<T>` | `T: Send` | Never (`!Share`) | Exclusive mutable capability cannot be concurrently shared (`AXS-CONC-012`) |
| Raw pointers `*const T`, `*mut T` | Never (`!Send`) | Never (`!Share`) | Raw pointers carry no aliasing or synchronization guarantees; require `unsafe impl` on encapsulating wrapper (`0298 §11`) |
| Function pointer `fn(A) -> R` | Always `Send` | Always `Share` | Stateless code pointer |
| Closure / Anonymous Fn env | All captured fields `: Send` | All captured fields `: Share` | Structural over synthesized capture record (`AXS-CONC-020`) |
| `Box<T>` (unique heap owner) | `T: Send` | `T: Share` | Equivalent to owning `T` by value |
| `Rc<T>` (non-atomic refcount) | Never (`!Send`) | Never (`!Share`) | Non-atomic reference counter would race on clone/drop across threads |
| `Arc<T>` (atomic refcount) | `T: Send + Share` | `T: Send + Share` | Any thread holding an `Arc<T>` may read `&T` (`T: Share`) and any thread may drop the last reference (`T: Send`) (`REQ-CONC-028`) |
| `UnsafeCell<T>` / `Cell<T>` / `RefCell<T>` | `T: Send` (`UnsafeCell`/`Cell`/`RefCell`) | Never (`!Share`) | Unsynchronized interior mutability forbids concurrent access |
| `Atomic<T>` (where `T` is atomic-capable) | Always `Send` | Always `Share` | Hardware/intrinsic atomic operations synchronize concurrent access (`REQ-CONC-102`) |
| `Mutex<T>` | `T: Send` | `T: Send` | Lock serializes access; moving `T` between lock holders across threads requires `T: Send` |
| `RwLock<T>` | `T: Send` | `T: Send + Share` | Readers concurrently view `T` (`T: Share`); writers may move/mutate `T` across threads (`T: Send`) |
| `MutexGuard<T>`, `RwLockReadGuard<T>`, `RwLockWriteGuard<T>` | Never (`!Send`) | `T: Share` (read/mutex guard view only) | Unlock must occur on the acquiring execution context (`0136 §28–32`) |
| Standard collections `Vec<T>`, `Map<K, V>`, `Set<T>` | Element types `: Send` | Element types `: Share` | Collections are not implicitly thread-safe for concurrent mutation (`REQ-CONC-141`); concurrent mutation requires explicit sync (`Mutex<Vec<T>>`, `ConcurrentMap<K, V>`) |
| `@thread_local` handle / `LocalKey<T>` | Never (`!Send`) | Never (`!Share`) | Bound to the current OS thread (`AXS-CONC-004`) |

**AXS-CONC-016** (`Arc<T>` does not grant `Share` or concurrent mutation; `REQ-CONC-028`).
Wrapping a type `T` in `Arc<T>` atomically synchronizes the reference count itself, but does **not** synchronize the payload `T` (`REQ-CONC-028`). Consequently:
1. If `T: !Share` (for example, `Cell<I32>` or an unsynchronized mutable handle), then `Arc<T>` is both `!Send` and `!Share`.
2. Even when `T: Send + Share` (so `Arc<T>: Send + Share`), `Arc<T>` only provides shared read access `view<T>` to its payload. Mutating `T` through `Arc` across execution contexts requires an explicit interior synchronization boundary such as `Arc<Mutex<T>>`, `Arc<RwLock<T>>`, or `Arc<Atomic<T>>`.

**AXS-CONC-017** (Negative implementations `impl !Send` / `impl !Share`; `T089`, `REQ-CONC-219`, `0298 §12`).
A type author may explicitly opt a nominal type `T` out of automatic `Send` or `Share` synthesis using a safe negative implementation:
```axiom
impl !Send for ThreadPinnedHandle {}
impl !Share for UnsyncedCache {}
```
1. Negative implementations are safe because restricting a type from crossing threads or being shared concurrently can never introduce a safety violation.
2. Any outer struct or enum containing a field whose type has `impl !Send` (or `impl !Share`) automatically becomes `!Send` (or `!Share`) unless the outer type explicitly provides an `unsafe impl` override (`AXS-CONC-018`).
3. Providing both a positive and a negative implementation of the same marker trait for the same target type in overlapping coherence domains is rejected with `AX_CONC_CONFLICTING_MARKER_IMPL`.

**AXS-CONC-018** (Explicit `unsafe impl Send` / `unsafe impl Share` override and residual checking; `REQ-CONC-126`, `REQ-CONC-127`, `REQ-CONC-128`, `REQ-CONC-219`).
1. **Mandatory `unsafe impl` boundary (`REQ-CONC-126`)**: When a type `T` contains raw pointers (`*const U`, `*mut U`), `UnsafeCell<U>`, FFI handles, or other `!Send`/`!Share` constituents because it implements custom internal synchronization, overriding the compiler's structural rejection requires an explicit `unsafe impl Send for T {}` and/or `unsafe impl Share for T {}`. Writing a non-unsafe `impl Send for T {}` or `impl Share for T {}` is rejected with `AX_CONC_SAFE_IMPL_MARKER`.
2. **Residual verification obligation (`REQ-CONC-127`, `REQ-CONC-128`)**: Declaring `unsafe impl Send for T` or `unsafe impl Share for T` trusts *only* the specific marker obligation asserted on `T` (often conditioned on generic bounds such as `unsafe impl<T: Send> Send for Mutex<T> {}`). The compiler MUST continue to verify all remaining checkable obligations, including generic `where` bounds on the `unsafe impl`, lifetime/region containment at `spawn`, capability exclusivity (`view<T>` vs `mut_view<T>`), and data-race checks on all callers using `T`.

**AXS-CONC-019** (Zero-cost compile-time proof erasure; `T403`, `REQ-CONC-144`, `0298 §15`).
`Send` and `Share` are purely compile-time semantic proofs. After semantic analysis and concurrency verification succeed:
1. No vtable, type descriptor, witness dictionary, or runtime tag may be emitted for `Send` or `Share`.
2. Satisfying `T: Send` or `T: Share` introduces zero runtime instructions, zero memory layout changes, and zero ABI overhead (`REQ-CONC-144`).

---

## 3. Closure Capture & Spawn / Spawn-Local Boundaries

**AXS-CONC-020** (Closure capture synthesis and structural `Send`/`Share`; `T401`, `REQ-CONC-005`, `REQ-CONC-006`, `REQ-CONC-125`).
Every closure expression is lowered during semantic analysis (`compiler/sema`) to an anonymous environment record whose fields correspond one-to-one with the variables or places captured from enclosing scopes (`REQ-CONC-005`):
1. A closure implements `Send` if and only if every execution-relevant captured field in its environment record satisfies `Send` (`REQ-CONC-005`, `REQ-CONC-125`).
2. A closure implements `Share` if and only if every execution-relevant captured field in its environment record satisfies `Share` (`REQ-CONC-006`, `REQ-CONC-125`).
3. Unreferenced bindings in the lexical scope that are not captured in the closure's synthesized environment record do not affect the closure's `Send` or `Share` traits (`REQ-CONC-125`).

**AXS-CONC-021** (Composition and trait dispatch without class inheritance; `T401`, `REQ-TYP-069`, `REQ-TYP-106`).
Axiom has no implementation inheritance (`class extends`) or implicit object-monitor locks (`REQ-TYP-069`). Concurrent tasks, actors, and runnable services are expressed via data structs, closures, and explicit trait conformance (`FnOnce`, `Fn`, `Future`, or domain traits) with explicit composition of state and synchronization fields (`REQ-TYP-106`).

**AXS-CONC-022** (`move` capture ownership transfer at `spawn` and no implicit copy; `T401`, `REQ-CONC-031`, `REQ-CONC-032`, `REQ-CONC-088`, `REQ-RES-044`).
When a closure or task body is passed to an unstructured or detached `spawn` boundary that may outlive the current stack frame:
1. **Explicit `move` ownership transfer (`REQ-CONC-031`, `REQ-CONC-088`)**: The spawned closure MUST capture its environment by value transfer (`move`). Each moved `!Copy` binding transfers ownership into the closure environment record, immediately invalidating the binding in the spawning parent context (`SPEC-10` move rule).
2. **No implicit copy or clone of `!Copy` values (`REQ-CONC-032`, `REQ-RES-044`)**: The compiler never inserts an implicit `.clone()` or bitwise copy for a `!Copy` resource to satisfy a concurrent capture. Types that satisfy `Copy` (plain value types with no resource destructor) are copied by value into the closure environment; `!Copy` resources must be moved (consuming the parent binding) or explicitly cloned (`Arc.clone(&x)`) by the programmer before `spawn`.
3. Passing a closure that captures outer stack variables by implicit borrow to an unstructured `spawn` without `move` (or outside a bounded `scope`) is rejected with `AX_CONC_SPAWN_REQUIRES_MOVE` or `AX_CONC_ESCAPING_VIEW`.

**AXS-CONC-023** (Prohibition of escaping non-static `view<T>` and `mut_view<T>` across `spawn`; `T401`, `REQ-CONC-008`, `REQ-CONC-009`, `REQ-CONC-029`, `REQ-CONC-033`, `REQ-CONC-132`).
1. **Escaping closure rule (`REQ-CONC-008`, `REQ-CONC-009`)**: Any closure that escapes its defining stack frame (by being returned from a function, stored in a heap/global structure, sent over a channel, or passed to an unscoped `spawn`) is forbidden from capturing a stack-scoped `view<T>` or `mut_view<T>` whose referent lifetime does not outlive `'static`.
2. **Spawn lifetime containment (`REQ-CONC-029`, `REQ-CONC-033`, `REQ-CONC-132`)**: An unscoped `spawn` requires its task closure `F` to satisfy `F: FnOnce() -> R + Send + 'static` and its return type `R: Send + 'static`. Capturing any non-`'static` `view<T>` or `mut_view<T>` into an unscoped `spawn` is rejected at compile time with `AX_CONC_ESCAPING_VIEW`.
3. **Structured `scope` exception (`AXS-CONC-025`)**: A stack-bound `view<T>` (where `T: Share`) or disjoint `mut_view<T>` (where `T: Send`) may be captured by a child task **only** inside a structured concurrency `scope` block (`std.task.scope`) whose lexical exit barrier guarantees that all child tasks complete before the borrowed region ends.

**AXS-CONC-024** (`spawn` vs `spawn_local` semantic obligations; `T401`, `REQ-CONC-072`).
The standard library and compiler distinguish cross-thread spawning from thread-pinned local spawning (`REQ-CONC-072`):

| Operation | Execution Domain | Closure Trait Bounds | Allowed Captures |
|---|---|---|---|
| `spawn(f)` | May execute on or migrate to any worker thread | `F: FnOnce() -> R + Send + 'static`, `R: Send + 'static` | Owned `Send` values (`move`), `'static` `view<T>` where `T: Share` |
| `spawn_local(f)` | Pinned strictly to the current OS thread's local executor | `F: FnOnce() -> R + 'static`, `R: 'static` (`!Send` allowed) | Owned `!Send` values (e.g., `Rc<T>`, thread-pinned handles), `'static` local references |
| `scope.spawn(f)` | May execute on any worker thread, joined before `scope` exits | `F: FnOnce() -> R + Send + 'scope`, `R: Send + 'scope` | Scoped `view<T>` (`T: Share`), disjoint `mut_view<T>` (`T: Send`), or moved `Send` values |

Even though `spawn_local(f)` removes the `Send` requirement because execution never leaves the current OS thread, it still enforces the `'static` escape bound (forbidding dangling stack borrows) and single-thread aliasing rules (`mut_view<T>` exclusivity across suspension points).

**AXS-CONC-025** (Structured concurrency `scope` vs explicit `detach`; `0091 §2–3`, `0126 §18`).
1. By default, structured concurrency (`std.task.scope`) binds the lifetime of every spawned child task to an enclosing lexical scope: the scope exit acts as an implicit join barrier and happens-before synchronization point for all child tasks spawned within it.
2. Unstructured task detachment (`spawn` returning a `JoinHandle<R>` or explicit `.detach()`) requires `'static` ownership of all captured data (`AXS-CONC-023`) so that no child task can ever observe a deallocated caller stack frame.

**AXS-CONC-026** (Suspension point `.await` capture obligations in async tasks; `0126 §23`, `0136 §30`).
For a multi-threaded `Task` whose `Future` must satisfy `Send`:
1. Every live local variable, `view<T>`, or `mut_view<T>` held across an `.await` suspension point becomes a field of the compiler-synthesized coroutine state machine.
2. If any value live across an `.await` point is `!Send` (such as a `MutexGuard<T>`, `RwLockReadGuard<T>`, `RwLockWriteGuard<T>`, or `Rc<T>`), the resulting `Future` is `!Send` and cannot be passed to multi-threaded `spawn` (`AX_CONC_CAPTURE_NOT_SEND` / `AX_CONC_GUARD_ESCAPE`).

---

## 4. Compile-Time Data-Race Freedom & Capability Disjointness

**AXS-CONC-030** (Formal definition of a data race on ordinary memory; `T402`, `REQ-CONC-004`, `REQ-CONC-111`, `REQ-CONC-139`, `REQ-CONC-154`, `REQ-CONC-194`).
Two memory operations $A$ and $B$ form a **data race** if all five of the following conditions hold simultaneously:
1. $A$ and $B$ are executed by different execution contexts (`Thread`, `Task`, `Fiber`, or `GPUKernel`),
2. The target memory regions of $A$ and $B$ overlap (`SAME`, `CONTAINS`, or `UNKNOWN`),
3. At least one of $A$ or $B$ is a write/mutation operation on ordinary (non-atomic) memory,
4. Neither operation is mediated by a valid hardware/intrinsic `Atomic<T>` protocol on the same atomic object, and
5. Neither $A \prec_{\text{hb}} B$ nor $B \prec_{\text{hb}} A$ holds in the `Happens-Before` partial order (`AXS-CONC-040`).

Safe Axiom code is statically guaranteed to be free of data races (`REQ-CONC-004`, `REQ-CONC-111`, `REQ-CONC-154`). Any program construct in safe code that could permit an unsynchronized concurrent write (`REQ-CONC-139`) or unsynchronized read/write pair (`REQ-CONC-194`) is rejected at compile time by the concurrency verifier (`compiler/sema/conc_check.ax`).

**AXS-CONC-031** (Concurrent capability conflict matrix; `T402`, `REQ-CONC-067`, `REQ-CONC-068`, `REQ-CONC-140`, `REQ-CONC-195`, `REQ-CONC-196`).
For any two concurrent execution contexts $C_1$ and $C_2$ operating on overlapping memory places without an intervening `Happens-Before` edge, the compile-time concurrency verifier enforces the following capability conflict matrix:

| Context $C_1$ Access | Context $C_2$ Access | Referent Bound | Verifier Decision | Diagnostic if Rejected |
|---|---|---|---|---|
| `READ` (`view<T>`) | `READ` (`view<T>`) | `T: Share` | **Allowed** (`REQ-CONC-068`, `REQ-CONC-140`, `REQ-CONC-195`) | — |
| `READ` (`view<T>`) | `READ` (`view<T>`) | `T: !Share` | **Rejected** (`REQ-CONC-027`, `REQ-CONC-137`) | `AX_CONC_VIEW_NOT_SHARE` / `AX_CONC_NOT_SHARE` |
| `READ` (`view<T>`) | `WRITE` (`mut_view<T>` / assign) | Any `T` | **Rejected** (`REQ-CONC-196`) | `AX_CONC_SHARED_MUT` |
| `WRITE` (`mut_view<T>` / assign) | `READ` (`view<T>`) | Any `T` | **Rejected** (`REQ-CONC-196`) | `AX_CONC_SHARED_MUT` |
| `WRITE` (`mut_view<T>` / assign) | `WRITE` (`mut_view<T>` / assign) | Any `T` | **Rejected** (`REQ-CONC-067`, `REQ-CONC-139`, `REQ-CONC-196`) | `AX_CONC_SHARED_MUT` |
| `ATOMIC` (`Atomic<T>` op) | `ATOMIC` (`Atomic<T>` op) | Atomic `T` | **Allowed** (`REQ-CONC-102`) | — |
| `ATOMIC` (`Atomic<T>` op) | Non-atomic `READ`/`WRITE` | Same location | **Rejected** (`REQ-CONC-169`) | `AX_CONC_ATOMIC_MUT_VIEW` |

**AXS-CONC-032** (Place/region overlap lattice and conservative `UNKNOWN` rule; `T402`, `REQ-CONC-165`, `REQ-CONC-167`, `REQ-CONC-168`).
When comparing two place projection paths $P_1$ and $P_2$ rooted at the same base object or region (`SPEC-11` `AXS-CAP-010`), the concurrency verifier classifies their spatial relationship using a four-element overlap lattice (`REQ-CONC-165`):
1. **`DISJOINT`**: $P_1$ and $P_2$ provably refer to non-overlapping byte ranges (for example, distinct struct fields `s.a` and `s.b`, or provably non-overlapping slice partitions via `split_at_mut`).
2. **`SAME`**: $P_1$ and $P_2$ denote the exact same place projection path (`s.a` and `s.a`).
3. **`CONTAINS`**: One place is a prefix/parent projection of the other (`s` and `s.a`, or `arr` and `arr[i]`).
4. **`UNKNOWN`**: Static analysis cannot prove disjointness (for example, dynamic array indices `arr[i]` and `arr[j]` where $i \neq j$ is not statically discharged by a trusted partition constructor, or pointer-aliased paths).

**Conservative soundness law (`REQ-CONC-167`, `REQ-CONC-168`)**: The concurrency verifier MUST NEVER treat `UNKNOWN` overlap as `DISJOINT`. Only pairs proven `DISJOINT` may hold concurrent `WRITE`/`WRITE` or `READ`/`WRITE` capabilities across execution contexts; `SAME`, `CONTAINS`, and `UNKNOWN` all trigger conflict rejection (`AX_CONC_SHARED_MUT`) whenever at least one access is a write.

**AXS-CONC-033** (Disjoint struct field and slice sub-range `mut_view` parallelism; `T402`, `REQ-CONC-065`, `REQ-CONC-066`, `REQ-CONC-084`, `REQ-CONC-129`, `REQ-CONC-170`, `REQ-CONC-171`).
1. **Whole-object mutable exclusivity (`REQ-CONC-065`, `REQ-CONC-084`, `REQ-CONC-170`)**: A single `mut_view<T>` pointing to the same object or overlapping field cannot be captured by or split across two concurrent tasks (`AX_CONC_SHARED_MUT`).
2. **Disjoint struct field splitting (`REQ-CONC-066`, `REQ-CONC-129`, `REQ-CONC-171`)**: Within a structured concurrency `scope`, a parent context may project distinct struct fields (`mut_view(&mut state.left)` and `mut_view(&mut state.right)`) where the field paths are statically `DISJOINT` and each field type satisfies `Send`, and pass one disjoint field `mut_view` to each concurrent child task. While those child tasks are active, the parent `state` cannot be accessed as a whole (`CONTAINS` conflict).
3. **Disjoint slice partitioning (`REQ-CONC-129`, `REQ-CONC-171`)**: A mutable slice `mut_view<[T]>` (where `T: Send`) may be partitioned into provably non-overlapping sub-slices via canonical partition APIs (`slice.split_at_mut(mid)` or `slice.chunks_mut(n)`) and distributed across concurrent scoped tasks. Arbitrary unverified index expressions `&mut slice[i]` and `&mut slice[j]` have `UNKNOWN` overlap and are rejected for concurrent capture (`AXS-CONC-032`).

**AXS-CONC-034** (Global / `static` mutable state and `@thread_local` isolation; `T402`, `REQ-CONC-012`).
1. **Immutable `static` items**: A global `static X: T = ...` is accessible concurrently by all execution contexts and therefore requires `T: Share`.
2. **Mutable `static` prohibition in safe code (`REQ-CONC-012`)**: Unsynchronized mutable global variables (`static mut`) cannot be read or written in safe Axiom code (`AX_CONC_UNSYNC_STATIC`). Global state that must be mutated across execution contexts in safe code MUST be wrapped in a `Share` synchronization primitive (`Atomic<T>`, `Mutex<T>`, `RwLock<T>`, `OnceLock<T>`). Direct access to raw `static mut` (needed only for low-level bootstrap or FFI ABI) is restricted to `unsafe` blocks where the programmer assumes the synchronization proof obligation.
3. **`@thread_local` globals**: A `@thread_local static` item is instantiated separately per OS thread. Capabilities (`view<T>` / `mut_view<T>`) derived from a `@thread_local` variable are scoped to a callback on the current thread and are unconditionally `!Send` and `!Share` so they can never escape to another thread or across a thread-migrating `.await` suspension point.

**AXS-CONC-035** (Synchronization primitives and guard invariants; `REQ-CONC-101`, `REQ-CONC-102`, `0136 §28–33`).
Locking (`Mutex<T>`, `RwLock<T>`), atomic operations (`Atomic<T>`), and memory ordering fences (`fence`) are distinct synchronization mechanisms with non-interchangeable contracts (`REQ-CONC-102`):
1. **`Mutex<T>` and `MutexGuard<T>`**: Acquiring a `Mutex<T>` returns an RAII guard `MutexGuard<T>` that mediates exclusive `view<T>` / `mut_view<T>` access to the protected payload. `MutexGuard<T>` is `!Copy` and `!Send`; its `Drop` implementation automatically releases the lock with `Release` memory ordering.
2. **`RwLock<T>`, `RwLockReadGuard<T>`, and `RwLockWriteGuard<T>` (`REQ-CONC-101`)**: `RwLock<T>` permits either multiple concurrent `RwLockReadGuard<T>` holders (granting `view<T>` when `T: Share`) OR a single exclusive `RwLockWriteGuard<T>` holder (granting `mut_view<T>`). While a `RwLockWriteGuard<T>` is active, no new `RwLockReadGuard<T>` or `RwLockWriteGuard<T>` acquisition can succeed (`REQ-CONC-101`). Both guard types are `!Copy` and `!Send`.
3. **No guard escape or borrow outliving guard (`0136 §29`)**: Any `view<T>` or `mut_view<T>` projected from a `MutexGuard<T>`, `RwLockReadGuard<T>`, or `RwLockWriteGuard<T>` is lifetime-bound to the guard instance (`'guard`). Returning or storing a capability derived from a guard so that it outlives the guard's destruction (unlock) is rejected with `AX_CONC_GUARD_ESCAPE`.
4. **No holding lock guards across `.await` (`0136 §30`)**: Holding a thread-blocking `MutexGuard` or `RwLock*Guard` across an async `.await` suspension point is rejected (`AX_CONC_GUARD_ESCAPE` / `AX_CONC_CAPTURE_NOT_SEND`) because the guard is `!Send` and holding an OS/spin lock across cooperative suspension risks executor deadlock. Async code must either drop the guard before `.await` or use an async-aware lock (`AsyncMutex<T>`).

**AXS-CONC-036** (`Atomic<T>` vs ordinary memory and `volatile != atomic`; `REQ-CONC-102`, `REQ-CONC-109`, `REQ-CONC-169`).
1. **No mixing atomic and non-atomic concurrent access (`REQ-CONC-169`)**: An `Atomic<T>` encapsulates its value behind atomic load/store/RMW operations (`load`, `store`, `swap`, `compare_exchange`, `fetch_add`, etc.). Safe code cannot project a concurrent non-atomic `mut_view<T>` into an `Atomic<T>` while concurrent contexts hold `view<Atomic<T>>` (`AX_CONC_ATOMIC_MUT_VIEW`).
2. **`volatile` is NOT inter-thread synchronization (`REQ-CONC-109`)**: `volatile_load` and `volatile_store` exist exclusively for memory-mapped I/O (`MMIO`), hardware registers, and externally observable machine accesses (`SPEC-04`). `volatile` operations do **not** guarantee atomicity against concurrent threads, do **not** establish `Synchronizes-With` or `Happens-Before` edges across execution contexts, and cannot substitute for `Atomic<T>` or `fence` in concurrent code (`REQ-CONC-109`).

**AXS-CONC-037** (`unsafe` concurrency precondition boundary & custom synchronization primitives; `REQ-CONC-107`, `REQ-CONC-128`, `REQ-CONC-157`).
1. **Custom synchronization primitives (`REQ-CONC-107`)**: Systems programmers may implement custom synchronization primitives (`SpinLock<T>`, `MCSLock<T>`, `SeqLock<T>`, `RCU<T>`, `HazardPointer<T>`, lock-free ring buffers) using `unsafe` blocks, `UnsafeCell<T>`, raw pointers, `Atomic<T>`, and `fence`. Their public safe API MUST restore Axiom's ownership, capability lifetime, and `Send`/`Share` invariants at the module/type boundary (`REQ-CONC-107`).
2. **Verifier remains active around `unsafe` (`REQ-CONC-128`, `REQ-CONC-157`)**: Entering an `unsafe` block or calling an `unsafe` function does NOT disable the compile-time concurrency and capability verifier (`REQ-CONC-157`). Once an `unsafe` block constructs or returns a safe `view<T>`, `mut_view<T>`, or owned `T`, all subsequent safe operations on that value or capability are checked strictly under the normal `Send`, `Share`, lifetime, and data-race rules (`REQ-CONC-128`, `REQ-CONC-157`).

**AXS-CONC-038** (FFI concurrency contracts; `REQ-CONC-117`).
Foreign functions (`extern "C"`) and opaque foreign types are **not** implicitly assumed to be thread-safe, reentrant, `Send`, or `Share` (`REQ-CONC-117`):
1. Opaque FFI handle types containing raw pointers or foreign descriptors default to `!Send` and `!Share`.
2. Safe Axiom wrappers around foreign libraries must either serialize foreign calls through a synchronization primitive (`Mutex`) or explicitly document and assert thread-safety via `unsafe impl Send` / `unsafe impl Share` on the wrapper type.

---

## 5. Happens-Before Memory Model & Optimizer Preservation Contract

**AXS-CONC-040** (`Sequenced-Before`, `Synchronizes-With`, and transitive `Happens-Before`; `T403`, `REQ-CONC-055`, `REQ-CONC-074`, `REQ-CONC-208`).
Axiom's memory model defines visibility of memory writes across execution contexts via three formal relations (`REQ-CONC-208`):
1. **`Sequenced-Before` ($\prec_{\text{sb}}$)**: Within a single execution context, evaluation order defines an irreflexive, transitive program-order relation $A \prec_{\text{sb}} B$.
2. **`Synchronizes-With` ($\prec_{\text{sw}}$)**: A release/publication synchronization action $S_{\text{rel}}$ in execution context $C_1$ *synchronizes-with* an acquire/observation synchronization action $S_{\text{acq}}$ in execution context $C_2$ ($S_{\text{rel}} \prec_{\text{sw}} S_{\text{acq}}$) when $S_{\text{acq}}$ observes the state transition produced by $S_{\text{rel}}$ under a valid synchronization protocol (`AXS-CONC-041`).
3. **`Happens-Before` ($\prec_{\text{hb}}$)**: The transitive closure of `Sequenced-Before` and `Synchronizes-With`:
   - If $A \prec_{\text{sb}} B$, then $A \prec_{\text{hb}} B$.
   - If $A \prec_{\text{sw}} B$, then $A \prec_{\text{hb}} B$.
   - If $A \prec_{\text{hb}} B$ and $B \prec_{\text{hb}} C$, then $A \prec_{\text{hb}} C$.

**Visibility guarantee (`REQ-CONC-055`)**: If a write $W$ to memory location $M$ happens-before a read $R$ from $M$ ($W \prec_{\text{hb}} R$) and no other write $W'$ to $M$ satisfies $W \prec_{\text{hb}} W' \prec_{\text{hb}} R$, then $R$ is guaranteed to observe either $W$ or a concurrent write diagnostic rejection (which is impossible for ordinary memory in safe code). In particular, all ordinary and atomic memory writes sequenced-before a synchronization release $S_{\text{rel}}$ become visible to all reads sequenced-after a matching synchronization acquire $S_{\text{acq}}$ (`REQ-CONC-055`).

**AXS-CONC-041** (Canonical `Synchronizes-With` edges; `T403`, `REQ-CONC-055`, `REQ-CONC-209`, `REQ-CONC-210`, `REQ-CONC-211`).
The following language and standard-library operations establish normative `Synchronizes-With` ($\prec_{\text{sw}}$) edges:

| Synchronization Pair | Release Action ($S_{\text{rel}}$) | Acquire Action ($S_{\text{acq}}$) | Semantic Guarantee |
|---|---|---|---|
| Task / Thread Creation (`REQ-CONC-209`) | Parent context call to `spawn` / `scope.spawn` | First instruction of spawned child context | All parent writes prior to `spawn` happen-before child execution |
| Task / Thread Completion (`REQ-CONC-209`) | Final completion & drop of child context | Return from `JoinHandle.join()` or exit of structured `scope` | All child writes prior to completion happen-before parent post-`join` / post-`scope` accesses |
| Mutual Exclusion (`REQ-CONC-210`) | Unlock (`Drop` of `MutexGuard` / `RwLockWriteGuard`) | Subsequent successful `lock()` / `read()` / `write()` on the same lock | All writes inside critical section $k$ happen-before accesses inside critical section $k+1$ |
| Channel Transfer (`REQ-CONC-210`) | `Sender.send(val)` on a `Channel<T>` | Matching `Receiver.recv()` returning `val` | All writes to `val` before `send` happen-before accesses to `val` after `recv` |
| Barrier Rendezvous | Every participant calling `Barrier.wait()` (arrival phase) | Every participant returning from `Barrier.wait()` (departure phase) | All writes before `wait()` in any participant happen-before reads after `wait()` in all participants |
| Atomic Release/Acquire (`REQ-CONC-055`, `REQ-CONC-211`) | Atomic `store` or RMW with `Release`, `AcqRel`, or `SeqCst` on `A` | Atomic `load` or RMW with `Acquire`, `AcqRel`, or `SeqCst` on `A` reading the stored value (or release sequence) | All memory writes prior to the `Release` operation happen-before memory operations after the `Acquire` operation |

**AXS-CONC-042** (Atomic memory orderings and `fence` semantics; `REQ-CONC-055`, `REQ-CONC-102`, `REQ-CONC-211`).
Axiom provides five memory orderings in `std.sync.atomic.Ordering`:
1. **`Relaxed`**: Guarantees indivisibility and per-location modification order coherence for the single atomic variable, but establishes **no** `Synchronizes-With` edge for other memory locations. `Relaxed` operations alone cannot safely publish non-atomic shared data across threads.
2. **`Acquire`**: Valid on loads and RMW operations. Prevents memory reads or writes sequenced-after the `Acquire` operation from being reordered before it; synchronizes-with a prior `Release`/`AcqRel`/`SeqCst` write to the same atomic variable.
3. **`Release`**: Valid on stores and RMW operations. Prevents memory reads or writes sequenced-before the `Release` operation from being reordered after it; makes prior memory operations visible to any subsequent `Acquire`/`AcqRel`/`SeqCst` read of the stored value (`REQ-CONC-055`).
4. **`AcqRel`**: Valid on read-modify-write (RMW) operations (`swap`, `compare_exchange`, `fetch_*`). Combines `Acquire` on the read phase and `Release` on the write phase.
5. **`SeqCst`**: Enforces `Acquire`/`Release` semantics plus a single total global modification order across all `SeqCst` operations in the program.
6. **`fence(ordering)` (`REQ-CONC-102`)**: Establishes an explicit memory ordering barrier between atomic operations and surrounding memory accesses within the current execution context without accessing an atomic variable itself (`Acquire`, `Release`, `AcqRel`, `SeqCst`), distinct from `compiler_fence(ordering)` which restricts only compiler instruction reordering on a single hardware thread (for signal/interrupt handlers).

**AXS-CONC-043** (Notification does not imply memory publication without release-acquire; `T403`, `REQ-CONC-090`).
Waking or signaling an execution context (such as an OS futex wake, event flag, or relaxed atomic counter increment) is distinct from publishing shared memory (`REQ-CONC-090`). Unless the signaling path establishes a valid `Release` $\prec_{\text{sw}}$ `Acquire` happens-before edge covering the shared payload, non-atomic writes performed before the signal are not considered synchronized with the woken execution context.

**AXS-CONC-044** (Cross-domain, host-device, and cross-process shared-memory synchronization; `T403`, `REQ-CONC-112`, `REQ-CONC-113`, `REQ-CONC-114`).
1. **Cross-execution-domain transfers (`REQ-CONC-112`)**: Whenever ownership or shared access crosses distinct execution domains (CPU worker thread to GPU/accelerator kernel, DMA engine, or external co-processor), both capability transfer rules and domain-specific synchronization barriers must hold.
2. **Host-device (`CPU` ↔ `GPU`) barriers (`REQ-CONC-113`, `0040`)**: CPU atomic operations or host mutexes alone do not synchronize device-local caches unless paired with an explicit stream/queue synchronization barrier or host-device fence (`DeviceStream.synchronize()`, host-device acquire/release event) that establishes a cross-domain happens-before edge before host or kernel reads/writes proceed.
3. **Cross-process / IPC shared memory (`REQ-CONC-114`)**: Memory mapped across OS process boundaries (`mmap` / IPC shared regions) lies outside single-process type guarantees; safe access requires process-shared atomic protocols or explicit IPC synchronization guards rather than ordinary unsynchronized `view<T>` / `mut_view<T>` projections.

**AXS-CONC-045** (MIR optimizer synchronization barrier and reordering preservation contract; `T403`, `REQ-CONC-074`, `REQ-CONC-122`, `REQ-CONC-124`, `REQ-CONC-215`, `SPEC-70`).
Every optimization pass in the compiler (`compiler/opt` operating on OptIR / SSA / MemorySSA per `SPEC-70`) MUST preserve the `Happens-Before` memory model (`REQ-CONC-074`, `REQ-CONC-215`):
1. **Synchronization operations as MemorySSA clobber/barrier nodes (`SPEC-70 AXS-OPT-021`)**: Every `spawn`, `join`, lock `acquire`/`release`, channel `send`/`recv`, `fence`, and non-`Relaxed` `Atomic` operation MUST be represented in MIR/OptIR with explicit memory effect metadata that acts as an optimization barrier according to its ordering semantics.
2. **Forbidden hoist/sink across barriers (`REQ-CONC-122`, `REQ-CONC-215`)**:
   - No memory load or store (to any potentially shared or escaped memory location) may be hoisted **above** an `Acquire` boundary (`lock()`, `join()`, `recv()`, `Atomic.load(Acquire)`, `fence(Acquire)`).
   - No memory load or store (to any potentially shared or escaped memory location) may be sunk **below** a `Release` boundary (`unlock()`, `spawn()`, `send()`, `Atomic.store(Release)`, `fence(Release)`).
3. **Forbidden speculative write introduction and stale load folding (`REQ-CONC-124`, `REQ-CONC-215`)**:
   - The optimizer MUST NOT invent speculative writes to any memory location that could be concurrently visible to another execution context (preventing out-of-thin-air or compiler-introduced data races).
   - Common Subexpression Elimination (CSE), GVN, LICM, and Dead Store Elimination (DSE) MUST NOT fold a load across an `Acquire` barrier or eliminate a store prior to a `Release` barrier when the target memory may be observed by another execution context (`REQ-CONC-122`, `REQ-CONC-124`).

**AXS-CONC-046** (Legal lock elision under the unobservable as-if rule; `REQ-CONC-119`).
The optimizer may elide a lock acquisition/release pair or coarsen adjacent critical sections on the same lock **only** when escape and alias analysis prove that the lock object is strictly thread-local (never escapes the current execution context) or that the transformation cannot alter any observable inter-thread `Happens-Before` synchronization (`REQ-CONC-119`).

**AXS-CONC-047** (Deterministic concurrency verification; `T403`, `REQ-CONC-166`).
Compile-time concurrency verification (`Send`/`Share` derivation, closure capture checking, place overlap classification, and data-race conflict detection) is a pure, deterministic function of the source program and compiler configuration (`REQ-CONC-166`). Running `axiomc` repeatedly on the same source inputs MUST produce identical verification results and identical diagnostic ordering regardless of host OS thread scheduling.

---

## 6. Concurrency Diagnostic Taxonomy (`AX_CONC_*`)

**AXS-CONC-050** (Canonical `AX_CONC_*` diagnostic codes; `T089`, `T401`, `T402`, `T403`, `REQ-CONC-212`, `REQ-CONC-213`, `REQ-CONC-214`, `REQ-CONC-216`).
All compile-time concurrency, marker-trait, capture, and memory-safety violations emit stable string diagnostic codes under the `AX_CONC_*` namespace (`spec/diagnostics.md` `AXD-021`):

| Diagnostic Code | Implementing Task | Trigger Condition | Primary Rule |
|---|---|---|---|
| `AX_CONC_NOT_SEND` | `T089` / `T401` | Value of type `T: !Send` transferred across an execution context boundary (`spawn`, `Channel.send`, cross-thread move) | `AXS-CONC-010`, `AXS-CONC-015` |
| `AX_CONC_NOT_SHARE` | `T089` / `T401` | Shared capability `view<T>` where `T: !Share` shared across execution contexts or stored in a global `static` | `AXS-CONC-010`, `AXS-CONC-012` |
| `AX_CONC_SAFE_IMPL_MARKER` | `T089` | Positive `impl Send for T` or `impl Share for T` written without the `unsafe` keyword | `AXS-CONC-013`, `AXS-CONC-018` |
| `AX_CONC_CONFLICTING_MARKER_IMPL` | `T089` | Both positive `unsafe impl Send`/`Share` and negative `impl !Send`/`!Share` declared for overlapping types | `AXS-CONC-017` |
| `AX_CONC_CAPTURE_NOT_SEND` | `T401` | Closure or async `Future` passed to `spawn` captures a `!Send` field (or `!Share` referent inside `view<T>`) | `AXS-CONC-020`, `AXS-CONC-026` |
| `AX_CONC_ESCAPING_VIEW` | `T401` | Escaping closure or unscoped `spawn` captures a non-`'static` stack-bound `view<T>` or `mut_view<T>` | `AXS-CONC-023` |
| `AX_CONC_SPAWN_REQUIRES_MOVE` | `T401` | Unscoped `spawn` closure captures outer bindings by implicit borrow instead of `move` ownership transfer | `AXS-CONC-022` |
| `AX_CONC_SHARED_MUT` | `T402` / `T403` | Unsynchronized concurrent `READ`/`WRITE` or `WRITE`/`WRITE` on overlapping (`SAME`, `CONTAINS`, or `UNKNOWN`) places | `AXS-CONC-031`, `AXS-CONC-032` |
| `AX_CONC_VIEW_NOT_SHARE` | `T402` | Concurrent `READ`/`READ` via `view<T>` across execution contexts when `T: !Share` | `AXS-CONC-031` |
| `AX_CONC_UNSYNC_STATIC` | `T402` | Safe code reads or writes an unsynchronized mutable `static` variable or exports a `@thread_local` view across threads | `AXS-CONC-034` |
| `AX_CONC_GUARD_ESCAPE` | `T402` | Capability derived from `MutexGuard` / `RwLock*Guard` escapes the guard's scope or a lock guard is held across `.await` | `AXS-CONC-035` |
| `AX_CONC_ATOMIC_MUT_VIEW` | `T402` | Concurrent non-atomic `mut_view<T>` access mixed with shared `Atomic<T>` access on the same location | `AXS-CONC-036` |
| `AX_CONC_LOCK_ORDER` | `T403` | Static lint warning/error for inverted lock acquisition order on the same lock pair across concurrent paths | `AXS-CONC-007` |

**AXS-CONC-051** (Structured diagnostic payload keys for concurrency errors; `T403`, `REQ-CONC-212`, `REQ-CONC-213`, `REQ-CONC-214`, `REQ-CONC-216`).
Every `AX_CONC_*` diagnostic emitted by `axiomc` (`--error-format=json` and human output) MUST include structured explanatory context (`REQ-CONC-216`) covering:
1. **`place` / `region`**: The exact source expression, captured variable, or field projection path (`state.count`, `slice[i]`) involved in the violation (`REQ-CONC-212`, `REQ-CONC-213`).
2. **`domain`**: The originating and target execution context boundaries (`Thread`, `Task` at `spawn`, `spawn_local`, `.await` suspension point, or `GPUKernel`).
3. **`sync_state`**: The observed capability pair and overlap classification (`WRITE vs READ (SAME)`, `WRITE vs WRITE (UNKNOWN)`, or failing constituent field chain `Outer -> Inner -> *mut U: !Send`).
4. **`reason` / `help`**: Actionable remediation guidance (e.g., move ownership into `spawn`, wrap shared mutable state in `Arc<Mutex<T>>` or `Atomic<T>`, use `scope` for stack-bounded views, or partition slices with `split_at_mut`) (`REQ-CONC-214`).

**AXS-CONC-052** (Constituent derivation trace for `Send` / `Share` failures; `T089`, `T401`).
When `AX_CONC_NOT_SEND`, `AX_CONC_NOT_SHARE`, or `AX_CONC_CAPTURE_NOT_SEND` is emitted for a composite struct, enum, or closure environment, the secondary diagnostic notes MUST trace the exact field chain from the outer type down to the leaf field that violated `Send` or `Share` (for example: `closure captures 'handle' of type Session -> field 'ptr' of type *mut RawConn is !Send`).

---

## 7. Canonical Conformance Examples (Positive & Negative)

All examples in this section use canonical Axiom syntax (`=` for binding/assignment, `.` for module/member qualification).

### 7.1 Positive: Ownership Transfer (`move`) and Shared Immutable `view<T>`

```axiom
use std.task
use std.sync.Arc

struct Config {
    pub workers: I32,
    pub label: String,
}
// Config automatically derives Send + Share because I32 and String are Send + Share.

pub fn run_owned_and_shared() {
    owned_buf = Vec.with_capacity(64)
    // Positive (AXS-CONC-022): move transfers ownership of owned_buf (Vec<I32>: Send) to child task.
    h = task.spawn(move || -> usize {
        owned_buf.len()
    })
    _ = h.join()

    // Positive (AXS-CONC-016, AXS-CONC-031): Arc<Config> is Send + Share; concurrent READ/READ is safe.
    cfg = Arc.new(Config { workers: 4, label: "prod" })
    cfg_clone = Arc.clone(&cfg)
    reader = task.spawn(move || -> I32 {
        cfg_clone.workers
    })
    _ = reader.join()
}
```

### 7.2 Negative: Capturing `!Send` Raw Pointer or Escaping Non-Static `view<T>`

```axiom
use std.task

struct RawHandle {
    ptr: *mut U8, // *mut U8 is !Send and !Share (AXS-CONC-015)
}

pub fn reject_non_send_and_escaping_view() {
    h = RawHandle { ptr: null_mut() }
    // ERROR [AX_CONC_CAPTURE_NOT_SEND]: RawHandle is !Send (field `ptr: *mut U8` is !Send)
    _ = task.spawn(move || {
        _ = h
    })

    local_val = 42
    v = view(&local_val)
    // ERROR [AX_CONC_ESCAPING_VIEW]: non-'static `view<I32>` cannot escape into unscoped `task.spawn`
    _ = task.spawn(move || -> I32 {
        *v
    })
}
```

### 7.3 Positive: Structured `scope` with Disjoint Field `mut_view` and Slice `split_at_mut`

```axiom
use std.task

struct PairState {
    pub left: I64,
    pub right: I64,
}

pub fn parallel_disjoint_mutation(state: mut_view<PairState>, data: mut_view<[I64]>) {
    // Project DISJOINT field mutable views (AXS-CONC-033):
    left_v = mut_view(&mut state.left)
    right_v = mut_view(&mut state.right)
    (first_half, second_half) = data.split_at_mut(data.len() / 2)

    task.scope(|s| {
        s.spawn(move || {
            *left_v = 10
            if first_half.len() > 0 {
                first_half[0] = 1
            }
        })
        s.spawn(move || {
            *right_v = 20
            if second_half.len() > 0 {
                second_half[0] = 2
            }
        })
    }) // Implicit join barrier: happens-before subsequent reads of `state` and `data` (AXS-CONC-041).
}
```

### 7.4 Negative: Concurrent Overlapping Mutation and `UNKNOWN` Dynamic Index Overlap

```axiom
use std.task

pub fn reject_overlapping_mutation(data: mut_view<[I64]>, i: usize, j: usize) {
    task.scope(|s| {
        // ERROR [AX_CONC_SHARED_MUT]: `data` captured mutably by two concurrent tasks (SAME overlap)
        s.spawn(|| { data[i] = 1 })
        s.spawn(|| { data[j] = 2 }) // Even if i != j at runtime, static overlap is UNKNOWN != DISJOINT (AXS-CONC-032)
    })
}
```

### 7.5 Synchronization Guards and Happens-Before Publication

```axiom
use std.sync.{Arc, Mutex}
use std.sync.atomic.{AtomicBool, Ordering}
use std.task

pub fn guard_and_atomic_publication() {
    shared_counter = Arc.new(Mutex.new(0))
    c1 = Arc.clone(&shared_counter)

    worker = task.spawn(move || {
        guard = c1.lock()
        *guard = *guard + 1
        // `guard` drops here at block end -> Release unlock synchronizes-with next lock() (AXS-CONC-041).
    })
    _ = worker.join()

    ready = Arc.new(AtomicBool.new(false))
    r1 = Arc.clone(&ready)
    producer = task.spawn(move || {
        // Release store establishes happens-before with Acquire load observing `true` (AXS-CONC-041):
        r1.store(true, Ordering.Release)
    })
    _ = producer.join()
    _ = ready.load(Ordering.Acquire)
}
```

---

## 8. Requirement & Conformance Traceability Matrix

### 8.1 Primary Requirements Covered by `T400` (`SPEC-30`)

| Requirement ID | Corpus Origin | Normative Rule(s) in `SPEC-30` | Summary of Normative Obligation |
|---|---|---|---|
| `REQ-CONC-019` | `0126 §Part V` | `AXS-CONC-001`, `AXS-CONC-002` | Unified ownership + capability + synchronization concurrency model |
| `REQ-CONC-021` | `0126 §1` | `AXS-CONC-003`, `AXS-CONC-004` | Execution context encapsulates local state, control flow, capabilities, and owned values |
| `REQ-CONC-025` | `0126 §5` | `AXS-CONC-010`, `AXS-CONC-015` | Cross-context ownership transfer requires `T: Send` |
| `REQ-CONC-026` | `0126 §6` | `AXS-CONC-011` | `Send` and `Share` are distinct (`Send` does not imply `Share`) |
| `REQ-CONC-027` | `0126 §7` | `AXS-CONC-010`, `AXS-CONC-012` | Concurrent shared access across execution contexts requires `T: Share` |
| `REQ-CONC-028` | `0126 §7` | `AXS-CONC-015`, `AXS-CONC-016` | Shared ownership (`Arc<T>`) of mutable data does not automatically grant `Share` or concurrent mutation |
| `REQ-CONC-050` | `0126 §33` | `AXS-CONC-008`, `AXS-CONC-035` | Synchronization contracts reside at the type/abstraction boundary |
| `REQ-CONC-055` | `0126 §39` | `AXS-CONC-040`, `AXS-CONC-041`, `AXS-CONC-042` | `Release` store/RMW makes prior memory operations visible to subsequent `Acquire` operations |
| `REQ-CONC-067` | `0126 §49` | `AXS-CONC-031`, `AXS-CONC-032` | Concurrent writes to the same field across execution contexts rejected without synchronization |
| `REQ-CONC-068` | `0126 §50` | `AXS-CONC-031` | Multiple execution contexts may concurrently read an immutable region via `view<T>` if `T: Share` |
| `REQ-CONC-073` | `0126 §59` | `AXS-CONC-010`, `AXS-CONC-012` | `Share` permits concurrent read `view<T>` without permitting concurrent mutation |
| `REQ-CONC-082` | `0126 §72` | `AXS-CONC-006` | Panic and cooperative cancellation are distinct operational states |
| `REQ-CONC-083` | `0126 §73` | `AXS-CONC-007` | Compiler not required to decide arbitrary dynamic deadlocks or enforce mandatory global lock hierarchies |
| `REQ-CONC-095` | `0126 §79` | `AXS-CONC-001` | No separate concurrency pointer hierarchy (`ThreadRef`/`SharedRef`); unified ownership & capabilities |
| `REQ-CONC-101` | `0136 §32` | `AXS-CONC-015`, `AXS-CONC-035` | Active `RwLockWriteGuard` excludes all new `RwLockReadGuard` and `RwLockWriteGuard` acquisitions |
| `REQ-CONC-102` | `0136 §33` | `AXS-CONC-015`, `AXS-CONC-035`, `AXS-CONC-036`, `AXS-CONC-042` | Locking (`Mutex`/`RwLock`), atomics (`Atomic<T>`), and fences (`fence`) are distinct mechanisms |
| `REQ-CONC-107` | `0136 §47` | `AXS-CONC-037` | Custom `unsafe` synchronization primitives must restore safe concurrency invariants at their public API |
| `REQ-CONC-109` | `0136 §51` | `AXS-CONC-036` | `volatile` is for MMIO/hardware access, not inter-thread synchronization or happens-before |
| `REQ-CONC-117` | `0136 §73` | `AXS-CONC-038` | FFI functions and opaque handles are not implicitly thread-safe (`Send`/`Share`/reentrant) |
| `REQ-CONC-119` | `0136 §79` | `AXS-CONC-046` | Lock elision permitted only when unobservable under the inter-thread happens-before model |
| `REQ-CONC-120` | `0136 §80` | `AXS-CONC-007` | False sharing is a performance concern (`@align`), not a language safety violation |
| `REQ-CONC-126` | `0136 §101+` | `AXS-CONC-013`, `AXS-CONC-018` | Overriding compiler `Send`/`Share` rejection requires explicit `unsafe impl Send`/`Share` |
| `REQ-CONC-127` | `0136 §101+` | `AXS-CONC-018` | Compiler continues to verify all remaining checkable obligations alongside `unsafe impl Send`/`Share` |
| `REQ-CONC-128` | `0136 §101+` | `AXS-CONC-018`, `AXS-CONC-037` | Safe code stays simple while `unsafe` retains systems power without disabling external verification |
| `REQ-CONC-131` | `0160 §27` | `AXS-CONC-011` | Compiler treats `Send` and `Share` as distinct semantic properties |
| `REQ-RT-022` | `1066 §2.C` | `AXS-CONC-003` | Differentiate lightweight `Task` (small, deterministic state) from OS `Thread` |
| `REQ-CONC-136` | `0270 §27, 0298 §9` | `AXS-CONC-010` | `Send` represents ownership transfer across execution domains |
| `REQ-CONC-137` | `0270 §8, 0298 §4` | `AXS-CONC-010`, `AXS-CONC-031` | `Share` represents concurrent read access capability |
| `REQ-CONC-138` | `0270 §39, 0298 §4` | `AXS-CONC-011` | `Send` and `Share` are semantically distinct |
| `REQ-CONC-139` | `0270 §20, 0298 §1` | `AXS-CONC-030`, `AXS-CONC-031` | Safe concurrent writes require exclusive access (`mut_view<T>` or synchronized guard) |
| `REQ-CONC-140` | `0270 §21, 0298 §6` | `AXS-CONC-010`, `AXS-CONC-031` | Safe concurrent read sharing requires valid `Share` semantics |
| `REQ-CONC-141` | `tasks/0416 §71` | `AXS-CONC-015` | Standard collections (`Vec`, `Map`, `Set`) are not implicitly synchronized; `Send`/`Share` derived structurally |
| `REQ-CONC-145` | `0435 §72..102` | `AXS-CONC-005` | No monolithic concurrency runtime; thread and async runtimes are modular link-on-demand components |
| `REQ-CONC-156` | `tasks/0482 §49..50` | `AXS-CONC-011`, `AXS-CONC-013` | `Send` and `Share` tracked as independent semantic properties in type/trait tables |

### 8.2 Downstream E11.1 Implementation & Verification Task Mapping

| Sibling Task | Scope Summary | Governing `SPEC-30` Rules | Downstream Requirements Covered |
|---|---|---|---|
| `T089` | `Send` and `Share` auto-traits in `std/core/marker.ax` & `compiler/sema` | `AXS-CONC-010`..`AXS-CONC-019`, `AXS-CONC-050`, `AXS-CONC-052` | `REQ-CONC-218`, `REQ-CONC-219` |
| `T401` | Closure capture & `spawn` / `spawn_local` boundary checking | `AXS-CONC-020`..`AXS-CONC-026`, `AXS-CONC-050`..`AXS-CONC-052` | `REQ-CONC-005`, `REQ-CONC-006`, `REQ-CONC-008`, `REQ-CONC-009`, `REQ-CONC-029`, `REQ-CONC-031`, `REQ-CONC-032`, `REQ-CONC-033`, `REQ-CONC-072`, `REQ-CONC-088`, `REQ-RES-044`, `REQ-TYP-069`, `REQ-TYP-106`, `REQ-CONC-125`, `REQ-CONC-132` |
| `T402` | Compile-time data-race verifier & shared mutable rejection | `AXS-CONC-030`..`AXS-CONC-038`, `AXS-CONC-050`, `AXS-CONC-051` | `REQ-CONC-004`, `REQ-CONC-012`, `REQ-CONC-065`, `REQ-CONC-066`, `REQ-CONC-084`, `REQ-CONC-111`, `REQ-CONC-129`, `REQ-CONC-154`, `REQ-CONC-157`, `REQ-CONC-165`, `REQ-CONC-167`, `REQ-CONC-168`, `REQ-CONC-169`, `REQ-CONC-170`, `REQ-CONC-171`, `REQ-CONC-194`, `REQ-CONC-195`, `REQ-CONC-196` |
| `T403` | Happens-before preservation in MIR optimizer & zero-cost erasure | `AXS-CONC-019`, `AXS-CONC-040`..`AXS-CONC-047`, `AXS-CONC-050`, `AXS-CONC-051` | `REQ-CONC-074`, `REQ-CONC-090`, `REQ-CONC-112`, `REQ-CONC-113`, `REQ-CONC-114`, `REQ-CONC-122`, `REQ-CONC-124`, `REQ-CONC-144`, `REQ-CONC-166`, `REQ-CONC-208`, `REQ-CONC-209`, `REQ-CONC-210`, `REQ-CONC-211`, `REQ-CONC-212`, `REQ-CONC-213`, `REQ-CONC-214`, `REQ-CONC-215`, `REQ-CONC-216` |
| `T404` | Concurrency & memory model conformance suite (`tests/conformance/concurrency/`) | `AXS-CONC-001`..`AXS-CONC-052`, `§7` | `REQ-CONC-016`, `REQ-CONC-018`, `REQ-CONC-085`, `REQ-CONC-086`, `REQ-CONC-087`, `REQ-CONC-089`, `REQ-CONC-094`, `REQ-CONC-158`..`REQ-CONC-164`, `REQ-CONC-176`, `REQ-CONC-181`, `REQ-CONC-182`, `REQ-CONC-183`, `REQ-CONC-192`, `REQ-CONC-193`, `REQ-CONC-197`, `REQ-CONC-202`..`REQ-CONC-207` |

---

## 9. Sources

- `docs/base/specs/0033_concurrency_parallism.md` — Baseline concurrency & parallelism model, `Send`/`Share` distinction, channels, tasks vs threads.
- `docs/base/specs/0040_gpu_heterogeneous_compute.md` — Host-device memory domains and cross-domain synchronization barriers.
- `docs/base/specs/0079_concurrency_scheduler_design.md` — M:N work-stealing task scheduler, `Task` vs `OSThread`, `spawn` vs `spawn_local`.
- `docs/base/specs/0091_structured_concurrency_cancellation.md` — Structured `TaskScope`, cooperative `CancelToken`, and panic vs cancellation separation.
- `docs/base/specs/0105_memory_model_ownership_interaction.md` — Storage domains, `Sequenced-Before`, `Synchronizes-With`, `Happens-Before`, atomic orderings, and optimizer reordering restrictions.
- `docs/base/specs/0126_ownership_concurrency_interaction_spec.md` — Unified ownership/capability concurrency model, closure captures, disjoint field/slice splitting, guard rules, and verifier architecture.
- `docs/base/specs/0136_concurrency_synchronization_spec.md` — Synchronization primitives (`Mutex`, `RwLock`, `Atomic`, `fence`), `volatile != atomic`, FFI contracts, lock elision, false sharing, and `unsafe impl Send`/`Share` boundary.
- `docs/base/tasks/0298_concurrency_marker_traits_send_share_rules.md` — Detailed marker auto-trait derivation, negative impls, and zero-cost erasure.
- `docs/base/tasks/0488_ownership_lifetime_region_capability_checker.md` — Region/capability overlap lattice (`DISJOINT`, `CONTAINS`, `SAME`, `UNKNOWN`) and conservative soundness rules.
- `docs/base/tasks/0685_concurrency_race_safety_checker.md` — Compile-time race verifier pipeline, `Happens-Before` optimizer contract, and `AX_CONC_*` diagnostic payloads.
- `spec/SPEC-10-ownership.md`, `spec/SPEC-11-capability.md`, `spec/SPEC-70-optir-ssa-memoryssa.md` — Canonical ownership, capability projection, and OptIR/MemorySSA specifications.
