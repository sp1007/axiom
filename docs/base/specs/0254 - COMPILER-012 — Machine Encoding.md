Tiếp tục với **COMPILER-012 — Final Machine Verification + Instruction Encoding**.

Đây là bước rất quan trọng vì từ đây Axiom không còn xử lý "ý nghĩa chương trình" nữa mà bắt đầu tạo **byte máy thực sự**.

# COMPILER-012 — Machine Encoding

## 1. Kiến trúc tổng thể

Pipeline chính thức:

```text id="q1n0g7"
Physical Machine IR
        │
        ▼
Machine Optimization
        │
        ▼
Final Machine Verification
        │
        ▼
Branch / Layout Planning
        │
        ▼
Instruction Encoding
        │
        ├── Machine Bytes
        ├── Fixups
        └── Relocations
        │
        ▼
Encoded Function / Section
        │
        ▼
Object Writer
```

Nguyên tắc:

> **Encoder không được suy luận semantics. Nó chỉ encode một Machine IR đã được verify.**

---

# 2. Machine IR phải gần như "assembly có cấu trúc"

Sau COMPILER-011:

```text id="r3j7uw"
ADD RAX, RBX
MOV RCX, [RSP+32]
CALL foo
RET
```

nhưng không phải text assembly.

Machine IR:

```text id="5e8g6z"
Instruction {
    opcode
    operands[]
    implicit_uses[]
    implicit_defs[]
    flags
    memory_behavior
    encoding_info
}
```

Ví dụ:

```text id="3y7m2k"
ADD64 {
    def: RAX
    use: RAX
    use: RBX
}
```

Encoder chỉ cần hỏi:

```text
opcode = ADD64
operands = RAX, RBX
```

→ byte sequence.

---

# 3. Instruction Descriptor

Ta đã có descriptor từ MACHINE-IR-002.

Cần hoàn thiện:

```text id="9c7e1x"
InstructionDesc {
    opcode
    mnemonic

    operand_schema
    implicit_uses
    implicit_defs

    register_constraints
    tied_operands
    early_clobbers

    required_features

    encoding
    size
    latency
    throughput

    side_effects
    memory_behavior
}
```

Trong đó:

```text id="w6v2q9"
encoding
```

là **target-specific**.

Không đưa x86 encoding vào generic Machine IR.

---

# 4. Không dùng text assembly làm intermediate representation

Không nên:

```text id="4j3x5v"
Machine IR
 ↓
"mov rax, rbx"
 ↓
assembler
```

vì như vậy Axiom vẫn phụ thuộc assembler.

Mục tiêu cuối cùng:

```text id="x0y6h1"
Machine IR
 ↓
Axiom Encoder
 ↓
raw machine bytes
```

Không cần:

- GNU as
- NASM
- MASM
- LLVM MC
- external assembler.

---

# 5. Encoder interface

Đề xuất:

```text id="e8m6qk"
InstructionEncoder {
    encode(
        instruction,
        encoding_context
    ) -> EncodedInstruction
}
```

Kết quả:

```text id="z3d7f4"
EncodedInstruction {
    bytes[]
    fixups[]
}
```

Ví dụ:

```text id="5x9p8a"
CALL foo
```

chưa biết địa chỉ `foo`.

Encoder tạo:

```text id="7d0s1n"
bytes = E8 00 00 00 00
fixup = PC_REL32(symbol=foo, offset=1)
```

Object writer/linker xử lý sau.

---

# 6. Fixup ≠ Relocation

Hai khái niệm cần phân biệt.

### Fixup

Thông tin:

> "Byte nào trong instruction cần sửa sau khi biết layout?"

Ví dụ:

```text id="z1w5op"
offset = 1
width = 4
kind = PC_REL32
symbol = foo
```

### Relocation

Thông tin object file:

> "Linker phải áp dụng relocation nào vào section/symbol này?"

Ví dụ:

```text id="j8c1m4"
R_X86_64_PC32
```

Do đó:

```text id="w7n0d3"
Machine IR
 → Encoder
 → Fixup
 → Object Writer
 → Relocation
```

---

# 7. x86-64 encoding

x86 là backend phức tạp nhất trong nhóm đầu tiên.

Một instruction có thể gồm:

```text id="z2n8qa"
Legacy Prefix
REX
Opcode
ModRM
SIB
Displacement
Immediate
```

hoặc:

```text id="6t1x4p"
VEX
Opcode
ModRM
SIB
Disp
Imm
```

hoặc:

```text id="7x8q2s"
EVEX
Opcode
ModRM
...
```

Axiom không nên encode bằng chuỗi if/else khổng lồ.

---

# 8. X86 Encoding Description

Nên có declarative encoding table:

```text id="m2v5k8"
X86Encoding {
    prefixes
    opcode_map
    opcode_bytes

    rex
    vex
    evex

    modrm
    sib

    immediate
    displacement

    operand_bindings
}
```

Ví dụ concept:

```text id="6v9s4n"
ADD r64, r/m64
    opcode = 01 /r
    modrm.reg = dst
    modrm.rm  = src
```

Encoder engine đọc descriptor rồi tạo byte.

---

# 9. ModRM

Đây là thành phần quan trọng:

```text id="e6r2p0"
ModRM:
    mod
    reg
    rm
```

Ví dụ:

```text id="c4h8a1"
ADD RAX, RBX
```

có thể encode:

```text
48 01 D8
```

Encoder phải tính:

```text id="j5d0qa"
REX.W
opcode
ModRM
```

từ operand metadata.

---

# 10. SIB

Memory addressing:

```text id="n4s8q6"
[base + index * scale + displacement]
```

phải hỗ trợ:

```text id="2k3x7v"
base
index
scale ∈ {1,2,4,8}
displacement
```

Machine IR đã có:

```text id="9x2f6k"
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

x86 encoder biến thành:

```text id="r8k1m4"
ModRM + SIB + displacement
```

---

# 11. REX

Không nên để instruction selector tự tạo REX.

Encoder biết:

```text id="3q5h9m"
needs_w
needs_r
needs_x
needs_b
```

và sinh:

```text id="0p4d6v"
REX = 0100WRXB
```

Điều này giảm đáng kể logic rải rác.

---

# 12. AArch64

AArch64 đơn giản hơn nhiều.

Phần lớn instruction:

```text id="f5h1q8"
32-bit fixed width
```

Encoder:

```text id="6j3m9s"
u32 instruction
```

→

```text id="7a2c4k"
4 bytes
```

Endian target quyết định byte order.

Ví dụ conceptual:

```text id="9m6x2p"
ADD X0, X1, X2
```

→ 32-bit instruction word.

Không cần ModRM/SIB.

---

# 13. RISC-V

RISC-V cần:

```text id="1q7f3m"
16-bit compressed
32-bit base
64-bit extensions
```

MVP:

```text id="4v8h0s"
RV64I
```

sau đó:

```text id="n1k6y9"
M
A
F
D
C
V
```

Encoder descriptor:

```text id="p3c5x7"
RiscVEncoding {
    opcode
    funct3
    funct7
    rd
    rs1
    rs2
    immediate
}
```

---

# 14. WASM

WASM không nên đi qua encoder register-machine.

Pipeline:

```text id="y8q4m2"
WASM Machine IR
    ↓
Stackification
    ↓
Structured Control Lowering
    ↓
WASM Opcode Encoding
    ↓
WASM Module
```

Ví dụ:

```text id="j5f7n3"
local.get 0
local.get 1
i64.add
return
```

sau đó encode thành WASM bytes.

---

# 15. Branch encoding

Đây là phần cần đặc biệt chú ý.

Ví dụ x86:

```text id="c7m2v8"
JMP rel8
```

nếu target quá xa:

```text id="r3x9q1"
JMP rel32
```

Axiom cần **branch relaxation**.

---

# 16. Branch relaxation

Không nên ngay từ đầu assume branch size cuối cùng.

Pipeline:

```text id="0j4q7k"
Initial Layout
      ↓
Short Branch Attempt
      ↓
Compute Offsets
      ↓
Check Range
      ↓
Expand Long Branch
      ↓
Re-layout
      ↓
Repeat until stable
```

Ví dụ:

```text id="m8c2y5"
Jcc rel8
```

không đủ:

```text id="h4x7q9"
Jcc rel32
```

---

# 17. Termination của relaxation

Không được lặp vô hạn.

Mỗi expansion phải có:

```text id="s9k3w1"
monotonic size increase
```

Ví dụ:

```text
short → near → long
```

không quay lại ngẫu nhiên.

Do đó algorithm kết thúc khi:

```text id="v2p6m8"
no instruction changed size
```

---

# 18. AArch64 branch range

AArch64 cũng có range giới hạn.

Nếu:

```text id="d4y8p1"
B target
```

không đủ range, có thể lower thành:

```text id="j2m6x9"
ADRP
ADD
BR
```

hoặc sequence phù hợp.

Điều này có thể cần một **late branch relaxation/legalization pass**.

---

# 19. Literal pools

Một số target cần literal pool.

Ví dụ:

```text id="q6m3w8"
large constant
```

không thể encode immediate trực tiếp.

Có thể:

```text id="x1v9c5"
constant → literal pool
```

Machine backend phải hỗ trợ:

```text id="p8k2d4"
LiteralPool {
    constants[]
    alignment
    placement
}
```

MVP x86-64 có thể giảm nhu cầu này vì có nhiều immediate/addressing mechanisms.

AArch64 sẽ cần sớm hơn.

---

# 20. Constant materialization

Không phải constant nào cũng có một instruction.

Ví dụ:

```text id="h3q7w2"
u64 0x123456789ABCDEF0
```

x86-64 có thể:

```text
movabs rax, imm64
```

AArch64 có thể cần nhiều `MOVZ/MOVK`.

Do đó:

```text id="k6x1m8"
CONST
```

đã được legalization trước đó thành target-appropriate form.

Encoder không tự biến một generic CONST thành 4 instruction.

---

# 21. Encoding và legalization phải tách nhau

Sai:

```text id="r0y7p2"
Encoder gặp constant lớn
→ tự generate instruction sequence
```

Đúng:

```text id="z5n3c9"
Legalization
→ instruction sequence
→ Encoder chỉ encode từng instruction
```

Encoder càng "ngu và chính xác" càng tốt.

---

# 22. Immediate validation

Encoder phải reject:

```text id="b2f8q4"
immediate không nằm trong encoding range
```

Ví dụ descriptor:

```text id="m5j9x1"
ImmediateField {
    bits
    signed
    shift
    alignment
    range
}
```

Encoder kiểm tra:

```text id="s7d3k0"
fits(immediate)
```

Không truncate im lặng.

---

# 23. Shift immediate

Ví dụ một target cho:

```text id="x3p8q6"
shift ∈ [0,63]
```

Nếu IR có:

```text id="n1v5r9"
shift 64
```

thì:

- nếu semantics là masked shift → legalizer đã xử lý;
- nếu semantics là checked → đã có check;
- nếu instruction encoding không biểu diễn được → reject/expand.

Encoder không được tự modulo 64.

---

# 24. Signed displacement

Tương tự:

```text id="p7x2m5"
disp = -128
```

phải encode chính xác theo field.

Nếu:

```text id="c4n8q1"
disp = 5000
```

nhưng field chỉ 8 bit:

```text id="m6y3s9"
reject
```

hoặc instruction legalization trước đó phải chọn sequence khác.

---

# 25. Symbol addresses

Ví dụ:

```text id="d8r1k7"
LEA RAX, symbol(foo)
```

không biết address cuối cùng.

Encoder:

```text id="w2m9x4"
emit placeholder
add fixup
```

Object writer:

```text id="q5c7v3"
emit relocation
```

Linker:

```text id="h1n6z8"
resolve
```

---

# 26. PC-relative addressing

Đây là cơ chế quan trọng cho:

- CALL;
- JMP;
- RIP-relative data;
- PIC.

Ví dụ:

```text id="z9f2c6"
CALL foo
```

conceptually:

```text
disp = address(foo) - address(next_instruction)
```

Nhưng encoder không cần biết address cuối.

Nó chỉ khai báo:

```text id="j4p8s2"
Fixup::PcRelative {
    width = 32
    addend = ...
}
```

---

# 27. PIC

Axiom nên coi PIC/PIE là target/link policy.

Không hard-code vào source semantics.

Ví dụ:

```text id="m5q1v7"
CodeModel:
    Static
    PIC
    PIE
    Large
```

Instruction selection/object writer phối hợp.

---

# 28. Relocation model

Object writer đã có:

```text id="x2c7n9"
Abs
PcRel
Got
Plt
Tls
SectionRelative
TargetSpecific
```

Encoder chỉ tạo fixup đủ thông tin.

Ví dụ:

```text id="f8m3q5"
Fixup {
    offset
    width
    kind
    symbol
    addend
}
```

Object writer chuyển:

```text id="k7v1p4"
FixupKind
```

→

```text
ELF relocation
PE relocation
Mach-O relocation
```

---

# 29. NOP và alignment

Machine layout có thể cần:

```text id="a4z8p2"
.align 16
```

Không được tạo padding tùy ý.

Target backend cung cấp:

```text id="q9n5m1"
nop_sequence(length)
```

x86 có nhiều dạng NOP tối ưu.

AArch64 có NOP 4-byte.

RISC-V tùy extension.

---

# 30. Function alignment

Function có thể có:

```text id="g2k7s5"
alignment = 16
```

Object writer/layout đặt function đúng alignment.

Encoder chỉ cung cấp padding bytes khi cần.

---

# 31. Instruction size

Machine instruction descriptor nên cung cấp:

```text id="e5p9q1"
size_range {
    min
    max
}
```

Ví dụ x86:

```text
JMP:
    short = 2
    near = 5
```

Branch relaxation sử dụng thông tin này.

---

# 32. Encoding size phải deterministic

Cùng:

```text id="m7x3c8"
Machine Instruction
Target
FeatureSet
```

phải cho cùng encoding.

Không có:

```text id="p2n9v5"
random encoding choice
```

trừ khi policy explicitly thay đổi.

---

# 33. CPU features

Ví dụ:

```text id="h8q1m6"
ADD
```

không cần feature.

Nhưng:

```text id="w4k7p2"
AVX2 instruction
```

cần:

```text id="z6m3c9"
Feature::AVX2
```

Machine verifier phải đảm bảo:

```text id="r1v8x4"
RequiredFeatures ⊆ AvailableFeatures
```

---

# 34. Feature policy

Có ba trạng thái:

```text id="b7q2n5"
Required
Available
Preferred
Disabled
```

Ví dụ:

```text
AVX2:
    Available
    Preferred
```

selector có thể chọn AVX2.

Nếu:

```text
AVX2:
    Disabled
```

không được encode.

---

# 35. Final Machine Verifier

Đây là verifier cuối trước bytes.

Kiểm tra:

### Register

```text id="j5v8q2"
no virtual register
valid physical register
valid class
valid alias
```

### Instruction

```text id="s3m7p1"
all operands valid
fixed regs satisfied
tied regs satisfied
early clobber valid
```

### Feature

```text id="c9x2k6"
required feature available
```

### ABI

```text id="v4n8q5"
calls valid
returns valid
stack alignment valid
```

### Memory

```text id="z1p6m9"
alignment valid
address space valid
atomic constraints valid
```

### Control flow

```text id="a8q3w7"
terminators valid
targets valid
```

---

# 36. Encoder verifier

Sau khi encode:

```text id="k3m7x1"
EncodedInstructionVerifier
```

có thể kiểm tra:

```text
encoded_size == expected_size
fixup offsets valid
instruction boundaries valid
```

Không cần full disassembler ở MVP.

Nhưng về sau có thể có:

```text id="n6v2q8"
Axiom Machine Decoder
```

để round-trip test.

---

# 37. Byte round-trip testing

Một test rất mạnh:

```text id="q4x9m2"
Machine IR
 ↓
Encode
 ↓
Decode
 ↓
Machine IR
```

Sau normalization:

```text id="z7p1c5"
original == decoded
```

Đặc biệt hữu ích cho:

- x86;
- AArch64;
- RISC-V.

Axiom sẽ có thể tự kiểm tra encoder của chính mình mà không cần assembler.

---

# 38. Differential testing trong bootstrap

Trong giai đoạn bootstrap:

```text id="m3k8q1"
Axiom Encoder
        vs
LLVM MC / system assembler
```

có thể dùng để kiểm tra.

Nhưng:

> **LLVM chỉ là oracle tạm thời, không phải dependency của compiler cuối.**

Điều này phù hợp bootstrap architecture đã chốt.

---

# 39. Instruction encoder data-driven

Repository:

```text id="d7p2m9"
compiler/
└── machine/
    ├── x86_64/
    │   ├── registers
    │   ├── instructions
    │   ├── encoding
    │   ├── relax
    │   └── encoder
    │
    ├── aarch64/
    │   ├── instructions
    │   ├── encoding
    │   └── encoder
    │
    └── riscv64/
        ├── instructions
        ├── encoding
        └── encoder
```

---

# 40. Không viết hàng nghìn `if`

Không nên:

```text
if opcode == ADD {
   if reg == ...
}
else if opcode == SUB {
...
}
```

Thay vào đó:

```text id="m8q3v6"
Instruction
    ↓
EncodingTemplate
    ↓
OperandBinding
    ↓
FieldEncoder
```

Ví dụ:

```text id="k2p7x9"
X86Template {
    opcode_map
    opcode
    rex_policy
    modrm_policy
    immediate_fields
}
```

---

# 41. X86 operand encoding abstraction

Có thể định nghĩa:

```text id="h4m9c2"
X86OperandEncoding =
    Reg
    RegReg
    RegMem
    MemReg
    RegImm
    RegMemImm
    Accumulator
    Relative
    OpcodePlusReg
    FixedReg
```

Đây không phải semantics.

Chỉ là encoding patterns.

---

# 42. AArch64 encoding abstraction

Ví dụ:

```text id="v6q1p8"
A64Format =
    R
    I
    B
    CB
    LoadStore
    Pair
    MoveWide
    ...
```

Mỗi format biết:

```text id="m3x7k5"
field positions
field widths
operand mappings
```

---

# 43. RISC-V format

```text id="j8p2n6"
R
I
S
B
U
J
```

Ví dụ:

```text id="c4m9x1"
R {
    funct7
    rs2
    rs1
    funct3
    rd
    opcode
}
```

Encoder cực kỳ đơn giản nếu descriptor chính xác.

---

# 44. Encoding errors

Compiler errors cần stable code.

Ví dụ:

```text id="q5v8m2"
AX1801 InvalidPhysicalRegister
AX1802 InvalidInstructionOperand
AX1803 RegisterConstraintViolation
AX1804 FeatureUnavailable
AX1805 ImmediateOutOfRange
AX1806 InvalidMemoryEncoding
AX1807 RelocationOverflow
AX1808 BranchOutOfRange
AX1809 InvalidFixup
AX1810 UnsupportedEncoding
```

Đây là lỗi compiler/toolchain, không phải runtime error.

---

# 45. Branch relaxation architecture

Nên tách:

```text id="s6k1x9"
BranchRelaxer {
    estimate_size()
    layout()
    relax()
    repeat_until_stable()
}
```

Nó làm việc trên Machine IR + layout.

Không nằm trong generic encoder.

---

# 46. Function layout

Thứ tự function:

```text id="n2m7c4"
MachineFunction
```

có thể được sắp xếp bởi:

```text id="p8x3q6"
FunctionLayoutPolicy
```

sau này hỗ trợ:

- hot/cold splitting;
- PGO;
- linker section ordering;
- code locality.

MVP:

```text
source order
```

là đủ.

---

# 47. Basic block layout

Tương tự:

```text id="y4k8m1"
entry
hot successor
cold successor
```

Machine optimizer có thể reorder.

Branch relaxation chạy **sau khi layout ổn định**.

---

# 48. Literal / constant placement

Về lâu dài:

```text id="d5q2x8"
MachineFunction
 ├── code
 ├── literal pools
 └── jump tables
```

Các object này có:

```text id="m7p1v3"
Alignment
Section
Relocation
Reachability
```

Không nhất thiết phải nằm ngay trong `.text`.

---

# 49. Jump tables

`switch` có thể hạ thành:

```text id="k6n3q9"
jump table
```

Machine IR có:

```text id="c8x2m5"
JumpTable {
    entries[]
    entry_size
    encoding
}
```

Object writer/layout xử lý placement.

---

# 50. Encoder không biết Object Format

Đây là separation cuối cùng:

```text id="w5m9q2"
Machine Encoder
    knows:
        ISA
        instruction encoding
        target CPU

Object Writer
    knows:
        ELF
        COFF
        Mach-O
        WASM
```

Encoder không biết:

```text
ELF section
PE section
Mach-O segment
```

---

# 51. Encoder cũng không biết Linker

Ví dụ:

```text id="x8q3m7"
CALL foo
```

Encoder chỉ:

```text
bytes + fixup
```

Linker sau này mới quyết định:

```text
foo address
PLT
GOT
import
weak symbol
```

---

# 52. Final backend contract

Sau COMPILER-012:

```text id="p6n2x8"
Machine IR
      ↓
MachineVerifier
      ↓
Layout
      ↓
BranchRelaxer
      ↓
Encoder
      ↓
Encoded Sections
```

Đầu ra:

```text id="m3q7v1"
EncodedSection {
    bytes
    symbols
    fixups
    alignment
    debug
    unwind
}
```

Sau đó OBJECT-002 tiếp nhận.

---

# 53. Bộ invariant

Đề xuất:

### AENC-34 — Encoding Preserves Machine Semantics

Byte sequence phải biểu diễn đúng Machine IR.

### AENC-35 — Encoder Does Not Perform Semantic Lowering

Encoder không thay đổi semantics.

### AENC-36 — Encoder Does Not Require External Assembler

Axiom có thể tự tạo machine bytes.

### AENC-37 — Encoding Is Deterministic

Cùng input → cùng bytes.

### AENC-38 — Invalid Operands Are Rejected

Không truncate hoặc sửa âm thầm.

### AENC-39 — Immediate Range Is Verified

Immediate phải phù hợp encoding field.

### AENC-40 — Register Encoding Is Target Defined

Physical register ID được target encoder ánh xạ.

### AENC-41 — Register Aliases Are Already Resolved

Encoder không làm register allocation.

### AENC-42 — Fixed Register Constraints Must Already Be Satisfied

Encoder không tự sửa allocation.

### AENC-43 — Feature Requirements Must Be Satisfied

Instruction không được encode nếu target feature unavailable.

### AENC-44 — Memory Address Encoding Is Target Specific

Generic memory operands được target encoder diễn giải.

### AENC-45 — Fixups Are Explicit

Không có địa chỉ chưa biết nào được patch ngầm.

### AENC-46 — Relocation Is Object-Writer Responsibility

Encoder tạo fixup; object writer tạo relocation.

### AENC-47 — Branch Relaxation Is Explicit

Branch size changes phải qua relaxation pass.

### AENC-48 — Branch Relaxation Terminates

Mỗi relaxation iteration phải tiến gần trạng thái ổn định.

### AENC-49 — Alignment Is Explicit

Padding do layout/target policy quyết định.

### AENC-50 — Encoder Does Not Know Object Format

ELF/PE/Mach-O/WASM object semantics nằm ngoài encoder.

### AENC-51 — Encoder Does Not Know Linker Policy

Symbol resolution thuộc linker.

### AENC-52 — Machine Bytes Are Independently Verifiable

Encoded instructions có thể được kiểm tra byte-level.

### AENC-53 — Decoder Round Trip Is Optional But Supported

Backend có thể cung cấp decoder để testing.

### AENC-54 — Bootstrap Differential Testing Is Non-Architectural

LLVM/system assembler chỉ là oracle tạm thời.

### AENC-55 — No Hidden Runtime Dependency

Encoding không yêu cầu compiler runtime.

### AENC-56 — ISA Backend Is Self-Contained

Backend chứa đủ logic cần thiết để encode target ISA.

### AENC-57 — Target Endianness Is Explicit

Byte serialization phải theo target.

### AENC-58 — Encoding Failure Is Compile-Time Diagnostic

Không có runtime fallback cho instruction encoding.

### AENC-59 — Relocation Overflow Is Diagnosed

Không truncate relocation value.

### AENC-60 — Final Encoding Is Independent Of Source Syntax

Encoder chỉ nhìn Machine IR.

---

# 54. Sau COMPILER-012, backend compiler đã "đóng"

Ta đã đi gần như trọn con đường:

```text id="f4k2m8"
Typed HIR
   ↓
Ownership
   ↓
MIR
   ↓
Optimization
   ↓
ABI/Layout
   ↓
LIR
   ↓
Legalization
   ↓
Instruction Selection
   ↓
Machine IR
   ↓
Register Allocation
   ↓
Frame
   ↓
Machine Optimization
   ↓
Encoding
   ↓
Bytes
```

Điều này có một hệ quả rất lớn cho Axiom:

> **Axiom không cần LLVM để trở thành compiler thực sự.**

LLVM vẫn rất hữu ích trong **bootstrap/differential testing**, nhưng kiến trúc cuối cùng đã không phụ thuộc LLVM.

---

# 55. Bước tiếp theo: OBJECT-002

Giờ ta chuyển sang tầng:

```text id="x7m3q1"
Machine Bytes
   ↓
Object Writer
   ↓
ELF / COFF / PE / Mach-O / WASM
```

Cụ thể **OBJECT-002 — Native Object Writer hoàn chỉnh**.

Phần này sẽ chốt:

- section model;
- symbol table;
- local/global/weak symbols;
- COMDAT/linkonce;
- ELF;
- COFF/PE;
- Mach-O;
- relocations;
- GOT/PLT;
- TLS relocations;
- debug sections;
- unwind sections;
- exception/unwind metadata;
- import/export;
- static library;
- object verification;
- deterministic object generation;
- `.axobj` nếu cần format trung gian riêng;
- và cuối cùng **Axiom có thể tự tạo `.o/.obj/.wasm` mà không cần assembler**.

Sau đó mới tới **LINKER-002**, nơi Axiom tự biến các object đó thành **ELF/EXE/Mach-O thực sự**.