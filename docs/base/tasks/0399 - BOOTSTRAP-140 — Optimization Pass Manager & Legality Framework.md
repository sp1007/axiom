# BOOTSTRAP-140 — Optimization Pass Manager & Legality Framework

**Trạng thái: FROZEN / COMPLETED**

Đây là phần khóa “bộ não điều phối” của optimizer Axiom. Từ đây, Axiom không chỉ có các optimization pass riêng lẻ, mà có một framework đảm bảo chúng **không bao giờ được phép đổi semantics chỉ để lấy performance**.

Nguyên tắc trung tâm:

> **Optimization is a proof-producing transformation, not a guess.**

---

# 1. Vị trí trong compiler

Pipeline chính thức:

```text
Verified MIR
    ↓
AliasInfo
EffectInfo
EscapeInfo
RangeInfo
LoopInfo
    ↓
SSA
    ↓
MemorySSA
    ↓
OptIR
    ↓
Optimization Pass Manager
    ↓
Optimized OptIR
    ↓
Representation Selection
    ↓
ABI Classification
    ↓
ABI MIR
```

`Verified MIR` vẫn là semantic source of truth.

---

# 2. Optimizer không được tự quyết semantics

Optimizer được phép:

```text
analyze
prove
transform
simplify
specialize
eliminate
reorder
vectorize
inline
```

Nhưng không được:

```text
invent ownership
invent no-alias
ignore Drop
ignore atomic ordering
ignore volatile
ignore IO
ignore panic semantics
ignore FFI effects
```

---

# 3. Pass Manager

Đề xuất:

```text
PassManager
 ├── AnalysisManager
 ├── TransformationManager
 ├── DependencyManager
 ├── LegalityEngine
 ├── InvalidationManager
 ├── CostModel
 ├── PipelinePlanner
 ├── VerificationHooks
 └── OptimizationRemarkDB
```

---

# 4. AnalysisManager

Quản lý các analysis:

```text
DominatorTree
PostDominatorTree
LoopInfo
ScalarEvolution
SSA
MemorySSA
AliasInfo
EffectInfo
EscapeInfo
RangeInfo
TargetInfo
CallGraph
ProfileInfo
```

Mỗi analysis có:

```text
AnalysisId
InputDependencies
Result
Revision
Validity
```

---

# 5. Transformation Pass

Mỗi pass có contract:

```text
Pass {
    id
    required_analyses
    preserved_analyses
    invalidated_analyses
    legality_rules
    cost_model
    transform()
}
```

Ví dụ:

```text
GVN {
    requires:
        DominatorTree
        MemorySSA
        AliasInfo
        EffectInfo

    preserves:
        OwnershipSemantics
        DropSemantics
        AtomicSemantics

    invalidates:
        selected SSA analyses
}
```

---

# 6. LegalityEngine

Đây là thành phần quan trọng.

Một transformation phải trả lời:

```text
IsLegal?
```

không phải:

```text
LooksSafe?
```

---

# 7. Proof result

Chuẩn hóa:

```text
ProofResult =
    Proven
    NotProven
    Contradicted
    Unknown
```

Không dùng boolean đơn giản.

Ví dụ:

```text
CanReorder(loadA, loadB)
    → Proven
```

hoặc:

```text
→ Unknown
```

thì pass **không được reorder**.

---

# 8. Optimization proof

Một transformation:

```text
T : Program A → Program B
```

chỉ hợp lệ nếu:

```text
ObservableSemantics(A) == ObservableSemantics(B)
```

trong phạm vi semantic model của Axiom.

---

# 9. Observable semantics

Bao gồm:

```text
return values
memory effects
IO
atomic behavior
volatile accesses
synchronization
panic behavior
Drop behavior
FFI-visible behavior
GPU-visible behavior
observable allocation identity
stable addresses
```

Không chỉ là “kết quả cuối cùng”.

---

# 10. Ví dụ DCE

```ax id="n7q2m4"
let x = compute();
return 10;
```

Có thể bỏ `compute()` **chỉ nếu** compiler chứng minh:

```text
Effects(compute) = none
Drop effects = none
IO = none
Panic = none
Allocation identity = unobservable
ExternalState = none
```

Nếu `compute()` có thể panic:

```text
compute()
```

không được xóa mặc định.

---

# 11. Dead Store Elimination

```ax id="r4m8p2"
x = 1;
x = 2;
use(x);
```

store `1` có thể bỏ nếu:

```text
no volatile
no atomic
no external observer
no address escape
no synchronization effect
```

---

# 12. Atomic không được DCE tùy tiện

```ax id="k5q3v8"
counter.fetch_add(1, Relaxed);
```

dù giá trị trả về không dùng, atomic operation vẫn có observable synchronization/atomic semantics tùy model.

Pass phải kiểm tra effect contract.

---

# 13. Volatile càng nghiêm ngặt

```ax id="p8n2m5"
volatile_store(device_reg, 1);
```

không được:

- DCE;
- CSE;
- reorder tùy tiện;
- merge tùy tiện.

---

# 14. IO

```ax id="v6r3q1"
print("A");
print("B");
```

Không được reorder.

Optimizer phải thấy:

```text
IO ordering dependency
```

---

# 15. Panic

Ví dụ:

```ax id="m2q7x4"
let x = 10 / y;
return 1;
```

Nếu `y == 0` có thể panic, không thể tùy tiện biến thành:

```text
return 1
```

trừ khi proof chứng minh `y != 0`.

---

# 16. Overflow

Vì Axiom không dùng signed-overflow UB:

```ax id="q8m4r1"
x + y
```

optimizer không được giả định:

```text
x + y cannot overflow
```

nếu semantic mode cho phép overflow defined.

Đây là điểm giúp Axiom tránh rất nhiều “compiler magic” nguy hiểm của C/C++.

---

# 17. InstCombine

Ví dụ:

```text
x + 0
```

có thể simplify nếu semantics cho phép.

Nhưng:

```text
x / x
```

không mặc định thành `1`.

Có thể có:

```text
x = 0
NaN
panic
overflow
```

tùy type/operation.

---

# 18. Fast Math

Floating-point phải có semantic profile.

Mặc định:

```text
StrictFP
```

Có thể có explicit:

```text
RelaxedFP
FastMath
```

ở compilation/configuration boundary phù hợp.

Optimizer không được tự bật fast-math.

---

# 19. Reassociation

Ví dụ:

```text
(a + b) + c
```

không mặc định đổi thành:

```text
a + (b + c)
```

với strict floating-point.

Integer cũng phải xét overflow semantics.

---

# 20. GVN/CSE

Global Value Numbering cần:

```text
same expression
same relevant memory state
same effects
same FP semantics
same atomic/volatile restrictions
```

MemorySSA + AliasInfo là nguồn chính để xác định memory state.

---

# 21. Load CSE

```ax id="f4q8m2"
a = x.value;
b = x.value;
```

có thể merge nếu giữa hai load:

```text
no clobber(x.value)
```

và không có observable memory effect làm thay đổi semantics.

---

# 22. Alias proof

Nếu:

```text id="k3m7p1"
write(R2)
```

và:

```text id="q8v4n6"
R1 NO_ALIAS R2
```

thì load R1 vẫn có thể được coi là available.

---

# 23. Inline

Inlining không phải chỉ là:

```text
function body → caller
```

Nó phải kiểm tra:

```text
code size
hotness
recursion
calling convention
effects
Drop
async
GPU
FFI
target features
```

---

# 24. Inline có thể làm thay đổi optimization opportunities

Ví dụ:

```ax id="m7r2q9"
foo(x)
```

sau inline:

```text
caller
  ↓
constant propagation
  ↓
branch elimination
  ↓
DCE
```

Do đó inlining được CostModel quyết định, nhưng legality vẫn là bắt buộc.

---

# 25. Devirtualization

```ax id="p5n8q3"
dyn Trait → method()
```

chỉ chuyển thành direct call khi concrete target được chứng minh.

Không được đoán.

---

# 26. Specialization

Generic:

```ax id="x3q7m2"
fn process<T: Trait>(x: T)
```

có thể tạo specialization:

```text
process_i32
process_MyType
```

nhưng semantics phải giống generic definition.

---

# 27. Code sharing

Không phải generic nào cũng cần duplicate machine code.

Nếu hai specialization có representation/behavior đủ tương thích:

```text
GenericInstance A
GenericInstance B
       ↓
 shared implementation
```

được phép.

---

# 28. Loop optimization

Pass Manager hỗ trợ:

```text
LoopSimplify
LoopRotate
LICM
InductionVariableSimplification
StrengthReduction
Unrolling
Peeling
Unswitching
Vectorization
Interleaving
```

---

# 29. LICM

Loop invariant:

```ax id="r6m2p8"
while i < n {
    x = config.value;
    ...
}
```

có thể đưa `x` ra ngoài loop nếu compiler chứng minh:

```text
config.value
```

không bị write/clobber trong loop.

MemorySSA + AliasInfo + EffectInfo phối hợp.

---

# 30. Bounds-check elimination

Axiom không cần programmer viết:

```text
unsafe
```

chỉ để bỏ bounds check.

Ví dụ:

```ax id="v7q3m1"
for i in 0..n {
    out[i] = input[i];
}
```

RangeInfo có thể chứng minh:

```text
0 <= i < n
n <= input.length
n <= out.length
```

→ bounds checks có thể biến mất.

---

# 31. Vectorization

Vectorizer cần proof:

```text
alias legality
range legality
dependency legality
overflow legality
FP legality
alignment
target features
```

Nếu không chứng minh được:

```text
scalar loop
```

vẫn hợp lệ.

---

# 32. Runtime versioning

Trong tương lai có thể:

```text
if runtime condition:
    vector path
else:
    scalar path
```

Nhưng runtime check chỉ là **optimization guard**.

Nó không thay thế safe verification.

---

# 33. Allocation optimization

Các pass:

```text
AllocationElimination
StackPromotion
ScalarReplacement
EscapeDrivenPromotion
BoxElimination
TemporaryElimination
```

dùng:

```text
EscapeInfo
AliasInfo
EffectInfo
Capability facts
ABI constraints
```

---

# 34. Không được biến shared thành unique

Ví dụ:

```text
Arc<T>
```

optimizer không được tự suy luận:

```text
Arc<T> → T
```

chỉ vì tại một điểm thấy một reference.

Phải chứng minh shared identity không observable.

---

# 35. Closure optimization

Closure:

```ax id="n4m8q2"
let f = |x| x + constant;
```

có thể:

```text
inline
eliminate environment
turn into function
```

nếu capture và identity không observable.

---

# 36. Async optimization

Có thể:

```text
FutureInlining
StateFieldElision
AwaitFusion
ReadyPathSpecialization
CoroutineDCE
StateSwitchOptimization
```

nhưng không được loại bỏ:

```text
observable suspension
cancellation semantics
waker behavior
in-flight operation ownership
```

---

# 37. GPU optimization

Các pass riêng:

```text
KernelInlining
KernelFusion
MemoryCoalescing
SharedMemoryPromotion
GPUVectorization
AddressSpacePromotion
LaunchOptimization
```

vẫn phải giữ:

```text
GPU memory model
atomic ordering
barrier semantics
host/device ownership
```

---

# 38. Pass pipeline không cố định cứng

Axiom nên có:

```text
PipelinePlanner
```

thay vì một chuỗi pass bất biến.

Ví dụ:

```text
-O0
-O1
-O2
-O3
-Os
-Oz
```

chỉ là **policy**.

Semantic result không được thay đổi.

---

# 39. `-O0` vẫn phải đúng

Đây là invariant rất quan trọng.

Nếu:

```text
-O0
```

và:

```text
-O3
```

cho semantics khác nhau:

```text
compiler bug
```

không phải “optimization behavior”.

---

# 40. Optimization levels

Đề xuất:

```text
-O0  minimal transformation
-O1  basic cleanup
-O2  full scalar optimization
-O3  aggressive loop/vector optimization
-Os  size-oriented
-Oz  extreme size
-Ofast  explicit relaxed semantic profile, nếu sau này cho phép
```

`-Ofast` không được âm thầm thay đổi Core semantics. Nếu có relaxed semantics, đó phải là một semantic/profile contract rõ ràng.

---

# 41. CostModel

Legality và profitability phải tách biệt.

```text
Legal ≠ Profitable
```

Ví dụ:

```text
Inlining = Legal
Inlining = NotProfitable
```

→ không inline.

---

# 42. CostModel

Có thể dùng:

```text
InstructionCost
CodeSizeCost
RegisterPressure
CacheCost
BranchCost
MemoryLatency
VectorWidth
CallOverhead
ProfileHotness
TargetFeatures
```

---

# 43. Profile-Guided Optimization

PGO cung cấp:

```text
hot/cold
branch probability
call frequency
loop trip counts
cache behavior estimates
```

Nhưng PGO không được thay đổi semantics.

---

# 44. Profile data không đáng tin tuyệt đối

Nếu profile:

```text
x = 99.9% true
```

compiler có thể optimize branch layout.

Nhưng không được giả định:

```text
x is always true
```

trừ khi có semantic proof.

---

# 45. Analysis invalidation

Ví dụ:

```text
Pass A modifies CFG
```

thì:

```text
DominatorTree
LoopInfo
SSA
MemorySSA
```

có thể bị invalid.

Pass Manager phải biết chính xác cái nào cần rebuild.

---

# 46. Preserved analyses

Nếu pass chỉ thay đổi arithmetic:

```text
x + 0 → x
```

có thể preserve:

```text
DominatorTree
LoopInfo
MemorySSA
AliasInfo
```

nếu thực sự không thay đổi chúng.

---

# 47. Không rebuild mọi thứ

Đây là điểm quan trọng cho tốc độ compiler.

Thay vì:

```text
pass
→ recompute all analyses
```

dùng:

```text
pass
→ precise invalidation
→ incremental update
```

---

# 48. Parallel pass execution

Các function độc lập:

```text
foo
bar
baz
```

có thể optimize song song.

Trong một function, các pass có dependency có thể vẫn tuần tự.

---

# 49. Determinism

Hai lần compile cùng:

```text
source
compiler version
target
config
profile
dependencies
comptime inputs
```

phải tạo cùng semantic decisions.

Parallelism không được làm thay đổi kết quả.

---

# 50. Optimization remarks

Compiler nên ghi:

```text
OptimizationRemark {
    PassId
    FunctionId
    SourceOrigin
    Decision
    Reason
    Cost
    RequiredFacts
    MissingFacts
}
```

Ví dụ:

```text
Vectorization rejected

reason:
  Alias relationship between out[i] and input[i] = UNKNOWN
```

Đây sẽ cực kỳ hữu ích cho AI.

---

# 51. `axc inspect optimize`

Đề xuất:

```text
axc inspect optimize foo
axc inspect optimize foo --pass vectorize
axc inspect optimize foo --why
axc inspect optimize foo --missed
```

---

# 52. AI optimization loop

AI có thể hỏi compiler:

```text
Why was this loop not vectorized?
```

Compiler trả lời có cấu trúc:

```text
Pass: Vectorize
Result: NotProven

Required:
  NoAlias(out, input)

Available:
  MAY_ALIAS(out, input)

Source:
  foo.ax:42
```

AI không cần đoán.

---

# 53. Failed optimization

Nếu proof thất bại:

```text
NotProven
```

pass phải:

```text
leave program unchanged
```

hoặc thử transformation khác có legality proof.

Không được “thử xem chạy không”.

---

# 54. Optimization verifier

Sau mỗi nhóm pass quan trọng có thể chạy:

```text
OptVerifier
```

kiểm tra:

```text
SSA validity
MemorySSA validity
CFG validity
type validity
effect consistency
alias fact consistency
target constraints
```

---

# 55. Semantic preservation checking

Trong debug/compiler-validation builds:

```text
Verified MIR
     ↓
Optimization
     ↓
Semantic checker
```

có thể kiểm tra transformation metadata.

Không nhất thiết chạy đầy đủ ở production build.

---

# 56. Pass transaction

Một pass có thể thực hiện:

```text
begin transaction
transform
verify
commit
```

Nếu invariant fail:

```text
rollback
```

Điều này rất hữu ích trong compiler development.

---

# 57. Optimization snapshots

Compiler debug mode có thể lưu:

```text
before-pass
after-pass
```

để tìm miscompilation.

Ví dụ:

```text
foo.pass.031.before.axir
foo.pass.031.after.axir
```

---

# 58. Không cho pass sửa ownership facts

Ví dụ AliasInfo nói:

```text
NO_ALIAS
```

pass không được tự viết:

```text
NO_ALIAS
```

chỉ vì muốn vectorize.

AliasInfo phải đến từ:

```text
verified semantic facts
```

hoặc runtime optimization guard hợp lệ.

---

# 59. Không cho optimization tạo safety proof

Đây là invariant cực kỳ quan trọng:

```text
Verification
     ↓
Optimization
```

không bao giờ:

```text
Optimization
     ↓
Verification proof
```

Ví dụ optimizer phát hiện:

```text
hai pointers hiện không overlap
```

không có nghĩa source program được phép tạo hai `mut_view` overlap rồi hy vọng optimizer cứu.

---

# 60. Optimization có thể làm mất information

Nếu pass scalarize:

```text
struct → scalars
```

phải lưu đủ metadata để các pass sau vẫn hiểu semantics cần thiết.

Compiler-only metadata có thể bị erase khi không còn cần.

---

# 61. Pass categories

Đề xuất chia:

```text
Canonicalization
Simplification
Scalar
Memory
CFG
Inlining
Interprocedural
Loop
Vector
Allocation
Async
GPU
Target
Size
Debug
```

---

# 62. Pass ordering

Không nên khóa thứ tự từng pass vĩnh viễn.

Thay vào đó khai báo:

```text
requires
provides
preserves
invalidates
```

Pipeline planner có thể lập dependency graph.

---

# 63. Ví dụ

```text
SROA
  ↓
InstCombine
  ↓
GVN
  ↓
DCE
```

Nhưng nếu một target/pass tạo cơ hội khác:

```text
Inlining
  ↓
SROA
  ↓
GVN
```

pipeline planner có thể chọn.

---

# 64. Fixed-point optimization

Một số nhóm:

```text
InstCombine
CFG Simplify
DCE
SCCP
```

có thể chạy tới fixed point:

```text
while changes:
    run passes
```

nhưng phải có giới hạn/termination guarantee.

---

# 65. Termination

Optimization framework phải đảm bảo không oscillate:

```text
A → B → A → B ...
```

Pass có:

```text
monotonic progress metric
iteration limit
canonical form
```

---

# 66. Canonical form

OptIR cần canonical representation để:

- giảm số lần optimization;
- tăng cache hit;
- deterministic;
- dễ debug;
- dễ AI inspect.

---

# 67. Optimization cache

Có thể cache:

```text
FunctionSemanticFingerprint
+
OptimizationConfig
+
TargetInfo
+
ProfileFingerprint
```

→ optimized IR.

Nhưng cache không được bypass verification.

---

# 68. Cross-module optimization

LTO có thể sử dụng:

```text
.axmeta
CallGraph
EffectSummary
TypeInfo
GenericInfo
Alias summaries
Profile
```

để tối ưu xuyên package/module.

---

# 69. Binary size

`-Os/-Oz` CostModel ưu tiên:

```text
code size
shared code
dead stripping
constant merging
outlining
```

nhưng không được hy sinh semantics.

---

# 70. Machine-dependent optimization

Các pass target-specific có thể nằm sau generic OptIR:

```text
Generic OptIR
      ↓
Target OptIR
      ↓
LIR
```

Không đưa x86 assumptions vào generic optimizer.

---

# 71. Target-independent vs target-dependent

```text
Target Independent:
    SCCP
    GVN
    DCE
    SROA
    LICM
    Alias
    Escape

Target Dependent:
    SIMD width
    instruction cost
    register pressure
    addressing modes
    branch cost
```

---

# 72. Optimization diagnostics

Ví dụ người dùng:

```text
axc inspect optimize foo
```

có thể nhận:

```text
loop #3
  bounds checks: eliminated
  vectorization: successful
  alias proof: proven
  allocation: none
  inlining: foo.bar
```

Đây chính là kiểu compiler “giải thích được” mà Axiom cần.

---

# 73. Các nguyên tắc đã khóa

### `AOPT-70`
Mọi transformation phải có legality contract.

### `AOPT-71`
Legality và profitability là hai quyết định độc lập.

### `AOPT-72`
Không có proof thì không được áp dụng transformation phụ thuộc proof đó.

### `AOPT-73`
Optimization không được tạo safety proof.

### `AOPT-74`
Optimizer không được thay đổi ownership semantics.

### `AOPT-75`
Optimizer không được thay đổi capability semantics.

### `AOPT-76`
Optimizer không được thay đổi Drop semantics.

### `AOPT-77`
Atomic semantics phải được bảo toàn.

### `AOPT-78`
Volatile semantics phải được bảo toàn.

### `AOPT-79`
Observable IO ordering phải được bảo toàn.

### `AOPT-80`
Panic behavior observable phải được bảo toàn.

### `AOPT-81`
Defined overflow semantics phải được bảo toàn.

### `AOPT-82`
Strict floating-point semantics không được tự động relax.

### `AOPT-83`
Unknown alias không được biến thành NoAlias.

### `AOPT-84`
Unknown effect không được biến thành Pure.

### `AOPT-85`
Unknown escape không được biến thành NoEscape.

### `AOPT-86`
Observable address không được bị optimization loại bỏ.

### `AOPT-87`
Observable allocation identity không được bị loại bỏ.

### `AOPT-88`
Stable-address contract phải được bảo toàn.

### `AOPT-89`
Async suspension semantics phải được bảo toàn.

### `AOPT-90`
GPU synchronization semantics phải được bảo toàn.

### `AOPT-91`
FFI contracts phải được tôn trọng.

### `AOPT-92`
Mọi invalidated analysis phải được cập nhật hoặc tính lại trước khi sử dụng.

### `AOPT-93`
Pass không được sử dụng stale analysis facts.

### `AOPT-94`
Optimization pipeline phải deterministic.

### `AOPT-95`
Optimization có thể chạy song song khi dependency cho phép.

### `AOPT-96`
Failed optimization không làm compilation fail nếu chương trình vẫn hợp lệ.

### `AOPT-97`
Failed proof chỉ làm giảm optimization opportunity.

### `AOPT-98`
OptIR phải luôn có thể truy nguyên về Verified MIR.

### `AOPT-99`
Optimization remarks phải có source provenance.

### `AOPT-100`
Optimization metadata không được trở thành runtime overhead nếu không cần thiết.

### `AOPT-101`
Pass Manager phải hỗ trợ incremental invalidation.

### `AOPT-102`
Pass execution phải có termination guarantee.

### `AOPT-103`
Pass ordering không được phụ thuộc vào race hoặc execution order không xác định.

### `AOPT-104`
CostModel không được override legality.

### `AOPT-105`
PGO không được thay đổi semantic correctness.

### `AOPT-106`
LTO không được thay đổi semantic correctness.

### `AOPT-107`
Optimization levels không được thay đổi observable program semantics.

### `AOPT-108`
Target-specific optimization không được làm ô nhiễm target-independent semantic rules.

### `AOPT-109`
Optimization verifier là safety net của compiler implementation.

### `AOPT-110`
Verified MIR remains the ultimate semantic correctness boundary.

---

# Kết quả của BOOTSTRAP-140

Axiom hiện có kiến trúc:

```text
                    SOURCE
                       │
                      HIR
                       │
                      MIR
                       │
              ┌────────┴────────┐
              │   VERIFICATION  │
              └────────┬────────┘
                       │
                 VERIFIED MIR
                       │
        ┌──────────────┼──────────────┐
        │              │              │
      Alias          Effect         Escape
        │              │              │
        └──────────────┼──────────────┘
                       │
                 SSA + MemorySSA
                       │
                     OptIR
                       │
               ┌───────┴────────┐
               │  PASS MANAGER  │
               └───────┬────────┘
                       │
               OPTIMIZED OptIR
                       │
                  ABI / LIR
                       │
                    MACHINE
```

Điểm rất mạnh của kiến trúc này là **compiler có thể ngày càng thông minh mà không phải làm ngôn ngữ ngày càng phiền phức**.

Programmer không cần viết:

```text
restrict
pure
readonly
noalias
inline
likely
cold
heap
stack
register
borrow lifetime
```

trừ khi đó thực sự là một **semantic/FFI/system contract** cần thiết.

Compiler tự suy luận càng nhiều càng tốt.

---

# BOOTSTRAP-141 — Interprocedural Analysis, Call Graph & Whole-Program Optimization

Bước tiếp theo nên giải quyết vấn đề mà các pass đơn-function chưa xử lý được:

```text
foo()
  ↓
bar()
  ↓
baz()
```

Compiler cần hiểu **toàn bộ chuỗi gọi hàm**, bao gồm:

- CallGraph;
- SCC/recursion;
- effect propagation;
- escape propagation;
- alias summaries;
- function specialization;
- inlining;
- devirtualization;
- dead function elimination;
- cross-module optimization;
- LTO;
- generic instances;
- dynamic dispatch;
- FFI boundaries;
- exported/public ABI boundaries.

Đặc biệt, BOOTSTRAP-141 sẽ khóa một nguyên tắc rất quan trọng cho mục tiêu hiệu năng của Axiom:

> **Compiler có thể nhìn xuyên qua abstraction boundary khi semantics cho phép, nhưng không được nhìn xuyên qua một boundary mà chương trình có quyền quan sát.**