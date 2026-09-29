# BOOTSTRAP-551 — FORMAL SEMANTICS, LANGUAGE SOUNDNESS CONTRACT, MEMORY MODEL, CONCURRENCY MODEL & MACHINE-CHECKABLE LANGUAGE INVARIANTS

**Trạng thái: COMPLETED / LOCKED**

`551` là lớp nền để khóa một nguyên tắc rất quan trọng của Axiom:

> **Mọi tối ưu hóa của compiler chỉ hợp lệ khi bảo toàn semantics đã được định nghĩa rõ ràng.**

Axiom không cần biến toàn bộ compiler thành một theorem prover. Thay vào đó, specification phải định nghĩa đủ chặt để:

- compiler implement được;
- optimizer biết transformation nào hợp lệ;
- backend biết behavior nào phải preserve;
- sanitizer/debugger biết violation nào là gì;
- differential testing có oracle;
- formal verification có thể kiểm tra các phần quan trọng.

---

# 551.1. Semantic hierarchy

Axiom dùng nhiều tầng semantics:

```text id="w9c3h7"
Source Syntax
      ↓
AST
      ↓
HIR
      ↓
Typed Semantic Model
      ↓
MIR
      ↓
LIR / Machine IR
      ↓
Machine Code
      ↓
Native Execution
```

Mỗi tầng có semantic contract riêng.

Không yêu cầu mọi tầng có representation giống nhau.

---

# 551.2. Semantic preservation

Compiler transformation:

```text id="g2m8k4"
Program P
   ↓
Transformation T
   ↓
Program P'
```

hợp lệ nếu:

```text id="v6q1p9"
ObservableBehavior(P)
    =
ObservableBehavior(P')
```

trong phạm vi semantics mà transformation được phép thay đổi.

---

# 551.3. Observable behavior

Observable behavior gồm:

```text id="r4x7n2"
return value
program termination
panic
abort
observable memory effects
volatile effects
atomic effects
I/O
filesystem effects
network effects
process effects
FFI effects
synchronization effects
externally visible timing contracts where explicitly specified
```

Không phải mọi internal detail đều observable.

---

# 551.4. Non-observable implementation detail

Compiler được phép thay đổi:

```text id="k8p3m5"
register allocation
instruction ordering
temporary representation
stack slot placement
internal allocation strategy
dead computation
internal CFG shape
```

nếu không thay đổi behavior được quan sát hợp lệ.

---

# 551.5. Semantic categories

Axiom phân biệt:

```text id="z1v6q4"
Defined
ImplementationDefined
TargetDependent
Unspecified
UndefinedBehavior
InvalidProgram
```

Đây là các trạng thái khác nhau.

---

# 551.6. Defined behavior

Nếu specification định nghĩa behavior:

```text id="f7m2x9"
defined
```

compiler phải preserve behavior.

---

# 551.7. Implementation-defined behavior

Một behavior có thể phụ thuộc implementation nhưng compiler phải công bố lựa chọn.

Ví dụ:

```text id="p3q8k1"
implementation-defined
```

phải xuất hiện trong target/compiler metadata.

---

# 551.8. Target-dependent behavior

Ví dụ:

```text id="x5n9r2"
pointer width
endianness
ABI
atomic capabilities
float capabilities
SIMD width
```

được quyết định bởi TargetSpec `483`.

---

# 551.9. Unspecified behavior

Compiler được chọn trong tập behavior được specification cho phép.

Nhưng compiler không được biến unspecified thành behavior nằm ngoài tập cho phép.

---

# 551.10. Undefined behavior

UB chỉ xuất hiện ở các boundary được specification định nghĩa rõ.

Ví dụ:

```text id="m8k4v1"
invalid raw pointer dereference
invalid alignment
invalid enum representation
violated unsafe invariant
invalid FFI contract
```

Safe Axiom code phải tránh UB trong semantic subset của language.

---

# 551.11. Invalid program

Một chương trình có lỗi compile-time:

```text id="q6p1z8"
type mismatch
unresolved symbol
ownership violation
invalid generic constraint
invalid pattern
```

là:

```text id="u3x7m5"
ill-formed / invalid program
```

không phải UB.

---

# 551.12. Semantic state

Execution state:

```text id="j8m2q4"
State {
    control
    locals
    memory
    resources
    threads
    tasks
    async_states
    external_state
}
```

---

# 551.13. Memory state

Memory semantics được mô hình hóa:

```text id="x4p9k2"
Memory {
    objects
    allocations
    bytes
    initialization
    lifetime
    permissions
    provenance
}
```

Không yêu cầu runtime phải lưu metadata này.

Đây là **semantic model**.

---

# 551.14. Object identity

Mỗi allocated object có semantic identity:

```text id="n7v3m8"
ObjectId
```

Object identity không nhất thiết tồn tại dưới dạng runtime ID.

---

# 551.15. Allocation

Allocation tạo một object/storage region:

```text id="r2k6x9"
allocate(size, align)
    →
Object
```

Lifetime bắt đầu sau allocation thành công và initialization phù hợp.

---

# 551.16. Deallocation

```text id="m5q8p1"
deallocate(object)
```

kết thúc allocation lifetime.

Sau đó access tới object là invalid trừ trường hợp semantics đặc biệt được quy định.

---

# 551.17. Stack lifetime

Stack object có lifetime theo scope/frame semantics.

Compiler được phép stack-promote/heap-promote khi:

```text id="c7x3n5"
observable lifetime semantics
```

được preserve.

---

# 551.18. Initialization semantics

Typed object có state:

```text id="v9p4k2"
Uninitialized
PartiallyInitialized
Initialized
Moved
Destroyed
```

Read chỉ hợp lệ khi giá trị đã được initialize hợp lệ.

---

# 551.19. Partial initialization

Compiler phải track:

```text id="a2m7x8"
field A initialized
field B uninitialized
```

Cleanup chỉ áp dụng cho field đã initialized.

---

# 551.20. Move semantics

Move:

```text id="x8q1m4"
source
   ↓
destination
```

chuyển ownership/value state.

Source không còn usable theo semantics của type.

---

# 551.21. Copy semantics

Copy tạo giá trị độc lập khi type cho phép.

Compiler không được tự biến:

```text id="j3p9v6"
copy
```

thành move nếu điều đó thay đổi observable behavior của destructor/resource ownership.

---

# 551.22. Drop semantics

`drop` là observable khi destructor có side effect.

Compiler chỉ được eliminate/drop reorder khi semantics cho phép.

---

# 551.23. Destruction ordering

Default:

```text id="k4x8n2"
last acquired
    ↓
first destroyed
```

Ordering này là semantic khi destructor effects có thể quan sát.

---

# 551.24. `defer`

`defer` được lower thành cleanup edge.

Ví dụ:

```text id="p7m2q9"
scope
 ├── body
 ├── return
 └── cleanup
```

mọi normal scope exit hợp lệ phải chạy cleanup tương ứng.

---

# 551.25. Panic semantics

Panic là observable termination/failure event.

Hai mode:

```text id="n6v3x8"
panic=abort
panic=unwind
```

---

# 551.26. Unwind semantics

Unwind phải:

```text id="q1k7m4"
destroy initialized resources
run required cleanup
propagate panic
```

Không được bỏ qua destructor có semantic effect.

---

# 551.27. Double panic

Nếu cleanup panic trong quá trình unwind:

```text id="z8p3x5"
→ abort
```

theo `425`.

---

# 551.28. Result semantics

`Result<T,E>` là ordinary value.

```text id="m4x9k1"
Ok(T)
Err(E)
```

Không có hidden exception.

---

# 551.29. `try` lowering

```text id="v6q2n8"
x := try foo()
```

tương đương semantic branching:

```text id="a9p5m3"
match foo() {
    Ok(v) => continue(v)
    Err(e) => return Err(e)
}
```

Optimizer được phép tạo branch machine-level tối ưu hơn.

---

# 551.30. Option semantics

```text id="r3m7x1"
Some(T)
None
```

không tương đương `null`.

Niche optimization được phép nếu representation vẫn preserve semantics.

---

# 551.31. Evaluation order

Axiom phải định nghĩa rõ evaluation order.

Nguyên tắc mặc định:

```text id="c8x2p6"
subexpressions are evaluated in specification-defined order
```

Compiler không được tự reorder hai expression có observable side effects nếu semantics không cho phép.

---

# 551.32. Pure expressions

Expression được đánh dấu pure khi:

```text id="y7n4m2"
no observable side effect
```

Compiler có thể:

- constant-fold;
- CSE;
- reorder;
- eliminate;

nếu không có hidden semantic dependency.

---

# 551.33. Effectful expressions

Ví dụ:

```text id="f1k8q3"
IO
atomic
volatile
allocation
panic
FFI
process
network
filesystem
```

có effects.

Optimizer phải tôn trọng effect ordering.

---

# 551.34. Effect ordering

Nếu:

```text id="x5m2p8"
A → side effect
B → side effect
```

và semantics yêu cầu A trước B:

```text id="z9q4v1"
A
↓
B
```

optimizer không được đổi thành:

```text id="d3k7m6"
B
↓
A
```

---

# 551.35. Integer semantics

Integer operations có explicit modes:

```text id="p8x3r2"
checked
wrapping
saturating
```

Default arithmetic semantics đã khóa từ `430`.

Compiler không được biến checked operation thành wrapping.

---

# 551.36. Signed overflow

Signed overflow trong checked/default operation:

```text id="m7q1x5"
→ defined failure behavior
```

theo operation semantics.

Không tự động coi mọi signed overflow là UB.

---

# 551.37. Wrapping arithmetic

```text id="k2v8n4"
wrapping_add
wrapping_sub
wrapping_mul
```

có semantics modulo rõ ràng.

Optimizer được phép tận dụng modulo semantics.

---

# 551.38. Saturating arithmetic

```text id="r6p3m9"
saturating_add
```

clamps tại giới hạn type.

Không được thay bằng unchecked arithmetic.

---

# 551.39. Floating-point semantics

Axiom phân biệt:

```text id="x4n8q2"
strict
fast
reproducible
```

---

# 551.40. Strict floating point

Strict mode preserve:

- NaN;
- infinity;
- signed zero;
- rounding;
- operation semantics;
- observable exception/status behavior nếu target contract yêu cầu.

---

# 551.41. Fast floating point

Fast mode cho phép transformation như:

```text id="j1m7v5"
reassociation
approximation
FMA contraction
```

chỉ trong phạm vi policy cho phép.

---

# 551.42. Reproducible numeric mode

Có thể yêu cầu:

```text id="z5q2x8"
same target
same inputs
same numeric configuration
→ reproducible result
```

Cross-CPU bitwise reproducibility chỉ được claim khi target/runtime contract đảm bảo.

---

# 551.43. Pointer semantics

Raw pointer có:

```text id="n3p8k6"
address
provenance
alignment
lifetime
access permissions
```

Provenance và numerical address là hai khái niệm khác nhau.

---

# 551.44. Pointer equality

Axiom phân biệt:

```text id="v8m4x1"
pointer identity/equality
```

với:

```text id="c2q7p5"
integer address equality
```

Không được tự interchange.

---

# 551.45. Pointer ordering

Không có universal pointer ordering semantics.

Ordering raw pointers chỉ hợp lệ khi operation/representation contract cho phép.

---

# 551.46. Pointer arithmetic

Pointer arithmetic chỉ hợp lệ trong object/address range được semantics cho phép.

Out-of-range pointer computation phải có semantics rõ ràng và dereference invalid nếu không thuộc valid object.

---

# 551.47. Alignment

Typed access yêu cầu:

```text id="m9x3k7"
address % align(T) == 0
```

Unaligned access phải explicit.

---

# 551.48. Byte reinterpretation

Không được mặc định:

```text id="p2v6n8"
bytes → T
```

là valid.

Cần:

```text id="r7m4x1"
validated representation
```

hoặc unsafe proof.

---

# 551.49. `MaybeUninit`

`MaybeUninit<T>` đại diện storage chưa có valid T.

```text id="k5q9p2"
MaybeUninit<T>
    ≠
T
```

---

# 551.50. Volatile semantics

Volatile operation là observable memory operation.

Compiler:

```text id="x8m3v6"
must not eliminate
must not merge arbitrarily
must preserve required ordering
```

theo target memory/volatile contract.

Volatile không phải synchronization primitive.

---

# 551.51. Atomic semantics

Atomic operations tuân theo:

```text id="n4p7k2"
Relaxed
Acquire
Release
AcqRel
SeqCst
```

---

# 551.52. Data race

Trong safe program subset:

```text id="z1x6m8"
conflicting unsynchronized concurrent accesses
```

phải bị ngăn bởi type/API/concurrency model.

Unsafe code có thể phá invariant và trở thành UB nếu contract bị vi phạm.

---

# 551.53. Memory ordering

Compiler chỉ được reorder atomic operations nếu transformation giữ nguyên allowed memory behaviors.

Không thể coi atomic như ordinary load/store.

---

# 551.54. Sequential consistency

`SeqCst` tạo global ordering semantics theo atomic model.

Compiler/backend phải preserve ordering tương ứng.

---

# 551.55. Thread creation

`spawn` tạo một execution context mới.

Observable effects của child thread chỉ được reorder theo synchronization semantics.

---

# 551.56. Join semantics

```text id="y3m8q2"
spawn
 ↓
child execution
 ↓
join
```

Sau `join`, kết quả/side effects mà memory model quy định phải observable.

---

# 551.57. Detached thread

Detached execution không được tự động giữ ownership của caller resources.

Lifetime phải được biểu diễn bởi runtime/thread abstraction.

---

# 551.58. Task semantics

Task là logical execution unit.

Không đồng nhất với OS thread.

---

# 551.59. Async semantics

```text id="k7p2x9"
async fn
```

được lower thành state machine nhưng observable behavior phải tương đương semantics async.

---

# 551.60. Suspension

Tại:

```text id="v4m8q1"
await
```

state phải được preserve:

```text id="a9x3n6"
locals
control state
pending resources
cleanup state
```

---

# 551.61. Cancellation

Cancellation là semantic event.

Compiler không được coi cancellation giống normal return nếu cleanup/failure semantics khác nhau.

---

# 551.62. Cancellation cleanup

Cancellation phải chạy cleanup cần thiết:

```text id="m2q7x5"
resources acquired before cancellation
        ↓
cleanup
```

---

# 551.63. Async race

Nếu cancellation xảy ra đồng thời completion:

```text id="p8n4k1"
one deterministic state transition
```

phải được chọn theo primitive semantics.

Không được tạo double completion.

---

# 551.64. Channels

Channel semantics gồm:

```text id="x6m3v9"
ordering
capacity
close
send
receive
failure
```

Compiler không được optimize away synchronization.

---

# 551.65. Actor semantics

Actor state mutation được serialized theo actor mailbox semantics.

Compiler không được tự song song hóa actor state mutation nếu điều đó phá ordering.

---

# 551.66. Reactive semantics

Reactive graph có semantic ordering:

```text id="r5q8n2"
input
 ↓
dependency
 ↓
computed
 ↓
effect
```

Optimizer có thể fuse computation nhưng phải preserve event/batch semantics.

---

# 551.67. Workflow semantics

Workflow node:

```text id="z7m2p4"
Pure
Read
Write
External
Irreversible
```

có semantic effects.

Compiler không được reorder irreversible effect qua dependency boundary.

---

# 551.68. Distributed semantics

Distributed execution phải acknowledge:

```text id="c1x6k8"
delay
duplication
reordering
partition
partial failure
clock skew
```

Compiler không được assume reliable ordered network nếu API không guarantee.

---

# 551.69. Time semantics

`474`:

```text id="n8p3v5"
Instant
Duration
Deadline
WallClock
VirtualClock
```

là các semantic types khác nhau.

Optimizer không được thay monotonic clock bằng wall clock.

---

# 551.70. Randomness

Random operation là effectful nếu random state observable.

Compiler không được tự:

```text id="m4x7q1"
duplicate random call
remove random call
reorder random call
```

nếu thay đổi sequence.

---

# 551.71. Deterministic randomness

Seeded PRNG:

```text id="v9q2m5"
same seed
+ same algorithm
+ same sequence
→ same sequence
```

trong stated compatibility scope.

---

# 551.72. Comptime semantics

`431`:

```text id="x3p8n6"
comptime
```

được xem là evaluation trước runtime.

Comptime result phải được semantic-equivalent với declared language semantics.

---

# 551.73. Comptime purity

Core comptime không được tự ý:

```text id="j6m1q9"
network
filesystem
process
```

trừ explicit build-system boundary.

---

# 551.74. Comptime determinism

Cùng:

```text id="r4x8p2"
source
compiler
target configuration
comptime inputs
```

phải cho cùng semantic result trong deterministic mode.

---

# 551.75. FFI semantics

FFI function có semantics được xác định bởi:

```text id="z2q7m5"
ABI
calling convention
layout
ownership
effects
foreign contract
```

---

# 551.76. Foreign uncertainty

Nếu compiler không biết behavior foreign function:

```text id="k8m3x1"
Unknown
```

không được assume pure/no-panic/no-block/no-alloc.

---

# 551.77. FFI panic boundary

Panic không được tự động xuyên FFI.

Boundary phải explicit:

```text id="p5v9q2"
catch
convert
abort
supported unwind ABI
```

---

# 551.78. External I/O

I/O là observable.

Compiler không được eliminate:

```text id="m7x2n4"
file.write(...)
```

chỉ vì return value không được sử dụng.

---

# 551.79. External state

Database/network/filesystem/process đều thuộc external state.

Compiler không được giả định external state immutable trừ khi contract chứng minh.

---

# 551.80. Security semantics

Tích hợp `549`:

```text id="x4q8m6"
trust
taint
secret
capability
authority
security effects
```

Security properties cũng là semantic constraints khi policy yêu cầu.

---

# 551.81. Capability semantics

Nếu function yêu cầu capability:

```text id="v2m7p9"
requires Capability C
```

compiler không được loại bỏ capability check nếu check là semantic requirement.

---

# 551.82. Observable capability use

Việc sử dụng capability có thể là security-relevant effect ngay cả khi API return value không có.

---

# 551.83. Governance semantics

Policy `545` có thể quyết định:

```text id="a8x3k1"
allow
deny
approval
runtime check
```

Nếu policy được bind compile-time, policy trở thành build semantic input.

---

# 551.84. Evidence semantics

`546` evidence không phải program value.

Nhưng claim:

```text id="q6p2m8"
"this property was proven"
```

phải có provenance.

---

# 551.85. Debug semantics

Debug information không được thay đổi normal semantics.

Compiler có thể bỏ debug info trong release.

---

# 551.86. Profiling semantics

Profiling instrumentation phải:

```text id="m9x4v7"
not alter program semantics
```

ngoại trừ explicit profiling mode cho phép observable timing differences.

---

# 551.87. Sanitizer semantics

Sanitizer là diagnostic instrumentation.

Một sanitizer failure không được biến thành semantics của normal release build.

---

# 551.88. Undefined behavior and optimization

Một transformation có thể dựa trên UB **chỉ sau khi semantics xác định operation nằm ngoài defined program domain**.

Compiler không được tự tạo UB để hợp thức hóa optimization.

---

# 551.89. `assume`

`assume(condition)` là explicit semantic promise.

Nếu false:

```text id="j3q8n5"
program exits defined semantic domain
```

Compiler được phép optimize dựa trên assumption.

---

# 551.90. Assertion

`assert(condition)` khác `assume`.

Nếu false:

```text id="x7m2p4"
defined assertion failure
```

Không được coi false assertion là UB.

---

# 551.91. Contract proof

`479` có:

```text id="r8k1v6"
Proven
RuntimeChecked
Unknown
Assumed
Disproven
```

549/551 dùng cùng distinction.

---

# 551.92. Optimization precondition

Mọi optimization có precondition:

```text id="p2m7x9"
OptimizationRule {
    name
    requires
    transforms
    preserves
    invalidates
}
```

---

# 551.93. Example optimization

Constant folding:

```text id="k5x8q1"
x = 2 + 3
```

→

```text id="v9m3p6"
x = 5
```

hợp lệ nếu:

- arithmetic semantics phù hợp;
- không có observable overflow behavior bị thay đổi;
- không có hidden effects.

---

# 551.94. Dead code elimination

DCE chỉ được loại bỏ computation nếu:

```text id="a4q7n2"
no observable result
no required cleanup
no volatile effect
no atomic effect
no external effect
no panic behavior
```

hoặc semantics cho phép elimination.

---

# 551.95. Common subexpression elimination

CSE chỉ hợp lệ khi expression:

```text id="m8x2p5"
pure
or effect-equivalent
```

và alias/memory state không làm thay đổi kết quả.

---

# 551.96. Load elimination

Load có thể eliminate nếu compiler chứng minh:

```text id="z6q1k4"
same object
same initialized state
no intervening write
not volatile
not externally modified
```

---

# 551.97. Bounds-check elimination

Có thể bỏ:

```text id="n3m7x8"
if index < length
```

nếu:

```text id="r5p2q9"
range proof
```

được chứng minh.

Proof phải được lưu metadata.

---

# 551.98. Allocation elimination

Heap allocation có thể loại bỏ khi:

```text id="k9x4m1"
identity not observable
lifetime not externally visible
destructor effects preserved
address not escaped
```

---

# 551.99. Escape analysis

Nếu object:

```text id="v2q8p6"
NoEscape
```

compiler có thể stack/promote/scalar-replace.

Nếu:

```text id="x5m1n7"
ThreadEscape
GlobalEscape
```

phải preserve lifetime/concurrency semantics.

---

# 551.100. Alias analysis

Alias information phải phân biệt:

```text id="c8p3x5"
ProvenNoAlias
PossibleAlias
Unknown
```

Không được coi `Unknown` là `NoAlias`.

---

# 551.101. `noalias`

`noalias` chỉ có hiệu lực khi contract chứng minh hoặc programmer explicit unsafe contract.

Không tự suy luận global noalias từ syntax.

---

# 551.102. Memory SSA

MIR/LIR có Memory SSA để biểu diễn:

```text id="m4x8q2"
MemoryDef
MemoryUse
MemoryPhi
```

Optimizer dùng nó để reason về memory dependencies.

---

# 551.103. CFG semantics

CFG phải preserve reachable control-flow semantics.

Basic block:

```text id="q7p2m9"
Block {
    instructions
    terminator
}
```

---

# 551.104. Terminator semantics

Mỗi block kết thúc bằng:

```text id="x3m6k8"
branch
switch
return
panic
abort
unreachable
invoke/unwind
suspend
```

Không có implicit fall-through semantics trong MIR.

---

# 551.105. SSA semantics

SSA value có một definition.

Phi node đại diện value phụ thuộc predecessor.

Optimizer không được thay phi semantics bằng arbitrary value.

---

# 551.106. Dominance

SSA transformation phải preserve dominance constraints.

Verifier phải kiểm tra:

```text id="r8m3q1"
use dominated by definition
```

trừ special phi semantics.

---

# 551.107. IR verifier

Mỗi IR stage có verifier:

```text id="k1x7p4"
HIR verifier
MIR verifier
LIR verifier
Machine IR verifier
Object verifier
```

---

# 551.108. MIR invariants

MIR verifier kiểm tra tối thiểu:

- valid types;
- valid blocks;
- valid terminators;
- dominance;
- initialization;
- ownership states;
- valid places;
- valid memory operations;
- valid calls;
- valid unwind edges;
- valid async states.

---

# 551.109. Machine IR invariants

Machine verifier kiểm tra:

- valid registers;
- valid register classes;
- legal operands;
- instruction constraints;
- ABI constraints;
- stack alignment;
- clobbers;
- target features.

---

# 551.110. Refinement relation

Mỗi lowering có:

```text id="v6p2n9"
SourceSemantics
      ↓
Refinement
      ↓
TargetSemantics
```

---

# 551.111. Refinement

Refinement không yêu cầu target representation giống source.

Chỉ cần:

```text id="j4x8m1"
Target behavior
⊆
allowed source behavior
```

đối với semantics nondeterministic.

---

# 551.112. Nondeterminism

Một source program có thể có nhiều legal execution do:

- thread scheduling;
- network timing;
- unspecified choices;
- OS behavior.

Compiler không cần giữ một execution cụ thể nếu target vẫn nằm trong allowed behavior set.

---

# 551.113. Undefined source behavior

Nếu source execution enters UB:

```text id="p9m3x6"
compiler has no obligation
```

trong phạm vi UB được specification định nghĩa.

Nhưng compiler không được tự mở rộng UB domain.

---

# 551.114. Safe subset

Axiom định nghĩa một safe semantic subset:

```text id="x5q8k2"
safe code
    →
no invalid typed memory access
no invalid ownership use
no data race through safe APIs
no invalid enum state
```

---

# 551.115. Unsafe subset

Unsafe code được phép biểu diễn low-level behavior nhưng programmer chịu trách nhiệm giữ explicit invariants.

Compiler vẫn kiểm tra:

- syntax;
- types;
- ABI;
- machine legality;
- các rule không bị unsafe tắt.

---

# 551.116. Unsafe does not mean unchecked

```text id="m2x7p4"
unsafe
```

không có nghĩa:

```text id="q9k3v8"
compiler accepts arbitrary invalid syntax/types
```

Nó chỉ mở một số operations bị giới hạn.

---

# 551.117. Semantic metadata

Mỗi semantic node có thể mang:

```text id="v4p8m1"
SemanticId
source_span
type
effects
ownership
contracts
security
provenance
```

Tích hợp `446`.

---

# 551.118. Semantic hash

Một semantic item có:

```text id="k7x2q5"
SemanticHash
```

được tính từ semantic representation, không phụ thuộc whitespace.

---

# 551.119. Semantic equivalence

Hai source representations có thể khác text:

```text id="m3p9x6"
Axiom source A
Axiom source B
```

nhưng cùng semantics trong phạm vi proof.

Compiler không tự tuyên bố equivalence nếu chưa có evidence.

---

# 551.120. Formal semantics representation

Specification nên có hai lớp:

```text id="z8q4m2"
Human-readable normative specification
             +
Machine-readable semantic rules
```

Machine-readable format có thể mô tả:

```text id="x1m7p5"
operation
preconditions
state transition
postconditions
effects
failure
```

---

# 551.121. Semantic rule example

Khái niệm:

```text id="a6p3v9"
ADD_I32(a,b)
requires:
    valid_i32(a)
    valid_i32(b)

result:
    checked(a+b)
```

Không phải source code executable; đây là semantic rule.

---

# 551.122. Transition system

Execution có thể mô hình hóa:

```text id="r5x8k1"
State
  ↓ instruction
State'
```

Ví dụ:

```text id="n2m7q4"
Store(place, value)
```

→ cập nhật memory state.

---

# 551.123. Semantic interpreter

Axiom có reference interpreter cho semantic subset:

```text id="p8x3m6"
AST/HIR/MIR
    ↓
Reference Semantics
    ↓
Result
```

Không phải production VM.

---

# 551.124. Interpreter use

Reference interpreter dùng cho:

- compiler tests;
- differential testing;
- optimization verification;
- fuzzing;
- language specification tests.

---

# 551.125. Optimization validation

Mỗi optimization có thể test:

```text id="q4m9x2"
before
→ reference execution

after
→ reference execution

compare observable behavior
```

---

# 551.126. Translation validation

Compiler không cần formal-prove toàn bộ compiler.

Thay vào đó có thể validate từng compilation:

```text id="z7p1m5"
Input IR
   ↓
Optimization
   ↓
Output IR
   ↓
validator
```

---

# 551.127. Proof-carrying optimization

Optimization có thể đính kèm:

```text id="x5q8m3"
OptimizationEvidence {
    rule
    assumptions
    proof
    source_nodes
    target_nodes
}
```

Không bắt buộc mọi optimization phải có formal proof.

---

# 551.128. Optimization evidence levels

```text id="k2m8p4"
Proven
Checked
Tested
Heuristic
Unknown
```

---

# 551.129. Compiler trust levels

Compiler transformation có thể phân loại:

```text id="v6x1q9"
Semantically verified
Mechanically checked
Test validated
Heuristic
```

AI/tooling có thể xem classification.

---

# 551.130. Miscompilation detection

Nếu:

```text id="p3q7m8"
reference semantics ≠ native result
```

đây là compiler correctness failure.

Compiler phải tạo reduced testcase khi có thể.

---

# 551.131. Differential compiler testing

So sánh:

```text id="m9x4k2"
Stage0
Stage1
Stage2
Reference Interpreter
Alternative backend
```

khi semantics cho phép.

---

# 551.132. Cross-target semantics

Same source:

```text id="z5p2q8"
x86-64
AArch64
WASM
```

phải preserve common language semantics.

Target-specific differences phải nằm trong documented target contract.

---

# 551.133. ABI refinement

ABI lowering phải preserve:

```text id="r8m3x1"
arguments
returns
stack
registers
alignment
callee/caller saved
aggregate representation
```

---

# 551.134. Object semantics

Object file không phải semantics của source nhưng phải preserve relocation/symbol/layout requirements cần cho final artifact.

---

# 551.135. Link semantics

Linker transformation phải preserve:

```text id="k7q2m5"
symbol resolution
relocation
section permissions
entry point
TLS
imports/exports
```

---

# 551.136. Native artifact semantics

Final executable phải satisfy:

```text id="v3p8x6"
target format
ABI
entry contract
runtime contract
security contract
```

---

# 551.137. Semantic compatibility with `484`

Language edition có thể thay đổi syntax/semantics.

Nhưng compiler phải biết:

```text id="x2m7q9"
edition
semantic ruleset
```

để tránh silent reinterpretation.

---

# 551.138. Semantic compatibility with packages

Package metadata phải chứa semantic assumptions relevant tới:

- ABI;
- effects;
- contracts;
- security;
- generic behavior.

---

# 551.139. Semantic compatibility with precompiled generics

Precompiled generic instance chỉ dùng được khi:

```text id="q5p8m2"
compiler ABI compatible
semantic rules compatible
target compatible
required features compatible
```

---

# 551.140. Semantic model and AI

AI có thể query:

```text id="m4x7k1"
what_is_defined_here()
what_is_observable()
why_is_this_optimization_legal()
what_assumption_is_used()
what_undefined_behavior_applies()
what_memory_rule_applies()
what_atomic_order_is_required()
```

---

# 551.141. Formal model and diagnostics

Diagnostic có thể trỏ tới:

```text id="z8p2n5"
semantic rule
invariant
precondition
proof
```

Ví dụ:

```text id="j6m3x9"
MIR-E551102
use of moved value

Rule:
MOVE-USE-001

State:
value = Moved

Required:
value = Owned | Copyable
```

---

# 551.142. Semantic snapshots

Compiler database có:

```text id="r1x7m4"
SemanticSnapshot {
    source_hash
    semantic_hash
    compiler
    edition
    target
}
```

Dùng cho incremental compilation và AI.

---

# 551.143. Semantic regression

Khi compiler thay đổi:

```text id="p8m2q6"
same source
same edition
same target
```

semantic output phải giữ ổn định trừ khi thay đổi được specification cho phép.

---

# 551.144. Semantic golden tests

Có golden tests cho:

```text id="x5q9n1"
AST
HIR
types
ownership
MIR
effects
layout
security
machine IR
```

---

# 551.145. Property-based semantic tests

Ví dụ property:

```text id="k3m8v2"
copy(x)
```

phải preserve x.

Hoặc:

```text id="r7p1x5"
checked_add
```

không được wrap.

---

# 551.146. Metamorphic semantic testing

Các transformation semantics-preserving được dùng làm oracle:

```text id="z2q6m8"
P
→ equivalent P'
```

sau đó:

```text id="m4x9p1"
compile(P)
compile(P')
```

phải có equivalent observable behavior.

---

# 551.147. Concurrency model checking

Subset concurrency có thể model-check:

```text id="v8m3q5"
atomics
mutex
channels
actors
```

với bounded execution.

Không claim exhaustive proof cho production scheduler.

---

# 551.148. Memory model checking

Có thể kiểm tra bounded:

```text id="x1p7m4"
allocation
move
drop
alias
atomic
thread
```

---

# 551.149. Realtime semantic checking

`461` có:

```text id="q6m2n8"
@realtime
```

Compiler có thể verify absence của:

- allocation;
- blocking;
- forbidden locks;
- unbounded operations;
- panic;
- IO;

theo effect metadata.

---

# 551.150. Semantic budgets

Formal checking phải có resource limits:

```text id="k9x4p2"
max_steps
max_memory
max_recursion
max_solver_time
```

Không để compiler bị treo vô hạn vì proof.

---

# 551.151. Incomplete proofs

Nếu checker timeout:

```text id="m3q8x1"
Unknown
```

Không phải:

```text id="p7n2v5"
Safe
```

---

# 551.152. Proof caching

Proof cache key:

```text id="x5m1q9"
semantic_hash
rule_id
compiler_analysis_version
target
policy
```

---

# 551.153. Formal verification boundary

Formal verifier ngoài compiler có thể consume:

```text id="r8p4k2"
semantic IR
contracts
invariants
proof obligations
```

Không cần compiler phải chứa toàn bộ theorem prover.

---

# 551.154. Specification as source of truth

Compiler implementation:

```text id="z6m2x8"
must follow specification
```

không được ngược lại:

```text id="q4p9n1"
implementation defines language semantics
```

---

# 551.155. Spec/compiler divergence

Nếu compiler behavior khác normative specification:

```text id="m7x3k5"
compiler bug
```

trừ trường hợp specification chưa định nghĩa behavior.

---

# 551.156. Semantic change control

Thay đổi semantic rule phải đi qua:

```text id="v1p8q4"
RFC/change record
 ↓
spec update
 ↓
semantic tests
 ↓
compiler implementation
 ↓
compatibility analysis
```

---

# 551.157. Compiler optimization contract

Compiler documentation phải có thể trả lời:

```text id="x8m4p2"
Why was this instruction removed?
Why was this load merged?
Why was this allocation eliminated?
Why was this branch removed?
Why was this check eliminated?
```

---

# 551.158. Optimization explainability

AI query:

```text id="k2q7m9"
why_optimized(node)
why_not_optimized(node)
show_assumptions(node)
show_proof(node)
show_effects(node)
show_alias_evidence(node)
show_range_proof(node)
```

---

# 551.159. No magical optimization

Nếu optimization dựa trên assumption:

```text id="p5m8x1"
assumption must be represented
```

Không được có hidden semantic assumption không thể truy vấn.

---

# 551.160. Security-aware semantics

Security policy có thể biến property thành compilation obligation:

```text id="z3q6m2"
secret !→ network
```

Compiler phải preserve policy semantics nếu policy bind vào artifact.

---

# 551.161. Governance-aware semantics

Governance rules không được âm thầm thay language semantics.

Chúng chỉ thêm:

```text id="m9p4x7"
build obligation
runtime obligation
deployment obligation
```

theo policy.

---

# 551.162. Resource semantics

Memory/CPU/GPU budgets có thể là policy contracts.

Nhưng:

```text id="x5m2q8"
budget target
```

không được tự biến thành absolute performance guarantee nếu platform không deterministic.

---

# 551.163. Timing semantics

Chỉ các API/annotation có explicit timing contract mới được optimizer coi timing là observable semantic requirement.

---

# 551.164. Cache semantics

Cache optimization:

```text id="k7p3m1"
must not change semantic result
```

Cache failure chỉ ảnh hưởng performance/build behavior, không language correctness.

---

# 551.165. Distributed cache semantics

Remote cache:

```text id="v4x8q2"
hit/miss
```

không được ảnh hưởng program semantics.

False hit là build correctness failure.

---

# 551.166. Build-script semantics

Build scripts là external execution.

Compiler phải preserve declared:

```text id="m2q9x5"
inputs
outputs
effects
```

---

# 551.167. Resource loader semantics

Resource loading `469` phải distinguish:

```text id="z8p1m6"
resource identity
filesystem path
memory address
URL
```

Compiler không được collapse các identity này.

---

# 551.168. Media semantics

Media:

```text id="q3m7x9"
PTS
DTS
timebase
clock
frame identity
```

phải được preserve khi compiler/library tối ưu media pipeline.

---

# 551.169. GPU semantics

GPU execution có:

```text id="x6p2m8"
device
queue
stream
event
memory space
synchronization
```

Optimizer không được biến explicit synchronization thành hidden global synchronization hoặc xóa dependency.

---

# 551.170. Tensor semantics

Tensor transformation phải preserve:

```text id="k9m4q1"
shape
dtype
layout
device
alias
numerical policy
```

---

# 551.171. Numerical tolerance

Numerical optimization chỉ được đổi kết quả trong tolerance khi API/numerical policy explicit cho phép.

Không có universal epsilon.

---

# 551.172. LLM semantics

Generation semantics có:

```text id="p7x3m5"
seed
sampling configuration
tokenizer
vocabulary
KV cache
context
stop conditions
```

Compiler/runtime optimization không được silently thay đổi chúng.

---

# 551.173. Agent semantics

Agent actions có:

```text id="z2m8q4"
goal
policy
capability
tool
observation
budget
approval
```

Optimizer không được duplicate irreversible tool calls.

---

# 551.174. Workflow semantics

Durable workflow compiler phải preserve:

```text id="x4p7n1"
checkpoint
retry
idempotency
event identity
compensation
approval
side effects
```

---

# 551.175. Replay semantics

Deterministic replay phải reproduce semantic state transition trong declared scope.

Irreversible external effects mặc định không replay thật.

---

# 551.176. Semantic equivalence for replay

Replay comparison có thể so:

```text id="m8q3x6"
state
events
outputs
effect decisions
```

không nhất thiết machine instructions giống nhau.

---

# 551.177. Formal semantic layers

Axiom specification cuối cùng nên có:

```text id="v5m2k9"
Layer 0 — Lexical
Layer 1 — Syntax
Layer 2 — Static Semantics
Layer 3 — Dynamic Semantics
Layer 4 — Memory Semantics
Layer 5 — Concurrency Semantics
Layer 6 — Effect Semantics
Layer 7 — ABI Semantics
Layer 8 — Target Semantics
Layer 9 — Optimization Semantics
```

---

# 551.178. Semantic dependency rule

Higher layer có thể depend lower layer:

```text id="q7x1m4"
Target
  ↓
ABI
  ↓
Memory
  ↓
Type
  ↓
Syntax
```

nhưng lower layer không được âm thầm phụ thuộc implementation của higher layer.

---

# 551.179. Specification modularity

Formal semantics phải chia module:

```text id="p4m8x2"
semantics/
    lexical
    syntax
    types
    values
    memory
    ownership
    effects
    concurrency
    async
    ffi
    comptime
    abi
    target
    optimization
```

---

# 551.180. Semantic versioning

Semantic rules có version:

```text id="x3q9m7"
SemanticRulesVersion
```

để metadata/artifacts biết chúng được tạo theo semantics nào.

---

# 551.181. Machine-readable semantic schema

Compiler xuất schema:

```text id="k6m2p8"
SemanticRule {
    rule_id
    version
    domain
    inputs
    preconditions
    transition
    outputs
    effects
    failure
    observables
}
```

---

# 551.182. Rule identity

Mỗi normative rule có stable ID:

```text id="z1p7x4"
MOVE-001
DROP-001
MEM-ACCESS-001
ATOMIC-ORDER-001
FFI-ABI-001
PANIC-001
```

Diagnostic và formal tooling dùng cùng identity.

---

# 551.183. Semantic trace

Compiler debug mode có thể produce:

```text id="m8q4x1"
AST
 ↓
HIR
 ↓
MIR
 ↓
optimization rule
 ↓
MIR'
 ↓
machine
```

---

# 551.184. Optimization trace

Ví dụ:

```text id="v2p9m5"
BoundsCheckElimination
assumption:
    0 <= i < 16

evidence:
    loop_range_proof #812

removed:
    bounds_check #144
```

---

# 551.185. Soundness target

Axiom không cần chứng minh toàn bộ compiler formally verified ngay từ phiên bản đầu.

Mục tiêu theo cấp:

```text id="q5x8m2"
Level 1
semantic specification

Level 2
IR verification

Level 3
reference interpreter

Level 4
translation validation

Level 5
formal proof of selected passes

Level 6
formally verified critical compiler components
```

---

# 551.186. Critical components

Ưu tiên formal verification cho:

```text id="m7p3x9"
ownership/drop lowering
bounds-check elimination
alias-sensitive optimization
atomic lowering
ABI lowering
machine encoder
relocation
linker
```

---

# 551.187. Machine encoder correctness

`420/438` machine encoder là trust-critical.

Có thể kiểm tra:

```text id="x4q8m1"
Instruction IR
    ↓
Encoder
    ↓
Bytes
```

bằng decoder/assembler reference hoặc formal model.

---

# 551.188. Linker correctness

Linker phải validate:

```text id="p2m6x9"
relocation target
symbol resolution
section layout
alignment
permissions
entry point
```

---

# 551.189. ABI correctness

ABI lowering golden tests:

```text id="z8q3m5"
Axiom caller
 ↔
C caller
 ↔
foreign implementation
```

---

# 551.190. Soundness evidence

Compiler release có:

```text id="m4x7p2"
SemanticValidationReport {
    compiler
    semantic_rules
    verified_passes
    tested_passes
    known_limitations
}
```

---

# 551.191. Known limitations

Axiom phải ghi rõ:

```text id="v9q2k6"
formal coverage incomplete
dynamic dispatch unknown
FFI behavior external
target-specific limitation
```

Không được biến incomplete coverage thành complete proof.

---

# 551.192. Security integration

`549` có thể consume semantic model để tìm:

```text id="x6m1p8"
taint
authority
secret
unsafe
trust
```

---

# 551.193. Static analysis integration

`478` consume:

```text id="k3p8m4"
CFG
types
effects
ownership
memory SSA
```

Không cần duplicate compiler semantic model.

---

# 551.194. Contract integration

`479` consume:

```text id="q7x2n5"
precondition
postcondition
invariant
proof state
```

và có thể feed optimization evidence.

---

# 551.195. Sanitizer integration

`480` dùng semantic rule để instrument đúng operations và không instrument sai volatile/atomic/unsafe semantics.

---

# 551.196. Performance integration

`450/476/481` có thể map:

```text id="m8p3x1"
machine instruction
→ MIR operation
→ source operation
```

để performance evidence không tách khỏi semantics.

---

# 551.197. AI integration

AI semantic engine có thể truy vấn toàn bộ:

```text id="z5q9m2"
definition
type
layout
ownership
effects
memory rule
concurrency rule
contract
security rule
optimization
ABI
machine mapping
```

---

# 551.198. Ultimate semantic invariant

Axiom phải đảm bảo:

```text id="x3m7p8"
Language Specification
       ↓
Semantic Rules
       ↓
Compiler IR
       ↓
Optimization
       ↓
Machine Code
```

không có một bước nào tự ý thay đổi meaning.

---

# 551.199. Hard invariants

1. Language specification là source of truth.
2. Compiler implementation không tự định nghĩa semantics.
3. AST phải có semantic interpretation.
4. HIR phải preserve source semantics.
5. MIR phải preserve HIR semantics.
6. LIR phải preserve MIR semantics.
7. Machine code phải preserve target semantics.
8. Optimization phải có semantic preconditions.
9. Observable behavior phải được định nghĩa.
10. Non-observable behavior có thể được tối ưu.
11. Defined behavior phải được preserve.
12. Implementation-defined behavior phải được ghi.
13. Target-dependent behavior phải được ghi.
14. Unspecified behavior phải nằm trong allowed behavior set.
15. UB phải được định nghĩa rõ boundary.
16. Invalid program khác UB.
17. Safe program không được phụ thuộc accidental UB.
18. Unsafe program phải giữ explicit unsafe boundary.
19. Unsafe không tắt type checking.
20. Unsafe không tắt syntax checking.
21. Unsafe không tắt ABI validation.
22. Initialization state phải được model.
23. Partial initialization phải được model.
24. Move phải được model.
25. Copy phải được model.
26. Drop phải được model.
27. Destructor ordering phải deterministic theo specification.
28. `defer` phải lower thành cleanup semantics.
29. Cleanup phải chạy trên normal exits.
30. Cleanup phải chạy trên unwind khi required.
31. Double panic phải có semantics.
32. Panic abort phải rõ.
33. Panic unwind phải rõ.
34. Result không được biến thành hidden exception.
35. Option không được biến thành implicit null.
36. Evaluation order phải deterministic theo specification.
37. Pure operation phải có effect contract.
38. Effectful operation phải preserve effect ordering.
39. I/O phải observable.
40. Volatile phải observable.
41. Atomic phải preserve memory ordering.
42. Volatile không phải atomic.
43. Atomic không phải volatile.
44. Data race semantics phải rõ.
45. Safe concurrency API phải preserve race-safety contract.
46. Thread semantics phải rõ.
47. Join semantics phải rõ.
48. Detached semantics phải rõ.
49. Async state phải preserve qua suspension.
50. Cancellation phải có semantic transition.
51. Cancellation phải chạy required cleanup.
52. Channel ordering phải rõ.
53. Channel close semantics phải rõ.
54. Actor mailbox ordering phải rõ.
55. Reactive propagation semantics phải rõ.
56. Workflow effect ordering phải rõ.
57. Distributed nondeterminism phải được model.
58. Network ordering không được assume nếu API không guarantee.
59. Clock semantics phải rõ.
60. Monotonic clock không được thay bằng wall clock.
61. Randomness phải được model là effect khi cần.
62. Comptime semantics phải deterministic trong deterministic mode.
63. Comptime không được tự có external authority.
64. FFI semantics phải có ABI.
65. Unknown FFI behavior không được assume pure.
66. FFI unwind boundary phải explicit.
67. Memory object lifetime phải được model.
68. Pointer provenance phải được model.
69. Pointer address và provenance phải phân biệt.
70. Pointer ordering không được universalize.
71. Alignment phải được preserve.
72. Unaligned access phải explicit.
73. Invalid typed reinterpretation không được tự coi valid.
74. MaybeUninit phải khác T.
75. Zero-bit validity không được assume.
76. Alias information phải có proof state.
77. Unknown alias không phải noalias.
78. `noalias` phải có contract.
79. Memory SSA phải preserve memory dependencies.
80. CFG phải có explicit terminator.
81. SSA definition phải dominate use.
82. Phi semantics phải đúng predecessor.
83. MIR phải có verifier.
84. LIR phải có verifier.
85. Machine IR phải có verifier.
86. Object phải có verifier.
87. Linker phải có verifier.
88. Every lowering phải có semantic refinement contract.
89. Refinement không yêu cầu representation identity.
90. Nondeterministic source cho phép target nằm trong legal behavior set.
91. Compiler không được mở rộng UB domain tùy ý.
92. `assume` khác `assert`.
93. `assert` failure không phải UB.
94. Contract failure phải có semantics.
95. Proven contract có thể tối ưu.
96. Unknown contract không phải proof.
97. Disproven contract phải được báo đúng.
98. Bounds-check elimination phải có range evidence.
99. Allocation elimination phải preserve lifetime/effects.
100. DCE phải preserve observable cleanup.
101. CSE phải preserve effects.
102. Load elimination phải preserve alias semantics.
103. Atomic optimization phải preserve memory model.
104. Floating optimization phải obey numeric policy.
105. Fast-math phải explicit.
106. Reproducible numeric mode phải explicit.
107. Numerical tolerance không được universalize.
108. GPU synchronization phải preserve dependency.
109. Tensor optimization phải preserve shape/dtype/layout/device semantics.
110. Model generation optimization phải preserve decoding semantics.
111. Agent optimization không được duplicate irreversible effect.
112. Workflow optimization phải preserve checkpoint/retry semantics.
113. Replay phải preserve declared state transitions.
114. Security policy có thể trở thành semantic obligation.
115. Capability checks không được silently eliminate.
116. Secret flow constraints phải preserve.
117. Governance policy không được silently alter language semantics.
118. Build policy phải explicit.
119. Semantic rules phải có stable IDs.
120. Semantic rules phải versioned.
121. Semantic metadata phải có semantic hash.
122. Semantic snapshots phải reproducible.
123. Semantic regression phải detectable.
124. Reference interpreter phải tồn tại cho semantic subset.
125. Reference interpreter không phải production VM.
126. Differential testing phải được hỗ trợ.
127. Translation validation phải được hỗ trợ.
128. Optimization evidence phải được machine-readable.
129. Optimization assumptions phải queryable.
130. Compiler không được có hidden optimization assumptions.
131. Formal verification không phải mandatory cho mọi pass.
132. Critical compiler passes phải có verification roadmap.
133. Machine encoder phải có correctness validation.
134. Object writer phải có correctness validation.
135. Linker phải có correctness validation.
136. ABI lowering phải có golden tests.
137. Cross-target semantics phải preserve common language behavior.
138. Target differences phải explicit.
139. Implementation differences không được leak thành undocumented semantics.
140. Compiler bug không được biến thành language rule.
141. Specification change phải có change record.
142. Specification change phải có semantic tests.
143. Edition phải identify semantic rules.
144. Package metadata phải identify semantic assumptions.
145. Precompiled code phải validate semantic compatibility.
146. Security analyzer phải consume semantic metadata.
147. Static analyzer phải consume compiler semantic model.
148. Contract engine phải consume semantic model.
149. Sanitizer phải consume semantic operation identity.
150. Profiler phải map runtime behavior về semantic nodes.
151. Debugger phải map semantic state về source.
152. AI tooling phải query semantic evidence.
153. Semantic unknown phải được preserve.
154. Timeout proof phải là Unknown.
155. Incomplete call graph phải là Unknown.
156. Unknown FFI phải là Unknown.
157. Unknown plugin phải là Unknown.
158. Unknown dynamic dispatch phải là Unknown.
159. Unknown distributed behavior phải được biểu diễn.
160. Formal proof chỉ có hiệu lực trong stated scope.
161. Test evidence không phải formal proof.
162. Runtime evidence không phải static proof.
163. Static proof không phải universal correctness proof.
164. Security proof không phải universal security guarantee.
165. Performance evidence không phải semantic proof.
166. Benchmark không phải correctness proof.
167. Reproducibility không phải correctness proof.
168. Signature không phải correctness proof.
169. Compiler self-check không phải trust root.
170. Semantic model không được yêu cầu runtime metadata.
171. Formal semantics không được bắt buộc VM.
172. Formal semantics không được bắt buộc GC.
173. Formal semantics không được bắt buộc borrow checker.
174. Formal semantics không được làm mất native compilation.
175. Formal semantics không được làm mất zero-cost abstraction.
176. Formal semantics phải hỗ trợ freestanding.
177. Formal semantics phải hỗ trợ unsafe low-level code.
178. Formal semantics phải hỗ trợ FFI.
179. Formal semantics phải hỗ trợ cross compilation.
180. Formal semantics phải hỗ trợ incremental compilation.
181. Semantic rules phải có machine-readable representation.
182. Semantic graph phải support reverse query.
183. Semantic graph phải support provenance.
184. Semantic graph phải support historical reconstruction.
185. Semantic graph phải support optimization explanation.
186. Semantic graph phải support security explanation.
187. Semantic graph phải support ABI explanation.
188. Semantic graph phải support machine mapping.
189. Semantic graph phải support AI query.
190. Semantic validation phải có resource limits.
191. Compiler proof process phải terminate.
192. Compiler không được treo vô hạn vì formal analysis.
193. Formal checking phải có deterministic mode.
194. Proof cache phải có semantic identity.
195. Optimization cache phải có rule identity.
196. Semantic cache phải invalidate khi rule thay đổi.
197. Compiler version phải nằm trong semantic evidence.
198. Language edition phải nằm trong semantic evidence.
199. Target phải nằm trong semantic evidence.
200. **Final invariant:** Axiom phải có một semantic contract đủ chặt để mọi lowering và optimization có thể được xem xét dưới quan hệ bảo toàn semantics; compiler có thể dùng reference semantics, IR verifier, translation validation và formal verification có chọn lọc thay vì phải formal-prove toàn bộ compiler, đồng thời vẫn giữ mục tiêu native, hiệu năng cao, zero-cost abstraction, unsafe low-level programming, FFI, concurrency và self-hosting.

**BOOTSTRAP-551: LOCKED.**

---

# BOOTSTRAP-552 — COMPILER CORRECTNESS ENGINE, TRANSLATION VALIDATION, OPTIMIZATION PROOF, DIFFERENTIAL EXECUTION & MISCOMPILATION FORENSICS

`551` đã định nghĩa **semantics**.

`552` xây dựng hệ thống để thực tế kiểm tra:

> **Compiler có thực sự giữ semantics đó qua hàng trăm optimization và backend transformation hay không?**

Kiến trúc:

```text id="7wq2m9"
                 Axiom Source
                      │
                      ▼
                Reference Semantics
                      │
                      ▼
                    HIR
                      │
                      ▼
                    MIR₀
                      │
             ┌────────┴────────┐
             ▼                 ▼
        Optimizer A       Optimizer B
             │                 │
             ▼                 ▼
           MIR₁              MIR₂
             │                 │
             └────────┬────────┘
                      ▼
              Translation Validator
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       Proven       Tested      Unknown
                      │
                      ▼
               Native Execution
                      │
                      ▼
              Differential Oracle
                      │
              ┌───────┴───────┐
              ▼               ▼
          Equivalent       Mismatch
                              │
                              ▼
                     Miscompilation
                       Forensics
```

`552` sẽ khóa:

- translation validation cho từng optimization;
- semantic equivalence checking;
- SMT/constraint-based checking ở các subset phù hợp;
- randomized differential execution;
- reference interpreter;
- cross-compiler differential testing;
- stage0/1/2 differential testing;
- optimization bisection;
- miscompilation minimization;
- wrong-code forensic report;
- pass provenance;
- machine-code semantic validation;
- backend differential testing;
- CPU emulator/reference execution cho các trường hợp quan trọng;
- fuzzing hướng semantics;
- compiler crash vs wrong-code distinction;
- deterministic reproduction;
- optimization proof cache;
- trusted/untrusted proof evidence;
- và quan trọng nhất: **một optimizer có bug không được âm thầm biến thành "language behavior".**