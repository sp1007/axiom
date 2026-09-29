# BOOTSTRAP-262 — AXIOM TARGET BACKEND CONTRACT + ARM64 BACKEND V1

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của task này không chỉ là thêm ARM64. Quan trọng hơn, nó **chứng minh Axiom LIR thực sự độc lập với ISA**.

Nếu sau BOOTSTRAP-261 ta thiết kế ARM64 bằng cách copy tư duy x86-64, kiến trúc backend sẽ dần bị “nhiễm x86”. Vì vậy 262 được chia thành:

```text
                    Axiom LIR
                       │
              TargetBackend Contract
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
       x86-64        ARM64        RISC-V
```

---

# 1. Nguyên tắc TargetBackend

Frontend tuyệt đối không biết:

```text
RAX
XMM0
RCX
RSP
x86 FLAGS
```

và cũng không biết:

```text
X0
X1
W0
SP
NZCV
```

của ARM64.

Frontend chỉ tạo:

```text
MIR → OptIR → ABI MIR → Axiom LIR
```

Backend nhận LIR và target facts.

---

# 2. TargetBackend Contract

Định nghĩa interface logic:

```text
TargetBackend {
    target_spec()
    register_model()
    abi_lower()
    legalize()
    select_instructions()
    allocate_registers()
    lower_frame()
    lower_atomics()
    lower_tls()
    lower_unwind()
    schedule()
    verify_machine()
    encode()
    emit_object()
}
```

Đây là **compiler-internal contract**, không phải trait mà programmer sử dụng.

---

# 3. Backend pipeline chuẩn

```text
Axiom LIR
    ↓
Target ABI Lowering
    ↓
Legalization
    ↓
Instruction Selection
    ↓
Virtual Register Machine IR
    ↓
Register Allocation
    ↓
Frame Lowering
    ↓
Post-RA Optimization
    ↓
Scheduling
    ↓
Machine Verification
    ↓
Encoding
    ↓
AxiomObject
```

---

# 4. TargetSpec chung

```text
TargetSpec {
    architecture
    pointer_width
    address_width
    endianness
    object_format
    data_layout
    calling_conventions
    register_model
    atomic_capabilities
    simd_capabilities
    tls_model
    unwind_model
    cpu_features
    system_abi
}
```

---

# 5. Target không chỉ là CPU

Ví dụ:

```text
x86_64-linux-gnu
x86_64-windows-msvc
aarch64-linux
aarch64-windows
aarch64-macos
```

là các target khác nhau.

---

# 6. Triple

Compiler duy trì:

```text
Build
Host
Target
```

như đã frozen ở 194.

Ví dụ:

```text
Build  = x86_64-windows
Host   = x86_64-windows
Target = aarch64-linux
```

---

# 7. DataLayout

Backend không được suy ra layout bằng architecture name.

`TargetSpec.DataLayout` xác định:

```text
integer sizes
pointer sizes
alignment
endianness
aggregate ABI facts
vector alignment
atomic widths
```

---

# 8. RegisterModel

Contract:

```text
RegisterModel {
    register_classes
    physical_registers
    aliases
    reserved_registers
    caller_saved
    callee_saved
    special_registers
}
```

---

# 9. Special registers

Có thể bao gồm:

```text
stack pointer
frame pointer
link/return register
status/flags
thread pointer
```

nhưng frontend không nhìn thấy chúng.

---

# 10. Register allocation contract

Backend allocator nhận:

```text
MachineFunction
```

và trả:

```text
AllocatedMachineFunction
```

với mọi virtual register đã được map hoặc spill.

---

# 11. CallingConvention interface

```text
CallingConvention {
    classify_argument(type)
    classify_return(type)
    assign_registers()
    assign_stack()
    lower_call()
    lower_return()
    caller_saved()
    callee_saved()
    stack_alignment()
    frame_requirements()
}
```

---

# 12. Aggregate classification

Đây là điểm cực kỳ quan trọng.

Không có rule:

> “struct luôn truyền bằng pointer.”

Thay vào đó:

```text
Semantic aggregate
        ↓
ABI classifier
        ↓
register / register-pair / stack / indirect
```

---

# 13. Machine instruction contract

```text
MachineInstr {
    opcode
    operands
    defs
    uses
    implicit_defs
    implicit_uses
    clobbers
    memory_effect
    target_features
}
```

---

# 14. Addressing model

LIR có semantic:

```text
base + offset
base + index * scale
```

nhưng không yêu cầu target phải có addressing mode tương ứng.

---

# 15. Legalizer

Nếu target không có operation:

```text
i128_add
```

Legalizer có thể expand:

```text
low_add
high_add_with_carry
```

---

# 16. Target-independent correctness

Mọi target backend phải bảo đảm:

```text
MachineSemantics(program)
=
AxiomSemantics(program)
```

---

# 17. ARM64 TargetSpec

ARM64/AArch64 V1:

```text
Architecture = AArch64
PointerWidth = 64
AddressWidth = 64
Endianness = Little
```

---

# 18. ARM64 register model

General-purpose:

```text
X0 ... X30
```

với sub-register 32-bit:

```text
W0 ... W30
```

---

# 19. SP

Stack pointer:

```text
SP
```

là special register.

Không coi `SP` như GPR thông thường trong allocator.

---

# 20. XZR/WZR

ARM64 có:

```text
XZR
WZR
```

zero register semantics.

Allocator phải model chúng như special architectural operands.

---

# 21. PC

PC không phải GPR.

Instruction/control-flow semantics quản lý PC.

---

# 22. SIMD/FP registers

```text
V0 ... V31
```

Có các view:

```text
B
H
S
D
Q
```

tương ứng các element width/vector interpretation.

---

# 23. ARM64 không có FLAGS kiểu x86

ARM64 có:

```text
NZCV
```

Condition flags.

Điều này rất hữu ích để kiểm tra thiết kế machine IR:

> FLAGS không được thiết kế riêng cho x86.

---

# 24. Condition flags

Các instruction có thể:

```text
define NZCV
use NZCV
```

Machine IR phải model dependency.

---

# 25. ARM64 integer arithmetic

```text
ADD
SUB
ADDS
SUBS
```

---

# 26. Carry arithmetic

Multiword integer:

```text
ADDS low
ADC  high
```

và tương tự subtraction.

---

# 27. Overflow

Axiom checked arithmetic có thể lower bằng condition flags.

Ví dụ conceptually:

```text
ADD
B.VS overflow_handler
```

---

# 28. Không dùng x86-specific overflow assumptions

Semantic numeric layer vẫn là authority.

---

# 29. Multiplication

```text
MUL
SMULL
UMULL
```

tùy width/operation.

---

# 30. Division

```text
SDIV
UDIV
```

---

# 31. Shift

ARM64 có:

```text
LSL
LSR
ASR
ROR
```

với operand forms phù hợp.

---

# 32. Bit manipulation

ARM64 feature-dependent:

```text
CLZ
RBIT
REV
CNT
```

và các extensions.

---

# 33. Instruction selection không được expose ISA-specific operation vào Core

Ví dụ programmer không cần viết:

```text
ARM64::LSL
```

trừ system/intrinsic layer.

---

# 34. Address calculation

ARM64 có:

```text
ADD
SUB
ADR
ADRP
```

và load/store addressing modes.

---

# 35. PC-relative global address

Compiler có thể dùng:

```text
ADRP
ADD
```

hoặc relocation sequence tương ứng.

---

# 36. Literal access

Backend có thể dùng:

```text
LDR literal
```

khi thích hợp.

---

# 37. Load/store architecture

ARM64 là load/store ISA.

Memory operations:

```text
LDR
STR
LDUR
STUR
```

và nhiều variants.

---

# 38. Không có x86-style memory operand arithmetic

Điều này là một test tốt cho LIR.

Ví dụ LIR:

```text
load i32 [base + index*4]
```

ARM64 có thể cần:

```text
ADD temp, base, index, LSL #2
LDR result, [temp]
```

hoặc addressing form khác.

---

# 39. Vì vậy LIR không được chứa:

```text
x86 addressing mode
```

---

# 40. Register allocation

ARM64 GPR allocation:

```text
X0-X30
```

với constraints ABI.

---

# 41. X/W alias

```text
X0
 └── W0
```

Allocator phải hiểu chúng là cùng physical register với width khác.

---

# 42. V register allocation

Vector register class:

```text
V0..V31
```

---

# 43. Calling conventions — AArch64

AAPCS64 là baseline ABI quan trọng.

General arguments:

```text
X0-X7
```

FP/SIMD arguments:

```text
V0-V7
```

---

# 44. Return

Scalar integer thường:

```text
X0
```

FP/vector:

```text
V0
```

theo ABI classification.

---

# 45. Large aggregate

AAPCS64 classification quyết định:

```text
registers
stack
indirect/sret
```

không hardcode trong type system.

---

# 46. Hidden sret

Nếu cần:

```text
X0 = result storage pointer
```

và các argument tiếp theo được shift theo ABI.

---

# 47. Source không thấy sret

Đây là ABI MIR concern.

---

# 48. Caller-saved / callee-saved

Backend lấy từ AAPCS64 descriptor.

Allocator phải preserve callee-saved registers khi function sử dụng chúng.

---

# 49. Link register

ARM64 dùng:

```text
X30 / LR
```

cho return address.

---

# 50. Call

Thông thường:

```text
BL target
```

---

# 51. Indirect call

```text
BLR register
```

---

# 52. Return

```text
RET
```

thường sử dụng LR.

---

# 53. Tail call

Có thể lower thành branch nếu:

- ABI hợp lệ
- cleanup hoàn tất
- stack state phù hợp
- semantic behavior giữ nguyên.

---

# 54. Stack frame

ARM64 stack alignment ABI yêu cầu alignment phù hợp; backend quản lý frame size và saved registers.

---

# 55. Frame pointer

Thông thường:

```text
X29 = FP
X30 = LR
```

nhưng omission có thể được dùng khi debug/unwind/profile cho phép.

---

# 56. Prologue concept

Ví dụ:

```text
save FP/LR
allocate frame
```

nhưng exact instruction sequence là backend detail.

---

# 57. Epilogue

```text
restore frame
restore FP/LR
RET
```

nếu cần.

---

# 58. Không mandatory frame

Leaf function nhỏ có thể:

```text
ADD
RET
```

---

# 59. ARM64 không có x86 red zone

Target backend không được tạo abstraction chung kiểu:

```text
has_red_zone
```

mà chỉ có:

```text
StackFramePolicy
```

và target-specific rules.

---

# 60. Windows ARM64

Windows ARM64 có ABI riêng.

Do đó:

```text
AArch64
```

không đồng nghĩa:

```text
one calling convention
```

---

# 61. macOS ARM64

Mach-O + Apple ABI/system conventions.

---

# 62. Linux ARM64

ELF + AAPCS64/system ABI.

---

# 63. Backend architecture

```text
AArch64Backend
 ├── AAPCS64
 ├── WindowsARM64ABI
 ├── AppleARM64ABI
 ├── InstructionSelector
 ├── Legalizer
 ├── RegisterAllocator
 ├── FrameLowerer
 ├── AtomicLowerer
 ├── TLSLowerer
 └── Encoder
```

---

# 64. SIMD baseline

ARM64 NEON là baseline vector capability trên AArch64 platform profiles phù hợp.

Backend mô hình hóa:

```text
V128
```

và element types.

---

# 65. Vector operation

LIR:

```text
vector_add<T,N>
```

có thể thành:

```text
ADD Vd.4S, Vn.4S, Vm.4S
```

ví dụ với 4 × f32/int32 lanes.

---

# 66. Floating point

ARM64 FP instructions:

```text
FADD
FSUB
FMUL
FDIV
```

---

# 67. FMA

```text
FMLA
FMLS
```

nếu semantics cho phép.

---

# 68. Strict FP

Tương tự x86:

```text
strict FP
```

không được tự ý biến thành relaxed arithmetic.

---

# 69. Fast math

Chỉ khi semantic profile cho phép.

---

# 70. Compare

ARM64 có:

```text
CMP
FCMP
```

và condition branching.

---

# 71. Conditional select

ARM64:

```text
CSEL
```

có thể lower branchless expressions.

---

# 72. Đây là backend optimization, không phải Core syntax.

---

# 73. Conditional set

Có thể dùng:

```text
CSET
```

cho boolean materialization.

---

# 74. Bitfield operations

ARM64 có:

```text
UBFM
SBFM
BFM
```

có thể tối ưu mask/shift/extract.

---

# 75. Instruction combining

LIR:

```text
shift
mask
```

có thể match một bitfield instruction.

---

# 76. Constant materialization

ARM64 thường cần sequence:

```text
MOVZ
MOVK
MOVN
```

cho constants lớn.

---

# 77. Backend cost model

Phải cân bằng:

```text
instruction count
code size
latency
throughput
register pressure
```

---

# 78. ADRP + ADD

Global/static address thường có thể lower thành PC-relative sequence.

---

# 79. GOT/PLT

Dynamic/PIC binaries có thể yêu cầu:

```text
GOT
PLT
```

hoặc platform equivalent.

Backend chỉ tạo relocation/reference semantics; linker hoàn thiện.

---

# 80. TLS

ARM64 TLS lowering phụ thuộc:

```text
OS
link mode
symbol visibility
TLS model
```

Backend không expose model này vào Core.

---

# 81. Atomic baseline

ARM64 hỗ trợ atomics với:

```text
LDXR/STXR
LDAXR/STLXR
```

và các atomic instruction extensions tùy architecture profile.

---

# 82. LSE

Nếu target hỗ trợ ARMv8.1-A LSE:

```text
LDADD
CAS
SWP
STADD
```

có thể được sử dụng.

---

# 83. Không có LSE

Compiler có thể expand atomic RMW thành LL/SC loop.

---

# 84. Ví dụ conceptual

```text
atomic_fetch_add
```

↓

```text
loop:
    load-exclusive
    add
    store-exclusive
    retry if failed
```

---

# 85. Atomic memory order

Backend map:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

sang ARM memory instructions/fences thích hợp.

---

# 86. DMB

Memory barriers có thể được sử dụng khi semantic ordering yêu cầu.

---

# 87. Compiler không được giả định:

> ARM64 mạnh như x86.

Memory model khác nhau.

---

# 88. Đây chính là lý do Axiom memory model phải độc lập ISA.

---

# 89. Volatile

ARM64 volatile memory access vẫn là memory side effect.

Không được eliminate/merge tùy tiện.

---

# 90. Device/MMIO

Backend/system target có thể yêu cầu:

```text
volatile load/store
barrier
specific ordering
```

theo platform contract.

---

# 91. Pointer authentication

Apple ARM64 có thể có PAC.

Axiom không đưa PAC vào Core.

System layer có intrinsic/ABI support khi cần.

---

# 92. Branch target identification

BTI tương tự là target security feature.

Backend/security layer quản lý.

---

# 93. SVE

Không đóng cứng SVE vào Core v1.

Target capability:

```text
SVE
```

có thể mở rộng vector backend.

---

# 94. SVE không được ép vào fixed-width Vector semantics

nếu semantics thực sự scalable.

---

# 95. SME

Tương tự:

```text
SME
```

là future target extension.

---

# 96. GPU

ARM64 CPU backend không đồng nghĩa GPU backend.

GPU vẫn đi qua:

```text
GPU TargetBackend
```

riêng.

---

# 97. Instruction encoding

ARM64 instructions fixed-width 32-bit trong A64 baseline.

Encoder nhận:

```text
MachineInstr
```

và tạo instruction bytes.

---

# 98. Encoder verification

Trước encode:

```text
opcode legal
operand legal
register class legal
immediate range legal
feature enabled
```

---

# 99. Relocations

Ví dụ conceptual:

```text
branch relocation
ADR/ADRP relocation
GOT relocation
TLS relocation
```

được ghi vào AxiomObject.

---

# 100. Branch range

Nếu branch target quá xa:

```text
conditional branch
```

có thể cần veneer/branch expansion.

---

# 101. Linker veneer

Một số range problems chỉ biết sau layout.

Do đó linker/backend phải có contract.

---

# 102. Object format

ARM64 backend có thể phát ra:

```text
ELF64
Mach-O64
PE64
```

thông qua ObjectWriter chung.

---

# 103. ARM64 không có linker riêng

chỉ có:

```text
AArch64 Machine Encoder
```

+

```text
generic ObjectWriter
```

+

```text
target-specific relocation definitions
```

---

# 104. Debug/unwind

Backend phát sinh platform-compatible unwind metadata.

Không đưa unwind format vào Core.

---

# 105. Machine IR example

Axiom:

```axiom
fn add(a: i64, b: i64) -> i64 {
    a + b
}
```

ARM64 conceptual:

```text
X0 = a
X1 = b

ADD X0, X0, X1
RET
```

---

# 106. Không stack.

Không heap.

Không runtime.

---

# 107. Struct example

Semantic:

```text
Pair<u64,u64>
```

ABI classifier có thể map thành:

```text
X0
X1
```

không tạo object.

---

# 108. Memory access

Semantic:

```text
x.field
```

có thể thành:

```text
LDR W0, [X1, #offset]
```

nếu layout/ABI cho phép.

---

# 109. Array

```text
a[i]
```

có thể:

```text
index calculation
LDR
```

hoặc fused addressing.

---

# 110. Bounds check

Nếu RangeInfo chứng minh:

```text
0 <= i < len
```

thì check có thể biến mất.

---

# 111. Nếu không chứng minh được

Machine code phải giữ semantic bounds behavior.

---

# 112. Ownership không đi xuống machine code

Ví dụ:

```text
Move x
```

không nhất thiết tạo instruction.

Nó đã được compiler verifier xử lý.

---

# 113. Copy cũng vậy.

```text
Copy x
```

có thể:

```text
register alias
```

hoặc physical move/copy nếu cần.

---

# 114. Drop

Nếu Drop cần runtime operation:

```text
call/drop sequence
```

Nếu type trivially destructible:

```text
nothing
```

---

# 115. Đây là abstraction erasure thực sự

Programmer có ownership semantics.

Machine code chỉ còn operations cần thiết.

---

# 116. Closure

Một closure:

```axiom
let f = |x| x + offset
```

có thể lower thành:

```text
environment = offset
```

nhưng nếu inline:

```text
offset
```

có thể nằm luôn trong register.

---

# 117. Không có:

```text
class Closure
vtable
GC object
heap allocation
```

trừ khi dynamic semantics thực sự yêu cầu.

---

# 118. Trait static dispatch

Generic:

```text
fn process<T: Add>(x: T)
```

sau specialization có thể trở thành direct machine function.

---

# 119. dyn Trait

Ngược lại:

```text
dyn Trait
```

có explicit dynamic call machinery.

---

# 120. Backend không quyết định có dynamic dispatch hay không

Đó là semantic/ABI layer.

---

# 121. Target-independent machine memory model

Machine backend nhận memory effects:

```text
Read
Write
Atomic
Volatile
IO
Foreign
```

Không tự suy luận rằng mọi load/store là reorderable.

---

# 122. Memory barrier insertion

ARM64 có thể cần barrier mà x86 không cần.

Do đó:

```text
Axiom semantics
      ↓
AtomicLowerer(target)
```

---

# 123. Đây là một test quan trọng

Nếu cùng một Axiom atomic function:

```text
atomic_store_release(x, v)
```

x86 có thể cần:

```text
MOV
```

trong một số trường hợp.

ARM64 có thể cần:

```text
STLR
```

Hai machine sequences khác nhau nhưng semantic contract giống nhau.

---

# 124. Target-independent optimization

Ví dụ:

```text
x + 0
```

nên được loại ở OptIR trước backend.

---

# 125. Target-dependent optimization

Ví dụ:

```text
LEA
```

hoặc:

```text
CSEL
```

chỉ tồn tại sau target lowering.

---

# 126. Boundary

```text
Semantic Optimization
        ↓
Target-independent
        ↓
ABI Lowering
        ↓
Target-dependent optimization
```

---

# 127. Target-independent passes không được kiểm tra:

```text
"CPU có LEA không?"
```

---

# 128. Target-dependent pass có thể.

---

# 129. Backend plugin model

Về compiler architecture:

```text
BackendRegistry
    ├── x86_64
    ├── aarch64
    ├── riscv64
    └── wasm32/wasm64
```

---

# 130. Target selection

```text
TargetId
    ↓
BackendRegistry.lookup()
    ↓
TargetBackend
```

---

# 131. Không compile frontend nhiều lần cho mỗi target nếu semantic facts không đổi

Có thể:

```text
Source
 ↓
Typed HIR
 ↓
MIR
```

sau đó compile nhiều target.

---

# 132. Nhưng target-dependent `@cfg`

phải được resolve trước semantic compilation khi configuration thay đổi.

---

# 133. Cross compilation

Ví dụ:

```text
ax build --target aarch64-linux
```

frontend vẫn chạy trên host x86-64.

---

# 134. Comptime

Comptime chạy trên:

```text
Host execution environment
```

trong khi generated program target là:

```text
Target environment
```

Hai khái niệm đã được frozen ở 194.

---

# 135. GPU interaction

ARM64 CPU host + GPU:

```text
AArch64 Backend
        +
GPU Backend
```

không trộn machine register models.

---

# 136. Cache identity

Backend output cache key:

```text
SemanticFingerprint
TargetId
TargetFeatures
ABI
OptimizationProfile
CodegenFingerprint
```

---

# 137. Testing

Một semantic test:

```text
fn add(...)
```

phải có expected behavior độc lập ISA.

---

# 138. Backend golden tests

Có thể có:

```text
expected x86 assembly
expected ARM64 assembly
```

nhưng đây **không phải semantic oracle**.

---

# 139. Semantic oracle

Vẫn là:

```text
ax-ref
ax-mir
```

---

# 140. Differential backend test

```text
Reference
    ↓
x86 executable
    ↓
result

Reference
    ↓
ARM64 executable
    ↓
result
```

phải tương đương.

---

# 141. Adversarial backend tests

Bắt buộc kiểm tra:

```text
overflow
division
unaligned
atomic
volatile
NaN
signed zero
struct return
sret
closure
dyn Trait
panic
Drop
TLS
FFI
SIMD
```

---

# 142. ABI conformance

Mỗi target ABI phải có test với foreign compiler khi ABI đó là foreign ABI.

Ví dụ:

```text
Axiom ↔ C
```

trên:

```text
x86_64
ARM64
Windows
Linux
macOS
```

---

# 143. Stable Axiom ABI

Không được suy ra từ AAPCS64 hay SysV.

Nó là:

```text
Axiom Stable ABI
```

được định nghĩa riêng.

---

# 144. Foreign ABI adapter

```text
Axiom ABI
   ↓
ABI Adapter
   ↓
C ABI
```

nếu cần.

---

# 145. Đây là kiến trúc rất quan trọng cho C/C++ interop.

---

# 146. Backend không được chứa semantic hacks

Không cho phép kiểu:

```text
if source_language == Axiom
    special x86 trick
```

Semantic transformation phải xảy ra trước backend hoặc thông qua target contract.

---

# 147. Backend diagnostics

Machine-level error:

```text
AXBACKEND-E001
```

Ví dụ:

```text
operation requires target feature AVX2
```

---

# 148. Không được biến backend failure thành ICE nếu có thể chẩn đoán bình thường.

---

# 149. Unsupported target feature

Compiler có thể:

```text
reject
fallback
runtime dispatch
```

tùy semantic contract.

---

# 150. Không tự ý fallback nếu fallback thay đổi semantics.

---

# 151. ABI validation

Trước encoding:

```text
ABI MIR
    ↓
ABI verifier
```

kiểm tra:

```text
argument locations
return locations
stack alignment
callee/caller saves
sret
variadic rules
unwind
TLS
```

---

# 152. Machine verifier

Sau allocation:

```text
Machine IR
    ↓
MachineVerifier
```

kiểm tra:

```text
register legality
operand widths
implicit defs/uses
stack frame
calls
clobbers
branches
memory effects
features
```

---

# 153. Encoder verifier

Trước bytes:

```text
EncodingVerifier
```

đảm bảo instruction operands có encoding hợp lệ.

---

# 154. Ba tầng verification

```text
SemanticVerifier
       ↓
ABIVerifier
       ↓
MachineVerifier
       ↓
EncoderVerifier
```

---

# 155. Đây là điểm cực kỳ phù hợp với triết lý Axiom:

> **Mỗi tầng chịu trách nhiệm chứng minh một loại invariant riêng.**

---

# 156. ARM64 invariant set

```text
AARM-20
ARM64 is a backend target and is not part of Axiom Core semantics.

AARM-21
Axiom LIR must not contain x86-specific concepts.

AARM-22
TargetBackend provides target-specific lowering behind a stable compiler contract.

AARM-23
AArch64 register classes are isolated from frontend semantics.

AARM-24
X/W register aliasing must be modeled correctly.

AARM-25
SP is not an ordinary allocatable GPR.

AARM-26
XZR/WZR are explicit architectural zero registers.

AARM-27
NZCV dependencies must be modeled.

AARM-28
Register allocation cannot alter semantic behavior.

AARM-29
AAPCS64 classification is an ABI concern.

AARM-30
Windows ARM64 and other platform ABIs may differ.

AARM-31
Aggregate arguments use ABI classification.

AARM-32
sret is ABI-generated and invisible to source semantics.

AARM-33
Caller/callee save rules are ABI-specific.

AARM-34
LR is modeled as an architectural call/return resource.

AARM-35
Frame layout is target/ABI controlled.

AARM-36
ARM64 has no x86 red-zone assumption.

AARM-37
Stack alignment is enforced at ABI boundaries.

AARM-38
Address calculations are represented semantically before target lowering.

AARM-39
ARM64 load/store addressing is target-specific.

AARM-40
ARM64 PC-relative addressing is backend/linker behavior.

AARM-41
SIMD semantics are independent of V-register naming.

AARM-42
NEON/SVE/SME are target capabilities, not Core language concepts.

AARM-43
FP instruction selection must preserve Axiom FP semantics.

AARM-44
FMA is selected only when semantically legal.

AARM-45
Conditional execution optimizations must preserve observable behavior.

AARM-46
Atomic lowering must preserve Axiom memory ordering.

AARM-47
LSE is optional and feature-controlled.

AARM-48
Without LSE, atomic operations may be expanded to LL/SC sequences.

AARM-49
Volatile operations remain observable.

AARM-50
Device/MMIO operations preserve required ordering contracts.

AARM-51
TLS lowering is target/ABI specific.

AARM-52
PIC/GOT/PLT behavior is target/linker specific.

AARM-53
Pointer authentication is system/ABI functionality, not Core semantics.

AARM-54
Instruction encoding occurs only after machine verification.

AARM-55
Relocations are emitted explicitly.

AARM-56
Branch range limitations may require backend or linker relaxation.

AARM-57
Object serialization is separated from instruction encoding.

AARM-58
Debug/unwind metadata is generated according to target ABI.

AARM-59
Backend code generation must be deterministic in reproducible mode.

AARM-60
Backend caches include target and codegen identity.

AARM-61
Semantic tests are independent of machine instruction sequences.

AARM-62
Assembly golden tests are implementation tests, not semantic authority.

AARM-63
x86-64 and ARM64 must produce equivalent observable behavior for equivalent targets.

AARM-64
Target-independent optimization must not depend on ARM64-specific instructions.

AARM-65
Target-dependent optimization begins only after target lowering.

AARM-66
Unsupported operations require legal expansion or explicit rejection.

AARM-67
Target features must never be silently assumed.

AARM-68
Machine verification must precede encoding.

AARM-69
ABI verification must precede final machine generation.

AARM-70
Target backend complexity must not leak into Axiom Core syntax.
```

---

# 157. Kiến trúc backend sau 262

Ta hiện có:

```text
                       Axiom LIR
                           │
                 ┌─────────┴─────────┐
                 │ TargetBackend API │
                 └─────────┬─────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
       x86-64            ARM64           RISC-V
          │                │
   ┌──────┴──────┐   ┌─────┴──────┐
   │ ABI         │   │ ABI        │
   │ Legalizer   │   │ Legalizer  │
   │ Selector    │   │ Selector   │
   │ RegAlloc    │   │ RegAlloc   │
   │ Frame       │   │ Frame      │
   │ Atomic      │   │ Atomic     │
   │ TLS         │   │ TLS        │
   │ Encoder     │   │ Encoder    │
   └──────┬──────┘   └─────┬──────┘
          │                │
          └───────┬────────┘
                  ▼
             AxiomObject
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
       PE        ELF      Mach-O
```

---

# 158. Ý nghĩa của bước này

Có một thay đổi kiến trúc rất lớn:

**Axiom không còn có “x86 backend” và “ARM backend” như hai codepath riêng biệt.**

Nó có:

> **một Backend Contract + nhiều Target Implementation.**

Điều này sẽ giúp RISC-V, WASM, Android, iOS, macOS... sau này không phá Core/LIR.

---

## BOOTSTRAP-263 — RISC-V 64 BACKEND + BACKEND PORTABILITY CONFORMANCE

Bước kế tiếp hợp lý là **RISC-V 64**, vì nó tiếp tục kiểm tra những giả định còn sót lại:

- register architecture khác x86/ARM;
- calling convention khác;
- load/store architecture;
- CSR/special registers;
- atomic extension;
- vector extension;
- compressed instruction;
- relocation;
- ELF;
- không có concept tương đương x86 FLAGS hay ARM NZCV theo cùng cách.

Quan trọng hơn, 263 sẽ tạo **Target Backend Conformance Suite**: bất kỳ backend mới nào muốn được Axiom compiler chấp nhận phải vượt qua cùng một tập semantic/ABI/machine invariants.