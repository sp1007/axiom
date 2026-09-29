# BOOTSTRAP-771 — AXASSEMBLER

**Title:** Native Machine Instruction Encoding, Assembly Syntax, Register Model, Relocation Emission, Inline Assembly, Object Encoding & Architecture Backend Runtime 5.0  
**Namespace:** `AXASSEMBLER`  
**Phase:** Axiom Native Toolchain / Machine Code & Assembly Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

# 1. Mục tiêu

`AXASSEMBLER` là lớp machine-level của Axiom, chịu trách nhiệm biến machine instruction representation thành binary encoding và cung cấp assembly infrastructure cho compiler.

```text
AXCOMPILER
    │
    ▼
Machine IR
    │
    ▼
AXASSEMBLER
    │
    ├── Register Model
    ├── Instruction Model
    ├── Operand Model
    ├── Encoding
    ├── Relocations
    ├── Sections
    ├── Symbols
    ├── Inline Assembly
    └── Assembly Parser/Printer
    │
    ▼
Object Artifact
    │
    ▼
AXLINKER
```

Mục tiêu quan trọng:

> **Native code generation của Axiom không cần phụ thuộc vào assembler bên ngoài.**

---

# 2. Boundary

`AXASSEMBLER` sở hữu:

- register descriptions;
- instruction descriptions;
- operand descriptions;
- instruction encoding;
- machine-byte emission;
- assembly parsing;
- assembly printing;
- relocation records;
- local symbol references;
- section fragments;
- fixups;
- inline assembly validation;
- machine-level diagnostics;
- architecture-specific encoding.

Không sở hữu:

```text
AXCOMPILER → semantic compilation
AXTOOLCHAIN → target/SDK/toolchain identity
AXBUILD → build orchestration
AXLINKER → final symbol resolution/linking
AXPACKAGE → distribution
AXSECURITY → security policy
```

---

# 3. Nguyên tắc kiến trúc

```text
Assembly text
      │
      ├── optional
      │
      ▼
Instruction IR
      │
      ▼
Encoder
      │
      ▼
Machine bytes
```

**Canonical compiler path:**

```text
Machine IR
   ↓
Instruction representation
   ↓
Encoder
   ↓
bytes
```

Không phải:

```text
Machine IR
 ↓
text assembly
 ↓
external assembler
 ↓
object
```

---

# 4. Supported initial architectures

Baseline:

```text
x86_64
AArch64
WASM32
```

Architecture interface phải cho phép mở rộng:

```text
RISC-V64
future CPU architectures
GPU instruction sets
custom accelerators
```

---

# 5. Architecture descriptor

```text
architecture {
    architecture_id
    family
    word_size
    endianness
    registers
    instructions
    features
    calling_conventions
    object_formats
}
```

---

# 6. Register model

Mỗi register có canonical ID:

```text
RegisterId
```

Không dùng string `"rax"` trong compiler hot path.

---

# 7. Register descriptor

```text
register {
    id
    name
    class
    width
    aliases
    encoding_id
    flags
}
```

---

# 8. Register classes

Ví dụ x86-64:

```text
GPR
XMM
YMM
ZMM
FLAGS
IP
SEGMENT
CONTROL
DEBUG
```

Không phải mọi register class đều accessible từ ordinary Axiom code.

---

# 9. Register aliases

Ví dụ conceptually:

```text
RAX
 ├── EAX
 ├── AX
 ├── AH
 └── AL
```

Register model phải biểu diễn alias/overlap chính xác.

---

# 10. Register overlap

Backend cần biết:

```text
write EAX
```

có ảnh hưởng tới:

```text
RAX
```

như thế nào.

Đây là thông tin machine semantics, không chỉ display metadata.

---

# 11. Register constraints

Inline assembly và register allocator có thể request:

```text
specific register
register class
register width
register pair
```

---

# 12. Instruction descriptor

```text
instruction {
    instruction_id
    mnemonic
    operand_pattern
    encoding_forms
    feature_requirements
    semantic_flags
    latency_metadata
    throughput_metadata
}
```

Latency/throughput chỉ là optimization metadata, không phải correctness semantics.

---

# 13. Operand model

Operand baseline:

```text
register
immediate
memory
symbol
label
relocation
vector
condition
```

---

# 14. Immediate

Immediate phải giữ exact bit width:

```text
imm8
imm16
imm32
imm64
```

và signedness/range constraint.

---

# 15. Memory operand

Canonical:

```text
memory_operand {
    base
    index
    scale
    displacement
    segment
    width
}
```

---

# 16. x86 addressing

Ví dụ conceptually:

```text
[base + index * scale + displacement]
```

được biểu diễn trực tiếp trong operand IR.

---

# 17. AArch64 addressing

AArch64-specific forms phải được model riêng, không ép vào x86 addressing abstraction.

---

# 18. WASM operands

WASM không có traditional register architecture.

AXASSEMBLER backend phải cho phép instruction model khác:

```text
locals
stack operands
memory indexes
control blocks
```

---

# 19. Instruction semantics

Instruction description phải phân biệt:

```text
encoding
semantic effect
register reads
register writes
memory reads
memory writes
control-flow effect
```

---

# 20. Instruction encoding

Encoder:

```text
Instruction
   +
Operands
   +
Target Features
   ↓
Validation
   ↓
Machine Bytes
```

---

# 21. Encoding validation

Trước emission:

```text
validate operands
validate register class
validate immediate range
validate feature requirement
validate addressing mode
validate encoding form
```

---

# 22. Encoding forms

Một mnemonic có thể có nhiều encoding forms.

Ví dụ conceptually:

```text
ADD r32, r/m32
ADD r/m32, r32
ADD r/m32, imm8
ADD r/m32, imm32
```

Encoder phải chọn encoding hợp lệ.

---

# 23. Encoding selection

Nếu nhiều encoding hợp lệ:

```text
shortest
canonical
performance-optimal
```

selection policy phải explicit.

---

# 24. Canonical encoding

Reproducible builds yêu cầu compiler chọn deterministic encoding khi nhiều encoding có cùng semantics.

---

# 25. Instruction prefixes

x86 encoder phải model:

```text
legacy prefixes
REX
VEX
EVEX
```

theo instruction encoding.

---

# 26. AArch64 fixed-width encoding

AArch64 instruction encoder phải validate fixed-width instruction representation.

---

# 27. WASM encoding

WASM instruction emitter phải encode:

```text
opcode
immediate
block type
memory argument
index
```

theo WASM target definition.

---

# 28. Machine instruction object

```text
machine_instruction {
    opcode
    operands[]
    flags
    source_location
    encoding_hint
}
```

---

# 29. Machine basic block

```text
machine_block {
    block_id
    instructions[]
    successors[]
    predecessors[]
}
```

---

# 30. Labels

Labels có compiler-internal identity:

```text
LabelId
```

Không dùng raw text names trong encoder.

---

# 31. Local branches

Branch tới local block:

```text
jump LabelId
```

được encoder tạo fixup.

---

# 32. Branch displacement

Encoder tính:

```text
target_address - next_instruction_address
```

theo architecture-specific rules.

---

# 33. Branch relaxation

Compiler có thể initially emit conservative branch encoding rồi relax:

```text
long jump
 ↓
short jump
```

nếu displacement phù hợp.

---

# 34. Relaxation

Relaxation phải deterministic.

Không được làm output phụ thuộc vào unordered hash iteration hoặc thread completion order.

---

# 35. Fixup

Fixup là unresolved machine-level field:

```text
fixup {
    offset
    width
    kind
    target
    addend
}
```

---

# 36. Relocation

Relocation dùng khi target address không thể resolve trong compilation unit.

```text
relocation {
    offset
    type
    symbol
    addend
}
```

---

# 37. Relocation distinction

```text
fixup
```

là internal encoder mechanism.

```text
relocation
```

là object-level record visible to linker.

---

# 38. Symbol reference

Instruction có thể reference:

```text
local symbol
global symbol
external symbol
TLS symbol
section symbol
```

---

# 39. Symbol visibility

AXASSEMBLER preserve requested:

```text
local
hidden
protected
public
weak
external
```

nếu object format hỗ trợ.

---

# 40. PC-relative references

Backend phải hỗ trợ:

```text
RIP-relative
PC-relative
page-relative
```

tùy architecture.

---

# 41. Absolute references

Absolute address relocation phải explicit.

Compiler không được vô tình tạo text-relocation khi target ABI forbids it.

---

# 42. Position-independent code

AXASSEMBLER hỗ trợ relocation forms cần cho:

```text
PIC
PIE
shared libraries
dynamic libraries
```

---

# 43. TLS

Thread-local storage references phải được encode theo target ABI.

---

# 44. Calling convention

AXASSEMBLER không định nghĩa calling convention cấp ngôn ngữ.

Nhưng phải cung cấp machine primitives để AXCOMPILER/AXTOOLCHAIN lower:

```text
argument register
return register
stack slot
callee-saved register
caller-saved register
```

---

# 45. Register metadata

Calling convention descriptor có thể query register sets:

```text
argument_regs
return_regs
caller_saved
callee_saved
reserved
scratch
```

---

# 46. Stack alignment

Encoder/backend phải support target ABI stack alignment requirements.

---

# 47. Stack probing

Nếu target ABI/OS yêu cầu stack probing, implementation thuộc backend/runtime boundary nhưng AXASSEMBLER phải encode required instructions.

---

# 48. Atomic instruction encoding

AXASSEMBLER cung cấp encoding cho target atomic instructions.

Memory-order semantics do compiler/backend xác định.

---

# 49. Fence instructions

Support:

```text
load fence
store fence
full fence
architecture-specific barriers
```

---

# 50. SIMD instructions

Backend instruction table phải model:

```text
SSE
AVX
AVX2
AVX-512
NEON
SVE
```

theo target capabilities.

Không assume all CPUs support them.

---

# 51. Feature validation

Instruction requiring unsupported CPU feature:

```text
compile error
```

hoặc compiler phải select fallback.

Không generate illegal instruction silently.

---

# 52. CPU feature sets

Target feature set:

```text
baseline
enabled
disabled
required
```

được AXTOOLCHAIN cung cấp.

---

# 53. Instruction aliases

Assembly printer có thể hiển thị aliases.

Encoder canonicalizes aliases thành canonical opcode representation.

---

# 54. Assembly parser

AXASSEMBLER có optional parser:

```text
assembly text
 ↓
tokens
 ↓
instruction
 ↓
machine instruction
```

Chủ yếu phục vụ:

- inline assembly;
- tests;
- debugging;
- developer tools.

---

# 55. Assembly syntax

Initial syntax có thể hỗ trợ:

```text
Axiom canonical assembly
Intel-like x86 syntax
AT&T-like compatibility syntax
```

nhưng canonical internal representation chỉ có **một**.

---

# 56. Assembly parser không phải compiler frontend

Assembly parser không thực hiện:

- type checking của Axiom;
- generic resolution;
- module resolution;
- language semantics.

---

# 57. Inline assembly

Nếu Axiom hỗ trợ:

```text
asm {
    ...
}
```

AXASSEMBLER validate assembly block.

---

# 58. Inline assembly operands

```text
asm {
    instruction ...
} in(x) out(y) clobber(...)
```

Exact syntax có thể được freeze ở language surface task.

---

# 59. Inline assembly effects

Compiler phải biết:

```text
register reads
register writes
memory read
memory write
flags
control flow
```

---

# 60. Memory clobber

Nếu inline assembly khai báo memory clobber:

```text
memory
```

compiler không được reorder memory operations qua boundary trái semantics.

---

# 61. Unknown effects

Inline assembly thiếu effect declaration phải bị giới hạn hoặc yêu cầu explicit unsafe mode.

Không được giả định `"no side effects"`.

---

# 62. Register clobber

Compiler phải reserve/clobber các registers được assembly block khai báo.

---

# 63. Inline assembly safety

Inline assembly mặc định thuộc unsafe boundary.

---

# 64. Privileged instructions

Các instruction như:

```text
system control
interrupt control
privileged registers
```

không được ordinary application code sử dụng nếu AXSECURITY/target privilege model không cho phép.

---

# 65. Instruction privilege metadata

Instruction descriptor có thể chứa:

```text
user
kernel
hypervisor
firmware
```

privilege class.

---

# 66. Object sections

AXASSEMBLER tạo section fragments:

```text
.text
.rodata
.data
.bss
.tls
.debug*
```

nhưng final section layout thuộc AXLINKER.

---

# 67. Section fragment

```text
section_fragment {
    section
    alignment
    bytes
    relocations[]
    symbols[]
}
```

---

# 68. Alignment

Encoder/object emitter phải preserve requested alignment.

---

# 69. Padding

Padding bytes trong executable sections phải deterministic.

---

# 70. Code alignment

Compiler có thể request:

```text
function_alignment
loop_alignment
hot_block_alignment
```

AXASSEMBLER chỉ encode/preserve request.

---

# 71. NOP generation

Backend cần architecture-specific NOP sequences cho alignment.

---

# 72. Multi-byte NOP

x86 backend phải có canonical multi-byte NOP generator.

---

# 73. Data emission

AXASSEMBLER có thể emit low-level constants:

```text
integer
float
bytes
addresses
zero-fill
alignment
```

---

# 74. String/data literals

Compiler-generated literal sections có thể được passed qua data emitter.

---

# 75. Endianness

Data encoding phải follow target endianness.

---

# 76. Floating constants

Binary representation phải exact theo target format.

---

# 77. NaN representation

Compiler must preserve requested NaN semantics where observable.

---

# 78. Object format boundary

AXASSEMBLER có thể tạo object fragment nhưng final object format implementation phải phối hợp với object emitter.

```text
AXASSEMBLER
    ↓
AXOBJECT
    ↓
AXLINKER
```

Nếu architecture hiện tại không có subsystem `AXOBJECT`, object encoding phần format-specific có thể nằm trong AXASSEMBLER cho tới khi `AXLINKER` được freeze.

---

# 79. PE/COFF

Windows target phải support machine-level data cần cho:

```text
PE64
COFF
```

---

# 80. ELF

Linux target:

```text
ELF64
```

---

# 81. Mach-O

macOS/iOS:

```text
Mach-O 64
```

---

# 82. WASM

WASM object/module emission khác native object format và phải được model như target-specific artifact.

---

# 83. Relocation abstraction

Internal relocation:

```text
RelocKind
```

độc lập object format.

Ví dụ:

```text
PC_REL
ABSOLUTE
GOT
PLT
TLS
BRANCH
PAGE_REL
```

Object emitter maps internal relocation → format-specific relocation.

---

# 84. Relocation validation

Emitter phải reject:

```text
unsupported relocation
overflow
invalid symbol
invalid addend
wrong width
wrong section
```

---

# 85. Relocation overflow

Không silently truncate relocation.

Compiler/linker phải produce explicit diagnostic.

---

# 86. Symbol binding

Symbol emission preserve binding semantics needed by linker.

---

# 87. Weak symbols

Nếu target format hỗ trợ weak symbols, emitter phải preserve them.

---

# 88. COMDAT / identical code folding metadata

Windows/COFF và các target tương tự có thể cần section/group metadata.

AXASSEMBLER phải expose generic grouping abstraction.

---

# 89. Function sections

Compiler có thể emit mỗi function vào section riêng khi build profile yêu cầu.

---

# 90. Dead stripping support

Object metadata phải cho linker biết unit boundaries để AXLINKER có thể dead-strip unused functions/data.

---

# 91. Link-time optimization metadata

AXASSEMBLER phải có khả năng attach compiler metadata/IR references tới object artifact khi LTO enabled.

---

# 92. Debug directives

Assembly printer có thể emit debug directives, nhưng canonical debug information phải là structured metadata.

---

# 93. Source mapping

Machine instruction có thể giữ:

```text
source_span
inline_stack
```

cho AXDIAGNOSTICS/debug tools.

---

# 94. Instruction-level debug mapping

Mapping:

```text
instruction offset
→ source location
```

phải deterministic.

---

# 95. Instruction scheduling

AXASSEMBLER không chịu trách nhiệm high-level scheduling.

Backend có thể reorder instructions trước khi encoder.

---

# 96. Hazard metadata

Instruction descriptor có thể cung cấp dependency information để scheduler:

```text
reads
writes
latency
resource
```

---

# 97. Microarchitecture profiles

Optional target tuning:

```text
generic-x86-64
zen-like
core-like
apple-like
arm-generic
```

Chỉ ảnh hưởng optimization/selection, không thay đổi language semantics.

---

# 98. Encoder API

Core:

```text
assembler_init()
assembler_shutdown()

architecture_open()
instruction_lookup()

instruction_validate()
instruction_encode()

register_lookup()
operand_validate()

label_create()
fixup_create()

section_begin()
section_emit()
section_align()

symbol_define()
symbol_reference()

relocation_emit()

assembly_parse()
assembly_print()

object_fragment_finalize()
```

---

# 99. Encoding result

```text
encode_result {
    status
    bytes
    fixups
    relocations
    diagnostics
}
```

---

# 100. Streaming encoder

Encoder phải hỗ trợ append trực tiếp vào output buffer.

Không bắt buộc build toàn bộ function bytes trong một giant temporary buffer.

---

# 101. Zero-allocation hot path

Normal instruction encoding không nên heap allocate.

Use:

```text
preallocated buffers
arena
small vectors
stack temporaries
```

---

# 102. Table-driven encoding

Instruction encodings nên được generated từ canonical machine description:

```text
ISA specification
 ↓
generated tables
 ↓
AXASSEMBLER
```

giảm handwritten encoder bugs.

---

# 103. Generated encoder tables

Build system có thể generate:

```text
opcode tables
operand constraints
encoding templates
feature requirements
```

thành static compiler data.

---

# 104. No runtime reflection requirement

Instruction lookup không cần reflection runtime.

Compiler sử dụng static tables.

---

# 105. Encoding template

Conceptually:

```text
encoding_template {
    opcode
    prefix_rules
    operand_encoding[]
    immediate_encoding
    displacement_encoding
    feature_mask
}
```

---

# 106. Operand matcher

Given:

```text
instruction + operands
```

matcher tìm encoding forms hợp lệ.

---

# 107. Encoding cost

Nếu nhiều encoding:

```text
cost =
    byte_size
    +
    performance_penalty
    +
    relocation_cost
```

policy-dependent.

---

# 108. Deterministic tie-break

Nếu cost bằng nhau:

```text
encoding_id
```

là deterministic tie-breaker.

---

# 109. Machine code verification

Development/debug builds có thể re-decode generated bytes:

```text
bytes
 ↓
decoder
 ↓
instruction
```

và compare với source machine instruction.

---

# 110. Encoder/decoder symmetry

Không bắt buộc mọi instruction decoder phải tồn tại trong release compiler, nhưng architecture tests phải verify encode/decode symmetry ở backend development.

---

# 111. Instruction decoder

Optional API:

```text
instruction_decode(bytes)
```

phục vụ:

- tests;
- disassembler;
- diagnostics;
- crash analysis.

---

# 112. Disassembler

AXASSEMBLER có thể cung cấp disassembly tooling.

Không phải requirement của compiler hot path.

---

# 113. Machine verifier

Verifier kiểm tra:

```text
invalid register
invalid immediate
invalid feature
invalid branch
invalid relocation
```

trước object emission.

---

# 114. Control-flow verification

Machine verifier có thể kiểm tra:

- valid block targets;
- branch labels;
- fallthrough;
- terminators.

---

# 115. Stack discipline verification

Backend development mode có thể validate expected stack adjustments.

---

# 116. ABI verification

Generated call sequences có thể được checked against AXTOOLCHAIN ABI descriptor.

---

# 117. External symbols

External symbol references được emitted without requiring resolution by AXASSEMBLER.

AXLINKER resolves them.

---

# 118. Import symbols

Platform-specific import metadata:

```text
DLL
framework
shared object
WASM import
```

được passed through object/link metadata.

---

# 119. Dynamic calls

PLT/GOT/IAT-like constructs depend on target object/link ABI.

AXASSEMBLER provides required relocation forms.

---

# 120. Position-independent branches

Architecture-specific PC-relative encoding phải được preferred khi ABI yêu cầu PIC/PIE.

---

# 121. Literal pools

Architectures như AArch64 có thể cần literal pools.

AXASSEMBLER phải support:

```text
literal_pool
literal_reference
pool_placement
```

---

# 122. Literal pool range

Backend phải verify literal reference displacement.

---

# 123. Constant islands

Nếu target cần constant islands, assembler backend phải support placement constraints.

---

# 124. Branch range

Backend must detect branch displacement overflow and either:

```text
relax
```

hoặc request compiler/backend to generate long branch sequence.

---

# 125. Veneers / trampolines

Nếu target ABI cần branch veneer/trampoline:

```text
AXASSEMBLER
```

có thể expose generation primitive; final placement có thể thuộc AXLINKER.

---

# 126. Large model

Absolute/large-address code models phải be explicit toolchain configuration.

---

# 127. Code model

Baseline:

```text
small
medium
large
position-independent
```

target-dependent.

---

# 128. TLS models

Native TLS reference models:

```text
local-exec
initial-exec
local-dynamic
general-dynamic
```

nếu target ABI hỗ trợ.

---

# 129. Section permissions

Object section metadata có thể indicate:

```text
read
write
execute
```

AXSECURITY/OS policy remains final authority.

---

# 130. W^X

Compiler/object emission phải hỗ trợ layouts compatible with W^X policies.

Không emit writable+executable code section trừ explicit platform requirement.

---

# 131. Executable stack metadata

Target object can request non-executable stack where format supports it.

---

# 132. Inline assembly and optimization barriers

Compiler must model assembly effects precisely enough for optimizer.

---

# 133. `volatile asm`

Explicit volatile assembly cannot be removed as dead code.

---

# 134. Nonvolatile asm

Nonvolatile asm can be optimized only if its declared effects permit.

---

# 135. Assembly labels

Local labels must avoid collision with compiler-generated symbols.

---

# 136. Symbol naming

Internal generated symbols use deterministic mangling:

```text
_axiom_<kind>_<stable-id>
```

Exact ABI mangling belongs language ABI specification.

---

# 137. Name mangling

Mangled name encodes:

```text
module
symbol
generic parameters
ABI
calling convention
```

where required.

---

# 138. Mangling stability

Public ABI symbols require stable mangling across compiler versions unless language ABI version changes.

---

# 139. Private symbols

Private compiler-generated names may change provided object semantics remain equivalent.

---

# 140. Generic symbols

Monomorphized generic symbol identity must be derived from canonical type identity, not source textual ordering.

---

# 141. Hash-based symbol identity

Long generic identities can use canonical hashes internally while retaining collision verification.

---

# 142. Collision handling

Hash collision must never silently merge symbols.

---

# 143. Object fragment API

```text
object_fragment {
    sections[]
    symbols[]
    relocations[]
    debug_records[]
    metadata[]
}
```

---

# 144. Atomic finalization

Object fragment should transition:

```text
BUILDING
 ↓
VALIDATED
 ↓
FINALIZED
```

After `FINALIZED`, immutable.

---

# 145. Error handling

Baseline errors:

```text
ASM_INVALID_INSTRUCTION
ASM_INVALID_OPERAND
ASM_REGISTER_ERROR
ASM_IMMEDIATE_OVERFLOW
ASM_FEATURE_UNAVAILABLE
ASM_ENCODING_ERROR
ASM_BRANCH_RANGE
ASM_RELOCATION_ERROR
ASM_SYMBOL_ERROR
ASM_SECTION_ERROR
ASM_ABI_ERROR
ASM_OBJECT_ERROR
ASM_INLINE_ASM_ERROR
ASM_INTERNAL_ERROR
```

---

# 146. Diagnostics

Machine-level diagnostic:

```text
diagnostic {
    code
    severity
    instruction
    operand
    source_span
    explanation
    suggestion
}
```

---

# 147. Example diagnostic

Conceptually:

```text
error ASM_FEATURE_UNAVAILABLE:
    instruction requires AVX2
    target baseline does not enable AVX2
```

---

# 148. Security

AXASSEMBLER must not grant privilege simply because an instruction can be encoded.

Ví dụ:

```text
CLI
HLT
MOV control-register
```

có thể encode được nhưng execution authority thuộc OS/security model.

---

# 149. Kernel/firmware mode

AXTOOLCHAIN target profile có thể permit privileged instruction sets cho:

```text
kernel
hypervisor
firmware
```

---

# 150. User-mode compiler

Ordinary user application target must reject explicitly privileged constructs where compile-time policy requires.

---

# 151. Deterministic output

Given identical:

```text
machine IR
target
ABI
features
assembler version
options
```

encoder phải produce identical bytes.

---

# 152. Parallel encoding

Independent functions có thể encode parallel.

Mỗi function có isolated encoder state.

---

# 153. Global state prohibition

No mutable global encoder state required for correctness.

---

# 154. Thread safety

Read-only architecture tables có thể shared giữa compiler workers.

---

# 155. Architecture table memory

Instruction/register tables nên là immutable compact data.

---

# 156. Generated architecture database

Canonical source:

```text
isa/
    x86_64/
    aarch64/
    wasm32/
```

có thể generate compiler tables.

---

# 157. ISA specification version

Architecture table có:

```text
isa_version
```

để reproducibility.

---

# 158. Backend version

```text
assembler_backend_version
```

tham gia compiler/toolchain fingerprint.

---

# 159. Cache integration

AXBUILD compiler cache phải include:

```text
AXASSEMBLER backend version
ISA version
target features
```

---

# 160. Object cache

Encoded object cache key phải include machine backend identity.

---

# 161. Reproducible padding

Padding/alignment bytes canonicalized.

---

# 162. Reproducible symbols

Generated local symbol IDs deterministic.

---

# 163. Reproducible relocations

Relocation ordering canonical:

```text
section
offset
symbol
type
addend
```

---

# 164. Reproducible sections

Section fragment ordering canonical.

---

# 165. Debug stripping

Assembler/object emitter supports:

```text
none
minimal
full
```

debug metadata modes.

---

# 166. Assembly source output

Optional:

```text
machine IR → assembly text
```

must preserve enough semantics for human inspection.

---

# 167. Assembly round-trip

Development test:

```text
machine instruction
 ↓ print
assembly
 ↓ parse
machine instruction
```

should canonicalize to equivalent instruction.

---

# 168. Canonical assembly

Printer should have one canonical Axiom assembly syntax.

---

# 169. Human-readable assembly

Printer may optionally output Intel/AT&T-style syntax for ecosystem familiarity.

---

# 170. Object inspection

Assembler tooling should expose:

```text
section list
symbol list
relocation list
instruction dump
```

---

# 171. Machine code size

Encoder should expose:

```text
encoded_size
```

for compiler optimization.

---

# 172. Code-size optimization

Backend can select shorter instruction encodings under `-Os/-Oz`.

---

# 173. Performance optimization

Backend can select instruction forms based on CPU target profile.

---

# 174. Register zeroing

Backend may use architecture-specific zero idioms when semantically equivalent.

---

# 175. Instruction fusion

Machine scheduling may prefer instruction sequences recognized by target CPU fusion rules.

This is optimization metadata, not language semantics.

---

# 176. Constant materialization

Backend selects optimal immediate construction:

```text
small immediate
literal pool
MOVZ/MOVK sequence
constant load
```

depending on architecture.

---

# 177. Address materialization

Global/static addresses may use:

```text
PC-relative
GOT
absolute
page-relative
```

according to code model.

---

# 178. Function call encoding

Calls may be:

```text
direct
indirect
PLT/IAT-like
tail call
```

depending on ABI and relocation model.

---

# 179. Return encoding

Backend emits ABI-compatible return sequence.

---

# 180. Prologue/epilogue primitives

AXASSEMBLER provides instruction-level primitives; AXCOMPILER/backend determines actual prologue/epilogue.

---

# 181. Frame pointer

Compiler option may:

```text
omit-frame-pointer
preserve-frame-pointer
```

according to debug/performance profile.

---

# 182. Stack maps

For diagnostics/async/runtime features, backend can emit stack maps:

```text
instruction address
live value locations
```

---

# 183. GC stack maps

AXASSEMBLER itself must not assume GC.

If an external runtime requires stack maps, they are optional metadata.

---

# 184. Exception unwind metadata

Backend can emit unwind metadata required by:

```text
Windows
DWARF
Mach-O
```

target conventions.

---

# 185. Unwind instruction encoding

Only machine encoding is owned here; semantic unwind generation belongs compiler/target ABI layer.

---

# 186. Crash diagnostics integration

AXDIAGNOSTICS consumes:

```text
instruction addresses
unwind metadata
source mappings
```

---

# 187. Faulting instruction metadata

Compiler may associate each emitted instruction range with source span/build ID.

---

# 188. Compiler self-hosting

AXASSEMBLER itself must eventually be implementable in Axiom.

Bootstrap path:

```text
Stage0 compiler
    ↓
AXASSEMBLER implementation
    ↓
Axiom assembler
```

---

# 189. Stage0 dependency

Stage0 may use a minimal existing assembler/object writer only as bootstrap scaffolding if required by implementation plan.

This is **temporary bootstrap infrastructure**, not a permanent Axiom dependency.

---

# 190. Stage1

Stage1 compiler contains:

```text
Axiom frontend
+
minimal AXASSEMBLER
```

---

# 191. Stage2

Stage2 compiles full:

```text
AXCOMPILER
AXASSEMBLER
AXLINKER
```

using Axiom itself.

---

# 192. Bootstrap verification

```text
Stage1
  ↓ compile compiler source
Stage2

Stage2
  ↓ compile same compiler source
Stage3
```

Then compare canonical artifacts.

---

# 193. Compiler/assembler split

Important:

```text
AXCOMPILER
```

decides **what instructions should exist**.

```text
AXASSEMBLER
```

decides **how those instructions become bytes**.

---

# 194. Linker split

```text
AXASSEMBLER
    ↓
bytes + relocations

AXLINKER
    ↓
global address resolution
    ↓
final binary
```

---

# 195. Why this split matters

Nó cho phép:

- compiler backend development độc lập;
- assembler testing độc lập;
- linker testing độc lập;
- direct machine-code generation;
- cross-target support;
- deterministic object generation.

---

# 196. Native API

Canonical ABI:

```text
AXASSEMBLER_ABI_1
```

Core types:

```text
AssemblerContext
Architecture
Register
Instruction
Operand
Section
Symbol
Fixup
Relocation
ObjectFragment
Diagnostic
```

---

# 197. Native initialization

```text
assembler_init()
assembler_shutdown()
```

---

# 198. Architecture API

```text
assembler_architecture_list()
assembler_architecture_open()
assembler_architecture_info()
assembler_architecture_features()
```

---

# 199. Register API

```text
register_lookup()
register_info()
register_aliases()
register_overlap()
```

---

# 200. Instruction API

```text
instruction_lookup()
instruction_info()
instruction_forms()
instruction_validate()
instruction_encode()
```

---

# 201. Operand API

```text
operand_register()
operand_immediate()
operand_memory()
operand_symbol()
operand_label()
operand_validate()
```

---

# 202. Label API

```text
label_create()
label_bind()
label_reference()
```

---

# 203. Section API

```text
section_create()
section_emit_bytes()
section_emit_instruction()
section_align()
section_finalize()
```

---

# 204. Symbol API

```text
symbol_define()
symbol_reference()
symbol_set_visibility()
symbol_set_binding()
```

---

# 205. Relocation API

```text
relocation_create()
relocation_emit()
relocation_validate()
```

---

# 206. Assembly API

```text
assembly_parse()
assembly_print()
assembly_disassemble()
```

---

# 207. Verification API

```text
assembler_verify_instruction()
assembler_verify_fragment()
assembler_verify_object()
```

---

# 208. Statistics API

```text
assembler_stats()
assembler_encoding_stats()
assembler_cache_stats()
```

---

# 209. Cache

Instruction encoding tables can be cached but are normally immutable static tables.

Repeated identical encoding operations may use specialized backend fast paths rather than generic cache lookup.

---

# 210. No mandatory heap allocation

Simple:

```text
encode(add rax, rbx)
```

should be possible with stack/local structures only.

---

# 211. Compiler integration example

Conceptually:

```text
machine_instruction {
    ADD,
    rax,
    rbx
}
```

→

```text
instruction_validate()
instruction_encode()
```

→

```text
machine bytes
```

---

# 212. Error propagation

Encoder errors must preserve:

```text
instruction
operand index
source location
architecture
feature set
```

---

# 213. Architecture portability

No x86-specific data types in generic assembler API.

---

# 214. Backend capability query

Compiler can ask:

```text
supports_instruction(...)
supports_register_class(...)
supports_relocation(...)
supports_inline_asm(...)
```

---

# 215. Target fallback

If requested instruction unavailable:

```text
backend fallback
```

may select alternative sequence.

AXASSEMBLER itself does not invent semantic fallback unless explicitly registered.

---

# 216. Semantic expansion

Example:

```text
high-level intrinsic
```

may lower to multiple instructions before AXASSEMBLER.

Assembler should not secretly expand arbitrary instructions except defined pseudo-instructions.

---

# 217. Pseudo-instructions

Optional:

```text
pseudo instruction
 ↓
canonical machine sequence
```

Useful for assembly source compatibility.

---

# 218. Pseudo-instruction determinism

Expansion must be deterministic and architecture-versioned.

---

# 219. Architecture-specific pseudo-ops

Examples may include:

```text
load-address
load-immediate
branch-long
```

when useful.

---

# 220. No semantic ambiguity

Pseudo-op must have exactly documented expansion semantics.

---

# 221. Machine verifier

Before finalizing object fragment:

```text
verify instructions
verify branches
verify relocations
verify symbols
verify section alignment
```

---

# 222. Object fragment validity

Invalid fragment cannot transition to `FINALIZED`.

---

# 223. Immutable finalized artifact

Once finalized:

```text
ObjectFragment
```

becomes immutable and safe for AXBUILD cache.

---

# 224. Concurrency

Different object fragments can encode simultaneously.

Architecture tables shared read-only.

---

# 225. Deterministic parallelism

Parallel encoding cannot affect:

- instruction bytes;
- symbol IDs;
- relocation ordering;
- section ordering.

---

# 226. Performance targets

AXASSEMBLER must aim for:

```text
O(number of emitted instructions)
```

normal encoding complexity.

---

# 227. Encoder memory

Memory approximately:

```text
machine bytes
+
relocation records
+
symbol metadata
```

not proportional to entire project source tree.

---

# 228. Hot-path design

Common instruction forms should use specialized generated encoders instead of generic dynamic dispatch.

---

# 229. Backend code generation

Architecture-specific generated code may compile instruction encoders into direct branch tables.

---

# 230. Generated machine descriptions

Preferred architecture:

```text
ISA description
     ↓
generator
     ↓
register table
instruction table
encoding table
decoder table
feature table
     ↓
AXASSEMBLER
```

---

# 231. ISA source validation

Generator must validate:

- duplicate opcode;
- overlapping encodings;
- invalid operand constraints;
- missing feature declarations;
- inconsistent register aliases.

---

# 232. Backend test generation

Every instruction description should generate baseline tests:

```text
valid operands
invalid operands
encoding bytes
feature requirements
decode roundtrip
```

---

# 233. Known-answer tests

Architecture test vectors:

```text
instruction
operands
expected bytes
```

must be maintained.

---

# 234. Differential testing

Where trusted external assemblers/disassemblers are available during development, Axiom may compare results.

This is **test infrastructure**, not runtime/compiler dependency.

---

# 235. Fuzz testing

Generate random valid machine instructions and test:

```text
encode
decode
canonicalize
```

---

# 236. Invalid-input fuzzing

Test:

- malformed assembly;
- invalid register combinations;
- immediate overflow;
- invalid relocation;
- branch overflow.

---

# 237. Security fuzzing

Assembly parser must resist:

- huge token sequences;
- pathological nesting;
- oversized literals;
- malicious symbol names;
- malformed relocation records.

---

# 238. Resource limits

Parser/encoder APIs can receive:

```text
max_input_size
max_instruction_count
max_symbol_count
max_relocation_count
```

---

# 239. Crash safety

Invalid assembly must return diagnostics rather than crash.

---

# 240. Formal invariants

```text
ASM-INV-01
AXASSEMBLER phải encode instruction theo target ISA chính xác.

ASM-INV-02
Invalid UTF-8 assembly source phải được reject tại parser boundary.

ASM-INV-03
Instruction operands phải được validate trước encoding.

ASM-INV-04
Register IDs phải canonical và deterministic.

ASM-INV-05
Register alias/overlap semantics phải chính xác.

ASM-INV-06
Immediate values không được silently truncate.

ASM-INV-07
Memory operands phải tuân thủ target addressing constraints.

ASM-INV-08
Instruction yêu cầu CPU feature không được encode nếu feature bị disabled.

ASM-INV-09
Canonical encoding phải deterministic.

ASM-INV-10
Multiple valid encodings phải có deterministic selection.

ASM-INV-11
Machine instruction encoding không được phụ thuộc assembly text trong canonical compiler path.

ASM-INV-12
Local branch targets phải được resolve hoặc tạo fixup hợp lệ.

ASM-INV-13
Branch displacement overflow không được silently wrap.

ASM-INV-14
Internal fixup và object relocation phải được phân biệt.

ASM-INV-15
Relocation width/type phải phù hợp target ABI.

ASM-INV-16
Relocation overflow phải tạo diagnostic.

ASM-INV-17
Undefined symbols không được silently resolve.

ASM-INV-18
Generated symbol identity phải deterministic.

ASM-INV-19
Relocation ordering phải deterministic.

ASM-INV-20
Section fragment ordering phải deterministic.

ASM-INV-21
Object fragment đã finalized phải immutable.

ASM-INV-22
Instruction bytes phải deterministic với cùng target inputs.

ASM-INV-23
Parallel encoding không được thay đổi output.

ASM-INV-24
Inline assembly phải khai báo hoặc chịu semantics effects tương ứng.

ASM-INV-25
Unknown inline-assembly effects không được giả định là side-effect-free.

ASM-INV-26
Privileged instruction không tự động được cấp execution authority.

ASM-INV-27
PIC/PIE code phải sử dụng relocation model tương ứng.

ASM-INV-28
TLS references phải tuân thủ target TLS ABI.

ASM-INV-29
Instruction alignment/padding phải deterministic.

ASM-INV-30
Machine feature metadata phải được preserve trong compilation fingerprint.

ASM-INV-31
Architecture backend không được phụ thuộc architecture-specific assumptions trong generic API.

ASM-INV-32
Object emission phải preserve required symbol visibility/binding.

ASM-INV-33
Machine verifier phải reject structurally invalid fragments.

ASM-INV-34
Assembly parser không được thay đổi Axiom semantic model.

ASM-INV-35
Assembly printer/parser canonical round-trip phải preserve instruction semantics.

ASM-INV-36
Assembler cache không được bỏ qua ISA/backend version.

ASM-INV-37
Compiler-generated debug/source mappings phải preserve instruction association.

ASM-INV-38
External assembler chỉ là optional interoperability/bootstrap component.

ASM-INV-39
AXASSEMBLER không được trở thành permanent third-party compiler/assembler dependency của Axiom.

ASM-INV-40
AXASSEMBLER chịu trách nhiệm machine instruction representation và encoding; global symbol resolution/final executable linking thuộc AXLINKER.
```

---

# 241. Definition of Done

`AXASSEMBLER 5.0` được freeze khi có architectural support cho:

- register model;
- register aliases;
- register overlap;
- register classes;
- instruction descriptions;
- operand model;
- immediate encoding;
- memory operands;
- x86-64 addressing;
- AArch64 addressing;
- WASM instruction model;
- instruction validation;
- feature validation;
- direct machine encoding;
- canonical encoding;
- branch encoding;
- branch relaxation;
- labels;
- fixups;
- relocations;
- symbols;
- visibility;
- PIC/PIE;
- TLS;
- SIMD;
- atomics;
- fences;
- instruction scheduling metadata;
- CPU tuning metadata;
- literal pools;
- constant islands;
- veneers;
- code models;
- section fragments;
- alignment;
- padding;
- data emission;
- symbol mangling interface;
- debug mapping;
- unwind metadata interface;
- inline assembly;
- assembly parser;
- assembly printer;
- disassembler interface;
- machine verifier;
- PE/COFF support;
- ELF support;
- Mach-O support;
- WASM support;
- deterministic encoding;
- parallel encoding;
- cache integration;
- fuzz testing;
- bootstrap/self-hosting path;
- `AXASSEMBLER_ABI_1`;
- 40 invariants.

**AXASSEMBLER 5.0 → FROZEN.**

---

# BOOTSTRAP-772 — AXLINKER

**Native Static/Dynamic Linker, Symbol Resolution, Relocation, Section Layout, Library Linking, Executable Construction, PE64/ELF/Mach-O/WASM Final Artifact & Native Binary Runtime 5.0**

Pipeline tiếp theo:

```text
                AXCOMPILER
                    │
                    ▼
               AXASSEMBLER
                    │
                    ▼
              Object Files
             /    │     \
            /     │      \
           ▼      ▼       ▼
       Static   Dynamic   Runtime
       Library  Library   Objects
           \      │       /
            \     │      /
             ▼    ▼     ▼
                AXLINKER
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
        PE64       ELF      Mach-O
                              │
                            WASM
```

Đây là subsystem cuối cùng biến các object/library rời rạc thành **native artifact hoàn chỉnh**. Nó sẽ đặc biệt quan trọng với mục tiêu Axiom đã đặt ra từ đầu: **tự tạo `.exe`, ELF, Mach-O, static library, dynamic library và liên kết chúng mà không cần phụ thuộc permanent vào linker/compiler bên ngoài.**