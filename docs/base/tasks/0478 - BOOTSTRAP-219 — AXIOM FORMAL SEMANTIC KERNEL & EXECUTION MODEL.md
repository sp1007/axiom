# BOOTSTRAP-219 — AXIOM FORMAL SEMANTIC KERNEL & EXECUTION MODEL

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là một trong những task quan trọng nhất của toàn bộ Axiom.

Từ trước tới nay chúng ta đã xác định rất nhiều quy tắc:

- ownership;
- `view` / `mut_view`;
- move/copy/clone;
- Drop;
- async;
- atomic;
- concurrency;
- effects;
- unsafe;
- GPU;
- FFI;
- MIR;
- optimizer.

Nhưng nếu mỗi subsystem tự diễn giải các quy tắc đó thì về lâu dài compiler sẽ xuất hiện **semantic drift**.

Vì vậy 219 khóa một nguyên tắc:

> **Axiom chỉ có một Semantic Kernel. Mọi frontend, verifier, interpreter, optimizer và backend đều phải quy về Semantic Kernel đó.**

---

# 1. Semantic Kernel là gì?

Không phải một thư viện.

Không phải runtime.

Không phải compiler module thông thường.

Nó là tập hợp các quy tắc trả lời chính xác:

> “Một chương trình Axiom có nghĩa gì?”

Kiến trúc:

```text
                    AXIOM SOURCE
                         │
                         ▼
                 ┌───────────────┐
                 │ Frontend      │
                 └───────┬───────┘
                         ▼
                 ┌───────────────┐
                 │ Typed HIR     │
                 └───────┬───────┘
                         ▼
                 ┌────────────────────┐
                 │    AXIOM MIR       │
                 └─────────┬──────────┘
                           │
                    ┌──────▼──────┐
                    │ SEMANTIC    │
                    │ KERNEL      │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         Interpreter    Verifier    Optimizer
              │            │            │
              └────────────┼────────────┘
                           ▼
                     ABI / Backend
```

---

# 2. Ba tầng semantics

Axiom nên phân biệt rõ:

### Tầng 1 — Source Semantics

Những gì programmer nhìn thấy:

```axiom
let x = foo()
x.bar()
```

### Tầng 2 — Core Semantic Model

Chương trình thực sự có nghĩa gì:

```text
Binding
Value
Place
Ownership
Capability
Effect
Control Flow
```

### Tầng 3 — Machine Semantics

Compiler thực hiện nó bằng:

```text
register
stack
memory
instruction
calling convention
```

Điểm cực kỳ quan trọng:

> **Tầng 3 không được thay đổi Tầng 2.**

---

# 3. Semantic state

Định nghĩa trạng thái chương trình:

```text
State =
{
    Store
    Heap
    Environment
    Control
    Effects
    ExecutionContext
}
```

Trong đó:

```text
Environment
    name → binding

Store
    place → value/state

Heap
    storage identity → storage

Control
    current execution point

Effects
    observable external state

ExecutionContext
    thread/task/device/etc.
```

Nhưng đây là **semantic model**, không phải yêu cầu runtime phải có các object tương ứng.

Compiler hoàn toàn có thể biến chúng thành:

```text
register
SSA value
stack slot
memory
```

---

# 4. Value

Một `Value` là semantic data.

Ví dụ:

```text
42 : i32
true : bool
Point { x: 1, y: 2 }
```

Value không đồng nghĩa với:

```text
memory block
```

Một value có thể được biểu diễn bằng:

```text
register
stack
constant
immediate
memory
multiple registers
```

Do đó:

> **Value identity ≠ memory identity.**

---

# 5. Place

`Place` là vị trí có thể chứa một value.

Ví dụ:

```axiom
let p = Point { x: 10, y: 20 }
```

Các place:

```text
p
p.x
p.y
```

MIR:

```text
Place(
    base = Local(p),
    projection = [Field(x)]
)
```

Array:

```text
a[3]
```

là:

```text
base + Index(3)
```

---

# 6. Place ≠ address

Đây là một distinction rất quan trọng.

```text
Place
```

là semantic location.

```text
Address
```

là machine location.

Ví dụ compiler có thể giữ:

```text
p.x → register X
```

mà không tồn tại memory address cho `p.x`.

Do đó:

> Không được định nghĩa semantics của Axiom dựa trên địa chỉ vật lý.

Điều này cho phép:

- SSA;
- scalar replacement;
- register allocation;
- struct field promotion;
- allocation elimination.

---

# 7. Storage

Storage là nơi chứa data khi representation yêu cầu.

Các domain:

```text
REGISTER
STACK
INLINE
HEAP
STATIC
TLS
ARENA
POOL
DEVICE
EXTERNAL
```

Nhưng:

```text
semantic value
```

không bị gắn cứng vào một storage domain.

Compiler có thể chuyển:

```text
STACK → REGISTER
HEAP → STACK
STACK → HEAP
```

nếu không phá observable semantics.

---

# 8. Ownership state machine

Ownership được formalize thành:

```text
UNINITIALIZED
     │
     ▼
   OWNED
   │   │
   │   ├──── Copy ────► OWNED
   │   │
   │   ├──── Move ────► MOVED
   │   │
   │   ├──── Drop ────► DROPPED
   │   │
   │   └──── Partial Move
   │                  │
   │                  ▼
   │             PARTIALLY_MOVED
   │
   └──── Reinitialize ──► OWNED
```

Các transition bất hợp lệ:

```text
MOVED → Read
DROPPED → Read
DROPPED → Move
MOVED → Drop
```

trừ khi semantic model quy định explicit reinitialization trước.

---

# 9. Copy semantics

Nếu:

```axiom
let b = a
```

và `a` có `Copy`:

```text
a ──Copy──► b
```

Semantic result:

```text
a = valid
b = valid
```

Nhưng physical compiler có thể:

```text
a và b → cùng một register
```

nếu lifetime không overlap hoặc value propagation cho phép.

Vì vậy:

> Copy là semantic duplication, không phải `memcpy`.

---

# 10. Move semantics

Nếu không Copy:

```axiom
let b = a
```

thì:

```text
a ──Move──► b
```

Sau transition:

```text
a = MOVED
b = OWNED
```

Không yêu cầu physical memory copy.

Compiler có thể chỉ chuyển:

```text
SSA ownership
```

từ `a` sang `b`.

---

# 11. Clone semantics

```axiom
let b = a.clone()
```

khác hoàn toàn:

```text
Copy
Move
```

Clone là một semantic operation có thể:

- allocate;
- copy deep data;
- execute arbitrary code;
- fail nếu API quy định;
- có effect.

Do đó optimizer chỉ được eliminate Clone khi chứng minh observable-equivalence.

---

# 12. Capability semantics

Capability là quyền truy cập.

Các capability cơ bản:

```text
READ
WRITE
MOVE
DROP
```

`view<T>`:

```text
READ
```

`mut_view<T>`:

```text
READ + WRITE
```

nhưng với exclusive access.

---

# 13. Capability formal state

Một capability có:

```text
Capability {
    provenance
    region
    access
    lifetime
    storage_domain
    execution_domain
}
```

Ví dụ:

```text
view<Point>
```

có:

```text
provenance = p
region     = whole(Point)
access     = READ
```

---

# 14. Region algebra

Region quan hệ:

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
p.x
p.y
```

compiler chứng minh:

```text
DISJOINT
```

nhưng:

```text
p
p.x
```

là:

```text
CONTAINS
```

---

# 15. Capability conflict rule

Hai capability conflict nếu:

```text
AccessConflict(A, B)
AND
MayOverlap(A.region, B.region)
```

Bảng:

| A | B | Conflict |
|---|---|---|
| READ | READ | Không |
| READ | WRITE | Có |
| WRITE | READ | Có |
| WRITE | WRITE | Có |
| MOVE | READ | Có |
| MOVE | WRITE | Có |
| DROP | READ | Có |
| DROP | WRITE | Có |

Nếu:

```text
MayOverlap = UNKNOWN
```

thì safe compiler **không được giả định disjoint**.

---

# 16. Owner và capability

Owner:

```text
p : OWNED
```

tạo:

```text
view(p)
```

thì:

```text
p = OWNED
cap = READ
```

Nhưng:

```text
drop(p)
```

không hợp lệ nếu capability còn sống.

Semantic rule:

```text
Destroy(owner)
requires
NoLiveDependentCapability(owner)
```

---

# 17. Capability lifetime

Không dùng lifetime annotation trong source.

Semantic lifetime được xác định bởi:

```text
first capability creation
        ↓
all uses
        ↓
last use
        ↓
capability dead
```

Compiler có thể shorten lifetime.

Ví dụ:

```axiom
let v = view(x)
print(v)
do_other_work()
```

Compiler có thể kết luận `v` chết ngay sau `print`.

---

# 18. Evaluation order

Axiom cần một evaluation order deterministic.

Nguyên tắc:

> **Không được để optimizer biến một chương trình deterministic thành chương trình có observable order khác.**

Ví dụ:

```axiom
foo(a(), b())
```

phải có thứ tự evaluation được Core quy định rõ.

Đề xuất:

```text
callee
→ arguments từ trái sang phải
→ call
```

Điều này giúp:

- Drop;
- IO;
- atomic;
- panic;
- unsafe;
- debugging

đều có semantics rõ.

---

# 19. Expression semantics

Mọi expression có:

```text
Expression
    ↓
Value
```

hoặc:

```text
Divergence
```

Ví dụ:

```text
panic()
```

có:

```text
type = never
```

và không tạo normal continuation.

---

# 20. `never`

`never` đại diện computation không trở lại bình thường.

Ví dụ:

```axiom
fn fail() -> never {
    panic("x")
}
```

Control-flow:

```text
Call fail
   ↓
NO NORMAL SUCCESSOR
```

Điều này rất hữu ích cho:

- CFG;
- exhaustiveness;
- optimizer;
- dead code elimination.

---

# 21. Block semantics

Block:

```axiom
{
    statement1
    statement2
    expression
}
```

có semantic value của expression cuối.

Ví dụ:

```axiom
let x = {
    let a = 10
    a + 20
}
```

→ `x = 30`.

Nếu block kết thúc bằng statement không trả value:

```text
unit
```

---

# 22. Control-flow semantics

MIR sử dụng CFG.

Các terminator cơ bản:

```text
Goto
Branch
Switch
Call
Return
Panic
Unreachable
Await
Yield
```

Mỗi basic block có:

```text
zero or more statements
exactly one terminator
```

---

# 23. Return semantics

Khi:

```axiom
return value
```

semantic execution:

```text
evaluate value
↓
transfer ownership/result
↓
execute required cleanup
↓
return to caller
```

Drop không được bỏ qua chỉ vì `return`.

---

# 24. Panic semantics

Panic là control-flow divergence hoặc exceptional control-flow tùy profile.

Profile:

```text
abort
```

thì:

```text
panic
 ↓
terminate
```

Profile:

```text
unwind
```

thì:

```text
panic
 ↓
cleanup
 ↓
unwind
```

Nhưng semantic invariant chung:

> Resource obligations không được bị bỏ qua.

---

# 25. Drop semantics

Drop được formalize như semantic cleanup.

Ví dụ:

```text
scope exit
```

tạo:

```text
Drop(local_3)
Drop(local_2)
Drop(local_1)
```

theo destruction order.

Compiler có thể optimize physical cleanup nhưng phải bảo toàn observable Drop effects.

---

# 26. Drop và optimizer

Nếu:

```text
Drop(T)
```

hoàn toàn không observable và storage không cần cleanup thật sự:

compiler có thể eliminate physical operation.

Nhưng nếu Drop:

```text
close(fd)
```

thì đó là:

```text
Effect = ExternalIO
```

và không được loại bỏ.

---

# 27. Function call semantics

Function call:

```text
Call(f, args)
```

bao gồm:

```text
evaluate callee
evaluate arguments
transfer required ownership/capabilities
execute body
produce result
restore caller state
```

ABI implementation có thể khác nhưng semantic sequence không đổi.

---

# 28. Effects

Mỗi operation có effect set.

Ví dụ:

```text
pure arithmetic
    {}

read memory
    {Read}

write memory
    {Write}

malloc-like operation
    {Allocate}

file.write()
    {Write, IO}

atomic.store()
    {Atomic, Synchronize?}
```

Effect set phục vụ optimizer và verifier.

---

# 29. Observable behavior

Đây là định nghĩa quan trọng cho compiler correctness.

Observable behavior gồm:

```text
Return value
Result
Panic/termination
External IO
Volatile access
Atomic behavior
Synchronization behavior
Foreign calls
Program-visible timing contracts when explicitly semantic
```

Không bao gồm mặc định:

```text
register allocation
stack address
instruction count
temporary allocation
internal SSA shape
```

---

# 30. Semantic equivalence

Hai chương trình:

```text
P
Q
```

semantic-equivalent nếu với mọi input hợp lệ và execution environment hợp lệ:

```text
Observable(P) = Observable(Q)
```

trong phạm vi semantics được định nghĩa.

Đây là nền tảng cho:

- optimizer;
- inlining;
- vectorization;
- allocation elimination;
- generic specialization;
- devirtualization.

---

# 31. Optimization rule

Optimizer chỉ được phép thực hiện:

```text
P → Q
```

nếu:

```text
Semantics(P) = Semantics(Q)
```

hoặc Q là implementation refinement được Core cho phép.

Ví dụ:

```text
Copy
```

có thể biến thành register reuse.

Nhưng:

```text
IO
```

không thể bị loại bỏ chỉ vì compiler thấy return value không được dùng.

---

# 32. Atomic semantics

Atomic operation không chỉ là memory read/write.

Ví dụ:

```axiom
atomic.store(x, 1, Release)
```

có:

```text
Value effect
+
Synchronization semantics
```

Semantic Kernel phải định nghĩa:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

và:

```text
happens-before
synchronizes-with
sequenced-before
```

---

# 33. Data race

Safe program không được có:

```text
conflicting concurrent non-atomic accesses
```

Semantic Kernel định nghĩa race ở mức:

```text
access
+
region
+
execution domain
+
ordering
```

không phải chỉ nhìn instruction.

---

# 34. Async semantics

`await` là một semantic suspension point.

```text
Running
   ↓
Evaluate Future
   ↓
Ready ─────────────→ Continue
   │
   └── Pending → Suspend
```

Mỗi suspension:

```text
SuspensionPointId
```

Compiler xác định state live tại điểm đó.

---

# 35. View across await

Ví dụ:

```axiom
async fn foo(x: mut_view<Data>) {
    await_something().await
    x.modify()
}
```

không mặc nhiên hợp lệ.

Compiler phải chứng minh execution/storage contract cho capability.

Nếu không:

```text
REJECT
```

Trong trường hợp an toàn, programmer không phải viết lifetime annotation.

---

# 36. Thread semantics

`spawn` không phải Core operation về scheduling.

Core chỉ định nghĩa:

```text
execution domain
+
Send
+
Share
+
synchronization
```

Library quyết định:

```text
OS thread
worker pool
fiber
task scheduler
```

---

# 37. Send semantics

Nếu:

```text
T : Send
```

thì ownership của `T` có thể chuyển execution domain.

Không đồng nghĩa:

```text
T : Share
```

và cũng không đồng nghĩa:

```text
T thread-safe mutable
```

---

# 38. Share semantics

`Share` cho phép concurrent access theo contract.

Ví dụ:

```text
Arc<T>
```

không tự biến:

```text
T
```

thành mutable thread-safe object.

Cần:

```text
Mutex<T>
RwLock<T>
Atomic<T>
```

hoặc abstraction tương đương.

---

# 39. Unsafe semantics

Đây là một điểm tôi muốn khóa rất rõ.

`unsafe` **không tạo ra một semantics khác**.

Nó chỉ cho programmer thực hiện operation mà compiler không thể tự chứng minh.

Ví dụ:

```text
integer → raw pointer
raw pointer → view
MMIO
pointer arithmetic
```

Unsafe có thể establish:

```text
TrustedPrecondition
```

sau đó safe verifier tiếp tục hoạt động.

Không có:

```text
unsafe = compiler turns off all checks
```

---

# 40. Foreign call semantics

FFI:

```text
extern "C" fn(...)
```

là một semantic boundary.

Nếu không có contract đầy đủ, compiler phải conservative:

```text
MayRead
MayWrite
MayEscape
MayPanic
MayBlock
MaySynchronize
MayCallBack
```

Không được tự đoán FFI purity.

---

# 41. Comptime semantics

Comptime cũng phải chạy cùng Semantic Kernel.

Điểm khác:

```text
ExecutionDomain = Compiler
```

và external capabilities bị giới hạn.

Do đó:

```text
comptime ownership
comptime Drop
comptime capability
```

vẫn phải tuân semantic rules.

---

# 42. GPU semantics

GPU không có semantic model riêng biệt hoàn toàn.

Nó kế thừa:

```text
Value
Place
Ownership
Capability
Region
Atomic
Effect
```

nhưng thêm:

```text
ExecutionDomain = GPU
StorageDomain = Device/Shared/Local/...
```

Điều này giúp compiler tránh tạo một “ngôn ngữ GPU thứ hai”.

---

# 43. Semantic Kernel → MIR

MIR phải là representation đủ mạnh để biểu diễn Semantic Kernel.

Bộ operation tối thiểu:

```text
Use
Copy
Move
Assign
Cast
Bitcast

Load
Store

MakeView
MakeMutView

Call
Return

Drop

Borrow/CreateCapability
ReleaseCapability

AtomicLoad
AtomicStore
AtomicRMW

Branch
Switch
Goto

Await
Panic
Unreachable
```

Không nhất thiết tất cả phải tồn tại như một opcode riêng; một số có thể là semantic annotations.

---

# 44. Reference interpreter

`ax-ref` phải interpret MIR theo semantic rules, không theo LLVM.

Ví dụ:

```text
MIR
 ↓
Semantic evaluation
 ↓
State transition
```

Điều này cho phép phát hiện:

```text
Compiler bug
LLVM bug
Optimization bug
ABI bug
```

bằng differential testing.

---

# 45. Small-step semantics

Axiom Core nên được formalize theo transition:

```text
⟨Program, State⟩
        →
⟨Program', State'⟩
```

Ví dụ Move:

```text
⟨Move(a → b), State⟩
        →
⟨Continue, State[a = MOVED, b = old(a)]⟩
```

Drop:

```text
⟨Drop(x), State⟩
        →
⟨Continue, State[x = DROPPED]⟩
```

Branch:

```text
⟨Branch(true, bb1, bb2), State⟩
        →
⟨bb1, State⟩
```

---

# 46. Determinism

Với cùng:

```text
Source
CompilerVersion
Target
BuildInputs
```

semantic compilation phải deterministic.

Đặc biệt:

```text
name resolution
type inference
trait resolution
ownership
capability verification
pattern matching
comptime deterministic mode
```

không được phụ thuộc:

```text
hash-map iteration
thread scheduling
agent behavior
```

---

# 47. Semantic error hierarchy

Kernel phải phân biệt:

```text
SyntaxError
ResolutionError
TypeError
TraitError
OwnershipError
CapabilityError
EffectError
ConcurrencyError
ComptimeError
FFIContractError
GPUConstraintError
```

Không dùng:

```text
CompilerError: something went wrong
```

cho semantic rejection.

---

# 48. Compiler correctness boundary

Khóa boundary:

```text
Source
  ↓
Parsing correctness
  ↓
Typed HIR correctness
  ↓
MIR lowering correctness
  ↓
Verification correctness
  ↓
       ★
 VERIFIED MIR
       ★
  ↓
Optimization correctness
  ↓
ABI lowering correctness
  ↓
Code generation correctness
```

Mỗi boundary có test oracle riêng.

---

# 49. Formal semantic kernel không cần formalize toàn bộ compiler

Đây là điểm quan trọng để tránh overengineering.

Không cần formal proof ngay cho:

```text
register allocator
instruction scheduler
cache heuristic
inlining heuristic
```

Trước tiên formalize phần:

```text
Core execution
ownership
capability
drop
effects
control flow
concurrency primitives
async
atomic
```

Optimizer dùng:

```text
semantic equivalence
+
pass invariants
+
translation validation
```

thay vì cần chứng minh toàn compiler bằng theorem prover.

---

# 50. Semantic Kernel files

Đề xuất cấu trúc specification:

```text
docs/spec/
├── semantic/
│   ├── axioms.md
│   ├── state.md
│   ├── values.md
│   ├── places.md
│   ├── storage.md
│   ├── ownership.md
│   ├── capabilities.md
│   ├── regions.md
│   ├── evaluation.md
│   ├── control-flow.md
│   ├── drop.md
│   ├── effects.md
│   ├── concurrency.md
│   ├── atomics.md
│   ├── async.md
│   ├── unsafe.md
│   ├── ffi.md
│   ├── comptime.md
│   ├── gpu.md
│   └── equivalence.md
```

Đây trở thành **Semantic Kernel Specification**.

---

# 51. Một thay đổi tư duy quan trọng

Từ giờ không nên nói:

> “Compiler có thể làm X.”

mà cần phân biệt:

### Semantic guarantee

```text
Axiom guarantees X
```

### Compiler optimization

```text
Compiler may implement X efficiently
```

### Implementation detail

```text
Current compiler happens to do X
```

Ví dụ:

> `Box<T>` có nhất thiết phải heap allocate?

**Không.**

Semantic guarantee chỉ là:

```text
owned dynamic-storage abstraction
```

Nếu address không observable, compiler có thể eliminate allocation.

---

# 52. Ba loại invariant

Mỗi Axiom feature từ giờ nên có ba tầng:

### Semantic invariant

Programmer-visible.

### Verification invariant

Compiler phải chứng minh.

### Optimization invariant

Optimizer được phép dựa vào.

Ví dụ `mut_view`:

```text
Semantic:
    mutable exclusive access

Verification:
    overlapping WRITE capability rejected

Optimization:
    proven disjoint regions may become NO_ALIAS
```

Đây là cách tránh việc optimization accidentally trở thành semantics.

---

# 53. Semantic Kernel và AI

Điều này đặc biệt phù hợp với mục tiêu AI-friendly của bạn.

AI có thể hỏi:

```text
WhyMove?
WhyBorrow?
WhyConflict?
WhyNotSend?
WhyAllocation?
WhyAwaitRejected?
WhyNoVectorization?
```

Compiler trả:

```text
Semantic fact
↓
Proof chain
↓
Source spans
↓
Relevant invariant
```

Ví dụ:

```text
ERROR AOWN-23

value `buffer` was moved here

Proof:
    buffer → Move → send_channel

Later use:
    buffer[0]

Ownership state:
    buffer = MOVED

Suggested action:
    use the returned ownership value
```

Không cần AI “suy luận” semantic bằng cách đọc compiler output mơ hồ.

---

# 54. Các invariant mới

Khóa:

```text
ASEM-20
Axiom has one normative semantic kernel.

ASEM-21
All executable language constructs have a defined semantic transition.

ASEM-22
Place identity is distinct from machine address identity.

ASEM-23
Value semantics are independent of physical representation.

ASEM-24
Ownership transitions are explicit in semantic MIR.

ASEM-25
Capability validity is defined independently of optimization.

ASEM-26
UNKNOWN alias/region information cannot establish safe disjointness.

ASEM-27
Observable effects constrain semantic-preserving optimization.

ASEM-28
Reference interpretation follows Semantic Kernel rules directly.

ASEM-29
Optimizations must preserve observable semantic behavior.

ASEM-30
Unsafe establishes explicit trusted preconditions rather than disabling verification.

ASEM-31
Comptime uses the same core semantic rules under a restricted execution domain.

ASEM-32
GPU execution extends the semantic model rather than replacing it.

ASEM-33
FFI boundaries require explicit semantic contracts.

ASEM-34
Semantic compilation is deterministic for identical semantic inputs.

ASEM-35
Semantic errors are never resolved by heuristic inference.

ASEM-36
Backend implementation details cannot redefine Core semantics.

ASEM-37
Runtime representation is not part of Core semantics unless explicitly observable.

ASEM-38
Semantic equivalence is the authority for optimization correctness.
```

---

# 55. Tình trạng kiến trúc sau 219

Hiện tại Axiom đã có:

```text
Language Design             ✓
Memory Model                ✓
Ownership                   ✓
Capability                  ✓
Concurrency                 ✓
Async                       ✓
GPU                         ✓
Comptime                    ✓
Type System                 ✓
Traits                      ✓
MIR                         ✓
Verification                ✓
Optimization                ✓
ABI                         ✓
Backend                     ✓
Object/Linker               ✓
Runtime                     ✓
Package                     ✓
Testing                     ✓
Tooling                     ✓
Security                    ✓
FFI                         ✓
Surface Syntax              ✓
Formal Semantic Kernel      ✓
```

Nói cách khác:

> **Phần “Axiom nên có nghĩa gì?” hiện đã đủ để chuyển sang giai đoạn “Axiom compiler phải implement nó như thế nào?”.**

---

# BOOTSTRAP-220 — tiếp theo

Bước tiếp theo nên là:

## **BOOTSTRAP-220 — AXIOM COMPILER INTERNAL API & DATA MODEL**

Đây sẽ là bước cực kỳ thực dụng.

Ta sẽ khóa **cấu trúc dữ liệu thật bên trong compiler**, không còn chỉ nói khái niệm:

```text
CompilerDB
SourceDB
SyntaxDB
TypeDB
TraitDB
HIRDB
MIRDB
LayoutDB
AbiDB
ComptimeDB
DiagnosticDB
CodegenDB
BuildDB
```

và chính xác hóa:

```text
TypeId
FunctionId
LocalId
Place
Operand
RValue
Statement
Terminator
BasicBlock
RegionId
CapabilityId
EffectSet
TraitGoal
GenericInstance
Layout
AbiSignature
SourceSpan
Diagnostic
Fingerprint
```

Đồng thời sẽ quyết định **memory representation của chính compiler**, incremental query model, interning, arena, generational IDs, serialization `.axdb`, parallel compilation và API giữa các AI agent/compiler subsystem.

Đây là bước cuối cùng trước khi có thể viết một **`AXIOM-COMPILER-IMPLEMENTATION-SPEC`** đủ chi tiết để agent bắt đầu tạo source code compiler thay vì tiếp tục thiết kế kiến trúc.