Tiếp tục.

# BOOTSTRAP-066 — Axiom Idiomatic Programming Model & Standard Syntax Patterns

064–065 đã xác định **ngôn ngữ cho phép viết gì**. 066 xác định **người dùng nên viết Axiom như thế nào**.

Điểm này rất quan trọng. Một ngôn ngữ có grammar đẹp nhưng idiom xấu vẫn sẽ trở nên khó dùng. Đặc biệt Axiom hướng tới AI-generated code, nên cần có các pattern có tính **canonical**: cùng một vấn đề → thường có một cách viết tự nhiên.

---

# 1. Nguyên tắc idiom của Axiom

Tôi đề xuất 8 nguyên tắc:

```text
1. Value first
2. Ownership only when semantically necessary
3. view/mut_view at access boundaries
4. Struct + function instead of class
5. Result/Option instead of exceptions/null
6. Generic + trait instead of inheritance
7. Async as control flow, not thread
8. Explicit expensive operations
```

Và một nguyên tắc lớn hơn:

> **Code bình thường phải nhìn giống code bình thường; chỉ những ranh giới quan trọng mới cần syntax đặc biệt.**

---

# 2. Khởi tạo value

Struct:

```axiom
let p = Point {
    x: 10
    y: 20
}
```

Không cần:

```text
new Point(...)
```

Không có `new` trong Core.

---

# 3. Constructor không phải language primitive

Nếu cần logic khởi tạo:

```axiom
impl User {
    fn create(id: u64, name: Str) -> User {
        User {
            id,
            name: String(name)
        }
    }
}
```

Gọi:

```axiom
let user = User.create(10, "Alice")
```

`create` chỉ là function/method.

Điều này giữ compiler đơn giản và không tạo “constructor magic”.

---

# 4. Initialization trực tiếp được ưu tiên

Nếu không có invariant đặc biệt:

```axiom
let p = Point {
    x: 10
    y: 20
}
```

không cần:

```axiom
let p = Point.new(10, 20)
```

---

# 5. Builder không phải Core pattern bắt buộc

Nếu object có nhiều tùy chọn:

```axiom
var config = Config {
    host: "localhost"
    port: 8080
    workers: 4
}
```

Thay vì ép mọi API phải có:

```text
ConfigBuilder
```

Builder chỉ là library design pattern.

---

# 6. Method = function

Axiom tiếp tục giữ nguyên triết lý:

```axiom
fn length(self: view<Vec2>) -> f32
```

có thể gọi:

```axiom
v.length()
```

Nhưng compiler semantic identity vẫn là function.

---

# 7. Không phân biệt “method thật” và “method giả”

Extension:

```axiom
fn is_empty(self: view<Vec<T>>) -> bool {
    self.length() == 0
}
```

Sau khi import:

```axiom
items.is_empty()
```

Compiler resolution:

```text
inherent
→ trait
→ extension
→ generic extension
```

đã freeze.

---

# 8. Không cần `this`

Axiom dùng:

```axiom
self
```

nhất quán với method receiver.

---

# 9. Receiver mặc định

Tôi đề xuất idiom:

```axiom
fn length(self) -> usize
```

được hiểu là read-only receiver:

```text
view<Self>
```

Khi cần mutation:

```axiom
fn clear(self: mut_view<Self>)
```

Khi consume:

```axiom
fn into_bytes(self: Self) -> Bytes
```

Như vậy ba semantic mode rất rõ:

```text
self              → read
mut_view<Self>    → mutate
Self              → consume
```

---

# 10. Có nên dùng `mut self`?

Sau khi xem xét lại toàn bộ syntax, tôi **không khuyến nghị** thêm:

```axiom
fn foo(mut self)
```

vì Axiom đã có:

```axiom
mut_view<Self>
```

Một semantic mechanism nên có một syntax chính.

Do đó:

```axiom
fn clear(self: mut_view<Self>)
```

là canonical.

---

# 11. Ownership transfer

Không cần keyword `move` trong function call thông thường.

```axiom
let a = create_buffer()
consume(a)
```

Compiler biết `a` bị move nếu parameter nhận ownership.

Sau đó:

```axiom
use(a)
```

→ compile error.

Điều này là ownership semantics, không phải syntax ceremony.

---

# 12. Explicit clone

Nếu muốn duplicate resource/value:

```axiom
let b = a.clone()
```

Không có implicit clone khi move không hợp lệ.

Đây là một điểm rất quan trọng:

```text
move ≠ copy ≠ clone
```

---

# 13. Copy

Copy type:

```axiom
let a = 10
let b = a
```

`i32` là Copy.

Nhưng:

```axiom
let a = String("hello")
let b = a
```

là move nếu String không Copy.

---

# 14. Explicit early drop

```axiom
drop(file)
```

Dùng khi muốn kết thúc resource lifetime sớm.

Không dùng:

```text
delete(file)
free(file)
```

---

# 15. Error handling canonical

Axiom không có exception.

Pattern chuẩn:

```axiom
fn load(path: Str) -> Result<Data, IoError> {
    let file = File.open(path)?
    let bytes = file.read_all()?
    parse(bytes)?
}
```

`?` trở thành một trong những syntax quan trọng nhất của Axiom.

---

# 16. Transform error

Nếu cần thêm context:

```axiom
let file = File.open(path)
    .map_error(|e| LoadError.Io(e))?
```

Không cần `try/catch`.

---

# 17. Match Result

Khi cần xử lý từng trường hợp:

```axiom
match load(path) {
    Ok(data) => process(data)
    Err(error) => report(error)
}
```

---

# 18. Option

Không có null-check:

```axiom
if user.name != null
```

Thay bằng:

```axiom
match user.name {
    Some(name) => print(name)
    None => print("unknown")
}
```

hoặc:

```axiom
if let Some(name) = user.name {
    print(name)
}
```

---

# 19. Option chaining

Không nên thêm một hệ thống optional chaining riêng vào Core v1.

Thay vào đó:

```axiom
let name = user.profile
    .and_then(|p| p.name)
```

Library `Option` đảm nhiệm.

---

# 20. Views

Đây là một trong những idiom đặc trưng nhất của Axiom.

Read:

```axiom
fn checksum(data: view<Bytes>) -> u64
```

Call:

```axiom
checksum(data)
```

Không cần:

```text
&data
```

---

# 21. Mutable view

```axiom
fn normalize(data: mut_view<Buffer>) {
    ...
}
```

Call:

```axiom
normalize(buffer)
```

Compiler tạo ephemeral mutable capability.

---

# 22. Persistent view

Khi thực sự cần giữ view:

```axiom
let header = view(packet.header)
```

Đây là nơi Axiom yêu cầu explicitness.

---

# 23. Không lạm dụng `view`

Sai idiom:

```axiom
fn foo(x: view<i32>) -> i32
```

nếu `i32` đơn giản và việc truyền value hiệu quả hơn.

Nên:

```axiom
fn foo(x: i32) -> i32
```

Compiler tự truyền register.

`view` dành cho **semantic alias/access**, không phải optimization hint.

---

# 24. Slice/view của collection

```axiom
fn sum(values: view<[i32]>) -> i32
```

Tuy nhiên ở syntax type-level, fixed array và dynamic slice cần phân biệt.

Tôi đề xuất chuẩn hóa library API thành:

```axiom
view<i32>
```

cho contiguous element region khi element type đã đủ xác định.

Ví dụ:

```axiom
fn sum(values: view<i32>) -> i32
```

Compiler/ABI representation có thể là:

```text
pointer + length
```

nhưng đây không phải source-level requirement.

---

# 25. Vì sao không `view<[T]>`?

`[T; N]` đã biểu thị fixed-size array.

`view<T>` biểu thị capability tới một region của T.

Do đó:

```text
[T; N]     = owning fixed array value
view<T>    = non-owning read region
```

đẹp và orthogonal hơn.

---

# 26. Collection ownership

Canonical:

```axiom
let values = Vec<i32>()
```

Nếu truyền vào function:

```axiom
process(values)
```

thì tùy signature:

```axiom
process(values)              // move
process(view(values))        // explicit stored/semantic view
```

hoặc ephemeral implicit view:

```axiom
fn process(values: view<i32>)
```

thì:

```axiom
process(values)
```

---

# 27. Iteration

Canonical:

```axiom
for item in items {
    process(item)
}
```

Không expose iterator internals trong code bình thường.

---

# 28. Mutable iteration

```axiom
for item in mut_view(items) {
    normalize(item)
}
```

hoặc library iterator có thể cung cấp mutable iteration abstraction.

Compiler verification vẫn phải đảm bảo không có conflicting mutable capabilities.

---

# 29. Không tạo syntax riêng cho ownership loop

Không cần:

```text
for &mut item
```

hay:

```text
for move item
```

trong Core.

Ownership được quyết định từ iteration semantics và element type.

---

# 30. Generics

Canonical:

```axiom
fn max<T: Ord>(a: T, b: T) -> T {
    if a > b { a } else { b }
}
```

Không cần verbose:

```text
where T implements Ord
```

trừ khi constraint phức tạp.

---

# 31. Trait usage

```axiom
trait Hash {
    fn hash(self) -> u64
}
```

Implementation:

```axiom
impl Hash for User {
    fn hash(self) -> u64 {
        ...
    }
}
```

---

# 32. Generic algorithm

```axiom
fn find<T: Eq>(items: view<T>, target: T) -> Option<usize> {
    for i in 0..items.length() {
        if items[i] == target {
            return Some(i)
        }
    }

    None
}
```

Một API như vậy có thể monomorphize hoàn toàn.

---

# 33. Dynamic polymorphism

Chỉ dùng khi thực sự cần runtime polymorphism:

```axiom
fn render(object: view<dyn Drawable>) {
    object.draw()
}
```

Không tự động biến generic thành dynamic dispatch.

---

# 34. Static polymorphism mặc định

```axiom
fn render<T: Drawable>(object: view<T>) {
    object.draw()
}
```

được ưu tiên khi compile-time specialization phù hợp.

---

# 35. Newtype

Dùng để ngăn nhầm lẫn semantic:

```axiom
struct UserId(u64)
struct ProductId(u64)
```

Hai loại này không interchangeable dù cùng physical representation có thể là `u64`.

---

# 36. Type alias

Dùng khi chỉ muốn đặt tên:

```axiom
type UserMap = Map<UserId, User>
```

Không tạo type identity mới.

---

# 37. Pattern matching

Canonical ADT:

```axiom
match result {
    Ok(value) => use(value)
    Err(error) => handle(error)
}
```

Không switch kiểu C làm abstraction chính.

---

# 38. `if let`

Dùng cho single interesting case:

```axiom
if let Some(user) = find_user(id) {
    show(user)
}
```

---

# 39. `match` cho nhiều trạng thái

```axiom
match state {
    Loading => ...
    Ready(data) => ...
    Failed(error) => ...
}
```

---

# 40. Struct pattern

```axiom
match point {
    Point { x: 0, y: 0 } => origin()
    Point { x, y } => show(x, y)
}
```

---

# 41. Destructuring

```axiom
let Point { x, y } = point
```

Ownership semantics áp dụng bình thường.

---

# 42. Loop control

```axiom
for item in items {
    if should_stop(item) {
        break
    }

    process(item)
}
```

Không cần exception/control-flow hack.

---

# 43. Labeled loop

```axiom
'search: for group in groups {
    for item in group {
        if found(item) {
            break 'search
        }
    }
}
```

---

# 44. Async

Canonical:

```axiom
async fn load() -> Result<Data, Error> {
    let response = request().await?
    let data = response.read().await?
    Ok(data)
}
```

Không spawn thread.

---

# 45. Sequential vs concurrent async

Sequential:

```axiom
let a = fetch_a().await
let b = fetch_b().await
```

Concurrent:

```axiom
let a = spawn(fetch_a())
let b = spawn(fetch_b())

let result_a = a.await?
let result_b = b.await?
```

Scheduler/executor thuộc library/runtime.

---

# 46. Structured concurrency

Canonical:

```axiom
scope {
    let a = spawn(task_a())
    let b = spawn(task_b())

    ...
}
```

Nếu standard library cung cấp structured task scope.

Không detach mặc định.

Detach phải explicit:

```axiom
detach(task)
```

---

# 47. Thread

Thread dùng khi cần execution domain riêng:

```axiom
let handle = thread.spawn(|| {
    worker()
})

handle.join()
```

Không coi thread là syntax primitive của language.

---

# 48. Channel

Ownership transfer:

```axiom
let channel = Channel<User>.bounded(64)

sender.send(user)?
```

`send` move `user`.

Nếu failed:

```axiom
Err(user)
```

theo semantics của channel API.

---

# 49. Shared state

Canonical:

```axiom
let state = Arc.new(Mutex.new(State()))
```

Không có implicit shared mutable state.

---

# 50. Atomic

```axiom
let counter = Atomic<u64>(0)

counter.fetch_add(1, AcqRel)
```

Atomic ordering explicit.

---

# 51. Lock

```axiom
{
    let guard = mutex.lock()
    guard.value += 1
}
```

Drop guard tự unlock.

Không cần:

```text
mutex.unlock()
```

cho normal RAII-style usage.

---

# 52. GPU

Kernel:

```axiom
@kernel
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
) {
    let i = kernel.index()
    out[i] = a[i] + b[i]
}
```

Launch:

```axiom
let event = gpu.launch(add, a, b, out)
event.await()?
```

Execution/storage domains vẫn được verifier kiểm tra.

---

# 53. Comptime

Canonical:

```axiom
const SIZE: usize = 1024
```

Khi cần computation:

```axiom
comptime {
    generate_tables()
}
```

Không tạo DSL riêng.

---

# 54. Reflection

Compile-time:

```axiom
comptime fn fields<T>() {
    ...
}
```

với compiler reflection APIs.

Không có:

```text
runtime.Type
```

trừ khi chương trình explicitly yêu cầu metadata.

---

# 55. FFI

Foreign declaration:

```axiom
extern "C" {
    fn puts(text: *const u8) -> i32
}
```

Nhưng application code nên bọc:

```axiom
fn print_c(text: Str) -> Result<(), Error> {
    ...
}
```

Raw pointer chỉ xuất hiện ở boundary.

---

# 56. Unsafe nên “mỏng”

Mục tiêu:

```axiom
fn safe_api(...) {
    ...
}
```

bên trong có thể có một boundary nhỏ:

```axiom
unsafe {
    ...
}
```

thay vì lan `unsafe` khắp application.

Ví dụ:

```axiom
fn read_u32(data: view<u8>) -> u32 {
    unsafe {
        ...
    }
}
```

sau đó phần còn lại safe.

---

# 57. Không dùng unsafe như optimization keyword

Không viết:

```text
unsafe
```

chỉ để bỏ bounds check.

Compiler có thể tự loại bounds check khi có proof.

Unsafe chỉ cần khi programmer thực sự vượt khỏi safe semantic guarantees.

---

# 58. Performance idiom

Axiom không yêu cầu programmer viết:

```text
inline
noalias
register
restrict
likely
```

cho các optimization bình thường.

Compiler tự dùng:

```text
ownership
capability
range analysis
escape analysis
type specialization
```

---

# 59. Explicit optimization hint

Nếu cần:

```axiom
@inline
fn tiny(...) { ... }
```

nhưng đây là hint/contract theo attribute semantics, không phải correctness mechanism.

---

# 60. Memory allocation

Application:

```axiom
let buffer = Buffer.new(4096)
```

Không:

```text
malloc
free
new
delete
```

trừ system/FFI layer.

---

# 61. Arena

Khi workload thực sự cần arena:

```axiom
let arena = Arena.new()

let a = arena.alloc(...)
let b = arena.alloc(...)
```

Arena là library abstraction.

Không đưa allocator parameter vào mọi generic collection.

---

# 62. Stable address

Nếu cần stable address:

```axiom
let object = StableBox.new(...)
```

hoặc một abstraction tương đương trong library.

Không coi:

```axiom
Box<T>
```

là mặc định stable-address storage.

---

# 63. Handle

Entity systems:

```axiom
let id = entities.create(entity)
```

sau đó:

```axiom
let entity = entities.get(id)
```

Handle là logical identity.

Không dùng raw pointer làm identity trong application code.

---

# 64. String philosophy

Ba khái niệm phải luôn phân biệt:

```text
Str      → borrowed text/view
String   → owned text
Bytes    → raw binary
```

Ví dụ API:

```axiom
fn parse(json: Str) -> Result<Value, ParseError>
```

Nếu cần giữ dữ liệu:

```axiom
let owned = String(json)
```

---

# 65. Không tự động convert Bytes ↔ String

Phải explicit:

```axiom
let text = bytes.to_utf8()?
```

và:

```axiom
let bytes = text.as_bytes()
```

UTF-8 validation không được bỏ qua.

---

# 66. File/resource

Canonical:

```axiom
fn read_config(path: Str) -> Result<Config, Error> {
    let file = File.open(path)?
    let text = file.read_to_string()?

    parse_config(text)
}
```

Drop xử lý resource cleanup.

Không cần:

```text
try
finally
```

---

# 67. Fallible cleanup

Nếu resource có thao tác cleanup có thể thất bại:

```axiom
file.close()?
```

trước khi Drop.

Drop không propagate recoverable error.

---

# 68. API design rule

Một API Axiom tốt nên ưu tiên:

```text
value → view → mut_view → ownership
```

chỉ khi semantics yêu cầu.

Không bắt caller cung cấp reference syntax cho mọi thứ.

---

# 69. AI-generated code guideline

Đây là điểm rất quan trọng với Axiom.

AI nên có canonical transformations:

```text
Need read-only access
→ view<T>

Need mutable access
→ mut_view<T>

Need ownership
→ T

Need optional value
→ Option<T>

Need recoverable failure
→ Result<T,E>

Need polymorphism
→ T: Trait

Need runtime polymorphism
→ dyn Trait

Need concurrency transfer
→ Send

Need concurrent shared access
→ Share + synchronization
```

Điều này giúp giảm “semantic guessing” của AI.

---

# 70. Anti-patterns mà compiler/tooling nên cảnh báo

Không nhất thiết reject, nhưng lint có thể cảnh báo:

```text
view<T> dùng cho scalar Copy nhỏ
Clone() không cần thiết
dyn Trait trong hot generic path
Arc<T> khi ownership độc quyền
unsafe quá rộng
raw pointer trong application layer
Box<T> khi value có thể inline
```

Đây là **lint/performance advice**, không phải language semantics.

---

# 71. Canonical application structure

Một package:

```text
app/
    axiom.toml
    src/
        main.ax
        model.ax
        service.ax
        storage.ax
```

`main.ax`:

```axiom
import app.service

fn main() {
    ...
}
```

Không ép mỗi declaration thành một file.

---

# 72. Module organization

Module nên tổ chức theo semantic responsibility:

```text
model
storage
network
render
```

không phải theo class hierarchy.

---

# 73. Public API

```axiom
pub struct User {
    pub id: UserId
    pub name: String
}
```

Nhưng native export:

```axiom
@export("user_create")
pub fn create_user(...) -> ...
```

Hai khái niệm tiếp tục độc lập.

---

# 74. Canonical naming

Compiler không enforce nhưng ecosystem convention:

```text
Type        → PascalCase
Function    → snake_case
Variable    → snake_case
Constant    → UPPER_SNAKE_CASE
Enum        → PascalCase
Variant     → PascalCase
Trait       → PascalCase
```

---

# 75. Canonical file naming

Khuyến nghị:

```text
snake_case.ax
```

nhưng module identity không phụ thuộc filesystem.

---

# 76. API philosophy

Axiom library nên ưu tiên:

```text
small functions
small structs
traits for behavior
generic algorithms
explicit ownership boundaries
```

thay vì:

```text
deep inheritance trees
large mutable objects
implicit global state
```

---

# 77. Một ví dụ “Axiom style”

```axiom
import std.fs
import std.io

struct Config {
    host: String
    port: u16
}

enum ConfigError {
    Io(IoError)
    Parse(ParseError)
}

impl Config {
    fn load(path: Str) -> Result<Config, ConfigError> {
        let file = File.open(path)
            .map_error(|e| ConfigError.Io(e))?

        let text = file.read_to_string()
            .map_error(|e| ConfigError.Io(e))?

        parse(text)
            .map_error(|e| ConfigError.Parse(e))
    }
}

fn main() {
    match Config.load("config.toml") {
        Ok(config) => {
            println(config.host)
            println(config.port)
        }

        Err(error) => {
            println(error)
        }
    }
}
```

Không có:

```text
class
new
delete
null
exception
try/catch
&mut
lifetime
virtual
override
```

nhưng vẫn có:

```text
RAII-like deterministic cleanup
ownership
error propagation
generic/trait system
safe memory
```

---

# 78. Đánh giá sau 066

Đến đây Axiom có một đặc điểm khá rõ:

```text
C/C++:
low-level power
        +
modern safety
        +
Rust-like ownership semantics
        +
Go-like simplicity
        +
functional ADT/pattern features
        +
GPU/async/comptime
```

nhưng **không bê nguyên syntax của từng ngôn ngữ**.

Đặc biệt, Axiom đang đi theo hướng:

> **Semantic richness, syntactic restraint.**

Đây là hướng tôi nghĩ phù hợp với mục tiêu ban đầu của bạn hơn việc cố làm Core “cực nhỏ”.

---

# 79. Frozen invariants — BOOTSTRAP-066

```text
AIDIOM-20   Axiom idioms must map directly to frozen semantic mechanisms.
AIDIOM-21   Ordinary value operations use value syntax.
AIDIOM-22   Ownership is not exposed through punctuation-heavy syntax.
AIDIOM-23   Struct initialization does not require new.
AIDIOM-24   new is not a Core memory-management primitive.
AIDIOM-25   delete is not a Core memory-management primitive.
AIDIOM-26   Constructor behavior is ordinary function behavior.
AIDIOM-27   Methods remain syntax over functions.
AIDIOM-28   Method receiver semantics remain explicit.
AIDIOM-29   Default receiver syntax denotes read-oriented access.
AIDIOM-30   Mutable receivers use mut_view semantics.
AIDIOM-31   Consuming receivers use owning Self semantics.
AIDIOM-32   Ownership transfer does not require move at ordinary call sites.
AIDIOM-33   Clone is explicit.
AIDIOM-34   Copy and Clone remain distinct semantics.
AIDIOM-35   Explicit drop is the canonical early-cleanup operation.
AIDIOM-36   Result is the canonical recoverable-failure abstraction.
AIDIOM-37   Option is the canonical absence abstraction.
AIDIOM-38   Exceptions are not the canonical error mechanism.
AIDIOM-39   ? is the canonical Result/Option propagation syntax.
AIDIOM-40   view<T> is the canonical read capability type.
AIDIOM-41   mut_view<T> is the canonical mutable capability type.
AIDIOM-42   Implicit ephemeral view passing is permitted only in defined contexts.
AIDIOM-43   Persistent capability bindings are explicit.
AIDIOM-44   view is not an optimization hint.
AIDIOM-45   mut_view is not an optimization hint.
AIDIOM-46   Views do not imply ownership.
AIDIOM-47   Collections expose ownership through ordinary value semantics.
AIDIOM-48   Iteration uses the iterator abstraction.
AIDIOM-49   Mutable iteration must satisfy capability verification.
AIDIOM-50   Generic algorithms use generic constraints rather than inheritance.
AIDIOM-51   Trait is the canonical static behavior abstraction.
AIDIOM-52   dyn Trait explicitly requests dynamic behavior.
AIDIOM-53   Static dispatch is preferred where semantics permit.
AIDIOM-54   Newtypes provide nominal semantic distinctions.
AIDIOM-55   Type aliases do not create nominal identity.
AIDIOM-56   Pattern matching is the canonical algebraic control mechanism.
AIDIOM-57   if let is canonical for one interesting pattern.
AIDIOM-58   match is canonical for multiple alternatives.
AIDIOM-59   Destructuring follows ownership semantics.
AIDIOM-60   Async syntax does not imply thread creation.
AIDIOM-61   spawn remains a library/runtime abstraction.
AIDIOM-62   Concurrent async tasks should use structured concurrency where possible.
AIDIOM-63   Detached execution must be explicit.
AIDIOM-64   Thread creation remains a library/runtime operation.
AIDIOM-65   Channels are ownership-transfer abstractions.
AIDIOM-66   Shared mutable state requires explicit synchronization.
AIDIOM-67   Atomic access uses explicit atomic semantics and ordering.
AIDIOM-68   GPU kernels use ordinary Axiom syntax plus explicit kernel metadata.
AIDIOM-69   Comptime uses ordinary Axiom syntax.
AIDIOM-70   Reflection remains compile-time by default.
AIDIOM-71   FFI declarations explicitly identify ABI boundaries.
AIDIOM-72   Raw pointers remain boundary/system abstractions.
AIDIOM-73   Unsafe regions should be narrow but this is an idiomatic guideline.
AIDIOM-74   Unsafe is not a general optimization switch.
AIDIOM-75   Compiler optimizations should not require ordinary programmer hints.
AIDIOM-76   Performance hints remain optional attributes.
AIDIOM-77   Allocation strategy is explicit only when semantically relevant.
AIDIOM-78   Stable address requires an explicit storage contract.
AIDIOM-79   Logical identity should prefer handles over raw addresses.
AIDIOM-80   Str, String and Bytes remain semantically distinct.
AIDIOM-81   Bytes-to-text conversion is explicit.
AIDIOM-82   Resource cleanup uses deterministic Drop.
AIDIOM-83   Fallible cleanup uses explicit Result-returning operations.
AIDIOM-84   Drop does not propagate recoverable failure.
AIDIOM-85   Application APIs should minimize unnecessary capability exposure.
AIDIOM-86   Small Copy values should normally be passed by value.
AIDIOM-87   Views are used when aliasing/access semantics matter.
AIDIOM-88   Raw pointers should normally remain outside application APIs.
AIDIOM-89   Compiler/linter may provide non-semantic performance guidance.
AIDIOM-90   Performance lints cannot redefine language semantics.
AIDIOM-91   Module organization is semantic, not class-hierarchy driven.
AIDIOM-92   Public visibility and native export remain distinct.
AIDIOM-93   Naming conventions are tooling/ecosystem conventions.
AIDIOM-94   File naming conventions do not define module identity.
AIDIOM-95   Canonical idioms should minimize equivalent stylistic forms.
AIDIOM-96   Core syntax should avoid redundant semantic mechanisms.
AIDIOM-97   AI-generated code should have canonical mappings from intent to syntax.
AIDIOM-98   Idiomatic patterns cannot bypass semantic verification.
AIDIOM-99   Library idioms may evolve without changing Core semantics.
AIDIOM-100  Idiomatic Axiom code should remain readable without understanding compiler internals.
```

---

## Một vấn đề cần giải quyết trước khi đi sâu hơn

Có một điểm **chưa nên freeze vội**: cú pháp `view`/`mut_view` hiện tại đã đủ tốt về semantics, nhưng chúng ta cần kiểm tra toàn bộ API collection:

```axiom
view<T>
mut_view<T>
```

đặc biệt với:

```text
Array
Vec
String
Bytes
slice
iterator
nested views
view của struct field
view của view
multi-dimensional data
GPU buffers
FFI slices
```

Nếu không audit kỹ, sau này rất dễ xuất hiện những trường hợp syntax đẹp nhưng type system trở nên rối.

### Mốc tiếp theo: **BOOTSTRAP-067 — Axiom Collection, Slice/View & Data Access Model**

067 sẽ giải quyết chính xác vấn đề này: thiết kế thống nhất cho **Array / Vec / Slice / Str / Bytes / Buffer / view / mut_view / indexing / slicing / iteration**, bao gồm cả aliasing, relocation, bounds checking, multidimensional data và GPU/device views.

Đây là một mốc quan trọng vì **80% code hệ thống thực tế sẽ chạm vào data access**, và đây cũng là nơi triết lý “không cần pointer/reference bureaucracy” của Axiom phải chứng minh được trong thực tế.