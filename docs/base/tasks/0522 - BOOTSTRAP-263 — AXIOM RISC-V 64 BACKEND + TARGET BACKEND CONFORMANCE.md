# BOOTSTRAP-263 — AXIOM RISC-V 64 BACKEND + TARGET BACKEND CONFORMANCE

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của 263 có hai phần:

1. Hoàn thiện backend thứ ba: **RISC-V 64**.
2. Dùng RISC-V để kiểm chứng rằng `Axiom LIR + TargetBackend Contract` thực sự không phụ thuộc x86-64 hay ARM64.

Đây là backend rất quan trọng vì RISC-V có ISA dạng modular, không có x86 FLAGS theo kiểu tương ứng, không có ARM64 NZCV, và có extension tùy chọn.

---

# 1. Backend architecture

```text
                         Axiom LIR
                             │
                    TargetBackend Contract
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
       x86-64              ARM64             RISC-V64
          │                  │                  │
          ▼                  ▼                  ▼
       Machine IR        Machine IR        Machine IR
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
                       AxiomObject
```

Frontend hoàn toàn không biết backend nào đang được sử dụng.

---

# 2. RISC-V philosophy

RISC-V không nên được coi là:

> “một ISA nhỏ hơn x86”.

Nó là một **ISA modular**.

Target thực tế có thể là:

```text
RV64I
RV64IM
RV64IMAFD
RV64GC
RV64GCV
...
```

Do đó `TargetSpec` phải coi extension là dữ liệu.

---

# 3. Baseline

Axiom RISC-V backend V1 chọn:

```text
RV64I
```

làm semantic baseline.

Các extension phổ biến:

```text
M
A
F
D
C
V
B
```

được bật riêng.

---

# 4. TargetFeatureSet

Ví dụ:

```text
TargetFeatureSet {
    rv64i: true
    m: true
    a: true
    f: true
    d: true
    c: true
}
```

---

# 5. `G`

Có thể cung cấp shorthand:

```text
RV64G
```

nghĩa là nhóm extension chuẩn tương ứng, nhưng compiler nội bộ phải expand thành feature set cụ thể.

Không được coi `G` là một instruction set nguyên khối.

---

# 6. Register model

RISC-V integer registers:

```text
x0 ... x31
```

---

# 7. ABI names

Backend có thể ánh xạ:

```text
x0 = zero
x1 = ra
x2 = sp
x3 = gp
x4 = tp
...
```

Tên ABI chỉ là backend metadata.

---

# 8. x0

`x0` luôn bằng zero.

Không phải register allocatable thông thường.

---

# 9. ra

```text
x1 = ra
```

lưu return address theo convention.

---

# 10. sp

```text
x2 = sp
```

special register.

Không đưa vào general allocator.

---

# 11. gp

```text
x3 = gp
```

platform/ABI dependent usage.

---

# 12. tp

```text
x4 = tp
```

được sử dụng cho thread-local storage conventions.

---

# 13. FP registers

Nếu F/D:

```text
f0 ... f31
```

---

# 14. Vector registers

Nếu V:

```text
v0 ... v31
```

Đây là một register class riêng.

---

# 15. Không có FLAGS register tương đương

Đây là một test rất quan trọng đối với Machine IR.

RISC-V thường thực hiện compare bằng giá trị integer:

```text
SLT
SLTU
```

rồi branch dựa trên register.

---

# 16. Vì vậy Machine IR không được giả định:

```text
compare → FLAGS → branch
```

Mà phải cho phép:

```text
compare → value
compare → branch
```

tùy target.

---

# 17. Generic condition representation

LIR có thể biểu diễn:

```text
Compare
Branch
```

Target selector quyết định:

```text
x86 → CMP/Jcc
ARM → CMP/B.cond
RISC-V → BLT/BGE/BEQ...
```

---

# 18. Integer arithmetic

RISC-V:

```text
ADD
SUB
```

---

# 19. Multiplication

M extension:

```text
MUL
MULH
MULHU
MULHSU
```

---

# 20. Division

```text
DIV
DIVU
REM
REMU
```

chỉ khi M extension có mặt.

---

# 21. Không có M

Compiler phải:

```text
software expansion
```

hoặc reject nếu operation/profile yêu cầu hardware operation.

---

# 22. Shift

```text
SLL
SRL
SRA
```

---

# 23. Immediate variants

```text
ADDI
ANDI
ORI
XORI
SLLI
SRLI
SRAI
```

---

# 24. Compare

```text
SLT
SLTU
SLTI
SLTIU
```

---

# 25. Branch

```text
BEQ
BNE
BLT
BGE
BLTU
BGEU
```

---

# 26. Conditional select

Baseline RV64I không có native conditional move tương tự ARM64 CSEL.

Compiler có thể dùng branch hoặc sequence phù hợp.

---

# 27. Đây là một test tốt cho LIR

Axiom:

```text
x = condition ? a : b
```

không cần biết target có `CSEL`, `CMOV`, hay không.

---

# 28. Address calculation

RISC-V có:

```text
ADDI
AUIPC
```

cho các pattern address.

---

# 29. PC-relative addressing

`AUIPC` có vai trò quan trọng.

Ví dụ conceptual:

```text
AUIPC t0, symbol_hi
ADDI  t0, t0, symbol_lo
```

---

# 30. Global access

PIC/relocation sequence được quyết định bởi:

```text
ABI
link model
visibility
object format
```

---

# 31. Load/store

```text
LB
LH
LW
LD
LBU
LHU
LWU
```

---

# 32. Store

```text
SB
SH
SW
SD
```

---

# 33. RISC-V load/store addressing

Thông thường:

```text
base + immediate
```

Không có x86:

```text
base + index * scale
```

---

# 34. LIR independence được chứng minh

Axiom LIR:

```text
load [base + index*4]
```

có thể được legalize thành:

```text
SLL index, 2
ADD address, base, index
LW value, 0(address)
```

---

# 35. Hoặc nếu address calculation đã được tối ưu trước đó, sequence có thể khác.

---

# 36. Immediate range

RISC-V immediate field có giới hạn theo instruction format.

Legalizer phải expand constants/address expressions khi không fit.

---

# 37. Large constants

Có thể dùng:

```text
LUI
ADDI
```

hoặc sequence phù hợp.

---

# 38. Constant optimization

Machine optimizer có thể chọn sequence ngắn nhất/nhanh nhất theo target.

---

# 39. Compressed extension

Nếu `C` enabled:

```text
C.ADD
C.ADDI
C.LW
C.SW
...
```

có thể giảm code size.

---

# 40. `C` không thay đổi semantic IR

Chỉ thay đổi encoding/instruction selection.

---

# 41. Code-size profile

`--profile size` có thể ưu tiên compressed instructions.

---

# 42. Floating point

F extension:

```text
f32
```

D extension:

```text
f64
```

---

# 43. FP instructions

Conceptually:

```text
FADD.S
FSUB.S
FMUL.S
FDIV.S

FADD.D
FSUB.D
FMUL.D
FDIV.D
```

---

# 44. FMA

Có:

```text
FMADD.S
FMADD.D
```

và variants.

---

# 45. Strict FP

Axiom strict FP semantics vẫn là authority.

Không được sử dụng FMA nếu kết quả observable thay đổi.

---

# 46. Integer ↔ FP conversion

RISC-V có các instruction conversion tương ứng.

ABI classifier quyết định argument/return locations.

---

# 47. RISC-V ABI

Backend phải hỗ trợ ít nhất:

```text
RV64 ABI
LP64
LP64D
```

khi tương ứng với target feature/ABI.

---

# 48. Integer arguments

Thông thường sử dụng:

```text
a0 ... a7
```

tức:

```text
x10 ... x17
```

---

# 49. Integer return

Thông thường:

```text
a0
a1
```

---

# 50. Floating arguments

ABI có FP argument registers khi ABI variant yêu cầu:

```text
fa0 ... fa7
```

---

# 51. Floating return

```text
fa0
fa1
```

tùy classification.

---

# 52. Aggregate classification

Giống architecture contract trước:

```text
struct
 ↓
ABI classifier
 ↓
registers / stack / indirect
```

---

# 53. sret

Large return có thể lower thành hidden result pointer.

Register/location cụ thể do ABI quyết định.

---

# 54. Programmer không thấy hidden pointer.

---

# 55. Stack alignment

Backend lấy từ ABI descriptor.

Không hardcode một alignment trong Core.

---

# 56. Callee-saved

Allocator nhận:

```text
caller_saved
callee_saved
```

từ RISC-V ABI.

---

# 57. ra preservation

Nếu function gọi function khác và cần giữ return address, prologue/frame lowering phải preserve `ra` theo ABI.

---

# 58. Leaf function

Function không call function khác có thể không cần save `ra` vào stack.

---

# 59. Ví dụ

```text
fn add(a: i64, b: i64) -> i64
```

conceptually:

```text
ADD a0, a0, a1
RET
```

---

# 60. Không cần stack frame.

---

# 61. Call

```text
JAL
```

hoặc indirect:

```text
JALR
```

---

# 62. Return

Conceptually:

```text
JALR x0, 0(ra)
```

assembler thường biểu diễn:

```text
RET
```

---

# 63. `RET` không nhất thiết là native opcode

Có thể là assembler pseudo-instruction.

Machine backend phải phân biệt real instruction và pseudo instruction.

---

# 64. Pseudo instructions

Backend có thể sử dụng:

```text
LI
MV
RET
CALL
TAIL
```

ở Machine IR trước final expansion.

---

# 65. Final encoder

Pseudo instructions phải được expand thành architectural instructions trước encoding.

---

# 66. Register allocator

Machine IR ban đầu:

```text
v0
v1
v2
```

sau allocation:

```text
a0
a1
t0
```

---

# 67. Temporary registers

ABI reserves một số caller-saved registers cho temporary allocation.

---

# 68. Spill

Nếu register pressure cao:

```text
v0 → stack slot
```

---

# 69. Stack slot

FrameLowerer tính offset cuối cùng.

---

# 70. Vector extension

Nếu `V` enabled:

```text
v0...v31
```

không nên được ép vào fixed 128/256/512-bit model.

---

# 71. Đây là điểm quan trọng.

RISC-V Vector là **vector-length agnostic/scalable**.

Do đó Axiom cần phân biệt:

```text
FixedVector<T,N>
ScalableVector<T>
```

ở compiler IR nếu muốn khai thác V extension đầy đủ.

---

# 72. Core không nhất thiết phải expose `ScalableVector`

Đây có thể là compiler/library abstraction.

---

# 73. VLEN

TargetSpec có thể chứa:

```text
VLEN
ELEN
vector capabilities
```

khi target biết compile-time.

---

# 74. Dynamic VL

Codegen phải tôn trọng semantics của vector-length configuration.

---

# 75. Vector register allocation

Không được giả định vector register có cùng physical width như x86 YMM/ZMM hoặc ARM V128.

---

# 76. Atomic extension

A extension:

```text
LR/SC
AMO
```

---

# 77. Atomic RMW

Ví dụ:

```text
AMOADD.W
AMOADD.D
```

---

# 78. Compare-exchange

RISC-V baseline A thường dùng:

```text
LR
SC
```

loop cho CAS-like operations.

---

# 79. Memory ordering

RISC-V có memory model khác x86.

Backend phải map:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

vào acquire/release bits + fences/sequence phù hợp.

---

# 80. `aq` / `rl`

Atomic instructions có thể sử dụng:

```text
aq
rl
```

flags.

---

# 81. Fence

```text
FENCE
```

có thể cần cho ordering.

---

# 82. Không được giả định atomic operation = ordinary load/store

---

# 83. Atomic width

Target capabilities xác định atomic widths.

Unsupported width:

```text
expand
fallback
reject
```

---

# 84. Misaligned access

Không được tự động giả định mọi misaligned access có semantics giống aligned access.

Axiom memory semantics + TargetSpec quyết định legality.

---

# 85. Volatile

RISC-V volatile access phải được giữ như observable machine memory operations.

---

# 86. MMIO

Platform layer có thể yêu cầu:

```text
volatile
fence
ordering
```

---

# 87. TLS

`tp` là architectural resource quan trọng.

Backend TLS model tùy:

```text
ELF
ABI
PIC/PIE
visibility
link mode
```

---

# 88. Thread pointer

Không cho register allocator sử dụng `tp` như GPR bình thường nếu ABI giữ semantics của nó.

---

# 89. ELF

RISC-V V1 ưu tiên:

```text
ELF64
```

---

# 90. Relocations

Backend/object layer phải hỗ trợ các relocation classes cần thiết cho:

```text
calls
PC-relative symbols
GOT
TLS
data
```

---

# 91. Relaxation

RISC-V toolchain có thể relax một số sequences sau link.

AxiomObject phải biểu diễn relocation semantics đủ để linker làm việc này.

---

# 92. Backend không tự giả định final address.

---

# 93. Linker relaxation

Ví dụ:

```text
AUIPC + ADDI
```

có thể được linker rút gọn nếu relocation conditions cho phép.

---

# 94. Backend correctness

Nếu relaxation không xảy ra, binary vẫn phải đúng.

---

# 95. Security extensions

Các extension như:

```text
Zicfiss
Zicfilp
```

nếu được hỗ trợ, thuộc target security configuration.

Không đưa vào Core.

---

# 96. Capability architectures

RISC-V ecosystem có thể có capability-oriented extensions/platforms.

Axiom pointer provenance vẫn là semantic model riêng.

---

# 97. Không đồng nhất:

```text
Axiom provenance
=
hardware capability pointer
```

Chúng có thể tương tác qua backend/system contract nhưng không phải một khái niệm.

---

# 98. Debug

Machine instruction giữ mapping:

```text
SourceSpan
MIR instruction
Machine instruction
```

---

# 99. Unwind

Backend phát sinh unwind information phù hợp ELF/platform ABI.

---

# 100. Machine verifier

RISC-V verifier kiểm tra:

```text
register legality
extension availability
immediate ranges
operand width
x0 restrictions
SP constraints
atomic legality
vector legality
branch range
relocations
ABI
```

---

# 101. Một điểm quan trọng: `x0`

Compiler không bao giờ được coi write vào `x0` là cách lưu value.

---

# 102. Example

```text
MOV x0, x5
```

semantic effect là bỏ kết quả.

Backend có thể dùng đó cho dead-value lowering nhưng phải hiểu x0 semantics.

---

# 103. Branch lowering

Axiom:

```text
if a < b
```

có thể:

```text
BLT a, b, target
```

không cần tạo compare result.

---

# 104. Hoặc nếu compare value được dùng:

```text
SLT t0, a, b
```

---

# 105. Đây là ví dụ cho thấy instruction selection phải nhìn **use context**.

---

# 106. Common subexpression

Nếu compare được dùng nhiều nơi:

```text
cmp = a < b
```

có thể materialize boolean một lần.

---

# 107. Nếu chỉ dùng làm branch

Không cần materialize boolean.

---

# 108. Đây là target-specific optimization sau semantic OptIR.

---

# 109. Branch inversion

Compiler có thể đổi:

```text
branch true
```

thành:

```text
branch false
```

để layout tốt hơn.

---

# 110. No semantic change

---

# 111. Compressed instruction selection

Nếu C enabled:

```text
Machine instruction
 ↓
size-aware selector
 ↓
compressed encoding
```

---

# 112. Nhưng không được để compressed instruction availability ảnh hưởng Core semantics.

---

# 113. Register allocator + compressed constraints

Một số compressed forms yêu cầu register subset.

Do đó backend có thể:

```text
prefer compact register
```

trong size profile.

---

# 114. Post-RA peephole

Có thể phát hiện:

```text
ADD x, x, 0
```

và loại bỏ.

---

# 115. Constant propagation

Nếu register đã known zero:

```text
ADD x, x0, y
```

có thể trở thành move-equivalent.

---

# 116. Machine scheduling

RISC-V backend cost model có:

```text
latency
throughput
pipeline
register pressure
```

theo CPU model.

---

# 117. Generic RISC-V

Nếu CPU model không xác định:

```text
generic-rv64
```

không giả định microarchitecture cụ thể.

---

# 118. CPU-specific

Ví dụ:

```text
sifive
thead
vendor-custom
```

nếu compiler có target model tương ứng.

---

# 119. Custom instructions

Không được hardcode vào Core.

System/compiler intrinsic có thể khai báo target-specific instruction.

---

# 120. Custom extension

TargetSpec:

```text
CustomExtension
```

có:

```text
opcode space
operand constraints
feature ID
ABI effects
memory effects
```

---

# 121. Không cho custom instruction tự ý phá verifier.

---

# 122. Inline ASM

RISC-V ASM constraints được target backend định nghĩa.

---

# 123. ASM clobbers

Phải khai báo:

```text
registers
memory
special state
```

nếu ảnh hưởng.

---

# 124. Machine effects

Custom instruction phải khai báo:

```text
Read
Write
Atomic
Volatile
IO
```

nếu cần.

---

# 125. Target Backend Conformance

Đây là phần quan trọng nhất của BOOTSTRAP-263.

Mỗi backend mới phải implement cùng contract.

---

# 126. Level 1 — Target description

Phải pass:

```text
TargetSpec tests
RegisterModel tests
Feature tests
DataLayout tests
```

---

# 127. Level 2 — ABI

Phải pass:

```text
argument classification
return classification
aggregate classification
sret
stack alignment
callee/caller save
variadic
TLS
unwind
```

---

# 128. Level 3 — Legalization

Phải test:

```text
integer widths
FP widths
vectors
atomics
unaligned
large constants
large aggregates
```

---

# 129. Level 4 — Instruction selection

Mọi LIR operation được:

```text
legal
lowered
expanded
```

hoặc reject rõ ràng.

Không được “im lặng bỏ qua”.

---

# 130. Level 5 — Register allocation

Test:

```text
high register pressure
cross-call values
register aliases
special registers
spill/reload
```

---

# 131. Level 6 — Frame

Test:

```text
zero-frame
leaf
non-leaf
large frame
alignment
dynamic frame
callee-save
unwind
```

---

# 132. Level 7 — Memory

Test:

```text
load
store
atomic
volatile
TLS
static
pointer arithmetic
address spaces
```

---

# 133. Level 8 — Control flow

Test:

```text
branch
loop
switch/match
indirect branch
call
tail call
return
panic
unwind
```

---

# 134. Level 9 — Numeric

Test:

```text
integer overflow
division
shifts
casts
f32
f64
NaN
infinity
signed zero
FMA
SIMD
```

---

# 135. Level 10 — Aggregate

Test:

```text
struct
tuple
enum
Option
Result
large return
large parameter
nested aggregate
alignment
padding
```

---

# 136. Level 11 — Ownership

Backend test program phải chứng minh rằng:

```text
Move
Copy
Drop
view
mut_view
```

không bị thay đổi bởi codegen.

---

# 137. Level 12 — Closure

Test:

```text
capture
Fn
FnMut
FnOnce
environment
closure escape
dynamic callable
```

---

# 138. Level 13 — Concurrency

Test:

```text
Atomic
Mutex
Channel
Send
Share
thread start
join
```

---

# 139. Level 14 — Async

Test:

```text
Future
await
suspension
Send across await
drop/cancel
```

---

# 140. Level 15 — FFI

Test:

```text
C ABI
foreign pointer
struct layout
calling convention
variadic
callbacks
TLS
```

---

# 141. Level 16 — Object

Test:

```text
ELF
PE
Mach-O
relocations
symbols
TLS
unwind
debug
dead strip
```

---

# 142. Level 17 — Reproducibility

Cùng inputs:

```text
source
compiler
target
features
profile
dependencies
```

phải tạo deterministic artifact trong reproducible mode.

---

# 143. Level 18 — Differential semantics

Đây là bài test mạnh nhất:

```text
ax-ref
   ↓
expected behavior
```

so với:

```text
x86 executable
ARM64 executable
RISC-V executable
```

---

# 144. Không so sánh assembly để quyết định correctness

Assembly chỉ là diagnostic/golden implementation detail.

---

# 145. Translation validation

Mỗi machine-level transformation quan trọng có thể được kiểm chứng:

```text
before Machine IR
        ↓
transform
        ↓
after Machine IR
```

với preconditions.

---

# 146. Backend pass contract

Mỗi pass phải khai báo:

```text
PassContract {
    Preconditions
    Reads
    Writes
    Preserves
    NewFacts
}
```

---

# 147. Ví dụ register allocation

Precondition:

```text
Machine IR structurally valid
```

Postcondition:

```text
all virtual registers assigned/spilled
all physical constraints satisfied
```

---

# 148. Machine verifier là authority cuối

Nếu allocator tạo machine code không hợp lệ:

```text
MachineVerifier
```

phải reject trước encoder.

---

# 149. Không được dựa vào assembler để bắt lỗi compiler.

---

# 150. Encoder failure

Encoder không nên là nơi đầu tiên phát hiện:

```text
invalid register
invalid immediate
invalid instruction feature
```

MachineVerifier phải bắt trước.

---

# 151. Backend API chuẩn

```text
trait TargetBackend {
    fn target_spec(...)
    fn lower_abi(...)
    fn legalize(...)
    fn select(...)
    fn allocate(...)
    fn lower_frame(...)
    fn lower_atomic(...)
    fn lower_tls(...)
    fn schedule(...)
    fn verify(...)
    fn encode(...)
    fn emit_object(...)
}
```

Đây là **compiler-internal protocol**, không phải public Axiom Core trait.

---

# 152. Backend-independent test harness

```text
BackendConformanceRunner {
    target
    feature_set
    abi
    test_suite
}
```

---

# 153. Test matrix

```text
                  x86-64   ARM64   RV64
Integer             ✓        ✓       ✓
FP                  ✓        ✓       ✓
SIMD                ✓        ✓       ✓
Atomic              ✓        ✓       ✓
ABI                 ✓        ✓       ✓
TLS                 ✓        ✓       ✓
FFI                 ✓        ✓       ✓
Debug               ✓        ✓       ✓
Unwind              ✓        ✓       ✓
Object              ✓        ✓       ✓
```

---

# 154. Backend portability rule

Một tính năng Core chỉ được coi là **backend-independent** nếu ít nhất:

```text
2+ substantially different ISAs
```

có thể implement mà không thay đổi semantic model.

Với Core quan trọng, RISC-V trở thành backend thứ ba để tăng độ tin cậy.

---

# 155. Điều này giúp phát hiện các lỗi thiết kế như

Nếu LIR yêu cầu:

```text
FLAGS
```

thì RISC-V sẽ phá ngay.

Nếu LIR yêu cầu:

```text
fixed 256-bit vector register
```

thì RISC-V V sẽ phá ngay.

Nếu LIR yêu cầu:

```text
base + index*scale
```

thì ARM64/RISC-V sẽ phá ngay.

Đây chính xác là điều ta muốn.

---

# 156. Target-independent LIR sau 263

LIR chỉ được phép biểu diễn semantic machine operations như:

```text
Load
Store
AtomicLoad
AtomicStore
AtomicRMW
Call
Return
Branch
Compare
Select
Add
Sub
Mul
Div
Shift
VectorOp
Convert
Bitcast
Address
Fence
Trap
```

chứ không được chứa:

```text
RAX
X0
XMM0
NZCV
FLAGS
LEA
CSEL
AUIPC
```

---

# 157. Target-specific Machine IR

Sau LIR mới xuất hiện:

```text
RAX
X0
XMM0
V0
NZCV
FLAGS
LEA
CSEL
AUIPC
```

---

# 158. Đây là boundary cực kỳ quan trọng

```text
Axiom LIR
   │
   │ target-independent
   ▼
Target Lowering
   │
   │ target-dependent
   ▼
Machine IR
```

---

# 159. Backend portability invariant

```text
ABACKEND-20
Target backends must implement a common compiler contract.

ABACKEND-21
Axiom LIR must not encode ISA-specific physical registers.

ABACKEND-22
Axiom LIR must not require an ISA-specific flags register.

ABACKEND-23
Axiom LIR must support targets without flags-based comparison.

ABACKEND-24
Axiom LIR must support fixed-width and scalable vector targets.

ABACKEND-25
Address expressions must remain target-independent before lowering.

ABACKEND-26
Calling convention classification is target/ABI specific.

ABACKEND-27
Aggregate ABI classification is never a Core type-system rule.

ABACKEND-28
Target features are explicit data.

ABACKEND-29
Unavailable instructions must never be emitted.

ABACKEND-30
Unsupported operations require legal expansion or explicit rejection.

ABACKEND-31
Machine verification precedes encoding.

ABACKEND-32
Register allocation is semantically transparent.

ABACKEND-33
Frame lowering is target/ABI specific.

ABACKEND-34
Atomic lowering must preserve Axiom memory semantics.

ABACKEND-35
Volatile lowering must preserve observability.

ABACKEND-36
TLS lowering is target/platform specific.

ABACKEND-37
Relocation semantics remain explicit.

ABACKEND-38
Object serialization remains separate from ISA encoding.

ABACKEND-39
Debug provenance survives backend lowering where possible.

ABACKEND-40
Unwind metadata must correspond to generated frame semantics.

ABACKEND-41
Target-specific optimization cannot alter Core semantics.

ABACKEND-42
CPU cost models affect code generation decisions only.

ABACKEND-43
Compressed instructions are encoding/code-size optimizations.

ABACKEND-44
Scalable vectors must not be modeled as fixed-width vectors.

ABACKEND-45
Special architectural registers cannot be treated as ordinary allocatable registers.

ABACKEND-46
Pseudo instructions must be expanded before final encoding.

ABACKEND-47
Relocation-sensitive sequences must remain valid without optional linker relaxation.

ABACKEND-48
Custom ISA extensions require explicit target feature contracts.

ABACKEND-49
Inline assembly must declare machine-visible effects.

ABACKEND-50
Backend failures must be diagnosable rather than silently producing invalid code.

ABACKEND-51
All target backends must pass common conformance suites.

ABACKEND-52
Semantic correctness is determined independently of assembly golden files.

ABACKEND-53
Equivalent Axiom programs must have equivalent observable behavior across targets.

ABACKEND-54
Backend caches include TargetId, feature set, ABI and codegen identity.

ABACKEND-55
Parallel backend compilation must preserve deterministic semantics.

ABACKEND-56
Backend implementation complexity must not leak into Core syntax.

ABACKEND-57
Adding a new ISA must not require changing Core semantics merely to accommodate its register architecture.

ABACKEND-58
Adding a new ABI must not require changing the language type system.

ABACKEND-59
Adding a new object format must not require changing frontend semantics.

ABACKEND-60
The TargetBackend Contract is the portability boundary of the native compiler.
```

---

# 160. Kết quả sau BOOTSTRAP-263

Axiom giờ có nền tảng:

```text
                    AXIOM LANGUAGE
                         │
                    Semantic Core
                         │
                    Verified MIR
                         │
                       OptIR
                         │
                      ABI MIR
                         │
                     Axiom LIR
                         │
              TargetBackend Contract
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
     x86-64            ARM64           RV64
        │                │                │
        ▼                ▼                ▼
   Machine IR       Machine IR       Machine IR
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                    AxiomObject
```

Đây là một mốc kiến trúc rất lớn.

**Từ đây trở đi, việc thêm CPU mới không còn là việc thiết kế lại compiler.** Nó chủ yếu là implement một `TargetBackend` mới và vượt qua conformance suite.

---

# BOOTSTRAP-264 — WASM BACKEND + TARGET CLASSIFICATION

Bước tiếp theo nên chuyển sang **WASM**, bởi WASM là bài kiểm tra còn khác biệt mạnh hơn RISC-V:

```text
x86-64 → register machine
ARM64  → register machine
RV64   → register machine
WASM   → virtual stack machine
```

Nó sẽ kiểm chứng một câu hỏi rất quan trọng:

> **Axiom LIR có thực sự độc lập với cả register machine lẫn stack machine hay không?**

BOOTSTRAP-264 sẽ thiết kế:

```text
Axiom LIR
   ↓
WASM TargetBackend
   ↓
Wasm IR
   ↓
locals / operand stack
   ↓
structured control flow
   ↓
linear memory
   ↓
WASM binary
```

đồng thời phải xử lý riêng **WASM32/WASM64, linear memory, table, indirect call, WASI, browser, GC proposal không bắt buộc, SIMD, threads/atomics và ABI** mà không làm rò rỉ các khái niệm này vào Axiom Core.