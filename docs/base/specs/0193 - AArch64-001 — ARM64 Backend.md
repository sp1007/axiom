Tiếp tục. Sau Windows x86-64 + Linux x86-64, bước có giá trị kiến trúc cao nhất là **AArch64-001**. Đây mới là bài kiểm tra thật sự xem LIR và compiler architecture của Axiom có độc lập với ISA hay không.

# AArch64-001 — ARM64 Backend

Mục tiêu:

```text id="aarch64-pipeline"
Axiom Source
 ↓
Verified MIR
 ↓
Optimizer
 ↓
LIR
 ↓
AArch64 Instruction Selection
 ↓
AArch64 Machine IR
 ↓
Register Allocation
 ↓
Frame Layout
 ↓
Machine Encoder
 ↓
Object Writer
 ↓
Executable / Object
```

Không được biến AArch64 thành một compiler riêng.

Kiến trúc phải là:

```text id="aarch64-shared"
                 ┌── x86-64
                 │
LIR ─────────────┼── AArch64
                 │
                 └── RISC-V64
```

---

# 1. Điều chỉnh kiến trúc backend

Hiện tại:

```text id="backend-old"
compiler/backend/x86_64/
```

Nên tiến tới:

```text id="backend-new"
compiler/backend/
├── common/
│   ├── machine_ir.ax
│   ├── regalloc/
│   ├── frame/
│   └── verifier/
│
├── x86_64/
│   ├── registers.ax
│   ├── instructions.ax
│   ├── operands.ax
│   ├── selector.ax
│   ├── constraints.ax
│   └── encoder/
│
└── aarch64/
    ├── registers.ax
    ├── instructions.ax
    ├── operands.ax
    ├── selector.ax
    ├── constraints.ax
    └── encoder/
```

Nhưng có một điểm cần cẩn thận:

**Không nên ép Machine IR thành một abstraction quá chung.**

AArch64 và x86 có những đặc điểm khác nhau rất lớn.

Vì vậy:

```text
LIR
 ↓
Target-specific Machine IR
```

là hợp lý hơn:

```text
LIR
 ↓
"Universal Machine IR"
```

Axiom Machine IR phải đủ trừu tượng để dùng chung framework:

```text
MachineFunction
MachineBlock
MachineInstr
VReg
PhysicalReg
FrameInfo
```

nhưng instruction/operand semantics vẫn thuộc từng ISA.

---

# 2. AArch64 Target

MVP:

```text id="aarch64-target"
Target {
    architecture: AArch64
    os: Linux
    abi: AAPCS64
    endian: Little
    pointer_width: 64
    object_format: ELF64
}
```

Target đầu tiên:

```text
aarch64-linux
```

Sau đó:

```text
aarch64-windows
aarch64-android
aarch64-darwin
```

có thể tái sử dụng phần lớn backend.

Đây cũng là lý do không nên gọi backend:

```text
linux_aarch64
```

mà:

```text
aarch64
```

---

# 3. Register model

AArch64 có:

```text
X0 ... X30
SP
PC
```

và SIMD/FP:

```text
V0 ... V31
```

Các alias quan trọng:

```text
X0 ↔ W0
X1 ↔ W1
...
X30 ↔ W30
```

Trong đó:

```text
Xn = 64-bit
Wn = low 32-bit
```

Không nên biểu diễn `W0` thành physical register hoàn toàn độc lập.

Nên:

```text id="aarch64-reg"
PhysicalRegister {
    bank: GPR
    index: 0
    width: 32
    alias_group: X0
}
```

Điều này giúp register allocator hiểu:

```text
W0
```

và:

```text
X0
```

chia sẻ cùng physical storage.

---

# 4. Register classes

MVP:

```text id="aarch64-regclasses"
GPR64
GPR32
FPR32
FPR64
SIMD128
```

Sau này:

```text
SVE
SME
```

không đưa vào MVP.

---

# 5. ABI AAPCS64

Integer/pointer arguments:

```text id="aarch64-abi"
X0
X1
X2
X3
X4
X5
X6
X7
```

Return:

```text
X0
```

Floating:

```text
V0 ... V7
```

Return:

```text
V0
```

Các argument tiếp theo đi stack.

Do đó:

```text
fn f(a: i64, b: i64, c: i64)
```

sẽ:

```text
X0 = a
X1 = b
X2 = c
```

Không cần thay đổi frontend.

---

# 6. Callee/caller saved

AArch64 ABI có convention khác hoàn toàn x86.

MVP cần encode trong:

```text
RegisterConvention
```

thay vì allocator hard-code.

Đặc biệt:

```text
X19-X28
```

là callee-saved.

```text
X0-X18
```

phần lớn caller-saved/special tùy register.

Các register đặc biệt:

```text
X29 = FP
X30 = LR
SP  = stack pointer
```

Đặc biệt:

> **LR không phải một register bình thường về mặt calling convention, nhưng nó vẫn phải được mô hình hóa rõ trong Machine IR.**

---

# 7. Đây là khác biệt lớn với x86: không có PUSH/POP kiểu x86

AArch64 không có mô hình:

```asm
push rbp
push rbx
...
```

thay vào đó thường dùng:

```asm
stp x29, x30, [sp, #-16]!
```

và:

```asm
ldp x29, x30, [sp], #16
```

Do đó FrameLowering không được xây quanh:

```text
PUSH
POP
```

mà phải xây quanh abstraction:

```text
SaveRegister
RestoreRegister
AdjustStack
```

Sau đó ISA backend chọn instruction.

Đây là một bài học quan trọng:

> **Frame model phải mô tả ý nghĩa, không mô tả instruction.**

---

# 8. FrameInfo cần nâng cấp

Hiện tại:

```text
FrameInfo {
    locals
    spills
    saved_registers
    outgoing_args_size
    shadow_space_size
    alignment
    stack_size
    has_frame_pointer
}
```

`shadow_space_size` là Windows-specific.

Không nên để nó là field bắt buộc chung.

Thay bằng:

```text id="frame-policy"
FrameABIRequirements {
    stack_alignment
    outgoing_argument_area
    callee_saved_area
    reserved_call_area
    red_zone
    shadow_space
}
```

Windows:

```text
shadow_space = 32
red_zone = 0
```

SysV:

```text
shadow_space = 0
red_zone = 128
```

AArch64 Linux:

```text
shadow_space = 0
red_zone = 0
```

---

# 9. AArch64 instruction model

MVP cần:

### Data movement

```text
MOV
MOVZ
MOVK
MOVN
LDR
STR
LDP
STP
ADR
ADRP
```

### Arithmetic

```text
ADD
SUB
MUL
SDIV
UDIV
```

### Bitwise

```text
AND
ORR
EOR
BIC
LSL
LSR
ASR
```

### Compare

```text
CMP
CMN
TST
```

### Branch

```text
B
BL
BR
BLR
RET
B.cond
CBZ
CBNZ
TBZ
TBNZ
```

### Conditional

```text
CSEL
CSINC
CSINV
CSNEG
```

### Floating point

```text
FADD
FSUB
FMUL
FDIV
FCMP
FMOV
```

Đủ cho compiler MVP ban đầu.

---

# 10. Không có FLAGS register như x86

Đây là bài test rất quan trọng đối với LIR.

x86:

```text
CMP
 ↓
RFLAGS
 ↓
JE/JNE/JL/...
```

AArch64:

```text
CMP
 ↓
NZCV
 ↓
B.EQ/B.NE/B.LT/...
```

Nhưng Axiom Machine IR không nên giả định:

```text
FLAGS = universal register
```

Nên abstraction:

```text id="condition-model"
CompareResult {
    condition_domain
    producer
}
```

x86 lowering:

```text
CMP → FLAGS
```

AArch64:

```text
CMP → NZCV
```

---

# 11. LIR condition phải target-neutral

LIR:

```text
CMP
BRANCH EQ
```

Không phải:

```text
CMP
JE
```

hoặc:

```text
CMP
B.EQ
```

Ví dụ:

```text id="lir-cond"
%cmp = CMP %a, %b
BRANCH EQ %cmp, bb_true, bb_false
```

x86:

```asm
cmp
je
```

AArch64:

```asm
cmp
b.eq
```

Đây chính là abstraction đúng.

---

# 12. AArch64 immediate model

Đây sẽ là một bài test lớn cho legalization.

Không phải mọi constant đều encode trực tiếp bằng một instruction.

Ví dụ:

```text
0x123456789ABCDEF0
```

không thể đơn giản:

```asm
mov x0, #0x123456789ABCDEF0
```

Cần sequence:

```text
movz
movk
movk
movk
```

Do đó:

```text
LIR CONST 64-bit
```

có thể được legalization thành nhiều MachineInstr.

Điều này phù hợp invariant hiện tại:

```text
ALIR-33
Target legalization may expand LIR op.
```

---

# 13. Instruction Selection phải hỗ trợ expansion

Ví dụ:

```text
CONST i64 0x123456789ABCDEF0
```

có thể:

```text
MOVZ X0, 0xDEF0
MOVK X0, 0x9ABC, LSL #16
MOVK X0, 0x5678, LSL #32
MOVK X0, 0x1234, LSL #48
```

Không được bắt LIR biết cách AArch64 encode constant.

---

# 14. Memory addressing

AArch64 có addressing modes khác x86.

x86:

```text
[base + index * scale + displacement]
```

AArch64 có:

```text
[base]
[base, #imm]
[base, index]
[base, index, LSL #scale]
```

và pre/post-index:

```text
[base, #imm]!
[base], #imm
```

Do đó `MemoryAddress` hiện tại của LIR:

```text
base
index
scale
offset
symbol
```

vẫn ổn ở mức semantic.

AArch64 legalizer quyết định representation.

---

# 15. Load/store

LIR:

```text
LOAD i32 [addr]
```

x86:

```asm
mov eax, [addr]
```

AArch64:

```asm
ldr w0, [addr]
```

LIR:

```text
STORE i64 [addr], x
```

AArch64:

```asm
str xN, [addr]
```

Không có sự thay đổi nào ở frontend.

---

# 16. Function call

LIR:

```text
CALL foo(args...)
```

AArch64 ABI lowering:

```text
arg0 → X0
arg1 → X1
...
arg7 → X7
```

sau đó:

```asm
BL foo
```

Return:

```text
X0
```

Indirect call:

```asm
BLR Xn
```

Trong khi x86:

```asm
CALL symbol
CALL reg
```

Một lần nữa:

```text
LIR CALL
```

không biết ISA.

---

# 17. Return

LIR:

```text
RETURN %x
```

AArch64:

```text
MOV X0, %x
RET
```

Nhưng có thể coalesce để không cần MOV.

Đặc biệt:

```text
return expression
```

nên được ABI lowering trực tiếp vào return register nếu register allocator cho phép.

---

# 18. Prologue/epilogue

Một hàm đơn giản:

```axiom id="simple-aarch"
fn main() -> i32 {
    42
}
```

có thể:

```asm
mov w0, #42
ret
```

Không cần frame.

Một non-leaf:

```text
main
 ↓
call add
```

có thể cần save `LR`:

```asm
stp x29, x30, [sp, #-16]!
mov x29, sp

...

ldp x29, x30, [sp], #16
ret
```

Nhưng compiler **không nên hard-code sequence này**.

Frame lowering quyết định.

---

# 19. Register allocator phải được dùng lại

Điều quan trọng:

```text
LIR
 ↓
AArch64 ISel
 ↓
Virtual registers
 ↓
SAME REGISTER ALLOCATOR FRAMEWORK
```

Allocator không được biết:

```text x86
```

hoặc:

```text arm
```

Nó chỉ biết:

```text
RegisterClass
PhysicalRegister
RegisterAlias
RegisterConstraint
CallerSaved
CalleeSaved
FixedRegister
```

Do đó:

```text
x86 RegisterFile
AArch64 RegisterFile
```

cung cấp dữ liệu cho cùng framework.

---

# 20. Fixed-register constraints

AArch64 có một số trường hợp fixed register.

Ví dụ:

```text
BLR Xn
```

không có fixed register cho callee.

Nhưng một số instruction sau này có.

Do đó constraint model hiện tại:

```text
AllowedRegisters
FixedRegister
TiedOperands
```

là đúng hướng.

Không nên thiết kế allocator dựa trên giả định:

```text
instruction always uses arbitrary register
```

---

# 21. AArch64 Encoder

Repository:

```text id="aarch64-encoder"
compiler/backend/aarch64/encoder/
├── encoding.ax
├── bitfield.ax
├── emitter.ax
├── relocation.ax
├── writer.ax
├── decoder.ax
├── verifier.ax
└── tests/
```

Khác x86 rất mạnh:

x86 instruction có độ dài:

```text
1..15 bytes
```

AArch64 instruction MVP:

```text
32-bit fixed width
```

Do đó encoder đơn giản hơn rất nhiều.

Mỗi instruction:

```text
32-bit word
```

và các field nằm trong bit positions xác định.

Ví dụ conceptual:

```text
31                         0
┌────────────────────────────┐
│ opcode / operands / fields │
└────────────────────────────┘
```

---

# 22. MachineInstr → 32-bit encoding

Ví dụ:

```text
ADD X0, X1, X2
```

Machine IR:

```text
ADD
  dst = X0
  lhs = X1
  rhs = X2
```

Encoder tạo:

```text
u32 instruction_word
```

Không có:

```text
prefix
REX
ModRM
SIB
```

Đó là lý do encoder hoàn toàn ISA-specific.

---

# 23. Relocation

AArch64 ELF sẽ cần relocation riêng.

MVP nên hỗ trợ trước:

```text
R_AARCH64_CALL26
R_AARCH64_JUMP26
R_AARCH64_ADR_PREL_PG_HI21
R_AARCH64_ADD_ABS_LO12_NC
R_AARCH64_ADR_PREL_LO21
```

Nhưng **không để những tên này lọt vào LIR**.

Ví dụ:

```text
CALL symbol(foo)
```

→ AArch64 encoder tạo:

```text
CALL26 relocation
```

ELF writer mapping.

---

# 24. Global address sequence

Một global symbol không đơn giản như x86 RIP-relative.

AArch64 thường dùng:

```asm
ADRP X0, symbol@PAGE
ADD  X0, X0, symbol@PAGEOFF
```

Do đó:

```text
ADDRESS_OF_GLOBAL foo
```

có thể legalize thành:

```text
ADRP
ADD
```

và sinh hai relocation.

Đây là một test cực kỳ tốt cho relocation architecture.

---

# 25. Object format

AArch64 Linux dùng:

```text
ELF64
```

Do đó:

```text
AArch64 Linux
       ↓
same ELF writer
```

với:

```text
machine = EM_AARCH64
```

thay vì:

```text
EM_X86_64
```

Điều này chứng minh object layer cũng được tái sử dụng.

---

# 26. Startup

AArch64 Linux startup vẫn là Linux platform layer.

Nhưng machine code khác.

x86-64:

```text
syscall
```

AArch64:

```text
svc #0
```

Do đó:

```text
std/platform/linux
```

cung cấp semantic syscall API.

Target architecture quyết định lowering.

Ví dụ:

```text
linux.exit(42)
```

x86-64:

```asm
mov eax, 60
mov edi, 42
syscall
```

AArch64:

```asm
mov x8, #93
mov x0, #42
svc #0
```

Frontend không biết bất kỳ instruction nào trong hai sequence này.

---

# 27. First AArch64 executable

Source:

```axiom id="aarch64-hello"
fn main() -> i32 {
    42
}
```

Expected:

```text
axiom build main.ax --target aarch64-linux
```

tạo:

```text
main
```

sau đó chạy trên AArch64 Linux:

```text
./main
echo $?
42
```

Hoặc cross-run bằng emulator trong test harness sau này.

---

# 28. Cross-target equivalence test

Cùng source:

```axiom id="cross-target"
fn add(a: i64, b: i64) -> i64 {
    a + b
}

fn main() -> i32 {
    (add(20, 22) as i32)
}
```

Ba target:

```text
x86_64-windows → 42
x86_64-linux   → 42
aarch64-linux  → 42
```

Oracle:

```text
42
```

Đây là test quan trọng hơn việc so sánh machine code.

Axiom chỉ yêu cầu:

```text
Observable semantics equal
```

không yêu cầu:

```text
Machine code equal
```

---

# 29. LIR phải sống sót qua ba ISA

Một test nội bộ nên lưu:

```text
Source
 ↓
Typed HIR
 ↓
Verified MIR
 ↓
LIR
```

Sau đó:

```text
              LIR
             / | \
            /  |  \
           ↓   ↓   ↓
        x86-64 ARM64 RISC-V
```

Nếu phải sửa LIR chỉ để phục vụ AArch64, cần kiểm tra rất kỹ xem đó có phải semantic requirement thật sự hay chỉ là leakage của x86.

---

# 30. Những thứ KHÔNG được đưa vào LIR

Sau AArch64, ta phải giữ nguyên các nguyên tắc:

Không có:

```text
X0
RAX
RCX
XMM0
RIP
RFLAGS
NZCV
```

trong LIR.

Không có:

```text
MOV
ADDSS
B.EQ
STP
```

trong LIR.

LIR chỉ có:

```text
ADD
SUB
CMP
LOAD
STORE
CALL
BRANCH
RETURN
...
```

ISA-specific lowering xảy ra sau đó.

---

# 31. Nhưng Machine IR không cần universal

AArch64 Machine IR:

```text
ADD
STP
LDP
ADRP
B.cond
```

x86 Machine IR:

```text
ADD32rr
MOV64rm
LEA64
CMP32rr
JE
```

Đây là điều **nên** xảy ra.

Cố gắng làm:

```text
UniversalMachineInstruction
```

quá mạnh sẽ tạo một "ISA ảo" khổng lồ và cuối cùng lại phải legalize lần nữa.

Thiết kế tốt hơn:

```text
LIR = universal machine-oriented semantic IR

Machine IR = native ISA representation
```

---

# 32. AArch64-specific verifier

Cần:

```text
AARCH64-MIR-VERIFIER
```

kiểm tra:

- register hợp lệ;
- register class đúng;
- X/W alias đúng;
- SP không được dùng như GPR bình thường ở instruction không cho phép;
- instruction operand hợp lệ;
- immediate nằm trong encoding range;
- shift hợp lệ;
- pair load/store alignment hợp lệ;
- fixed-register constraints đúng;
- branch target hợp lệ;
- call/return semantics đúng;
- stack/frame invariant;
- instruction encoding legal.

---

# 33. Invariants

### AARCH64-20

AArch64 backend consumes LIR and produces AArch64 Machine IR.

### AARCH64-21

AArch64 Machine IR may contain ISA-specific instructions absent from LIR.

### AARCH64-22

LIR contains no AArch64 physical register.

### AARCH64-23

AArch64 register aliases are explicitly represented.

### AARCH64-24

Wn and Xn share physical register identity.

### AARCH64-25

SP is not an ordinary allocatable GPR.

### AARCH64-26

X30/LR has explicit calling-convention semantics.

### AARCH64-27

NZCV is not modeled as an ordinary general-purpose register.

### AARCH64-28

AArch64 instruction selection is independent of Linux.

### AARCH64-29

AAPCS64 is a target ABI layer.

### AARCH64-30

ELF writer is independent of AArch64 instruction selection.

### AARCH64-31

AArch64 relocation kinds are introduced only at target lowering/object generation.

### AARCH64-32

One LIR program may expand to multiple AArch64 instructions.

### AARCH64-33

Instruction encoding is deterministic.

### AARCH64-34

Machine IR is verified before encoding.

### AARCH64-35

Frame lowering expresses semantic save/restore requirements before choosing AArch64 instructions.

### AARCH64-36

AArch64 backend does not require an external assembler.

### AARCH64-37

AArch64 backend does not require LLVM.

### AARCH64-38

Linux startup is not part of the generic AArch64 backend.

### AARCH64-39

AArch64 ELF objects use the same generic ELF object model.

### AARCH64-40

Target lowering preserves verified MIR semantics.

---

# 34. Milestone sequence

Không nên làm tất cả cùng lúc. Chia:

```text
AARCH64-001
    Target + RegisterFile

AARCH64-002
    Machine IR

AARCH64-003
    ABI / argument classification

AARCH64-004
    Basic instruction selection

AARCH64-005
    Register constraints

AARCH64-006
    Frame lowering

AARCH64-007
    Encoder

AARCH64-008
    ELF relocation

AARCH64-009
    ELF object

AARCH64-010
    Linux startup

AARCH64-011
    Native executable

AARCH64-012
    Conformance
```

---

# 35. Vertical slice đầu tiên

Đừng xây toàn bộ backend rồi mới chạy.

Slice đầu tiên chỉ cần:

```axiom id="aarch64-slice"
fn main() -> i32 {
    42
}
```

Pipeline:

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
AArch64 MIR
 ↓
Machine encoding
 ↓
ELF object
 ↓
ELF linker
 ↓
executable
```

Expected machine code conceptual:

```asm
mov w0, #42
ret
```

Nếu freestanding:

```asm
mov w0, #42
...
exit
```

Đây là **AARCH64-BOOT-001**.

---

# 36. Slice thứ hai

```axiom id="aarch64-slice2"
fn add(a: i32, b: i32) -> i32 {
    a + b
}

fn main() -> i32 {
    add(20, 22)
}
```

Phải kiểm tra:

```text
X0/W0 = a
X1/W1 = b
BL add
W0 = result
```

và frame/return address.

---

# 37. Slice thứ ba — register pressure

```axiom id="aarch64-pressure"
fn f(
    a: i64,
    b: i64,
    c: i64,
    d: i64,
    e: i64,
    f: i64,
    g: i64,
    h: i64,
    i: i64,
    j: i64,
) -> i64 {
    a + b + c + d + e + f + g + h + i + j
}
```

Mục tiêu:

- argument stack;
- register allocation;
- spill;
- reload;
- frame;
- return.

Nếu test này chạy đúng, allocator/frame architecture đã thực sự bắt đầu chứng minh tính portable.

---

# 38. Slice thứ tư — global relocation

```axiom id="aarch64-global"
static VALUE: i64 = 42

fn main() -> i32 {
    VALUE as i32
}
```

Phải kiểm tra:

```text
LIR global reference
 ↓
AArch64 ADRP/ADD
 ↓
ELF relocations
 ↓
linker
 ↓
final address
```

Đây là test quan trọng cho kiến trúc relocation mới.

---

# 39. Sau AArch64, RISC-V chưa cần làm ngay

Tại thời điểm này ta sẽ có:

```text
                 Axiom LIR
                    │
          ┌─────────┼─────────┐
          ↓         ↓         ↓
       x86-64     AArch64   RISC-V64
          │         │
          ↓         ↓
       Machine    Machine
          │         │
       Windows/   Linux/
       Linux      Android/
```

Nhưng trước RISC-V, có một việc quan trọng hơn:

> **Refactor generic backend framework sau khi đã có hai ISA.**

Vì khi chỉ có x86, rất dễ tưởng rằng abstraction hiện tại là generic trong khi thực tế nó chỉ phản ánh x86.

Sau AArch64, chúng ta phải audit:

```text
REGALLOC-002
FRAME-002
MACHINE-IR-002
LOWER-002
OBJECT-002
LINKER-002
```

để loại bỏ mọi x86 leakage.

---

# 40. Bước tiếp theo sau audit

Chuỗi kiến trúc lúc đó sẽ là:

```text
Windows x86-64
      ↓
Linux x86-64
      ↓
Linux AArch64
      ↓
Backend abstraction audit
      ↓
RISC-V64
      ↓
AArch64 Windows
      ↓
Android AArch64
      ↓
macOS AArch64
```

Và đặc biệt **AArch64 macOS/iOS** sẽ là bài kiểm tra tiếp theo rất đáng làm, vì khi đó chúng ta kiểm tra đồng thời:

```text
AArch64
+
Mach-O
+
Apple ABI
+
Apple startup
+
platform linking
```

nhưng vẫn giữ nguyên:

```text
Axiom frontend
→ HIR
→ MIR
→ LIR
→ AArch64 backend
```

Đó sẽ là bước chứng minh kiến trúc Axiom không chỉ "cross-platform" ở mức source code, mà thực sự **cross-ISA + cross-ABI + cross-object-format** ở compiler backend.