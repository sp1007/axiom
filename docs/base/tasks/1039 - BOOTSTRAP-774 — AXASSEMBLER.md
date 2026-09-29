# BOOTSTRAP-774 — AXASSEMBLER

**Title:** Native Machine Instruction Encoder, Register/Instruction Model, Assembly Parser, Relocation Generation, ISA Backends, Inline Assembly & Deterministic Machine-Code Emission Runtime 5.0  
**Namespace:** `AXASSEMBLER`  
**Phase:** Axiom Native Toolchain / Machine Code Generation  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

# 1. Vai trò

`AXASSEMBLER` là tầng chịu trách nhiệm biến **machine instruction representation / assembly representation** thành bytes máy và AXOBJECT.

```text
AXCOMPILER
    ↓
Instruction Selection
    ↓
Machine Instruction IR
    ↓
AXASSEMBLER
    ├── register encoding
    ├── instruction encoding
    ├── immediate encoding
    ├── addressing mode encoding
    ├── relocation creation
    ├── fixups
    └── AXOBJECT emission
          ↓
       AXLINKER
```

AXASSEMBLER **không** quyết định:

- semantic type checking;
- global symbol resolution;
- final virtual addresses;
- final section layout;
- executable format;
- package/build dependency graph.

---

# 2. Mục tiêu thiết kế

AXASSEMBLER phải đạt:

1. không phụ thuộc GNU `as`;
2. không phụ thuộc LLVM MC;
3. không phụ thuộc MASM/NASM;
4. encode trực tiếp machine code;
5. deterministic;
6. target-specific nhưng API thống nhất;
7. có thể chạy độc lập;
8. hỗ trợ compiler backend;
9. hỗ trợ inline assembly;
10. hỗ trợ external assembly interoperability;
11. phát hiện lỗi encoding trước linker;
12. tạo relocation chính xác;
13. có thể tự host bằng Axiom về sau.

---

# 3. Nguyên tắc quan trọng

Không xây assembler theo kiểu:

```text
text assembly
   ↓
parser
   ↓
magic string
   ↓
machine bytes
```

làm kiến trúc chính.

Thay vào đó:

```text
             ┌──────────────┐
Axiom source │              │
compiler ───→│ Machine Inst │
             │   Model      │
             └──────┬───────┘
                    ↓
             AXASSEMBLER
                    ↓
             Encoder backend
                    ↓
               machine bytes
```

Text assembler chỉ là **một frontend**.

---

# 4. Canonical machine instruction model

```text
MachineInstruction {
    opcode
    operands[]
    modifiers
    encoding_constraints
    source_location
}
```

---

# 5. Opcode identity

Opcode không được dùng string làm canonical identity.

```text
OpcodeId : u32
```

Backend có bảng instruction definitions.

---

# 6. Operand model

Canonical operand types:

```text
REGISTER
IMMEDIATE
MEMORY
LABEL
SYMBOL
REGISTER_LIST
VECTOR
MASK
```

---

# 7. Register model

```text
Register {
    class
    index
    width
    flags
}
```

---

# 8. Register classes

Baseline:

```text
GENERAL
FLOAT
VECTOR
MASK
SPECIAL
CONTROL
DEBUG
SYSTEM
```

Không phải target nào cũng implement tất cả.

---

# 9. Register identity

Register được xác định bằng:

```text
RegisterClass
RegisterIndex
RegisterWidth
```

Ví dụ x86-64:

```text
GPR 0 64
GPR 0 32
GPR 0 16
GPR 0 8
```

có thể đại diện các subregister tương ứng.

---

# 10. Register aliases

Backend định nghĩa alias:

```text
RAX
EAX
AX
AL
```

với quan hệ overlap chính xác.

---

# 11. Register overlap

Assembler phải biết:

```text
AL ⊂ AX ⊂ EAX ⊂ RAX
```

để validate instruction operands và implicit clobbers.

---

# 12. Register allocation boundary

AXASSEMBLER **không làm register allocation**.

Việc này thuộc AXCOMPILER backend.

---

# 13. Register constraints

Instruction definition có thể yêu cầu:

```text
specific register
register class
register width
even register
paired register
```

---

# 14. Immediate operand

```text
Immediate {
    value
    width
    signedness
}
```

---

# 15. Immediate validation

Assembler phải reject:

```text
immediate > encoding range
```

thay vì silently truncate.

---

# 16. Symbolic immediate

Có thể:

```text
ImmediateExpression {
    symbol
    addend
    relocation_kind
}
```

---

# 17. Memory operand

```text
MemoryOperand {
    base
    index
    scale
    displacement
    address_width
}
```

---

# 18. Scale

Baseline:

```text
1
2
4
8
```

trên ISA hỗ trợ scaled indexing.

---

# 19. Absolute memory

Target có thể cho phép:

```text
base = NONE
index = NONE
disp = constant/symbol
```

---

# 20. PC-relative address

Operand có:

```text
relative_to = PC
```

và tạo relocation tương ứng.

---

# 21. Label operand

Local control-flow reference:

```text
LabelRef {
    label_id
}
```

---

# 22. Symbol operand

External/global reference:

```text
SymbolRef {
    symbol_id
}
```

---

# 23. Local label

Local labels không cần trở thành global symbols.

Assembler có thể resolve ngay trong section nếu khoảng cách biết được.

---

# 24. Forward label

Assembler phải hỗ trợ:

```text
jump label
...
label:
```

bằng fixup table.

---

# 25. Fixup

```text
Fixup {
    section
    offset
    width
    kind
    expression
}
```

---

# 26. Local fixup

Nếu target address cuối cùng đã xác định trong cùng section, assembler có thể resolve.

---

# 27. Link relocation

Nếu symbol nằm ngoài object:

```text
fixup
 ↓
AXOBJECT relocation
```

---

# 28. Relocation boundary

AXASSEMBLER tạo relocation.

AXLINKER **apply** relocation.

```text
AXASSEMBLER:
S/A/P relationship description

AXLINKER:
final S/P
 ↓
bytes
```

---

# 29. Instruction definition

Mỗi instruction backend cần mô tả:

```text
InstructionDefinition {
    opcode
    operand_pattern
    encoding
    feature_requirements
    implicit_inputs
    implicit_outputs
    flags
}
```

---

# 30. Operand pattern

Ví dụ:

```text
ADD
REGISTER_GPR64
REGISTER_GPR64
```

hoặc:

```text
ADD
REGISTER_GPR64
IMMEDIATE
```

---

# 31. Encoding definition

Encoding không hardcode trong parser.

Backend có encoding descriptors.

---

# 32. x86-64 backend

Baseline phải hỗ trợ:

- legacy prefixes;
- REX;
- VEX;
- EVEX;
- opcode maps;
- ModRM;
- SIB;
- displacement;
- immediate.

---

# 33. x86 opcode maps

Backend phải support:

```text
legacy map
0F
0F 38
0F 3A
```

và extensions cần thiết.

---

# 34. REX

Encoder tự tính:

```text
W
R
X
B
```

không yêu cầu compiler tự xây prefix bytes.

---

# 35. ModRM

Model:

```text
ModRM {
    mod
    reg
    rm
}
```

Encoder tính byte.

---

# 36. SIB

```text
SIB {
    scale
    index
    base
}
```

---

# 37. x86 displacement

Encoder chọn:

```text
disp8
disp32
```

khi semantics cho phép.

---

# 38. x86 immediate

Instruction definition xác định:

```text
imm8
imm16
imm32
imm64
```

và signed extension rules.

---

# 39. x86 branch

Assembler phải support:

```text
short
near
```

branch encoding.

---

# 40. Branch relaxation

Ví dụ:

```text
short jump
```

nếu không đủ range:

```text
near jump
```

---

# 41. Relaxation algorithm

```text
initial encoding
 ↓
resolve local labels
 ↓
range check
 ↓
expand if required
 ↓
repeat until stable
```

---

# 42. Relaxation termination

Assembler phải guarantee termination.

---

# 43. Branch oscillation

Không được có trạng thái:

```text
short → long → short → long
```

do layout instability.

---

# 44. x86 conditional branches

Encoder phải biết:

```text
Jcc
```

condition code encoding.

---

# 45. CALL/JMP external symbol

Ví dụ conceptual:

```text
call foo
```

→ PC-relative relocation nếu ABI/format yêu cầu.

---

# 46. RIP-relative addressing

```text
mov rax, [rip + symbol]
```

phải generate relocation đúng target ABI.

---

# 47. x86-64 code models

Assembler không tự chọn code model.

Compiler supplies constraints.

---

# 48. AArch64 backend

Baseline:

- fixed 32-bit instructions;
- register encoding;
- immediate encoding;
- branch encoding;
- load/store addressing;
- literal pools;
- relocation forms.

---

# 49. AArch64 register model

```text
X0..X30
W0..W30
SP
ZR
```

plus SIMD/FP:

```text
V0..V31
```

---

# 50. AArch64 instruction size

Instruction luôn:

```text
4 bytes
```

ở baseline AArch64.

---

# 51. AArch64 immediate validation

Bitfield encoding phải validate range/alignment.

---

# 52. AArch64 branch

Support:

```text
B
BL
B.cond
CBZ
CBNZ
TBZ
TBNZ
```

ở backend baseline.

---

# 53. AArch64 PC-relative relocation

Assembler tạo symbolic relocation cho các forms như:

```text
ADRP
ADD
LDR literal
BL
```

---

# 54. AArch64 page semantics

Backend phải distinguish:

```text
page(symbol)
pageoff(symbol)
```

để linker không nhầm relocation.

---

# 55. AArch64 load/store

Addressing modes:

```text
base
base + immediate
base + register
pre-index
post-index
```

tùy instruction.

---

# 56. AArch64 literal pools

Assembler phải có abstraction cho:

```text
literal_pool
```

nếu compiler/backend sử dụng.

---

# 57. Literal pool placement

Không được đặt literal ngoài branch/load range.

---

# 58. AArch64 veneers

Nếu branch target vượt range:

```text
branch
 ↓
veneer/stub
```

Việc tạo final veneer thuộc AXLINKER khi target chưa biết.

Assembler chỉ mô tả relocation/range requirements.

---

# 59. WASM backend

WASM không phải machine-code ISA kiểu CPU.

AXASSEMBLER vẫn cung cấp encoder cho:

```text
WASM binary instruction stream
```

---

# 60. WASM instruction model

```text
opcode
immediate
blocktype
memoryarg
index
```

---

# 61. WASM indices

Symbolic references có thể tạo:

```text
function_index relocation
global_index relocation
memory_index relocation
table_index relocation
```

---

# 62. WASM locals

Compiler backend quản lý local allocation.

Assembler encode local indices.

---

# 63. WASM structured control flow

Assembler phải validate nesting:

```text
block
loop
if
else
end
```

---

# 64. WASM stack typing

AXASSEMBLER cần validation đủ để đảm bảo instruction stream hợp lệ, nhưng semantic type checking chính vẫn thuộc AXCOMPILER.

---

# 65. ISA feature model

Mỗi instruction có:

```text
required_features[]
```

Ví dụ:

```text
AVX2
AVX512F
NEON
SVE
```

---

# 66. Feature mismatch

Nếu target không có feature:

```text
ASM_UNSUPPORTED_FEATURE
```

---

# 67. Instruction aliases

Text assembler có thể cho:

```text
mov
```

nhưng canonical representation phải resolve thành instruction ID.

---

# 68. Pseudo instructions

Pseudo-op chỉ tồn tại ở assembly frontend.

Ví dụ:

```text
nop-like
li
la
```

sẽ lower thành real instructions.

---

# 69. Compiler không phụ thuộc pseudo instructions

AXCOMPILER backend có thể tạo canonical machine instructions trực tiếp.

---

# 70. Assembly parser

Text syntax:

```text
label:
    mov rax, rbx
    add rax, 1
```

parser gồm:

```text
lexer
 ↓
parser
 ↓
assembly AST
 ↓
canonical instruction
```

---

# 71. Assembly syntax

Axiom nên có syntax native riêng:

```text
mov rax, rbx
```

và không cần bắt buộc giống NASM/MASM.

---

# 72. Foreign syntax adapters

Có thể hỗ trợ:

```text
Intel-like
AT&T-like
```

qua frontend adapters.

Không để chúng làm canonical representation.

---

# 73. Assembly AST

```text
AsmNode =
    Instruction
    Label
    Directive
    Section
    Constant
    SymbolDeclaration
```

---

# 74. Directives

Baseline:

```text
.section
.global
.extern
.align
.byte
.word
.long
.quad
.zero
```

---

# 75. Directive lowering

Directive phải lower thành AXOBJECT section/symbol/data semantics.

---

# 76. Inline assembly

Axiom hỗ trợ:

```text
asm {
    ...
}
```

nhưng compiler phải quản lý boundary.

---

# 77. Inline asm operands

```text
asm {
    "add %0, %1"
}
```

không phải canonical design.

Native model:

```text
asm {
    add {out}, {in}
}
```

---

# 78. Constraint system

Inline asm cần:

```text
input
output
inout
clobber
memory
register constraint
```

---

# 79. Clobbers

Compiler phải biết register nào bị phá:

```text
clobber("rax")
```

---

# 80. Memory clobber

```text
clobber(memory)
```

ngăn optimizer reorder memory operations qua asm khi semantics yêu cầu.

---

# 81. Volatile asm

```text
asm volatile
```

không được loại bỏ bởi optimizer.

---

# 82. Nonvolatile asm

Compiler có thể eliminate/reorder nếu constraints cho phép.

---

# 83. Unsafe boundary

Inline asm mặc định thuộc:

```text
unsafe
```

context.

---

# 84. Register allocation interaction

Inline asm constraints phải được AXCOMPILER chuyển xuống register allocator.

AXASSEMBLER chỉ validate final chosen operands.

---

# 85. Memory ordering

Assembler không tự tạo memory barriers trừ khi instruction đó thực sự là barrier.

---

# 86. Atomic instructions

Backend encode:

```text
LOCK
CAS
LL/SC
atomic load/store
```

theo ISA.

Semantic atomic ordering thuộc AXCOMPILER/AXTASK/AXMEMORY.

---

# 87. Instruction flags

Instruction definition có thể mô tả:

```text
reads_flags
writes_flags
clobbers_flags
```

---

# 88. Implicit operands

Ví dụ instruction có implicit:

```text
RAX
RDX
FLAGS
```

Backend phải khai báo.

---

# 89. Implicit dependencies

Compiler sử dụng metadata này để scheduling/register allocation.

---

# 90. Instruction latency

Không phải correctness requirement.

Có thể lưu optional:

```text
latency
throughput
```

phục vụ optimizer.

---

# 91. Microarchitecture model

AXASSEMBLER không hardcode performance của CPU.

Performance model thuộc optimization backend.

---

# 92. Encoding database

Instruction definitions nên được generate từ **machine-readable ISA specification data**.

Không nên viết hàng chục nghìn instruction bằng parser logic thủ công.

---

# 93. ISA database

Concept:

```text
ISA DB
 ├── opcode
 ├── operands
 ├── encoding
 ├── features
 ├── aliases
 ├── implicit effects
 └── relocations
```

---

# 94. Generated encoder

Từ ISA DB có thể generate:

```text
instruction matcher
encoder
decoder metadata
validator
```

---

# 95. Decoder

AXASSEMBLER nên có optional decoder:

```text
bytes
 ↓
instruction
```

để:

- disassembler;
- verifier;
- tests;
- diagnostics.

---

# 96. Encoder/decoder symmetry

Mục tiêu:

```text
encode(decode(bytes)) == canonical(bytes)
```

trong supported subset.

---

# 97. Canonical instruction encoding

Nếu nhiều encodings cùng semantics, assembler chọn canonical encoding deterministic.

---

# 98. Shortest encoding

Không phải lúc nào shortest cũng canonical.

Policy phải explicit.

---

# 99. Optimization vs encoding

Compiler quyết định instruction.

Assembler quyết định byte encoding hợp lệ.

---

# 100. Machine code buffer

```text
CodeBuffer {
    bytes
    fixups[]
}
```

---

# 101. Section builder

```text
SectionBuilder {
    append_bytes()
    append_instruction()
    align()
    define_label()
    add_fixup()
}
```

---

# 102. Symbol emission

Assembler có thể:

```text
define_local
define_global
declare_external
```

---

# 103. Local symbols

Local label có thể được stripped khỏi final binary.

---

# 104. Global symbols

Global symbols trở thành AXOBJECT symbols.

---

# 105. External symbols

External declaration tạo undefined symbol.

---

# 106. Alignment directive

Assembler phải emit padding deterministic.

---

# 107. Padding policy

Default:

```text
code alignment → architecture-safe NOP sequence
data alignment → zero
```

---

# 108. NOP generation

x86 backend phải có multi-byte NOP generation.

AArch64 có NOP instruction.

WASM dùng semantics phù hợp.

---

# 109. Data emission

Assembler phải hỗ trợ:

```text
.byte
.u16
.u32
.u64
.f32
.f64
.string
.zero
```

---

# 110. Endianness

Data encoding theo target endianness.

---

# 111. Floating constants

Assembler phải encode IEEE representation chính xác khi target dùng IEEE.

---

# 112. String constants

Native assembly string directives dùng UTF-8 mặc định nếu không chỉ định encoding khác.

---

# 113. UTF-8

Parser source assembler:

```text
UTF-8
```

default.

---

# 114. Identifier encoding

Symbol names internally là UTF-8.

Foreign object names được giữ raw byte representation nếu target ABI yêu cầu.

---

# 115. Symbol mangling

AXASSEMBLER không tự mangle Axiom names.

Compiler chịu trách nhiệm.

---

# 116. C ABI names

External C symbols phải preserve target ABI naming conventions.

---

# 117. Object emission

Sau assembly:

```text
AXASSEMBLER
 ↓
AXOBJECT builder
 ↓
AXO
```

---

# 118. Native object emission

Default native compiler path:

```text
AXCOMPILER
 ↓
AXASSEMBLER
 ↓
AXOBJECT
```

---

# 119. Direct machine-code emission

Compiler có thể bypass text assembly:

```text
MachineInstruction
 ↓
Encoder
 ↓
AXOBJECT
```

Đây là **production path chính**.

---

# 120. Text assembler path

```text
.asm
 ↓
AsmParser
 ↓
MachineInstruction
 ↓
Encoder
 ↓
AXOBJECT
```

Đây là interoperability/developer path.

---

# 121. Error taxonomy

```text
ASM_INVALID_OPCODE
ASM_INVALID_OPERAND
ASM_INVALID_REGISTER
ASM_INVALID_IMMEDIATE
ASM_INVALID_ADDRESSING
ASM_UNSUPPORTED_FEATURE
ASM_INVALID_ENCODING
ASM_RELOCATION_ERROR
ASM_SYMBOL_ERROR
ASM_FIXUP_ERROR
ASM_BRANCH_RANGE
ASM_ALIGNMENT_ERROR
ASM_SYNTAX_ERROR
ASM_DIRECTIVE_ERROR
ASM_INLINE_CONSTRAINT_ERROR
```

---

# 122. Diagnostics

Ví dụ:

```text
error ASM_INVALID_OPERAND:
    instruction `add`
    operand 2
    expected: GPR64 or imm32
    received: vector128
```

---

# 123. Source mapping

Assembler diagnostics preserve:

```text
file
line
column
instruction index
```

---

# 124. Object source metadata

Assembler can emit instruction/source mapping metadata into AXOBJECT.

---

# 125. Determinism

Same:

```text
instruction sequence
target
features
assembler version
```

→ exact same bytes.

---

# 126. Parallel assembly

Independent functions/sections can be assembled concurrently.

---

# 127. Deterministic parallelism

Parallel completion order không được ảnh hưởng:

- symbol IDs;
- section order;
- object bytes;
- relocation ordering.

---

# 128. Thread-local builders

Workers sử dụng local builder.

Sau đó merge deterministic.

---

# 129. No global mutable encoder state

ISA backend data nên immutable/read-only.

---

# 130. Memory architecture

Assembler hot path nên:

```text
arena
small vectors
stack/local structs
```

thay vì heap allocation cho từng operand.

---

# 131. Small-vector optimization

Operand count của instruction thường nhỏ.

Do đó:

```text
InlineArray<Operand, 4>
```

hoặc equivalent là phù hợp.

---

# 132. Object streaming

Assembler có thể stream section contents vào object writer.

---

# 133. Large data sections

Không bắt buộc giữ toàn bộ `.rodata` trong RAM.

---

# 134. Large generated code

Code buffer có thể dùng chunks:

```text
chunk 64 KiB
→ next chunk
```

thay vì realloc liên tục.

---

# 135. Fixup storage

Fixups nên compact:

```text
section_id
offset
kind
symbol_id
addend
```

---

# 136. Branch relaxation storage

Assembler cần giữ đủ thông tin để re-encode branch mà không parse bytes ngược.

---

# 137. No textual round-trip

Compiler không được:

```text
IR
 ↓ stringify assembly
 ↓ parse assembly
 ↓ encode
```

trong production path.

---

# 138. This is critical

Pipeline chuẩn:

```text
IR
 ↓
MachineInstruction
 ↓
Encoder
```

chứ không:

```text
IR
 ↓
assembly text
 ↓
parser
```

Điều này giảm CPU, RAM và tránh lỗi parser.

---

# 139. API

```text
assembler_context_create()
assembler_context_destroy()

assembler_target_open()
assembler_target_features()

assembler_encode_instruction()
assembler_encode_block()

assembler_define_label()
assembler_define_symbol()
assembler_declare_external()

assembler_add_fixup()
assembler_resolve_fixups()

assembler_emit_data()
assembler_align()

assembler_finalize_section()
assembler_finalize_object()
```

---

# 140. Encoder API

```text
encode_instruction(
    target,
    features,
    instruction,
    output
)
```

Result:

```text
encoded_bytes
fixups[]
```

---

# 141. Decoder API

```text
decode_instruction(
    target,
    bytes
)
```

Result:

```text
instruction
length
```

---

# 142. Validation API

```text
validate_instruction()
validate_operands()
validate_encoding()
validate_features()
```

---

# 143. ISA backend API

```text
isa_backend_open()
isa_opcode_lookup()
isa_encode()
isa_decode()
isa_register_lookup()
isa_relocation_map()
isa_feature_check()
```

---

# 144. Inline asm API

```text
inline_asm_parse()
inline_asm_validate()
inline_asm_lower()
inline_asm_constraints()
```

---

# 145. Object API integration

```text
assembler_emit_object()
```

phải trả về AXOBJECT-compatible artifact.

---

# 146. ABI

```text
AXASSEMBLER_ABI_1
```

version độc lập với:

```text
AXOBJECT_ABI_1
```

---

# 147. Bootstrap

Stage 0:

```text
external assembler
```

có thể được dùng để bootstrap.

Stage 1:

```text
Axiom AXASSEMBLER
```

build bởi external compiler.

Stage 2:

```text
AXASSEMBLER
```

build bằng Axiom compiler.

---

# 148. Self-hosting convergence

Kiểm tra:

```text
Stage1 assembler
 ↓ build AXASSEMBLER
Stage2 assembler
 ↓ build itself
Stage3
```

Machine/object artifacts phải hội tụ theo deterministic rules.

---

# 149. External assembler fallback

Cho phép:

```text
--assembler=external
```

nhưng chỉ là compatibility/bootstrap mode.

---

# 150. Production rule

Native AXASSEMBLER phải là default.

External assembler không được là mandatory dependency.

---

# 151. x86-64 minimum ISA

Native backend phải hỗ trợ đủ instruction set để compiler tự bootstrap runtime và compiler, ít nhất:

- integer arithmetic;
- branches;
- calls/returns;
- loads/stores;
- stack operations;
- bit operations;
- shifts;
- comparisons;
- SSE2 baseline;
- required atomic operations.

---

# 152. AArch64 minimum ISA

Ít nhất:

- integer arithmetic;
- branches;
- calls/returns;
- loads/stores;
- stack;
- compare;
- bit operations;
- atomics required by runtime;
- FP/SIMD baseline khi compiler cần.

---

# 153. WASM minimum ISA

Ít nhất:

- integer;
- float;
- control flow;
- memory;
- calls;
- locals;
- globals;
- tables nếu target ABI cần.

---

# 154. CPU feature dispatch

AXASSEMBLER không tự generate runtime dispatch.

AXCOMPILER/AXRUNTIME quyết định multiversioning.

---

# 155. Multi-versioned functions

Assembler chỉ encode từng variant:

```text
foo.default
foo.avx2
foo.avx512
```

---

# 156. Security

Assembler phải reject:

- invalid encodings;
- unsupported privileged instructions trong restricted target mode;
- malformed inline asm constraints.

---

# 157. Privileged instruction policy

Encoding instruction ≠ permission to execute it.

OS/runtime security boundary vẫn thuộc AXSECURITY.

---

# 158. Kernel mode

Axiom toolchain có thể có:

```text
target privilege = user/kernel
```

để compiler/assembler validate appropriate instruction subsets.

---

# 159. W^X

Assembler không quyết định W^X.

Nó chỉ tạo section flags.

AXLINKER/loader enforce final executable layout.

---

# 160. Code signing

Assembler không sign code.

Signature boundary thuộc AXTRUST/AXCRYPTO/platform toolchain.

---

# 161. Binary verification

AXASSEMBLER phải đảm bảo:

```text
instruction encoding valid
```

nhưng không chịu trách nhiệm verify final executable.

---

# 162. Machine-code verifier

Optional decoder có thể kiểm tra:

```text
bytes
 ↓
decode
 ↓
re-encode
```

---

# 163. Golden encoding tests

Mỗi instruction family phải có:

```text
input operands
expected bytes
```

---

# 164. Differential ISA tests

Trong development có thể compare với:

- Intel/AMD documented encoding;
- Arm architecture reference;
- WebAssembly specification.

Production không phụ thuộc external assembler.

---

# 165. Fuzz encoder

Generate random valid instruction operands.

Test:

```text
encode
 ↓
decode
 ↓
canonical compare
```

---

# 166. Invalid operand fuzzing

Random malformed operands không được crash encoder.

---

# 167. Relocation tests

Mỗi relocation class:

```text
symbol
place
addend
width
range
```

được test độc lập.

---

# 168. Branch relaxation tests

Test:

```text
near
far
boundary-1
boundary
boundary+1
```

---

# 169. Alignment tests

Test mọi power-of-two alignment baseline.

---

# 170. Cross-target tests

Một compiler test suite phải có:

```text
x86_64
aarch64
wasm32
```

---

# 171. Cross-format tests

Same instruction/object semantics:

```text
AXO
COFF
ELF
Mach-O
WASM
```

khi target hỗ trợ.

---

# 172. Performance benchmark

Đo:

```text
instructions/sec
MB machine-code/sec
objects/sec
peak memory
```

---

# 173. Large-function benchmark

Assembler phải xử lý function hàng triệu instructions mà không có allocation explosion.

---

# 174. Compilation scaling

Parallel assembly phải scale theo CPU cores trong giới hạn memory bandwidth.

---

# 175. Hot-path rule

Không được:

```text
hash string opcode
regex parse
heap allocate operand
```

cho mỗi compiler-generated instruction.

---

# 176. Canonical internal representation

Compiler nên truyền:

```text
OpcodeId
RegisterId
Immediate
MemoryOperand
```

thay vì strings.

---

# 177. String parsing only at boundary

Text assembly parsing là cold path tương đối.

---

# 178. Generated backend tables

ISA backend tables có thể được generated tại build time.

---

# 179. Backend package

Conceptual:

```text
AXASSEMBLER
 ├── core
 ├── x86_64
 ├── aarch64
 └── wasm32
```

---

# 180. Extension architecture

Future:

```text
riscv64
arm32
power64
```

không được sửa core assembler API.

---

# 181. Target plugin boundary

ISA backend interface:

```text
TargetAssemblerBackend
```

---

# 182. Backend registration

```text
assembler_register_backend()
assembler_find_backend()
```

---

# 183. No dynamic plugin requirement

Built-in backend phải hoạt động mà không cần dynamic plugin.

---

# 184. Static linking

Core compiler có thể statically include target backends.

---

# 185. Cross compiler

Một Axiom compiler binary có thể:

```text
host = x86_64-windows
target = aarch64-linux
```

bằng cách chọn backend target.

---

# 186. Target-independent frontend

AXCOMPILER semantic frontend không biết encoding bytes.

---

# 187. Target-specific lowering

AXCOMPILER backend chuyển typed IR:

```text
Target-independent MIR
 ↓
Target-specific MachineInstruction
 ↓
AXASSEMBLER
```

---

# 188. Register allocation

```text
Machine IR
 ↓
register allocation
 ↓
physical registers
 ↓
AXASSEMBLER
```

---

# 189. Scheduling

Instruction scheduling thuộc compiler optimization/backend, không assembler.

---

# 190. Peephole optimization

Có thể có **encoding-level canonicalization**, nhưng không biến AXASSEMBLER thành optimizer.

---

# 191. Example

Conceptual input:

```text
mov rax, 42
ret
```

Canonical:

```text
MOV
  dst = RAX
  src = IMM(42)

RET
```

Encoder:

```text
instruction
 ↓
opcode definition
 ↓
operand matching
 ↓
encoding selection
 ↓
bytes
```

---

# 192. Relocatable example

```text
call foo
```

Assembler:

```text
CALL rel32
```

và tạo:

```text
relocation {
    type = PC_REL
    width = 32
    symbol = foo
}
```

AXLINKER sau đó giải quyết địa chỉ thực.

---

# 193. Local branch example

```text
jmp L1
...
L1:
```

Nếu cùng section và range biết được:

```text
assembler resolves
```

không cần linker relocation.

---

# 194. External branch

```text
jmp external_function
```

→ AXOBJECT relocation.

---

# 195. Final responsibility split

```text
AXCOMPILER
semantic + optimization + register allocation

AXASSEMBLER
instruction → bytes + fixups

AXOBJECT
artifact representation

AXLINKER
symbols + final addresses + relocations + binary
```

Đây là boundary **không được phá vỡ**.

---

# 196. 40 invariants

```text
ASM-INV-01
Mọi instruction phải có OpcodeId hợp lệ.

ASM-INV-02
Mọi operand phải match instruction definition.

ASM-INV-03
Register phải thuộc register class hợp lệ.

ASM-INV-04
Register width phải tương thích instruction.

ASM-INV-05
Register alias/overlap phải được backend định nghĩa.

ASM-INV-06
Immediate không được silently truncate.

ASM-INV-07
Memory operand phải có addressing mode hợp lệ.

ASM-INV-08
Scale phải thuộc tập được ISA hỗ trợ.

ASM-INV-09
Unsupported ISA feature phải được reject.

ASM-INV-10
Instruction encoding phải deterministic.

ASM-INV-11
Canonical encoding phải deterministic.

ASM-INV-12
Mọi symbolic reference phải có relocation hoặc local resolution hợp lệ.

ASM-INV-13
Fixup offset phải nằm trong section.

ASM-INV-14
Fixup width phải phù hợp encoding.

ASM-INV-15
Relocation semantics phải preserve qua AXOBJECT.

ASM-INV-16
Relocation overflow không được silently truncate.

ASM-INV-17
Local branch relaxation phải terminate.

ASM-INV-18
Branch relaxation không được tạo oscillation.

ASM-INV-19
Forward labels phải được resolve hoặc emit relocation hợp lệ.

ASM-INV-20
Undefined external symbol phải được biểu diễn explicit.

ASM-INV-21
Assembler không thực hiện global symbol resolution.

ASM-INV-22
Assembler không quyết định final virtual addresses.

ASM-INV-23
Assembler không quyết định final section layout.

ASM-INV-24
Compiler-generated machine instructions không cần round-trip qua text.

ASM-INV-25
Text assembly chỉ là frontend, không phải canonical IR.

ASM-INV-26
Inline asm phải khai báo constraints/clobbers hợp lệ.

ASM-INV-27
Unsafe inline asm không được bypass compiler safety boundary silently.

ASM-INV-28
Implicit registers/flags phải được instruction definition khai báo.

ASM-INV-29
Target endianness phải được áp dụng cho data emission.

ASM-INV-30
Alignment padding phải deterministic.

ASM-INV-31
Parallel assembly không được thay đổi output.

ASM-INV-32
ISA tables phải immutable trong encoding hot path.

ASM-INV-33
Assembler parser không được execute embedded code.

ASM-INV-34
Malformed assembly/object emission request không được crash process.

ASM-INV-35
Assembler phải enforce resource limits.

ASM-INV-36
AXASSEMBLER không được yêu cầu external assembler trong production mode.

ASM-INV-37
Native backends phải có target-independent backend interface.

ASM-INV-38
AXASSEMBLER phải emit AXOBJECT-compatible artifacts.

ASM-INV-39
Native ABI phải expose AXASSEMBLER_ABI_1.

ASM-INV-40
Instruction encoding thuộc AXASSEMBLER; semantic compilation và global linking thuộc AXCOMPILER/AXLINKER tương ứng.
```

---

# 197. Definition of Done

`AXASSEMBLER 5.0` được freeze khi có:

- canonical MachineInstruction model;
- opcode database;
- register model;
- operand model;
- immediate validation;
- memory addressing;
- labels;
- symbols;
- fixups;
- relocation generation;
- branch relaxation;
- deterministic encoding;
- AXOBJECT emission;
- text assembly frontend;
- native assembly syntax;
- inline assembly;
- constraints/clobbers;
- x86-64 encoder;
- AArch64 encoder;
- WASM encoder;
- feature validation;
- instruction decoder;
- ISA database generation;
- foreign syntax adapter boundary;
- C ABI compatibility;
- debug/source mapping;
- deterministic parallel assembly;
- mmap/stream-friendly output;
- fuzz tests;
- golden tests;
- relocation tests;
- branch-range tests;
- cross-target tests;
- native self-host bootstrap;
- `AXASSEMBLER_ABI_1`;
- 40 invariants.

**AXASSEMBLER 5.0 → FROZEN.**

---

# BOOTSTRAP-775 — AXBINARY

Kiến trúc hiện đã hoàn chỉnh hơn:

```text
AXCOMPILER
     ↓
AXASSEMBLER
     ↓
AXOBJECT
     ↓
AXLINKER
     ↓
┌───────────────────────────┐
│        AXBINARY            │
│ PE64 / ELF64 / Mach-O      │
│ WASM / image validation    │
│ headers / segments / load  │
│ imports / exports / entry  │
└─────────────┬─────────────┘
              ↓
        Native Artifact
```

**BOOTSTRAP-775 — AXBINARY: Native Executable Image Model, PE64/ELF64/Mach-O/WASM Binary Construction, Headers, Segments, Imports/Exports, Entry Point, Load Layout, Binary Validation & Cross-Platform Native Image ABI 5.0**

Task kế tiếp sẽ khóa **lớp binary image cuối cùng giữa AXLINKER và file executable thực tế**, đặc biệt quan trọng cho mục tiêu Axiom tự tạo `.exe`, ELF, Mach-O, Android/iOS và WASM mà không cần toolchain bên thứ ba.