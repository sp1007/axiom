# BOOTSTRAP-372 — Axiom Symbolic Computation, Expression Graph & Compile-Time Algebra Engine

Sau **371 — Automatic Differentiation**, bước tiếp theo nên là **Symbolic/Expression Computation**.

Lý do: AD đã giúp Axiom biến chương trình thành gradient/JVP/VJP, nhưng để compiler có thể **tối ưu các biểu thức toán học ở mức cao hơn**, cần một tầng hiểu được cấu trúc biểu thức thay vì chỉ nhìn thấy các phép toán MIR riêng lẻ.

Mục tiêu không phải biến Axiom thành Mathematica/SymPy. Mục tiêu là xây một **Expression Algebra Engine** có thể dùng chung cho:

- constant folding nâng cao;
- symbolic simplification;
- AD;
- tensor expression fusion;
- linear algebra rewriting;
- compile-time math;
- kernel generation;
- shape reasoning;
- numerical optimization.

---

## 1. Ba loại biểu thức phải được phân biệt

Axiom cần phân biệt:

```text
Runtime Expression
Compile-Time Expression
Symbolic Expression
```

Ví dụ:

```text
let x = runtime_value();
let y = x * 2;
```

là runtime.

Trong:

```text
comptime {
    let x = 10;
    let y = x * 2;
}
```

compiler có thể evaluate hoàn toàn.

Còn:

```text
symbolic x;
y = x * x + 2*x;
```

là symbolic representation.

Ba loại này có thể dùng chung một số infrastructure nhưng **không được nhập nhằng semantic**.

---

# 2. Không thêm Symbolic Runtime Object vào Core

Không nên biến mọi biểu thức thành:

```text
ExprNode*
ExprNode*
ExprNode*
```

ở runtime.

Đây sẽ tạo:

- allocation;
- indirection;
- object lifetime;
- virtual dispatch;
- cache miss.

Thay vào đó:

```text
Source
 ↓
AST/HIR
 ↓
Expression Graph
 ↓
Optimization
 ↓
ordinary MIR
```

Expression graph chủ yếu là **compiler representation**.

Nếu người dùng muốn symbolic expression runtime, đó là library abstraction.

---

# 3. Expression DAG thay vì AST thuần túy

AST:

```text
       +
      / \
     *   *
    / \ / \
   x  x x  2
```

có thể chứa nhiều node trùng lặp.

Compiler nên canonicalize thành DAG:

```text
       +
      / \
     *   2
    / \
   x   x
```

và nhận ra:

```text
x*x
```

chỉ cần một expression node.

---

# 4. Structural identity

Expression engine cần phân biệt:

```text
a + b
```

và:

```text
b + a
```

Không được tự động coi chúng giống nhau nếu numerical semantics không cho phép.

Đây là điểm rất quan trọng với floating point.

Ví dụ:

```text
(a + b) + c
```

không nhất thiết bằng:

```text
a + (b + c)
```

ở floating-point.

Do đó expression canonicalization phải phụ thuộc:

```text
NumericalContract
```

---

# 5. Algebraic identities

Compiler có thể biết các identity:

```text
x + 0 = x
x * 1 = x
x * 0 = 0
x - x = 0
x / 1 = x
```

nhưng chỉ rewrite khi semantics cho phép.

Ví dụ:

```text
x * 0
```

với floating-point không nhất thiết đơn giản tuyệt đối thành `0` nếu cần bảo toàn:

```text
NaN
signed zero
```

Do đó:

```text
AlgebraicIdentityProof
```

phải đi kèm.

---

# 6. Integer và floating-point có algebra khác nhau

Integer:

```text
x + 0 = x
```

thường có thể chứng minh theo semantics.

Floating point:

```text
x + 0 = x
```

có thể phụ thuộc:

```text
-0
NaN
rounding
```

Axiom không được dùng algebra của số thực cho machine floating-point một cách mù quáng.

---

# 7. Numerical contract

Expression optimizer đọc:

```text
Strict
Deterministic
Fast
Approximate
```

để quyết định phép biến đổi.

Ví dụ:

```text
(a + b) + c
```

→

```text
a + (b + c)
```

chỉ legal nếu numerical contract cho phép reassociation.

---

# 8. Common Subexpression Elimination

Expression DAG hỗ trợ mạnh cho:

```text
let a = expensive(x);
let b = expensive(x);
```

Compiler có thể nhận ra:

```text
expensive(x)
```

giống nhau và dùng chung kết quả.

Nhưng chỉ nếu:

```text
pure
same inputs
same effects
same numerical semantics
```

---

# 9. Pure expression

Expression engine cần metadata:

```text
ExpressionEffect
```

Ví dụ:

```text
x * y
```

pure.

Trong khi:

```text
read_sensor()
```

có effect.

Không được CSE:

```text
read_sensor()
```

chỉ vì AST giống nhau.

---

# 10. Expression categories

Mỗi expression có thể thuộc:

```text
Literal
Variable
Unary
Binary
Call
Cast
Load
Store
Index
Reduction
TensorOp
LinearAlgebraOp
Derivative
```

Expression engine không cần hiểu toàn bộ semantics của mọi library.

Nó sử dụng trait/interface:

```text
AlgebraicOperator
```

để mở rộng.

---

# 11. Operator properties

Compiler có thể lưu:

```text
Associative
Commutative
Idempotent
Identity
Absorbing
Distributive
Invertible
Monotonic
Pure
Deterministic
```

Ví dụ:

```text
integer addition
```

có:

```text
Associative
Commutative
Identity = 0
```

theo integer semantics tương ứng.

Floating-point addition không mặc định được đánh dấu `Associative`.

---

# 12. Algebraic traits không phải subtype

Không cần:

```text
class Number
class Ring extends Number
class Field extends Ring
```

Thay vào đó:

```text
trait Add
trait Mul
trait Ring
trait Field
```

và compiler/comptime có thể sử dụng metadata.

Điều này phù hợp với thiết kế struct + trait của Axiom.

---

# 13. Symbolic variables

Nếu library cần symbolic runtime/compile-time:

```text
Symbol<T>
```

có thể tồn tại ở library.

Nhưng compiler hiểu:

```text
SymbolicExpressionDB
```

ở compile-time.

Ví dụ:

```text
comptime let x = symbol<f64>("x");
```

có thể tạo expression graph.

---

# 14. Symbolic simplification

Engine cần rewrite system.

Ví dụ:

```text
x + x
```

→

```text
2*x
```

nếu algebra contract cho phép.

Hoặc:

```text
x*x
```

→

```text
pow(x, 2)
```

chỉ khi target optimization có lợi.

Compiler **không nên biến mọi expression thành canonical mathematical notation**.

Mục tiêu là tối ưu machine execution.

---

# 15. Rewrite rules

Một rewrite:

```text
A → B
```

phải có:

```text
RewriteRule {
    pattern
    replacement
    precondition
    semantic_contract
    cost_model
}
```

Ví dụ:

```text
x * 1 → x
```

với precondition:

```text
no observable NaN/exception difference
```

---

# 16. Rewrite termination

Một hệ rewrite tự do có thể tạo vòng:

```text
x*x → pow(x,2)
pow(x,2) → x*x
```

Do đó compiler phải có:

```text
RewritePriority
RewritePhase
CanonicalForm
```

và mỗi phase có termination guarantee.

Không cho rewrite engine chạy vô hạn.

---

# 17. E-Graph

Axiom có thể dùng **e-graph/equality saturation** ở compiler layer cho những optimization phức tạp.

Concept:

```text
a + (b + c)
```

có thể giữ nhiều equivalent representation:

```text
(a+b)+c
a+(b+c)
...
```

sau đó cost model chọn implementation.

Nhưng đây **không được là mandatory representation cho toàn compiler**.

Chỉ dùng khi bài toán đủ phức tạp.

---

# 18. Equality không có nghĩa là bit-identical

Compiler phải phân biệt:

```text
SemanticEquivalent
NumericallyEquivalent
BitEquivalent
ObservableEquivalent
```

Ví dụ hai floating expressions có cùng toán học nhưng khác rounding.

Chỉ:

```text
BitEquivalent
```

mới cho phép thay thế trong Strict FP profile.

---

# 19. Tensor expression graph

Task 369/370 đã có tensor expression graph.

372 nên biến nó thành infrastructure dùng chung.

Ví dụ:

```text
C = A @ B + D @ E
```

Expression graph:

```text
        +
       / \
     matmul matmul
      / \    / \
     A   B  D   E
```

Compiler có thể:

- fuse;
- tile;
- reorder;
- common-subexpression;
- chọn kernel;
- materialize;
- tránh temporary.

---

# 20. Linear algebra rewriting

Ví dụ:

```text
transpose(A @ B)
```

có thể rewrite thành:

```text
transpose(B) @ transpose(A)
```

nhưng phải kiểm tra:

```text
layout
storage
numerical contract
alias
```

Đặc biệt nếu transpose chỉ là view thì cost model có thể chọn giữ expression ban đầu.

---

# 21. Matrix multiplication reassociation

Ví dụ:

```text
(A @ B) @ C
```

và:

```text
A @ (B @ C)
```

có cùng mathematical result nhưng cost có thể rất khác.

Expression engine + shape information có thể chọn:

```text
A @ (B @ C)
```

nếu số phép tính thấp hơn.

Đây là một optimization rất mạnh cho compiler.

---

# 22. Shape-aware algebra

Expression node cần có:

```text
Shape
Layout
DType
Storage
Device
NumericalContract
```

Ví dụ:

```text
A: [1024,64]
B: [64,1024]
```

compiler biết:

```text
A @ B
```

hợp lệ.

Nếu:

```text
A: [1024,64]
B: [32,1024]
```

thì reject trước code generation.

---

# 23. Symbolic shape

Shape có thể chứa:

```text
N
M
K
```

và constraint:

```text
A: [N,K]
B: [K,M]
```

Expression engine không cần biết giá trị runtime của `K`.

Shape solver chỉ cần chứng minh:

```text
A.cols == B.rows
```

---

# 24. Compile-time algebra

Comptime có thể dùng engine để tính:

```text
comptime let n = 2^10;
comptime let tile = choose_tile(n);
```

hoặc:

```text
comptime let layout = derive_layout(shape);
```

Không cần textual macro.

---

# 25. AD integration

372 phải cung cấp expression structure cho 371.

Ví dụ:

```text
f(x) = x*x + sin(x)
```

AD có thể thấy:

```text
Add(
    Mul(x,x),
    Sin(x)
)
```

và áp derivative rule trực tiếp.

Điều này tốt hơn việc AD phải reverse-engineer machine instructions.

---

# 26. AD + expression simplification

Sau AD:

```text
2*x + cos(x)
```

compiler có thể simplify.

Ví dụ derivative của:

```text
x + x
```

có thể ban đầu sinh:

```text
1 + 1
```

rồi simplify thành:

```text
2
```

Nhưng simplification phải chạy trước khi target lowering.

---

# 27. Gradient graph fusion

Ví dụ:

```text
y = sin(x * x)
```

backward graph:

```text
dy
 ↓
cos(x*x)
 ↓
2*x
```

Compiler có thể fuse thành một kernel thay vì tạo intermediate tensors.

Đây là nơi:

```text
ExpressionGraph
+
ADGraph
+
TensorGraph
```

nên hội tụ.

---

# 28. Cost model

Không phải expression đơn giản nhất về mặt algebra là nhanh nhất.

Compiler phải có:

```text
ExpressionCostModel
```

xem:

- instruction count;
- latency;
- throughput;
- register pressure;
- memory traffic;
- vectorization;
- cache;
- GPU occupancy;
- kernel launch;
- temporary allocation;
- numerical precision.

Ví dụ:

```text
pow(x,2)
```

có thể không tốt bằng:

```text
x*x
```

trên một số target.

---

# 29. Materialization boundary

Expression graph có thể giữ lazy lâu nhất có thể.

Nhưng compiler phải quyết định lúc nào cần:

```text
MATERIALIZE
```

Ví dụ:

```text
A @ B + C @ D
```

có thể fused.

Nhưng nếu:

```text
let x = ...
call_external(x)
```

và external API yêu cầu contiguous buffer, phải materialize.

---

# 30. CompilerDB

Task này bổ sung:

```text
ExpressionDB
ExpressionNodeDB
ExpressionGraphDB
ExpressionDagDB
ExpressionIdentityDB
ExpressionEffectDB
ExpressionPropertyDB
ExpressionTypeDB
ExpressionShapeDB
ExpressionLayoutDB
ExpressionStorageDB
ExpressionDeviceDB
ExpressionRewriteDB
RewriteRuleDB
RewritePhaseDB
RewriteProofDB
CanonicalFormDB
AlgebraPropertyDB
AlgebraIdentityDB
AlgebraLawDB
EqualityDB
EqualityClassDB
EGraphDB
EGraphRuleDB
EGraphCostDB
ExpressionCostModelDB
ExpressionCseDB
ExpressionFusionDB
ExpressionMaterializationDB
ExpressionSymbolicDB
SymbolDB
SymbolicConstraintDB
ExpressionComptimeDB
ExpressionADDB
ExpressionTensorDB
ExpressionLinearAlgebraDB
ExpressionVerificationDB
```

---

# 31. MIR additions

Ở mức MIR semantic:

```text
EXPR_BEGIN
EXPR_END

EXPR_REWRITE
EXPR_CANONICALIZE
EXPR_CSE
EXPR_FUSE
EXPR_MATERIALIZE

ALGEBRA_ADD
ALGEBRA_MUL
ALGEBRA_DIV
ALGEBRA_POW

ALGEBRA_REDUCE
ALGEBRA_DISTRIBUTE
ALGEBRA_FACTOR

SYMBOLIC_CONST
SYMBOLIC_VAR
SYMBOLIC_APPLY
```

Tuy nhiên phần lớn:

```text
EXPR_*
SYMBOLIC_*
```

sẽ biến mất trước final MIR.

Chúng là **compiler semantic infrastructure**, không phải runtime instruction.

---

# 32. Proof system

Mỗi rewrite quan trọng phải có:

```text
ExpressionRewriteProof
```

gồm:

```text
OriginalExpression
ReplacementExpression
Preconditions
NumericalContract
EffectContract
TypeContract
ShapeContract
LayoutContract
AliasContract
CostJustification
```

---

# 33. Một nguyên tắc cực kỳ quan trọng

Axiom **không được trở thành compiler chỉ tối ưu khi hiểu toán học**.

Ví dụ:

```text
fn f(x: MyNumber) {
    ...
}
```

library có thể cung cấp algebra metadata.

Compiler có thể hiểu:

```text
Add
Mul
Zero
One
```

mà không cần biết `MyNumber` là class con của `Number`.

Đây là lý do trait + semantic metadata phù hợp với Axiom.

---

# 34. Invariants

### `ASYM-01`
Symbolic representation không phải runtime requirement.

### `ASYM-02`
Expression graph không được bắt buộc allocation.

### `ASYM-03`
Expression graph có thể được materialize bằng SSA/MIR.

### `ASYM-04`
Algebraic rewrite phải tuân type semantics.

### `ASYM-05`
Algebraic rewrite phải tuân numerical contract.

### `ASYM-06`
Compiler không được áp dụng mathematical identity nếu machine semantics không chứng minh tương đương.

### `ASYM-07`
Floating-point reassociation không được mặc định legal.

### `ASYM-08`
Expression CSE chỉ được áp dụng khi effect semantics cho phép.

### `ASYM-09`
Expression optimizer phải phân biệt semantic equivalence và bit equivalence.

### `ASYM-10`
Rewrite rules phải có termination strategy.

### `ASYM-11`
Rewrite cycle không được làm compiler non-terminating.

### `ASYM-12`
E-graph là optimization facility, không phải mandatory compiler representation.

### `ASYM-13`
E-graph extraction phải tuân semantic constraints.

### `ASYM-14`
Cost model được phép quyết định giữa các semantic-equivalent representations.

### `ASYM-15`
Shape constraints phải được kiểm tra trước phép toán tensor/linear algebra.

### `ASYM-16`
Symbolic shape phải hỗ trợ runtime dimensions khi có constraint tương ứng.

### `ASYM-17`
Expression optimization không được phá ownership.

### `ASYM-18`
Expression optimization không được phá capability/alias guarantees.

### `ASYM-19`
Expression fusion không được thay đổi observable evaluation semantics.

### `ASYM-20`
Expression materialization chỉ xảy ra khi semantic/ABI/execution boundary yêu cầu hoặc cost model chứng minh cần.

### `ASYM-21`
Expression engine phải tích hợp với Tensor semantics.

### `ASYM-22`
Expression engine phải tích hợp với Linear Algebra semantics.

### `ASYM-23`
Expression engine phải tích hợp với AD transformation.

### `ASYM-24`
AD-generated expressions phải được phép đi qua cùng rewrite infrastructure.

### `ASYM-25`
Comptime expression evaluation không được tạo runtime dependency ngoài semantics được yêu cầu.

### `ASYM-26`
Symbolic runtime libraries không được tự động trở thành compiler runtime dependency.

### `ASYM-27`
Custom algebra properties phải có explicit semantic contract.

### `ASYM-28`
Compiler không được giả định algebraic laws chỉ vì tên operator.

### `ASYM-29`
Expression optimization phải có verification/validation path.

### `ASYM-30`
Mọi expression abstraction không còn observable sau optimization phải được xóa hoàn toàn khỏi generated code.

---

## Kiến trúc sau 372

Lúc này tầng toán học của Axiom bắt đầu có một cấu trúc khá mạnh:

```text
                 Numeric Semantics
                        │
                        ▼
               Expression Algebra
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
       Tensor      Linear Algebra      AD
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                Unified Expr Graph
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
        SIMD         Parallel         GPU
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                  Native Backend
```

Điểm quan trọng là **371 và 372 không tạo hai hệ thống riêng biệt**. AD, Tensor và Linear Algebra đều có thể cùng đi qua **Expression Graph → Optimization → MIR**, giúp Axiom tránh việc về sau phải xây ba compiler optimizer khác nhau cho AI, toán học và GPU.