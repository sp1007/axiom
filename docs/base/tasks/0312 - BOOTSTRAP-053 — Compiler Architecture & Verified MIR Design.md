Tiếp tục.

# BOOTSTRAP-053 — Compiler Architecture & Verified MIR Design

Mục tiêu của 053 là khóa **kiến trúc compiler thực tế**, đặc biệt là MIR. Đây là điểm chuyển từ thiết kế ngôn ngữ sang thiết kế một compiler có thể xây dựng được.

Nguyên tắc trung tâm:

> **AST/HIR biểu diễn ý định của programmer. MIR biểu diễn semantics đã được resolve. Verified MIR biểu diễn chương trình mà compiler đã chứng minh thỏa các invariant của Axiom.**

Sau Verified MIR, các tầng dưới **không được tự diễn giải lại semantics của ngôn ngữ**.

---

# 1. Kiến trúc compiler tổng thể

Kiến trúc được freeze như sau:

```text
Source
  │
  ▼
Lexer
  │
  ▼
Parser
  │
  ▼
AST
  │
  ▼
Module / Name Resolution
  │
  ▼
HIR
  │
  ▼
Typed HIR
  │
  ├──────────────► Trait Solver
  │
  ├──────────────► Comptime / Reflection
  │
  └──────────────► Generic Resolution
  │
  ▼
MIR Construction
  │
  ├──────────────► Closure Lowering
  ├──────────────► Pattern Lowering
  ├──────────────► Async Lowering
  └──────────────► GPU / FFI Legality
  │
  ▼
Semantic Verification
  │
  ├── Ownership
  ├── Capability
  ├── Drop
  ├── Send / Share
  ├── Concurrency
  ├── Async
  ├── GPU
  └── FFI
  │
  ▼
Drop Elaboration
  │
  ▼
Verified MIR
  │
  ▼
Semantic Optimization
  │
  ▼
Representation / Layout
  │
  ▼
ABI MIR
  │
  ▼
Axiom LIR
  │
  ▼
Machine IR
  │
  ▼
Register Allocation
  │
  ▼
Machine Encoding
  │
  ▼
Object
  │
  ▼
Link
  │
  ▼
Native Artifact
```

---

# 2. AST không phải semantic representation

AST chỉ cần giữ cấu trúc source.

Ví dụ:

```axiom
let x = foo(a + b)
```

AST có thể là:

```text
Let
 ├─ name: x
 └─ initializer
     └─ Call
         ├─ foo
         └─ Add
             ├─ a
             └─ b
```

AST **không nên** chứa:

- ownership state
- resolved DeclarationId
- trait candidate
- ABI
- machine layout
- register
- capability provenance

Nếu nhồi tất cả vào AST, compiler sẽ rất khó bảo trì.

---

# 3. HIR — High-level semantic structure

HIR bắt đầu mang semantic identity.

Ví dụ:

```text
Call {
    callee: DeclarationId(42)
    args: [
        ...
    ]
}
```

Tên `foo` đã được resolve thành declaration cụ thể.

HIR cũng có:

```text
TypeId
GenericParamId
TraitId
FieldId
VariantId
LocalId
```

---

# 4. Typed HIR

Typed HIR là nơi mọi expression đã có type.

Ví dụ:

```text
a + b
```

sau trait resolution có thể trở thành:

```text
Add::add(a, b)
```

hoặc compiler intrinsic:

```text
I32Add(a, b)
```

Backend không cần biết vì sao.

---

# 5. Declaration identity

Compiler không dùng string làm identity.

```text
"foo"
```

chỉ là source spelling.

Identity:

```text
PackageId
ModuleId
DeclarationId
```

được dùng xuyên compiler.

Điều này đã thống nhất với 047.

---

# 6. MIR là semantic execution representation

MIR không còn phản ánh syntax trực tiếp.

Ví dụ:

```axiom
let x = foo(a + b)
```

có thể thành:

```text
bb0:
    t0 = Add(a, b)
    t1 = Call foo(t0)
    x  = Move(t1)
    Return
```

MIR phải biểu diễn:

- values
- places
- control flow
- calls
- memory access
- ownership transitions
- capability operations
- Drop
- allocation
- async suspension
- atomics
- volatile
- panic edges

---

# 7. MIR dùng Place thay vì chỉ Value

Đây là một quyết định quan trọng.

```text
Value
```

và:

```text
Place
```

khác nhau.

Ví dụ:

```axiom
user.name
```

có thể là:

```text
Place {
    base: Local(user)
    projection: Field(name)
}
```

Trong khi:

```text
user.name + 1
```

tạo một Value.

---

# 8. Place projection

MIR hỗ trợ projection:

```text
Local
 ├─ Field
 ├─ Index
 ├─ Deref
 └─ Slice/View projection
```

Ví dụ:

```text
user.address.city
```

thành:

```text
Local(user)
  → Field(address)
  → Field(city)
```

Ownership/capability verifier hoạt động trên Place.

---

# 9. Local state

Mỗi local có semantic state:

```text
UNINIT
INIT
MOVED
PARTIALLY_MOVED
DROPPED
```

Ví dụ:

```text
let x = Resource()
let y = x
```

MIR:

```text
x = Resource()
y = Move(x)
```

Verifier:

```text
x → MOVED
y → INIT
```

---

# 10. MIR basic block

MIR dùng CFG:

```text
BasicBlock
    statements*
    terminator
```

Terminator gồm:

```text
Goto
Branch
Switch
Call
Return
Unreachable
Panic
Suspend
```

Có thể bổ sung:

```text
Invoke
```

nếu panic/unwind profile cần explicit exceptional edge.

---

# 11. Call trong MIR

Call không chỉ là:

```text
call foo
```

mà mang semantic information:

```text
Call {
    callee
    args
    destination
    unwind
}
```

Ownership verifier biết:

```text
argument #0 = Move
argument #1 = Read
```

Capability verifier biết:

```text
argument #2 = WRITE capability
```

---

# 12. MIR AccessKind

Chuẩn hóa:

```text
READ
WRITE
MOVE
DROP
BORROW_VIEW
BORROW_MUT_VIEW
```

Trong đó `BORROW` ở đây là **compiler-internal semantic operation**, không phải programmer-facing borrow syntax.

Điều này cực kỳ quan trọng.

Axiom vẫn không cần:

```text
&x
&mut x
'a
```

trong safe source.

---

# 13. View trong MIR

Ví dụ:

```axiom
let v = view(data)
```

có thể lower thành:

```text
v = MakeView {
    owner: data,
    region: Whole(data),
    access: READ
}
```

Sau verification, representation có thể chỉ còn:

```text
pointer + length
```

hoặc bị scalarize hoàn toàn.

---

# 14. `mut_view`

```axiom
let v = mut_view(data)
```

MIR:

```text
v = MakeMutView {
    owner: data,
    region: Whole(data),
    access: WRITE
}
```

Verifier đảm bảo:

```text
no conflicting READ/WRITE/WRITE capability
```

---

# 15. Capability provenance

Mỗi capability nội bộ có:

```text
CapabilityId
Owner
Region
Access
Lifetime
StorageDomain
ExecutionDomain
```

Ví dụ:

```text
Capability #17

owner        = Local #4
region       = Field #2
access       = WRITE
storage      = LOCAL
execution    = THREAD
```

Đây là compiler metadata.

Không nhất thiết tồn tại trong binary.

---

# 16. Region representation

Region không cần chỉ là pointer range.

MIR semantic region có thể là:

```text
Whole(x)
Field(x, f)
Index(x, i)
Range(x, start, end)
Subregion(...)
```

Compiler có thể prove:

```text
Field(x, a)
```

và:

```text
Field(x, b)
```

là DISJOINT nếu `a != b`.

---

# 17. Region lattice

Giữ model:

```text
DISJOINT
SAME
CONTAINS
CONTAINED_BY
OVERLAPS
UNKNOWN
```

Verifier không được biến:

```text
UNKNOWN
```

thành:

```text
DISJOINT
```

chỉ vì optimizer “nghĩ rằng chắc không overlap”.

---

# 18. Ownership verifier

Ownership verifier hoạt động trên CFG.

Ví dụ:

```axiom
if cond {
    use(x)
} else {
    move(x)
}
use(x)
```

Sau merge:

```text
branch A: x = INIT
branch B: x = MOVED
```

→ trạng thái không hợp lệ.

Compiler báo lỗi.

---

# 19. Ownership state không phải runtime data

Ví dụ:

```text
INIT
MOVED
DROPPED
```

không được compile thành runtime enum.

Đây là compile-time proof state.

---

# 20. Drop elaboration

Trước:

```text
Verified MIR candidate
```

Sau:

```text
Drop-elaborated MIR
```

Compiler chèn:

```text
Drop(x)
```

tại:

- scope exit
- return
- break
- continue
- panic/unwind
- early `?`
- partial move paths

---

# 21. Drop tree

Compiler duy trì drop tree:

```text
Scope
 ├── a
 ├── b
 └── c
```

Exit:

```text
Drop(c)
Drop(b)
Drop(a)
```

trừ các value đã moved.

---

# 22. User Drop

Nếu:

```text
struct Resource
```

có custom Drop:

```text
drop(self)
```

compiler phải coi Drop là semantic behavior.

Không được reorder destruction tùy tiện.

---

# 23. Derived Drop

Nếu compiler-generated:

```text
Drop(S)
```

compiler có thể hiểu field-level destruction.

Do đó partial move được phép.

---

# 24. Panic edges

MIR phải có khả năng biểu diễn:

```text
normal continuation
panic continuation
```

Ví dụ:

```text
Call foo()
 ├── normal → bb2
 └── panic  → bb3
```

Trong abort profile, panic edge có thể lower thành terminal abort.

---

# 25. `?` lowering

```axiom
let x = foo()?
```

được lower thành:

```text
t0 = Call foo()

switch t0:
    Ok(v)  → x = v
    Err(e) → cleanup + return Err(e)
```

Không cần exception machinery.

---

# 26. Match lowering

Source:

```axiom
match x {
    A => ...
    B => ...
}
```

→ pattern decision tree.

Sau đó:

```text
SwitchInt
SwitchEnum
RangeCheck
...
```

Backend không biết `match` nữa.

---

# 27. Loop lowering

```axiom
loop {
    ...
}
```

→ CFG:

```text
header
   ↓
body
   ↓
backedge
```

Break:

```text
body → exit
```

---

# 28. Closure lowering

```axiom
|x| x + offset
```

thành compiler-generated struct:

```text
ClosureEnv {
    offset: T
}
```

và function:

```text
closure_call(env, x)
```

Nhưng đây là compiler representation.

Không nhất thiết user nhìn thấy type này.

---

# 29. Closure capture verification

Nếu closure capture:

```text
view(data)
```

thì compiler kiểm tra lifetime.

Nếu:

```text
move(data)
```

ownership chuyển vào closure.

Nếu capture:

```text
mut_view(data)
```

exclusive capability được transfer vào closure theo contract.

---

# 30. Async lowering

Source:

```axiom
async fn f() {
    a()
    await b()
    c()
}
```

MIR trước async lowering:

```text
a()
await b()
c()
```

Sau:

```text
FutureState {
    state: StateId
    live_values...
}
```

CFG:

```text
State0
  ↓
a()
  ↓
Poll(b)
  ├─ Ready → State1
  └─ Pending → return Pending

State1
  ↓
c()
  ↓
return Ready
```

---

# 31. Suspension point identity

Mỗi `.await` có:

```text
SuspensionPointId
```

Compiler dùng nó để:

- xác định live values
- kiểm tra capability
- kiểm tra Send
- debug mapping
- optimize state machine

---

# 32. Future không cần heap

Ví dụ:

```axiom
let future = f()
```

compiler có thể đặt Future:

```text
register
stack
inline
caller storage
heap
```

tùy semantics.

---

# 33. Future Send analysis

Compiler tính:

```text
State live across await
```

Nếu state chứa non-Send object:

```text
spawn(f())
```

→ reject.

Nhưng:

```text
run_local(f())
```

có thể hợp lệ.

---

# 34. Generic monomorphization

Ví dụ:

```axiom
fn max<T: Ord>(a: T, b: T) -> T
```

sử dụng:

```text
max<i32>
max<f64>
```

Compiler tạo specialization semantic:

```text
GenericInstanceId
```

Sau đó optimize từng specialization.

---

# 35. Không monomorphize mù

Compiler có thể deduplicate:

```text
max<u32>
max<u64>
```

nếu machine representation và semantics cho phép chia sẻ implementation.

Do đó:

> Generic specialization identity ≠ machine code identity.

---

# 36. Trait solver boundary

Trait solver chạy trước MIR optimization.

Input:

```text
T: Trait
```

Output:

```text
TraitResolution
```

Ví dụ:

```text
Add<i32>
→ intrinsic i32_add
```

Backend không tự tìm trait implementation.

---

# 37. Comptime compiler subsystem

Comptime có:

```text
Comptime VM
```

nhưng:

> **Comptime VM không phải runtime của executable.**

Nó chỉ tồn tại trong compiler.

---

# 38. Comptime generated HIR

Ví dụ:

```text
comptime generate(...)
```

→ declarations/HIR mới.

Sau đó:

```text
Generated HIR
 ↓
Normal Resolver
 ↓
Normal Type Checker
 ↓
Normal Verification
```

---

# 39. GPU lowering

`@kernel` vẫn là Axiom function.

Compiler tạo:

```text
Kernel MIR
```

với execution/storage domain:

```text
GPU
Device
Shared
Local
...
```

Sau đó GPU backend riêng lower xuống target ISA.

---

# 40. CPU/GPU semantic commonality

Cả hai đều dùng:

```text
Type
Ownership
Capability
Drop
Atomic
Memory ordering
```

nhưng GPU có legality bổ sung.

Không tạo một language frontend thứ hai.

---

# 41. FFI lowering

Ví dụ:

```axiom
extern "C" fn foo(x: i32) -> i32
```

MIR:

```text
ForeignCall {
    abi: C
    symbol: foo
    args...
}
```

Sau ABI lowering:

```text
calling convention
register assignment
stack arguments
return registers
```

---

# 42. ABI MIR

ABI MIR là boundary:

```text
semantic value
        ↓
ABI representation
```

Ví dụ struct:

```text
S { a: i32, b: i32 }
```

có thể trở thành:

```text
register pair
```

hoặc:

```text
stack aggregate
```

tùy ABI.

---

# 43. Layout xảy ra sau semantic verification

Đây là nguyên tắc cần freeze:

```text
ownership
≠
layout
```

Không được quyết định ownership semantics dựa trên layout.

---

# 44. Axiom LIR

LIR là machine-independent low-level representation.

Nó nên có:

```text
integer ops
float ops
memory load/store
branches
calls
returns
atomic
volatile
address calculation
stack slots
basic aggregate operations
```

nhưng chưa có:

```text
x86 register
ARM register
AVX instruction
```

---

# 45. Machine IR

Machine IR mới biết:

```text
x86-64
AArch64
RISC-V
WASM
...
```

Ví dụ:

```text
virtual register
physical register
instruction
operand
condition code
calling convention
```

---

# 46. Register allocation

Pipeline:

```text
Machine-independent optimization
        ↓
Instruction selection
        ↓
Machine optimization
        ↓
Register allocation
        ↓
Spill/reload
        ↓
Final machine code
```

Không register allocate quá sớm.

---

# 47. SSA

Axiom MIR không nhất thiết phải là SSA ngay từ đầu.

Đề xuất:

```text
MIR = ownership-aware CFG
```

Sau verification:

```text
MIR
 ↓
SSA transformation
 ↓
SSA optimizer
```

Điều này tránh làm ownership analysis phụ thuộc quá sớm vào SSA representation.

---

# 48. Vì sao không SSA ngay từ đầu?

Ownership là property của:

```text
Place
Local
Field
Projection
CFG
```

SSA value không luôn biểu diễn tốt:

```text
partial move
Drop
capability region
storage identity
```

Do đó semantic MIR nên giữ abstraction cao hơn SSA.

---

# 49. SSA không phải semantic source of truth

Sau khi chuyển SSA:

```text
x1
x2
x3
```

có thể xuất hiện.

Nhưng:

```text
ownership identity
```

vẫn truy được từ MIR provenance/debug/semantic metadata.

---

# 50. Optimization legality

Optimizer được cung cấp:

```text
Verified MIR
```

và các invariant.

Ví dụ:

```text
x.view
y.mut_view
```

đã chứng minh DISJOINT.

Optimizer có thể sử dụng fact đó.

---

# 51. Optimization không được tự tạo safety fact

Ví dụ optimizer thấy:

```text
x + 4
```

không được tự kết luận:

```text
"No alias"
```

trừ khi có semantic fact hoặc proof hợp lệ.

---

# 52. Bounds-check elimination

Source:

```axiom
a[i]
```

MIR có:

```text
BoundsCheck(a, i)
Load(...)
```

Optimizer chỉ xóa check khi có proof:

```text
0 <= i < len(a)
```

---

# 53. Unsafe unchecked access

```text
unsafe unchecked_load(...)
```

không tạo semantic guarantee cho safe code.

Nó chỉ nói:

```text
programmer accepted machine-level precondition
```

---

# 54. Atomic MIR

Atomic operation phải giữ:

```text
operation
ordering
scope
width
type
```

Ví dụ:

```text
AtomicLoad
AtomicStore
AtomicRMW
AtomicCAS
```

Ordering không được bị optimizer xóa.

---

# 55. Volatile MIR

Riêng:

```text
VolatileLoad
VolatileStore
```

Không được biến thành ordinary load/store nếu làm mất observable machine access.

---

# 56. Allocation MIR

Giữ:

```text
Alloc
Dealloc
```

nhưng semantic:

```text
StorageKind
Lifetime
Alignment
Size
Domain
```

không nhất thiết là:

```text
malloc/free
```

---

# 57. Stable storage

MIR phải có semantic marker:

```text
StableAddress
```

nếu storage contract yêu cầu.

Optimizer nhìn thấy marker này thì không được stack-promote/scalarize làm mất identity.

---

# 58. Device storage

GPU:

```text
Alloc {
    domain: DEVICE
}
```

không được lower thành CPU malloc.

---

# 59. External storage

Ví dụ FFI:

```text
ExternalStorage
```

thì compiler không được tự `Dealloc` nếu ownership contract là:

```text
OwnedByForeign
```

---

# 60. Debug information

Mỗi semantic entity nên có stable internal identity:

```text
SourceSpanId
LocalId
DeclarationId
TypeId
InstructionId
```

Debug mapping:

```text
Source
 ↓
HIR
 ↓
MIR
 ↓
LIR
 ↓
Machine
```

---

# 61. Incremental compilation

Compiler cache không cache đơn giản theo source text.

Cache key có:

```text
source fingerprint
public semantic fingerprint
compiler semantic version
target
features
comptime dependencies
ABI configuration
```

---

# 62. Parallel compiler

Các phase có thể parallel:

```text
module resolution
generic instantiation
comptime
optimization
codegen
```

nhưng kết quả phải deterministic.

---

# 63. Compiler verifier layering

Nên có:

```text
TypeVerifier
OwnershipVerifier
CapabilityVerifier
DropVerifier
ConcurrencyVerifier
AsyncVerifier
GpuVerifier
FfiVerifier
AbiVerifier
```

Nhưng đây là **các pass**, không phải các semantic systems độc lập.

Chúng cùng đọc/ghi một verification state.

---

# 64. Verification context

Có thể hình dung:

```text
VerificationContext {
    types
    ownership
    capabilities
    regions
    drops
    execution_domains
    storage_domains
    concurrency
    async_state
    gpu_state
    ffi_contracts
}
```

Các verifier phối hợp qua context.

---

# 65. Không verifier nào được “undo”

Một verifier sau khi chứng minh:

```text
capability #17 valid
```

pass sau không được làm mất fact một cách semantic.

Nếu representation bị erase:

```text
capability metadata → erased
```

thì đó là **proof erasure**, không phải semantic invalidation.

---

# 66. Verified MIR là compiler trust boundary

Đây là quyết định lớn nhất của 053:

> **Verified MIR là semantic trust boundary của compiler.**

Trước nó:

```text
compiler đang chứng minh chương trình
```

Sau nó:

```text
compiler đang tối ưu một chương trình đã được chứng minh
```

---

# 67. Nếu optimizer có bug?

Optimizer không được phép thay đổi semantics.

Về kiến trúc:

```text
Verified MIR
    ↓
Optimizer
    ↓
same semantic program
```

Có thể có:

```text
MIR verifier
```

chạy lại sau các transformation quan trọng.

Đặc biệt:

- LTO
- aggressive alias transformations
- async transformations
- GPU transformations
- representation transformations

---

# 68. Semantic verifier sau optimization

Không nhất thiết chạy full expensive verifier sau mọi pass.

Có thể chia:

```text
Semantic Verification
        ↓
Verified MIR
        ↓
Optimization with preserved invariants
        ↓
Lightweight IR Verification
```

Pass nào phá invariant representation thì phải reconstruct/reverify fact tương ứng.

---

# 69. Compiler diagnostics

Diagnostic không chỉ là:

```text
error: borrow...
```

mà structured:

```text
code: AOWN-xxx
entity: LocalId(42)
reason:
  value was moved here

move_site:
  file.ax:21:9

use_site:
  file.ax:24:5
```

AI tooling có thể đọc trực tiếp.

---

# 70. AI compiler API

Compiler nên expose semantic queries:

```text
get_symbol()
get_type()
get_trait_impls()
get_callers()
get_callees()
explain_ownership()
explain_capability()
explain_send()
explain_optimization()
explain_allocation()
explain_abi()
```

Đây không phải language feature.

Đây là compiler tooling API.

---

# 71. Error model

Mỗi semantic error có stable ID:

```text
AOWN-...
ACAP-...
ADROP-...
ATYPE-...
ATRAIT-...
AASYNC-...
AGPU-...
AFFI-...
AABI-...
```

Rendered message có thể thay đổi.

Machine error ID không đổi trong semantic version.

---

# 72. Compiler internal database

Nên dùng một semantic database kiểu:

```text
PackageDB
ModuleDB
DeclDB
TypeDB
TraitDB
ConstDB
MirDB
LayoutDB
AbiDB
CodegenDB
```

với dependency graph.

Điều này rất phù hợp incremental compilation và AI tooling.

---

# 73. Không để AST làm database trung tâm

AST là input artifact.

Semantic database mới là trung tâm.

```text
Source
 ↓
AST
 ↓
Semantic DB
 ↓
HIR/MIR
```

Điều này cũng giúp IDE không phải parse toàn bộ source mỗi lần AI hỏi:

> “Type của `foo` là gì?”

---

# 74. Compiler bootstrap roadmap

Kiến trúc này cho phép bootstrap theo nhiều giai đoạn.

### Stage 0

Compiler prototype viết bằng ngôn ngữ khác:

```text
Parser
Resolver
HIR
MIR
Interpreter
```

### Stage 1

Axiom interpreter:

```text
Source
→ MIR
→ Interpreter
```

### Stage 2

Axiom LIR:

```text
MIR
→ LIR
```

### Stage 3

Native encoder:

```text
LIR
→ x86-64 / ARM64 / RISC-V
```

### Stage 4

Object writer:

```text
Object
ELF
PE/COFF
Mach-O
WASM
```

### Stage 5

Linker.

### Stage 6

Compiler self-hosted bằng Axiom.

---

# 75. Không phụ thuộc LLVM vĩnh viễn

LLVM có thể được dùng trong **bootstrap**, nếu cần.

Nhưng kiến trúc Axiom không được thiết kế thành:

```text
Axiom AST
 ↓
LLVM IR forever
```

Mà:

```text
Axiom Semantic IR
 ↓
Axiom LIR
 ↓
Machine IR
```

LLVM có thể là backend tạm thời:

```text
Axiom LIR
 ↓ adapter
LLVM IR
```

sau đó loại bỏ.

---

# 76. Tương tự linker

Giai đoạn đầu có thể dùng linker hệ thống.

Final:

```text
Axiom Object Writer
+
Axiom Linker
```

để đạt mục tiêu:

> compiler/toolchain cuối cùng không phụ thuộc mandatory third-party compiler/linker.

---

# 77. Self-hosting boundary

Compiler cuối cùng gồm:

```text
axiomc
├── frontend
├── semantic
├── verifier
├── optimizer
├── LIR
├── x86 backend
├── arm64 backend
├── riscv backend
├── wasm backend
├── object writer
├── linker
└── package/build
```

và chính nó được compile bằng Axiom.

---

# 78. Một điểm cần khóa: compiler IR ≠ language ABI

MIR/LIR là internal compiler formats.

Không hứa:

```text
MIR v1
```

tương thích binary giữa compiler versions.

Chỉ artifact/ABI contract mới có stability requirement.

---

# 79. Một điểm cần khóa: IR serialization

Có thể serialize:

```text
HIR metadata
Typed HIR
MIR
optimization cache
```

nhưng format internal có version.

Không được coi compiler IR là public stable ABI.

---

# 80. 053 — kiến trúc đã khóa

Các invariant chính:

```text
ACOMP-20   AST is syntactic representation.
ACOMP-21   HIR contains resolved semantic identities.
ACOMP-22   Typed HIR contains resolved type information.
ACOMP-23   MIR is the primary semantic execution representation.
ACOMP-24   MIR represents ownership-relevant value transitions.
ACOMP-25   MIR represents capability-relevant accesses.
ACOMP-26   MIR represents deterministic control flow.
ACOMP-27   MIR represents Drop obligations before code generation.
ACOMP-28   MIR represents allocation as semantic storage operations.
ACOMP-29   MIR represents atomic operations explicitly.
ACOMP-30   MIR represents volatile operations explicitly.
ACOMP-31   MIR represents panic behavior explicitly.
ACOMP-32   MIR represents async suspension explicitly after lowering.
ACOMP-33   MIR represents GPU execution/storage domains explicitly.
ACOMP-34   MIR represents foreign calls with explicit ABI contracts.
ACOMP-35   Place identity is distinct from Value identity.
ACOMP-36   Ownership state is compiler semantic state.
ACOMP-37   Capability state is compiler semantic state.
ACOMP-38   Capability provenance is represented before proof erasure.
ACOMP-39   Region relations are explicit to the verifier.
ACOMP-40   UNKNOWN overlap cannot be treated as DISJOINT.
ACOMP-41   Ownership verification operates across control-flow joins.
ACOMP-42   Moved values cannot be implicitly reused.
ACOMP-43   Drop elaboration follows verified ownership state.
ACOMP-44   Moved fields are not dropped.
ACOMP-45   User-defined Drop restricts partial moves.
ACOMP-46   Closure lowering preserves capture semantics.
ACOMP-47   Async lowering preserves suspension semantics.
ACOMP-48   Future state contains only values live across suspension.
ACOMP-49   Future Send validity is determined from its retained state.
ACOMP-50   Generic resolution precedes final backend code generation.
ACOMP-51   Trait solving is not a backend responsibility.
ACOMP-52   Comptime-generated declarations re-enter normal semantic compilation.
ACOMP-53   GPU lowering reuses Axiom semantic verification.
ACOMP-54   FFI lowering preserves explicit foreign ABI contracts.
ACOMP-55   ABI lowering occurs after semantic verification.
ACOMP-56   Representation layout does not redefine source semantics.
ACOMP-57   Axiom LIR is machine-independent.
ACOMP-58   Machine IR is target-specific.
ACOMP-59   Register allocation occurs after instruction-level optimization.
ACOMP-60   SSA is an optimization representation, not the sole semantic source of truth.
ACOMP-61   Verified MIR is the compiler semantic trust boundary.
ACOMP-62   Optimization cannot invalidate established semantic invariants.
ACOMP-63   Proof metadata may be erased only after its obligations are discharged.
ACOMP-64   Backend code generation does not reinterpret language semantics.
ACOMP-65   Optimization preserves observable program semantics.
ACOMP-66   Compiler transformations are deterministic for identical semantic inputs.
ACOMP-67   Parallel compilation does not change semantic results.
ACOMP-68   Compiler diagnostics have stable machine-readable identifiers.
ACOMP-69   Semantic entities have stable internal identities within compilation.
ACOMP-70   Compiler tooling may query semantic information without reparsing all source.
ACOMP-71   Internal IR formats are not automatically stable public ABIs.
ACOMP-72   Bootstrap backends may be replaced without changing Axiom semantics.
ACOMP-73   LLVM or another external backend is not a permanent semantic dependency.
ACOMP-74   Final self-hosted compilation can use Axiom-owned backend components.
ACOMP-75   Object generation and linking preserve explicit ABI contracts.
ACOMP-76   Compiler cache identity includes semantic dependencies.
ACOMP-77   Optimization caches include target configuration.
ACOMP-78   Comptime dependencies participate in incremental invalidation.
ACOMP-79   Debug mappings preserve source-to-semantic-to-machine provenance where possible.
ACOMP-80   No compiler phase after semantic verification may silently reintroduce source-level ambiguity.
```

---

# Kiến trúc Axiom hiện tại đã đạt một mốc quan trọng

Từ đầu đến đây, chúng ta đã đi từ:

```text
"muốn một ngôn ngữ nhanh và đơn giản"
```

đến một architecture khá rõ:

```text
                AXIOM LANGUAGE
                      │
          ┌───────────┴───────────┐
          │                       │
      Surface                   Semantics
      Syntax                     │
                                 ▼
                          Typed HIR
                                 │
                                 ▼
                               MIR
                                 │
             ┌───────────────────┼──────────────────┐
             │                   │                  │
         Ownership          Capability          Traits
             │                   │                  │
             ├──────────────┬────┴────┬─────────────┤
             │              │         │
           Drop           Async      GPU
             │              │         │
             └──────────────┼─────────┘
                            ▼
                     VERIFIED MIR
                            │
                            ▼
                  SEMANTIC OPTIMIZER
                            │
                            ▼
                      ABI / Layout
                            │
                            ▼
                          LIR
                            │
                            ▼
                       Machine IR
                            │
                            ▼
                     Native Binary
```

Và quan trọng nhất, **compiler có thể phức tạp bên trong mà ngôn ngữ vẫn đơn giản bên ngoài**.

Đây chính là hướng phù hợp với mục tiêu Axiom mà bạn đặt ra từ đầu.

---

## BOOTSTRAP-054 — Compiler Type/Memory/Semantic Core Implementation Specification

Bước tiếp theo nên đi sâu hơn nữa: **không còn chỉ nói compiler có những phase nào**, mà xác định **các data structure cốt lõi mà compiler phải thực sự implement**.

053 đã nói:

```text
MIR có LocalId
MIR có Place
MIR có Capability
MIR có Region
MIR có Ownership state
```

054 sẽ định nghĩa cụ thể:

- `TypeId`, `Type`
- `TypeInterner`
- `SymbolId`, `DeclarationId`
- `Place`
- `Projection`
- `Value`
- `Local`
- `BasicBlock`
- `MIR`
- `Operand`
- `Rvalue`
- `Terminator`
- `Capability`
- `Region`
- `OwnershipState`
- `DropTree`
- `TraitRef`
- `GenericInstance`
- `ConstValue`
- `ComptimeValue`
- `StorageDomain`
- `ExecutionDomain`
- `SourceMap`
- `Diagnostic`
- `SemanticFingerprint`

Đây sẽ là **spec gần với implementation nhất từ trước tới nay** và là điểm rất phù hợp để sau đó giao cho AI agent bắt đầu tạo repository/compiler skeleton thực sự.