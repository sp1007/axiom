# BOOTSTRAP-319 — AXIOM COMPILER PASS CONTRACT SYSTEM & PROOF-CARRYING TRANSFORMATIONS

Sau 318, Axiom đã có cơ chế **kiểm tra semantic equivalence**. Bước tiếp theo hợp lý là biến nó thành cơ chế mà **mọi compiler pass bắt buộc phải tuân theo**.

Mục tiêu của 319:

> Không còn compiler pass nào chỉ là một đoạn code “thử biến đổi IR rồi hy vọng đúng”. Mỗi pass phải khai báo nó cần gì, tạo ra gì, làm mất fact nào, giữ nguyên semantic property nào, và có cách xác minh kết quả.

---

## 319.1. Vấn đề cần giải quyết

Ví dụ một pass:

```text
ConstantFolding
```

hiện tại có thể đơn giản làm:

```text
2 + 3
```

→

```text
5
```

Nhưng compiler cần biết:

```text
Pass này yêu cầu fact gì?
Pass này được phép thay đổi gì?
Pass này có thể invalidate analysis nào?
Pass này có thể gây panic/trap không?
Pass này có thay đổi effect không?
Pass này có ảnh hưởng ownership/capability không?
Pass này có cần translation validation không?
```

319 đưa tất cả thành **machine-readable contract**.

---

# 319.2. PassContract

Mỗi pass phải có metadata:

```text
PassContract {
    id
    name
    input_ir
    output_ir

    required_facts
    produced_facts

    preserved_properties
    transformed_properties

    invalidated_analyses

    semantic_effect
    legality_conditions

    validation_strategy
    cost_model

    determinism
    parallelism
}
```

Ví dụ:

```text
PassContract {
    id: "opt.constant_fold"

    input_ir: "MIR"
    output_ir: "MIR"

    required_facts:
        Typed
        DefinedOperation

    produced_facts:
        ConstantValue

    preserved:
        Ownership
        Capability
        Effects
        PanicBehavior

    invalidates:
        RangeInfo

    validation:
        Symbolic
        Differential
}
```

---

# 319.3. Fact System

319 chính thức biến các compiler analysis thành một **Proof/Fact Graph**.

Ví dụ:

```text
TypeChecked
    ↓
Initialized
    ↓
Owned
    ↓
NoAlias
    ↓
Pure
    ↓
LoopInvariant
```

Mỗi fact có:

```text
Fact {
    id
    subject
    proposition
    provenance
    confidence
    dependencies
}
```

Không có concept:

```text
probably_true
```

Chỉ có:

```text
PROVEN
DISPROVEN
UNKNOWN
```

---

# 319.4. Provenance của Fact

Compiler phải biết:

> Fact này đến từ đâu?

Ví dụ:

```text
NoAlias(a, b)
```

có thể đến từ:

```text
CapabilityAnalysis
```

hoặc:

```text
@noalias FFI contract
```

hoặc:

```text
unsafe trusted contract
```

Do đó:

```text
FactProvenance {
    source
    rule_id
    analysis_id
    source_span
    dependencies
}
```

Điều này cực kỳ quan trọng khi debug optimizer.

---

# 319.5. Fact Dependency Graph

Ví dụ:

```text
NoAlias(a,b)
     │
     ├── LoopVectorization
     ├── LoadForwarding
     └── StoreElimination
```

Nếu một transformation làm mất:

```text
NoAlias(a,b)
```

thì compiler tự động biết phải invalidate các proof phụ thuộc vào fact đó.

Không cần lập trình viên/compiler-pass tự nhớ từng analysis.

---

# 319.6. Analysis Invalidation

Ví dụ:

```text
GVN
```

thay đổi CFG.

Một số fact cũ có thể không còn đúng:

```text
Dominance
LoopInfo
Liveness
RangeInfo
MemorySSA
```

Pass phải khai báo:

```text
invalidates:
    CFG
    Dominance
    LoopInfo
```

Framework tự động đánh dấu:

```text
STALE
```

và yêu cầu recompute khi cần.

---

# 319.7. Preservation Contract

Ngược lại, pass có thể nói:

```text
preserves:
    TypeInfo
    Ownership
    Capability
    ABI
```

Compiler verifier kiểm tra rằng pass thực sự không phá những property này.

Ví dụ pass chỉ đổi:

```text
BasicBlock layout
```

không được phép vô tình thay đổi:

```text
OwnershipState
```

---

# 319.8. Transformation Transaction

Mọi pass nên chạy theo mô hình:

```text
Snapshot
   ↓
Transform
   ↓
Verify
   ↓
Validate
   ↓
Commit
```

Không phải:

```text
Transform
   ↓
IR đã bị sửa trực tiếp
   ↓
phát hiện lỗi
   ↓
không biết rollback thế nào
```

Do đó:

```text
PassTransaction {
    input_snapshot
    working_ir
    generated_facts
    invalidated_facts
    proof_obligations
    validation_result
}
```

Chỉ `commit()` khi toàn bộ điều kiện đạt.

---

# 319.9. Atomic Pass Commit

Nếu:

```text
Pass A
```

thất bại:

```text
Pass A
→ no-op
```

không được để IR ở trạng thái nửa biến đổi.

Điều này đặc biệt quan trọng khi:

- compiler chạy song song
- compiler bị cancellation
- compiler daemon
- IDE incremental compilation
- AI agent sửa compiler
- compiler crash recovery

---

# 319.10. Proof-Carrying Transformation

Một transformation thành công tạo:

```text
TransformationResult {
    output
    certificate
    generated_facts
    invalidated_facts
}
```

Ví dụ:

```text
LoopVectorization
```

có certificate:

```text
VectorizationCertificate {
    loop_id
    iteration_space
    dependency_proof
    alignment_proof
    alias_proof
    overflow_proof
    target_support
}
```

Sau đó validator chỉ cần kiểm tra certificate.

---

# 319.11. Không bắt buộc Proof phải là Formal Theorem

Axiom không nên tự trói mình vào một theorem prover duy nhất.

Một proof có thể đến từ:

```text
TypeChecker
OwnershipVerifier
CapabilityAnalysis
RangeAnalysis
EffectAnalysis
SymbolicEvaluator
SMT Solver
ARI
Target Model
Unsafe Contract
FFI Contract
```

Tất cả đều tạo ra:

```text
Fact
```

theo cùng một hệ thống.

---

# 319.12. Proof Strength

Không phải mọi fact đều có cùng nguồn tin cậy.

Đề xuất:

```text
Intrinsic
VerifiedAnalysis
SpecificationRule
TrustedContract
ForeignContract
UnsafeAssumption
Heuristic
```

Nhưng cần phân biệt rõ:

### Heuristic không được làm semantic proof

Ví dụ:

```text
BranchProbability = 99%
```

không thể dùng để chứng minh:

```text
branch is unreachable
```

Nó chỉ được dùng cho optimization cost model.

---

# 319.13. Semantic Facts và Performance Facts

Hai nhóm phải tách biệt.

### Semantic fact

```text
NoAlias
NoPanic
Pure
Initialized
Disjoint
Send
Share
ConstantTime
```

### Performance fact

```text
LikelyHot
BranchProbability
CacheFriendly
VectorWidth
Latency
```

Performance fact **không bao giờ được dùng để chứng minh semantic correctness**.

Đây là một invariant rất quan trọng.

---

# 319.14. Pass Scheduling

Compiler có thể xây dependency graph:

```text
Pass A
 ↓
Pass B
 ↓
Pass C
```

nhưng thay vì hard-code toàn bộ thứ tự, scheduler dựa trên:

```text
requires facts
produces facts
invalidates facts
```

Ví dụ:

```text
Vectorize
requires:
    LoopInfo
    NoAlias
    RangeInfo
    TargetSIMD

```

Scheduler tự biết cần chạy analysis nào trước.

---

# 319.15. Analysis-as-a-Service

Một analysis không nhất thiết là pass tuyến tính.

Ví dụ:

```text
NoAlias(a,b)
```

có thể được request trực tiếp:

```text
facts.require(NoAlias(a,b))
```

Compiler:

```text
if cached:
    return cached

run required analysis

verify

cache result
```

Điều này phù hợp hoàn toàn với kiến trúc `CompilerDB`.

---

# 319.16. Demand-Driven Analysis

Không cần chạy:

```text
AllAnalysis
```

cho mọi function.

Nếu function không vectorize:

```text
VectorDependenceAnalysis
```

không cần chạy.

Nếu không có async:

```text
AsyncStateAnalysis
```

không cần chạy.

Nếu không có GPU:

```text
GpuLegalityAnalysis
```

không cần chạy.

Đây là một cách giảm compile time rất lớn.

---

# 319.17. Proof Cache

Fact có key:

```text
FactKey {
    subject
    proposition
    semantic_fingerprint
    analysis_version
    target_context
}
```

Ví dụ:

```text
NoAlias(foo.arg0, foo.arg1)
```

được cache.

Nếu source không thay đổi và dependencies không thay đổi:

```text
reuse
```

---

# 319.18. Cross-Pass Proof Reuse

Đây là một điểm rất mạnh.

Ví dụ:

```text
CapabilityAnalysis
```

đã chứng minh:

```text
a DISJOINT b
```

thì:

```text
Vectorizer
MemoryOptimizer
LoadStoreOptimizer
Scheduler
```

đều có thể sử dụng cùng fact.

Không cần mỗi pass tự viết lại alias analysis.

---

# 319.19. Proof Invalidation

Nếu:

```text
a
```

được mutate:

```text
a[i] = x
```

compiler tự xác định những fact nào mất hiệu lực.

Ví dụ:

```text
ValueKnown(a)       → invalid
Range(a)            → invalid
MemoryValue(a)      → invalid

Type(a)             → preserved
Ownership(a)        → preserved
```

Không invalidate quá mức.

---

# 319.20. Semantic Firewall

Giữa các compiler subsystem tồn tại một **Semantic Firewall**.

```text
Frontend
    ↓
Semantic Firewall
    ↓
Optimizer
    ↓
Semantic Firewall
    ↓
Backend
```

Optimizer không thể tự ý tạo:

```text
OwnershipFact
CapabilityFact
SendFact
```

nếu không có verifier chứng minh.

Backend không thể tự ý thay đổi:

```text
Type
Ownership
Effect
```

Nó chỉ được transform representation trong phạm vi contract.

---

# 319.21. Pass Capability

Mỗi pass có capability riêng:

```text
PassCapabilities {
    read_types
    modify_cfg
    modify_memory
    modify_control_flow
    introduce_calls
    eliminate_calls
    introduce_allocations
    eliminate_allocations
    change_representation
}
```

Ví dụ:

```text
DeadCodeElimination
```

không có quyền:

```text
introduce_new_effect
```

Nếu pass cố làm:

```text
DCE → insert IO
```

compiler framework từ chối.

---

# 319.22. Effect Budget

Pass phải khai báo effect transformation.

Ví dụ:

```text
Inlining
```

có thể thay đổi:

```text
Call
```

thành:

```text
Body
```

nhưng tổng observable effects phải tương đương.

Pass không được biến:

```text
Pure
```

thành:

```text
IO
```

hay:

```text
Atomic
```

nếu contract không cho phép.

---

# 319.23. Allocation Contract

Optimization được phép biến:

```text
allocate
use
deallocate
```

thành:

```text
stack/register
```

nếu allocation không observable.

Nhưng nếu allocation thuộc observable contract:

```text
custom allocator
FFI
address identity
allocation failure exposed
```

thì không được tự ý loại bỏ.

---

# 319.24. Identity Contract

Compiler phải phân biệt:

```text
Value Identity
Storage Identity
Logical Identity
```

Một pass chỉ được merge hai object nếu semantic contract cho phép.

Ví dụ:

```text
x = Box(...)
y = x
```

không thể CSE thành cùng storage nếu chương trình quan sát:

```text
storage identity
```

Ngược lại:

```text
pure temporary value
```

có thể scalarize.

---

# 319.25. Concurrency Contract

Pass không được làm mất:

```text
happens-before
atomic ordering
synchronization
```

Ví dụ:

```text
release_store(flag)
acquire_load(flag)
```

không được reorder thành code phá synchronizes-with relationship.

Compiler phải có:

```text
ConcurrencyContract
```

làm legality boundary.

---

# 319.26. Async Contract

Async lowering đặc biệt cần contract:

```text
async fn
```

→

```text
Future state machine
```

phải bảo toàn:

- suspension points
- state
- ownership
- drop
- cancellation
- wake behavior
- Send/Share
- observable effects

Ví dụ:

```text
view<T>
```

không được vô tình trở thành field sống qua await nếu điều đó vi phạm capability lifetime.

---

# 319.27. GPU Contract

GPU transformations cũng dùng cùng framework:

```text
Kernel
 ↓
GPU IR
 ↓
Lowered GPU IR
 ↓
Target ISA
```

Phải bảo toàn:

```text
address space
memory ordering
barrier
atomic scope
kernel legality
host/device boundary
```

Kernel fusion chỉ được thực hiện nếu dependency proof cho phép.

---

# 319.28. Deterministic Pass Execution

Một compiler build giống nhau phải tạo cùng:

```text
IR
facts
certificates
diagnostics
artifact
```

trừ metadata được định nghĩa là nondeterministic.

Pass scheduler không được để:

```text
thread timing
```

thay đổi semantic result.

---

# 319.29. AI Agent Safety

319 đặc biệt hữu ích cho workflow AI agent.

AI có thể sửa optimizer:

```text
compiler/optimizer/foo.ax
```

Nhưng compiler không tin AI.

Pipeline:

```text
AI modifies pass
        ↓
Compiler builds
        ↓
PassContract check
        ↓
Verifier
        ↓
Translation Validation
        ↓
Conformance tests
        ↓
Differential tests
        ↓
Commit candidate
```

AI không thể "tự tuyên bố":

```text
this optimization is safe
```

---

# 319.30. Compiler Self-Protection

Một pass binary/plugin không được phép inject semantic facts trực tiếp.

Ví dụ không được:

```text
facts.add(NoAlias(a,b))
```

Chỉ được:

```text
facts.request(NoAlias(a,b))
```

và phải có analysis/proof provider hợp lệ.

Đây là một lớp bảo vệ rất quan trọng khi Axiom compiler ngày càng được AI phát triển.

---

# 319.31. API

Các API chính:

```text
register_pass(contract, implementation)
```

```text
require_fact(fact)
```

```text
prove_fact(fact)
```

```text
invalidate_fact(fact)
```

```text
begin_transformation()
```

```text
commit_transformation()
```

```text
rollback_transformation()
```

```text
validate_transformation()
```

```text
get_fact_provenance()
```

```text
explain_fact()
```

```text
explain_pass_legality()
```

```text
query_pass_dependencies()
```

---

# 319.32. Implementation Tree

```text
compiler/correctness/
├── contracts/
│   ├── pass_contract.ax
│   ├── capability.ax
│   ├── effect_contract.ax
│   └── semantic_contract.ax
│
├── facts/
│   ├── fact.ax
│   ├── fact_graph.ax
│   ├── provenance.ax
│   ├── dependency.ax
│   ├── invalidation.ax
│   └── cache.ax
│
├── proof/
│   ├── provider.ax
│   ├── obligation.ax
│   ├── certificate.ax
│   └── strength.ax
│
├── transaction/
│   ├── snapshot.ax
│   ├── transaction.ax
│   ├── commit.ax
│   └── rollback.ax
│
├── scheduler/
│   ├── pass_scheduler.ax
│   ├── analysis_scheduler.ax
│   └── dependency_graph.ax
│
└── firewall/
    ├── semantic_firewall.ax
    ├── effect_firewall.ax
    └── fact_firewall.ax
```

---

# 319.33. Invariants

```text
APASS-20  Every compiler pass has an explicit PassContract.

APASS-21  A pass cannot consume an unproven semantic fact.

APASS-22  UNKNOWN is never treated as PROVEN.

APASS-23  Performance heuristics cannot establish semantic facts.

APASS-24  Every fact has provenance.

APASS-25  Fact dependencies are explicit.

APASS-26  Invalid facts cannot be consumed.

APASS-27  Transformations are transactional.

APASS-28  Failed transformations cannot leave partial semantic state.

APASS-29  Passes may only modify properties declared by their contract.

APASS-30  Semantic facts cannot be injected without a valid proof provider.

APASS-31  Preservation claims are independently verifiable.

APASS-32  Semantic and performance facts are separate domains.

APASS-33  Proof caches are fingerprinted.

APASS-34  Invalidated facts are never silently reused.

APASS-35  Pass ordering must respect fact dependencies.

APASS-36  Independent analyses may execute concurrently.

APASS-37  Pass execution is deterministic.

APASS-38  ABI, FFI, concurrency, async and GPU contracts participate in the same framework.

APASS-39  AI-generated compiler changes pass through exactly the same validation pipeline.

APASS-40  The pass framework cannot redefine language semantics.
```

---

# 319.34. Definition of Done

BOOTSTRAP-319 hoàn thành khi:

1. Có `PassContract`.
2. Có unified `Fact`.
3. Có `FactGraph`.
4. Có provenance.
5. Có dependency/invalidation.
6. Có proof provider.
7. Có certificate.
8. Có transactional transformation.
9. Có pass scheduler.
10. Có demand-driven analysis.
11. Có proof cache.
12. Có cross-pass fact reuse.
13. Có semantic firewall.
14. Có performance/semantic fact separation.
15. Có effect budget.
16. Có allocation/identity contract.
17. Có concurrency contract.
18. Có async contract.
19. Có GPU contract.
20. Có ABI/FFI contract.
21. Có AI-agent validation boundary.
22. Có test suite cố ý đưa pass sai để framework bắt được.
23. Có deterministic parallel execution.
24. Có incremental fact invalidation.
25. Có end-to-end:
   ```text
   Pass
   → Contract
   → Required Facts
   → Transformation
   → Proof
   → Validation
   → Certificate
   → Commit
   ```

---

## Nguyên tắc đóng băng của 319

> **Compiler pass không được phép nói “tôi nghĩ transformation này đúng”. Nó phải nói “đây là điều kiện để transformation đúng, đây là những fact chứng minh điều kiện đó, đây là những semantic property tôi bảo toàn, và đây là certificate để kiểm tra lại”.**

Với 318 + 319, Axiom bắt đầu có một **compiler correctness architecture hoàn chỉnh**, trong đó correctness không còn chỉ là một bộ test chạy sau khi compiler viết xong, mà trở thành **một phần của chính kiến trúc compiler**.