# SPEC-31 — Atomics, Memory Ordering, Fences, x86-64 Lowering & Oracle Schedule Exploration

## Tóm tắt

Đặc tả chính tắc (`SPEC-31`) cho kiểu nguyên tử `Atomic<T>`, mô hình thứ tự bộ nhớ (`Ordering`), hàng rào bộ nhớ (`fence` / `compiler_fence`), phép hạ tầng qua `MIR` / `LIR`, bảng ánh xạ tập lệnh máy `x86-64`, và ngữ nghĩa kiểm chứng thăm dò lịch trình tất định trong trình thông dịch `oracle` của ngôn ngữ Axiom (`E11.2`). Tài liệu này hợp nhất các quy tắc từ `docs/base/specs/0092`, `0128`, `0161`, `0162`, `0208` và các đặc tả tác vụ `0328`, `0515`, nối tiếp nền tảng đồng thời của `SPEC-30` (`E11.1`) và hợp đồng mở rộng lõi `SPEC-04` (`AXS-EXT-020`, `AXS-EXT-023`, `AXS-EXT-043`, `AXS-EXT-051`).
Các quyết định cốt lõi:
- Phân tách tuyệt đối ba chế độ truy cập bộ nhớ: bộ nhớ thông thường (`ordinary memory`), bộ nhớ nguyên tử (`Atomic<T>`), và truy cập phần cứng quan sát được (`Volatile<T>` / `MMIO`). `volatile` không bao giờ tạo đồng bộ hóa liên luồng (`Happens-Before`), và `Atomic<T>` không bao giờ chuyển đổi ngầm hay tường minh sang `mut_view<T>` để vượt qua giao thức nguyên tử.
- Chốt 5 mức `Ordering` (`Relaxed`, `Acquire`, `Release`, `AcqRel`, `SeqCst`), các thao tác chuẩn trong `std.sync.atomic` (`new`, `load`, `store`, `swap`, `compare_exchange`, `compare_exchange_weak`, `fetch_add`, `fetch_sub`, `fetch_and`, `fetch_or`, `fetch_xor`, `fence`, `compiler_fence`, `spin_loop_hint`, `is_lock_free`), số học bù hai quay vòng (`wrapping two's-complement`) cho phép toán số nguyên `RMW`, và kiểm tra hợp lệ của `Ordering` ngay tại thời điểm biên dịch.
- Định nghĩa tập câu lệnh `MIR` `Atomic` riêng biệt (`AXS-EXT-043`), các phép toán `LIR` `Atomic*`/`Fence` (`AXS-EXT-051`), bảng chọn lệnh và mã hóa byte-exact trên `x86-64` (`MOV`, `XCHG`, `LOCK XADD`, `LOCK CMPXCHG`, `LOCK AND/OR/XOR`, `MFENCE`, `PAUSE`), mô hình đồng hồ véc-tơ (`vector clock`) và bộ thăm dò lịch trình tất định trong `oracle` (`T408`), cùng 6 bài kiểm tra chuẩn `litmus` (`MP`, `MP-Fence`, `SB`, `LB`, `RMW`, `CAS-ABA`) cho `T409`.

Status: draft (T405, 2026-11-03)
Owner: axiom-architect
Consolidates: `docs/base/specs/0092 - Axiom — Atomic, Memory Ordering & Lock-Free Model v0.1.md`, `docs/base/specs/0128 - AXIOM LANGUAGE SPECIFICATION v0.1 — Part VII.md`, `docs/base/specs/0161 - AXIOM MIR v0.1.md` (§30), `docs/base/specs/0162 - AXIOM LIR v0.1.md` (§12, §32, §43), `docs/base/specs/0208 - ATOMIC-001.md`, `docs/base/tasks/0328 - BOOTSTRAP-069 — Axiom Low-Level Memory, Atomics, Volatile & Machine Access.md`, `docs/base/tasks/0515 - BOOTSTRAP-256 — AXIOM MEMORY ACCESS, LOADSTORE, ATOMICVOLATILE & MEMORY ORDERING LOWERING.md`
Covers: `REQ-ATM-001`, `REQ-CONC-013`, `REQ-CONC-059`, `REQ-CONC-060`, `REQ-CONC-097`, `REQ-ATM-002`, `REQ-ATM-014`, `REQ-ATM-015`, `REQ-ATM-031`, `REQ-MIR-144`, `REQ-CONC-172`, `REQ-CONC-174`, `REQ-CONC-178`
Consumers: `T406` (`std/sync/atomic.ax`, typeck/verifier validation, MIR lowering), `T407` (LIR atomic ops & x86-64 codegen/encoding), `T408` (MIR interpreter oracle atomic memory model & deterministic schedule explorer), `T409` (atomic & memory-ordering litmus conformance suite), `E11.3` (`T090`, `T410`–`T414`), `E13.2` / `E13.6` (`Volatile<T>` / `Mmio<T>` boundary)

---

## 1. Foundational Separation: Atomic Memory vs. Ordinary Memory vs. Volatile Access

**AXS-ATM-001** (Three distinct memory access regimes; `REQ-ATM-001`, `REQ-CONC-013`, `REQ-CONC-059`, `REQ-CONC-172`, `REQ-CONC-178`, `tasks/0328 §1`, `tasks/0515 §52–60`).
Axiom partitions memory accesses into three mutually exclusive semantic regimes that the type system, MIR verifier, optimizer, and backend MUST keep strictly distinct:

| Access Regime | Canonical Abstraction | Primary Guarantee | Compiler Optimization Contract |
|---|---|---|---|
| **Ordinary Memory** | Owned `T`, `view<T>`, `mut_view<T>` | Single-owner lifecycle & compile-time capability disjointness (`SPEC-10`, `SPEC-11`, `SPEC-30`) | Freely scalarized, forwarded, coalesced, hoisted, sunk, or eliminated within `Happens-Before` boundaries (`SPEC-70`..`SPEC-73`) |
| **Atomic Memory** | `Atomic<T>` (`std.sync.atomic`) | Indivisible modification, per-object modification order (`mo`), and explicit inter-thread `Synchronizes-With` ordering (`Ordering`) | Dedicated MIR `Atomic` and LIR `Atomic*` operations; never lowered to ordinary loads/stores or weakened across synchronization edges (`REQ-MIR-144`) |
| **Volatile / MMIO Memory** | `Volatile<T>`, `Mmio<T>`, `volatile_load` / `volatile_store` (`E13.2`, `E13.6`) | Preservation of externally observable hardware/device side effects (`count`, `width`, `program order`) | Dedicated MIR `VolatileLoad`/`VolatileStore`; never eliminated, merged, or duplicated, and **never** treated as inter-thread synchronization (`REQ-ATM-031`) |

**AXS-ATM-002** (Atomicity is a property of storage, not ad-hoc operations on ordinary values; `REQ-ATM-002`, `REQ-ATM-027`, `REQ-CONC-013`, `REQ-CONC-118`, `0092 §2`, `0128 §2, §40`).
1. **Storage-bound semantics (`REQ-ATM-002`, `AATOM-20`)**: Atomicity in Axiom is an intrinsic property of an `Atomic<T>` storage instance, never an ad-hoc operation applied to an ordinary variable `x: T` or capability `mut_view<T>` (`REQ-CONC-013`). Safe Axiom provides no C-style free function `atomic_fetch_add(&mut x, 1)` on ordinary memory.
2. **Storage identity vs. type identity (`REQ-ATM-027`, `0128 §40`)**: Atomic modification order and `Synchronizes-With` edges bind to a specific `Atomic<T>` storage location (object identity), never to the type `Atomic<T>` in the abstract. Two distinct instances `a: Atomic<u64>` and `b: Atomic<u64>` have independent modification orders; a `Release` store to `a` establishes no synchronization with an `Acquire` load from `b` unless mediated by a transitive chain on the same atomic location or a `fence` pair (`AXS-ATM-027`).
3. **No hidden compiler atomic promotion (`REQ-CONC-118`, `0136 §77`)**: The compiler MUST NOT silently promote ordinary unsynchronized memory accesses into atomic instructions to mask a data race, nor demote `Atomic<T>` accesses into ordinary memory accesses (`REQ-CONC-133`).

**AXS-ATM-003** (Orthogonality of atomicity, ordering, and visibility; `REQ-CONC-174`, `0208 §1`, `tasks/0328 AMEMLOW-29`, `tasks/0515 AMEM-79`).
Atomicity and memory ordering are distinct semantic properties (`REQ-CONC-174`):
1. **Atomicity** guarantees that a read, write, or read-modify-write on a single `Atomic<T>` location executes as an indivisible unit without torn reads or partial writes (`REQ-ATM-013`), and participates in that location's total modification order (`REQ-ATM-012`).
2. **Memory Ordering (`Ordering`)** governs how ordinary and atomic memory operations surrounding the atomic access in program order ($\prec_{\text{sb}}$) may be reordered by the compiler or hardware and when they become visible ($\prec_{\text{hb}}$) to other execution contexts (`0208 §1`).
3. An atomic operation with `Ordering.Relaxed` is fully atomic yet imposes zero inter-location ordering constraints (`REQ-CONC-053`, `REQ-ATM-006`).

**AXS-ATM-004** (Architectural separation of foundational concurrency & memory concepts; `REQ-CONC-097`, `REQ-ASY-166`, `REQ-CONC-098`, `REQ-CONC-142`, `0126 §81`, `0128 §52–54`).
The Axiom language specification and compiler enforce strict pairwise non-equivalence across the following foundational concepts (`REQ-CONC-097`, `REQ-ASY-166`):
1. **`Send` $\neq$ `Share`**: Cross-context ownership transfer (`Send`) is independent of concurrent read capability sharing (`Share`) (`SPEC-30 AXS-CONC-011`).
2. **`Move` $\neq$ `Copy`**: Ownership transfer (`Move`, invalidating the source binding) is distinct from implicit bit-level value duplication (`Copy`) and explicit resource duplication (`Clone`).
3. **`Ownership` $\neq$ `Capability`**: Owning a value `T` (controlling destruction) is distinct from holding a temporary read (`view<T>`) or write (`mut_view<T>`) projection (`SPEC-10`, `SPEC-11`).
4. **`Capability` $\neq$ `Synchronization`**: Holding `view<T>` or `mut_view<T>` defines access permissions within a region, whereas establishing cross-context temporal ordering requires an explicit synchronization primitive (`Atomic<T>`, `Mutex<T>`, `RwLock<T>`, `Channel<T>`, `fence`).
5. **`Atomic<T>` $\neq$ `Volatile<T>`**: Inter-thread synchronization (`Atomic<T>`) is completely separate from externally observable MMIO/device register access (`Volatile<T>`) (`REQ-ATM-001`, `REQ-CONC-059`).
6. **`Thread` $\neq$ `Task`**: Preemptive OS threads (`std.thread.Thread`) with dedicated stacks and TLS are distinct from lightweight, cooperatively suspended asynchronous tasks (`std.task.Task`) (`SPEC-30 AXS-CONC-003`).
7. **`Panic` $\neq$ `Cancellation`**: Unrecoverable contract failure (`panic`) is distinct from cooperative task cancellation (`CancelToken`) (`SPEC-30 AXS-CONC-006`).
8. **`Arc<T>` $\neq$ `Mutex<T>` and `Rc<T>` $\neq$ `Arc<T>` (`REQ-CONC-098`, `REQ-CONC-142`, `REQ-ASY-166`)**: Shared ownership requires explicit container selection (`Rc<T>` for single-thread non-atomic reference counting; `Arc<T>` for thread-safe atomic reference counting). `Arc<T>` atomically synchronizes only its internal reference counters; it does **not** make access to the payload `T` atomic and does **not** grant mutable access (`mut_view<T>`) without an explicit interior synchronization primitive such as `Arc<Mutex<T>>`, `Arc<RwLock<T>>`, or `Arc<Atomic<T>>`.
9. **`Mutex<T>` $\neq$ `Atomic<T>` (`REQ-ASY-166`)**: `Mutex<T>` is a mutual-exclusion lock that guards an arbitrary payload `T` by issuing a scoped `MutexGuard<T>` (`mut_view<T>`), whereas `Atomic<T>` performs lock-free or target-atomic indivisible operations directly on a bounded scalar/pointer representation without issuing a capability guard or functioning as a general lock.

**AXS-ATM-005** (Prohibition of `mut_view<T>` conversion and mixed ordinary/atomic access; `REQ-ATM-003`, `REQ-CONC-013`, `REQ-CONC-062`, `REQ-CONC-063`, `REQ-CONC-064`, `REQ-CONC-069`, `REQ-CONC-092`, `REQ-CONC-108`, `REQ-CONC-173`, `0128 §3–4, §39`).
1. **No `Atomic<T>` $\to$ `mut_view<T>` or `view<T>` projection (`REQ-ATM-003`, `REQ-CONC-063`, `REQ-CONC-064`, `REQ-CONC-092`, `REQ-CONC-173`)**: Safe Axiom forbids projecting an ordinary mutable capability `mut_view<T>` or ordinary shared capability `view<T>` to the inner scalar payload of an `Atomic<T>`. An `Atomic<T>` does not dereference to `T`, does not coerce to `T` or `mut_view<T>`, and exposes no `.get_mut()` or field-projection escape in safe code. Any attempt to form `mut_view` of the inner storage of an `Atomic<T>` or to mutate `Atomic<T>` through ordinary assignment is rejected at compile time with `AX_CONC_ATOMIC_MUT_VIEW`.
2. **No implicit shared mutable references (`REQ-CONC-069`)**: All concurrent mutation of shared state in safe code MUST pass through an explicit synchronization API (`Atomic<T>.store` / `swap` / `compare_exchange` / `fetch_*`, `Mutex<T>.lock()`, or `RwLock<T>.write()`).
3. **No concurrent mixing of atomic and non-atomic access (`REQ-CONC-062`, `REQ-CONC-108`)**: Accessing the same memory location concurrently through an `Atomic<T>` operation in one execution context and a non-atomic read or write in another execution context without an intervening `Happens-Before` barrier is a data race. Safe code prevents this statically by encapsulating the storage inside `Atomic<T>` (`AXS-ATM-002`); in `unsafe` code, concurrent mixed atomic/ordinary access is undefined behavior trapped deterministically by the MIR interpreter oracle (`AX_UNSAFE_INTERP_UB`, exit code `125`, `AXS-ATM-052`).

**AXS-ATM-006** (`Volatile<T>` and MMIO are distinct from `Atomic<T>` and CPU fences; `REQ-ATM-001`, `REQ-ATM-031`, `REQ-CONC-059`, `REQ-CONC-060`, `REQ-CONC-178`, `0128 §30–32`, `tasks/0414 §70`).
1. **Physical memory and MMIO require `unsafe` and explicit `volatile` (`REQ-ATM-031`)**: Direct physical memory access and memory-mapped I/O (`MMIO`) registers reside outside ordinary RAM semantics (`External` / `Device` storage domain). Constructing or mapping an MMIO address requires `unsafe`, and reading or writing hardware registers requires explicit volatile operations (`Volatile<T>`, `Mmio<T>`, `MmioRO<T>`, `MmioWO<T>`, `volatile_load`, `volatile_store` per `SPEC-04 AXS-EXT-020, AXS-EXT-043`).
2. **`volatile` does NOT synchronize threads (`REQ-CONC-060`, `REQ-CONC-178`)**: A `volatile` load or store guarantees only that the compiler emits the exact machine memory instruction without eliding, merging, or reordering it relative to other volatile operations on the same thread. It does **not** guarantee multi-byte indivisibility across concurrent CPU cores where hardware requires a `LOCK` prefix or atomic instruction, and it establishes **zero** `Synchronizes-With` or `Happens-Before` edges between threads (`REQ-CONC-060`).
3. **`volatile` is distinct from atomic ordering and CPU fences (`REQ-ATM-001`, `REQ-ATM-031`, `REQ-CONC-059`)**: Where a hardware driver requires both an observable MMIO register access and a CPU/device memory barrier, the programmer must combine explicit `volatile` access with an explicit `fence` or architecture-specific device barrier (`tasks/0328 §39`, `AMEMLOW-41..48`).

**AXS-ATM-007** (`Atomic<T>` does not imply lock-free, wait-free, or fair execution; `REQ-ATM-014`, `REQ-ATM-015`, `REQ-CONC-061`, `REQ-CONC-121`, `REQ-CONC-201`, `0092 §11, §17`, `0128 §15–18`).
1. **Atomicity $\neq$ lock-free (`REQ-ATM-014`, `REQ-CONC-061`, `AATOM-29`)**: `Atomic<T>` guarantees indivisible operation semantics and memory ordering, but does not universally guarantee across all target architectures that every supported width is implemented via lock-free CPU instructions. On targets lacking native hardware atomics for a given width, the backend or target runtime may lower `Atomic<T>` to a striped spinlock or OS atomic helper while preserving the exact `Happens-Before` contract (`REQ-CONC-061`). Code that requires hardware lock-free execution MUST query `is_lock_free<T>()` (`AXS-ATM-013`, `REQ-CONC-121`).
2. **Lock-free $\neq$ wait-free (`REQ-ATM-015`, `AATOM-30`)**: Even when `Atomic<T>` is lock-free on a target (guaranteeing system-wide progress under contention), individual operations—such as `compare_exchange` retry loops or LL/SC sequences on RISC architectures—are not guaranteed to be wait-free (bounded per-thread step count under arbitrary contention).
3. **No implicit fairness, starvation-freedom, or deadlock-freedom (`REQ-CONC-201`)**: Core atomic primitives and spin loops do not guarantee FIFO fairness, starvation freedom under adversarial OS scheduling, or absence of logical livelock/deadlock in user-written protocols.

**AXS-ATM-008** (Raw pointer atomics `Atomic<*const T>` / `Atomic<*mut T>`, ABA non-mitigation, and explicit memory reclamation; `REQ-CONC-076`, `REQ-CONC-077`, `REQ-CONC-078`, `REQ-CONC-079`, `REQ-ATM-028`, `REQ-ATM-029`, `REQ-ATM-030`, `0092 §18–19, §24, §34`, `0128 §44–51`).
1. **Pointer atomicity $\neq$ pointee validity or ownership (`REQ-CONC-078`, `REQ-ATM-028`, `AATOM-31`)**: `Atomic<*const T>` and `Atomic<*mut T>` guarantee atomic reads, writes, and RMW updates of the **pointer address value** itself. They do **not** own the referent `T`, do **not** extend or validate the referent's lifetime, and do **not** make dereferencing the loaded `*const T` or `*mut T` safe (`REQ-CONC-078`, `REQ-ATM-028`). Dereferencing a pointer obtained from `Atomic<*mut T>.load(ord)` requires an `unsafe` block governed by an established validity, alignment, and aliasing contract (`SPEC-30 AXS-CONC-037`).
2. **No implicit memory reclamation (`REQ-CONC-077`, `AATOM-33`)**: Swapping or CAS-replacing a pointer in `Atomic<*mut T>` does not deallocate the old pointee or prevent concurrent readers from still observing the old address (`REQ-CONC-077`). Safe reclamation of nodes unlinked from lock-free structures requires explicit library/system reclamation protocols (such as `Arc<T>`, epoch-based reclamation, hazard pointers, or generational arena handles `Handle<T>`).
3. **No compiler ABA mitigation (`REQ-CONC-076`, `REQ-ATM-030`, `AATOM-32`)**: Primitive atomic operations (`compare_exchange`, `compare_exchange_weak`) compare bit patterns (such as raw pointer addresses $A \to B \to A$) and MUST NOT be assumed to detect or prevent the ABA problem (`REQ-ATM-030`). ABA prevention (via tagged pointers, version counters, `(index, generation)` handles, or hazard/epoch guards) is the responsibility of the lock-free data structure or library abstraction (`REQ-CONC-076`).
4. **Safe encapsulation boundary for lock-free structures (`REQ-CONC-079`, `REQ-ATM-029`)**: Lock-free queues, stacks, and maps built atop `Atomic<*mut T>` and `unsafe` pointer reclamation MUST encapsulate their raw pointers, ABA protection, and lifetime invariants behind a safe module/type boundary (`unsafe impl Send` / `unsafe impl Share`) before exposing operations to safe Axiom code.

---

## 2. `Atomic<T>` Lang-Item Type, Supported Widths, Alignment & Standard API

**AXS-ATM-010** (`Atomic<T>` lang-item declaration and target-supported element types; `T406`, `REQ-CONC-051`, `SPEC-04 AXS-EXT-020, AXS-EXT-023`).
`Atomic<T>` is declared in `std/sync/atomic.ax` as a compiler-recognized generic lang-item struct (`@lang("atomic")`):
```axiom
@lang("atomic")
pub struct Atomic<T> {
    v: T,
}
```
1. **Supported element types (`REQ-CONC-051`)**: Instantiating `Atomic<T>` is valid if and only if `T` is one of the following target-supported atomic scalar or raw-pointer types:
   - Boolean: `bool` (1-byte representation: `0u8` for `false`, `1u8` for `true`),
   - Signed integers: `i8`, `i16`, `i32`, `i64`, `isize`,
   - Unsigned integers: `u8`, `u16`, `u32`, `u64`, `usize`,
   - Raw pointers: `*const U`, `*mut U` (for any pointee type `U` where `*const U` / `*mut U` is a thin machine pointer of width `usize`).
2. **Rejection of unsupported types (`T406`)**: Instantiating `Atomic<T>` with any other type—including `i128`/`u128` (unless a future target profile explicitly enables double-word atomics), floating-point types (`f32`, `f64`), fat views/slices (`view<U>`, `mut_view<U>`, `Str`, `view<[U]>`), tuples, arrays, structs, or enums—is rejected at compile time by `compiler/types/typeck.ax` with `AX_CONC_INVALID_ATOMIC_TYPE`.
3. **Private inner field**: The backing field `v: T` of `Atomic<T>` is private to `std.sync.atomic` and compiler-intercepted; user code cannot read `atom.v`, write `atom.v = x`, or project `view(atom.v)` / `mut_view(atom.v)` (`AXS-ATM-005`).

**AXS-ATM-011** (Memory layout, natural alignment, and prohibition of `@repr(packed)` on `Atomic<T>`; `T406`, `0092 §10`, `0208 §28`, `tasks/0515 §133`, `REQ-ATM-013`).
1. **Size and natural alignment**: For every supported type `T`, `size_of<Atomic<T>>()` equals `size_of<T>()` and `align_of<Atomic<T>>()` equals `size_of<T>()` (natural alignment: 1 byte for `bool`/`i8`/`u8`, 2 bytes for `i16`/`u16`, 4 bytes for `i32`/`u32`, and 8 bytes for `i64`/`u64`/`isize`/`usize`/`*const U`/`*mut U` on 64-bit targets).
2. **No object header or hidden allocation (`0092 §3, AATOM-20`, `0208 AATOM-48`)**: `Atomic<T>` has zero runtime header overhead and performs no implicit heap allocation. An `Atomic<i64>` may reside inline in a stack frame, inside a struct, in `.data`/`.bss` `static` storage, or inside a heap allocation (`Arc<Atomic<i64>>`).
3. **Prohibition of misaligned or packed atomic fields (`0208 §28`)**: Hardware atomic instructions require naturally aligned addresses to guarantee indivisibility without split-cache-line traps or torn accesses (`REQ-ATM-013`). Placing an `Atomic<T>` (or a composite type containing an `Atomic<T>`) inside a `@repr(packed)` struct, or specifying `@align(N)` smaller than `size_of<T>()`, is rejected at compile time with `AX_CONC_INVALID_ATOMIC_ALIGNMENT`.

**AXS-ATM-012** (Ownership and `Send`/`Share` semantics of `Atomic<T>`; `T406`, `0208 §34–35, AATOM-43..44`, `SPEC-30 AXS-CONC-015`).
1. **`Atomic<T>: !Copy`**: `Atomic<T>` does **not** implement `Copy`. Implicit bitwise copying of an `Atomic<T>` is forbidden because duplicating an atomic storage location silently splits its modification order (`REQ-ATM-027`).
2. **Owned move and `into_inner`**: When an execution context holds unique ownership of an `Atomic<T>` binding, it may move the `Atomic<T>` by value to another binding or execution context (`let other = counter`), or consume it via `Atomic<T>.into_inner(self) -> T` without synchronization overhead because no concurrent `view<Atomic<T>>` can exist while moving an owned value (`0208 §34`).
3. **`Send` and `Share` derivation**:
   - For all supported integer and boolean types `T` (`bool`, `i8`..`i64`, `u8`..`u64`, `isize`, `usize`), `Atomic<T>` implements both `Send` and `Share` (`SPEC-30 AXS-CONC-015`).
   - For raw pointer atomics `Atomic<*const U>` and `Atomic<*mut U>`, the atomic container itself implements `Send` and `Share` in systems code so lock-free structures can share atomic pointer slots across threads, while reading or writing the raw pointer value and dereferencing it remains governed by `unsafe` raw-pointer rules (`AXS-ATM-008`, `REQ-CONC-078`, `REQ-ATM-028`).

**AXS-ATM-013** (Target lock-free capability query `is_lock_free`; `T406`, `REQ-ATM-016`, `REQ-CONC-061`, `REQ-CONC-121`, `0092 §11`, `0128 §18`, `0208 §15`).
`std.sync.atomic` provides a target-aware query function and associated method (`REQ-ATM-016`, `REQ-CONC-121`):
```axiom
pub fn is_lock_free<T>() -> bool
```
and `Atomic<T>.is_lock_free() -> bool`:
1. Returns `true` if and only if the target architecture natively executes all primitive atomic operations (`load`, `store`, `swap`, `compare_exchange`, `fetch_*`) on `Atomic<T>` using lock-free machine instructions without internal locks.
2. On `x86_64-windows` and `x86_64-linux` (and `aarch64-*` / `riscv64-*`), `is_lock_free<T>()` evaluates to `true` (and can be constant-folded by the compiler) for all 1-byte, 2-byte, 4-byte, and 8-byte supported atomic types (`bool`, `i8`..`i64`, `u8`..`u64`, `isize`, `usize`, `*const U`, `*mut U`).

**AXS-ATM-014** (Canonical `std/sync/atomic.ax` surface types and method signatures; `T406`, `REQ-ATM-004`, `REQ-ATM-005`, `REQ-ATM-017`, `REQ-ATM-021`, `REQ-ATM-023`, `0092 §4, §26`, `0128 §5–6, §19–29`, `0208 §2, §10–13`).
The module `std.sync.atomic` (`std/sync/atomic.ax`) defines the canonical types and operations below (using canonical Axiom syntax):

```axiom
module std.sync.atomic

pub enum Ordering {
    Relaxed,
    Acquire,
    Release,
    AcqRel,
    SeqCst,
}

pub struct CasResult<T> {
    pub ok: bool,
    pub val: T,
}

@lang("atomic")
pub struct Atomic<T> {
    v: T,
}
```

The canonical operations supported on `Atomic<T>` and in `std.sync.atomic` are:

| Operation / Function | Receiver / Signature | Allowed `T` | Semantic Summary |
|---|---|---|---|
| `Atomic.new(val: T) -> Atomic<T>` | Associated constructor | All supported `T` | Initializes a new owned `Atomic<T>` storage location with `val` |
| `atom.into_inner(self) -> T` | By-value owned `self` | All supported `T` | Consumes uniquely owned `Atomic<T>` and returns inner `T` |
| `atom.load(self: view<Atomic<T>>, ord: Ordering) -> T` | Shared `view<Atomic<T>>` | All supported `T` | Atomically reads and returns an ordinary value `T` (`REQ-ATM-004`) |
| `atom.store(self: view<Atomic<T>>, val: T, ord: Ordering)` | Shared `view<Atomic<T>>` | All supported `T` | Atomically writes `val` into storage (`REQ-ATM-005`) |
| `atom.swap(self: view<Atomic<T>>, val: T, ord: Ordering) -> T` | Shared `view<Atomic<T>>` | All supported `T` | Atomically replaces current value with `val` and returns previous `T` (`REQ-ATM-021`) |
| `atom.compare_exchange(self: view<Atomic<T>>, expected: T, desired: T, success: Ordering, failure: Ordering) -> CasResult<T>` | Shared `view<Atomic<T>>` | All supported `T` | Strong CAS: if current $==$ `expected`, writes `desired` (`ok = true, val = expected`); else returns current (`ok = false, val = current`); never fails spuriously (`REQ-ATM-017`, `REQ-ATM-018`) |
| `atom.compare_exchange_weak(self: view<Atomic<T>>, expected: T, desired: T, success: Ordering, failure: Ordering) -> CasResult<T>` | Shared `view<Atomic<T>>` | All supported `T` | Weak CAS: same as `compare_exchange` but permitted to fail spuriously (`ok = false, val = current`) even when current $==$ `expected` (`REQ-ATM-017`, `REQ-ATM-019`) |
| `atom.fetch_add(self: view<Atomic<T>>, val: T, ord: Ordering) -> T` | Shared `view<Atomic<T>>` | Integer `T` (`i8..i64`, `u8..u64`, `isize`, `usize`) | Atomically replaces current $c$ with $c +_{\text{wrap}} \text{val}$ and returns $c$ (`REQ-ATM-021`, `REQ-ATM-022`) |
| `atom.fetch_sub(self: view<Atomic<T>>, val: T, ord: Ordering) -> T` | Shared `view<Atomic<T>>` | Integer `T` | Atomically replaces current $c$ with $c -_{\text{wrap}} \text{val}$ and returns $c$ (`REQ-ATM-021`, `REQ-ATM-022`) |
| `atom.fetch_and(self: view<Atomic<T>>, val: T, ord: Ordering) -> T` | Shared `view<Atomic<T>>` | Integer `T` and `bool` | Atomically replaces current $c$ with $c \mathbin{\&} \text{val}$ and returns $c$ (`REQ-ATM-021`) |
| `atom.fetch_or(self: view<Atomic<T>>, val: T, ord: Ordering) -> T` | Shared `view<Atomic<T>>` | Integer `T` and `bool` | Atomically replaces current $c$ with $c \mathbin{|} \text{val}$ and returns $c$ (`REQ-ATM-021`) |
| `atom.fetch_xor(self: view<Atomic<T>>, val: T, ord: Ordering) -> T` | Shared `view<Atomic<T>>` | Integer `T` and `bool` | Atomically replaces current $c$ with $c \oplus \text{val}$ and returns $c$ (`REQ-ATM-021`) |
| `fence(ord: Ordering)` | Module function | — | Establishes an inter-thread hardware/memory ordering fence (`REQ-ATM-023`, `REQ-ATM-024`) |
| `compiler_fence(ord: Ordering)` | Module function | — | Establishes a single-thread compiler instruction reordering barrier without emitting CPU fence instructions (`REQ-CONC-179`) |
| `spin_loop_hint()` | Module function | — | Emits a processor spin-wait hint (`PAUSE` on x86-64) without altering memory semantics |
| `is_lock_free<T>() -> bool` | Module / associated fn | All supported `T` | Returns `true` if `Atomic<T>` is hardware lock-free on the target (`REQ-ATM-016`) |

*Note on method call syntax and type aliases*: Method calls on an owned local `counter: Atomic<i64>` or through a shared view `v: view<Atomic<i64>>` automatically pass `view<Atomic<i64>>` as the receiver (`counter.load(Ordering.Acquire)`). Standard type aliases `AtomicBool = Atomic<bool>`, `AtomicI8 = Atomic<i8>`, `AtomicI16 = Atomic<i16>`, `AtomicI32 = Atomic<i32>`, `AtomicI64 = Atomic<i64>`, `AtomicIsize = Atomic<isize>`, `AtomicU8 = Atomic<u8>`, `AtomicU16 = Atomic<u16>`, `AtomicU32 = Atomic<u32>`, `AtomicU64 = Atomic<u64>`, `AtomicUsize = Atomic<usize>`, and `AtomicPtr<T> = Atomic<*mut T>` may also be exported by `std.sync.atomic` for convenience.

**AXS-ATM-015** (Mandatory explicit `Ordering` parameter at low-level atomic boundaries; `0092 §8–9`, `0208 §9, AATOM-27..28`).
1. Every low-level atomic operation (`load`, `store`, `swap`, `compare_exchange`, `compare_exchange_weak`, `fetch_*`, `fence`, `compiler_fence`) requires an explicit `Ordering` argument (two `Ordering` arguments `success` and `failure` for `compare_exchange` and `compare_exchange_weak`). There are no single-argument overloads that silently default to `SeqCst` or `Relaxed`.
2. Furthermore, the `Ordering` argument(s) passed to any atomic method or fence MUST be a compile-time constant `Ordering` enumerator (`Ordering.Relaxed`, `Ordering.Acquire`, `Ordering.Release`, `Ordering.AcqRel`, or `Ordering.SeqCst`) so that `compiler/types/typeck.ax`, the MIR verifier, and the target backend can statically verify and lower the exact memory ordering (`0161 §30`, `0162 §12`). Passing a runtime-computed dynamic expression as an `Ordering` argument is rejected with `AX_CONC_INVALID_ATOMIC_ORDERING`.

**AXS-ATM-016** (Value-boundary semantics of `load` and `store`; `REQ-ATM-004`, `REQ-ATM-005`, `0092 §9`, `0128 §5–6`).
1. **`load` returns an ordinary value (`REQ-ATM-004`)**: `atom.load(ord)` reads the current value of `atom` indivisibly according to `ord` and returns an ordinary, non-atomic value of type `T`. Subsequent arithmetic or copying on the returned local binding `let x: T = atom.load(Ordering.Acquire)` uses ordinary register/value semantics.
2. **`store` consumes an ordinary value (`REQ-ATM-005`)**: `atom.store(val, ord)` evaluates the ordinary value `val: T` and writes it indivisibly to `atom` according to `ord`, establishing `Release` publication constraints for preceding memory accesses when `ord` is `Release` or `SeqCst`.
3. **No implicit conversion (`0092 §9`)**: There is no implicit conversion `Atomic<T> -> T` or `T -> Atomic<T>`.

**AXS-ATM-017** (Indivisible RMW execution and wrapping two's-complement integer arithmetic; `REQ-ATM-021`, `REQ-ATM-022`, `0128 §23–25, §66 AATOM-39`).
1. **Single modification-order step (`REQ-ATM-021`)**: Every primitive read-modify-write (`RMW`) operation (`swap`, `fetch_add`, `fetch_sub`, `fetch_and`, `fetch_or`, `fetch_xor`, and the success path of `compare_exchange` / `compare_exchange_weak`) executes as a single indivisible step in the target `Atomic<T>` object's modification order: no other atomic write to the same location can interleave between the RMW's read of the old value $v_{\text{old}}$ and its write of the new value $v_{\text{new}}$, and the operation always returns $v_{\text{old}}$.
2. **Wrapping two's-complement arithmetic for integer RMW (`REQ-ATM-022`, `AATOM-39`)**: Unlike ordinary `+` and `-` in Axiom (which perform checked overflow traps by default per `SPEC-03`), `fetch_add` and `fetch_sub` on integer `Atomic<T>` types unconditionally use **wrapping two's-complement arithmetic modulo $2^W$** where $W \in \{8, 16, 32, 64\}$ is the bit-width of `T`:
   - For unsigned `T` (`u8`, `u16`, `u32`, `u64`, `usize`): $v_{\text{new}} = (v_{\text{old}} \pm \text{val}) \bmod 2^W$. For example, on `Atomic<u8>`, `fetch_add(1, Ordering.Relaxed)` when $v_{\text{old}} = 255$ stores $0$ and returns $255$.
   - For signed `T` (`i8`, `i16`, `i32`, `i64`, `isize`): $v_{\text{new}}$ is computed in two's-complement representation modulo $2^W$ without trapping on signed overflow (`i64.MAX` $+_{\text{wrap}} 1 = $ `i64.MIN`).
   - Primitive atomic RMW operations **never** panic or trap on arithmetic overflow (`0128 §25`).
3. **Type restrictions on `fetch_add` / `fetch_sub` vs bitwise RMW**: `fetch_add` and `fetch_sub` are valid only on integer `Atomic<T>` (`i8`..`i64`, `u8`..`u64`, `isize`, `usize`). Calling `fetch_add`/`fetch_sub` on `Atomic<bool>` or `Atomic<*mut U>`, or calling `fetch_and`/`fetch_or`/`fetch_xor` on `Atomic<*mut U>`, is rejected at compile time (`AX_CONC_INVALID_ATOMIC_TYPE`).

**AXS-ATM-018** (Strong vs. weak compare-and-exchange semantics; `REQ-ATM-017`, `REQ-ATM-018`, `REQ-ATM-019`, `0092 §26–27`, `0128 §19–22`, `0208 §10–12`).
Both `compare_exchange` and `compare_exchange_weak` atomically compare the current value $v_{\text{cur}}$ of `Atomic<T>` with `expected` (by bitwise/value equality of the scalar or pointer representation) and return `CasResult<T> { ok, val }`:
1. **Strong CAS (`compare_exchange`, `REQ-ATM-018`)**:
   - If $v_{\text{cur}} == \text{expected}$, it atomically replaces the stored value with `desired` under `success` ordering and returns `CasResult { ok: true, val: expected }`. It is **forbidden** from failing spuriously when $v_{\text{cur}} == \text{expected}$ (`REQ-ATM-018`).
   - If $v_{\text{cur}} \neq \text{expected}$, it leaves the stored value unchanged, performs an atomic load observation under `failure` ordering, and returns `CasResult { ok: false, val: v_cur }`.
2. **Weak CAS (`compare_exchange_weak`, `REQ-ATM-019`)**:
   - Has the same signature and result structure as `compare_exchange`, except that even when $v_{\text{cur}} == \text{expected}$, the operation is permitted to fail spuriously (treating the access as a failed CAS observation under `failure` ordering and returning `CasResult { ok: false, val: v_cur }` without writing `desired`).
   - On LL/SC architectures (such as AArch64 or RISC-V), `compare_exchange_weak` lowers to a single LL/SC attempt without an inner retry loop, whereas `compare_exchange` loops on spurious SC failure. On `x86-64`, both lower to `LOCK CMPXCHG`, while the MIR interpreter oracle deterministically exercises spurious failure on `compare_exchange_weak` (`AXS-ATM-054`).

**AXS-ATM-019** (Hardware memory `fence` vs. `compiler_fence` vs. `spin_loop_hint`; `REQ-ATM-023`, `REQ-ATM-024`, `REQ-CONC-075`, `REQ-CONC-179`, `0128 §26–29`, `0208 §23–24`, `tasks/0328 §13–14`).
Axiom strictly separates CPU/inter-thread memory fences from single-thread compiler reordering barriers (`REQ-CONC-179`):
1. **`fence(ord: Ordering)` (`REQ-ATM-023`, `REQ-ATM-024`, `REQ-CONC-075`)**: A hardware and compiler synchronization barrier that establishes execution ordering constraints across threads without reading from or writing to any specific memory location (`REQ-ATM-024`). Valid orderings are `Acquire`, `Release`, `AcqRel`, and `SeqCst` (`AXS-ATM-026`). The compiler optimizer and target backend MUST preserve `fence(ord)` semantics (`REQ-CONC-075`).
2. **`compiler_fence(ord: Ordering)` (`REQ-CONC-179`)**: Restricts only the **compiler** (MIR/OptIR passes and LIR/machine instruction scheduling) from reordering memory accesses across the barrier according to `ord` (`Acquire`, `Release`, `AcqRel`, `SeqCst`), while emitting **zero CPU instructions** at the target machine level. `compiler_fence` does not synchronize different hardware threads; it is intended for single-CPU interrupt/signal handler ordering (`SPEC-30 AXS-CONC-003`).
3. **`spin_loop_hint()`**: Hints to the processor that the calling execution context is in a busy-wait spin loop (emitting `PAUSE` `F3 90` on x86-64). It is a no-op with respect to memory values and `Happens-Before` relations.

---

## 3. Memory Orderings, Validation Matrix & Synchronization Semantics

**AXS-ATM-020** (Five canonical memory orderings; `REQ-CONC-052`, `REQ-ATM-032`, `0092 §5`, `0128 §7–12`, `0208 §3–8`, `tasks/0328 §5`).
Axiom defines exactly five memory orderings in `std.sync.atomic.Ordering` (`REQ-CONC-052`, `REQ-ATM-032`):
1. `Ordering.Relaxed`
2. `Ordering.Acquire`
3. `Ordering.Release`
4. `Ordering.AcqRel`
5. `Ordering.SeqCst`

`Consume` ordering (`memory_order_consume` in C11) is intentionally excluded from Axiom Core v1 (`tasks/0328 §5`, `tasks/0515 AMEM-82`); dependency-ordered reads use `Ordering.Acquire`.

**AXS-ATM-021** (Per-location modification order `mo` and coherence axioms; `REQ-ATM-012`, `REQ-ATM-013`, `0128 §13–14`).
For every distinct `Atomic<T>` storage instance $X$, all atomic write operations (`new` initialization, `store`, `swap`, `fetch_*`, and successful `compare_exchange` / `compare_exchange_weak`) on $X$ in an execution are totally ordered by a per-location **modification order** $\prec_{\text{mo}}^X$ (`REQ-ATM-012`). Every atomic operation on $X$ is indivisible (`REQ-ATM-013`) and obeys the four standard per-location coherence axioms with respect to `Happens-Before` ($\prec_{\text{hb}}$):
1. **Write-Write Coherence (`CoWW`)**: If two atomic writes $W_1$ and $W_2$ to $X$ satisfy $W_1 \prec_{\text{hb}} W_2$, then $W_1 \prec_{\text{mo}}^X W_2$.
2. **Read-Read Coherence (`CoRR`)**: If two atomic reads $R_1$ and $R_2$ from $X$ satisfy $R_1 \prec_{\text{hb}} R_2$, and $R_1$ reads from write $W_1$ while $R_2$ reads from write $W_2$, then either $W_1 = W_2$ or $W_1 \prec_{\text{mo}}^X W_2$ (a later read on a happens-before path can never observe an earlier store in $\prec_{\text{mo}}^X$).
3. **Read-Write Coherence (`CoRW`)**: If an atomic read $R$ from $X$ happens-before an atomic write $W_2$ to $X$ ($R \prec_{\text{hb}} W_2$), and $R$ reads from $W_1$, then $W_1 \prec_{\text{mo}}^X W_2$.
4. **Write-Read Coherence (`CoWR`)**: If an atomic write $W_1$ to $X$ happens-before an atomic read $R$ from $X$ ($W_1 \prec_{\text{hb}} R$), and $R$ reads from $W_2$, then either $W_1 = W_2$ or $W_1 \prec_{\text{mo}}^X W_2$ ($R$ cannot read a store overwritten in modification order before $W_1$).

**AXS-ATM-022** (`Relaxed` ordering semantics and no-silent-upgrade rule; `REQ-CONC-053`, `REQ-ATM-006`, `REQ-ATM-009`, `REQ-CONC-175`, `0128 §7, §10, AATOM-22`).
1. **Indivisibility + modification order only (`REQ-CONC-053`, `REQ-ATM-006`, `REQ-CONC-175`)**: An atomic operation with `Ordering.Relaxed` guarantees indivisibility and per-location coherence (`AXS-ATM-021`) on that single `Atomic<T>` location, but establishes **no** `Synchronizes-With` ($\prec_{\text{sw}}$) edge and imposes no ordering constraints on surrounding accesses to other ordinary or atomic memory locations.
2. **No silent upgrade by compiler (`REQ-ATM-009`)**: The compiler semantic analyzer and MIR optimizer MUST NOT automatically upgrade `Ordering.Relaxed` to `Ordering.Acquire` or `Ordering.Release` in the IR (`0128 §10`), nor may the concurrency verifier assume that a `Relaxed` operation publishes ordinary memory writes (`REQ-CONC-175`).

**AXS-ATM-023** (`Release` and `Acquire` synchronization and release sequences; `REQ-CONC-054`, `REQ-CONC-055`, `REQ-ATM-007`, `REQ-ATM-008`, `REQ-ATM-026`, `0128 §8–9, §38, AATOM-23..24`).
1. **`Release` publication (`REQ-CONC-055`, `REQ-ATM-008`, `AATOM-24`)**: An atomic write $W_{\text{rel}}$ (`store` with `Release` or `SeqCst`, or RMW with `Release`, `AcqRel`, or `SeqCst`) on location $X$ acts as a publication boundary: no ordinary or atomic memory read or write sequenced-before $W_{\text{rel}}$ ($A \prec_{\text{sb}} W_{\text{rel}}$) may be reordered after $W_{\text{rel}}$.
2. **`Acquire` observation (`REQ-CONC-054`, `REQ-ATM-007`, `AATOM-23`)**: An atomic read $R_{\text{acq}}$ (`load` with `Acquire` or `SeqCst`, or RMW/failed-CAS with `Acquire`, `AcqRel`, or `SeqCst`) on location $X$ acts as an observation boundary: no ordinary or atomic memory read or write sequenced-after $R_{\text{acq}}$ ($R_{\text{acq}} \prec_{\text{sb}} B$) may be reordered before $R_{\text{acq}}$.
3. **`Synchronizes-With` and `Happens-Before` (`REQ-ATM-026`)**: When $R_{\text{acq}}$ on $X$ observes the value written by $W_{\text{rel}}$ on $X$ (or observes any write in the **release sequence** headed by $W_{\text{rel}}$—defined as $W_{\text{rel}}$ followed by any contiguous chain of atomic RMW operations on $X$ of any ordering, including `Relaxed`), $W_{\text{rel}}$ *synchronizes-with* $R_{\text{acq}}$ ($W_{\text{rel}} \prec_{\text{sw}} R_{\text{acq}}$). By transitivity (`SPEC-30 AXS-CONC-040`), every memory write $A \prec_{\text{sb}} W_{\text{rel}}$ happens-before every memory read or write $B$ where $R_{\text{acq}} \prec_{\text{sb}} B$ ($A \prec_{\text{hb}} B$), guaranteeing that $B$ observes $A$ (`REQ-CONC-054`, `REQ-ATM-026`).

**AXS-ATM-024** (`AcqRel` bidirectional RMW ordering; `REQ-CONC-056`, `REQ-ATM-010`, `0128 §11, AATOM-25`).
An atomic read-modify-write operation (`swap`, `fetch_*`, or the success path of `compare_exchange` / `compare_exchange_weak`) with `Ordering.AcqRel` simultaneously performs an `Acquire` read on the observed old value and a `Release` write of the new value (`REQ-CONC-056`, `REQ-ATM-010`). Consequently, it both synchronizes-with prior `Release` writes in the location's modification order and publishes all preceding memory accesses of the current execution context to subsequent `Acquire` readers.

**AXS-ATM-025** (`SeqCst` total global order and non-weakening contract; `REQ-CONC-057`, `REQ-ATM-011`, `REQ-CONC-177`, `0128 §12, AATOM-26`).
1. **Global sequentially consistent total order $\prec_S$ (`REQ-CONC-177`)**: In addition to satisfying all `Acquire` (for loads), `Release` (for stores), and `AcqRel` (for RMWs) guarantees, every atomic operation and `fence` marked `Ordering.SeqCst` participates in a single global total order $\prec_S$ across all `SeqCst` actions in the program (`REQ-CONC-177`, `AATOM-26`):
   - $\prec_S$ is consistent with `Happens-Before`: if $A \prec_{\text{hb}} B$ for two `SeqCst` operations, then $A \prec_S B$.
   - $\prec_S$ is consistent with every per-location modification order $\prec_{\text{mo}}^X$.
   - Any `SeqCst` load $R$ on $X$ observes either the latest `SeqCst` write $W$ to $X$ preceding $R$ in $\prec_S$, or a non-`SeqCst` write to $X$ that does not happen-before $W$.
   - In particular, in the Store Buffering (`SB`) litmus pattern (`x.store(1, SeqCst); r0 = y.load(SeqCst)` $\parallel$ `y.store(1, SeqCst); r1 = x.load(SeqCst)` with initial `x = 0, y = 0`), the outcome `r0 == 0 && r1 == 0` is **forbidden** under `SeqCst`.
2. **Forbidden weakening (`REQ-CONC-057`, `REQ-ATM-011`)**: Compiler optimization passes and target code generation MUST NOT weaken `Ordering.SeqCst` to `AcqRel`, `Acquire`, `Release`, or `Relaxed` (`REQ-CONC-057`, `REQ-ATM-011`).

**AXS-ATM-026** (Compile-time `Ordering` legality matrix & CAS failure-ordering rules; `T406`, `REQ-CONC-058`, `REQ-ATM-020`, `0092 §7`, `0128 §22`, `0208 §13, §39`).
`compiler/types/typeck.ax` and `compiler/verify/verifier.ax` MUST statically validate the `Ordering` argument(s) of every atomic operation and fence against the normative matrix below. Any disallowed ordering is rejected at compile time with `AX_CONC_INVALID_ATOMIC_ORDERING`:

| Operation | `Relaxed` | `Acquire` | `Release` | `AcqRel` | `SeqCst` | Rejection Rule Summary |
|---|---|---|---|---|---|---|
| `atom.load(ord)` | **Valid** | **Valid** | **ERROR** | **ERROR** | **Valid** | Load performs no write; `Release` and `AcqRel` are rejected (`0208 §39 AXM002/AXM003`) |
| `atom.store(val, ord)` | **Valid** | **ERROR** | **Valid** | **ERROR** | **Valid** | Store performs no read; `Acquire` and `AcqRel` are rejected |
| `atom.swap(val, ord)` / `atom.fetch_*(val, ord)` | **Valid** | **Valid** | **Valid** | **Valid** | **Valid** | RMW performs both read and write; all 5 orderings are valid |
| `compare_exchange[_weak]` `success` ordering | **Valid** | **Valid** | **Valid** | **Valid** | **Valid** | Successful CAS is an RMW; all 5 orderings are valid |
| `compare_exchange[_weak]` `failure` ordering | **Valid** | **Valid** | **ERROR** | **ERROR** | **Valid*** | Failed CAS performs only a read: `Release` and `AcqRel` are unconditionally rejected (`REQ-ATM-020`), AND `failure` cannot be stronger than `success` (`REQ-CONC-058`, see below) |
| `fence(ord)` / `compiler_fence(ord)` | **ERROR** | **Valid** | **Valid** | **Valid** | **Valid** | A `Relaxed` fence has no ordering effect and is rejected (`REQ-ATM-023`) |

**CAS `(success, failure)` pair constraint (`REQ-CONC-058`, `REQ-ATM-020`, `0208 §13`)**:
1. The `failure` ordering of `compare_exchange` and `compare_exchange_weak` MUST NEVER be `Ordering.Release` or `Ordering.AcqRel` (`REQ-ATM-020`).
2. The `failure` ordering MUST NOT be stronger than the `success` ordering (`REQ-CONC-058`):
   - If `success == Ordering.Relaxed` or `success == Ordering.Release`, then `failure` may only be `Ordering.Relaxed` (since `Release` has no acquire component, `failure: Acquire` or `failure: SeqCst` is stronger on the read path and is rejected with `AX_CONC_INVALID_ATOMIC_ORDERING`).
   - If `success == Ordering.Acquire` or `success == Ordering.AcqRel`, then `failure` may be `Ordering.Relaxed` or `Ordering.Acquire` (`failure: SeqCst` is rejected).
   - If `success == Ordering.SeqCst`, then `failure` may be `Ordering.Relaxed`, `Ordering.Acquire`, or `Ordering.SeqCst`.

**AXS-ATM-027** (Explicit `fence` synchronization semantics; `REQ-ATM-023`, `REQ-ATM-024`, `REQ-CONC-075`, `0128 §26–28`).
A `fence(ord)` establishes `Synchronizes-With` ($\prec_{\text{sw}}$) edges in combination with atomic operations on any atomic location $X$ as follows (`REQ-ATM-023`, `REQ-ATM-024`):
1. **Fence-to-Atomic (`Release` fence $\prec_{\text{sw}}$ `Acquire` read)**: If a `fence(Release | AcqRel | SeqCst)` $F_{\text{rel}}$ is sequenced-before an atomic write $W$ to $X$ ($F_{\text{rel}} \prec_{\text{sb}} W$, even if $W$ is `Relaxed`), and an atomic read $R_{\text{acq}}$ (`Acquire | AcqRel | SeqCst`) on $X$ observes $W$ (or its release sequence), then $F_{\text{rel}} \prec_{\text{sw}} R_{\text{acq}}$.
2. **Atomic-to-Fence (`Release` write $\prec_{\text{sw}}$ `Acquire` fence)**: If an atomic write $W_{\text{rel}}$ (`Release | AcqRel | SeqCst`) on $X$ is observed by an atomic read $R$ on $X$ (even if $R$ is `Relaxed`), and $R$ is sequenced-before a `fence(Acquire | AcqRel | SeqCst)` $F_{\text{acq}}$ ($R \prec_{\text{sb}} F_{\text{acq}}$), then $W_{\text{rel}} \prec_{\text{sw}} F_{\text{acq}}$.
3. **Fence-to-Fence (`Release` fence $\prec_{\text{sw}}$ `Acquire` fence)**: If $F_{\text{rel}} \prec_{\text{sb}} W$ on $X$, $R$ on $X$ observes $W$ (or its release sequence), and $R \prec_{\text{sb}} F_{\text{acq}}$, then $F_{\text{rel}} \prec_{\text{sw}} F_{\text{acq}}$.
4. **`SeqCst` Fence**: A `fence(Ordering.SeqCst)` participates in the global total order $\prec_S$ (`AXS-ATM-025`) and acts as a full store-load memory barrier preventing any `SeqCst` or ordinary write sequenced-before the fence from being reordered after any `SeqCst` or ordinary read sequenced-after the fence.

**AXS-ATM-028** (Heterogeneous / GPU execution-domain `AtomicScope` extension point; `0128 §63–64, AATOM-38`, `0208 §27, AATOM-50`).
In CPU/host code, all `Atomic<T>` and `fence` operations default to `AtomicScope.System` (coherent across all CPU hardware threads in the process). For heterogeneous GPU/device kernels (`E22.1`–`E22.3`, `SPEC-04 AXS-EXT-051`), the LIR and MIR atomic metadata include an explicit `scope` field (`Thread = 0`, `Workgroup = 1`, `Device = 2`, `System = 3`, defaulting to `System` on host targets) without altering the five core `Ordering` semantics (`AATOM-38`, `AATOM-50`).

---

## 4. MIR `Atomic` Statement Lowering, Verifier & Optimizer Preservation Contract

**AXS-ATM-030** (Dedicated MIR `Atomic` statement representation; `T406`, `SPEC-04 AXS-EXT-043`, `REQ-MIR-144`, `REQ-CONC-133`, `0161 §30`).
1. **No lowering to ordinary `MIR_STMT_ASSIGN` (`REQ-CONC-133`, `REQ-MIR-144`)**: Calls to `Atomic<T>` methods (`load`, `store`, `swap`, `compare_exchange`, `compare_exchange_weak`, `fetch_add`, `fetch_sub`, `fetch_and`, `fetch_or`, `fetch_xor`) and `std.sync.atomic.{fence, compiler_fence, spin_loop_hint}` MUST NOT be lowered to ordinary MIR `Assign` reads/writes (`0161 §30`). Only `Atomic.new(val)` and `atom.into_inner()` (which construct or consume an unshared, uniquely owned value before/after concurrent sharing) lower to aggregate construction / field move.
2. **MIR statement kinds (`compiler/mir/mir.ax`)**: Following `SPEC-04 AXS-EXT-043`, `compiler/mir/mir.ax` defines `MIR_STMT_ATOMIC` alongside `MIR_STMT_ASSIGN`, `MIR_STMT_STORAGE_LIVE`, `MIR_STMT_STORAGE_DEAD`, and `MIR_STMT_DROP`:
   - `atomic_op: u8`:
     - `MIR_ATOMIC_LOAD = 0u8`
     - `MIR_ATOMIC_STORE = 1u8`
     - `MIR_ATOMIC_SWAP = 2u8`
     - `MIR_ATOMIC_ADD = 3u8` (`fetch_add`)
     - `MIR_ATOMIC_SUB = 4u8` (`fetch_sub`)
     - `MIR_ATOMIC_AND = 5u8` (`fetch_and`)
     - `MIR_ATOMIC_OR = 6u8` (`fetch_or`)
     - `MIR_ATOMIC_XOR = 7u8` (`fetch_xor`)
     - `MIR_ATOMIC_CMPXCHG = 8u8` (`compare_exchange`, strong)
     - `MIR_ATOMIC_CMPXCHG_WEAK = 9u8` (`compare_exchange_weak`, weak)
     - `MIR_ATOMIC_FENCE = 10u8` (`fence`)
     - `MIR_ATOMIC_COMPILER_FENCE = 11u8` (`compiler_fence`)
     - `MIR_ATOMIC_SPIN_HINT = 12u8` (`spin_loop_hint`)
   - `ordering: u8` (and `fail_ordering: u8` for `CMPXCHG` / `CMPXCHG_WEAK`):
     - `MIR_ORDER_RELAXED = 0u8`
     - `MIR_ORDER_ACQUIRE = 1u8`
     - `MIR_ORDER_RELEASE = 2u8`
     - `MIR_ORDER_ACQ_REL = 3u8`
     - `MIR_ORDER_SEQ_CST = 4u8`
   - `place`: Destination `MirPlace` receiving the result (`T` for `load`/`swap`/`fetch_*`, `CasResult<T>` for `CMPXCHG`/`CMPXCHG_WEAK`, unused for `store`/`fence`/`compiler_fence`/`spin_loop_hint`).
   - `atomic_src` / operands: Target atomic address/place operand (`view<Atomic<T>>` or `*mut Atomic<T>`), value operand `val: MirOperand` (for `store`, `swap`, `fetch_*`, or `expected` for CAS), and second value operand `desired: MirOperand` (for `CMPXCHG` / `CMPXCHG_WEAK`).

**AXS-ATM-031** (Canonical MIR text format for `inspect --emit=mir` and `--emit=mir-opt`; `T406`).
To ensure deterministic inspection dumps (`tests/mir/atomics/*.ax`), `compiler/mir/mir.ax` prints `MIR_STMT_ATOMIC` statements in the following canonical textual forms (where `<ord>` is `Relaxed`, `Acquire`, `Release`, `AcqRel`, or `SeqCst`):
- `Load`: `<dst> = atomic_load <ord> <ptr_op>`
- `Store`: `atomic_store <ord> <ptr_op>, <val_op>`
- `Swap`: `<dst> = atomic_rmw xchg <ord> <ptr_op>, <val_op>`
- `FetchAdd`: `<dst> = atomic_rmw add <ord> <ptr_op>, <val_op>`
- `FetchSub`: `<dst> = atomic_rmw sub <ord> <ptr_op>, <val_op>`
- `FetchAnd`: `<dst> = atomic_rmw and <ord> <ptr_op>, <val_op>`
- `FetchOr`: `<dst> = atomic_rmw or <ord> <ptr_op>, <val_op>`
- `FetchXor`: `<dst> = atomic_rmw xor <ord> <ptr_op>, <val_op>`
- `CompareExchange`: `<dst> = atomic_cmpxchg <succ_ord> <fail_ord> <ptr_op>, <expected_op>, <desired_op>`
- `CompareExchangeWeak`: `<dst> = atomic_cmpxchg_weak <succ_ord> <fail_ord> <ptr_op>, <expected_op>, <desired_op>`
- `Fence`: `atomic_fence <ord>`
- `CompilerFence`: `compiler_fence <ord>`
- `SpinLoopHint`: `spin_loop_hint`

**AXS-ATM-032** (MIR verifier invariants on `MIR_STMT_ATOMIC`; `T406`, `compiler/verify/verifier.ax`).
The MIR verifier (`compiler/verify/verifier.ax`) independently re-verifies every `MIR_STMT_ATOMIC` statement (`INV-PIPE-002`, `INV-PIPE-003`):
1. The target atomic operand must refer to an `Atomic<T>` place or `view<Atomic<T>>` where `T` satisfies `AXS-ATM-010` (1/2/4/8-byte integer, `bool`, or raw pointer) with natural alignment (`AXS-ATM-011`).
2. The `ordering` (and `fail_ordering` on CAS) must satisfy the legality matrix of `AXS-ATM-026`.
3. For `load`, `swap`, and `fetch_*`, the destination `place` must have type `T` and be writable; for `CMPXCHG` and `CMPXCHG_WEAK`, the destination `place` must have type `CasResult<T>` (`{ ok: bool, val: T }`).
4. No `MIR_RVALUE_REF` with `MIR_BORROW_MUT` (`mut_view<T>`) may project into the inner storage field of `Atomic<T>` (`AXS-ATM-005`).

**AXS-ATM-033** (Optimizer preservation contract for MIR `Atomic` statements; `T406`, `REQ-CONC-014`, `REQ-CONC-091`, `REQ-ATM-009`, `REQ-ATM-011`, `REQ-ATM-025`, `REQ-MIR-144`, `REQ-ASY-062`, `0128 §34–35, AATOM-27, AATOM-40`).
Every MIR and OptIR optimization pass—specifically including `compiler/opt/const_fold.ax`, `compiler/opt/dce.ax`, CSE, GVN, LICM, DSE, and async coroutine state-machine optimization (`REQ-ASY-062`)—MUST obey the following rules on `MIR_STMT_ATOMIC`:
1. **No dead-code elimination (`dce.ax`, `REQ-ATM-025`, `REQ-MIR-144`)**: A `MIR_STMT_ATOMIC` statement has observable memory and synchronization side effects. Even if the destination local `<dst>` of an `atomic_load`, `atomic_rmw`, or `atomic_cmpxchg` is never read again, `dce.ax` MUST NOT delete the `MIR_STMT_ATOMIC` statement or mark its operand locals as dead.
2. **No constant folding or load-to-load coalescing (`const_fold.ax`, `REQ-MIR-144`, `0128 §34`)**: `const_fold.ax` (and CSE/GVN) MUST NOT fold an `atomic_load` from a known prior `atomic_store` or `Atomic.new`, MUST NOT merge two consecutive `a.load(Acquire)` calls into one load, and MUST NOT coalesce two `a.store(v, Release)` calls in general concurrent code (`REQ-ATM-025`).
3. **No ordering weakening or strengthening (`REQ-CONC-014`, `REQ-CONC-091`, `REQ-ATM-009`, `REQ-ATM-011`)**: Optimization passes MUST preserve the exact `ordering` and `fail_ordering` fields on every `MIR_STMT_ATOMIC` (`Relaxed` is never upgraded to `Acquire`/`Release`; `SeqCst` is never weakened to `AcqRel`/`Acquire`/`Release`/`Relaxed`).
4. **Reordering barrier for surrounding ordinary memory (`SPEC-30 AXS-CONC-045`, `REQ-ASY-062`)**:
   - Ordinary memory reads and writes MUST NOT be hoisted above an `Acquire`, `AcqRel`, or `SeqCst` `MIR_STMT_ATOMIC` (`load`, `rmw`, `cmpxchg`, `fence`, `compiler_fence`).
   - Ordinary memory reads and writes MUST NOT be sunk below a `Release`, `AcqRel`, or `SeqCst` `MIR_STMT_ATOMIC` (`store`, `rmw`, `cmpxchg`, `fence`, `compiler_fence`).
   - In async functions (`REQ-ASY-062`), Future state merging, scalarization, and `.await` fusion MUST preserve the exact execution sequence and ordering of all `MIR_STMT_ATOMIC` statements relative to suspension points, panics, drop cleanups, and FFI calls.

**AXS-ATM-034** (Scheduling yield-point hook compatibility around atomics; `REQ-ASY-061`, `0127 §59`).
Because every atomic operation and fence is preserved as an explicit `MIR_STMT_ATOMIC` node (`AXS-ATM-030`), concurrency sanitizers (`E17.6`) and the MIR interpreter oracle's deterministic schedule explorer (`T408`, `AXS-ATM-053`) may treat each `MIR_STMT_ATOMIC` statement as a well-defined scheduling yield/interleaving point to explore concurrent execution schedules and detect data races without altering language semantics (`REQ-ASY-061`).


---

## 5. LIR Atomic Operations & x86-64 Instruction Selection / Encoding

**AXS-ATM-040** (Dedicated LIR atomic instruction kinds & metadata; `T407`, `SPEC-04 AXS-EXT-051`, `REQ-CONC-134`, `0162 §30`, `tasks/0328 §7`).
1. **Explicit LIR representation (`REQ-CONC-134`)**: `compiler/lir/lir.ax` lowers `MIR_STMT_ATOMIC` statements (`AXS-ATM-030`) into dedicated LIR atomic instructions rather than generic load/store/ALU operations (`0162 §30`, `tasks/0328 §7`):
   - `LIR_INST_ATOMIC_LOAD`: atomic read of width `bit_width` (`8`, `16`, `32`, `64`) with `ordering` (`Relaxed`, `Acquire`, `SeqCst`).
   - `LIR_INST_ATOMIC_STORE`: atomic write of width `bit_width` (`8`, `16`, `32`, `64`) with `ordering` (`Relaxed`, `Release`, `SeqCst`).
   - `LIR_INST_ATOMIC_RMW`: atomic read-modify-write of width `bit_width` (`8`, `16`, `32`, `64`), `rmw_op` (`Xchg = 0`, `Add = 1`, `Sub = 2`, `And = 3`, `Or = 4`, `Xor = 5`), and `ordering` (`Relaxed`, `Acquire`, `Release`, `AcqRel`, `SeqCst`).
   - `LIR_INST_ATOMIC_CAS`: atomic compare-and-exchange of width `bit_width` (`8`, `16`, `32`, `64`), `is_weak: bool`, `ordering` (`success`), and `fail_ordering` (`failure`), producing `CasResult<T>` (`ok: bool`, `val: T`).
   - `LIR_INST_FENCE`: memory or compiler fence with `is_compiler_only: bool` and `ordering` (`Acquire`, `Release`, `AcqRel`, `SeqCst`).
   - `LIR_INST_PAUSE`: processor spin-wait hint (`spin_loop_hint()`).
2. **Metadata preservation (`SPEC-04 AXS-EXT-051`)**: Every LIR atomic node carries `(ordering, fail_ordering, rmw_op, is_weak, bit_width, align, addr_space, scope)` in its auxiliary metadata (`LirAtomicMeta`), where `align == bit_width / 8`, `addr_space == 0` (flat host memory), and `scope == AtomicScope.System` (`3u8`) on host targets (`AXS-ATM-028`).

**AXS-ATM-041** (LIR optimization & instruction-scheduling barrier contract and textual dump; `T407`, `REQ-CONC-135`, `0162 §30, ALIR-23`).
1. **Preservation up to instruction selection (`REQ-CONC-135`, `ALIR-23`)**: LIR peephole, copy-propagation, dead-store, and machine-instruction scheduling passes (`SPEC-77`) MUST preserve `LIR_INST_ATOMIC_*`, `LIR_INST_FENCE`, and `LIR_INST_PAUSE` nodes and their exact memory orderings up to target instruction selection. No LIR pass may reorder memory loads or stores across an `Acquire`, `Release`, `AcqRel`, or `SeqCst` LIR atomic or fence instruction (`REQ-CONC-135`).
2. **Canonical LIR dump format (`inspect --emit=lir`)**: For deterministic verification in `tests/lir/atomics/*.ax`, `compiler/lir/lir.ax` formats LIR atomic instructions as:
   - `vDst = atomic_load.<w> <ord> [vPtr]`
   - `atomic_store.<w> <ord> [vPtr], vVal`
   - `vDst = atomic_rmw.<w> <rmw_op> <ord> [vPtr], vVal`
   - `vVal, vOk = atomic_cas.<w> <strength> <succ_ord> <fail_ord> [vPtr], vExpected, vDesired` (where `<strength>` is `strong` or `weak`, and `<w>` is `b8`, `b16`, `b32`, or `b64`)
   - `atomic_fence <ord>` / `compiler_fence <ord>`
   - `atomic_pause`

**AXS-ATM-042** (x86-64 Total Store Order (TSO) hardware memory model properties; `T407`, `0092 §15–17`, `0162 §30`, `tasks/0328 §7`, `tasks/0515 §12`).
On x86-64 under standard write-back (`WB`) cacheable memory (Total Store Order, TSO):
1. **Naturally aligned 1-, 2-, 4-, and 8-byte loads and stores are hardware-atomic**: Because `AXS-ATM-011` guarantees natural alignment (`align_of::<Atomic<T>>() == size_of::<T>()`), no naturally aligned `Atomic<T>` operation ever crosses a 64-byte cache-line boundary (`0092 §15`).
2. **TSO hardware ordering guarantees**:
   - Reads are never reordered with other reads ($\text{Load} \to \text{Load}$ preserved in hardware).
   - Writes are never reordered with other writes ($\text{Store} \to \text{Store}$ preserved in hardware).
   - Writes are never reordered with earlier reads ($\text{Load} \to \text{Store}$ preserved in hardware).
   - Consequently, `Acquire` loads and `Release` stores are satisfied in x86-64 hardware by ordinary `MOV` instructions **combined with a compiler scheduling barrier** that forbids the compiler from reordering operations across the instruction.
3. **TSO store-buffer forwarding ($\text{Store} \to \text{Load}$ reordering)**:
   - On x86-64, a processor's store buffer allows a subsequent load to a **different** address to execute before an earlier buffered store becomes globally visible to other cores.
   - To enforce the global total order $\prec_S$ of `Ordering.SeqCst` (`AXS-ATM-025`), either `SeqCst` stores must drain the store buffer (via `XCHG`, which carries an implicit hardware `LOCK` prefix) OR `SeqCst` loads must be preceded by `MFENCE`. Axiom adopts the canonical zero-fence-on-load convention: **`SeqCst` loads lower to `MOV` (with compiler barrier), and `SeqCst` stores lower to `XCHG [ptr], reg`** (`0092 §15`, `tasks/0328 §7`, `tasks/0515 §12`).
4. **Hardware `LOCK`-prefixed instructions are full TSO barriers**: Every x86-64 instruction with an explicit or implicit `LOCK` prefix (`XCHG`, `LOCK XADD`, `LOCK CMPXCHG`, `LOCK ADD/SUB/AND/OR/XOR`) drains the processor store buffer and provides full `SeqCst` memory ordering on x86-64 regardless of whether the source-level `Ordering` was `Relaxed`, `Acquire`, `Release`, `AcqRel`, or `SeqCst`.

**AXS-ATM-043** (Normative x86-64 instruction selection matrix for all atomic operations; `T407`, `REQ-CONC-075`, `REQ-CONC-134`, `REQ-CONC-135`, `REQ-CONC-179`).
`compiler/target/x64/` MUST lower LIR atomic instructions according to the following complete matrix across all supported bit widths (`8`, `16`, `32`, `64`):

| LIR Operation | `Ordering` | x86-64 Lowering (8 / 16 / 32 / 64-bit) | Hardware Barrier / Notes |
|---|---|---|---|
| `LIR_INST_ATOMIC_LOAD` | `Relaxed`, `Acquire`, `SeqCst` | `MOV reg, [ptr]` (`mov al/ax/eax/rax, [r_ptr]`) + compiler barrier (`Acquire`/`SeqCst`) | TSO preserves $\text{Load}\to\text{Load}$ and $\text{Load}\to\text{Store}$; `SeqCst` store uses `XCHG` so `SeqCst` load needs only `MOV` |
| `LIR_INST_ATOMIC_STORE` | `Relaxed`, `Release` | `MOV [ptr], reg` (`mov [r_ptr], al/ax/eax/rax`) + compiler barrier (`Release`) | TSO preserves $\text{Load}\to\text{Store}$ and $\text{Store}\to\text{Store}$ |
| `LIR_INST_ATOMIC_STORE` | `SeqCst` | `XCHG [ptr], reg` (`xchg [r_ptr], al/ax/eax/rax`) | `XCHG` with a memory operand asserts hardware `LOCK` implicitly, draining the store buffer (`Store->Load` barrier) |
| `LIR_INST_ATOMIC_RMW` (`Xchg` / `swap`) | Any (`Relaxed`..`SeqCst`) | `XCHG [ptr], reg` (`xchg [r_ptr], reg`); result in `reg` | Implicit hardware `LOCK` on memory operand; returns old value in `reg` |
| `LIR_INST_ATOMIC_RMW` (`Add` / `fetch_add`) | Any (`Relaxed`..`SeqCst`) | `LOCK XADD [ptr], reg`; result (old value) returned in `reg` | Explicit `F0` (`LOCK`) prefix; atomically computes `[ptr] = old + reg` and sets `reg = old` |
| `LIR_INST_ATOMIC_RMW` (`Sub` / `fetch_sub`) | Any (`Relaxed`..`SeqCst`) | `NEG reg` followed by `LOCK XADD [ptr], reg`; result (old value) in `reg` | Two's-complement negation of `val` followed by `LOCK XADD` returns the exact pre-subtraction value |
| `LIR_INST_ATOMIC_RMW` (`And`, `Or`, `Xor`) | Any (`Relaxed`..`SeqCst`) | `LOCK CMPXCHG [ptr], r_new` retry loop (or `LOCK AND/OR/XOR [ptr], reg` only when return value is provably unused in LIR) | x86-64 has no `XAND`/`XOR`/`XXOR` returning old value; see `AXS-ATM-044` |
| `LIR_INST_ATOMIC_CAS` (`strong` or `weak`) | Any valid `(succ, fail)` | `MOV rax/eax/ax/al, r_expected`; `LOCK CMPXCHG [ptr], r_desired`; `SETE r_ok`; `r_val = rax/eax/ax/al` | On x86-64, both `compare_exchange` and `compare_exchange_weak` lower to `LOCK CMPXCHG` (`AXS-ATM-045`) |
| `LIR_INST_FENCE` (`is_compiler_only = false`) | `Acquire`, `Release`, `AcqRel` | Compiler scheduling barrier only (`0` machine bytes emitted) | TSO hardware already enforces `Acquire`, `Release`, and `AcqRel` ordering without `MFENCE` (`REQ-CONC-075`) |
| `LIR_INST_FENCE` (`is_compiler_only = false`) | `SeqCst` | `MFENCE` (`0F AE F0`) + compiler scheduling barrier | Full hardware store-load barrier (`REQ-CONC-075`, `0128 §26`) |
| `LIR_INST_FENCE` (`is_compiler_only = true`) | `Acquire`, `Release`, `AcqRel`, `SeqCst` | Compiler scheduling barrier only (`0` machine bytes emitted) | `compiler_fence` never emits CPU instructions (`REQ-ATM-031`) |
| `LIR_INST_PAUSE` | — | `PAUSE` (`F3 90`) | x86-64 spin-wait pipeline hint (`REQ-CONC-179`) |

**AXS-ATM-044** (x86-64 RMW lowering details for `fetch_add`, `fetch_sub`, `fetch_and`, `fetch_or`, `fetch_xor`; `T407`).
1. **`fetch_add` and `fetch_sub`**:
   - For `fetch_add(ptr, val)`: move `val` into scratch/output register `r_tmp`, emit `LOCK XADD [r_ptr], r_tmp`, and read the old value from `r_tmp`.
   - For `fetch_sub(ptr, val)`: move `val` into `r_tmp`, emit two's-complement `NEG r_tmp` (wrapping modular negation), emit `LOCK XADD [r_ptr], r_tmp`, and read the old value from `r_tmp`.
2. **`fetch_and`, `fetch_or`, `fetch_xor` (`LOCK CMPXCHG` loop)**:
   - Because x86-64 `LOCK AND/OR/XOR [ptr], reg` overwrites `[ptr]` without returning the old value, `LIR_INST_ATOMIC_RMW` for `And`, `Or`, and `Xor` lowers to a local machine-level retry loop:
     ```text
         mov     rax, [r_ptr]          ; initial load of current value (sized: al/ax/eax/rax)
     .L_rmw_retry:
         mov     r_Scratch, rax        ; copy current expected value
         and|or|xor r_Scratch, r_Val   ; compute desired = current OP val
         lock cmpxchg [r_ptr], r_Scratch ; if [r_ptr] == rax, set [r_ptr] = r_Scratch & ZF=1; else rax = [r_ptr] & ZF=0
         jne     .L_rmw_retry          ; retry on contention using updated rax
         mov     r_Dst, rax            ; old value observed by the winning CMPXCHG
     ```
   - Notice that on `CMPXCHG` failure, hardware automatically updates `al/ax/eax/rax` with the latest value from `[r_ptr]`, so `.L_rmw_retry` branches directly to `mov r_Scratch, rax` without a redundant memory load.

**AXS-ATM-045** (x86-64 `compare_exchange` and `compare_exchange_weak` lowering; `T407`, `REQ-CONC-056`, `REQ-ATM-017`).
1. `LOCK CMPXCHG [r_ptr], r_desired` implicitly compares the accumulator (`AL` for 8-bit, `AX` for 16-bit, `EAX` for 32-bit, `RAX` for 64-bit) with `[r_ptr]`:
   - If equal: `ZF = 1`, and `r_desired` is written to `[r_ptr]`; accumulator retains `expected`.
   - If not equal: `ZF = 0`, and `[r_ptr]` is loaded into the accumulator (`AL`/`AX`/`EAX`/`RAX`).
2. After `LOCK CMPXCHG [r_ptr], r_desired`:
   - `SETE r_ok` captures `ZF` (`1u8` on success, `0u8` on failure) for `CasResult.ok`.
   - The accumulator (`AL`/`AX`/`EAX`/`RAX`) holds `CasResult.val` (which equals `expected` when `ZF == 1` and equals the actual observed value at `[r_ptr]` when `ZF == 0`).
3. Because x86-64 provides direct cache-coherent `LOCK CMPXCHG` rather than LL/SC (`LDXR`/`STXR`), `compare_exchange_weak` lowers to the exact same `LOCK CMPXCHG` sequence on x86-64 (never failing spuriously on native x86-64 hardware, while the MIR oracle tests spurious failure per `AXS-ATM-054`).

**AXS-ATM-046** (x86-64 fence and spin-loop hint lowering; `T407`, `REQ-CONC-075`, `REQ-CONC-178`, `REQ-CONC-179`, `REQ-ATM-031`).
1. `fence(Ordering.SeqCst)` emits the 3-byte instruction `MFENCE` (`0F AE F0`) and acts as a two-way LIR scheduling barrier (`REQ-CONC-075`).
2. `fence(Ordering.Acquire)`, `fence(Ordering.Release)`, and `fence(Ordering.AcqRel)` emit `0` machine bytes on x86-64 (TSO already orders $\text{Load}\to\text{Load}$, $\text{Load}\to\text{Store}$, and $\text{Store}\to\text{Store}$) while acting as a hard LIR instruction-scheduling barrier.
3. `compiler_fence(ord)` (`Acquire`, `Release`, `AcqRel`, `SeqCst`) emits `0` machine bytes on all targets and acts strictly as a compiler optimization and LIR scheduling barrier (`REQ-CONC-178`, `REQ-ATM-031`).
4. `spin_loop_hint()` emits the 2-byte instruction `PAUSE` (`F3 90`) on x86-64 (`REQ-CONC-179`).

**AXS-ATM-047** (Byte-exact x86-64 machine encoding specification for atomic instructions; `T407`, `tests/encode/atomics`).
`compiler/target/x64/encode.ax` MUST encode atomic instructions with the exact prefixes and opcodes below (where `REX` is emitted as needed for 64-bit operand size `REX.W = 0x48`, extended registers `R8`–`R15` via `REX.R`/`REX.B`, or uniform byte registers `SPL`/`BPL`/`SIL`/`DIL`):
1. **Prefix ordering rule**: For 16-bit locked instructions, both `0xF0` (`LOCK`) and `0x66` (operand-size override) are legacy prefixes; `compiler/target/x64/encode.ax` emits `F0` first (`F0 66 ...`) for canonical determinism. For 64-bit locked instructions, `0xF0` precedes the `REX` byte (`F0 48 ...`), matching the Intel SDM requirement that `REX` immediately precede the opcode/escape byte.
2. **Exact opcode table**:

| Instruction | Width | Prefix(es) | Opcode Bytes | ModR/M & Operands |
|---|---|---|---|---|
| `XCHG [r_ptr], reg` | 8-bit | *(REX if needed)* | `86` | `ModR/M(mod, reg=r_val, rm=r_ptr)` (implicit hardware `LOCK`) |
| `XCHG [r_ptr], reg` | 16-bit | `66` *(+ REX if ext reg)* | `87` | `ModR/M(mod, reg=r_val, rm=r_ptr)` |
| `XCHG [r_ptr], reg` | 32-bit | *(REX if ext reg)* | `87` | `ModR/M(mod, reg=r_val, rm=r_ptr)` |
| `XCHG [r_ptr], reg` | 64-bit | `REX.W` (`48`..`4F`) | `87` | `ModR/M(mod, reg=r_val, rm=r_ptr)` |
| `LOCK XADD [r_ptr], reg` | 8-bit | `F0` *(+ REX if needed)* | `0F C0` | `ModR/M(mod, reg=r_val, rm=r_ptr)` |
| `LOCK XADD [r_ptr], reg` | 16-bit | `F0 66` *(+ REX if ext)* | `0F C1` | `ModR/M(mod, reg=r_val, rm=r_ptr)` |
| `LOCK XADD [r_ptr], reg` | 32-bit | `F0` *(+ REX if ext)* | `0F C1` | `ModR/M(mod, reg=r_val, rm=r_ptr)` |
| `LOCK XADD [r_ptr], reg` | 64-bit | `F0 REX.W` (`F0 48`..`4F`) | `0F C1` | `ModR/M(mod, reg=r_val, rm=r_ptr)` |
| `LOCK CMPXCHG [r_ptr], reg` | 8-bit | `F0` *(+ REX if needed)* | `0F B0` | `ModR/M(mod, reg=r_desired, rm=r_ptr)` (compares with `AL`) |
| `LOCK CMPXCHG [r_ptr], reg` | 16-bit | `F0 66` *(+ REX if ext)* | `0F B1` | `ModR/M(mod, reg=r_desired, rm=r_ptr)` (compares with `AX`) |
| `LOCK CMPXCHG [r_ptr], reg` | 32-bit | `F0` *(+ REX if ext)* | `0F B1` | `ModR/M(mod, reg=r_desired, rm=r_ptr)` (compares with `EAX`) |
| `LOCK CMPXCHG [r_ptr], reg` | 64-bit | `F0 REX.W` (`F0 48`..`4F`) | `0F B1` | `ModR/M(mod, reg=r_desired, rm=r_ptr)` (compares with `RAX`) |
| `MFENCE` | — | — | `0F AE F0` | Fixed 3-byte encoding |
| `PAUSE` | — | `F3` | `90` | Fixed 2-byte encoding (`F3 90`) |

---

## 6. MIR Interpreter Oracle Memory Model & Deterministic Schedule Explorer

**AXS-ATM-050** (Oracle atomic location state and modification-order store buffer; `T408`, `REQ-ATM-012`, `REQ-ATM-013`, `REQ-ATM-021`, `REQ-CONC-062`).
The MIR interpreter (`compiler/interp/`) serves as the executable semantic oracle (`INV-ORACLE-001`, `INV-ORACLE-002`). For every memory allocation or place containing an `Atomic<T>`:
1. **Atomic tag & width**: The interpreter marks the byte range $[addr, addr + \text{size})$ as an **atomic location** of bit width $w \in \{8, 16, 32, 64\}$ (`AXS-ATM-010`).
2. **Modification-order log ($\prec_{\text{mo}}^X$, `REQ-ATM-012`, `REQ-ATM-013`)**: Each atomic location $X$ maintains an ordered modification history $H(X) = [W_0, W_1, \dots, W_k]$, where $W_0$ is the initializing write (`Atomic.new(v)` or `static` initializer) and each entry $W_i$ records:
   - `val: u64`: the bit-pattern written to $X$,
   - `writer_tid: u32`: the logical thread/task ID that performed the write,
   - `order: Ordering`: the memory ordering of the write,
   - `rel_clock: VectorClock`: the release vector clock attached to $W_i$ (integrating release sequences per `AXS-ATM-024`),
   - `seq_cst_index: u64`: the position of $W_i$ in the global `SeqCst` total order $\prec_S$ (`0` if non-`SeqCst`),
   - `is_rmw: bool`: whether $W_i$ was produced by an RMW (`swap`, `fetch_*`, or successful CAS) reading $W_{i-1}$.
3. **Indivisibility and RMW atomicity (`REQ-ATM-021`)**: Every atomic RMW (`swap`, `fetch_*`, or successful `compare_exchange[_weak]`) in the oracle reads the latest entry $W_k$ at the tail of $H(X)$ and appends $W_{k+1}$ as its immediate successor in $\prec_{\text{mo}}^X$. Two concurrent RMWs can never read the same $W_k$.

**AXS-ATM-051** (Vector-clock happens-before and release-sequence tracking in the oracle; `T408`, `REQ-CONC-054`, `REQ-ATM-006`, `REQ-ATM-007`, `REQ-ATM-008`, `REQ-ATM-010`, `REQ-ATM-026`, `REQ-ATM-032`).
The oracle tracks happens-before ($\prec_{\text{hb}}$) across logical threads $t \in \{0, \dots, N-1\}$ using vector clocks $C: \text{ThreadId} \to \text{Epoch}$ (`u64`):
1. **Per-thread clocks**: Each logical thread $t$ maintains:
   - `clock[t]`: current thread vector clock (with `clock[t][t]` incremented on every step/synchronization action),
   - `acq_fence_clock[t]`: vector clock accumulated by atomic reads on thread $t$ since its last `Acquire` fence (for Atomic-to-Fence synchronization `AXS-ATM-027(2)`),
   - `rel_fence_clock[t]`: snapshot of `clock[t]` at the most recent `fence(Release | AcqRel | SeqCst)` on thread $t$ (for Fence-to-Atomic synchronization `AXS-ATM-027(1)`).
   - A global `seq_cst_fence_clock: VectorClock` and monotonic counter `seq_cst_tick: u64` track the total order $\prec_S$ (`AXS-ATM-025`).
2. **Store update rules (`REQ-ATM-006`, `REQ-ATM-007`, `REQ-ATM-008`)**:
   - On `store(val, ord)` to $X$ by thread $t$:
     - If `ord` has release semantics (`Release`, `AcqRel`, `SeqCst`), `W.rel_clock = clock[t]`.
     - If `ord == Relaxed`, `W.rel_clock = rel_fence_clock[t]` (so a preceding `fence(Release)` still propagates via a `Relaxed` store per `AXS-ATM-027(1)`, while a pure `Relaxed` store without a fence carries no new happens-before clock, satisfying `REQ-ATM-008`).
     - If `ord == SeqCst`, increment `seq_cst_tick` and record `W.seq_cst_index = seq_cst_tick`.
3. **RMW release-sequence propagation (`REQ-ATM-032`, `AXS-ATM-024`)**:
   - On an RMW write $W_{k+1}$ reading $W_k$ on $X$ by thread $t$:
     - Base clock: start from $W_k.\text{rel\_clock}$ (preserving the release sequence headed by any earlier `Release` store in $H(X)$ even when $W_{k+1}$ is `Relaxed`, `REQ-ATM-032`).
     - If the RMW itself has release semantics (`Release`, `AcqRel`, `SeqCst`), join (`max` element-wise) with `clock[t]`; otherwise join with `rel_fence_clock[t]`.
4. **Load observation & Acquire join rules (`REQ-CONC-054`, `REQ-ATM-007`, `REQ-ATM-010`, `REQ-ATM-026`)**:
   - A load $R$ on $X$ by thread $t$ is coherent (`REQ-ATM-026`) with any write $W_i \in H(X)$ such that no later write $W_j$ ($j > i$) is already visible to thread $t$ ($W_j\text{.epoch} \le \text{clock}[t][W_j\text{.writer\_tid}]$) and, if $R$ is `SeqCst`, $W_i$ does not precede the latest `SeqCst` write to $X$ in $\prec_S$ (`AXS-ATM-025`). Under the default latest-value schedule (or after reading $W_i$ selected by the deterministic schedule explorer `AXS-ATM-053`):
     - Always join $W_i.\text{rel\_clock}$ into `acq_fence_clock[t]` (so a subsequent `fence(Acquire)` on thread $t$ will synchronize with $W_i$ per `AXS-ATM-027(2)`).
     - If $R$ has acquire semantics (`Acquire`, `AcqRel`, `SeqCst`), join $W_i.\text{rel\_clock}$ directly into `clock[t]` (`clock[t] = clock[t] \sqcup W_i.\text{rel\_clock}`), making all writes that happened-before $W_i$ visible to thread $t$ (`REQ-CONC-054`, `REQ-ATM-007`, `REQ-ATM-010`).
5. **Fence update rules (`AXS-ATM-027`)**:
   - On `fence(Release | AcqRel | SeqCst)` on thread $t$: set `rel_fence_clock[t] = clock[t]`.
   - On `fence(Acquire | AcqRel | SeqCst)` on thread $t$: set `clock[t] = clock[t] \sqcup acq_fence_clock[t]`.
   - On `fence(SeqCst)` on thread $t$: additionally join `seq_cst_fence_clock` into `clock[t]` and update `seq_cst_fence_clock = seq_cst_fence_clock \sqcup clock[t]`.

**AXS-ATM-052** (Oracle detection of ordinary data races and mixed atomic/ordinary races; `T408`, `REQ-CONC-062`, `AXS-ATM-004`).
For every byte of ordinary memory, the oracle records the last writer `(write_tid, write_epoch)` and per-thread last reader epochs `read_epoch[tid]`:
1. **Ordinary data-race check**: On an ordinary write by thread $t$, if an earlier write `(w_tid, w_epoch)` has `w_epoch > clock[t][w_tid]`, or any reader `r_tid != t` has `read_epoch[r_tid] > clock[t][r_tid]`, the oracle immediately halts execution and emits `AX_UNSAFE_INTERP_UB` (exit code `125`) identifying the unsynchronized conflicting access. Similarly, on an ordinary read by thread $t$, if `write_epoch > clock[t][write_tid]`, the oracle emits `AX_UNSAFE_INTERP_UB` (exit code `125`).
2. **Mixed atomic/ordinary check (`REQ-CONC-062`)**: If an ordinary read or write targets a byte range marked as an active `Atomic<T>` location (e.g. via raw-pointer cast inside `unsafe`) concurrently with an unsynchronized atomic access (`atomic_epoch > clock[t][atomic_tid]`), or an atomic operation targets an unaligned/partially overlapping address, the oracle immediately halts with `AX_UNSAFE_INTERP_UB` (exit code `125`).

**AXS-ATM-053** (Deterministic multi-threaded schedule exploration in the oracle; `T408`, `REQ-ASY-061`, `INV-DET-003`).
Because the self-hosted MIR interpreter executes deterministically on a single host thread (`INV-DET-003`):
1. Concurrent tasks spawned in the interpreter (`std.thread.spawn`, `std.thread.scope`, or oracle litmus harness threads) are executed by a cooperative user-space scheduler inside `compiler/interp/`.
2. Every `MIR_STMT_ATOMIC` operation (`load`, `store`, `swap`, `fetch_*`, `compare_exchange`, `compare_exchange_weak`, `fence`, `spin_loop_hint`) acts as an explicit scheduler yield/interleaving point (`AXS-ATM-034`, `REQ-ASY-061`).
3. Given a deterministic schedule seed $S \in \mathbb{N}$ (default `0`, or stepped over a bounded schedule range $S \in [0, K)$ in litmus tests), the oracle selects the next runnable logical thread and—for `Relaxed`/`Acquire` loads in weak-memory litmus tests—selects among the coherence-valid writes $W_i \in H(X)$ (`AXS-ATM-051(4)`) using a pure deterministic PRNG (`SplitMix64` / `xorshift64*` seeded solely by $S$). Identical source code and seed $S$ produce byte-identical execution traces, diagnostics, and exit codes across all machines (`INV-DET-001`..`003`).

**AXS-ATM-054** (Deterministic spurious failure simulation for `compare_exchange_weak`; `T408`, `REQ-ATM-018`, `REQ-ATM-019`).
To verify that callers of `compare_exchange_weak` place it inside a retry loop and properly handle spurious failures (`REQ-ATM-017`..`019`):
1. When the oracle executes `MIR_ATOMIC_CMPXCHG_WEAK` on location $X$ and the current value at $X$ equals `expected`:
   - In deterministic weak-CAS test mode (or on every odd/seeded weak-CAS attempt per `(location, thread)` counter before succeeding on retry), the oracle may deterministically take the **spurious failure path**: it leaves $H(X)$ unmodified, applies the `failure` memory ordering (`AXS-ATM-026`), and returns `CasResult { ok: false, val: expected }`.
   - To guarantee forward progress (`liveness`), after at most 1 deterministic spurious failure at a given modification index $k = |H(X)|$ for thread $t$, the next `compare_exchange_weak` by thread $t$ seeing the same modification index $k$ and matching `expected` succeeds normally.
2. When the oracle executes `MIR_ATOMIC_CMPXCHG` (strong `compare_exchange`), it **never** fails spuriously (`REQ-ATM-018`): if the value at $X$ equals `expected`, the CAS always succeeds and returns `CasResult { ok: true, val: expected }`.

---

## 7. Atomic Diagnostic Taxonomy, Litmus Test Specifications & Conformance Examples

### 7.1 Atomic Diagnostic Codes (`CONC` Area)

**AXS-ATM-060** (Atomic diagnostic code table; `T406`, `T408`, `spec/diagnostics.md §11`, `0128 §58`, `0208 §39`).
Self-hosted `axiomc` (`compiler/diag/code.ax`) and `spec/diagnostics.md §11` define the following diagnostic codes for `E11.2`:

| Code | Area | Sev | Emitted By | Trigger Condition & Structured `data` Keys |
|---|---|---|---|---|
| `AX_CONC_INVALID_ATOMIC_TYPE` | `CONC` | E | `types/typeck.ax`, `verify/verifier.ax` (`T406`) | `Atomic<T>` instantiated with a type `T` outside the allowed 1-, 2-, 4-, or 8-byte integer, `bool`, or raw-pointer set (`AXS-ATM-010`, `REQ-CONC-051`, `REQ-ATM-004`). `data.type` = found type name |
| `AX_CONC_INVALID_ATOMIC_ORDERING` | `CONC` | E | `types/typeck.ax`, `verify/verifier.ax` (`T406`) | Disallowed `Ordering` for an atomic operation or fence (`load` with `Release`/`AcqRel`, `store` with `Acquire`/`AcqRel`, `fence`/`compiler_fence` with `Relaxed`, CAS `failure` with `Release`/`AcqRel`, or CAS `failure` stronger than `success`; `AXS-ATM-026`, `REQ-CONC-058`, `REQ-ATM-020`, `REQ-ATM-023`). `data.op`, `data.ordering`, `data.fail_ordering` |
| `AX_CONC_INVALID_ATOMIC_ALIGNMENT` | `CONC` | E | `types/typeck.ax`, `verify/verifier.ax` (`T406`) | `Atomic<T>` placed inside a `@packed` struct, given a sub-natural `@align(N)` where `N < size_of::<T>()`, or accessed at a statically underaligned offset (`AXS-ATM-011`, `REQ-CONC-052`, `REQ-ATM-005`). `data.required_align`, `data.actual_align` |
| `AX_CONC_ATOMIC_MUT_VIEW` | `CONC` | E | `sema/`, `types/typeck.ax`, `verify/verifier.ax` (`T402`/`T406`) | Attempt to form a `mut_view<T>` into the underlying value of `Atomic<T>` or mix non-atomic `mut_view` access with concurrent `Atomic<T>` access (`AXS-ATM-005`, `SPEC-30 AXS-CONC-036`, `REQ-CONC-063`) |
| `AX_UNSAFE_INTERP_UB` | `UNSAFE` | E (exit 125) | `interp/` (`T061a`/`T408`) | Runtime oracle detection of an unsynchronized data race on ordinary memory, a mixed atomic/ordinary access race, or an unaligned raw-pointer atomic access (`AXS-ATM-052`, `REQ-CONC-062`) |

### 7.2 Normative Conformance Litmus Test Specifications (`T409`)

The conformance suite in `tests/conformance/p11/e11_2_atomics/` (`T409`) MUST implement and pass the following six normative litmus families in both `--interp` (oracle across deterministic schedules) and native x86-64 execution (`INV-ORACLE-002`):

**AXS-ATM-061** (`LITMUS-MP`: Message Passing with `Release` / `Acquire`; `REQ-CONC-054`, `REQ-CONC-077`, `REQ-ATM-010`, `REQ-ATM-028`, `0092 §25`, `0128 §59`, `tasks/0515 §6`).
- **Initial state**: Ordinary shared payload `data: i64 = 0` (protected by synchronization) and `ready = Atomic.new(false)`.
- **Thread 1 (Producer)**:
  1. Writes `data = 42` (ordinary memory write).
  2. Executes `ready.store(true, Ordering.Release)`.
- **Thread 2 (Consumer)**:
  1. Executes `if ready.load(Ordering.Acquire) { r = data }`.
- **Required Postcondition**: Whenever Thread 2 observes `ready.load(Ordering.Acquire) == true`, the happens-before chain $\text{write}(data = 42) \prec_{\text{sb}} \text{store}_{\text{Rel}}(ready, \text{true}) \prec_{\text{sw}} \text{load}_{\text{Acq}}(ready) \prec_{\text{sb}} \text{read}(data)$ guarantees `r == 42` (`r == 0` is **forbidden**), and the oracle reports **zero** data races on `data`.
- **Negative / Contrast Case (`MP-Relaxed` in oracle)**: If Thread 1 uses `Ordering.Relaxed` or Thread 2 uses `Ordering.Relaxed` without fences, no $\prec_{\text{sw}}$ edge is formed (`AXS-ATM-021`); in `unsafe` raw-pointer mode, the oracle's race detector (`AXS-ATM-052`) flags the unsynchronized read of `data` with `AX_UNSAFE_INTERP_UB`.

**AXS-ATM-062** (`LITMUS-MP-FENCE`: Message Passing with `Relaxed` Atomics and Explicit `fence`; `REQ-CONC-075`, `REQ-ATM-023`, `REQ-ATM-024`, `AXS-ATM-027`).
- **Initial state**: `data: i64 = 0`, `ready = Atomic.new(0i32)`.
- **Thread 1 (Producer)**:
  1. Writes `data = 99`.
  2. Executes `fence(Ordering.Release)`.
  3. Executes `ready.store(1, Ordering.Relaxed)`.
- **Thread 2 (Consumer)**:
  1. Executes `r_flag = ready.load(Ordering.Relaxed)`.
  2. If `r_flag == 1`, executes `fence(Ordering.Acquire)` followed by `r_data = data`.
- **Required Postcondition**: By `AXS-ATM-027(3)` (Fence-to-Fence synchronization), $F_{\text{rel}} \prec_{\text{sw}} F_{\text{acq}}$ whenever `r_flag == 1`, so `r_data == 99` is guaranteed and no data race occurs on `data`.

**AXS-ATM-063** (`LITMUS-SB`: Store Buffering under `SeqCst` vs `Relaxed`; `REQ-CONC-076`, `REQ-ATM-009`, `REQ-ATM-011`, `REQ-ATM-028`, `0092 §25`, `tasks/0515 §12`).
- **Initial state**: `x = Atomic.new(0i32)`, `y = Atomic.new(0i32)`.
- **Thread 1**: `x.store(1, ord); r0 = y.load(ord)`
- **Thread 2**: `y.store(1, ord); r1 = x.load(ord)`
- **Required Postconditions**:
  1. **When `ord == Ordering.SeqCst`**: The total order $\prec_S$ (`AXS-ATM-025`) and x86-64 `XCHG` store-buffer drain (`AXS-ATM-042`) **forbid** the outcome `(r0 == 0 && r1 == 0)`. Across all oracle schedules and native runs, at least one of `r0 == 1` or `r1 == 1` MUST hold (`r0 + r1 >= 1`).
  2. **When `ord == Ordering.Relaxed` (or `Release`/`Acquire`)**: The outcome `(r0 == 0 && r1 == 0)` is **permitted** by the Axiom memory model (`AXS-ATM-021`) because neither store synchronizes with the other thread's load, and the oracle's weak-memory coherence explorer (`AXS-ATM-051(4)`, `AXS-ATM-053`) can deterministically witness `(r0 == 0 && r1 == 0)` without UB.

**AXS-ATM-064** (`LITMUS-LB`: Load Buffering and Coherence (`CoRR`, `CoWR`, `CoWW`, `CoRW`); `REQ-ATM-012`, `REQ-ATM-013`, `REQ-ATM-026`, `REQ-ATM-028`).
- **Coherence invariant (`CoRR`)**: On a single atomic variable `x = Atomic.new(0i32)` with Thread 1 executing `x.store(1, Ordering.Relaxed)` and `x.store(2, Ordering.Relaxed)`, if Thread 2 executes `r1 = x.load(Ordering.Relaxed); r2 = x.load(Ordering.Relaxed)` and observes `r1 == 2`, then `r2 == 1` is **forbidden** (`r2` MUST be `2` because $1 \prec_{\text{mo}}^x 2$, `REQ-ATM-013`, `REQ-ATM-026`).
- **Load Buffering (`LB` under `Acquire`/`Release`)**: With `x = Atomic.new(0i32), y = Atomic.new(0i32)`, Thread 1 executing `r0 = x.load(Ordering.Acquire); y.store(r0, Ordering.Release)`, and Thread 2 executing `r1 = y.load(Ordering.Acquire); x.store(r1, Ordering.Release)`, the out-of-thin-air outcome `(r0 == 1 && r1 == 1)` (or any value not written by the program) is **strictly forbidden** under all orderings (`r0 == 0 && r1 == 0`).

**AXS-ATM-065** (`LITMUS-RMW`: Concurrent `fetch_add` Counter & Ticket/Spinlock Exclusion; `REQ-CONC-078`, `REQ-ATM-021`, `REQ-ATM-029`, `REQ-ATM-032`).
- **Part A (Lossless concurrent `fetch_add`)**: $N$ threads each execute $M$ iterations of `counter.fetch_add(1, Ordering.Relaxed)`.
  - Every `fetch_add` on `counter` returns a distinct old value in $[0, N \times M - 1]$ (`REQ-ATM-021`).
  - After all threads join, `counter.load(Ordering.Relaxed) == N * M` with zero lost updates (`REQ-CONC-078`, `REQ-ATM-029`).
- **Part B (Release sequence over RMW chain & Spinlock mutual exclusion; `REQ-ATM-032`)**:
  - A spinlock implemented with `locked = Atomic.new(false)`, acquiring via `while !locked.compare_exchange_weak(false, true, Ordering.Acquire, Ordering.Relaxed).ok { spin_loop_hint() }` and releasing via `locked.store(false, Ordering.Release)`, protects an ordinary shared counter `shared_non_atomic: i64`.
  - Across all $N$ threads and $M$ critical-section increments, `shared_non_atomic == N * M` and the oracle's race detector (`AXS-ATM-052`) reports **zero** data races because every `Release` unlock synchronizes-with the next thread's `Acquire` CAS (`AXS-ATM-024`, `REQ-ATM-032`).

**AXS-ATM-066** (`LITMUS-CAS-ABA`: `compare_exchange` vs `compare_exchange_weak` Retry Loop & Tagged-State ABA Prevention; `REQ-CONC-079`, `REQ-ATM-017`, `REQ-ATM-018`, `REQ-ATM-019`, `REQ-ATM-030`, `tasks/0515 §11`).
- **Part A (`compare_exchange_weak` retry loop under spurious failure)**:
  - A CAS loop increments an atomic state `state: Atomic<u64>` by multiplying by 2 and adding 1 using `compare_exchange_weak(cur, next, Ordering.AcqRel, Ordering.Acquire)`:
    - Even when the oracle injects deterministic spurious failures (`AXS-ATM-054`, `REQ-ATM-018`), the retry loop updates `cur = res.val` and converges to the exact mathematically expected state (`REQ-ATM-017`, `REQ-ATM-019`).
  - Conversely, `compare_exchange` (strong) on an uncontended `Atomic<u64>` with matching `expected` succeeds on the very first attempt (`attempts == 1`, `REQ-ATM-018`).
- **Part B (ABA prevention via packed `(tag: u32, index: u32)` in `Atomic<u64>`, `REQ-CONC-079`, `REQ-ATM-030`, `tasks/0515 §11`)**:
  - Lock-free Treiber stack / free-list heads that reuse node indices or pointers are vulnerable to the classic ABA problem ($A \to B \to A$) if CAS only compares the raw index/pointer.
  - The conformance test packs a 32-bit monotonic generation tag `(tag + 1) << 32 | head_idx` into `Atomic<u64>`. When an intervening thread pops $A$, pops $B$, and pushes $A$ back, the generation tag increments from `tag` to `tag + 2`, causing the first thread's `compare_exchange` expecting `(tag << 32) | A` to detect the ABA modification (`res.ok == false`) and reload the updated head safely without corrupting the free-list (`REQ-CONC-079`, `REQ-ATM-030`).

### 7.3 Canonical Source Examples (Positive & Negative)

#### Positive Example: Message Passing & Lock-Free CAS Loop (Canonical Axiom Syntax)
```axiom
module examples.atomics_ok

use std.sync.atomic.Atomic
use std.sync.atomic.Ordering
use std.sync.atomic.fence
use std.sync.atomic.spin_loop_hint

pub fn atomic_cas_accumulate(slot: view<Atomic<i64>>, delta: i64) -> i64 {
    let mut cur = slot.load(Ordering.Relaxed)
    loop {
        let next = cur + delta
        let res = slot.compare_exchange_weak(
            cur,
            next,
            Ordering.AcqRel,
            Ordering.Acquire
        )
        if res.ok {
            return res.val
        }
        cur = res.val
        spin_loop_hint()
    }
}

pub fn fence_publish(flag: view<Atomic<u32>>, v: u32) -> u32 {
    fence(Ordering.Release)
    flag.store(v, Ordering.Relaxed)
    let observed = flag.load(Ordering.Relaxed)
    fence(Ordering.Acquire)
    return observed
}
```

#### Negative Examples: Compile-Time Rejections (`tests/ui/concurrency/atomics/`)
```axiom
module examples.atomics_err

use std.sync.atomic.Atomic
use std.sync.atomic.Ordering
use std.sync.atomic.fence

struct Pair {
    a: i64,
    b: i64,
}

// 1. Invalid atomic element type (16 bytes, not a 1/2/4/8-byte scalar)
pub fn bad_atomic_type() {
    let _bad = Atomic.new(Pair { a: 1, b: 2 }) // ERROR: AX_CONC_INVALID_ATOMIC_TYPE
}

// 2. Invalid memory ordering for load / store / fence / CAS
pub fn bad_atomic_orderings(x: view<Atomic<i32>>) {
    let _v1 = x.load(Ordering.Release) // ERROR: AX_CONC_INVALID_ATOMIC_ORDERING
    let _v2 = x.load(Ordering.AcqRel)  // ERROR: AX_CONC_INVALID_ATOMIC_ORDERING
    x.store(1, Ordering.Acquire)       // ERROR: AX_CONC_INVALID_ATOMIC_ORDERING
    x.store(1, Ordering.AcqRel)        // ERROR: AX_CONC_INVALID_ATOMIC_ORDERING
    fence(Ordering.Relaxed)            // ERROR: AX_CONC_INVALID_ATOMIC_ORDERING

    // CAS failure ordering cannot be Release/AcqRel
    let _r1 = x.compare_exchange(0, 1, Ordering.SeqCst, Ordering.Release) // ERROR: AX_CONC_INVALID_ATOMIC_ORDERING
    // CAS failure ordering cannot be stronger than success ordering
    let _r2 = x.compare_exchange(0, 1, Ordering.Relaxed, Ordering.Acquire) // ERROR: AX_CONC_INVALID_ATOMIC_ORDERING
    let _r3 = x.compare_exchange(0, 1, Ordering.Release, Ordering.Acquire) // ERROR: AX_CONC_INVALID_ATOMIC_ORDERING
}

// 3. Invalid atomic alignment inside a @packed struct
@packed
struct MisalignedAtomic {
    pad: u8,
    counter: Atomic<u64>, // ERROR: AX_CONC_INVALID_ATOMIC_ALIGNMENT
}
```

---

## 8. Requirement & Conformance Traceability Matrix

### 8.1 Primary `T405` `covers:` Requirements (13 Requirements)

| Requirement ID | Summary | Canonical Rule(s) in `SPEC-31` |
|---|---|---|
| `REQ-ATM-001` | Separation between ordinary memory (capability-checked, race-free) and atomic synchronization memory (`Atomic<T>`, `Ordering`) | `AXS-ATM-001`, `AXS-ATM-002`, `AXS-ATM-004` |
| `REQ-CONC-013` | Explicit memory ordering (`Relaxed`, `Acquire`, `Release`, `AcqRel`, `SeqCst`) required on every atomic operation | `AXS-ATM-014`, `AXS-ATM-020` |
| `REQ-CONC-059` | Explicit `Ordering` enum with `Relaxed`, `Acquire`, `Release`, `AcqRel`, and `SeqCst` | `AXS-ATM-020` |
| `REQ-CONC-060` | Normative semantics for `Relaxed`, `Acquire`, `Release`, `AcqRel`, and `SeqCst` | `AXS-ATM-021`..`AXS-ATM-025` |
| `REQ-CONC-097` | Every atomic operation explicitly specifies its `Ordering` at the call site; no implicit default ordering | `AXS-ATM-014`, `AXS-ATM-020` |
| `REQ-ATM-002` | `Atomic<T>` provides explicit `load`, `store`, `swap`, `compare_exchange`, `compare_exchange_weak`, and arithmetic/bitwise `fetch_*` operations | `AXS-ATM-014`..`AXS-ATM-016` |
| `REQ-ATM-014` | All atomic operations take explicit `Ordering` parameters (`compare_exchange` / `compare_exchange_weak` take `success` and `failure` orderings) | `AXS-ATM-014`, `AXS-ATM-015`, `AXS-ATM-020` |
| `REQ-ATM-015` | No implicit default memory ordering on any `Atomic<T>` method or fence | `AXS-ATM-014`, `AXS-ATM-020` |
| `REQ-ATM-031` | `compiler_fence(order)` restricts compiler instruction reordering without emitting CPU barrier instructions | `AXS-ATM-007`, `AXS-ATM-018`, `AXS-ATM-046` |
| `REQ-MIR-144` | MIR represents atomic operations and orderings explicitly (`MIR_STMT_ATOMIC`) so optimizer passes never treat them as ordinary `Assign` reads/writes | `AXS-ATM-030`..`AXS-ATM-033` |
| `REQ-CONC-172` | `Atomic<T>` is the canonical shared synchronization primitive operable via shared `view<Atomic<T>>` (`Atomic<T>: Send + Share`) | `AXS-ATM-001`, `AXS-ATM-005`, `AXS-ATM-012` |
| `REQ-CONC-174` | Standard library `std.sync.atomic` surface (`Atomic<T>`, `Ordering`, `CasResult<T>`, `fence`, `compiler_fence`, `spin_loop_hint`, type aliases) | `AXS-ATM-010`..`AXS-ATM-019` |
| `REQ-CONC-178` | Explicit `fence(ord)` and `compiler_fence(ord)` APIs and synchronization semantics | `AXS-ATM-007`, `AXS-ATM-018`, `AXS-ATM-027`, `AXS-ATM-046` |

### 8.2 Downstream `E11.2` Task Coverage Map (`T406`–`T409`)

| Downstream Task | Scope | Normative `SPEC-31` Rules | Covered `CATALOG.md` Requirements | Verification Suites |
|---|---|---|---|---|
| `T406` | `std/sync/atomic.ax` lang-item & API, `Ordering` legality matrix, `MIR_STMT_ATOMIC` lowering, MIR verifier & optimizer (`const_fold`, `dce`) preservation, diagnostics | `AXS-ATM-003`, `AXS-ATM-005`, `AXS-ATM-008`, `AXS-ATM-010`..`027`, `AXS-ATM-030`..`034`, `AXS-ATM-060` | `REQ-CONC-014, 051, 052, 053, 056, 057, 058, 061, 062, 063, 064, 069, 091, 092, 098, 108, 118, 121, 133, 142, 173, 175, 177, 201`, `REQ-ASY-061, 062, 166`, `REQ-ATM-003, 004, 005, 009, 011, 016, 017, 020, 022, 023, 024, 025, 027` | `tests/mir/atomics`, `tests/ui/concurrency/atomics` |
| `T407` | LIR atomic ops (`LIR_INST_ATOMIC_*`, `LIR_INST_FENCE`, `LIR_INST_PAUSE`), x86-64 TSO instruction selection & byte-exact encoding (`LOCK XADD`, `LOCK CMPXCHG`, `XCHG`, `MFENCE`, `PAUSE`) | `AXS-ATM-040`..`AXS-ATM-047` | `REQ-CONC-075, 134, 135, 179` | `tests/lir/atomics`, `tests/encode/atomics`, `tests/run/concurrency/atomics_native` |
| `T408` | MIR interpreter oracle atomic memory model, modification-order store buffer, vector-clock release/acquire & release sequences, deterministic schedule explorer, spurious `compare_exchange_weak` failure | `AXS-ATM-050`..`AXS-ATM-054` | `REQ-CONC-054`, `REQ-ATM-006, 007, 008, 010, 012, 013, 018, 019, 021, 026, 032` | `tests/run/concurrency/atomics_oracle` |
| `T409` | End-to-end atomic litmus & conformance suite (`LITMUS-MP`, `LITMUS-MP-FENCE`, `LITMUS-SB`, `LITMUS-LB`, `LITMUS-RMW`, `LITMUS-CAS-ABA`) across `--interp` and native x86-64 | `AXS-ATM-061`..`AXS-ATM-066` | `REQ-CONC-076, 077, 078, 079`, `REQ-ATM-028, 029, 030` | `tests/conformance/p11/e11_2_atomics` |

---

## 9. Sources

- `docs/base/specs/0092 - Axiom Memory Model & Atomic Operations Specification.md` (§1–§28)
- `docs/base/specs/0128 - Axiom Memory Model & Atomics Specification (C++20 happens-before, orderings, fences, volatile vs atomic).md` (§1–§64, `AATOM-20`..`40`)
- `docs/base/specs/0161 - Axiom M4 HIR & MIR Architecture Specification.md` (§30, atomic MIR statements)
- `docs/base/specs/0162 - Axiom M5 LIR, Calling Convention & Codegen Specification.md` (§30, `ALIR-23`, atomic LIR instructions)
- `docs/base/specs/0208 - Axiom Standard Library — sync & atomic Deep Specification.md` (§1–§39, `AATOM-50`)
- `docs/base/tasks/0328 - Axiom P4-T5 Intrinsics, Atomics, Volatile & Hardware Primitives Specification.md` (§6–§12)
- `docs/base/tasks/0515 - Axiom Deep Spec — P7-T2 Concurrency Runtime, Work-Stealing, Channels & Sync Primitives.md` (§6, §11–§12)
- `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-043`, `AXS-EXT-051`)
- `spec/SPEC-30-concurrency.md` (`AXS-CONC-001`..`060`)
- `spec/diagnostics.md` (`AXD-021`, §11)
- `spec/invariants.md` (`INV-CONC-001`..`007`, `INV-PIPE-002`..`003`, `INV-ORACLE-001`..`002`)
- `spec/requirements/CATALOG.md` (`E11.2` requirements `REQ-ATM-*`, `REQ-CONC-*`, `REQ-MIR-144`, `REQ-ASY-061`..`062`, `REQ-ASY-166`)
