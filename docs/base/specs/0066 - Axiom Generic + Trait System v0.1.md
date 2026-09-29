Tiếp tục. Đây là phần tôi nghĩ cần **khóa rất cẩn thận**: Generic + Trait Solver. Nếu thiết kế sai, Axiom rất dễ đi từ “đơn giản nhưng mạnh” thành một phiên bản khó hiểu của C++ templates/Rust traits.

# Axiom Generic + Trait System v0.1

Tôi đề xuất một nguyên tắc lớn:

> **Generic là compile-time abstraction. Trait là compile-time contract. Runtime polymorphism chỉ xuất hiện khi programmer yêu cầu `dyn`.**

Mô hình:

```text
Generic
   │
   ├── type parameter
   ├── const parameter
   └── trait constraints
          │
          ▼
      Trait Solver
          │
          ├── prove constraint
          ├── select implementation
          └── reject ambiguity
          │
          ▼
       Typed MIR
          │
          ▼
   specialization / codegen
```

---

# 1. Generic không phải runtime feature

Ví dụ:

```axiom
fn add<T: Add>(a: T, b: T) -> T {
    a + b
}
```

Không có nghĩa binary chứa:

```text
add<T>
```

và runtime phải tìm `T`.

Compiler có thể tạo:

```text
add<i32>
add<i64>
add<f64>
```

hoặc chia sẻ machine code nếu representations/operations tương đương.

Do đó:

```text
Generic
   ↓
compile-time
   ↓
machine code
```

---

# 2. Generic HIR trước, MIR sau

Không nên instantiate generic ngay trong parser/type checker.

Pipeline:

```text
Source
 ↓
AST
 ↓
Generic HIR
 ↓
Type checking
 ↓
Generic Typed HIR
 ↓
Instantiation
 ↓
Typed MIR
```

Ví dụ:

```axiom
fn square<T: Mul>(x: T) -> T {
    x * x
}
```

compiler giữ:

```text
square<T>
```

cho đến khi có:

```axiom
square<i64>(10)
```

sau đó instantiate:

```text
square<i64>
```

và tạo MIR cụ thể.

---

# 3. Type parameter

Cú pháp có thể:

```axiom
fn max<T: Ord>(a: T, b: T) -> T {
    if a > b { a } else { b }
}
```

Struct:

```axiom
struct Box<T> {
    value: T
}
```

Enum:

```axiom
enum Option<T> {
    Some(T),
    None
}
```

Đây là đủ mạnh cho phần lớn systems programming.

---

# 4. Const generic

Tôi vẫn muốn Axiom có compile-time value parameters:

```axiom
struct Matrix<T, const N: usize> {
    data: Array<T, N>
}
```

Ví dụ:

```text
Matrix<f32, 4>
Matrix<f32, 16>
```

Nhưng cần **giới hạn mạnh**.

Không nên ngay từ đầu cho:

```text
const N: arbitrary_type
```

hay dependent types.

V0.1:

```text
const parameter
 ├── integer
 ├── bool
 └── maybe enum later
```

---

# 5. Không có dependent type system tổng quát

Ví dụ:

```text
fn foo<T, x: T>(...)
```

và type phụ thuộc arbitrary value:

```text
Array<T, f(x + y * z)>
```

không nên trở thành một hệ thống type-level programming hoàn chỉnh.

Chỉ cần:

```text
Array<T, N>
```

với `N` compile-time constant.

Điều này giữ compiler và trait solver nhỏ hơn rất nhiều.

---

# 6. Trait chỉ mô tả capability/contract

Ví dụ:

```axiom
trait Add<Rhs = Self> {
    type Output;

    fn add(self, rhs: Rhs) -> Self.Output;
}
```

Trait không chứa:

```text
data fields
object state
```

Nó chỉ nói:

```text
Type X supports operation Y
```

---

# 7. `impl`

Ví dụ:

```axiom
struct Vec2 {
    x: f32
    y: f32
}

impl Add for Vec2 {
    fn add(self, rhs: Vec2) -> Vec2 {
        Vec2 {
            x: self.x + rhs.x,
            y: self.y + rhs.y
        }
    }
}
```

Semantic:

```text
Add(Vec2, Vec2)
      ↓
implementation found
      ↓
direct static function
```

Không cần vtable.

---

# 8. Primitive operators

Tôi không muốn compiler biến:

```axiom
a + b
```

thành một generic trait call quá sớm.

Frontend có thể biểu diễn:

```text
BinaryOp(Add, a, b)
```

Type checker:

```text
built-in numeric fast path
        OR
trait resolution
```

Ví dụ:

```text
i64 + i64
```

compiler biết trực tiếp:

```text
INTEGER_ADD_CHECKED
```

Trong khi:

```text
Vec2 + Vec2
```

có thể resolve:

```text
Add::add
```

Như vậy primitive arithmetic vẫn cực kỳ dễ tối ưu.

---

# 9. Associated type

Tôi vẫn giữ associated type:

```axiom
trait Iterator {
    type Item;

    fn next(self: mut_view<Self>) -> Option<Self.Item>;
}
```

Ví dụ:

```axiom
struct RangeIter {
    current: i64
    end: i64
}

impl Iterator for RangeIter {
    type Item = i64;

    ...
}
```

Sau resolution:

```text
Iterator::Item<RangeIter>
       ↓
i64
```

Không cần runtime metadata.

---

# 10. Associated type không nên là arbitrary type function

Tôi không muốn:

```text
type Output<T, U, V, X> = complicated_type_function(...)
```

được dùng như một ngôn ngữ type-level hoàn chỉnh.

Trait solver chỉ cần xử lý:

```text
TraitRef
AssociatedType
Type equality
Generic constraints
```

ở mức bounded.

---

# 11. Trait solver không phải theorem prover

Đây là quyết định rất quan trọng.

Solver của Axiom chỉ nên giải các dạng:

```text
T: Trait
T == U
Assoc<T>::Item == U
T implements Trait<X>
```

và logical combination đơn giản:

```text
T: A + B
```

Không cho:

```text
∀ T where ...
```

hoặc recursion tùy ý trên type-level.

Mục tiêu:

```text
predictable
terminating
fast
deterministic
```

---

# 12. Trait solving có giới hạn

Ví dụ:

```text
SolverDepth
SolverSteps
RecursionLimit
```

Nếu vượt:

```text
AX_TRAIT_0012
trait resolution exceeded compiler limit
```

Không được:

```text
compiler chạy vô hạn
```

hoặc stack overflow.

---

# 13. Coherence

Ta cần một rule rất mạnh:

> **Một cặp `(Trait, Type)` chỉ có tối đa một applicable implementation trong một compilation universe.**

Ví dụ:

```axiom
trait Serialize { ... }

impl Serialize for User { ... }
```

Không thể đồng thời:

```axiom
impl Serialize for User { ... }
impl Serialize for User { ... }
```

---

# 14. Orphan rule

Tôi vẫn đề xuất:

`impl Trait for Type` hợp lệ nếu:

```text
Trait thuộc package hiện tại
OR
Type thuộc package hiện tại
```

Không cho:

```text
foreign trait
+
foreign type
```

Ví dụ package A định nghĩa:

```text
Display
```

package B định nghĩa:

```text
User
```

package C không thể tùy ý tạo:

```text
impl Display for User
```

nếu cả hai đều foreign.

Điều này ngăn dependency graph trở nên không xác định.

---

# 15. Extension methods

Nhưng vẫn cần khả năng mở rộng.

Có thể:

```axiom
fn to_json(x: User) -> Text { ... }
```

và gọi:

```axiom
user.to_json()
```

nếu function được import.

Nhưng đây là **extension function**, không phải thêm method vào foreign type về mặt semantic ownership.

Method resolution:

```text
1. inherent
2. trait
3. imported extension
4. generic extension
5. ambiguity → error
```

Đã thống nhất trước.

---

# 16. Không có “magic method search” vô hạn

Nếu:

```axiom
x.foo()
```

compiler chỉ search trong một tập xác định.

Không:

```text
x
 ↓
trait A
 ↓
trait B
 ↓
extension C
 ↓
package D
 ↓
package E
 ↓
...
```

vô hạn.

Import boundary phải giới hạn candidate set.

Điều này giúp:

- compile nhanh;
- diagnostics rõ;
- AI dễ sửa;
- refactoring predictable.

---

# 17. Generic inference

Ví dụ:

```axiom
fn identity<T>(x: T) -> T {
    x
}

let x = identity(42);
```

Compiler suy ra:

```text
T = i64
```

Không cần:

```axiom
identity<i64>(42)
```

Nhưng nếu:

```axiom
let x = identity();
```

→ thiếu thông tin → error.

---

# 18. Inference phải dựa trên constraint solving

Ví dụ:

```axiom
fn convert<T, U>(x: T) -> U
```

và:

```axiom
let x: i64 = convert(value);
```

Compiler có:

```text
T = type(value)
U = i64
```

Nếu còn constraint:

```text
T: Convert<U>
```

solver phải prove:

```text
Convert<type(value), i64>
```

Không prove được:

```text
AX_TRAIT_0003
unsatisfied constraint
```

---

# 19. Không implicit conversion chỉ vì có trait

Đây là điểm tôi muốn khóa.

Nếu:

```axiom
impl From<i32> for i64
```

thì:

```axiom
let x: i64 = value_i32;
```

**không tự động gọi `From`.**

Muốn convert:

```axiom
let x = i64.from(value_i32);
```

hoặc syntax conversion được chọn sau.

Trait implementation không tự biến thành implicit conversion.

Điều này giữ semantics rõ.

---

# 20. Specialization

Có hai loại:

### Compiler specialization

Compiler quyết định:

```text
generic<T>
 ↓
T = i64
 ↓
optimize
```

hoàn toàn được.

### Programmer-defined specialization

Ví dụ:

```text
impl<T> Foo for T
impl Foo for i64
```

và compiler phải chọn special-case.

Tôi đề nghị:

> **Không hỗ trợ programmer-defined specialization trong v0.1.**

Nó tạo overlap/coherence complexity lớn.

---

# 21. Generic implementation

Cho phép:

```axiom
impl<T: Add> Add for Box<T> {
    ...
}
```

Solver phải instantiate:

```text
Box<i64>
```

và prove:

```text
i64: Add
```

Nếu không:

```text
not applicable
```

---

# 22. Monomorphization

V0.1:

```text
generic HIR
      ↓
instantiate
      ↓
typed MIR
      ↓
optimize
```

Ví dụ:

```text
max<i64>
max<f64>
max<User>
```

mỗi specialization có MIR riêng.

Ưu điểm:

- optimization mạnh;
- inline tốt;
- static dispatch;
- không runtime generic metadata.

---

# 23. Nhưng không bắt buộc duplicate machine code

Ví dụ:

```text
foo<u32>
foo<i32>
```

có thể sau legalization trở thành cùng machine sequence.

Compiler có thể merge:

```text
foo<u32> ──┐
           ├── machine implementation
foo<i32> ──┘
```

Nếu semantic/ABI cho phép.

Do đó:

```text
Monomorphization
≠
one binary copy per instantiation
```

---

# 24. Generic code sharing là optimizer

Không nên đưa nó vào language semantics.

Language chỉ nói:

```text
foo<i32>
foo<i64>
```

là những instantiations hợp lệ.

Compiler quyết định:

```text
duplicate
inline
merge
specialize
erase
```

---

# 25. Trait object

Khi programmer viết:

```axiom
dyn Drawable
```

lúc đó runtime polymorphism xuất hiện.

Conceptual:

```text
dyn Drawable
├── data_ptr
└── dispatch_ptr
```

Dispatch table có thể chứa:

```text
method pointers
drop function
size
alignment
metadata
```

tùy ABI.

Nhưng đây là **explicit dynamic dispatch**.

---

# 26. Static vs dynamic

```axiom
fn draw<T: Drawable>(x: T)
```

→ static dispatch.

```axiom
fn draw(x: dyn Drawable)
```

→ dynamic dispatch.

Sự khác biệt nhìn thấy ngay trong source.

Đây là điều tôi đánh giá rất quan trọng cho performance predictability.

---

# 27. `dyn Trait` phải có object-safety-like rule

Không phải trait nào cũng có thể trở thành `dyn Trait`.

Ví dụ trait có method:

```axiom
fn clone<T>(&self) -> T
```

không thể tạo một runtime object nếu runtime không biết T.

Do đó compiler phải kiểm tra trait có thể erase type parameters hay không.

Nhưng thay vì gọi hệ thống “object safety” quá phức tạp, ta có thể gọi:

```text
DynamicDispatchCompatible
```

và compiler kiểm tra bounded rules.

---

# 28. Generic + `dyn`

Ví dụ:

```axiom
fn draw_all<T: Drawable>(items: view<T>)
```

static:

```text
T known
↓
direct calls
```

Trong khi:

```axiom
fn draw_all(items: view<dyn Drawable>)
```

dynamic:

```text
data_ptr
dispatch_ptr
↓
indirect call
```

Programmer quyết định trade-off.

---

# 29. Trait composition

Có thể:

```axiom
trait Shape: Drawable + Transformable {
}
```

Ý nghĩa:

```text
Shape
requires Drawable
requires Transformable
```

Không có:

```text
Shape
inherits Drawable data
```

Trait chỉ là constraint composition.

---

# 30. Blanket implementation

Cho phép:

```axiom
impl<T: Display> Printable for T {
    ...
}
```

nhưng cần cẩn thận coherence.

Nếu package có:

```text
impl<T: A> B for T
```

thì nó có thể áp dụng cho rất nhiều types.

Tôi đề nghị v0.1 cho blanket impl, nhưng solver phải enforce coherence nghiêm ngặt.

---

# 31. Associated constants

Có thể:

```axiom
trait Numeric {
    const ZERO: Self;
}
```

và:

```axiom
impl Numeric for i64 {
    const ZERO = 0;
}
```

Compiler resolve:

```text
Numeric::ZERO<i64>
```

thành compile-time value.

Không cần runtime lookup.

---

# 32. Associated functions

Ví dụ:

```axiom
trait From<T> {
    fn from(value: T) -> Self;
}
```

Call:

```axiom
let x = i64.from(value);
```

Compiler resolve:

```text
From<i32>::from<i64>
```

thành direct call/static function.

---

# 33. Operator traits

Có thể định nghĩa:

```text
Add
Sub
Mul
Div
Neg
Eq
Ord
Index
```

nhưng compiler có intrinsic mappings.

Ví dụ:

```axiom
a + b
```

type checker:

```text
if primitive numeric:
    builtin arithmetic
else:
    resolve Add
```

Điều này tránh trait machinery cho mọi integer addition.

---

# 34. Trait solver algorithm

Tôi đề xuất **không dùng một theorem prover tổng quát**.

Solver dạng:

```text
Goal
 │
 ├── builtin rule?
 │
 ├── exact impl?
 │
 ├── generic impl?
 │
 ├── associated type equality?
 │
 └── impossible / ambiguous
```

Ví dụ:

```text
Goal:
    Vec<i64>: Iterator
```

solver:

```text
lookup impl Iterator for Vec<T>
        ↓
T = i64
        ↓
success
```

---

# 35. Canonical goal

Internal representation:

```text
TraitGoal {
    type: TypeId
    trait: TraitId
    args: [TypeId]
}
```

Ví dụ:

```text
Vec<i64>: Iterator
```

thành:

```text
TraitGoal {
    type = Vec<i64>
    trait = Iterator
}
```

Associated type:

```text
Iterator::Item<Vec<i64>> == i64
```

thành equality constraint.

---

# 36. Solver cache

Trait resolution sẽ xảy ra cực nhiều.

Do đó:

```text
Goal
 ↓
canonicalize
 ↓
cache lookup
 ↓
solve
 ↓
cache result
```

Result:

```text
PROVEN
DISPROVEN
AMBIGUOUS
OVERFLOW
```

Điều này cũng rất hữu ích cho compiler performance.

---

# 37. Diagnostics phải giải thích proof failure

Ví dụ:

```text
AX_TRAIT_0003

cannot satisfy:
    T: Add

required by:
    foo<T>()

because:
    no implementation of Add found for T

required at:
    a + b
```

Hoặc:

```text
AX_TRAIT_0007

multiple implementations match:
    Add<T> for Wrapper<T>
    Add<T> for T

type inference cannot select one
```

Không chỉ:

```text
trait error
```

---

# 38. Trait solver phải deterministic

Cùng source + cùng package graph:

```text
solver result
```

phải giống nhau.

Không phụ thuộc:

- hash map iteration order;
- file order;
- machine;
- optimization level.

Nếu có nhiều candidate hợp lệ mà không có rule ưu tiên:

```text
AMBIGUOUS
```

Không “chọn cái đầu tiên tìm thấy”.

---

# 39. Generic + ownership

Ví dụ:

```axiom
fn consume<T>(x: T) {
    use(x);
}
```

Không cần:

```text
T: Copy
```

nếu body chỉ move/use một lần.

Nhưng:

```axiom
fn duplicate<T>(x: T) {
    let a = x;
    let b = x;
}
```

solver/type checker phát hiện:

```text
T must be Copy
```

hoặc source phải explicit:

```axiom
let b = x.clone();
```

Điều này rất phù hợp nguyên tắc trước:

> **Generic constraints nên phát sinh từ operation thực sự cần thiết, không bắt programmer khai báo thừa.**

---

# 40. Generic + Drop

Nếu:

```axiom
fn foo<T>(x: T) {
}
```

và `T` có thể có Drop:

```text
foo<File>
```

thì compiler phải đảm bảo Drop đúng.

Nhưng không cần:

```text
T: Drop
```

trong source.

Compiler-known property:

```text
Drop(T)
```

được instantiate sau khi T được biết.

`Drop` không phải ordinary trait mà programmer có thể implement tùy ý.

---

# 41. `Copy` cũng vậy

```text
Copy
Drop
Send
Share
Sized
```

tiếp tục là **compiler-known properties**.

Không biến chúng thành trait solver arbitrary.

Điều này giảm đáng kể complexity.

---

# 42. Trait solver và compiler phases

Tôi đề xuất:

```text
AST
 ↓
Name Resolution
 ↓
Generic Type Checking
 ↓
Constraint Collection
 ↓
Trait Solving
 ↓
Typed HIR
 ↓
Instantiation
 ↓
MIR
```

Nhưng có thể solver được gọi lazy trong type checking.

Quan trọng là:

> MIR chỉ được tạo khi tất cả semantic generic/trait constraints của đoạn code đã được resolve.

---

# 43. Axiom Generic Invariants

### ATG-21 — Compile-Time Genericity
Generic abstraction không yêu cầu runtime metadata mặc định.

### ATG-22 — Deterministic Inference
Inference phải deterministic.

### ATG-23 — Bounded Trait Solver
Trait solver phải bounded và terminating.

### ATG-24 — Coherence
Không tồn tại nhiều applicable impl cho cùng trait/type context.

### ATG-25 — Explicit Dynamic Dispatch
Runtime polymorphism chỉ xuất hiện qua explicit dynamic type/operation.

### ATG-26 — No Implicit Conversion via Traits
Trait implementation không tự tạo implicit conversion.

### ATG-27 — Generic Constraint Minimality
Chỉ yêu cầu property/constraint thực sự cần thiết.

### ATG-28 — Specialization Is Compiler Strategy
Code specialization/sharing là compiler decision, không phải source semantic guarantee.

### ATG-29 — Type Identity Independent of Representation
Distinct semantic types có thể có identical machine representation.

### ATG-30 — Abstraction Erasure
Compile-time generic/trait machinery biến mất nếu không có observable runtime semantics.

---

# Một vấn đề lớn tôi muốn giải quyết tiếp theo

Đến đây Axiom đã có:

```text
Primitive
Struct
Enum
Tuple
Array
Generic
Trait
Closure
Option
Result
Pattern
Ownership
View
Region
Effect
Concurrency
Async
```

Nhưng còn một thứ cực kỳ quan trọng cho **performance thực tế**:

## **Memory layout + representation control**

Chúng ta đã nói:

```text
compiler-controlled layout
repr(C)
packed
align
```

nhưng chưa thiết kế đầy đủ.

Tôi muốn tiếp theo chốt:

```text
1. struct layout
2. enum/tag layout
3. niche optimization
4. alignment/padding
5. SIMD/vector types
6. bitfields?
7. packed structs
8. endian
9. explicit representation
10. ABI representation
11. `repr(C)`
12. stable layout guarantees
```

Đây là chỗ Axiom có thể đạt mục tiêu **“abstraction cao nhưng binary cực thấp”**. Đặc biệt cần quyết định **bitfield có nên là Core feature hay chỉ là library/intrinsic**, và cách cho programmer kiểm soát layout khi viết OS/network/game/embedded code mà không biến mọi struct bình thường thành một đống annotation.