Tiếp tục với **MACHINE-IR-002 — Register / Memory / Instruction Model**. Đây là lớp đầu tiên thực sự mô hình hóa CPU, nhưng vẫn phải giữ backend đủ tổng quát để Axiom không bị khóa vào x86-64.

# MACHINE-IR-002 — REGISTER / MEMORY / INSTRUCTION MODEL

## 1. Nguyên tắc

Machine IR phải biểu diễn **những gì CPU thực sự có**, nhưng không được chứa logic của một target khác.

```text
LIR
 ↓
Target Legalization
 ↓
Machine IR
 ↓
Register Allocation
 ↓
Machine Scheduling
 ↓
Machine Encoder
```

Machine IR biết:

- physical register
- register class
- instruction
- memory operand
- addressing mode
- flags
- condition code
- implicit register use/def
- instruction constraints
- target feature

Nhưng:

> Machine IR không biết ownership, borrow, trait, generic, `Result`, `Option` hay `view`.

Những thứ đó đã biến mất hoặc đã được chứng minh từ MIR.

---

# 2. Register model

Ta cần 3 tầng.

```text
Virtual Register
        ↓
Register Class
        ↓
Physical Register
```

Ví dụ:

```text
v17 : GPR64
        ↓
        RAX
```

hoặc:

```text
v21 : FPR128
        ↓
        XMM3
```

---

# 3. PhysicalRegister

Không nên dùng string:

```text
"rax"
```

mà dùng ID:

```text
PhysicalRegisterId
```

Ví dụ:

```text
RAX = 0
RBX = 1
...
```

Tên chỉ phục vụ:

- debug
- diagnostics
- assembly output

Compiler nội bộ dùng ID.

---

# 4. Register descriptor

Mỗi register có:

```text
RegisterDesc {
    id
    name
    class
    width
    aliases
    super_register
    sub_registers
    encoding
    flags
}
```

Ví dụ conceptual:

```text
RAX
 ├── EAX
 ├── AX
 ├── AH
 └── AL
```

Compiler phải biết chúng overlap.

---

# 5. Register alias

Đây là vấn đề cực kỳ quan trọng trên x86.

```text
AL
```

ghi một phần:

```text
RAX
```

nhưng không giống:

```text
EAX
```

vì ghi EAX có zero-extension lên RAX.

Do đó register descriptor phải hỗ trợ:

```text
Overlap
PartialWrite
ZeroExtendWrite
PreserveUpper
```

Đây là thông tin machine semantics, không phải register allocator tự suy đoán.

---

# 6. Register unit

Một abstraction tốt hơn alias đơn giản là:

```text
RegisterUnit
```

Ví dụ:

```text
RAX
```

có các units:

```text
bits 0..7
bits 8..15
bits 16..31
bits 32..63
```

Register allocation có thể dùng register units để phát hiện conflict.

Ví dụ:

```text
AL
```

và:

```text
RAX
```

conflict.

---

# 7. RegisterClass

```text
RegisterClass {
    id
    registers[]
    allocation_order[]
    spill_size
    spill_alignment
}
```

Ví dụ:

```text
GPR64
FPR32
FPR64
Vector128
Vector256
Vector512
```

Nhưng không phải target nào cũng cần tất cả.

---

# 8. Register class hierarchy

Không nên tạo inheritance phức tạp.

Thay vào đó:

```text
GPR8
GPR16
GPR32
GPR64
```

có thể liên hệ bằng:

```text
CompatibleRegisterClass
```

Ví dụ:

```text
GPR32 → GPR64
```

nếu instruction cho phép.

Target legalization quyết định.

---

# 9. Virtual registers

Machine IR vẫn có virtual register:

```text
%v0
%v1
%v2
```

nhưng khác LIR:

### LIR

```text
v0 : GPR
```

### Machine IR

```text
v0 : X86_GPR64
```

hoặc:

```text
v0 : A64_GPR64
```

Machine IR đã target-specific.

---

# 10. Physical vs virtual

Machine IR instruction có thể:

```text
ADD v1, v2, v3
```

trước RA.

Sau RA:

```text
ADD RAX, RBX, RCX
```

Nhưng không nhất thiết phải tạo một IR hoàn toàn khác.

Một instruction operand có:

```text
RegisterOperand {
    virtual | physical
}
```

Register allocation thay thế virtual bằng physical.

---

# 11. Register masks

CALL cần biết register nào bị clobber.

Không nên lưu:

```text
[RAX, RCX, RDX, ...]
```

ở mỗi CALL.

Dùng:

```text
RegisterMask
```

bitset.

Ví dụ:

```text
CALL foo
clobber = 0b001101...
```

Lợi ích:

- nhanh
- compact
- dễ so sánh
- register allocator sử dụng trực tiếp

---

# 12. Reserved registers

Một số register không được allocator sử dụng:

```text
SP
FP
thread pointer
platform register
stack probe register
```

TargetDescription:

```text
reserved_registers
```

Allocator không bao giờ cấp chúng.

---

# 13. Special registers

Có các register không thuộc normal GPR/FPR:

```text
SP
FP
FLAGS
PC
TLS
VECTOR_STATE
```

Không nên coi chúng đều là general register.

Ví dụ:

```text
SP
```

chỉ được dùng trong các operation hợp lệ.

---

# 14. Condition Codes

x86:

```text
ZF
CF
SF
OF
```

AArch64:

```text
N
Z
C
V
```

Không nên hard-code tên flags trong generic optimizer.

Machine IR nên có:

```text
ConditionCode
```

Ví dụ:

```text
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

Target maps chúng thành physical flags conditions.

---

# 15. Flags là machine resource

Ví dụ:

```text
CMP RAX, RBX
JE label
```

`CMP` tạo flags.

`JE` đọc flags.

Machine scheduler phải biết:

```text
CMP
    DEF Flags

JE
    USE Flags
```

Nếu không, scheduler có thể di chuyển instruction sai.

---

# 16. Flags không nhất thiết là register

Đây là điểm nên đóng băng:

> Flags được mô hình hóa như **machine resource**, không nhất thiết như một normal register.

Ví dụ:

```text
MachineResource::Flags
```

Instruction descriptor:

```text
implicit_defs = Flags
implicit_uses = Flags
```

---

# 17. Instruction Descriptor

Đây sẽ là trung tâm của Machine IR.

```text
InstructionDesc {
    opcode
    operands[]
    implicit_uses[]
    implicit_defs[]
    clobbers
    constraints
    features
    encoding
    latency
    throughput
    size
    flags
}
```

---

# 18. Operand descriptor

```text
Operand {
    kind
    constraint
}
```

Kind:

```text
Register
Immediate
Memory
Label
Block
Condition
RegisterMask
StackSlot
Symbol
```

---

# 19. Register constraint

Ví dụ x86 `imul` có thể yêu cầu:

```text
RAX
```

cho một operand.

Không nên encode:

```text
if opcode == IMUL:
    force RAX
```

trong allocator.

Instruction descriptor phải nói:

```text
operand[0] = fixed physical RAX
```

---

# 20. Tied operands

Một số instruction yêu cầu:

```text
destination == input
```

Ví dụ:

```text
x86:
imul r64
```

có thể sử dụng:

```text
RAX = RAX * operand
```

Machine IR cần:

```text
tied_operand(0, 1)
```

Register allocator sẽ đảm bảo cùng register.

---

# 21. Early-clobber

Một số instruction ghi output trước khi đọc toàn bộ input.

Machine constraints cần:

```text
EarlyClobber
```

để allocator không cấp cùng register sai cách.

---

# 22. Multiple definitions

Ví dụ:

```text
DIV
```

có thể tạo:

```text
RAX = quotient
RDX = remainder
```

Machine IR:

```text
DIV {
    defs: [v_q, v_r]
    uses: [v_dividend, v_divisor]
}
```

Instruction descriptor mô tả fixed register constraints.

---

# 23. Implicit operands

Ví dụ x86:

```text
DIV
```

ngầm sử dụng:

```text
RAX
RDX
```

và định nghĩa:

```text
RAX
RDX
```

Không được giấu thông tin này khỏi IR.

```text
implicit_uses = [RAX, RDX]
implicit_defs = [RAX, RDX]
```

---

# 24. Memory operand

Đây là phần cực quan trọng.

Không nên hạ ngay:

```text
LOAD [address]
```

thành một register chứa address + load riêng nếu target có addressing mode mạnh.

Machine IR nên có:

```text
MemoryOperand {
    base
    index
    scale
    displacement
    segment
    address_space
    alignment
}
```

---

# 25. x86 addressing

Ví dụ:

```text
mov rax, [rbx + rcx*8 + 32]
```

Machine IR:

```text
MemoryOperand {
    base = RBX
    index = RCX
    scale = 8
    displacement = 32
}
```

Instruction selector có thể fold:

```text
ADD address
LOAD
```

thành một memory operand.

---

# 26. AArch64 addressing

AArch64 có:

```text
[base, #imm]
[base, index]
[base, index, shift]
```

Machine IR memory operand có thể biểu diễn generic:

```text
base
index
scale
shift
offset
```

Target legalization reject những combination không hợp lệ.

---

# 27. RISC-V

RISC-V chủ yếu:

```text
offset(base)
```

Nếu LIR yêu cầu:

```text
base + index*8
```

legalizer phải biến thành:

```text
MUL
ADD
LOAD
```

Đây là lý do cần:

```text
Legalization
```

trước encoding.

---

# 28. AddressingMode abstraction

Không nên để LIR biết x86 addressing.

Machine IR có:

```text
AddressExpr {
    base
    index
    scale
    offset
}
```

Target legalization quyết định instruction nào có thể consume expression trực tiếp.

---

# 29. Immediate operands

Immediate phải có semantic width:

```text
Imm {
    value
    width
    signedness
}
```

Không đơn giản:

```text
int64
```

Ví dụ x86:

```text
imm8
imm32
```

AArch64:

```text
12-bit shifted immediate
```

RISC-V:

```text
12-bit signed
```

Legalizer phải kiểm tra.

---

# 30. Constant materialization

Nếu:

```text
const 0x123456789ABCDEF0
```

không fit immediate:

Machine lowering có thể tạo:

```text
MOVZ
MOVK
MOVK
MOVK
```

hoặc literal pool.

LIR chỉ nói:

```text
CONST large_integer
```

Machine legalizer quyết định.

---

# 31. Symbol operands

Machine IR cần:

```text
SymbolRef {
    symbol
    relocation_kind
}
```

Ví dụ:

```text
LOAD_GLOBAL foo
```

có thể thành:

```text
RIP-relative
GOT
TLS
absolute
```

tùy target/PIE/model.

---

# 32. Relocation không thuộc instruction selector

Instruction selector chỉ tạo:

```text
SymbolRef
```

Object writer mới quyết định relocation encoding.

Pipeline:

```text
Machine IR
 ↓
Encoder
 ↓
Encoded instruction + relocation
 ↓
Object
```

Không để ELF knowledge vào x86 instruction selector.

---

# 33. Instruction encoding

Instruction descriptor có:

```text
Encoding {
    format
    fields[]
    opcode_bits
    prefix_rules
    relocation_sites
}
```

Ví dụ conceptual:

```text
MOV_R64_RM64
```

có:

```text
REX.W
opcode
ModRM
SIB
disp
```

Encoder đọc descriptor và operands.

---

# 34. Không dùng external assembler

Mục tiêu Axiom cuối cùng:

```text
Machine IR
 ↓
Axiom Encoder
 ↓
machine bytes
```

Không:

```text
Axiom
 ↓
.asm
 ↓
NASM/GAS
```

Điều này phù hợp mục tiêu self-contained compiler.

---

# 35. Instruction feature requirements

Instruction descriptor:

```text
features = [
    SSE2
]
```

hoặc:

```text
AVX2
```

hoặc:

```text
AArch64::LSE
```

Compiler target:

```text
x86-64 baseline
```

không được phát ra AVX2 nếu target không cho phép.

---

# 36. Target features

Có ba mức:

```text
Required
Available
Preferred
```

Ví dụ:

```text
AVX2
```

có thể:

```text
required by function
available target
preferred optimization
```

---

# 37. CPU-specific optimization

Ví dụ:

```text
-march=znver4
```

target feature set:

```text
SSE
SSE2
AVX
AVX2
AVX512...
```

Machine optimizer có thể chọn:

```text
instruction latency
throughput
```

phù hợp CPU.

Nhưng semantic correctness không phụ thuộc CPU tuning.

---

# 38. Instruction cost model

Descriptor:

```text
latency
throughput
size
```

không phải absolute truth cho mọi CPU.

Nên:

```text
InstructionCostModel
```

là target CPU-specific.

Ví dụ:

```text
GenericX86
Zen4
Skylake
AppleM
```

Machine scheduler dùng model tương ứng.

---

# 39. Instruction semantics

Đây là phần rất quan trọng cho verifier/optimizer.

Mỗi instruction cần có machine effect:

```text
defs
uses
memory
flags
side_effects
```

Ví dụ:

```text
ADD
    reads dst
    reads src
    writes dst
    writes flags
```

---

# 40. Side effects

Instruction flags:

```text
Pure
MayTrap
ReadsMemory
WritesMemory
Volatile
Barrier
Call
Branch
Return
```

Ví dụ:

```text
ADD
```

gần như pure ngoài flags.

```text
LOAD
```

reads memory.

```text
STORE
```

writes memory.

```text
SYSCALL
```

side-effecting/call-like.

---

# 41. Trap semantics

Một số instructions có thể trap:

```text
DIV
LOAD
STORE
```

nếu invalid.

Optimizer không được tùy tiện biến:

```text
may_trap
```

thành:

```text
no_trap
```

trừ khi chứng minh.

---

# 42. Undefined machine behavior

Ở machine level có những operations target-specific.

Ví dụ:

```text
ud2
```

Axiom có:

```text
TRAP
```

và target encode:

```text
UD2
BRK
EBREAK
```

Tốt hơn là optimizer hiểu semantic:

```text
UNREACHABLE
```

và:

```text
TRAP
```

khác nhau.

---

# 43. `UNREACHABLE`

`UNREACHABLE` nghĩa:

> Compiler đã chứng minh control flow không thể đến đây trong defined execution.

Có thể không phát sinh instruction.

`TRAP` nghĩa:

> Nếu execution đến đây, phải gây machine-level failure.

Hai cái không được nhập làm một.

---

# 44. Branch

Machine IR:

```text
BR target
BRCOND condition, target_true, target_false
```

Target legalizer có thể:

```text
CMP
JCC
```

hoặc:

```text
CBZ
```

hoặc:

```text
BNE
```

---

# 45. Condition materialization

Nếu source cần:

```text
bool x = a < b;
```

Machine IR có thể:

```text
CMP a,b
SETCC LT → v0
```

Nhưng nếu:

```text
if a < b
```

thì không nhất thiết tạo bool:

```text
CMP
JLT
```

Instruction selector phải phân biệt:

```text
condition as control-flow
```

và:

```text
condition as value
```

---

# 46. Select

LIR:

```text
v3 = SELECT cond, v1, v2
```

Machine legalizer:

x86:

```text
CMOV
```

hoặc branch.

AArch64:

```text
CSEL
```

GPU có thể khác.

---

# 47. Machine basic block

Machine IR vẫn dùng:

```text
MachineFunction
    MachineBasicBlock[]
```

Mỗi block:

```text
instructions
successors
predecessors
```

Sau block layout:

```text
fallthrough
branch
jump
```

được tối ưu.

---

# 48. CFG vẫn rất quan trọng

Machine optimizer có thể thực hiện:

```text
branch folding
block merging
jump threading
fallthrough optimization
cold block outlining
```

nhưng không được phá:

```text
exception/unwind edges
```

nếu panic=unwind.

---

# 49. Unwind information

Machine IR cần đánh dấu các instruction thay đổi frame state:

```text
CFI_DEF_CFA
CFI_OFFSET
CFI_RESTORE
```

nhưng tốt hơn:

> Không nhúng DWARF encoding trực tiếp vào Machine IR.

Machine IR có:

```text
FrameState
```

hoặc abstract unwind directives.

Target object writer biến chúng thành:

```text
.eh_frame
.pdata/.xdata
```

---

# 50. Debug location

Mỗi Machine instruction nên có:

```text
DebugLoc {
    source_file
    line
    column
    inline_chain
}
```

Nhưng debug metadata không được làm thay đổi generated semantics.

Optimizer có thể merge/remove debug locations.

---

# 51. Inline function provenance

Nếu:

```text
foo()
```

inline vào:

```text
bar()
```

Machine IR cần giữ:

```text
inline chain
```

để debugger biết:

```text
bar → foo → ...
```

---

# 52. Machine instruction identity

Không dùng opcode string.

```text
OpcodeId
```

Ví dụ:

```text
X86_ADD_R64_RM64
A64_ADD_X
RV64_ADD
```

Các opcode này target-specific.

Generic Machine IR có thể có:

```text
GenericADD
```

trước legalization.

Sau legalization:

```text
X86_ADD_R64_RM64
```

---

# 53. Generic machine opcodes

Có hai lựa chọn:

### A

LIR → trực tiếp target-specific Machine IR.

### B

LIR → generic Machine IR → target-specific.

Tôi chọn:

```text
LIR
 ↓
Target Legalization
 ↓
Target-specific Machine IR
```

Không thêm một generic machine layer nữa.

Lý do:

```text
LIR
```

đã là generic low-level layer.

Thêm:

```text
Generic MIR
```

sẽ tăng compiler complexity mà không mang nhiều lợi ích.

---

# 54. Machine IR instruction descriptor

Kiến trúc đề xuất:

```text id="w0n0qt"
InstructionDesc {
    opcode
    mnemonic

    operands
    defs
    uses

    implicit_defs
    implicit_uses

    register_constraints
    tied_operands
    early_clobbers

    memory_behavior
    side_effects

    required_features

    encoding

    size
    latency
    throughput
}
```

Đây có thể trở thành **single source of truth** cho backend.

---

# 55. Machine verifier

Trước register allocation:

```text id="7d5v3r"
MachineVerifier
```

kiểm tra:

- opcode hợp lệ
- operands đúng type
- register class đúng
- fixed register constraint hợp lệ
- tied operands
- implicit defs/uses
- memory operands
- required features
- CFG
- branch targets
- physical/virtual register consistency
- flags dependency
- call clobbers

Sau register allocation chạy verifier lần nữa.

---

# 56. Hai trạng thái Machine IR

### Pre-RA

```text id="8h4x0m"
Virtual registers
+
physical fixed registers
```

### Post-RA

```text id="m2q3u6"
Physical registers only
```

Sau RA:

> Không được còn virtual register.

Invariant cực kỳ quan trọng.

---

# 57. Post-RA Machine IR

Ví dụ:

```text id="lyu9v9"
MOV v0, v1
ADD v0, v2
RET v0
```

sau RA:

```text id="0sjp70"
MOV RAX, RDI
ADD RAX, RSI
RET RAX
```

Spill:

```text id="w1q8fj"
STORE [stack+16], RAX
LOAD RAX, [stack+16]
```

---

# 58. Register allocator interface

Machine IR nên cung cấp:

```text id="h9e8ur"
LiveInterval
RegisterPressure
RegisterClass
RegisterMask
SpillCost
```

Allocator không cần hiểu:

```text
Result
Option
Trait
ownership
```

---

# 59. Register allocation MVP

Vẫn giữ quyết định trước:

### Bootstrap:

```text id="qv0m9w"
Linear Scan
```

### Sau đó:

```text id="g0j7n2"
Greedy / PBQP-like / advanced allocator
```

Không cần bắt đầu bằng allocator phức tạp.

Điều quan trọng hơn là Machine IR model đúng.

---

# 60. Machine IR invariants

Đóng băng:

### AMIR-60
**Machine IR Is Target-Specific**

### AMIR-61
**Machine IR Uses Explicit Register Classes**

### AMIR-62
**Physical Registers Have Stable Internal IDs**

### AMIR-63
**Register Aliases Are Explicit**

### AMIR-64
**Partial Register Semantics Are Explicit**

### AMIR-65
**Register Units Model Overlap**

### AMIR-66
**Flags Are Explicit Machine Resources**

### AMIR-67
**Instruction Implicit Uses/Defs Are Explicit**

### AMIR-68
**Instruction Constraints Are Declarative**

### AMIR-69
**Tied Operands Are Explicit**

### AMIR-70
**Early-Clobber Constraints Are Explicit**

### AMIR-71
**CALL Clobbers Are Explicit**

### AMIR-72
**Memory Operands Are Structured**

### AMIR-73
**Addressing Modes Are Target-Legalized**

### AMIR-74
**Immediate Constraints Are Target-Defined**

### AMIR-75
**Symbol References Are Relocation-Aware**

### AMIR-76
**Instruction Encoding Is Backend Data**

### AMIR-77
**Instruction Features Are Explicit**

### AMIR-78
**Instruction Costs Are Target-CPU Dependent**

### AMIR-79
**Machine Side Effects Are Explicit**

### AMIR-80
**Trap And Unreachable Are Distinct**

### AMIR-81
**Machine CFG Is Explicit**

### AMIR-82
**Unwind State Is Represented Abstractly**

### AMIR-83
**Debug Locations Are Non-Semantic Metadata**

### AMIR-84
**Pre-RA Machine IR May Contain Virtual Registers**

### AMIR-85
**Post-RA Machine IR Contains No Virtual Registers**

### AMIR-86
**Machine IR Must Pass Verification Before Encoding**

### AMIR-87
**Machine Encoding Requires No External Assembler**

### AMIR-88
**Machine IR Contains No High-Level Type-System Semantics**

---

# 61. Một quyết định kiến trúc rất quan trọng

Tới đây tôi khuyên Axiom **không xây một “universal instruction set”**.

Không nên cố tạo:

```text
AX_ADD
AX_LOAD
AX_VECTOR
```

rồi bắt mọi CPU giả vờ giống nhau mãi.

Thay vào đó:

```text
LIR
```

mới là abstraction chung.

Sau đó:

```text
x86 Machine IR
AArch64 Machine IR
RISC-V Machine IR
WASM Machine IR
```

có thể có những instruction rất khác nhau.

Điều này cho phép Axiom tận dụng đặc điểm CPU thay vì hạ mọi thứ xuống một common denominator.

---

# 62. Pipeline backend hoàn chỉnh

Sau các bước vừa đóng băng:

```text
                     VERIFIED MIR
                           │
                           ▼
                    ABI CLASSIFIER
                           │
                           ▼
                       ABI MIR
                           │
                           ▼
                         LIR
                           │
              ┌────────────┴────────────┐
              │   LIR OPTIMIZATION      │
              └────────────┬────────────┘
                           ▼
                 TARGET LEGALIZATION
                           │
                           ▼
                    MACHINE IR
                           │
                 ┌─────────┴─────────┐
                 │                   │
          Machine Optimization   Pre-RA Verify
                 │                   │
                 └─────────┬─────────┘
                           ▼
                  REGISTER ALLOCATION
                           ▼
                     SPILL/RELOAD
                           ▼
                    FRAME LAYOUT
                           ▼
                  PROLOGUE/EPILOGUE
                           ▼
                   POST-RA OPTIMIZE
                           ▼
                    MACHINE VERIFY
                           ▼
                     INSTRUCTION
                       ENCODING
                           ▼
                       OBJECT
```

Có một tinh chỉnh:

**Pre-RA Machine Optimization** và **Post-RA Machine Optimization** nên là hai nhóm riêng, bởi vì trước RA có thể đổi virtual-register graph rất mạnh, còn sau RA phải bảo toàn physical-register constraints.

---

# Bước kế tiếp

Phần tiếp theo nên là:

## `MACHINE-IR-003 — TARGET LEGALIZATION & INSTRUCTION SELECTION`

Đây là lúc ta thiết kế cách biến:

```text
LIR:
    v3 = ADD v1, v2
```

thành:

```text
x86:
    ADD rax, rbx
```

nhưng đồng thời xử lý những trường hợp khó hơn:

```text
64-bit constant
→ nhiều instruction

vector operation
→ AVX2 / SSE / scalar fallback

division
→ target-specific sequence

large multiply
→ MUL + implicit registers

SELECT
→ CMOV / CSEL / branch

memory addressing
→ LEA / folded addressing

atomic CAS
→ LOCK CMPXCHG / LL-SC / LSE

64-bit division
→ target-specific lowering
```

Đây sẽ là bước quyết định **Axiom có thể tự sinh machine code chất lượng cao hay chỉ là compiler “dịch được code”**.