# BOOTSTRAP-231 — COMPILER INTRINSICS, BUILTINS, TARGET OPERATIONS & INLINE ASM

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của task này là khóa một nguyên tắc:

> **Axiom phải cho phép truy cập sức mạnh gần mức ASM, nhưng không biến ngôn ngữ thành một tập hợp instruction của từng CPU.**

---

# 1. Ba tầng phải được tách biệt

```text
Axiom Semantic Primitive
        ↓
Compiler Intrinsic
        ↓
Target Operation
        ↓
Machine Instruction
```

Ví dụ:

```axiom
let x = a.leading_zeros()
```

không có nghĩa Axiom bắt buộc phải sinh đúng một instruction cụ thể.

Compiler có thể chọn:

```text
x86    → LZCNT / BSR sequence
ARM64  → CLZ
RISC-V → CLZ
GPU    → target-specific operation
software fallback → algorithm
```

Programmer viết **ý nghĩa**, compiler chọn **cách thực hiện**.

---

# 2. Semantic primitive

Đây là operation mà ngôn ngữ thực sự định nghĩa.

Ví dụ:

```text
add
sub
mul
div
checked_add
wrapping_add
saturating_add
rotate_left
rotate_right
leading_zeros
trailing_zeros
popcount
```

Các operation này có semantics độc lập CPU.

---

# 3. Compiler builtin

Builtin là operation compiler hiểu trực tiếp:

```text
__builtin_xxx
```

nhưng **không nên là surface syntax thông thường của Axiom**.

Thay vào đó:

```text
Axiom source
    ↓
ordinary function / trait API
    ↓
compiler recognizes intrinsic implementation
```

Điều này giữ language sạch.

---

# 4. Intrinsic

Intrinsic là semantic operation được compiler map đặc biệt.

Ví dụ conceptual:

```text
Intrinsic::PopCount<T>
Intrinsic::RotateLeft<T>
Intrinsic::VectorShuffle<T>
Intrinsic::AtomicCAS<T>
Intrinsic::Prefetch
Intrinsic::Fence
```

Intrinsic có:

```text
semantic definition
type rules
effect rules
target requirements
fallback policy
verification rules
```

---

# 5. Intrinsic không phải magic

Mỗi intrinsic phải có specification:

```text
Intrinsic {
    Identity
    InputTypes
    OutputType
    Effects
    Safety
    ConstBehavior
    TargetRequirements
    Fallback
    OptimizationContract
}
```

Nếu không định nghĩa được semantics → không được đưa vào compiler.

---

# 6. Không cho intrinsic phá type system

Ví dụ không thể:

```text
intrinsic_magic(x)
```

rồi compiler bỏ qua:

- type checking;
- ownership;
- capability;
- alignment;
- initialization;
- ABI.

Intrinsic vẫn đi qua semantic verifier.

---

# 7. Pure intrinsic

Ví dụ:

```text
popcount(x)
rotate_left(x, n)
byte_swap(x)
```

có thể là:

```text
Pure
```

Compiler được phép constant-fold.

---

# 8. Memory intrinsic

Ví dụ:

```text
copy_nonoverlap
prefetch
memset
memcpy
```

không thể coi giống arithmetic.

Chúng có:

```text
Read
Write
Alias
Alignment
Overlap
Volatile
```

effects tương ứng.

---

# 9. `memcpy`

Axiom không cần expose C-style raw pointer API cho ordinary programming.

Compiler có thể recognize:

```axiom
copy(dst, src)
```

và lower thành:

```text
inline copy
SIMD copy
REP MOVSB
NEON sequence
vector loop
library call
```

tùy context.

---

# 10. Copy semantics vs physical copy

Nếu:

```axiom
let b = a
```

là semantic Copy, compiler có thể:

```text
register reuse
SSA substitution
load elimination
memcpy
vector move
```

Không được hiểu rằng source code yêu cầu physical memory copy.

---

# 11. Move intrinsic

Tương tự:

```text
Move
```

là semantic ownership operation.

Không nhất thiết sinh machine instruction.

---

# 12. Atomic intrinsic

Atomic phải được compiler nhận diện trực tiếp.

Ví dụ API library:

```axiom
counter.fetch_add(1, Relaxed)
```

compiler resolve:

```text
AtomicFetchAdd<T>
```

sau đó target lowering.

---

# 13. SIMD

Axiom không muốn programmer phải viết:

```text
_mm_add_ps(...)
```

cho code portable.

Thay vào đó:

```axiom
let c = a + b
```

trên vector type.

Compiler có thể tự vectorize.

Khi cần kiểm soát rõ hơn:

```axiom
simd_add(a, b)
```

hoặc vector operations typed.

---

# 14. SIMD abstraction

Semantic model:

```text
Vector<T, N>
Mask<N>
```

với:

```text
add
sub
mul
div
min
max
shuffle
select
reduce
load
store
```

Compiler map sang:

```text
SSE
AVX2
AVX-512
NEON
SVE
RVV
GPU
```

---

# 15. Không guarantee instruction cụ thể

Nếu programmer viết:

```axiom
simd_add(a, b)
```

compiler guarantee semantic vector operation.

Không guarantee:

```text
VMOVDQA
VADDPS
```

cụ thể.

Nếu cần instruction-level guarantee → system layer.

---

# 16. Target-specific intrinsic

Một số operation thực sự chỉ tồn tại trên target.

Ví dụ:

```text
AES instruction
SHA instruction
CRC instruction
matrix acceleration
special vector instruction
```

Axiom cho phép:

```text
@target(...)
```

hoặc capability yêu cầu target.

---

# 17. Target requirement

Intrinsic có metadata:

```text
TargetRequirement {
    Architecture
    Features
    MinimumVersion
}
```

Ví dụ:

```text
requires x86.avx2
```

Compiler phải kiểm tra tại compile time.

---

# 18. Không có CPU feature → compile error hoặc fallback

Library có thể định nghĩa:

```text
static dispatch
dynamic dispatch
software fallback
```

Ví dụ:

```text
hash(data)
```

có thể chọn:

```text
AVX2 implementation
SSE implementation
scalar implementation
```

---

# 19. Multiversioning

Compiler có thể tạo:

```text
hash.avx2
hash.sse4
hash.scalar
dispatcher
```

và chọn runtime implementation.

Nhưng:

> **Dynamic dispatch là library/compiler feature, không phải semantics bắt buộc của function.**

---

# 20. `@target`

`@target` nên mô tả requirement, không phải bắt compiler sử dụng instruction cụ thể.

Ví dụ conceptual:

```axiom
@target(cpu.avx2)
fn fast_hash(...) { ... }
```

nghĩa là function chỉ hợp lệ khi target có AVX2.

---

# 21. `@target` inheritance

Nếu function A gọi function B:

```text
A requires AVX2
B requires AVX2
```

compiler propagates requirement.

Nếu:

```text
A generic
B AVX2-only
```

compiler không được silently tạo binary không hợp lệ.

---

# 22. Target capability

Target features trở thành compiler fact:

```text
TargetFeature {
    name
    supported
    guaranteed
    optional
}
```

---

# 23. Runtime CPU detection

Đây là khác với compile target.

```text
compile target:
    x86-64 baseline

runtime CPU:
    AVX2 available
```

Compiler có thể tạo multiversioning.

---

# 24. `@requires`

Có thể dùng abstraction:

```text
@requires(cpu.avx2)
```

nhưng semantic meaning là:

> code này chỉ được instantiate/lower khi capability tồn tại.

Không phải optimization hint.

---

# 25. Compile-time target branching

```axiom
@cfg(target_arch = "x86_64")
```

có thể select implementation.

Đây là compile-time selection.

---

# 26. Runtime dispatch

Nếu cần:

```text
if cpu_has_avx2() {
    fast()
} else {
    fallback()
}
```

compiler không được bỏ nhánh chỉ vì compile target hỗ trợ AVX2 nếu runtime capability chưa được chứng minh.

---

# 27. CPU intrinsics không làm Core phình to

Core chỉ cần semantic categories:

```text
integer
floating point
vector
atomic
memory
fence
target feature
unsafe machine access
```

Danh sách instruction nằm ở backend target database.

---

# 28. Instruction database

Compiler backend có:

```text
TargetInstructionDB
```

chứa:

```text
opcode
operands
latency
throughput
register constraints
encoding
feature requirements
side effects
memory behavior
```

Nhưng đây là implementation/backend knowledge.

Không phải language specification.

---

# 29. Backend lowering

```text
Axiom IR:

VectorAdd<f32, 8>
        ↓
Legalization
        ↓
TargetVectorAdd
        ↓
AVX2 VADDPS
```

Hoặc:

```text
VectorAdd<f32, 8>
        ↓
two 4-wide operations
```

nếu target không hỗ trợ width 8.

---

# 30. Legalization

Target legalization chịu trách nhiệm:

```text
unsupported width
unsupported type
unsupported atomic width
unsupported instruction
address-space mismatch
ABI constraints
register constraints
```

Không đẩy các vấn đề này vào frontend.

---

# 31. Scalarization

Ví dụ:

```text
Vector<i32, 3>
```

target chỉ hỗ trợ width 4.

Compiler có thể:

```text
vector width 4
mask unused lane
```

hoặc scalarize.

Semantic value vẫn là vector 3 phần tử.

---

# 32. Constant evaluation

Intrinsic pure phải có thể được xử lý bởi comptime nếu semantics cho phép.

Ví dụ:

```axiom
const MASK = popcount(0xff)
```

→ compiler tính lúc build.

---

# 33. Comptime intrinsic

Comptime VM không cần mô phỏng instruction CPU.

Nó thực hiện semantic operation:

```text
PopCount(255)
→ 8
```

---

# 34. Không được compile-time phụ thuộc CPU instruction

Sai:

```text
comptime:
    execute CPU instruction X
```

Đúng:

```text
comptime:
    evaluate semantic operation X
```

Target-specific instruction chỉ là backend realization.

---

# 35. Floating-point intrinsic

Ví dụ:

```text
sqrt
sin
cos
fma
```

phải phân biệt:

```text
strict semantic operation
fast-math operation
target approximation
```

---

# 36. Strict FP

```axiom
sqrt(x)
```

phải tuân semantics của Axiom FP profile.

Compiler không được tự đổi thành approximation chỉ vì nhanh hơn.

---

# 37. Fast math

Có thể:

```axiom
@fast_math
```

hoặc compiler profile tương ứng.

Khi bật:

```text
reassociation
approximation
FTZ/DAZ
FMA contraction
```

chỉ được phép theo contract đã định nghĩa.

---

# 38. Crypto intrinsic

Ví dụ:

```text
AES
SHA
carryless multiply
```

có thể là target intrinsic.

Nhưng crypto API cấp cao không nên expose raw instruction.

Ví dụ:

```axiom
aes_gcm_encrypt(...)
```

library có thể chọn hardware implementation.

---

# 39. Constant-time

Intrinsic dùng trong:

```axiom
@constant_time
```

phải có latency/security classification phù hợp.

Compiler không được biến operation thành sequence có secret-dependent branch nếu vi phạm contract.

---

# 40. Memory prefetch

`prefetch` là một trường hợp đặc biệt.

Nó có thể được xem là optimization/system intrinsic:

```text
Prefetch {
    address
    locality
    read/write
}
```

Không được coi là semantic data dependency.

Nếu target không support → có thể bỏ.

---

# 41. Nhưng prefetch không được làm thay đổi correctness

Compiler có thể:

```text
prefetch(ptr)
```

→ no-op.

Không được dựa vào prefetch để đảm bảo memory validity.

---

# 42. Cache hints

Các hint như:

```text
prefetch
cache flush
cache invalidate
```

phải phân biệt:

```text
performance hint
vs
architectural memory operation
```

Cache flush trong DMA/device code có thể có semantic effect.

---

# 43. Inline assembly

Axiom cần inline assembly vì systems programming.

Nhưng:

> **Inline ASM là escape hatch, không phải API chính.**

Syntax có thể thuộc system/unsafe layer:

```axiom
unsafe asm {
    ...
}
```

---

# 44. ASM không được bypass compiler knowledge hoàn toàn

Inline asm phải khai báo:

```text
inputs
outputs
clobbers
memory effects
register constraints
target
```

Conceptual:

```text
asm(
    instruction = "...",
    inputs = [...],
    outputs = [...],
    clobbers = [...],
    memory = ...
)
```

---

# 45. `asm` semantic contract

Compiler phải biết ít nhất:

```text
Read registers
Write registers
Clobber registers
Read memory
Write memory
Atomic/volatile characteristics
Control-flow effects
```

---

# 46. `asm volatile`

Có thể hỗ trợ:

```text
volatile asm
```

nhưng nghĩa phải rõ:

> compiler không được xóa/reorder assembly theo cách vi phạm declared observable effect.

---

# 47. Memory clobber

ASM có thể khai báo:

```text
memory
```

nghĩa compiler phải coi ASM có thể đọc/ghi memory theo contract.

---

# 48. Không cho ASM giả mạo semantic type

Nếu ASM output:

```text
i32
```

compiler nhận một `i32` hợp lệ.

Nếu programmer muốn reinterpret:

```text
bitcast
```

hoặc unsafe representation operation phải được dùng.

ASM không tự động phá type invariant.

---

# 49. ASM và ownership

Ví dụ ASM ghi vào buffer:

```text
asm modifies buf
```

compiler phải biết `buf` là:

```text
WRITE capability
```

Nếu chỉ có read-only view:

```text
view<T>
```

→ reject.

---

# 50. ASM và alias

Nếu ASM có:

```text
memory = clobber
```

compiler mất một số alias facts.

Khi ASM contract cụ thể hơn:

```text
writes region R
```

compiler giữ được optimization nhiều hơn.

---

# 51. Raw machine instruction

Có thể có system API:

```text
cpu::rdtsc()
cpu::pause()
cpu::cpuid(...)
```

nhưng nên implement bằng compiler intrinsic.

Programmer không cần inline ASM cho các operation phổ biến.

---

# 52. `rdtsc` không phải pure

Timing instruction phụ thuộc machine state.

Do đó effects phải được định nghĩa.

Ví dụ:

```text
ReadCPUState
```

thay vì `Pure`.

---

# 53. `pause`

`pause` là machine hint.

Có thể có:

```text
cpu::pause()
```

với effect:

```text
CPUHint
```

Compiler không nên tự xóa nếu programmer explicitly yêu cầu machine hint trong spin loop.

---

# 54. System intrinsics

Những thứ như:

```text
interrupt_enable
disable_interrupt
port_io
mmio
syscall
rdmsr
```

thuộc system/unsafe layer.

Không đưa vào Core.

---

# 55. Syscall

Syscall không phải compiler intrinsic bắt buộc.

Có thể:

```text
std::os::linux::syscall(...)
```

và compiler/backend xử lý ABI.

---

# 56. ABI intrinsic

Compiler phải hỗ trợ intrinsic liên quan:

```text
va_arg
stack_probe
return_address
frame_address
unwind
```

nhưng chỉ system/compiler API.

Không nên xuất hiện trong normal Core programming.

---

# 57. Stack allocation

Nếu có:

```text
alloca
```

thì đây là storage intrinsic.

Compiler phải kiểm tra:

- lifetime;
- alignment;
- dynamic size;
- escape;
- cleanup.

Không được cho programmer tạo arbitrary invalid storage trong safe code.

---

# 58. Atomic wait/notify

Đây là ví dụ không nên hạ thành một raw CPU instruction.

Semantic API:

```text
atomic_wait
atomic_notify
```

backend/runtime có thể dùng:

```text
futex
WaitOnAddress
parking
spin
platform primitive
```

---

# 59. Compiler builtin vs library function

Một function có thể nhìn như library:

```axiom
fn popcount(x: u64) -> u32
```

nhưng compiler nhận diện implementation/intrinsic và lower thành instruction.

Programmer không cần biết.

---

# 60. Intrinsic fallback

Mỗi portable intrinsic nên có:

```text
SemanticDefinition
NativeLowering*
PortableFallback
```

`*` nghĩa native lowering có thể tồn tại hoặc không.

---

# 61. Fallback không được thay đổi semantics

Ví dụ:

```text
popcount
```

native:

```text
POPCNT
```

fallback:

```text
software bit counting
```

Hai implementation phải cho cùng semantic result.

---

# 62. Intrinsic versioning

Intrinsic identity phải stable:

```text
IntrinsicId
SemanticVersion
```

Compiler implementation có thể thay đổi machine lowering.

Điều này quan trọng với:

- cached artifacts;
- `.axlib`;
- reproducible builds;
- compiler compatibility.

---

# 63. Intrinsic effect metadata

Ví dụ:

```text
popcount
    Pure

atomic_load
    AtomicRead

memcpy
    Read + Write

volatile_read
    VolatileRead

rdtsc
    ReadCPUState

asm
    declared effects
```

---

# 64. Intrinsic safety metadata

```text
Safe
Unsafe
SafeUnderContract
```

Ví dụ:

```text
popcount → Safe
atomic_load → Safe
raw_load → Unsafe
bitcast → condition-dependent
asm → Unsafe
mmio → Unsafe/system
```

---

# 65. Capability requirements

Memory intrinsic phải khai báo:

```text
RequiredCapability:
    READ
    WRITE
    MOVE
```

Ví dụ:

```text
copy(src, dst)
```

yêu cầu:

```text
src READ
dst WRITE
```

và nếu non-overlap:

```text
DISJOINT
```

---

# 66. Intrinsic contracts đi vào MIR

Không tạo “special hidden path”.

Ví dụ:

```text
Intrinsic::AtomicCAS
```

sẽ trở thành MIR:

```text
AtomicCompareExchange
```

với:

```text
ordering
memory scope
type
location
```

---

# 67. Điều này rất quan trọng cho compiler correctness

Pipeline:

```text
Frontend
   ↓
Intrinsic Resolution
   ↓
Typed MIR
   ↓
Verification
   ↓
Optimization
```

Không:

```text
frontend
   ↓
magic backend shortcut
```

---

# 68. GPU intrinsic

GPU cũng dùng cùng nguyên tắc.

Ví dụ:

```text
subgroup_shuffle
warp_reduce
barrier
shared_load
shared_store
```

được semantic hóa.

Backend chọn:

```text
SPIR-V
CUDA
Metal
D3D
WebGPU
```

---

# 69. GPU portability

Không phải GPU nào cũng có cùng primitive.

Do đó:

```text
@requires(gpu.subgroup)
```

hoặc library fallback.

Không được giả định warp size cố định.

---

# 70. CPU/GPU abstraction

Có thể có:

```text
simd
```

portable CPU semantic vector.

Và:

```text
subgroup
```

GPU execution-group abstraction.

Không nhập chúng thành một primitive.

---

# 71. Intrinsic namespace

Đề xuất:

```text
std::intrinsic
std::cpu
std::gpu
std::arch
std::system
```

nhưng:

```text
std::intrinsic
```

chủ yếu dành cho compiler/library implementation.

Application programmer ưu tiên API cấp cao.

---

# 72. Machine-level escape hatch

Hierarchy:

```text
High-level API
      ↓
Portable intrinsic
      ↓
Target intrinsic
      ↓
Inline ASM
      ↓
Raw machine/system access
```

Càng xuống thấp:

- portability giảm;
- compiler freedom giảm;
- programmer responsibility tăng.

---

# 73. Không cần `volatile` cho performance

Một lỗi thiết kế thường gặp:

```text
volatile = don't optimize
```

Axiom không dùng volatile như vậy.

Nếu muốn ngăn optimizer vì performance debugging → không dùng volatile.

Volatile chỉ dành cho observable machine/device memory semantics.

---

# 74. `black_box`

Testing/benchmark cần:

```text
black_box(x)
```

để ngăn compiler suy ra value không observable trong benchmark.

Đây là compiler/testing semantic primitive riêng.

Không đồng nghĩa volatile.

---

# 75. Benchmark correctness

Ví dụ:

```axiom
black_box(compute(data))
```

Compiler không được optimize away `compute` nếu black_box contract yêu cầu observable consumption.

---

# 76. Instruction selection

Machine instruction selection nên tối ưu theo:

```text
latency
throughput
code size
register pressure
target pipeline
microarchitecture
```

nhưng đây là backend concern.

Không thay đổi semantics.

---

# 77. CPU microarchitecture tuning

Compiler có thể có:

```text
-march
-mcpu
-mtune
```

tương đương concept.

Phải phân biệt:

```text
semantic target
vs
performance tuning target
```

---

# 78. Binary reproducibility

Instruction selection có thể thay đổi theo compiler version/microarchitecture target.

Artifact fingerprint phải ghi:

```text
TargetSpec
CPUFeatures
CodegenFingerprint
```

---

# 79. Semantic fingerprint không phụ thuộc instruction selection

Nếu cùng:

```text
source
API
types
ABI
semantics
```

nhưng compiler chọn:

```text
AVX2
```

thay vì:

```text
scalar
```

thì SemanticFingerprint không thay đổi.

CodegenFingerprint thay đổi.

---

# 80. Đây là kiến trúc đúng cho `.axlib`

`.axlib` có thể chứa:

```text
semantic metadata
generic metadata
ABI
required target features
optimization summaries
native objects
```

Consumer compiler có thể chọn implementation phù hợp.

---

# 81. Intrinsic specialization

Generic:

```axiom
fn hash<T>(x: T)
```

compiler có thể specialize:

```text
T = u64
```

và sử dụng:

```text
POPCNT
CRC
AES
```

nếu semantic contract cho phép.

---

# 82. Compiler không được “invent” intrinsic semantics

Ví dụ compiler thấy:

```text
x * 2
```

không có nghĩa compiler được tự biến thành một operation có semantics khác chỉ vì instruction nhanh hơn.

Instruction selection phải preserve:

```text
overflow semantics
FP semantics
atomic semantics
side effects
```

---

# 83. Integer overflow

Ví dụ Axiom:

```text
checked_add
wrapping_add
saturating_add
```

là semantic operations khác nhau.

Backend có thể dùng cùng instruction nếu semantics tương ứng.

---

# 84. Carry/borrow

Low-level crypto/bignum cần:

```text
add_with_carry
sub_with_borrow
mul_wide
```

Nên là semantic integer primitives/library operations.

Không buộc programmer viết ASM.

---

# 85. Wide multiplication

Ví dụ:

```text
mul_wide(u64, u64)
→ (hi: u64, lo: u64)
```

Backend:

```text
x86 → MUL
ARM → UMULH + MUL
RISC-V → MULHU + MUL
```

Đây chính xác là abstraction Axiom nên có.

---

# 86. Bit manipulation

Core/library nên cung cấp semantic operations:

```text
bit_and
bit_or
bit_xor
bit_not
shift
rotate
reverse_bits
reverse_bytes
popcount
clz
ctz
```

Compiler nhận diện chúng khi có lợi.

---

# 87. No instruction naming in normal code

Không nên:

```axiom
x86_vpternlog(...)
```

trong portable application code.

Nếu thật sự cần:

```text
std::arch::x86::vpternlog
```

và function mang target requirement.

---

# 88. Architecture namespace

Ví dụ:

```text
std::arch::x86
std::arch::arm
std::arch::riscv
```

chứa target-specific operations.

Chúng không thuộc Core semantics.

---

# 89. Unsafe boundary

Target-specific operation có thể:

```text
Safe
```

nếu compiler có thể đảm bảo tất cả preconditions.

Hoặc:

```text
Unsafe
```

nếu programmer phải đảm bảo machine-level invariant.

---

# 90. Compiler intrinsic registry

Compiler architecture:

```text
IntrinsicRegistry
├── Arithmetic
├── BitOps
├── Memory
├── Atomic
├── SIMD
├── FloatingPoint
├── Crypto
├── CPU
├── GPU
├── ABI
├── Comptime
└── Testing
```

Mỗi intrinsic có descriptor.

---

# 91. Intrinsic resolution

Frontend:

```text
name resolution
→ declaration
→ trait/inherent method
→ intrinsic marker
```

Không hard-code tên function ở parser.

---

# 92. HIR representation

HIR:

```text
Call {
    callee = FunctionId
}
```

nếu function được compiler đánh dấu intrinsic:

```text
IntrinsicId
```

được attach trong semantic layer.

---

# 93. MIR representation

MIR không nên giữ:

```text
Call("x86_vaddps")
```

mà giữ:

```text
IntrinsicOp {
    intrinsic_id
    operands
    semantic_contract
}
```

sau đó mới lower.

---

# 94. LIR

LIR có:

```text
TargetOp
```

ví dụ:

```text
TargetOp::VectorAdd
TargetOp::AtomicCAS
TargetOp::Fence
TargetOp::CRC32
```

---

# 95. Machine IR

Machine IR cuối cùng mới có:

```text
Instruction {
    opcode
    operands
    registers
    flags
}
```

---

# 96. Từ đó pipeline hoàn chỉnh

```text
Axiom Source
    ↓
AST
    ↓
HIR
    ↓
Intrinsic Resolution
    ↓
MIR
    ↓
Ownership/Capability/Effect Verification
    ↓
Verified MIR
    ↓
OptIR
    ↓
Target Legalization
    ↓
Axiom LIR
    ↓
Machine IR
    ↓
Instruction Selection
    ↓
Register Allocation
    ↓
Encoding
```

---

# 97. Inline ASM cuối pipeline

ASM vẫn đi qua semantic boundary:

```text
InlineASM
    ↓
ASM Contract
    ↓
MIR/LIR machine barrier
    ↓
Register allocation
    ↓
Encoding
```

Không để parser trực tiếp nhét bytes vào executable.

---

# 98. Raw machine bytes

Có thể cần cho bootloader/firmware/hardware đặc biệt.

Nhưng:

```text
emit bytes
```

phải thuộc system/unsafe facility.

Compiler phải coi nó là opaque machine effect.

---

# 99. Self-hosting implication

Khi Axiom compiler tự viết bằng Axiom, compiler source có thể định nghĩa:

```text
compiler/intrinsics
compiler/targets/x86
compiler/targets/arm64
compiler/targets/riscv
compiler/targets/gpu
```

Target database trở thành dữ liệu có cấu trúc, không phải một đống hardcoded frontend cases.

---

# 100. Frozen invariants

```text
AINTR-20
Every compiler intrinsic has an explicit semantic identity.

AINTR-21
Every intrinsic has defined type semantics.

AINTR-22
Every intrinsic has defined effect semantics.

AINTR-23
Every intrinsic has defined safety requirements.

AINTR-24
Every intrinsic has explicit target requirements when target-dependent.

AINTR-25
Intrinsic semantics are independent of machine instruction selection.

AINTR-26
Target instruction selection must preserve intrinsic semantics.

AINTR-27
Intrinsic lowering cannot bypass ownership verification.

AINTR-28
Intrinsic lowering cannot bypass capability verification.

AINTR-29
Intrinsic lowering cannot bypass effect verification.

AINTR-30
Intrinsic lowering cannot bypass concurrency verification.

AINTR-31
Pure intrinsics may participate in compile-time evaluation when permitted.

AINTR-32
Comptime intrinsic evaluation uses semantic behavior, not physical instruction execution.

AINTR-33
Portable intrinsics should provide a semantic fallback where practical.

AINTR-34
Fallback implementations must preserve intrinsic semantics.

AINTR-35
Target-specific intrinsics must declare target requirements.

AINTR-36
Unsupported target requirements produce a compile-time diagnostic unless an explicit fallback exists.

AINTR-37
Runtime CPU feature detection is distinct from compile-time target capability.

AINTR-38
Runtime multiversioning must preserve one semantic function contract.

AINTR-39
Target annotations are semantic requirements, not arbitrary optimizer hints.

AINTR-40
Instruction names are not part of portable Axiom semantics.

AINTR-41
SIMD semantics are defined independently of CPU vector ISA.

AINTR-42
GPU intrinsics are defined independently of a single GPU backend.

AINTR-43
CPU subgroup operations and GPU subgroup operations are distinct abstractions.

AINTR-44
Memory intrinsics carry explicit read/write/alias/alignment semantics.

AINTR-45
Atomic intrinsics preserve atomicity and memory-order semantics.

AINTR-46
Volatile operations remain distinct from atomic operations.

AINTR-47
Prefetch is a performance hint unless explicitly specified otherwise.

AINTR-48
Performance hints cannot establish memory safety.

AINTR-49
Inline assembly is an explicit low-level escape hatch.

AINTR-50
Inline assembly must declare relevant inputs, outputs, clobbers and memory effects.

AINTR-51
Inline assembly cannot implicitly invalidate ownership facts without a declared effect.

AINTR-52
Inline assembly cannot manufacture safe capabilities without an explicit safety contract.

AINTR-53
Inline assembly target validity is checked against TargetSpec.

AINTR-54
Machine instructions cannot directly appear as ordinary Core syntax.

AINTR-55
Architecture-specific operations belong to system/architecture libraries or compiler facilities.

AINTR-56
Compiler builtins are implementation mechanisms, not necessarily user-facing language syntax.

AINTR-57
Intrinsic identity is stable independently of machine implementation.

AINTR-58
Semantic fingerprints do not depend on instruction selection.

AINTR-59
Codegen fingerprints include relevant target/code-generation choices.

AINTR-60
Target legalization may decompose an intrinsic into multiple operations.

AINTR-61
Target legalization may scalarize or widen vector operations when semantics are preserved.

AINTR-62
Unsupported hardware operations may use software implementations when contract permits.

AINTR-63
Strict floating-point intrinsics cannot silently become approximate operations.

AINTR-64
Fast-math behavior requires an explicit semantic contract.

AINTR-65
Constant-time functions require intrinsic transformations to preserve their timing/security contract.

AINTR-66
CPU state operations are not automatically pure.

AINTR-67
System operations such as MMIO, port I/O and interrupt control remain outside Core.

AINTR-68
Raw machine memory operations require appropriate system/unsafe contracts.

AINTR-69
Intrinsic effects participate in EffectInfo.

AINTR-70
Intrinsic memory effects participate in MemorySSA.

AINTR-71
Intrinsic alias contracts participate in AliasInfo.

AINTR-72
Intrinsic synchronization effects participate in the memory model.

AINTR-73
Optimizer transformations may use intrinsic facts but cannot weaken their contracts.

AINTR-74
Inline assembly is treated conservatively when its declared effects are insufficient.

AINTR-75
An intrinsic with unknown observable effects cannot be treated as pure.

AINTR-76
Compiler-generated intrinsic use must remain semantically valid after specialization.

AINTR-77
Generic specialization may select target intrinsics only when target requirements are proven.

AINTR-78
Target-specific intrinsics must remain isolated from portable semantic code.

AINTR-79
The backend owns instruction selection and encoding.

AINTR-80
The frontend must not contain architecture-specific instruction-selection logic.

AINTR-81
The Axiom LIR represents target operations before final machine encoding.

AINTR-82
Machine IR represents concrete target instructions.

AINTR-83
Instruction scheduling cannot violate semantic dependencies.

AINTR-84
Register allocation cannot alter semantic values.

AINTR-85
ASM clobbers must be respected by register allocation.

AINTR-86
Intrinsic implementations may change across compiler versions without changing their semantic identity.

AINTR-87
Target instruction databases are compiler/backend data, not language semantics.

AINTR-88
Compiler intrinsic implementations must have conformance tests.

AINTR-89
Each intrinsic lowering must be testable against a semantic reference.

AINTR-90
Different target lowerings are valid when they implement the same Axiom semantics.
```

---

# 101. Kết quả kiến trúc quan trọng

Axiom giờ có thể đạt đồng thời ba mục tiêu:

### Code thông thường

```axiom
let c = a + b
```

→ compiler tự tối ưu.

### Code hiệu năng cao

```axiom
let c = simd_add(a, b)
```

→ programmer yêu cầu semantic vector operation.

### Code cực thấp

```axiom
unsafe asm { ... }
```

→ programmer có quyền kiểm soát machine level.

Nhưng ba tầng không bị trộn vào nhau.

```text
        Axiom semantic code
                 │
        ┌────────┴────────┐
        ↓                 ↓
 Portable Intrinsics   Target Intrinsics
        │                 │
        └────────┬────────┘
                 ↓
             LIR
                 ↓
           Machine IR
                 ↓
              ASM
```

Đây là cách Axiom có thể hướng tới **“hiệu năng như C/C++/ASM nhưng ngôn ngữ không biến thành assembly syntax.”**

---

# TASK TIẾP THEO

## **BOOTSTRAP-232 — Axiom Object Model: Functions, Closures, Methods, Traits, Generics & Dynamic Dispatch — IMPLEMENTATION SPEC**

Task này sẽ khóa phần còn lại của **behavior model** của Axiom, đặc biệt vấn đề mà ta đã bàn trước đây:

> **Không có class, vậy method/override/inheritance/dynamic dispatch thực sự được compiler biểu diễn thế nào?**

Sẽ đi sâu vào:

```text
struct
   ↓
inherent function
   ↓
method sugar
   ↓
trait
   ↓
impl
   ↓
generic static dispatch
   ↓
monomorphization
   ↓
devirtualization
   ↓
dyn Trait
   ↓
vtable / fat pointer khi thực sự cần
```

và quan trọng nhất: **làm thế nào để `override` không cần `class`/`virtual`/`this`, nhưng vẫn hỗ trợ polymorphism mạnh mà không tạo overhead mặc định.**