# BOOTSTRAP-149 — Profile-Guided Optimization, Feedback-Directed Compilation & Auto-Tuning
**STATUS: FROZEN / COMPLETED**

> **Axiom cho phép compiler học từ hành vi thực tế của chương trình để chọn cách tối ưu tốt hơn, nhưng profile chỉ được phép thay đổi chiến lược tối ưu — tuyệt đối không thay đổi semantics.**

Đây là tầng biến compiler từ:

```text
"đoán cách tối ưu"
```

thành:

```text
"đoán → đo thực tế → học → biên dịch lại"
```

---

## 1. Vị trí trong toàn pipeline

```text id="pgo001"
SOURCE
  ↓
Semantic Compilation
  ↓
Verified MIR
  ↓
Optimization
  ↓
Instrumented Binary
  ↓
REAL EXECUTION
  ↓
Profile Collection
  ↓
Profile Database
  ↓
Feedback Analysis
  ↓
Optimized Compilation
  ├── Inlining
  ├── Specialization
  ├── Devirtualization
  ├── Loop Optimization
  ├── Vectorization
  ├── Data Layout
  ├── Branch Layout
  ├── Code Splitting
  └── CPU Scheduling
  ↓
Final Binary
```

---

# 2. PGO không phải một phần của language semantics

Điểm này phải đóng băng:

```text
Program semantics
        ≠
Profile
        ≠
Optimization decision
```

Nếu không có profile:

```text
Program → valid binary
```

Có profile:

```text
Program + profile → different optimization
```

nhưng:

```text
Semantics(program)
=
Semantics(program + profile)
```

---

# 3. ProfileData

Axiom nên có một profile database riêng:

```text id="pgo002"
ProfileDB {
    FunctionProfile
    CallProfile
    BranchProfile
    LoopProfile
    ValueProfile
    MemoryProfile
    AllocationProfile
    VectorProfile
    TypeProfile
    TargetProfile
}
```

Không nhúng profile trực tiếp vào source code.

---

# 4. Function hotness

Compiler thu thập:

```text id="pgo003"
function call count
function execution time
inclusive time
exclusive time
```

Ví dụ:

```text id="pgo004"
process()
    calls: 2,401,839,211
    hotness: VERY_HOT

parse()
    calls: 2,193
    hotness: COLD
```

Compiler có thể:

```text
VERY_HOT → aggressive optimization
COLD → optimize for size
```

---

# 5. Call profile

Ví dụ:

```ax id="pgo005"
process(item)
```

gọi:

```text
transform(item)
```

Nếu `transform` là dynamic dispatch:

```text id="pgo006"
transform
 ├── impl A: 96.4%
 ├── impl B: 3.1%
 └── impl C: 0.5%
```

Compiler có thể tạo:

```text id="pgo007"
if likely A:
    direct A
else:
    generic dispatch
```

Đây là **profile-guided devirtualization**.

---

# 6. Branch profile

Ví dụ:

```ax id="pgo008"
if condition {
    hot()
} else {
    rare()
}
```

Profile:

```text id="pgo009"
true  = 99.2%
false = 0.8%
```

Compiler có thể:

- layout hot block trước;
- cold block tách ra;
- chọn branch direction;
- tối ưu instruction cache;
- cân nhắc branchless transformation.

Nhưng không được giả định `true` luôn đúng.

Profile chỉ là **prediction**.

---

# 7. Profile không phải proof

Đây là invariant cực kỳ quan trọng.

Nếu profile nói:

```text id="pgo010"
condition == true: 100%
```

compiler **không được biến**:

```text id="pgo011"
if condition
```

thành:

```text id="pgo012"
always true
```

trừ khi có semantic proof độc lập.

Profile:

```text id="pgo013"
likely
```

không phải:

```text id="pgo014"
proven
```

---

# 8. Loop profile

Compiler thu thập:

```text id="pgo015"
trip count
min trip count
max trip count
average trip count
distribution
hotness
```

Ví dụ:

```text id="pgo016"
Loop #4

average iterations: 128
median: 96
95 percentile: 512
```

Điều này cực kỳ hữu ích cho:

- unrolling;
- vectorization;
- peeling;
- versioning;
- prefetch;
- branch optimization.

---

# 9. Value profiling

Ví dụ:

```ax id="pgo017"
switch opcode {
    ...
}
```

Profile:

```text id="pgo018"
ADD = 70%
MOV = 20%
MUL = 8%
other = 2%
```

Compiler có thể sắp xếp hot cases trước.

Hoặc với indirect call:

```text id="pgo019"
target A = 91%
target B = 7%
target C = 2%
```

có thể tạo guarded fast path.

---

# 10. Type profiling

Trong generic/dynamic code:

```text id="pgo020"
dyn Trait
```

runtime có thể quan sát concrete type.

Profile:

```text id="pgo021"
TypeA = 94%
TypeB = 5%
TypeC = 1%
```

Compiler có thể:

```text id="pgo022"
if type == TypeA {
    specialized fast path
} else {
    generic path
}
```

Điều này rất mạnh khi kết hợp:

```text
149 PGO
+
142 Devirtualization
```

---

# 11. Allocation profiling

Compiler có thể biết:

```text id="pgo023"
allocation count
allocation size
lifetime
call site
escape behavior
```

Ví dụ:

```text id="pgo024"
foo():
    4,000,000 allocations
    average size = 64 bytes
```

Compiler có thể tối ưu:

```text id="pgo025"
stack promotion
scalar replacement
arena candidate
allocation elimination
```

nhưng chỉ khi semantics cho phép.

Profile không được tự ý biến một observable heap allocation thành stack allocation nếu allocation identity/address/storage semantics được chương trình quan sát.

---

# 12. Memory profile

Có thể thu thập:

```text id="pgo026"
cache miss
load/store hotness
working set
stride
branch locality
allocation locality
```

Sau đó hỗ trợ:

```text id="pgo027"
data layout
field ordering
hot/cold splitting
prefetch
loop transformation
SoA decisions
```

Đây là cầu nối trực tiếp với **BOOTSTRAP-146**.

---

# 13. PGO + Data Layout

Ví dụ:

```ax id="pgo028"
struct Particle {
    position: Vec3,
    velocity: Vec3,
    color: Color,
    debug_name: String,
    metadata: Metadata
}
```

Profile cho thấy:

```text id="pgo029"
position → 99%
velocity → 98%
color    → 97%

debug_name → 0.01%
metadata   → 0.001%
```

Compiler có thể cân nhắc:

```text id="pgo030"
hot fields together
cold fields separated
```

miễn là layout không observable theo contract.

---

# 14. PGO + Vectorization

Giả sử compiler có:

```text id="pgo031"
vector width 8
```

nhưng profile cho thấy:

```text id="pgo032"
n thường = 5
```

Vectorization có thể không đáng.

Ngược lại:

```text id="pgo033"
n thường = 1000000
```

thì vectorization + aggressive unrolling có thể đáng hơn.

Do đó:

```text id="pgo034"
VectorCost =
static cost
+
profile trip count
+
hotness
+
target cost
```

---

# 15. PGO + Inlining

Không inline tất cả function hot.

Ví dụ:

```text id="pgo035"
A hot
B hot
A calls B
```

Nếu `B` lớn:

```text id="pgo036"
inline B
```

có thể làm:

```text
instruction cache ↑
register pressure ↑
code size ↑
```

Do đó:

```text id="pgo037"
InlineProfit =
call_frequency
×
estimated_call_cost
+
exposed_optimization
-
code_size_cost
-
register_pressure_cost
```

---

# 16. PGO + Code Layout

Một executable có thể được sắp xếp:

```text id="pgo038"
.text.hot
.text
.text.cold
```

Các function thường gọi nhau được đặt gần nhau.

Mục tiêu:

```text id="pgo039"
instruction cache
iTLB
branch locality
code locality
```

COLD code có thể tách khỏi hot path.

---

# 17. Function splitting

Ví dụ:

```ax id="pgo040"
fn process() {
    fast_path();

    if rare_error {
        expensive_error_handling();
    }
}
```

Compiler có thể tạo concept:

```text id="pgo041"
process.hot
process.cold
```

Không phải programmer-visible function.

---

# 18. Sampling PGO

Không nhất thiết phải instrument mọi instruction.

Có thể dùng:

```text id="pgo042"
Sampling PGO
```

để giảm overhead.

Nguồn profile có thể gồm:

```text
instrumentation
sampling
hardware performance counters
runtime feedback
```

Tất cả được normalize thành:

```text id="pgo043"
Axiom Profile Format
```

---

# 19. Instrumentation PGO

Compiler tạo binary:

```text id="pgo044"
program.profile
```

runtime thu thập:

```text id="pgo045"
function counters
branch counters
call counters
value counters
loop counters
```

Sau đó:

```text
axc profile merge
```

gộp nhiều workload.

---

# 20. Profile merging

Ví dụ có:

```text id="pgo046"
profile-server.axprof
profile-desktop.axprof
profile-test.axprof
```

Compiler không đơn giản cộng mù.

Profile record có:

```text id="pgo047"
weight
source
timestamp
target
build identity
workload identity
```

để tránh profile không tương thích.

---

# 21. Profile validity

Một profile phải ghi:

```text id="pgo048"
Compiler semantic version
Target
Architecture
ABI
CPU features
Optimization configuration
Program fingerprint
Module fingerprint
Profile schema version
```

Nếu binary/source thay đổi quá lớn:

```text id="pgo049"
profile stale
```

Compiler có thể:

```text
reject
downgrade confidence
partially reuse
```

---

# 22. Semantic fingerprint

Axiom đã có:

```text id="pgo050"
SemanticFingerprint
```

149 sử dụng nó.

Profile nên gắn với:

```text id="pgo051"
FunctionSemanticFingerprint
```

thay vì chỉ:

```text
function_name
```

Như vậy rename function hoặc thay đổi source không tạo ra profile mapping sai.

---

# 23. Profile confidence

Mỗi profile datum nên có:

```text id="pgo052"
ProfileFact {
    value
    sample_count
    confidence
    age
    provenance
}
```

Ví dụ:

```text id="pgo053"
branch true = 98.7%
samples = 8,421,332
confidence = high
```

Nếu chỉ có:

```text
samples = 3
```

thì compiler không nên quá tin.

---

# 24. Profile decay

Profile cũ không nhất thiết bị xóa ngay.

Có thể dùng:

```text id="pgo054"
weighted history
```

Ví dụ:

```text id="pgo055"
recent profile: 80%
older profile: 20%
```

Nhưng điều này phải là **tooling/build policy**, không phải language semantics.

---

# 25. Auto-Tuning

Đây là phần mạnh hơn PGO.

Compiler có nhiều configuration:

```text id="pgo056"
unroll = 2
unroll = 4
unroll = 8

vector width = 128
vector width = 256
vector width = 512

inline threshold = ...
```

Auto-tuner có thể:

```text
generate candidate
        ↓
benchmark
        ↓
measure
        ↓
select candidate
```

Nhưng phải cực kỳ cẩn thận.

---

# 26. Auto-tuning không được benchmark tùy tiện

Axiom nên giới hạn:

```text id="pgo057"
AutoTuneScope
```

ví dụ:

```text
function
loop
module
whole program
```

và có:

```text id="pgo058"
time budget
iteration budget
measurement budget
```

Không để compiler vô tình chạy benchmark hàng giờ trong build bình thường.

---

# 27. Reproducibility

Auto-tuning có thể tạo kết quả khác nhau do:

```text id="pgo059"
CPU temperature
OS scheduling
background load
turbo frequency
noise
```

Do đó:

### Normal build

```text
deterministic heuristic
```

### Auto-tuned build

```text
profile-dependent build
```

Build artifact phải ghi rõ:

```text id="pgo060"
optimization feedback identity
```

---

# 28. Benchmark result không phải semantic input

Một benchmark chỉ quyết định:

```text id="pgo061"
candidate A vs B
```

Không quyết định:

```text
program meaning
```

Nếu measurement thất thường:

```text id="pgo062"
confidence ↓
```

chứ không được ảnh hưởng correctness.

---

# 29. Feedback loop

Kiến trúc đầy đủ:

```text id="pgo063"
                 ┌──────────────┐
                 │ Source       │
                 └──────┬───────┘
                        ↓
                 Instrumented Build
                        ↓
                    Execution
                        ↓
                 Profile Collection
                        ↓
                    Profile DB
                        ↓
                 Feedback Analysis
                        ↓
              Optimization Decisions
                        ↓
                  Final Binary
                        │
                        └──────→ next profile
```

Compiler dần có thể tối ưu tốt hơn theo workload thực tế.

---

# 30. PGO + CPU Microarchitecture

Đây là điểm rất quan trọng.

Static compiler:

```text id="pgo064"
"AVX2 có vẻ tốt"
```

Profile:

```text id="pgo065"
"loop này thật sự nóng"
```

Microarchitecture model:

```text id="pgo066"
"256-bit vector có cost X"
```

Kết hợp:

```text id="pgo067"
PGO
+
TargetCostModel
+
VectorCost
+
RegisterPressure
```

→ quyết định tốt hơn.

---

# 31. PGO + Memory Hierarchy

Profile có thể phát hiện:

```text id="pgo068"
L1 miss
L2 miss
LLC miss
branch miss
TLB miss
```

Compiler có thể điều chỉnh:

```text id="pgo069"
loop order
data layout
blocking/tiling
prefetch
code placement
```

Tuy nhiên hardware counters khác nhau giữa CPU.

Vì vậy Axiom phải normalize thành abstraction:

```text id="pgo070"
CacheMiss
BranchMiss
TLBMiss
MemoryLatency
```

Backend có thể map từ counter cụ thể.

---

# 32. Security

PGO không được làm mất các security semantics.

Ví dụ:

```text id="pgo071"
constant-time crypto
```

không được:

```text
PGO thấy branch luôn true
→ eliminate branch
```

nếu branch/data-dependent behavior là một phần của security contract.

Do đó nên có:

```text id="pgo072"
@constant_time
```

ở system/crypto layer nếu Axiom cần guarantee này.

Khi contract tồn tại, optimizer phải tôn trọng nó.

---

# 33. PGO và unsafe

Profile không thể làm:

```text id="pgo073"
UNKNOWN alias
```

thành:

```text
NO_ALIAS
```

chỉ vì runtime chưa từng quan sát overlap.

Profile chỉ cung cấp:

```text
observed behavior
```

không phải:

```text
proof of all possible executions
```

---

# 34. PGO và concurrency

Compiler không được suy luận:

```text id="pgo074"
"race chưa từng xảy ra"
```

→ program safe.

Safety vẫn do verifier quyết định.

PGO chỉ có thể giúp:

```text id="pgo075"
lock hotness
contention
scheduler policy
```

ở runtime/optimization level phù hợp.

---

# 35. PGO profile format

Đề xuất artifact:

```text id="pgo076"
.axprof
```

Cấu trúc:

```text
AxiomProfile {
    schema_version
    program_fingerprint
    target
    abi
    cpu_features

    functions[]
    calls[]
    branches[]
    loops[]
    values[]
    types[]
    memory[]
    allocations[]

    provenance
}
```

Binary format nên compact và deterministic.

---

# 36. CLI

Thêm:

```text id="pgo077"
axc profile instrument
axc profile run
axc profile merge
axc profile inspect
axc profile validate
axc build --profile-use=app.axprof
axc build --profile-generate
axc tune
```

AI có thể:

```text id="pgo078"
axc inspect profile foo
axc inspect profile foo --branches
axc inspect profile foo --loops
axc inspect profile foo --optimization-impact
```

---

# 37. Optimization explanation

Ví dụ:

```text id="pgo079"
Inlining decision: YES

Function: parse_token
Call frequency: 8.4M
Caller hotness: VERY_HOT

Estimated benefit:
    call overhead reduction
    constant propagation
    branch simplification

Estimated cost:
    +11 instructions
    +2 registers

Decision:
    INLINE
```

Hoặc:

```text id="pgo080"
Vector width: 256-bit

Profile:
    trip count median = 1024

Cost:
    vector setup = low
    register pressure = medium
    remainder = negligible

Decision:
    VECTORIZE
```

Điều này cực kỳ hữu ích cho AI agent.

---

# 38. Không để PGO làm compiler “học sai”

Có ba tầng niềm tin:

```text id="pgo081"
PROVEN
   ↑
OBSERVED
   ↑
HEURISTIC
```

### Proven

Từ semantic verifier.

### Observed

Từ runtime profile.

### Heuristic

Từ compiler cost model.

Không được trộn ba loại này.

Đây là một kiến trúc rất quan trọng.

---

# 39. Optimization decision model

Mọi transformation nên có:

```text id="pgo082"
Legality
Confidence
Profitability
```

Trong đó:

```text
Legality
    → semantic proof

Confidence
    → profile / analysis confidence

Profitability
    → target cost + profile
```

Ví dụ:

```text
Legality = PROVEN
Confidence = HIGH
Profitability = HIGH
→ transform
```

Không bao giờ:

```text
Legality = UNKNOWN
Confidence = HIGH
→ transform
```

---

# 40. Invariants

Đóng băng:

### `APGO-20`
Profile data never changes program semantics.

### `APGO-21`
Profile observations are not semantic proofs.

### `APGO-22`
Profile cannot establish ownership, capability, alias, safety or concurrency guarantees.

### `APGO-23`
Profile-guided optimization must remain valid for all semantically legal executions.

### `APGO-24`
Profile affects optimization profitability and strategy only.

### `APGO-25`
Profile validity is tied to program and target identity.

### `APGO-26`
Stale profiles must be rejected or assigned reduced confidence.

### `APGO-27`
Profile data has provenance and confidence.

### `APGO-28`
Function, call, branch, loop and value profiles are independently representable.

### `APGO-29`
PGO may guide inlining.

### `APGO-30`
PGO may guide specialization.

### `APGO-31`
PGO may guide devirtualization but cannot prove dynamic target identity.

### `APGO-32`
PGO may guide vectorization and vector width selection.

### `APGO-33`
PGO may guide loop unrolling and peeling.

### `APGO-34`
PGO may guide data-layout optimization only where layout is not semantically observable.

### `APGO-35`
PGO may guide hot/cold code splitting.

### `APGO-36`
PGO may guide branch layout.

### `APGO-37`
PGO may guide memory/cache optimization.

### `APGO-38`
PGO may guide CPU microarchitecture decisions.

### `APGO-39`
Auto-tuning results are optimization feedback, not semantic information.

### `APGO-40`
Auto-tuning must have explicit resource/time boundaries.

### `APGO-41`
Profile-dependent artifacts must record profile identity.

### `APGO-42`
Normal reproducible builds must not depend on uncontrolled external measurement noise.

### `APGO-43`
Security contracts constrain PGO transformations.

### `APGO-44`
Atomic, volatile, synchronization and FFI semantics constrain PGO transformations.

### `APGO-45`
Unknown analysis facts cannot become proven solely from observed executions.

### `APGO-46`
Optimization decisions distinguish legality from profitability.

### `APGO-47`
Profile confidence must not override semantic legality.

### `APGO-48`
PGO remains optional.

### `APGO-49`
Programs must compile and remain semantically valid without profile data.

### `APGO-50`
Profile data is inspectable and machine-readable.

### `APGO-51`
Profile transformations preserve source provenance.

### `APGO-52`
Profile analysis is deterministic given identical profile input and compiler configuration.

### `APGO-53`
PGO does not weaken the Verified MIR boundary.

---

# Kiến trúc tối ưu của Axiom hiện tại

Chúng ta đã hình thành gần như đầy đủ một **optimizing native compiler hiện đại**:

```text
                         SOURCE
                            ↓
                           HIR
                            ↓
                           MIR
                            ↓
                    ┌──────────────┐
                    │  VERIFIER    │
                    └──────┬───────┘
                           ↓
                     VERIFIED MIR
                           ↓
              ┌────────────┼────────────┐
              ↓            ↓            ↓
           Alias         Effect       Escape
              └────────────┼────────────┘
                           ↓
                    SSA + MemorySSA
                           ↓
                          OptIR
                           ↓
                  Interprocedural
                           ↓
              Inline / Specialize / Devirt
                           ↓
                     Loop Optimize
                           ↓
                    Memory Optimize
                           ↓
                    Data Layout
                           ↓
                     Vectorization
                           ↓
                 CPU Microarchitecture
                           ↓
                           PGO
                           ↓
                    Optimized OptIR
                           ↓
                       ABI MIR
                           ↓
                       Axiom LIR
                           ↓
                      Machine IR
                           ↓
                  Register Allocation
                           ↓
                       Scheduling
                           ↓
                      Machine Code
```

Điểm đặc biệt của kiến trúc này là **PGO nằm trên tất cả các optimizer**, thay vì là một optimizer độc lập. Nó cung cấp thông tin cho các optimizer khác.

---

# BOOTSTRAP-150 — Whole-Program Optimization, LTO & Link-Time Semantic Optimization

Bước tiếp theo nên xử lý **toàn bộ chương trình sau khi compiler đã nhìn thấy package graph + object graph + profile**.

Mục tiêu:

```text
Multiple Modules
      ↓
Multiple Packages
      ↓
Generic Instances
      ↓
Call Graph
      ↓
LTO
      ↓
Cross-Module Inlining
      ↓
Cross-Module Specialization
      ↓
Cross-Module Devirtualization
      ↓
Global DCE
      ↓
Global Data Layout
      ↓
Global Code Layout
      ↓
Final Native Binary
```

Đây sẽ là tầng rất quan trọng để đạt mục tiêu ban đầu của Axiom: **abstraction ở cấp package/module vẫn có thể biến mất hoàn toàn ở binary khi không có observable boundary**, đồng thời tận dụng `.axmeta`, SemanticFingerprint, PGO, generic specialization và linker để tối ưu xuyên toàn bộ chương trình.