# AXIOM TRAIT SOLVER + METHOD RESOLUTION v0.1

Đây là phần cần thiết kế rất cẩn thận. Nếu trait system quá mạnh, Axiom sẽ mất ưu điểm **đơn giản + compile nhanh + diagnostics rõ ràng**.

Mục tiêu của Axiom:

> Trait là cơ chế mô tả capability/behavior và ràng buộc compile-time, **không phải một ngôn ngữ logic tổng quát**.

---

# 1. Trait model

Ví dụ:

```axiom
trait Ord {
    fn compare(self: view<Self>, other: view<Self>) -> i32
}
```

Một type có thể implement:

```axiom
impl Ord for User {
    fn compare(...) -> i32 {
        ...
    }
}
```

Trait system phải trả lời:

```text
Does Type T satisfy Trait Ord?
```

và:

```text
Which implementation applies?
```

---

# 2. Trait obligation

Khi compiler gặp:

```axiom
fn max<T: Ord>(a: T, b: T) -> T {
    ...
}
```

nó tạo constraint:

```text
T : Ord
```

Đây gọi là:

```text
TraitObligation
```

Không resolve ngay nếu `T` vẫn là inference variable.

---

# 3. Solver states

Solver chỉ có bốn kết quả chính:

```text
PROVEN
DISPROVEN
AMBIGUOUS
OVERFLOW
```

Không có:

```text
UNKNOWN_FOREVER
MAGIC
TRY_RANDOMLY
```

---

# 4. PROVEN

Ví dụ:

```axiom
struct User {}

impl Display for User {}
```

Compiler hỏi:

```text
User : Display ?
```

→

```text
PROVEN
```

---

# 5. DISPROVEN

```axiom
struct User {}
```

không có:

```text
impl Ord for User
```

Compiler hỏi:

```text
User : Ord ?
```

→

```text
DISPROVEN
```

---

# 6. AMBIGUOUS

Ví dụ:

```text
T : Ord
```

nhưng `T` vẫn chưa biết là type nào.

Solver không được đoán.

→

```text
AMBIGUOUS
```

Sau khi inference biết:

```text
T = i32
```

solver chạy lại.

---

# 7. OVERFLOW

Trait recursion:

```axiom
trait A<T> {}
trait B<T> : A<T> {}
trait C<T> : B<T> {}
```

Nếu dependency graph hoặc associated type normalization tạo chuỗi vô hạn, solver phải dừng.

→

```text
OVERFLOW
```

Không được làm compiler treo.

---

# 8. Trait implementation identity

Mỗi impl có:

```text
ImplId
TraitId
SelfType
GenericParams
WhereClauses
Methods
AssociatedTypes
```

Ví dụ:

```axiom
impl<T: Ord> Foo<T> for Bar<T>
```

semantic:

```text
ImplId(42)

Trait = Foo<T>
Self  = Bar<T>

constraint:
T : Ord
```

---

# 9. Coherence

Axiom đã khóa:

> Một `impl Trait for Type` chỉ hợp lệ nếu **Trait hoặc Type thuộc package hiện tại**.

Ví dụ package A:

```axiom
trait Serialize {}
```

Package B:

```axiom
struct User {}
```

Package C không được:

```axiom
impl Serialize for User {}
```

nếu cả `Serialize` và `User` đều foreign.

---

# 10. Tại sao cần coherence?

Nếu không:

```text
Package A:
impl Display for User

Package B:
impl Display for User
```

thì chương trình phụ thuộc cả A và B không biết implementation nào đúng.

Axiom không dùng:

```text
last import wins
```

hay:

```text
dependency order wins
```

Mà compile error.

---

# 11. Không có user specialization v0.1

Không cho:

```axiom
impl<T> Foo for T {}
impl Foo for i32 {}
```

với ý nghĩa implementation thứ hai override implementation thứ nhất.

Điều này tránh:

```text
generic impl selection
→ specialization ranking
→ overlap analysis
→ priority
```

rất phức tạp.

Compiler có thể tự tối ưu specialization bên trong.

Nhưng:

> **Specialization không được observable trong source semantics.**

---

# 12. Blanket implementation

Có thể hỗ trợ:

```axiom
impl<T: Copy> Clone for T {
    ...
}
```

nhưng phải chịu coherence + overlap rules.

Ví dụ:

```axiom
impl<T: Copy> Clone for T {}
impl Clone for User {}
```

Nếu `User: Copy`, hai impl cùng match.

→ **compile error**.

Không có specialization.

---

# 13. Solver không backtrack vô hạn

Không làm kiểu:

```text
try impl A
  fail
try impl B
  fail
try impl C
...
```

không giới hạn.

Solver có:

```text
SolverBudget {
    max_steps
    max_depth
    max_normalization
}
```

---

# 14. Deterministic solver

Cùng source:

```text
compiler version
target
semantic configuration
```

→ cùng kết quả solver.

Không phụ thuộc:

- HashMap iteration order
- thread scheduling
- optimization level.

---

# 15. Trait goal

Internal representation:

```text
TraitGoal {
    trait_id: TraitId
    self_type: TypeId
    args: [TypeId]
}
```

Ví dụ:

```text
Ord<i32>
```

conceptual:

```text
TraitGoal {
    trait = Ord
    self = i32
}
```

---

# 16. Candidate impl

Solver lấy tất cả impl có thể match:

```text
Goal:
Display<User>

Candidates:
Impl #1 Display for User
Impl #2 Display for T where T: Debug
...
```

Sau đó:

1. applicability
2. substitution
3. where constraints
4. coherence/overlap guarantees
5. determine unique result

---

# 17. Không dùng runtime dispatch để giải trait

Nếu:

```axiom
fn print<T: Display>(x: T)
```

thì trait resolution compile-time.

Không tạo vtable.

Compiler có thể inline:

```text
print<User>
```

thành implementation cụ thể.

---

# 18. `dyn Trait`

Nếu programmer muốn runtime dispatch:

```axiom
fn print(x: dyn Display)
```

thì đây là semantic request rõ ràng.

Trait solver không biến static trait thành dynamic trait.

---

# 19. Static vs dynamic

```text
T: Display
```

→ static constraint.

```text
dyn Display
```

→ dynamic dispatch representation.

Không có implicit transition:

```text
T
↓
dyn Trait
```

trừ khi language-defined conversion tại boundary được thiết kế rõ ràng.

---

# 20. Associated type

Ví dụ:

```axiom
trait Iterator {
    type Item
}
```

và:

```axiom
impl Iterator for Numbers {
    type Item = i32
}
```

Goal:

```text
Iterator<Numbers>::Item
```

phải normalize thành:

```text
i32
```

---

# 21. Associated type normalization

Internal:

```text
Normalize(
    Projection {
        trait = Iterator
        self = Numbers
        assoc = Item
    }
)
```

→ `i32`.

Nếu chưa biết:

```text
AMBIGUOUS
```

Nếu không có implementation:

```text
DISPROVEN
```

---

# 22. Associated type không phải runtime value

`Item`:

```text
type Item
```

là compile-time type relation.

Không tạo runtime metadata.

---

# 23. Associated function

```axiom
trait From<T> {
    fn from(x: T) -> Self
}
```

`Self` là type hiện tại của impl.

Ví dụ:

```axiom
impl From<i32> for UserId
```

thì:

```text
From<i32>::from
```

trả:

```text
UserId
```

---

# 24. Method resolution

Đây là phần programmer trực tiếp cảm nhận.

Ví dụ:

```axiom
x.length()
```

Resolver đã xác định `x`.

Type checker biết:

```text
type(x) = Vec2
```

Method resolver tìm theo thứ tự:

```text
1. inherent methods
2. directly applicable trait methods
3. explicitly imported extension methods
4. generic extension methods
```

Đây là thứ tự đã định trước.

---

# 25. Inherent method

```axiom
impl Vec2 {
    fn length(self: view<Self>) -> f32 {
        ...
    }
}
```

```axiom
v.length()
```

→ `Vec2.length`.

Nếu tồn tại inherent method phù hợp, nó được ưu tiên.

---

# 26. Trait method

```axiom
trait Length {
    fn length(self: view<Self>) -> f32
}

impl Length for Vec2 {
    ...
}
```

Nếu không có inherent `length`, solver có thể tìm:

```text
Vec2 : Length
```

và chọn trait method.

---

# 27. Extension method

```axiom
fn length(self: view<Vec2>) -> f32 {
    ...
}
```

Đây chỉ là function.

Nếu module import extension:

```axiom
import geometry.extensions { length }
```

thì:

```axiom
v.length()
```

có thể resolve tới function đó.

---

# 28. Extension không silently override

Nếu đã có:

```axiom
impl Vec2 {
    fn length(...)
}
```

và import:

```axiom
fn length(Vec2)
```

thì extension **không override** inherent method.

Inherent thắng theo semantic rule.

---

# 29. Ambiguous trait methods

Nếu:

```axiom
trait A {
    fn foo(...)
}

trait B {
    fn foo(...)
}
```

và:

```axiom
impl A for User {}
impl B for User {}
```

thì:

```axiom
user.foo()
```

→ ambiguous.

Không chọn theo import order.

---

# 30. Explicit qualification

Cần một syntax để programmer giải ambiguity.

Ta có token `::` rồi.

Ví dụ conceptual:

```axiom
A::foo(user)
```

hoặc trong trait-oriented syntax tương đương được đặc tả sau.

Điểm quan trọng:

> Resolver không tự đoán explicit trait qualification.

Nếu syntax cuối cùng của `<T as Trait>::foo` được bật sau, parser/HIR đã có thể giữ `QualifiedPath` để trait resolver xử lý.

---

# 31. Method syntax chỉ là sugar

```axiom
v.length()
```

semantic cuối cùng có thể trở thành:

```text
Call {
    callee = FunctionId(...)
    args = [v]
}
```

Do đó Axiom không cần một hệ thống “method object” riêng.

---

# 32. Receiver modes

Ví dụ:

```axiom
fn read(self: view<Self>)
fn mutate(self: mut_view<Self>)
fn consume(self: Self)
```

Method resolver phải kiểm tra receiver compatibility.

Ví dụ:

```text
immutable owner
    ↓
view<Self>
```

có thể tạo ephemeral view.

Nhưng:

```text
view<Self>
    ↓
mut_view<Self>
```

không hợp lệ.

---

# 33. Ownership chưa được verifier xử lý ở đây

Method resolver chỉ tạo semantic requirement:

```text
receiver requires view<Self>
```

Ownership/capability verifier sau đó chứng minh capability có thể được tạo.

Điều này giữ phase separation.

---

# 34. Trait bounds

```axiom
fn sort<T: Ord + Copy>(x: mut_view<T>)
```

tạo:

```text
T : Ord
T : Copy
```

Hai obligations độc lập.

Solver có thể giải song song.

---

# 35. Supertraits

Cho phép:

```axiom
trait Debug {}

trait Display: Debug {}
```

nghĩa:

```text
T : Display
```

suy ra:

```text
T : Debug
```

Solver tạo implied obligation.

---

# 36. Không có recursive supertrait

Không:

```axiom
trait A: B {}
trait B: A {}
```

hoặc nếu compiler cho declaration graph tồn tại, solver phải phát hiện cycle và reject.

Tôi khuyến nghị **cấm cycle ngay trait declaration phase**.

Diagnostic:

```text
AX_TRAIT_0007
cyclic supertrait dependency
```

---

# 37. Trait dependency graph

Compiler xây:

```text
TraitGraph
```

Ví dụ:

```text
Display
   ↓
Debug

Serialize
   ↓
Clone
```

Graph phải acyclic.

---

# 38. Auto traits

Axiom đã có:

```text
Copy
Drop
Send
Share
Sized
```

Nhưng không nên để chúng hoạt động giống nhau.

### Copy

Compiler-known semantic property.

### Drop

Compiler-known semantic property.

### Send / Share

Compiler-derived concurrency properties.

### Sized

Type/layout property.

Do đó chúng có thể được biểu diễn bằng trait-like interface nhưng solver backend có intrinsic rules.

---

# 39. `Send`

Ví dụ:

```axiom
spawn(move || work(data))
```

Nếu task có thể migrate thread:

```text
data : Send
```

solver kiểm tra recursively.

---

# 40. `Share`

```text
Arc<T>
```

có thể yêu cầu:

```text
T : Share
```

`Share` không đồng nghĩa `Send`.

---

# 41. Compiler-derived Send/Share

Axiom v1.0 không cho user:

```text
negative impl !Send
```

Thay vào đó compiler suy ra dựa trên semantic fields/types.

Ví dụ conceptual:

```text
struct FileHandle {
    raw: ...
}
```

platform abstraction có thể đánh dấu semantic concurrency property bằng compiler-known/library metadata.

---

# 42. Copy và Drop

Solver phải reject:

```text
T : Copy
```

nếu T có semantic Drop obligation.

Đây không phải ordinary trait implementation.

Đây là invariant của ownership system.

---

# 43. Trait solver không được phá abstraction

Ví dụ:

```axiom
fn foo<T: Display>(x: T)
```

Programmer không cần biết compiler đang:

```text
monomorphize
inline
devirtualize
specialize internally
```

Tất cả là optimization.

---

# 44. Solver và monomorphization

Khi compiler thấy:

```axiom
foo(123)
```

có thể tạo:

```text
foo<i32>
```

nhưng semantics của generic function phải được xác định trước.

Monomorphization không được thay đổi trait resolution.

---

# 45. Trait solver cache

Trait goal thường lặp lại:

```text
i32 : Copy
i32 : Ord
i32 : Send
```

Nên cache:

```text
TraitCache<Key, Result>
```

Key:

```text
TraitId
SelfType
TraitArguments
RelevantEnvironmentFingerprint
```

---

# 46. Cycle detection

Ví dụ:

```text
Goal A<T>
 → requires B<T>
 → requires A<T>
```

Solver phải phát hiện active goal:

```text
ActiveStack
```

Không recursive vô hạn.

---

# 47. Solver budget

Đề xuất:

```text
TraitSolverConfig {
    max_depth
    max_steps
    max_normalization_steps
    max_candidate_count
}
```

Compiler CLI có thể cho tăng giới hạn.

Nhưng vượt giới hạn:

```text
AX_TRAIT_0010
trait resolution overflow
```

Không treo compiler.

---

# 48. Không cho trait solver tự sinh code

Solver chỉ trả semantic result:

```text
PROVEN
DISPROVEN
AMBIGUOUS
OVERFLOW
```

Không tự generate executable code.

Codegen/monomorphization phase làm việc đó.

---

# 49. Trait solver invariants

```text
ATRAIT-20
Trait and type are distinct semantic entities.

ATRAIT-21
Coherence prevents conflicting foreign implementations.

ATRAIT-22
Trait resolution is deterministic.

ATRAIT-23
Inherent methods have priority.

ATRAIT-24
Dynamic dispatch is explicit.

ATRAIT-25
dyn Trait requires object-safe behavior.

ATRAIT-26
Trait obligations have finite solver evaluation.

ATRAIT-27
Solver cycles are detected.

ATRAIT-28
Solver overflow is a compile-time error.

ATRAIT-29
Ambiguous trait resolution is a compile-time error.

ATRAIT-30
User specialization is not part of v0.1.

ATRAIT-31
Compiler-internal specialization cannot change observable semantics.

ATRAIT-32
Blanket implementations cannot overlap ambiguously.

ATRAIT-33
Associated types are compile-time relations.

ATRAIT-34
Associated type normalization is deterministic.

ATRAIT-35
Supertrait dependency graph is acyclic.

ATRAIT-36
Trait resolution does not depend on optimization level.

ATRAIT-37
Trait resolution does not depend on machine target unless the trait itself is target-defined.

ATRAIT-38
Trait solver does not perform runtime dispatch.

ATRAIT-39
Trait solver does not perform ownership verification.

ATRAIT-40
Trait solver does not perform capability verification.

ATRAIT-41
Trait solver does not perform code generation.

ATRAIT-42
Trait cache keys include all semantic inputs affecting the result.
```

---

# 50. Method resolution invariants

```text
AMETHOD-20
Inherent methods have highest priority.

AMETHOD-21
Trait methods are considered only when applicable.

AMETHOD-22
Extension methods require explicit import.

AMETHOD-23
Extension methods cannot silently override inherent methods.

AMETHOD-24
Ambiguous applicable methods are errors.

AMETHOD-25
Method lookup does not use runtime values.

AMETHOD-26
Method lookup does not depend on optimization.

AMETHOD-27
Receiver capability requirements are explicit.

AMETHOD-28
Method syntax lowers to ordinary semantic calls.

AMETHOD-29
Method resolution does not itself transfer ownership.

AMETHOD-30
Method resolution does not itself create persistent capabilities.
```

---

# 51. Một ví dụ hoàn chỉnh

```axiom
trait Display {
    fn display(self: view<Self>) -> Text
}

struct User {
    name: Text
}

impl Display for User {
    fn display(self: view<Self>) -> Text {
        self.name
    }
}

fn print<T: Display>(x: view<T>) {
    x.display()
}

fn main() {
    let user = User {
        name: "Hưng"
    }

    print(user)
}
```

Compiler:

```text
Resolver
    ↓
User → StructId(1)
Display → TraitId(2)
print → FunctionId(3)
main → FunctionId(4)
```

Type checker:

```text
user : User

print
    T = User

obligation:
    User : Display
```

Trait solver:

```text
User : Display
    ↓
ImplId(5)
    ↓
PROVEN
```

Method resolver:

```text
user.display()
    ↓
Display::display for User
```

Typed HIR:

```text
Call FunctionId(Display::display<User>)
```

Sau đó mới đến ownership/capability verification.

---

# 52. Một quyết định rất quan trọng: không có “duck typing”

Axiom không làm:

```text
nếu T có method foo()
    thì coi T là Foo
```

Trait phải tồn tại:

```text
T : Foo
```

Điều này giúp:

- ABI rõ ràng
- diagnostics rõ
- API fingerprint rõ
- generic constraints deterministic
- IDE/AI tooling dễ phân tích.

---

# 53. Không có implicit trait conversion

Không:

```text
T : Into<U>
```

rồi compiler tự biến:

```text
T → U
```

trong mọi context.

Conversion phải được viết rõ:

```axiom
x as U
```

hoặc function:

```axiom
U.from(x)
```

hoặc operator/API đã được định nghĩa.

---

# 54. Trait system của Axiom nên dừng ở đây

Không thêm vào v0.1:

```text
higher-kinded types
dependent types
type-level arithmetic
user specialization
negative impl
trait aliases
arbitrary associated type recursion
implicit conversion traits
automatic coercion graphs
type classes with global search
```

Không phải vì compiler không thể làm.

Mà vì chúng **không cần thiết cho mục tiêu của Axiom**.

Đây chính là cách giữ compiler mạnh nhưng language surface nhỏ.

---

# 55. TYPE-004 / TRAIT-001 implementation milestone

Repository:

```text
compiler/
├── traits/
│   ├── trait_def.rs
│   ├── impl_def.rs
│   ├── goal.rs
│   ├── obligation.rs
│   ├── solver.rs
│   ├── normalize.rs
│   ├── coherence.rs
│   ├── cache.rs
│   ├── method.rs
│   └── diagnostics.rs
│
└── typeck/
    ├── obligations.rs
    ├── generic.rs
    ├── associated.rs
    └── method_calls.rs
```

Test tối thiểu:

```text
trait A {}
struct X {}
impl A for X {}

assert X : A
```

và negative:

```text
struct X {}
require X : A
```

→ `DISPROVEN`.

---

# 56. Thứ tự tiếp theo

Sau Trait Solver, ta **chưa đi ngay vào ownership verifier**.

Cần hoàn thiện Typed HIR trước:

```text
Lexer
 ↓
Parser
 ↓
AST
 ↓
Resolver
 ↓
HIR
 ↓
Type Kernel
 ↓
Trait Solver
 ↓
Method Resolution
 ↓
Typed HIR
```

Sau đó mới:

```text
Typed HIR
 ↓
Ownership Analysis
 ↓
Capability Analysis
 ↓
Drop Analysis
 ↓
Verified MIR
```

Và phần kế tiếp nên là:

# **AXIOM TYPED HIR + EXPRESSION SEMANTICS v0.1**

Ở đó ta sẽ khóa toàn bộ semantics của:

- `if`
- `match`
- `for`
- `while`
- function call
- method call
- closure
- `?`
- `await`
- assignment
- field/index access
- casts
- operators
- `never`
- implicit owner → `view`
- implicit owner → `mut_view`

để sau đó ownership checker có một input **đã hoàn toàn có type và semantic identity**.