# BOOTSTRAP-233 — AXIOM FORMAL SEMANTIC KERNEL & OPERATIONAL SEMANTICS

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là một mốc rất quan trọng: từ đây Axiom không chỉ có “thiết kế ngôn ngữ”, mà bắt đầu có **một định nghĩa toán học/operational đủ chính xác để compiler, interpreter, optimizer và test suite cùng dựa vào**.

Mục tiêu:

> **Nếu hai implementation Axiom khác nhau cùng tuân thủ Semantic Kernel, chúng phải quan sát được cùng một hành vi.**

Compiler được phép tối ưu tùy ý **sau khi chứng minh semantic preservation**.

---

# 1. Semantic Kernel là gì?

Axiom chia thành:

```text
Surface Syntax
      ↓
AST
      ↓
HIR
      ↓
MIR
      ↓
┌─────────────────────────────┐
│ AXIOM FORMAL SEMANTIC KERNEL│
└─────────────────────────────┘
      ↓
Verified MIR
      ↓
OptIR
      ↓
Machine Code
```

Semantic Kernel không mô tả:

- register allocation
- instruction scheduling
- LLVM
- x86 instruction
- ARM instruction
- vtable layout cụ thể
- stack frame cụ thể
- malloc implementation

Nó chỉ mô tả **chương trình Axiom có nghĩa gì**.

---

# 2. Ba tầng semantics

Axiom sử dụng ba tầng:

```text
Level 0 — Source Semantics
Level 1 — MIR Semantics
Level 2 — Machine Observable Semantics
```

## Source

Con người viết:

```axiom
let x = 10
let y = x + 20
```

## MIR

Compiler canonicalize:

```text
x = 10
y = Add(x, 20)
return y
```

## Machine

Có thể thành:

```text
mov eax, 30
ret
```

Ba tầng phải có quan hệ:

```text
Source behavior
    ≡
MIR behavior
    ≡
Machine observable behavior
```

---

# 3. Semantic state

Định nghĩa abstract machine state:

```text
State =
{
    Environment
    Memory
    Ownership
    Capabilities
    Execution
    Effects
    Control
    ExternalState
}
```

Có thể biểu diễn:

```text
Σ = ⟨ρ, μ, Ω, Κ, χ, ε, κ, ξ⟩
```

Trong đó:

```text
ρ = Environment
μ = Memory
Ω = Ownership state
Κ = Capability state
χ = Execution context
ε = Effect state
κ = Control state
ξ = External state
```

---

# 4. Environment

Environment ánh xạ identifier → semantic entity:

```text
ρ : Name → Binding
```

Ví dụ:

```axiom
let x = 42
```

thì:

```text
ρ[x] = LocalBinding(LocalId, Type=i32)
```

Environment không nhất thiết đại diện cho runtime memory.

Compiler có thể eliminate local hoàn toàn.

---

# 5. Memory

Formal memory không đồng nhất với physical RAM.

```text
μ : Location → Byte/Value
```

nhưng location có semantic identity:

```text
Location =
    StackRegion
    HeapRegion
    StaticRegion
    TLSRegion
    DeviceRegion
    ExternalRegion
```

Đây là **abstract memory**, không phải OS address space.

---

# 6. Storage identity

Mỗi observable storage entity có:

```text
StorageId
```

Compiler có thể thay đổi:

```text
StorageId → register
StorageId → stack
StorageId → heap
```

nếu không thay đổi observable semantics.

---

# 7. Place

Axiom formalize `Place`:

```text
Place =
    Local(LocalId)
    | Field(Place, FieldId)
    | Index(Place, Index)
    | Deref(RawPointer)       // unsafe
```

Ví dụ:

```axiom
point.x
```

canonical:

```text
Field(Local(point), x)
```

---

# 8. Value

Value là semantic content.

```text
Value =
    Primitive
    | Struct
    | Enum
    | Array
    | Function
    | Closure
    | Capability
    | Resource
    | DynamicTrait
    | ...
```

Value không đồng nghĩa với một block bytes.

---

# 9. Representation independence

Hai representation:

```text
u64 = 42
```

có thể tồn tại dưới:

```text
register
stack slot
memory
constant pool
```

mà semantic value vẫn là:

```text
42
```

Do đó:

> **Representation is not semantics unless explicitly exposed.**

---

# 10. Ownership state

Formal ownership state:

```text
Ownership =
    Uninit
    Owned
    Moved
    PartiallyMoved(Set<Field>)
    Dropped
```

Đây là semantic state của verifier.

---

# 11. Initialization

Một Place chỉ có thể đọc nếu:

```text
Ownership(place) == Owned
```

hoặc semantic equivalent hợp lệ.

Ví dụ:

```axiom
let x: i32
print(x)
```

→ reject.

Formal rule:

```text
READ(x)
requires Initialized(x)
```

---

# 12. Move

Ví dụ:

```axiom
let b = a
```

nếu `a` là non-Copy:

```text
Before:
a = Owned

After:
a = Moved
b = Owned
```

Không yêu cầu physical memory copy.

---

# 13. Copy

Nếu:

```text
T: Copy
```

thì:

```axiom
let b = a
```

semantic effect:

```text
a = Owned
b = Owned
```

Cả hai độc lập.

---

# 14. Clone

```axiom
let b = a.clone()
```

là một ordinary function call:

```text
Clone::clone(a)
```

Compiler không được biến Move thành Clone chỉ vì thuận tiện.

---

# 15. Drop

Khi ownership kết thúc:

```text
Owned → Dropped
```

compiler elaborates:

```text
DROP(place)
```

Drop là semantic event trước khi tối ưu.

Sau đó compiler có thể chứng minh:

```text
DROP(x)
```

không observable ngoài resource/effect semantics và loại bỏ physical work nếu hợp lệ.

---

# 16. Exactly-once cleanup

Invariant:

```text
∀ owned resource R:
    Drop(R) occurs exactly once
```

trừ trường hợp ownership được chuyển sang owner khác.

Move:

```text
A owns R
    ↓
Move
    ↓
B owns R
```

không tạo thêm Drop.

---

# 17. Partial move

Ví dụ:

```axiom
struct Pair {
    a: String
    b: String
}
```

Nếu:

```axiom
let x = pair.a
```

thì:

```text
pair.a = Moved
pair.b = Owned
```

Compiler có thể Drop `pair.b`.

---

# 18. Custom Drop restriction

Nếu type có custom Drop:

```text
struct T implements Drop
```

thì partial move bị hạn chế theo frozen ownership rules.

Lý do:

```text
Drop::drop(&self)
```

có thể cần toàn bộ logical object state.

Do đó verifier không được đoán.

---

# 19. Capability state

Formal capability:

```text
Capability =
{
    Provenance
    Region
    Access
    Lifetime
    StorageDomain
    ExecutionDomain
}
```

---

# 20. Read capability

```axiom
view<T>
```

semantic capability:

```text
Access = READ
```

Nhiều READ có thể coexist:

```text
view<T>
view<T>
view<T>
```

nếu provenance/lifetime hợp lệ.

---

# 21. Mutable capability

```axiom
mut_view<T>
```

semantic:

```text
Access = WRITE
```

và exclusive.

Không thể có:

```text
mut_view<T>
+
view<T>
```

cùng region nếu write capability còn active.

---

# 22. Region

Mỗi capability có region:

```text
RegionId
```

Quan hệ:

```text
DISJOINT
SAME
CONTAINS
CONTAINED_BY
OVERLAPS
UNKNOWN
```

---

# 23. Capability conflict

Formal:

```text
WRITE(R1) conflicts READ(R2)
if MayOverlap(R1,R2)
```

và:

```text
WRITE(R1) conflicts WRITE(R2)
if MayOverlap(R1,R2)
```

Nhưng:

```text
WRITE(field.a)
WRITE(field.b)
```

có thể coexist nếu:

```text
DISJOINT(a,b)
```

được chứng minh.

---

# 24. Unknown is not disjoint

Đây là invariant quan trọng:

```text
UNKNOWN ≠ DISJOINT
```

Compiler không được dùng:

```text
"không biết overlap"
```

như:

```text
"chắc chắn không overlap"
```

---

# 25. Capability lifetime

Capability phải có:

```text
start
end
```

và:

```text
end <= owner lifetime
```

Không có safe capability dangling.

---

# 26. Owner destruction rule

Không thể:

```text
owner = Drop
capability(owner) = live
```

Do đó:

```axiom
let p = view(x)
drop(x)
```

bị reject nếu `p` còn sống.

---

# 27. Relocation rule

Nếu:

```text
Vec<T>
```

đang có active:

```text
view<T>
```

thì operation có thể relocate storage phải bị chặn.

Compiler có thể:

1. trì hoãn relocation
2. chứng minh capability không còn live
3. dùng stable storage
4. reject

---

# 28. Semantic evaluation

Expression evaluation là deterministic.

Ví dụ:

```axiom
f(a(), b())
```

Axiom phải xác định rõ evaluation order.

Canonical:

```text
evaluate receiver/function
→ evaluate arguments left-to-right
→ call
```

Không phụ thuộc optimizer.

---

# 29. Why this matters

Nếu source:

```axiom
f(a(), b())
```

có side effects, compiler không được đổi thành:

```text
b()
a()
f(...)
```

chỉ vì machine code thuận tiện.

Optimization chỉ được thay đổi thứ tự nếu chứng minh:

```text
observable behavior preserved
```

---

# 30. Function call transition

Conceptual transition:

```text
⟨Call(f,args), Σ⟩
        →
⟨Body(f), Σ'⟩
```

với:

```text
Σ' =
    bind parameters
    transfer/match ownership
    establish capabilities
    establish effects
```

---

# 31. Return

Return:

```axiom
return value
```

phải:

1. evaluate value
2. verify return capability
3. Drop remaining locals
4. transfer returned ownership
5. exit function

Thứ tự cleanup phải deterministic.

---

# 32. Return view

Ví dụ:

```axiom
fn first(x: view<Array>) -> view<Element>
```

return capability phải preserve provenance:

```text
returned_view.provenance = source.provenance
```

và verifier phải chứng minh:

```text
source owner lifetime >= returned capability lifetime
```

---

# 33. Control-flow semantics

Mọi function được canonicalize thành CFG.

```text
BasicBlock
    ↓
Terminator
```

Các terminator:

```text
Jump
Branch
Switch
Return
Panic
Unreachable
Call
AwaitSuspend
```

---

# 34. `if`

```axiom
if cond {
    a
} else {
    b
}
```

formal:

```text
evaluate cond
    ↓
true → block A
false → block B
    ↓
join
```

Ownership state tại join phải được compatible.

---

# 35. `match`

`match` được lower thành decision tree.

Nhưng semantic requirement:

```text
all possible values covered
```

được kiểm tra trước lowering.

---

# 36. Exhaustiveness

Nếu:

```axiom
enum Option<T> {
    Some(T)
    None
}
```

mà:

```axiom
match x {
    Some(v) => ...
}
```

→ reject vì thiếu `None`.

---

# 37. Pattern bindings

Pattern binding tạo local ownership/capability theo semantics của pattern.

Ví dụ:

```axiom
Some(value)
```

có thể:

```text
Move payload
```

hoặc:

```text
View payload
```

tùy pattern/type context.

Không implicit clone.

---

# 38. `loop`

```axiom
loop {
    ...
}
```

là CFG cycle.

Verifier phải đạt fixed point cho:

```text
ownership
capability
initialization
effects
```

---

# 39. `break`

`break value` nếu được phép trả value khỏi loop phải có join semantics rõ ràng.

Conceptually:

```text
loop result =
    join(all break values)
```

Type inference phải thống nhất.

---

# 40. `?`

```axiom
let x = foo()?
```

không phải magic exception.

Nó lower thành:

```text
match foo() {
    Ok(v) => v
    Err(e) => return Err(e)
}
```

Ownership/drop semantics được áp dụng như `match`.

---

# 41. Panic

Panic là control transition:

```text
Normal
   ↓
Panic
```

Tùy profile:

```text
Abort
Unwind
Custom
```

---

# 42. Panic ≠ Result

```text
Result
```

là ordinary semantic value.

```text
panic
```

là abnormal control flow.

Compiler không được coi chúng giống nhau.

---

# 43. Effect semantics

Formal effect set:

```text
E =
{
    Read,
    Write,
    Allocate,
    Deallocate,
    Drop,
    Atomic,
    Volatile,
    IO,
    Synchronize,
    Panic,
    Foreign,
    Unsafe,
    GPU,
    Async
}
```

Function có:

```text
Effects(f)
```

---

# 44. Pure function

Nếu function được compiler chứng minh pure:

```text
Effects(f) = {}
```

compiler có thể aggressive optimize.

Ví dụ:

```text
f(10) + f(10)
```

có thể CSE thành:

```text
tmp = f(10)
tmp + tmp
```

---

# 45. Effect prevents invalid optimization

Nếu:

```axiom
fn log() -> i32
```

có:

```text
IO
```

compiler không thể tự động xóa:

```text
log()
```

chỉ vì return value không được dùng.

---

# 46. Volatile

`volatile` là observable memory interaction.

Compiler phải preserve:

```text
volatile load/store
```

và không được treat như ordinary load/store.

---

# 47. Atomic

Atomic operation có hai dimensions:

```text
Atomicity
Memory ordering
```

Ví dụ:

```text
AtomicLoad(Relaxed)
AtomicStore(Release)
CompareExchange(Acquire,Relaxed)
```

Formal semantics phải map tới memory model.

---

# 48. Happens-before

Axiom định nghĩa:

```text
HB =
transitive closure(
    sequenced-before
    +
    synchronizes-with
)
```

Optimizer không được tạo execution observable vi phạm memory model.

---

# 49. Data race

Safe Axiom program:

```text
no data race
```

Compiler verifier phải reject unsafe concurrent access nếu không có valid synchronization.

---

# 50. Unsafe semantics

`unsafe` không có nghĩa:

```text
anything is allowed
```

Mà:

```text
programmer may establish trusted preconditions
```

Ví dụ:

```axiom
unsafe {
    p->field
}
```

có thể establish:

```text
p is valid
aligned
initialized
accessible
```

nhưng compiler chỉ tiếp tục safe reasoning dựa trên **contract cụ thể**.

---

# 51. Undefined behavior

Axiom nên hạn chế UB tối đa.

Safe Core:

```text
invalid operation
→ compile-time rejection
```

Unsafe:

```text
violated unsafe contract
→ outside safe semantic guarantee
```

Nhưng compiler vẫn không được tự ý biến mọi unsafe code thành arbitrary behavior nếu semantics/ABI contract còn quy định.

---

# 52. Numeric semantics

Integer overflow phải có defined behavior.

Các operation:

```text
checked
wrapping
saturating
```

hoặc semantics mặc định được frozen ở numeric subsystem.

Không có C-style:

```text
signed overflow = arbitrary UB
```

trong safe Core.

---

# 53. Floating point

Default:

```text
strict FP
```

`fast-math` là explicit semantic mode.

Do đó compiler chỉ được:

```text
reassociate
fuse
approximate
```

khi profile/annotation cho phép.

---

# 54. Async semantics

Async function:

```axiom
async fn f()
```

được formalize như:

```text
Future<T>
```

với:

```text
Poll(Future)
    =
Ready(T)
    |
Pending
```

---

# 55. Await transition

```axiom
x.await
```

có thể:

```text
Ready(v)
    → continue
```

hoặc:

```text
Pending
    → Suspend
```

Các local sống qua suspension trở thành state machine fields.

---

# 56. Async ownership

Trước suspension:

```text
LiveAcrossAwait
```

được phân tích.

View/capability không thể sống qua await nếu contract không cho phép.

Owned values có thể.

---

# 57. Cancellation

Cancellation không phải:

```text
panic
```

và không phải:

```text
Drop
```

nó là một control/execution event do async abstraction định nghĩa.

---

# 58. Thread semantics

Thread spawn:

```text
spawn(f)
```

yêu cầu closure/task thỏa:

```text
Send
```

nếu execution domain có thể migrate.

Ownership transfer xảy ra tại boundary.

---

# 59. Channel

Channel send:

```text
send(value)
```

có semantic:

```text
ownership transfer
+
synchronization
```

Không implicit serialization.

---

# 60. GPU semantics

Kernel execution:

```text
launch(kernel,args)
```

tạo:

```text
ExecutionDomain = GPU
```

và kiểm tra:

```text
GPU legality
storage domains
capabilities
synchronization
```

---

# 61. Comptime semantics

`comptime` sử dụng cùng semantic model:

```text
ownership
types
Drop
capabilities
effects
```

nhưng chạy trong:

```text
Compiler Execution Environment
```

Không phải runtime process.

---

# 62. Comptime external state

Ví dụ:

```text
ReadFilesystem
```

là explicit external effect.

Nếu sử dụng input đó:

```text
BuildFingerprint
```

phải thay đổi.

Do đó cache không thể trả artifact cũ sai semantics.

---

# 63. FFI semantics

Foreign call:

```axiom
extern "C" fn foo(...)
```

được xem là:

```text
Foreign effect
```

và verifier dùng:

```text
FfiContract
```

để biết:

```text
ownership
nullability
alignment
thread safety
effects
error behavior
callback lifetime
```

---

# 64. External state

Semantic machine cần model:

```text
ExternalState
```

nhưng không cần mô phỏng toàn OS.

Observable external effects gồm:

```text
IO
filesystem
network
process
volatile
FFI
environment
clock
randomness
```

---

# 65. Nondeterminism

Axiom không cấm nondeterministic programs.

Nhưng nondeterminism phải nằm trong semantic boundary được định nghĩa.

Ví dụ:

```text
random()
```

không thể bị compiler constant-fold nếu không có deterministic contract.

---

# 66. Observable behavior

Hai program được coi equivalent nếu không phân biệt được bởi các observable:

```text
Return value
Result
Panic
Termination
IO
Volatile operations
Atomic behavior
Synchronization behavior
FFI-visible behavior
Process/environment effects
```

---

# 67. Optimization correctness

Compiler transformation:

```text
P → P'
```

chỉ legal nếu:

```text
Obs(P) = Obs(P')
```

hoặc:

```text
Obs(P') ⊆ allowed behaviors(P)
```

theo semantic category tương ứng.

---

# 68. Compiler freedom

Compiler được phép:

```text
eliminate allocation
eliminate copy
eliminate move
inline
devirtualize
reorder independent operations
scalarize
vectorize
fuse loops
specialize
merge functions
split functions
```

nếu semantic obligations được giữ nguyên.

---

# 69. Allocation erasure

Source:

```axiom
let x = Box(value)
use(x)
```

có thể compile thành:

```text
register value
```

nếu:

```text
address never observable
allocation effects absent
storage contract not exposed
```

---

# 70. Copy erasure

Source semantic:

```text
Copy(a)
```

không bắt buộc machine copy.

Compiler có thể dùng cùng physical register nếu không có observable alias.

---

# 71. Move erasure

Move chỉ là ownership transition.

Do đó:

```text
a → b
```

có thể không tạo machine instruction nào.

---

# 72. Dynamic dispatch erasure

Source:

```axiom
dyn Drawable
```

nếu compiler chứng minh concrete target:

```text
Circle
```

thì:

```text
dynamic call
```

→

```text
direct call
```

được phép.

---

# 73. Semantic fingerprint

Mỗi semantic artifact có fingerprint dựa trên:

```text
Public declarations
Types
Traits
Generic constraints
Effects
ABI contracts
Comptime dependencies
Target semantics where relevant
```

Không dựa chỉ vào generated machine code.

---

# 74. Reference interpreter

`ax-ref` sẽ implement:

```text
Semantic Kernel
```

chứ không implement:

```text
LLVM
x86
ARM
```

Mục tiêu:

```text
ax-ref program
        ↓
canonical observable result
```

---

# 75. MIR interpreter

`ax-mir` chạy:

```text
MIR
```

Do đó có thể test:

```text
Source
   ↓
AST/HIR
   ↓
MIR
```

và so sánh:

```text
ax-ref(source)
==
ax-mir(MIR)
```

---

# 76. Translation validation

Mỗi optimizer pass:

```text
MIR → OptIR
```

phải có:

```text
Preconditions
Transformation
Preserved invariants
Semantic obligation
Validation
```

Ví dụ:

```text
LICM
```

chỉ move instruction nếu effects/alias/dependencies cho phép.

---

# 77. Semantic proof boundary

Architecture chính thức:

```text
Parsed Program
      ↓
Typed Program
      ↓
MIR
      ↓
VERIFIER
      ↓
Verified MIR
      ↓
OPTIMIZER
      ↓
Optimized MIR
      ↓
ABI
      ↓
Machine
```

**Verified MIR là trust boundary.**

---

# 78. Compiler không được optimize trước verification

Không:

```text
MIR
 ↓
aggressive optimization
 ↓
safety verification
```

Mà:

```text
MIR
 ↓
verification
 ↓
Verified MIR
 ↓
optimization
```

Điều này tránh optimization vô tình che mất bug semantic.

---

# 79. Formal judgments

Semantic Kernel sử dụng các judgment kiểu:

```text
Γ ⊢ e : T
```

nghĩa:

```text
under environment Γ,
expression e has type T
```

Ownership:

```text
Γ ; Ω ⊢ e ⇓ Ω'
```

Capability:

```text
Γ ; Ω ; Κ ⊢ e : T
```

Evaluation:

```text
⟨e, Σ⟩ → ⟨e', Σ'⟩
```

Completion:

```text
⟨e, Σ⟩ ⇓ ⟨v, Σ'⟩
```

---

# 80. Small-step và big-step

Axiom dùng cả hai.

## Big-step

Dùng cho:

```text
reference interpreter
high-level semantic tests
```

Ví dụ:

```text
⟨e, Σ⟩ ⇓ ⟨v, Σ'⟩
```

## Small-step

Dùng cho:

```text
async
concurrency
atomics
panic
suspension
observable ordering
```

---

# 81. Why both?

Big-step dễ hiểu:

```text
expression → result
```

Small-step cần thiết khi có:

```text
multiple execution steps
suspension
interleaving
synchronization
```

Do đó không nên ép toàn bộ Axiom vào một semantic style duy nhất.

---

# 82. Semantic determinism

Sequential Core phải deterministic:

```text
same input
+
same external state
+
same defined execution conditions
→ same observable behavior
```

Concurrency có thể nondeterministic theo memory model.

---

# 83. Concurrency semantics

Không cố định scheduler.

Thay vào đó semantic model định nghĩa:

```text
allowed executions
```

Scheduler có thể:

```text
FIFO
work-stealing
priority
OS scheduler
GPU scheduler
```

miễn execution nằm trong allowed semantic set.

---

# 84. Memory model abstraction

Axiom không mô phỏng CPU cache.

Nó định nghĩa:

```text
Atomic ordering
Happens-before
Synchronization
Data-race freedom
```

CPU backend chịu trách nhiệm mapping:

```text
Axiom memory model
        ↓
x86
ARM
RISC-V
WASM
GPU
```

---

# 85. Stable address

Stable address không phải property mặc định của value.

Nếu API yêu cầu:

```text
StableAddress
```

thì semantic storage contract được tạo.

Compiler không được relocate storage theo cách phá contract.

---

# 86. Raw pointer semantics

Raw pointer:

```text
*const T
*mut T
```

là machine-level capability candidate, nhưng không tự động trở thành safe capability.

Integer:

```text
usize
```

→ pointer không được suy luận provenance tự động.

---

# 87. Pointer provenance

Formal pointer:

```text
Pointer =
{
    Address
    Provenance
}
```

Một integer chỉ có:

```text
Address-like value
```

không tự có:

```text
Provenance
```

---

# 88. `unsafe` pointer conversion

Unsafe contract có thể establish:

```text
pointer p
belongs to storage S
valid for region R
aligned for T
initialized
accessible
```

Sau boundary:

```text
p → safe view<T>
```

nếu contract đầy đủ.

---

# 89. Semantic resources

Resource semantics:

```text
ResourceState =
    Acquired
    Moved
    Released
```

Ví dụ File:

```text
File acquired
    ↓
Move
    ↓
new owner
    ↓
Drop
    ↓
OS handle released
```

Nhưng:

```text
Drop ≠ protocol close
```

---

# 90. Explicit external effects

Nếu:

```axiom
file.write(data)
```

thì effect:

```text
IO + Write
```

Compiler không được eliminate chỉ vì return value không được sử dụng.

---

# 91. Semantic error taxonomy

Semantic Kernel phân biệt:

```text
TypeError
OwnershipError
CapabilityError
TraitError
EffectError
ControlFlowError
FFIError
ConcurrencyError
ComptimeError
GPUError
UnsafeContractViolation
```

Tooling có thể expose stable diagnostic IDs.

---

# 92. Semantic error vs compiler bug

Nếu program hợp lệ mà compiler:

```text
reject
```

→ compiler conformance failure.

Nếu:

```text
Verified MIR
```

được generate sai machine behavior:

→ **miscompilation**.

Nếu verifier itself violates formal rules:

→ **compiler correctness bug**.

---

# 93. Semantic oracle hierarchy

Authority:

```text
Formal Semantic Kernel
        ↓
Reference Interpreter
        ↓
MIR Interpreter
        ↓
Compiler
        ↓
Optimizer
        ↓
Backend
```

Compiler không được tự định nghĩa semantics khác Kernel.

---

# 94. Spec change protocol

Nếu phát hiện Core semantics cần thay đổi:

```text
Proposal
 ↓
Semantic rule update
 ↓
Reference interpreter
 ↓
Conformance tests
 ↓
Compiler
 ↓
Optimizer proof obligations
 ↓
Freeze
```

Không sửa compiler trước rồi coi implementation là specification.

---

# 95. Golden semantic programs

Axiom phải có bộ chương trình nhỏ:

```text
semantic/ownership/
semantic/capability/
semantic/drop/
semantic/control/
semantic/pattern/
semantic/trait/
semantic/async/
semantic/concurrency/
semantic/comptime/
semantic/ffi/
```

Mỗi test có expected observable behavior.

---

# 96. Example: ownership

```axiom
fn test() {
    let a = String("hello")
    let b = a

    use(b)
}
```

Valid.

```axiom
fn test() {
    let a = String("hello")
    let b = a

    use(a)
}
```

Reject:

```text
use-after-move
```

---

# 97. Example: capability

```axiom
fn f(x: mut_view<Vec<i32>>) {
    ...
}
```

Compiler guarantees exclusive access.

Không cần programmer viết:

```text
lifetime
borrow
'a
&mut
```

---

# 98. Example: method

Source:

```axiom
v.length()
```

Semantic canonicalization:

```text
length(v)
```

Reference interpreter chỉ cần implement một semantics.

---

# 99. Example: trait

```axiom
fn render<T: Drawable>(x: T) {
    x.draw()
}
```

Trait resolution xảy ra compile time.

Reference semantics sees:

```text
Call(Circle::draw, x)
```

sau resolution.

---

# 100. Example: dynamic dispatch

```axiom
fn render(x: dyn Drawable) {
    x.draw()
}
```

Reference semantics sees:

```text
DynamicDispatch(Drawable, draw, x)
```

ABI implementation decides physical dispatch.

---

# 101. Semantic lowering theorem

Mỗi lowering stage cần chứng minh:

```text
⟦Source⟧
=
⟦AST⟧
=
⟦HIR⟧
=
⟦MIR⟧
```

Sau optimization:

```text
⟦MIR⟧
=
⟦OptIR⟧
```

Sau ABI lowering:

```text
⟦OptIR⟧
=
⟦ABI-MIR⟧
```

Cuối cùng:

```text
⟦ABI-MIR⟧
≈
⟦Machine⟧
```

với `≈` là observable equivalence trên target.

---

# 102. Optimization theorem

Một optimization pass `P` hợp lệ nếu:

```text
Verified(MIR)
∧ Preconditions(P, MIR)
→
Equivalent(MIR, P(MIR))
```

Nếu precondition không chứng minh được:

```text
do not transform
```

Không được:

```text
assume
guess
heuristic-as-proof
```

---

# 103. Formal Kernel không quá lớn

Không đưa mọi library vào formal Core.

Kernel chỉ cần formalize:

```text
Values
Places
Types
Ownership
Capabilities
Evaluation
Control flow
Effects
Memory model
Concurrency primitives
Async
Unsafe boundary
Comptime
FFI boundary
```

Các API như:

```text
HTTP
SQL
GUI
Tensor
JSON
```

không cần là Semantic Kernel primitive.

---

# 104. Semantic kernel ≠ compiler implementation

Đây là distinction phải đóng băng:

```text
Semantic Kernel:
    what Axiom means

Compiler:
    how Axiom becomes executable

Optimizer:
    how executable representation becomes faster

Backend:
    how semantics map to target machine
```

---

# 105. Frozen invariants

```text
ASEM-20
The Formal Semantic Kernel is the normative authority for Core semantics.

ASEM-21
Compiler implementations must conform to the Semantic Kernel.

ASEM-22
Reference interpretation is derived from the Semantic Kernel.

ASEM-23
MIR semantics must preserve source semantics.

ASEM-24
Verified MIR is the optimization trust boundary.

ASEM-25
Optimization may transform only semantically verified programs.

ASEM-26
Optimization legality requires proven preconditions.

ASEM-27
Failure to prove an optimization precondition prevents that transformation.

ASEM-28
Optimization cannot redefine language semantics.

ASEM-29
Representation is not semantic unless explicitly observable.

ASEM-30
Storage placement is not semantic unless a storage contract exposes it.

ASEM-31
Move is an ownership transition and does not require a physical copy.

ASEM-32
Copy is semantic duplication and does not require a physical copy.

ASEM-33
Clone is explicit and is never introduced implicitly by the semantic model.

ASEM-34
Owned resources are released exactly once.

ASEM-35
Moved values cannot be read or dropped by the previous owner.

ASEM-36
Partial ownership is tracked at place granularity.

ASEM-37
Safe capability provenance must remain valid.

ASEM-38
Unknown region overlap cannot be treated as disjoint.

ASEM-39
Mutable capabilities are exclusive over potentially overlapping regions.

ASEM-40
An owner cannot be destroyed while a dependent safe capability remains live.

ASEM-41
Storage relocation cannot invalidate a live stable-address contract.

ASEM-42
Returned capabilities preserve valid provenance.

ASEM-43
Raw pointer provenance is not inferred from integer values.

ASEM-44
Unsafe operations may establish only explicitly defined trusted preconditions.

ASEM-45
Safe verification resumes only for established unsafe contracts.

ASEM-46
Sequential evaluation order is deterministic.

ASEM-47
Compiler optimization cannot reorder observable effects illegally.

ASEM-48
Result failure and panic are distinct semantic mechanisms.

ASEM-49
Panic is abnormal control flow rather than an ordinary Result value.

ASEM-50
Async suspension is explicit semantic control flow.

ASEM-51
Values live across suspension are subject to async ownership rules.

ASEM-52
Send and Share remain distinct semantic properties.

ASEM-53
Safe programs cannot contain data races.

ASEM-54
Atomicity and memory ordering are distinct properties.

ASEM-55
Happens-before is part of the concurrency semantics.

ASEM-56
FFI boundaries require explicit contracts for unspecified foreign behavior.

ASEM-57
Comptime follows the same core type and ownership semantics.

ASEM-58
Comptime external effects are explicit and participate in build identity.

ASEM-59
Generated code must re-enter normal semantic verification.

ASEM-60
Dynamic dispatch is semantic only when required by the dynamic abstraction.

ASEM-61
Static dispatch may be optimized into direct machine calls.

ASEM-62
Dynamic dispatch may be eliminated when its target is proven.

ASEM-63
Dynamic dispatch elimination cannot change observable behavior.

ASEM-64
Generic abstraction does not imply runtime allocation.

ASEM-65
Trait implementation selection is determined before optimization.

ASEM-66
Optimization level cannot change trait implementation selection.

ASEM-67
Observable external effects cannot be silently eliminated.

ASEM-68
Volatile operations are distinct from ordinary memory operations.

ASEM-69
Floating-point transformations must respect the active FP semantic profile.

ASEM-70
Numeric overflow behavior is defined by the numeric semantic contract.

ASEM-71
The reference interpreter is an executable semantic oracle.

ASEM-72
The MIR interpreter is a semantic validation layer.

ASEM-73
Source and MIR interpreters must agree on observable behavior.

ASEM-74
Miscompilation after Verified MIR is a compiler correctness failure.

ASEM-75
A compiler rejection of a semantically valid program is a conformance failure.

ASEM-76
The Semantic Kernel is independent of target instruction-set representation.

ASEM-77
Target lowering must preserve Semantic Kernel observables.

ASEM-78
Concurrency semantics define allowed executions rather than a particular scheduler.

ASEM-79
The Semantic Kernel does not require a monolithic runtime.

ASEM-80
The Semantic Kernel does not require a garbage collector.

ASEM-81
The Semantic Kernel does not require object headers.

ASEM-82
The Semantic Kernel does not require heap allocation for ordinary values.

ASEM-83
The Semantic Kernel does not expose compiler-internal storage decisions.

ASEM-84
Semantic equivalence is defined over observable behavior rather than machine instruction identity.

ASEM-85
Formal semantic changes require corresponding interpreter and conformance updates.
```

---

# 106. Kiến trúc sau BOOTSTRAP-233

Axiom hiện có một đường authority rất rõ:

```text
                 ┌──────────────────────┐
                 │ Formal Semantic Kernel│
                 └──────────┬───────────┘
                            │
                 ┌──────────▼───────────┐
                 │ Reference Interpreter│
                 └──────────┬───────────┘
                            │
                 ┌──────────▼───────────┐
                 │ Compiler Frontend    │
                 └──────────┬───────────┘
                            │
                 ┌──────────▼───────────┐
                 │         MIR          │
                 └──────────┬───────────┘
                            │
                      VERIFICATION
                            │
                 ┌──────────▼───────────┐
                 │     Verified MIR     │
                 └──────────┬───────────┘
                            │
                       OPTIMIZATION
                            │
                 ┌──────────▼───────────┐
                 │        OptIR         │
                 └──────────┬───────────┘
                            │
                         ABI/LIR
                            │
                 ┌──────────▼───────────┐
                 │     Machine Code     │
                 └──────────────────────┘
```

Đây là một điểm rất đáng giữ cho Axiom:

> **Compiler không phải nơi quyết định ngôn ngữ có nghĩa gì. Semantic Kernel mới quyết định.**

Nhờ vậy sau này nếu Gemini/Antigravity viết compiler, Claude viết compiler, hoặc chính Axiom self-host compiler được viết lại từ đầu, tất cả vẫn có cùng một “hợp đồng vật lý”.

---

# TASK TIẾP THEO

## **BOOTSTRAP-234 — Axiom Compiler Implementation Blueprint & Repository Architecture**

Bây giờ chúng ta đã có gần như toàn bộ **language architecture + formal semantics**. Task tiếp theo sẽ chuyển từ:

> “Axiom nên hoạt động như thế nào?”

sang:

> **“Chính xác phải viết compiler như thế nào để tạo ra Axiom đầu tiên?”**

Sẽ thiết kế cụ thể:

```text
axiom/
├── compiler/
│   ├── lexer/
│   ├── syntax/
│   ├── parser/
│   ├── ast/
│   ├── resolver/
│   ├── types/
│   ├── traits/
│   ├── hir/
│   ├── mir/
│   ├── verifier/
│   ├── comptime/
│   ├── interpreter/
│   ├── opt/
│   ├── abi/
│   ├── lir/
│   ├── backend/
│   ├── object/
│   ├── linker/
│   └── driver/
├── std/
├── tests/
├── spec/
└── tools/
```

và quan trọng nhất:

### **lộ trình “First Executable”**

Từ:

```text
Bootstrap compiler
    ↓
parse Axiom
    ↓
typecheck
    ↓
MIR
    ↓
verify
    ↓
LLVM/LLD bootstrap backend
    ↓
hello.exe
```

sau đó:

```text
Axiom compiler
    ↓
Axiom compiler
    ↓
Axiom compiler
```

cho đến:

```text
Axiom self-hosted compiler
+
Axiom self-hosted object writer
+
Axiom self-hosted linker
```

Task 234 sẽ là **bản thiết kế thực thi đầu tiên có thể đưa thẳng cho AI-agent để bắt đầu tạo repository và code compiler**, thay vì chỉ tiếp tục mô tả lý thuyết.