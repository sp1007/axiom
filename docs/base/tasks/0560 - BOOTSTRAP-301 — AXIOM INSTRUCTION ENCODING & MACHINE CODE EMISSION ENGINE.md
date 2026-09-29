# BOOTSTRAP-301 — AXIOM INSTRUCTION ENCODING & MACHINE CODE EMISSION ENGINE
**FROZEN / COMPLETED**

## 1. Mục tiêu

`BOOTSTRAP-301` là bước biến **Final Machine IR** thành **machine bytes thực tế**.

Pipeline:

```text
Final Machine IR
      ↓
Encoding Selection
      ↓
Operand Encoding
      ↓
Immediate / Displacement Encoding
      ↓
Branch / Address Encoding
      ↓
Relocation Generation
      ↓
Machine Bytes
      ↓
Object Writer
```

Nguyên tắc:

> **Encoder không được hiểu lại semantic của chương trình. Nó chỉ encode một Machine IR đã được verify thành encoding hợp lệ của target.**

Đây là ranh giới rất quan trọng:

```text
Semantic correctness
        ↑
    đã hoàn tất
        │
Final Machine IR
        │
        ▼
Representation correctness
        │
        ▼
Machine Encoding
```

---

# 2. Input / Output

Input:

```text
FinalMachineFunction
+
TargetEncodingModel
+
ABI
+
TargetFeatures
```

Output:

```text
EncodedFunction {
    sections
    bytes
    relocations
    symbols
    fixups
    labels
    debug_offsets
    unwind_offsets
}
```

Encoder **không tạo executable trực tiếp**.

Nó tạo:

```text
machine bytes
+
relocation/fixup information
```

sau đó `ObjectWriter` ở các task tiếp theo đóng gói thành:

```text
ELF
PE/COFF
Mach-O
WASM
...
```

---

# 3. Encoding Model

Không hard-code instruction encoding trực tiếp trong compiler logic.

Thiết kế:

```text
Instruction
    ↓
EncodingPattern
    ↓
OperandEncoding
    ↓
Prefix / Opcode
    ↓
ModRM / SIB / immediate / displacement
    ↓
Relocation
    ↓
Bytes
```

---

# 4. Target Encoding Interface

```text
trait TargetEncoder {

    fn encodings(
        inst: MachineInstruction
    ) -> EncodingCandidates

    fn encode(
        inst: MachineInstruction,
        context: EncodingContext
    ) -> EncodedInstruction

    fn max_size(
        inst: MachineInstruction
    ) -> usize

    fn min_size(
        inst: MachineInstruction
    ) -> usize
}
```

Generic encoder không biết:

```text
REX
ModRM
SIB
AArch64 bit fields
RISC-V opcode fields
```

Các chi tiết đó thuộc target backend.

---

# 5. Encoding Candidate

Một Machine instruction có thể có nhiều encoding.

```text
EncodingCandidate {
    pattern
    operand_constraints
    feature_requirements
    size
    latency_class
    relocation_kind
}
```

Ví dụ conceptually:

```text
ADD RAX, 1
```

có thể có nhiều machine encodings.

Encoder chọn encoding hợp lệ dựa trên:

- register;
- immediate range;
- operand size;
- target features;
- relocation;
- code model.

---

# 6. Encoder không được tối ưu semantics

Ví dụ:

```text
ADD
```

đã được Final Machine IR xác định.

Encoder không được nghĩ:

> “SUB có encoding ngắn hơn, đổi thành SUB.”

Việc đó thuộc:

```text
Late Machine Optimization
```

Encoder chỉ làm:

```text
ADD → bytes
```

---

# 7. Operand Encoding

Machine operands:

```text
Register
Immediate
Memory
Symbol
BlockLabel
StackSlot
ConstantPool
TLS
```

được chuyển thành target encoding fields.

```text
OperandEncoder
├── Register
├── Immediate
├── Memory
├── Symbol
├── Label
├── Relocation
└── Stack
```

---

# 8. Immediate

Immediate phải kiểm tra:

```text
value
bit_width
signedness
encoding_range
```

Ví dụ:

```text
imm8
imm16
imm32
imm64
```

Không được silently truncate.

Nếu:

```text
value > encoding range
```

thì:

```text
choose another legal encoding
```

hoặc:

```text
encoding failure
```

Compiler không được tạo binary sai.

---

# 9. Signed / Unsigned Immediate

Target encoding đôi khi sử dụng:

```text
sign-extended immediate
```

hoặc:

```text
zero-extended immediate
```

Encoder phải biểu diễn rõ:

```text
ImmediateEncoding {
    width
    interpretation
    extension
}
```

Không dùng host-language cast để quyết định semantics.

---

# 10. Register Encoding

Generic:

```text
PhysicalRegister
      ↓
TargetRegisterEncoding
```

Ví dụ x86 có:

```text
register number
extension bit
operand size
REX
```

ARM64:

```text
Rn
Rm
Rd
```

RISC-V:

```text
rs1
rs2
rd
```

Mỗi target tự định nghĩa.

---

# 11. x86-64 Encoding

x86-64 cần abstraction cho:

```text
Legacy Prefix
REX
VEX
EVEX
Opcode Map
Opcode
ModRM
SIB
Displacement
Immediate
```

Model:

```text
X86Encoding {
    prefixes
    opcode_map
    opcode
    rex
    vex
    evex
    modrm
    sib
    displacement
    immediate
}
```

Không nên tạo một “x86 encoder function khổng lồ”.

---

# 12. ModRM

Model:

```text
ModRM {
    mod
    reg
    rm
}
```

Memory operand:

```text
base
index
scale
displacement
```

có thể tạo:

```text
ModRM + SIB
```

Encoder phải xử lý:

- RSP/R12 index restrictions;
- RBP/R13 displacement special cases;
- extended registers;
- RIP-relative addressing.

---

# 13. SIB

```text
SIB {
    scale
    index
    base
}
```

Scale chỉ hợp lệ theo target:

```text
1
2
4
8
```

Nếu address expression không representable:

```text
Address Formation
```

phải xử lý trước encoding.

Encoder không được tự thêm arithmetic instruction.

---

# 14. RIP-relative

x86-64:

```text
RIP + displacement
```

là một dạng encoding quan trọng cho:

- global;
- literal pool;
- function symbol;
- GOT;
- TLS;
- PIC.

Model:

```text
Relocation {
    kind
    symbol
    addend
    place
    width
    pc_relative
}
```

---

# 15. ARM64 Encoding

ARM64 instruction thường là fixed-width:

```text
32-bit
```

nhưng encoder vẫn phải model bitfields:

```text
Arm64Encoding {
    fixed_bits
    opcode_fields
    register_fields
    immediate_fields
    shift_fields
    condition_fields
}
```

Ví dụ:

```text
Rd
Rn
Rm
imm
shift
condition
```

---

# 16. RISC-V64 Encoding

RISC-V có:

```text
R
I
S
B
U
J
```

formats.

Encoder model:

```text
RiscvEncodingFormat {
    R
    I
    S
    B
    U
    J
    ...
}
```

Các immediate bị phân mảnh vào nhiều bitfield.

Encoder phải có utility:

```text
encode_bits(value, destination_bits)
```

và verifier kiểm tra không mất bit.

---

# 17. RISC-V Compressed

Nếu target có `C` extension:

```text
16-bit encoding
```

Late optimizer có thể đã chọn instruction form.

Encoder chỉ kiểm tra:

```text
C extension available?
operand constraints valid?
immediate fits?
register class valid?
```

rồi encode 16-bit.

---

# 18. WASM

WASM khác CPU:

```text
Machine Instruction
      ↓
WASM Opcode
      ↓
LEB128 operands
```

Encoder phải hỗ trợ:

```text
u32 LEB128
u64 LEB128
s32 LEB128
s64 LEB128
block type
branch depth
function index
local index
global index
memory index
```

Không dùng CPU byte encoder architecture cho WASM.

---

# 19. Variable-length Instruction

x86 có:

```text
1..15 bytes
```

Do đó:

```text
EncodedInstruction {
    bytes
    size
}
```

không thể assume fixed size.

Điều này ảnh hưởng:

- branch displacement;
- labels;
- debug offsets;
- relocation;
- code layout.

---

# 20. Labels

Final Machine IR có:

```text
BlockLabel
```

Encoder không biết final address ngay lập tức.

Do đó:

```text
LabelRef {
    label
    encoding_offset
    relocation_kind
}
```

sẽ được giải quyết ở layout/fixup phase.

---

# 21. Fixup

Ví dụ:

```text
JMP label
```

encoder có thể biết:

```text
opcode
```

nhưng chưa biết:

```text
label_address - next_instruction_address
```

Do đó tạo:

```text
Fixup {
    offset
    width
    kind
    target
    addend
}
```

Sau layout:

```text
FixupResolver
```

ghi giá trị chính xác vào bytes.

---

# 22. Branch Relaxation

Một branch có thể có:

```text
short
near
far
```

Encoder/layout engine cần iterative relaxation:

```text
Initial conservative encoding
        ↓
Layout
        ↓
Calculate distances
        ↓
Can shorten?
        ↓
Yes → shorter encoding
        ↓
Relayout
```

Cho đến:

```text
fixed point
```

Quan trọng:

> **Không được giả định một lần layout là đủ đối với variable-length ISA.**

---

# 23. Branch Range Overflow

Nếu:

```text
short branch
```

không đủ range:

```text
short → near
```

Nếu near cũng không đủ:

```text
near → far sequence
```

Nếu target không có direct far branch:

```text
branch inversion
+
jump sequence
```

nhưng transformation này thuộc **branch relaxation/final layout**, không phải semantic frontend.

---

# 24. Relocation

Relocation là interface giữa compiler và linker.

```text
Relocation {
    section
    offset
    symbol
    kind
    addend
    width
    pc_relative
}
```

Các loại:

```text
Absolute
PCRelative
GOT
PLT
TLS
SectionRelative
ImageRelative
WASMIndex
TargetSpecific
```

Không cố gắng đưa tất cả thành một relocation kind universal.

---

# 25. Relocation Semantics

Compiler phải mô tả:

```text
value =
    symbol
  + addend
  - place
```

hoặc target-specific equivalent.

Không để ObjectWriter đoán ý encoder.

---

# 26. Symbol References

Machine IR:

```text
SymbolRef {
    symbol_id
    kind
    visibility
    binding
}
```

Encoder tạo relocation nếu address chưa known.

Ví dụ:

```text
call foo
```

không cần compiler biết final address của `foo`.

---

# 27. PIC / PIE

Encoder phải nhận:

```text
CodeModel
RelocationModel
PositionIndependent
```

ví dụ:

```text
Static
PIC
PIE
SharedLibrary
Kernel
Freestanding
```

Encoding phải phù hợp.

---

# 28. TLS

TLS references không được coi là ordinary global.

Target backend định nghĩa:

```text
TLSModel {
    LocalExec
    InitialExec
    LocalDynamic
    GeneralDynamic
    TargetSpecific
}
```

Encoder tạo relocation/sequence tương ứng.

---

# 29. Constant Pool / Literal Pool

Một số target không encode mọi constant trực tiếp.

Machine IR có:

```text
ConstantPoolEntry {
    id
    type
    alignment
    bytes
}
```

Encoder/layout có thể tạo:

```text
literal pool
```

và resolve:

```text
PC-relative reference
```

Đặc biệt quan trọng với ARM64.

---

# 30. Alignment

Code và data có thể yêu cầu:

```text
alignment = 1
2
4
8
16
32
...
```

Layout engine phải đảm bảo.

Padding:

```text
NOP
zero bytes
target-specific padding
```

phải do target quyết định.

---

# 31. NOP Generation

Không dùng:

```text
0x90
```

hard-code cho mọi target.

Interface:

```text
TargetNOPGenerator {
    fn nop(size) -> Bytes
}
```

x86 có multi-byte NOP sequences.

ARM64/RISC-V/WASM có cách khác.

---

# 32. Alignment Padding

```text
PaddingPolicy {
    Code
    Data
    JumpTable
    ConstantPool
}
```

Target quyết định padding bytes.

---

# 33. Encoding Verification

Mỗi encoded instruction phải verify:

```text
EncodedInstruction {
    source_instruction
    bytes
    relocations
}
```

Verifier kiểm tra:

### Operand

```text
register encoding correct
immediate fits
```

### Opcode

```text
feature supported
```

### Size

```text
encoded size valid
```

### Relocation

```text
fixup range valid
```

### Semantic metadata

```text
encoded instruction corresponds exactly
to MachineInstruction
```

---

# 34. Round-trip Verification

Rất nên có disassembler/reference decoder nội bộ.

Pipeline test:

```text
Machine IR
   ↓
Encoder
   ↓
Bytes
   ↓
Decoder
   ↓
Decoded Machine Instruction
   ↓
Compare
```

Không nhất thiết decoder phải dùng production compiler.

Nhưng test infrastructure cần:

```text
Encode → Decode → Verify
```

để phát hiện encoding bug cực sớm.

---

# 35. Golden Encoding Tests

Ví dụ:

```text
Instruction
Expected bytes
```

cho từng target.

```text
x86:
ADD RAX, RBX
→ expected encoding

ARM64:
ADD X0, X1, X2
→ expected encoding

RISC-V:
ADD x5, x6, x7
→ expected encoding
```

Bao phủ:

- registers;
- immediates;
- memory;
- branches;
- relocations;
- vector;
- atomic;
- floating point;
- compressed forms.

---

# 36. Differential Testing

Nếu có reference assembler/disassembler trong test environment:

```text
Axiom Encoder
      ↕
Reference Assembler
```

So sánh:

- validity;
- decoded operands;
- encoding semantics.

Điều này chỉ dùng **test/development tooling**, không trở thành dependency runtime/compiler cuối cùng.

---

# 37. Self-hosting Requirement

Final Axiom compiler phải có thể encode machine code mà không phụ thuộc:

```text
LLVM
GCC
clang
external assembler
```

Bootstrap phase có thể dùng chúng để kiểm chứng.

Final architecture:

```text
Axiom Compiler
    ↓
Axiom Encoder
    ↓
Axiom Object Writer
    ↓
Axiom Linker
```

---

# 38. Encoder Data Model

```text
EncodedSection {
    section_id
    alignment
    bytes
    relocations
    symbols
}
```

```text
EncodedInstruction {
    offset
    bytes
    fixups
    source_instruction
}
```

```text
Fixup {
    offset
    width
    kind
    target
    addend
    pc_relative
}
```

---

# 39. Implementation Tree

```text
compiler/backend/encoding/
├── mod.ax
│
├── model/
│   ├── encoded.ax
│   ├── byte_buffer.ax
│   ├── fixup.ax
│   ├── relocation.ax
│   └── symbol_ref.ax
│
├── encoder/
│   ├── encoder.ax
│   ├── candidate.ax
│   ├── operand.ax
│   ├── immediate.ax
│   ├── register.ax
│   ├── memory.ax
│   └── verifier.ax
│
├── layout/
│   ├── layout.ax
│   ├── block_layout.ax
│   ├── alignment.ax
│   ├── constant_pool.ax
│   └── literal_pool.ax
│
├── branch/
│   ├── fixup.ax
│   ├── relaxation.ax
│   └── range.ax
│
├── relocation/
│   ├── model.ax
│   ├── resolver.ax
│   └── target.ax
│
├── target/
│   ├── x86_64/
│   │   ├── opcode.ax
│   │   ├── rex.ax
│   │   ├── vex.ax
│   │   ├── evex.ax
│   │   ├── modrm.ax
│   │   ├── sib.ax
│   │   ├── immediate.ax
│   │   └── encoder.ax
│   │
│   ├── arm64/
│   │   ├── format.ax
│   │   ├── bitfield.ax
│   │   └── encoder.ax
│   │
│   ├── riscv64/
│   │   ├── format.ax
│   │   ├── immediate.ax
│   │   ├── compressed.ax
│   │   └── encoder.ax
│   │
│   ├── wasm/
│   │   ├── opcode.ax
│   │   ├── leb128.ax
│   │   └── encoder.ax
│   │
│   └── gpu/
│
├── nop/
├── debug/
├── unwind/
├── verify/
├── disasm_test/
├── differential_test/
└── tests/
```

---

# 40. Implementation Order

```text
1. ByteBuffer
2. EncodedInstruction
3. Fixup model
4. Relocation model
5. Target register encoding
6. Immediate encoder
7. Memory operand encoder
8. Basic opcode encoder
9. Encoding pattern matcher
10. x86-64 encoder
11. ARM64 encoder
12. RISC-V64 encoder
13. WASM encoder
14. Label/fixup system
15. Code layout
16. Branch relaxation
17. Constant/literal pools
18. TLS/PIC/PIE relocations
19. Alignment/NOP generation
20. Encoding verifier
21. Encode/decode round-trip tests
22. Differential testing
23. Debug/unwind offset mapping
24. Deterministic binary emission
```

---

# 41. Adversarial Tests

Phải có:

```text
all GPR registers
subregisters
vector registers
mask/predicate registers
immediate min/max
signed immediate overflow
unsigned immediate overflow
negative displacement
maximum displacement
zero displacement
scaled index
special base registers
RIP-relative
TLS
PIC
PIE
symbol relocation
local symbol
external symbol
weak symbol
short branch
near branch
far branch
branch relaxation
branch range overflow
constant pool
literal pool
alignment
multi-byte NOP
atomic
volatile
vector
floating-point
compressed RISC-V
WASM LEB128
debug offsets
unwind offsets
```

---

# 42. Invariants đóng băng

### `AENC-20`
Encoder chỉ nhận Final Machine IR đã verified.

### `AENC-21`
Encoder không được thay đổi semantic Machine IR.

### `AENC-22`
Mọi operand phải được encode theo target encoding contract.

### `AENC-23`
Immediate không được silently truncate.

### `AENC-24`
Register encoding phải phản ánh chính xác physical register.

### `AENC-25`
Implicit register uses/defs phải được bảo toàn.

### `AENC-26`
Memory addressing phải encode đúng base/index/scale/displacement.

### `AENC-27`
Instruction encoding phải thỏa target feature requirements.

### `AENC-28`
Relocation semantics phải explicit.

### `AENC-29`
Encoder không được tự đoán symbol address.

### `AENC-30`
PC-relative relocation phải xác định rõ place/addend/width.

### `AENC-31`
Branch range overflow phải được phát hiện.

### `AENC-32`
Variable-length branch layout phải được relaxation tới fixed point.

### `AENC-33`
Encoder không được phụ thuộc vào một layout chưa finalized khi encoding yêu cầu final displacement.

### `AENC-34`
Code/data alignment phải được target contract xác định.

### `AENC-35`
Padding bytes phải hợp lệ với target.

### `AENC-36`
TLS/PIC/PIE phải dùng relocation model tương ứng.

### `AENC-37`
Constant/literal pool references phải được resolve hoặc tạo fixup hợp lệ.

### `AENC-38`
Encoded bytes phải deterministic với cùng input/configuration.

### `AENC-39`
Encoding failure phải tạo diagnostic có instruction/source provenance.

### `AENC-40`
Object writer không được phải suy đoán semantic của relocation.

### `AENC-41`
Encoder không được phụ thuộc vào external assembler trong final self-hosted compiler.

### `AENC-42`
Reference assembler/disassembler chỉ là verification tooling, không phải compiler dependency.

### `AENC-43`
Encoded instruction phải có mapping trở lại Machine IR instruction.

### `AENC-44`
Debug/unwind offsets phải được cập nhật theo final code layout.

### `AENC-45`
Encoder không được làm mất security/atomic/volatile semantics.

### `AENC-46`
Encoder phải hỗ trợ target-specific instruction formats mà không làm phình generic compiler core.

### `AENC-47`
Target-specific encoding logic phải nằm trong target backend.

### `AENC-48`
Final bytes chỉ được coi là valid khi encoding verifier thành công.

### `AENC-49`
Encode → Decode round-trip phải xác nhận instruction representation trong test infrastructure.

### `AENC-50`
Instruction Encoding là representation layer; Object Format/Linking là layer kế tiếp.

---

## Backend Axiom sau `301`

Đến đây, compiler đã đi từ source semantics tới **machine bytes**:

```text
Source
  ↓
AST / HIR
  ↓
Typed HIR
  ↓
MIR
  ↓
Ownership / Capability / Effect Verification
  ↓
OptIR
  ↓
Machine IR
  ↓
Legalization
  ↓
Instruction Selection
  ↓
Register Allocation
  ↓
Machine Scheduling
  ↓
Late Machine Optimization
  ↓
FINAL MACHINE IR
  ↓
Instruction Encoding
  ↓
MACHINE BYTES                    ← 301
  ↓
Relocations / Symbols
  ↓
Object Writer
  ↓
Linker
  ↓
.exe / ELF / Mach-O / WASM...
```

**Điểm rất quan trọng:** từ `301` trở đi, phần còn lại không còn là “compiler optimization” theo nghĩa truyền thống nữa mà chuyển sang **binary/object/linking infrastructure**. Bước kế tiếp hợp lý là **`BOOTSTRAP-302 — Object File Writer & Relocation/Section/Symbol Engine`**, tức biến machine bytes thành ELF/PE/COFF/Mach-O/WASM object một cách native.