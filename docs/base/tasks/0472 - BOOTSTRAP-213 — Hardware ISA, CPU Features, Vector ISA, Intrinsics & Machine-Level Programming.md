# BOOTSTRAP-213 — Hardware ISA, CPU Features, Vector ISA, Intrinsics & Machine-Level Programming

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của 213:

> **Axiom không được gắn cứng vào một ISA cụ thể. Core language ổn định, còn compiler/backend tự khai thác ISA của từng CPU/accelerator.**

Kiến trúc:

```text
                    Axiom Source
                         │
                         ▼
                    Semantic MIR
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
       Generic Optimization     Target Analysis
                                     │
                ┌────────────────────┼────────────────────┐
                ▼                    ▼                    ▼
              x86-64               ARM64                RISC-V
                │                    │                    │
          AVX/AVX-512             NEON/SVE             RVV
          AMX/Crypto              SVE2/SME             V/Z*
                │                    │                    │
                └────────────────────┼────────────────────┘
                                     ▼
                              Machine IR
                                     │
                                     ▼
                               Native Code
```

---

# 213.1. Core không biết ISA

Core không chứa:

```text
AVX2
SSE
NEON
SVE
RVV
AMX
```

Đây là Target/Backend knowledge.

---

# 213.2. TargetSpec mở rộng

`TargetSpec` hiện có thêm:

```text
InstructionSet
FeatureSet
VectorISA
MatrixISA
CryptoISA
AtomicISA
FloatingPointISA
CacheTopology
RegisterFile
CallingConvention
```

---

# 213.3. Feature là capability

Ví dụ:

```text
AVX2
AVX512F
AES
FMA
SVE2
RVV
```

được biểu diễn như compiler-known target features.

---

# 213.4. Không được giả định feature

Code chỉ được dùng instruction nếu:

```text
target supports feature
```

hoặc function có explicit feature contract.

---

# 213.5. `@target_feature`

Concept:

```axiom
@target_feature("avx2")
fn dot_fast(...) -> f32 {
    ...
}
```

Compiler có quyền sử dụng AVX2 trong function đó.

---

# 213.6. Feature không thay đổi semantics

Nếu AVX2 không tồn tại:

```text
generic implementation
```

có thể được chọn.

Không được biến chương trình thành invalid chỉ vì optimization target khác.

---

# 213.7. Function multiversioning

Một API:

```text
dot()
```

có thể có:

```text
dot_scalar()
dot_sse()
dot_avx2()
dot_avx512()
```

nhưng programmer chỉ thấy:

```text
dot()
```

---

# 213.8. CPU dispatch

Runtime/compiler có thể chọn:

```text
CPU feature detection
        ↓
dispatch
        ↓
best valid implementation
```

---

# 213.9. Static dispatch

Nếu binary target cố định:

```text
-target-cpu=native
```

compiler có thể chọn trực tiếp AVX2.

Không cần runtime dispatch.

---

# 213.10. Dynamic dispatch

Nếu binary portable:

```text
generic
 ↓
CPU detection
 ↓
AVX2
```

---

# 213.11. Dispatch overhead

Compiler có thể:

```text
cache selected function pointer
```

hoặc specialize caller.

---

# 213.12. Whole-program optimization

LTO có thể phát hiện:

```text
CPU feature known
```

và loại bỏ:

```text
scalar fallback
```

nếu không còn reachable.

---

# 213.13. Fat binary

Axiom có thể tạo:

```text
binary
├── generic
├── AVX2
├── AVX512
└── AMX
```

với dispatch table.

---

# 213.14. Architecture variants

Tương tự:

```text
ARM64
├── baseline
├── NEON
├── SVE
└── SVE2
```

---

# 213.15. RISC-V extensions

Không hard-code extension list vào Core.

Target database có thể biết:

```text
M
A
F
D
C
V
Zba
Zbb
Zbc
Zbs
...
```

---

# 213.16. ISA feature implication

Compiler cần biết:

```text
SVE2 → required baseline features
```

hoặc:

```text
AVX512 feature family
```

để tránh tạo instruction không hợp lệ.

---

# 213.17. Feature compatibility graph

Target database:

```text
Feature
 ├── requires
 ├── implies
 ├── conflicts
 └── enables
```

---

# 213.18. Vector type

Vector/SIMD abstraction từ 168 giữ nguyên.

Concept:

```text
Vec<T, N>
Mask<N>
```

---

# 213.19. Fixed-width vector

```text
Vec<f32, 8>
```

có thể map:

```text
AVX2 → ymm
```

---

# 213.20. Scalable vector

Đối với SVE/RVV:

```text
ScalableVec<T>
```

không cần cố định số lane tại source level.

---

# 213.21. Portable SIMD

Programmer nên viết:

```text
vector operation
```

thay vì:

```text
asm("...")
```

khi không cần instruction-specific behavior.

---

# 213.22. Vector lowering

Compiler:

```text
Vector IR
 ↓
Target Vector Legalization
 ↓
ISA instructions
```

---

# 213.23. Vector width selection

Compiler có thể chọn:

```text
128
256
512
VL-dependent
```

theo target.

---

# 213.24. Vectorization không phải semantic requirement

Scalar semantics:

```text
for i ...
```

có thể trở thành:

```text
SIMD loop
```

nếu proven legal.

---

# 213.25. Masking

Compiler phải hỗ trợ:

```text
masked load
masked store
select
predicate
```

để vectorize tail loops.

---

# 213.26. Gather/scatter

Nếu target hỗ trợ:

```text
gather
scatter
```

compiler có thể sử dụng.

Nếu không:

```text
scalar/vector fallback
```

---

# 213.27. Horizontal reduction

Compiler hỗ trợ:

```text
reduce_add
reduce_min
reduce_max
```

với strict numerical semantics.

---

# 213.28. FMA

`a*b+c` không mặc định có nghĩa là FMA nếu strict FP yêu cầu giữ rounding behavior.

Fast-math/numerical profile mới cho phép contraction.

---

# 213.29. Floating-point feature selection

Target backend phải biết:

```text
FMA
FP16
BF16
FP8
```

nhưng semantic type vẫn thuộc numeric system.

---

# 213.30. Matrix ISA

Các ISA như:

```text
AMX
SME
```

có thể được backend biểu diễn bằng MatrixIR.

Không cần thêm syntax Core.

---

# 213.31. Tensor ISA

Tensor operations từ 209 có thể lower:

```text
TensorIR
 ↓
MatrixIR
 ↓
AMX/SME/GPU
```

---

# 213.32. Crypto ISA

Ví dụ:

```text
AES
SHA
CRC
```

compiler/library có thể dispatch sang intrinsic hardware.

---

# 213.33. Crypto semantics

Hardware acceleration không được thay đổi:

```text
key semantics
constant-time contract
zeroization
```

---

# 213.34. Constant-time backend

Nếu function:

```text
@constant_time
```

backend phải tránh lowering thành instruction sequence vi phạm contract.

---

# 213.35. Instruction cost model

Compiler target database có thể chứa:

```text
latency
throughput
uops
port pressure
dependency
```

---

# 213.36. Cost model không phải semantic model

Cost data chỉ dùng:

```text
optimization
instruction selection
scheduling
```

Không dùng để quyết định correctness.

---

# 213.37. CPU microarchitecture

Compiler có thể target:

```text
generic x86-64
Zen
Zen 4
Zen 5
Alder Lake
...
```

nhưng microarchitecture model là optimization data.

---

# 213.38. `target-cpu`

Build profile có thể:

```text
-target-cpu=native
-target-cpu=x86-64-v3
```

hoặc tương đương.

---

# 213.39. Portable CPU levels

Có thể hỗ trợ feature levels:

```text
baseline
v2
v3
v4
```

theo platform ABI ecosystem.

---

# 213.40. ABI baseline

Feature optimization không được phá stable ABI.

---

# 213.41. Calling convention

Backend cần model:

```text
register arguments
stack arguments
return registers
callee-saved
caller-saved
vector registers
aggregate return
```

---

# 213.42. Calling convention không phải type semantics

Một function:

```text
fn add(a: i32, b: i32) -> i32
```

semantic type vẫn giống nhau dù ABI lowering khác.

---

# 213.43. `extern`

Foreign ABI:

```text
extern "C"
```

được lower sau semantic type checking.

---

# 213.44. Custom calling convention

System layer có thể hỗ trợ:

```text
@callconv("interrupt")
@callconv("syscall")
@callconv("vectorcall")
```

nếu target có.

---

# 213.45. Register constraints

Inline asm/intrinsics cần compiler biết:

```text
fixed register
register class
early-clobber
input/output constraints
```

---

# 213.46. Inline assembly

Giữ nguyên nguyên tắc:

```text
unsafe asm { ... }
```

nhưng contract phải mô tả effects.

---

# 213.47. Register variables

Không expose kiểu:

```text
register int x;
```

như language primitive.

Register allocation thuộc compiler.

---

# 213.48. Explicit register binding

Chỉ system/unsafe API khi hardware ABI bắt buộc:

```text
@register("x0")
```

---

# 213.49. Register binding phải local

Không biến register assignment thành global source-level optimization constraint.

---

# 213.50. Intrinsic

Intrinsic là compiler-known function:

```text
intrinsic::<...>
```

hoặc compiler-resolved standard API.

---

# 213.51. Intrinsic không phải runtime library

Nếu intrinsic map trực tiếp instruction:

```text
no function call
no runtime dependency
```

---

# 213.52. Portable intrinsic

Ưu tiên:

```text
portable vector operation
```

trước:

```text
ISA-specific intrinsic
```

---

# 213.53. ISA-specific intrinsic

Dùng khi cần:

```text
special instruction
exact latency
special register behavior
```

---

# 213.54. Intrinsic legality

Compiler phải reject nếu target không hỗ trợ instruction.

Không emit illegal opcode rồi hy vọng runtime không gọi.

---

# 213.55. CPU dispatch metadata

CompilerDB có thể expose:

```text
required_features
preferred_features
fallback
```

cho AI/IDE.

---

# 213.56. Auto-vectorization

Pipeline:

```text
Loop
 ↓
Dependence Analysis
 ↓
Alias Analysis
 ↓
Range Analysis
 ↓
Cost Model
 ↓
Vectorization
 ↓
Vector Legalization
```

---

# 213.57. Alias analysis từ Axiom capability

Đây là lợi thế lớn:

```text
mut_view disjoint
        ↓
NoAlias
        ↓
vectorization
```

Axiom không cần programmer viết `restrict`.

---

# 213.58. Runtime alias checks

Nếu compiler không chứng minh được statically nhưng có thể check cheaply:

```text
runtime check
 ↓
fast vector path
 ↓
fallback scalar path
```

có thể được sử dụng.

---

# 213.59. Runtime check correctness

Check failure phải quay về implementation semantic equivalent.

---

# 213.60. Loop versioning

Compiler có thể tạo:

```text
if proven_non_alias:
    SIMD
else:
    scalar
```

---

# 213.61. Alignment specialization

Compiler có thể kiểm tra:

```text
pointer alignment
```

và chọn:

```text
aligned load
unaligned load
```

---

# 213.62. Alignment không được đoán

Chỉ dùng aligned instruction khi alignment được:

```text
proven
or
explicit contract
```

---

# 213.63. Prefetch

Prefetch là performance hint.

Không được thay đổi semantics.

---

# 213.64. Cache-aware optimization

Compiler có thể dùng:

```text
cache line
cache size
associativity
```

nếu target model có dữ liệu.

---

# 213.65. Instruction scheduling

Machine backend có thể reorder instructions trong dependency constraints.

---

# 213.66. Scheduling correctness

Phải giữ:

```text
data dependencies
memory dependencies
atomic ordering
volatile ordering
asm constraints
```

---

# 213.67. Register allocation

Axiom backend sử dụng:

```text
SSA
Liveness
Interference
RegisterClass
SpillCost
```

---

# 213.68. Register pressure

Compiler có thể quyết định:

```text
unroll
vector width
inline
```

dựa trên register pressure.

---

# 213.69. Spill

Spill là implementation detail.

Không thay đổi semantic storage identity.

---

# 213.70. Stack slots

Stack slot không phải semantic variable identity.

Compiler có thể:

```text
register
stack
scalar
```

---

# 213.71. Machine-level identity

Chỉ khi programmer/system contract yêu cầu:

```text
address
register
ABI symbol
volatile memory
```

thì physical identity trở thành observable.

---

# 213.72. Tail calls

Backend có thể thực hiện tail-call optimization nếu:

```text
ABI permits
semantic behavior preserved
```

---

# 213.73. Calling convention optimization

Internal ABI có thể khác stable/public ABI.

---

# 213.74. Stable ABI boundary

Tại:

```text
@abi(stable)
```

compiler phải giữ:

```text
calling convention
layout
symbol
error/panic contract
```

---

# 213.75. Internal ABI freedom

Bên trong application:

```text
compiler free
```

to choose optimized calling conventions.

---

# 213.76. Cross-function vectorization

LTO có thể:

```text
inline
specialize
vectorize
```

cross-module nếu ABI obligations cho phép.

---

# 213.77. Generic specialization

Ví dụ:

```text
fn add<T: Numeric>(...)
```

có thể specialize:

```text
f32
f64
i32
Vec<f32, 8>
```

---

# 213.78. Generic + ISA

Một generic function có thể có:

```text
baseline specialization
AVX2 specialization
AVX512 specialization
```

---

# 213.79. Code-size control

Không specialize vô hạn.

Compiler cost model cân bằng:

```text
speed
binary size
compile time
```

---

# 213.80. Cold/hot paths

Compiler có thể sử dụng:

```text
@cold
@hot
```

hoặc profile-derived information.

Không ảnh hưởng semantics.

---

# 213.81. PGO

PGO từ 149 có thể quyết định:

```text
inline
branch layout
function cloning
CPU dispatch
```

---

# 213.82. CPU dispatch + PGO

Có thể kết hợp:

```text
CPU features
+
runtime profile
+
PGO
```

---

# 213.83. Security hardening

Backend phải hỗ trợ:

```text
stack protector
CFI
shadow stack
BTI
PAC
W^X
```

tùy target/profile.

---

# 213.84. Security feature ≠ language semantic feature

Hardening không được yêu cầu bởi mọi Axiom binary.

---

# 213.85. Portable source

Mục tiêu:

```text
same source
 ↓
x86-64
ARM64
RISC-V
WASM
```

trong phạm vi API/platform tương thích.

---

# 213.86. Architecture-specific optimization

Code vẫn có thể:

```text
if @target_feature(...)
```

hoặc compile-time conditional.

---

# 213.87. Target conditional

Đã có `@cfg`.

Có thể:

```axiom
@cfg(target_arch = "x86_64")
...
```

nhưng semantic selection xảy ra trước production verification.

---

# 213.88. CPU runtime detection

Runtime detection chỉ dùng khi binary chứa nhiều implementation.

Không cần trong static target build.

---

# 213.89. Dispatch ABI

Function variants phải có compatible logical API.

Compiler tạo dispatcher:

```text
dispatch(args)
 ↓
implementation(args)
```

---

# 213.90. Dispatcher optimization

Nếu compiler biết CPU statically:

```text
dispatcher removed
```

---

# 213.91. Axiom Machine IR

Sau ABI lowering:

```text
Axiom LIR
 ↓
Machine IR
```

Machine IR phải biểu diễn:

```text
Register
VirtualRegister
PhysicalRegister
Instruction
MemoryOperand
BasicBlock
CallingConvention
FeatureRequirement
```

---

# 213.92. Target legalization

Generic operation:

```text
VectorAdd
```

có thể lower thành:

```text
AVX2_ADD
SVE_ADD
RVV_ADD
scalar loop
```

---

# 213.93. Instruction selection

Backend sử dụng:

```text
pattern matching
cost model
target constraints
```

---

# 213.94. Machine verifier

Trước machine encoding:

```text
MachineVerifier
```

kiểm tra:

```text
register constraints
operand types
feature requirements
ABI
clobbers
instruction legality
```

---

# 213.95. Illegal instruction prevention

Không được tạo machine code nếu:

```text
required feature
```

không tồn tại trong selected target.

---

# 213.96. Object metadata

Object có thể lưu:

```text
required CPU features
minimum ISA
ABI
```

để linker/build system kiểm tra.

---

# 213.97. Link-time feature validation

Nếu object A yêu cầu:

```text
AVX2
```

target binary không hỗ trợ:

```text
link/build error
```

hoặc dispatch variant isolation nếu artifact được thiết kế cho multi-versioning.

---

# 213.98. AI/compiler interface

`ax inspect` có thể trả:

```text
function: matrix_mul
required_features:
  - AVX2
  - FMA

vectorized: yes
vector_width: 8
unroll_factor: 4
estimated_register_pressure: 22
fallback: scalar
```

AI có thể sử dụng **fact này**, không phải đoán từ assembly.

---

# 213.99. Hardware optimization invariants — `AHW`

### `AHW-20`
Core semantics shall remain ISA-independent.

### `AHW-21`
ISA features shall be represented as target capabilities.

### `AHW-22`
Unsupported instructions shall never be emitted for a target.

### `AHW-23`
Target features shall not silently alter language semantics.

### `AHW-24`
Feature-dependent code shall have explicit target contracts.

### `AHW-25`
Function multiversioning shall preserve one logical API.

### `AHW-26`
Runtime dispatch shall be removable when target features are statically known.

### `AHW-27`
Vector semantics shall remain distinct from physical register width.

### `AHW-28`
Scalable vector ISAs shall be representable without hard-coding vector length into Core semantics.

### `AHW-29`
SIMD transformations shall preserve ownership and capability rules.

### `AHW-30`
Compiler-derived NoAlias shall require proof.

### `AHW-31`
Unknown aliasing shall never justify unsafe vectorization.

### `AHW-32`
Runtime alias checks may guard optimized implementations only when fallback semantics are equivalent.

### `AHW-33`
Alignment-sensitive instructions shall require proven or contracted alignment.

### `AHW-34`
Floating-point contraction shall respect the active numerical profile.

### `AHW-35`
Constant-time contracts shall constrain backend instruction selection.

### `AHW-36`
Crypto acceleration shall preserve security semantics.

### `AHW-37`
Instruction scheduling shall preserve memory, atomic, volatile, and assembly ordering constraints.

### `AHW-38`
Inline assembly shall declare machine-visible effects.

### `AHW-39`
Assembly clobbers shall participate in register allocation.

### `AHW-40`
Internal calling conventions may be optimized independently of stable ABI contracts.

### `AHW-41`
Stable ABI boundaries shall preserve their declared representation and calling convention.

### `AHW-42`
Register allocation shall remain an implementation detail unless explicitly exposed by a system contract.

### `AHW-43`
Spilling shall not alter semantic storage identity.

### `AHW-44`
Machine legalization shall precede final instruction encoding.

### `AHW-45`
Machine verification shall reject illegal register/instruction/feature combinations.

### `AHW-46`
Object artifacts shall retain required target feature information where necessary.

### `AHW-47`
Generic specialization shall remain bounded by compiler cost policies.

### `AHW-48`
ISA-specific optimization shall not require ISA-specific source languages.

### `AHW-49`
Target-specific intrinsics shall remain explicitly target-gated.

### `AHW-50`
Portable vector APIs shall remain available independently of specific ISA intrinsics.

### `AHW-51`
CPU dispatch shall preserve semantic equivalence among implementations.

### `AHW-52`
PGO may influence hardware optimization but shall not alter semantics.

### `AHW-53`
Security hardening shall remain independent from ordinary language semantics.

### `AHW-54`
Hardware optimization metadata shall be queryable through CompilerDB.

### `AHW-55`
AI tooling shall consume compiler-proven hardware facts rather than infer correctness from assembly.

### `AHW-56`
Axiom shall support architecture-specific optimization without architecture-specific Core syntax.

### `AHW-57`
Backend cost models shall never be correctness authorities.

### `AHW-58`
Target microarchitecture models may evolve independently from language semantics.

### `AHW-59`
Axiom shall support CPU, GPU, accelerator, and future ISA backends through the same semantic pipeline.

### `AHW-60`
New hardware instructions shall be integrable without redesigning Core language semantics.

---

# 213.100. Kiến trúc quan trọng nhất

Sau 213, Axiom có thể đạt một nguyên tắc rất mạnh:

```text
                 Axiom Source
                      │
                semantic intent
                      │
                      ▼
                 Generic MIR
                      │
          ┌───────────┴───────────┐
          │                       │
      CPU target              GPU target
          │                       │
    ┌─────┼─────┐             ┌───┼───┐
    ▼     ▼     ▼             ▼   ▼   ▼
  x86    ARM   RISC-V        GPU NPU TPU
    │
 ┌──┼─────────────┐
 ▼  ▼             ▼
SSE AVX2        AVX512/AMX
```

Programmer **không cần viết một ngôn ngữ mới cho mỗi phần cứng**.

Đó là một trong những điểm khác biệt quan trọng giữa Axiom và cách tiếp cận "intrinsics everywhere".

---

# BOOTSTRAP-214 — Compiler Self-Hosting, Bootstrap Trust, Reproducible Compiler & Compiler-as-Program

**TRẠNG THÁI: NEXT**

Đến đây Axiom đã có gần như toàn bộ **language/runtime/platform architecture**. Bước tiếp theo nên quay ngược lại chính compiler.

214 sẽ thiết kế vấn đề cực quan trọng:

```text
Axiom Compiler
    │
    ├── Lexer
    ├── Parser
    ├── Resolver
    ├── Type Checker
    ├── Trait Solver
    ├── Comptime
    ├── HIR
    ├── MIR
    ├── Verifier
    ├── Optimizer
    ├── LIR
    ├── Backend
    ├── Object Writer
    ├── Linker
    └── Build System
             │
             ▼
       Axiom Compiler
```

Trọng tâm sẽ là:

> **Làm thế nào để Axiom tự biên dịch chính nó, bootstrap từ compiler ngoài sang compiler Axiom-native, kiểm chứng compiler không tự phá semantics, và cuối cùng có một toolchain hoàn toàn self-hosted mà không phụ thuộc compiler/linker bên thứ ba?**

Đặc biệt sẽ xử lý:

```text
Stage 0 bootstrap
Stage 1 Axiom frontend
Stage 2 Axiom backend
Stage 3 Axiom linker
Stage 4 self-host
Stage 5 compiler self-build
Stage 6 reproducible bootstrap
Stage 7 diverse double compilation
Stage 8 compiler trust root
Stage 9 self-hosted release toolchain
```

Đây sẽ là bước chuyển từ **“thiết kế một ngôn ngữ”** sang **“thiết kế một hệ sinh thái compiler hoàn chỉnh có khả năng tự tồn tại.”**