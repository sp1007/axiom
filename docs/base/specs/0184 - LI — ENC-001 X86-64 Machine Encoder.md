# LI — ENC-001: X86-64 Machine Encoder

Ta hoàn thiện tầng **Machine IR → bytecode x86-64**. Đây là điểm Axiom bắt đầu tự tạo machine code thực sự, không qua assembler.

Pipeline:

```text
Machine IR
   ↓
X86 Encoding Form
   ↓
Prefix
   ↓
REX
   ↓
Opcode
   ↓
ModRM
   ↓
SIB
   ↓
Displacement
   ↓
Immediate
   ↓
Bytes + Relocations
```

---

## 1. Nguyên tắc encoder

Encoder **không hiểu**:

- ownership
- borrow/view
- trait
- generic
- Drop
- MIR
- ABI semantics cấp cao

Nó chỉ hiểu:

```text
MachineInstr
```

và target x86-64.

Invariant:

```text
AENC-20
Encoder does not change program semantics.

AENC-21
Encoder does not perform register allocation.

AENC-22
Encoder does not perform linking.

AENC-23
Unresolved symbols become relocations.

AENC-24
Physical registers determine register encoding.

AENC-25
Encoding form is explicit.

AENC-26
Encoding is deterministic.

AENC-27
No assembler is required.

AENC-28
Encoder output is independently verifiable.
```

---

# 2. Encoding abstraction

Không viết:

```text
if opcode == ADD ...
if opcode == MOV ...
```

rải khắp encoder.

Dùng:

```text
EncodingForm {
    opcode
    prefixes
    operand_encoding
    rex_policy
    modrm_policy
    sib_policy
    immediate_policy
    displacement_policy
}
```

Ví dụ conceptual:

```text
ADD32rr
    opcode = 01 /r
    dst = ModRM.reg
    src = ModRM.rm
```

---

# 3. Operand encoding kinds

```text
EncodingOperand =
    OpcodeRegister
    ModRMReg
    ModRMRM
    SIBIndex
    SIBBase
    Immediate
    Displacement
    Relative
    FixedRegister
```

Điều này cho phép một instruction definition mô tả encoding thay vì viết encoder riêng.

---

# 4. Register encoding

```text
RegisterEncoding {
    code: u4
    rex_required: bool
}
```

Ví dụ conceptual:

```text
RAX = 0
RCX = 1
RDX = 2
RBX = 3
RSP = 4
RBP = 5
RSI = 6
RDI = 7
R8  = 0 + REX.B
...
R15 = 7 + REX.B
```

---

# 5. REX

```text
REX = 0100WRXB
```

Axiom representation:

```text
Rex {
    W: bool
    R: bool
    X: bool
    B: bool
}
```

Encoder tự sinh REX từ operands.

Ví dụ:

```text
MOV R8, RAX
```

sẽ cần `REX.R`.

```text
MOV RAX, R8
```

cần `REX.B`.

```text
MOV R8, R9
```

có cả `R` và `B`.

---

# 6. Không cho Machine IR chứa REX

Machine IR:

```text
MOV R8, R9
```

Không:

```text
MOV REX.RB, R8, R9
```

Điều này giữ Machine IR độc lập với byte encoding.

---

# 7. Opcode bytes

```text
Opcode {
    bytes[]
    map
}
```

MVP phải hỗ trợ:

```text
one-byte opcode
0F map
0F 38 map
0F 3A map
```

Mặc dù MVP chưa cần toàn bộ instruction set.

---

# 8. ModRM

```text
ModRM {
    mod: u2
    reg: u3
    rm: u3
}
```

Các mode:

```text
00
01
10
11
```

Trong đó:

```text
11 = register
```

và:

```text
00/01/10 = memory
```

---

# 9. SIB

```text
SIB {
    scale: u2
    index: u3
    base: u3
}
```

scale:

```text
00 → 1
01 → 2
10 → 4
11 → 8
```

---

# 10. Memory encoder

Machine operand:

```text
Memory {
    base
    index
    scale
    displacement
}
```

Ví dụ:

```text
[RAX + RCX*4 + 16]
```

encoder quyết định:

```text
ModRM
+
SIB
+
disp8
```

nếu `16` phù hợp.

---

# 11. RIP-relative

PE/COFF và x86-64 đều cần RIP-relative addressing.

Ví dụ:

```text
MOV RAX, [RIP + disp32]
```

Machine operand:

```text
Memory {
    base = RIP
    displacement = symbol
}
```

Encoder:

```text
opcode
ModRM
disp32 = relocation
```

Đây sẽ rất quan trọng cho:

- global variables
- read-only constants
- function references
- jump tables.

---

# 12. Symbol operand

```text
SymbolOperand {
    symbol
    addend
    relocation_kind
}
```

Ví dụ:

```text
CALL foo
```

không encode địa chỉ `foo`.

Nó tạo:

```text
E8 00 00 00 00
```

và relocation.

---

# 13. Relative branches

Ví dụ:

```text
JMP label
```

Machine IR:

```text
JMP block3
```

Nếu block3 nằm gần:

```text
rel8
```

nếu xa:

```text
rel32
```

MVP nên dùng `rel32` trước để đơn giản.

Sau đó thêm branch relaxation.

---

# 14. Branch relaxation

Giai đoạn sau:

```text
JMP rel32
```

có thể giảm thành:

```text
JMP rel8
```

nếu khoảng cách phù hợp.

Tương tự:

```text
Jcc rel32
```

→

```text
Jcc rel8
```

Đây là optimization encoding, không phải semantic optimization.

---

# 15. `MOV`

MVP phải hỗ trợ ít nhất:

```text
MOV r,r
MOV r,imm
MOV r,m
MOV m,r
```

Ví dụ:

```text
MOV EAX,42
```

→ immediate form.

```text
MOV RAX,RBX
```

→ register form.

```text
MOV RAX,[RCX+8]
```

→ memory form.

---

# 16. ALU

Encoder hỗ trợ:

```text
ADD
SUB
AND
OR
XOR
CMP
TEST
```

với:

```text
reg-reg
reg-mem
mem-reg
reg-imm
```

tùy instruction legality.

---

# 17. `LEA`

```text
LEA RAX,[RBX+RCX*4+8]
```

là một encoding form đặc biệt:

```text
opcode
ModRM
SIB
disp
```

không load memory.

---

# 18. Shift

```text
SHL
SHR
SAR
```

có các form:

```text
shift by 1
shift by imm8
shift by CL
```

Do đó encoding form phải phân biệt.

---

# 19. Fixed-register instructions

`IDIV`:

```text
IDIV r/m64
```

Machine IR:

```text
IDIV %v0
```

Encoder chỉ encode operand.

Constraints:

```text
RAX
RDX
```

đã được Machine IR/allocator đảm bảo.

Encoder không tự move operand.

---

# 20. CALL

Direct:

```text
CALL symbol
```

→

```text
E8 rel32
```

Indirect:

```text
CALL RAX
```

→ indirect ModRM form.

---

# 21. RET

```text
RET
```

→

```text
C3
```

Không có relocation.

---

# 22. PUSH / POP

MVP:

```text
PUSH reg
POP reg
```

Dùng cho:

- callee-saved registers
- một số frame strategy.

---

# 23. SYSCALL

```text
SYSCALL
```

là fixed opcode.

Nhưng Windows hosted program **không nên mặc định gọi syscall trực tiếp**.

Platform API layer vẫn dùng:

```text
extern "system"
```

hoặc Axiom Windows library.

`SYSCALL` chỉ cần cho low-level/freestanding/system code.

---

# 24. Encoder API

```text
Encoder {
    fn encode_function(
        function: MachineFunction
    ) -> EncodedFunction
}
```

Kết quả:

```text
EncodedFunction {
    bytes
    relocations
    symbol_offsets
}
```

---

# 25. Relocation

```text
Relocation {
    offset
    type
    symbol
    addend
}
```

Không để encoder phụ thuộc PE hoặc ELF.

Ví dụ:

```text
CALL foo
```

có thể tạo abstract:

```text
REL32(foo)
```

COFF writer sau đó chuyển thành relocation cụ thể.

Đây là một abstraction rất đáng giữ.

---

# 26. Relocation kinds

v0.1:

```text
REL32
ABS32
ABS64
```

Target object writer map:

```text
Windows COFF
Linux ELF
```

sang format-specific relocation.

---

# 27. Encoded block

```text
EncodedBlock {
    block_id
    offset
    bytes
}
```

Machine function:

```text
EncodedFunction {
    blocks[]
    relocations[]
}
```

---

# 28. Symbol offsets

Ví dụ:

```text
foo:
    ...
bar:
    ...
```

encoder ghi:

```text
SymbolOffset {
    symbol
    section_offset
}
```

COFF writer dùng nó để tạo symbol table.

---

# 29. Padding

Machine block có thể cần alignment.

```text
ALIGN 16
```

Nhưng alignment nên được biểu diễn như:

```text
MachineDirective::Align
```

không phải fake instruction.

Encoder phát sinh:

```text
NOP
```

hoặc padding bytes phù hợp.

---

# 30. NOP

MVP:

```text
90
```

Sau này có multi-byte NOP để align code:

```text
0F 1F ...
```

---

# 31. Constant pool

Đừng nhét mọi constant lớn trực tiếp vào instruction.

Machine function có:

```text
ConstantPool {
    entries[]
}
```

Ví dụ:

```text
f64 constant
large integer
vector constant
jump table
```

Selector có thể reference:

```text
CONST_POOL #3
```

Encoder/object writer đặt chúng vào section phù hợp.

---

# 32. Jump table

`switch` có thể được lower thành:

```text
jump table
```

Machine IR:

```text
JUMP_TABLE index
```

hoặc target-specific pseudo instruction.

Sau đó lowering thành:

```text
base + index*8
```

và indirect jump.

MVP có thể dùng decision tree trước; jump table là optimization sau.

---

# 33. Pseudo instructions

Machine IR được phép có pseudo:

```text
COPY
LOAD_STACK
STORE_STACK
PROLOGUE
EPILOGUE
```

nhưng:

> **Không pseudo nào được tồn tại khi encoder bắt đầu.**

Pipeline:

```text
Machine IR
 ↓
Pseudo Expansion
 ↓
Real Machine IR
 ↓
Verifier
 ↓
Encoder
```

---

# 34. Đây là điểm cần thêm

```text
compiler/backend/x86_64/
├── pseudo/
│   ├── copy.ax
│   ├── spill.ax
│   ├── prologue.ax
│   ├── epilogue.ax
│   └── expand.ax
```

Encoder chỉ nhận **real instructions**.

---

# 35. Encoder verifier

Trước encode:

```text
verify_encoding_form(instr)
```

Kiểm:

```text
opcode tồn tại
operand count
operand class
register width
memory legality
immediate range
fixed constraints
```

Ví dụ:

```text
MOV EAX,RBX
```

phải bị reject vì width mismatch.

---

# 36. Byte verifier

Sau encode:

```text
EncodedVerifier
```

kiểm:

```text
instruction length > 0
relocation offset hợp lệ
symbol reference hợp lệ
branch target tồn tại
section offset hợp lệ
```

---

# 37. Decoder tối giản

Đây là phần tôi muốn Axiom có ngay từ đầu.

```text
bytes
 ↓
Minimal X86 Decoder
 ↓
DecodedInstr
```

Không cần decode toàn bộ x86.

Chỉ decode subset Axiom compiler phát ra.

---

# 38. Encoder differential test

Có ba kết quả:

```text
Axiom Encoder
External reference decoder
Axiom Minimal Decoder
```

Trong development có thể dùng một decoder/reference implementation bên ngoài để test.

Nhưng:

> production compiler không phụ thuộc nó.

---

# 39. Oracle

Test:

```text
MachineInstr
   ↓
Axiom encoder
   ↓
bytes
   ↓
Axiom decoder
```

và:

```text
MachineInstr'
```

phải tương đương.

Sau đó chạy binary:

```text
native result
```

so với:

```text
semantic Oracle result
```

Đây là đường kiểm chứng mạnh nhất.

---

# 40. Encoder golden tests

Ví dụ:

```text
MOV EAX,42
```

expected:

```text
B8 2A 00 00 00
```

```text
RET
```

expected:

```text
C3
```

```text
MOV RAX,RBX
```

expected:

```text
48 89 D8
```

```text
ADD RAX,RBX
```

expected:

```text
48 01 D8
```

```text
LEA RAX,[RBX+RCX*4+8]
```

expected bytes được golden-test riêng.

---

# 41. Encoder milestone

```text
ENC-001 register encoding
ENC-002 REX
ENC-003 ModRM
ENC-004 SIB
ENC-005 displacement
ENC-006 immediate
ENC-007 MOV
ENC-008 ALU
ENC-009 shifts
ENC-010 CMP/TEST
ENC-011 LEA
ENC-012 CALL/RET
ENC-013 branches
ENC-014 fixed-register instructions
ENC-015 RIP-relative
ENC-016 relocations
ENC-017 constant pool
ENC-018 pseudo expansion
ENC-019 verifier
ENC-020 encoder/decoder differential tests
```

---

# 42. Đến đây Axiom đã vượt qua một mốc rất lớn

Ta có:

```text
Axiom
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
Optimizer
  ↓
LIR
  ↓
x86 Instruction Selection
  ↓
Register Allocation
  ↓
Frame
  ↓
Machine IR
  ↓
X86 Encoder
  ↓
RAW MACHINE BYTES
```

Phần còn thiếu để có `.exe` là:

```text
RAW MACHINE BYTES
      ↓
COFF Object
      ↓
PE64 Linker
      ↓
Windows EXE
```

---

# LII — COFF-001: Windows Object Writer

Đây là bước tiếp theo.

Ta sẽ **không tạo PE trực tiếp từ compiler function**.

Axiom trước tiên tạo:

```text
hello.obj
```

theo COFF.

Sau đó:

```text
axiom-link hello.obj
```

→

```text
hello.exe
```

Kiến trúc:

```text
Machine Encoder
       ↓
EncodedObject
       ↓
COFF Writer
       ↓
.obj
       ↓
PE Linker
       ↓
PE32+
```

---

## 43. COFF object abstraction

```text
CoffObject {
    machine
    sections[]
    symbols[]
    relocations[]
    string_table
}
```

Windows x64:

```text
machine = IMAGE_FILE_MACHINE_AMD64
```

---

## 44. Section MVP

Ban đầu:

```text
.text
.rdata
.data
.bss
```

Trong đó:

```text
.text  = executable + readable
.rdata = readable
.data  = readable + writable
.bss   = readable + writable
```

---

## 45. `.text`

Ví dụ:

```text
.text:
    B8 2A 00 00 00
    C3
```

symbol:

```text
main → offset 0
```

---

## 46. `.rdata`

Dùng cho:

- string literals
- constant pool
- read-only data.

Ví dụ:

```text
hello world
```

không nên nằm trong `.text`.

---

## 47. `.data`

Global mutable:

```axiom
static counter: i32 = 0
```

→ `.data` nếu initialized.

---

## 48. `.bss`

Uninitialized/zero-initialized storage:

```text
static buffer: Array<u8, 4096>
```

có thể map:

```text
.bss
```

Không cần chứa 4096 zero bytes trong object.

---

## 49. COFF symbol table

Symbol:

```text
CoffSymbol {
    name
    value
    section
    type
    storage_class
}
```

MVP cần:

```text
external
static
section
function
object
```

---

## 50. Relocation

COFF relocation gắn với section:

```text
CoffRelocation {
    virtual_address
    symbol_index
    type
}
```

Windows x64 MVP:

```text
IMAGE_REL_AMD64_REL32
IMAGE_REL_AMD64_ADDR64
IMAGE_REL_AMD64_ADDR32
```

---

## 51. Object writer không resolve symbol

Ví dụ:

```text
CALL add
```

object writer ghi:

```text
.text:
E8 00 00 00 00
```

và:

```text
.reloc:
offset = ...
symbol = add
type = REL32
```

Linker mới resolve.

---

## 52. COFF invariants

```text
ACOFF-20
COFF writer preserves encoded machine bytes.

ACOFF-21
Relocations are preserved exactly.

ACOFF-22
Symbol identity is deterministic.

ACOFF-23
Section alignment is explicit.

ACOFF-24
Section flags are explicit.

ACOFF-25
Object writer does not perform semantic optimization.

ACOFF-26
Object writer does not resolve external symbols.

ACOFF-27
Object output is deterministic.

ACOFF-28
No external assembler is required.

ACOFF-29
COFF objects are independently inspectable.
```

---

# 53. Milestone cực quan trọng tiếp theo

Ta sẽ làm:

```text
LII — COFF-001
```

với acceptance test:

```text
source
  ↓
Axiom compiler
  ↓
Machine code
  ↓
hello.obj
```

Sau đó kiểm tra:

```text
hello.obj
 ├── .text
 ├── symbols
 └── relocations
```

**chưa cần linker**.

Khi `.obj` chính xác, ta mới xây:

```text
LIII — PE-LINK-001
```

để tự link thành `.exe`.

Điều này tạo ra một boundary cực sạch:

```text
compiler backend
      │
      ▼
   COFF .obj
      │
      ▼
 Axiom linker
      │
      ▼
   PE32+ .exe
```

và cuối cùng chiếc laptop Windows của bạn sẽ trở thành **platform bootstrap đầu tiên để Axiom tự sinh native executable**, thay vì phải dựa vào Linux/WSL hay LLVM.