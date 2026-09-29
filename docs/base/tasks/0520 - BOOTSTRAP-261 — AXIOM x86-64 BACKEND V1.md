# BOOTSTRAP-261 — AXIOM x86-64 BACKEND V1

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là backend ISA đầu tiên được đặc tả đủ sâu để triển khai compiler thực tế.

Mục tiêu không phải biến Axiom thành “ngôn ngữ x86”. Ngược lại:

> **Axiom LIR phải target-independent; x86-64 chỉ là backend đầu tiên thực hiện Target Lowering + Instruction Selection + Register Allocation + Encoding.**

---

# 1. Kiến trúc tổng thể

```text
Verified MIR
    ↓
Semantic OptIR
    ↓
ABI MIR
    ↓
Axiom LIR
    ↓
x86-64 Target Lowering
    ↓
x86-64 Machine IR
    ↓
Instruction Selection
    ↓
Register Allocation
    ↓
Spill / Reload
    ↓
Machine Scheduling
    ↓
Machine Verification
    ↓
x86-64 Encoding
    ↓
AxiomObject
    ↓
PE / ELF / Mach-O
```

---

# 2. TargetSpec

Mỗi compilation target có `TargetSpec`.

x86-64 V1:

```text
Architecture        = x86_64
PointerWidth        = 64
AddressWidth        = 64
Endianness          = Little
RegisterWidth       = 64
ObjectFormats       = PE64 / ELF64 / Mach-O64
```

Các feature:

```text
SSE2
SSE3
SSSE3
SSE4.1
SSE4.2
AVX
AVX2
FMA
AVX512
AES
PCLMULQDQ
BMI1
BMI2
POPCNT
LZCNT
```

không phải tất cả đều mặc định bật.

---

# 3. Baseline CPU

Axiom không được mặc định giả định AVX2.

Baseline x86-64 V1:

```text
x86-64
SSE2
```

CPU-specific optimization có thể bật thêm:

```text
-march=native
```

hoặc target profile tương đương.

---

# 4. Target Feature Set

Compiler giữ:

```text
TargetFeatureSet
```

Ví dụ:

```text
{
    sse2: true
    avx: true
    avx2: true
    fma: true
}
```

Instruction selector chỉ được sử dụng instruction mà TargetFeatureSet cho phép.

---

# 5. CPU multiversioning

Axiom có thể tạo:

```text
fn process_baseline(...)
fn process_avx2(...)
fn process_avx512(...)
```

và dispatch runtime nếu programmer/library yêu cầu.

Không được tự động tạo runtime dispatch cho mọi function.

---

# 6. Register classes

x86-64 backend định nghĩa:

```text
GPR
XMM
YMM
ZMM
FLAGS
```

---

# 7. GPR

64-bit:

```text
RAX RBX RCX RDX
RSI RDI RBP RSP
R8  R9  R10 R11
R12 R13 R14 R15
```

---

# 8. Subregisters

Backend hiểu:

```text
RAX
 ├── EAX
 ├── AX
 │    ├── AH
 │    └── AL
```

và tương tự các GPR khác.

---

# 9. FLAGS

FLAGS không phải register thông thường.

Instruction có thể:

```text
define flags
use flags
```

Compiler phải model dependency.

---

# 10. XMM/YMM/ZMM

```text
XMM0..XMM31
YMM0..YMM31
ZMM0..ZMM31
```

Số register khả dụng phụ thuộc ISA mode/features.

---

# 11. Register aliases

Ví dụ:

```text
XMM0 ⊂ YMM0 ⊂ ZMM0
```

Machine IR phải biết aliasing giữa register classes.

---

# 12. Register allocation

Axiom dùng register allocator độc lập target-level:

```text
LiveInterval
Interference
RegisterClass
RegisterConstraint
SpillCost
Rematerialization
```

---

# 13. V1 allocator

Khuyến nghị:

> **Linear scan cho debug/fast compilation + graph coloring hoặc PBQP-like allocator cho optimized release.**

Không cần ép một thuật toán duy nhất cho mọi profile.

---

# 14. Fast build

```text
ax build --profile dev
```

có thể dùng:

```text
linear scan
```

để giảm compile time.

---

# 15. Release

```text
ax build --release
```

có thể dùng allocator mạnh hơn.

Semantics giống nhau.

---

# 16. Calling convention

x86-64 backend phải tách:

```text
Axiom ABI
SysV AMD64 ABI
Windows x64 ABI
C ABI
```

---

# 17. SysV AMD64

Integer/pointer arguments chủ yếu:

```text
RDI
RSI
RDX
RCX
R8
R9
```

FP/vector:

```text
XMM0...
```

Return:

```text
RAX/RDX
XMM0/XMM1
```

theo classification.

---

# 18. Windows x64

Integer/pointer argument registers:

```text
RCX
RDX
R8
R9
```

FP arguments:

```text
XMM0..XMM3
```

---

# 19. Shadow space

Windows x64 call frame có:

```text
32-byte shadow/home space
```

Caller phải cung cấp theo ABI.

---

# 20. SysV red zone

SysV AMD64 có red zone.

Axiom backend có thể sử dụng trong profile phù hợp.

Windows không có red zone tương đương.

---

# 21. Không được đưa red zone vào Axiom semantic model

Nó chỉ là backend ABI optimization.

---

# 22. Stack alignment

Backend phải bảo đảm ABI-required alignment trước call.

Thông thường:

```text
16-byte alignment
```

tại call boundary theo ABI.

---

# 23. Stack frame

Machine frame có thể chứa:

```text
arguments
locals
spills
saved registers
temporary storage
outgoing arguments
alignment padding
```

---

# 24. Frame pointer

Không bắt buộc.

Release có thể:

```text
omit frame pointer
```

Debug/unwind/profile có thể yêu cầu giữ.

---

# 25. Stack probing

Large stack allocation có thể yêu cầu stack probing tùy OS/ABI.

Backend/system layer chịu trách nhiệm.

---

# 26. Dynamic stack allocation

Nếu Axiom hỗ trợ runtime dynamic stack allocation:

```text
alloca-like operation
```

phải được biểu diễn trong LIR/ABI layer.

Không đưa vào Core syntax.

---

# 27. Function classification

Trước instruction selection:

```text
Axiom ABI Signature
```

↓

```text
Physical ABI Signature
```

Ví dụ:

```text
fn add(a: i64, b: i64) -> i64
```

↓

```text
RDI = a
RSI = b
RAX = return
```

theo SysV.

---

# 28. Aggregate arguments

Struct không mặc định truyền bằng pointer.

ABI classifier quyết định:

```text
register
register pair
stack
indirect
```

---

# 29. Small struct

Ví dụ:

```axiom
struct Pair {
    a: u64
    b: u64
}
```

có thể được truyền bằng:

```text
RDI
RSI
```

tùy ABI.

---

# 30. Large struct

Có thể trở thành:

```text
hidden pointer
```

hoặc stack memory.

---

# 31. sret

Return struct lớn có thể lower:

```text
fn make() -> Large
```

thành conceptually:

```text
fn make(out: *mut Large)
```

ở ABI MIR.

Đây là compiler-generated ABI detail.

---

# 32. Programmer không thấy hidden sret parameter

---

# 33. Caller allocation

Axiom ưu tiên:

```text
caller allocates result storage
```

khi ABI cho phép.

Điều này phù hợp memory model đã thiết kế.

---

# 34. Không cần:

```text
malloc result
copy result
free result
```

chỉ để return một struct lớn.

---

# 35. Scalar return

Primitive integer:

```text
RAX
```

FP:

```text
XMM0
```

tùy ABI.

---

# 36. Multi-return

Axiom có thể biểu diễn:

```text
fn divmod(...) -> (i64, i64)
```

Compiler ABI classifier quyết định:

```text
RAX
RDX
```

nếu phù hợp.

---

# 37. Tuple return

Tuple là semantic aggregate.

Không có guarantee rằng tuple luôn là stack object.

---

# 38. Closure ABI

Static closure:

```text
fn invoke(env, arg)
```

có thể được compiler lower thành direct function + environment pointer/value.

---

# 39. Environment elimination

Nếu closure inline được:

```text
environment
```

có thể biến mất hoàn toàn.

---

# 40. Dynamic callable

`dyn Fn` có explicit runtime representation.

Backend ABI phải hỗ trợ:

```text
data pointer
call target
metadata/vtable
```

theo callable ABI.

---

# 41. Nhưng concrete closure không tự trở thành object.

---

# 42. Trait object

`dyn Trait` cũng có explicit ABI:

```text
data
metadata/vtable
```

Physical representation là ABI detail.

---

# 43. Function pointer

Không capture:

```text
fn(i32) -> i32
```

có thể là một machine code pointer.

---

# 44. Generic function

Static generic:

```text
fn add<T: Add>(...)
```

được specialize/monomorphize/code-share.

Không cần dynamic dispatch.

---

# 45. Integer instruction selection

Axiom LIR:

```text
add
sub
mul
div
rem
and
or
xor
shl
shr
sar
```

được target selector map sang x86 instructions.

---

# 46. Add

```text
ADD
```

---

# 47. Sub

```text
SUB
```

---

# 48. Multiplication

```text
IMUL
```

hoặc forms phù hợp.

---

# 49. Division

Signed:

```text
IDIV
```

Unsigned:

```text
DIV
```

Backend phải chuẩn bị dividend registers theo x86 semantics.

---

# 50. Division by zero

Đây là semantic behavior đã được Axiom numeric model xác định.

Backend phải đảm bảo behavior đó.

---

# 51. Shift

```text
SHL
SHR
SAR
```

---

# 52. Rotate

Library/compiler intrinsic nếu semantic operation tồn tại:

```text
ROL
ROR
```

---

# 53. Bit operations

Có thể dùng:

```text
BSF
BSR
TZCNT
LZCNT
POPCNT
```

chỉ khi feature/semantics phù hợp.

---

# 54. Compare

Axiom:

```text
compare(a,b)
```

có thể lower:

```text
CMP
```

hoặc:

```text
TEST
```

tùy pattern.

---

# 55. Boolean

Axiom `bool` semantic là boolean, không phải arbitrary integer.

Backend representation có thể là:

```text
0 / 1
```

---

# 56. Boolean normalization

Nếu source guarantees bool:

```text
0 or 1
```

compiler có thể dùng branchless operations.

---

# 57. Floating point

Baseline:

```text
SSE2
```

V1 không phụ thuộc x87.

---

# 58. f32

```text
ADDSS
SUBSS
MULSS
DIVSS
```

---

# 59. f64

```text
ADDSD
SUBSD
MULSD
DIVSD
```

---

# 60. SIMD

Axiom Vector<T,N> lowering phụ thuộc:

```text
SSE
AVX
AVX2
AVX512
```

---

# 61. Auto-vectorization

Loop:

```axiom
for i in 0..n {
    out[i] = a[i] + b[i]
}
```

có thể trở thành vector loop.

---

# 62. Vector width

Compiler chọn:

```text
128
256
512
```

dựa trên target features + cost model.

---

# 63. Không expose register width trong Core

Programmer viết semantic vector.

---

# 64. Mask

AVX512 có native mask registers.

Các target khác có thể lower mask thành vector/integer representation.

---

# 65. FMA

Nếu:

```text
a * b + c
```

và fast-math/FP contract cho phép:

```text
VFMADD
```

---

# 66. Strict FP

Nếu strict semantics yêu cầu rounding behavior cụ thể, compiler không được tự động thay bằng FMA nếu kết quả quan sát được thay đổi.

---

# 67. Fast-math

Chỉ khi explicit profile/attribute cho phép relaxation.

---

# 68. Memory addressing

x86 Machine IR hỗ trợ:

```text
base
index
scale
displacement
```

---

# 69. Scale

```text
1
2
4
8
```

---

# 70. Ví dụ

LIR:

```text
load i32 [base + index*4 + 16]
```

có thể trực tiếp thành một x86 memory operand.

---

# 71. Không cần address instruction riêng.

---

# 72. LEA

`LEA` có thể dùng để tính integer address/expression mà không load memory.

---

# 73. Compiler phải phân biệt:

```text
LEA = address arithmetic
```

với:

```text
MOV = memory load
```

---

# 74. Stack slot

Machine IR:

```text
StackSlot(id, size, alignment)
```

sau frame layout được biến thành:

```text
[RSP + offset]
```

hoặc:

```text
[RBP - offset]
```

---

# 75. Spill

Register allocator có thể tạo:

```text
spill RAX → stack slot
reload stack slot → RAX
```

---

# 76. Spill không thay đổi semantic ownership.

Chỉ là physical storage.

---

# 77. Callee-saved

Backend ABI descriptor xác định register nào phải preserve.

Ví dụ SysV:

```text
RBX
RBP
R12-R15
```

và Windows có tập khác.

---

# 78. Caller-saved

Các register caller phải coi là clobbered sau call nếu ABI quy định.

---

# 79. Call clobber set

Mỗi call Machine IR node có:

```text
uses
defs
clobbers
```

---

# 80. Tail call

Axiom compiler có thể optimize:

```text
return f(x)
```

thành tail call nếu:

- ABI cho phép
- frame conditions cho phép
- no cleanup còn cần thực hiện
- semantic observable behavior giữ nguyên.

---

# 81. Tail recursion

Có thể được tối ưu thành loop khi proof hợp lệ.

Không phải mọi recursion đều phải được tối ưu.

---

# 82. Branch

Axiom:

```text
if condition
```

↓

```text
CMP/TEST
Jcc
```

---

# 83. Branchless lowering

Compiler có thể dùng:

```text
CMOV
SETcc
bit operations
```

nếu cost model tốt.

---

# 84. Branch prediction

Backend không được giả định branch prediction là semantic.

PGO có thể cung cấp profile.

---

# 85. PGO

Profile có thể thay đổi:

```text
block layout
branch ordering
inlining
unrolling
vectorization
```

nhưng không thay đổi semantics.

---

# 86. Basic block layout

Hot blocks gần nhau để giảm:

```text
I-cache misses
branch displacement
```

---

# 87. Cold blocks

Có thể tách sang cold section.

---

# 88. Function sections

Release/size profile có thể dùng:

```text
.text.<function>
```

để linker dead-strip.

---

# 89. Data sections

Tương tự:

```text
.rodata
.data
.bss
```

và section splitting khi hữu ích.

---

# 90. PIC/PIE

Backend cần:

```text
PositionIndependent
```

flag.

---

# 91. Windows

PE relocation model.

---

# 92. Linux

ELF PIC/PIE.

---

# 93. macOS

Mach-O PIC.

---

# 94. Global access

Compiler không hardcode absolute address.

Tùy target/link mode:

```text
RIP-relative
GOT
TLS sequence
```

---

# 95. RIP-relative

x86-64 ưu tiên:

```text
RIP + displacement
```

cho nhiều static symbols.

---

# 96. TLS

Backend phải support x86-64 TLS models:

```text
local-exec
initial-exec
local-dynamic
general-dynamic
```

hoặc abstraction tương ứng.

---

# 97. Programmer không cần biết TLS model.

Compiler/linker chọn theo visibility/link mode.

---

# 98. Atomic operations

Baseline cần hỗ trợ:

```text
LOCK XADD
LOCK CMPXCHG
LOCK XCHG
```

và atomic load/store sequences phù hợp.

---

# 99. Memory order

Axiom:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

được lower thành x86 sequence phù hợp.

x86 có memory ordering tương đối mạnh, nên một số Axiom operations có thể cần ít/no explicit fence.

---

# 100. SeqCst fence

Backend phải emit fencing khi cần, ví dụ:

```text
MFENCE
```

hoặc sequence tương đương.

---

# 101. LOCK instruction

LOCKed RMW có atomic ordering semantics cần được model.

---

# 102. Atomic 128-bit

Không được mặc định assume lock-free.

Backend target capability:

```text
CMPXCHG16B
```

có thể được dùng khi available.

---

# 103. Nếu không có

Compiler dùng library/runtime fallback hoặc reject target capability.

---

# 104. Volatile

Volatile memory access phải trở thành machine memory operation.

Không được dead-code eliminate.

---

# 105. Inline assembly

Axiom system layer cần một abstraction kiểu:

```text
asm {
    ...
}
```

nhưng **không thuộc Core safe semantics**.

V1 backend cần định nghĩa machine-level constraints.

---

# 106. ASM constraints

Conceptually:

```text
inputs
outputs
clobbers
memory
volatile
```

---

# 107. ASM không được phá verifier một cách âm thầm

Nếu ASM có side effect memory:

```text
memory clobber
```

phải được khai báo.

---

# 108. Safer recommendation

Phần lớn intrinsic CPU nên được biểu diễn bằng compiler-known functions thay vì inline ASM.

Ví dụ:

```text
cpu::x86::pause()
cpu::x86::rdtsc()
```

---

# 109. Instruction selection

Machine selector dùng:

```text
pattern
cost
target features
register constraints
memory constraints
```

---

# 110. Pattern example

```text
a + 0
```

→

```text
a
```

ở OptIR trước instruction selection.

---

# 111. Multiply constant

```text
x * 8
```

có thể trở thành:

```text
SHL x, 3
```

nếu semantics tương đương.

---

# 112. LEA multiply-add

```text
x * 5 + y
```

có thể thành:

```text
LEA
```

nếu phù hợp.

---

# 113. Instruction combining

```text
load
add
store
```

có thể match thành instruction pattern tối ưu hơn.

---

# 114. Peephole

Sau allocation:

```text
mov rax, rbx
mov rcx, rax
```

có thể eliminate intermediate move.

---

# 115. Copy coalescing

Register allocator nên cố gắng gán cùng register cho:

```text
source
destination
```

khi không conflict.

---

# 116. Rematerialization

Cheap values như:

```text
constant
address
```

có thể tính lại thay vì spill.

---

# 117. Stack slot coloring

Các local có lifetime không overlap có thể dùng cùng stack slot.

---

# 118. Đây là physical optimization, không thay đổi ownership lifetime semantics.

---

# 119. Unwind

Machine backend phải phát sinh unwind metadata nếu profile yêu cầu.

Windows:

```text
.pdata
.xdata
```

Linux:

```text
.eh_frame
```

hoặc model phù hợp.

---

# 120. Panic abort profile

Nếu:

```text
panic = abort
```

có thể bỏ phần lớn unwind machinery.

---

# 121. Panic unwind profile

Nếu:

```text
panic = unwind
```

backend phải tạo đúng unwind info và cleanup landing paths.

---

# 122. Landing pads

MIR cleanup:

```text
Drop
```

phải được lower đúng.

---

# 123. Debug

Machine instruction giữ:

```text
SourceSpan
FunctionId
BasicBlockId
MIR instruction
```

mapping.

---

# 124. Debug variable locations

Compiler có thể track:

```text
x → RAX
x → [RSP+32]
x → optimized out
```

theo từng instruction range.

---

# 125. AI tooling

`ax explain --machine` có thể trả:

```text
source expression
↓
MIR
↓
LIR
↓
x86 instruction
↓
reason
```

---

# 126. Ví dụ

```axiom
fn add(a: i64, b: i64) -> i64 {
    a + b
}
```

SysV conceptual:

```text
RDI = a
RSI = b
RAX = RDI + RSI
RET
```

Compiler không cần tạo stack frame.

---

# 127. Đây là mục tiêu quan trọng:

Một function Axiom đơn giản phải có khả năng compile thành **ít instruction như code assembly tương đương**, thay vì bị ép qua runtime abstraction.

---

# 128. Windows example

Cùng source:

```text
RCX = a
RDX = b
RAX = RCX + RDX
RET
```

---

# 129. Source semantics không đổi.

Chỉ ABI lowering thay đổi.

---

# 130. Function prologue

Nếu không cần stack:

```text
add
ret
```

có thể là toàn bộ function.

---

# 131. Không mandatory prologue.

---

# 132. No mandatory runtime call

Một chương trình:

```axiom
fn main() {
}
```

không mặc định kéo theo:

```text
GC
reflection
async runtime
thread runtime
allocator
```

---

# 133. Startup

Executable entrypoint được linker/startup layer tạo.

---

# 134. Freestanding

Có thể:

```text
_start
```

→ Axiom function trực tiếp.

---

# 135. Machine verifier

Trước encoding phải kiểm tra:

```text
register class
operand size
instruction legality
feature requirement
memory alignment
addressing mode
implicit registers
flags dependencies
call ABI
stack alignment
unwind constraints
```

---

# 136. Ví dụ instruction legality

```text
AVX512 instruction
```

không được xuất nếu:

```text
AVX512 = false
```

---

# 137. VEX/EVEX state

Backend phải model các encoding/state effects cần thiết, đặc biệt transition giữa legacy SSE và AVX.

---

# 138. Zero-upper semantics

VEX instructions có semantics khác legacy SSE về upper vector bits.

Machine IR phải hiểu để tránh dependency/incorrect register state.

---

# 139. Register pressure

Cost model phải tính:

```text
GPR pressure
XMM/YMM/ZMM pressure
spill cost
call boundaries
```

---

# 140. Vector register pressure

Không mặc định vectorize chỉ vì instruction tồn tại.

---

# 141. Code size

`--profile size` ưu tiên:

```text
shorter encoding
fewer instructions
cold splitting
deduplication
```

nhưng không được phá performance semantics.

---

# 142. `xor eax,eax`

Pattern:

```text
x = 0
```

có thể chọn zero idiom.

---

# 143. Nhưng machine optimizer phải hiểu dependency semantics.

---

# 144. Constant materialization

Compiler chọn:

```text
immediate
literal pool
.rodata
register construction
```

tùy size/cost.

---

# 145. Large constants

Có thể dùng literal pool hoặc sequence.

---

# 146. Floating constants

Compiler chọn load từ:

```text
constant pool
```

hoặc instruction synthesis nếu có lợi.

---

# 147. Branch relaxation

Short branch vs near branch có thể được quyết định sau layout.

---

# 148. Relocation

Machine encoder tạo relocation records thay vì giả định final address.

---

# 149. Symbol reference

```text
call foo
```

có thể thành relocation:

```text
R_X86_64_PC32
```

hoặc PE tương ứng.

---

# 150. Backend không tự link symbol.

Linker xử lý relocation.

---

# 151. ObjectWriter

x86 backend tạo logical:

```text
AxiomObject
```

sau đó serializer chọn:

```text
ELF64
PE64
Mach-O64
```

---

# 152. ELF

Sections:

```text
.text
.rodata
.data
.bss
.tdata
.tbss
.eh_frame
.debug_*
```

nếu cần.

---

# 153. PE

Conceptually:

```text
.text
.rdata
.data
.pdata
.xdata
.reloc
```

---

# 154. Mach-O

Backend/object writer mapping tương ứng.

---

# 155. x86-64 backend không chứa business logic của linker.

---

# 156. Architecture boundary

```text
x86 Backend
    ↓
AxiomObject
    ↓
Object Writer
    ↓
Linker
```

---

# 157. Điều này cho phép sau này:

```text
ARM64 Backend
RISC-V Backend
WASM Backend
```

cùng sử dụng linker/object infrastructure.

---

# 158. CompilerDB additions

```text
X86TargetDB
RegisterDB
CallingConventionDB
MachineInstrDB
InstructionPatternDB
RegisterAllocDB
FrameDB
UnwindDB
AsmConstraintDB
X86FeatureDB
```

---

# 159. Core IDs

```text
RegisterId
RegisterClassId
MachineInstrId
MachineBlockId
MachineFunctionId
StackSlotId
CallingConventionId
TargetFeatureId
RelocationKindId
```

---

# 160. Machine IR

Conceptual:

```text
MachineFunction
 ├── MachineBlock*
 │    └── MachineInstr*
 ├── VirtualRegister*
 ├── StackSlot*
 ├── CallingConvention
 ├── FrameInfo
 └── UnwindInfo
```

---

# 161. Machine instruction

```text
MachineInstr {
    opcode
    operands
    defs
    uses
    implicit_defs
    implicit_uses
    memory_effect
    flags_effect
    target_features
    debug_location
}
```

---

# 162. Virtual registers

Instruction selection ban đầu dùng:

```text
vreg0
vreg1
vreg2
```

chưa phải physical register.

---

# 163. Allocation

↓

```text
vreg0 → RAX
vreg1 → RCX
```

---

# 164. Machine legalization

Một operation LIR có thể chưa hợp lệ x86.

Ví dụ:

```text
i128 division
```

cần expand thành sequence.

---

# 165. Legalizer

```text
MachineLegalizer
```

xử lý:

```text
unsupported width
unsupported atomic
unsupported vector op
unsupported addressing
```

---

# 166. Expansion

Ví dụ conceptual:

```text
128-bit add
```

↓

```text
ADD low
ADC high
```

---

# 167. Carry flag

Machine IR phải model FLAGS dependency giữa:

```text
ADD
ADC
```

---

# 168. Multiword arithmetic

Axiom `i128/u128` có thể được hỗ trợ semantic từ sớm dù machine baseline là 64-bit.

---

# 169. Backend không cần CPU native 128-bit integer register.

---

# 170. Big integer

`BigInt` là library abstraction, không phải machine primitive.

---

# 171. Division lowering

Nếu compiler biết divisor constant:

```text
x / 10
```

có thể biến thành multiply-high/shift sequence.

---

# 172. Nhưng numeric semantics phải được chứng minh tương đương.

---

# 173. Overflow semantics

Machine instruction tự nhiên có wrapping arithmetic.

Nếu Axiom operation là checked:

```text
ADD
JO trap
```

hoặc equivalent.

---

# 174. Saturating arithmetic

Có thể dùng SIMD/native instruction hoặc scalar expansion.

---

# 175. Checked arithmetic

Compiler có thể eliminate check khi RangeInfo chứng minh không overflow.

---

# 176. Trap

Trap target:

```text
panic
abort
trap
```

phụ thuộc panic/error profile.

---

# 177. No undefined overflow

Đây là một điểm Axiom khác C/C++.

Backend không được tận dụng signed-overflow UB vì Axiom không có semantics đó.

---

# 178. Alias assumptions

x86 backend nhận:

```text
AliasInfo
```

từ compiler.

Không tự tạo:

```text
NO_ALIAS
```

nếu frontend không chứng minh.

---

# 179. Memory ordering

Instruction scheduler không được reorder:

```text
atomic
volatile
fence
foreign effect
```

qua boundary không hợp lệ.

---

# 180. Ordinary loads

Được reorder mạnh hơn nếu MemorySSA + AliasInfo chứng minh.

---

# 181. Instruction scheduler

Có thể tối ưu:

```text
latency
throughput
port pressure
dependency chains
```

theo CPU model.

---

# 182. CPU model

Target:

```text
generic-x86-64
znver4
znver5
skylake
...
```

có cost table khác nhau.

---

# 183. Không cần compiler frontend biết microarchitecture.

---

# 184. Cost model

Có:

```text
Latency
ReciprocalThroughput
CodeSize
RegisterPressure
PortPressure
```

---

# 185. Instruction selection cost

Compiler chọn sequence:

```text
shorter
faster
less register pressure
```

theo optimization profile.

---

# 186. `-O0`

Ưu tiên:

```text
debuggability
fast compilation
simple code
```

---

# 187. `-O1`

Basic local optimization.

---

# 188. `-O2`

Default release optimization:

```text
inlining
CSE
LICM
vectorization
register allocation
```

---

# 189. `-O3`

Aggressive optimization.

---

# 190. `-Os`

Code size.

---

# 191. `-Oz`

Extreme size mode nếu cần.

---

# 192. Axiom không cần copy GCC flag semantics

Tên profile chỉ là compiler UX.

---

# 193. Determinism

Cùng:

```text
source
compiler semantic version
target
features
profile
dependencies
```

phải tạo cùng semantic result.

Machine layout cũng nên deterministic khi build inputs giống nhau.

---

# 194. Reproducibility

Không để:

```text
random register allocation
random symbol ordering
random section ordering
```

ảnh hưởng artifact nếu deterministic mode bật.

---

# 195. Parallel compilation

Machine functions có thể codegen song song.

Global ordering chỉ được áp dụng ở object serialization.

---

# 196. Cache

Machine code cache key bao gồm:

```text
FunctionSemanticFingerprint
TargetId
CPUFeatures
OptimizationProfile
CodegenVersion
ABI
```

---

# 197. Cache không được bỏ qua semantic fingerprint.

---

# 198. Incremental

Một function thay đổi không nên buộc compile lại toàn bộ module nếu dependencies không đổi.

---

# 199. Cross-module optimization

LTO nhận:

```text
MIR summaries
OptIR summaries
Machine cost data
```

---

# 200. Final architecture

```text
             ┌─────────────────────────┐
             │      Axiom Core          │
             └────────────┬────────────┘
                          ↓
                     Verified MIR
                          ↓
                      OptIR
                          ↓
                     ABI MIR
                          ↓
                     Axiom LIR
                          │
              ┌───────────┴───────────┐
              │                       │
          x86-64 Backend          ARM64 later
              │
       ┌──────┴───────┐
       ↓              ↓
 Instruction       Register
 Selection         Allocation
       │              │
       └──────┬───────┘
              ↓
        Machine IR
              ↓
        Machine Verify
              ↓
          Encoder
              ↓
        AxiomObject
              ↓
       ┌──────┼───────┐
       ↓      ↓       ↓
      ELF    PE     Mach-O
```

---

# 201. Các invariant chính

```text
AX86-20
x86-64 is a backend target, not part of Axiom Core semantics.

AX86-21
Axiom LIR must remain target-independent.

AX86-22
Target-specific instruction selection occurs only after semantic verification.

AX86-23
TargetFeatureSet controls legal instruction selection.

AX86-24
The compiler must never emit an instruction requiring an unavailable target feature.

AX86-25
Register classes are explicit machine-level entities.

AX86-26
Register aliases must be modeled by the allocator.

AX86-27
FLAGS dependencies must be explicitly modeled.

AX86-28
Physical register allocation cannot change semantic program behavior.

AX86-29
Spills are physical storage transformations only.

AX86-30
Stack slots do not create semantic ownership objects.

AX86-31
Stack layout is backend/ABI controlled.

AX86-32
Frame pointers are optional unless required by ABI/debug/unwind constraints.

AX86-33
Red-zone use is a backend ABI property.

AX86-34
Windows shadow space is a backend ABI property.

AX86-35
Calling convention lowering occurs before final instruction selection.

AX86-36
Axiom ABI and foreign ABIs are distinct contracts.

AX86-37
Aggregate ABI classification is target/ABI specific.

AX86-38
Hidden ABI parameters must never become source-level semantic parameters.

AX86-39
sret is an ABI lowering mechanism.

AX86-40
Caller allocation is preferred where ABI permits.

AX86-41
Closure environments may be passed explicitly or eliminated.

AX86-42
Concrete closures do not imply object headers.

AX86-43
dyn Trait representation is explicit and ABI-controlled.

AX86-44
Static dispatch remains the default.

AX86-45
Tail-call optimization requires ABI and cleanup legality.

AX86-46
x86-64 integer operations must preserve Axiom overflow semantics.

AX86-47
Axiom signed overflow cannot be optimized using C/C++ signed-overflow UB assumptions.

AX86-48
Checked arithmetic may be optimized away only when proven safe.

AX86-49
Floating-point instruction selection must preserve the active FP semantic profile.

AX86-50
Fast-math is an explicit semantic relaxation.

AX86-51
Strict FP cannot be replaced by mathematically equivalent but observably different operations.

AX86-52
SIMD width is selected by target features and cost model.

AX86-53
Core vector semantics do not expose x86 register width.

AX86-54
AVX/SSE register-state semantics must be modeled.

AX86-55
Memory operands preserve required alignment and access semantics.

AX86-56
LEA is address/integer computation, not a memory load.

AX86-57
Atomic operations cannot be lowered to ordinary operations.

AX86-58
Volatile operations cannot be removed as dead ordinary memory accesses.

AX86-59
Memory ordering must survive instruction scheduling.

AX86-60
Foreign calls without sufficient memory contracts are conservative barriers.

AX86-61
Inline assembly cannot silently invalidate compiler memory/ownership assumptions.

AX86-62
ASM constraints must declare relevant inputs, outputs and clobbers.

AX86-63
Instruction legalization may expand one semantic operation into multiple instructions.

AX86-64
Instruction expansion must preserve semantics.

AX86-65
Unsupported atomic widths require legal fallback or target rejection.

AX86-66
Machine instruction scheduling must preserve observable dependencies.

AX86-67
CPU cost models affect optimization only, not semantics.

AX86-68
PGO may affect layout and optimization decisions but not semantics.

AX86-69
Function layout may be optimized independently of source ordering.

AX86-70
Cold code may be separated when semantic reachability is preserved.

AX86-71
PIC/PIE is a target/link model concern.

AX86-72
RIP-relative addressing is a backend optimization/ABI mechanism.

AX86-73
TLS models are backend/linker concerns.

AX86-74
Unwind metadata must correspond to generated machine frames.

AX86-75
Abort profiles may omit unnecessary unwind machinery.

AX86-76
Debug information must preserve source-to-machine provenance where available.

AX86-77
Machine code generation must remain deterministic for fixed inputs in reproducible mode.

AX86-78
Incremental machine-code cache identity must include target and codegen inputs.

AX86-79
Parallel code generation must not introduce semantic nondeterminism.

AX86-80
Object generation is separate from linking.

AX86-81
x86-64 instruction selection must not embed linker policy.

AX86-82
Relocations are represented explicitly.

AX86-83
ELF, PE and Mach-O serialization are object-writer concerns.

AX86-84
Machine verification occurs before final encoding.

AX86-85
Final machine code must satisfy both Axiom semantics and x86-64 architectural constraints.

AX86-86
Backend optimization may reduce instruction count below naive source-to-machine lowering.

AX86-87
No mandatory runtime call may be introduced solely because a semantic operation exists.

AX86-88
A trivial Axiom function must be able to compile to the minimal legal machine sequence.

AX86-89
Backend complexity must not leak into Core syntax.

AX86-90
The same semantic program must retain equivalent behavior across x86-64 ABIs.
```

---

## Một kết quả rất quan trọng

Đến đây, Axiom đã có một đường đi tương đối hoàn chỉnh:

```text
Axiom source
   ↓
semantic model
   ↓
ownership
   ↓
capability
   ↓
effects
   ↓
MIR
   ↓
verification
   ↓
optimization
   ↓
ABI
   ↓
LIR
   ↓
x86-64
   ↓
machine code
   ↓
object
   ↓
native executable
```

Điều này có nghĩa **không còn cần thêm một abstraction layer chỉ để “nối” language với machine code**.

---

# BOOTSTRAP-262 — ARM64 BACKEND V1

Bước kế tiếp nên làm song song hai mục tiêu:

```text
x86-64 backend ──┐
                 ├── TargetBackend Contract
ARM64 backend ───┘
```

Thay vì thiết kế ARM64 độc lập một cách lặp lại.

**BOOTSTRAP-262** sẽ đặc tả `TargetBackend` interface chung:

```text
TargetSpec
RegisterModel
CallingConvention
InstructionSet
Legalizer
InstructionSelector
RegisterAllocator
FrameLowerer
UnwindEmitter
TLSLowerer
AtomicLowerer
ObjectEmitter
```

Sau đó triển khai ARM64 làm backend thứ hai.

Đây là bước rất quan trọng: **nếu chỉ có x86-64, rất dễ vô tình để những giả định của x86-64 lọt vào Axiom LIR.** ARM64 sẽ đóng vai trò “kiểm chứng kiến trúc” trước khi tiếp tục sang RISC-V, WASM và các target khác.