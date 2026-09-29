# XLVII — X86-001: Target Description + Machine IR

Ta chuyển hẳn sang backend x86-64. Mục tiêu của phase này là:

```text
Axiom LIR
    ↓
x86-64 Target Lowering
    ↓
Machine IR
```

Sau phase này, compiler đã có representation đủ chính xác để bắt đầu **register allocation và encoding machine code**.

---

# 1. Target Description

Không hard-code x86 rải rác trong compiler.

Thiết kế:

```text
Target
├── Architecture
├── ABI
├── RegisterFile
├── InstructionSet
├── CallingConvention
├── DataLayout
├── RelocationModel
├── ObjectFormat
└── Features
```

Interface:

```text
Target {
    architecture
    abi
    registers
    instructions
    calling_convention
    data_layout
    relocations
    object_format
    features
}
```

x86-64 Linux v0.1:

```text
architecture = x86_64
abi          = SystemV_AMD64
pointer      = 64
endianness   = little
object       = ELF64
```

---

# 2. Tại sao Target Description phải data-driven?

Không nên viết:

```text
if target == x86 {
   ...
}
```

ở hàng trăm nơi.

Thay vào đó:

```text
Target
  ↓
TargetLowering
  ↓
MachineIR
```

Sau này thêm:

```text
AArch64
RISC-V64
WASM
```

mà semantic compiler không thay đổi.

---

# 3. Register File

x86-64 GPR:

```text
RAX
RBX
RCX
RDX
RSI
RDI
RBP
RSP
R8
R9
R10
R11
R12
R13
R14
R15
```

Special:

```text
RIP
RFLAGS
```

SIMD:

```text
XMM0 ... XMM31
```

v0.1 Linux backend thực tế chủ yếu cần:

```text
XMM0 ... XMM15
```

vì baseline System V environment không yêu cầu AVX-512.

---

# 4. Register aliases

Đây là phần Machine IR phải làm đúng.

Ví dụ:

```text
RAX
├── EAX
├── AX
├── AH
└── AL
```

Không coi chúng là 5 register độc lập.

Phải có:

```text
Register {
    id
    class
    width
    parent
    subrange
}
```

Ví dụ:

```text
RAX
  └── EAX
       └── AX
          ├── AH
          └── AL
```

---

# 5. Register classes

v0.1:

```text
GPR64
GPR32
GPR16
GPR8

XMM

FLAGS
```

Có thể thêm:

```text
MMX
YMM
ZMM
```

sau.

---

# 6. Virtual register

LIR:

```text
%v0 : I32
```

Machine IR:

```text
$v0 : GPR32
```

Register allocator cuối cùng:

```text
$v0 → EAX
```

---

# 7. Machine Operand

```text
MachineOperand =
    Register
    Immediate
    Memory
    Symbol
    Block
    ConstantPool
```

Ví dụ:

```text
MOV EAX, 42
```

representation:

```text
MOV
  Register(EAX)
  Immediate(42)
```

---

# 8. Memory Operand

x86 memory operand:

```text
[base + index * scale + displacement]
```

Representation:

```text
MemoryOperand {
    base: Register?
    index: Register?
    scale: 1 | 2 | 4 | 8
    displacement: i32
    segment: Segment?
}
```

Ví dụ:

```text
[RBX + RCX*8 + 16]
```

→

```text
base = RBX
index = RCX
scale = 8
disp = 16
```

---

# 9. Symbol memory operand

Global:

```text
foo
```

có thể:

```text
MemoryOperand {
    symbol = foo
    displacement = 0
}
```

Relocation chưa resolve tại Machine IR.

---

# 10. Machine instruction

```text
MachineInstr {
    opcode
    operands[]
    implicit_uses[]
    implicit_defs[]
    flags
}
```

Ví dụ:

```text
ADD EAX, EBX
```

Machine IR:

```text
MachineInstr {
    opcode = ADD32rr
    operands = [
        Reg(EAX),
        Reg(EBX)
    ]
}
```

---

# 11. Vì sao opcode phải phân biệt operand form?

Không nên chỉ có:

```text
ADD
```

vì x86 có:

```text
ADD r,r
ADD r,imm
ADD r,m
ADD m,r
```

và các width:

```text
8
16
32
64
```

Do đó target instruction description có:

```text
Opcode
Operand constraints
Encoding form
```

Ví dụ:

```text
ADD32rr
ADD32ri
ADD32rm
ADD32mr
```

Có thể internal opcode naming khác, nhưng semantic distinction phải tồn tại.

---

# 12. Instruction Definition

Mỗi opcode:

```text
InstructionDef {
    opcode
    operands
    implicit_uses
    implicit_defs
    constraints
    encoding
    latency
    throughput
    flags
}
```

Ví dụ `ADD r32,r32`:

```text
defs:
    destination
    FLAGS

uses:
    destination
    source
```

---

# 13. RFLAGS

Không coi flags như integer register bình thường.

Machine IR có:

```text
FLAGS
```

Ví dụ:

```text
CMP EAX, EBX
JG block1
```

`CMP`:

```text
implicit_defs = FLAGS
```

`JG`:

```text
implicit_uses = FLAGS
```

---

# 14. Condition code

Machine IR:

```text
COND_EQ
COND_NE
COND_LT
COND_LE
COND_GT
COND_GE
COND_ULT
COND_ULE
COND_UGT
COND_UGE
```

Lowering:

```text
EQ  → JE
NE  → JNE
LT  → JL
LE  → JLE
GT  → JG
GE  → JGE
ULT → JB
ULE → JBE
UGT → JA
UGE → JAE
```

---

# 15. Basic x86 instruction set v0.1

Cần trước tiên:

```text
MOV
LEA

ADD
SUB
IMUL
IDIV

AND
OR
XOR
SHL
SHR
SAR

CMP
TEST

JMP
JE
JNE
JL
JLE
JG
JGE
JB
JBE
JA
JAE

CALL
RET

PUSH
POP

SYSCALL
```

Sau đó:

```text
NEG
NOT
SETcc
CMOVcc
```

---

# 16. `MOV`

Các dạng:

```text
reg ← reg
reg ← imm
reg ← mem
mem ← reg
```

Machine selector chọn encoding.

Ví dụ:

```text
MOV EAX, 42
```

có thể encode:

```text
B8 + rd
imm32
```

Không cần assembler.

---

# 17. `LEA`

`LEA` không chỉ dùng load address.

Compiler có thể dùng:

```text
LEA RAX, [RDI + RSI*4]
```

để thực hiện:

```text
a + b*4
```

không cần memory access.

Đây là một trong những optimization backend quan trọng.

---

# 18. CALL

Machine IR:

```text
CALL Symbol(add)
```

hoặc:

```text
CALL Register(RAX)
```

Direct call:

```text
E8 rel32
```

Indirect:

```text
FF /2
```

---

# 19. RET

v0.1:

```text
RET
```

encoding:

```text
C3
```

---

# 20. Stack Frame

Không mặc định dùng:

```text
PUSH RBP
MOV RBP,RSP
```

Axiom backend phải cho phép frame-pointer omission.

Frame:

```text
FrameLayout {
    local_size
    spill_size
    saved_register_size
    outgoing_arg_size
    alignment
    has_fp
}
```

---

# 21. Leaf function

Ví dụ:

```axiom id="3n7z6c"
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

không cần stack:

```text
ADD EDI, ESI
MOV EAX, EDI
RET
```

hoặc trực tiếp:

```text
LEA EAX, [RDI + RSI]
RET
```

nếu legal và đúng semantics.

---

# 22. System V AMD64 ABI

Integer/pointer arguments:

```text
RDI
RSI
RDX
RCX
R8
R9
```

Return:

```text
RAX
```

Floating-point:

```text
XMM0
XMM1
XMM2
...
```

FP return:

```text
XMM0
```

---

# 23. Caller-saved

```text
RAX
RCX
RDX
RSI
RDI
R8
R9
R10
R11
```

Caller phải giữ nếu cần sau CALL.

---

# 24. Callee-saved

```text
RBX
RBP
R12
R13
R14
R15
```

Nếu function sử dụng chúng:

```text
save
...
restore
```

Machine frame pass chịu trách nhiệm.

---

# 25. RSP

`RSP` là special.

Không đưa `RSP` vào register allocator như GPR bình thường.

Compiler phải đảm bảo:

```text
stack alignment
valid call frame
balanced stack
```

---

# 26. Stack alignment

System V AMD64 yêu cầu stack alignment thích hợp tại call boundary.

Frame lowering phải tính:

```text
local
+ spill
+ saved regs
+ outgoing args
+ alignment padding
```

Không hardcode một con số ở từng call.

---

# 27. ABI lowering

LIR:

```text
CALL add(%v0, %v1)
```

ABI lowering:

```text
$v0 → RDI
$v1 → RSI
CALL add
result → RAX
```

Machine IR:

```text
MOV RDI, %v0
MOV RSI, %v1
CALL add
```

Register allocator có thể làm cho một số move biến mất.

---

# 28. Parallel move

Không nên lower argument moves tuần tự ngây thơ.

Ví dụ:

```text
v0 → RDI
v1 → RSI
```

đơn giản.

Nhưng:

```text
RDI → RSI
RSI → RDI
```

cần parallel-move resolution:

```text
temp = RDI
RDI = RSI
RSI = temp
```

Backend phải có:

```text
ParallelMoveResolver
```

---

# 29. Return ABI

LIR:

```text
RETURN %v0
```

ABI:

```text
%v0 → RAX
RET
```

FP:

```text
%v0 → XMM0
RET
```

Aggregate có thể:

```text
RAX/RDX
XMM0/XMM1
sret pointer
```

tùy ABI classification.

---

# 30. ABI classification

Không hardcode:

```text
if sizeof(T) <= 8
```

một cách đơn giản.

Phải có:

```text
ABIClassifier
```

input:

```text
TypeLayout
```

output:

```text
ABIValue {
    registers
    stack
    indirect
}
```

v0.1 có thể implement subset cho:

```text
integer
pointer
f32
f64
small aggregates
large aggregates
```

---

# 31. Small aggregate

Ví dụ:

```text
struct Pair {
    a: i64
    b: i64
}
```

System V có thể trả qua:

```text
RAX
RDX
```

Machine backend phải hỗ trợ nhiều return values.

---

# 32. Large aggregate

Có thể dùng:

```text
sret
```

Caller cấp storage:

```text
RDI = destination
```

callee ghi kết quả.

Điều này phù hợp với Axiom caller-allocated return semantics.

---

# 33. Machine block

```text
MachineBlock {
    id
    instructions[]
    successors[]
    predecessors[]
}
```

Không giữ AST/HIR information trong MachineBlock.

Debug mapping giữ riêng:

```text
DebugLocation
```

---

# 34. Machine function

```text
MachineFunction {
    function_id
    blocks[]
    virtual_registers
    frame_info
    calling_convention
    attributes
}
```

---

# 35. Machine verifier

Trước register allocation:

```text
MachineVerifier
```

kiểm:

```text
opcode hợp lệ
operand count
operand class
implicit use/def
branch target
memory operand
register alias
calling convention
```

Sau register allocation kiểm thêm:

```text
physical register
spill slots
frame references
```

Sau encoding còn một verifier cuối.

---

# 36. Three-stage verifier

Nên có:

```text
LIRVerifier
      ↓
MachineVerifier
      ↓
EncodedObjectVerifier
```

### LIRVerifier

semantic machine-neutral.

### MachineVerifier

x86 instruction correctness.

### ObjectVerifier

ELF/relocation correctness.

Điều này giúp lỗi backend định vị rất nhanh.

---

# 37. Target feature model

x86 feature:

```text
SSE2
SSE4.2
AVX
AVX2
AVX512F
BMI1
BMI2
FMA
...
```

v0.1 baseline:

```text
x86-64 + SSE2
```

Không tự dùng AVX2 nếu binary không yêu cầu.

---

# 38. CPU feature dispatch

Sau này:

```axiom id="v3g76q"
@target_feature("avx2")
fn fast(...)
```

Nhưng v0.1:

```text
TargetFeatures
```

chỉ là compiler configuration.

---

# 39. Machine IR example

Source:

```axiom id="i5f4yb"
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

LIR:

```text
%v0 = ADD_CHECKED %a, %b
RETURN %v0
```

Machine IR trước allocation:

```text
bb0:
    %r2:GPR32 = ADD_CHECKED %r0:GPR32, %r1:GPR32
    RETURN %r2
```

ABI-fixed:

```text
%r0 → EDI
%r1 → ESI
%r2 → EAX
```

Sau allocation:

```text
bb0:
    ADD EDI, ESI
    MOV EAX, EDI
    RET
```

Có thể optimizer/backend chọn:

```text
LEA EAX, [RDI + RSI]
RET
```

nhưng phải đảm bảo checked-add semantics. Vì signed overflow phải được phát hiện, `LEA` đơn thuần **không đủ** nếu overflow observable. Đây là ví dụ vì sao semantic lowering và machine optimization phải giữ distinction.

---

# 40. Checked arithmetic x86

Ví dụ:

```text
ADD_CHECKED
```

cần:

```text
ADD EAX, EDI
JO overflow
```

hoặc equivalent.

Overflow path:

```text
CALL panic_integer_overflow
```

hoặc profile-specific trap.

Optimizer chỉ được biến thành `LEA` nếu chứng minh overflow impossible.

---

# 41. Điều này bảo vệ mục tiêu performance

Axiom không nói:

> “mọi abstraction phải biến thành một instruction”.

Mà:

> **mọi abstraction không có observable runtime semantics phải được phép biến mất.**

Checked arithmetic có observable panic:

```text
20 + 22
```

có thể tối ưu mạnh.

```text
MAX_INT + 1
```

không thể biến thành wrapping ADD.

---

# 42. X86 repository

```text id="l7td4f"
compiler/backend/x86_64/
├── target.ax
├── registers.ax
├── register_classes.ax
├── aliases.ax
├── instructions.ax
├── encoding.ax
├── operands.ax
├── memory.ax
├── flags.ax
├── abi/
│   ├── sysv64.ax
│   ├── classify.ax
│   ├── args.ax
│   └── returns.ax
├── lowering.ax
├── machine_ir.ax
├── frame.ax
├── verifier.ax
└── tests/
```

---

# 43. X86 invariants

```text id="8f0l3c"
AX86-20
Physical registers are target-specific.

AX86-21
Virtual registers are allocated only after target lowering.

AX86-22
Register aliases share physical storage identity.

AX86-23
RSP is not a general allocatable register.

AX86-24
RFLAGS is modeled through implicit use/def.

AX86-25
Instruction operand constraints are explicit.

AX86-26
Memory operands explicitly represent base/index/scale/displacement.

AX86-27
Calling convention lowering is separate from semantic type checking.

AX86-28
Callee-saved registers are preserved when used.

AX86-29
Caller-saved registers may be clobbered by calls.

AX86-30
Stack alignment is verified at call boundaries.

AX86-31
ABI return classification is explicit.

AX86-32
Aggregate returns may use indirect sret.

AX86-33
Target features control instruction availability.

AX86-34
Machine IR contains no unresolved high-level ownership semantics.

AX86-35
Machine verifier runs before encoding.

AX86-36
Encoding does not depend on an external assembler.

AX86-37
Instruction selection preserves LIR semantics.

AX86-38
Illegal target instructions are rejected before encoding.

AX86-39
Machine output is deterministic.

AX86-40
Backend does not depend on LLVM/GCC.
```

---

# XLVIII — REGALLOC-001: Linear Scan Register Allocation

Bước kế tiếp rất rõ: **register allocation**.

Ta có:

```text id="c6v0m4"
LIR virtual registers
       ↓
x86 Machine IR virtual registers
       ↓
Live Interval Analysis
       ↓
Linear Scan
       ↓
Physical Registers
       ↓
Spill/Reload
```

---

## 44. Vì sao chọn Linear Scan trước?

Không phải vì nó luôn tối ưu nhất.

Mà vì:

- triển khai nhanh;
- dễ debug;
- deterministic;
- phù hợp compiler v0.1;
- dễ tạo compiler tự host;
- đủ tốt cho `-O0/-O1`;
- sau này thay bằng graph coloring mà không đổi semantic pipeline.

Do đó:

```text id="knx4q5"
v0.1 → Linear Scan
v0.2+ → Linear Scan + coalescing
v0.x → Graph Coloring / PBQP / target-specific allocator nếu cần
```

---

# 45. Live interval

Ví dụ:

```text id="zq0w4j"
%a = CONST 10      // 1
%b = CONST 20      // 2
%c = ADD %a,%b     // 3
RETURN %c          // 4
```

Intervals:

```text id="f1z3y6"
a: [1,3]
b: [2,3]
c: [3,4]
```

`a` và `b` overlap:

```text id="x1u8ad"
a ─────────
b   ────────
```

c có thể reuse register của a/b sau last use.

---

# 46. Register allocation algorithm

Basic:

```text id="x9n2j4"
sort intervals by start

active = []

for interval in intervals:
    expire old intervals

    if register available:
        assign register
    else:
        spill one interval
```

---

# 47. Register classes

Không được cho:

```text id="4b7qj6"
I64 → XMM
F64 → RAX
```

trừ khi explicit conversion.

Allocator nhận:

```text id="a8g5p2"
RegisterClass
```

Ví dụ:

```text
I32 → GPR32
I64 → GPR64
F32 → XMM
F64 → XMM
```

---

# 48. Register aliases trong allocator

Nếu:

```text id="c1r7by"
EAX
```

được dùng:

```text id="0p4x5s"
RAX
```

cũng bị xem là occupied.

Allocator phải hiểu alias hierarchy.

Không thể:

```text id="t7q8em"
EAX = v1
RAX = v2
```

cùng thời điểm nếu live overlap.

---

# 49. Fixed registers

Một số instructions có register constraint.

Ví dụ `IDIV` x86:

```text id="q8j6u4"
RAX/RDX
```

input/output cố định.

Machine IR phải biểu diễn:

```text id="9rj1zw"
implicit_uses = RAX,RDX
implicit_defs = RAX,RDX
```

Allocator sẽ tránh conflict hoặc insert moves.

---

# 50. CALL clobbers

CALL có:

```text id="5h1w2k"
implicit_defs =
RAX RCX RDX RSI RDI R8 R9 R10 R11
XMM...
```

theo ABI.

Nếu value còn live qua CALL:

```text id="z8e5al"
v0 live
CALL
use(v0)
```

allocator không thể đặt `v0` vào caller-saved register nếu không spill/save.

Có thể:

```text id="l2s3z9"
v0 → RBX
```

hoặc spill.

---

# 51. Spill

Nếu hết register:

```text id="t1x7pn"
SPILL v0 → stack_slot_3
```

Before use:

```text id="5jv0q8"
RELOAD stack_slot_3 → register
```

Spill slot:

```text id="k4s8cx"
StackSlot {
    id
    size
    alignment
    offset
}
```

Offset chưa cần biết ngay.

---

# 52. Spill không phải source allocation

Điều này rất quan trọng.

```text id="2i0x7a"
source variable
```

không đồng nghĩa:

```text id="qj4l9p"
stack slot
```

Spill chỉ là compiler implementation detail.

---

# 53. Register allocation invariant

```text id="e0c1j8"
AREG-20
Every virtual register has a valid register class.

AREG-21
Overlapping live intervals cannot share incompatible physical storage.

AREG-22
Register aliases are treated as overlapping storage.

AREG-23
Fixed-register instructions impose explicit constraints.

AREG-24
Call clobbers are modeled as register definitions.

AREG-25
Values live across calls cannot rely on clobbered registers without preservation.

AREG-26
Spill slots have valid size and alignment.

AREG-27
Reloads restore the correct value.

AREG-28
Allocation is deterministic.

AREG-29
Allocation preserves Machine IR semantics.

AREG-30
Register allocation does not modify source ownership semantics.

AREG-31
Spilling does not imply source-visible memory allocation.

AREG-32
Physical register assignment occurs only after target lowering.
```

---

# 54. Vertical slice tiếp theo

Với:

```axiom id="8h4x5x"
fn main() -> i32 {
    42
}
```

Machine IR:

```text
bb0:
    %v0:GPR32 = MOVri32 42
    RETURN %v0
```

Allocation:

```text
%v0 → EAX
```

Machine IR:

```text
bb0:
    MOV EAX, 42
    RET
```

Encoder sẽ tạo:

```text
B8 2A 00 00 00
C3
```

Đây là **machine code thực sự**.

Bước sau đó là **ENC-001: x86 instruction encoder**, rồi **OBJ-001: ELF64 object writer**. Khi hai phần này hoàn thành, Axiom có thể tạo `.o` mà không cần assembler; tiếp theo `axiom-link` sẽ tạo ELF executable hoàn chỉnh.