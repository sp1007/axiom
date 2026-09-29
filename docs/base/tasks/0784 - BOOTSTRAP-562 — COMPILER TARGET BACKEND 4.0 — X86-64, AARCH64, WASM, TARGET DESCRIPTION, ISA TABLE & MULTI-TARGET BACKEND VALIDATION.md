# BOOTSTRAP-562 — COMPILER TARGET BACKEND 4.0 — X86-64, AARCH64, WASM, TARGET DESCRIPTION, ISA TABLE & MULTI-TARGET BACKEND VALIDATION

**Trạng thái: COMPLETED / LOCKED**

`562` khóa kiến trúc **Target Backend** của Axiom: cách mô tả ISA, register file, instruction, encoding/decoding, CPU features, target ABI và target-specific lowering mà không làm compiler core phụ thuộc cứng vào từng kiến trúc.

Mục tiêu quan trọng:

> **Thêm một ISA mới phải chủ yếu là thêm Target Description + Backend Policy, không phải sửa semantic compiler, MIR, optimizer, linker hay toàn bộ codegen.**

---

# 562.1. Backend architecture

```text id="u7k3m9"
                    Axiom Compiler
                         │
                         ▼
                  TargetSpec Resolver
                         │
                         ▼
                  TargetDescription
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       ISA Model      ABI Model      OS Model
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                  Target Backend
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
 Instruction         Register          Feature
 Selection           Allocation        Policy
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
                     Scheduler
                         │
                         ▼
                    Frame Lowering
                         │
                         ▼
                 Branch Relaxation
                         │
                         ▼
                    Encoder
                         │
                         ▼
                    Object/WASM
```

---

# 562.2. TargetDescription

Target không chỉ là ISA.

```text id="m5q8v2"
TargetDescription {
    target_id
    architecture
    subarchitecture
    os
    environment
    abi
    object_format
    pointer_width
    endianness
    features
    cpu_model
    tuning_model
    register_file
    instruction_set
    lowering_policy
}
```

---

# 562.3. Target identity

Target identity phải canonical.

Ví dụ:

```text id="x8n3q7"
x86_64-pc-windows-msvc
x86_64-unknown-linux-gnu
aarch64-apple-darwin
aarch64-apple-ios
wasm32-unknown-wasi
```

Axiom không được dùng chuỗi target tùy ý làm identity nội bộ.

---

# 562.4. Canonical Target ID

Compiler canonicalizes:

```text
user target string
        ↓
TargetTriple
        ↓
TargetSpec
        ↓
TargetFingerprint
```

---

# 562.5. TargetFingerprint

Bao gồm tối thiểu:

```text id="q4m9v1"
architecture
ABI
OS
object format
pointer width
endianness
CPU baseline
enabled features
disabled features
tuning model
```

---

# 562.6. ISA Model

ISA model mô tả:

```text id="k7x2m5"
Instruction
Register
RegisterClass
RegisterAlias
Operand
Encoding
Decoding
Feature
Constraint
```

---

# 562.7. ISA description không phải source compiler

ISA description là dữ liệu có cấu trúc.

Ví dụ concept:

```text id="v3n8q1"
instruction ADD {
    operands: GPR, GPR, GPR
    effects: arithmetic
    encoding: ...
    features: base
}
```

---

# 562.8. Declarative backend

Axiom ưu tiên declarative definitions:

```text id="p6m2x8"
ISA Description
       ↓
Generated:
 ├─ opcode tables
 ├─ encoder tables
 ├─ decoder tables
 ├─ operand validators
 ├─ register metadata
 └─ feature predicates
```

---

# 562.9. Generated code

Compiler build có thể generate source code từ ISA description.

Generated code phải deterministic.

---

# 562.10. Không yêu cầu runtime generator

ISA tables phải được compile thành compiler binary.

Không được yêu cầu runtime parse ISA description để compile chương trình thông thường.

---

# 562.11. Register description

```text id="n8q3v5"
Register {
    id
    name
    width
    class
    aliases[]
    encoding
    units[]
    flags
}
```

---

# 562.12. Register units

Dùng để model overlap.

Ví dụ:

```text id="c5m7x2"
RAX
 ├── EAX
 ├── AX
 ├── AL
 └── AH
```

---

# 562.13. Register class

Mỗi target định nghĩa:

```text id="q2v8m4"
GPR
FP
Vector
Mask
Predicate
Special
```

---

# 562.14. Reserved registers

Backend phải có policy cho:

```text id="x7k3n9"
SP
FP
TLS
platform register
scratch register
```

---

# 562.15. Allocatable registers

Mỗi register có trạng thái:

```text id="m4q8v1"
Allocatable
Reserved
Fixed
Conditional
```

---

# 562.16. Register aliasing

Allocator phải sử dụng ISA metadata, không hard-code alias logic trong allocator generic.

---

# 562.17. Instruction definition

```text id="v9m2k6"
InstructionDef {
    opcode
    mnemonic
    operands
    implicit_uses
    implicit_defs
    constraints
    effects
    encoding
    features
    scheduling_class
}
```

---

# 562.18. Instruction effects

Ví dụ:

```text id="p3x7q2"
ReadRegister
WriteRegister
ReadMemory
WriteMemory
ReadFlags
WriteFlags
Call
Return
Branch
Trap
Atomic
Barrier
```

---

# 562.19. Operand kinds

```text id="n6m8v3"
Register
Immediate
Memory
Label
Symbol
Predicate
VectorConstant
```

---

# 562.20. Operand constraint

Ví dụ:

```text id="x4q9m1"
GPR64
Immediate8
Memory32
SpecificRegister(RAX)
```

---

# 562.21. Operand predicates

ISA backend có thể khai báo:

```text id="k8v2m5"
fits_signed(bits)
fits_unsigned(bits)
is_register_class(...)
is_aligned(...)
has_feature(...)
```

---

# 562.22. Encoding model

Encoding phải là dữ liệu có cấu trúc:

```text id="m7q3x9"
Encoding {
    opcode_bits
    prefix
    operand_fields
    immediate_fields
    displacement_fields
    constraints
}
```

---

# 562.23. Decoder

Decoder sử dụng cùng ISA definition để tạo:

```text id="v5n8q2"
bytes
 ↓
Instruction
 ↓
Operands
```

---

# 562.24. Encoder/decoder consistency

Encoder và decoder không được duy trì hai bảng semantics độc lập.

---

# 562.25. Canonical instruction representation

Instruction sau decode phải canonical để dễ so sánh.

---

# 562.26. Multiple encodings

Một operation có thể có nhiều encoding.

Ví dụ:

```text id="q3m7x8"
short
legacy
VEX
EVEX
```

Backend chọn theo legality + cost.

---

# 562.27. Encoding preference

Cost model có thể ưu tiên:

```text id="x8v2n4"
smaller
faster
feature-compatible
```

---

# 562.28. Semantic opcode

Các encoding khác nhau của cùng operation phải map tới semantic opcode tương ứng.

---

# 562.29. Instruction feature requirement

Ví dụ:

```text id="m5q9k1"
AVX instruction
→ requires AVX
```

Compiler không được emit nếu feature unavailable.

---

# 562.30. Feature graph

Feature được mô hình hóa như graph:

```text id="n4x7v2"
Base
 ├── SSE
 │    └── AVX
 │         └── AVX2
 └── ...
```

Không giả định mọi ISA có hierarchy giống nhau.

---

# 562.31. Feature implication

```text id="q8m3x6"
Feature A implies B
```

Compiler tự suy ra B khi A bật.

---

# 562.32. Feature conflict

```text id="v2k7m9"
Feature A conflicts B
```

→ diagnostic.

---

# 562.33. Explicit disable

Nếu user disable feature implied bởi feature khác:

Compiler phải báo conflict hoặc áp dụng policy deterministic.

Không silently ignore.

---

# 562.34. Feature profiles

Target có thể định nghĩa profile:

```text id="x5n8q3"
baseline
native
portable
server
mobile
embedded
```

---

# 562.35. `cpu`

Axiom target configuration có:

```text id="m6q2v8"
cpu_model
```

CPU model quyết định legal features + tuning.

---

# 562.36. `features`

User có thể override feature:

```text id="p9x3m5"
+feature
-feature
```

---

# 562.37. CPU model ≠ tuning only

CPU model có thể ảnh hưởng cả legality nếu target policy cho phép, nhưng phải thể hiện rõ trong TargetFingerprint.

---

# 562.38. Tuning

Tuning chỉ thay đổi:

- instruction cost;
- scheduling;
- register preference;
- vectorization policy;
- branch heuristics.

Không thay đổi semantics.

---

# 562.39. Baseline portability

Compiler phải support target baseline riêng biệt với native CPU optimization.

---

# 562.40. x86-64 backend

Target family:

```text id="k4m8q2"
x86-64
```

phải hỗ trợ instruction encoding variable-length.

---

# 562.41. x86-64 register model

Tối thiểu:

```text id="v7n3x5"
GPR
XMM
YMM
ZMM
FLAGS
```

với aliases phù hợp.

---

# 562.42. x86-64 GPR

Backend phải model:

```text id="q2m9v6"
RAX RBX RCX RDX
RSI RDI RBP RSP
R8-R15
```

và subregister relationships.

---

# 562.43. x86-64 FLAGS

FLAGS phải là implicit machine state.

Instructions như:

```text id="x8k3m1"
ADD
SUB
CMP
TEST
```

phải khai báo flags effects.

---

# 562.44. x86 addressing

Backend phải model:

```text id="n5q7v2"
base
index
scale
displacement
```

---

# 562.45. x86 scale

Scale hợp lệ phải được ISA definition kiểm soát.

---

# 562.46. x86 prefixes

Encoder phải hỗ trợ đúng prefix semantics.

---

# 562.47. REX

REX encoding phải được generated/validated từ operand requirements.

---

# 562.48. VEX

VEX instructions phải require appropriate feature.

---

# 562.49. EVEX

EVEX phải model:

- extended registers;
- masking;
- broadcast;
- vector length;
- rounding/SAE khi applicable.

---

# 562.50. x86 instruction aliases

Mnemonic aliases không được tạo semantic opcode mới nếu semantics giống nhau.

---

# 562.51. x86 immediate encoding

Compiler phải chọn immediate width hợp lệ.

---

# 562.52. x86 branch

Backend phải support:

```text id="m3x8q7"
short
near
indirect
conditional
```

---

# 562.53. x86 branch relaxation

Phải integrate `561` relaxation.

---

# 562.54. x86 atomic

Backend phải map Axiom atomic semantics tới instruction sequences chính xác.

---

# 562.55. x86 SIMD

Backend phải expose vector widths theo feature.

---

# 562.56. x86 floating-point

Phải support modern SSE/AVX floating-point model; legacy x87 chỉ là compatibility target nếu cần.

---

# 562.57. x86 TLS

TLS models phải integrate với target OS/ABI.

---

# 562.58. x86-64 object formats

Có thể kết hợp:

```text id="q7v2m4"
ELF
PE/COFF
Mach-O
```

với cùng ISA backend nhưng object backend riêng.

---

# 562.59. AArch64 backend

AArch64 có fixed-width 32-bit instructions.

---

# 562.60. AArch64 registers

```text id="x3m8q5"
X0-X30
SP
PC
NZCV
```

và W-register views.

---

# 562.61. X/W aliases

```text id="v6q2n9"
X0
└── W0
```

phải được model bằng register units.

---

# 562.62. AArch64 zero register

`XZR/WZR` phải được model như special architectural register semantics, không phải ordinary storage register.

---

# 562.63. SP distinction

`SP` không được coi hoàn toàn giống `XZR`.

Operand constraints phải phân biệt context.

---

# 562.64. AArch64 addressing

Hỗ trợ các dạng:

```text id="m5k9x3"
base + offset
base + register
pre-index
post-index
scaled
```

khi ISA cho phép.

---

# 562.65. AArch64 immediate

Instruction-specific immediate constraints phải được declaratively mô tả.

---

# 562.66. AArch64 conditional branch

Backend phải model condition codes từ NZCV.

---

# 562.67. AArch64 compare

Compare instructions có thể implicit-write NZCV.

---

# 562.68. AArch64 literal pool

Literal references phải được range-checked.

---

# 562.69. AArch64 veneer

Long branch/call phải có veneer/thunk mechanism khi cần.

---

# 562.70. AArch64 SIMD/FP

Register class:

```text id="q8m4v2"
V0-V31
```

phải support scalar/vector views theo ISA.

---

# 562.71. AArch64 crypto

Crypto instructions chỉ được emit khi feature enabled.

---

# 562.72. SVE/SVE2

Nếu support, SVE phải có model khác với fixed-width NEON.

Không được giả định mọi vector có kích thước compile-time cố định.

---

# 562.73. SVE vector length

Backend phải model vector-length-agnostic semantics.

---

# 562.74. AArch64 atomics

Atomic instruction selection phải respect memory order.

---

# 562.75. AArch64 pointer authentication

PAC-related instructions chỉ được emit khi security/target policy yêu cầu và feature tồn tại.

---

# 562.76. Apple AArch64

Apple-specific ABI/platform rules nằm ở Target/ABI layer, không copy vào generic AArch64 ISA.

---

# 562.77. WASM backend

WASM không phải register machine.

Do đó:

```text id="n3q7m8"
WASM
```

không bắt buộc chạy qua CPU register allocation.

---

# 562.78. WASM Machine IR adapter

`561` được mở rộng bằng backend capability:

```text id="x8m2v5"
RegisterMachineBackend
StackMachineBackend
```

---

# 562.79. WASM stack machine

```text id="q5n9k3"
local.get
local.set
i32.add
i64.mul
br
call
return
```

---

# 562.80. WASM locals

SSA/MIR values được map tới WASM locals hoặc stack operations.

---

# 562.81. WASM structured control flow

CFG arbitrary phải lower thành structured WASM control flow.

---

# 562.82. WASM block

Backend phải generate:

```text id="m7x4q2"
block
loop
if
else
end
br
br_if
```

phù hợp CFG.

---

# 562.83. Irreducible CFG

Compiler phải có strategy:

```text id="v2k8m5"
structured lowering
or
state-machine lowering
```

---

# 562.84. WASM memory

Axiom memory model phải map tới WASM linear memory với explicit bounds semantics.

---

# 562.85. WASM memory64

Nếu target bật memory64, pointer/index width phải phản ánh TargetSpec.

---

# 562.86. WASM tables

Function references/indirect calls phải map tới WASM table semantics.

---

# 562.87. WASM reference types

Reference values phải được model riêng với integers.

---

# 562.88. WASM SIMD

SIMD instructions được expose khi feature bật.

---

# 562.89. WASM threads

Atomic instructions và shared memory chỉ được emit khi threads feature target cho phép.

---

# 562.90. WASM bulk memory

Bulk memory instructions là target feature.

---

# 562.91. WASM exceptions

Nếu target profile hỗ trợ exception proposal, backend có thể sử dụng; nếu không phải lower sang Result/panic strategy phù hợp.

---

# 562.92. WASM ABI

WASM ABI không được nhầm với native SysV/Win64/AAPCS64.

---

# 562.93. WASI

WASI là platform/runtime contract, không phải ISA.

---

# 562.94. WASM imports

Generated module phải khai báo imports explicit.

---

# 562.95. No hidden WASM host dependency

Compiler không tự thêm arbitrary host functions.

---

# 562.96. WASM exports

Public Axiom functions có thể map thành WASM exports theo module policy.

---

# 562.97. WASM component model

Nếu được hỗ trợ, component model nằm ở higher-level ABI/tooling layer, không thay đổi WASM core instruction semantics.

---

# 562.98. ISA vs ABI separation

```text id="k6m3x8"
ISA
 ├── instructions
 ├── registers
 └── encoding

ABI
 ├── calling convention
 ├── data layout
 ├── symbol convention
 └── OS integration
```

Không được trộn hai tầng.

---

# 562.99. ISA vs object format

```text id="q8v2n5"
x86-64 + ELF
x86-64 + PE/COFF
x86-64 + Mach-O
```

là các tổ hợp hợp lệ.

---

# 562.100. Target matrix

Compiler phải validate matrix:

| ISA | ABI/Platform | Object |
|---|---|---|
| x86-64 | SysV | ELF |
| x86-64 | Win64 | PE/COFF |
| x86-64 | Darwin | Mach-O |
| AArch64 | Linux | ELF |
| AArch64 | Apple | Mach-O |
| AArch64 | iOS | Mach-O |
| WASM32 | WASI | WASM |
| WASM64 | WASI profile | WASM |

---

# 562.101. Target capabilities

TargetDescription phải expose:

```text id="m4q9x7"
supports_threads
supports_atomics
supports_simd
supports_exceptions
supports_tls
supports_unwind
supports_dynamic_linking
supports_shared_memory
```

---

# 562.102. Capability ≠ feature

Platform capability và ISA feature phải là hai namespaces.

---

# 562.103. Target legality query

Codegen có API:

```text id="v7x2m5"
target.supports(feature)
target.supports_instruction(opcode)
target.supports_abi(operation)
```

---

# 562.104. No string-based legality

Không dùng:

```text
if target.name == "x86_64"
```

rải rác trong compiler.

---

# 562.105. Backend hooks

Generic codegen chỉ gọi abstraction:

```text id="q3m8v1"
TargetBackend::lower(...)
TargetBackend::select(...)
TargetBackend::legalize(...)
```

---

# 562.106. Target-specific lowering

Được phép khi semantics không biểu diễn đủ bằng generic operations.

---

# 562.107. Target intrinsic

Axiom có intrinsic mechanism:

```text id="x5k9n2"
@intrinsic("x86.avx2.add_i32")
```

nhưng intrinsic phải target-gated.

---

# 562.108. Intrinsic portability

Portable code không được vô tình phụ thuộc target intrinsic.

---

# 562.109. Feature-gated APIs

Standard library có thể expose:

```text id="m8q4v6"
simd.avx2
simd.neon
```

với compile-time capability checks.

---

# 562.110. Compile-time target query

Comptime có thể query:

```text id="v3n7x5"
target.arch
target.os
target.pointer_width
target.features
```

nhưng phải deterministic.

---

# 562.111. Runtime CPU detection

Chỉ cần khi binary chứa multiple variants hoặc explicit runtime dispatch.

---

# 562.112. CPU feature validation

Runtime dispatch phải đảm bảo function variant không được gọi trên CPU không hỗ trợ.

---

# 562.113. Multi-versioning metadata

```text id="q7m2k8"
FunctionVariant {
    symbol
    required_features[]
}
```

---

# 562.114. Dispatch resolver

Có thể generate:

```text id="x4v9m1"
resolver()
```

nhưng phải obey platform initialization rules.

---

# 562.115. IFUNC-like mechanisms

Nếu platform hỗ trợ, có thể sử dụng.

Nếu không, Axiom-generated resolver được dùng.

---

# 562.116. Target-independent optimization

Optimizer không được duplicate x86/AArch64 logic nếu transformation target-independent.

---

# 562.117. Target-aware optimizer

Cost model nhận TargetInfo.

---

# 562.118. Legalizer interface

```text id="n6q3m8"
legalize_operation(op, target)
```

phải deterministic.

---

# 562.119. Selection interface

```text id="m2x7v5"
select(operation, target)
```

---

# 562.120. Register allocator interface

Allocator generic nhận `RegisterInfo`.

---

# 562.121. Scheduler interface

Scheduler nhận:

```text id="q9v4k2"
SchedModel
InstructionInfo
ResourceModel
```

---

# 562.122. Frame lowering interface

```text id="x8m3n6"
FrameLowering {
    compute_frame()
    emit_prologue()
    emit_epilogue()
    emit_call_frame()
}
```

---

# 562.123. Branch relaxation interface

```text id="v5q2m9"
BranchRelaxer {
    measure()
    relax()
    stabilize()
}
```

---

# 562.124. Encoder interface

```text id="k3m8x1"
Encoder {
    encode()
    size()
    validate()
}
```

---

# 562.125. Decoder interface

```text id="q7v4n2"
Decoder {
    decode()
    validate()
}
```

---

# 562.126. Round-trip

```text
Instruction
   ↓ encode
Bytes
   ↓ decode
Instruction'
```

phải:

```text
Instruction ≡ Instruction'
```

ở semantic level.

---

# 562.127. Invalid bytes

Decoder phải reject invalid encoding thay vì tạo instruction giả.

---

# 562.128. Decoder fuzzing

Mỗi backend phải chịu fuzz testing trên arbitrary byte sequences.

---

# 562.129. Encoder fuzzing

Mỗi legal MachineInstruction được encode; illegal combinations phải reject.

---

# 562.130. Differential assembler validation

Trong development, Axiom có thể so sánh encoding với independent reference assembler/disassembler.

Điều này chỉ là validation tool, **không phải dependency của production compiler**.

---

# 562.131. No third-party backend dependency

Production compilation:

```text
Axiom
 ↓
Axiom Target Backend
 ↓
Axiom Encoder
 ↓
Axiom Object Writer/Linker
```

Không:

```text
Axiom
 ↓
LLVM/GCC/Clang
```

---

# 562.132. Backend source organization

```text id="m8q3v7"
compiler/
  target/
    model/
    features/
    abi/
    x86_64/
      registers
      instructions
      encoding
      lowering
      scheduling
    aarch64/
      registers
      instructions
      encoding
      lowering
      scheduling
    wasm/
      instructions
      control
      memory
      lowering
```

---

# 562.133. Shared infrastructure

Không duplicate:

```text id="x5m9q2"
MachineIR
Verifier
RegisterAllocator
PassManager
Cache
DebugMapping
Validation
```

trừ khi target thật sự cần specialization.

---

# 562.134. Target backend plugin boundary

Backend có thể compile thành internal compiler component.

Không yêu cầu dynamic plugin trong production.

---

# 562.135. Future ISA

Kiến trúc phải cho phép thêm:

```text id="q2v7m4"
RISC-V
ARM32
PowerPC
LoongArch
```

mà không sửa semantic core.

---

# 562.136. New ISA checklist

ISA mới cần implement:

```text id="n8x3m5"
RegisterInfo
InstructionSet
FeatureSet
Legalizer
Selector
SchedModel
FrameLowering
BranchRelaxer
Encoder
Decoder
ABI adapters
```

---

# 562.137. ABI reuse

Một ISA có thể có nhiều ABI.

Không copy ISA backend.

---

# 562.138. OS reuse

Một ISA + ABI có thể target nhiều OS.

---

# 562.139. Object format reuse

Object writer độc lập với ISA.

---

# 562.140. Example composition

```text id="m6q1x8"
AArch64
   +
AAPCS64
   +
Linux
   +
ELF
```

hoặc:

```text
AArch64
   +
Apple ABI
   +
iOS
   +
Mach-O
```

---

# 562.141. Feature fingerprint

Machine code cache identity phải chứa toàn bộ feature set ảnh hưởng legality/codegen.

---

# 562.142. Tuning fingerprint

Nếu scheduling/cost thay đổi, tuning model phải tham gia cache identity.

---

# 562.143. Cross-target cache isolation

Không bao giờ reuse native code:

```text id="x3m7q9"
x86-64
```

cho:

```text
AArch64
```

---

# 562.144. Cross-feature cache isolation

Không reuse AVX2-generated function cho baseline target.

---

# 562.145. Semantic cache distinction

Semantic cache của `559` có thể reusable giữa target nếu query target-independent.

Machine code cache thì target-specific.

---

# 562.146. Query classification

Compiler query phải khai báo:

```text id="v8n2m5"
TargetIndependent
TargetDependent
```

---

# 562.147. Target-independent examples

```text id="q4m9x1"
name resolution
generic type checking
trait solving
```

---

# 562.148. Target-dependent examples

```text id="m7x3v8"
layout
ABI
instruction selection
register allocation
encoding
```

---

# 562.149. Cross-target compilation

Một source snapshot có thể được compile đồng thời:

```text id="n5q8k2"
x86-64
AArch64
WASM
```

mà semantic frontend được reuse.

---

# 562.150. Cross-target dependency graph

```text id="x8m4q3"
Source
  │
  ▼
Semantic Queries
  │
  ├──────────┬──────────┐
  ▼          ▼          ▼
x86-64     AArch64     WASM
backend     backend     backend
```

---

# 562.151. Target-independent semantic hash

Semantic hash không được chứa machine register assignments.

---

# 562.152. Target-specific codegen hash

Machine code hash phải phụ thuộc:

```text id="v6q2m9"
semantic input
target fingerprint
codegen profile
compiler version
```

---

# 562.153. Reproducible backend

Fixed:

```text id="m3x7n1"
source
target
features
compiler
optimization profile
```

→ same machine artifact.

---

# 562.154. Randomness

Không dùng random register allocation/scheduling trong production deterministic mode.

Nếu randomized testing bật:

```text seed
```

phải là explicit input.

---

# 562.155. Backend diagnostics

Ví dụ:

```text id="q8m4v2"
E562001 Unsupported target feature
E562002 Invalid instruction operand
E562003 Register allocation failure
E562004 Illegal instruction selection
E562005 ABI/backend mismatch
E562006 Branch range overflow
E562007 Invalid encoding
E562008 Decoder mismatch
E562009 Target configuration conflict
E562010 Unsupported target combination
```

---

# 562.156. Machine-readable target errors

Diagnostic phải chứa:

```text id="x5n9k3"
target
feature
instruction
operand
source span
suggested correction
```

---

# 562.157. AI backend query

AI semantic API phải cho phép:

```text
why_instruction_selected
why_feature_required
why_register_spilled
why_vectorization_failed
why_target_not_supported
why_branch_relaxed
```

---

# 562.158. Evidence

Mỗi explanation phải phân biệt:

```text id="m2q7x5"
Fact
CostModelDecision
Heuristic
Unknown
```

---

# 562.159. Target capability query

Ví dụ:

```text
target.supports("avx2")
target.supports("simd")
target.supports("atomics")
```

---

# 562.160. Backend test hierarchy

```text id="v7x3m8"
ISA unit tests
 ↓
Encoder/decoder tests
 ↓
Machine selection tests
 ↓
Register allocation tests
 ↓
ABI tests
 ↓
Object tests
 ↓
Execution tests
 ↓
Cross-target conformance
```

---

# 562.161. Instruction golden tests

Mỗi instruction family cần:

```text id="q3m9k2"
input operands
expected bytes
expected decoded form
expected effects
```

---

# 562.162. Encoding edge tests

Phải test:

- min/max immediate;
- negative displacement;
- maximum register;
- aliases;
- feature boundaries;
- invalid operands.

---

# 562.163. Branch tests

Test:

```text id="x8m2v6"
near
far
conditional
unconditional
forward
backward
```

---

# 562.164. Register allocator cross-target tests

Cùng Machine IR có thể chạy qua:

```text id="n4q7m1"
x86 register info
AArch64 register info
```

và kết quả phải hợp lệ theo từng target.

---

# 562.165. WASM-specific tests

Test:

```text id="m6v2q9"
structured CFG
deep nesting
br_table
indirect call
linear memory
SIMD
atomics
```

---

# 562.166. CPU feature tests

Compile cùng source với:

```text id="q8x3m5"
baseline
feature+
feature-
```

và verify target legality.

---

# 562.167. Multi-version tests

Verify runtime dispatch never selects unsupported variant.

---

# 562.168. ABI cross-tests

Generated Axiom function gọi từ C ABI reference program và ngược lại.

---

# 562.169. Independent execution oracle

Có thể dùng:

```text id="v5m9x2"
Axiom interpreter
reference runtime
```

để compare output.

---

# 562.170. Differential machine execution

`552`:

```text id="q3k8n6"
same semantic input
→ target A
→ target B
```

chỉ compare những semantics platform-independent.

---

# 562.171. Target-specific behavior

Không yêu cầu byte-identical hoặc floating-point identical nếu target semantics cho phép khác biệt.

---

# 562.172. Floating-point policy

Strict FP và fast FP phải là explicit compilation policy.

---

# 562.173. Endianness

TargetDescription phải explicit:

```text id="x7m4q2"
Little
Big
```

Không được assume little-endian trong generic layout engine.

---

# 562.174. Pointer width

`32/64` phải đến từ TargetSpec.

---

# 562.175. Data model

ABI layer quyết định:

```text id="m8q3v5"
pointer size
long size
alignment
calling convention
```

không ISA description.

---

# 562.176. Relocation capability

Target backend phải expose relocation forms mà object backend cần.

---

# 562.177. Code model

Target có thể support:

```text id="q5x9n1"
small
medium
large
PIC
PIE
```

khi phù hợp.

---

# 562.178. Addressing model

Codegen phải biết giới hạn address/displacement của target.

---

# 562.179. Large code model

Nếu direct branch/address không fit, backend phải emit alternative sequence/relocation.

---

# 562.180. Linker cooperation

Backend phải phối hợp với linker relaxation nhưng không giả định linker là assembler.

---

# 562.181. Target-specific relocation

Relocation type thuộc Object/Target integration layer.

---

# 562.182. Backend verification pipeline

```text id="v4m8q2"
Machine IR
 ↓
Target legality
 ↓
Instruction selection verifier
 ↓
Register verifier
 ↓
Frame verifier
 ↓
Scheduling verifier
 ↓
Relaxation verifier
 ↓
Encoder verifier
 ↓
Object validation
```

---

# 562.183. Formal backend contract

Mỗi backend phải cung cấp:

```text id="x6q3n9"
legal(operation)
select(operation)
encode(instruction)
decode(bytes)
```

và:

```text
decode(encode(I)) ≡ I
```

đối với mọi instruction legal.

---

# 562.184. Backend semantic equivalence

Target-specific lowering phải satisfy:

```text id="m2v7k5"
Semantics(MIR)
=
Semantics(MachineIR)
```

---

# 562.185. Feature equivalence

Hai target profiles khác nhau có thể tạo machine code khác nhau nhưng semantic contract phải giống nhau.

---

# 562.186. No backend semantic drift

ISA backend không được tự định nghĩa lại:

- integer overflow;
- ownership;
- memory model;
- panic;
- Result;
- concurrency semantics.

Các semantics này đến từ core language/IR.

---

# 562.187. Memory model

Backend chỉ implement memory ordering được quy định bởi `424/437`.

---

# 562.188. Atomic lowering proof

Atomic lowering critical path phải có evidence trong `552`.

---

# 562.189. Security-sensitive lowering

Pointer authentication, CFI, stack protection, constant-time codegen phải retain security policy metadata từ `549`.

---

# 562.190. Realtime-sensitive lowering

`@realtime` code không được vô tình nhận machine/runtime sequence tạo blocking/allocation.

---

# 562.191. Debug/unwind

Backend phải cung cấp target-specific unwind encoding cho `440`.

---

# 562.192. Debug register mapping

Debugger cần mapping:

```text id="q7m3x8"
Axiom value
→ Machine location
→ Physical register / stack
```

---

# 562.193. Register location lists

Optimized values có thể thay đổi location theo PC range.

---

# 562.194. Stack maps

Nếu runtime features yêu cầu stack maps, backend phải generate exact locations.

---

# 562.195. Safepoint assumption

Không có GC → không được tạo GC safepoint machinery mặc định.

---

# 562.196. Native backend size

Target descriptions phải ưu tiên generated compact tables; không duplicate giant runtime structures.

---

# 562.197. Backend startup

Compiler phải load target definitions nhanh; production binary không parse textual ISA specification.

---

# 562.198. Adding ISA without semantic modification

Acceptance test:

> Thêm một backend ISA mới mà không cần sửa parser, type checker, ownership engine, trait solver, semantic MIR hoặc package system.

---

# 562.199. Multi-target acceptance

Một source package phải có thể:

```text
check once
      ↓
semantic snapshot
      ├── x86-64
      ├── AArch64
      └── WASM
```

và chỉ target-dependent stages được chạy riêng.

---

# 562.200. HARD INVARIANTS

1. Target identity phải canonical.
2. Target fingerprint phải deterministic.
3. Target fingerprint phải chứa mọi input ảnh hưởng machine code.
4. ISA và ABI phải tách biệt.
5. ISA và object format phải tách biệt.
6. OS và ISA phải tách biệt.
7. Target backend không được sửa semantic language rules.
8. ISA description phải là source of truth cho instruction metadata.
9. Encoder và decoder không được duy trì semantic tables độc lập.
10. Mọi legal instruction phải có encoding.
11. Mọi encoded instruction phải decode được khi decoder hỗ trợ format đó.
12. `decode(encode(I))` phải semantic-equivalent với `I`.
13. Invalid instruction phải bị reject.
14. Invalid operand combination phải bị reject.
15. Unsupported feature phải bị reject.
16. Compiler không được emit instruction ngoài target feature set.
17. Feature implication phải deterministic.
18. Feature conflict phải được phát hiện.
19. Explicit feature disable không được silently ignore.
20. CPU model phải nằm trong target identity khi ảnh hưởng codegen.
21. Tuning model phải nằm trong cache identity khi ảnh hưởng codegen.
22. Tuning không được thay đổi semantics.
23. Register definitions phải là target data.
24. Register aliases phải được model chính xác.
25. Register units phải phản ánh overlap.
26. Reserved registers không được allocate.
27. Fixed registers phải được enforce.
28. Register classes phải chính xác.
29. Special registers phải được model riêng khi semantics khác ordinary registers.
30. Instruction implicit uses/defs phải explicit.
31. Instruction effects phải explicit.
32. Memory effects phải explicit.
33. Atomic effects phải explicit.
34. Trap effects phải explicit.
35. Branch effects phải explicit.
36. Calling convention không được hard-code trong ISA definition.
37. ABI lowering không được hard-code vào semantic MIR.
38. Generic register allocator không được biết tên register cụ thể.
39. Generic scheduler không được hard-code ISA opcode.
40. Generic optimizer không được phụ thuộc vào target string.
41. Không được rải `if target == ...` trong compiler core.
42. Target-specific behavior phải đi qua TargetBackend/TargetInfo.
43. Instruction selection phải kiểm tra legality.
44. Legalization phải preserve semantics.
45. Target expansion phải preserve semantics.
46. Intrinsic target-specific phải explicit.
47. Intrinsic phải feature-gated khi cần.
48. Portable code không được tự động nhận target-specific instructions ngoài policy.
49. Runtime CPU dispatch phải kiểm tra feature.
50. Multi-versioned function phải khai báo required features.
51. Không được gọi variant unsupported.
52. x86 register aliasing phải chính xác.
53. x86 FLAGS effects phải chính xác.
54. x86 addressing constraints phải chính xác.
55. x86 prefix semantics phải chính xác.
56. VEX/EVEX feature requirements phải chính xác.
57. x86 immediate range phải được validate.
58. x86 branch relaxation phải preserve target.
59. x86 atomic lowering phải preserve memory order.
60. x86 SIMD lowering phải preserve vector semantics.
61. AArch64 X/W aliases phải chính xác.
62. AArch64 SP không được nhầm với XZR.
63. AArch64 NZCV effects phải chính xác.
64. AArch64 immediate constraints phải chính xác.
65. AArch64 addressing constraints phải chính xác.
66. AArch64 literal ranges phải được kiểm tra.
67. AArch64 veneers phải preserve call semantics.
68. AArch64 SIMD/FP registers phải được model chính xác.
69. SVE không được giả định fixed vector length.
70. AArch64 atomic ordering phải preserve.
71. WASM backend không được ép vào CPU register model.
72. WASM stack semantics phải được preserve.
73. WASM structured control flow phải hợp lệ.
74. Irreducible CFG phải có deterministic lowering.
75. WASM locals phải có đúng type.
76. WASM linear memory semantics phải preserve.
77. WASM memory width phải theo target.
78. WASM tables phải được type-check.
79. WASM reference values không được nhầm với integers.
80. WASM SIMD phải feature-gated.
81. WASM threads phải feature-gated.
82. WASM atomics phải feature-gated.
83. WASI không được coi là ISA.
84. WASM imports phải explicit.
85. WASM exports phải explicit.
86. Không được tạo hidden host dependency.
87. Object format phải độc lập backend ISA.
88. Một ISA phải hỗ trợ nhiều object formats khi hợp lệ.
89. Một ISA phải hỗ trợ nhiều ABI khi hợp lệ.
90. Một ABI có thể được dùng trên nhiều OS khi hợp lệ.
91. Target matrix phải được validate.
92. Unsupported target combination phải diagnostic.
93. Endianness phải explicit.
94. Pointer width phải explicit.
95. ABI data model phải explicit.
96. Code model phải explicit khi relevant.
97. PIC/PIE phải explicit.
98. TLS model phải explicit.
99. Relocation capabilities phải explicit.
100. Backend phải expose target capabilities.
101. ISA features và platform capabilities phải tách namespace.
102. Target-independent semantic queries phải có thể reuse cross-target.
103. Target-dependent queries không được reuse sai target.
104. Semantic cache không được chứa machine register assignments.
105. Machine cache phải chứa target identity.
106. Machine cache phải chứa feature set.
107. Machine cache phải chứa ABI.
108. Machine cache phải chứa relevant tuning model.
109. Machine cache hit phải equivalent fresh compilation.
110. Cross-ISA machine cache reuse phải bị cấm.
111. Cross-feature unsafe cache reuse phải bị cấm.
112. Cross-ABI machine cache reuse phải bị cấm.
113. Cross-object-format assumptions phải bị cấm.
114. Cross-target frontend reuse không được làm mất target-specific semantics.
115. Parallel target compilation phải deterministic.
116. Worker ordering không được ảnh hưởng artifact semantics.
117. Backend output phải reproducible.
118. Randomized backend testing phải dùng explicit seed.
119. Encoder phải deterministic.
120. Decoder phải deterministic.
121. ISA table generation phải deterministic.
122. Generated backend code phải reproducible.
123. Backend build không được yêu cầu third-party compiler backend.
124. Production codegen không được route qua LLVM.
125. Production codegen không được route qua GCC.
126. Production codegen không được route qua Clang.
127. Production codegen không được route qua MSVC compiler backend.
128. Independent assembler/disassembler chỉ được dùng cho validation development.
129. Backend verifier phải chạy trước encoding.
130. Encoder verifier phải chạy.
131. Decoder fuzzing phải được thực hiện.
132. Encoder fuzzing phải được thực hiện.
133. Invalid byte streams không được crash compiler.
134. Invalid MachineIR không được crash compiler.
135. Instruction selection failures phải diagnostic.
136. Register allocation failures phải diagnostic.
137. Target configuration failures phải diagnostic.
138. Feature conflicts phải diagnostic.
139. Unsupported instructions phải diagnostic.
140. Unsupported ABI combinations phải diagnostic.
141. Branch range overflow phải relax hoặc diagnostic.
142. Literal range overflow phải resolve hoặc diagnostic.
143. Long-address requirements phải resolve hoặc diagnostic.
144. Machine transformations phải giữ provenance.
145. Debug mappings phải preserve source relationship.
146. Unwind mappings phải match frame transformations.
147. Stack maps phải match actual machine locations.
148. Security hardening phải preserve target policy.
149. Constant-time policy phải survive target lowering.
150. Realtime restrictions phải survive target lowering.
151. `no_alloc` không được bị phá bởi backend helper.
152. `no_block` không được bị phá bởi backend helper.
153. `no_panic` không được bị phá bởi backend transformation.
154. Atomic semantics phải integrate với memory model.
155. Floating-point policy phải integrate với target lowering.
156. Fast-math không được tự động bật.
157. Strict FP semantics phải preserve.
158. NaN behavior phải respect language policy.
159. Signed-zero behavior phải respect language policy.
160. Integer overflow semantics phải preserve.
161. Division edge cases phải preserve.
162. Pointer provenance phải preserve.
163. Alignment semantics phải preserve.
164. Volatile semantics phải preserve.
165. Memory ordering phải preserve.
166. Function address identity phải preserve khi observable.
167. Symbol visibility phải preserve.
168. Calling convention phải preserve.
169. Function pointer ABI phải preserve.
170. Struct ABI phải preserve.
171. Vector ABI phải preserve.
172. Variadic ABI phải preserve.
173. Return ABI phải preserve.
174. TLS ABI phải preserve.
175. Panic/unwind ABI phải preserve.
176. Freestanding target không được tự tạo libc dependency.
177. WASM target không được tự tạo host dependency.
178. Target-specific runtime helper phải explicit.
179. Runtime helper phải thuộc approved runtime contract.
180. Target backend không được tự định nghĩa ownership semantics.
181. Target backend không được tự định nghĩa type semantics.
182. Target backend không được tự định nghĩa trait semantics.
183. Target backend không được tự định nghĩa concurrency semantics.
184. Target backend không được tự định nghĩa error semantics.
185. Target backend phải tích hợp với `421` ABI.
186. Target backend phải tích hợp với `422` layout.
187. Target backend phải tích hợp với `424` atomics.
188. Target backend phải tích hợp với `440` debug/unwind.
189. Target backend phải tích hợp với `445` security.
190. Target backend phải tích hợp với `549` security policy.
191. Target backend phải tích hợp với `552` correctness validation.
192. Target backend phải tích hợp với `553` optimization.
193. Target backend phải tích hợp với `559` query identity.
194. Target backend phải tích hợp với `561` machine pipeline.
195. Serial và parallel backend execution phải equivalent.
196. Backend cache hit và fresh backend execution phải equivalent.
197. ISA backend mới không được yêu cầu sửa semantic core.
198. Target backend phải có instruction/encoding/ABI/conformance tests.
199. Multi-target compilation phải reuse semantic work khi dependency cho phép.
200. **Final invariant:** Axiom phải có một Target Backend Architecture trong đó **ISA, ABI, OS, object format, CPU features và tuning là các lớp độc lập nhưng composable**; instruction selection, register allocation, scheduling và encoding phải lấy metadata từ Target Description thay vì hard-code compiler core; x86-64, AArch64 và WASM phải cùng tuân một machine-code correctness contract; và việc thêm ISA mới phải không phá vỡ semantic compiler.

**BOOTSTRAP-562: LOCKED.**

---

# NEXT — BOOTSTRAP-563

## COMPILER LTO 2.0 — WHOLE-PROGRAM IR, THIN-LTO, CROSS-MODULE OPTIMIZATION, DE VIRTUALIZATION, GLOBAL ANALYSIS & LINK-TIME CODE GENERATION

Sau `561–562`, Axiom đã khóa:

```text
MIR
 ↓
Machine IR
 ↓
Target Backend
 ↓
Machine Code
 ↓
Object
```

nhưng `553` mới chỉ khóa **framework optimization tổng quát**. Phần còn thiếu quan trọng là cách compiler tối ưu **qua ranh giới module/package/object file** mà vẫn giữ được:

- ABI;
- symbol visibility;
- incremental compilation;
- distributed cache;
- deterministic build;
- debug/unwind;
- generic specialization;
- dynamic library boundaries;
- FFI;
- correctness evidence.

`563` sẽ khóa kiến trúc:

```text id="p8m4x7"
Module A ──┐
Module B ──┼──→ Semantic/Optimization Summary
Module C ──┘              │
                          ▼
                    Whole Program Graph
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
          Inlining    Devirtualize   Constant
                                   Propagation
              │           │           │
              └───────────┼───────────┘
                          ▼
                    Thin-LTO / Full-LTO
                          │
                          ▼
                     Codegen 561
                          │
                          ▼
                   Object / Linker 420
```

Trọng tâm tiếp theo sẽ là **cross-module optimization mà không biến build system thành monolithic compiler**, đồng thời tận dụng semantic metadata/cache đã khóa ở `554/559`, compiler daemon `555`, parallelism `558`, correctness engine `552` và optimization framework `553`.

**NEXT TASK: BOOTSTRAP-563.**