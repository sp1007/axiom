# BOOTSTRAP-240 — AXIOM TRAIT SYSTEM, TRAIT SOLVER & GENERIC CONSTRAINT ENGINE

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của tầng này:

> **Trait là contract về capability/behavior; generic là compile-time abstraction; Trait Solver là bộ máy chứng minh các constraint đó.**

Axiom không dùng inheritance để biểu diễn quan hệ giữa type.

---

# 1. Kiến trúc tổng thể

```text
Generic Definition
       │
       ▼
Generic Parameters
       │
       ▼
Trait Bounds / Constraints
       │
       ▼
Trait Goals
       │
       ▼
Trait Solver
       │
 ┌─────┼─────────────┐
 ▼     ▼             ▼
Proven NotProven  Ambiguous
       │
       ▼
Typed HIR / MIR
```

Trait Solver **không được trở thành type checker thứ hai**.

Nó chỉ giải quyết các proposition liên quan đến traits, implementations và associated items.

---

# 2. Trait là behavior contract

Ví dụ:

```axiom
trait Display {
    fn display(self: view<Self>) -> Str
}
```

Trait nói:

```text
Type T có behavior Display
```

Không nói:

```text
T kế thừa từ Display
T có object header
T có vtable
T có base class
```

---

# 3. Một type có thể implement nhiều trait

```axiom
struct User {
    id: u64
}

impl Display for User { ... }
impl Clone for User { ... }
impl Send for User { ... }
```

Không có giới hạn kiểu single inheritance.

---

# 4. Trait không chứa state

Trait Core v1 mô tả:

```text
functions
associated types
associated constants
constraints
```

Không chứa instance fields.

State thuộc struct/enum.

---

# 5. Associated function

```axiom
trait Factory {
    fn create() -> Self
}
```

Không có receiver.

Đây là associated function.

---

# 6. Associated constant

```axiom
trait Limits {
    const MAX: usize
}
```

Semantic identity:

```text
AssociatedConstId
```

không phải ordinary module constant.

---

# 7. Associated type

```axiom
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self::Item>
}
```

`Item` là associated type.

---

# 8. `Self`

Trong trait:

```text
Self
```

là implicit type parameter đại diện cho implementing type.

Ví dụ:

```axiom
impl Iterator for IntIterator {
    type Item = i32
}
```

suy ra:

```text
Self = IntIterator
Self::Item = i32
```

---

# 9. Trait implementation

```axiom
impl Display for User {
    fn display(self: view<User>) -> Str {
        ...
    }
}
```

Compiler tạo:

```text
ImplId
```

với:

```text
TraitId
SelfType
GenericParameters
WhereConstraints
AssociatedItems
```

---

# 10. Generic implementation

```axiom
impl<T: Display> Display for Box<T> {
    ...
}
```

Đây là conditional implementation.

Solver phải chứng minh:

```text
T: Display
```

trước khi impl áp dụng.

---

# 11. Trait goal

Solver nhận goal:

```text
T: Display
```

internal form:

```text
TraitGoal {
    Type: T
    Trait: Display
}
```

---

# 12. Solver result

Chuẩn:

```text
Proven
NotProven
Ambiguous
Error
```

Không dùng Boolean đơn giản.

`Ambiguous` rất quan trọng trong generic compilation.

---

# 13. Candidate discovery

Ví dụ:

```text
T: Display
```

solver tìm:

```text
impl Display for i32
impl Display for String
impl<T: Display> Display for Box<T>
...
```

Candidate set phải được xác định deterministic.

---

# 14. Không quét toàn bộ thế giới

Solver không được:

```text
scan every package
scan every declaration
```

mỗi lần gặp trait goal.

Compiler duy trì indexed implementation database:

```text
TraitId
    ↓
ImplIndex
    ↓
Candidate ImplIds
```

---

# 15. Impl index

Ví dụ:

```text
Display
 ├── i32
 ├── f32
 ├── String
 ├── User
 └── Box<T>
```

Index có thể thêm key theo Self type head:

```text
(Display, i32)
(Display, String)
(Display, Box)
```

giảm candidate search cực mạnh.

---

# 16. Generic head

Với:

```axiom
impl<T> Display for Box<T>
```

head là:

```text
Box<_>
```

Solver dùng type constructor để index.

---

# 17. Unification của impl

Goal:

```text
Box<i32>: Display
```

candidate:

```text
impl<T> Display for Box<T>
```

unify:

```text
T = i32
```

sau đó solve remaining constraints.

---

# 18. Conditional implementation

```axiom
impl<T: Display> Display for Box<T>
```

Goal:

```text
Box<User>: Display
```

Solver:

```text
unify T = User
 ↓
solve User: Display
 ↓
Proven
```

---

# 19. Recursion

Ví dụ:

```text
Box<T>: Display
requires T: Display
```

solver gặp:

```text
Box<Box<User>>: Display
```

sẽ recursively solve:

```text
Box<User>: Display
User: Display
```

---

# 20. Cycle detection

Nếu:

```text
A: TraitX
requires B: TraitY

B: TraitY
requires A: TraitX
```

solver phải detect cycle.

Không recurse vô hạn.

---

# 21. Recursive goal state

Internal:

```text
GoalState:
    Unseen
    Evaluating
    Proven
    NotProven
    Ambiguous
    Error
```

`Evaluating → same goal` tạo cycle.

Solver áp dụng well-founded rule hoặc fixed-point semantics phù hợp với loại predicate.

---

# 22. Không suy luận cycle thành True

Đây là nguyên tắc an toàn:

```text
cycle
≠
Proven
```

Nếu solver không chứng minh được:

```text
NotProven
```

hoặc `Ambiguous` tùy semantic context.

Không bao giờ:

```text
unknown → true
```

---

# 23. Coherence

Một program không được có hai impl mâu thuẫn:

```axiom
impl Display for User {}
impl Display for User {}
```

→ error.

---

# 24. Orphan rule

Để giữ semantic ổn định:

Một package chỉ được define implementation khi có ownership hợp lệ đối với ít nhất một phía của:

```text
Trait
Type
```

Ví dụ conceptually:

```text
local trait + foreign type       allowed
foreign trait + local type      allowed
foreign trait + foreign type    forbidden
```

trừ các compiler/library mechanisms đặc biệt.

---

# 25. Vì sao cần orphan rule?

Nếu mọi package đều có thể viết:

```text
impl Display for String
```

thì:

```text
Package A → Display(String)
Package B → Display(String)
```

có thể tạo hai semantic universe khác nhau.

Orphan rule ngăn điều đó.

---

# 26. Coherence trước optimization

Trait selection phải hoàn tất trước:

```text
inlining
specialization
devirtualization
LTO
```

Optimizer không được quyết định trait implementation.

---

# 27. Trait selection deterministic

Candidate ordering không dựa trên:

```text
source order
file order
hash order
import order
build machine
parallel execution order
```

Phải dựa trên semantic specificity/coherence rules.

---

# 28. Specialization

Axiom không nên cho arbitrary specialization v1.

Ví dụ Rust-style:

```text
impl<T> Trait for T
impl Trait for i32
```

có thể tạo overlap.

Nếu không có explicit specialization model:

```text
ambiguous/overlap
```

→ reject.

---

# 29. Constrained specialization

Nếu sau này hỗ trợ specialization:

```text
general impl
    ↓
more specific impl
```

phải có partial-order rule rõ ràng.

Không dựa vào declaration order.

---

# 30. Associated type projection

Ví dụ:

```axiom
fn first<I: Iterator>(x: I) -> I::Item
```

`I::Item` là projection.

Internal:

```text
ProjectionType {
    Base = I
    Associated = Item
}
```

---

# 31. Projection normalization

Nếu:

```axiom
impl Iterator for Numbers {
    type Item = i32
}
```

thì:

```text
Numbers::Item
```

normalize:

```text
i32
```

---

# 32. Projection ambiguity

Nếu compiler chưa biết concrete `I`:

```text
I::Item
```

không được tự chọn.

Nó giữ projection symbolic.

Khi context đủ mạnh, solver normalize.

---

# 33. Projection equality

Goal:

```text
I::Item = i32
```

là type-system constraint.

Solver phải tìm impl phù hợp hoặc giữ unresolved.

---

# 34. Associated constants

Tương tự:

```text
I::MAX
```

resolve:

```text
AssociatedConstId
```

sau đó instantiate implementation.

---

# 35. Associated functions

```text
T::create()
```

có thể require trait context.

Resolver tìm candidate associated item.

Trait solver xác nhận implementation.

---

# 36. Supertraits

Axiom có thể hỗ trợ:

```axiom
trait Ordered: Equatable {
    fn compare(...)
}
```

Ý nghĩa:

```text
T: Ordered
⇒
T: Equatable
```

Đây là logical implication.

Không phải inheritance.

---

# 37. Supertrait graph

```text
Ordered
   │
   ▼
Equatable
   │
   ▼
...
```

Graph phải acyclic về semantic expansion hoặc solver phải xử lý cycle.

Khuyến nghị:

> Supertrait cycles bị cấm.

---

# 38. Trait default method

```axiom
trait Printable {
    fn print(self: view<Self>) {
        ...
    }
}
```

Impl có thể không override.

Concrete implementation dùng default.

---

# 39. Override không cần keyword

```axiom
impl Printable for User {
    fn print(self: view<User>) {
        ...
    }
}
```

Tự động thay thế default implementation.

Không cần:

```text
override
```

vì compiler biết trait context.

---

# 40. Signature compatibility

Override phải khớp trait contract.

Không được thay đổi:

```text
parameter semantics
return type
required capabilities
effect obligations
ABI contract
```

trừ variance/adapter rules được định nghĩa rõ.

---

# 41. Trait method effects

Trait có thể yêu cầu effect:

```text
Display::display
    Read
```

Implementation không được vi phạm contract.

Ví dụ trait yêu cầu pure nhưng implementation thực hiện IO:

```text
invalid
```

---

# 42. Generic trait

```axiom
trait Converter<T> {
    fn convert(...)
}
```

Nếu cho phép generic trait, TraitId cần generic parameters.

Nhưng cần tránh ambiguity.

Khuyến nghị hỗ trợ generic traits trong v1.

---

# 43. Trait identity

```text
TraitId
```

được xác định bởi declaration identity.

Không phải:

```text
trait name string
```

Hai package có:

```text
A::Display
B::Display
```

là hai trait khác nhau.

---

# 44. Trait aliases

Core v1 **không cần trait alias**.

Có thể xây dựng bằng:

```text
trait Printable: Display + Debug {}
```

nếu semantic nhu cầu đủ.

Giảm thêm một construct.

---

# 45. Generic where clauses

Syntax:

```axiom
fn foo<T, U>(x: T, y: U)
where
    T: Display
    U: Clone
```

Semantic:

```text
Goal(T: Display)
Goal(U: Clone)
```

---

# 46. Constraint normalization

Solver canonicalize:

```text
T: A
U: B
T: A
```

thành:

```text
T: A
U: B
```

duplicate constraints không tạo work lặp lại.

---

# 47. Generic environment

Mỗi generic definition có:

```text
GenericEnvironment {
    TypeParameters
    ConstParameters
    TraitBounds
    EqualityConstraints
}
```

Ví dụ:

```text
T: Iterator
T::Item: Clone
N > 0
```

---

# 48. Generic parameter dependencies

Constraints có thể phụ thuộc:

```text
T: Iterator
T::Item: Clone
```

Solver phải giải theo dependency graph.

---

# 49. Const generic constraints

Ví dụ:

```axiom
fn sum<const N: usize>(x: [N]i32)
```

Type system biết:

```text
N : usize
```

Nhưng Core v1 không cần theorem prover tổng quát.

---

# 50. Const expression constraints

Cho phép một tập hữu hạn expression compile-time:

```text
N + 1
N * 2
```

nếu compiler có canonical const evaluator.

Không hỗ trợ:

```text
arbitrary symbolic mathematics
```

trong type system.

---

# 51. Type-level arithmetic

Không biến Axiom thành dependent type language.

Mục tiêu:

```text
const generic
+
compile-time evaluator
+
bounded type-level facts
```

là đủ cho:

```text
arrays
SIMD widths
tensor dimensions
buffer sizes
```

---

# 52. Trait auto properties

Các properties:

```text
Copy
Drop
Send
Share
Sized
FfiSafe
GpuLegal
```

được solver/compiler derive theo rule.

Không phải tất cả đều ordinary user traits.

---

# 53. Auto trait

Có thể có compiler-known auto properties:

```text
IsSend<T>
IsShare<T>
IsCopy<T>
```

được tính structural.

Ví dụ:

```text
struct Pair<T, U> {
    a: T
    b: U
}
```

`Pair<T,U>: Send` nếu:

```text
T: Send
U: Send
```

---

# 54. Không cho user tùy tiện fake auto properties

Không nên cho:

```text
unsafe impl Send for T
```

trong Core.

Unsafe abstraction phải đi qua compiler-defined trusted boundary.

Nếu không, memory/concurrency guarantees mất ý nghĩa.

---

# 55. Trait object

```text
dyn Trait
```

được phép nếu Trait object-safe.

Trait solver xác định:

```text
ConcreteType implements Trait
```

Runtime representation do ABI layer.

---

# 56. Dynamic dispatch không mặc định

```axiom
fn render(x: dyn Renderable)
```

là explicit.

Generic:

```axiom
fn render<T: Renderable>(x: T)
```

là static dispatch mặc định.

---

# 57. Static vs dynamic

```text
T: Trait
    ↓
compile-time candidate
    ↓
static dispatch
```

trong khi:

```text
dyn Trait
    ↓
runtime dispatch
```

Không tự chuyển static thành dynamic vì tiện codegen.

---

# 58. Trait upcasting

Nếu:

```axiom
trait Animal {}
trait Dog: Animal {}
```

có:

```text
dyn Dog
```

→

```text
dyn Animal
```

chỉ khi compiler chứng minh upcast contract.

Explicit hoặc coercion được whitelist.

---

# 59. Downcast

```text
dyn Trait → ConcreteType
```

không implicit safe.

Nếu runtime metadata được bật và Trait cung cấp contract thích hợp, library API có thể thực hiện checked downcast.

---

# 60. Trait solver và method resolution

Resolver phát hiện:

```text
candidate method
```

Trait solver xác định:

```text
candidate applicable?
```

Sau đó type checker chọn final callable.

Không để resolver tự giả định implementation.

---

# 61. Candidate specificity

Ví dụ:

```text
impl<T> Trait for Box<T>
impl Trait for Box<i32>
```

Nếu specialization được bật, `Box<i32>` phải chọn specific impl.

Nếu specialization chưa được bật:

```text
overlap
```

→ compile error.

---

# 62. Solver architecture

Đề xuất:

```text
TraitSolver
├── GoalCanonicalizer
├── ImplIndex
├── CandidateSelector
├── Unifier
├── ProjectionNormalizer
├── CycleDetector
├── CoherenceChecker
├── SpecializationChecker
├── GoalCache
└── DiagnosticBuilder
```

---

# 63. Canonical goals

Ví dụ:

```text
T: Display
```

không cache bằng raw TypeVar ID vì ID khác nhau giữa inference contexts.

Canonicalize:

```text
?0: Display
```

rồi cache.

---

# 64. Solver cache

Key:

```text
CanonicalGoal
+
EnvironmentFingerprint
+
CompilerSemanticVersion
```

Result:

```text
Proven / NotProven / Ambiguous / Error
```

---

# 65. Environment fingerprint

Solver result phụ thuộc:

```text
trait definitions
impl set
generic environment
feature configuration
target-relevant constraints where applicable
```

Thay đổi những thứ này phải invalidate cache.

---

# 66. Incremental solver

Nếu thêm một function implementation không liên quan:

```text
impl UnrelatedTrait for OtherType
```

không được invalidate mọi trait goals.

Impl index dependency graph giúp giới hạn invalidation.

---

# 67. Parallel solver

Independent goals:

```text
T: Display
U: Clone
V: Send
```

có thể solve parallel.

Kết quả phải deterministic.

---

# 68. Solver fuel/depth limit

Compiler cần giới hạn:

```text
maximum recursion depth
maximum candidate expansion
maximum normalization steps
```

để source code pathological không làm compiler recurse vô hạn.

Nhưng giới hạn này chỉ là compiler-resource safeguard.

Không biến semantic result thành random.

---

# 69. Overflow của solver

Nếu vượt resource limit:

```text
TraitResolutionOverflow
```

không được trả:

```text
Proven
```

Có thể trả compiler diagnostic yêu cầu giảm constraint complexity hoặc tăng compiler limit.

---

# 70. Ambiguous vs overflow

```text
Ambiguous
```

= semantics chưa xác định.

```text
Overflow
```

= compiler không hoàn tất được proof trong resource budget.

Hai trạng thái phải khác nhau.

---

# 71. Negative reasoning

Core v1 không nên hỗ trợ:

```text
T: !Trait
```

một cách tổng quát.

Negative impl có thể cực kỳ phức tạp cho solver/coherence.

Khuyến nghị:

> Không có general negative trait bounds trong Core v1.

---

# 72. Nhưng compiler vẫn cần negative facts nội bộ

Ví dụ:

```text
IsCopy<T> = false
```

có thể là compiler fact do `Drop`.

Đây không phải user-facing negative trait system.

---

# 73. Trait specialization v1

Khuyến nghị frozen:

```text
No unrestricted specialization
No negative bounds
No arbitrary overlapping impl
```

để solver nhỏ, predictable.

---

# 74. Generic API vẫn rất mạnh

Ví dụ:

```axiom
fn sort<T: Ord>(items: mut_view<T>) { ... }

fn map<T, U, F>(
    items: view<T>,
    f: F
) -> Vec<U>
where
    F: Fn(T) -> U
{
    ...
}
```

Đủ để xây:

```text
collections
iterators
algorithms
numeric
tensor
GUI
networking
```

mà không cần inheritance.

---

# 75. Trait composition

```axiom
fn process<T>(x: T)
where
    T: Display + Clone + Send
```

semantic:

```text
T: Display
T: Clone
T: Send
```

Ba goals độc lập.

---

# 76. Trait bounds không tạo runtime cost

Generic constraint:

```text
T: Display
```

không tự tạo:

```text
vtable
runtime check
object header
```

Static dispatch mặc định.

---

# 77. Zero-cost abstraction

Ví dụ:

```axiom
fn sum<T: Numeric>(items: view<T>) -> T
```

có thể compile thành machine code tương đương specialized loop.

Trait abstraction biến mất nếu không observable.

---

# 78. Dynamic dispatch cost explicit

Nếu programmer chọn:

```text
dyn Numeric
```

thì runtime dispatch representation là observable implementation cost.

Không được compiler “giả vờ” đó là static dispatch nếu runtime semantics yêu cầu dynamic identity.

---

# 79. Trait solver không phụ thuộc optimizer

Solver phải hoàn thành trước:

```text
inlining
constant folding
LTO
PGO
vectorization
```

Do đó:

```text
optimization level
```

không thể thay đổi trait meaning.

---

# 80. Diagnostic của trait failure

Thay vì:

```text
trait bound not satisfied
```

Axiom nên cung cấp proof tree:

```text
Required:
    User: Serializable

Candidates:
    Serializable for NetworkPacket
    Serializable for FileHeader

No implementation:
    Serializable for User

Possible required bound:
    User: WireSafe
```

---

# 81. Diagnostic proof tree

Internal:

```text
Goal User: Serializable
 ├── Candidate #1 rejected
 │      Self mismatch
 │
 ├── Candidate #2 rejected
 │      Self mismatch
 │
 └── No applicable implementation
```

AI IDE có thể consume trực tiếp.

---

# 82. Solver explain API

```text
ax explain trait User: Serializable
```

có thể trả:

```text
goal
candidate set
selected impl
subgoals
normalizations
coherence facts
confidence/state
```

Không phải AI tự tái tạo reasoning từ source.

---

# 83. Formal semantics

Trait semantics có thể biểu diễn:

```text
Implemented(T, Trait)
```

và rule:

```text
Impl:
    T matches Self
    all where-goals proven
--------------------------------
    Implemented(T, Trait)
```

Default method selection không thay đổi proposition `Implemented`.

---

# 84. Core logical model

Các predicate chính:

```text
SameType(A, B)

WellFormed(T)

Implements(T, Trait)

Normalize(Projection) = Type

Compatible(A, B)

Coercible(A, B)

HasAssociatedType(T, Trait, Name)

HasAssociatedConst(...)
```

Đây là nền tảng cho formal specification.

---

# 85. Type system ↔ Trait solver

```text
TypeDB
   │
   ├── Type equality
   ├── Generic substitution
   ├── Normalization
   │
   ▼
TraitSolver
   │
   ├── Implements
   ├── Associated types
   ├── Associated constants
   └── Method applicability
```

Không tạo vòng dependency không kiểm soát.

---

# 86. Trait solver ↔ Ownership

Ví dụ:

```text
T: Send
```

Trait solver có thể cung cấp fact.

Nhưng ownership/concurrency verifier vẫn kiểm tra actual value flow.

Không thể chỉ vì:

```text
T: Send
```

mà bỏ qua:

```text
move
capability
lifetime
```

---

# 87. Trait solver ↔ GPU

```text
T: GpuLegal
```

có thể được compiler derive.

Nhưng kernel verifier vẫn kiểm tra:

```text
address space
execution domain
synchronization
capability
```

---

# 88. Trait solver ↔ FFI

```text
T: FfiSafe<C>
```

là semantic property.

ABI layer vẫn quyết định:

```text
layout
calling convention
symbol
```

---

# 89. Trait solver ↔ comptime

Generic/comptime:

```axiom
comptime fn make<T: Default>() -> T
```

solver chứng minh `T: Default`.

Comptime evaluator không tự tạo một trait system khác.

---

# 90. Trait Solver Complexity Budget

Đây là một quyết định quan trọng.

Axiom **không** theo hướng:

```text
full dependent types
+
higher-kinded types
+
arbitrary negative reasoning
+
unrestricted specialization
+
general theorem proving
```

trong Core v1.

Thay vào đó:

```text
Nominal Types
+
Generics
+
Traits
+
Associated Types
+
Associated Const
+
Const Generics
+
Deterministic Constraint Solver
```

đủ mạnh cho mục tiêu systems language.

---

# 91. Trait system sau 240

Axiom hiện có:

```text
                TYPE
                  │
        ┌─────────┴──────────┐
        │                    │
     Generic               Trait
        │                    │
        └───────┬────────────┘
                ▼
          Constraint Graph
                │
                ▼
          Trait Solver
                │
       ┌────────┼────────┐
       ▼        ▼        ▼
    Proven   Ambiguous  Failed
       │
       ▼
    Typed HIR
```

Đây là nền tảng đủ mạnh để xây **Iterator, Collections, Numeric, Tensor, GUI, Network, FFI...** mà không cần class hierarchy.

---

# 92. Invariants đóng băng

```text
ATRAIT-20
Traits define behavior contracts, not inheritance.

ATRAIT-21
Traits do not implicitly introduce object headers or runtime dispatch.

ATRAIT-22
A type may implement multiple traits.

ATRAIT-23
Every trait has stable semantic identity.

ATRAIT-24
Every implementation has stable ImplId identity.

ATRAIT-25
Trait goals have explicit semantic states.

ATRAIT-26
Ambiguous trait goals are never treated as proven.

ATRAIT-27
Trait candidate discovery is deterministic.

ATRAIT-28
Trait candidate discovery uses indexed semantic data, not arbitrary global scanning.

ATRAIT-29
Trait selection does not depend on source/import order.

ATRAIT-30
Coherence prevents conflicting implementations.

ATRAIT-31
Orphan rules constrain foreign trait/foreign type implementations.

ATRAIT-32
Generic implementations may impose explicit trait constraints.

ATRAIT-33
Conditional implementations are selected only after their constraints are proven.

ATRAIT-34
Trait recursion must terminate or produce an explicit solver state.

ATRAIT-35
Trait cycles are never implicitly considered proven.

ATRAIT-36
Associated types are first-class semantic projections.

ATRAIT-37
Associated type normalization is deterministic.

ATRAIT-38
Associated constants have semantic identity distinct from ordinary constants.

ATRAIT-39
Associated functions have semantic identity distinct from ordinary module functions.

ATRAIT-40
Self is an explicit semantic type parameter within trait contexts.

ATRAIT-41
Supertraits represent logical constraints, not object inheritance.

ATRAIT-42
Supertrait cycles are forbidden in Core v1.

ATRAIT-43
Default trait methods may be replaced by concrete implementations without an override keyword.

ATRAIT-44
Trait implementation signatures must satisfy the trait contract.

ATRAIT-45
Trait effects are checked as semantic callable obligations.

ATRAIT-46
Generic constraints are compile-time obligations by default.

ATRAIT-47
Static generic dispatch is the default.

ATRAIT-48
Dynamic dispatch requires explicit dyn Trait semantics.

ATRAIT-49
Trait objects require object-safe traits.

ATRAIT-50
Trait upcasting is permitted only through defined semantic rules.

ATRAIT-51
Implicit safe downcasting is forbidden.

ATRAIT-52
Unrestricted specialization is forbidden in Core v1.

ATRAIT-53
Arbitrary overlapping implementations are forbidden.

ATRAIT-54
General negative trait bounds are forbidden in Core v1.

ATRAIT-55
Compiler-known negative facts do not constitute a user-facing negative trait system.

ATRAIT-56
Auto properties such as Send, Share, Copy and Drop are derived by semantic rules.

ATRAIT-57
User code cannot arbitrarily assert safety-critical auto properties.

ATRAIT-58
Trait solving is independent of optimization level.

ATRAIT-59
Trait solving is independent of machine representation.

ATRAIT-60
Trait solving is independent of storage allocation strategy.

ATRAIT-61
Trait solving does not perform ownership verification.

ATRAIT-62
Trait solving does not perform capability verification.

ATRAIT-63
Trait solving does not perform ABI lowering.

ATRAIT-64
Trait goals are canonicalizable.

ATRAIT-65
Trait solver results are incrementally cacheable.

ATRAIT-66
Trait caches are invalidated by semantic dependency changes.

ATRAIT-67
Independent trait goals may be solved in parallel deterministically.

ATRAIT-68
Solver resource exhaustion is distinct from semantic ambiguity.

ATRAIT-69
Solver resource exhaustion cannot produce a false Proven result.

ATRAIT-70
Trait diagnostics preserve candidate and constraint provenance.

ATRAIT-71
Trait proof trees are inspectable by compiler tooling.

ATRAIT-72
AI systems cannot select or override trait implementations.

ATRAIT-73
Generated code must pass the same trait solver.

ATRAIT-74
Comptime code uses the same trait semantics.

ATRAIT-75
GPU legality uses the same trait/type foundations.

ATRAIT-76
FFI safety properties use the same trait/type foundations.

ATRAIT-77
Generic abstraction may be completely erased after semantic verification.

ATRAIT-78
Runtime overhead is never introduced merely because a static trait bound exists.

ATRAIT-79
Dynamic dispatch overhead is explicit and semantically observable.

ATRAIT-80
Trait resolution completes before production code generation.

ATRAIT-81
No unresolved trait goal may enter Verified MIR.

ATRAIT-82
Partial semantic trait results cannot establish production correctness.

ATRAIT-83
Trait semantics are defined independently of compiler implementation details.

ATRAIT-84
The trait solver is deterministic across parallel and incremental compilation.

ATRAIT-85
Trait implementation meaning is stable under unrelated declaration reordering.
```

---

# TASK TIẾP THEO

## **BOOTSTRAP-241 — AXIOM TYPE INFERENCE, CONSTRAINT SOLVING & EXPRESSION TYPING**

239 đã định nghĩa **Type System**, 240 định nghĩa **Trait Solver**. Bước tiếp theo cần đi sâu vào thứ thực sự biến expression thành Typed HIR:

```text
literal
variable
call
method call
field
index
array
tuple
struct literal
enum constructor
closure
if
match
loop
async/await
cast
?
operator
generic invocation
```

và pipeline:

```text
Expression
   ↓
Expected Type
   ↓
Inference Variables
   ↓
Constraints
   ↓
Unification
   ↓
Coercion
   ↓
Trait Goals
   ↓
Normalization
   ↓
Solved Type
   ↓
Typed HIR
```

Đặc biệt 241 sẽ đóng băng **bidirectional type checking + expression inference**, để từ đây chúng ta có thể chuyển sang các tầng semantic sâu hơn mà compiler thực sự có thể triển khai.