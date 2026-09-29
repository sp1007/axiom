# BOOTSTRAP-106 — Axiom Semantic Verification Engine
**FROZEN / COMPLETED**

Đây là “hàng rào an toàn” giữa semantic compiler và optimizer.

Mục tiêu:

> **Axiom phải tự chứng minh được ownership, lifetime, aliasing, capability, concurrency và resource safety trong safe code — nhưng không bắt programmer viết lifetime/borrow annotation.**

Và một nguyên tắc rất quan trọng:

> **Compiler có thể từ chối một chương trình khi không chứng minh được an toàn; nhưng không được tự giả định nó an toàn.**

---

# 1. Vị trí của Verifier

```text
Fully Typed HIR
      ↓
     MIR
      ↓
┌──────────────────────────┐
│     SEMANTIC VERIFIER    │
│                          │
│ Initialization           │
│ Ownership                │
│ Drop                     │
│ Capability               │
│ Provenance               │
│ Aliasing                 │
│ Escape                   │
│ Send / Share             │
│ Async                    │
│ Concurrency              │
│ GPU                      │
│ FFI                      │
│ Comptime                 │
└────────────┬─────────────┘
             ↓
       VERIFIED MIR
             ↓
          OptIR
```

**Optimizer không được nhận unverified MIR.**

---

# 2. Verifier không phải borrow checker kiểu Rust

Axiom không muốn programmer viết:

```text
'a
&'a T
&'a mut T
where 'a: 'b
```

Thay vào đó compiler tự tạo:

```text
CapabilityId
RegionId
ProvenanceId
Lifetime
AccessMode
```

và giải chúng internally.

Vì vậy:

```text
Rust:
programmer + compiler
    ↓
lifetime reasoning

Axiom:
compiler
    ↓
lifetime reasoning
```

---

# 3. Kiến trúc Verifier

Đề xuất một framework chung:

```text
VerifierEngine
 ├── CFGAnalysis
 ├── InitAnalysis
 ├── OwnershipAnalysis
 ├── DropAnalysis
 ├── CapabilityAnalysis
 ├── RegionAnalysis
 ├── AliasAnalysis
 ├── EscapeAnalysis
 ├── SendShareAnalysis
 ├── AsyncAnalysis
 ├── ConcurrencyAnalysis
 ├── GPUAnalysis
 ├── FFIAnalysis
 └── ComptimeAnalysis
```

Các analysis chia sẻ cùng dataflow infrastructure.

---

# 4. Generic Dataflow Engine

Không viết từng verifier thành một hệ thống riêng.

```text
DataflowAnalysis<State>
```

có:

```text
initial_state()
transfer(block, state)
join(state_a, state_b)
equals(a, b)
```

Có thể chạy:

```text
Forward
Backward
Forward + Backward
```

---

# 5. Tại sao dùng chung framework?

Ownership, initialization và capability đều là dataflow problem.

Ví dụ:

```text
bb0
 ├── bb1
 └── bb2
      ↓
     bb3
```

Verifier cần merge state tại `bb3`.

Một framework thống nhất giúp:

- dễ kiểm chứng
- incremental
- cache
- parallel
- debug
- AI explainability

---

# 6. CFG trước tiên

Verifier xây:

```text
CFG
```

với:

- predecessors
- successors
- dominators
- post-dominators
- loops
- unreachable blocks
- exceptional edges

---

# 7. Reachability

Block không reachable:

```text
unreachable:
    ...
```

không cần thực hiện ownership analysis bình thường.

Nhưng compiler vẫn có thể:

- warning
- error
- eliminate

tùy semantics.

---

# 8. Definite Initialization

Mỗi `Place` có state:

```text
UNINIT
INIT
MOVED
PARTIAL
DROPPED
```

Ví dụ:

```axiom id="b2fjr9"
let x: String;

if condition {
    x = make();
}

print(x);
```

Nếu có path:

```text
condition = false
```

thì:

```text
x = UNINIT
```

→ reject.

---

# 9. Merge initialization

Ví dụ:

```text
path A: x = INIT
path B: x = INIT
```

→

```text
INIT
```

Nhưng:

```text
path A: INIT
path B: UNINIT
```

→

```text
MAYBE_INIT
```

và read không hợp lệ.

---

# 10. Ownership State

Ownership state:

```text
UNOWNED
OWNED
MOVED
PARTIALLY_MOVED
DROPPED
```

Compiler tracking theo `Place`.

Ví dụ:

```text
a = Owned
b = Move(a)
```

sau đó:

```text
a = Moved
b = Owned
```

---

# 11. Ownership tree

Nếu:

```text
p.position
p.velocity
```

thì ownership state không chỉ ở `p`.

Compiler duy trì place tree:

```text
p
├── position
└── velocity
```

Điều này cho phép partial move.

---

# 12. Partial move

```axiom id="ry9r9p"
let p = Particle(...);

let x = p.position;
use(p.velocity);
```

Nếu hợp lệ:

```text
p
├── position → MOVED
└── velocity → OWNED
```

Drop cuối scope chỉ xử lý field còn owned.

---

# 13. Custom Drop

Nếu `Particle` có custom Drop:

```text
partial move
```

không được tự động cho phép nếu phá invariant của Drop.

Đây là lý do:

```text
Drop
```

là một semantic property chứ không chỉ là function.

---

# 14. Copy

Verifier xử lý:

```text
Copy(place)
```

khác:

```text
Move(place)
```

Copy:

```text
source remains valid
```

Move:

```text
source ownership consumed
```

---

# 15. Copy không làm mất ownership

```axiom id="w3akqf"
let a: i32 = 10;
let b = a;
use(a);
use(b);
```

hợp lệ.

Verifier biết:

```text
i32 : Copy
```

---

# 16. Clone

```axiom id="7g0zjk"
let b = a.clone();
```

Verifier coi đó là một function call bình thường về ownership:

```text
a remains valid
b receives new ownership
```

Không có “implicit clone state”.

---

# 17. Drop verification

Verifier phải đảm bảo:

```text
Drop(x)
```

chỉ xảy ra khi:

```text
x = INIT/OWNED
```

không:

```text
UNINIT
MOVED
DROPPED
```

---

# 18. Exactly-once cleanup

Mục tiêu:

> Mỗi owning resource phải được cleanup đúng semantic số lần.

Không phải literal “exactly once Drop instruction” vì optimization có thể eliminate hoặc fuse cleanup.

Semantic requirement là:

```text
resource initialized
→ cleanup obligation exists
→ cleanup discharged exactly once
```

---

# 19. Cleanup on every exit

Các đường ra:

```text
return
break
continue
panic
unwind
fallthrough
```

đều phải xử lý resource.

Verifier kiểm tra cleanup graph.

---

# 20. Cleanup ladder

Ví dụ:

```text
scope:
    a
    b
    c
```

Khi thoát:

```text
Drop(c)
Drop(b)
Drop(a)
```

trừ những resource đã moved/dropped.

---

# 21. Capability model

Mỗi capability:

```text
Capability {
    id
    owner
    region
    provenance
    access
    lifetime
    storage_domain
    execution_domain
}
```

---

# 22. Access modes

Core:

```text
READ
WRITE
MOVE
DROP
```

Trong đó:

```text
READ + READ
```

hợp lệ.

Nhưng:

```text
READ + WRITE
WRITE + WRITE
```

không hợp lệ nếu overlap.

---

# 23. Region model

Compiler không chỉ dùng:

```text
same / different
```

mà có:

```text
DISJOINT
SAME
CONTAINS
CONTAINED_BY
OVERLAPS
UNKNOWN
```

Ví dụ:

```text
particle.position
particle.velocity
```

→ `DISJOINT`.

---

# 24. Region conflict

Nếu:

```text
R1 OVERLAPS R2
```

và:

```text
C1 = WRITE
C2 = READ
```

→ conflict.

Nếu:

```text
R1 DISJOINT R2
```

→ có thể đồng thời.

---

# 25. Unknown không đồng nghĩa overlap

Nhưng:

```text
UNKNOWN
```

không được coi là:

```text
DISJOINT
```

Ví dụ:

```axiom id="qz8m0v"
fn f(a: mut_view<i32>, b: mut_view<i32>)
```

Nếu compiler không chứng minh `a` và `b` disjoint:

→ safe call có thể bị reject.

---

# 26. Nhưng Axiom không nên reject quá nhiều

Đây là điểm khác biệt quan trọng.

Compiler có thể lấy thông tin từ:

- array index ranges
- struct fields
- slices
- API contracts
- ownership
- loop induction variables
- generic constraints
- `disjoint` abstractions
- compiler-known containers

để chứng minh disjoint.

---

# 27. Ví dụ field splitting

```axiom id="5r1rjd"
fn f(p: mut_view<Particle>) {
    update_position(p.position);
    update_velocity(p.velocity);
}
```

Verifier:

```text
p.position → R1
p.velocity → R2

R1 DISJOINT R2
```

→ hợp lệ.

---

# 28. Slice splitting

Library có thể cung cấp:

```axiom id="r7q8uc"
split_at(data, index)
```

semantic contract:

```text
left.region DISJOINT right.region
```

Compiler không cần biết implementation chi tiết để sử dụng guarantee đã được verify.

---

# 29. Capability lifetime

Compiler không cần programmer khai báo lifetime.

Nó tính:

```text
first use
last use
scope
CFG paths
escape
await boundaries
```

Ví dụ:

```axiom id="2r3jbb"
let v = view(data);

use(v);

other();

```

Nếu `v` không còn dùng:

```text
capability lifetime ends
```

ngay tại điểm semantic cuối cùng phù hợp.

---

# 30. Compiler có thể rút ngắn lifetime

Nếu:

```axiom id="3mb8b7"
let v = view(data);
use(v);
mutate(data);
```

compiler biết `v` chết sau `use(v)`.

Do đó:

```text
READ capability
    ↓
use
    ↓
capability ends
    ↓
WRITE capability
```

hợp lệ.

Không cần lexical scope kết thúc mới release capability.

---

# 31. Đây là một lợi thế lớn của Axiom

Programmer không cần viết:

```text
{
    let v = ...
}
```

chỉ để “đánh dấu lifetime”.

Compiler tự tìm semantic last-use.

---

# 32. Escape analysis

Mỗi value/capability có escape state:

```text
NO_ESCAPE
ARGUMENT_ESCAPE
RETURN_ESCAPE
HEAP_ESCAPE
THREAD_ESCAPE
EXTERNAL_ESCAPE
UNKNOWN_ESCAPE
```

---

# 33. View return

Ví dụ:

```axiom id="0wx8o8"
fn first(data: view<Array<i32>>) -> view<i32>
```

Compiler phải chứng minh:

```text
returned view
    ↓
provenance = data
```

và owner của `data` vẫn sống đủ lâu.

Nếu không chứng minh được:

→ reject.

---

# 34. Không cho dangling view

Ví dụ:

```axiom id="4z5d9x"
fn bad() -> view<i32> {
    let data = [1, 2, 3];
    return view(data);
}
```

Compiler:

```text
data lifetime ends
returned view escapes
```

→ reject.

Không cần lifetime annotation.

---

# 35. View stored in owner

Ví dụ:

```text id="t9u1tb"
struct Holder {
    data: Array<i32>,
    view: view<i32>
}
```

đây là relationship phức tạp vì:

```text
view → data
```

Compiler phải chứng minh self-referential invariant.

**Khuyến nghị Core v1:**

> Không cho phép safe self-referential ownership pattern nếu compiler không có stable-address/storage contract để chứng minh.

Programmer phải dùng abstraction như:

```text
Handle
index
offset
stable storage
```

thay vì tự tạo dangling self-reference.

---

# 36. Stable address

Verifier phân biệt:

```text
relocatable storage
```

và:

```text
stable-address storage
```

Nếu `view` hoặc external system yêu cầu address stability:

```text
storage contract = STABLE
```

thì relocation bị cấm.

---

# 37. `Vec` relocation

Ví dụ:

```axiom id="1jhz1a"
let v = Vec<i32>();
let view = view(v);

v.push(10);
```

Nếu `push` có thể realloc:

```text
live view
+
potential relocation
```

→ compiler phải:

- reject
- hoặc prove capacity/no relocation
- hoặc API contract đảm bảo operation không relocate.

Không được giả định `reserve()` vĩnh viễn giữ địa chỉ.

---

# 38. `reserve` không phải stable-address guarantee

Đây là invariant quan trọng:

> **Capacity guarantee ≠ address stability guarantee.**

Chỉ storage contract mới tạo stable address.

---

# 39. Provenance

Raw pointer:

```text id="0r1qqq"
*mut T
```

có provenance machine-level.

Verifier không được suy:

```text
integer 0x1234
```

→ valid pointer.

Safe capability phải có provenance hợp lệ.

---

# 40. Unsafe boundary

Ví dụ:

```axiom id="r0j9g2"
unsafe {
    let p = address_of(x);
}
```

Unsafe cho phép programmer tạo machine-level assumption.

Nhưng:

> **unsafe không tắt verifier.**

---

# 41. Unsafe contract

Nếu:

```text id="9y1c8q"
raw pointer → mut_view<T>
```

unsafe boundary phải thiết lập:

```text
pointer valid
alignment valid
region valid
lifetime valid
access permission valid
```

Sau đó verifier tiếp tục tracking capability.

---

# 42. Unsafe không biến mọi thứ thành trusted

Không cho:

```text id="y6wwgr"
unsafe {
    everything_is_safe();
}
```

Mà chỉ những semantic precondition cụ thể được established.

---

# 43. Send analysis

Khi:

```axiom id="c4bqhz"
spawn(task);
```

compiler xác định state của task.

Nếu task cần chuyển ownership sang thread:

```text
T : Send
```

phải proven.

---

# 44. Send != Share

Ví dụ:

```text id="e2a6d8"
Buffer : Send
Buffer : !Share
```

có nghĩa:

```text id="f0b4c0"
thread A
    Move Buffer
        ↓
thread B
```

được.

Nhưng đồng thời chia sẻ Buffer cho A+B thì không.

---

# 45. Share analysis

`Share` nghĩa:

> có thể tồn tại concurrent access theo contract của type.

Nhưng:

```text id="6vrzjw"
Share<T>
```

không tự có nghĩa:

```text mutable access
```

---

# 46. Mutable shared access

Ví dụ:

```text id="z7t1iz"
Arc<Mutex<T>>
```

thì:

```text id="d0m3px"
Arc → shared ownership
Mutex → synchronization
guard → exclusive capability
```

Mỗi lớp có trách nhiệm riêng.

---

# 47. Arc không làm T thread-safe

```text id="4jv7d4"
Arc<T>
```

không tự biến:

```text
T : !Share
```

thành:

```text
T : Share
```

Compiler phải kiểm tra đúng trait semantics.

---

# 48. Data race verification

Safe Axiom phải reject:

```text id="o9y3wv"
thread A: WRITE(x)
thread B: READ(x)
```

nếu:

```text
same region
no synchronization
```

---

# 49. Nhưng compiler không cần chứng minh toàn bộ runtime schedule

Đây là điểm quan trọng để giữ compile-time khả thi.

Verifier không cố mô phỏng mọi thread interleaving.

Nó chứng minh:

```text
ownership
capability
synchronization contracts
```

đủ để đảm bảo safe concurrent access.

---

# 50. Happens-before

Verifier dùng memory model đã frozen:

```text id="4eq2cs"
sequenced-before
synchronizes-with
happens-before
```

Ví dụ:

```text
Release(store)
      ↓
Acquire(load)
```

có synchronization relation.

---

# 51. Lock guards

```axiom id="y0o4cz"
let guard = mutex.lock();
modify(guard.value);
```

Verifier biết:

```text
guard owns lock capability
```

và:

```text
Drop(guard)
```

→ unlock semantic.

---

# 52. Guard không được Copy

Verifier đảm bảo:

```text id="n6k5wm"
MutexGuard : !Copy
```

vì nếu copy:

```text
two guards
same lock
```

sẽ phá ownership.

---

# 53. Guard across await

```axiom id="d8yq8s"
async fn f() {
    let guard = mutex.lock();
    await something();
    use(guard);
}
```

Mặc định:

→ reject.

Lý do:

- giữ synchronous lock qua suspension
- có thể block executor
- lock capability sống qua await

Async-aware lock có API riêng và semantics riêng.

---

# 54. Async verifier

Tại mỗi:

```text id="p0w3la"
Suspend(S1)
```

compiler tính:

```text id="fpxb1d"
LiveValues
LiveCapabilities
LiveGuards
LiveResources
```

sau đó kiểm tra:

```text id="qkzjgl"
Send
storage stability
execution domain
```

---

# 55. Future state

Chỉ những gì sống qua suspension mới vào Future state.

Verifier cung cấp facts cho Async Lowering/Optimization.

---

# 56. Cancellation

Cancellation không được coi là panic.

Verifier phải đảm bảo khi Future bị drop:

```text id="i8e9l7"
initialized state fields
```

được cleanup đúng.

---

# 57. In-flight operations

Nếu:

```text id="u1xk21"
async_read(buffer)
```

đang chạy và Future bị drop, compiler/runtime contract phải xác định:

```text operation cancelled?
operation continues?
buffer retained?
```

Không được để memory lifetime phụ thuộc vào assumption mơ hồ.

---

# 58. Channel verification

Channel:

```text id="v8i5g2"
send(value)
```

semantic:

```text id="h7v2ar"
ownership transfer
```

Sau successful send:

```text id="b5u7re"
sender no longer owns value
```

---

# 59. Zero-copy channel

Verifier không yêu cầu physical copy.

Có thể:

```text id="q0r3ko"
ownership transfer
```

và runtime truyền:

```text pointer/handle
```

miễn semantic ownership đúng.

---

# 60. GPU verification

Kernel verifier kiểm tra:

```text id="l3z0te"
no illegal host operation
no blocking host mutex
no arbitrary host pointer
valid device storage
valid address space
valid synchronization
valid atomic
```

---

# 61. GPU capability

```text id="8h0t2y"
DeviceView<T>
```

không thể tự biến thành:

```text id="i6p4ea"
HostView<T>
```

Storage domain phải match.

---

# 62. GPU race detection

Nếu hai GPU threads có:

```text id="v3knjv"
WRITE
WRITE
same region
no atomic/barrier
```

→ kernel không hợp lệ.

Compiler có thể yêu cầu:

```text id="w4e8w2"
Atomic
Barrier
disjoint partition
```

---

# 63. FFI verification

Foreign call được coi conservative:

```text id="7d1xzn"
may read
may write
may alias
may escape
```

trừ khi FFI contract cung cấp thông tin tốt hơn.

---

# 64. Vì sao conservative?

Compiler không thể nhìn vào binary C library và tự biết:

```text id="5f4sqz"
pointer ownership
aliasing
thread behavior
```

Do đó default:

```text id="8s0r2k"
UNKNOWN
```

an toàn hơn giả định.

---

# 65. Comptime verification

Comptime chạy trong compiler environment nhưng vẫn phải tuân:

```text id="4h7i5s"
ownership
Drop
capability
sandbox
```

Unsafe comptime không được bypass sandbox.

---

# 66. Verification state

Mỗi MIR function có:

```text id="l9e2qp"
VerificationStatus
```

```text
UNVERIFIED
VERIFYING
VERIFIED
FAILED
```

Compiler cache được:

```text id="y7m1v8"
Verified MIR
```

nếu semantic fingerprint không thay đổi.

---

# 67. Incremental verification

Nếu chỉ thay:

```axiom id="l5c6r2"
fn unrelated() { ... }
```

không nên verify lại toàn package.

Dependency graph cho phép:

```text id="g0j2z9"
changed declaration
    ↓
affected MIR
    ↓
affected verification
```

---

# 68. Parallel verification

Các function độc lập có thể verify song song.

Nhưng kết quả phải deterministic.

```text id="r3j4y9"
parallel verification
==
serial semantic result
```

---

# 69. Compiler complexity không thành programmer complexity

Đây là thành quả quan trọng nhất của 106.

Programmer chỉ viết:

```axiom id="j1y2r3"
fn process(data: Data) {
    ...
}
```

Compiler internally có thể tạo:

```text id="g8h4k2"
Ownership graph
Capability graph
Region graph
Escape graph
Drop graph
CFG
Send/Share constraints
```

Không cần bắt programmer nhìn thấy tất cả.

---

# 70. Nhưng compiler phải giải thích được

Khi reject:

```text id="t0e8f1"
borrow conflict
```

không nên chỉ nói:

```text id="w3r7a5"
borrow error
```

Mà:

```text id="u2p5n8"
Cannot create mutable access to `data`.

Existing capability:
    READ
    source: line 18
    region: data[0..128]

Requested capability:
    WRITE
    source: line 22
    region: data[64..192]

Region relation:
    OVERLAPS
```

Đây là cực kỳ quan trọng cho AI coding agent.

---

# 71. Explain API

Compiler nên expose:

```text
axiom explain ownership x
axiom explain capability x
axiom explain lifetime x
axiom explain alias x
axiom explain send x
axiom explain drop x
axiom explain await x
```

và machine-readable:

```text
--format=json
```

---

# 72. Không formal-proof toàn bộ chương trình

Axiom không nên biến Core v1 thành theorem prover.

Mục tiêu là:

```text
dataflow analysis
+
type system
+
ownership
+
capability
+
explicit unsafe contracts
```

thay vì:

```text
dependent type theorem proving
```

Điều này giữ compiler thực tế.

---

# 73. Failure principle

Nếu compiler không chứng minh được:

```text id="f2e7r1"
safe
```

thì:

```text id="a9c8v4"
reject
```

hoặc programmer phải đi qua:

```text id="b3d2e1"
unsafe
```

với contract rõ ràng.

Không:

```text id="h1g2f3"
guess safe
```

---

# 74. Performance của verifier

Một mối lo hợp lý là:

> “Nếu compiler tự làm tất cả việc này thì compile sẽ rất chậm?”

Thiết kế để tránh điều đó:

### 1. Locality

Phần lớn ownership inference là local function analysis.

### 2. Incremental

Cache kết quả theo semantic fingerprint.

### 3. Shared dataflow engine

Không chạy hàng chục framework độc lập.

### 4. Fast path

Các function đơn giản có thể dùng verifier path đơn giản.

### 5. Escalation

Chỉ những case phức tạp mới chạy analysis sâu.

---

# 75. Verification tiers

Có thể thiết kế:

```text
Tier 0
Local type/init checks

Tier 1
Ownership/drop

Tier 2
Capability/alias/escape

Tier 3
Concurrency/async

Tier 4
GPU/FFI/comptime contracts
```

Không phải function nào cũng cần chạy toàn bộ mọi analysis.

---

# 76. Không có “safe nhưng unchecked”

Axiom nên giữ invariant:

> **Nếu compiler tuyên bố safe, semantic verifier đã kiểm tra các invariant tương ứng.**

Không có:

```text
safe
but skipped ownership
```

vì optimization hoặc compile-speed.

---

# 77. Unsafe là một boundary, không phải một mode

Ví dụ:

```axiom id="5z6q8r"
unsafe {
    raw_write(ptr, value);
}
```

Verifier vẫn kiểm tra:

- type
- CFG
- Drop
- initialized state
- các invariant không bị unsafe contract phá vỡ.

Chỉ một số machine-level assumptions được trusted.

---

# 78. Trusted Computing Base

Axiom nên cố giữ TCB nhỏ:

```text
Lexer
Parser
Type checker
Verifier
MIR semantics
Backend
```

Trong đó:

```text
unsafe source
```

không làm toàn compiler trở thành “trust me”.

---

# 79. Verified MIR → Optimizer

Sau BOOTSTRAP-106:

```text
Unverified MIR
      ↓
Verification
      ↓
Verified MIR
      ↓
┌─────────────────────────┐
│ Optimizer may assume:   │
│                         │
│ no invalid ownership    │
│ no invalid Drop         │
│ no invalid capability   │
│ no safe data race       │
│ valid initialization    │
│ valid async state       │
│ valid GPU access        │
└────────────┬────────────┘
             ↓
           OptIR
```

Đây là boundary cực kỳ mạnh.

---

# 80. Invariants — `AVERIFY-20..`

### `AVERIFY-20`
Only Verified MIR may enter semantic optimization.

### `AVERIFY-21`
Verification is deterministic.

### `AVERIFY-22`
Verification results are independent of optimization level.

### `AVERIFY-23`
Definite initialization is checked on all reachable CFG paths.

### `AVERIFY-24`
A value cannot be read before initialization.

### `AVERIFY-25`
A moved value cannot be read or moved again without valid reinitialization.

### `AVERIFY-26`
A dropped value cannot be dropped again.

### `AVERIFY-27`
Ownership state is tracked at place granularity.

### `AVERIFY-28`
Partial moves are tracked at field/projection granularity where permitted.

### `AVERIFY-29`
Custom Drop restrictions are enforced before accepting partial moves.

### `AVERIFY-30`
Every ownership obligation is discharged exactly once semantically.

### `AVERIFY-31`
All control-flow exits perform required cleanup.

### `AVERIFY-32`
Panic/unwind cleanup follows the selected panic profile.

### `AVERIFY-33`
Copy does not consume ownership.

### `AVERIFY-34`
Move consumes ownership.

### `AVERIFY-35`
Clone never appears implicitly.

### `AVERIFY-36`
Every safe capability has valid provenance.

### `AVERIFY-37`
Capability access mode is explicit.

### `AVERIFY-38`
READ/WRITE conflicts are rejected when regions may overlap.

### `AVERIFY-39`
WRITE/WRITE conflicts are rejected when regions may overlap.

### `AVERIFY-40`
Unknown overlap cannot be treated as proven disjoint.

### `AVERIFY-41`
Proven disjoint regions may be accessed independently.

### `AVERIFY-42`
Capability lifetime cannot exceed its valid provenance.

### `AVERIFY-43`
An owner cannot be destroyed while dependent capabilities remain live.

### `AVERIFY-44`
Relocation is forbidden while a stable-address contract requires address stability.

### `AVERIFY-45`
Relocatable storage cannot be exposed through an invalid long-lived capability.

### `AVERIFY-46`
Returned views must retain valid provenance.

### `AVERIFY-47`
Dangling safe views are rejected.

### `AVERIFY-48`
Raw pointer provenance is not inferred from integer addresses.

### `AVERIFY-49`
Unsafe may establish explicit trusted preconditions.

### `AVERIFY-50`
Safe verification resumes after an unsafe boundary.

### `AVERIFY-51`
Unsafe does not disable unrelated semantic verification.

### `AVERIFY-52`
Send is checked independently from Share.

### `AVERIFY-53`
Share does not imply mutable shared access.

### `AVERIFY-54`
Safe data races are rejected.

### `AVERIFY-55`
Synchronization contracts are respected in concurrent access analysis.

### `AVERIFY-56`
Mutex guards are ownership-bearing non-Copy capabilities.

### `AVERIFY-57`
Synchronous guards cannot cross await unless an explicit contract permits it.

### `AVERIFY-58`
Values live across suspension are checked for required Send/storage properties.

### `AVERIFY-59`
Future drop cleans initialized state fields.

### `AVERIFY-60`
Cancellation is distinct from panic.

### `AVERIFY-61`
Channel send/receive preserves ownership semantics.

### `AVERIFY-62`
GPU host/device capability domains are not implicitly interchangeable.

### `AVERIFY-63`
GPU race/synchronization rules are verified before kernel code generation.

### `AVERIFY-64`
Foreign calls are conservatively analyzed unless an explicit contract provides stronger facts.

### `AVERIFY-65`
Comptime code obeys core semantic safety rules.

### `AVERIFY-66`
Generated code cannot bypass semantic verification.

### `AVERIFY-67`
Verification analyses share a common dataflow framework.

### `AVERIFY-68`
Independent verification units may be analyzed in parallel.

### `AVERIFY-69`
Verification results are incrementally cacheable.

### `AVERIFY-70`
Compiler explanations retain the source provenance and semantic facts behind a verification failure.

### `AVERIFY-71`
The compiler must reject when required safety facts cannot be proven rather than guessing.

### `AVERIFY-72`
Safe source code never depends on optimizer behavior to become valid.

### `AVERIFY-73`
Verification may erase semantic metadata only after all corresponding obligations are discharged.

### `AVERIFY-74`
The optimizer may rely on verified ownership/capability facts.

### `AVERIFY-75`
Verification does not require programmer-written lifetime or borrow annotations.

### `AVERIFY-76`
The verifier must distinguish semantic resource lifetime from physical storage lifetime.

### `AVERIFY-77`
Physical allocation and deallocation are not inferred merely from ownership state.

### `AVERIFY-78`
The verifier does not require every valid program to expose its internal ownership graph to source syntax.

### `AVERIFY-79`
Verification diagnostics are structured and machine-readable.

### `AVERIFY-80`
The trusted semantic verifier is part of the compiler's correctness boundary.

---

# Kết quả của 106

Đến đây Axiom đã có một kiến trúc khá đặc biệt:

```text
                    PROGRAMMER
                         │
                         │ simple source
                         ▼
                  ┌─────────────┐
                  │    HIR      │
                  └──────┬──────┘
                         │
                  compiler infers
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      TYPE SYSTEM     OWNERSHIP     CAPABILITY
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                       MIR
                         │
                  ┌──────▼──────┐
                  │  VERIFIER   │
                  └──────┬──────┘
                         │
                  "PROVEN SAFE"
                         │
                         ▼
                    VERIFIED MIR
                         │
                         ▼
                       OPTIR
```

Điểm đáng chú ý là **Axiom không cố làm compiler đơn giản bằng cách bỏ safety**.

Nó làm ngược lại:

> **Compiler phức tạp hơn, programmer đơn giản hơn.**

Đây rất phù hợp với mục tiêu ban đầu của bạn.

---

# BOOTSTRAP-107 — Axiom Semantic Optimization & OptIR

Bây giờ mới đến phần tối ưu hóa thực sự.

Chúng ta đã có:

```text
103 Frontend
104 Type / Inference / Elaboration
105 HIR → MIR
106 MIR Verification
```

Bước 107 sẽ khóa:

```text
Verified MIR
      ↓
SSA Construction
      ↓
MemorySSA
      ↓
AliasInfo
      ↓
EffectInfo
      ↓
RangeInfo
      ↓
EscapeInfo
      ↓
LoopInfo
      ↓
TargetInfo
      ↓
OptIR
      ↓
Optimization Pipeline
```

Đặc biệt cần giải quyết một vấn đề rất quan trọng đối với mục tiêu Axiom:

> **Làm sao compiler có thể tận dụng ownership/capability facts để tối ưu mạnh như C/C++ `restrict`/manual optimization, nhưng programmer không phải viết `restrict`, lifetime hay alias annotations?**

Và đồng thời khóa các optimization quan trọng:

- allocation elimination
- scalar replacement
- load/store elimination
- alias analysis
- no-alias inference
- bounds-check elimination
- devirtualization
- generic specialization
- closure elimination
- async state minimization
- loop optimization
- vectorization
- inlining
- LTO
- PGO
- binary-size optimization

Đây là nơi **mục tiêu “Axiom nhanh bằng hoặc hơn C/C++”** bắt đầu được biến thành kiến trúc compiler cụ thể.