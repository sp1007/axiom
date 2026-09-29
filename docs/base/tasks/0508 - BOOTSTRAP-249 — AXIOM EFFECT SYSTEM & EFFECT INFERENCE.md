# BOOTSTRAP-249 — AXIOM EFFECT SYSTEM & EFFECT INFERENCE

**TRẠNG THÁI: FROZEN / COMPLETED**

Effect System của Axiom phải giải quyết một vấn đề rất cụ thể:

> **Compiler cần biết một operation có thể quan sát hoặc ảnh hưởng đến thế giới bên ngoài đến mức nào, nhưng programmer không nên bị bắt viết effect annotation cho mọi hàm.**

Do đó Axiom chọn:

> **Effects are semantic facts, not programmer bureaucracy.**

Compiler **suy luận effect**, kiểm tra effect và sử dụng effect cho optimization. Annotation chỉ xuất hiện khi cần **giới hạn, yêu cầu hoặc công bố contract đặc biệt**.

---

# 1. Effect là gì?

Effect mô tả những tác động semantic mà một expression/function có thể gây ra.

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

có thể được compiler suy ra:

```text
Pure
```

Trong khi:

```axiom
fn write_file(file: File, data: view<u8>) -> Result<usize, Error>
```

có effect:

```text
IO
Write
Foreign/OS-resource
```

---

# 2. Effect không phải ownership

Hai khái niệm này phải tách biệt.

```text
Ownership → ai sở hữu giá trị?
Capability → ai được truy cập vùng nhớ?
Effect → operation có thể làm gì?
```

Ví dụ:

```axiom
fn consume(x: Buffer) { ... }
```

có thể:

```text
Move + Read
```

nhưng Move không tự động có nghĩa là IO.

---

# 3. Effect không phải capability

Ví dụ:

```axiom
fn sum(x: view<i32>) -> i32
```

có:

```text
Read memory
```

nhưng không có:

```text
IO
```

---

# 4. Effect không phải exception

Axiom không dùng effect system để biến mọi lỗi thành exception.

```text
Result → recoverable outcome
Panic  → unrecoverable control effect
```

---

# 5. Effect categories

Axiom v1 định nghĩa semantic effect categories:

```text
PURE
READ
WRITE
ALLOCATE
DEALLOCATE
DROP
PANIC
IO
ATOMIC
SYNCHRONIZE
VOLATILE
BLOCKING
ASYNC
FOREIGN
PROCESS
COMPTIME
GPU
UNSAFE
```

Không phải tất cả đều cùng một tầng.

---

# 6. Effect hierarchy

Compiler nên phân loại effect theo tính chất thay vì tạo một hierarchy duy nhất:

```text
Memory:
    READ
    WRITE
    ALLOCATE
    DEALLOCATE
    DROP

Control:
    PANIC
    ASYNC
    BLOCKING

Concurrency:
    ATOMIC
    SYNCHRONIZE

External:
    IO
    PROCESS
    FOREIGN
    VOLATILE

Execution:
    GPU
    COMPTIME
    UNSAFE
```

---

# 7. PURE

`PURE` nghĩa là expression không tạo observable effect.

Ví dụ:

```axiom
fn square(x: i32) -> i32 {
    x * x
}
```

Compiler có thể:

- inline
- CSE
- constant fold
- eliminate
- reorder
- vectorize

miễn semantic dependencies được giữ.

---

# 8. READ

READ biểu thị đọc state/memory.

Ví dụ:

```axiom
fn get_x(p: view<Point>) -> f32 {
    p.x
}
```

Có:

```text
READ
```

Nhưng READ không nhất thiết là observable effect bên ngoài.

---

# 9. WRITE

WRITE thay đổi state.

```axiom
fn set_x(p: mut_view<Point>, x: f32) {
    p.x = x
}
```

Có:

```text
WRITE
```

---

# 10. READ/WRITE không chỉ là memory

Có thể có:

```text
READ:
    memory
    atomic
    external resource
    process state
    environment

WRITE:
    memory
    file
    socket
    process state
    device
```

Compiler dùng domain cụ thể để reason chính xác hơn.

---

# 11. ALLOCATE

Allocation là effect semantic khi allocation có thể quan sát hoặc thất bại theo contract.

Tuy nhiên:

> **Compiler optimization có thể eliminate allocation.**

Ví dụ:

```axiom
fn f() -> Box<Point> {
    Box(Point { x: 1, y: 2 })
}
```

Nếu `Box` không escape, allocation có thể bị loại.

---

# 12. ALLOCATE không đồng nghĩa heap

Một allocation semantic operation có thể lower thành:

```text
stack
register
arena
pool
heap
caller-provided storage
```

---

# 13. DEALLOCATE

Resource/storage release.

`Drop` và `DEALLOCATE` phải phân biệt.

```text
DROP
→ semantic destruction

DEALLOCATE
→ physical storage release
```

Một Drop có thể không deallocate.

---

# 14. DROP

Drop là observable nếu destructor có effect.

Ví dụ:

```axiom
struct File {
    ...
}
```

Drop có thể release OS resource.

Do đó compiler không được tùy ý loại bỏ Drop chỉ vì giá trị không còn được đọc.

---

# 15. Trivial Drop

Nếu compiler chứng minh Drop không có observable behavior:

```text
trivial drop
```

có thể được erase.

---

# 16. PANIC

Panic là control-flow effect.

Ví dụ:

```axiom
fn divide(a: i32, b: i32) -> i32 {
    a / b
}
```

nếu division-by-zero profile gây panic/trap, operation có potential `PANIC`.

---

# 17. Panic không phải Result

Compiler không được biến:

```text
panic
```

thành:

```text
Result
```

trừ khi một abstraction explicit thực hiện conversion.

---

# 18. IO

IO là external observable effect:

```text
file
socket
console
device
terminal
```

Compiler phải coi IO là semantic barrier phù hợp.

---

# 19. IO ordering

Ví dụ:

```axiom
write("A")
write("B")
```

không được tự ý đảo thành:

```text
write("B")
write("A")
```

---

# 20. Pure computation quanh IO

Compiler vẫn được optimize:

```axiom
let x = expensive_pure_calculation()
write(x)
```

nhưng không được đưa operation qua IO nếu làm thay đổi observable behavior.

---

# 21. PROCESS

Process effects:

```text
spawn
kill
wait
exit
environment mutation
signal
```

được đánh dấu `PROCESS`.

---

# 22. Environment

Environment read:

```axiom
env.get("PATH")
```

có external read effect.

Không được coi là pure mặc dù return type có thể chỉ là `String`.

---

# 23. FOREIGN

Foreign call:

```axiom
extern "C" fn foo(...)
```

mặc định:

```text
FOREIGN
```

và compiler conservative về memory/effects nếu không có contract.

---

# 24. FFI contract

Nếu FFI declaration cung cấp contract:

```text
reads memory X
writes memory Y
pure
noalias
nothrow
```

compiler có thể dùng các facts đó.

---

# 25. Không tin FFI mặc định

Nếu contract không đủ:

```text
FOREIGN
UNKNOWN_READ
UNKNOWN_WRITE
```

Không được giả định pure.

---

# 26. ATOMIC

Atomic operation:

```axiom
atomic_load(x, Acquire)
atomic_store(x, value, Release)
```

có:

```text
ATOMIC
```

và memory-order semantics.

---

# 27. Atomic ≠ Synchronize

Một relaxed atomic có:

```text
ATOMIC
```

nhưng không nhất thiết tạo:

```text
SYNCHRONIZE
```

happens-before.

---

# 28. SYNCHRONIZE

Ví dụ:

```text
Mutex.unlock
Channel.send
Thread.join
Semaphore.release
```

có synchronization semantics.

---

# 29. VOLATILE

Volatile là effect riêng.

```text
VOLATILE
```

Compiler không được treat volatile load/store như ordinary memory access.

---

# 30. Volatile ≠ Atomic

```text
volatile
```

không đảm bảo atomicity.

```text
atomic
```

không có nghĩa là volatile hardware access.

---

# 31. BLOCKING

Blocking biểu thị operation có thể block execution context.

Ví dụ:

```text
blocking file read
mutex lock
thread join
```

Nhưng một async operation chờ completion không nhất thiết là `BLOCKING`.

---

# 32. ASYNC

`async` effect liên quan tới suspension/control-flow.

Một `async fn` tạo Future.

Việc **gọi** async function không nhất thiết thực hiện IO ngay.

---

# 33. Await

`.await` có:

```text
ASYNC
```

và tạo SuspensionPoint.

Compiler phải kiểm tra:

```text
live values
capabilities
guards
Send
storage
```

---

# 34. GPU

GPU operation có execution-domain effect:

```text
GPU
```

Ví dụ:

```axiom
launch(kernel, buffer)
```

có thể:

```text
GPU
ASYNC
```

nếu launch asynchronous.

---

# 35. GPU completion

`GpuEvent.wait()` có synchronization semantics.

Do đó:

```text
GPU + SYNCHRONIZE
```

có thể xuất hiện.

---

# 36. COMPTIME

Comptime execution không phải runtime effect.

Ví dụ:

```axiom
const X = comptime compute()
```

có:

```text
COMPTIME
```

trong compiler execution environment.

---

# 37. Comptime external effects

Nếu comptime đọc filesystem:

```text
COMPTIME
+ external capability
+ READ
```

và input phải tham gia build fingerprint.

---

# 38. UNSAFE

`unsafe` không phải effect theo nghĩa “operation làm thay đổi state”.

Nó là **trust boundary**.

Compiler có thể biểu diễn:

```text
UNSAFE
```

như effect/requirement để tooling theo dõi.

---

# 39. Unsafe không tắt effect system

```axiom
unsafe {
    *ptr = value
}
```

vẫn có:

```text
WRITE
UNSAFE
```

---

# 40. Effect set

Function semantic type có thể chứa effect set:

```text
FnType {
    params
    result
    effects
}
```

---

# 41. Programmer không bắt buộc viết effects

Ví dụ:

```axiom
fn foo(x: i32) -> i32 {
    x * 2
}
```

Compiler tự suy ra:

```text
PURE
```

Không cần:

```text
fn foo(...) -> ... effects(PURE)
```

---

# 42. Effect inference

Pipeline:

```text
Expression
    ↓
Local effects
    ↓
Call graph facts
    ↓
Trait/generic normalization
    ↓
Effect propagation
    ↓
Function effect summary
```

---

# 43. Direct effect

Ví dụ:

```axiom
fn f() {
    atomic_store(...)
}
```

Direct effect:

```text
ATOMIC
```

---

# 44. Transitive effect

```axiom
fn f() {
    g()
}

fn g() {
    write_file(...)
}
```

Compiler suy ra:

```text
f → IO
g → IO
```

---

# 45. Effect propagation

Nếu:

```text
A calls B
```

thì:

```text
Effects(A) ⊇ Effects(B)
```

trừ khi compiler có proof rằng call path không thực thi hoặc abstraction specializes it away.

---

# 46. Generic functions

```axiom
fn map<T, U>(...) { ... }
```

effect có thể phụ thuộc callback:

```text
Effects(map) =
    intrinsic effects
    ∪ Effects(callback)
```

---

# 47. Generic effect polymorphism

Axiom không cần bắt programmer viết:

```text
fn map<E>()
```

Compiler tự suy luận effect theo instantiated callable.

---

# 48. Example

```axiom
fn apply<T>(x: T, f: fn(T) -> T) -> T {
    f(x)
}
```

Nếu:

```text
f = pure_function
```

instance có thể trở thành pure.

Nếu:

```text
f = write_file
```

instance có IO.

---

# 49. Trait methods

Trait callable contract có effect information.

Concrete implementation không được silently violate stronger declared contract.

---

# 50. Effect subtyping

Ví dụ một API yêu cầu:

```text
PURE
```

thì function có:

```text
IO
```

không thỏa.

---

# 51. Pure boundary

Có thể có API:

```axiom
comptime fn evaluate(...)
```

hoặc compiler intrinsic yêu cầu pure callable.

Compiler kiểm tra effect inferred.

---

# 52. `@pure`

Không cần cho ordinary functions.

Có thể có:

```axiom
@pure
fn ...
```

như **asserted/required contract**.

Nhưng compiler phải verify.

Nếu body có IO:

→ compile error.

---

# 53. Không cho programmer fake purity

Không cho:

```axiom
@pure
fn evil() {
    write_file(...)
}
```

compile thành pure chỉ vì annotation.

---

# 54. Trusted intrinsic

Compiler intrinsic/system primitive có thể có externally specified effect contract.

Nhưng intrinsic phải:

- có semantic definition;
- target constraints;
- fallback;
- verification contract.

---

# 55. Effect of memory reads

Ordinary local variable read:

```text
READ
```

về compiler analysis.

Nhưng compiler có thể classify nó là **non-observable internal effect**.

Điều này rất quan trọng để optimization không bị bó tay.

---

# 56. Observable vs internal effects

Đề xuất hai tầng:

```text
Semantic Effects
    ↓
Optimization Effect Facts
```

Ví dụ:

```text
READ(local SSA value)
```

không nên trở thành barrier.

---

# 57. Memory effect lattice

Optimizer dùng:

```text
NO_MEMORY
READ_ONLY
WRITE
READ_WRITE
UNKNOWN_MEMORY
```

theo region.

---

# 58. Region-sensitive effects

Ví dụ:

```axiom
fn sum(a: view<i32>, b: view<i32>) -> i32
```

compiler biết read regions.

Nếu:

```text
a region ≠ b region
```

có thể load/optimize độc lập.

---

# 59. Capability → Effect

`view<T>` tạo:

```text
READ(region)
```

`mut_view<T>` cho phép:

```text
READ(region)
WRITE(region)
```

nhưng capability verifier quyết định legality.

---

# 60. Effect ≠ permission

`mut_view` cho phép WRITE.

Nhưng expression:

```axiom
x = 1
```

mới thực sự tạo WRITE effect.

---

# 61. Effect region

Internal effect representation:

```text
Effect {
    kind
    region
    storage_domain
    execution_domain
    ordering
    observability
}
```

---

# 62. Effect ordering

Compiler cần biết effect nào phải giữ thứ tự.

Ví dụ:

```text
Write(A)
Write(B)
```

nếu A/B disjoint và không observable externally, có thể reorder.

Nếu là:

```text
FileWrite
FileWrite
```

thứ tự có thể observable.

---

# 63. Effect commutativity

Compiler có thể ghi nhận:

```text
commutative
non_commutative
unknown
```

để tối ưu.

---

# 64. Effect dependency

Hai operations có dependency nếu:

```text
Write(A) → Read(A)
Write(A) → Write(A)
Atomic → dependent atomic
IO → IO
Sync → dependent operation
```

---

# 65. Effect elimination

Compiler có thể eliminate:

```text
pure computation
dead local write
dead allocation
```

nếu không observable.

---

# 66. Effect cannot be erased blindly

Ví dụ:

```axiom
let x = file.write(data)
```

dù `x` không được dùng:

`file.write` vẫn phải thực thi.

---

# 67. Drop effects

```axiom
{
    let f = open(...)
}
```

`f` không được dùng nhưng Drop vẫn có thể close/release resource.

---

# 68. External effect roots

Effect analysis phải đánh dấu roots:

```text
IO
volatile
atomic
sync
FFI
process
observable Drop
panic
```

---

# 69. Pure function memoization

Compiler có thể CSE/pure-call elimination khi:

```text
no external effects
```

và arguments/results semantics phù hợp.

---

# 70. Environment dependency

Không coi:

```axiom
env.get(...)
```

là pure chỉ vì function không mutate memory argument.

---

# 71. Time

```axiom
clock.now()
```

là external read:

```text
IO / ENVIRONMENT / EXTERNAL
```

Không pure.

---

# 72. Random

Non-deterministic RNG:

```text
EXTERNAL
```

hoặc specialized effect.

CSPRNG có thêm security semantics.

---

# 73. Scientific deterministic RNG

Seeded deterministic RNG có thể pure theo state-value model:

```axiom
fn next(rng: Rng) -> (Rng, u64)
```

Nếu không đọc external entropy.

---

# 74. Global mutable state

Access global mutable state tạo:

```text
READ/WRITE
```

và synchronization requirements nếu shared.

---

# 75. TLS

TLS read/write là external execution-state effect:

```text
READ/WRITE
TLS
```

nhưng vẫn không necessarily IO.

---

# 76. Static constants

Immutable compile-time constant:

```text
PURE
```

---

# 77. Static mutable

Static mutable state phải explicit/system and effectful.

Không được giả định pure.

---

# 78. Function calls

Compiler distinguishes:

```text
direct known call
generic call
dyn call
foreign call
indirect function pointer
```

Effect inference khác nhau.

---

# 79. Direct known call

Có thể lấy exact effect summary.

---

# 80. Generic call

Instantiate effect summary after generic substitution.

---

# 81. `dyn Trait` call

Nếu dynamic implementation unknown:

compiler dùng trait-object effect contract.

Nếu contract không đủ:

```text
UNKNOWN
```

---

# 82. Function pointer

Function pointer effect type phải là part of callable signature.

Ví dụ conceptually:

```text
fn(i32) -> i32 ! PURE
```

Nhưng syntax effect annotation không nhất thiết expose trong Core v1.

---

# 83. Why effect belongs to callable type

Nếu không:

```text
fn pure_fn(...)
fn io_fn(...)
```

cùng type thì compiler không thể enforce:

```text
requires_pure_callback
```

một cách sound.

---

# 84. Effect polymorphism

Compiler có thể internally represent:

```text
E₁
E₂
```

cho generic callable.

Programmer không cần nhìn thấy effect variable trong đa số trường hợp.

---

# 85. Effect constraints

Ví dụ một compiler intrinsic yêu cầu:

```text
Effects(F) ⊆ {PURE, READ}
```

solver kiểm tra.

---

# 86. Effect inference cycles

Ví dụ:

```text
A → B
B → A
```

Effect solver phải compute fixed point.

---

# 87. Recursive function

```axiom
fn recurse(x: i32) {
    recurse(x - 1)
}
```

Nếu không có direct effect khác:

```text
PURE
```

có thể là kết quả.

---

# 88. Recursive effect fixed point

Khởi tạo:

```text
Effects(f) = DirectEffects(f)
```

sau đó propagate đến fixed point.

---

# 89. Effect lattice

Compiler có thể dùng join:

```text
PURE
 < READ
 < READ_WRITE
 < UNKNOWN
```

cho memory effects.

External effects dùng orthogonal bitsets thay vì ép vào một linear lattice.

---

# 90. Orthogonal effect set

Một function có thể đồng thời:

```text
READ
ATOMIC
IO
PANIC
```

Không nên biến thành một giá trị duy nhất như:

```text
"IO > Atomic > Read"
```

vì mất thông tin.

---

# 91. Effect bitset

Internal representation phù hợp:

```text
EffectMask
```

+

```text
RegionEffect[]
```

+

```text
ExternalEffect[]
```

---

# 92. Effect summary

```text
EffectSummary {
    mask
    memory_reads
    memory_writes
    allocations
    synchronization
    external_resources
    panic_behavior
    async_behavior
    execution_domain
}
```

---

# 93. Function effect cache

Effect summary là compiler query:

```text
EffectOf(FunctionId, GenericInstanceId, TargetId)
```

---

# 94. Incremental invalidation

Nếu function `g` thay đổi effect:

```text
g → IO
```

compiler invalidates callers' effect summaries.

Không cần recompile unrelated functions.

---

# 95. Trait solver integration

Trait implementation có thể có effect facts.

Ví dụ generic:

```text
T: Serialize
```

`serialize(t)` effect phụ thuộc selected implementation.

---

# 96. Effect + specialization

Sau monomorphization:

```text
generic_call
```

có thể specialize thành pure function.

Optimizer có thể tận dụng.

---

# 97. Effect + inlining

Inlining có thể expose effects.

Ví dụ:

```text
foo() → call pure bar()
```

Sau inline, compiler có thể eliminate toàn bộ computation.

---

# 98. Effect + DCE

Nếu:

```text
x = pure()
```

và `x` không dùng:

→ eliminate.

Nếu:

```text
x = IO()
```

→ không eliminate.

---

# 99. Effect + CSE

Hai pure calls cùng arguments:

```text
a = f(x)
b = f(x)
```

có thể CSE nếu `f` pure và không phụ thuộc hidden external state.

---

# 100. Effect + LICM

Loop-invariant pure/read-only operation có thể hoist.

Nhưng:

```text
IO
volatile
atomic
sync
```

phải tuân thủ dependency.

---

# 101. Effect + vectorization

Compiler có thể vectorize:

```axiom
for x in array {
    y = x * 2
}
```

nếu effect/alias analysis chứng minh không có dependency phá semantics.

---

# 102. Effect + parallelization

Pure computation dễ parallelize.

Memory writes cần region/disjointness.

External effects thường cấm automatic parallel reorder.

---

# 103. Effect + concurrency

Effect system không tự chứng minh race freedom.

Hai hệ thống:

```text
Effect analysis
+
Capability/concurrency verifier
```

phối hợp.

---

# 104. Atomic ordering

Effect summary phải giữ:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

không chỉ bit `ATOMIC`.

---

# 105. Synchronization dependency

Compiler phải biết:

```text
unlock → lock
send → receive
spawn → start
join → completion
```

để không reorder xuyên qua synchronization semantics.

---

# 106. Effect + async

Async lowering tạo:

```text
ASYNC
```

và suspension points.

Effect summary của Future phải phản ánh operations có thể xảy ra khi polled, không phải chỉ khi Future được tạo.

---

# 107. Important distinction

```axiom
let f = async_operation()
```

không nhất thiết:

```text
IO now
```

Mà:

```text
construct Future
```

Khi:

```axiom
f.await
```

operation được driven.

---

# 108. Effect + cancellation

Cancellation không phải panic.

Future drop có thể trigger Drop effects nhưng không mặc định là external cancellation.

---

# 109. Effect + Drop

Future chứa resource:

```text
Drop
```

có thể xảy ra khi cancellation/drop.

---

# 110. Effect + GPU

Kernel:

```axiom
@kernel
fn add(...) { ... }
```

effect analysis phải chạy riêng theo GPU legality.

---

# 111. GPU kernel effects

Kernel có thể:

```text
READ Device
WRITE Device
ATOMIC
SYNCHRONIZE
```

nhưng không:

```text
PROCESS
FILE IO
HOST syscall
```

---

# 112. GPU launch

Host:

```text
launch(kernel)
```

có:

```text
GPU
ASYNC
```

và resource/capability effects.

---

# 113. Effect + comptime

Comptime effect summary được đánh giá trong compiler environment.

Không được nhầm:

```text
comptime IO
```

với runtime IO.

---

# 114. Build identity

Comptime external effects ảnh hưởng:

```text
SemanticFingerprint
BuildFingerprint
```

nếu input thay đổi.

---

# 115. Effect + FFI

FFI không contract:

```text
UNKNOWN_MEMORY
FOREIGN
```

FFI contract đầy đủ:

```text
precise effects
```

cho optimizer.

---

# 116. Effect + volatile

Foreign hardware/MMIO:

```text
VOLATILE
```

không được CSE hoặc eliminate như normal loads/stores.

---

# 117. Effect + process

```axiom
child.wait()
```

có synchronization effect.

`kill()` là external process effect.

Drop handle không mặc định là kill.

---

# 118. Effect + filesystem

`File.read`:

```text
IO
READ_EXTERNAL
```

`File.write`:

```text
IO
WRITE_EXTERNAL
```

---

# 119. Effect + networking

Socket:

```text
send → IO + WRITE_EXTERNAL
recv → IO + READ_EXTERNAL
```

DNS:

```text
IO + NETWORK
```

---

# 120. Effect + database

Database transaction operations:

```text
READ_EXTERNAL
WRITE_EXTERNAL
IO
```

Commit có semantic ordering.

---

# 121. Effect + serialization

Serialization vào caller-owned buffer:

```text
READ(input)
WRITE(output)
```

nhưng có thể hoàn toàn memory-local.

Không phải IO.

---

# 122. Effect + cryptography

Pure hash:

```text
READ
PURE computation
```

CSPRNG:

```text
EXTERNAL entropy
```

Secure memory zeroization:

```text
WRITE
SECURITY effect
```

---

# 123. Effect + constant time

`@constant_time` không phải effect.

Nó là **execution property/constraint**.

Compiler phải kiểm tra separately.

---

# 124. Effect + unsafe

`unsafe` là trust boundary.

Không dùng effect system để thay thế safety verifier.

---

# 125. Effect + security taint

Secret flow:

```text
Security/Taint analysis
```

khác:

```text
Effect analysis
```

Nhưng hai hệ thống có thể exchange facts.

---

# 126. Effect annotations

Core v1 chỉ nên có annotation cho **contractual restrictions**, ví dụ conceptually:

```axiom
@pure
fn ...
```

hoặc:

```text
@no_panic
@blocking
```

nhưng chỉ những annotation thực sự cần public API contract mới nên freeze.

---

# 127. Inference-first

Default:

```text
No annotation
→ compiler infers
```

---

# 128. Public API effect documentation

Compiler/IDE có thể hiển thị:

```text
fn save(...) -> Result<...>

Effects:
    IO
    WRITE
    PANIC: no
```

Không cần programmer viết chúng.

---

# 129. AI interface

```text
ax explain effects foo
```

trả structured result:

```text
Direct:
    WRITE(user)

Transitive:
    IO via save()

May panic:
    no

May block:
    yes

Synchronization:
    mutex.lock/unlock
```

---

# 130. Effect diagnostics

Ví dụ API yêu cầu pure:

```text
function argument must be PURE
actual function has:
    IO
```

---

# 131. Effect mismatch

Không nói:

```text
"invalid function"
```

mà:

```text
required effects ⊇/⊆ actual effects
```

theo constraint cụ thể.

---

# 132. Effect contracts must be sound

Nếu annotation nói:

```text
@pure
```

compiler phải prove.

---

# 133. Trusted external declarations

Một số system intrinsic/ABI functions không thể prove từ source.

Chúng được phép có **trusted external semantic contracts**.

Toolchain phải mark chúng là trusted.

---

# 134. Effect soundness boundary

```text
Source body
→ inferred effects
→ verified

Foreign/intrinsic
→ explicit contract
→ trusted boundary
```

---

# 135. Effect unknown

Nếu compiler không biết:

```text
UNKNOWN_EFFECT
```

Không được giả định pure.

---

# 136. Unknown is conservative

```text
UNKNOWN ≠ PURE
```

đây là invariant bắt buộc.

---

# 137. Effect refinement

Sau inlining/devirtualization:

```text
UNKNOWN
```

có thể trở thành:

```text
PURE
```

nếu compiler prove được.

---

# 138. Optimization does not define semantics

Optimizer có thể làm effect summary nhỏ hơn về physical execution.

Nhưng semantic behavior vẫn phải tương đương.

---

# 139. Example: allocation elimination

Source:

```axiom
fn f() -> i32 {
    let x = Box(42)
    *use_internal(x)
}
```

Nếu Box không escape:

```text
semantic allocation
```

có thể trở thành:

```text
no physical allocation
```

Effect system không được coi đó là semantic contradiction.

---

# 140. Effect vs physical instruction

Một semantic:

```text
ALLOCATE
```

có thể không còn `malloc` machine instruction sau optimization.

---

# 141. Effect summary after optimization

Nên phân biệt:

```text
SemanticEffectSummary
```

và:

```text
OptimizationEffectFacts
```

để không làm semantics phụ thuộc optimization level.

---

# 142. Required architecture

```text
Typed HIR
   ↓
Effect Inference
   ↓
Semantic Effect Summary
   ↓
Verified MIR
   ↓
Optimization Effect Facts
   ↓
OptIR
```

---

# 143. Compiler databases

Thêm:

```text
EffectDB
EffectSummary
EffectConstraint
EffectQuery
```

vào `CompilerDB`.

---

# 144. Query API

```text
EffectOf(FunctionId)
EffectOf(GenericInstanceId)
EffectOf(ExpressionId)
EffectOf(CallSiteId)
```

---

# 145. Dependency graph

```text
Expression
   ↓
Function
   ↓
Generic Instance
   ↓
Trait Implementation
   ↓
Effect Summary
```

---

# 146. Effect caching

Cache key:

```text
FunctionId
GenericInstance
Target
FeatureSet
ABI
```

Comptime-dependent effect cũng phải include comptime dependencies.

---

# 147. Target-specific effects

Một function có thể khác effect theo target.

Ví dụ implementation:

```text
Windows → IOCP
Linux   → io_uring
```

Semantic external effect vẫn:

```text
IO
```

physical backend khác.

---

# 148. Target-specific blocking

Một API có thể:

```text
blocking on one backend
nonblocking on another
```

Nếu đây là semantic API contract khác nhau, effect summary phải target-specific.

---

# 149. Hosted vs freestanding

Freestanding program không có OS IO effect implementation.

Compiler phải reject unavailable effects/API rather than silently link runtime.

---

# 150. Runtime component elimination

Effect graph hỗ trợ runtime trimming:

```text
No IO
→ no IO runtime

No async
→ no async executor

No reflection
→ no reflection runtime
```

---

# 151. Effect-guided linking

Linker/build system có thể dùng compiler facts để tránh kéo unnecessary runtime components.

Nhưng final reachability vẫn dựa trên actual symbol/resource dependencies.

---

# 152. Effect-guided binary size

`--profile size` có thể tận dụng:

```text
PURE
dead effects
runtime dependencies
```

để aggressive eliminate code.

---

# 153. Effect + linker

External symbols must remain roots when effect/resource semantics require them.

---

# 154. Effect + LTO

LTO có thể propagate effects across package boundaries khi metadata/ABI contract cho phép.

---

# 155. Stable ABI

Stable ABI phải encode effect contract nếu effect là part of public semantic callable contract.

Ví dụ một ABI boundary không thể thay:

```text
no-panic
```

thành:

```text
may-panic
```

nếu caller relies on contract.

---

# 156. Package metadata

`.axmeta` nên chứa:

```text
FunctionEffectSummary
TraitEffectContract
FFIEffectContract
```

để compiler không cần source.

---

# 157. Binary compatibility

Effect contract changes có thể là semantic API change.

Ví dụ:

```text
pure → IO
```

là thay đổi đáng kể với callers yêu cầu purity.

---

# 158. Effect inference and ABI

Internal effect facts có thể phong phú hơn stable ABI.

Không expose implementation-specific region IDs trong ABI.

---

# 159. Effect normalization

Trait/generic effect expressions phải normalize trước khi compare.

---

# 160. Effect solver

Conceptual:

```text
EffectGoal
    ↓
Known direct effects
    ↓
Call graph
    ↓
Trait resolution
    ↓
Generic substitution
    ↓
Constraint propagation
    ↓
Fixed point
```

---

# 161. Cycles

Recursive call cycles phải converge.

Nếu effect inference không resolve được trong budget:

```text
compile error
```

hoặc conservative `UNKNOWN`, tùy semantic context.

Nếu function contract requires `PURE`:

`UNKNOWN` không satisfy.

---

# 162. No unsound fallback

Không được:

```text
solver timeout
→ assume PURE
```

---

# 163. Effect inference and dead branches

Trong Complete Semantic Mode, source branch vẫn type/effect check.

`@cfg` mới loại branch trước semantic compilation.

---

# 164. Constant branch

Nếu condition compile-time known:

optimizer có thể eliminate branch sau semantic validation.

---

# 165. Effect of unreachable runtime branch

Nếu branch không thể runtime-reach theo proven semantics, optimizer có thể loại.

Nhưng effect inference trước optimization vẫn phải sound.

---

# 166. Effect and `match`

Pattern facts giúp compiler biết arm nào reachable.

Effects của unreachable arm không trở thành runtime effect.

Nhưng source semantic validity vẫn được kiểm tra.

---

# 167. Effect and closure

Closure effect summary:

```text
capture effects
body effects
called functions
```

Capture itself không necessarily effectful.

---

# 168. Closure invocation

Capturing closure carries callable effect contract.

---

# 169. Effect and iterator

Iterator `next()` effect được suy ra.

`map` inherits callback effects.

Lazy adapter không thực thi callback khi constructed.

---

# 170. Effect and lazy evaluation

Ví dụ:

```axiom
let iter = xs.map(f)
```

không nghĩa `f` đã chạy.

Effect `f` xảy ra khi iterator is consumed.

---

# 171. Effect and collection allocation

`collect()` có allocation effect nếu final storage is observable/required, nhưng allocation có thể be optimized.

---

# 172. Effect and errors

`Result` không tự động tạo effect.

```text
Result<T,E>
```

là ordinary value.

---

# 173. Fallible allocation

Allocation API có thể:

```text
Result<Box<T>, AllocError>
```

Error là value; allocation operation có `ALLOCATE`.

---

# 174. Panic profile

Effect summary có thể chứa:

```text
MayPanic
```

Panic strategy:

```text
abort
unwind
custom
```

là target/profile configuration.

---

# 175. No-panic contract

Có thể compiler expose:

```text
@no_panic
```

sau này nếu cần.

Contract phải recursively prove all reachable operations.

---

# 176. No-blocking contract

Tương tự:

```text
@nonblocking
```

có thể hữu ích cho async/UI/GPU contexts.

Compiler verifies transitive effects.

---

# 177. GPU legality as effect constraint

Kernel context có implicit constraints:

```text
forbidden:
    IO
    PROCESS
    BLOCKING
    arbitrary FOREIGN
```

---

# 178. Async context

Một async function không tự động cấm blocking.

Nhưng API có thể yêu cầu:

```text
NonBlocking
```

và compiler reject blocking calls.

---

# 179. UI context

UI callback framework có thể yêu cầu:

```text
UI-safe
nonblocking
```

dựa trên effect constraints.

---

# 180. Interrupt context

System layer có thể yêu cầu:

```text
no allocation
no blocking
no IO
restricted synchronization
```

Effect solver có thể verify.

---

# 181. Effect policies

Thay vì hardcode nhiều annotations, library/system API có thể define policy:

```text
EffectConstraint {
    allowed
    forbidden
    required
}
```

---

# 182. Example

Conceptually:

```text
@context(no_blocking, no_allocation)
fn interrupt_handler(...)
```

Compiler verifies.

Syntax này có thể thuộc system layer, không nhất thiết Core.

---

# 183. Effect policy inheritance

Nested call phải satisfy caller context.

---

# 184. Effect policy and generic code

Generic function không cần biết concrete effect trước.

Compiler kiểm tra mỗi instantiation/context.

---

# 185. Effect specialization

Generic:

```text
fn process<F>(f: F)
```

có thể specialize pure/non-pure variants.

---

# 186. Effect devirtualization

Nếu dyn call được proven concrete:

```text
unknown effect
```

→ exact effect.

---

# 187. Effect + dynamic loading

Dynamic plugin effect cannot be fully known unless metadata contract exists.

Plugin ABI must publish required effect capabilities.

---

# 188. Effect + reflection

Runtime reflection may imply:

```text
metadata read
```

but compile-time reflection is distinct.

---

# 189. Effect + metadata stripping

If no runtime reflection:

metadata may be stripped.

Effect system can identify reflection runtime roots.

---

# 190. Effect + serialization metadata

Compile-time generated serializer may be pure/memory-only.

Runtime schema discovery may have metadata/read effects.

---

# 191. Effect + database transactions

Transaction commit has external observable state.

Optimizer cannot reorder commit around unrelated external operations if behavior changes.

---

# 192. Effect + network retries

Retry logic is library semantics, not compiler effect magic.

Compiler sees calls/effects; library defines retry behavior.

---

# 193. Effect + locks

Lock acquisition:

```text
SYNCHRONIZE
BLOCKING
```

if blocking lock.

Try-lock may:

```text
SYNCHRONIZE
```

without `BLOCKING`.

---

# 194. Effect + channel

Send/receive:

```text
SYNCHRONIZE
```

and potentially:

```text
BLOCKING
```

depending on API.

Async channel await:

```text
SYNCHRONIZE
ASYNC
```

rather than ordinary blocking.

---

# 195. Effect + atomics

Atomic operation includes memory order in effect metadata:

```text
AtomicEffect {
    kind
    ordering
    scope
}
```

---

# 196. Effect + volatile

```text
VolatileEffect {
    read/write
    address_space
}
```

---

# 197. Effect + external resources

File/socket/process/device all use shared compiler resource machinery but remain distinct effect domains.

---

# 198. Effect + ownership

Drop of File:

```text
DROP
IO/resource-release
```

depending on semantic contract.

Ownership verifier ensures exactly-once cleanup.

Effect system ensures cleanup cannot be optimized away incorrectly.

---

# 199. Effect + capability

A capability gives potential access.

Effect represents actual operation.

This distinction is critical:

```text
mut_view<T>
```

does not mean WRITE occurred.

Only:

```axiom
x = value
```

creates WRITE.

---

# 200. Final architecture

```text
                    Typed HIR
                        │
                        ▼
                 Effect Inference
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
   Local Effects    Call Effects    Trait Effects
        │               │                │
        └───────────────┼────────────────┘
                        ▼
                 Effect Solver
                        │
                        ▼
               Semantic Effect DB
                        │
                        ▼
                  Verified MIR
                        │
        ┌───────────────┼─────────────────┐
        ▼               ▼                 ▼
   Ownership       Capability         Effect Facts
        │               │                 │
        └───────────────┼─────────────────┘
                        ▼
                       OptIR
                        │
              ┌─────────┼─────────┐
              ▼         ▼         ▼
            CSE       LICM      Vectorize
              │         │         │
              └─────────┼─────────┘
                        ▼
                    ABI / LIR
```

---

# 201. FROZEN INVARIANTS

```text
AEFFECT-20
Effects are semantic facts.

AEFFECT-21
Ordinary functions use effect inference by default.

AEFFECT-22
Programmers are not required to annotate ordinary effects.

AEFFECT-23
Effect inference is deterministic.

AEFFECT-24
Effect inference is separate from ownership verification.

AEFFECT-25
Effect inference is separate from capability verification.

AEFFECT-26
Effect inference is separate from security/taint analysis.

AEFFECT-27
PURE means no observable semantic effect.

AEFFECT-28
READ and WRITE are distinct effects.

AEFFECT-29
ALLOCATE and DEALLOCATE are distinct semantic concepts.

AEFFECT-30
DROP is distinct from physical deallocation.

AEFFECT-31
PANIC is a control-flow effect.

AEFFECT-32
Result-based recoverable failure is not itself an effect.

AEFFECT-33
IO is externally observable.

AEFFECT-34
PROCESS effects are externally observable.

AEFFECT-35
FOREIGN calls are conservative unless an explicit contract exists.

AEFFECT-36
Unknown foreign effects are never assumed pure.

AEFFECT-37
ATOMIC is distinct from SYNCHRONIZE.

AEFFECT-38
VOLATILE is distinct from ATOMIC.

AEFFECT-39
BLOCKING is distinct from ASYNC suspension.

AEFFECT-40
GPU execution effects are distinct from ordinary CPU effects.

AEFFECT-41
COMPTIME effects execute in the compiler environment.

AEFFECT-42
Comptime external inputs participate in build identity.

AEFFECT-43
UNSAFE does not disable effect analysis.

AEFFECT-44
Unsafe operations remain subject to effect tracking.

AEFFECT-45
Function callable types carry sufficient effect information for effect-constrained APIs.

AEFFECT-46
Generic effect behavior is inferred after instantiation.

AEFFECT-47
Trait implementation effects are included in effect resolution.

AEFFECT-48
Dynamic calls use their declared effect contract or conservative unknown effects.

AEFFECT-49
Effect inference propagates transitively through reachable calls.

AEFFECT-50
Recursive effect inference reaches a deterministic fixed point.

AEFFECT-51
Effect solver failure never defaults to PURE.

AEFFECT-52
UNKNOWN effects do not satisfy PURE requirements.

AEFFECT-53
Effects are represented as orthogonal facts rather than a single total ordering.

AEFFECT-54
Memory effects may be region-sensitive.

AEFFECT-55
Capability regions can refine memory effect analysis.

AEFFECT-56
READ does not imply external observability.

AEFFECT-57
Internal memory effects must not unnecessarily prevent optimization.

AEFFECT-58
External observable effects must not be eliminated.

AEFFECT-59
Observable IO ordering must be preserved.

AEFFECT-60
Synchronization ordering must be preserved.

AEFFECT-61
Atomic ordering semantics must be preserved.

AEFFECT-62
Volatile semantics must be preserved.

AEFFECT-63
Observable Drop semantics must be preserved.

AEFFECT-64
Effect summaries are independent of physical instruction order.

AEFFECT-65
Semantic effects are distinct from optimized physical effects.

AEFFECT-66
Allocation elimination does not invalidate semantic effect correctness.

AEFFECT-67
Compiler optimization may refine effect facts but cannot alter observable semantics.

AEFFECT-68
Pure expressions may be reordered when semantic dependencies permit.

AEFFECT-69
Pure expressions may be eliminated when their results are unused.

AEFFECT-70
Effectful expressions may not be eliminated merely because their return value is unused.

AEFFECT-71
Effectful expressions may not be reordered across conflicting observable effects.

AEFFECT-72
Effect analysis participates in CSE legality.

AEFFECT-73
Effect analysis participates in LICM legality.

AEFFECT-74
Effect analysis participates in DCE legality.

AEFFECT-75
Effect analysis participates in vectorization legality.

AEFFECT-76
Effect analysis participates in parallelization legality.

AEFFECT-77
Effect analysis participates in inlining and specialization decisions.

AEFFECT-78
Devirtualization may refine previously unknown effect information.

AEFFECT-79
LTO may propagate effect information across package boundaries when contracts permit.

AEFFECT-80
Stable ABI contracts must preserve required effect semantics.

AEFFECT-81
Effect metadata may be stored in .axmeta.

AEFFECT-82
Effect summaries are incrementally cached.

AEFFECT-83
Effect dependencies participate in incremental invalidation.

AEFFECT-84
Effect inference may execute in parallel.

AEFFECT-85
Parallel effect inference produces deterministic results.

AEFFECT-86
Effect diagnostics expose causal call chains.

AEFFECT-87
Effect diagnostics distinguish direct from transitive effects.

AEFFECT-88
Effect diagnostics can identify the operation introducing a forbidden effect.

AEFFECT-89
AI tooling may query effect facts but cannot override effect verification.

AEFFECT-90
GPU contexts enforce GPU-specific effect constraints.

AEFFECT-91
Async contexts preserve suspension-related effect semantics.

AEFFECT-92
Blocking and asynchronous waiting are not interchangeable effects.

AEFFECT-93
Comptime effects are not runtime effects.

AEFFECT-94
Target-specific implementations may have different physical effects while preserving the same semantic contract.

AEFFECT-95
Freestanding targets reject unavailable external effects rather than silently introducing runtime dependencies.

AEFFECT-96
Effect information can guide runtime-component elimination.

AEFFECT-97
Effect information can guide binary-size optimization.

AEFFECT-98
Effect inference cannot bypass ownership or capability verification.

AEFFECT-99
Effect analysis must preserve the Semantic Oracle behavior.

AEFFECT-100
Optimized execution must be observationally equivalent to the effect semantics established by Verified MIR.
```

---

# Kết quả kiến trúc sau BOOTSTRAP-249

Axiom hiện đã có một chuỗi rất quan trọng:

```text
Type
 ↓
Expression
 ↓
Place
 ↓
Pattern
 ↓
Ownership
 ↓
Capability
 ↓
Effect
 ↓
Verified MIR
 ↓
Optimization
```

Điều này giải quyết một vấn đề cốt lõi của mục tiêu **“compiler phức tạp nhưng programmer đơn giản”**:

Programmer viết:

```axiom
fn process(data: Buffer) -> Result<usize, Error> {
    let x = transform(data)
    save(x)?
}
```

không cần tự khai báo:

```text
ownership
lifetime
borrow
alias
effect
allocation
drop
thread safety
```

Compiler tự xây dựng toàn bộ semantic graph phía sau.

---

## Task tiếp theo: **BOOTSTRAP-250 — AXIOM CONSTANT EVALUATION, COMPTIME EXECUTION & BUILD-TIME SEMANTICS**

Phần này sẽ **không thiết kế lại comptime baseline đã frozen**, mà sẽ đi xuống mức compiler-executable cụ thể:

```text
const
comptime fn
comptime {}
Type-level computation
const generics
compile-time branching
compile-time generated declarations
reflection
comptime memory
comptime ownership/drop
comptime capabilities
comptime sandbox
comptime caching
build fingerprints
determinism
cross-target comptime
```

và đặc biệt sẽ chốt câu hỏi rất quan trọng cho Axiom:

> **Axiom có thể dùng comptime mạnh đến đâu để thay thế macro/procedural-macro/type-level machinery mà vẫn giữ ngôn ngữ đơn giản và compiler implementation khả thi?**