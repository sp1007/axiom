Tiếp tục với **LIR-001 — Axiom Low-Level IR**. Đây là lớp cầu nối giữa MIR đã kiểm chứng và machine code. Mục tiêu là **đủ thấp để tạo native code tốt, nhưng chưa bị khóa vào x86/AArch64**.

# LIR-001 — Axiom Low-Level IR

## 1. Vai trò của LIR

Ta giữ 3 tầng:

```text
MIR
 │
 │ semantic / ownership / capability
 ▼
Axiom LIR
 │
 │ machine-oriented, target-independent
 ▼
Machine IR
 │
 │ target-specific
 ▼
Machine Code
```

### MIR

Biết:

```text
ownership
drop
capability
async state
trait dispatch
generic specialization
pattern
high-level control flow
```

### LIR

Biết:

```text
SSA
basic blocks
virtual registers
memory
load/store
calls
returns
branches
atomic
SIMD
stack slots
ABI
```

### Machine IR

Biết:

```text
x86 registers
AArch64 registers
RISC-V registers
instruction constraints
calling convention registers
instruction encoding constraints
```

**LIR tuyệt đối không biết `rax`, `x0`, `sp`, `xmm0`.**

---

# 2. Nguyên tắc quan trọng nhất

Axiom LIR phải là:

> **SSA-based, typed, explicit-memory, target-independent, close-to-machine.**

Không nên biến nó thành một LLVM clone.

Axiom kiểm soát toàn bộ compiler nên LIR có thể được thiết kế đúng với semantics Axiom thay vì phải hỗ trợ hàng nghìn legacy case.

---

# 3. Một LIR function

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32 {
    return a + b
}
```

có thể trở thành:

```text
fn @add(%a: i32, %b: i32) -> i32 {
entry:
    %r0 = add i32 %a, %b
    ret %r0
}
```

LIR không cần biết `a` và `b` ban đầu đến từ:

```text
rdi
rsi
```

ABI lowering/Machine backend sẽ quyết định sau.

---

# 4. SSA

Axiom LIR dùng SSA.

Một value được định nghĩa đúng một lần:

```text
%a0 = ...
%a1 = ...
%a2 = ...
```

Không:

```text
a = 1
a = 2
a = 3
```

theo nghĩa mutable machine variable.

Mutable source variable:

```axiom
var x = 10

x = x + 1
x = x * 2
```

có thể thành:

```text
%x0 = const 10
%x1 = add %x0, 1
%x2 = mul %x1, 2
```

---

# 5. Nhưng không phải mọi thứ đều SSA value

Đây là điểm quan trọng.

Memory không nên bị giả lập hoàn toàn bằng SSA.

Ví dụ:

```axiom
var x: i32
x = 10
foo(&mut x)
print(x)
```

LIR có:

```text
%slot = stack_slot i32

store %slot, 10

call @foo %slot

%x = load %slot
call @print %x
```

Tức:

```text
SSA → values
Memory → explicit storage
```

---

# 6. Hai loại dữ liệu

LIR phân biệt:

```text
Value
Memory
```

### Value

```text
%i
%f
%ptr
%vector
```

### Memory

```text
stack
global
heap/storage
external
device
```

Không được biến mọi pointer thành một generic integer.

---

# 7. Pointer trong LIR

LIR có pointer type:

```text
ptr<T>
```

nhưng semantics thấp hơn `view<T>`.

Ví dụ:

```text
view<i32>
```

sau verification có thể lower thành:

```text
ptr<i32>
len
```

Capability metadata có thể đã được erase.

Nhưng raw pointer và safe-derived pointer vẫn phải giữ provenance information trong compiler khi cần.

---

# 8. Address space

Không nên chỉ có:

```text
ptr<T>
```

mà internal LIR nên hỗ trợ:

```text
ptr<T, addrspace>
```

Ví dụ:

```text
addrspace::Generic
addrspace::Stack
addrspace::Device
addrspace::Shared
addrspace::Constant
addrspace::External
```

Điều này đặc biệt quan trọng cho GPU.

Source-level programmer không nhất thiết phải nhìn thấy chúng.

---

# 9. Load / Store

Primitive:

```text
%v = load T, %ptr
store T %value, %ptr
```

Metadata:

```text
alignment
volatile
atomic_order
address_space
```

Ví dụ:

```text
%v = load i32, %p align 4
```

---

# 10. Atomic

Không biến atomic thành function call mặc định.

LIR:

```text
%old = atomic_load %p, Acquire
atomic_store %p, %v, Release
%old = atomic_rmw add %p, %x, Relaxed
```

CAS:

```text
%result =
    cmpxchg %p, %expected, %desired,
    success=AcqRel,
    failure=Acquire
```

LIR giữ ordering semantics cho tới backend.

---

# 11. Volatile

Volatile riêng:

```text
%v = volatile_load %p
volatile_store %p, %v
```

Không đồng nhất:

```text
volatile == atomic
```

Vì:

```text
volatile
    = observable machine access

atomic
    = synchronization + atomicity
```

---

# 12. Arithmetic

LIR có primitive rõ:

```text
add
sub
mul
div
rem
neg
```

Integer semantics phải được xác định.

Ví dụ:

```text
add.checked
add.wrap
add.saturate
```

hoặc tốt hơn, MIR đã resolve semantics và LIR opcode phản ánh trực tiếp:

```text
add
add_wrap
add_sat
```

Không để backend tự đoán.

---

# 13. Signed overflow

Không có:

```text
"compiler tùy ý vì UB"
```

trong safe Axiom arithmetic.

Ví dụ:

```text
%i = add.checked %a, %b
```

có thể lower thành:

```text
value + overflow_flag
```

hoặc branch/trap tùy profile.

Optimizer chỉ được bỏ check nếu chứng minh được không thể overflow.

---

# 14. Comparison

LIR:

```text
icmp.eq
icmp.ne
icmp.lt
icmp.le
icmp.gt
icmp.ge
```

Nhưng signed/unsigned phải rõ:

```text
icmp.slt
icmp.ult
```

Ví dụ:

```text
%r = icmp.slt i32 %a, %b
```

---

# 15. Floating point

Tách khỏi integer:

```text
fcmp
fadd
fsub
fmul
fdiv
frem
```

Không được để optimizer tùy tiện coi:

```text
NaN
-0
infinity
```

là integer-like.

Fast-math phải là explicit optimization profile/attribute.

Ví dụ:

```text
@fast_math
```

hoặc function/module optimization policy.

---

# 16. Control Flow

LIR dùng basic blocks:

```text
entry
then
else
merge
```

Ví dụ:

```text
entry:
    %c = icmp.slt %x, 0
    br %c, then, else

then:
    ...
    jump merge

else:
    ...
    jump merge

merge:
    ...
```

---

# 17. Phi

SSA merge:

```text
merge:
    %v = phi [
        (%a, then),
        (%b, else)
    ]
```

Nhưng tôi đề xuất internal representation có thể lưu phi dưới dạng block arguments:

```text
then:
    jump merge(%a)

else:
    jump merge(%b)

merge(%v):
    ...
```

### Lý do

Block arguments thường dễ xử lý hơn trong một số compiler pass:

```text
CFG
SSA construction
lowering
pattern matching
coroutine lowering
```

Do đó:

> **Axiom LIR nên dùng block parameters thay vì phi nodes làm representation chính.**

Khi cần export/debug/interoperate có thể materialize phi.

---

# 18. Function call

```text
%r = call @foo(%a, %b)
```

Call metadata:

```text
calling_convention
tail_call
readonly
no_return
may_unwind
```

Nhưng chỉ những thuộc tính compiler đã chứng minh hoặc source contract cho phép mới được gắn.

---

# 19. Tail call

LIR hỗ trợ:

```text
tailcall @foo(...)
```

Nhưng backend có quyền reject nếu target ABI không hỗ trợ dạng tail call đó.

Source semantic:

```text
tail-recursive
```

có thể được compiler optimize thành loop mà không cần tailcall machine instruction.

---

# 20. Return

```text
ret %value
```

hoặc:

```text
ret_void
```

Nếu ABI đã lower sret:

```text
store result → hidden result pointer
ret_void
```

Nhưng source MIR vẫn giữ:

```text
return BigStruct
```

cho đến ABI lowering.

---

# 21. Unreachable / Trap

LIR:

```text
unreachable
trap
```

Ví dụ:

```text
if impossible_condition {
    trap
}
```

`unreachable` nghĩa:

> CFG path này đã được chứng minh không thể tiếp tục.

Không được dùng `unreachable` chỉ để “giúp optimizer” nếu chưa có semantic proof.

---

# 22. Calls không return

Function:

```axiom
fn abort() -> never
```

LIR:

```text
call @abort
unreachable
```

Hoặc call instruction có:

```text
noreturn
```

---

# 23. Stack allocation

LIR:

```text
%slot = stack_alloc T align N
```

Không phải:

```text
malloc()
```

Stack storage chỉ tồn tại trong function frame.

Nếu compiler thấy:

```text
stack_alloc
store
load
```

không cần address escape, có thể scalarize hoàn toàn.

---

# 24. Dynamic allocation

MIR:

```text
alloc
```

đến LIR:

```text
%p = alloc size, align
```

Nhưng LIR allocation vẫn chưa nhất thiết là:

```text
malloc
```

Backend/runtime có thể lower:

```text
alloc
→ allocator call
→ arena bump
→ stack expansion
→ static pool
→ inline storage
```

---

# 25. Deallocation

```text
dealloc %p
```

Nhưng semantic distinction:

```text
Drop
≠
Dealloc
```

Một Drop có thể:

```text
close(fd)
```

mà không deallocate memory.

LIR chỉ nhận `dealloc` khi storage lifetime thực sự kết thúc.

---

# 26. Lifetime markers

LIR nên có:

```text
lifetime_start %storage
lifetime_end %storage
```

nhưng đây là **compiler metadata**, không phải source semantics.

Chúng giúp:

- stack slot reuse
- register allocation
- DSE
- alias analysis
- sanitizer/debug
- stack coloring

---

# 27. Alias metadata

Axiom có lợi thế lớn vì MIR đã chứng minh capability.

Ví dụ:

```axiom
fn copy(
    src: view<u8>,
    dst: mut_view<u8>
)
```

nếu compiler chứng minh:

```text
DISJOINT(src, dst)
```

LIR có thể gắn:

```text
!noalias
```

cho memory access tương ứng.

Điểm quan trọng:

> `noalias` là **compiler fact được chứng minh**, không phải lời hứa tùy tiện của programmer.

Điều này cho phép vectorization mạnh mà không cần đưa `restrict` vào source language v0.1.

---

# 28. Memory ordering

LIR cần memory effect classification:

```text
Pure
Read
Write
ReadWrite
Atomic
Volatile
Call
Unknown
```

Ví dụ:

```text
add → Pure
load → Read
store → Write
atomic → Atomic
call unknown → Unknown
```

Optimizer dùng nó để reorder instruction an toàn.

---

# 29. Memory barrier

LIR:

```text
fence Acquire
fence Release
fence SeqCst
```

và:

```text
compiler_fence
```

được giữ riêng.

---

# 30. SIMD

LIR không nên có hàng trăm opcode ISA-specific.

Nên có generic:

```text
vector<T, N>
```

và:

```text
vadd
vsub
vmul
vdiv
vload
vstore
shuffle
broadcast
extract
insert
```

Ví dụ:

```text
%v = vadd <4 x f32> %a, %b
```

Target lowering quyết định:

```text
SSE
AVX
AVX2
AVX-512
NEON
SVE
RVV
```

---

# 31. Target intrinsic

Khi generic LIR không đủ:

```text
target_intrinsic "x86.avx2.foo"
```

Nhưng đây phải là escape hatch của backend, không phải API Core phổ biến.

---

# 32. Function attributes

LIR function có thể có:

```text
noreturn
readonly
readnone
willreturn
cold
hot
inline_hint
noinline
alwaysinline
nounwind
```

Nhưng cần phân biệt:

### Semantic guarantee

Ví dụ:

```text
noreturn
```

### Optimization hint

Ví dụ:

```text
inline_hint
```

Không được biến hint thành semantic requirement.

---

# 33. Inline

Source không nên phụ thuộc vào:

```axiom
@inline
```

để đúng semantics.

Có thể có:

```axiom
@inline
@noinline
```

nhưng:

```text
@inline = optimization request
```

không phải:

```text
@inline = semantic guarantee
```

---

# 34. Global

LIR:

```text
global @counter : i64
```

metadata:

```text
mutable
constant
alignment
section
visibility
TLS
linkage
initializer
```

Ví dụ:

```text
tls global @counter : i64
```

---

# 35. Sections

Không nên cho source-level code tự do thao túng ELF/PE section.

System layer có thể:

```axiom
@section(".text.hot")
```

nhưng đó là target-specific/unsafe-level facility.

LIR có:

```text
section = ".text.hot"
```

nếu đã được target layer xác nhận.

---

# 36. Debug information

LIR instruction nên có:

```text
source_location
```

ví dụ:

```text
file
line
column
scope
inline_chain
```

Điều này cho phép:

```text
source
 ↓
MIR
 ↓
LIR
 ↓
Machine instruction
```

và debugger có thể quay về đúng source.

---

# 37. Unwind

LIR giữ:

```text
cleanup edge
unwind edge
```

nhưng không chứa DWARF/SEH instruction.

Ví dụ:

```text
call @foo
normal → next
unwind → cleanup
```

Backend quyết định:

```text
DWARF
SEH
Mach-O unwind
```

---

# 38. Coroutine / async

Sau async lowering:

```axiom
async fn foo()
```

không còn là một magic LIR instruction.

Nó trở thành:

```text
state machine
frame
poll function
resume
suspend
```

Ví dụ:

```text
FutureFoo {
    state
    local_a
    local_b
}
```

LIR thấy:

```text
load state
switch state
...
store state
return Pending
```

Điều này rất phù hợp với mục tiêu runtime optional.

---

# 39. Closure

Closure cũng được lowering trước LIR.

Ví dụ:

```axiom
let x = 10

let f = |y| x + y
```

có thể thành:

```text
struct Closure {
    x: i32
}

fn closure_call(env: *Closure, y: i32) -> i32
```

Sau đó nếu không escape:

```text
Closure
```

có thể bị scalarize/eliminate hoàn toàn.

---

# 40. Dynamic dispatch

`dyn Trait` sau MIR resolution trở thành:

```text
data_ptr
vtable_ptr
```

hoặc target-specific equivalent.

LIR call:

```text
%fn = load_vtable_slot ...
call_indirect %fn, %data
```

Không được phép tự động xuất hiện dynamic dispatch ở LIR nếu source là static dispatch.

---

# 41. Indirect call

```text
call_indirect %fn(%args)
```

phải có function signature:

```text
call_indirect<T>(...)
```

để optimizer/backend biết:

```text
parameter ABI
return ABI
calling convention
```

Không phải generic untyped jump.

---

# 42. Jump table

`match` trên enum/integer có thể lower thành:

```text
switch
```

LIR:

```text
switch %tag {
    0 → case0
    1 → case1
    default → default
}
```

Target lowering quyết định:

```text
branch chain
jump table
binary search
bit test
```

---

# 43. Memory safety đã xong trước LIR

Đây là boundary rất quan trọng:

```text
MIR:
    capability verification
    ownership
    lifetime
    alias
    bounds
```

sau đó:

```text
LIR:
    machine-oriented optimization
```

LIR optimizer **không được phá vỡ invariant đã được MIR chứng minh**.

---

# 44. LIR verification

Mỗi LIR pass phải có verifier.

Ví dụ:

```text
LIRVerifier
```

kiểm tra:

```text
SSA dominance
block terminators
type consistency
valid CFG
memory operand type
atomic ordering
alignment
call signature
ABI consistency
unwind consistency
address-space consistency
```

Compiler development sẽ an toàn hơn rất nhiều nếu:

```text
Pass → Verify → Pass → Verify
```

thay vì:

```text
20 passes → crash
```

---

# 45. Pass architecture

Đề xuất:

```text
LIR
 ↓
Canonicalize
 ↓
SCCP
 ↓
DCE
 ↓
CSE
 ↓
GVN
 ↓
SimplifyCFG
 ↓
LICM
 ↓
Loop optimization
 ↓
Vectorization
 ↓
Memory optimization
 ↓
Inlining
 ↓
Lowering
```

Nhưng không nên khóa thứ tự quá sớm.

Compiler có pass manager:

```text
Pass
Analysis
PreservedAnalysis
InvalidatedAnalysis
```

---

# 46. Analysis cache

Các analysis:

```text
DominatorTree
LoopInfo
AliasAnalysis
MemorySSA
RangeAnalysis
ValueRange
CallGraph
EscapeAnalysis
```

cần cache.

Mỗi pass khai báo:

```text
preserves:
    DominatorTree
    LoopInfo
```

hoặc invalidate.

Điều này sẽ quyết định compiler có thể scale tới các project lớn hay không.

---

# 47. MemorySSA

Axiom nên cân nhắc **MemorySSA** ngay từ thiết kế LIR.

Ví dụ:

```text
store A
store B
load A
```

optimizer cần biết load A phụ thuộc store nào.

MemorySSA giúp:

```text
DSE
load forwarding
LICM
alias optimization
```

mà không cần biến toàn bộ memory thành SSA values.

---

# 48. Escape analysis

Do Axiom đã có memory model mạnh, LIR nên nhận kết quả:

```text
NoEscape
ArgEscape
ReturnEscape
GlobalEscape
UnknownEscape
```

Ví dụ:

```axiom
fn make() -> Vec {
    ...
}
```

không đồng nghĩa heap allocation.

Compiler có thể:

```text
caller stack
register
sret
heap
```

tùy escape.

---

# 49. Allocation optimization

Ví dụ:

```axiom
fn f() -> i32 {
    let x = Box::new(42)
    return *x
}
```

nếu không observable:

```text
Box allocation
→ eliminated
```

LIR cuối:

```text
ret 42
```

Đây là một ví dụ điển hình của:

```text
Abstraction Erasure
```

---

# 50. LIR representation đề xuất

Một function:

```text
LIRFunction {
    signature
    calling_convention
    blocks[]
    values[]
    stack_slots[]
    globals[]
    attributes
    debug_info
}
```

Block:

```text
LIRBlock {
    id
    parameters[]
    instructions[]
    terminator
}
```

Instruction:

```text
LIRInstruction {
    opcode
    operands[]
    result[]
    type
    metadata
    source_location
}
```

---

# 51. Không dùng text IR làm compiler internal representation

Có thể có textual format:

```text
.axlir
```

nhưng compiler internal phải là:

```text
typed graph / arena representation
```

không parse text giữa các pass.

Text IR chỉ phục vụ:

```text
debugging
tests
compiler development
AI inspection
reproduction
```

---

# 52. Axiom LIR textual format

Ví dụ:

```text
fn @add(%a: i32, %b: i32) -> i32 {
entry:
    %r0 = add i32 %a, %b
    ret %r0
}
```

Điểm hay là AI agent có thể đọc rất dễ.

Ta có thể yêu cầu compiler:

```bash
axiomc --emit=lir foo.ax
```

và:

```bash
axiomc --verify=lir foo.ax
```

---

# 53. Machine-independent optimization

LIR là nơi lý tưởng để làm:

```text
constant folding
constant propagation
DCE
CSE
GVN
SCCP
CFG simplification
loop invariant code motion
escape analysis
allocation elimination
memory optimization
vectorization
```

Machine IR mới làm:

```text
instruction selection
register allocation
peephole
scheduling
```

---

# 54. Register model

LIR chỉ có:

```text
virtual register
```

Ví dụ:

```text
%v0
%v1
%v2
```

Có register classes:

```text
Integer
Float
Vector
Predicate
Address
```

nhưng không có physical register.

---

# 55. Register constraints

Một số instruction cần constraint:

```text
division
special multiply
SIMD instruction
atomic
calling convention
```

LIR có thể biểu diễn:

```text
requires register class X
```

Machine backend mới map:

```text
%v0 → rax
%v1 → rcx
```

---

# 56. Stack slots

Register allocator có thể spill:

```text
%v7
```

thành:

```text
stack_slot #3
```

Nhưng stack slot phải được quản lý bởi backend.

LIR trước register allocation có thể chỉ cần:

```text
alloca/stack_slot
```

còn spill slot được tạo ở Machine IR.

---

# 57. LIR không nên quá thấp

Không đưa vào LIR:

```text
x86 LEA
x86 MOV
ARM ADRP
ARM LDR literal
RISC-V AUIPC
```

Đó là Machine IR.

Nếu LIR đã chứa những thứ này:

> LIR không còn target-independent nữa.

---

# 58. LIR cũng không nên quá cao

Không giữ:

```text
Trait
Ownership
Option
Result
async/await
match
closure
generic
```

ở LIR.

Những thứ đó phải được lower trước.

---

# 59. Boundary chính thức

Tôi đề xuất đóng boundary:

```text
                 HIGH LEVEL
                     │
                     ▼
                    MIR
                     │
          semantic verification
                     │
                     ▼
               VERIFIED MIR
                     │
          semantic lowering
                     │
                     ▼
                    LIR
                     │
       target-independent optimization
                     │
                     ▼
               LEGALIZED LIR
                     │
        target-specific lowering
                     │
                     ▼
               MACHINE IR
                     │
          register allocation
                     │
                     ▼
              FINAL MACHINE IR
                     │
                     ▼
              MACHINE ENCODER
```

---

# 60. Invariants LIR

Chốt nhóm:

### ALIR-20
**LIR Is SSA-Based**

### ALIR-21
**Memory Is Explicitly Represented**

### ALIR-22
**SSA Values Are Distinct From Memory Storage**

### ALIR-23
**LIR Is Target Independent**

### ALIR-24
**Physical Registers Do Not Exist In Generic LIR**

### ALIR-25
**Machine Registers Exist Only In Machine IR**

### ALIR-26
**LIR Preserves ABI Contracts**

### ALIR-27
**LIR Preserves Atomic Ordering**

### ALIR-28
**Volatile Is Distinct From Atomic**

### ALIR-29
**Integer Overflow Semantics Are Explicit**

### ALIR-30
**Floating-Point Semantics Are Explicit**

### ALIR-31
**Pointer Values Are Not Integers**

### ALIR-32
**Address Spaces Are Explicit Where Required**

### ALIR-33
**Safe Capability Verification Completes Before LIR**

### ALIR-34
**LIR Optimization Cannot Invalidate Verified Semantics**

### ALIR-35
**Proven Alias Facts May Be Lowered Into Optimization Metadata**

### ALIR-36
**No Source-Level Restrict Is Required**

### ALIR-37
**Aggregate Return May Already Be ABI-Lowered**

### ALIR-38
**SRet Is Represented Explicitly After ABI Lowering**

### ALIR-39
**Allocation Is Explicit But Not Necessarily Heap Allocation**

### ALIR-40
**Drop And Deallocation Are Distinct**

### ALIR-41
**Async Is Lowered Before Generic LIR**

### ALIR-42
**Closures Are Lowered Before Generic LIR**

### ALIR-43
**Generic Static Dispatch Is Eliminated Before LIR**

### ALIR-44
**Dynamic Dispatch Remains Explicit**

### ALIR-45
**Every Basic Block Has One Terminator**

### ALIR-46
**Block Parameters Form The Canonical SSA Merge Representation**

### ALIR-47
**Every LIR Function Is Independently Verifiable**

### ALIR-48
**Optimization Hints Cannot Change Program Semantics**

### ALIR-49
**Target-Specific Instructions Require Explicit Target Intrinsics**

### ALIR-50
**LIR Textual Form Is Debug/Inspection Format, Not Required Internal Representation**

---

# 61. Một thay đổi kiến trúc đáng giá

Với thiết kế này, Axiom không cần một IR duy nhất kiểu “làm tất cả”.

Ta có:

```text
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
LIR
 ↓
Machine IR
```

Mỗi IR có **một trách nhiệm rất rõ**.

Đây là hướng phù hợp với mục tiêu của bạn: compiler có thể cực kỳ phức tạp bên trong nhưng programmer chỉ nhìn thấy một ngôn ngữ tương đối đơn giản.

---

# Tiếp theo: MACHINE-IR-001

Bây giờ đã đủ nền tảng để đi vào phần khó nhất của native compiler:

**Machine IR + instruction selection + register allocation + ABI register assignment.**

Ta sẽ phải quyết định:

```text
Machine IR
    ↓
Instruction Selection
    ↓
Legalization
    ↓
Register Classes
    ↓
Physical Registers
    ↓
Register Allocation
    ↓
Spill/Reload
    ↓
Instruction Scheduling
    ↓
Peephole
    ↓
Machine Encoding
```

và đặc biệt thiết kế sao cho **Axiom có thể tự sinh x86-64 machine code mà không cần LLVM**, sau đó mở rộng sang **AArch64/RISC-V/WASM**. Đây sẽ là nền móng thực sự cho mục tiêu cuối cùng: **Axiom tự biên dịch thành native executable độc lập với compiler/toolchain bên ngoài**.