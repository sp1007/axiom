# BOOTSTRAP-379 — Axiom Constraint Solver, Compile-Time Logic & Generic Proof Engine

Sau **378 — Units, Dimensions & Physical Type Safety**, một nhu cầu kiến trúc lớn xuất hiện.

Axiom hiện đã có rất nhiều hệ thống cần **suy luận compile-time**:

- Generic constraints;
- Trait constraints;
- Type equality;
- Shape constraints;
- Dimension equations;
- Unit compatibility;
- Array lengths;
- Numeric properties;
- Ownership/capability facts;
- Parallelization proofs;
- Solver preconditions;
- AD legality;
- Comptime conditions.

Nếu mỗi subsystem tự xây một solver riêng, compiler sẽ nhanh chóng trở thành một tập hợp các hệ thống suy luận không tương thích.

Vì vậy **379** nên xây một **Constraint/Proof Engine dùng chung**.

> Mục tiêu: **một engine suy luận compile-time dùng chung cho toàn Axiom, nhưng không biến ngôn ngữ thành một theorem prover khó sử dụng.**

---

# 1. Constraint không phải runtime check

Axiom phân biệt:

```text id="p3c9vn"
CompileTimeConstraint
RuntimeConstraint
Proof
```

Ví dụ:

```text id="k4r8sx"
N > 0
```

Nếu `N` compile-time known:

```text id="w6m2qa"
→ CompileTimeConstraint
```

Nếu không:

```text id="h8x5zc"
→ RuntimeCheck
```

Compiler không được giả vờ đã chứng minh điều mà nó chưa chứng minh.

---

# 2. Constraint là semantic object

Một constraint có dạng:

```text id="x7v2bm"
Constraint {
    expression
    variables
    domain
    assumptions
    source
}
```

Ví dụ:

```text id="m5q8kd"
Dim<T> == Length
```

hoặc:

```text id="z1c6xp"
Shape<A>[1] == Shape<B>[0]
```

---

# 3. Constraint classes

Axiom cần phân loại:

```text id="f8n3yw"
TypeConstraint
TraitConstraint
ValueConstraint
ShapeConstraint
DimensionConstraint
UnitConstraint
OwnershipConstraint
CapabilityConstraint
AliasConstraint
EffectConstraint
NumericConstraint
LayoutConstraint
ConcurrencyConstraint
ExecutionConstraint
```

Không phải constraint nào cũng dùng cùng algorithm.

---

# 4. Một engine, nhiều solver

Không nên ép:

```text id="a5w9qc"
TraitSolver
```

giải tất cả.

Kiến trúc:

```text id="j7m2vk"
Constraint Engine
       │
       ├── Type Solver
       ├── Trait Solver
       ├── Shape Solver
       ├── Dimension Solver
       ├── Numeric Solver
       ├── Ownership Solver
       └── Generic Proof Solver
```

Nhưng chúng chia sẻ:

- constraint representation;
- dependency graph;
- caching;
- proof objects;
- invalidation;
- diagnostics.

---

# 5. Constraint normalization

Ví dụ:

```text id="y8p4cr"
A + B = B + A
```

nếu domain cho phép commutativity, có thể canonicalize.

Dimension:

```text id="v1n7sx"
Length * Time^-1
```

→ canonical vector.

Shape:

```text id="e4m9qb"
(N, M) == (N, M)
```

→ trivially true.

Normalization giảm số lượng constraint cần giải.

---

# 6. Constraint states

Mỗi constraint có trạng thái:

```text id="k3x8vm"
PROVEN_TRUE
PROVEN_FALSE
ASSUMED
DEFERRED
RUNTIME_CHECK
UNKNOWN
CONFLICT
```

Đây là distinction rất quan trọng.

`UNKNOWN` không đồng nghĩa `FALSE`.

---

# 7. Open constraints

Generic function:

```text id="y5m2rz"
fn f<T>(x: T)
```

có thể chứa constraint chưa biết:

```text id="r9c7wk"
T: Numeric
```

Compiler không cần resolve ngay.

Constraint được defer đến monomorphization/instantiation.

---

# 8. Constraint propagation

Ví dụ:

```text id="s4n8xa"
A = B
B = C
C = f64
```

engine suy ra:

```text id="j6p3mv"
A = f64
B = f64
C = f64
```

Không cần từng subsystem tự implement propagation.

---

# 9. Dependency graph

Constraint:

```text id="b7v2zn"
Shape<A>[0] == Shape<B>[1]
```

phụ thuộc vào:

```text id="q1m8xd"
Shape<A>
Shape<B>
```

CompilerDB phải track dependency.

Khi generic instantiation thay đổi, chỉ invalidate constraint liên quan.

---

# 10. Proof object

Kết quả không chỉ là:

```text id="1c7qxm"
true
```

mà:

```text id="4p8vzn"
Proof {
    proposition
    assumptions
    derivation
    dependencies
    solver
    confidence
}
```

Điều này rất quan trọng cho:

- diagnostics;
- translation validation;
- compiler debugging;
- AI-assisted compiler interface.

---

# 11. Proof levels

Có thể phân biệt:

```text id="8q2kma"
IntrinsicProof
DerivedProof
TrustedProof
RuntimeChecked
```

Ví dụ:

```text id="5w3xjr"
1 + 1 == 2
```

là intrinsic.

Một unsafe API có thể tạo:

```text id="p7c4yk"
TrustedProof
```

nhưng phải mang provenance.

---

# 12. Unsafe không được tạo “magic truth”

Ví dụ programmer:

```text id="u3n8qa"
unsafe assume x < N
```

không nên biến thành global truth.

Thay vào đó:

```text id="m6v2zc"
TrustedFact {
    proposition: x < N
    provenance: unsafe_site
    scope: current_region
}
```

Scope phải được giới hạn.

---

# 13. Proof lifetime

Proof cũng có validity conditions.

Ví dụ:

```text id="n8q3vb"
x < N
```

có thể không còn đúng sau mutation của `x`.

Compiler phải invalidate dependent proofs.

---

# 14. Value constraints

Compile-time:

```text id="5z1w7m"
N > 0
N % 4 == 0
```

có thể dùng cho:

- array;
- SIMD width;
- tensor shape;
- tile size;
- alignment.

---

# 15. Shape constraints

Ví dụ:

```text id="q8m4cx"
A: Tensor<[N, K]>
B: Tensor<[K, M]>
```

constraint:

```text id="r5p7vn"
A.shape[1] == B.shape[0]
```

→ matmul legal.

Constraint engine không cần biết implementation của matmul.

---

# 16. Dimension constraints

378 có:

```text id="x9k2mv"
Dim<T> == Length / Time
```

379 cung cấp solver infrastructure để giải.

Ví dụ:

```text id="m3v8qa"
Dim<A> * Dim<B> = Dim<C>
```

có thể normalize thành linear equations trên exponent vector.

---

# 17. Trait constraints

Ví dụ:

```text id="z7c1nx"
T: Numeric
T: Copy
T: Send
```

Trait solver xử lý specialization/coherence.

Nhưng kết quả được lưu vào chung proof system.

---

# 18. Associated type constraints

Ví dụ:

```text id="b6p4yk"
Iterator<Item = T>
```

có thể tạo equality:

```text id="f8r2mz"
Iterator<T>::Item == T
```

Constraint engine quản lý dependency.

---

# 19. Generic value constraints

Ví dụ:

```text id="j4n9qx"
fn simd<T, N>()
where N > 0
```

Nếu:

```text id="c7m2vp"
N = 8
```

constraint proven.

Nếu:

```text id="y1x5ks"
N = runtime_value
```

thì compile-time solver không thể chứng minh.

API có thể yêu cầu runtime validation hoặc dynamic path.

---

# 20. Specialization

Constraint engine có thể quyết định:

```text id="w8q3mn"
if T: SIMD
```

để chọn implementation.

Ví dụ:

```text id="r2v7cx"
generic path
SIMD path
GPU path
```

Compiler specialization chọn path có proof hợp lệ.

---

# 21. Conditional compilation

`@cfg` có thể dựa trên constraint:

```text id="u6m1za"
target.arch == x86_64
```

hoặc:

```text id="x4q9bc"
feature("gpu")
```

Constraint evaluation xảy ra trước code generation.

---

# 22. Constraint implication

Một proof có thể imply proof khác.

Ví dụ:

```text id="n5v2pk"
N % 16 == 0
```

implies:

```text id="x8q4mw"
N % 8 == 0
```

Compiler có thể sử dụng implication rules.

---

# 23. Numeric constraints

Ví dụ:

```text id="r3m7cy"
T: Floating
```

hoặc:

```text id="p9x2kv"
N >= 2
```

hoặc:

```text id="b5q8zn"
stride > 0
```

Constraint solver có thể dùng arithmetic reasoning hạn chế.

Không cần full SMT solver trong compiler Core.

---

# 24. Vì sao không dùng SMT cho mọi thứ?

Một compiler không nên phụ thuộc bắt buộc vào:

```text id="j4w8mq"
Z3
CVC5
...
```

vì:

- binary lớn;
- compile latency;
- dependency;
- nondeterminism/version differences;
- khó self-host.

Axiom nên có **built-in lightweight solver**.

External theorem/SMT solver chỉ là optional development/verification tool.

---

# 25. Solver hierarchy

Có thể:

```text id="m6x1rv"
Level 0 — constant evaluation
Level 1 — canonicalization
Level 2 — equality/substitution
Level 3 — interval/range reasoning
Level 4 — linear constraints
Level 5 — domain-specific solvers
Level 6 — optional external prover
```

Compiler chỉ leo lên level cao hơn khi cần.

---

# 26. Range analysis

Ví dụ:

```text id="p8q4ys"
0 <= i < N
```

cho phép compiler loại bỏ:

```text id="g7m2xc"
array bounds check
```

Đây là một trong những ứng dụng quan trọng nhất.

---

# 27. Range facts

Compiler lưu:

```text id="d3n9vk"
RangeFact {
    value
    lower_bound
    upper_bound
    provenance
}
```

Ví dụ:

```text id="j5w8qa"
i ∈ [0, N-1]
```

Optimization engine sử dụng proof.

---

# 28. Overflow constraints

Ví dụ:

```text id="r1m7cz"
i + 1 < N
```

có thể chứng minh không overflow nếu type semantics yêu cầu.

Điều này kết nối:

```text id="q8x3vn"
Numeric
+
Range
+
Bounds
```

---

# 29. Alignment constraints

Ví dụ:

```text id="w4k9mb"
ptr % 32 == 0
```

có thể prove SIMD alignment.

Nhưng alignment assumption từ unsafe phải mang TrustedProof.

---

# 30. Alias constraints

Ví dụ:

```text id="s6v2px"
view<A> DISJOINT view<B>
```

Constraint engine có thể lưu:

```text id="y7m4qn"
AliasProof
```

để vectorizer/parallelizer dùng.

---

# 31. Effect constraints

Generic function có thể yêu cầu:

```text id="c9x2za"
F: Pure
```

hoặc:

```text id="n4m8vb"
F: NonBlocking
```

Compiler có thể kiểm tra effect subset.

---

# 32. Execution constraints

GPU kernel:

```text id="q2p7xc"
@kernel
```

có thể tạo constraints:

```text id="m8v3za"
NoFileIO
NoBlocking
DeviceSafe
NoHostPointer
```

Constraint engine dùng cùng infrastructure.

---

# 33. Ownership constraints

Ví dụ:

```text id="r7k1mq"
view<T> lifetime <= owner lifetime
```

đây là semantic constraint.

Không nhất thiết biểu diễn dưới dạng user-visible lifetime syntax.

Compiler solver xử lý internally.

---

# 34. Constraint solving order

Đề xuất:

```text id="h3x8qv"
Parse
 ↓
Resolve
 ↓
Collect Constraints
 ↓
Normalize
 ↓
Solve Cheap Constraints
 ↓
Propagate Facts
 ↓
Domain Solvers
 ↓
Monomorphization
 ↓
Re-solve
 ↓
Proof Finalization
```

Không nên giải toàn bộ constraint một lần duy nhất.

---

# 35. Incremental solving

CompilerDB phải cache:

```text id="u6r2mn"
ConstraintKey
SolverVersion
Dependencies
Proof
```

Nếu source thay đổi một function nhỏ:

```text id="g9x5vb"
```

không cần solve lại toàn project.

---

# 36. Proof invalidation

Khi dependency thay đổi:

```text id="m3q8yk"
proof → stale
```

không được sử dụng stale proof.

CompilerDB đánh dấu:

```text id="q7v1xc"
VALID
STALE
INVALID
```

---

# 37. Cyclic constraints

Generic types có thể tạo:

```text id="r5n8mz"
A requires B
B requires A
```

Solver phải phát hiện cycle.

Không được:

```text id="c2x7qa"
infinite recursion
```

---

# 38. Recursive trait constraints

Các constraint recursive cần termination strategy:

```text id="y4m9pk"
depth limit
cycle detection
coinductive rules
```

tùy loại solver.

Không được để source code dễ dàng tạo compiler stack overflow.

---

# 39. Constraint diagnostics

Thay vì:

```text id="s3v7nx"
type mismatch
```

Axiom nên có:

```text id="k8m2qc"
Required:
    Dim<T> = Length / Time

Found:
    Dim<T> = Length

Derived from:
    parameter `distance`
    parameter `time`

Constraint became inconsistent at:
    expression ...
```

Đây rất phù hợp với mục tiêu **AI-friendly compiler**.

---

# 40. Proof explanation

Compiler có thể xuất:

```text id="z6q1mw"
Why is this bounds check removable?

1. i >= 0
2. i < N
3. index range = [0, N-1]
4. array length = N
5. therefore index is valid
```

Không phải user cần đọc mỗi lần; đây là diagnostic/debug/AI interface.

---

# 41. AI compiler interface

Compiler có thể expose machine-readable:

```text id="p4n8yx"
ConstraintGraph
ProofGraph
FailedConstraint
SuggestedAssumption
```

AI agent có thể hỏi compiler:

```text id="f8m3vq"
"Why can't this kernel be parallelized?"
```

Compiler trả:

```text id="d7x1za"
WRITE(A[i])
WRITE(A[j])

Potential overlap:
    i == j is not disproven
```

Đây là một capability rất mạnh của Axiom.

---

# 42. Proof-guided optimization

Optimization pass có thể yêu cầu:

```text id="c6r9km"
require proof:
    NoAlias(A,B)
```

Nếu solver cung cấp proof:

```text id="n2x7qp"
→ optimization enabled
```

Nếu không:

```text id="y5m8zc"
→ giữ generic safe path
```

Không cần unsafe source annotation.

---

# 43. Runtime fallback

Constraint không chứng minh được compile time:

```text id="v4q9mx"
N % 8 == 0
```

compiler có thể tạo:

```text id="j7k2pn"
if N % 8 == 0
    optimized_path
else
    generic_path
```

nếu optimization semantics cho phép.

Đây là **runtime proof specialization**.

---

# 44. Versioned proofs

Proof phụ thuộc compiler semantics.

Do đó cache proof phải bao gồm:

```text id="e8m3qw"
language_semantic_version
compiler_version
target
feature_set
solver_version
dependencies
```

Tránh reuse proof không còn hợp lệ.

---

# 45. Comptime integration

`comptime` có thể generate constraint:

```text id="x2p7vn"
comptime {
    assert(...)
}
```

Nhưng assertion phải đi vào Proof/Constraint engine thay vì một hệ thống riêng.

---

# 46. Reflection integration

Reflection query:

```text id="m5c8zr"
is_numeric(T)
```

có thể trở thành compile-time proposition:

```text id="q9v1xb"
Numeric(T) == true
```

---

# 47. Units integration

378:

```text id="z4m7kp"
Dim<A> * Dim<B> == Dim<C>
```

379 cung cấp generic constraint infrastructure.

Unit solver trở thành domain solver chứ không phải một compiler subsystem biệt lập.

---

# 48. Tensor integration

Shape:

```text id="b6x2qn"
A[M,K]
B[K,N]
```

→ constraint:

```text id="r8v3ym"
K_A == K_B
```

Proof này có thể được dùng trực tiếp bởi:

- matmul;
- bounds elimination;
- kernel generation;
- GPU launch.

---

# 49. Graph integration

Graph algorithm:

```text id="q1m9vc"
Dijkstra
```

có thể yêu cầu:

```text id="t6x4za"
Weight:
    Ordered
    Additive
    NonNegative
```

Trait + value constraints được solve cùng framework.

---

# 50. Solver integration

ODE:

```text id="m7x2pk"
Dim(dy/dt) == Dim(rhs)
```

PDE:

```text id="v5q8nc"
Dim(lhs) == Dim(rhs)
```

Tất cả đi qua cùng constraint architecture.

---

# 51. CompilerDB

Task 379 bổ sung:

```text id="q4m8yb"
ConstraintDB
ConstraintNodeDB
ConstraintExprDB
ConstraintVariableDB
ConstraintDomainDB
ConstraintDependencyDB
ConstraintNormalizationDB
ConstraintPropagationDB
ConstraintSolverDB
ConstraintSolverCacheDB
ConstraintStateDB
ConstraintConflictDB
ConstraintCycleDB
ConstraintDiagnosticDB

ProofDB
ProofNodeDB
ProofEdgeDB
ProofDerivationDB
ProofDependencyDB
ProofProvenanceDB
ProofValidityDB
ProofInvalidationDB
ProofCacheDB
ProofExplainDB
ProofExportDB

FactDB
FactNodeDB
FactRangeDB
FactEqualityDB
FactInequalityDB
FactAliasDB
FactOwnershipDB
FactCapabilityDB
FactEffectDB
FactExecutionDB
FactLayoutDB
FactNumericalDB

GenericConstraintDB
ShapeConstraintDB
DimensionConstraintDB
UnitConstraintDB
NumericConstraintDB
TraitConstraintDB
```

---

# 52. MIR additions

Constraint engine không nên biến MIR thành theorem-prover IR quá nặng.

Chỉ cần semantic anchors:

```text id="e9w3qa"
ASSERT_COMPTIME
ASSUME_TRUSTED
PROVE
CHECK_CONSTRAINT
RUNTIME_GUARD
PROOF_GUARD
PROOF_INVALIDATE
```

Optimization phase có thể dùng proof metadata ngoài MIR.

---

# 53. Proof-carrying transformations

Ví dụ vectorization:

```text id="u7m2xc"
Original loop
        ↓
Dependence analysis
        ↓
NoAlias proof
        ↓
Bounds proof
        ↓
Numerical proof
        ↓
Vectorized loop
```

Transformation lưu:

```text id="n3v8qy"
TransformationProof
```

Validation engine có thể kiểm tra lại.

---

# 54. Constraint solver không phải theorem prover đầy đủ

Đây là giới hạn quan trọng.

Axiom Core chỉ cần giải tốt:

```text id="x5q9mk"
equalities
inequalities
ranges
types
traits
shapes
dimensions
effects
ownership facts
layout facts
```

Không cần chứng minh:

```text id="r4c7zn"
Goldbach conjecture
```

hay arbitrary mathematical theorem.

---

# 55. External prover

Sau này có thể:

```text id="k8m2vx"
axiom verify --external-prover
```

sử dụng SMT/theorem prover để:

- compiler development;
- library verification;
- formal certification;
- research.

Nhưng kết quả external phải được:

```text id="m2q7yc"
validated
versioned
scoped
```

Không trở thành mandatory compiler dependency.

---

# 56. Invariants

### `ACONSTRAINT-01`
Mọi compile-time constraint phải có trạng thái explicit.

### `ACONSTRAINT-02`
`UNKNOWN` không được coi là `FALSE`.

### `ACONSTRAINT-03`
Compiler không được sử dụng proof đã invalid.

### `ACONSTRAINT-04`
Mọi proof phải có dependency provenance.

### `ACONSTRAINT-05`
Unsafe assumption phải có scope và provenance.

### `ACONSTRAINT-06`
Constraint solver phải hỗ trợ incremental invalidation.

### `ACONSTRAINT-07`
Constraint normalization phải tạo canonical representation.

### `ACONSTRAINT-08`
Solver phải phát hiện cyclic dependency nguy hiểm.

### `ACONSTRAINT-09`
Solver failure không được gây compiler hang vô hạn.

### `ACONSTRAINT-10`
Generic constraints có thể defer tới instantiation.

### `ACONSTRAINT-11`
Trait constraints phải tích hợp dependency/proof infrastructure chung.

### `ACONSTRAINT-12`
Shape constraints phải có thể được dùng bởi optimization.

### `ACONSTRAINT-13`
Dimension constraints phải có thể được dùng bởi scientific type checking.

### `ACONSTRAINT-14`
Range proofs có thể được dùng để loại bỏ bounds checks.

### `ACONSTRAINT-15`
Alias proofs có thể được dùng bởi vectorization/parallelization.

### `ACONSTRAINT-16`
Effect proofs có thể được dùng để xác định legality của transformation.

### `ACONSTRAINT-17`
Execution-domain proofs phải được kiểm tra trước code generation.

### `ACONSTRAINT-18`
Proofs không được thay đổi observable program semantics.

### `ACONSTRAINT-19`
Runtime guards phải preserve correctness khi compile-time proof unavailable.

### `ACONSTRAINT-20`
Specialized fast paths phải có fallback hợp lệ nếu runtime condition false.

### `ACONSTRAINT-21`
Proof cache phải phụ thuộc compiler/language semantic version.

### `ACONSTRAINT-22`
Proof cache phải phụ thuộc target/configuration khi cần.

### `ACONSTRAINT-23`
Comptime assertions phải tích hợp constraint infrastructure.

### `ACONSTRAINT-24`
Reflection predicates phải có thể trở thành compile-time constraints.

### `ACONSTRAINT-25`
Proof explanations phải giữ đủ provenance để compiler/AI giải thích kết quả.

### `ACONSTRAINT-26`
External provers không phải mandatory compiler dependencies.

### `ACONSTRAINT-27`
Trusted proof phải được phân biệt với intrinsically verified proof.

### `ACONSTRAINT-28`
Constraint solver không được yêu cầu full theorem proving cho Core compilation.

### `ACONSTRAINT-29`
Optimization pass chỉ được yêu cầu proof mà transformation thực sự cần.

### `ACONSTRAINT-30`
Constraint/proof infrastructure không được tạo runtime overhead khi proof đã được compile-time discharge.

---

## Kiến trúc mới sau 379

Đây là một task có ý nghĩa kiến trúc rất lớn:

```text
                    Axiom Compiler
                         │
                  Constraint Engine
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   Type/Trait       Shape/Dimension    Ownership
        │                │                │
        ├────────────┬───┴────┬───────────┤
        │            │        │           │
      Alias        Effect   Numeric     Execution
        │            │        │           │
        └────────────┴────────┴───────────┘
                         │
                    Proof Graph
                         │
             ┌───────────┼───────────┐
             │           │           │
          Compiler    Optimizer    AI/IDE
          Correctness  Legality   Explanation
```

Điểm cốt lõi của **379** là từ đây Axiom không còn có hàng chục subsystem “tự suy luận” độc lập. Chúng chia sẻ một **ngôn ngữ constraint/proof nội bộ thống nhất**.

Điều này đặc biệt phù hợp với mục tiêu ban đầu của Axiom:

> **Programmer viết ít annotation; compiler tự chứng minh càng nhiều càng tốt.**

Ví dụ một đoạn code có thể đồng thời được compiler chứng minh:

```text
Shape hợp lệ
+ Dimension hợp lệ
+ Alias không chồng lấn
+ Bounds hợp lệ
+ Không data race
+ SIMD legal
+ GPU legal
```

mà programmer không cần viết một loạt `lifetime`, `restrict`, `unsafe`, `shape assertion` hay optimization pragma chỉ để giúp compiler hiểu điều mà compiler hoàn toàn có khả năng tự suy luận.