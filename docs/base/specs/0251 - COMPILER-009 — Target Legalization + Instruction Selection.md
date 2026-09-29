# COMPILER-009 — Target Legalization + Instruction Selection

Đây là phase biến **LIR target-independent** thành **Machine IR target-specific**.

Mục tiêu quan trọng nhất của Axiom:

> **Không thiết kế backend theo kiểu “AST/HIR → x86 instruction”. Mọi target đều đi qua cùng semantic/LIR contract, sau đó target backend tự legalize và select instruction.**

Pipeline chính:

```text
Optimized MIR
      │
      ▼
ABI Lowering
      │
      ▼
LIR
      │
      ▼
Target Legalization
      │
      ├── Type legalization
      ├── Operation legalization
      ├── Address legalization
      ├── Atomic legalization
      ├── Vector legalization
      └── Calling-convention legalization
      │
      ▼
Instruction Selection
      │
      ▼
Machine IR
      │
      ▼
Machine Optimization
      │
      ▼
Register Allocation
```

---

# 1. Target backend không được chứa semantic logic

Backend **không được quyết định**:

- ownership;
- Drop;
- borrow/view validity;
- Send/Share;
- trait resolution;
- async legality;
- type inference.

Những thứ đó đã hoàn thành trước LIR.

Backend chỉ cần biết:

```text
value
memory
control flow
ABI
registers
features
machine constraints
```

---

# 2. Target Description

Backend nhận:

```text
TargetDescription
```

đã định nghĩa trong TARGET-001:

```text
Architecture
ISA
CPU
Features
ABI
CallingConvention
Endian
PointerWidth
RegisterFile
AtomicCapabilities
TLS
Unwind
ObjectFormat
```

Ví dụ:

```text
x86_64-linux
x86_64-windows
aarch64-linux
aarch64-macos
riscv64-linux
wasm32-wasi
```

---

# 3. Legalization

LIR có thể chứa operation mà target không hỗ trợ trực tiếp.

Ví dụ:

```text
LIR:
    DIV i64
```

Target có thể:

```text
native instruction
```

hoặc:

```text
runtime helper
```

hoặc:

```text
instruction sequence
```

hoặc:

```text
reject
```

---

# 4. Legalization không thay đổi semantics

Ví dụ:

```text
DIV Checked
```

không thể biến thành machine division rồi bỏ kiểm tra divide-by-zero nếu semantic contract yêu cầu panic/trap.

Legalizer phải giữ:

```text
overflow
divide-by-zero
signedness
rounding
atomic ordering
volatile
```

---

# 5. Legalization result

Tôi đề xuất:

```text
LegalizeResult {
    Legal
    Expand(sequence)
    Custom(target_operation)
    LibCall(helper)
    Reject(diagnostic)
}
```

Nhưng `LibCall` không có nghĩa bắt buộc dùng libc/libgcc.

Nó có thể là:

```text
Axiom compiler helper
```

do chính Axiom cung cấp.

---

# 6. Không phụ thuộc compiler/runtime bên ngoài

Ví dụ target không có native:

```text
u128 multiplication
```

Axiom có thể sinh:

```text
__axiom_mul_u128
```

hoặc inline instruction sequence.

Không cần:

```text
libgcc
compiler-rt
MSVC runtime
LLVM runtime
```

trừ khi người dùng explicit chọn foreign runtime.

---

# 7. Type legalization

Initial primitive:

```text
i8 i16 i32 i64
u8 u16 u32 u64
isize usize
f32 f64
bool
```

Target backend có thể không có native register width cho mọi type.

Ví dụ x86-64:

```text
i8
i16
i32
i64
```

đều legal nhưng register semantics khác nhau.

---

# 8. Boolean legalization

Axiom semantic:

```text
bool = true | false
```

Machine representation có thể:

```text
0 / 1
```

nhưng compiler phải normalize boolean khi cần.

Ví dụ:

```text
x = bool_value
```

không được để arbitrary nonzero byte trở thành safe `true` nếu semantic invariant yêu cầu canonical representation.

---

# 9. Integer legalization

Một operation:

```text
ADD i64
```

thường:

```text
native
```

Trong khi:

```text
ADD i128
```

sau này có thể:

```text
lo + lo
hi + hi + carry
```

---

# 10. `i128/u128`

Không cần đưa `i128/u128` vào v0.1 primitive set ngay.

Nhưng backend architecture phải **cho phép**:

```text
Legal type
Expanded type
```

để sau này thêm mà không phá compiler.

---

# 11. Multi-register value

Ví dụ conceptual:

```text
u128
```

có thể:

```text
RAX:RDX
```

hoặc:

```text
four 32-bit registers
```

hoặc:

```text
stack
```

LIR nên hỗ trợ:

```text
multi-value
```

từ ABI/layout.

---

# 12. Large integer operations

Ví dụ:

```text
u128 * u128
```

legalizer có thể expand thành:

```text
64x64 multiplication
+
cross products
+
carry
```

Sau đó Machine IR mới xử lý register constraints.

---

# 13. Division

Division là ví dụ điển hình target-specific.

x86-64 có implicit registers cho một số integer division.

Machine selection phải xử lý:

```text
RAX
RDX
divisor
quotient
remainder
```

với fixed-register constraints.

AArch64/RISC-V có mô hình khác.

Do đó:

> Không encode implicit-register assumptions trong generic LIR.

---

# 14. Division by zero

Semantic MIR biết:

```text
DIV
```

với semantics.

Legalizer tạo:

```text
check divisor == 0
branch panic
```

nếu target instruction không tự cung cấp đúng semantics.

Hoặc tận dụng machine trap nếu và chỉ nếu trap mapping đúng Axiom semantics.

---

# 15. Signed division overflow

Trường hợp:

```text
MIN_INT / -1
```

phải được xử lý theo overflow semantics Axiom.

Không được mặc định lấy hành vi CPU nếu khác semantics.

---

# 16. Shift

LIR:

```text
SHL
SHR
SAR
```

phải chứa semantics shift count.

Ví dụ Axiom có thể chốt:

```text
shift count masked
```

hoặc:

```text
out-of-range → defined behavior
```

Legalizer phải tuân thủ đúng quy tắc đó.

---

# 17. Bit operations

Các operation:

```text
CLZ
CTZ
POPCOUNT
BSWAP
BITREV
```

nên tồn tại ở LIR nếu semantic library/core sử dụng.

Target:

```text
native
```

hoặc:

```text
expand
```

---

# 18. `SELECT`

LIR:

```text
SELECT condition, a, b
```

có thể hạ thành:

```text
CMOV
CSEL
branch
```

tùy target/cost model.

Không được bắt buộc branchless.

---

# 19. Flags

Đây là điểm đặc biệt quan trọng.

Generic LIR:

```text
CMP a, b
COND_BR EQ
```

x86 có flags.

AArch64 cũng có condition flags.

RISC-V thường tạo integer comparison result.

Machine instruction selector chịu trách nhiệm chuyển:

```text
generic condition
```

thành:

```text
target flags / register result
```

---

# 20. Không biến flags thành generic LIR state

Không nên thêm:

```text
CPUFlags
```

vào generic LIR.

Vì:

```text
x86 flags
AArch64 NZCV
RISC-V comparison register
```

khác nhau.

Flags là Machine IR resource.

---

# 21. Address legalization

Generic LIR:

```text
LOAD base + index * scale + offset
```

x86 có:

```text
base + index*scale + disp
```

AArch64 có:

```text
base + immediate
base + register
base + shifted register
```

RISC-V khác.

Legalizer chọn representation hợp lệ.

---

# 22. Address folding

Ví dụ:

```text
%p = ADD base, offset
%v = LOAD %p
```

x86 có thể:

```text
LOAD [base + offset]
```

thay vì:

```text
LEA temp
LOAD [temp]
```

Machine optimizer cũng có thể làm việc này.

---

# 23. `LEA`

Không nên tạo `LEA` trong LIR.

LIR chỉ:

```text
ADDRESS base + index*scale + offset
```

x86 selector có thể chọn:

```text
LEA
```

nếu có lợi.

---

# 24. Memory alignment

LIR LOAD/STORE có:

```text
size
alignment
volatile
atomic
address_space
```

Nếu alignment:

```text
known >= required
```

backend có thể chọn instruction phù hợp.

Nếu:

```text
unaligned
```

target-specific legalization.

---

# 25. Atomic legalization

LIR:

```text
ATOMIC_CAS
```

x86:

```text
LOCK CMPXCHG
```

AArch64:

```text
LSE CAS
```

hoặc:

```text
LDXR/STXR loop
```

RISC-V:

```text
LR/SC
```

hoặc extension phù hợp.

Semantic ordering không thay đổi.

---

# 26. Atomic ordering mapping

Axiom:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Target backend mapping phải bảo toàn semantics.

Ví dụ target có instruction mạnh hơn cần thiết:

```text
native stronger instruction
```

được phép.

Không được dùng instruction yếu hơn.

---

# 27. Atomic wait/notify

LIR có thể giữ abstraction:

```text
ATOMIC_WAIT
ATOMIC_NOTIFY
```

Legalizer có thể chọn:

```text
OS primitive
futex
wait-on-address
spin + park
runtime helper
```

Đây là trường hợp runtime capability có thể xuất hiện.

---

# 28. Volatile

Volatile phải tồn tại xuyên suốt:

```text
MIR
→ LIR
→ Machine IR
```

Không được:

```text
DCE
load folding
store elimination
reordering
```

như ordinary memory.

---

# 29. `volatile != atomic`

Backend không được coi:

```text
volatile
```

là:

```text
atomic
```

và ngược lại.

Hai semantic contract khác nhau.

---

# 30. Memory barriers

LIR:

```text
FENCE
```

Machine backend chọn:

```text
x86 MFENCE/LFENCE/SFENCE
AArch64 DMB/DSB/ISB
RISC-V FENCE
```

tùy semantics.

---

# 31. SIMD/vector legalization

Axiom có thể có target-independent vector operations:

```text
Vector<T,N>
```

Nhưng target không nhất thiết hỗ trợ đúng:

```text
N × sizeof(T)
```

---

# 32. Vector legal types

Ví dụ:

```text
<f32 x 4>
<f32 x 8>
<i32 x 4>
<i32 x 8>
```

x86:

```text
SSE
AVX
AVX2
AVX-512
```

AArch64:

```text
NEON
SVE
```

RISC-V:

```text
V
```

---

# 33. Vector expansion

Nếu target không có:

```text
vector operation
```

legalizer có thể:

```text
split vector
```

Ví dụ:

```text
<f32 x 8>
```

→

```text
<f32 x 4>
<f32 x 4>
```

hoặc scalarize.

---

# 34. Feature dispatch

Axiom cần phân biệt:

```text
required feature
preferred feature
available feature
```

Ví dụ:

```text
AVX2 available
```

Compiler có thể generate AVX2.

Nếu binary cần chạy trên baseline CPU:

```text
target feature set
```

không được vượt quá contract.

---

# 35. CPU dispatch sau này

Có thể hỗ trợ:

```text
@target_feature("avx2")
fn fast(...)
```

và runtime dispatch:

```text
if cpu_has_avx2 {
    fast()
} else {
    scalar()
}
```

Nhưng không cần biến CPU feature dispatch thành Core semantic complexity.

---

# 36. Instruction Selection

Sau legalization:

```text
LIR operation
```

→:

```text
Machine instruction pattern
```

Ví dụ:

```text
ADD i64
```

x86:

```text
ADD r64, r64
```

AArch64:

```text
ADD Xd, Xn, Xm
```

RISC-V:

```text
ADD rd, rs1, rs2
```

---

# 37. Pattern matching

Instruction selector nên có data-driven pattern table:

```text
Pattern {
    match
    predicate
    result
    cost
    required_features
}
```

Ví dụ conceptual:

```text
ADD
  + i64
  + register/register
      →
ADD64
```

---

# 38. Không hardcode toàn bộ selector bằng if/else

Không nên:

```text
if op == ADD
    if type == i64
        ...
```

hàng nghìn dòng.

Thay vào đó:

```text
TargetInstructionPatterns
```

và một selector engine chung.

---

# 39. Nhưng không cần “universal DAG machine”

Tôi không khuyến nghị xây một framework selector quá trừu tượng ngay từ đầu.

MVP:

```text
generic LIR
→ target pattern matcher
→ Machine IR
```

Sau này mới thêm:

- DAG;
- GlobalISel-like matching;
- superinstruction;
- peephole selector.

---

# 40. Selection strategy

MVP nên hỗ trợ:

```text
LocalPattern
BlockPattern
CFGPattern
```

đúng hướng MACHINE-IR-002.

---

# 41. Local pattern

Ví dụ:

```text
ADD
MUL
LOAD
STORE
CMP
```

→ một instruction.

---

# 42. Block pattern

Ví dụ:

```text
CMP
COND_BR
```

x86:

```text
CMP
Jcc
```

không cần materialize boolean.

---

# 43. CFG pattern

Ví dụ:

```text
if cond {
    x = a
} else {
    x = b
}
return x
```

có thể:

```text
SELECT
```

→:

```text
CMOV/CSEL
```

nếu cost model có lợi.

---

# 44. Compare + branch fusion

Generic:

```text
%cmp = CMP a,b
COND_BR %cmp
```

Machine:

```text
CMP a,b
JNE label
```

Không tạo temporary boolean register nếu target flags cho phép.

---

# 45. Compare + set

Generic:

```text
x = a < b
```

x86:

```text
SETcc
```

AArch64:

```text
CSET
```

RISC-V:

```text
SLT
```

---

# 46. Constant materialization

```text
CONST 64-bit
```

không nhất thiết thành một instruction.

x86:

```text
MOV imm64
```

hoặc:

```text
XOR reg,reg
...
```

AArch64 có thể:

```text
MOVZ/MOVK
```

nhiều instruction.

RISC-V:

```text
LUI
ADDI
...
```

Selector chọn sequence.

---

# 47. Constant pool

Large constants:

```text
vector
large aggregate
floating constants
```

có thể đặt vào:

```text
.rodata
```

và Machine IR dùng:

```text
SymbolRef
```

hoặc constant-pool entry.

---

# 48. Floating point

Không được cho optimizer tự ý biến:

```text
f32/f64
```

theo algebraic identities không hợp lệ nếu Axiom chưa định nghĩa floating-point fast-math semantics.

Ví dụ:

```text
x + 0
```

không nhất thiết bằng `x` với mọi IEEE-754 corner case.

---

# 49. Fast-math

Có thể có profile/annotation sau:

```text
@fast_math
```

nhưng **không nên bật mặc định**.

MVP:

> IEEE-ish semantics được bảo toàn; không tự ý reassociate FP.

---

# 50. FMA

Nếu source:

```text
a * b + c
```

không mặc định fuse thành:

```text
FMA
```

nếu rounding semantics thay đổi.

Sau này có explicit fast-math/contract.

---

# 51. Division/modulo optimization

Constant divisor:

```text
x / 10
```

có thể biến thành:

```text
multiply-high
shift
```

nếu MIR semantics được bảo toàn.

Đây là target-independent + target-dependent optimization phối hợp.

---

# 52. Strength reduction

Ví dụ:

```text
x * 2
```

→ shift/add nếu target/cost model có lợi.

Không phải lúc nào cũng tốt.

Do đó:

```text
CostModel
```

quyết định.

---

# 53. Cost model

Target cần:

```text
TargetCostModel {
    latency(op)
    throughput(op)
    code_size(op)
    register_pressure(op)
    branch_cost
    load_cost
    store_cost
}
```

Không cần chính xác tuyệt đối ở v1.

---

# 54. Code-size mode

`-Os` / `-Oz` có thể chọn:

```text
smaller instruction
```

thay vì nhanh hơn.

Ví dụ:

```text
branch
```

thay vì sequence lớn.

---

# 55. Register pressure hint

Instruction selector nên expose:

```text
register pressure
```

để tránh tạo sequence khiến allocator spill quá nhiều.

Đặc biệt:

```text
large constants
vector operations
multi-register arithmetic
```

---

# 56. x86-64 backend MVP

Tôi đề xuất thứ tự instruction support:

### Integer

```text
MOV
LEA
ADD
SUB
ADC
SBB
IMUL
MUL
IDIV
DIV
NEG
NOT
AND
OR
XOR
SHL
SHR
SAR
ROL
ROR
```

### Compare/control

```text
CMP
TEST
SETcc
Jcc
JMP
CALL
RET
CMOVcc
```

### Memory

```text
MOV load/store
MOVZX
MOVSX
```

### Floating

```text
MOVSS
MOVSD
ADDSS
ADDSD
SUBSS
SUBSD
MULSS
MULSD
DIVSS
DIVSD
```

Sau đó:

```text
SSE2
SSE4.1
AVX
AVX2
AVX-512
```

---

# 57. AArch64 MVP

```text
MOV
ADD
SUB
MUL
SDIV
UDIV
AND
ORR
EOR
LSL
LSR
ASR
CMP
CSEL
B
B.cond
BL
RET
LDR
STR
```

sau đó:

```text
NEON
SVE
LSE atomics
```

---

# 58. RISC-V MVP

Base:

```text
RV64I
```

sau đó:

```text
M
A
F
D
C
V
```

tùy target.

Không ép vector extension vào base backend.

---

# 59. WASM không nên giả lập Machine IR x86

WASM là backend khác biệt:

```text
LIR
 ↓
Wasm Machine IR
 ↓
Wasm binary
```

WASM có:

- stack machine;
- locals;
- structured control flow;
- linear memory.

Do đó không nên ép WASM thành:

```text
virtual registers
```

rồi giả vờ giống x86.

Machine IR abstraction phải cho phép backend-specific model.

---

# 60. Đây là một chỉnh sửa quan trọng

MACHINE-IR hiện tại đã định nghĩa virtual registers, nhưng cần bổ sung:

> **Machine IR là target-machine semantic representation, không bắt buộc mọi target phải có cùng execution model.**

Với x86/AArch64/RISC-V:

```text
register-machine
```

Với WASM:

```text
stack/local-machine
```

Do đó:

```text
MachineIRModel =
    RegisterMachine
    | StackMachine
    | Hybrid
```

---

# 61. Encoder không biết semantics

Sau selection:

```text
Machine IR
```

encoder chỉ encode:

```text
opcode
operands
registers
immediates
relocations
```

Không kiểm tra ownership.

---

# 62. Machine verifier

Trước encoding phải kiểm tra:

```text
physical register validity
register class
operand constraints
fixed registers
tied operands
early clobbers
memory operand
features
CFG
ABI
```

---

# 63. Fixed registers

Ví dụ x86 division:

```text
RAX
RDX
```

Machine instruction descriptor:

```text
implicit_uses
implicit_defs
```

để allocator biết.

---

# 64. Tied operands

CAS:

```text
expected
desired
memory
```

có thể có constraints.

Machine descriptor biểu diễn:

```text
tied operand
```

không hardcode trong allocator.

---

# 65. Early clobber

Một số instructions:

```text
```

ghi output trước khi đọc hết input.

Machine descriptor phải có:

```text
early_clobber
```

để tránh register allocation sai.

---

# 66. Register units

x86:

```text
RAX
EAX
AX
AL
```

không phải bốn register độc lập.

Machine backend dùng:

```text
RegisterUnits
```

để biểu diễn alias.

---

# 67. Partial register semantics

Ví dụ:

```text
write EAX
```

zero-extends lên RAX.

Trong khi:

```text
write AX
```

không.

Đây phải là machine semantics rõ ràng.

---

# 68. Target features

Machine instruction:

```text
required_features = AVX2
```

Machine verifier kiểm tra:

```text
available_features ⊇ required_features
```

Nếu không:

```text
compile diagnostic
```

không tạo binary sai.

---

# 69. Instruction selector fallback

Ví dụ:

```text
vector_add
```

Target không có AVX2:

```text
vector expansion
```

hoặc:

```text
scalar expansion
```

Nếu feature profile yêu cầu AVX2 nhưng CPU target không có:

```text
diagnostic
```

---

# 70. Runtime helper ABI

Nếu operation cần compiler helper:

```text
__axiom_div_i128
```

helper cũng phải có:

```text
Axiom internal ABI
```

hoặc target ABI phù hợp.

Helper không phải magic compiler feature.

---

# 71. Helper có thể được link statically

Final architecture:

```text
Axiom compiler
+
Axiom runtime/helper archive
```

hoặc compiler trực tiếp emit function.

Nếu helper không được dùng:

```text
không link
```

---

# 72. Runtime-free

Ví dụ chương trình:

```axiom
fn main() {
    let x = 1 + 2;
}
```

không cần:

```text
thread runtime
GC
async runtime
allocator
panic runtime
```

Nếu target code không cần.

---

# 73. Panic helper demand-driven

Nếu:

```text
panic=abort
```

thì binary có thể chỉ cần:

```text
__axiom_panic_abort
```

hoặc inline trap/syscall/OS termination.

Nếu program không panic:

```text
dead code elimination
```

có thể remove helper.

---

# 74. Stack probing

Large stack allocation:

```text
STACK_ALLOC_DYNAMIC
```

target ABI/security layer có thể yêu cầu stack probing.

Legalizer/frame lowering phối hợp.

Không phải generic LIR instruction.

---

# 75. TLS

TLS access cũng target-specific.

LIR:

```text
TLS_ADDRESS symbol
```

Machine backend:

```text
FS/GS
TLS relocation
TPIDR
TLS descriptor
...
```

tùy target.

---

# 76. PIC/PIE

LIR có:

```text
SymbolRef
RelocationKind
```

Machine/object layer quyết định:

```text
RIP-relative
GOT
PLT
ADR/ADRP
...
```

Không hardcode ELF behavior vào selector.

---

# 77. Instruction selection + linker

Selector chỉ tạo relocation-aware Machine IR.

Ví dụ:

```text
CALL external_symbol
```

→ machine instruction + relocation.

Object writer/linker xử lý relocation.

---

# 78. Backend interface

Tôi chốt:

```text id="e6xxj5"
TargetBackend {
    target_info()
    legalizer()
    instruction_selector()
    register_info()
    frame_lowering()
    asm_encoder()
    object_writer()
}
```

và:

```text id="3k5j5c"
Legalizer {
    legalize_type()
    legalize_operation()
    legalize_memory()
    legalize_atomic()
    legalize_vector()
}
```

---

# 79. Backend directory

```text id="a3m4k7"
compiler/machine/
├── generic/
│   ├── machine_ir/
│   ├── verifier/
│   └── pattern/
│
├── x86_64/
│   ├── target/
│   ├── registers/
│   ├── legalize/
│   ├── select/
│   ├── patterns/
│   ├── instructions/
│   ├── encoding/
│   └── abi/
│
├── aarch64/
├── riscv64/
└── wasm/
```

---

# 80. Bootstrap target

Không nên làm cả bốn target cùng lúc.

Thứ tự:

```text
1. x86_64 Linux
2. x86_64 Windows
3. AArch64 Linux
4. AArch64 macOS/iOS
5. RISC-V64
6. WASM32
```

x86-64 Linux là vertical slice đầu tiên.

---

# 81. Test architecture

Mỗi instruction:

```text
semantic test
→ LIR test
→ Machine IR test
→ encoding test
```

Ví dụ:

```text
i64 add
```

phải test:

```text
source result
MIR result
LIR
Machine IR
machine bytes
```

---

# 82. Encoding golden tests

Ví dụ Machine IR:

```text
ADD RAX, RBX
```

expected:

```text
machine bytes
```

Golden test.

Nhưng không nên phụ thuộc byte sequence trong semantic tests.

---

# 83. Differential backend test

Trong bootstrap, có thể:

```text
Axiom LIR
→ Axiom x86 backend
```

so sánh với:

```text
reference backend / temporary LLVM
```

nhưng chỉ để kiểm tra:

```text
result
ABI
edge cases
```

LLVM **không trở thành dependency kiến trúc**.

---

# 84. Fuzzing

Đây là phase rất phù hợp để fuzz.

Pipeline:

```text
random source
 ↓
parser
 ↓
typed MIR
 ↓
optimizer
 ↓
legalizer
 ↓
machine
 ↓
execute
```

so sánh với:

```text
MIR interpreter
```

Đặc biệt fuzz:

- integer overflow;
- shifts;
- division;
- enum;
- aggregate return;
- atomic;
- alias;
- weird control flow.

---

# 85. Backend invariant set

Chốt:

```text id="z4l8p0"
ALGL-20  Legalization Preserves Semantics
ALGL-21  Legalization Is Deterministic
ALGL-22  Unsupported Operations Are Explicitly Expanded Or Rejected
ALGL-23  Runtime Helpers Are Optional
ALGL-24  Runtime Helpers Do Not Require Foreign Compilers
ALGL-25  Integer Semantics Are Preserved
ALGL-26  Floating Semantics Are Preserved
ALGL-27  Overflow Semantics Are Preserved
ALGL-28  Divide-By-Zero Semantics Are Preserved
ALGL-29  Shift Semantics Are Preserved
ALGL-30  Atomic Ordering Is Preserved
ALGL-31  Volatile Semantics Are Preserved
ALGL-32  Address-Space Semantics Are Preserved
ALGL-33  Alignment Requirements Are Preserved
ALGL-34  Vector Semantics Are Preserved
ALGL-35  Target Features Are Explicit
ALGL-36  Unsupported Target Features Produce Diagnostics
ALGL-37  Generic LIR Does Not Depend On Physical Registers
ALGL-38  Generic LIR Does Not Depend On Target Flags
ALGL-39  Generic LIR Does Not Depend On Target Addressing Modes
ALGL-40  Instruction Selection Is Target Specific
ALGL-41  Instruction Patterns Are Declarative Where Practical
ALGL-42  Instruction Selection Preserves ABI Requirements
ALGL-43  Fixed Register Constraints Are Explicit
ALGL-44  Tied Operands Are Explicit
ALGL-45  Early Clobbers Are Explicit
ALGL-46  Register Aliases Are Explicit
ALGL-47  Partial Register Semantics Are Explicit
ALGL-48  Machine IR Is Verifiable Before Allocation
ALGL-49  Machine IR Contains No Unresolved Generic Type Semantics
ALGL-50  Machine IR Contains No Ownership Verification Responsibility
ALGL-51  Machine IR Contains No Trait Resolution Responsibility
ALGL-52  Machine IR Contains No Async Semantic Responsibility
ALGL-53  Runtime Helpers Are Demand Driven
ALGL-54  Internal Helpers Have Explicit ABI
ALGL-55  Constant Materialization Is Target Specific
ALGL-56  Address Folding Is Target Specific
ALGL-57  Atomic Lowering Is Target Specific
ALGL-58  Vector Legalization Is Target Specific
ALGL-59  WASM May Use A Different Machine Execution Model
ALGL-60  Backend Does Not Require LLVM
ALGL-61  Backend Does Not Require An External Assembler
ALGL-62  Backend Does Not Require A Foreign Linker In Final Architecture
ALGL-63  Machine Encoding Is Deterministic
ALGL-64  Target Backend Can Be Tested Against MIR Semantics
```

---

# 86. Điểm cần sửa nhẹ trong kiến trúc trước

Có một điều tôi muốn **chốt lại rõ hơn** so với MACHINE-IR-002:

### Machine IR không nên bị ép thành một IR giống nhau cho mọi ISA.

Đúng hơn:

```text
LIR
 │
 ├── Register-machine backend
 │      ├── x86-64
 │      ├── AArch64
 │      └── RISC-V
 │
 └── Stack/structured backend
        └── WASM
```

Nhưng interface chung vẫn là:

```text
MachineIR
MachineVerifier
Register/Operand model
Encoding
Object
```

Đối với WASM, một số phase như register allocation sẽ được thay bằng:

```text
local allocation
stackification
structured CFG lowering
```

Đây là cách tránh việc kiến trúc Axiom bị “x86 hóa”.

---

# 87. Và đây là điểm rất quan trọng với mục tiêu không phụ thuộc LLVM

Axiom lúc này đã có đủ tầng để **tự trở thành một compiler thực sự**:

```text
Parser
   ↓
Type system
   ↓
Ownership
   ↓
MIR
   ↓
Optimizer
   ↓
Layout
   ↓
ABI
   ↓
LIR
   ↓
Legalizer
   ↓
Instruction Selector
   ↓
Machine IR
   ↓
Register Allocation
   ↓
Encoder
   ↓
Object Writer
   ↓
Linker
```

LLVM chỉ còn là **công cụ tham chiếu trong bootstrap**, không còn là một “cái lõi bị phụ thuộc”.

---

## Bước tiếp theo: **COMPILER-010 — Register Allocation + Spill/Reload + Frame Integration**

Đây sẽ là phase cuối cùng trước khi Axiom thực sự có thể biến Machine IR thành mã máy hoàn chỉnh.

Ta sẽ chốt:

```text
Virtual Registers
      ↓
Register Classes
      ↓
Liveness
      ↓
Interference
      ↓
Linear Scan MVP
      ↓
Register Assignment
      ↓
Spill
      ↓
Reload
      ↓
Rematerialization
      ↓
Register Coalescing
      ↓
Physical Machine IR
      ↓
Final Frame Layout
      ↓
Prologue/Epilogue
```

Đặc biệt cần thiết kế sao cho **MVP có thể rất đơn giản nhưng sau này nâng từ Linear Scan lên Greedy/Graph Coloring mà không phải viết lại toàn bộ backend**.