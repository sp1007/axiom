# BOOTSTRAP-147 — CPU Microarchitecture-Aware Optimization & Instruction-Level Optimization
**STATUS: FROZEN / COMPLETED**

> **Axiom tối ưu theo đặc tính của CPU mục tiêu, nhưng không đưa kiến thức về từng CPU cụ thể vào semantics của ngôn ngữ.**

Đây là tầng tối ưu ngay trước Machine IR, nối khoảng cách giữa **OptIR cấp chương trình** và **thực tế pipeline của CPU**.

---

## 1. Vị trí trong compiler

```text
Verified MIR
    ↓
SSA + MemorySSA
    ↓
OptIR
    ↓
Loop / Memory / Data Layout / Vectorization
    ↓
Interprocedural Optimization
    ↓
Optimized OptIR
    ↓
CPU Microarchitecture Optimization
    ├─ Target Cost Model
    ├─ Instruction Selection Hints
    ├─ Dependency Analysis
    ├─ Register Pressure Analysis
    ├─ Branch Optimization
    ├─ Instruction Fusion
    ├─ Scheduling
    └─ Pipeline Optimization
    ↓
ABI MIR
    ↓
Axiom LIR
    ↓
Machine IR
```

Điểm quan trọng:

**147 không thay thế LIR/Backend.**

Nó quyết định *chiến lược* tối ưu; backend quyết định chính xác instruction encoding.

---

# 2. Không hard-code từng CPU

Axiom không nên có kiểu:

```text
if CPU == Intel 14900K:
    ...
else if CPU == AMD 9950X:
    ...
```

Điều đó sẽ nhanh chóng trở thành một compiler maintenance nightmare.

Thay vào đó:

```text
Target ISA
    +
Target Microarchitecture Profile
    +
Measured/Declared Cost Model
    +
Optimization Policy
```

Ví dụ:

```text
x86-64
 ├── generic
 ├── modern-intel
 └── modern-amd

AArch64
 ├── generic
 ├── apple-like
 └── arm-server

RISC-V
 ├── rv64-generic
 └── vendor-profile
```

Microarchitecture profile chỉ là **optimization data**, không phải language semantics.

---

# 3. TargetCostModel

Compiler cần một abstraction:

```text
TargetCostModel {
    instruction_latency
    instruction_throughput
    uop_count
    register_pressure
    load_cost
    store_cost
    branch_cost
    mispredict_cost
    vector_cost
    call_cost
    spill_cost
    dependency_cost
    fusion_bonus
    instruction_size
    alignment_cost
}
```

Các con số không phải semantics.

Ví dụ:

```text
ADD:
    latency    = 1
    throughput = 0.25

DIV:
    latency    = high
    throughput = low
```

Compiler không được biến những con số này thành quy tắc ngôn ngữ.

---

# 4. Latency và Throughput

Compiler phải phân biệt:

### Latency

Bao lâu trước khi kết quả có thể được sử dụng.

```text
a = ...
b = expensive(a)
c = b + 1
```

Nếu `expensive` có dependency chain dài:

```text
a → b → c → d → e
```

thì latency rất quan trọng.

### Throughput

Bao nhiêu instruction có thể hoàn thành mỗi chu kỳ khi pipeline đầy.

Ví dụ:

```text
for (...) {
    a[i] += b[i];
}
```

Có thể có rất nhiều phép toán độc lập:

```text
a0 + b0
a1 + b1
a2 + b2
a3 + b3
```

Compiler ưu tiên throughput và instruction-level parallelism.

---

# 5. Dependency Analysis

Axiom xây dựng dependency graph:

```text
Instruction
    ↓
Register dependency
Memory dependency
Control dependency
Atomic dependency
Volatile dependency
```

Ví dụ:

```text
a = x + y
b = a * 2
c = p + q
d = c * 3
```

Graph:

```text
x ─┐
   ├→ a → b
y ─┘

p ─┐
   ├→ c → d
q ─┘
```

Compiler có thể thực hiện:

```text
a
c
b
d
```

thay vì bị khóa bởi thứ tự source.

Nhưng **evaluation order semantic của Axiom vẫn phải được bảo toàn**.

Chỉ các phép tính không có observable dependency mới được reorder.

---

# 6. Register Pressure

Đây là một trong những vấn đề quan trọng nhất.

Ví dụ compiler inline quá nhiều:

```text
f()
g()
h()
i()
j()
k()
```

có thể giảm số call nhưng tạo quá nhiều live values:

```text
r1
r2
r3
...
r40
```

CPU chỉ có số register hữu hạn.

Kết quả:

```text
register
   ↓
spill
   ↓
stack
   ↓
load/store
```

Có thể làm code **chậm hơn** dù số instruction logic ít hơn.

Do đó CostModel phải cân bằng:

```text
Inlining benefit
       vs
Register pressure
       vs
Code size
       vs
Cache pressure
```

---

# 7. Register-pressure-aware optimization

Compiler phải có:

```text
RegisterPressureAnalysis
```

cho từng basic block / loop.

Ví dụ:

```text
Pressure = number of simultaneously-live register values
```

Khi pressure quá cao:

```text
prefer:
    recomputation
    smaller inline
    less unrolling
    shorter live ranges
    rematerialization
```

thay vì:

```text
spill everything
```

---

# 8. Dependency Breaking

Một dependency chain dài có thể được phá nếu semantic cho phép.

Ví dụ:

```text
x = x + a
x = x + b
x = x + c
x = x + d
```

có dependency:

```text
x → x → x → x
```

Compiler có thể biến thành:

```text
x1 = x + a
x2 = x + b
x3 = x + c
x4 = x + d

x = x1 + x2 + x3 + x4
```

nếu semantics cho phép.

Đây là **reassociation**, nhưng phải đặc biệt cẩn thận với floating-point.

Axiom không được tự ý biến:

```text
f64
```

thành fast-math.

Chỉ khi floating-point mode cho phép.

---

# 9. Instruction Fusion

Compiler nên nhận biết những pattern mà CPU có thể fuse.

Ví dụ:

```text
compare
+
conditional branch
```

hoặc:

```text
multiply
+
add
```

có thể map thành:

```text
FMA
```

khi FP semantics cho phép.

OptIR có thể giữ:

```text
a * b + c
```

Machine backend quyết định:

```text
FMA
```

hay:

```text
MUL
ADD
```

Không nên đưa `FMA` vào Core language semantics.

---

# 10. x86-64

x86-64 cần backend đặc biệt mạnh vì:

- nhiều addressing modes;
- FLAGS;
- variable-length instructions;
- macro-fusion;
- micro-op decomposition;
- register classes phức tạp;
- SIMD generations;
- AVX/AVX2/AVX-512;
- instruction-size effects.

Axiom không cần expose tất cả cho programmer.

Compiler có:

```text
X86CostModel
X86InstructionSelector
X86Scheduler
X86RegisterAllocator
X86Peephole
```

---

# 11. AVX/SSE transition

Đây là vấn đề backend cần hiểu.

Compiler không nên chỉ nghĩ:

```text
vector instruction = faster
```

mà phải xem:

```text
vector width
register pressure
target ISA
instruction domain
transition penalties
spill cost
frequency effects
```

Ví dụ compiler có thể chọn:

```text
scalar
128-bit SIMD
256-bit SIMD
512-bit SIMD
```

dựa trên target.

Source code vẫn chỉ có:

```ax
for i in 0..n {
    out[i] = a[i] + b[i];
}
```

Không cần programmer viết:

```text
_mm256_add_ps(...)
```

trừ khi programmer thực sự muốn explicit SIMD API.

---

# 12. Branch Optimization

Branch prediction ảnh hưởng rất lớn đến hiệu năng.

Compiler phân tích:

```text
BranchProbability
BranchFrequency
LoopDepth
Hotness
PGO data
```

Ví dụ:

```ax
if condition {
    hot_path()
} else {
    cold_path()
}
```

Compiler có thể layout:

```text
HOT
HOT
HOT
...
COLD
```

để giảm instruction-cache pressure và branch penalties.

---

# 13. Branchless optimization

Một branch:

```text
if x > 0 {
    a
} else {
    b
}
```

có thể được biến thành:

```text
conditional select
```

nếu:

- cả hai path đều an toàn;
- không có observable effect bị thay đổi;
- cost model cho thấy có lợi.

Không được biến thành branchless chỉ vì “branchless luôn nhanh hơn”.

---

# 14. Loop-aware microarchitecture optimization

Loop là nơi tầng 147 phối hợp mạnh nhất với:

- 143 Loop Optimization
- 145 Memory Optimization
- 146 Data Layout
- SIMD/vectorization

Ví dụ:

```ax
for i in 0..n {
    out[i] = a[i] * scale + bias;
}
```

Compiler có thể tạo:

```text
vector load
vector multiply
vector add
vector store
```

sau đó scheduler tiếp tục tối ưu:

```text
load
load
compute
load
compute
store
...
```

để che latency bộ nhớ.

---

# 15. Software pipelining

Với loop phù hợp, compiler có thể overlap:

```text
iteration N:
    load

iteration N-1:
    compute

iteration N-2:
    store
```

thành pipeline:

```text
LOAD → COMPUTE → STORE
   ↘       ↘        ↘
      next iteration
```

Nhưng chỉ thực hiện nếu:

- dependency hợp lệ;
- register pressure chấp nhận được;
- memory behavior phù hợp;
- target cost model cho thấy lợi ích.

---

# 16. Instruction Scheduling

Scheduler hoạt động trên Machine IR/LIR gần cuối pipeline.

Mục tiêu:

```text
maximize ILP
minimize stalls
minimize register pressure
preserve dependencies
```

Không chỉ đơn giản:

```text
sort instructions by latency
```

mà phải xét:

```text
Data dependency
Memory dependency
Register pressure
Port/resource pressure
Branch boundaries
Atomic ordering
Volatile
Call clobbers
```

---

# 17. Port/resource pressure

Trên CPU hiện đại, không phải mọi instruction đều cạnh tranh cùng một tài nguyên.

Compiler có thể model:

```text
ExecutionResource
    ├── Integer ALU
    ├── FP
    ├── Load
    ├── Store
    ├── Vector
    └── Branch
```

Cost model dùng thông tin này để tránh tạo ra:

```text
10 load-heavy instructions
```

trong khi execution resources khác đang rảnh.

---

# 18. Machine-aware peephole

Sau instruction selection:

```text
Machine IR
```

có thể xuất hiện pattern:

```text
MOV R1, 0
ADD R1, R2
```

có thể thay bằng instruction tốt hơn tùy ISA.

Nhưng peephole optimizer phải:

```text
local
target-specific
semantics-preserving
```

Không được trở thành nơi chứa semantic logic.

---

# 19. AArch64

AArch64 cần cost model riêng:

```text
AArch64CostModel
AArch64Selector
AArch64Scheduler
AArch64RegisterAllocator
```

Compiler cần hiểu:

- fixed 32-bit instruction encoding;
- register model;
- addressing modes;
- conditional select;
- SIMD/NEON;
- SVE/SVE2 nếu target hỗ trợ;
- load/store behavior;
- branch structure.

Nhưng cùng một OptIR có thể dùng lại:

```text
x86 backend
AArch64 backend
RISC-V backend
```

---

# 20. RISC-V

RISC-V càng cho thấy lý do phải tách:

```text
ISA
vs
microarchitecture
```

Ví dụ:

```text
RV64I
RV64GC
RV64 + vector
vendor extensions
```

Compiler không nên giả định mọi RV64 CPU có cùng throughput/latency.

---

# 21. CPU Feature Model

Axiom dùng:

```text
TargetFeatures
```

ví dụ:

```text
x86:
    sse2
    avx
    avx2
    avx512

arm:
    neon
    sve
    sve2

riscv:
    M
    A
    F
    D
    V
```

Nhưng:

```text
ISA feature ≠ microarchitecture performance
```

ISA nói:

> instruction này tồn tại.

Microarchitecture nói:

> instruction này chạy như thế nào trên CPU cụ thể.

---

# 22. Multi-versioning

Axiom có thể hỗ trợ:

```text
generic version
optimized version
```

Ví dụ conceptually:

```text
foo_generic()
foo_avx2()
foo_avx512()
```

Runtime dispatch chọn implementation phù hợp.

Đây là system/library/compiler feature, không làm thay đổi semantics của `foo`.

---

# 23. Profile-Guided Optimization

PGO cung cấp:

```text
actual branch frequency
actual hot functions
actual loop hotness
actual call targets
```

Compiler có thể dùng để:

```text
inline
devirtualize
reorder blocks
split hot/cold
specialize
unroll
vectorize
```

PGO chỉ thay đổi **optimization decisions**, không thay đổi chương trình có nghĩa gì.

---

# 24. CPU model không được làm compiler phụ thuộc vào một CPU

Kiến trúc cuối:

```text
                ┌────────────────────┐
                │   Target ISA       │
                └─────────┬──────────┘
                          ↓
                ┌────────────────────┐
                │ Generic Cost Model │
                └─────────┬──────────┘
                          ↓
                ┌────────────────────┐
                │ Microarch Profile  │
                └─────────┬──────────┘
                          ↓
                ┌────────────────────┐
                │ Optimization Policy│
                └─────────┬──────────┘
                          ↓
                       Machine
```

Về lâu dài có thể có:

```text
static target profile
dynamic CPU dispatch
PGO profile
user benchmark profile
```

nhưng tất cả chỉ ảnh hưởng optimizer.

---

# 25. Optimization correctness boundary

Đây là invariant cực kỳ quan trọng:

```text
Verified MIR
    ↓
Optimization
    ↓
Machine
```

Optimization **không được tạo safety proof**.

Ví dụ:

```text
UNKNOWN alias
```

không được scheduler tự suy ra:

```text
NO_ALIAS
```

Tương tự:

```text
atomic
volatile
FFI
panic
Drop
ownership
capability
```

đều là semantic constraints mà scheduler phải tôn trọng.

---

# 26. Memory ordering

CPU scheduler không được reorder:

```text
Release
Acquire
SeqCst
```

theo cách phá vỡ Axiom memory model.

Ví dụ:

```ax
atomic_store(x, 1, Release);
atomic_load(y, Acquire);
```

không thể biến thành một thứ tự máy khác làm thay đổi happens-before semantics.

Tầng microarchitecture phải nhận:

```text
MemoryEffect
Ordering
Synchronization
```

từ OptIR/LIR.

---

# 27. Compiler barriers và CPU fences

Phải giữ riêng:

```text
CompilerBarrier
CPUFence
Atomic
Volatile
```

Không được coi chúng là cùng một thứ.

Ví dụ:

```text
compiler barrier
```

có thể chỉ cấm compiler reorder.

Trong khi:

```text
CPU fence
```

tạo semantics ở processor memory-order level.

---

# 28. Cost model phải có confidence

Một điểm tôi đề xuất thêm cho Axiom:

```text
CostEstimate {
    value
    source
    confidence
}
```

Ví dụ:

```text
latency = 4
source = target_profile
confidence = high
```

hoặc:

```text
vectorization_gain = estimated
confidence = medium
```

Điều này giúp compiler/AI giải thích:

```text
Why was this loop not vectorized?
```

Không chỉ:

> cost too high

mà:

```text
Vectorization rejected.

Reason:
- estimated register pressure: high
- estimated spill cost: high
- target vector width: 256
- expected speedup: low
```

---

# 29. AI Compiler Interface

Axiom compiler nên expose:

```text
axc inspect microarch foo
axc inspect schedule foo
axc inspect pressure foo
axc inspect branches foo
axc inspect instructions foo
axc inspect target-cost foo
```

Ví dụ:

```text
Function: process_particles

Loop #2
  vectorized: yes
  vector width: 8
  estimated speedup: 3.1x

Register pressure:
  before: 11
  after: 14

Branch:
  predicted hot path: 94%

Instruction fusion:
  FMA: 6
  compare+branch fusion: 3
```

Đây sẽ rất hữu ích cho AI agent khi tối ưu code.

---

# 30. Invariants

Đóng băng:

### `AMICRO-20`
Microarchitecture optimization never changes Axiom semantics.

### `AMICRO-21`
ISA semantics and microarchitecture cost are distinct.

### `AMICRO-22`
Cost models influence optimization decisions only.

### `AMICRO-23`
Latency and throughput are distinct cost dimensions.

### `AMICRO-24`
Register pressure must participate in profitability decisions.

### `AMICRO-25`
Spill cost must be modeled explicitly.

### `AMICRO-26`
Instruction scheduling preserves all semantic dependencies.

### `AMICRO-27`
Memory, atomic, volatile and foreign effects constrain scheduling.

### `AMICRO-28`
Instruction fusion requires semantic equivalence.

### `AMICRO-29`
Floating-point reassociation requires permitted FP semantics.

### `AMICRO-30`
Branch optimization preserves observable evaluation order.

### `AMICRO-31`
Branchless transformation is optional optimization, not semantic lowering.

### `AMICRO-32`
SIMD selection depends on target capabilities and legality.

### `AMICRO-33`
AVX/SSE/vector-domain interactions are backend concerns.

### `AMICRO-34`
ISA feature availability and microarchitectural performance are separate.

### `AMICRO-35`
PGO changes profitability decisions, never semantics.

### `AMICRO-36`
CPU-specific profiles must not become language semantics.

### `AMICRO-37`
Optimization must remain valid on the declared target profile.

### `AMICRO-38`
Unknown aliasing cannot be converted into NoAlias by cost optimization.

### `AMICRO-39`
Optimization cannot weaken ownership/capability verification.

### `AMICRO-40`
Optimization cannot create a safety proof.

### `AMICRO-41`
Machine scheduling is deterministic under reproducible configuration.

### `AMICRO-42`
Target-specific optimization remains isolated from Core language semantics.

### `AMICRO-43`
Cost-model uncertainty may reduce optimization aggressiveness but never invalidate correctness.

### `AMICRO-44`
Source→MIR→OptIR→LIR→Machine provenance must remain inspectable.

### `AMICRO-45`
AI-facing optimization explanations must identify the rejected/selected transformation and its relevant constraints.

---

# Kết quả

Pipeline Axiom hiện đã tiến tới:

```text
SOURCE
 ↓
HIR
 ↓
MIR
 ↓
VERIFICATION
 ↓
VERIFIED MIR
 ↓
Alias
 ↓
Effect
 ↓
Escape
 ↓
SSA + MemorySSA
 ↓
OptIR
 ↓
Interprocedural
 ↓
Inlining / Specialization / Devirtualization
 ↓
Loop Optimization
 ↓
Memory Optimization
 ↓
Data Layout Optimization
 ↓
Vectorization
 ↓
CPU Microarchitecture Optimization   ← 147
 ↓
ABI MIR
 ↓
Axiom LIR
 ↓
Machine IR
 ↓
Register Allocation
 ↓
Machine Scheduling
 ↓
Machine Encoding
 ↓
Object
 ↓
Link
 ↓
Native Binary
```

Điểm rất quan trọng là Axiom lúc này **không còn chỉ là “ngôn ngữ có optimizer mạnh”**. Chúng ta đang hình thành một compiler architecture có khả năng đi từ semantic ownership/capability ở đầu pipeline xuống tận **cache, SIMD, register pressure, instruction scheduling và CPU pipeline** mà không bắt lập trình viên phải viết những chi tiết đó.

---

# BOOTSTRAP-148 — Vectorization, SIMD & Auto-Vectorization Engine

Task tiếp theo nên tập trung vào một tầng rất quan trọng còn thiếu: **vectorization thực sự**.

Nó sẽ nối:

```text
Loop Analysis
     ↓
Memory Dependence
     ↓
Alias/Range Proof
     ↓
Data Layout
     ↓
Vector Legality
     ↓
Vector Cost Model
     ↓
SIMD Transformation
     ↓
Vector Width Selection
     ↓
Epilogue / Remainder Handling
     ↓
Masked Vectorization
     ↓
Target ISA
```

Đặc biệt cần giải quyết một câu hỏi quan trọng cho Axiom:

> Làm thế nào để code kiểu

```ax
for i in 0..n {
    out[i] = a[i] + b[i];
}
```

tự động trở thành SIMD code **mà không cần pointer, `restrict`, intrinsic, unsafe hay annotation vectorization**, nhưng vẫn đảm bảo tuyệt đối semantics của `view`, `mut_view`, aliasing, bounds, floating-point và GPU?

Đây sẽ là bước rất đáng làm tiếp theo.