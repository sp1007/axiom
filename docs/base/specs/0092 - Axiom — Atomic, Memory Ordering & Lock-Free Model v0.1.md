Tiếp tục.

# Axiom — Atomic, Memory Ordering & Lock-Free Model v0.1

Đây là phần cần làm rất chắc vì nếu thiết kế sai, Axiom có thể vừa **khó dùng** vừa mất lợi thế hiệu năng.

Mục tiêu:

> **Safe code có memory model rõ ràng; low-level code vẫn có đủ quyền để viết lock-free algorithm như C/C++; compiler không được tự ý làm yếu synchronization.**

---

## 1. Không để programmer phải hiểu memory model ở mọi nơi

Axiom nên chia thành 3 tầng:

```text
Application code
      │
      │ Mutex / Channel / Arc
      ▼
Concurrent library
      │
      │ Atomic
      ▼
System / lock-free code
      │
      │ Unsafe + explicit ordering
      ▼
CPU / hardware
```

Phần lớn application chỉ cần:

```axiom
mutex.lock()
channel.send(x)
channel.receive()
```

Chỉ system programmer mới thường xuyên viết:

```axiom
atomic.load(Ordering.Acquire)
atomic.compare_exchange(...)
```

Như vậy **ngôn ngữ không cần đơn giản hóa atomic bằng cách làm yếu nó**.

---

# 2. Atomic là type property

Không nên cho phép:

```axiom
var x: i64

atomic_add(&x, 1)
```

trong safe code.

Thay vào đó:

```axiom
var x = Atomic<i64>.new(0)

x.fetch_add(1, Ordering.Relaxed)
```

Lý do:

```text
i64
```

và

```text
Atomic<i64>
```

có semantics hoàn toàn khác nhau.

Compiler nhìn thấy type là biết ngay:

```text
i64           → ordinary memory
Atomic<i64>   → atomic memory
```

---

# 3. Atomic không nhất thiết phải là object

Surface syntax:

```axiom
Atomic<i64>
```

không có nghĩa phải tồn tại object header.

Compiler có thể hạ xuống:

```text
memory location
+
alignment
+
atomic machine operation
```

Ví dụ:

```axiom
let counter = Atomic<i64>.new(0)
```

có thể trở thành một `i64` bình thường trong `.bss` hoặc stack, tùy context.

---

# 4. Atomic operations

Core primitive tối thiểu:

```text
load
store
swap
fetch_add
fetch_sub
fetch_and
fetch_or
fetch_xor
compare_exchange
compare_exchange_weak
```

Có thể bổ sung:

```text
fetch_max
fetch_min
```

ở library nếu target hỗ trợ hiệu quả hoặc compiler tự lower.

Không nên nhồi hàng chục operation vào language core.

---

# 5. Ordering

Giữ 5 mức:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Đây là tập đủ mạnh cho hệ thống hiện đại.

### Relaxed

Đảm bảo atomicity của chính atomic operation nhưng không tạo synchronization ordering.

```axiom
counter.fetch_add(1, Relaxed)
```

phù hợp cho:

```text
statistics
reference counters đặc biệt
work counters
non-synchronizing state
```

---

# 6. Release / Acquire

Đây là cặp quan trọng nhất.

Concept:

```text
Thread A

data = 42
flag.store(1, Release)
```

và:

```text
Thread B

if flag.load(Acquire) == 1 {
    use(data)
}
```

Khi Acquire đọc được giá trị phù hợp từ Release:

```text
data = 42
      │
      ▼
Release
      │
      │ synchronizes-with
      ▼
Acquire
      │
      ▼
use(data)
```

Compiler không được reorder qua boundary nếu làm thay đổi semantics.

---

# 7. AcqRel

Dùng cho operation vừa đọc vừa publish.

Ví dụ CAS:

```axiom
queue.head.compare_exchange(
    old,
    new,
    Ordering.AcqRel,
    Ordering.Acquire
)
```

Success:

```text
Acquire + Release
```

Failure:

```text
Acquire
```

Tách success/failure ordering là cần thiết cho lock-free algorithms.

---

# 8. SeqCst

`SeqCst` nên tồn tại nhưng **không phải default**.

```axiom
atomic.store(1, Ordering.SeqCst)
```

Nó tạo một thứ tự tuần tự nhất quán trên các SeqCst operations theo memory model.

Không nên làm:

```axiom
atomic.store(1)
```

tự động thành SeqCst.

Nếu làm vậy:

- dễ dùng hơn một chút
- nhưng dễ tạo code chậm hơn
- và che mất semantics.

Axiom ưu tiên:

> **explicit semantics at semantic boundaries.**

---

# 9. Không có implicit atomic conversion

Không:

```axiom
Atomic<i64> → i64
```

và cũng không:

```axiom
i64 → Atomic<i64>
```

trong phép toán.

Phải viết:

```axiom
x.load(Ordering.Relaxed)
```

hoặc:

```axiom
Atomic<i64>.new(value)
```

Điều này giúp compiler và AI agent đọc code rất dễ.

---

# 10. Atomic alignment

Atomic type phải có alignment phù hợp target.

Ví dụ:

```text
Atomic<i64>
```

có thể yêu cầu 8-byte alignment trên target thông thường.

Nếu target không hỗ trợ native atomic operation:

```text
compiler
   ├── native instruction
   ├── library fallback
   └── compile-time unsupported
```

Không được âm thầm biến atomic thành ordinary load/store.

---

# 11. Lock-free property

Không nên giả định:

```text
Atomic<T> == always lock-free
```

Axiom nên có compile-time query:

```axiom
Atomic<i64>.is_lock_free()
```

hoặc tốt hơn:

```axiom
is_lock_free<Atomic<i64>>()
```

Compiler có thể biết:

```text
LOCK_FREE
NOT_LOCK_FREE
UNKNOWN
```

Nếu programmer cần guarantee:

```axiom
require_lock_free<Atomic<i64>>()
```

thì compilation fail trên target không đáp ứng.

---

# 12. Memory model phải độc lập CPU

Axiom semantic model:

```text
Source
  ↓
Atomic semantics
  ↓
MIR
  ↓
LIR
  ↓
x86 / ARM / RISC-V
```

Không được định nghĩa:

```text
Acquire = x86 instruction X
```

Thay vào đó:

```text
Acquire = semantic ordering
```

Backend quyết định instruction sequence.

Ví dụ x86 có memory model tương đối mạnh; ARM có thể cần instruction/barrier khác.

Program semantics vẫn giống nhau.

---

# 13. Atomic fence

Có thể có:

```axiom
atomic.fence(Ordering.Acquire)
atomic.fence(Ordering.Release)
atomic.fence(Ordering.SeqCst)
```

nhưng nên để ở **system/concurrency library**, không khuyến khích application code.

Compiler phải hiểu fence là semantic barrier.

---

# 14. Compiler optimization và atomics

Compiler được phép:

```text
inline
constant-fold
eliminate dead ordinary operations
reorder ordinary operations
```

nhưng **không được vượt qua atomic boundary một cách làm thay đổi observable memory ordering**.

Ví dụ không được biến:

```text
ordinary write
Release store
```

thành:

```text
Release store
ordinary write
```

nếu điều đó phá synchronization semantics.

---

# 15. Data race là invalid safe program

Cần phân biệt:

```text
data race
```

với:

```text
atomic race
```

Ví dụ:

```text
Thread A: x = 1
Thread B: x = 2
```

với `x: i32` shared mutable:

```text
INVALID
```

Nhưng:

```text
Atomic<i32>
```

thì:

```text
VALID
```

và kết quả phụ thuộc atomic semantics.

---

# 16. Race detector không phải memory model

Runtime sanitizer có thể hỗ trợ:

```text
-race
```

nhưng nó không thay thế compiler verification.

Axiom nên có:

```text
compile-time safety
+
optional dynamic race detection
```

Dynamic tool giúp tìm bug trong:

- unsafe code
- FFI
- runtime/library implementation
- compiler bugs

---

# 17. Lock-free không có nghĩa wait-free

Axiom không nên dùng một từ chung kiểu:

```text
AtomicQueue
```

rồi tuyên bố mọi thứ lock-free.

Các property cần phân biệt:

```text
Blocking
Lock-free
Wait-free
Obstruction-free
```

Đây là **algorithm/library properties**, không phải language primitives.

---

# 18. ABA problem

Ví dụ:

```text
A → B → A
```

CAS có thể thấy:

```text
expected == A
```

nhưng object giữa hai lần kiểm tra đã thay đổi.

Axiom không thể tự giải quyết ABA bằng compiler.

Library có thể dùng:

```text
generation
tagged pointer
hazard pointer
epoch reclamation
```

Đặc biệt ở đây mô hình `generation` mà ta đã chọn cho `Handle<T>` rất hữu ích.

---

# 19. Handle + generation

Ví dụ:

```text
Handle<Node>
```

conceptually:

```text
(index, generation)
```

Khi remove:

```text
generation++
```

Handle cũ:

```text
(index, old_generation)
```

không còn hợp lệ.

Điều này giải quyết **stale logical handles**.

Nhưng cần lưu ý:

> generation handle **không tự giải quyết memory reclamation của raw lock-free pointers**.

Hai vấn đề phải giữ riêng:

```text
logical stale handle
```

vs

```text
physical memory reclamation
```

---

# 20. `AtomicShared<T>`

Sau này standard library có thể cung cấp:

```axiom
AtomicShared<T>
```

nhưng không nên biến `Arc<T>` thành atomic pointer một cách implicit.

Ví dụ:

```axiom
var current: AtomicShared<Config>
```

cho phép:

```text
load
store
swap
compare_exchange
```

với ownership semantics rõ ràng.

Đây là abstraction rất mạnh cho:

```text
configuration snapshots
read-mostly state
lock-free publication
versioned state
```

---

# 21. Shared mutable state

Axiom nên làm cho pattern này rõ ràng:

```axiom
Arc<Mutex<T>>
```

hoặc:

```axiom
Arc<RwLock<T>>
```

thay vì:

```axiom
Arc<T>
```

rồi compiler somehow cho phép mutation.

`Arc<T>` chỉ giải quyết:

```text
shared ownership
```

Không giải quyết:

```text
mutable synchronization
```

---

# 22. Không có implicit atomic reference counting

Đây là điểm quan trọng để giữ performance.

Không làm:

```text
passing object
    ↓
automatically increment RC
```

Axiom không có implicit reference counting.

Nếu muốn:

```axiom
Arc<T>
```

thì programmer chọn nó.

Compiler vẫn có thể tối ưu:

```text
Arc clone/drop
```

khi semantics cho phép.

---

# 23. `Arc` có thể được compiler tối ưu

Ví dụ:

```axiom
fn foo(x: Arc<Data>) {
    use(x)
}
```

Compiler có thể chứng minh không có escape/copy thật sự cần thiết.

Nhưng không được bỏ atomic refcount nếu observation của program phụ thuộc vào nó.

Đây là nguyên tắc:

> **Optimization may erase implementation, never semantic ownership.**

---

# 24. Unsafe lock-free code

Axiom cần cho phép:

```axiom
unsafe fn push(node: *mut Node) {
    ...
}
```

nhưng unsafe không biến mọi thứ thành:

```text
"compiler trusts me blindly"
```

Compiler vẫn kiểm tra:

- types
- layout
- syntax
- ABI
- initialization
- machine constraints

Nhưng programmer chịu trách nhiệm với:

- pointer validity
- reclamation
- synchronization protocol
- aliasing invariant
- atomic algorithm correctness

---

# 25. Có nên có `unsafe atomic`?

Không.

Atomic primitive bản thân nó nên là **safe**.

Ví dụ:

```axiom
counter.fetch_add(1, Relaxed)
```

không cần `unsafe`.

Bởi vì compiler có thể đảm bảo:

```text
operation is atomic
```

Còn **algorithm** dùng atomic có đúng hay không là chuyện khác.

Nếu programmer dùng atomic sai logic:

```text
lost update
livelock
ABA
incorrect ordering
```

đó có thể là logical bug mà không phải memory safety violation.

---

# 26. `compare_exchange` API

Tôi đề xuất:

```axiom
let result = x.compare_exchange(
    expected,
    desired,
    Ordering.AcqRel,
    Ordering.Acquire
)
```

trả về một enum kiểu:

```axiom
enum CasResult<T> {
    Success(T),
    Failure(T)
}
```

hoặc API tương đương.

Quan trọng là:

> **Không mutate `expected` bằng một side-channel khó hiểu.**

Result semantics sẽ thân thiện hơn với compiler/AI.

---

# 27. Spurious failure

`compare_exchange_weak` có thể fail dù giá trị thực tế bằng expected.

Nó phù hợp trong loop:

```axiom
loop {
    let old = x.load(Relaxed)

    let r = x.compare_exchange_weak(
        old,
        old + 1,
        AcqRel,
        Relaxed
    )

    if r.success {
        break
    }
}
```

Compiler có thể optimize loop rất mạnh.

---

# 28. Atomic memory model trong MIR

MIR cần explicit:

```text
ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS
ATOMIC_FENCE
```

với:

```text
ordering
volatile=false/true
type
alignment
```

Ví dụ conceptually:

```text
ATOMIC_STORE
    ptr = %p
    value = %v
    ordering = RELEASE
```

Không được hạ atomic thành ordinary `STORE` quá sớm.

---

# 29. LIR

LIR giữ semantics:

```text
ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS
FENCE
```

Sau đó target lowering mới quyết định:

```text
x86
ARM64
RISC-V
WASM
```

---

# 30. Lock-free library architecture

Tôi đề xuất standard library sau này:

```text
std.concurrent
├── thread
├── channel
├── mutex
├── rwlock
├── condition
├── barrier
├── semaphore
├── atomic
├── arc
├── once
└── lockfree
    ├── queue
    ├── stack
    ├── ring
    ├── epoch
    ├── hazard
    └── atomic_shared
```

Trong đó:

```text
atomic
```

gần Core.

Còn:

```text
lockfree
```

hoàn toàn library/system layer.

---

# 31. `Once`

Một primitive rất hữu ích:

```axiom
Once
```

cho:

```axiom
once.call(|| {
    initialize()
})
```

Dùng cho:

- lazy initialization
- singleton resource
- global initialization có kiểm soát

Nhưng **không tạo hidden global constructor**.

---

# 32. Thread-local

Axiom nên hỗ trợ semantic:

```text
thread_static
```

Ví dụ:

```axiom
@thread_local
static var buffer: Buffer
```

Nhưng compiler/runtime chỉ link TLS support khi cần.

Không phải mọi executable đều có TLS runtime overhead.

---

# 33. False sharing

Không nên thêm language keyword.

Library:

```axiom
CachePadded<T>
```

hoặc:

```axiom
@align(64)
```

là đủ.

Ví dụ:

```axiom
struct Counters {
    @align(64)
    a: Atomic<i64>

    @align(64)
    b: Atomic<i64>
}
```

Đây là một ví dụ tốt về nguyên tắc:

> **compiler/language cung cấp primitive nhỏ; library cung cấp abstraction.**

---

# 34. Memory reclamation — quyết định quan trọng

Tôi chốt:

### Core không có:

```text
GC
RC
hazard pointer
epoch
RCU
reclamation runtime
```

### Library/System có thể có:

```text
Arc
Weak
Epoch
Hazard
AtomicShared
Pool
Arena
```

### Unsafe programmer có:

```text
raw pointer
custom reclamation
custom allocator
custom lock-free algorithm
```

Như vậy Axiom vẫn đủ sức viết kernel/runtime/database/game engine.

---

# 35. Atomic invariants

Bổ sung:

```text
AATOM-01  Atomicity Is Type-Semantic
AATOM-02  Atomic Is Not Implicit
AATOM-03  Ordering Is Explicit
AATOM-04  Relaxed Preserves Atomicity
AATOM-05  Acquire/Release Synchronization Is Preserved
AATOM-06  AcqRel Preserves Both Directions
AATOM-07  SeqCst Is Explicit
AATOM-08  Failure Ordering Is Explicit
AATOM-09  Atomic Alignment Is Enforced
AATOM-10  Lock-Free Is Not Assumed
AATOM-11  Atomic != Volatile
AATOM-12  Compiler Cannot Weaken Ordering
AATOM-13  Backend Must Preserve Atomic Semantics
AATOM-14  Fences Are Semantic
AATOM-15  Data Race Requires Synchronization
AATOM-16  Unsafe May Implement Custom Synchronization
AATOM-17  Memory Reclamation Is Not Core
AATOM-18  ABA Is Library/System Responsibility
AATOM-19  Lock-Free Is Not Wait-Free
AATOM-20  Atomic APIs Have No Hidden Allocation
```

---

# 36. Một điểm tôi muốn thay đổi so với nhiều ngôn ngữ hiện đại

Không nên bắt programmer phải viết:

```text
Send + Sync + 'static + lifetime...
```

ở khắp nơi.

Axiom source code:

```axiom
thread.spawn(move || {
    process(data)
})
```

Compiler tự kiểm tra:

```text
capture
  ↓
ownership
  ↓
escape
  ↓
Send
  ↓
lifetime
```

Chỉ khi có lỗi mới nói:

```text
AX_CONC_0007
value `data` cannot be transferred to another execution context
reason: type contains non-Send state
```

Đây chính là:

> **Compiler Complexity Is Not Language Complexity.**

---

# 37. Tổng thể concurrency model sau khi hoàn thiện

```text
                     Axiom
                       │
              ┌────────┴────────┐
              │                 │
          Sequential        Concurrent
              │                 │
          Ownership       Ownership + Access
                                │
                 ┌──────────────┼──────────────┐
                 │              │              │
               Thread        Channel        Async
                 │              │              │
                Send          Send        State Machine
                 │                             │
                 └──────────────┬──────────────┘
                                │
                         Synchronization
                                │
                    ┌───────────┼───────────┐
                    │           │           │
                  Mutex       Atomic      RwLock
                    │           │
                    └─────┬─────┘
                          │
                    Lock-free layer
                          │
             ┌────────────┼────────────┐
             │            │            │
           Epoch       Hazard      AtomicShared
```

Đây là kiến trúc tôi đánh giá phù hợp với mục tiêu Axiom hơn việc cố nhét tất cả vào type system.

---

# Tiếp tục → Async lowering sâu

Bây giờ nền atomic đã đủ. Bước kế tiếp là **Async State Machine + Executor + Cancellation + Stackless/Stackful coroutine**.

Đây là chỗ chúng ta phải quyết định một vấn đề rất quan trọng:

> **Axiom có cần runtime/executor cho `async` hay compiler có thể tạo async code gần như zero-cost và để executor hoàn toàn bên ngoài?**

Hướng tôi nghiêng về hiện tại là **compiler chỉ tạo state machine; executor là library/platform component**, nhưng cần phân tích sâu trước khi đóng băng quyết định này.