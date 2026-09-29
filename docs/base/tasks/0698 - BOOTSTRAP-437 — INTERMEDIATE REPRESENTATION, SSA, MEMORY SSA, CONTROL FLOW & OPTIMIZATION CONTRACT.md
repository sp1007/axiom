# BOOTSTRAP-437 — INTERMEDIATE REPRESENTATION, SSA, MEMORY SSA, CONTROL FLOW & OPTIMIZATION CONTRACT

**Trạng thái: COMPLETED / LOCKED**

Mục tiêu của task này là khóa IR đủ rõ để có thể **bắt đầu viết compiler backend thực tế**, nhưng không biến Axiom thành một bản sao của LLVM.

Kiến trúc IR chính:

```text
AST
 ↓
HIR
 ↓
MIR
 ↓
LIR
 ↓
Machine IR
 ↓
Machine Encoder
 ↓
Object
```

Trong đó:

- **HIR**: semantic/high-level representation.
- **MIR**: canonical middle representation, nơi ownership/control flow trở nên explicit.
- **LIR**: low-level target-independent representation gần machine hơn.
- **Machine IR**: target-specific instruction representation.

---

## 437.1 — Nguyên tắc thiết kế IR

Axiom IR phải đạt 6 mục tiêu đồng thời:

1. dễ verify;
2. dễ optimize;
3. dễ debug;
4. dễ codegen;
5. đủ nhỏ để compiler tự implement;
6. không khóa compiler vào một ISA cụ thể.

Không thiết kế IR để hỗ trợ mọi optimization có thể tưởng tượng.

---

# 437.2 — HIR

HIR giữ semantic structure sau khi syntax sugar được xử lý.

Ví dụ:

```text
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

HIR vẫn có:

```text
Function
 ├── Parameter a : i32
 ├── Parameter b : i32
 └── BinaryAdd(a, b)
```

nhưng không còn phụ thuộc trực tiếp vào parser syntax.

---

# 437.3 — HIR không phải optimizer IR

HIR không cố biểu diễn:

```text
register
stack slot
machine instruction
```

Nó phục vụ semantic processing.

---

# 437.4 — HIR node identity

Mỗi semantic node có:

```text
HirId
SourceSpan
TypeId
```

khi cần.

---

# 437.5 — HIR expressions

Các expression canonical:

```text
Literal
Variable
Unary
Binary
Call
MethodCall
Field
Index
Cast
Tuple
Array
StructInit
EnumInit
Match
If
Block
Loop
Return
Break
Continue
Try
Closure
Async
```

---

# 437.6 — HIR statements

Canonical:

```text
Let
Assign
Expression
Defer
Return
```

Các syntax khác được lowering.

---

# 437.7 — HIR pattern

Pattern đã được type-check:

```text
Wildcard
Binding
Literal
Tuple
Struct
Enum
Range
Or
Guard
```

---

# 437.8 — HIR generic instantiation

HIR có thể chứa:

```text
GenericFunctionRef
GenericInstanceRef
```

nhưng specialization chưa nhất thiết phải generate ngay.

---

# 437.9 — HIR trait dispatch

Static trait call sau resolution có thể trở thành:

```text
DirectFunctionRef
```

Dynamic trait call:

```text
DynMethodCall
```

---

# 437.10 — HIR ownership annotations

Các expression có thể được đánh dấu semantic ownership behavior:

```text
Move
Copy
Borrow/View
Consume
Produce
```

MIR sẽ biến chúng thành hành vi explicit hơn.

---

# 437.11 — MIR mục tiêu

MIR là **canonical executable semantic representation**.

Mọi high-level syntax cuối cùng phải lower về MIR.

---

# 437.12 — MIR instruction model

Mỗi MIR instruction có dạng conceptual:

```text
Instruction {
    opcode
    operands
    result
    type
    source
}
```

---

# 437.13 — SSA quyết định

Axiom MIR **không bắt buộc pure SSA**.

Lý do:

- ownership;
- mutable locals;
- cleanup;
- addressable locals;
- debug;
- lowering đơn giản hơn.

Thay vào đó:

> **LIR/Optimization IR sử dụng SSA.**

---

# 437.14 — MIR local

MIR có local slots:

```text
LocalId
TypeId
StorageClass
Mutability
```

Ví dụ:

```text
a: i32
b: i32
tmp: i32
```

---

# 437.15 — MIR place

Place biểu diễn storage:

```text
Place =
    Local
  | Field(Place, FieldId)
  | Index(Place, Value)
  | Deref(Value)
```

---

# 437.16 — Value vs Place

Hai khái niệm phải tách biệt.

```text
Value
```

là giá trị.

```text
Place
```

là vị trí chứa giá trị.

Ví dụ:

```text
x = y
```

là:

```text
read Place(y)
write Place(x)
```

---

# 437.17 — MIR statements

Core MIR operations:

```text
StorageLive
StorageDead
Assign
Move
Copy
Load
Store
BorrowView
Drop
Defer
```

---

# 437.18 — MIR terminators

```text
Goto
Branch
Switch
Call
Return
Panic
Unreachable
Invoke
Suspend
```

---

# 437.19 — Basic block

Mỗi block có:

```text
BlockId
instructions[]
terminator
```

Invariant:

> Một basic block luôn kết thúc bằng đúng một terminator.

---

# 437.20 — CFG

MIR tạo Control Flow Graph:

```text
Block
 ↓
successors
```

và:

```text
predecessors
```

được tính/cache.

---

# 437.21 — CFG example

```text
        entry
          │
       condition
       /       \
      ▼         ▼
   then        else
      \         /
       ▼       ▼
         merge
           │
         return
```

---

# 437.22 — Dominator tree

Optimizer cần:

```text
DominatorTree
```

để xác định:

```text
A dominates B
```

---

# 437.23 — Post-dominator

Có thể tính:

```text
PostDominatorTree
```

cho:

- control-flow optimization;
- cleanup;
- structured control flow;
- branch reasoning.

---

# 437.24 — Critical edge

CFG analysis phải nhận diện:

```text
critical edge
```

để SSA construction và block splitting hoạt động chính xác.

---

# 437.25 — Phi values

Khi MIR được chuyển SSA:

```text
x3 = phi(x1, x2)
```

Phi có một input cho mỗi predecessor tương ứng.

---

# 437.26 — Phi placement

Phi placement dựa trên:

```text
dominance frontier
```

hoặc thuật toán tương đương.

---

# 437.27 — SSA invariant

Mỗi SSA value:

```text
defined exactly once
```

và mọi use phải được dominate bởi definition.

---

# 437.28 — SSA không phải source semantics

SSA chỉ là representation.

Không expose SSA cho người dùng Axiom.

---

# 437.29 — Memory SSA

Axiom dùng **Memory SSA ở LIR/optimization layer**, không bắt buộc MIR.

Memory SSA biểu diễn dependency giữa các memory operations.

---

# 437.30 — Memory token

Conceptual:

```text
Memory0
   │
 Store A
   │
Memory1
   │
 Load B
```

Load biết nó phụ thuộc memory state tương ứng.

---

# 437.31 — Tại sao không dùng memory SSA ngay MIR

MIR cần dễ hiểu cho:

```text
ownership
drop
addressable locals
debug
```

Memory SSA quá sớm sẽ làm semantic lowering phức tạp không cần thiết.

---

# 437.32 — Memory operation categories

LIR phân biệt:

```text
Load
Store
AtomicLoad
AtomicStore
AtomicRMW
Fence
VolatileLoad
VolatileStore
```

---

# 437.33 — Alias classes

Memory accesses có metadata:

```text
AliasClass
```

nhưng mặc định compiler phải conservative.

---

# 437.34 — `noalias`

`noalias` chỉ xuất hiện khi:

```text
language semantics
hoặc explicit valid contract
```

chứng minh được.

Không tự đoán.

---

# 437.35 — Memory ordering

Atomic IR giữ:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

đã khóa tại BOOTSTRAP-424.

---

# 437.36 — Volatile semantics

Volatile operation không được:

- xóa;
- duplicate;
- reorder tùy tiện.

---

# 437.37 — Undefined behavior boundary

IR phải phân biệt:

```text
Defined
Poison/invalid internal state
Explicit Unsafe
Unreachable
```

Axiom không nên sử dụng mô hình poison phức tạp như một yêu cầu bắt buộc.

---

# 437.38 — Invalid IR

Nếu verifier phát hiện invalid IR:

```text
compiler internal error
```

không được emit artifact.

---

# 437.39 — Integer semantics

IR phải ghi rõ overflow mode khi operation cần:

```text
Add
Sub
Mul
```

có thể là:

```text
checked
wrapping
saturating
```

---

# 437.40 — Không có implicit overflow semantics

Optimizer không được biến:

```text
checked add
```

thành:

```text
wrapping add
```

chỉ vì thuận tiện.

---

# 437.41 — Integer comparison

IR có operation riêng:

```text
ICmpSigned
ICmpUnsigned
```

tránh nhầm semantics.

---

# 437.42 — Floating-point

IR:

```text
FAdd
FSub
FMul
FDiv
FCmp
```

với floating-point mode metadata khi cần.

---

# 437.43 — Floating-point optimization

Compiler không được giả định:

```text
(a+b)+c == a+(b+c)
```

trừ khi optimization mode cho phép relaxed floating-point semantics.

---

# 437.44 — NaN

IR phải preserve IEEE behavior mặc định.

---

# 437.45 — Bitcast

`bitcast` chỉ đổi interpretation của cùng representation khi layout cho phép.

Không phải numeric conversion.

---

# 437.46 — Numeric conversion

IR riêng:

```text
IntToFloat
FloatToInt
IntExtend
IntTruncate
FloatExtend
FloatTruncate
```

---

# 437.47 — Pointer/address IR

LIR có:

```text
Address
Pointer
```

nhưng không được coi mọi integer là pointer.

---

# 437.48 — Pointer arithmetic

Pointer arithmetic phải có semantics explicit.

Không cho optimizer giả định mọi integer arithmetic trên address đều hợp lệ.

---

# 437.49 — Slice representation

Slice/view có thể lower thành:

```text
(ptr, len)
```

---

# 437.50 — String representation

String view:

```text
(ptr, len)
```

String owner:

```text
(ptr, len, capacity, allocator metadata nếu cần)
```

Layout cụ thể được quyết định bởi type layout.

---

# 437.51 — Aggregate values

Struct/tuple có thể tồn tại ở MIR dưới dạng:

```text
AggregateValue
```

---

# 437.52 — Aggregate decomposition

Optimizer/LIR có thể scalarize:

```text
struct Vec2 { x, y }
```

thành:

```text
x
y
```

nếu ABI/escape semantics cho phép.

---

# 437.53 — Aggregate memory

Nếu aggregate address escape:

```text
alloca/storage
```

có thể cần tồn tại.

---

# 437.54 — Scalar Replacement

SROA:

```text
aggregate memory
→ scalar SSA values
```

là optimization quan trọng của Axiom.

---

# 437.55 — Tuple lowering

Tuple không có hidden runtime object.

Nó có thể:

```text
registers
stack
memory
```

tùy use/ABI.

---

# 437.56 — Enum lowering

Enum:

```text
tag + payload
```

hoặc niche optimized representation.

---

# 437.57 — Enum switch

Pattern matching enum thường lower thành:

```text
load tag
switch tag
```

sau đó optimizer có thể loại bỏ load thừa.

---

# 437.58 — Niche optimization

Ví dụ conceptual:

```text
Option<NonNull<T>>
```

có thể dùng một representation value cho `None`.

---

# 437.59 — Niche invariant

Niche optimization chỉ hợp lệ nếu:

```text
unused representation
```

được type/layout system xác nhận.

---

# 437.60 — Function values

Function pointer:

```text
FnPtr
```

là first-class value.

---

# 437.61 — Direct call

Nếu function identity biết tại compile time:

```text
CallDirect
```

---

# 437.62 — Indirect call

Nếu function pointer:

```text
CallIndirect
```

---

# 437.63 — Trait dynamic call

```text
CallVTable
```

được biểu diễn explicit trước codegen.

---

# 437.64 — Tail call

IR có:

```text
TailCall
```

nếu ABI/target cho phép.

---

# 437.65 — Call attributes

Call/function có thể có metadata:

```text
inline_hint
noinline
cold
hot
noreturn
no_alloc
no_panic
```

Chỉ những attribute có semantics hợp lệ mới được optimizer sử dụng.

---

# 437.66 — `noreturn`

Function trả:

```text
never
```

được biểu diễn:

```text
Call
→ Unreachable
```

---

# 437.67 — Panic

Panic path:

```text
operation
 ↓
Panic
```

hoặc:

```text
operation
 ↓
Invoke
```

nếu unwind enabled.

---

# 437.68 — Exception/unwind IR

Unwind không phải default.

Khi enabled:

```text
Invoke
LandingPad/Cleanup
Resume
```

---

# 437.69 — Cleanup correctness

Mọi path thoát scope phải chạy cleanup cần thiết.

Đây là invariant từ BOOTSTRAP-423.

---

# 437.70 — Cleanup lowering

Ví dụ:

```text
let a = acquire()
let b = acquire()

return
```

MIR:

```text
acquire a
acquire b
drop b
drop a
return
```

---

# 437.71 — Conditional cleanup

Nếu:

```text
if condition {
    a = acquire()
}
```

chỉ path initialized mới drop `a`.

---

# 437.72 — Cleanup optimization

Nếu compiler chứng minh:

```text
resource never initialized
```

cleanup không được emit.

---

# 437.73 — Drop elaboration

Ownership checker tạo semantic drop requirements.

MIR biến chúng thành explicit `Drop`.

Sau đó optimizer có thể:

```text
remove redundant drop
```

nếu type trivial hoặc lifetime đã kết thúc.

---

# 437.74 — Drop flags

Partial initialization có thể cần:

```text
drop_flag
```

Compiler có thể optimize flag thành control flow hoặc eliminate hoàn toàn.

---

# 437.75 — `defer`

`defer` được lower thành cleanup action gắn với scope.

---

# 437.76 — Return value + cleanup

Compiler phải đảm bảo:

```text
compute return value
→ preserve/move result
→ cleanup locals
→ return
```

không overwrite return value.

---

# 437.77 — Temporary lifetime

Temporary value sống đủ lâu theo semantic rules nhưng không lâu hơn cần thiết.

---

# 437.78 — Temporary optimization

Compiler có thể:

```text
temporary
→ register
```

hoặc eliminate hoàn toàn.

---

# 437.79 — Move lowering

Move không nhất thiết là machine instruction.

Nếu source value chỉ chuyển ownership:

```text
MIR state transition
```

có thể đủ.

---

# 437.80 — Copy lowering

Copy có thể trở thành:

```text
register copy
load/store
memcpy
```

tùy representation.

---

# 437.81 — Clone lowering

`clone()` là ordinary function call.

Compiler không assume cheap.

---

# 437.82 — Memory copy

IR:

```text
MemCopy
MemMove
MemSet
```

có semantic size/alignment.

Backend có thể inline hoặc gọi runtime implementation.

---

# 437.83 — Allocation IR

Allocation:

```text
Alloc
Realloc
Free
```

được explicit.

---

# 437.84 — Allocator identity

Allocation có thể mang:

```text
AllocatorId
```

để compiler biết deallocation tương ứng.

---

# 437.85 — Allocation optimization

Không được merge allocations nếu làm thay đổi:

- address identity;
- lifetime;
- allocator semantics;
- observable behavior.

---

# 437.86 — Stack allocation

```text
StackAlloc
```

có thể được tạo bởi optimizer/backend.

Không nhất thiết source-level construct.

---

# 437.87 — Escape analysis

Escape analysis chạy trên:

```text
allocation graph
+
call graph
+
alias graph
```

---

# 437.88 — Escape states

Canonical:

```text
NoEscape
FunctionEscape
ThreadEscape
GlobalEscape
```

---

# 437.89 — Stack promotion invariant

Chỉ promotion:

```text
heap → stack
```

khi compiler chứng minh object không escape lifetime stack.

---

# 437.90 — Async IR

Async HIR:

```text
async fn
```

được lower thành explicit state machine.

---

# 437.91 — Async states

Conceptual:

```text
State0
State1
State2
Completed
```

---

# 437.92 — Suspend

MIR:

```text
Suspend(state_id)
```

---

# 437.93 — Resume

Executor gọi:

```text
Poll(frame)
```

→:

```text
Pending
Ready(value)
```

---

# 437.94 — Async frame

Frame chỉ chứa locals sống qua suspension.

---

# 437.95 — Async frame optimization

Dead locals không được giữ trong frame.

---

# 437.96 — Closure IR

Closure:

```text
Closure {
    code
    captures
}
```

được hạ thành explicit environment structure.

---

# 437.97 — Closure call

```text
CallClosure {
    code_ptr
    environment
    args
}
```

---

# 437.98 — Closure capture analysis

Chỉ capture biến được sử dụng.

---

# 437.99 — Closure environment layout

Environment layout được đưa qua type/layout engine như struct thông thường.

---

# 437.100 — Generator-like state

Nếu sau này có generator:

```text
generator
→ state machine
```

tái sử dụng async infrastructure.

---

# 437.101 — LIR

LIR là IR target-independent nhưng gần machine.

LIR không còn:

```text
high-level match
generic trait resolution
ownership abstraction
```

---

# 437.102 — LIR types

Chủ yếu:

```text
i1
i8
i16
i32
i64
f16
f32
f64
ptr
vector
aggregate
```

---

# 437.103 — Target-dependent types

Target-specific vector/register classes chỉ xuất hiện ở Machine IR.

---

# 437.104 — LIR operations

Core:

```text
integer arithmetic
floating arithmetic
comparison
conversion
load
store
address calculation
call
return
branch
select
atomic
fence
```

---

# 437.105 — Select

Ternary/select:

```text
select(cond, a, b)
```

có thể lower thành:

```text
branch
```

hoặc conditional move.

---

# 437.106 — Address calculation

LIR:

```text
GEP/base+offset
```

nhưng semantics phải bảo toàn type/layout bounds assumptions.

---

# 437.107 — GEP simplification

Không sao chép LLVM GEP semantics.

Axiom dùng một operation đơn giản hơn:

```text
AddressOf(base, offset)
```

với layout-proven offset khi có thể.

---

# 437.108 — Constant propagation

LIR optimizer thực hiện:

```text
const + const
→ const
```

---

# 437.109 — Constant folding

Bao gồm:

```text
integer
float
comparison
cast
layout constants
```

theo semantic rules.

---

# 437.110 — SCCP

Sparse conditional constant propagation có thể được dùng.

Không bắt buộc ở bootstrap compiler nếu complexity chưa cần thiết.

---

# 437.111 — Dead code elimination

DCE loại:

```text
unused pure computations
unreachable blocks
unused internal functions
```

nhưng phải giữ side effects.

---

# 437.112 — Side-effect classification

Operation được phân loại:

```text
Pure
ReadMemory
WriteMemory
Atomic
Volatile
Call
ControlEffect
```

---

# 437.113 — Pure operation

Pure operation có thể:

```text
CSE
DCE
reorder
```

nếu dependencies cho phép.

---

# 437.114 — Call side effects

Call mặc định conservative.

Function attributes có thể cung cấp additional facts.

---

# 437.115 — Common Subexpression Elimination

CSE chỉ merge expressions khi:

```text
same operands
same operation
same relevant memory state
no observable side effects
```

---

# 437.116 — Global Value Numbering

GVN có thể dùng trên SSA.

---

# 437.117 — Load CSE

Load chỉ CSE nếu memory dependency chứng minh không có intervening write.

---

# 437.118 — Store forwarding

Nếu:

```text
store x
load x
```

và không có aliasing store:

```text
load → stored value
```

---

# 437.119 — Memory dependence

Memory optimization dựa trên:

```text
Memory SSA
+
Alias Analysis
```

---

# 437.120 — Alias analysis levels

Bootstrap:

```text
BasicAliasAnalysis
```

sau đó có thể mở rộng:

```text
TypeBasedAliasAnalysis
NoAlias contracts
Escape-based analysis
```

---

# 437.121 — Loop representation

CFG loop analysis:

```text
LoopInfo
```

xác định:

```text
header
latches
body
exits
```

---

# 437.122 — Loop invariant code motion

LICM được phép đưa computation ra ngoài loop nếu:

```text
pure
hoistable
dominance-safe
memory-safe
```

---

# 437.123 — Loop strength reduction

Có thể transform:

```text
i * constant
```

thành incremental form khi target phù hợp.

---

# 437.124 — Induction variables

Loop optimizer nhận diện induction variables.

---

# 437.125 — Bounds-check elimination

Ví dụ:

```text
for i in 0..len(a) {
    x = a[i]
}
```

compiler có thể chứng minh:

```text
0 <= i < len(a)
```

và loại bounds check.

---

# 437.126 — Bounds-check proof

Proof sources:

```text
range analysis
loop induction
dominance
constant ranges
slice length propagation
```

---

# 437.127 — Không speculative bounds elimination

Không được bỏ check dựa trên heuristic.

---

# 437.128 — Inlining

Inlining cost model xét:

```text
instruction count
call frequency
hot/cold
generic specialization
code size
recursion
```

---

# 437.129 — Always-inline

`@inline(always)` là hint mạnh nhưng compiler vẫn phải bảo vệ correctness/resource limits.

---

# 437.130 — No-inline

`@noinline` cấm inline trừ trường hợp compiler bắt buộc vì ABI/lowering.

---

# 437.131 — Cold paths

Compiler có thể tách:

```text
normal path
cold/error path
```

để cải thiện locality.

---

# 437.132 — Panic cold path

Panic thường được đánh dấu cold.

---

# 437.133 — Result error path

`Err` không mặc định cold về semantic.

Optimizer có thể sử dụng profile information nhưng không được assume error hiếm.

---

# 437.134 — Branch prediction metadata

Có thể lưu:

```text
likely
unlikely
profile probability
```

nhưng đây là optimization metadata, không semantic requirement.

---

# 437.135 — Profile-guided optimization

PGO là optional.

Profile data không được làm thay đổi semantics.

---

# 437.136 — Vectorization

Vectorizer có thể sử dụng:

```text
loop dependence analysis
alias analysis
target SIMD capabilities
```

---

# 437.137 — Auto-vectorization safety

Không vectorize nếu có dependency/alias/atomic semantics chưa được chứng minh.

---

# 437.138 — Parallelization

Compiler **không tự động biến ordinary loops thành threads**.

Parallelism phải explicit/library-level theo BOOTSTRAP-424.

---

# 437.139 — SIMD vs threads

SIMD:

```text
data parallel within execution context
```

Thread:

```text
independent execution contexts
```

Hai optimization khác nhau.

---

# 437.140 — Atomic optimization

Atomic không được biến thành non-atomic operation.

---

# 437.141 — Atomic weakening

Compiler không được tự giảm:

```text
SeqCst → Relaxed
```

chỉ vì nhanh hơn.

---

# 437.142 — Atomic strengthening

Strengthening có thể đúng về semantics nhưng không được làm mặc định nếu gây unnecessary cost trừ khi language semantics đã định nghĩa.

---

# 437.143 — Fence

Fence là explicit IR instruction.

Optimizer chỉ được loại nếu chứng minh semantics không thay đổi.

---

# 437.144 — Thread spawn

`spawn` không phải ordinary function call trong semantic IR.

Có effect:

```text
ThreadEscape
```

và runtime boundary.

---

# 437.145 — Join

Join là synchronization operation.

Compiler không được reorder memory operations qua join nếu vi phạm memory model.

---

# 437.146 — Channel operations

Channel send/receive được coi là side-effecting synchronization operations.

---

# 437.147 — Lock operations

Lock/unlock không được reorder tùy tiện.

---

# 437.148 — Unsafe IR

Unsafe operations được đánh dấu:

```text
Unsafe
```

nhưng sau khi semantic validation chúng vẫn có thể được optimize theo machine semantics.

---

# 437.149 — Debug metadata

Mỗi IR instruction có thể giữ:

```text
DebugLoc
```

không bắt buộc ở `-O0`? Không: `-O0` ưu tiên giữ đầy đủ.

---

# 437.150 — Optimization source mapping

Optimizer phải cố preserve:

```text
source → IR
```

mapping.

---

# 437.151 — Debug value tracking

Compiler có thể track:

```text
variable x
→ SSA value
```

để debugger hiển thị giá trị.

---

# 437.152 — Debug optimization tradeoff

`-O0`:

```text
predictable debugging
```

`-O2`:

```text
maximum normal optimization
```

`-O3`:

```text
aggressive optimization
```

---

# 437.153 — Optimization profiles

Chuẩn:

```text
-O0
-O1
-O2
-O3
-Os
-Oz
```

Ý nghĩa cụ thể có thể điều chỉnh nhưng phải stable.

---

# 437.154 — `-Os`

Ưu tiên code size.

---

# 437.155 — `-Oz`

Ưu tiên artifact size tối đa, kể cả trade-off performance.

---

# 437.156 — Debug build

Debug profile có:

```text
-O0
debug info
assertions
overflow checks
```

theo cấu hình.

---

# 437.157 — Release build

Release:

```text
-O2
strip policy configurable
panic policy configurable
```

---

# 437.158 — Sanitizer instrumentation

Compiler có thể instrument:

```text
bounds
integer
address
thread
undefined behavior
```

ở debug/sanitize builds.

---

# 437.159 — Sanitizer runtime

Sanitizer runtime là optional component.

Không nằm trong normal executable nếu không dùng.

---

# 437.160 — IR verifier

Mỗi IR stage có verifier:

```text
verify_hir
verify_mir
verify_lir
verify_machine_ir
```

---

# 437.161 — HIR verifier

Kiểm tra:

```text
types
resolved symbols
patterns
generic substitutions
```

---

# 437.162 — MIR verifier

Kiểm tra:

```text
CFG
locals
types
moves
drops
terminators
```

---

# 437.163 — LIR verifier

Kiểm tra:

```text
SSA
types
memory dependencies
calls
ABI constraints
```

---

# 437.164 — Machine IR verifier

Kiểm tra:

```text
register classes
operand legality
ABI
instruction constraints
```

---

# 437.165 — Machine encoder verifier

Encoded instruction phải có:

```text
valid opcode
valid operands
correct size
correct fixups
```

---

# 437.166 — IR serialization

IR có thể serialize để:

- caching;
- debugging;
- compiler development;
- distributed builds.

Format phải versioned.

---

# 437.167 — IR cache safety

Không load cached IR nếu:

```text
compiler version
target
semantic hash
IR schema
```

không tương thích.

---

# 437.168 — IR hash

Mỗi canonical IR unit có stable semantic hash.

---

# 437.169 — Function-level caching

Function codegen có thể cache theo:

```text
FunctionSemanticHash
+
Target
+
OptimizationProfile
+
ABI
+
CompilerVersion
```

---

# 437.170 — Cross-module optimization cache

Nếu public ABI không thay đổi, implementation-only changes không nhất thiết invalidate downstream interface artifacts.

---

# 437.171 — Whole-program cache

Final binary cache key bao gồm:

```text
all reachable artifact hashes
link configuration
target
linker version
runtime components
```

---

# 437.172 — Reproducible IR

Cùng semantic input phải tạo:

```text
equivalent canonical IR
```

không phụ thuộc thread scheduling.

---

# 437.173 — Parallel optimization

Functions độc lập có thể optimize parallel.

---

# 437.174 — Global optimization barrier

Optimization cần cross-function information phải chạy sau khi summaries available.

---

# 437.175 — Function summary

Có thể lưu:

```text
size
calls
effects
allocations
panic
memory behavior
hotness
```

---

# 437.176 — Effect summary

Ví dụ:

```text
foo:
    no_alloc
    no_io
    may_panic
```

Optimizer có thể sử dụng nhưng summary phải được verify.

---

# 437.177 — Call graph

Compiler xây:

```text
CallGraph
```

với edges:

```text
direct
indirect
virtual/dynamic
unknown
```

---

# 437.178 — Indirect calls

Nếu target không biết:

```text
CallIndirect
```

không được giả định callee.

---

# 437.179 — Devirtualization

Dynamic dispatch có thể được devirtualize nếu compiler chứng minh concrete target duy nhất trong scope optimization.

Không thay đổi semantics.

---

# 437.180 — Generic devirtualization

Static generics thường đã không cần dynamic dispatch.

---

# 437.181 — Dead function elimination

Internal functions không reachable từ roots có thể bị loại.

---

# 437.182 — Exported functions

Exported functions là linker roots.

---

# 437.183 — FFI functions

`extern` symbols được giữ theo linkage contract.

---

# 437.184 — Intrinsics

Compiler intrinsic có semantic definition riêng:

```text
intrinsic id
signature
effects
lowering
```

---

# 437.185 — Intrinsic fallback

Nếu intrinsic có portable fallback:

```text
target implementation
```

nếu không:

```text
compile error
```

---

# 437.186 — Backend contract

LIR phải có đủ thông tin để backend xác định:

```text
instruction
register
memory
ABI
control flow
```

mà không cần quay lại AST.

---

# 437.187 — Backend không type-check

Backend chỉ verify IR legality.

Semantic type checking đã hoàn thành.

---

# 437.188 — Backend không resolve trait

Trait resolution phải hoàn thành trước LIR.

---

# 437.189 — Backend không biết ownership

Ownership đã được lower thành:

```text
move
copy
drop
memory lifetime
```

Backend chỉ tối ưu các operations này.

---

# 437.190 — Backend không biết generic

Sau monomorphization, backend nhận concrete instances.

---

# 437.191 — Dynamic trait exception

Backend vẫn biết dynamic vtable call ABI vì đây là concrete representation.

---

# 437.192 — IR lowering pipeline khóa

```text
AST
 ↓
HIR
 │
 ├── semantic queries
 ├── type
 ├── trait
 ├── ownership
 └── comptime
 ↓
MIR
 ↓
MIR cleanup/drop elaboration
 ↓
SSA construction
 ↓
LIR
 ↓
Memory SSA
 ↓
Optimization
 ↓
ABI lowering
 ↓
Machine IR
 ↓
Register allocation
 ↓
Instruction scheduling
 ↓
Machine encoding
```

---

# 437.193 — Bootstrap optimizer

Compiler đầu tiên không cần implement toàn bộ optimizer.

Phase 1:

```text
constant folding
dead code elimination
CFG simplify
basic inlining
copy propagation
```

Phase 2:

```text
SSA
GVN
SROA
escape analysis
bounds-check elimination
```

Phase 3:

```text
LICM
vectorization
PGO
LTO
advanced alias analysis
```

---

# 437.194 — `-O0` architecture

Ngay cả `-O0`, compiler vẫn phải:

```text
lower HIR → MIR → LIR
```

nhưng bỏ phần lớn optimization.

---

# 437.195 — `-O0` correctness

Không có optimization không được thay đổi semantics.

---

# 437.196 — Minimal LIR

Bootstrap LIR tối thiểu:

```text
const
add/sub/mul/div
cmp
load/store
address
call
return
branch
phi
alloca
memcpy
atomic
```

Đây là bộ operation đủ để xây compiler native đầu tiên.

---

# 437.197 — Machine IR tối thiểu

Machine IR cần:

```text
MachineOpcode
VirtualRegister
PhysicalRegister
Immediate
MemoryOperand
Label
SymbolReference
```

---

# 437.198 — Virtual registers

Instruction selection tạo virtual registers.

Register allocator map chúng sang physical registers.

---

# 437.199 — Spill

Nếu thiếu physical registers:

```text
virtual register
→ stack spill slot
```

---

# 437.200 — Spill reload

```text
load spill slot
→ virtual/physical register
```

được chèn tự động.

---

# 437.201 — Register classes

Ví dụ x86-64:

```text
GPR
XMM
FLAGS
```

AArch64:

```text
GPR
FP/SIMD
```

---

# 437.202 — Register constraints

Instruction có thể yêu cầu:

```text
specific register
register class
paired registers
```

---

# 437.203 — ABI register constraints

Function arguments/returns được precolored theo ABI.

---

# 437.204 — Stack slot layout

Stack frame builder xác định:

```text
locals
spills
outgoing args
alignment
saved registers
```

---

# 437.205 — Red zone

Backend target/ABI quyết định có thể sử dụng red zone hay không.

Không hard-code trong language.

---

# 437.206 — Stack probing

Nếu target/OS ABI yêu cầu stack probing, backend/runtime integration xử lý.

---

# 437.207 — Frame pointer

Có thể:

```text
omit frame pointer
```

ở release.

Debug profile có thể giữ.

---

# 437.208 — Instruction scheduling

Sau register allocation hoặc trước tùy backend.

Backend được phép chọn chiến lược.

---

# 437.209 — Peephole optimization

Machine IR hỗ trợ:

```text
instruction pattern
→ cheaper equivalent sequence
```

---

# 437.210 — Machine-level constant folding

Ví dụ:

```text
mov rax, 0
add rax, 0
```

→

```text
xor/zeroing sequence
```

nếu target semantics cho phép.

---

# 437.211 — Target cost model

Mỗi backend cung cấp:

```text
latency
throughput
size
register pressure
```

khi cần.

Không hard-code x86 assumptions vào optimizer chung.

---

# 437.212 — Cost model không phải semantic

Cost model chỉ ảnh hưởng lựa chọn optimization.

Không ảnh hưởng program correctness.

---

# 437.213 — Code-size optimization

Optimizer có thể chọn:

```text
short branch
smaller instruction
outlining
shared code
```

---

# 437.214 — Branch relaxation

Machine/object layer có thể relax:

```text
short branch
→ long branch
```

hoặc ngược lại.

---

# 437.215 — Relocation-aware optimization

Backend không được tạo relocation sequence không hợp lệ.

---

# 437.216 — Position-independent code

LIR/Machine IR hỗ trợ:

```text
PIC
PIE
```

khi target ABI yêu cầu.

---

# 437.217 — TLS lowering

TLS operation:

```text
TLSAddress
```

được lower theo target ABI.

---

# 437.218 — GOT/PLT

Không đưa GOT/PLT vào generic LIR.

Chúng xuất hiện ở:

```text
ABI/object/linker lowering
```

---

# 437.219 — Exception tables

Nếu unwind enabled:

```text
Machine IR
→ unwind metadata
→ object sections
```

---

# 437.220 — Stack maps

Async, GC-less runtime và debugging không yêu cầu GC maps.

Nhưng stack maps có thể cần cho:

```text
debugger
deoptimization future
async runtime
```

nếu feature cần.

---

# 437.221 — No GC maps by default

Axiom runtime không cần GC scanning metadata.

---

# 437.222 — IR concurrency metadata

Atomic and synchronization instructions giữ memory order.

---

# 437.223 — Async state metadata

State-machine transitions phải có source mapping để debugger có thể hiển thị async call stack tốt nhất có thể.

---

# 437.224 — Compiler crash diagnostics

Nếu verifier thất bại:

Compiler phải emit:

```text
compiler bug
phase
IR unit
source location
compiler version
target
```

và tùy chọn dump IR.

---

# 437.225 — IR dump commands

CLI có thể hỗ trợ:

```text
axiom dump-ir
axiom dump-hir
axiom dump-mir
axiom dump-lir
axiom dump-machine
```

---

# 437.226 — IR dump format

Có hai format:

```text
human-readable
machine-readable
```

---

# 437.227 — AI-readable IR

Machine-readable IR nên có:

```text
function
blocks
instructions
types
source spans
dependencies
effects
```

để AI agent có thể query thay vì đọc toàn bộ compiler source.

---

# 437.228 — Semantic query example

Agent có thể hỏi:

```text
query type_of("foo")
```

trả:

```text
fn(i32, i32) -> i32
```

---

# 437.229 — IR query example

Agent có thể hỏi:

```text
query cfg("foo")
```

trả:

```text
blocks: 4
branches: 2
loops: 1
calls: 3
```

---

# 437.230 — Optimization explanation

Compiler có thể optional report:

```text
"inlined foo into bar"
"removed bounds check"
"stack-promoted allocation"
```

Điều này đặc biệt hữu ích cho AI tooling.

---

# 437.231 — Không để explanation ảnh hưởng codegen

Optimization explanation là diagnostic/telemetry.

Không phải semantic input.

---

# 437.232 — Optimization reproducibility

Cùng:

```text
source
compiler
target
flags
profile
```

phải cho kết quả deterministic.

---

# 437.233 — Parallel optimization determinism

Nếu functions optimize parallel:

```text
thread order
```

không được thay đổi final artifact.

---

# 437.234 — Floating-point reproducibility

Nếu build yêu cầu reproducible floating-point semantics:

```text
FP mode
target features
compiler flags
```

phải được ghi rõ.

---

# 437.235 — IR feature version

Mỗi IR serialization format có:

```text
IRVersion
```

---

# 437.236 — Compiler version compatibility

Không hứa binary compatibility giữa mọi compiler versions.

Cache chỉ valid khi compatibility contract cho phép.

---

# 437.237 — Optimization pass interface

Mỗi pass:

```text
Pass {
    name
    input_ir
    output_ir
    required_analyses
    preserved_analyses
}
```

---

# 437.238 — Analysis cache

Có thể cache:

```text
DominatorTree
LoopInfo
AliasInfo
CallGraph
EffectSummary
```

---

# 437.239 — Analysis invalidation

Nếu pass sửa CFG:

```text
DominatorTree
LoopInfo
```

phải invalidate hoặc update.

---

# 437.240 — Pass manager

Axiom có:

```text
ModulePassManager
FunctionPassManager
MachinePassManager
```

nhưng implementation có thể đơn giản hơn ở bootstrap.

---

# 437.241 — Optimization pipeline configuration

Compiler internal:

```text
-O0 → pipeline A
-O1 → pipeline B
-O2 → pipeline C
-O3 → pipeline D
```

---

# 437.242 — No mandatory LLVM compatibility

Axiom IR không cần:

```text
LLVM IR compatibility
```

---

# 437.243 — Why custom IR

Custom IR cho phép:

- ownership semantics phù hợp Axiom;
- Result/Option;
- deterministic cleanup;
- explicit allocator;
- simpler implementation;
- direct native backend.

---

# 437.244 — IR layering invariant

```text
HIR knows semantics.
MIR knows executable semantic flow.
LIR knows machine-independent operations.
Machine IR knows target machine.
```

Không đảo ngược dependency.

---

# 437.245 — Core IR operations

Bộ core cuối cùng:

```text
Constants
Copies
Moves
Arithmetic
Comparison
Conversions
Aggregate construction/extraction
Load
Store
Address
Call
Return
Branch
Switch
Select
Alloc
Free
MemCopy
MemSet
Atomic
Fence
Drop
Panic
Unreachable
Suspend
```

---

# 437.246 — Hard invariants

1. HIR không chứa machine-specific assumptions.
2. MIR là canonical semantic executable representation.
3. MIR không bắt buộc SSA.
4. LIR dùng SSA.
5. Memory SSA chỉ cần từ optimization/LIR layer.
6. Value và Place tách biệt.
7. Ownership đã được explicit hóa trước backend.
8. Drop semantics không được mất trong lowering.
9. Atomic ordering không được thay đổi tùy tiện.
10. Volatile không được optimize như memory bình thường.
11. Overflow semantics phải được preserve.
12. Floating-point semantics phải được preserve.
13. Unsafe không biến thành implicit safe.
14. Bounds checks chỉ được loại khi có proof.
15. Dynamic dispatch explicit.
16. Generic static dispatch concrete trước backend.
17. ABI lowering trước machine emission.
18. Backend không type-check.
19. Linker không hiểu HIR/MIR.
20. Machine encoder không hiểu source language.
21. Mỗi IR có verifier.
22. Invalid IR không được emit artifact.
23. Optimization không được thay đổi semantics.
24. Parallel optimization phải deterministic.
25. Cache hit phải tương đương cache miss.
26. Debug/source mapping phải được preserve ở mức khả thi.
27. Compiler crash phải tạo đủ information để reproduce.
28. IR không phụ thuộc LLVM.
29. IR đủ nhỏ để bootstrap compiler tự implement.
30. IR đủ mạnh để hỗ trợ native performance ngang hoặc vượt C/C++ trong các workload phù hợp.

---

# BOOTSTRAP-437.247 — Kiến trúc IR Axiom đã khóa

Pipeline compiler hiện đã đủ rõ ở mức implementation:

```text
                    SOURCE
                       │
                       ▼
                    PARSER
                       │
                       ▼
                      AST
                       │
                       ▼
                  SEMANTIC DB
                       │
              ┌────────┼────────┐
              │        │        │
             TYPE    TRAIT   OWNERSHIP
              │        │        │
              └────────┼────────┘
                       ▼
                      HIR
                       │
                       ▼
                      MIR
                 ┌─────┴─────┐
                 │ CFG        │
                 │ Cleanup    │
                 │ Ownership  │
                 └─────┬─────┘
                       ▼
                  SSA / Memory
                       ▼
                      LIR
                       │
          ┌────────────┼────────────┐
          │            │            │
       Inline         DCE        SROA
          │            │            │
          └────────────┼────────────┘
                       ▼
                  ABI LOWERING
                       ▼
                  MACHINE IR
                       │
                  REGISTER ALLOC
                       │
                  INSTRUCTION SEL
                       │
                  MACHINE ENCODE
                       ▼
                    OBJECT
                       ▼
                  AXIOM LINKER
                       ▼
                NATIVE ARTIFACT
```

**BOOTSTRAP-437 hoàn tất.**

---

# BOOTSTRAP-438 — TARGET ISA, MACHINE BACKEND FRAMEWORK & X86-64/AARCH64 CODE GENERATION

Task tiếp theo sẽ khóa phần còn thiếu để compiler thực sự phát machine code:

- Target abstraction;
- CPU feature model;
- x86-64 register model;
- x86-64 instruction selection;
- AArch64 register model;
- AArch64 instruction selection;
- addressing modes;
- immediate encoding;
- branch lowering;
- call/return;
- prologue/epilogue;
- register allocation interface;
- stack frame;
- SIMD;
- atomics;
- TLS;
- PIC/PIE;
- target feature detection;
- machine instruction constraints;
- instruction encoder integration với **BOOTSTRAP-420**;
- golden machine-code tests.

Sau **438**, architecture sẽ đi thẳng vào phần **native object/linker integration và bootstrap compiler implementation** thay vì tiếp tục mở rộng language semantics.