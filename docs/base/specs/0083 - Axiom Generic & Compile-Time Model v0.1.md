Tiếp tục từ baseline hiện tại, phần hợp lý nhất là chốt **Generic + Trait Solver + Monomorphization + Compile-time Execution**. Đây là một trong những điểm quyết định Axiom có thực sự đạt mục tiêu “ngôn ngữ cấp cao nhưng hiệu năng kiểu C/C++” hay không.

# Axiom Generic & Compile-Time Model v0.1

## 1. Nguyên tắc lớn

Tôi đề xuất Axiom đi theo mô hình:

> **Generic là abstraction ở compile-time, không phải abstraction runtime.**

Tức là:

```axiom
fn max<T: Ord>(a: T, b: T) -> T {
    if a > b { a } else { b }
}
```

không mặc định tạo ra:

```text
runtime generic object
runtime type information
boxed value
virtual call
reflection metadata
```

Mà compiler có thể biến thành các phiên bản chuyên biệt:

```text
max<i32>
max<f64>
max<MyStruct>
```

và sau đó inline/eliminate tiếp.

Điều này rất phù hợp với mục tiêu của Axiom:

```text
High-level source
       ↓
Generic abstraction
       ↓
Compile-time specialization
       ↓
Concrete machine code
```

---

# 2. Monomorphization nên là mặc định

Ví dụ:

```axiom
fn sum<T: Add>(a: T, b: T) -> T {
    a + b
}

fn main() {
    let a = sum(10, 20)
    let b = sum(1.5, 2.5)
}
```

Compiler có thể tạo:

```text
sum<i32>
sum<f64>
```

Sau optimization:

```text
a = 10 + 20
b = 1.5 + 2.5
```

Thậm chí cả hai có thể được constant-fold.

### Nhưng không nên bắt buộc mỗi instantiation phải tạo code riêng

Đây là điểm quan trọng.

Monomorphization là **compiler strategy**, không phải semantic requirement.

Ví dụ:

```axiom
fn identity<T>(x: T) -> T {
    x
}
```

Compiler có thể:

```text
identity<i32>
identity<i64>
identity<f32>
```

hoặc nếu representation/codegen cho phép:

```text
shared_identity
```

hoặc inline toàn bộ.

Do đó:

> **Source-level generic identity ≠ machine-level duplicated function.**

---

# 3. Không nên cho programmer điều khiển specialization trong v0.1

Tôi vẫn giữ quyết định trước đó:

```text
NO:
specialize<T>
default specialization
priority specialization
partial specialization
```

trong Core v0.1.

Ví dụ không nên có:

```axiom
specialize fn foo<i32>(...)
```

Lý do không phải vì specialization xấu.

Mà vì nó làm compiler phải giải quyết một lượng lớn vấn đề:

```text
overlap
priority
coherence
ambiguity
separate compilation
incremental compilation
trait resolution
code generation
```

Trong khi compiler **tự biết** lúc nào specialization có lợi.

Ví dụ compiler có thể tự quyết định:

```text
generic implementation
        ↓
constant propagation
        ↓
devirtualization
        ↓
inlining
        ↓
dead code elimination
```

hoặc:

```text
generic implementation
        ↓
specialized implementation
```

### Nguyên tắc

> **Programmer mô tả semantic behavior. Compiler quyết định implementation specialization.**

Đây là một điểm rất phù hợp với triết lý Axiom:

**Compiler Complexity Is Not Language Complexity.**

---

# 4. Trait solver không được trở thành theorem prover

Đây là chỗ cần cực kỳ cẩn thận.

Axiom có:

```axiom
trait Add<Rhs> {
    type Output
    fn add(self: T, rhs: Rhs) -> Self.Output
}
```

Compiler cần giải:

```text
Does T implement Add<Rhs>?
What is Add<Rhs>::Output?
Which implementation applies?
```

Nhưng **không nên** biến type system thành hệ thống chứng minh toán học.

Trait solver phải có giới hạn rõ ràng:

```text
PROVEN
DISPROVEN
AMBIGUOUS
OVERFLOW
```

và:

```text
maximum recursion depth
maximum solver steps
cycle detection
memoization
```

Ví dụ:

```axiom
fn foo<T>(x: T)
where T: A + B
```

compiler phải có thể chứng minh:

```text
T implements A
T implements B
```

Nếu không chứng minh được:

```text
compile error
```

không được “đoán”.

---

# 5. Trait resolution phải deterministic

Ví dụ:

```axiom
trait Printable {
    fn print(self: view<Self>)
}
```

và:

```axiom
impl Printable for User { ... }
```

thì:

```axiom
user.print()
```

phải luôn resolve cùng một implementation trong cùng compilation universe.

Không được phụ thuộc:

```text
file order
import order
compiler hash
optimization level
```

Đây là lý do coherence/orphan rule rất quan trọng.

---

# 6. Associated type nên giữ

Tôi cho rằng Axiom **nên có associated types** ngay từ v0.1.

Ví dụ:

```axiom
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self.Item>
}
```

Sau đó:

```axiom
struct Range {
    start: i64
    end: i64
}

impl Iterator for Range {
    type Item = i64

    fn next(self: mut_view<Self>) -> Option<i64> {
        ...
    }
}
```

Điều này tốt hơn việc phải truyền quá nhiều generic parameter:

```axiom
Iterator<Range, i64, ...>
```

Associated type cũng rất hữu ích cho:

```text
Iterator
Add
Index
Future
Allocator
Serializer
Deserializer
Collection
```

---

# 7. `impl Trait` và `dyn Trait` phải cực kỳ khác nhau

Axiom nên phân biệt rõ:

### Static

```axiom
fn make_shape() -> impl Shape
```

nghĩa là:

```text
một concrete type
+
compiler biết type
+
static dispatch
+
có thể inline
+
không cần vtable
```

### Dynamic

```axiom
fn draw(shape: dyn Shape)
```

nghĩa là programmer **yêu cầu dynamic dispatch**.

Conceptually:

```text
data_ptr
dispatch_ptr
```

Không có:

```text
object header
```

trên object gốc.

Điều này rất quan trọng.

```text
struct Dog
```

không tự nhiên trở thành:

```text
[object header]
[data]
[vtable]
```

Chỉ khi programmer dùng abstraction dynamic:

```text
dyn Shape
```

thì representation dynamic mới xuất hiện.

---

# 8. Generic + dyn Trait

Ví dụ:

```axiom
fn draw_all<T: Shape>(items: view<T>) {
    for x in items {
        x.draw()
    }
}
```

Đây là static:

```text
draw_all<Circle>
draw_all<Rectangle>
```

Compiler có khả năng:

```text
inline
devirtualize
vectorize
unroll
```

Trong khi:

```axiom
fn draw_one(x: dyn Shape) {
    x.draw()
}
```

là dynamic.

Như vậy Axiom cho programmer lựa chọn rất rõ:

```text
generic / impl Trait → static abstraction
dyn Trait             → dynamic abstraction
```

Không có hidden cost.

---

# 9. Generic constraints phải tối thiểu

Không nên bắt compiler resolve những constraint không cần thiết.

Ví dụ:

```axiom
fn sum<T: Add>(a: T, b: T) -> T
```

chỉ cần `Add`.

Không nên yêu cầu:

```axiom
T: Copy + Sized + Clone + Send + Share + ...
```

trừ khi implementation thực sự cần.

Compiler có thể **suy ra các property nội bộ**.

Ví dụ:

```axiom
fn spawn<T>(x: T)
```

nếu `x` được chuyển sang thread:

```text
T: Send
```

được phát hiện bởi semantic analysis.

Không nhất thiết programmer phải viết:

```axiom
fn spawn<T: Send>(...)
```

trong mọi trường hợp.

Tuy nhiên, đối với **public API contract**, constraint cần thiết để caller type-check được vẫn phải được biểu diễn trong generic signature/metadata.

---

# 10. Compile-time execution

Đây là phần tôi nghĩ Axiom nên làm mạnh hơn C++ nhưng **không biến thành một ngôn ngữ meta-programming riêng**.

Nguyên tắc:

> **Compile-time execution sử dụng chính semantics của Axiom.**

Không tạo thêm một ngôn ngữ thứ hai.

Ví dụ:

```axiom
const SIZE = 1024
```

hoặc:

```axiom
comptime {
    ...
}
```

có thể chạy bằng:

```text
Typed MIR
   ↓
Compile-time evaluator
   ↓
Semantic Oracle
```

---

# 11. `const` và `comptime` nên có vai trò khác nhau

Tôi đề xuất:

### `const`

Là **giá trị compile-time**.

```axiom
const PAGE_SIZE = 4096
const BUFFER_SIZE = PAGE_SIZE * 4
```

Compiler có thể yêu cầu expression phải evaluate được tại compile-time.

---

### `comptime`

Là **thực thi code tại compile-time**.

Ví dụ:

```axiom
comptime fn factorial(n: u64) -> u64 {
    if n == 0 {
        1
    } else {
        n * factorial(n - 1)
    }
}
```

sau đó:

```axiom
const N = factorial(10)
```

Compiler thực thi function đó.

---

# 12. Không nên cho `comptime` quyền truy cập hệ thống mặc định

Nếu compile-time code được phép:

```text
read arbitrary file
network
execute process
access environment
```

thì build trở nên:

```text
non-reproducible
unsafe
hard to cache
hard to sandbox
hard to cross compile
```

Do đó mặc định:

```text
comptime
 ├── deterministic
 ├── sandboxed
 ├── no network
 ├── no arbitrary filesystem
 ├── no process execution
 └── bounded resource usage
```

Nếu cần filesystem/code generation:

```text
explicit build tool / build capability
```

chứ không mở quyền cho mọi `comptime`.

---

# 13. Compile-time evaluator nên dùng cùng semantic engine

Đây là kiến trúc rất đáng giữ.

Không nên có:

```text
Runtime semantics
     ↓
Runtime interpreter

Compile-time semantics
     ↓
Một evaluator hoàn toàn khác
```

vì sẽ dễ xảy ra:

```text
runtime: A
compile-time: B
```

Thay vào đó:

```text
             Typed MIR
                │
        ┌───────┴────────┐
        ↓                ↓
 Semantic Oracle    Native Backend
        │
        ├── Runtime interpretation
        └── Compile-time evaluation
```

Như vậy compile-time execution trở thành một **execution mode của Axiom**, không phải ngôn ngữ thứ hai.

---

# 14. Nhưng compile-time không cần hỗ trợ toàn bộ runtime

Ví dụ:

```axiom
fn read_file() -> Result<Text, Error> {
    ...
}
```

không nhất thiết compile-time executable.

Compiler có thể gắn capability:

```text
CT:
PURE
ALLOC
READ_CONST
```

và từ chối:

```text
IO
SPAWN
NETWORK
FFI
VOLATILE
UNKNOWN
```

trừ khi explicitly được cấp quyền.

Điều này tận dụng luôn **Effect System** đã thiết kế.

---

# 15. Generic + comptime + const generic

Axiom nên hỗ trợ:

```axiom
struct Matrix<T, N: usize, M: usize> {
    data: Array<T, N * M>
}
```

nhưng chỉ nên hỗ trợ **bounded const generics**.

Cho phép:

```text
integer constants
boolean constants
basic compile-time expressions
```

Không nên ngay từ đầu có:

```text
full dependent types
type-level theorem proving
arbitrary values as types
```

Ví dụ:

```axiom
Array<T, N>
```

rất hữu ích.

Nhưng:

```axiom
Array<T, if complicated_theorem(...) then N else M>
```

không cần thiết cho mục tiêu Axiom.

---

# 16. Generic metadata

Để separate compilation hoạt động, compiler không thể chỉ lưu machine code.

Ví dụ module:

```axiom
pub fn sort<T: Ord>(x: mut_view<T>) { ... }
```

module khác import nó.

Compiler cần biết:

```text
function signature
generic parameters
trait constraints
associated types
const parameters
visibility
effects nếu cần
ABI attributes
representation requirements
```

Do đó object/package metadata nên chứa **typed generic interface information**.

Nhưng:

> Metadata compile-time ≠ runtime metadata.

Sau khi chương trình build xong, toàn bộ generic metadata không cần tồn tại trong executable nếu không có reflection yêu cầu.

---

# 17. Incremental compilation

Generic là nơi dễ phá incremental build.

Ví dụ:

```text
A:
    fn foo<T: Trait>(...)
```

B:

```text
foo<MyType>()
```

Nếu implementation của `foo` thay đổi:

```text
A source changed
```

thì compiler cần biết specialization nào bị ảnh hưởng.

Do đó Semantic Interface Fingerprint nên bao gồm:

```text
generic signature
trait constraints
associated types
const constraints
semantic body hash
representation requirements
```

Có thể chia:

```text
Interface Fingerprint
Implementation Fingerprint
Specialization Fingerprint
```

để tránh rebuild không cần thiết.

---

# 18. Code bloat phải là trách nhiệm của compiler

Đây là một điểm quan trọng đối với mục tiêu binary nhỏ.

Naive monomorphization:

```text
foo<i8>
foo<i16>
foo<i32>
foo<i64>
foo<u8>
foo<u16>
foo<u32>
foo<u64>
...
```

có thể làm binary phình rất lớn.

Axiom nên có **multi-level generic code sharing**:

```text
                    Generic
                       │
             ┌─────────┴─────────┐
             ↓                   ↓
      specialize             share
             │                   │
      optimized code       common implementation
```

Compiler có thể nhận ra:

```text
foo<u32>
foo<i32>
```

có cùng machine representation/behavior đủ để share code.

Hoặc:

```text
generic algorithm
       ↓
one implementation
       +
specialized hot paths
```

Programmer không cần quyết định.

---

# 19. Đây cũng là lý do không nên expose specialization sớm

Nếu programmer có:

```axiom
specialize foo<i32>
```

thì compiler không còn tự do:

```text
share
merge
clone
inline
outline
devirtualize
```

theo cách tốt nhất.

Vì vậy:

> **Specialization trong Axiom v0.1 là optimization decision, không phải language feature.**

---

# 20. Một nguyên tắc rất mạnh có thể thêm vào Axiom

Tôi đề xuất chính thức hóa:

### AGEN-01 — Generic Erasure

> Generic constructs that are not required by observable runtime semantics must be erased before final machine representation.

Ví dụ:

```axiom
fn identity<T>(x: T) -> T {
    x
}
```

Không cần:

```text
generic descriptor
type ID
runtime generic table
```

---

### AGEN-02 — Specialization Freedom

Compiler được phép:

```text
monomorphize
share
inline
clone
outline
devirtualize
erase
```

miễn là observable semantics không đổi.

---

### AGEN-03 — Trait Runtime Explicitness

Trait abstraction không tạo runtime dispatch trừ khi programmer sử dụng dynamic dispatch hoặc một abstraction library yêu cầu nó.

---

### AGEN-04 — Bounded Resolution

Trait resolution phải deterministic, terminating và có resource bounds.

---

### AGEN-05 — Compile-time Semantic Unity

Compile-time execution và runtime execution dùng chung semantic model.

---

### AGEN-06 — Compile-time Capability Isolation

Compile-time code không có quyền hệ thống ngoài capability được cấp rõ ràng.

---

### AGEN-07 — No Runtime Generic Metadata

Generic metadata chỉ tồn tại ở compilation/build/debug/explicit-reflection boundary khi cần.

---

### AGEN-08 — Code-size Freedom

Compiler được phép lựa chọn specialization hoặc code sharing để cân bằng:

```text
performance
binary size
compile time
cache locality
```

---

# 21. Kiến trúc compiler sau khi bổ sung phần này

Pipeline hiện tại nên thành:

```text
Source
  ↓
AST
  ↓
Resolver
  ↓
HIR
  ↓
Generic Analysis
  ↓
Type Checking
  ↓
Trait Resolution
  ↓
Const/Comptime Evaluation
  ↓
Closure/Async Analysis
  ↓
MIR
  ↓
Ownership / Capability
Effect
Concurrency
Pattern
Drop
Verification
  ↓
Verified MIR
  ↓
Generic Instantiation
  ↓
Specialization / Code Sharing
  ↓
Semantic Optimization
  ↓
ABI Lowering
  ↓
LIR
  ↓
Machine Backend
```

Một điểm tôi muốn sửa rất nhẹ so với pipeline trước: **generic instantiation không nên cố định cứng là “ngay trước optimization”**. Compiler nên có thể instantiate lazily và optimize sau khi biết context.

---

# 22. Kết luận thiết kế

Tôi sẽ chốt hướng này cho Axiom:

| Thành phần | Axiom |
|---|---|
| Generic | Có |
| Monomorphization | Mặc định/ưu tiên |
| Code sharing | Compiler tự quyết định |
| Specialization | Compiler tự quyết định |
| Programmer specialization | Không v0.1 |
| Trait | Có |
| Associated types | Có |
| Trait solver | Bounded |
| Theorem proving | Không |
| `impl Trait` | Static |
| `dyn Trait` | Dynamic, explicit |
| Vtable | Chỉ dynamic abstraction |
| Runtime generic metadata | Không |
| Const generics | Có, bounded |
| Dependent types | Không |
| `const` | Có |
| `comptime` | Có |
| Compile-time interpreter | Có |
| Compile-time FS/network | Không mặc định |
| Macro language riêng | Chưa cần |
| Runtime reflection | Opt-in |

Điểm quan trọng nhất là Axiom **không cố làm type system “thông minh nhất có thể”**. Nó làm type system **đủ mạnh để compiler chứng minh safety và generate code cực tốt**, rồi dừng ở đó.

Đây là hướng giúp Axiom tránh hai cực:

```text
C/C++
  ↓
runtime rất ít
nhưng programmer phải tự quản lý quá nhiều
```

và:

```text
Rust/GC/managed systems
  ↓
safety/abstraction mạnh
nhưng programmer phải chịu nhiều machinery hoặc runtime constraints
```

Axiom hướng tới:

```text
              Axiom
                │
     ┌──────────┴──────────┐
     ↓                     ↓
Programmer sees       Compiler handles
simple semantics      complex proof/optimization
     │                     │
     └──────────┬──────────┘
                ↓
          native machine code
```

**Chủ đề tiếp theo tôi đề xuất đi thẳng vào là `Syntax & Surface Language v0.1`**: chúng ta đã thiết kế gần như toàn bộ semantic engine, nhưng chưa chốt đủ chặt **cú pháp thực tế của Axiom** — đặc biệt `struct`, `trait`, `impl`, generic, `view/mut_view`, `match`, `error handling`, closure, `async`, attributes và module syntax. Đây là lúc có thể thiết kế một syntax rất gọn mà không phải mang theo những rắc rối cú pháp của C++/Rust.