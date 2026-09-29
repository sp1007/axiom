# BOOTSTRAP-318 — AXIOM COMPILER CORRECTNESS, TRANSLATION VALIDATION & SEMANTIC EQUIVALENCE ENGINE

## 318.1. Mục tiêu

Axiom đã có:

- **315** — Formal Semantics
- **316** — AXSpec machine-readable specification
- **317** — Reference Interpreter (ARI)
- **310** — Testing & Verification
- các verifier cho Ownership / Capability / Effect / Concurrency / GPU / ABI
- pipeline compiler từ Source → Machine Code

Nhưng vẫn còn một câu hỏi quan trọng:

> **Làm sao biết mỗi bước biến đổi của compiler thực sự giữ nguyên ý nghĩa chương trình?**

BOOTSTRAP-318 xây dựng cơ chế **Translation Validation + Semantic Equivalence** để trả lời câu hỏi đó.

Mục tiêu không phải chứng minh compiler bằng một theorem prover khổng lồ, mà là tạo một hệ thống trong đó:

> **Mỗi transformation phải có semantic contract, và compiler phải có khả năng kiểm tra rằng transformation không làm thay đổi observable behavior.**

---

# 318.2. Nguyên tắc nền tảng

### CORR-PRINCIPLE-01 — Semantic Preservation

Nếu compiler biến đổi:

```text
A → B
```

thì phải chứng minh hoặc kiểm tra:

```text
Semantics(A) ≡ Semantics(B)
```

trong phạm vi observable behavior mà Axiom định nghĩa.

---

### CORR-PRINCIPLE-02 — Optimization Cannot Define Semantics

Optimization không được quyết định chương trình "có nghĩa gì".

Thứ tự quyền lực:

```text
AXSpec
   ↓
Reference Semantics
   ↓
Compiler Transformation Contract
   ↓
Verifier
   ↓
Optimization
```

Không được phép:

```text
Optimization
   ↓
"compiler thấy thế này nhanh hơn nên coi như đúng"
```

---

### CORR-PRINCIPLE-03 — Proof Before Optimization

Một optimization chỉ được áp dụng nếu các precondition cần thiết đã được chứng minh.

Ví dụ:

```text
a[i] + a[i]
```

→

```text
2 * a[i]
```

chỉ hợp lệ nếu:

- load không volatile
- không có concurrent mutation quan sát được
- không có effect xen giữa
- overflow semantics được bảo toàn
- floating-point mode cho phép
- alias/effect analysis chứng minh phép biến đổi hợp lệ

---

# 318.3. Semantic Equivalence Model

Axiom định nghĩa nhiều mức equivalence.

### Level 0 — Structural Equivalence

Hai IR giống cấu trúc.

Chủ yếu dùng debugging.

---

### Level 1 — Value Equivalence

Với cùng input:

```text
result(A) == result(B)
```

---

### Level 2 — Memory Equivalence

Ngoài return value còn phải giữ:

- observable memory
- ownership
- initialization
- Drop effects
- allocation effects nếu observable

---

### Level 3 — Effect Equivalence

Phải giữ:

- I/O
- synchronization
- atomic ordering
- panic/trap
- foreign calls
- volatile
- external effects

---

### Level 4 — Observable Semantic Equivalence

Mức cao nhất:

```text
ObservableBehavior(A)
    ≡
ObservableBehavior(B)
```

Đây là equivalence chính thức của compiler.

---

# 318.4. Translation Pipeline

Compiler correctness framework nhìn toàn bộ pipeline:

```text
Source
  │
  ▼
AST
  │
  ▼
HIR
  │
  ▼
Typed HIR
  │
  ▼
MIR
  │
  ▼
Verified MIR
  │
  ▼
OptIR
  │
  ▼
ABI MIR
  │
  ▼
LIR
  │
  ▼
Machine IR
  │
  ▼
Final Machine IR
  │
  ▼
Machine Code
  │
  ▼
Native Image
```

Mỗi cạnh là một **Translation Boundary**.

Ví dụ:

```text
HIR → MIR
```

phải có contract riêng.

```text
MIR → OptIR
```

phải có contract riêng.

```text
LIR → Machine IR
```

phải có contract riêng.

---

# 318.5. Translation Contract

Mỗi compiler transformation phải khai báo:

```text
TransformationContract {
    id
    input_ir
    output_ir

    preconditions
    preserved_properties
    transformed_properties

    semantic_effects
    invalidated_facts

    proof_requirements
    validation_strategy

    failure_policy
}
```

Ví dụ:

```text
contract.scalar.constant_fold {
    input = MIR
    output = MIR

    requires:
        operands_are_constant
        operation_defined

    preserves:
        value
        type
        effects
        panic_behavior

    validation:
        symbolic
        differential
}
```

---

# 318.6. Semantic Certificate

Compiler có thể tạo:

```text
SemanticCertificate
```

chứa:

```text
{
    transformation_id,
    input_fingerprint,
    output_fingerprint,

    required_facts,
    proven_facts,

    semantic_relation,

    verifier_version,
    spec_version
}
```

Certificate không nhất thiết phải chứa toàn bộ proof.

Có thể chỉ chứa:

```text
"Transformation T được áp dụng vì facts F1,F2,F3 đã được verifier chứng minh."
```

---

# 318.7. Proof Obligation

Khi optimization cần một điều kiện chưa biết:

```text
x + y
```

→

```text
...
```

compiler tạo:

```text
ProofObligation {
    condition
    source_span
    transformation
    required_analysis
}
```

Ví dụ:

```text
PO-001:

prove:
    region(a) DISJOINT region(b)

required_by:
    vectorize.loop.42
```

Nếu không chứng minh được:

```text
UNKNOWN
```

thì optimization **không được phép giả định true**.

---

# 318.8. Translation Relation

Một representation thấp hơn không nhất thiết giống representation cao hơn.

Ví dụ:

```text
Vec3
```

có thể biến thành:

```text
r0 = x
r1 = y
r2 = z
```

Do đó cần:

```text
TranslationRelation
```

mô tả cách state của representation trước được ánh xạ sang representation sau.

```text
Relation {
    source_state
    target_state

    value_mapping
    memory_mapping
    control_mapping
    effect_mapping
}
```

---

# 318.9. State Mapping

Ví dụ:

```text
HIR:

v.x = a
v.y = b
v.z = c
```

sau optimization:

```text
r0 = a
r1 = b
r2 = c
```

Framework biết:

```text
HIR.v.x ↔ Machine.r0
HIR.v.y ↔ Machine.r1
HIR.v.z ↔ Machine.r2
```

Không yêu cầu representation giống nhau.

Chỉ yêu cầu observable semantics tương đương.

---

# 318.10. Optimization Validation

Mỗi optimization pass phải khai báo:

```text
PassContract
```

Ví dụ:

```text
LoopInvariantCodeMotion
```

requires:

```text
expression is pure
expression does not depend on mutated memory
expression cannot trap differently
```

preserves:

```text
value
effects
panic behavior
memory semantics
```

Nếu pass không chứng minh được:

```text
do_not_transform
```

Không có kiểu:

```text
probably_safe
```

---

# 318.11. Local Translation Validation

Mỗi transformation có thể được kiểm tra ngay tại chỗ.

Ví dụ:

```text
Before:
    x = a + 0

After:
    x = a
```

Validator kiểm tra:

```text
type(a)
overflow semantics
floating semantics
effects
```

Nếu hợp lệ:

```text
VALID
```

Nếu không:

```text
REJECT
```

---

# 318.12. Global Translation Validation

Một số transformation chỉ có ý nghĩa khi xem cả function.

Ví dụ:

```text
Inlining
Loop unrolling
Tail duplication
Coroutine lowering
Vectorization
Register allocation
```

cần kiểm tra toàn function hoặc region.

Framework hỗ trợ:

```text
LocalValidation
RegionValidation
FunctionValidation
ModuleValidation
WholeProgramValidation
```

---

# 318.13. ARI Integration

ARI từ BOOTSTRAP-317 trở thành semantic oracle.

Ví dụ:

```text
Original MIR
     │
     ▼
    ARI
     │
     ▼
Observable Trace A


Optimized MIR
     │
     ▼
    ARI
     │
     ▼
Observable Trace B
```

So sánh:

```text
Trace A ≡ Trace B
```

ARI đặc biệt hữu ích cho:

- optimizer testing
- MIR transformations
- async lowering
- ownership transformations
- coroutine lowering
- effect-preserving transformations
- compiler regression

---

# 318.14. Không được phụ thuộc hoàn toàn vào ARI

ARI không thể trực tiếp mô phỏng vô hạn mọi machine behavior.

Vì vậy cần nhiều validation layer:

```text
                    ┌──────────────┐
                    │ AXSpec       │
                    └──────┬───────┘
                           │
                    Reference Model
                           │
        ┌──────────────────┼─────────────────┐
        ▼                  ▼                 ▼
   Symbolic Proof      ARI Execute      Static Proof
        │                  │                 │
        └──────────────────┼─────────────────┘
                           ▼
                  Translation Validation
                           │
                           ▼
                    Native Validation
```

---

# 318.15. Machine-Level Validation

Ở backend, equivalence không còn là:

```text
IR instruction == machine instruction
```

mà là:

```text
MachineState_before
        ↓
Machine instructions
        ↓
MachineState_after
```

phải tương thích với:

```text
IRState_before
        ↓
IR semantics
        ↓
IRState_after
```

Cần một:

```text
MachineSemanticModel
```

ở mức đủ để kiểm tra:

- registers
- flags
- memory
- control flow
- calling convention
- stack
- atomic operations
- volatile
- traps

---

# 318.16. Register Allocation Validation

Register allocator có thể biến:

```text
v1 = ...
v2 = ...
```

thành:

```text
rax = ...
rbx = ...
```

Validator phải kiểm tra:

```text
live ranges
register aliases
fixed registers
call clobbers
spill/reload
stack slots
flags
```

để đảm bảo không làm thay đổi semantics.

Đặc biệt:

> Stack-slot reuse không được biến thành semantic alias.

---

# 318.17. ABI Translation Validation

ABI lowering phải bảo toàn:

```text
argument values
return values
ownership
layout
alignment
calling convention
register/stack placement
panic behavior
foreign effects
```

Ví dụ:

```text
Axiom:

fn foo(x: Vec3) -> f64
```

có thể trở thành:

```text
x → XMM0/XMM1
result → XMM0
```

Validator phải biết mapping này đúng với ABI target.

---

# 318.18. FFI Boundary Validation

FFI là translation boundary đặc biệt.

Ví dụ:

```text
Axiom Vec<T>
      ↓
C ABI
      ↓
external_function
```

Compiler phải kiểm tra:

```text
repr
alignment
size
calling convention
ownership
alias contract
panic contract
thread contract
async contract
```

Không được suy luận:

```text
extern function → safe
```

---

# 318.19. Unsafe Boundary

`unsafe` không được coi là:

```text
semantic equivalence disabled
```

Mà:

```text
unsafe establishes trusted precondition
```

Sau boundary:

```text
unsafe
   ↓
trusted fact
   ↓
normal verifier
   ↓
normal optimization
```

Ví dụ:

```text
unsafe {
    assume_disjoint(a, b)
}
```

nếu API này tồn tại sau này, compiler phải ghi nhận:

```text
TrustedFact:
    region(a) DISJOINT region(b)
```

và provenance của fact.

---

# 318.20. Security Preservation

BOOTSTRAP-314 đã định nghĩa:

- ConstantTime
- Secret
- Provenance
- TrustLevel
- FFI boundary

318 phải đảm bảo optimizer không phá contract.

Ví dụ:

```text
@constant_time
fn compare(...)
```

không được optimization thành code có timing-dependent behavior nếu contract cấm điều đó.

---

# 318.21. Mismatch Localization

Nếu:

```text
Original ≠ Optimized
```

không chỉ báo:

```text
compiler bug
```

mà phải tìm transformation đầu tiên gây divergence.

Pipeline:

```text
A
↓
B
↓
C
↓
D
↓
E
```

Nếu:

```text
A ≡ B
B ≡ C
C ≠ D
```

thì:

```text
D transformation
```

là suspect đầu tiên.

---

# 318.22. Automatic Reduction

Khi phát hiện mismatch:

```text
program
```

được reducer thu nhỏ:

```text
10,000 LOC
       ↓
2,000
       ↓
300
       ↓
27
```

cho đến khi vẫn giữ:

```text
semantic divergence
```

Output:

```text
minimal reproducer
```

với:

- source
- compiler revision
- target
- optimization pass
- semantic trace
- before/after IR
- certificate
- proof obligations

---

# 318.23. Validation Modes

Không thể validate toàn bộ mọi chương trình ở mọi build vì chi phí quá cao.

Axiom có các mode:

### `none`

Không runtime translation validation.

Dùng cho production build nếu đã được compiler trust model chấp nhận.

### `basic`

Validate critical transformations.

### `checked`

Validate mọi transformation có thể kiểm tra hiệu quả.

### `full`

ARI + differential + translation validation + extensive backend checks.

### `bootstrap`

Mức cao nhất cho compiler self-hosting.

---

# 318.24. Proof Cache

Proof/result được cache:

```text
ProofCacheKey {
    input_fingerprint
    output_fingerprint
    transformation_id
    compiler_semantic_version
    target
    relevant_facts
}
```

Nếu cùng transformation + cùng semantic facts:

```text
reuse certificate
```

Điều này rất quan trọng cho compiler lớn.

---

# 318.25. Parallel Validation

Các transformation độc lập có thể validate song song:

```text
Function A ── validation
Function B ── validation
Function C ── validation
Function D ── validation
```

Kết quả phải deterministic.

---

# 318.26. Incremental Validation

Nếu chỉ thay đổi:

```text
function foo
```

không cần validate lại toàn bộ package nếu dependency semantic fingerprint không thay đổi.

Compiler sử dụng:

```text
SemanticFingerprint
TransformationFingerprint
ProofFingerprint
```

để xác định phần nào phải validate lại.

---

# 318.27. Compiler Correctness Database

Thêm:

```text
CorrectnessDB
```

vào CompilerDB:

```text
CompilerDB
 ├── SourceDB
 ├── TypeDB
 ├── TraitDB
 ├── HIRDB
 ├── MIRDB
 ├── ...
 ├── SpecDB
 ├── ReferenceDB
 └── CorrectnessDB
```

`CorrectnessDB` lưu:

- transformation contracts
- semantic relations
- proof obligations
- certificates
- validation results
- mismatch records
- proof cache
- reducer artifacts

---

# 318.28. API

Core API:

```text
validate_translation(input, output, contract)
```

```text
prove_transformation(transformation)
```

```text
validate_optimization(pass, function)
```

```text
check_semantic_equivalence(a, b)
```

```text
generate_certificate(transformation)
```

```text
validate_certificate(certificate)
```

```text
find_first_divergence(trace_a, trace_b)
```

```text
reduce_mismatch(testcase)
```

```text
explain_validation_failure(result)
```

```text
validate_codegen(ir, machine)
```

```text
validate_abi(source_abi, lowered_abi)
```

---

# 318.29. AI Interface

AI compiler interface được mở rộng:

```text
explain_transformation
explain_proof_obligation
explain_certificate
explain_equivalence
explain_validation_failure
show_semantic_relation
show_first_divergence
reduce_compiler_bug
```

Ví dụ AI có thể hỏi:

```text
Why was this loop vectorized?
```

Compiler trả:

```text
Transformation: LOOP-VEC-042

Required facts:
  A disjoint B          ✓
  no volatile access    ✓
  no aliasing mutation  ✓
  overflow semantics    ✓
  target SIMD support   ✓

Certificate:
  CORR-CERT-8F31...
```

Đây là điểm rất quan trọng đối với mục tiêu **AI-friendly compiler** của Axiom.

---

# 318.30. Implementation Tree

Đề xuất:

```text
compiler/correctness/
├── contracts/
│   ├── transformation.ax
│   ├── optimization.ax
│   ├── lowering.ax
│   └── abi.ax
│
├── relation/
│   ├── semantic_relation.ax
│   ├── state_mapping.ax
│   ├── value_mapping.ax
│   ├── memory_mapping.ax
│   └── effect_mapping.ax
│
├── proof/
│   ├── obligation.ax
│   ├── proof_engine.ax
│   ├── certificate.ax
│   └── proof_cache.ax
│
├── validation/
│   ├── local.ax
│   ├── region.ax
│   ├── function.ax
│   ├── module.ax
│   ├── native.ax
│   └── differential.ax
│
├── machine/
│   ├── machine_model.ax
│   ├── register_validation.ax
│   ├── stack_validation.ax
│   └── abi_validation.ax
│
├── mismatch/
│   ├── detector.ax
│   ├── locator.ax
│   ├── reducer.ax
│   └── report.ax
│
└── correctness_db.ax
```

---

# 318.31. Invariants

Đăng ký nhóm invariant:

```text
ACORR-20  Every transformation has a semantic contract.

ACORR-21  No transformation may rely on an unproven semantic fact.

ACORR-22  UNKNOWN is never equivalent to PROVEN.

ACORR-23  Optimization must preserve observable semantics.

ACORR-24  Transformation validation is independent of optimization intent.

ACORR-25  Semantic equivalence may differ from structural equivalence.

ACORR-26  Representation changes require an explicit translation relation.

ACORR-27  ABI lowering must preserve ABI-visible semantics.

ACORR-28  Register allocation must preserve live-value semantics.

ACORR-29  Stack-slot reuse must not introduce semantic aliasing.

ACORR-30  Unsafe establishes explicit trusted facts; it does not disable validation.

ACORR-31  FFI boundaries require explicit semantic contracts.

ACORR-32  Security properties marked non-relaxable must survive translation.

ACORR-33  Validation failure must identify the earliest known divergent transformation.

ACORR-34  Mismatch reduction must preserve the semantic divergence.

ACORR-35  Cached certificates are valid only under their dependency fingerprints.

ACORR-36  Validation results are deterministic.

ACORR-37  Optimizer correctness must not depend on ARI implementation details.

ACORR-38  Reference semantics remain the final semantic authority.

ACORR-39  Machine validation must respect target-specific semantics.

ACORR-40  No compiler stage may silently redefine observable behavior.
```

---

# 318.32. Definition of Done

BOOTSTRAP-318 chỉ hoàn thành khi:

1. Có `TransformationContract`.
2. Có `SemanticRelation`.
3. Có `ProofObligation`.
4. Có `SemanticCertificate`.
5. Có `CorrectnessDB`.
6. HIR→MIR có translation contract.
7. MIR→OptIR có validation framework.
8. OptIR→ABI MIR có contract.
9. ABI MIR→LIR có contract.
10. LIR→Machine IR có machine relation.
11. Register allocation có validation.
12. ABI lowering có validation.
13. FFI boundary có validation.
14. Unsafe boundary có trusted-fact model.
15. Security contracts được theo dõi.
16. ARI có thể làm semantic oracle.
17. Có differential execution.
18. Có mismatch localization.
19. Có automatic reducer.
20. Có proof/certificate cache.
21. Có incremental validation.
22. Có parallel validation.
23. Có AI explanation API.
24. Có compiler correctness diagnostics.
25. Có test suite cho từng translation boundary.
26. Có end-to-end validation:
   ```text
   Source
   → Reference
   → MIR
   → Optimized MIR
   → Machine
   ```
27. Có khả năng phát hiện ít nhất các compiler bug cố ý được cài vào optimizer/backend.
28. Có reproducible correctness artifacts.

---

## 318.33. Kết luận kiến trúc

Sau BOOTSTRAP-318, Axiom có một chuỗi rất quan trọng:

```text
315  Formal Semantics
        ↓
316  Machine-readable Specification
        ↓
317  Reference Interpreter
        ↓
318  Translation Validation
        ↓
310  Testing / Fuzzing / Differential Verification
```

Điều này tạo thành **correctness spine** của compiler.

Điểm quan trọng nhất là:

> **Axiom không yêu cầu compiler phải được chứng minh hoàn toàn bằng formal theorem proving ngay từ đầu. Thay vào đó, compiler được xây dựng để mỗi transformation có contract, mỗi giả định có proof/fact, mỗi thay đổi có thể được validate, và mọi divergence đều có thể truy ngược về transformation gây ra nó.**

Đây là nền tảng cần thiết trước khi tiếp tục mở rộng các tầng compiler cao hơn.