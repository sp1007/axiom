# BOOTSTRAP-215 — Formal Semantic Kernel & Unified Axiom Semantics

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là bước rất quan trọng: từ trước tới nay Axiom đã có rất nhiều subsystem được đóng băng riêng lẻ. 215 biến chúng thành **một semantic kernel thống nhất** để sau này compiler, reference interpreter, optimizer và specification đều dựa trên cùng một nền tảng.

Nguyên tắc:

> **Có đúng một định nghĩa về semantics. Mọi compiler phase, interpreter, optimizer, backend và tooling đều phải quy chiếu về định nghĩa đó.**

---

# 215.1. Ba tầng cần tách biệt

Axiom có ba tầng:

```text
┌──────────────────────────────────────┐
│          Language Semantics          │
│   "Chương trình có nghĩa gì?"        │
└──────────────────┬───────────────────┘
                   │
┌──────────────────▼───────────────────┐
│          Abstract Machine            │
│ ownership / capability / memory ...  │
└──────────────────┬───────────────────┘
                   │
┌──────────────────▼───────────────────┐
│       Physical Implementation         │
│ CPU / GPU / ABI / registers / RAM    │
└──────────────────────────────────────┘
```

Compiler được phép thay đổi tầng dưới nhưng không được thay đổi tầng trên.

---

# 215.2. Semantic Kernel

Kernel tối thiểu gồm:

```text
Value
Type
Place
Ownership
Capability
Storage
Effect
Execution
Control Flow
Resource
Concurrency
Async
Comptime
Unsafe
Foreign Boundary
```

---

# 215.3. Program State

Semantic state:

```text
State =
{
    Environment,
    Store,
    OwnershipState,
    CapabilityState,
    ExecutionState,
    EffectState
}
```

Không đồng nhất `Store` với physical memory.

---

# 215.4. Environment

Environment ánh xạ:

```text
Variable → Value / Place
```

Ví dụ:

```text
x → Place(42)
```

---

# 215.5. Store

Store chứa semantic objects:

```text
Place → ObjectState
```

ObjectState có thể:

```text
UNINIT
INIT
MOVED
PARTIAL
DROPPED
```

---

# 215.6. Physical memory không phải semantic Store

Compiler có thể biến:

```text
x
```

thành:

```text
register
stack slot
SSA value
memory
```

mà semantics không thay đổi.

---

# 215.7. Expression semantics

Mọi expression có thể được mô hình hóa:

```text
⟨Expression, State⟩
        ↓
⟨Result, State'⟩
```

---

# 215.8. Result của evaluation

Result không chỉ là value:

```text
EvalResult =
    Value
    Return
    Break
    Continue
    Panic
    Trap
    Suspend
    Diverge
```

---

# 215.9. Deterministic evaluation order

Axiom xác định evaluation order.

Compiler không được reorder những operations nếu reorder làm thay đổi observable behavior.

---

# 215.10. Pure computation

Nếu compiler chứng minh expression:

```text
Pure
```

thì có nhiều quyền optimization hơn.

---

# 215.11. Effects

Semantic effect set:

```text
Read
Write
Allocate
Deallocate
Drop
Atomic
Volatile
IO
Network
Synchronize
Foreign
Panic
Suspend
GPU
```

---

# 215.12. Effect không đồng nghĩa side effect đơn giản

Ví dụ:

```text
Read
```

có thể là read-only observable state.

`Pure` chỉ khi compiler chứng minh không có observable external effect.

---

# 215.13. Function semantics

Function được mô hình hóa:

```text
Arguments
    ↓
Pre-state
    ↓
Body evaluation
    ↓
Return / Panic / Diverge
    ↓
Post-state
```

---

# 215.14. Ownership là semantic state

Ownership không chỉ là compiler warning.

Ví dụ:

```text
let b = a
```

nếu `a` non-Copy:

```text
Owner(a) → Owner(b)
```

và `a` chuyển sang:

```text
Moved
```

---

# 215.15. Copy semantics

Nếu:

```text
let b = a
```

với `Copy`:

```text
a remains valid
b becomes independent semantic value
```

Không bắt buộc physical copy.

---

# 215.16. Move semantics

Move là:

```text
ownership state transition
```

không phải:

```text
memcpy
```

---

# 215.17. Clone semantics

Clone là explicit operation:

```text
a.clone()
```

có thể:

```text
allocate
copy
transform
fail
```

tùy type.

---

# 215.18. Drop semantics

Khi ownership kết thúc:

```text
Owned
 ↓
Drop
 ↓
Released
```

Drop là observable nếu resource release có observable effect.

---

# 215.19. Drop ordering

Mặc định:

```text
reverse initialization/declaration order
```

và phải được giữ ở semantic level.

---

# 215.20. Partial move

Ví dụ:

```text
struct S {
    a: A,
    b: B
}
```

có thể:

```text
move s.a
```

khi `S` cho phép partial move.

State:

```text
S
├── a → MOVED
└── b → OWNED
```

---

# 215.21. Custom Drop

Nếu `S` có custom Drop:

```text
partial move
```

bị hạn chế theo ownership rules đã đóng băng.

---

# 215.22. Capability semantics

Capability:

```text
Capability =
{
    Provenance,
    Region,
    Access,
    Lifetime,
    StorageDomain
}
```

---

# 215.23. `view<T>`

Semantic:

```text
READ capability
```

không phải ownership.

---

# 215.24. `mut_view<T>`

Semantic:

```text
WRITE capability
```

và phải exclusive đối với vùng tương ứng.

---

# 215.25. Capability validity

Một capability hợp lệ nếu:

```text
owner alive
provenance valid
region valid
access permitted
lifetime active
```

---

# 215.26. Aliasing semantics

Các capability:

```text
READ + READ
```

hợp lệ.

```text
READ + WRITE
```

xung đột.

```text
WRITE + WRITE
```

xung đột nếu overlap có thể xảy ra.

---

# 215.27. Unknown ≠ Disjoint

Đây là invariant cực quan trọng:

```text
UNKNOWN
```

không bao giờ được suy diễn thành:

```text
DISJOINT
```

---

# 215.28. Proven disjoint

Nếu compiler chứng minh:

```text
region(A) ∩ region(B) = ∅
```

thì hai mutable capabilities có thể tồn tại đồng thời.

---

# 215.29. Optimization bridge

Proof:

```text
DISJOINT
```

có thể trở thành internal:

```text
NO_ALIAS
```

để optimizer vectorize.

---

# 215.30. Storage semantics

Semantic storage domain:

```text
LOCAL
STATIC
TLS
DYNAMIC
INLINE
MAPPED
DEVICE
EXTERNAL
```

---

# 215.31. Storage domain ≠ physical location

`DYNAMIC` không nhất thiết có nghĩa:

```text
malloc()
```

Compiler có thể eliminate allocation.

---

# 215.32. Stable address

Địa chỉ chỉ trở thành semantic property khi explicit contract yêu cầu.

Ví dụ:

```text
stable storage
```

sẽ cấm relocation bất hợp lệ.

---

# 215.33. Logical identity

Axiom phân biệt:

```text
Value Identity
Storage Identity
Logical Identity
```

Không được suy ra Logical Identity từ địa chỉ.

---

# 215.34. Resource semantics

Resource có:

```text
Acquire
Own
Use
Transfer
Release
```

nhưng không cần một universal `Resource` type.

---

# 215.35. Resource failure

Acquire/close có thể:

```text
Result
```

Drop không dùng để che giấu recoverable failure.

---

# 215.36. Concurrency semantics

Unified model:

```text
Ownership
+
Capability
+
Synchronization
+
Execution Domain
```

---

# 215.37. Execution domain

Semantic execution domain:

```text
Thread
Task
Fiber
GPU
Interrupt
Foreign
```

---

# 215.38. Send

`Send` cho phép ownership transfer:

```text
Domain A
   ↓ Move
Domain B
```

---

# 215.39. Share

`Share` cho phép concurrent shared access theo contract.

Không đồng nghĩa mutable access.

---

# 215.40. Atomic semantics

Atomic operation là semantic operation riêng:

```text
AtomicLoad
AtomicStore
AtomicRMW
CAS
```

---

# 215.41. Memory ordering

Axiom dùng:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

với happens-before model đã đóng băng.

---

# 215.42. Data race

Safe Axiom không cho phép:

```text
conflicting concurrent non-atomic accesses
```

nếu không có synchronization contract phù hợp.

---

# 215.43. Async semantics

`async fn` là function tạo Future.

```text
call async fn
        ↓
Future
```

Không tự động spawn.

---

# 215.44. Suspension

`await` tạo:

```text
SuspensionPoint
```

và compiler kiểm tra state sống qua suspension.

---

# 215.45. Async state

Chỉ values cần thiết sau suspension mới trở thành state fields.

---

# 215.46. View qua await

View không được sống qua await nếu compiler không chứng minh storage/execution contract cho phép.

---

# 215.47. Cancellation

Cancellation:

```text
Cancel
```

khác:

```text
Panic
```

và khác:

```text
Drop Future
```

---

# 215.48. Comptime semantics

Comptime là execution trong compiler environment:

```text
Source
 ↓
Comptime VM
 ↓
Comptime Value
```

---

# 215.49. Runtime/comptime separation

Comptime resource không tự động trở thành runtime resource.

---

# 215.50. Comptime external effects

Filesystem/network/environment/tool execution phải qua capability.

---

# 215.51. Comptime determinism

Trong reproducible mode:

```text
nondeterministic input
```

phải bị hạn chế hoặc explicit dependency.

---

# 215.52. GPU semantics

GPU không phải một "CPU nhanh hơn".

GPU có:

```text
Execution Domain
Storage Domain
Synchronization Domain
```

riêng.

---

# 215.53. Host → Device

Transfer là explicit semantic operation.

---

# 215.54. GPU completion

Launch:

```text
submit()
```

không nhất thiết đồng nghĩa:

```text
computation completed
```

`GpuEvent` biểu diễn completion.

---

# 215.55. GPU capability

Device view phải có:

```text
valid device provenance
correct address space
correct lifetime
```

---

# 215.56. FFI semantics

Foreign function là semantic boundary:

```text
Axiom
 ↓
FfiContract
 ↓
Foreign ABI
```

---

# 215.57. Foreign uncertainty

Nếu compiler không biết foreign function có effect gì:

```text
conservative effect model
```

được sử dụng.

---

# 215.58. Unsafe semantics

Unsafe không có nghĩa:

```text
compiler stops checking
```

Nó nghĩa:

```text
programmer establishes trusted preconditions
```

---

# 215.59. Unsafe boundary

Ví dụ:

```text
raw pointer
 ↓ unsafe
validated capability
 ↓
safe code
```

Sau boundary compiler tiếp tục verification.

---

# 215.60. Panic semantics

Panic là control-flow event:

```text
normal execution
       ↓
     panic
       ↓
abort / unwind
```

tùy profile.

---

# 215.61. `never`

Expression diverging:

```text
never
```

có thể:

```text
panic
abort
loop forever
exit process
```

tùy semantics.

---

# 215.62. `Result`

`Result<T,E>` là ordinary value.

Không có exception machinery ẩn.

---

# 215.63. `?`

`?` là syntactic/control-flow sugar cho:

```text
success → continue
failure → return
```

với conversion rules đã định nghĩa.

---

# 215.64. Pattern semantics

`match` phải exhaustive trong Complete Semantic Mode.

---

# 215.65. Pattern evaluation

Pattern matching không được đọc field đã:

```text
Moved
```

---

# 215.66. Representation independence

Semantic:

```text
struct Point { x, y }
```

không mặc định cam kết:

```text
offset(x)
offset(y)
```

---

# 215.67. `@repr`

Representation contract biến một phần physical representation thành observable ABI property.

---

# 215.68. Serialization independence

Memory layout:

```text
≠
```

wire representation.

---

# 215.69. ABI independence

Semantic function:

```text
fn f(...)
```

không tự động cam kết:

```text
C ABI
```

trừ khi explicit.

---

# 215.70. Observable behavior

Đây là định nghĩa quan trọng nhất của semantic equivalence.

Observable behavior bao gồm:

```text
Return value
Result
Panic
Termination
IO
Volatile effects
Atomic synchronization
Foreign effects
Resource effects
GPU-visible effects
```

---

# 215.71. Optimization equivalence

Nếu:

```text
Program A
Program B
```

có cùng observable behavior trong mọi allowed execution thì transformation hợp lệ.

---

# 215.72. Compiler freedom

Compiler được:

```text
inline
clone
specialize
vectorize
reorder
eliminate
scalarize
allocate differently
```

miễn semantics được bảo toàn.

---

# 215.73. Allocation elimination

Nếu allocation không observable:

```text
allocate
 ↓
eliminate
```

hợp lệ.

---

# 215.74. Copy elimination

Nếu Copy semantics không yêu cầu physical copy:

```text
copy
 ↓
SSA value
```

hợp lệ.

---

# 215.75. Move elimination

Move có thể biến mất hoàn toàn ở machine level.

Ownership transition vẫn tồn tại ở semantic level.

---

# 215.76. Drop elimination

Drop chỉ có thể loại bỏ nếu compiler chứng minh:

```text
no observable cleanup effect
```

---

# 215.77. Effect-aware optimization

Compiler không được loại bỏ:

```text
IO
volatile
observable synchronization
required zeroization
```

chỉ vì kết quả return không được sử dụng.

---

# 215.78. Memory model boundary

Compiler được reorder ordinary memory operations khi không vi phạm:

```text
capability rules
happens-before
volatile semantics
foreign contracts
```

---

# 215.79. Reference Interpreter

`ax-ref` thực thi semantic model trực tiếp.

Mục tiêu:

```text
simple
obvious
correct
```

không phải tốc độ.

---

# 215.80. MIR Interpreter

`ax-mir` thực thi:

```text
Verified MIR
```

để kiểm tra frontend/verifier.

---

# 215.81. Semantic pipeline

Canonical pipeline:

```text
Source
 ↓
AST
 ↓
HIR
 ↓
Typed HIR
 ↓
MIR
 ↓
Verified MIR
 ↓
OptIR
 ↓
ABI MIR
 ↓
LIR
 ↓
Machine IR
 ↓
Machine Code
```

---

# 215.82. Verified MIR là semantic executable form

Verified MIR phải đủ thông tin để biểu diễn toàn bộ Core semantics cần thiết.

---

# 215.83. OptIR không được trở thành semantic source

OptIR chỉ là optimization representation.

Semantic truth vẫn nằm ở:

```text
Verified MIR
+
Formal Semantic Kernel
```

---

# 215.84. Machine code không phải specification

Assembly output không phải semantic authority.

---

# 215.85. Backend correctness

Backend phải chứng minh:

```text
Verified MIR
        ↓
Machine Code
```

preserves observable behavior.

---

# 215.86. Formal semantic relation

Khái niệm:

```text
MIR ⇓ Behavior
```

và:

```text
MachineCode ⇓ Behavior
```

Compiler correctness yêu cầu hai behavior tương thích.

---

# 215.87. Undefined behavior cực kỳ hạn chế

Safe Axiom không dùng UB như một công cụ optimization thông thường.

Nếu operation không hợp lệ:

```text
compile-time rejection
```

hoặc semantics rõ ràng như:

```text
panic
trap
Result
```

tùy trường hợp.

---

# 215.88. Unsafe invalid behavior

Unsafe có thể cho phép programmer tạo state không được compiler chứng minh.

Nhưng contract phải xác định boundary.

---

# 215.89. Integer overflow

Đã frozen:

```text
checked
wrapping
saturating
```

được xác định rõ.

Không dựa vào C-style signed-overflow UB.

---

# 215.90. Floating-point semantics

Strict FP giữ:

```text
NaN
Infinity
-0
rounding
ordering constraints
```

theo numerical profile.

---

# 215.91. Fast math

Fast math là explicit semantic/numerical profile.

Compiler không tự biến strict program thành fast-math.

---

# 215.92. Constant-time

`@constant_time` trở thành semantic/security contract.

Backend phải tôn trọng contract.

---

# 215.93. Zeroization

Secure zeroization là observable security behavior.

Optimizer không được xóa nếu contract yêu cầu thực hiện.

---

# 215.94. Compiler proofs

Mọi optimization proof có thể được biểu diễn:

```text
Precondition
Transformation
Preserved Invariants
Postcondition
```

---

# 215.95. Proof failure

Nếu compiler không chứng minh được:

```text
optimization
```

thì:

```text
do not transform
```

Không được đoán.

---

# 215.96. Semantic certainty

CompilerDB sử dụng:

```text
PROVEN
DISPROVEN
UNKNOWN
AMBIGUOUS
ERROR
INCOMPLETE
```

đã thống nhất với diagnostics/AI tooling.

---

# 215.97. AI semantic interface

AI có thể hỏi:

```text
Why is this move invalid?
Why can't this view escape?
Why wasn't this loop vectorized?
Why can't this value cross await?
```

Compiler trả proof/fact.

AI không được trở thành semantic authority.

---

# 215.98. Formal Kernel invariants — `ASEM`

### `ASEM-20`
Axiom shall have one authoritative semantic model.

### `ASEM-21`
Compiler phases shall not independently redefine Core semantics.

### `ASEM-22`
Reference interpretation shall be based on the semantic model.

### `ASEM-23`
Verified MIR shall represent executable semantic meaning.

### `ASEM-24`
Optimization representations shall not replace semantic authority.

### `ASEM-25`
Physical representation shall remain distinct from semantic value.

### `ASEM-26`
Physical storage location shall not be observable unless explicitly contracted.

### `ASEM-27`
Ownership shall be part of semantic state.

### `ASEM-28`
Capability validity shall be part of semantic state.

### `ASEM-29`
Move shall represent an ownership transition.

### `ASEM-30`
Copy shall represent semantic value duplication.

### `ASEM-31`
Clone shall remain explicit.

### `ASEM-32`
Drop shall have deterministic semantic ordering.

### `ASEM-33`
Partial ownership states shall be representable.

### `ASEM-34`
Invalid ownership states shall be rejected before production code generation.

### `ASEM-35`
Capability lifetime shall not exceed provenance validity.

### `ASEM-36`
Unknown aliasing shall never be treated as proven disjointness.

### `ASEM-37`
Safe mutable capabilities shall obey exclusivity rules.

### `ASEM-38`
Storage domain shall remain distinct from ownership.

### `ASEM-39`
Logical identity shall remain distinct from physical address.

### `ASEM-40`
Execution domain shall remain distinct from storage domain.

### `ASEM-41`
Send shall remain distinct from Share.

### `ASEM-42`
Synchronization shall define ordering rather than ownership.

### `ASEM-43`
Atomicity shall remain distinct from memory ordering.

### `ASEM-44`
Async suspension shall be explicit semantic control flow.

### `ASEM-45`
Cancellation shall remain distinct from panic.

### `ASEM-46`
Comptime execution shall remain distinct from runtime execution.

### `ASEM-47`
Comptime external authority shall be explicit.

### `ASEM-48`
GPU execution/storage domains shall remain explicit.

### `ASEM-49`
Foreign calls shall cross explicit ABI/semantic contracts.

### `ASEM-50`
Unsafe operations shall not silently disable semantic verification.

### `ASEM-51`
Observable behavior shall define semantic equivalence.

### `ASEM-52`
Compiler optimizations shall preserve observable behavior.

### `ASEM-53`
Effectful operations shall not be eliminated without proof of non-observability.

### `ASEM-54`
Strict numerical semantics shall not be silently replaced by relaxed semantics.

### `ASEM-55`
Security contracts shall constrain optimization where required.

### `ASEM-56`
Reference semantics shall be independent of target machine representation.

### `ASEM-57`
Backend implementation shall preserve the semantic model.

### `ASEM-58`
Linking shall preserve observable program behavior.

### `ASEM-59`
Undefined behavior shall not be used as a general optimization mechanism in safe Core.

### `ASEM-60`
Semantic uncertainty shall never be promoted to proof.

### `ASEM-61`
AI-generated code shall enter the same semantic pipeline as human-written code.

### `ASEM-62`
AI tooling shall consume semantic facts rather than redefine semantics.

### `ASEM-63`
Compiler diagnostics shall be explainable in terms of semantic rules.

### `ASEM-64`
Every semantic rule shall have conformance tests.

### `ASEM-65`
Every optimization rule shall have correctness validation.

### `ASEM-66`
Every machine-level lowering boundary shall have validation coverage.

### `ASEM-67`
Semantic rules shall remain independent of optimization level.

### `ASEM-68`
Semantic rules shall remain independent of compiler parallelism.

### `ASEM-69`
Semantic rules shall remain independent of cache state.

### `ASEM-70`
Semantic rules shall remain stable across supported target architectures unless explicitly target-defined.

---

# 215.99. Kết quả quan trọng của 215

Bây giờ Axiom có một trục hoàn chỉnh:

```text
                 AXIOM SEMANTICS
                       │
       ┌───────────────┼────────────────┐
       ▼               ▼                ▼
    Values         Ownership        Effects
       │               │                │
       └───────────────┼────────────────┘
                       ▼
                  Capabilities
                       │
                ┌──────┴──────┐
                ▼             ▼
           Concurrency      Async
                │             │
                └──────┬──────┘
                       ▼
                  Verified MIR
                       │
                       ▼
                    OptIR
                       │
                       ▼
                  ABI / LIR
                       │
                       ▼
                 Machine Code
```

Điểm quan trọng nhất là **không còn mỗi subsystem có một "định nghĩa đúng" riêng**. Ownership, memory, async, GPU, FFI, security, numerical semantics… đều quy về cùng một semantic model.

---

# BOOTSTRAP-216 — Axiom Language Specification v1.0: Consolidation, Conflict Resolution & Feature Freeze

**TRẠNG THÁI: NEXT**

Đây là bước tiếp theo rất hợp lý.

Sau 215, thay vì tiếp tục thêm feature vô hạn, 216 sẽ làm việc mà một language project thực sự cần trước khi implementation lớn:

> **Rà soát toàn bộ specification đã thiết kế, phát hiện mâu thuẫn, quyết định precedence, loại bỏ feature trùng lặp, phân Core / Standard Library / System / Experimental và đóng băng Axiom v1.0.**

Đặc biệt sẽ tạo:

```text
Axiom Language
├── Core v1.0
├── Standard Library v1.0
├── System Layer v1.0
├── Compiler Contract v1.0
├── ABI Contract v1.0
├── FFI Contract v1.0
├── GPU Profile v1.0
├── Freestanding Profile v1.0
└── Experimental / Future
```

và một **Conflict Resolution Matrix** để nếu hai specification trước đây vô tình mâu thuẫn thì có một quy tắc duy nhất quyết định cái nào thắng, thay vì tiếp tục chồng thêm quyết định mới.