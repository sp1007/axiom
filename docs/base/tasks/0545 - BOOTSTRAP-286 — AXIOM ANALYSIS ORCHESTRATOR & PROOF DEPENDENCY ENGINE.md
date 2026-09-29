# BOOTSTRAP-286 — AXIOM ANALYSIS ORCHESTRATOR & PROOF DEPENDENCY ENGINE
## FROZEN / COMPLETED

### 1. Mục tiêu

Sau `BOOTSTRAP-281..285`, Axiom đã có các engine riêng:

```text
281 Ownership / Initialization / Move
282 Capability / View / Alias
283 Effect
284 Escape / Storage Lifetime
285 Interprocedural Semantic Analysis
```

Vấn đề tiếp theo không phải viết thêm một analysis riêng, mà là **cách các analysis này phối hợp với nhau**.

Nếu mỗi optimizer tự gọi từng analysis:

```text
Inlining → gọi Ownership
          → gọi Alias
          → gọi Effect
          → gọi Escape
          → gọi Interprocedural
```

thì compiler rất nhanh trở thành một hệ thống phụ thuộc chéo, khó incremental và khó chứng minh tính đúng đắn.

Axiom cần một tầng trung gian:

```text
                    CompilerDB
                        │
                        ▼
              Analysis Orchestrator
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
     Ownership      Capability      Effect
          │             │             │
          └──────┬──────┴──────┬──────┘
                 ▼             ▼
              Escape      Interprocedural
                 │             │
                 └──────┬──────┘
                        ▼
                 Proof Dependency
                        │
                        ▼
                Verified Facts
                        │
                        ▼
              Optimization Gateway
                        │
                        ▼
                   OptIR passes
```

### Nguyên tắc trung tâm

> **Analysis quyết định compiler biết gì. Proof Dependency quyết định compiler được phép dựa vào điều gì.**

Optimizer **không được tự suy luận lại semantic safety**.

---

# 2. Phân biệt Fact và Proof

Đây là điểm rất quan trọng.

Không phải mọi kết quả analysis đều có cùng mức độ tin cậy.

Ví dụ:

```text
Alias = UNKNOWN
```

là một fact.

Trong khi:

```text
NoAlias(a, b)
```

sau khi capability verifier chứng minh được là một **proof**.

Do đó:

```text
Fact
    ↓
Analysis
    ↓
Evidence
    ↓
Proof
    ↓
Optimization permission
```

Compiler phải phân biệt rõ:

```text
ObservedFact
DerivedFact
ProvenFact
AssumedFact
InvalidatedFact
```

Không được biến:

```text
"chưa phát hiện alias"
```

thành:

```text
"không có alias"
```

---

# 3. Proof Object

Mỗi fact quan trọng dùng cho optimization phải có nguồn gốc.

```text
Proof {
    proof_id: ProofId

    subject: SemanticSubject

    proposition: Proposition

    status: ProofStatus

    source_analysis: AnalysisId

    dependencies: [ProofDependency]

    assumptions: [Assumption]

    revision: RevisionId

    fingerprint: SemanticFingerprint
}
```

### ProofStatus

```text
Proven
Disproven
Unknown
Conditional
Assumed
Invalidated
```

Trong optimizer thông thường:

```text
Proven
```

mới có thể làm cơ sở cho transform yêu cầu proof.

`Assumed` chỉ được dùng trong các boundary được đánh dấu rõ, chẳng hạn:

```text
unsafe
FFI contract
trusted intrinsic
target-specific contract
```

và phải mang theo nguồn assumption.

---

# 4. Proposition

Không lưu proof dưới dạng chuỗi text.

Phải có semantic representation.

Ví dụ:

```text
NoAlias {
    region_a
    region_b
}
```

```text
Initialized(place)
```

```text
Owned(place)
```

```text
DoesNotEscape(place)
```

```text
MayPanic(function)
```

```text
DoesNotSuspend(function)
```

```text
Send(type)
```

```text
GpuLegal(function)
```

```text
StableAddress(storage)
```

```text
ReadOnly(region)
```

```text
NoObservableEffect(function)
```

Ví dụ:

```text
Proposition =
    Ownership(...)
    Capability(...)
    Alias(...)
    Effect(...)
    Escape(...)
    Panic(...)
    Concurrency(...)
    Async(...)
    GPU(...)
    FFI(...)
    Layout(...)
    ABI(...)
```

Điều này cho phép compiler truy vấn proof bằng cấu trúc semantic thay vì parsing message.

---

# 5. Proof Dependency Graph

Proof có thể phụ thuộc proof khác.

Ví dụ compiler muốn chứng minh:

```text
CanVectorize(loop)
```

có thể cần:

```text
NoAlias(a,b)
NoAlias(a,out)
NoAlias(b,out)

NoObservableCall(loop)

NoVolatileAccess(loop)

NoUnknownForeignCall(loop)

BoundsProven(i)
```

Dependency graph:

```text
                  CanVectorize
                  /    |     \
                 /     |      \
           NoAlias   NoEffect   Bounds
            /  \        |         |
           /    \       |         |
     Capability Effect  Interproc Range
         |       |         |
      Ownership  CallGraph  MIR
```

Nếu một proof dependency thay đổi:

```text
Capability proof invalidated
        ↓
NoAlias invalidated
        ↓
CanVectorize invalidated
```

Optimizer không cần tự biết toàn bộ chuỗi này.

---

# 6. Proof Dependency

```text
ProofDependency {
    proof_id: ProofId

    dependency_kind:
        Requires
        DerivedFrom
        Assumes
        InvalidatedBy

    source: ProofId | QueryKey | InputId
}
```

Nhưng dependency không chỉ giới hạn ở proof.

Có thể phụ thuộc:

```text
SourceInput
MIR revision
Type definition
Trait implementation
Comptime result
Target feature
ABI configuration
FFI contract
```

Ví dụ:

```text
NoAlias proof
    ↓
depends on
    CapabilitySummary
    Type layout
    MIR revision
    Function summary
```

---

# 7. Analysis Identity

Mỗi analysis có ID ổn định:

```text
AnalysisId {
    Ownership
    Initialization
    Capability
    Alias
    Effect
    Escape
    Interprocedural
    Concurrency
    Async
    GPU
    FFI
    Panic
    Range
    Layout
    ...
}
```

Không tạo nhiều hệ thống cache riêng.

Tất cả đi qua:

```text
CompilerDB
    ↓
AnalysisOrchestrator
    ↓
QueryEngine
```

---

# 8. Analysis Contract

Mỗi analysis phải khai báo contract:

```text
AnalysisContract {
    analysis_id

    inputs
    prerequisites

    produces

    invalidation_inputs

    monotonic

    incremental

    parallelizable

    deterministic
}
```

Ví dụ:

```text
CapabilityAnalysis:

inputs:
    VerifiedMIR
    OwnershipFacts
    TypeDB

prerequisites:
    OwnershipAnalysis

produces:
    CapabilityFacts
    AliasFacts
    ProvenanceFacts

invalidation:
    MIR
    type definitions
    function summaries

monotonic:
    true

parallelizable:
    true

deterministic:
    true
```

---

# 9. Analysis Dependency DAG

Orchestrator xây dependency graph:

```text
HIR
 │
 ▼
MIR
 │
 ▼
Ownership
 │
 ├──────────────┐
 ▼              ▼
Capability     Escape
 │              │
 └──────┬───────┘
        ▼
      Effect
        │
        ▼
 Interprocedural
        │
        ▼
   Proof Builder
        │
        ▼
 Optimization
```

Tuy nhiên graph **không được hard-code thành một pipeline duy nhất**.

Một optimization chỉ yêu cầu những proof cần thiết.

---

# 10. Demand-Driven Analysis

Ví dụ optimizer cần:

```text
CanEliminateAllocation(allocation_42)
```

Orchestrator không chạy toàn bộ compiler analysis.

Nó resolve:

```text
CanEliminateAllocation
    ↓
DoesNotEscape
    ↓
EscapeAnalysis
    ↓
Ownership
    ↓
MIR
```

Nếu cần thêm:

```text
NoObservableEffect
```

thì mới request:

```text
EffectAnalysis
```

Đây là:

> **Demand-driven semantic analysis.**

Lợi ích lớn cho:

- incremental compilation
- IDE
- compiler speed
- LTO
- huge projects
- AI compiler queries

---

# 11. Analysis Request

```text
AnalysisRequest {
    function: FunctionId

    analysis: AnalysisId

    scope:
        Function
        Module
        Package
        Program

    precision:
        Fast
        Normal
        Precise

    revision: RevisionId
}
```

Ví dụ:

```text
request(
    function = foo,
    analysis = Escape,
    precision = Precise
)
```

---

# 12. Precision Levels

Không phải query nào cũng cần mức chính xác tối đa.

```text
Fast
Normal
Precise
```

Ví dụ:

```text
Fast:
    conservative summary

Normal:
    field-sensitive

Precise:
    path-sensitive
    symbolic range
    interprocedural refinement
```

Nhưng có một invariant rất quan trọng:

> **Precision thấp chỉ được làm mất optimization opportunity, không được làm thay đổi semantic correctness.**

Ví dụ:

```text
Precise → NoAlias
Fast    → Unknown
```

là hợp lệ.

Nhưng:

```text
Precise → NoAlias
Fast    → WrongNoAlias
```

là lỗi compiler.

---

# 13. Proof Builder

Tạo một tầng chuyên chuyển analysis facts thành proofs.

```text
Analysis Facts
      ↓
Proof Builder
      ↓
Proof Validation
      ↓
Proof Store
```

Ví dụ:

```text
CapabilityAnalysis:
    Region(A) DISJOINT Region(B)

        ↓

ProofBuilder

        ↓

Proof:
    NoAlias(A,B)
```

Proof builder phải kiểm tra:

```text
- source analysis valid
- revision matches
- dependencies valid
- proposition well-formed
- assumptions explicit
- target scope valid
```

---

# 14. Proof Lifetime

Proof không tồn tại vĩnh viễn.

Ví dụ sửa:

```text
fn foo(a: view<A>, b: view<B>)
```

thành:

```text
fn foo(a: view<A>, b: mut_view<B>)
```

có thể làm thay đổi:

```text
Capability
Alias
Effect
Interprocedural
Optimization proofs
```

Do đó proof gắn với revision:

```text
Proof {
    revision = R42
}
```

Compiler chuyển sang:

```text
R43
```

thì proof cũ chỉ còn hợp lệ nếu dependency graph chứng minh nó vẫn valid.

---

# 15. Proof Invalidation

Không invalidate toàn bộ compiler.

Ví dụ:

```text
Type T changed
```

chỉ invalidate những proof phụ thuộc:

```text
T
    ↓
Layout(T)
    ↓
CapabilitySummary(foo)
    ↓
NoAlias(foo)
    ↓
Vectorization(foo)
```

Các proof độc lập vẫn giữ nguyên.

Đây là nền tảng cho incremental compilation quy mô lớn.

---

# 16. Proof Cache

Proof cache nằm trong CompilerDB:

```text
ProofDB
├── ProofStore
├── ProofDependencyGraph
├── ProofIndex
├── ProofFingerprint
├── ProofInvalidation
└── ProofQuery
```

Không cho optimizer tự tạo cache proof riêng.

---

# 17. Optimization Gateway

Đây là boundary rất quan trọng.

Optimizer không được gọi trực tiếp:

```text
CapabilityAnalysis::is_noalias(...)
```

mà phải đi qua:

```text
OptimizationGateway
```

Ví dụ:

```text
gateway.require(
    NoAlias(a, b)
)
```

hoặc:

```text
gateway.require(
    DoesNotEscape(x)
)
```

Nếu proof tồn tại:

```text
ALLOW TRANSFORM
```

Nếu không:

```text
DENY TRANSFORM
```

Không được có logic:

```text
if unknown:
    assume true
```

---

# 18. Transform Contract

Mỗi optimization pass phải khai báo preconditions.

Ví dụ:

```text
TransformContract {
    transform_id

    required_proofs

    forbidden_effects

    invalidation_set

    preserves:
        ownership
        capability
        effects
        panic
        concurrency
        async
        gpu
        ffi
}
```

Ví dụ vectorization:

```text
VectorizeLoop {
    requires:
        LoopCanonical
        NoAlias
        BoundsSafe
        NoVolatile
        NoUnsafeUnknownCall
        CompatibleEffects

    preserves:
        observable behavior
        memory ordering
        panic behavior
}
```

---

# 19. Transform Result

Optimizer không chỉ trả về MIR mới.

```text
TransformResult {
    transformed_ir

    applied_proofs

    generated_facts

    invalidated_facts

    source_mapping

    cost_model_info
}
```

Sau transform, compiler phải biết proof nào còn hợp lệ.

Ví dụ:

```text
Loop unrolling
```

có thể giữ:

```text
NoAlias
Bounds
```

nhưng tạo ra:

```text
new instruction ranges
new CFG
new source mappings
```

và có thể invalidate một số CFG-sensitive facts.

---

# 20. Proof-Carrying Optimization

Một transform hợp lệ có dạng:

```text
Input IR
   +
Required Proofs
   ↓
Transform
   ↓
Output IR
   +
Preserved Proofs
   +
New Proofs
   +
Invalidated Proofs
```

Không phải:

```text
Input IR
   ↓
Optimizer "nghĩ rằng" transform an toàn
   ↓
Output IR
```

Đây là một trong những nền tảng quan trọng nhất để compiler Axiom có thể tiến tới compiler correctness mạnh hơn.

---

# 21. Semantic Optimization Boundary

Pipeline được khóa lại thành:

```text
                 Verified MIR
                      │
                      ▼
             Analysis Orchestrator
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
     Facts           Proofs       Summaries
       │              │              │
       └──────────────┼──────────────┘
                      ▼
             Optimization Gateway
                      │
                      ▼
                     OptIR
                      │
                      ▼
                Optimizer Passes
```

Điểm quan trọng:

> **Optimizer chỉ được hoạt động trên IR đã qua semantic verification và phải sử dụng proof gateway cho các transform phụ thuộc semantic facts.**

---

# 22. Interaction với Ownership

Ví dụ:

```text
let x = make_buffer()
use(x)
```

Ownership engine chứng minh:

```text
x = Owned
x = consumed
```

Optimization không được tự giả định rằng:

```text
x không còn được sử dụng
```

mà lấy:

```text
OwnershipProof
```

để thực hiện dead-storage elimination.

---

# 23. Interaction với Capability

Ví dụ:

```text
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
)
```

Capability engine chứng minh:

```text
a ∩ b = ∅
a ∩ out = ∅
b ∩ out = ∅
```

Proof builder tạo:

```text
NoAlias(a,b)
NoAlias(a,out)
NoAlias(b,out)
```

Vectorizer được phép dùng chúng.

Nếu một trong ba chuyển thành:

```text
UNKNOWN
```

thì vectorizer phải tự động fallback:

```text
scalar implementation
```

không được báo lỗi compiler.

---

# 24. Interaction với Effect

Ví dụ:

```text
fn calculate(x: i32) -> i32
```

Effect engine chứng minh:

```text
No IO
No Atomic
No Volatile
No Synchronize
No Foreign
No Panic
```

Optimizer có thể dùng proof để:

```text
CSE
GVN
DCE
LICM
Inlining
Constant propagation
```

nhưng chỉ trong phạm vi mà các precondition tương ứng được chứng minh.

---

# 25. Interaction với Escape

Ví dụ:

```text
let x = Box::new(T)
return x.value
```

Escape:

```text
x → NoEscape
```

cho phép:

```text
heap allocation elimination
```

nếu các proof khác cũng hợp lệ.

Kết quả có thể:

```text
heap → stack
```

hoặc:

```text
stack → register
```

hoặc:

```text
allocation → completely eliminated
```

nhưng semantic ownership không thay đổi.

---

# 26. Interaction với Async

Proof:

```text
DoesNotLiveAcrossAwait(x)
```

cho phép optimizer không đưa `x` vào coroutine state.

Ngược lại:

```text
LiveAcrossAwait(x)
```

buộc compiler giữ semantic state.

Optimization có thể thay đổi physical representation nhưng không được loại bỏ giá trị cần tồn tại qua suspension.

---

# 27. Interaction với Concurrency

Ví dụ optimizer muốn reorder:

```text
atomic_store
normal_store
atomic_load
```

Effect + concurrency proofs phải xác nhận rằng reorder không phá:

```text
sequenced-before
synchronizes-with
happens-before
atomic ordering
volatile semantics
```

Không được coi atomic như ordinary load/store.

---

# 28. Interaction với GPU

GPU optimizer có thể yêu cầu:

```text
GpuLegal
NoHostCapabilityEscape
NoIllegalAddressSpaceAccess
NoRace
ValidBarrierOrdering
```

Fusion kernel chỉ được thực hiện nếu proof dependency cho phép.

---

# 29. Interaction với FFI

Foreign call mặc định:

```text
UnknownEffects
UnknownAlias
UnknownEscape
UnknownPanic
UnknownSynchronization
```

Do đó optimization phải conservative.

Nếu FFI contract cung cấp:

```text
@noalias
@readonly
@nothrow
@pure
```

compiler tạo **contract proofs** sau khi validate contract theo rule của Axiom.

Không được coi annotation của người dùng tự động là sự thật.

---

# 30. Unsafe và Proof

`unsafe` không tạo:

```text
EverythingIsTrue
```

Nó chỉ tạo:

```text
TrustedAssumption(...)
```

Ví dụ:

```text
raw pointer p
```

unsafe contract nói:

```text
p points to initialized T
p is aligned
p is valid for READ
```

thì Proof Builder có:

```text
Assumed(
    ValidPointer(p,T)
)
```

Các proof tiếp theo phải giữ provenance:

```text
TrustedPointer
      ↓
SafeCapability
      ↓
CapabilityProof
```

Không được biến assumption thành unconditional fact không có nguồn.

---

# 31. Proof Explanation

Axiom cần hỗ trợ:

```text
Why was this optimization not applied?
```

Ví dụ:

```text
Vectorization rejected.

Required proof:
    NoAlias(a, out)

Status:
    UNKNOWN

Dependency:
    capability summary of foo()

Root cause:
    foo() calls foreign function bar()

Foreign contract:
    alias behavior unspecified
```

Đây là cực kỳ quan trọng cho:

- programmer
- IDE
- compiler developers
- AI coding agents

---

# 32. AI Query API

AI có thể hỏi:

```text
explain proof NoAlias(foo.a, foo.out)
```

Compiler trả:

```text
PROVEN

Evidence:
    Capability #1842
    Region R17
    Region R19
    relation = DISJOINT

Source:
    foo.ax:42

Dependencies:
    Ownership #921
    MIR revision #184
```

Hoặc:

```text
explain why heap allocation remains
```

Compiler:

```text
Allocation #42 cannot be eliminated.

Reason:
    ReturnEscape

Dependency:
    foo() returns Buffer<T>

Caller:
    main()

Escape chain:
    allocation
      → return value
      → caller storage
```

AI không cần đọc hàng nghìn dòng compiler log.

---

# 33. Determinism

Analysis orchestrator phải bảo đảm:

```text
1 worker
4 workers
16 workers
```

cho cùng:

```text
source
compiler semantic version
target
configuration
dependencies
comptime inputs
```

sẽ tạo:

```text
same semantic facts
same proof fingerprints
same diagnostics
```

Thứ tự thực thi song song không được ảnh hưởng semantic result.

---

# 34. Parallel Analysis

Các analysis độc lập có thể chạy song song:

```text
             MIR
              │
       ┌──────┼──────┐
       ▼      ▼      ▼
   Ownership Effect Escape
       │      │      │
       └──────┼──────┘
              ▼
        Interprocedural
```

Orchestrator phải quản lý:

```text
dependency readiness
work stealing
cancellation
deduplication
query sharing
revision consistency
```

Hai request giống nhau:

```text
Request A: Escape(foo)
Request B: Escape(foo)
```

phải dùng chung computation đang chạy thay vì chạy hai lần.

---

# 35. Cycles

Interprocedural recursion:

```text
foo → bar → baz → foo
```

được xử lý bằng:

```text
SCC
 ↓
initial summaries
 ↓
monotone iteration
 ↓
fixed point
 ↓
proof generation
```

Proof không được xuất bản là `Proven` trước khi SCC đạt trạng thái ổn định.

---

# 36. Partial Analysis

IDE có thể yêu cầu analysis khi source chưa hoàn chỉnh.

Khi đó:

```text
Partial
Unknown
ErrorType
Unresolved
```

được phép tồn tại trong:

```text
Partial Semantic Mode
```

nhưng tuyệt đối không được đi vào:

```text
Verified MIR
Optimization Proof
Final Codegen
```

trừ các trường hợp compiler recovery có semantic contract rõ ràng.

---

# 37. Analysis Snapshot

Mỗi compilation snapshot:

```text
AnalysisSnapshot {
    revision
    target
    profile
    feature_set

    mir_revision

    facts
    proofs
    summaries

    fingerprint
}
```

Điều này hỗ trợ:

- IDE
- incremental compiler
- parallel build
- LTO
- distributed compilation
- compiler server

---

# 38. Module Structure

Đề xuất:

```text
compiler/analysis/orchestrator/
├── mod.ax
├── analysis_id.ax
├── analysis_contract.ax
├── analysis_request.ax
├── analysis_scheduler.ax
├── analysis_dependency.ax
├── analysis_state.ax
├── analysis_snapshot.ax
├── precision.ax
├── demand.ax
├── parallel.ax
├── cancellation.ax
├── dedup.ax
└── tests/
```

Proof subsystem:

```text
compiler/analysis/proof/
├── mod.ax
├── proof_id.ax
├── proof.ax
├── proposition.ax
├── proof_status.ax
├── proof_dependency.ax
├── proof_store.ax
├── proof_graph.ax
├── proof_builder.ax
├── proof_validator.ax
├── proof_fingerprint.ax
├── proof_cache.ax
├── invalidation.ax
├── explanation.ax
└── tests/
```

Optimization boundary:

```text
compiler/optimization/gateway/
├── mod.ax
├── optimization_gateway.ax
├── transform_contract.ax
├── proof_requirement.ax
├── proof_checker.ax
├── transform_result.ax
├── preserved_facts.ax
├── invalidated_facts.ax
└── tests/
```

---

# 39. Implementation Order

```text
1. AnalysisId
2. AnalysisContract
3. AnalysisRequest
4. Analysis dependency graph
5. Demand-driven scheduler
6. Query deduplication
7. Revision-aware invalidation
8. Parallel scheduling
9. Proof Proposition model
10. Proof object
11. Proof dependency graph
12. Proof validator
13. Proof fingerprint
14. Proof cache
15. Analysis → Proof builder
16. Optimization Gateway
17. Transform Contract
18. Transform Result
19. Proof explanation
20. CompilerDB integration
21. Cross-module proof support
22. LTO proof refinement
23. adversarial testing
```

---

# 40. Adversarial Tests

### Test 1 — Unknown ≠ NoAlias

```text
a = unknown_call()
b = unknown_call()
```

Expected:

```text
Alias = UNKNOWN
NoAlias proof = absent
```

Vectorization must not assume disjointness.

---

### Test 2 — Proof invalidation

```text
foo(a: view<T>, b: view<T>)
```

proves:

```text
NoAlias(a,b)
```

Change function signature/implementation so overlap becomes possible.

Expected:

```text
NoAlias proof invalidated
```

but unrelated proofs remain cached.

---

### Test 3 — Worker determinism

Compile with:

```text
1 worker
8 workers
32 workers
```

Expected:

```text
identical semantic fingerprints
identical proof fingerprints
```

---

### Test 4 — Unsafe assumption provenance

```text
unsafe raw pointer → trusted capability
```

Expected proof chain:

```text
UnsafeAssumption
 → ValidCapability
 → NoAlias / Readable / Writable
```

Không được mất nguồn assumption.

---

### Test 5 — FFI

```text
foreign fn foo(...)
```

không contract.

Expected:

```text
UnknownAlias
UnknownEscape
UnknownEffects
```

---

### Test 6 — Async

```text
x
await
```

Nếu `x` không live qua await:

```text
DoesNotLiveAcrossAwait(x)
```

Nếu live:

```text
LiveAcrossAwait(x)
```

---

### Test 7 — Recursive SCC

```text
a → b → c → a
```

Expected:

```text
summary iteration
→ fixed point
→ stable fingerprints
```

Không infinite loop.

---

### Test 8 — Stale proof

Proof revision:

```text
R100
```

IR revision:

```text
R101
```

nếu dependency thay đổi:

```text
proof status = Invalidated
```

Optimizer không được sử dụng proof cũ.

---

### Test 9 — Optimization rollback

Transform yêu cầu:

```text
NoAlias
```

nhưng proof bị invalidated giữa lúc planning và commit.

Expected:

```text
transform rejected/replanned
```

Không được commit IR dựa trên stale proof.

---

### Test 10 — Precision

```text
Fast → UNKNOWN
Precise → Proven
```

Expected semantics giống nhau.

Chỉ optimization opportunity khác nhau.

---

# 41. Frozen Invariants

### `AORCH-20..45`

```text
AORCH-20  — One Authoritative Analysis Orchestrator
AORCH-21  — One Shared Analysis Dependency Graph
AORCH-22  — Analysis Results Are Revision-Bound
AORCH-23  — Demand-Driven Analysis Is Supported
AORCH-24  — Analysis Requests Are Typed
AORCH-25  — Analysis Dependencies Are Explicit
AORCH-26  — Duplicate Analysis Requests Share Computation
AORCH-27  — Analysis Invalidation Is Dependency-Driven
AORCH-28  — Analysis Precision Cannot Change Semantics
AORCH-29  — Unknown Never Becomes Proven By Default
AORCH-30  — Analysis Results Are Deterministic
AORCH-31  — Parallel Scheduling Cannot Change Semantic Results
AORCH-32  — Recursive Analysis Uses Monotone Fixed Points
AORCH-33  — Analysis Snapshots Are Revision-Coherent
AORCH-34  — Partial Analysis Cannot Enter Verified Codegen
AORCH-35  — Analysis Caches Are Owned By CompilerDB
AORCH-36  — Analysis Implementations Do Not Create Independent Semantic Caches
AORCH-37  — Cancellation Cannot Publish Partial Verified Results
AORCH-38  — Analysis Identity Is Stable
AORCH-39  — Analysis Contracts Declare Preconditions And Outputs
AORCH-40  — Analysis Precision May Reduce Optimization But Not Correctness
AORCH-41  — Cross-Module Analysis Uses Explicit Dependencies
AORCH-42  — LTO May Refine But Not Contradict Published Contracts
AORCH-43  — Analysis Facts Preserve Provenance
AORCH-44  — Semantic Analysis Is Independent Of Physical Code Generation
AORCH-45  — The Orchestrator Is The Authoritative Analysis Scheduler
```

### `APROOF-20..65`

```text
APROOF-20  — Every Optimization-Critical Proof Has Explicit Provenance
APROOF-21  — Proofs Are Semantic Objects, Not Diagnostic Strings
APROOF-22  — Proofs Are Revision-Bound
APROOF-23  — Proof Dependencies Are Explicit
APROOF-24  — Invalid Dependencies Invalidate Dependent Proofs
APROOF-25  — Unknown Is Never Equivalent To Proven
APROOF-26  — Assumptions Are Distinct From Proven Facts
APROOF-27  — Unsafe Assumptions Preserve Their Source
APROOF-28  — FFI Contracts Preserve Their Source
APROOF-29  — Proof Fingerprints Are Deterministic
APROOF-30  — Proof Results Are Independent Of Worker Count
APROOF-31  — Proofs Cannot Outlive Required Semantic Dependencies
APROOF-32  — Proof Graphs Are Incrementally Invalidatable
APROOF-33  — Proofs May Depend On Other Proofs
APROOF-34  — Proof Cycles Must Reach A Validated Fixed Point
APROOF-35  — Unvalidated Proofs Cannot Authorize Optimization
APROOF-36  — Conditional Proofs Cannot Be Promoted To Unconditional Proofs
APROOF-37  — Must And May Facts Remain Distinct
APROOF-38  — Provenance Is Preserved Through Proof Derivation
APROOF-39  — Proof Scope Is Explicit
APROOF-40  — Target Configuration Is Part Of Target-Specific Proof Identity
APROOF-41  — Layout-Dependent Proofs Depend On Layout Revision
APROOF-42  — ABI-Dependent Proofs Depend On ABI Configuration
APROOF-43  — Comptime-Dependent Proofs Depend On Comptime Inputs
APROOF-44  — Capability Proofs Depend On Capability Validity
APROOF-45  — Ownership Proofs Depend On Ownership Verification
APROOF-46  — Alias Proofs Require Actual Alias Evidence
APROOF-47  — Effect Proofs Require Effect Analysis
APROOF-48  — Escape Proofs Require Escape Analysis
APROOF-49  — Concurrency Proofs Preserve Memory-Ordering Semantics
APROOF-50  — Async Proofs Preserve Suspension Semantics
APROOF-51  — GPU Proofs Preserve Execution And Storage Domains
APROOF-52  — FFI Proofs Require Explicit Contracts Or Conservative Unknown
APROOF-53  — Proof Cache Data Is Untrusted Until Revalidated
APROOF-54  — Proof Explanation Can Trace To Root Dependencies
APROOF-55  — Proofs Cannot Override Semantic Verification
APROOF-56  — Proofs Cannot Be Fabricated By Optimizer Passes
APROOF-57  — Optimization Passes Consume Proofs Through The Gateway
APROOF-58  — Stale Proofs Cannot Authorize Transforms
APROOF-59  — Proof Invalidations Are Transitive
APROOF-60  — Proof Generation Is Separate From Optimization
APROOF-61  — Proofs May Be Preserved, Refined, Or Invalidated By Transforms
APROOF-62  — Proof-Carrying Transforms Declare Their Preconditions
APROOF-63  — Failed Proof Requirements Cause Transform Rejection, Not Semantic Guessing
APROOF-64  — Proofs Preserve Source And IR Provenance
APROOF-65  — Proof Is A Correctness Boundary For Optimization
```

### `AOPTGATE-20..40`

```text
AOPTGATE-20 — All Semantic-Safety-Sensitive Transforms Use OptimizationGateway
AOPTGATE-21 — Every Transform Declares Required Proofs
AOPTGATE-22 — Missing Proofs Forbid The Corresponding Transform
AOPTGATE-23 — Unknown Proofs Are Not Implicit Permission
AOPTGATE-24 — Transform Results Declare Invalidated Facts
AOPTGATE-25 — Preserved Proofs Must Be Explicitly Validated
AOPTGATE-26 — Transform Output Must Remain Semantically Verifiable
AOPTGATE-27 — Optimization Cannot Weaken Ownership Semantics
AOPTGATE-28 — Optimization Cannot Weaken Capability Semantics
AOPTGATE-29 — Optimization Cannot Weaken Effect Semantics
AOPTGATE-30 — Optimization Cannot Weaken Concurrency Semantics
AOPTGATE-31 — Optimization Cannot Weaken Async Semantics
AOPTGATE-32 — Optimization Cannot Weaken GPU Safety Semantics
AOPTGATE-33 — Optimization Cannot Weaken FFI Contracts
AOPTGATE-34 — Optimization Cannot Introduce Observable Behavior Not Permitted By Source Semantics
AOPTGATE-35 — Optimization Cannot Depend On Optimization-Level-Specific Safety
AOPTGATE-36 — Transform Planning And Commit Must Use Coherent Revisions
AOPTGATE-37 — Stale Transform Plans Must Be Rejected Or Revalidated
AOPTGATE-38 — Failed Optimization Must Preserve The Original Verified Program
AOPTGATE-39 — Optimization Diagnostics Can Explain Missing Proofs
AOPTGATE-40 — Verified MIR Remains The Semantic Source Of Truth
```

---

# 42. Kiến trúc Axiom sau BOOTSTRAP-286

Từ đây compiler có một ranh giới rất sạch:

```text
                 FRONTEND
                    │
                    ▼
                   HIR
                    │
                    ▼
                   MIR
                    │
                    ▼
        ┌────────────────────────┐
        │ Semantic Verification  │
        │  Ownership             │
        │  Capability             │
        │  Effect                │
        │  Escape                │
        │  Interprocedural       │
        └───────────┬────────────┘
                    │
                    ▼
             VERIFIED MIR
                    │
                    ▼
          ANALYSIS ORCHESTRATOR
                    │
                    ▼
              PROOF ENGINE
                    │
                    ▼
          OPTIMIZATION GATEWAY
                    │
                    ▼
                  OptIR
                    │
                    ▼
              OPTIMIZATION
                    │
                    ▼
             ABI / CODEGEN
```

Đây là điểm chuyển quan trọng: **Axiom không còn chỉ có các analysis riêng lẻ; nó đã có cơ chế thống nhất để biến kết quả phân tích thành các bằng chứng có thể kiểm soát việc tối ưu hóa.**

**BOOTSTRAP-286 hoàn tất và được đóng băng.**