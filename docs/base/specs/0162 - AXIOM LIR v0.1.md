Tiếp tục theo đúng thứ tự. Bây giờ chúng ta chốt **AXIOM LIR v0.1** và ranh giới giữa semantic MIR với machine backend.

Đây là bước rất quan trọng: nếu LIR thiết kế sai, Axiom sẽ dễ bị khóa vào x86-64 hoặc vô tình biến compiler thành “LLVM frontend”. Mục tiêu của Axiom là **tự chủ backend**, nên LIR phải đủ thấp để sinh machine code trực tiếp nhưng vẫn đủ trừu tượng để hỗ trợ x86-64, ARM64, RISC-V, WASM…

# AXIOM LIR v0.1

## 1. Vai trò của LIR

Pipeline chính thức:

```text
Source
  ↓
AST
  ↓
HIR
  ↓
Typed HIR
  ↓
Ownership / Capability
  ↓
MIR
  ↓
Verified MIR
  ↓
Semantic Optimization
  ↓
LIR
  ↓
Target Lowering
  ↓
Machine IR
  ↓
Register Allocation
  ↓
Machine Encoding
  ↓
Object
  ↓
Link
  ↓
Native Binary
```

MIR trả lời:

> **Chương trình có nghĩa gì?**

LIR trả lời:

> **Chương trình cần những thao tác máy tính nào?**

Machine IR trả lời:

> **CPU cụ thể thực hiện chúng bằng instruction nào?**

---

# 2. LIR không phải LLVM IR

Axiom không nên:

```text
Axiom → LLVM IR → LLVM
```

vì như vậy LLVM trở thành một phần semantic architecture của Axiom.

Thay vào đó:

```text
Axiom MIR
     ↓
Axiom LIR
     ↓
Axiom Machine IR
     ↓
Axiom Encoder
```

LLVM có thể được dùng **tùy chọn trong bootstrap compiler** để kiểm chứng hoặc benchmark backend, nhưng không phải dependency của kiến trúc cuối cùng.

---

# 3. LIR phải giữ những gì?

LIR cần giữ:

```text
Virtual registers
Memory operations
Branches
Calls
Returns
Atomics
Address calculations
ABI information
Calling convention
Function attributes
Target-independent constraints
```

Không còn:

```text
Trait
Generic
Ownership
Capability
Pattern
Method resolution
High-level async
```

Những thứ đó phải biến mất trước LIR.

---

# 4. LIR không còn ownership

Ví dụ MIR:

```text id="gcvk2n"
MOVE x
DROP y
VIEW x
```

Sau Verified MIR và semantic lowering:

```text id="0x7f2f"
MOV
LOAD
STORE
CALL
```

Ownership facts đã hoàn thành nhiệm vụ.

LIR không cần biết:

```text id="r3z0cf"
“x đang Owned”
```

trừ khi thông tin đó cần thiết cho debug hoặc optimizer metadata.

---

# 5. Virtual Register

LIR sử dụng virtual register:

```text id="f0qg2s"
v0
v1
v2
v3
```

Ví dụ:

```text id="zhd7yd"
v0 = CONST 10
v1 = CONST 20
v2 = ADD v0, v1
RETURN v2
```

Chưa có:

```text id="h2q7nj"
RAX
RBX
X0
X1
```

Register allocation xử lý sau.

---

# 6. Register Class

LIR nên có register class target-independent:

```text id="j4s3bl"
Int
Float
Vector
Predicate
Address
Aggregate
```

Không nên định nghĩa:

```text id="t0l5ya"
RAX
RCX
XMM0
```

ở LIR.

Target backend map:

```text id="p2m8d7"
LIR RegisterClass
       ↓
Target RegisterClass
       ↓
Physical Register
```

---

# 7. Primitive LIR Types

LIR không cần toàn bộ Axiom type system.

Chỉ cần machine-relevant types:

```text id="8o4rhl"
I8
I16
I32
I64
U8
U16
U32
U64

F32
F64

PTR
V128
V256
V512

FLAGS / CONDITION
```

Aggregate lớn được scalarize hoặc lower thành memory.

---

# 8. Address Representation

LIR cần một abstraction:

```text id="5a8j17"
Address {
    base: Register?
    index: Register?
    scale: 1|2|4|8
    offset: i64
    symbol: Symbol?
}
```

Ví dụ:

```text id="r5zqzv"
LOAD
    [base=v0 + index=v1 * 4 + offset=8]
```

x86-64 có thể map trực tiếp.

ARM64/RISC-V sẽ legalize thành nhiều instruction nếu cần.

---

# 9. Memory Operations

Core:

```text id="l4x3ib"
LOAD
STORE

LOAD8
LOAD16
LOAD32
LOAD64

STORE8
STORE16
STORE32
STORE64
```

Không cần nhất thiết tách mọi variant trong semantic MIR.

LIR mới cần kích thước chính xác.

---

# 10. Alignment

Mỗi memory operation có metadata:

```text id="o1f5gi"
alignment
volatile
atomic
address_space
```

Ví dụ:

```text id="g1n2jw"
LOAD {
    type: I32
    alignment: 4
    volatile: false
    address_space: Host
}
```

---

# 11. Volatile

Volatile phải tồn tại riêng:

```text id="5r8w7f"
VOLATILE_LOAD
VOLATILE_STORE
```

Không được coi:

```text id="8njmve"
volatile == atomic
```

Hai semantic hoàn toàn khác nhau.

---

# 12. Atomic LIR

LIR:

```text id="1t8d1j"
ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS
FENCE
```

Metadata:

```text id="3x4h5n"
ordering
scope
size
address_space
```

Ví dụ:

```text id="8p7kq4"
ATOMIC_CAS
    addr=v0
    expected=v1
    desired=v2
    success=AcqRel
    failure=Acquire
```

Target lowering quyết định instruction cụ thể.

---

# 13. Không để backend tự hiểu Axiom memory model

Đây là boundary quan trọng.

MIR:

```text id="qv55kl"
ATOMIC_CAS
```

đã có semantic ordering.

LIR vẫn phải giữ ordering cho đến khi target lowering chứng minh mapping hợp lệ.

Không được:

```text id="n3d5kk"
backend:
“CAS thì cứ dùng instruction mặc định”
```

---

# 14. Control Flow

LIR:

```text id="5dd4co"
JMP
BR
SWITCH
RETURN
TRAP
UNREACHABLE
```

Conditional branch dùng condition code abstraction:

```text id="2m8n3k"
EQ
NE
LT
LE
GT
GE
ULT
ULE
UGT
UGE
```

---

# 15. Compare

LIR:

```text id="x4s2f8"
CMP
```

tạo:

```text id="f9z7pu"
Condition
```

Ví dụ:

```text id="8k6p9n"
v2 = CMP_LT v0, v1
BR v2, bb_true, bb_false
```

Target backend có thể fuse:

```text id="3o7f1a"
CMP + BR
```

thành một instruction sequence tối ưu.

---

# 16. Arithmetic

Core:

```text id="g2h0m4"
ADD
SUB
MUL
DIV
REM

AND
OR
XOR
SHL
SHR

NEG
NOT
```

Nhưng overflow semantics phải được xử lý trước đó.

Ví dụ Axiom:

```text id="0q7r8n"
checked +
wrapping +%
saturating +|
```

LIR cần biết semantics tương ứng.

Có thể biểu diễn:

```text id="k2z4j1"
ADD_CHECKED
ADD_WRAP
ADD_SAT
```

trước khi target legalization.

---

# 17. Checked arithmetic

Ví dụ:

```text id="3z1f6c"
v2 = ADD_CHECKED v0, v1
```

Có thể lower:

```text id="j9m0h5"
v2 = ADD v0, v1
overflow = ...
BR overflow, panic, continue
```

Hoặc x86:

```text id="v4m8c2"
ADD
JO
```

Backend quyết định.

---

# 18. Saturating arithmetic

Target có instruction saturation:

```text id="d2w8k5"
SAT_ADD
```

thì dùng trực tiếp.

Target không có:

```text id="j5z0la"
CMP
ADD
SELECT
```

LIR giữ semantic:

> kết quả phải saturate.

---

# 19. Calls

LIR:

```text id="3n8q4v"
CALL
```

với:

```text id="g1k5qa"
callee
args
return_values
calling_convention
attributes
```

Ví dụ:

```text id="q8x4p0"
CALL @foo
    args=[v0, v1]
    returns=[v2]
    cc=axiom
```

---

# 20. Calling Convention

Tách:

```text id="2f8y4w"
Function Type
        ↓
ABI Lowering
        ↓
Calling Convention
```

Các convention:

```text id="b8m1sa"
axiom
C
system
target-specific
```

LIR không tự suy ra C ABI từ function type.

ABI lowering đã quyết định:

```text id="c1v5k9"
argument registers
stack arguments
return registers
aggregate passing
aggregate return
callee/caller saved
alignment
```

---

# 21. Aggregate ABI

Ví dụ:

```axiom id="ax5r7c"
fn make() -> Vec4
```

ABI có thể:

```text id="k7v3nd"
return in registers
```

hoặc:

```text id="f1n8zp"
hidden sret pointer
```

LIR đã nhận kết quả sau ABI lowering.

Do đó backend không cần hiểu Axiom struct semantics.

---

# 22. `sret`

Nếu target ABI yêu cầu caller-provided return storage:

```text id="1q8v3a"
CALL foo
    sret = v0
```

Điều này phù hợp với nguyên tắc trước đây:

> Caller-allocated returns được phép.

Không cần heap allocation.

---

# 23. Tail Call

LIR nên hỗ trợ:

```text id="r4m6j2"
TAIL_CALL
```

nhưng semantic eligibility phải được xác định trước/ở ABI lowering.

Backend có thể biến thành:

```text id="3g7k0s"
JMP callee
```

nếu ABI cho phép.

---

# 24. Inline Assembly

Không đưa inline asm thành “string instruction”.

LIR:

```text id="f8p2q1"
INLINE_ASM {
    template
    inputs
    outputs
    clobbers
    memory_effect
}
```

Machine backend chịu trách nhiệm encode.

Compiler vẫn biết:

```text id="w2z6m9"
read memory?
write memory?
register clobber?
control-flow?
```

---

# 25. Function Attributes

LIR có metadata:

```text id="3n7b5v"
noinline
alwaysinline
cold
hot
noreturn
readonly
writeonly
readnone
nounwind
nosuspend
```

Nhưng cần phân biệt:

> Một số là **compiler facts**, một số là **user contract**.

Không được tự gán `readonly` nếu compiler chưa chứng minh.

---

# 26. Memory Effect

LIR call:

```text id="9v3f6k"
CALL foo
```

có:

```text id="5x8r1c"
MemoryEffect:
    None
    Read
    Write
    ReadWrite
    Unknown
```

Càng chính xác càng tốt.

Nhưng compiler không được giả định foreign function là pure nếu không có contract.

---

# 27. Stack Frame

LIR **không nên trực tiếp quyết định stack offset cuối cùng**.

Có:

```text id="9w5r3k"
StackObject {
    id
    size
    alignment
    lifetime
    kind
}
```

Register allocator / frame layout sẽ quyết định:

```text id="v2f7q8"
[rbp-32]
[sp+64]
```

hoặc omit hoàn toàn.

---

# 28. Stack Object vs Heap

LIR không cần gọi:

```text id="1n4w8z"
HEAP_ALLOC
```

nếu semantic allocation không yêu cầu heap.

Thay vào đó:

```text id="2j9m6p"
STACK_OBJECT
DYNAMIC_ALLOC
STATIC_ADDRESS
```

được sinh trong target lowering từ MIR semantic storage.

---

# 29. Escape Optimization

Ví dụ:

```axiom id="a7m3k1"
fn make() -> Box<Vec2>
```

Nếu address không observable và semantics cho phép, optimizer có thể:

```text id="g8v4p2"
eliminate allocation
```

LIR cuối cùng có thể chỉ:

```text id="r1d6x9"
RETURN registers
```

Đây là một trong các optimization rất quan trọng cho mục tiêu hiệu năng của Axiom.

---

# 30. Vector/SIMD

LIR hỗ trợ:

```text id="p8c4t7"
V128
V256
V512
```

operations:

```text id="w2f5m9"
VADD
VSUB
VMUL
VDIV
VAND
VOR
VXOR
VSHL
VSHR

VLOAD
VSTORE
VSHUFFLE
VPERMUTE
```

Target không có vector width tương ứng thì legalizer chia nhỏ.

---

# 31. Auto-vectorization

Không cần source syntax:

```text id="4j6m8n"
@vectorize
```

Optimizer có thể phát hiện:

```text id="0x8z2c"
for i in 0..n {
    a[i] += b[i]
}
```

và biến thành:

```text id="k4v9p1"
vector loop
```

LIR chỉ nhận vector operations sau optimization.

---

# 32. Address Spaces

LIR cần giữ:

```text id="8z2m4x"
Generic
Host
Device
Shared
Local
Private
Constant
External
```

đặc biệt cho GPU.

CPU backend thường collapse chúng thành generic address space nếu semantics cho phép.

GPU backend thì không.

---

# 33. GPU Kernel

Ví dụ:

```axiom id="j6x3p8"
@kernel
fn add(...)
```

sau lowering:

```text id="h4k7m2"
LIR Function {
    execution_domain = GPU
}
```

và memory operations có address space:

```text id="x9q1v5"
LOAD Device
STORE Device
```

Do đó một LIR có thể phục vụ cả CPU và GPU mà không nhét GPU semantics vào frontend.

---

# 34. Function-level target properties

Ví dụ:

```text id="5q8v2j"
FunctionTargetInfo {
    cpu_features
    execution_domain
    abi
    calling_convention
    address_spaces
}
```

Ví dụ:

```text id="r6m3k9"
x86-64:
    SSE2
    AVX2
```

Không nên hard-code trong generic optimizer.

---

# 35. Target Legalization

Đây là boundary:

```text id="9z5k1q"
Axiom LIR
    ↓
Target Legalizer
    ↓
Legal LIR
```

Ví dụ LIR:

```text id="v4m7s2"
I128_ADD
```

x86-64 không có scalar i128 native instruction.

Legalizer có thể biến thành:

```text id="b3q8n6"
ADD64 low
ADC64 high
```

ARM64 cũng có sequence tương ứng.

---

# 36. Machine IR

Sau legalization:

```text id="h1x7c4"
Legal LIR
   ↓
Machine IR
```

Machine IR có:

```text id="m9q3v5"
physical/virtual registers
target instructions
register constraints
immediates
addressing modes
flags
implicit operands
```

Ví dụ x86:

```text id="s4k8n1"
ADD64
RAX
RBX
```

ARM:

```text id="z6p2w8"
ADD
X0
X1
X2
```

---

# 37. Register Allocation

Pipeline:

```text id="k7m2d4"
Machine IR
 ↓
liveness
 ↓
interference / allocation
 ↓
physical registers
 ↓
spill/reload
```

Có thể hỗ trợ:

```text id="1w8q5a"
linear scan
graph coloring
PBQP
target-specific allocator
```

MVP nên chọn **linear scan** trước để compiler chạy được, sau đó thêm allocator tốt hơn.

---

# 38. Spill

Nếu hết register:

```text id="c8r1m5"
v17
```

có thể:

```text id="y4q9n2"
STORE [stack+32]
...
LOAD v17
```

Spill/reload phải xảy ra sau register allocation.

---

# 39. Instruction Selection

Có thể dùng:

```text id="m3v7k2"
pattern matching
```

Ví dụ:

```text id="x1z8q4"
ADD
LOAD
```

→ x86:

```text id="p6n2w9"
ADD rax, [rbx+8]
```

Không nhất thiết phải tạo:

```text id="LOAD temp
ADD temp
```

nếu target cho phép memory operand.

---

# 40. LIR Optimizer và Machine Optimizer khác nhau

### LIR optimizer

Target-independent:

```text id="8j3q6v"
constant folding
CSE
DCE
GVN
LICM
loop transforms
alias analysis
inlining
SROA
vectorization
```

### Machine optimizer

Target-specific:

```text id="7q4m9k"
instruction scheduling
peephole
register coalescing
target idioms
microarchitecture tuning
```

---

# 41. Không over-engineer LIR

LIR v0.1 **không cần**:

```text id="p3r7x1"
GC safepoints
exception landing pads
object headers
vtable primitives
language-level coroutine objects
borrow metadata
trait solver metadata
```

Chỉ đưa vào nếu target ABI/runtime thực sự cần.

---

# 42. LIR Serialization

Có canonical textual format:

```text id="c5m8q2"
axiom-lir 0.1

fn add(i32, i32) -> i32 {
bb0:
    v0 = arg 0
    v1 = arg 1
    v2 = add.i32 v0, v1
    return v2
}
```

Và:

```text id="d7x2n5"
.alir
```

Binary cache.

---

# 43. LIR invariants

```text id="f9w3k7"
ALIR-20
Every LIR value has a machine-relevant type.

ALIR-21
Every virtual register has exactly one register class.

ALIR-22
Every memory operation has explicit size/alignment semantics.

ALIR-23
Atomic operations retain ordering until target lowering.

ALIR-24
Volatile is distinct from atomic.

ALIR-25
Calls have explicit calling convention.

ALIR-26
Aggregate ABI lowering is explicit.

ALIR-27
No ownership semantics remain required for correctness.

ALIR-28
No unresolved high-level type semantics remain.

ALIR-29
LIR is target-independent before legalization.

ALIR-30
Target legalization preserves LIR semantics.

ALIR-31
Machine IR may introduce target-specific instructions.

ALIR-32
Register allocation does not change program semantics.

ALIR-33
Spill/reload preserves value semantics.

ALIR-34
Instruction selection preserves observable behavior.

ALIR-35
LIR serialization is deterministic.
```

---

# 44. Repository

Chốt:

```text id="q2m8x6"
compiler/lir/
├── value.ax
├── type.ax
├── instruction.ax
├── memory.ax
├── atomic.ax
├── call.ax
├── control.ax
├── function.ax
├── stack.ax
├── builder.ax
├── verify.ax
├── serialize.ax
└── tests/

compiler/backend/
├── lowering/
├── isel/
├── machine/
├── regalloc/
├── spill/
├── schedule/
└── encode/
```

Target:

```text id="b8k3r6"
targets/
├── x86_64/
│   ├── target/
│   ├── abi/
│   ├── legalize/
│   ├── isel/
│   ├── machine/
│   ├── regalloc/
│   ├── encoder/
│   └── elf/
│
├── aarch64/
├── riscv64/
├── wasm32/
└── ...
```

---

# 45. Backend MVP

Không làm tất cả target ngay.

Tôi đề xuất:

```text id="m5v2q8"
Target #1
x86_64 Linux ELF
```

vì nó cho phép kiểm chứng gần như toàn bộ native pipeline:

```text
Axiom
 ↓
MIR
 ↓
Verified MIR
 ↓
LIR
 ↓
x86_64 Machine IR
 ↓
register allocation
 ↓
machine encoding
 ↓
ELF object
 ↓
linker
 ↓
native ELF
```

Sau đó:

```text id="p7n4x1"
x86_64 Windows PE/COFF
        ↓
AArch64
        ↓
RISC-V64
        ↓
WASM
        ↓
Mach-O
```

---

# 46. Nhưng có một điểm còn quan trọng hơn backend

Đừng viết linker ngay.

Trước tiên cần:

```text id="a6q2m9"
Machine Encoder
        ↓
Object Writer
```

sinh được:

```text id="0s7d3k"
ELF relocatable object
```

Sau đó mới xây linker.

Ví dụ:

```text
foo.ax
 ↓
foo.o

bar.ax
 ↓
bar.o

foo.o + bar.o
 ↓
Axiom Linker
 ↓
program
```

Điều này giúp cô lập bug.

---

# 47. Native bootstrap milestone

Đây sẽ là milestone cực lớn:

```text id="BOOT-001"

fn main() {
    ...
}
```

→

```text id="4q8m2w"
ELF executable
```

**không LLVM**

**không GCC**

**không Clang**

**không external compiler**

Chỉ có:

```text id="x9m4c7"
Axiom frontend
Axiom MIR
Axiom LIR
Axiom x86 backend
Axiom encoder
Axiom object writer
Axiom linker
minimal startup
```

Đây mới là lúc tuyên bố kiến trúc compiler Axiom thực sự đã đứng độc lập.

---

# 48. Thứ tự implementation sau LIR

Tôi chốt roadmap compiler backend như sau:

```text
LIR-001
LIR data model

LIR-002
LIR verifier

LIR-003
MIR → LIR lowering

X86-001
x86-64 target description

X86-002
x86-64 ABI

X86-003
instruction selection

X86-004
machine IR

X86-005
register allocation

X86-006
spill/reload

X86-007
instruction encoder

OBJ-001
ELF object writer

LINK-001
minimal ELF linker

BOOT-001
native hello world

BOOT-002
multi-module native program

BOOT-003
C FFI

BOOT-004
stdlib bootstrap
```

---

# 49. Và ngay sau đó mới đến Optimizer “thực chiến”

Một điều tôi muốn điều chỉnh so với roadmap trước:

**Không nên xây optimizer lớn trước khi có một backend chạy được.**

Nên có:

```text id="8c2k6v"
MIR
 ↓
LIR
 ↓
x86
 ↓
ELF
 ↓
executable
```

trước.

Sau đó:

```text id="4m7x1p"
Semantic Optimizer v0.1
```

và có thể benchmark:

```text
-O0
-O1
-O2
-O3
-Os
```

Từ đó mới biết Axiom thực sự đạt tới đâu so với C/C++/Rust/Go chứ không chỉ dựa trên lý thuyết.

---

## Bước tiếp theo

Sau khi LIR đã được khóa, **khối tiếp theo nên là `x86-64 Backend v0.1`**, bắt đầu từ **Target Description + ABI + instruction encoding**, với mục tiêu cụ thể đầu tiên:

```text
fn main() {
    return
}
```

→ **Axiom tự sinh ELF64 executable hoàn chỉnh bằng machine code của chính nó**, chưa cần optimizer, chưa cần stdlib lớn.

Đây là vertical slice đầu tiên chứng minh toàn bộ kiến trúc Axiom từ source → native binary.