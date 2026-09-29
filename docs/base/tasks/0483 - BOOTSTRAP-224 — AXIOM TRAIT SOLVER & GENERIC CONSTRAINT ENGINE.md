# BOOTSTRAP-224 — AXIOM TRAIT SOLVER & GENERIC CONSTRAINT ENGINE

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là phần quyết định Axiom có thể đạt được mục tiêu **generic mạnh nhưng không biến compiler thành một hệ thống type-level quá phức tạp**.

Nguyên tắc trung tâm:

> **Trait solver chỉ chứng minh các semantic obligations cần thiết. Nó không trở thành một ngôn ngữ lập trình type-level riêng.**

---

## 1. Vai trò của Trait Solver

Pipeline:

```text
Typed HIR
   │
   ├── Type equality
   ├── Generic constraints
   ├── Trait obligations
   └── Associated-type projections
             │
             ▼
        Trait Solver
             │
      ┌──────┼──────┐
      ▼      ▼      ▼
   Proven  Failed  Ambiguous
      │
      ▼
Resolved Typed HIR
```

Trait solver **không được phép**:

- tự sửa program;
- tự chọn candidate dựa trên thứ tự hash;
- tạo implicit conversion;
- bỏ qua ambiguity;
- biến `Unknown` thành `Proven`.

---

# 2. Trait là gì?

Trait là **behavioral contract**.

```axiom
trait Add<Rhs> {
    type Output

    fn add(self, rhs: Rhs) -> Self::Output
}
```

Trait không phải:

```text
class
interface object
vtable
runtime type
```

Trait có thể hoàn toàn biến mất sau compilation nếu static dispatch được dùng.

---

# 3. Trait declaration

Semantic representation:

```text
TraitDef {
    id: TraitId
    name: Symbol
    generic_params: GenericParams
    supertraits: [TraitRef]
    associated_types: [AssocTypeDef]
    associated_consts: [AssocConstDef]
    methods: [MethodDef]
    visibility: Visibility
    attributes: TraitAttributes
}
```

---

# 4. Trait reference

Ví dụ:

```text
T: Ord
```

được biểu diễn:

```text
TraitRef {
    trait: Ord
    self_type: T
    args: []
}
```

Ví dụ:

```text
T: Add<U>
```

```text
TraitRef {
    trait: Add
    self_type: T
    args: [U]
}
```

---

# 5. Trait Goal

Solver nhận:

```text
Goal
```

Ví dụ:

```text
Prove(T: Ord)
```

hoặc:

```text
Prove(Point: Add<Point, Output = Point>)
```

hoặc:

```text
Normalize(<T as Iterator>::Item) = U
```

---

# 6. Solver result

Chuẩn hóa thành:

```text
TraitResult =
    Proven
    NotProven
    Ambiguous
    Error
```

Không dùng Boolean.

`false` và `chưa đủ thông tin` là hai trạng thái hoàn toàn khác nhau.

---

# 7. Impl declaration

Ví dụ:

```axiom
impl Add<i32> for Point {
    type Output = Point

    fn add(self, rhs: i32) -> Point {
        ...
    }
}
```

Semantic:

```text
ImplDef {
    id: ImplId
    trait_ref: Add<i32> for Point
    generics: ...
    where_clauses: ...
    associated_values: ...
    methods: ...
}
```

---

# 8. Generic impl

```axiom
impl<T: Add<T>> Add<T> for Vec<T> {
    ...
}
```

Candidate áp dụng cho:

```text
Vec<i32>
Vec<f32>
```

nếu obligation:

```text
i32: Add<i32>
```

hoặc:

```text
f32: Add<f32>
```

được chứng minh.

---

# 9. Candidate selection

Với:

```text
T: Trait
```

solver:

```text
lookup trait
    ↓
collect impl candidates
    ↓
unify candidate
    ↓
apply substitutions
    ↓
generate where-obligations
    ↓
solve nested obligations
    ↓
filter invalid candidates
    ↓
select exactly one
```

---

# 10. Không chọn theo declaration order

Nếu:

```text
impl A for T
impl B for T
```

cùng match một goal nhưng không có semantic rule phân biệt:

```text
T: Trait
```

→ ambiguity.

Không:

```text
"candidate đầu tiên thắng"
```

---

# 11. Coherence

Axiom cần coherence mạnh.

Một trait/type combination phải có **một implementation hợp lệ duy nhất** trong một package coherence domain.

Điều này ngăn:

```text
Package A:
impl Display for User

Package B:
impl Display for User
```

và chương trình không biết implementation nào đúng.

---

# 12. Orphan rule

Đề xuất:

Một package chỉ được implement trait cho type nếu package đó sở hữu:

- trait; hoặc
- type.

Ví dụ:

```text
my_trait + foreign_type       → allowed
foreign_trait + my_type       → allowed
my_trait + my_type            → allowed
foreign_trait + foreign_type  → rejected
```

---

# 13. Fundamental types

Compiler cần đánh dấu một số type/compiler primitives là:

```text
fundamental
```

để coherence không bị phá bởi wrapper/newtype rules.

Ví dụ:

```text
Option
Result
view
mut_view
function types
```

có thể có compiler-defined treatment.

---

# 14. Blanket impl

Ví dụ:

```axiom
impl<T: Copy> Clone for T {
    ...
}
```

là blanket implementation.

Solver phải index chúng cẩn thận vì:

```text
impl<T> Trait for T
```

có thể match cực nhiều type.

---

# 15. Impl indexing

Không scan toàn bộ impl database.

Index theo:

```text
TraitId
+
SelfTypeHead
+
Generic shape
```

Ví dụ:

```text
Add + Point
Add + Vec
Add + primitive
```

---

# 16. Type head

Ví dụ:

```text
Vec<i32>
```

type head:

```text
Vec
```

```text
i32
```

type head:

```text
I32
```

```text
T
```

type head:

```text
TypeVariable
```

Blanket impl có thể có:

```text
Wildcard
```

---

# 17. Generic substitution

```text
Substitution {
    params: [GenericParamId]
    values: [TypeId | ConstValue]
}
```

Ví dụ:

```text
T → i32
U → f64
N → 16
```

---

# 18. Substitution phải immutable

Không mutate substitution đang được dùng bởi query khác.

Tạo:

```text
S'
```

từ:

```text
S
```

Điều này giúp incremental compiler và parallel solver an toàn.

---

# 19. Where clause

```axiom
fn sort<T>(x: mut_view<T>)
where
    T: Ord
{
    ...
}
```

được chuyển thành:

```text
GenericConstraint:
    T: Ord
```

Body được type-check trong environment đã có assumption:

```text
Assumption(T: Ord)
```

---

# 20. Assumption vs proven fact

Đây là điểm quan trọng.

Trong generic function:

```text
T: Ord
```

solver không cần tìm implementation cụ thể.

Nó có thể trả:

```text
ProvenByAssumption
```

về mặt nội bộ.

Không được nhầm với concrete implementation.

---

# 21. Solver environment

```text
SolverEnv {
    assumptions
    substitutions
    recursion_depth
    target_context
    mode
}
```

`target_context` chỉ được dùng khi trait/constraint thực sự target-dependent.

---

# 22. Supertrait

```axiom
trait Ordered: Eq + Comparable {
}
```

Nếu:

```text
T: Ordered
```

solver có thể derive:

```text
T: Eq
T: Comparable
```

nhưng chỉ thông qua declaration của `Ordered`.

---

# 23. Supertrait graph

Trait graph phải kiểm tra cycle:

```text
A: B
B: C
C: A
```

→ declaration error.

Không để cycle lọt vào solver.

---

# 24. Associated type

```axiom
trait Iterator {
    type Item
}
```

Projection:

```text
<T as Iterator>::Item
```

là:

```text
Projection {
    self_type: T
    trait: Iterator
    assoc: Item
}
```

---

# 25. Projection normalization

Ví dụ:

```axiom
impl Iterator for Counter {
    type Item = i32
}
```

thì:

```text
<Counter as Iterator>::Item
```

normalize:

```text
i32
```

---

# 26. Projection với generic

```axiom
impl<T> Iterator for Vec<T> {
    type Item = T
}
```

Do đó:

```text
<Vec<f32> as Iterator>::Item
```

→

```text
f32
```

---

# 27. Lazy normalization

Không eagerly normalize mọi projection.

Chỉ normalize khi:

- type equality cần;
- function signature cần;
- overload/method resolution cần;
- layout cần;
- MIR lowering cần.

---

# 28. Associated constants

Cho phép:

```axiom
trait Numeric {
    const ZERO: Self
}
```

Projection:

```text
<T as Numeric>::ZERO
```

Type checker phải biết:

```text
type = T
```

nhưng value resolution có thể deferred tới monomorphization/comptime khi thích hợp.

---

# 29. Associated functions

Trait:

```axiom
trait Factory {
    fn create() -> Self
}
```

Call:

```text
T::create()
```

tạo trait obligation:

```text
T: Factory
```

và method resolution.

---

# 30. Default methods

```axiom
trait Printable {
    fn print(self) {
        ...
    }
}
```

Concrete impl có thể override.

Không cần:

```text
override
```

trong Core.

---

# 31. Override semantics

Nếu concrete impl có:

```text
fn print(self) { ... }
```

thì concrete method thắng default method.

Nhưng:

```text
impl Printable for T
```

chỉ được có **một method implementation** cho mỗi trait method.

---

# 32. Method resolution

Với:

```axiom
x.foo()
```

candidate order đã frozen:

```text
1. inherent methods
2. trait methods
3. imported extension methods
4. generic extension methods
```

Mỗi candidate được type-check bằng solver.

---

# 33. Inherent method

```axiom
fn length(self: Vec2) -> f32
```

không cần trait.

Compiler index:

```text
TypeId(Vec2)
+
method name
```

để lookup O(1)/gần O(1).

---

# 34. Trait method candidate

Nếu:

```axiom
trait Length {
    fn length(self) -> usize
}
```

và:

```text
Vec2: Length
```

solver xác nhận implementation.

---

# 35. Extension method

```axiom
fn length(v: Vec2) -> usize
```

nếu được import có thể cho:

```text
v.length()
```

Nhưng extension method không được tự động tìm trên toàn package graph.

Chỉ search trong explicit import scope.

---

# 36. Generic extension

Ví dụ:

```axiom
fn first<T>(x: view<Vec<T>>) -> Option<T>
```

có thể được candidate sau extension thông thường.

---

# 37. Ambiguous method

Nếu:

```text
A::foo
B::foo
```

đều match:

```text
x.foo()
```

và không có priority rule:

```text
AXTRAIT-AMBIGUOUS
```

Compiler không đoán.

---

# 38. Trait solver và operator

```axiom
a + b
```

→:

```text
Goal:
    Add<typeof(a), typeof(b)>
```

Resolve:

```text
Output
method
```

Sau đó Typed HIR chứa implementation cụ thể hoặc dispatch descriptor.

---

# 39. Static dispatch

Mặc định:

```text
T: Trait
```

→ static dispatch.

Sau monomorphization:

```text
call concrete_function
```

Không tạo vtable nếu không cần.

---

# 40. Dynamic dispatch

Chỉ khi:

```axiom
dyn Trait
```

hoặc API yêu cầu dynamic dispatch.

Solver tạo:

```text
DynDispatchInfo
```

và ABI phase quyết định representation.

---

# 41. Trait solver không tạo heap

Trait resolution:

```text
T: Trait
```

không có semantic allocation.

Dynamic trait object có thể cần runtime metadata, nhưng đó là representation concern.

---

# 42. Trait object compatibility

Trait có thể không compatible với:

```text
dyn Trait
```

nếu method yêu cầu những thông tin không tồn tại sau type erasure.

Ví dụ generic method:

```axiom
trait Foo {
    fn transform<T>(self, x: T)
}
```

không thể tự động trở thành dyn method.

---

# 43. Self-sensitive methods

Methods trả:

```text
Self
```

hoặc nhận concrete `Self` có thể yêu cầu special object-safety treatment.

Solver phải kiểm tra explicit dyn compatibility.

---

# 44. Generic trait

```axiom
trait Converter<T> {
    fn convert(self) -> T
}
```

Goal:

```text
Point: Converter<String>
```

TraitRef phải bao gồm:

```text
TraitId
Self
GenericArguments
```

---

# 45. Multiple trait parameters

```axiom
trait Add<Rhs, Output> {
}
```

cho phép solver unify:

```text
Add<i32, f64, f64>
```

Tuy nhiên Axiom nên ưu tiên associated `Output` cho những API quen thuộc để giảm generic parameter noise.

---

# 46. Generic constraints không phải subtype

```text
T: Ord
```

không có nghĩa:

```text
T <: Ord
```

Trait là constraint về behavior.

---

# 47. Trait bounds trong type

Ví dụ:

```axiom
struct Boxed<T: Send> {
    value: T
}
```

constraint có thể được lưu tại declaration.

Nhưng solver vẫn phải validate khi instantiate.

---

# 48. Auto traits

Axiom cần compiler-derived properties như:

```text
Copy
Drop
Send
Share
Sized
```

Nhưng không nhất thiết biến tất cả thành user-visible trait declarations.

Có thể có:

```text
AutoProperty
```

nội bộ.

---

# 49. Send derivation

Ví dụ:

```text
struct Pair<T,U> {
    a: T
    b: U
}
```

compiler có thể derive:

```text
Send(Pair<T,U>)
```

nếu:

```text
Send(T)
Send(U)
```

và không có field ngăn Send.

---

# 50. Share derivation

Tương tự:

```text
Share(Pair<T,U>)
```

nếu mọi field thỏa semantic Share contract.

Nhưng compiler không suy ra mutable sharing.

---

# 51. Copy derivation

```text
Copy(struct)
```

nếu toàn bộ semantic fields Copy và không có Drop/resource restriction.

---

# 52. Drop derivation

Struct có field:

```text
File
```

sẽ có:

```text
Drop
```

nếu File là Drop-bearing.

---

# 53. Auto-property solver

Thay vì tạo hàng nghìn impl source-level:

```text
Pair<i32,i32>: Copy
```

compiler có thể query:

```text
derive_auto_property(Copy, Pair<i32,i32>)
```

Điều này giảm metadata và solver workload.

---

# 54. Negative reasoning

Axiom v1 nên **không hỗ trợ arbitrary negative impl reasoning** kiểu:

```text
T: !Trait
```

trong generic user code.

Lý do:

- tăng complexity;
- khó coherence;
- dễ tạo ambiguity;
- khó incremental reasoning.

Compiler vẫn có thể biết một property là `NotProven`.

---

# 55. Unknown không phải NotImplemented

Solver:

```text
NotProven
```

có nghĩa:

> Không thể chứng minh obligation trong context hiện tại.

Không có nghĩa:

> Trait chắc chắn không tồn tại.

---

# 56. Cycle detection

Ví dụ:

```text
T: A
A requires T: B
B requires T: A
```

Solver phải phát hiện cycle.

Không:

```text
infinite recursion
stack overflow
compiler hang
```

---

# 57. Coinductive vs inductive reasoning

Axiom v1 nên dùng **inductive proof semantics** cho ordinary trait obligations.

Cycle không tự động trở thành `Proven`.

Điều này an toàn và deterministic hơn.

---

# 58. Solver depth

Có:

```text
max_trait_depth
max_projection_depth
max_normalization_depth
max_generic_instantiation_depth
```

để bảo vệ compiler.

Vượt giới hạn:

```text
AXTRAIT-DEPTH
```

chứ không ICE.

---

# 59. Memoization

Cache:

```text
GoalKey → SolverResult
```

Key gồm:

```text
TraitRef
Substitution
AssumptionFingerprint
CompilerRevision
```

---

# 60. Canonical goal

Hai goal semantic giống nhau phải canonicalize:

```text
<T as Add<i32>>::Output
```

không khác:

```text
projection generated from equivalent syntax
```

---

# 61. Canonical variables

Solver dùng:

```text
CanonicalGoal {
    bound_type_variables
    bound_const_variables
    goal
}
```

để memoize generic queries độc lập với local TypeVarId.

---

# 62. Query engine

CompilerDB:

```text
solve_trait(goal)
normalize_projection(projection)
resolve_method(receiver, name)
resolve_operator(op, lhs, rhs)
derive_auto_property(property, type)
```

là incremental queries.

---

# 63. Parallel solver

Các obligations độc lập:

```text
T: Send
U: Share
V: Clone
```

có thể solve song song.

Kết quả merge deterministic.

---

# 64. Trait solver không phụ thuộc backend

Không được hỏi:

```text
"x86 có hỗ trợ trait này không?"
```

trong ordinary trait solving.

Target-specific properties đi qua TargetSpec/Gpu legality/etc.

---

# 65. Comptime interaction

Comptime có thể instantiate generic code:

```axiom
comptime {
    ...
}
```

nhưng mọi generated declaration vẫn phải qua:

```text
resolution
type checking
trait solving
ownership
verification
```

---

# 66. Trait solver + comptime

Không cho comptime code tự sửa:

```text
TraitDB
TypeDB
```

Nó chỉ tạo source/HIR/declarations hợp lệ thông qua compiler APIs.

---

# 67. Trait solver + ownership

Trait solver có thể tạo property:

```text
T: Copy
T: Send
T: Share
```

nhưng không quyết định:

```text
local x = Owned
```

Ownership verifier làm việc đó.

---

# 68. Trait solver + capability

Tương tự:

```text
view<T>
mut_view<T>
```

là type-level capability categories.

Solver không theo dõi:

```text
CapabilityId C1 live
```

Verifier đảm nhiệm.

---

# 69. Trait solver + layout

Không resolve:

```text
size_of(T)
```

thành machine size trong generic checking trừ khi compile-time constraint yêu cầu.

LayoutDB xử lý physical layout.

---

# 70. Trait solver + specialization

Axiom v1:

```text
User specialization = restricted / not available
```

Compiler internal specialization được phép nếu:

```text
semantic equivalence proven
```

Ví dụ optimizer có thể inline:

```text
T::add
```

sau khi concrete target được chứng minh.

---

# 71. Generic code generation contract

Trait solver output:

```text
DispatchResolution {
    Static(FunctionId)
    DefaultMethod(FunctionId)
    Dynamic(TraitObjectMethod)
}
```

Backend không phải tự giải trait.

---

# 72. Generic instance graph

Compiler xây:

```text
GenericInstanceGraph
```

Ví dụ:

```text
main
 └── sort<Point>
      ├── compare<Point>
      └── swap<Point>
```

Graph được dùng cho:

- monomorphization;
- code size;
- incremental compilation;
- LTO;
- specialization.

---

# 73. Monomorphization boundary

Trait solver phải hoàn tất:

```text
all required static dispatch
```

trước ABI lowering.

Không để backend tự quyết:

```text
T: Trait
```

---

# 74. Generic code sharing

Compiler có thể phát hiện:

```text
foo<i32>
foo<u32>
```

cùng machine representation/behavior requirements.

Có thể share implementation.

Nhưng semantic identity vẫn khác:

```text
GenericInstanceId ≠ necessarily CodegenInstanceId
```

---

# 75. Trait solver diagnostics

Ví dụ:

```text
cannot satisfy:
    Point: Add<String>

required by:
    expression `point + text`

candidate implementations:
    Point: Add<Point>
    Point: Add<i32>

neither matches String
```

Diagnostics phải chỉ ra:

```text
goal
candidate
failed constraint
source location
```

---

# 76. Ambiguous diagnostic

Ví dụ:

```text
cannot determine implementation of:
    T: Convert<U>

multiple implementations remain possible.

T is not sufficiently constrained.
```

Không tự chọn.

---

# 77. Candidate proof trace

Mỗi solved goal có thể giữ optional:

```text
ProofTrace
```

Ví dụ:

```text
T: Ord
 └── assumption from generic bound
```

hoặc:

```text
Point: Add<Point>
 └── impl #42
```

Tooling/AI có thể truy vấn proof.

---

# 78. AI interface

`ax explain trait` có thể trả:

```text
Goal:
    Point: Add<Point>

Result:
    Proven

Resolution:
    impl Add<Point> for Point

Source:
    package::math::point

Dispatch:
    Static

Generic substitution:
    none
```

AI không được phép sửa semantic result.

---

# 79. Trait solver implementation architecture

Đề xuất:

```text
TraitDB
├── TraitIndex
├── ImplIndex
├── AutoPropertyIndex
├── ProjectionIndex
└── CoherenceIndex

TraitSolver
├── GoalCanonicalizer
├── CandidateCollector
├── Unifier
├── ObligationForest
├── ProjectionNormalizer
├── CycleDetector
├── CoherenceChecker
├── AutoPropertySolver
├── DynCompatibilityChecker
└── MemoTable
```

---

# 80. Obligation Forest

Thay vì recursion thuần:

```text
Goal A
 ├── Goal B
 │    └── Goal C
 └── Goal D
```

dùng:

```text
ObligationForest
```

cho phép:

- parallel solving;
- cycle detection;
- cancellation;
- diagnostics;
- memoization.

---

# 81. Candidate state

```text
CandidateState =
    Applicable
    Failed(Unification)
    Failed(WhereClause)
    Failed(Coherence)
    Ambiguous
```

Không mất lý do failure.

---

# 82. Solver algorithm

Pseudo-logic:

```text
solve(goal):
    canonicalize(goal)

    if cache contains:
        return cache

    if goal is assumption:
        return Proven

    if goal is cycle:
        return Ambiguous / Error
        // depending on cycle category

    candidates = collect(goal)

    for candidate:
        unify(candidate, goal)

        if unification fails:
            discard

        solve candidate obligations

    select:
        0 candidates → NotProven
        1 candidate  → Proven
        >1 equivalent → Proven
        >1 incompatible → Ambiguous
```

---

# 83. Equivalent candidates

Nếu nhiều candidates tồn tại nhưng semantic equivalent theo coherence/specialization rules:

```text
impl candidate A
impl candidate B
```

chỉ được merge nếu language rules chứng minh chúng không tạo hai semantics khác nhau.

Không dùng source order để merge.

---

# 84. Trait solver resource safety

Solver phải có:

```text
time budget
depth budget
memory budget
query cancellation
```

IDE query không được treo compiler vì một generic expression pathological.

---

# 85. Trait solver correctness boundary

Trước khi Typed HIR production:

```text
No unresolved required trait obligations
No ambiguous dispatch
No invalid projection
No coherence violation
No invalid dyn trait
```

---

# 86. Acceptance test — basic trait

```axiom
trait Printable {
    fn print(self)
}

struct User {}

impl Printable for User {
    fn print(self) {}
}
```

Call:

```axiom
let u = User {}
u.print()
```

Expected:

```text
Printable(User)
→ Proven
→ static dispatch
```

---

# 87. Acceptance test — generic

```axiom
fn show<T: Printable>(x: T) {
    x.print()
}
```

Inside body:

```text
T: Printable
```

is an assumption.

Không cần biết T là type nào.

---

# 88. Acceptance test — concrete generic

```axiom
show(User {})
```

Solver:

```text
T → User
User: Printable → Proven
```

---

# 89. Acceptance test — associated type

```axiom
trait Iterator {
    type Item
}

struct Counter {}

impl Iterator for Counter {
    type Item = i32
}
```

Expected:

```text
<Counter as Iterator>::Item
→ i32
```

---

# 90. Acceptance test — operator

```axiom
struct Vec2 {}

impl Add<Vec2> for Vec2 {
    type Output = Vec2
    ...
}
```

Then:

```axiom
let c = a + b
```

Expected:

```text
Add<Vec2, Vec2>
→ Proven
Output = Vec2
```

---

# 91. Acceptance test — ambiguity

Nếu có hai applicable implementations không thể phân biệt:

```text
A
B
```

Expected:

```text
AXTRAIT-AMBIGUOUS
```

---

# 92. Acceptance test — orphan rule

Foreign trait + foreign type:

```text
impl ForeignTrait for ForeignType
```

Expected:

```text
AXTRAIT-ORPHAN
```

---

# 93. Acceptance test — recursive obligation

```text
A<T> requires B<T>
B<T> requires A<T>
```

Expected:

```text
no infinite recursion
deterministic diagnostic/result
```

---

# 94. Acceptance test — Send

```text
struct Pair<T,U> {
    a: T
    b: U
}
```

Nếu:

```text
Send(T)
Send(U)
```

→:

```text
Send(Pair<T,U>)
```

---

# 95. Acceptance test — !Send field

Nếu:

```text
Send(T)
!Send(U)
```

thì:

```text
!Send(Pair<T,U>)
```

---

# 96. Acceptance test — dyn

```axiom
fn use(x: dyn Printable) {}
```

Nếu Printable không dyn-compatible:

```text
AXTRAIT-DYN
```

Không tự heap-box hoặc sửa trait.

---

# 97. Acceptance test — no accidental dispatch

```axiom
fn f<T: Add<T>>(x: T) -> T {
    x + x
}
```

Expected:

```text
trait obligation
static dispatch
```

Không:

```text
runtime reflection
vtable
```

trừ khi source yêu cầu dynamic dispatch.

---

# 98. Acceptance test — method priority

Nếu type có:

```text
inherent foo()
```

và trait cũng có:

```text
foo()
```

method resolution phải chọn inherent method theo frozen priority.

---

# 99. Acceptance test — extension import

Không import extension:

```text
x.foo()
```

không được search arbitrary package.

Có explicit import:

```text
use package::foo
```

→ candidate xuất hiện.

---

# 100. Acceptance test — determinism

Chạy compiler nhiều lần với:

- hash seed khác;
- thread count khác;
- query scheduling khác.

Phải cho cùng:

```text
TraitResult
selected candidate
Typed HIR
diagnostic ordering
```

---

# 101. Invariants

```text
ATRAIT-20
Every trait obligation has a deterministic semantic identity.

ATRAIT-21
Trait solving produces Proven, NotProven, Ambiguous or Error rather than Boolean-only results.

ATRAIT-22
Trait resolution never depends on hash iteration order.

ATRAIT-23
Candidate selection is semantic, not declaration-order based.

ATRAIT-24
A required trait obligation must be proven before production Typed HIR proceeds.

ATRAIT-25
Ambiguous obligations are never silently resolved.

ATRAIT-26
Trait identity is distinct from runtime representation.

ATRAIT-27
Static trait dispatch introduces no mandatory runtime object.

ATRAIT-28
Dynamic dispatch occurs only through explicit dynamic trait semantics.

ATRAIT-29
Associated-type projections are normalized lazily.

ATRAIT-30
Projection normalization cannot bypass type verification.

ATRAIT-31
Generic substitution is immutable and deterministic.

ATRAIT-32
Generic constraints are semantic obligations, not subtype relationships.

ATRAIT-33
Supertrait obligations are derived only from declared supertraits.

ATRAIT-34
Trait inheritance cycles are rejected.

ATRAIT-35
Coherence prevents conflicting implementations within a coherence domain.

ATRAIT-36
Orphan rules prevent uncontrolled foreign-trait/foreign-type implementations.

ATRAIT-37
Blanket implementations are indexed and cannot bypass coherence.

ATRAIT-38
Auto properties such as Copy, Drop, Send and Share are independently derived.

ATRAIT-39
Send and Share remain independent properties.

ATRAIT-40
Trait solving does not determine concrete ownership state.

ATRAIT-41
Trait solving does not determine concrete capability lifetime.

ATRAIT-42
Trait solving does not determine physical layout.

ATRAIT-43
Trait solving is backend-independent except for explicitly target-dependent constraints.

ATRAIT-44
Negative trait reasoning is not general user-level Core v1 functionality.

ATRAIT-45
Unknown or insufficiently constrained information never becomes proof.

ATRAIT-46
Recursive obligation evaluation is cycle-safe.

ATRAIT-47
Solver recursion/resource limits cannot cause compiler crashes.

ATRAIT-48
Trait query results are incrementally cacheable.

ATRAIT-49
Independent obligations may be solved in parallel without changing results.

ATRAIT-50
Every selected dispatch target has a traceable semantic proof.

ATRAIT-51
Generic instance identity is distinct from generated machine-code identity.

ATRAIT-52
Internal compiler specialization cannot change observable semantics.

ATRAIT-53
Generated comptime declarations re-enter normal trait verification.

ATRAIT-54
AI/tooling interfaces may inspect trait proofs but cannot override them.

ATRAIT-55
Trait solver completion is a correctness boundary before MIR lowering.
```

---

# Vị trí của Axiom sau 224

Ta hiện có một pipeline rất rõ:

```text
Source
  ↓
Lexer
  ↓
Lossless Syntax
  ↓
AST
  ↓
Resolution
  ↓
Type System
  ↓
Trait Solver        ← 224
  ↓
Typed HIR
  ↓
MIR
  ↓
Ownership
  ↓
Capability
  ↓
Effects
  ↓
Verified MIR
```

Điểm đáng giá nhất của thiết kế này là **programmer không phải gánh complexity của trait solver**.

Programmer chỉ viết:

```axiom
fn sort<T: Ord>(items: mut_view<T>) {
    ...
}
```

Trong khi compiler âm thầm xử lý:

```text
generic substitution
candidate search
coherence
associated types
auto properties
dispatch
proof caching
cycle detection
parallel solving
```

Đúng với triết lý Axiom:

> **Compiler Complexity Is Not Language Complexity.**

---

# BOOTSTRAP-225 — HIR → MIR SEMANTIC LOWERING

Bước tiếp theo là biến Typed HIR thành **MIR có semantics hoàn chỉnh**, trước khi ownership/capability verifier can thiệp.

225 sẽ khóa:

```text
HIR → MIR lowering
Place
Projection
Operand
RValue
Statement
Terminator
BasicBlock
Control Flow
Evaluation Order
Temporary
Desugaring
Method Call
Operator Call
Pattern Binding
Match
Loop
Closure
Async
Comptime
Drop Candidates
Capability Creation
Move/Copy classification
Return
Panic
? propagation
Short-circuit
Indexing
Slicing
```

Đây sẽ là **semantic execution model trung tâm của Axiom**: sau 225, mọi chương trình Core đều phải có một MIR representation có thể chạy được bằng `ax-mir`, trước khi optimizer hay native backend được phép đụng vào.