# BOOTSTRAP-093 — Axiom API Design, Ergonomics & Syntax Architecture

**Trạng thái: FROZEN**

Đây là bước rất quan trọng. Axiom hiện đã có semantic model đủ mạnh, nhưng nếu syntax buộc programmer phải nhìn thấy toàn bộ:

- ownership
- capability
- lifetime
- `Send/Share`
- generic constraints
- error propagation
- async state
- storage
- ABI

thì Axiom sẽ rơi đúng vào vấn đề mà ta đang cố tránh.

Mục tiêu của BOOTSTRAP-093:

> **Compiler hiểu nhiều hơn programmer phải viết.**

Hay chính xác hơn:

> **Semantic explicitness không đồng nghĩa với syntactic verbosity.**

---

# 1. Nguyên tắc syntax chính

Axiom frozen 8 nguyên tắc:

```text
1. Explicit semantics
2. Minimal ceremony
3. Predictable inference
4. No hidden runtime behavior
5. No magical implicit conversion
6. Context-aware syntax sugar
7. AI-friendly structure
8. Same semantics with or without sugar
```

Ví dụ:

```text
let x = foo(a, b)?
```

không phải compiler "đoán".

Compiler biết chính xác:

```text
x : T
foo : (A, B) -> Result<T,E>
? : Result propagation
```

---

# 2. `let` và `var`

Giữ:

```text
let
var
```

Ý nghĩa:

```text
let x = 10     // binding immutable
var x = 10     // binding mutable
```

Không dùng:

```text
const
mutable
mut
```

cho local binding.

`const` đã có semantic compile-time khác.

---

# 3. Immutable by default

```text
let user = User(...)
```

không cho phép:

```text
user.name = ...
```

Nếu muốn thay đổi:

```text
var user = User(...)
```

Đây là một trong những cơ chế đơn giản nhất nhưng đem lại rất nhiều thông tin cho compiler.

---

# 4. Không bắt programmer viết ownership thường xuyên

Không:

```text
fn foo(x: owned T)
fn foo(x: borrow T)
fn foo(x: &'a T)
```

Core syntax:

```text
fn foo(x: T)
```

nghĩa là function nhận value theo ownership semantics thông thường.

Nếu muốn chỉ đọc:

```text
fn foo(x: view<T>)
```

Nếu muốn mutate caller:

```text
fn foo(x: mut_view<T>)
```

Đây là **semantic boundary** nên explicit.

---

# 5. Method syntax vẫn cực ngắn

Định nghĩa:

```text
fn length(self: Vec2) -> f32 {
    ...
}
```

gọi:

```text
v.length()
```

Compiler hiểu:

```text
length(v)
```

Không cần class.

---

# 6. Receiver inference

Các trường hợp:

```text
fn length(self: Vec2)
fn normalize(self: mut_view<Vec2>)
fn clone(self: view<Vec2>)
```

được compiler phân biệt.

Programmer không cần:

```text
&self
&mut self
self
```

như một syntax system riêng.

---

# 7. Explicit view chỉ xuất hiện ở semantic boundary

Ví dụ:

```text
fn sum(a: view<i32>) -> i32
```

gọi:

```text
sum(array)
```

Compiler có thể tạo ephemeral view tự động.

Nhưng:

```text
let v = array
```

không tự biến thành view.

Nếu muốn lưu capability:

```text
let v = view(array)
```

Đây là quy tắc cực quan trọng:

> **Implicit conversion chỉ được phép khi nó không tạo lifetime/ownership ambiguity.**

---

# 8. `mut_view`

Ví dụ:

```text
fn fill(out: mut_view<i32>) {
    for i in 0..out.len {
        out[i] = 0
    }
}
```

Gọi:

```text
fill(buffer)
```

không cần:

```text
&mut buffer
```

Compiler tạo mutable capability tạm thời.

Nếu programmer muốn giữ capability:

```text
let out = mut_view(buffer)
```

---

# 9. Không có `&` làm reference syntax

Axiom tránh:

```text
&x
&mut x
```

vì `&` dễ bị hiểu thành:

```text
address
reference
borrow
```

Thay vào đó:

```text
view(x)
mut_view(x)
address_of(x)
```

Ba semantics khác nhau, ba syntax khác nhau.

---

# 10. Pointer syntax chỉ ở system code

```text
let p: *mut Node
```

và:

```text
*p
```

chỉ hợp lệ trong unsafe/system context.

Application code chủ yếu dùng:

```text
x.field
x[index]
view(x)
mut_view(x)
```

---

# 11. Không có `new`

Không:

```text
new Foo(...)
```

Core.

Object/resource allocation đến từ type/API:

```text
Box.new(...)
Vec.new(...)
String.new(...)
DeviceBuffer.new(...)
```

Điều này khiến allocation semantic thuộc về abstraction cụ thể.

---

# 12. Constructor không phải language primitive

Axiom không cần:

```text
constructor
destructor
```

đặc biệt.

Chỉ cần function:

```text
fn new(...) -> Self
```

Ví dụ:

```text
impl User {
    fn new(name: String) -> Self {
        ...
    }
}
```

Gọi:

```text
let user = User.new(name)
```

hoặc:

```text
let user = User::new(name)
```

### Quyết định syntax

Axiom dùng:

```text
Type::function()
```

cho associated/static functions.

Method:

```text
value.function()
```

Ví dụ:

```text
let x = Vec2::new(1, 2)
x.length()
```

---

# 13. Associated functions không cần class

```text
struct Vec2 {
    x: f32,
    y: f32
}

impl Vec2 {
    fn new(x: f32, y: f32) -> Self {
        Vec2 { x, y }
    }
}
```

`impl` chỉ gom behavior.

Không tạo runtime object/class metadata.

---

# 14. Field syntax đơn giản

```text
user.name
player.position.x
mesh.vertices[i]
```

Compiler resolve:

```text
field identity
projection
capability
layout
```

nhưng programmer chỉ thấy field access.

---

# 15. Struct literal

```text
let p = Point {
    x: 10,
    y: 20
}
```

Nếu tất cả field đã rõ, có thể:

```text
let p = Point { 10, 20 }
```

nhưng **không nên cho phép positional struct literal mặc định** nếu field order không phải semantic contract.

Do đó:

> Named field initialization là canonical syntax.

---

# 16. Update syntax

Có thể hỗ trợ:

```text
let b = User {
    name: "Bob",
    ..a
}
```

Semantics:

- copy/move field theo ownership;
- không implicit clone.

Nếu `a` chứa non-Copy field:

```text
..a
```

có thể Move field đó.

Compiler xử lý partial move.

---

# 17. Pattern matching

Canonical:

```text
match value {
    Some(x) => ...
    None => ...
}
```

Không thêm quá nhiều pattern syntax ở Core v1.

Nhưng destructuring:

```text
match point {
    Point { x, y } => ...
}
```

được hỗ trợ.

---

# 18. `if let`

```text
if let Some(user) = find_user(id) {
    ...
}
```

là syntax sugar cho match một nhánh.

Tương tự:

```text
while let Some(item) = iterator.next() {
    ...
}
```

---

# 19. `for`

```text
for item in items {
    ...
}
```

Không có hidden allocation.

Compiler lower:

```text
IntoIterator
Iterator.next()
```

và optimizer có thể inline/fuse toàn bộ.

---

# 20. `?` là syntax quan trọng nhất cho Result

Axiom không muốn:

```text
match result {
    Ok(v) => v,
    Err(e) => return Err(e)
}
```

lặp lại hàng trăm lần.

Do đó:

```text
let file = File.open(path)?
```

là canonical.

---

# 21. Optional chaining?

Không nên thêm hàng loạt syntax như:

```text
?.
?? 
```

ngay Core v1.

Vì `Option` đã có:

```text
map
and_then
unwrap_or
```

và `match`.

Tuy nhiên một **optional access operator** có thể xem xét ở syntax layer sau khi API thực tế chứng minh nhu cầu.

Không freeze nó vào Core hiện tại.

---

# 22. No null

Axiom:

```text
Option<T>
```

thay cho:

```text
T?
null
```

Điều này giữ type system sạch.

---

# 23. Generic syntax

Canonical:

```text
fn max<T: Ord>(a: T, b: T) -> T
```

và:

```text
struct Vec<T> {
    ...
}
```

Đây là syntax quen thuộc, AI cũng dễ sinh.

---

# 24. Multiple constraints

```text
fn process<T: Read + Write + Send>(x: T) {
    ...
}
```

Không cần:

```text
where T: ...
```

cho trường hợp đơn giản.

`where` có thể được hỗ trợ khi constraint dài:

```text
fn process<T>(x: T)
where
    T: Read + Write,
    T: Send
{
}
```

Nhưng đây là formatting alternative, không thay đổi semantics.

---

# 25. Generic type inference

```text
let x = Vec::new()
```

compiler phải suy luận nếu context đủ mạnh.

Ví dụ:

```text
let x: Vec<i32> = Vec::new()
```

Nếu không đủ information:

```text
Vec::new()
```

→ diagnostic rõ ràng:

```text
cannot infer generic parameter T
```

Không đoán tùy tiện.

---

# 26. Explicit generic arguments

Khi cần:

```text
parse::<User>(data)
```

hoặc Axiom có thể dùng:

```text
parse<User>(data)
```

### Quyết định

Dùng:

```text
foo::<T>()
```

để tránh ambiguity giữa:

```text
foo<T>
```

và comparison/operator syntax.

---

# 27. Trait implementation

Canonical:

```text
impl Display for User {
    fn display(self: view<User>, out: mut_view<String>) {
        ...
    }
}
```

Không có:

```text
implements
extends
inherits
```

---

# 28. Method resolution vẫn không tạo dynamic dispatch

```text
user.display()
```

compiler resolve:

```text
inherent method
trait method
extension method
```

sau đó static dispatch mặc định.

Dynamic dispatch phải explicit.

---

# 29. Dynamic dispatch

```text
let x: dyn Display = ...
```

là explicit semantic request.

Compiler có thể tạo:

```text
data pointer
vtable
metadata
```

nhưng chỉ khi cần.

Không tự biến mọi trait thành virtual dispatch.

---

# 30. No `virtual`

Không:

```text
virtual fn
override fn
```

trong Core v1.

Override trait default method chỉ đơn giản:

```text
impl Display for User {
    fn display(...) {
        ...
    }
}
```

---

# 31. Extension methods

Ví dụ library:

```text
fn is_empty(self: view<String>) -> bool
```

Import:

```text
import text.is_empty
```

Sau đó:

```text
name.is_empty()
```

Extension method không cần:

```text
extend class
```

---

# 32. Ambiguous method resolution

Nếu:

```text
TraitA.foo(x)
TraitB.foo(x)
```

đều applicable:

```text
x.foo()
```

→ compile error.

Programmer phải disambiguate:

```text
TraitA::foo(x)
```

Không compiler tự chọn theo import order.

---

# 33. Closure syntax

Giữ syntax đơn giản:

```text
let f = |x| x * 2
```

Multi-line:

```text
let f = |x| {
    let y = x * 2
    y + 1
}
```

Capture semantics compiler inference.

---

# 34. Force move capture

Khi cần:

```text
let f = move |x| {
    use(data, x)
}
```

`move` chỉ có ý nghĩa capture ownership.

Không cần:

```text
'a
```

---

# 35. Async syntax

```text
async fn load() -> Result<Data, Error> {
    let data = read().await?
    Ok(data)
}
```

Đây là syntax quen thuộc nhưng semantic model vẫn:

```text
Future
state machine
suspension point
```

---

# 36. Spawn

Không làm:

```text
async fn
```

tự động chạy.

Phải:

```text
let task = spawn(load())
```

hoặc executor-specific API.

Điều này giữ:

> async ≠ thread ≠ execution.

---

# 37. Parallel syntax

Không thêm quá nhiều Core keyword.

Thay vì:

```text
parallel for
```

Core có thể dùng library:

```text
parallel_for(items, |item| {
    ...
})
```

hoặc:

```text
items.par_iter().for_each(...)
```

Compiler nhận diện parallel abstraction để tối ưu nếu phù hợp.

---

# 38. GPU syntax

Giữ:

```text
@kernel
fn add(...) {
}
```

và launch ở library/system layer:

```text
gpu.launch(add, ...)
```

Không tạo:

```text
__global__
__device__
__host__
```

nhiều dialect như CUDA.

---

# 39. Comptime syntax

Canonical:

```text
const MAX = 1024
```

và:

```text
comptime {
    ...
}
```

hoặc:

```text
comptime fn generate(...) -> ... {
}
```

Không có macro language riêng.

---

# 40. Attributes

```text
@repr(C)
struct Foo { ... }

@export("foo")
fn foo(...) { ... }

@kernel
fn kernel(...) { ... }
```

Attribute phải có registry/compiler meaning.

Không biến attributes thành một ngôn ngữ thứ hai.

---

# 41. Error syntax

Không:

```text
try {
}
catch {
}
```

Canonical:

```text
fn foo() -> Result<T, Error> {
    let x = operation()?
    Ok(x)
}
```

Panic:

```text
panic("invalid state")
```

Assert:

```text
assert(condition)
```

---

# 42. Assertions

Nên có ba mức:

```text
assert(condition)
debug_assert(condition)
unreachable()
```

`assert` semantic runtime check.

`debug_assert` profile-dependent.

`unreachable` nói với compiler:

> Control flow này không hợp lệ theo program invariant.

Nếu thực tế reached → panic/trap theo profile.

---

# 43. `defer` không cần

Axiom đã có deterministic Drop.

Do đó không thêm:

```text
defer
finally
```

cho resource cleanup.

Nếu cần scope-local action không phải resource:

```text
ScopeGuard
```

có thể là library abstraction.

---

# 44. Named arguments

Không cần Core v1.

```text
foo(
    timeout: 10,
    retries: 3
)
```

có thể gây ambiguity với field labels/patterns.

Nếu sau này cần, thêm ở syntax layer.

Không phải semantic requirement.

---

# 45. Default arguments

Không có Core v1.

Dùng:

```text
fn foo(x: Config)
```

với:

```text
Config.default()
```

hoặc overload-like helper functions.

Tránh hidden API ambiguity.

---

# 46. Operator overload

Operators là trait-based:

```text
a + b
```

→ trait resolution.

Ví dụ:

```text
impl Add for Vec2 {
    ...
}
```

Không tạo magic operator semantics riêng cho từng type.

Các operator control-flow:

```text
&&
||
?
```

có semantics riêng.

---

# 47. No implicit conversions

Đây là một trong những quyết định quan trọng nhất.

Không:

```text
i32 → i64
u32 → i64
float → int
```

một cách ngầm định nếu có risk.

Viết:

```text
x as i64
```

hoặc API conversion phù hợp.

Điều này giúp:

- compiler deterministic;
- AI ít đoán;
- overload resolution đơn giản;
- numeric bugs giảm.

---

# 48. Literal inference

Axiom vẫn cho phép:

```text
let x: i32 = 10
```

Compiler biết literal `10` có type context `i32`.

Nhưng:

```text
let x = 10
```

phải có default integer type deterministic.

Ví dụ frozen:

```text
integer literal default → i32
floating literal default → f64
```

nếu không có context.

---

# 49. Semicolon

Để syntax dễ parse và AI dễ generate:

> **Axiom dùng semicolon để kết thúc statement.**

Ví dụ:

```text
let x = 10;
let y = x + 1;
```

Expression cuối block có thể không cần `;`:

```text
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Điều này giữ expression-oriented programming mà không làm parser mơ hồ.

---

# 50. Blocks là expressions

```text
let x = {
    let a = 10;
    let b = 20;
    a + b
};
```

`if`:

```text
let x = if condition {
    10
} else {
    20
};
```

`match`:

```text
let x = match value {
    Some(v) => v,
    None => 0
};
```

---

# 51. Không có truthiness

Không:

```text
if x { ... }
```

nếu `x` không phải bool.

Phải:

```text
if x != 0 { ... }
```

hoặc:

```text
if !x.is_empty() { ... }
```

Điều này rất tốt cho compiler và AI.

---

# 52. Assignment không phải expression

Axiom nên giữ:

```text
x = value;
```

là statement.

Không:

```text
if (x = foo()) { ... }
```

Điều này loại bỏ một lớp bug C-style.

---

# 53. Equality rõ ràng

```text
==
!=
```

là semantic equality.

Nếu cần bitwise:

```text
bit_eq()
```

hoặc explicit bit representation API.

Đặc biệt floating-point:

```text
NaN
-0
```

không được lẫn với bytewise equality.

---

# 54. String syntax

```text
let name = "Axiom";
```

là string literal UTF-8.

Không tự động biến thành heap `String`.

Context có thể:

```text
Str
String
```

và compiler/API thực hiện semantics phù hợp.

Nếu cần owned:

```text
let name = String.from("Axiom");
```

hoặc literal coercion vào expected `String` nếu semantics không gây hidden surprising cost.

---

# 55. Không overloading syntax bằng magic

Ví dụ không nên có:

```text
@
$
#
%%
??
!!!
```

cho mọi tính năng.

Axiom ưu tiên:

```text
fn
struct
enum
trait
impl
let
var
if
match
for
loop
async
await
comptime
unsafe
view
mut_view
```

và attributes có namespace rõ.

---

# 56. AI-Friendly Syntax

Đây là một mục tiêu riêng của Axiom.

Code phải dễ phân tích theo AST.

Ví dụ:

```text
fn process(
    input: view<Data>,
    output: mut_view<Data>
) -> Result<(), ProcessError>
```

Một AI có thể suy ra ngay:

```text
input  = read-only
output = mutable capability
return = recoverable failure
```

Không cần suy luận:

```text
&mut
lifetime
trait bounds hidden elsewhere
exception specification
```

---

# 57. Semantic Surface vs Syntax Surface

Axiom có hai tầng:

```text
Syntax Surface
────────────────────
fn
struct
let
var
view
mut_view
Result
Option
async
await
...

Semantic Surface
────────────────────
ownership
provenance
regions
aliasing
liveness
escape
Send
Share
Drop
storage
ABI
effects
...
```

Compiler thực hiện mapping:

```text
Syntax
  ↓
AST
  ↓
HIR
  ↓
Semantic elaboration
```

Programmer chủ yếu làm việc với Syntax Surface.

Compiler làm việc với Semantic Surface.

---

# 58. Explicitness Boundary

Một nguyên tắc mới được freeze:

> **Chỉ bắt programmer viết explicit khi việc implicit có thể thay đổi ownership, lifetime, aliasing, dispatch hoặc observable runtime behavior.**

Ví dụ:

```text
sum(array)
```

→ implicit ephemeral view: OK.

Nhưng:

```text
let x = view(array)
```

→ explicit.

Vì capability trở thành stored value.

Tương tự:

```text
foo(x)
```

→ static dispatch.

Nhưng:

```text
let x: dyn Trait
```

→ explicit dynamic dispatch.

---

# 59. Syntax Sugar phải có canonical expansion

Mọi sugar trong Axiom phải có expansion xác định.

Ví dụ:

```text
x.foo(a)
```

canonical semantic:

```text
foo(x, a)
```

`?`:

```text
match result {
    Ok(v) => v,
    Err(e) => return Err(convert(e))
}
```

`for`:

```text
iterator protocol
```

`async/await`:

```text
Future/state machine
```

Điều này cực kỳ quan trọng cho compiler và AI.

---

# 60. Không có "magic fallback"

Nếu compiler không resolve được:

```text
x.foo()
```

không thử:

```text
reflection
dynamic dispatch
runtime lookup
global method
```

để cứu chương trình.

Resolution deterministic:

```text
inherent
→ trait
→ imported extension
→ generic extension
→ error
```

---

# 61. Diagnostics phải nói semantic reason

Không chỉ:

```text
type mismatch
```

mà:

```text
expected mut_view<T>
but argument is already borrowed by capability C17
```

hoặc:

```text
cannot move `buffer`
because capability C4 is still live
```

Điều này giúp programmer sửa lỗi mà không cần hiểu toàn bộ compiler internals.

---

# 62. Diagnostics có machine representation

Ví dụ:

```text
{
    "code": "ACAP-204",
    "kind": "capability_conflict",
    "operation": "mutable_access",
    "region": "buffer[0..1024]",
    "conflict": "C17",
    "reason": "live_read_capability"
}
```

CLI hiển thị đẹp.

IDE/AI nhận JSON.

---

# 63. Không có syntax để "đánh lừa compiler"

Không cho:

```text
unsafe {
    // magically disables all checking
}
```

Unsafe chỉ là boundary.

Nếu muốn:

```text
assume(...)
```

phải thuộc unsafe/system semantics và tạo trusted precondition cụ thể.

Không có:

```text
disable_borrow_checker
disable_lifetime
disable_type_check
```

---

# 64. Syntax cho unsafe

Canonical:

```text
unsafe {
    ...
}
```

hoặc:

```text
unsafe fn read_raw(...)
```

Unsafe càng nhỏ càng tốt:

```text
let value = unsafe {
    *ptr
};
```

thay vì:

```text
unsafe {
    // entire application
}
```

---

# 65. Import syntax

Canonical:

```text
import std.io.File;
import std.collections.Vec;
```

Selective:

```text
import std.io.{File, Socket};
```

Alias:

```text
import graphics.Texture as Tex;
```

Export:

```text
pub struct User { ... }
```

`pub` không đồng nghĩa binary export.

---

# 66. Module API

Một module public:

```text
pub fn load(...)
pub struct Config
```

nhưng native symbol chỉ xuất hiện nếu:

```text
@export("axiom_load")
```

Hai concept hoàn toàn tách biệt.

---

# 67. Package path

Code:

```text
import graphics.texture;
```

không chứa:

```text
../../../src/
```

Package manager giải quyết package identity.

Compiler nhận semantic module graph.

---

# 68. API ergonomics cho ownership

Một API tốt:

```text
fn parse(data: view<u8>) -> Result<Document, ParseError>
```

Gọi:

```text
let doc = parse(bytes)?;
```

Một API không tốt:

```text
fn parse(
    ptr: *const u8,
    len: usize,
    lifetime: ...
)
```

Raw pointer chỉ dành cho system boundary.

---

# 69. API ergonomics cho mutation

Tốt:

```text
fn normalize(x: mut_view<Vec2>)
```

Gọi:

```text
normalize(vector);
```

Không cần:

```text
normalize(&mut vector);
```

Compiler vẫn kiểm tra exclusive mutation.

---

# 70. API ergonomics cho stable identity

Không:

```text
fn find(ptr: *const Entity)
```

App-level:

```text
fn find(id: EntityId) -> Option<view<Entity>>
```

Hoặc nếu cần mutation:

```text
fn get_mut(id: EntityId) -> Option<mut_view<Entity>>
```

Compiler + container đảm bảo capability.

---

# 71. API ergonomics cho resource

Tốt:

```text
let file = File.open(path)?;
let data = file.read_all()?;
```

Không cần:

```text
handle = os_open(...)
resource = wrap_handle(...)
```

trong application code.

System wrapper chứa toàn bộ complexity.

---

# 72. API ergonomics cho async

```text
async fn load_asset(id: AssetId) -> Result<Asset, Error> {
    let bytes = load_bytes(id).await?;
    decode(bytes)?
}
```

Đọc gần như synchronous code.

Nhưng compiler vẫn tạo:

```text
Future
state machine
suspension points
ownership states
```

---

# 73. API ergonomics cho GPU

```text
@kernel
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
) {
    ...
}
```

Host:

```text
let event = gpu.launch(add, a, b, out)?;
event.wait()?;
```

Không cần programmer quản lý:

```text
CUDA context
raw device pointer
kernel ABI
stream lifetime
```

trừ system-level code.

---

# 74. API ergonomics cho comptime

Ví dụ:

```text
const SIZE = 1024;

comptime {
    assert(size_of<MyStruct>() <= SIZE);
}
```

Không cần macro DSL.

---

# 75. Syntax không quyết định performance

Ví dụ:

```text
array.map(|x| x * 2)
```

không có nghĩa:

```text
allocate closure
allocate iterator
allocate array
```

Compiler có thể:

```text
inline
fuse
scalarize
vectorize
```

Syntax mô tả abstraction.

Optimizer quyết định representation.

---

# 76. Nhưng syntax không được che giấu semantic cost

Nếu API:

```text
clone()
```

thì cost có thể lớn.

Không biến:

```text
x.clone()
```

thành implicit copy.

Axiom phân biệt:

```text
Copy
Clone
Move
```

rất rõ.

---

# 77. Một ví dụ hoàn chỉnh

```text
struct User {
    id: u64,
    name: String,
}

impl User {
    fn rename(self: mut_view<User>, name: String) {
        self.name = name;
    }
}

fn load_user(id: u64) -> Result<User, Error> {
    let file = File.open("users.db")?;
    let data = file.read_all()?;

    parse_user(data)
}

async fn process(id: u64) -> Result<(), Error> {
    let user = load_user(id)?;

    println(user.name);

    Ok(())
}
```

Programmer không phải viết:

```text
lifetime
borrow
reference
allocator
exception
future state
thread safety
drop glue
```

nhưng compiler vẫn biết tất cả.

---

# 78. Khi cần low-level

System programmer vẫn có quyền:

```text
unsafe fn write_register(
    addr: usize,
    value: u32
) {
    let p = address_to_ptr<mut u32>(addr);
    *p = value;
}
```

Đây là nơi complexity xuất hiện vì **machine semantics thực sự cần nó**.

Không nên cố giấu complexity này bằng magic.

---

# 79. Hai tầng lập trình

Axiom vì vậy có thể có:

```text
Application Axiom
────────────────────────
struct
trait
view
Result
Option
Handle
async
comptime
GPU
collections

System Axiom
────────────────────────
unsafe
raw pointer
ABI
repr
volatile
atomic
syscall
interrupt
inline asm
device memory
```

Cùng một ngôn ngữ.

Không tạo "Axiom Safe" và "Axiom Low-level" thành hai ngôn ngữ riêng.

---

# 80. Nguyên tắc thiết kế API cho Axiom

Mọi API Core/Standard Library nên ưu tiên thứ tự:

```text
1. Value semantics
2. Ownership semantics
3. Capability semantics
4. Logical identity
5. Explicit resource state
6. Explicit synchronization
7. Explicit unsafe boundary
8. Representation only when necessary
```

Không expose machine detail nếu semantic abstraction đã đủ.

---

# 81. Frozen invariants

## Syntax

**ASYNTAX-20 — Syntax Must Have Deterministic Semantic Meaning**

**ASYNTAX-21 — Syntax Sugar Must Have A Canonical Semantic Expansion**

**ASYNTAX-22 — Syntax Must Not Introduce Hidden Runtime Semantics**

**ASYNTAX-23 — Blocks Are Expressions**

**ASYNTAX-24 — Assignment Is Not An Expression**

**ASYNTAX-25 — Conditions Require Boolean Values**

**ASYNTAX-26 — Statements Use Deterministic Termination Rules**

---

## Ownership / Capability

**ASYNTAX-27 — Ownership Is Not Expressed Through General Lifetime Syntax**

**ASYNTAX-28 — Read Access Uses `view<T>`**

**ASYNTAX-29 — Mutable Access Uses `mut_view<T>`**

**ASYNTAX-30 — Ephemeral Owner-to-View Conversion May Be Implicit**

**ASYNTAX-31 — Stored Capability Creation Is Explicit**

**ASYNTAX-32 — Raw Pointer Syntax Is Restricted To Unsafe/System Contexts**

**ASYNTAX-33 — Address-Taking Is Distinct From View Creation**

---

## Methods / Traits

**ASYNTAX-34 — Methods Are Function Syntax Sugar**

**ASYNTAX-35 — No Class Syntax Exists In Core**

**ASYNTAX-36 — Trait Dispatch Is Static By Default**

**ASYNTAX-37 — Dynamic Dispatch Is Explicit**

**ASYNTAX-38 — Method Resolution Is Deterministic**

**ASYNTAX-39 — Ambiguous Method Resolution Is A Compile Error**

**ASYNTAX-40 — Trait Default Methods May Be Replaced By Concrete Implementations**

---

## Errors

**ASYNTAX-41 — Recoverable Failure Uses Result**

**ASYNTAX-42 — Absence Uses Option**

**ASYNTAX-43 — `?` Is Explicit Error-Propagation Syntax**

**ASYNTAX-44 — Panic Is Not A General Error-Propagation Mechanism**

**ASYNTAX-45 — Exceptions Are Not Required By Core Syntax**

---

## Async / Comptime

**ASYNTAX-46 — Async Does Not Imply Execution**

**ASYNTAX-47 — Await Is The Suspension Syntax**

**ASYNTAX-48 — Spawn Is Explicit**

**ASYNTAX-49 — Comptime Is Explicit**

**ASYNTAX-50 — Comptime Is Not A Separate Programming Language**

---

## Conversion / Types

**ASYNTAX-51 — Arbitrary Implicit Numeric Conversion Is Forbidden**

**ASYNTAX-52 — Explicit Conversion Has Explicit Syntax**

**ASYNTAX-53 — Bitcast Is Distinct From Numeric Conversion**

**ASYNTAX-54 — Null Is Not A Safe Core Value**

**ASYNTAX-55 — Generic Inference Must Be Deterministic**

---

## Performance

**ASYNTAX-56 — Syntax Sugar Does Not Require Runtime Allocation**

**ASYNTAX-57 — Abstraction Syntax Does Not Imply Dynamic Dispatch**

**ASYNTAX-58 — Abstraction Syntax Does Not Imply Heap Allocation**

**ASYNTAX-59 — Closure Syntax Does Not Imply Heap Allocation**

**ASYNTAX-60 — Iterator Syntax Does Not Imply Allocation**

**ASYNTAX-61 — Async Syntax Does Not Imply Heap Allocation**

**ASYNTAX-62 — Compiler May Erase Zero-Cost Abstractions**

---

## AI / Tooling

**ASYNTAX-63 — Syntax Must Map Cleanly To Structured AST**

**ASYNTAX-64 — Semantic Diagnostics Must Identify The Actual Constraint**

**ASYNTAX-65 — Compiler Diagnostics Have Stable Machine-Readable Codes**

**ASYNTAX-66 — Syntax Resolution Must Not Depend On Heuristic Guessing**

**ASYNTAX-67 — Compiler Must Not Use Runtime Reflection To Resolve Ordinary Syntax**

---

## Architecture

**ASYNTAX-68 — Explicitness Is Required At Semantic Boundaries**

**ASYNTAX-69 — Implicitness Is Allowed When It Cannot Change Ownership Or Lifetime Meaning**

**ASYNTAX-70 — Compiler Complexity Must Not Become Programmer Syntax Complexity**

**ASYNTAX-71 — One Semantic Question Should Have One Primary Syntax Mechanism**

**ASYNTAX-72 — Application Syntax And System Syntax Are Layers Of The Same Language**

**ASYNTAX-73 — Unsafe Syntax Must Be Localizable**

**ASYNTAX-74 — API Ergonomics Must Not Weaken Semantic Guarantees**

**ASYNTAX-75 — Syntax Evolution Must Preserve Existing Semantic Meaning**

---

# 82. Axiom syntax hiện tại

Sau BOOTSTRAP-093, phần Core syntax đã khá rõ:

```text
Declarations
    fn
    struct
    enum
    trait
    impl
    type
    const

Bindings
    let
    var

Control
    if
    match
    loop
    while
    for
    break
    continue
    return

Ownership / Access
    view
    mut_view
    move semantics
    unsafe
    *

Errors
    Result
    Option
    ?
    panic
    assert

Async
    async
    await

Compile-time
    comptime
    @cfg
    @derive

ABI/System
    @repr
    @export
    extern
    @kernel
```

Và quan trọng hơn, **không cần bổ sung hàng chục keyword để expose compiler internals**.

---

# 83. Một nguyên tắc lớn được xác lập

Axiom đang đi theo hướng khá khác Rust/C++:

### C++

```text
language feature
    ↓
runtime/compiler complexity
    ↓
programmer complexity
```

### Rust

```text
strong semantic guarantees
    ↓
powerful compiler
    ↓
significant programmer-facing lifetime/trait syntax
```

### Axiom

```text
strong semantic guarantees
          ↓
      powerful compiler
          ↓
   semantic inference
          ↓
simple explicit boundaries
          ↓
      concise code
```

Đây có thể trở thành một trong những **định hướng cốt lõi nhất của Axiom**.

---

## Bước tiếp theo

Sau khi syntax/API đã được chốt, một vấn đề còn rất lớn trước khi đi vào các thư viện cấp cao:

# **BOOTSTRAP-094 — Axiom Standard Library Architecture & Prelude**

Ở đó ta sẽ quyết định chính xác **những gì thuộc Core Library, Standard Library và System Library**, API naming/convention, `Vec/String/HashMap/Arc/Mutex/File/Socket/Future/GPU` nên có interface thế nào, và đặc biệt:

> **Làm sao standard library của Axiom vừa cực mạnh như Rust/C++ ecosystem, vừa không kéo theo một runtime khổng lồ vào mọi executable.**