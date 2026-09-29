Tiếp tục với **MACHINE-IR-003 — Target Legalization & Instruction Selection**.

Đây là lớp quyết định Axiom có tận dụng được từng CPU hay không. Tôi đề xuất tách rõ **Legalization** và **Instruction Selection**, vì hai việc này khác nhau.

# MACHINE-IR-003

## 1. Pipeline chính

```text
LIR
 │
 ├── LIR Optimization
 │
 ▼
Target Legalization
 │
 ▼
Legal LIR / Selection IR
 │
 ▼
Instruction Selection
 │
 ▼
Target Machine IR
 │
 ▼
Machine Optimization
```

Hai câu hỏi khác nhau:

**Legalization:**

> Operation này có biểu diễn trực tiếp trên target không?

**Instruction Selection:**

> Nếu có nhiều cách biểu diễn, cách nào phù hợp nhất?

---

# 2. Ví dụ đơn giản

Axiom LIR:

```text
v3 = ADD i64 v1, v2
```

x86-64 có:

```text
ADD r64, r64
```

→ Legal.

AArch64 cũng có:

```text
ADD Xd, Xn, Xm
```

→ Legal.

Nhưng giả sử:

```text
v3 = SATURATING_ADD i64 v1, v2
```

CPU có thể không có instruction trực tiếp.

Legalization biến thành:

```text
ADD
CMP
SELECT
```

hoặc sequence target-specific.

---

# 3. Legalization categories

Giữ hệ thống đã đề xuất:

```text
Legal
Expand
Promote
Split
Lower
Custom
Reject
```

### Legal

Target hỗ trợ trực tiếp.

```text
ADD i64
→ ADD
```

### Promote

Đổi sang type lớn hơn.

```text
ADD i8
→ ADD i32
→ truncate i8
```

### Expand

Một operation thành nhiều operation.

```text
ABS
→ CMP + NEG + SELECT
```

### Split

Một giá trị lớn thành nhiều phần.

```text
i128
→ lo64 + hi64
```

### Lower

Đổi sang primitive khác.

```text
MEMCPY
→ LOAD/STORE loop
```

### Custom

Backend tự xử lý.

```text
ATOMIC_CAS
```

### Reject

Không thể biểu diễn target.

---

# 4. Legalization không được làm mất semantics

Ví dụ:

```text
checked_add
```

không thể đơn giản thành:

```text
ADD
```

nếu overflow behavior bị thay đổi.

Legalizer phải giữ:

```text
result
overflow condition
trap/error behavior
```

---

# 5. Target description

Mỗi target cần một database:

```text
TargetDescription {
    architecture
    pointer_width
    endian
    registers
    register_classes
    instructions
    legal_types
    legal_operations
    calling_conventions
    address_spaces
    atomic_capabilities
    features
}
```

Ví dụ:

```text
x86_64
aarch64
riscv64
wasm32
```

---

# 6. CPU target khác architecture target

Đừng gộp:

```text
x86-64
```

với:

```text
Zen 4
Skylake
Haswell
```

Nên:

```text
Target
    Architecture = x86_64
    ABI = SysV
    CPU = generic-x86-64
    Features = SSE2
```

hoặc:

```text
CPU = znver4
Features = AVX2,...
```

---

# 7. Instruction Selection

Sau legalization:

```text
v3 = ADD v1, v2
```

selector có thể chọn:

```text
ADD_REG_REG
```

nhưng với:

```text
v3 = ADD v1, constant
```

có thể chọn:

```text
ADD_REG_IMM
```

Đây là selection, không phải legalization.

---

# 8. Selection phải nhìn cả context

Ví dụ:

```text
v3 = MUL v1, 8
```

Không nhất thiết chọn:

```text
MUL
```

x86 có thể dùng:

```text
LEA
```

nếu context phù hợp.

```text
v3 = v1 * 8
```

→

```text
LEA v3, [v1 + v1*8?]
```

Thực tế scale 8 chỉ có thể biểu diễn phù hợp với một address expression; selector phải kiểm tra target addressing constraints.

---

# 9. DAG-based selection

MVP có thể dùng Selection DAG:

```text
ADD
├── MUL
│   ├── x
│   └── 8
└── y
```

Target pattern:

```text
ADD
  (MUL x, const)
```

có thể match instruction pattern đặc biệt.

---

# 10. Nhưng không nên phụ thuộc DAG mãi mãi

Đề xuất:

### MVP

```text
DAG / pattern matching
```

### Sau này

```text
Global instruction selection
+ machine-aware cost model
```

Vì một instruction sequence tối ưu đôi khi cần nhìn xuyên basic block.

---

# 11. Pattern definition

Không hard-code:

```text
if opcode == ADD && operand == ...
```

quá nhiều trong C/Axiom source.

Backend nên có declarative pattern:

```text
Pattern {
    match
    constraints
    replace
    cost
    features
}
```

Conceptual:

```text
ADD(x, CONST(c))
    where fits_add_imm(c)
→ ADDri(x, c)
```

---

# 12. Pattern priority

Có thể có nhiều pattern:

```text
ADD reg, reg
ADD reg, imm
LEA
INC
SUB -imm
```

Selector cần:

```text
Cost
Legality
Register pressure
Code size
CPU model
```

Không đơn giản chọn pattern đầu tiên.

---

# 13. Cost model

Ví dụ:

```text
Candidate A:
    1 instruction
    latency 1
    size 4

Candidate B:
    2 instructions
    latency 2
    size 6
```

→ A thường tốt hơn.

Nhưng nếu:

```text
A:
    requires special register

B:
    uses any GPR
```

B có thể tốt hơn khi register pressure cao.

Do đó cost phải có:

```text
static cost
latency
throughput
code size
register pressure
```

---

# 14. Code-size optimization

Axiom nên hỗ trợ:

```text
-Osize
```

hoặc tương đương.

Selector có thể ưu tiên:

```text
smaller encoding
```

thay vì:

```text
faster sequence
```

Ví dụ x86 có nhiều encoding cho cùng semantics.

---

# 15. Fast vs size profiles

Không nên hard-code một optimizer duy nhất.

Target options:

```text
OptimizationMode:
    Debug
    O0
    O1
    O2
    O3
    Os
    Oz
```

Không nhất thiết phải giống LLVM/GCC về semantics.

Chỉ cần semantics ổn định.

---

# 16. Integer operations

### ADD

```text
ADD
```

### SUB

```text
SUB
```

### MUL

```text
MUL
```

Nhưng:

```text
DIV
REM
```

khó hơn.

---

# 17. Division

Axiom:

```text
v3 = SDIV v1, v2
```

x86 có fixed-register constraints.

Ví dụ conceptual:

```text
RAX = dividend
RDX = sign_extend(RAX)
IDIV divisor
RAX = quotient
RDX = remainder
```

Instruction selector cần tạo:

```text
COPY RAX <- v1
SIGN_EXTEND_DIVIDEND
IDIV divisor
v3 <- RAX
```

và nếu `%`:

```text
v3 <- RDX
```

Register allocator phải hiểu fixed registers.

---

# 18. Division by constant

Đây là optimization quan trọng.

```text
x / 10
```

không nhất thiết phải dùng hardware DIV.

Optimizer có thể biến thành:

```text
multiply by magic constant
shift
adjust
```

Nhưng đây là **semantic optimization**, không chỉ instruction selection.

Do đó:

```text
MIR/LIR optimization
```

có thể thực hiện trước selection.

---

# 19. Overflow semantics

Axiom không cho phép C-style signed-overflow UB.

Điều này ảnh hưởng optimizer rất lớn.

Nếu:

```text
a + b
```

là checked semantics, optimizer **không được** giả định:

```text
a+b cannot overflow
```

trừ khi chứng minh.

Đây là điểm quan trọng để tránh optimizer sai.

---

# 20. Checked add

Có thể hạ:

```text
checked_add(a,b)
```

thành:

```text
ADD
SET_OVERFLOW
```

Ví dụ x86:

```text
ADD
JO overflow
```

hoặc:

```text
ADD
SETO
```

tùy context.

---

# 21. Wrapping add

```text
wrapping_add
```

chỉ cần:

```text
ADD
```

Không cần overflow handling.

---

# 22. Saturating add

Nếu CPU hỗ trợ:

```text
SAT_ADD
```

→ direct.

Nếu không:

```text
ADD
detect overflow
clamp
```

Selection pattern có thể phụ thuộc type.

---

# 23. Boolean representation

Axiom:

```text
bool
```

không nhất thiết luôn là 1 byte ở Machine IR.

Register representation có thể:

```text
GPR
flags
predicate register
```

Ví dụ:

```text
if a < b
```

có thể không materialize bool.

Đây là một optimization rất quan trọng.

---

# 24. Compare + branch fusion

LIR:

```text
v = CMP_LT a,b
BR v
```

selector nên nhận diện:

```text
CMP
+
BR
```

và chọn:

```text
CMP
JLT
```

thay vì:

```text
CMP
SETLT
TEST
JNZ
```

---

# 25. Compare + select

```text
x = select(a < b, x, y)
```

x86:

```text
CMP
CMOV
```

AArch64:

```text
CMP
CSEL
```

Nếu branch rẻ hơn hoặc condition unlikely:

```text
branch
```

có thể được chọn tùy cost model.

---

# 26. Memory folding

LIR:

```text
v1 = ADD base, offset
v2 = LOAD v1
```

x86 selector:

```text
MOV v2, [base + offset]
```

Không cần tạo ADD.

Đây là lý do selector nên match cả expression tree.

---

# 27. Address computation

Một abstraction quan trọng:

```text
AddressExpr
```

có thể:

```text
base
+
index * scale
+
offset
```

Selector kiểm tra:

```text
target supports addressing?
```

x86:

```text
yes
```

RISC-V:

```text
no
```

→ materialize address bằng ADD/MUL.

---

# 28. Load/store selection

LIR:

```text
LOAD i32
```

x86:

```text
MOV r32, [mem]
```

AArch64:

```text
LDR Wd, [Xn]
```

RISC-V:

```text
LW rd, offset(rs1)
```

Ba instruction semantics khác encoding nhưng cùng LIR semantic.

---

# 29. Alignment

Nếu LIR nói:

```text
alignment = 16
```

selector có thể dùng instruction yêu cầu alignment.

Nếu:

```text
alignment = 1
```

không được giả định aligned.

Compiler chỉ được tăng alignment khi proven.

---

# 30. Vectorization boundary

SIMD nên được biểu diễn ở LIR:

```text
Vector<f32, 4>
```

hoặc target-independent vector type.

Ví dụ:

```text
ADD <4 x f32>
```

Target:

```text
SSE
AVX
NEON
SVE
RVV
```

selector chọn instruction.

---

# 31. Fixed-width vector vs scalable vector

Không nên bắt Axiom v1 phải mô hình hóa mọi SIMD capability.

MVP:

```text
Vector<T, N>
```

với:

```text
N
```

compile-time constant.

Scalable vector:

```text
SVE
RVV
```

có thể thêm abstraction sau.

Nhưng LIR nên để:

```text
VectorLengthKind =
    Fixed
    Scalable
```

để không đóng cửa kiến trúc.

---

# 32. Atomic selection

Axiom:

```text
atomic_cas(ptr, expected, desired, AcqRel, Acquire)
```

x86:

```text
LOCK CMPXCHG
```

AArch64 có thể:

```text
CAS
```

hoặc:

```text
LDXR
STXR
```

RISC-V:

```text
LR/SC
```

hoặc extension tương ứng.

Semantics giữ ở LIR:

```text
ATOMIC_CAS
```

target selector quyết định implementation.

---

# 33. Atomic ordering không được mất

Không được biến:

```text
AcqRel
```

thành:

```text
Relaxed
```

chỉ vì target có instruction thuận tiện.

Target mapping phải bảo toàn hoặc mạnh hơn semantics theo quy tắc hợp lệ.

---

# 34. Atomic fallback

Nếu target không có native atomic width:

```text
Atomic<u128>
```

có thể:

```text
runtime helper
```

hoặc:

```text
Reject
```

tùy target/profile.

Quan trọng:

> Đây là capability của target, không phải compiler tự giả định.

---

# 35. Runtime helper

Một operation có thể lower thành:

```text
CALL __axiom_atomic_u128_cas
```

Nhưng runtime helper phải là **optional capability**.

Không được khiến mọi Axiom executable tự động link runtime.

---

# 36. `memcpy`

LIR:

```text
MEMCPY dst, src, size, alignment
```

Target có thể:

```text
inline small copy
REP MOVSB
vector sequence
CALL runtime helper
```

Selection + optimization quyết định.

`memcpy` không nhất thiết phải là external libc call.

---

# 37. `memset`

Tương tự:

```text
MEMSET dst, value, size
```

Có thể inline hoặc gọi helper.

Điều này rất quan trọng cho mục tiêu:

> Axiom không phụ thuộc libc.

---

# 38. Large aggregate copy

Compiler có thể nhận:

```text
struct Big { ... }
```

và thay:

```text
COPY Big
```

bằng:

```text
MEMCPY
```

hoặc scalarized fields.

Đây là nơi value semantics của Axiom vẫn có thể đạt hiệu năng C/C++.

---

# 39. `Option<T>` niche

Đây là trường hợp cần ABI + optimizer phối hợp.

Ví dụ:

```text
Option<NonNull<T>>
```

có thể biểu diễn:

```text
0 = None
nonzero = Some(ptr)
```

Machine IR không còn cần biết `Option`.

Sau layout/ABI lowering:

```text
Option<NonNull<T>>
```

→ một pointer.

Đây chính là:

> semantic abstraction erased before Machine IR.

---

# 40. `Result<T,E>`

Nếu:

```text
Result<i32, bool>
```

ABI lowering có thể chọn:

```text
register value
+
tag
```

Nếu:

```text
Result<Pointer, ErrorCode>
```

có thể có niche optimization.

Không hard-code representation trong Machine IR.

---

# 41. `view<T>`

Một `view<T>` thường trở thành:

```text
pointer + length
```

nhưng compiler có thể truyền:

```text
pointer
length
```

qua registers.

Ví dụ:

```text
fn sum(v: view<i32>)
```

SysV có thể:

```text
RDI = ptr
RSI = len
```

AArch64:

```text
X0 = ptr
X1 = len
```

Không có object/header runtime.

---

# 42. `mut_view<T>`

ABI giống `view<T>` về representation, nhưng semantic verification đã đảm bảo:

```text
exclusive write capability
```

Machine IR không cần carry "mutable" metadata.

---

# 43. Dynamic Trait object

Conceptual representation:

```text
dyn Trait
{
    data
    vtable
}
```

ABI lowering:

```text
data pointer
vtable pointer
```

Call:

```text
load method address
indirect call
```

Không có hidden object header trong concrete struct.

---

# 44. Closure

Capturing closure:

```text
closure {
    code_ptr
    environment
}
```

có thể ABI-lower thành:

```text
fn_ptr
env_ptr
```

Hoặc nếu statically known:

```text
inline environment
```

và sau inlining có thể biến mất hoàn toàn.

---

# 45. Async Future

Đây là một abstraction rất quan trọng.

```text
async fn foo()
```

đã được lower trước LIR thành state machine.

Future state:

```text
struct FooFuture {
    state
    captured values
}
```

Sau optimization:

- state có thể nằm trên stack
- future có thể được inline
- allocation có thể bị loại bỏ
- poll có thể được inline

Không có:

```text
async runtime object
```

bắt buộc.

---

# 46. Async state machine và Machine IR

Machine IR chỉ thấy:

```text
switch state
load captured values
call poll
return Pending/Ready
```

Nếu compiler tối ưu tốt, một async chain nhỏ có thể trở thành machine code gần như state machine viết tay.

---

# 47. Instruction selection không được biết async

Đây là nguyên tắc quan trọng:

```text
async
Future
await
```

phải biến mất trước Machine IR.

Machine backend chỉ xử lý control flow và data flow thông thường.

---

# 48. Target-independent intrinsic

Axiom cần một tập intrinsic nhỏ:

```text
ctlz
cttz
popcount
bswap
rotate
fma
sqrt
min
max
prefetch
```

Những intrinsic này có semantics target-independent.

Target selector:

```text
POPCOUNT
→ POPCNT
```

hoặc fallback sequence.

---

# 49. CPU intrinsic fallback

Ví dụ:

```text
ctz(x)
```

Nếu CPU có:

```text
TZCNT
```

dùng nó.

Nếu không:

```text
BSF
```

nhưng semantics với zero khác nhau.

Do đó fallback phải preserve Axiom semantics.

---

# 50. `sqrt`

```text
sqrt(f64)
```

có thể:

```text
hardware sqrt
```

hoặc:

```text
runtime/libm
```

tùy target/profile/fast-math policy.

Không được tự ý thay đổi IEEE semantics nếu program đang ở strict floating-point mode.

---

# 51. Floating point policy

Nên đóng băng từ bây giờ:

```text
FPMode {
    Strict
    Fast
}
```

### Strict

Giữ:

- NaN semantics
- signed zero
- rounding
- exceptions theo target model
- operation ordering cần thiết

### Fast

Compiler được phép:

- reassociation
- contraction
- approximate operations
- bỏ một số strict guarantees

Nhưng phải explicit.

Không nên để `-O3` tự biến strict FP thành fast math.

---

# 52. Instruction selector architecture

Tôi đề xuất:

```text
InstructionSelector {
    target
    patterns
    cost_model

    select(function)
}
```

Target backend:

```text
X86Selector
AArch64Selector
RISCVSelector
WasmSelector
```

Pattern database:

```text
X86Patterns
A64Patterns
RVPatterns
```

---

# 53. Không nên viết selector bằng hàng nghìn `if`

Sai hướng:

```text
if op == ADD:
    if type == ...
        ...
```

Đúng hơn:

```text
semantic opcode
      ↓
pattern matcher
      ↓
candidate instructions
      ↓
constraints
      ↓
cost
      ↓
best legal pattern
```

Backend dễ mở rộng hơn rất nhiều.

---

# 54. Nhưng pattern system cũng không được quá “magic”

Pattern matcher cần debug được.

Khi compiler chọn:

```text
LEA
```

phải có khả năng diagnostic/debug:

```text
Selected:
    X86_LEA_R64_MEM

Because:
    ADD(MUL(x,8),y)

Rejected:
    IMUL
    reason: higher cost
```

Không cần đưa cho người dùng bình thường, nhưng compiler developer cần.

---

# 55. Fallback hierarchy

Mỗi operation nên có:

```text
native instruction
      ↓
instruction sequence
      ↓
compiler-generated helper
      ↓
runtime helper
      ↓
compile error
```

Ví dụ:

```text
u128_div
```

target không hỗ trợ:

```text
native
↓
software sequence
↓
__axiom_u128_div
```

Không được âm thầm gọi libc.

---

# 56. Runtime helper ABI

Nếu cần helper:

```text
__axiom_memcpy
__axiom_i128_div
__axiom_atomic_u128_cas
```

phải dùng:

```text
Axiom Runtime ABI
```

hoặc target system ABI nếu explicit.

Runtime helper chỉ được link nếu thực sự được sử dụng.

---

# 57. Instruction selection + PGO

Sau này cost model có thể nhận profile:

```text
branch_probability
block_frequency
call_frequency
```

Ví dụ:

```text
if likely(condition)
```

có thể chọn layout tốt hơn.

Nhưng PGO chỉ tối ưu, không thay đổi semantics.

---

# 58. Branch layout

Machine optimizer sau selection:

```text
hot block
cold block
```

có thể reorder:

```text
fallthrough = hot
branch = cold
```

Giảm branch penalty.

---

# 59. Cold code

Panic/error paths:

```text
panic
Err
trap
```

thường có thể được đánh dấu cold bởi compiler facts.

Nhưng đây là optimization hint, không semantic guarantee.

---

# 60. Selection và code size

Axiom nên có hai cost model chính:

```text
SpeedCost
SizeCost
```

và combined:

```text
OptimizationGoal {
    Speed
    Size
    Balanced
}
```

---

# 61. Invariants

Đóng băng nhóm:

### ALEGAL-20
**Legalization Preserves Semantics**

### ALEGAL-21
**Legalization Is Target-Aware**

### ALEGAL-22
**Unsupported Operations Have Explicit Lowering**

### ALEGAL-23
**Illegal Operations Cannot Reach Machine Encoding**

### ALEGAL-24
**Promotion Preserves Value Semantics**

### ALEGAL-25
**Expansion Preserves Failure Semantics**

### ALEGAL-26
**Atomic Ordering Survives Legalization**

### ALEGAL-27
**Volatile Semantics Survive Legalization**

### ALEGAL-28
**Address-Space Semantics Survive Legalization**

### ALEGAL-29
**Target Feature Requirements Are Explicit**

### ALEGAL-30
**Runtime Helpers Are Capability-Linked**

### ASEL-20
**Instruction Selection Is Target-Specific**

### ASEL-21
**Selection Is Constraint-Aware**

### ASEL-22
**Selection Uses A Target Cost Model**

### ASEL-23
**Selection May Fold Address Computation**

### ASEL-24
**Selection May Fuse Compatible Operations**

### ASEL-25
**Selection Must Preserve Overflow Semantics**

### ASEL-26
**Selection Must Preserve Floating-Point Semantics**

### ASEL-27
**Selection Must Preserve Atomic Semantics**

### ASEL-28
**Selection Must Respect Register Constraints**

### ASEL-29
**Selection Must Respect Implicit Register Effects**

### ASEL-30
**Selection Must Not Depend On High-Level Runtime Objects**

### ASEL-31
**Selection May Eliminate Abstraction Artifacts**

### ASEL-32
**Selection Must Not Introduce Hidden Runtime Dependencies**

### ASEL-33
**Fallback Lowering Must Preserve Semantics**

### ASEL-34
**Selection Is Deterministic For A Fixed Target Configuration**

### ASEL-35
**Selection Diagnostics Must Be Inspectable By Compiler Developers**

---

# 62. Kiến trúc backend lúc này

Axiom backend đã có hình khá hoàn chỉnh:

```text
                    VERIFIED MIR
                         │
                         ▼
                   ABI LOWERING
                         │
                         ▼
                       LIR
                         │
                         ▼
                LIR OPTIMIZATION
                         │
                         ▼
                 LEGALIZATION
                         │
                         ▼
              INSTRUCTION SELECTION
                         │
                         ▼
                  MACHINE IR
                         │
              ┌──────────┴──────────┐
              │                     │
        PRE-RA OPTIMIZATION   MACHINE VERIFY
              │                     │
              └──────────┬──────────┘
                         ▼
                 REGISTER ALLOCATION
                         ▼
                    SPILL/RELOAD
                         ▼
                   FRAME LAYOUT
                         ▼
                 PROLOGUE/EPILOGUE
                         ▼
                 POST-RA OPTIMIZER
                         ▼
                  MACHINE VERIFY
                         ▼
                  MACHINE ENCODER
                         ▼
                     OBJECT
```

Và quan trọng nhất:

```text
MIR
= "chương trình có nghĩa gì?"

LIR
= "cần những low-level operations nào?"

Machine IR
= "CPU này thực hiện chúng bằng instruction nào?"

Encoder
= "instruction đó biến thành byte nào?"
```

Đây là ranh giới rất sạch.

---

## Bước tiếp theo: `MACHINE-IR-004 — Register Allocation`

Bây giờ mới tới phần **Register Allocation + Spill/Reload**, nơi ta giải quyết:

```text
v0 ────────┐
v1 ────────┼──→ RAX
v2 ────────┼──→ RBX
v3 ────────┼──→ RCX
v4 ────────┘
```

khi có 30.000 virtual registers nhưng CPU chỉ có vài chục register.

Ta sẽ thiết kế:

- live interval
- liveness analysis
- interference
- register pressure
- Linear Scan MVP
- fixed registers
- register aliases
- call-clobber
- spill cost
- spill/reload
- rematerialization
- register coalescing
- two-address instructions
- phi elimination
- parallel copy
- stack slot allocation
- split live range
- caller/callee saved
- register allocation cho SIMD
- allocation cho `RAX/RDX` kiểu division
- allocation cho flags
- cuối cùng chứng minh **post-RA Machine IR không còn virtual register**.