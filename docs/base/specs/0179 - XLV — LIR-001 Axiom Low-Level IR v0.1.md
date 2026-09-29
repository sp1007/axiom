# XLV — LIR-001: Axiom Low-Level IR v0.1

Đây là bước chuyển từ **semantic compiler** sang **machine compiler**.

Từ đây Axiom có hai thế giới rất rõ:

```text
Semantic world
Source
 → AST
 → HIR
 → Typed HIR
 → Ownership
 → Capability
 → Drop
 → MIR
 → Verified MIR

Machine world
Verified MIR
 → LIR
 → Machine IR
 → Register Allocation
 → Encoding
 → Object
```

**LIR không được biết `ownership`, `view`, `trait`, `generic`, `Option`, `Result`... là gì.** Những khái niệm đó đã được giải quyết hoặc lower trước LIR.

---

# 1. Vai trò chính xác của LIR

LIR là:

> Target-neutral machine-oriented IR, đủ thấp để backend phát sinh machine code trực tiếp, nhưng chưa phụ thuộc ISA cụ thể.

Nó không phải LLVM IR clone.

Pipeline:

```text
Verified MIR
     │
     │ semantic lowering
     ↓
   Axiom LIR
     │
     │ target lowering / legalization
     ↓
Machine IR
     │
     ↓
Register Allocation
     │
     ↓
Encoded Machine Instructions
```

---

# 2. Tại sao cần LIR?

Nếu từ MIR đi thẳng x86:

```text
MIR → x86
```

backend sẽ phải hiểu quá nhiều semantic:

```text
Drop
Ownership
Capability
Generic
Enum
Async
Trait
```

Điều đó làm backend trở thành một compiler frontend thứ hai.

LIR tạo boundary:

```text
Frontend/semantic compiler
        │
        │ Verified MIR
        ▼
========================
        LIR
========================
        │
        ▼
Target backend
```

Backend chỉ quan tâm:

```text
register
memory
branch
call
ABI
atomic
instruction legality
```

---

# 3. LIR không phải SSA thuần

Chốt:

> LIR sử dụng virtual registers + CFG, nhưng cho phép memory locations và mutable storage.

Ví dụ:

```text id="1p4xby"
%v0 = CONST i32 10
%v1 = CONST i32 20
%v2 = ADD %v0, %v1
RETURN %v2
```

Nhưng stack/local storage vẫn có thể tồn tại:

```text id="7td8vo"
STACK_OBJECT
LOAD
STORE
```

Optimizer có thể biến memory thành registers.

---

# 4. LIR value categories

LIR chỉ cần một số machine-oriented types.

```text id="dd42ft"
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

FLAGS
PREDICATE
```

Có thể giữ signedness ở operation/type metadata khi cần.

Không còn:

```text id="dplp2t"
Text
Vec<T>
Option<T>
Result<T,E>
UserStruct
Trait
view<T>
mut_view<T>
```

Các loại đó đã được representation lowering.

---

# 5. Aggregate

Aggregate không biến mất ngay.

Ví dụ:

```axiom id="9ccjka"
struct Vec2 {
    x: f32
    y: f32
}
```

Verified MIR có aggregate semantics.

LIR có thể biểu diễn:

```text id="fpt7gq"
AggregateValue {
    fields
}
```

hoặc scalarized:

```text id="5i3ksd"
%vx = ...
%vy = ...
```

Optimizer quyết định.

Do đó LIR cần hỗ trợ **Aggregate/Address** đủ lâu để không ép backend phải hiểu source struct.

---

# 6. Virtual registers

LIR register:

```text id="w9t1mm"
VReg {
    id
    class
    type
}
```

Register classes:

```text id="1o4mjm"
Int
Float
Vector
Predicate
Address
```

Ví dụ:

```text id="1p80co"
%v0 : I64
%v1 : I64
%v2 : I64
```

Backend sau này mapping:

```text id="qj4j2m"
%v0 → RDI
%v1 → RSI
%v2 → RAX
```

---

# 7. Không dùng physical register trong LIR

Không:

```text id="odn4ye"
RAX = ...
```

ở LIR.

Chỉ:

```text id="3j7jfj"
%v0 = ...
```

Physical registers chỉ xuất hiện ở Machine IR.

Điều này cho phép cùng một LIR chạy:

```text id="7ysh3v"
x86-64
ARM64
RISC-V
WASM
```

---

# 8. Memory operand

LIR cần memory abstraction:

```text id="kgn2tb"
MemoryAddress {
    base: Option<VReg>
    index: Option<VReg>
    scale: 1 | 2 | 4 | 8
    offset: i64
    symbol: Option<SymbolRef>
}
```

Ví dụ:

```text id="5b1s3u"
[base + index * 8 + 16]
```

Đây là abstraction gần machine nhưng chưa x86-specific.

ARM64 backend có thể legalize thành instruction khác.

---

# 9. LOAD

```text id="2w45u4"
%v1 = LOAD I32 [addr]
```

Metadata:

```text id="7dyu5o"
size
alignment
volatile
memory_order
address_space
```

Không mặc định volatile.

---

# 10. STORE

```text id="mlz4kk"
STORE I32 [addr], %v1
```

LIR phải biết:

```text id="x5ax5x"
alignment
size
address space
```

để backend không tạo access sai alignment.

---

# 11. Volatile

Volatile phải riêng:

```text id="x2vpxj"
VOLATILE_LOAD
VOLATILE_STORE
```

Không dùng:

```text id="14i1qb"
LOAD + volatile=true
```

như một optimization hint đơn thuần.

Volatile có semantic memory effect.

---

# 12. Atomics

LIR giữ atomic semantics:

```text id="f5tr4u"
ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS
FENCE
```

Ví dụ:

```text id="2p0t7a"
%v = ATOMIC_LOAD ptr, Acquire
```

Backend x86/ARM64 sẽ lower ordering phù hợp.

---

# 13. Arithmetic

LIR có:

```text id="x9d7lv"
ADD
SUB
MUL
DIV
REM
```

nhưng checked/wrapping/saturating phải được biểu diễn trước khi semantics bị mất.

Có hai hướng.

### Cách 1

```text id="d9b4ah"
ADD_CHECKED
ADD_WRAP
ADD_SAT
```

### Cách 2

Lower checked/saturating thành sequence.

Chốt cho v0.1:

> **Giữ semantic opcode ở đầu LIR; legalizer mới lower thành machine sequence.**

Ví dụ:

```text id="zknb3m"
ADD_CHECKED i32
```

x86 backend có thể:

```text
ADD
JO overflow_block
```

---

# 14. Wrapping arithmetic

```text id="g7m2jj"
ADD_WRAP
```

có thể trực tiếp:

```text id="j16o9q"
ADD
```

vì integer machine arithmetic thường tự wrap.

Nhưng optimizer không được giả định mọi target đều giống nhau trước legalize.

---

# 15. Saturating arithmetic

```text id="7e0kq7"
ADD_SAT
```

x86 có thể dùng:

```text
PADDS*
```

đối với vector hoặc sequence cho scalar.

Backend quyết định.

---

# 16. Comparison

LIR:

```text id="w5ys5x"
CMP
```

produces:

```text id="h6o8qf"
CONDITION
```

Conditions:

```text id="e5b2i8"
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

Không encode x86 flags ở LIR.

---

# 17. Branch

```text id="2x4oj5"
BRANCH condition, true_block, false_block
```

Backend x86:

```text
CMP
JE
```

hoặc:

```text
TEST
JNE
```

---

# 18. Return

```text id="wxm4lh"
RETURN [%v0]
```

ABI lowering sau đó quyết định:

```text id="tw9t3y"
%v0 → RAX
```

---

# 19. CALL

LIR call:

```text id="3v5ih1"
CALL {
    callee
    args
    returns
    calling_convention
    attributes
}
```

Ví dụ:

```text id="x7ij3b"
%v2 = CALL add(%v0, %v1) cc=AXIOM
```

Không trực tiếp:

```text id="8xq5fq"
RDI = %v0
RSI = %v1
CALL add
```

Đó là ABI lowering.

---

# 20. Calling convention

LIR phải giữ:

```text id="m8o5zq"
CallingConvention {
    kind
    varargs
    return_style
}
```

Các loại:

```text id="1j8qtx"
Axiom
C
System
Fast
VectorCall
...
```

v0.1 chỉ cần:

```text id="q8l4f5"
Axiom
C
System
```

---

# 21. Aggregate return

Đây là một điểm rất quan trọng.

Ví dụ:

```axiom id="n0x3wp"
fn make_vec() -> Vec2
```

Có thể ABI trả:

```text id="s5a0w9"
XMM0/XMM1
```

hoặc hidden return pointer:

```text id="4v1bma"
RDI = destination
CALL make_vec
```

LIR không được hardcode.

Nó biểu diễn:

```text id="xq0n8h"
RETURN Aggregate(Vec2)
```

ABI lowering quyết định.

---

# 22. SRet

Nếu aggregate return cần caller allocation:

```text id="z9wy72"
CALL {
    return = indirect
    sret = %addr
}
```

Sau ABI lowering:

```text id="8m8r3f"
RDI = %addr
CALL
```

Điều này phù hợp với:

```text id="t8yq9f"
AMEM-29 Caller-Allocated Returns Are Permitted.
```

---

# 23. Tail call

Có thể hỗ trợ:

```text id="q4v9de"
TAILCALL
```

nhưng v0.1 không bắt buộc.

Nếu ABI/target cho phép:

```text id="3i0r8h"
foo() → tailcall bar()
```

sẽ tránh frame.

---

# 24. Stack objects

LIR có:

```text id="zv1y4k"
STACK_OBJECT {
    id
    size
    alignment
}
```

Sau frame lowering:

```text id="a9k8x3"
stack offset = -32(%rbp)
```

Nhưng LIR chưa biết `%rbp`.

---

# 25. `ALLOCA` không tồn tại trong LIR v0.1

Không tạo:

```text id="b7kh3j"
ALLOCA
```

như LLVM.

Thay vào đó:

```text id="vtxvuj"
STACK_OBJECT
```

và frame layout pass quyết định.

Lý do: Axiom không muốn semantic stack allocation bị trộn với target stack frame.

---

# 26. Global/static

LIR có:

```text id="7fjxjd"
GLOBAL_REF Symbol
```

và:

```text id="n0fj8x"
ADDRESS_OF_GLOBAL Symbol
```

Target backend sẽ tạo relocation.

---

# 27. Memory effects

Mỗi instruction/call có:

```text id="q84bq1"
MemoryEffect
```

```text id="z8c4a7"
None
Read
Write
ReadWrite
Unknown
```

Ví dụ:

```text id="7sgc7k"
ADD
→ None

LOAD
→ Read

STORE
→ Write

CALL unknown
→ Unknown
```

Optimizer sử dụng thông tin này.

---

# 28. Pure call

Nếu compiler chứng minh:

```text id="4mbyi7"
CALL foo
MemoryEffect=None
NoPanic
```

thì optimizer có thể DCE nếu result unused.

Nhưng:

```text id="y9r0n4"
CALL syscall
MemoryEffect=Unknown
```

không được loại.

---

# 29. Function attributes

LIR function:

```text id="v6jz2d"
FunctionAttrs {
    calling_convention
    memory_effect
    no_return
    no_unwind
    cold
    hot
    inline_hint
    no_inline
}
```

Không phải tất cả source-visible.

Compiler facts có thể được thêm.

---

# 30. Inline assembly

LIR phải có structured asm:

```text id="l6w4v5"
INLINE_ASM {
    template
    inputs
    outputs
    clobbers
    memory_effect
}
```

Không cho backend tự parse string semantics.

Ví dụ:

```text id="j2r5u1"
inputs:
    %v0 → register
outputs:
    %v1 ← register
clobbers:
    RAX
memory:
    ReadWrite
```

x86 backend mới hiểu instruction template.

---

# 31. Address spaces

LIR có:

```text id="u7v1x8"
AddressSpace {
    Generic
    Host
    Device
    Shared
    Local
    Private
    Constant
    External
}
```

CPU v0.1 chủ yếu:

```text id="5qj5fa"
Generic
```

GPU backend sau này dùng phần còn lại.

---

# 32. LIR instruction set v0.1

### Constants

```text id="jv6jkl"
CONST
SYMBOL_ADDR
```

### Data

```text id="u0q4l1"
COPY
LOAD
STORE
MEMCPY
MEMSET
```

### Arithmetic

```text id="1m6w7x"
ADD
SUB
MUL
DIV
REM

ADD_CHECKED
SUB_CHECKED
MUL_CHECKED

ADD_WRAP
SUB_WRAP
MUL_WRAP

ADD_SAT
SUB_SAT
MUL_SAT
```

### Bit

```text id="j5k4a0"
AND
OR
XOR
NOT
SHL
SHR
SAR
```

### Comparison

```text id="q44q34"
CMP
```

### Control

```text id="1r4xhv"
JMP
BRANCH
SWITCH
RETURN
TRAP
UNREACHABLE
```

### Calls

```text id="8e5jgl"
CALL
TAILCALL
```

### Atomics

```text id="h9j0kj"
ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS
FENCE
```

### Special

```text id="wq9z9k"
VOLATILE_LOAD
VOLATILE_STORE
INLINE_ASM
```

---

# 33. LIR không còn Drop

Ví dụ:

```axiom id="gj7qfy"
let x = resource()
```

MIR:

```text id="zqj4p7"
%x = CALL resource()
...
DROP %x
```

Sau lowering:

```text id="o5l0dc"
CALL resource_constructor
...
CALL resource_destructor
```

hoặc nếu Drop là intrinsic/library operation:

```text id="cr9e1g"
CALL drop_impl
```

Sau đó optimizer có thể inline.

LIR không biết đây là ownership Drop nữa.

---

# 34. LIR không còn view

MIR:

```text id="y5c7la"
%v = VIEW x
```

LIR:

```text id="u5e9ck"
%ptr = ADDRESS_OF x
%len = ...
```

hoặc nếu view đã chỉ được dùng để prove safety:

```text id="6z6c3m"
VIEW biến mất hoàn toàn.
```

Đây chính là **abstraction erasure**.

---

# 35. LIR không còn generic

```axiom id="x0gd6q"
fn max<T: Ord>(a: T, b: T) -> T
```

sau monomorphization:

```text id="yqcrkj"
max_i32
max_f64
...
```

LIR chỉ thấy concrete function.

Dynamic trait:

```axiom id="r0vv5e"
dyn Trait
```

sẽ thành:

```text id="9e5k5r"
data_ptr
dispatch_ptr
```

và indirect call.

---

# 36. LIR không còn `Option`

Ví dụ:

```text id="3fg9ev"
Option<i32>
```

representation có thể:

```text id="5z93kv"
tag + payload
```

hoặc niche:

```text id="a2h8p0"
single register
```

LIR nhận representation cuối cùng từ layout lowering.

---

# 37. LIR verifier

Trước Machine IR phải kiểm:

```text id="m9f7vx"
ALIRVerifier
```

### Register

```text
valid VReg
valid register class
type compatible
```

### Memory

```text
valid address
valid alignment
valid size
valid address space
```

### CFG

```text
valid block
valid terminator
reachable targets
```

### Calls

```text
valid calling convention
argument count/types
return types
```

### Atomics

```text
valid ordering
valid width
valid atomic capability
```

---

# 38. LIR invariants

Chốt:

```text id="5i0dkl"
ALIR-20
LIR is target-neutral.

ALIR-21
LIR contains no unresolved source-language semantics.

ALIR-22
Ownership semantics are resolved before LIR.

ALIR-23
Capability semantics are resolved before LIR.

ALIR-24
Drop semantics are resolved before LIR.

ALIR-25
Generic parameters are resolved before LIR unless represented by explicit runtime metadata.

ALIR-26
Virtual registers are target-independent.

ALIR-27
Physical registers do not appear in LIR.

ALIR-28
Memory operations carry explicit size and alignment.

ALIR-29
Volatile operations are semantically distinct from ordinary memory operations.

ALIR-30
Atomic ordering remains explicit until target lowering.

ALIR-31
Calling convention remains explicit until ABI lowering.

ALIR-32
Aggregate return representation may remain abstract until ABI lowering.

ALIR-33
Target legalization may expand one LIR instruction into multiple machine instructions.

ALIR-34
LIR optimization cannot change source-visible semantics.

ALIR-35
LIR has no mandatory runtime dependency.

ALIR-36
LIR is deterministic.

ALIR-37
LIR verification precedes target lowering.

ALIR-38
LIR does not depend on a third-party compiler IR.

ALIR-39
LIR does not require an assembler.

ALIR-40
LIR can represent runtime-free freestanding programs.
```

---

# 39. Repository

Thêm:

```text id="n5i5xz"
compiler/lir/
├── value.ax
├── types.ax
├── vreg.ax
├── memory.ax
├── instruction.ax
├── block.ax
├── function.ax
├── calling_convention.ax
├── effects.ax
├── atomic.ax
├── asm.ax
├── verifier.ax
├── lowering.ax
└── tests/
    ├── constants.ax
    ├── arithmetic.ax
    ├── branch.ax
    ├── call.ax
    ├── aggregate.ax
    ├── memory.ax
    └── atomic.ax
```

---

# XLVI — LIR-001 vertical slice

Bây giờ source:

```axiom id="d0uk4h"
fn main() -> i32 {
    42
}
```

Verified MIR:

```text
bb0:
    %0 = CONST i32 42
    RETURN %0
```

LIR:

```text
function main:
bb0:
    %v0:I32 = CONST 42
    RETURN %v0
```

Không runtime.

---

## Arithmetic

Source:

```axiom id="qkblz3"
fn main() -> i32 {
    20 + 22
}
```

LIR:

```text
bb0:
    %v0 = CONST I32 20
    %v1 = CONST I32 22
    %v2 = ADD_CHECKED %v0, %v1
    RETURN %v2
```

---

## Function call

```axiom id="r3gk5x"
fn add(a: i32, b: i32) -> i32 {
    a + b
}

fn main() -> i32 {
    add(20, 22)
}
```

LIR:

```text
add:
bb0:
    %r = ADD_CHECKED %a, %b
    RETURN %r

main:
bb0:
    %a = CONST I32 20
    %b = CONST I32 22
    %r = CALL add(%a, %b), cc=Axiom
    RETURN %r
```

Sau này x86 backend mới biến nó thành:

```text
mov edi, 20
mov esi, 22
call add
mov eax, ...
ret
```

---

# XLVII — Bước tiếp theo: Machine IR x86-64

Từ đây ta **không nên thiết kế thêm semantics ngôn ngữ**.

Phần còn lại là compiler backend thuần:

```text
LIR
 ↓
x86-64 Target Lowering
 ↓
Machine IR
 ↓
Register Allocation
 ↓
Frame Layout
 ↓
Instruction Selection
 ↓
Encoding
 ↓
ELF Object
 ↓
axiom-link
```

Bước kế tiếp sẽ là **X86-001: Target Description + Machine IR**, trong đó ta chốt chính xác:

- register file `RAX...R15`, `XMM0...`
- register aliases `RAX/EAX/AX/AH/AL`
- register classes
- System V AMD64 calling convention
- stack/frame model
- MachineInstr representation
- memory operands `[base + index*scale + displacement]`
- implicit register use/def
- flags
- instruction constraints
- ABI lowering
- và sau đó **Linear Scan Register Allocation**.

Đây là lúc Axiom bắt đầu tự xây một backend machine-code thực sự, **không LLVM, không GCC, không assembler**.