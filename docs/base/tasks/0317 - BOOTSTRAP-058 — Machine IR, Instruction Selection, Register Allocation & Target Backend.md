Tiếp tục.

# BOOTSTRAP-058 — Machine IR, Instruction Selection, Register Allocation & Target Backend

058 là bước cuối của chuỗi **semantic → native code**. Nếu 057 trả lời *“function được truyền/nhận như thế nào qua ABI?”*, thì 058 trả lời:

> **“Làm thế nào biến Axiom LIR thành đúng machine instructions, đúng register, đúng stack và đúng binary?”**

Mục tiêu đầu tiên nên là **x86-64 + AArch64 + RISC-V64**, sau đó mở rộng các target khác.

---

# 1. Kiến trúc backend

Pipeline hoàn chỉnh:

```text
Verified MIR
      ↓
   OptIR / SSA
      ↓
   ABI MIR
      ↓
  Axiom LIR
      ↓
 ┌───────────────────────┐
 │    Target Backend     │
 │                       │
 │ Legalization          │
 │ Instruction Selection │
 │ Register Allocation   │
 │ Stack Frame           │
 │ Scheduling             │
 │ Peephole              │
 │ Encoding              │
 └───────────┬───────────┘
             ↓
        Machine IR
             ↓
        Machine Code
```

---

# 2. Machine IR

Machine IR phải khác LIR.

LIR vẫn machine-independent:

```text
add i32
load
store
call
branch
```

Machine IR biết:

```text
x86:
rax
rbx
xmm0
rsp
rflags
```

hoặc:

```text
ARM64:
x0
x1
v0
sp
nzcv
```

---

# 3. Machine register model

Backend không hard-code register vào optimizer.

Mỗi target cung cấp:

```text
RegisterFile {
    physical_registers
    register_classes
    aliases
    reserved_registers
    caller_saved
    callee_saved
    special_registers
}
```

---

# 4. Register classes

Ví dụ x86-64:

```text
GPR64
GPR32
XMM
YMM
ZMM
FLAGS
```

AArch64:

```text
GPR64
GPR32
FP32
FP64
SIMD128
```

RISC-V:

```text
GPR
FPR
Vector
```

---

# 5. Virtual registers

Trước register allocation:

```text
v0
v1
v2
```

thay vì:

```text
rax
rbx
```

Điều này giúp instruction selection và optimization đơn giản hơn.

---

# 6. Physical register allocation

Sau đó:

```text
v0 → rax
v1 → rcx
v2 → rdx
```

hoặc spill:

```text
v3 → [rsp+32]
```

---

# 7. Register allocation không nên là một pass “ngây thơ”

Đề xuất:

```text
Liveness
   ↓
Interference
   ↓
Register class constraints
   ↓
Allocation
   ↓
Spill
   ↓
Reload
   ↓
Reallocation
```

---

# 8. Linear scan vs graph coloring

Axiom nên hỗ trợ cả hai.

### Fast compile

```text
Linear Scan
```

### Maximum optimization

```text
Graph/priority-based allocator
```

Ban đầu có thể dùng:

```text
Linear Scan
```

và nâng cấp allocator sau.

---

# 9. Spill cost

Compiler không chỉ chọn register bất kỳ.

Cost dựa trên:

```text
use frequency
loop depth
register pressure
instruction constraints
rematerialization cost
```

Một value dùng trong hot loop nên tránh spill.

---

# 10. Rematerialization

Ví dụ:

```text
x = constant 42
```

Nếu register pressure cao, thay vì:

```text
store 42 → stack
load stack
```

compiler có thể tạo lại:

```text
mov reg, 42
```

---

# 11. Instruction selection

LIR:

```text
x = a + b
```

x86:

```text
add
```

ARM64:

```text
add
```

RISC-V:

```text
add
```

Nhưng pattern không đơn giản chỉ là mapping 1:1.

---

# 12. Addressing modes

Ví dụ x86:

```text
load [base + index*scale + displacement]
```

Một biểu thức:

```text
a[i]
```

có thể hạ thành **một memory operand** thay vì:

```text
multiply
add
load
```

nếu target hỗ trợ.

---

# 13. Target-specific instruction combining

Ví dụ:

```text
base + index * 8
```

x86 có thể combine thành:

```text
[base + index*8]
```

ARM/RISC-V có addressing modes khác.

Do đó Machine IR phải giữ đủ thông tin để legalization.

---

# 14. Instruction legalization

Một LIR operation có thể không tồn tại trên target.

Ví dụ:

```text
i128_add
```

trên target không có native i128.

Lower:

```text
low64
high64
ADC
```

hoặc sequence tương đương.

---

# 15. Multi-register values

Một type có thể cần:

```text
rax:low
rdx:high
```

ABI/Codegen phải hiểu value location có thể là:

```text
Register
RegisterPair
Stack
Memory
```

---

# 16. Wide integer

Axiom có thể hỗ trợ `i128/u128` về sau.

Trên x86-64:

```text
128-bit
```

có thể dùng:

```text
rax:rdx
```

hoặc stack tùy context.

Không cần CPU native i128 để language support i128.

---

# 17. Floating point

Machine backend phải phân biệt:

```text
f32
f64
```

với:

```text
integer bits
```

`bitcast` có semantics riêng nhưng backend có thể sử dụng move instruction tương ứng.

---

# 18. NaN semantics

Nếu Axiom không bật fast-math:

```text
NaN
-0
Infinity
```

phải được bảo toàn theo floating semantics đã định nghĩa.

Không được tự động áp dụng:

```text
x + 0 == x
```

nếu semantics không đảm bảo điều đó.

---

# 19. Fast-math

Không nên có:

```text
-O3 = fast math
```

Đây là sai.

Fast-math phải là **explicit semantic/optimization contract** nếu Axiom sau này hỗ trợ.

---

# 20. SIMD lowering

Vector type:

```text
Vec<f32, 8>
```

có thể lower:

```text
AVX2 ymm
```

hoặc:

```text
NEON
```

hoặc scalar fallback.

---

# 21. Portable SIMD

Axiom nên phân biệt:

```text
portable vector semantics
```

với:

```text
target intrinsic
```

Ví dụ:

```text
simd<f32, 8>
```

là abstraction.

Compiler chọn:

```text
AVX2
AVX-512
SVE
RVV
scalar
```

---

# 22. Explicit intrinsic

System layer vẫn cho phép:

```text
x86::_mm256_...
arm::...
riscv::...
```

nhưng đây là target-specific.

---

# 23. Vector register pressure

Vector registers phải được tính vào allocator:

```text
GPR pressure
FP/SIMD pressure
```

đồng thời.

---

# 24. Instruction scheduling

Sau register allocation, compiler có thể reorder instructions để:

```text
hide latency
maximize throughput
reduce stalls
```

nhưng phải preserve:

```text
memory semantics
atomic ordering
volatile
observable effects
```

---

# 25. Dependency graph

Scheduler tạo:

```text
Instruction DAG
```

với dependency:

```text
RAW
WAR
WAW
Memory dependency
Control dependency
```

---

# 26. CPU model

Target configuration nên chứa:

```text
CPUModel {
    architecture
    microarchitecture
    features
    latency
    throughput
    scheduling_model
    cache_preferences
}
```

Không cần chính xác tuyệt đối cho mọi CPU; backend có thể dùng generic model.

---

# 27. Generic target

Ví dụ:

```text
x86-64-v2
x86-64-v3
x86-64-v4
arm64
rv64gc
```

là baseline target profiles.

Sau đó:

```text
-march=native
```

có thể bật feature phù hợp.

---

# 28. Stack frame

Function có:

```text
locals
spills
saved registers
outgoing args
alignment
dynamic allocations
```

Compiler tính:

```text
FrameLayout
```

---

# 29. Stack allocation

Local:

```axiom id="6n9w6n"
let x = Point(...)
```

không nhất thiết tạo stack slot.

Nếu scalarizable:

```text
x.x → register
x.y → register
```

---

# 30. Stack slot chỉ tồn tại khi cần

Ví dụ:

```text
address_of(x)
```

làm địa chỉ observable.

Khi đó compiler phải tạo storage thật.

Đây là sự kết hợp trực tiếp giữa:

```text
semantic address observability
```

và:

```text
Machine frame allocation
```

---

# 31. Stack alignment

Backend phải đảm bảo target ABI:

```text
SP alignment
call alignment
local alignment
```

đúng tại mọi call site.

---

# 32. Red zone

x86-64 target ABI có thể hỗ trợ red zone.

Backend có thể tận dụng nếu:

```text
ABI permits
target configuration permits
```

Không biến nó thành language semantic.

---

# 33. Prologue / epilogue

Compiler tạo:

```text
push/save
frame setup
...
restore
return
```

nhưng có thể optimize thành:

```text
leaf function
```

không cần frame.

---

# 34. Leaf optimization

```text
fn add(a,b)
```

nếu không call function khác và không cần stack:

```text
add
ret
```

cực kỳ nhỏ.

---

# 35. Tail calls

Nếu semantic + ABI cho phép:

```text
call f
return
```

→

```text
jump f
```

không tạo stack frame mới.

---

# 36. Tail-call legality

Phải kiểm tra:

```text
return ABI compatible
argument locations compatible
stack state compatible
callee/caller ABI
unwind constraints
```

---

# 37. Calling convention lowering

057 tạo:

```text
AbiArg
AbiReturn
```

058 biến chúng thành:

```text
physical registers
stack slots
moves
```

Ví dụ conceptual:

```text
arg0 → rdi
arg1 → rsi
return → rax
```

với SysV x86-64.

---

# 38. Caller/callee saved

Backend ABI table quy định:

```text
caller-saved
callee-saved
```

Allocator phải biết.

---

# 39. Register save optimization

Không nên save tất cả callee-saved registers.

Chỉ save register thực sự sử dụng.

---

# 40. Shrink wrapping

Nếu function chỉ dùng một callee-saved register ở cold path:

```text
save/restore
```

có thể đưa gần path sử dụng.

Đây là optimization nâng cao.

---

# 41. Stack maps

GC không tồn tại trong Core nên Axiom **không cần stack maps cho GC**.

Nhưng stack maps vẫn có thể cần cho:

```text
debugging
unwinding
async runtime
exception/unwind profiles
sanitizers
```

chỉ khi component cần.

---

# 42. Unwind information

Native object có thể chứa:

```text
DWARF CFI
Windows unwind info
Mach-O unwind info
```

nếu panic/unwind/debug configuration yêu cầu.

---

# 43. Không có unwind machinery mặc định

Freestanding:

```text
panic = abort
```

có thể không cần unwinder.

Binary nhỏ hơn.

---

# 44. Debug info

Backend tạo mapping:

```text
source span
 ↓
MIR
 ↓
OptIR
 ↓
Machine instruction
```

để debugger biết:

```text
breakpoint
line
variable
function
```

---

# 45. Debug vs optimization

Optimized code có thể:

```text
variable eliminated
function inlined
instruction reordered
```

Debug info phải phản ánh thực tế, không giả vờ rằng machine code vẫn giống source.

---

# 46. DWARF

Linux/ELF có thể dùng:

```text
DWARF
```

Windows:

```text
CodeView/PDB
```

macOS:

```text
DWARF
```

WASM:

```text
DWARF/source map tùy toolchain
```

---

# 47. Machine instruction encoder

Không nên phụ thuộc assembler ngoài production.

Backend cần:

```text
Encoder {
    encode(instruction)
    encode_operands()
    emit_relocation()
}
```

---

# 48. x86 encoder

Phải xử lý:

```text
prefix
REX
VEX
EVEX
opcode
ModRM
SIB
displacement
immediate
```

Đây là phần code tương đối lớn nhưng hoàn toàn có thể self-host.

---

# 49. AArch64 encoder

Instruction thường fixed-width 32-bit.

Điều này làm encoder đơn giản hơn x86.

---

# 50. RISC-V encoder

Cũng tương đối modular:

```text
R
I
S
B
U
J
```

và extensions.

---

# 51. Relocation emission

Ví dụ:

```text
call foo
```

nếu `foo` ở object khác:

```text
machine instruction
+
relocation(foo)
```

ObjectWriter xử lý tiếp.

---

# 52. Branch relaxation

Một branch ban đầu:

```text
short jump
```

có thể không đủ range.

Backend cần:

```text
branch relaxation
```

→ long jump sequence.

---

# 53. Constant pool

Một số target cần:

```text
literal pools
jump tables
constant islands
```

Backend phải quản lý.

---

# 54. Jump tables

`match` hoặc switch:

```text
switch x
```

có thể lower thành:

```text
jump table
```

nếu density phù hợp.

Nếu sparse:

```text
binary search
decision tree
```

---

# 55. Pattern matching → machine code

Pipeline:

```text
match
 ↓
decision tree
 ↓
CFG
 ↓
OptIR
 ↓
switch/jumps
 ↓
machine
```

Không cần runtime pattern engine.

---

# 56. Bounds checks

Nếu 056 đã prove:

```text
i < len
```

Machine backend không tạo check.

Nếu chưa prove:

```text
compare
conditional branch
panic path
```

---

# 57. Panic cold path

Có thể tạo:

```text
hot:
    ...
    jmp continue

cold:
    panic_bounds()
```

và đặt cold section xa hot code.

---

# 58. Code layout

Compiler/linker có thể tối ưu:

```text
hot code
cold code
unlikely error paths
```

để tăng instruction-cache locality.

---

# 59. Function ordering

PGO có thể sắp xếp:

```text
hot functions together
```

giảm I-cache/TLB misses.

---

# 60. Link-time optimization

Machine backend có thể giữ enough metadata để LTO:

```text
inline
constant fold
function reorder
dead strip
```

sau module compilation.

---

# 61. Axiom LIR nên giữ target-neutral

Ví dụ:

```text
LIR_ADD
LIR_LOAD
LIR_STORE
LIR_BRANCH
LIR_CALL
```

không:

```text
X86_ADD_RAX_RBX
```

Target-specific chỉ xuất hiện từ Machine IR.

---

# 62. Legalization boundary

```text
Axiom LIR
    ↓
Target Legalization
    ↓
Machine IR
```

Ví dụ:

```text
128-bit add
```

có thể trở thành:

```text
ADD low
ADC high
```

---

# 63. Machine IR vẫn cần SSA-like form?

Có thể giữ virtual registers ở Machine IR trước allocation:

```text
vreg
```

Sau allocation:

```text
physreg/stack
```

Điều này giúp backend modular hơn.

---

# 64. Phi elimination

SSA:

```text
v3 = phi(v1, v2)
```

trước register allocation cần chuyển thành:

```text
parallel_copy
```

tại predecessor.

Sau đó resolve parallel copies.

---

# 65. Parallel copy

Ví dụ:

```text
r1 ← r2
r2 ← r1
```

không thể thực hiện tuần tự đơn giản.

Có thể cần:

```text
tmp
```

Backend phải giải quyết cycle.

---

# 66. Register coalescing

Nếu:

```text
v1 = v2
```

và không conflict:

```text
v1
v2
```

có thể cùng physical register.

→ loại bỏ move.

---

# 67. Copy propagation

Machine-level:

```text
mov rax, rbx
add rax, rcx
```

có thể tránh move nếu allocator đặt value trực tiếp vào `rax`.

---

# 68. Peephole optimization

Cuối backend có:

```text
Machine peephole
```

ví dụ:

```text
mov rax, 0
```

→ target-specific zero idiom.

Nhưng phải bảo toàn flags semantics.

---

# 69. Instruction flags

Đây là vấn đề quan trọng trên x86.

```text
add
```

có thể thay đổi FLAGS.

Nếu FLAGS không được sử dụng:

```text
```

optimizer có thể chọn sequence khác.

Nếu branch phụ thuộc FLAGS:

```text
```

phải preserve.

Machine IR cần model implicit register dependencies.

---

# 70. Implicit operands

Instruction:

```text
idiv
```

có implicit:

```text
rax
rdx
```

Machine IR phải biết.

Không thể coi instruction chỉ có explicit operands.

---

# 71. Calling instruction effects

`call` có thể:

```text
clobber caller-saved registers
modify memory
modify flags
```

ABI model phải encode điều này.

---

# 72. Inline assembly

`asm` unsafe/system phải khai báo:

```text
inputs
outputs
clobbers
memory effects
```

Nếu khai báo sai:

> programmer chịu trách nhiệm unsafe contract.

Nhưng compiler vẫn không được giả định những register/memory effects không được phép bỏ qua.

---

# 73. Interrupt/naked functions

`@interrupt`, `@naked` là system-level.

Backend phải cho phép custom prologue/epilogue khi target ABI yêu cầu.

Nhưng các function này không được đi qua pipeline ordinary như function bình thường nếu contract khác.

---

# 74. Kernel backend

`@kernel` không phải CPU function bình thường.

Pipeline:

```text
Axiom LIR
 ↓
GPU Machine IR
 ↓
GPU ISA
```

với:

```text
address spaces
thread IDs
barriers
GPU calling convention
```

---

# 75. Nhưng semantic front-end vẫn dùng chung

Đây là điểm đã freeze:

```text
Axiom source
      ↓
same parser/type system/MIR/verifier
      ↓
CPU backend
GPU backend
```

Không tạo “GPU language” thứ hai.

---

# 76. Backend interface

Nên có abstraction:

```text
TargetBackend {
    target_info()
    abi()
    legalize()
    select_instructions()
    allocate_registers()
    lower_frame()
    schedule()
    encode()
    emit_object()
}
```

Không để frontend biết x86/ARM details.

---

# 77. Target-independent backend tests

Có test:

```text
LIR → expected semantic Machine behavior
```

không nhất thiết hard-code register.

Target tests riêng:

```text
x86 encoding
ARM encoding
RISC-V encoding
```

---

# 78. Golden machine-code tests

Ví dụ:

```text
source
 ↓
expected bytes
```

dùng cho encoder.

Rất hữu ích để phát hiện regression.

---

# 79. Differential testing

Trong bootstrap:

```text
Axiom backend
vs
LLVM backend
```

có thể so sánh:

```text
program output
ABI behavior
edge cases
```

Không nhất thiết machine code giống nhau.

---

# 80. Self-host transition

Roadmap:

```text
Phase 1
Axiom frontend
→ LLVM
```

```text
Phase 2
Axiom frontend
→ Axiom LIR
→ external backend
```

```text
Phase 3
Axiom LIR
→ Axiom Machine IR
→ own encoder
```

```text
Phase 4
own ObjectWriter
→ own Linker
```

```text
Phase 5
compiler itself written in Axiom
```

---

# 81. Bootstrap compiler

Compiler đầu tiên có thể viết bằng:

```text
Rust/C++/whatever bootstrap implementation
```

Nhưng cuối cùng:

```text
axiomc
```

được build bởi:

```text
axiomc
```

Đó mới là self-hosting.

---

# 82. Self-hosting không đồng nghĩa “không bao giờ dùng tool ngoài”

Axiom có thể dùng:

```text
system linker
debugger
OS SDK
GPU driver
```

khi mục tiêu là interoperability.

Nhưng **compiler semantic/codegen core không phụ thuộc compiler khác**.

---

# 83. Native target priority

Tôi đề xuất thứ tự:

```text
1. x86-64 Linux
2. x86-64 Windows
3. AArch64 Linux/macOS
4. AArch64 Windows
5. RISC-V64
6. WASM
7. iOS/Android packaging
```

Lý do là 3 kiến trúc đầu tiên cung cấp coverage rất tốt cho backend architecture.

---

# 84. Không nên hỗ trợ quá nhiều ISA ngay

Backend đầu tiên cần:

```text
x86-64
AArch64
RISC-V64
```

nhưng architecture phải pluginized để sau này thêm:

```text
ARM32
WASM
PowerPC
LoongArch
MIPS
```

không phải sửa compiler frontend.

---

# 85. Machine backend invariant

Một nguyên tắc quan trọng:

> **Machine backend không được hiểu Axiom semantics.**

Nó chỉ nhận:

```text
verified ABI/LIR
```

và biến thành machine code.

Nếu backend bắt đầu tự quyết định:

```text
ownership
Drop
Send
view
```

thì architecture đã sai tầng.

---

# 86. Frozen invariants — BOOTSTRAP-058

```text
AMACH-20   Machine IR is target-specific and follows Axiom LIR lowering.
AMACH-21   Axiom LIR remains target-independent.
AMACH-22   Machine IR may use virtual registers before physical allocation.
AMACH-23   Physical register allocation occurs after target instruction constraints are known.
AMACH-24   Register classes are target-defined.
AMACH-25   Caller-saved and callee-saved registers are defined by the target ABI.
AMACH-26   Register allocation preserves ABI requirements.
AMACH-27   Register allocation preserves program semantics.
AMACH-28   Spill locations are represented explicitly.
AMACH-29   Spill and reload operations preserve value semantics.
AMACH-30   Rematerialization is permitted when semantic results are unchanged.
AMACH-31   Instruction selection may use target-specific addressing modes.
AMACH-32   Instruction selection may combine multiple LIR operations into one instruction.
AMACH-33   Instruction legalization expands unsupported operations into valid target sequences.
AMACH-34   Legalization preserves integer and floating-point semantics.
AMACH-35   Wide values may occupy multiple machine registers or memory locations.
AMACH-36   Function arguments and returns follow the ABI classification established by ABI MIR.
AMACH-37   Calling conventions are explicit machine backend contracts.
AMACH-38   Function calls model required register and memory clobbers.
AMACH-39   Implicit machine operands are explicitly modeled.
AMACH-40   Machine flags/register state is modeled when observable by subsequent instructions.
AMACH-41   Instruction scheduling preserves data, memory and control dependencies.
AMACH-42   Instruction scheduling preserves atomic and volatile semantics.
AMACH-43   Instruction scheduling cannot reorder operations across forbidden synchronization boundaries.
AMACH-44   Stack frame layout is target and ABI dependent.
AMACH-45   Local values do not require physical stack slots unless semantics or register pressure require them.
AMACH-46   Observable addresses require real addressable storage.
AMACH-47   Register allocation may eliminate semantically unnecessary moves.
AMACH-48   Phi nodes are eliminated before final machine code generation.
AMACH-49   Parallel copies are resolved correctly across register-allocation boundaries.
AMACH-50   Register coalescing may eliminate redundant copies.
AMACH-51   Leaf functions may omit unnecessary stack frames.
AMACH-52   Prologue and epilogue generation follows target ABI requirements.
AMACH-53   Only actually used callee-saved registers need preservation.
AMACH-54   Tail calls require ABI-compatible conditions.
AMACH-55   Branch relaxation preserves control-flow semantics.
AMACH-56   Jump tables are optional implementation strategies for multi-way control flow.
AMACH-57   Machine-level bounds checks are emitted only when semantic proof has not eliminated them.
AMACH-58   Panic/error paths may be placed in cold code sections.
AMACH-59   Debug information maps source semantics to generated machine locations.
AMACH-60   Debug information does not alter program semantics.
AMACH-61   Native unwind information is emitted only when the selected profile requires it.
AMACH-62   Freestanding abort-only programs need not contain unwind machinery.
AMACH-63   Machine encoders are target-specific.
AMACH-64   Production Axiom toolchains are intended to provide native instruction encoding.
AMACH-65   Object emission is separate from instruction encoding.
AMACH-66   Relocations are represented explicitly before final link resolution.
AMACH-67   Machine code generation may emit target-specific relocations.
AMACH-68   Peephole optimization must preserve machine-visible flags and dependencies.
AMACH-69   Fast-math transformations are not implied by ordinary optimization levels.
AMACH-70   Floating-point transformations must preserve the selected floating-point semantic profile.
AMACH-71   SIMD lowering may select native vector instructions or scalar fallback.
AMACH-72   Portable SIMD semantics are distinct from target-specific intrinsics.
AMACH-73   Target features constrain legal instruction selection.
AMACH-74   Backend target configuration is explicit and deterministic.
AMACH-75   Machine backend does not reinterpret ownership semantics.
AMACH-76   Machine backend does not reinterpret capability semantics.
AMACH-77   Machine backend does not introduce mandatory runtime machinery solely because of source abstractions.
AMACH-78   GPU backends consume verified Axiom IR rather than a separate source language.
AMACH-79   CPU and GPU backend details remain isolated after common semantic verification.
AMACH-80   Inline assembly declares required operands and clobbers.
AMACH-81   Unsafe inline assembly cannot silently invalidate unrelated compiler invariants.
AMACH-82   Interrupt/naked functions use explicit system-level ABI contracts.
AMACH-83   Target-specific register and instruction details do not leak into ordinary language semantics.
AMACH-84   Machine backend output must preserve ABI contracts.
AMACH-85   Machine backend output must preserve representation contracts.
AMACH-86   Machine backend output must preserve memory-model semantics.
AMACH-87   Machine backend output must preserve observable Drop behavior.
AMACH-88   Machine backend output must preserve panic behavior under the selected profile.
AMACH-89   Machine backend output must preserve FFI calling and ownership contracts.
AMACH-90   Machine backend transformations are deterministic for a fixed target/configuration.
AMACH-91   Backend optimizations may use PGO data but cannot override semantic constraints.
AMACH-92   Backend correctness is testable independently of frontend syntax.
AMACH-93   Instruction encoders support golden-byte regression tests.
AMACH-94   Bootstrap external backends may be used without becoming language semantic dependencies.
AMACH-95   Long-term native code generation does not require LLVM or another external compiler backend.
```

---

# Axiom đã đi đến một mốc rất quan trọng

Nếu ghép 055–058:

```text
                 AXIOM SOURCE
                      │
                      ▼
               Semantic Compiler
                      │
              ┌───────┴───────┐
              │               │
         Ownership         Capability
         Lifetime          Concurrency
         Drop              Async/GPU
              │               │
              └───────┬───────┘
                      ▼
                 VERIFIED MIR
                      │
                      ▼
                    OptIR
              ┌───────┼────────┐
              │       │        │
            SSA    MemorySSA  Alias
              │       │        │
              └───────┼────────┘
                      ▼
                  ABI MIR
                      │
                      ▼
                  Axiom LIR
                      │
                      ▼
                 Machine IR
                      │
          ┌───────────┼────────────┐
          ▼           ▼            ▼
       x86-64       ARM64       RISC-V
          │           │            │
          └───────────┼────────────┘
                      ▼
                 Machine Code
                      │
                      ▼
                   Object
                      │
                      ▼
                   Linker
                      │
                      ▼
             EXE / ELF / Mach-O
```

Đây là kiến trúc mà tôi cho rằng **đáng freeze ở mức compiler architecture**.

Điểm đặc biệt của Axiom là safety system không đứng ngoài compiler optimization:

```text
Ownership
Capability
Region
Lifetime
        ↓
    Safety proof
        ↓
    Alias facts
        ↓
    Optimization
        ↓
    Better machine code
```

Tức là cùng một thông tin vừa giúp **ngăn lỗi**, vừa giúp compiler **tối ưu mạnh**.

---

## BOOTSTRAP-059 — Native Object Writer & Linker Architecture

Bước tiếp theo sẽ đi thẳng vào phần còn thiếu để hoàn thành native toolchain:

- Object model chung
- ELF/PE-COFF/Mach-O/WASM
- Sections
- Symbols
- Relocations
- COMDAT/linkonce
- TLS
- Static library
- Shared library
- Import/export
- Dynamic linking
- PLT/GOT
- Mach-O stubs/bind/rebase
- PE import/export tables
- ELF dynamic sections
- Linker symbol resolution
- Dead stripping
- Section GC
- LTO/link-time metadata
- startup objects
- executable layout
- ASLR/PIE
- cuối cùng: **Axiom Linker không cần GCC/Clang/LLD**.